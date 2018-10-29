import json

import graphene
import grpc
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound,
                                     WalletInstanceNotRunning)
from backend.lnd.models import LNDWallet
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class NewAddressError(graphene.ObjectType):
    error_message = graphene.String()


class NewAddressSuccess(graphene.ObjectType):
    address = graphene.String()


class NewAddressPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, WalletInstanceNotFound,
                 WalletInstanceNotRunning, NewAddressError, NewAddressSuccess)


class NewAddressQuery(graphene.ObjectType):
    ln_new_address = graphene.Field(
        NewAddressPayload,
        description=process_lnd_doc_string(
            lnrpc.LightningServicer.NewAddress.__doc__),
        address_type=graphene.String(
            default_value="np2wkh",
            description="""
- p2wkh:  Pay to witness key hash
- np2wkh: Pay to nested witness key hash (default)
"""))

    def resolve_ln_new_address(self, info, address_type):
        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return WalletInstanceNotFound()

        return get_info_query(res.first(), address_type)


def get_info_query(wallet: LNDWallet, address_type: str) -> str:
    cfg = build_lnd_wallet_config(wallet.pk)

    channel_data = build_grpc_channel_manual(
        rpc_server="127.0.0.1",
        rpc_port=cfg.rpc_listen_port_ipv4,
        cert_path=cfg.tls_cert_path,
        macaroon_path=cfg.admin_macaroon_path)

    if channel_data.error is not None:
        return channel_data.error

    stub = lnrpc.LightningStub(channel_data.channel)

    if address_type == "p2wkh":
        request = ln.NewAddressRequest(type="WITNESS_PUBKEY_HASH")
    elif address_type == "np2wkh":
        request = ln.NewAddressRequest(type="NESTED_PUBKEY_HASH")
    else:
        return NewAddressError(error_message="Unknown address type")

    try:
        response = stub.NewAddress(
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
    return NewAddressSuccess(json_data["address"])
