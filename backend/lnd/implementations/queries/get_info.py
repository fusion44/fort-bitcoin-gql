"""Implementation for the LnGetInfo query"""
import json

import graphene
import grpc
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound)
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnInfoType
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config)


class GetInfoError(graphene.ObjectType):
    error_message = graphene.String()


class GetInfoSuccess(graphene.ObjectType):
    ln_info = graphene.Field(LnInfoType)


class GetInfoPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, WalletInstanceNotFound,
                 GetInfoError, GetInfoSuccess)


class GetInfoQuery(graphene.ObjectType):
    ln_get_info = graphene.Field(
        GetInfoPayload,
        description=
        "GetInfo returns general information concerning the lightning node including it’s identity pubkey, alias, the chains it is connected to, and information concerning the number of open+pending channels.",
    )

    def resolve_ln_get_info(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return WalletInstanceNotFound()

        return get_info_query(res.first())


def get_info_query(wallet: LNDWallet) -> LnInfoType:
    cfg = build_lnd_wallet_config(wallet.pk)

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
        response = stub.GetInfo(
            request, metadata=[('macaroon', channel_data.macaroon)])
    except grpc.RpcError as exc:
        print(exc)
        raise exc

    json_data = json.loads(
        MessageToJson(
            response,
            preserving_proto_field_name=True,
            including_default_value_fields=True,
        ))
    return GetInfoSuccess(LnInfoType(json_data))
