"""Implementation for the init wallet mutation"""
import time

import graphene
import grpc
from django.db.models import QuerySet

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound,
                                     WalletInstanceNotRunning)
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnInfoType
from backend.lnd.utils import (LNDWalletConfig, build_grpc_channel_manual,
                               build_lnd_wallet_config,
                               lnd_instance_is_running, process_lnd_doc_string)


class StopDaemonSuccess(graphene.ObjectType):
    info = graphene.Field(LnInfoType)


class StopDaemonError(graphene.ObjectType):
    error_message = graphene.String()


class StopDaemonPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, WalletInstanceNotFound,
                 StopDaemonError, StopDaemonSuccess, WalletInstanceNotRunning)


class StopDaemonMutation(graphene.Mutation):
    Output = StopDaemonPayload

    @staticmethod
    def description():
        """Returns the description for this mutation. 
        The String is fetched directly from the lnd grpc package
        """
        return process_lnd_doc_string(
            lnrpc.LightningServicer.StopDaemon.__doc__)

    def mutate(
            self,
            info,
    ):
        """https://api.lightning.community/?python#stopdaemon"""

        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res: QuerySet = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return WalletInstanceNotFound()

        wallet: LNDWallet = res.first()

        cfg: LNDWalletConfig = build_lnd_wallet_config(wallet.pk)

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
            # pylint: disable=E1101
            print(exc)
            return ServerError.generic_rpc_error(exc.code(), exc.details())

        start = time.time()
        while True:
            if not lnd_instance_is_running(cfg):
                return StopDaemonSuccess()

            if time.time() - start >= 10:
                return StopDaemonError(
                    error_message=
                    "Unable to shutdown the process within 10 seconds")

            time.sleep(1)
