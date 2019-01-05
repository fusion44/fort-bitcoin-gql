"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import codecs
import collections
import configparser
import os
import subprocess

import aiogrpc
import grpc
import psutil

from backend.error_responses import ServerError, WalletInstanceNotRunning

CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")

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


def build_grpc_channel_manual(rpc_server,
                              rpc_port,
                              cert_path,
                              macaroon_path=None,
                              is_async=False) -> ChannelData:
    """Opens a grpc channel and returns the data as part of the ChannelData
    object. If an error occurs, ChannelData.error will not be None."""

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
        network,
    ]

    if node == "btcd":
        lnd_args.extend([
            "--bitcoin.node=btcd",
            "--btcd.rpchost=localhost",
        ])
    elif node == "bitcoind":
        lnd_args.extend([
            "--bitcoin.node=bitcoind",
            "--bitcoind.rpchost=localhost",
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
