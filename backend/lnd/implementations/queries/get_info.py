"""Implementation for the LnGetInfo query"""
import json

import grpc
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnInfoType
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config)


def get_info_query(wallet: LNDWallet) -> LnInfoType:
    cfg = build_lnd_wallet_config(wallet.pk)

    channel_data = build_grpc_channel_manual(
        rpc_server="127.0.0.1",
        rpc_port=cfg.rpc_listen_port_ipv4,
        cert_path=cfg.tls_cert_path,
        macaroon_path=cfg.admin_macaroon_path)

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
    return LnInfoType(json_data)
