import grpc
import pytest
from _pytest.monkeypatch import MonkeyPatch
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from mixer.backend.django import mixer

import backend
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound)
from backend.lnd.implementations import GetLnWalletStatusQuery
from backend.lnd.implementations.queries.get_ln_wallet_status import (
    GetLnWalletStatusLocked, GetLnWalletStatusNotInitialized,
    GetLnWalletStatusOperational)
from backend.lnd.models import LNDWallet
from backend.lnd.utils import ChannelData
from backend.test_utils import utils

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


class FakeLightningStubUnimplemented(object):
    def __init__(self, *args, **kwargs):
        pass

    def GetInfo(self, *args, **kwargs):
        err = grpc.RpcError()
        err.code = lambda: grpc.StatusCode.UNIMPLEMENTED
        err.details = lambda: "Failed building the channel"
        raise err


class FakeLightningStubNoError(object):
    def __init__(self, *args, **kwargs):
        pass

    def GetInfo(self, *args, **kwargs):
        return {}


def test_get_ln_wallet_status(monkeypatch: MonkeyPatch):
    channel_data = ChannelData(
        channel=object(), macaroon="macaroon_data".encode(), error=None)
    monkeypatch.setattr(
        backend.lnd.implementations.queries.get_ln_wallet_status,
        "build_grpc_channel_manual",
        lambda rpc_server, rpc_port, cert_path, macaroon_path: channel_data)

    monkeypatch.setattr(
        backend.lnd.implementations.queries.get_ln_wallet_status,
        "build_lnd_wallet_config", lambda pk: utils.fake_lnd_wallet_config())

    query = GetLnWalletStatusQuery()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = utils.mock_resolve_info(req)

    query = GetLnWalletStatusQuery()
    ret = query.resolve_get_ln_wallet_status(resolve_info)

    assert isinstance(
        ret, Unauthenticated), "Should be an instance of Unauthenticated"

    # "login" a user
    req.user = mixer.blend("auth.User")
    ret = query.resolve_get_ln_wallet_status(resolve_info)
    assert isinstance(ret, WalletInstanceNotFound
                      ), "Should be an instance of WalletInstanceNotFound"

    wallet = LNDWallet()
    wallet.owner = req.user
    wallet.public_alias = "public_alias"
    wallet.name = "name"
    wallet.testnet = True
    wallet.initialized = False
    wallet.save()

    ret = query.resolve_get_ln_wallet_status(resolve_info)
    assert isinstance(
        ret, GetLnWalletStatusNotInitialized
    ), "Should be an instance of GetLnWalletStatusNotInitialized"

    wallet.initialized = True
    wallet.save()

    # Test build channel failure
    monkeypatch.setattr(
        backend.lnd.implementations.queries.get_ln_wallet_status,
        "build_grpc_channel_manual",
        lambda *args, **kwargs: utils.fake_build_grpc_channel_manual(
            ServerError(error_message="Some error occurred!")))

    ret = query.resolve_get_ln_wallet_status(resolve_info)
    assert isinstance(ret, ServerError), "Should be an instance of ServerError"

    # Test the get info request
    monkeypatch.setattr(
        backend.lnd.implementations.queries.get_ln_wallet_status,
        "build_grpc_channel_manual",
        lambda *args, **kwargs: utils.fake_build_grpc_channel_manual())

    monkeypatch.setattr(
        backend.lnd.implementations.queries.get_ln_wallet_status.lnrpc,
        "LightningStub", FakeLightningStubUnimplemented)

    monkeypatch.setattr(
        backend.lnd.implementations.queries.get_ln_wallet_status.ln,
        "GetInfoRequest", object)

    ret = query.resolve_get_ln_wallet_status(resolve_info)
    assert isinstance(ret, GetLnWalletStatusLocked
                      ), "Should be an instance of GetLnWalletStatusLocked"

    monkeypatch.setattr(
        backend.lnd.implementations.queries.get_ln_wallet_status.lnrpc,
        "LightningStub", FakeLightningStubNoError)

    ret = query.resolve_get_ln_wallet_status(resolve_info)
    assert isinstance(
        ret, GetLnWalletStatusOperational
    ), "Should be an instance of GetLnWalletStatusOperational"
