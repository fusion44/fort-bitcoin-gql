"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import codecs
import collections
import configparser
import hashlib
import logging
import os
import subprocess

import aiogrpc
import grpc
import psutil

from backend.error_responses import ServerError, WalletInstanceNotRunning
from backend.lnd.models import IPAddress

CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")

LOGGER = logging.getLogger(__name__)

ChannelData = collections.namedtuple('ChannelData',
                                     ['channel', 'macaroon', 'error'])

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

BTCNodeConfig = collections.namedtuple(
    'BTCNodeConfig',
    [
        "bitcoin_node",  # btcd and bitcoind
        "network",  # btcd and bitcoind
        "rpc_username",  # btcd and bitcoind
        "rpc_password",  # btcd and bitcoind
        "rpc_host",  # btcd and bitcoind
        "rpc_port",  # btcd and bitcoind
        "bitcoind_rpc_use_https",  # bitcoind only
        "bitcoind_zmqpubrawblock",  # bitcoind only
        "bitcoind_zmqpubrawtx",  # bitcoind only
    ])


class ChannelCache():
    """ChannelCache opens and caches opened gRPC channels.

    Use get() to retrieve the channel.

    The gRPC Channel class documentation states that gRPC
    will try to reconnect upon failure.

    lru_cache is not used to avoid premature channel closing
    """

    def __init__(self):
        self._cache = {}

    def get(self, rpc_server, rpc_port, cert_path, macaroon_path,
            is_async) -> ChannelData:
        """Gets a channel for the given parameters. If there is no 
        active channel in the cache it'll open transparently one 
        for the caller.

        Args:
            rpc_server: rpc server address
            rpc_port: rpc server port
            cert_path: path to the certificate
            macaroon_path: path to the macaroon file
            is_async: whether this channel should by an async channel

        Returns:
            A ChannelData object
        """

        hash_str = "{}-{}-{}-{}-{}".format(rpc_server, rpc_port, cert_path,
                                           macaroon_path, is_async)
        _hash = hashlib.md5(hash_str.encode("utf-8")).hexdigest()
        try:
            # check if channel exists
            channel_data = self._cache[_hash]
            return channel_data
        except KeyError:
            # channel does not yet exist, open it
            channel_data = self._open_channel(rpc_server, rpc_port, cert_path,
                                              macaroon_path, is_async)
            self._cache[_hash] = channel_data
            LOGGER.info("New channel opened. Cache size: %s", len(self._cache))
            return channel_data

    def _open_channel(self, rpc_server, rpc_port, cert_path, macaroon_path,
                      is_async) -> ChannelData:
        try:
            macaroon = ""
            if macaroon_path is not None:
                with open(macaroon_path, 'rb') as f:
                    macaroon_bytes = f.read()
                    macaroon = codecs.encode(macaroon_bytes, 'hex')

            rpc_url = "{}:{}".format(rpc_server, rpc_port)

            cert = open(cert_path, "rb").read()
        except FileNotFoundError as file_error:
            print(file_error)
            return ChannelData(
                channel=None,
                macaroon=None,
                error=ServerError(error_message=str(file_error)))

        try:
            if is_async:
                creds = aiogrpc.ssl_channel_credentials(cert)
                channel = aiogrpc.secure_channel(rpc_url, creds)
            else:
                creds = grpc.ssl_channel_credentials(cert)
                channel = grpc.secure_channel(rpc_url, creds)
                grpc.channel_ready_future(channel).result(timeout=2)

        except grpc.RpcError as exc:
            # pylint: disable=E1101
            print(exc)
            return ChannelData(
                channel=None,
                macaroon=None,
                error=ServerError.generic_rpc_error(exc.code(), exc.details()))
        except grpc.FutureTimeoutError as exc:
            print(exc)
            return ChannelData(
                channel=None, macaroon=None, error=WalletInstanceNotRunning())

        return ChannelData(channel=channel, macaroon=macaroon, error=None)


CHANNEL_CACHE = ChannelCache()


def build_grpc_channel_manual(rpc_server,
                              rpc_port,
                              cert_path,
                              macaroon_path=None,
                              is_async=False) -> ChannelData:
    """Opens a grpc channel and returns the data as part of the ChannelData
    object. If an error occurs, ChannelData.error will not be None."""
    return CHANNEL_CACHE.get(rpc_server, rpc_port, cert_path, macaroon_path,
                             is_async)


def build_lnd_wallet_config(pk) -> LNDWalletConfig:
    """Generates the wallet configuration from the wallet id

    pk: The wallet id
    """
    path = os.path.join(CONFIG["DEFAULT"]["lnd_data_path"], str(pk))

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


