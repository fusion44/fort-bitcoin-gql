"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import grpc
import pytest
from graphql.execution.base import ResolveInfo

from backend.lnd.utils import (LNDWalletConfig, ChannelData)

pytestmark = pytest.mark.django_db


def mock_resolve_info(req) -> ResolveInfo:
    return ResolveInfo(None, None, None, None, None, None, None, None, None,
                       req)


def raise_error(err):
    """Raises the given error. Useful for mocking
    functions that raise exceptions using lambdas"""
    raise err


def fake_lnd_wallet_config():
    return LNDWalletConfig(
        data_dir="",
        tls_cert_path="",
        tls_key_path="",
        admin_macaroon_path="",
        read_only_macaroon_path="",
        log_dir="",
        listen_port_ipv4="",
        listen_port_ipv6="",
        rpc_listen_port_ipv4="",
        rpc_listen_port_ipv6="",
        rest_port_ipv4="",
        rest_port_ipv6="")


def fake_build_grpc_channel_manual(error=None):
    """Returns a fake ChannelData object"""
    if error:
        return ChannelData(channel=None, macaroon=None, error=error)
    return ChannelData(channel=object(), macaroon=b"", error=None)