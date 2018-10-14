import json

import graphene
import grpc
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound)
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnChannel
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class ListChannelsError(graphene.ObjectType):
    error_message = graphene.String()


class ListChannelsSuccess(graphene.ObjectType):
    channels = graphene.List(LnChannel)


class ListChannelsPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, WalletInstanceNotFound,
                 ListChannelsError, ListChannelsSuccess)


class ListChannelsQuery(graphene.ObjectType):
    ln_list_channels = graphene.Field(
        ListChannelsPayload,
        description=process_lnd_doc_string(
            lnrpc.LightningServicer.ListChannels.__doc__))

    def resolve_ln_list_channels(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return WalletInstanceNotFound()

        return list_channels_query(res.first())


def list_channels_query(wallet: LNDWallet):
    cfg = build_lnd_wallet_config(wallet.pk)

    channel_data = build_grpc_channel_manual(
        rpc_server="127.0.0.1",
        rpc_port=cfg.rpc_listen_port_ipv4,
        cert_path=cfg.tls_cert_path,
        macaroon_path=cfg.admin_macaroon_path)

    if channel_data.error is not None:
        return channel_data.error

    stub = lnrpc.LightningStub(channel_data.channel)
    request = ln.ListChannelsRequest()

    try:
        response = stub.ListChannels(
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
    channel_list = []
    for c in json_data["channels"]:
        channel_list.append(LnChannel(c))
    return ListChannelsSuccess(channel_list)
