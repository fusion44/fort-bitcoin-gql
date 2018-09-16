"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import codecs
import collections
import configparser
import os

import aiogrpc
import graphene
import grpc

from backend import exceptions
from backend.lnd import types

CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")

ChannelData = collections.namedtuple('ChannelData', ['channel', 'macaroon'])

LNDWalletConfig = collections.namedtuple('LNDWalletConfig', [
    "data_dir",
    "tls_cert_path",
    "tls_key_path",
    "admin_macaroon_path",
    "read_only_macaroon_path",
    "log_dir",
    "listen_port_ipv4",
    "listen_port_ipv6",
    "rpc_listen_port_ipv4",
    "rpc_listen_port_ipv6",
    "rest_port_ipv4",
    "rest_port_ipv6",
])


def build_grpc_channel_manual(rpc_server,
                              rpc_port,
                              cert_path,
                              macaroon_path=None,
                              is_async=False) -> ChannelData:
    macaroon = ""
    if macaroon_path is not None:
        with open(macaroon_path, 'rb') as f:
            macaroon_bytes = f.read()
            macaroon = codecs.encode(macaroon_bytes, 'hex')

    rpc_url = "{}:{}".format(rpc_server, rpc_port)

    cert = open(cert_path, "rb").read()

    if is_async:
        creds = aiogrpc.ssl_channel_credentials(cert)
        channel = aiogrpc.secure_channel(rpc_url, creds)
    else:
        creds = grpc.ssl_channel_credentials(cert)
        channel = grpc.secure_channel(rpc_url, creds)

    grpc.channel_ready_future(channel).result(timeout=2)

    return ChannelData(channel=channel, macaroon=macaroon)


def build_grpc_channel(testnet=False, is_async=False,
                       macaroon=True) -> ChannelData:
    """Builds a gRPC channel
    
    testnet: True if channel should be build for testnet
    is_async: Set to true if it is handled as a stream
    """
    rpc_server = CONFIG["LND_MAINNET"]["rpc_server"]
    rpc_port = CONFIG["LND_MAINNET"]["rpc_port"]
    cert_path = CONFIG["LND_MAINNET"]["lnd_cert_file"]
    macaroon_path = CONFIG["LND_MAINNET"]["lnd_macaroon"]

    if testnet:
        rpc_server = CONFIG["LND_TESTNET"]["rpc_server"]
        rpc_port = CONFIG["LND_TESTNET"]["rpc_port"]
        cert_path = CONFIG["LND_TESTNET"]["lnd_cert_file"]
        macaroon_path = CONFIG["LND_TESTNET"]["lnd_macaroon"]

    with open(macaroon_path, 'rb') as f:
        macaroon_bytes = f.read()
        macaroon = codecs.encode(macaroon_bytes, 'hex')
        f.close()

    rpc_url = "{}:{}".format(rpc_server, rpc_port)
    cert = open(cert_path, "rb").read()
    if is_async:
        creds = aiogrpc.ssl_channel_credentials(cert)
        channel = aiogrpc.secure_channel(rpc_url, creds)
    else:
        creds = grpc.ssl_channel_credentials(cert)
        channel = grpc.secure_channel(rpc_url, creds)
    return ChannelData(channel=channel, macaroon=macaroon)


def build_lnd_wallet_config(pk) -> LNDWalletConfig:
    """Generates the wallet configuration from the wallet id

    pk: The wallet id
    """
    path = os.path.join(CONFIG["DEFAULT"]["lnd_data_path"], str(pk))

    if not os.path.exists(path):
        os.makedirs(path)

    default_listen_port = 19739
    default_rpc_port = 12009
    default_rest_port = 8079

    return LNDWalletConfig(
        data_dir=path,
        tls_cert_path=path + "/tls.cert",
        tls_key_path=path + "/tls.key",
        admin_macaroon_path=path + "/admin.macaroon",
        read_only_macaroon_path=path + "/readonly.macaroon",
        log_dir=path + "/logs",
        listen_port_ipv6=default_listen_port + pk * 2,
        listen_port_ipv4=default_listen_port + pk * 2 - 1,
        rpc_listen_port_ipv6=default_rpc_port + pk * 2,
        rpc_listen_port_ipv4=default_rpc_port + pk * 2 - 1,
        rest_port_ipv6=default_rest_port + pk * 2,
        rest_port_ipv4=default_rest_port + pk * 2 - 1)
