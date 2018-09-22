"""Implementation for the init wallet mutation"""
import time

import graphene
import grpc
from django.db.models import QuerySet

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import ServerError, Unauthenticated
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnInfoType
from backend.lnd.utils import (LNDWalletConfig, build_grpc_channel_manual,
                               build_lnd_wallet_config,
                               lnd_instance_is_running)


class StopDaemonSuccess(graphene.ObjectType):
    info = graphene.Field(LnInfoType)


class StopDaemonInstanceNotFound(graphene.ObjectType):
    error_message = graphene.String(
        default_value="No wallet instance found for User")
    suggestions = graphene.String(
        default_value=
        "Use createLightningWallet and lnInitWallet to create the wallet")


class StopDaemonInstanceNotRunning(graphene.ObjectType):
    error_message = graphene.String(
        default_value="The instance is not running")
    suggestions = graphene.String(
        default_value="Use startDaemon to start the wallet instance")


class StopDaemonError(graphene.ObjectType):
    error_message = graphene.String()


class StopDaemonPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, StopDaemonInstanceNotFound,
                 StopDaemonInstanceNotRunning, StopDaemonError,
                 StopDaemonSuccess)


class StopDaemonMutation(graphene.Mutation):
    Output = StopDaemonPayload

    def mutate(
            self,
            info,
    ):
        """https://api.lightning.community/?python#stopdaemon"""

        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res: QuerySet = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return StopDaemonInstanceNotFound()

        wallet: LNDWallet = res.first()

        cfg: LNDWalletConfig = build_lnd_wallet_config(wallet.pk)

        if not lnd_instance_is_running(cfg):
            return StopDaemonInstanceNotRunning()

        channel_data = build_grpc_channel_manual(
            rpc_server="127.0.0.1",
            rpc_port=cfg.rpc_listen_port_ipv4,
            cert_path=cfg.tls_cert_path,
            macaroon_path=cfg.admin_macaroon_path,
        )

        if channel_data.error is not None:
            return channel_data.error

        # stop daemon
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.StopRequest()
        try:
            response = stub.StopDaemon(
                request, metadata=[('macaroon', channel_data.macaroon)])
        except grpc.RpcError as exc:
            print(exc)
            return ServerError.generic_rpc_error(exc.code, exc.details)  # pylint: disable=E1101

        start = time.time()
        while True:
            if not lnd_instance_is_running(cfg):
                return StopDaemonSuccess()

            if time.time() - start >= 10:
                return StopDaemonError(
                    error_message=
                    "Unable to shutdown the process within 10 seconds")

            time.sleep(1)
