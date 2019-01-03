"""Various utility functions for this project

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import configparser

from bitcoinrpc.authproxy import AuthServiceProxy

CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")


def make_rpc_auth_url(testnet=False):
    """Constructs the RPC authentication URL from configuration

    Keyword arguments:
        testnet -- whether to build the url for testnet (default False)

    Returns:
        AuthServiceProxy -- bitcoinrpc.authproxy.AuthServiceProxy with the auth info
    """

    if testnet:
        config = CONFIG["BITCOIND_TESTNET"]
    else:
        config = CONFIG["BITCOIND_MAINNET"]

    http_type = "http"

    if config["btc_rpc_use_https"] == "true":
        http_type = "https"

    url = "{}://{}:{}@{}:{}".format(
        http_type, config["btc_rpc_username"], config["btc_rpc_password"],
        config["btc_rpc_host"], config["btc_rpc_port"])

    return AuthServiceProxy(url)
