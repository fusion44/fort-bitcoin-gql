import json

import graphene
import grpc
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound)
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnChannelBalance
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config)


class GetChannelBalanceError(graphene.ObjectType):
    error_message = graphene.String()


class GetChannelBalanceSuccess(graphene.ObjectType):
    ln_channel_balance = graphene.Field(LnChannelBalance)


class GetChannelBalanceResponse(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, GetChannelBalanceError,
                 GetChannelBalanceSuccess, WalletInstanceNotFound)


class GetChannelBalanceQuery(graphene.ObjectType):
    """Contains some Lightning RPC queries"""

    ln_get_channel_balance = graphene.Field(
        GetChannelBalanceResponse,
        description=
        "ChannelBalance returns the total funds available across all open channels in satoshis."
    )

    def resolve_ln_get_channel_balance(self, info, **kwargs):
        """https://api.lightning.community/#channelbalance"""
        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return WalletInstanceNotFound()

        cfg = build_lnd_wallet_config(res.first().pk)

        channel_data = build_grpc_channel_manual(
            rpc_server="127.0.0.1",
            rpc_port=cfg.rpc_listen_port_ipv4,
            cert_path=cfg.tls_cert_path,
            macaroon_path=cfg.admin_macaroon_path)
        if channel_data.error is not None:
            return channel_data.error

        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.ChannelBalanceRequest()

        try:
            response = stub.ChannelBalance(
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
        return GetChannelBalanceSuccess(LnChannelBalance(json_data))
