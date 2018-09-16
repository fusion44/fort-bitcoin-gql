"""Implementation for the generate seed query"""

import json

from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnGenSeedResponse
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config)


def gen_seed_query(
        wallet: LNDWallet,
        aezeed_passphrase: str,
        seed_entropy: str,
) -> LnGenSeedResponse:
    cfg = build_lnd_wallet_config(wallet.pk)

    channel_data = build_grpc_channel_manual(
        rpc_server="127.0.0.1",
        rpc_port=cfg.rpc_listen_port_ipv4,
        cert_path=cfg.tls_cert_path,
    )
    stub = lnrpc.WalletUnlockerStub(channel_data.channel)
    request = ln.GenSeedRequest(
        aezeed_passphrase=aezeed_passphrase, seed_entropy=seed_entropy)
    response = stub.GenSeed(request)
    json_data = json.loads(
        MessageToJson(response, preserving_proto_field_name=True))
    return LnGenSeedResponse(json_data)
