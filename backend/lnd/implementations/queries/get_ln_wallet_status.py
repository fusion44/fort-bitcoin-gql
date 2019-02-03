import logging

import graphene
import grpc

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound,
                                     WalletInstanceNotRunning)
from backend.lnd.models import LNDWallet
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config)

LOGGER = logging.getLogger(__name__)


class GetLnWalletStatusError(graphene.ObjectType):
    error_message = graphene.String()


class GetLnWalletStatusNotInitialized(graphene.ObjectType):
    error_message = graphene.String(default_value="Wallet is not initialized")
    suggestions = graphene.String(
        default_value="Use the startDaemon mutation to unlock")


class GetLnWalletStatusLocked(graphene.ObjectType):
    error_message = graphene.String(default_value="Wallet is encrypted.")
    suggestions = graphene.String(
        default_value="Use the startDaemon mutation to unlock")


class GetLnWalletStatusOperational(graphene.ObjectType):
    info = graphene.String(default_value="running_normally")


class GetLnWalletStatusResponse(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, GetLnWalletStatusError,
                 WalletInstanceNotFound, WalletInstanceNotRunning,
                 GetLnWalletStatusOperational, GetLnWalletStatusLocked,
                 GetLnWalletStatusNotInitialized)


class GetLnWalletStatusQuery(graphene.ObjectType):
    get_ln_wallet_status = graphene.Field(
        GetLnWalletStatusResponse,
        description="GetWalletStatus returns the current state of the wallet",
    )

    def resolve_get_ln_wallet_status(self, info, **kwargs):
        """retrieve the current state of the wallet"""

        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res = LNDWallet.objects.filter(owner=info.context.user)

        # LND instance is not yet created.
        # User should call createWallet
        if not res:
            return WalletInstanceNotFound()

        # Wallet database object was created but
        # it is not yet initialized
        if not res.first().initialized:
            return GetLnWalletStatusNotInitialized()

        cfg = build_lnd_wallet_config(res.first().pk)

        channel_data = build_grpc_channel_manual(
            rpc_server="127.0.0.1",
            rpc_port=cfg.rpc_listen_port_ipv4,
            cert_path=cfg.tls_cert_path,
            macaroon_path=cfg.admin_macaroon_path)
        if channel_data.error is not None:
            return channel_data.error

        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.GetInfoRequest()

        try:
            stub.GetInfo(
                request, metadata=[('macaroon', channel_data.macaroon)])
        except grpc.RpcError as exc:
            # pylint: disable=E1101

            # This is a wanted exception.
            # When GetInfo returns UNIMPLEMENTED the wallet is likely locked
            if exc.code() == grpc.StatusCode.UNIMPLEMENTED:
                return GetLnWalletStatusLocked()

            # Unexpected exception
            LOGGER.exception(exc)
            return ServerError.generic_rpc_error(exc.code(), exc.details())

        return GetLnWalletStatusOperational()