def build_lnd_startup_args(autopilot: bool, wallet):
    node = CONFIG["DEFAULT"]["bitcoin_node"]
    network = "--bitcoin.testnet" if wallet.testnet else "--bitcoin.mainnet"

    cfg = build_lnd_wallet_config(wallet.pk)

    ip = IPAddress.objects.get(pk=1)

    lnd_args = [
        "nohup",
        "lnd",
        "--alias={}".format(wallet.public_alias),
        "--datadir={}".format(cfg.data_dir),
        "--tlscertpath={}".format(cfg.tls_cert_path),
        "--tlskeypath={}".format(cfg.tls_key_path),
        "--adminmacaroonpath={}".format(cfg.admin_macaroon_path),
        "--readonlymacaroonpath={}".format(cfg.read_only_macaroon_path),
        "--logdir={}".format(cfg.log_dir),
        "--listen=0.0.0.0:{}".format(cfg.listen_port_ipv4),
        "--listen=[::1]:{}".format(cfg.listen_port_ipv6),
        "--rpclisten=localhost:{}".format(cfg.rpc_listen_port_ipv4),
        "--rpclisten=[::1]:{}".format(cfg.rpc_listen_port_ipv4),
        "--restlisten=localhost:{}".format(cfg.rest_port_ipv4),
        "--restlisten=[::1]:{}".format(cfg.rest_port_ipv6),
        "--bitcoin.active",
        "--externalip={}:{}".format(ip.ip_address, cfg.listen_port_ipv4),
        network,
    ]

    node_cfg = get_node_config()

    if node == "btcd":
        lnd_args.extend([
            "--bitcoin.node=btcd",
            "--btcd.rpchost={}:{}".format(node_cfg.rpc_host,
                                          node_cfg.rpc_port),
            "--btcd.rpcuser={}".format(node_cfg.rpc_username),
            "--btcd.rpcpass={}".format(node_cfg.rpc_password),
        ])
    elif node == "bitcoind":
        lnd_args.extend([
            "--bitcoin.node=bitcoind",
            "--bitcoind.rpchost={}:{}".format(node_cfg.rpc_host,
                                              node_cfg.rpc_port),
            "--bitcoind.rpcuser={}".format(node_cfg.rpc_username),
            "--bitcoind.rpcpass={}".format(node_cfg.rpc_password),
            "--bitcoind.zmqpubrawblock={}".format(
                node_cfg.bitcoind_zmqpubrawblock),
            "--bitcoind.zmqpubrawtx={}".format(node_cfg.bitcoind_zmqpubrawtx),
        ])
    else:
        raise ValueError("Node should either be 'bitcoind' or 'btcd'")

    if autopilot:
        lnd_args.extend([
            "--autopilot.active",
            "--autopilot.maxchannels=5",
            "--autopilot.allocation=0.6",
        ])

    return {"args": lnd_args, "data_dir": cfg.data_dir}


def lnd_instance_is_running(cfg: LNDWalletConfig) -> bool:
    args = ['pgrep', '-f', "lnd.*--datadir={}".format(cfg.data_dir)]
    try:
        output = subprocess.check_output(args).decode().splitlines()
    except subprocess.CalledProcessError as exc:
        if exc.returncode is 1:
            return False

        raise RuntimeError(
            "Command '{}' return with error (code {}): {}".format(
                exc.cmd, exc.returncode, exc.output))

    if len(output) > 1:
        raise RuntimeError(
            "Found more than one lnd instance with the given data dir. PID's {}"
            .format(output))

    return psutil.pid_exists(int(output[0]))


def process_lnd_doc_string(doc: str):
    lines = doc.splitlines()
    new_doc_string = ""
    for line in lines:  # type: str
        line = line.strip()
        if line and not line.startswith("*"):
            new_doc_string += line + " "
    return new_doc_string


def get_node_config():
    bitcoin_node = CONFIG["DEFAULT"]["bitcoin_node"]  # btcd and bitcoind
    network = CONFIG["DEFAULT"]["network"]
    rpc_username = ""
    rpc_password = ""
    rpc_host = ""
    rpc_port = ""
    bitcoind_rpc_use_https = ""
    bitcoind_zmqpubrawblock = ""
    bitcoind_zmqpubrawtx = ""

    node_cfg = None
    if network == "testnet":
        if bitcoin_node == "btcd":
            node_cfg = CONFIG["BTCD_TESTNET"]
        elif bitcoin_node == "bitcoind":
            node_cfg = CONFIG["BITCOIND_TESTNET"]
        else:
            raise ValueError("Node should either be 'bitcoind' or 'btcd'")
    elif network == "mainnet":
        if bitcoin_node == "btcd":
            node_cfg = CONFIG["BTCD_MAINNET"]
        elif bitcoin_node == "bitcoind":
            node_cfg = CONFIG["BITCOIND_MAINNET"]
        else:
            raise ValueError("Node should either be 'bitcoind' or 'btcd'")
    else:
        raise ValueError("Network should either be 'testnet' or 'mainnet'")

    # applicable for both nodes
    rpc_username = node_cfg["btc_rpc_username"]
    rpc_password = node_cfg["btc_rpc_password"]
    rpc_host = node_cfg["btc_rpc_host"]
    rpc_port = node_cfg["btc_rpc_port"]

    # Bitcoind only
    if bitcoin_node == "bitcoind":
        bitcoind_rpc_use_https = node_cfg["btc_rpc_use_https"]
        bitcoind_zmqpubrawblock = node_cfg["btc_zmqpubrawblock"]
        bitcoind_zmqpubrawtx = node_cfg["btc_zmqpubrawtx"]

    return BTCNodeConfig(
        bitcoin_node=bitcoin_node,
        network=network,
        rpc_username=rpc_username,
        rpc_password=rpc_password,
        rpc_host=rpc_host,
        rpc_port=rpc_port,
        bitcoind_rpc_use_https=bitcoind_rpc_use_https,
        bitcoind_zmqpubrawblock=bitcoind_zmqpubrawblock,
        bitcoind_zmqpubrawtx=bitcoind_zmqpubrawtx,
    )
