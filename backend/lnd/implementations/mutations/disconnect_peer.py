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


class DisconnectPeerSuccess(graphene.ObjectType):
    result = graphene.String(default_value="OK")
    pubkey = graphene.String(
        description="The identity pubkey of the connected Lightning node")


class DisconnectPeerError(graphene.ObjectType):
    error_message = graphene.String()
    pubkey = graphene.String(description="The identity pubkey of the peer")


class DisconnectPeerPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, DisconnectPeerError,
                 WalletInstanceNotFound, WalletInstanceNotRunning,
                 DisconnectPeerSuccess)


class DisconnectPeerMutation(graphene.Mutation):
    class Arguments:
        pubkey = graphene.String(
            description="The identity pubkey of the Lightning node",
            required=True)

    @staticmethod
    def description():
        """Returns the description for this mutation. 
        The String is fetched directly from the lnd grpc package
        """
        return process_lnd_doc_string(
            lnrpc.LightningServicer.DisconnectPeer.__doc__)

    Output = DisconnectPeerPayload

    def mutate(self, info, pubkey: str):
        """https://api.lightning.community/?python#disconnectpeer"""

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
        request = ln.DisconnectPeerRequest(pub_key=pubkey)
        try:
            stub.DisconnectPeer(
                request, metadata=[('macaroon', channel_data.macaroon)])
        except grpc.RpcError as exc:
            # pylint: disable=E1101
            print(exc)
            if "unable to disconnect peer: peer {} is not connected".format(
                    pubkey) in exc.details():
                return DisconnectPeerError(
                    error_message="Peer not connected", pubkey=pubkey)

            return ServerError.generic_rpc_error(exc.code(), exc.details())

        return DisconnectPeerSuccess(pubkey=pubkey)
