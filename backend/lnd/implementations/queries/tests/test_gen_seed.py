import grpc
import pytest
from _pytest.monkeypatch import MonkeyPatch
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from mixer.backend.django import mixer

import backend
from backend.error_responses import ServerError, Unauthenticated
from backend.lnd.implementations import GenSeedQuery
from backend.lnd.implementations.queries.gen_seed import \
    GenSeedWalletInstanceNotFound
from backend.lnd.models import LNDWallet
from backend.test_utils.test_utils import mock_resolve_info

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_gen_seed(monkeypatch: MonkeyPatch):
    """
    test if user is authenticated ✓
    test if user has active wallet instance ✓
    test if FileNotFoundError is handled
    test if RPC errors are handled ✓
    test if RPC timeout errors are handled
    test if aezeed_passphrase is passed to GenSeedRequest
    test if seed_entropy is passed to GenSeedRequest
    """

    test_input = {"aezeed_passphrase": "123", "seed_entropy": "456"}

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)

    query = GenSeedQuery()
    ret = query.resolve_ln_gen_seed(resolve_info, **test_input)

    assert isinstance(
        ret, Unauthenticated), "Should be an instance of Unauthenticated"

    # "login" a user
    req.user = mixer.blend("auth.User")
    ret = query.resolve_ln_gen_seed(resolve_info, **test_input)

    # create a wallet by another user
    # the the logged in user doesn't have a wallet yet
    # so it should not return the other users wallet
    mixer.blend(LNDWallet, owner=mixer.blend("auth.User"))

    assert isinstance(
        ret, GenSeedWalletInstanceNotFound
    ), "Should be an instance of GenSeedWalletInstanceNotFound"

    mixer.blend(LNDWallet, owner=req.user)

    # Test for FileNotFoundErrors
    err_message = "File /home/btc/lnd/lnd.conf not found"
    monkeypatch.setattr(
        backend.lnd.implementations.queries.gen_seed,
        "build_grpc_channel_manual",
        lambda rpc_server, rpc_port, cert_path: raise_error(FileNotFoundError(err_message))
    )

    ret = query.resolve_ln_gen_seed(resolve_info, **test_input)

    assert isinstance(ret, ServerError), "Should throw a ServerError"
    assert ret.error_message is err_message, "Should shot the correct message"

    # Test for errors while establishing gRPC channel
    monkeypatch.setattr(backend.lnd.implementations.queries.gen_seed,
                        "build_grpc_channel_manual",
                        fake_build_channel_RPC_err)

    ret = query.resolve_ln_gen_seed(resolve_info, **test_input)

    assert isinstance(ret, ServerError), "Should throw a server error"
    assert "Failed building the channel" in ret.error_message, "Should contain the right message"

    # Test for gRPC channel timeouts
    monkeypatch.setattr(backend.lnd.implementations.queries.gen_seed,
                        "build_grpc_channel_manual",
                        lambda rpc_server, rpc_port, cert_path: raise_error(grpc.FutureTimeoutError()))

    ret = query.resolve_ln_gen_seed(resolve_info, **test_input)

    assert isinstance(ret, ServerError), "Should throw a server error"
    assert "gRPC connection timeout" in ret.error_message, "Should contain the right message"


def raise_error(err):
    raise err


def fake_build_channel_RPC_err(rpc_server, rpc_port, cert_path):
    err = grpc.RpcError()
    err.code = 1337
    err.details = "Failed building the channel"
    raise err
