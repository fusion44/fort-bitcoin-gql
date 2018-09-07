"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import codecs
import collections
import configparser

import grpc
import aiogrpc

CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")

ChannelData = collections.namedtuple('ChannelData', ['channel', 'macaroon'])


def build_grpc_channel(testnet=False, is_async=False) -> ChannelData:
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
