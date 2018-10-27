import json

import graphene
import grpc
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound)
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnPeer
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class ListPeersError(graphene.ObjectType):
    error_message = graphene.String()


class ListPeersSuccess(graphene.ObjectType):
    peers = graphene.List(LnPeer)


class ListPeersPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, WalletInstanceNotFound,
                 ListPeersError, ListPeersSuccess)


class ListPeersQuery(graphene.ObjectType):
    ln_list_peers = graphene.Field(
        ListPeersPayload,
        description=process_lnd_doc_string(
            lnrpc.LightningServicer.ListPeers.__doc__))

    def resolve_ln_list_peers(self, info, **kwargs):
        """https://api.lightning.community/#listpeers"""
        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return WalletInstanceNotFound()

        return list_peers_query(info, res.first())


def get_peer_has_channel(channel_data, peer_list):
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
    temp_map = {}
    for peer in peer_list:
        temp_map[peer.pub_key] = peer

    for channel in json_data["channels"]:
        try:
            temp_map[channel["remote_pubkey"]].has_channel = True
        except KeyError:
            pass


def list_peers_query(info, wallet: LNDWallet):
    cfg = build_lnd_wallet_config(wallet.pk)

    channel_data = build_grpc_channel_manual(
        rpc_server="127.0.0.1",
        rpc_port=cfg.rpc_listen_port_ipv4,
        cert_path=cfg.tls_cert_path,
        macaroon_path=cfg.admin_macaroon_path)

    if channel_data.error is not None:
        return channel_data.error

    stub = lnrpc.LightningStub(channel_data.channel)
    request = ln.ListPeersRequest()

    try:
        response = stub.ListPeers(
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
    peer_list = []
    for c in json_data["peers"]:
        peer_list.append(LnPeer(c))

    for selection in info.field_asts[0].selection_set.selections:
        if hasattr(selection, "type_condition"):
            if selection.type_condition.name.value == "ListPeersSuccess":
                for field in selection.selection_set.selections[
                        0].selection_set.selections:
                    if field.name.value == "hasChannel":
                        get_peer_has_channel(channel_data, peer_list)
                        break

    return ListPeersSuccess(peer_list)
