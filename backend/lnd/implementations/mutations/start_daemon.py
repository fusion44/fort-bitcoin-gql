"""Implementation of the start daemon query"""
import json
import os
import subprocess
import time

import graphene
import grpc
from django.db.models import QuerySet
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import ServerError, Unauthenticated
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnInfoType
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_startup_args, build_lnd_wallet_config,
                               lnd_instance_is_running)


class StartDaemonSuccess(graphene.ObjectType):
    info = graphene.Field(LnInfoType)


class StartDaemonInstanceNotFound(graphene.ObjectType):
    error_message = graphene.String(
        default_value="No wallet instance found for User")
    suggestions = graphene.String(
        default_value=
        "Use createLightningWallet and lnStartDaemon to create the wallet")


class StartDaemonInstanceIsAlreadyRunning(graphene.ObjectType):
    error_message = graphene.String(
        default_value="The instance is already running")
    suggestions = graphene.String(
        default_value=
        "In case of problems, RestartDaemon might help resolve them")


class StartDaemonError(graphene.ObjectType):
    error_message = graphene.String()


class StartDaemonPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, StartDaemonInstanceNotFound,
                 StartDaemonError, StartDaemonInstanceIsAlreadyRunning,
                 StartDaemonSuccess)


class StartDaemonMutation(graphene.Mutation):
    class Arguments:
        """The arguments class for the mutation"""
        wallet_password = graphene.String(
            description=
            "wallet_password should be the current valid passphrase for the daemon. This will be required to decrypt on-disk material that the daemon requires to function properly."
        )

        recovery_window = graphene.Int(
            default_value=0,
            description=
            "recovery_window is an optional argument specifying the address lookahead when restoring a wallet seed. The recovery window applies to each invdividual branch of the BIP44 derivation paths. Supplying a recovery window of zero indicates that no addresses should be recovered, such after the first initialization of the wallet."
        )

        autopilot = graphene.Boolean(
            default_value=False,
            description="Whether the autopilot feature should be used.")

    Output = StartDaemonPayload

    @staticmethod
    def description():
        """Returns the description for this mutation."""
        return "Starts the LND daemon and unlocks the wallet"

    def mutate(self, info, autopilot: bool, wallet_password: str,
               recovery_window: int):
        """Starts the LND process and unlocks the wallet if user provides the password"""

        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res: QuerySet = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return StartDaemonInstanceNotFound()

        wallet: LNDWallet = res.first()

        return start_daemon_mutation(
            wallet,
            autopilot,
            wallet_password,
        )


def start_daemon_mutation(wallet: LNDWallet,
                          autopilot: bool,
                          wallet_password: str,
                          recovery_window: int = 0) -> LnInfoType:
    cfg = build_lnd_wallet_config(wallet.pk)

    if lnd_instance_is_running(cfg):
        return StartDaemonInstanceIsAlreadyRunning()

    try:
        args = build_lnd_startup_args(autopilot, wallet)
        # Start LND instance
        subprocess.Popen(
            args["args"],
            cwd=r'{}'.format(args["data_dir"]),
            preexec_fn=os.setpgrp)

        time.sleep(2)
    except grpc.RpcError as exc:
        # pylint: disable=E1101
        print(exc)
        return ServerError.generic_rpc_error(exc.code(), exc.details())

    # build the channel to the newly started daemon

    channel_data = build_grpc_channel_manual(
        rpc_server="127.0.0.1",
        rpc_port=cfg.rpc_listen_port_ipv4,
        cert_path=cfg.tls_cert_path,
        macaroon_path=cfg.admin_macaroon_path)

    if channel_data.error is not None:
        return channel_data.error

    # unlock the wallet
    stub = lnrpc.WalletUnlockerStub(channel_data.channel)
    request = ln.UnlockWalletRequest(
        wallet_password=wallet_password.encode(),
        recovery_window=recovery_window)
    stub.UnlockWallet(request)

    # LND requires a few seconds after unlocking until
    # it's fully operational
    time.sleep(5)

    # Unlocking the wallet requires a rebuild of the channel
    channel_data = build_grpc_channel_manual(
        rpc_server="127.0.0.1",
        rpc_port=cfg.rpc_listen_port_ipv4,
        cert_path=cfg.tls_cert_path,
        macaroon_path=cfg.admin_macaroon_path,
        rebuild=True)

    if channel_data.error is not None:
        return channel_data.error

    # get the latest info
    stub = lnrpc.LightningStub(channel_data.channel)
    request = ln.GetInfoRequest()

    try:
        response = stub.GetInfo(
            request, metadata=[('macaroon', channel_data.macaroon)])
    except grpc.RpcError as exc:
        # pylint: disable=E1101
        print(exc)
        return ServerError.generic_rpc_error(exc.code(), exc.details())

    json_data = json.loads(
        MessageToJson(
            response,
            preserving_proto_field_name=True,
            including_default_value_fields=True,
        ))
    return StartDaemonSuccess(info=LnInfoType(json_data))
