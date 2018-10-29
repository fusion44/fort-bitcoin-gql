import graphene
import grpc
from django.db.models import QuerySet

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound,
                                     WalletInstanceNotRunning)
from backend.lnd.models import LNDWallet
from backend.lnd.utils import (LNDWalletConfig, build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class ConnectPeerSuccess(graphene.ObjectType):
    result = graphene.String(default_value="OK")
    pubkey = graphene.String(
        description="The identity pubkey of the connected Lightning node")


class ConnectPeerError(graphene.ObjectType):
    error_message = graphene.String()
    pubkey = graphene.String(
        description="The identity pubkey of the failed peer")
    host = graphene.String(description="The host of the failed peer")


class ConnectPeerPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, ConnectPeerError,
                 WalletInstanceNotFound, WalletInstanceNotRunning,
                 ConnectPeerSuccess)


class ConnectPeerMutation(graphene.Mutation):
    class Arguments:
        pubkey = graphene.String(
            description="The identity pubkey of the Lightning node",
            required=True)

        host = graphene.String(
            description=
            "The network location of the lightning node, e.g. 69.69.69.69:1337 or localhost:10011",
            required=True)

        perm = graphene.Boolean(
            description=
            "If set, the daemon will attempt to persistently connect to the target peer. Otherwise, the call will be synchronous.",
            default_value=False)

    @staticmethod
    def description():
        """Returns the description for this mutation. 
        The String is fetched directly from the lnd grpc package
        """
        return process_lnd_doc_string(
            lnrpc.LightningServicer.ConnectPeer.__doc__)

    Output = ConnectPeerPayload

    def mutate(self, info, pubkey: str, host: str, perm: bool):
        """https://api.lightning.community/?python#connectpeer"""

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

        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.ConnectPeerRequest(
            addr={
                "pubkey": pubkey,
                "host": host
            }, perm=perm)
        try:
            response = stub.ConnectPeer(
                request, metadata=[('macaroon', channel_data.macaroon)])
        except grpc.RpcError as exc:
            # pylint: disable=E1101
            print(exc)
            if "dial tcp {}: connect: connection refused".format(
                    host) in exc.details():
                return ConnectPeerError(
                    error_message="Peer refused to connect",
                    pubkey=pubkey,
                    host=host)
            if "already connected to peer: {}".format(host) in exc.details():
                return ConnectPeerError(
                    error_message="Already connected to peer",
                    pubkey=pubkey,
                    host=host)

            return ServerError.generic_rpc_error(exc.code(), exc.details())

        return ConnectPeerSuccess(pubkey=pubkey)
