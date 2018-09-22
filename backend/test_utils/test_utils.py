"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import grpc
import pytest
from graphql.execution.base import ResolveInfo

pytestmark = pytest.mark.django_db


def mock_resolve_info(req) -> ResolveInfo:
    return ResolveInfo(None, None, None, None, None, None, None, None, None,
                       req)


def raise_error(err):
    """Raises the given error. Useful for mocking
    functions that raise exceptions using lambdas"""
    raise err


def fake_build_channel_gRPC_err(rpc_server, rpc_port, cert_path,
                                macaroon_path):
    err = grpc.RpcError()
    err.code = 1337
    err.details = "Failed building the channel"
    raise err
