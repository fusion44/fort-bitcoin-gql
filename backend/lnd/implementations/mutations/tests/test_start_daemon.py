import pytest
from _pytest.monkeypatch import MonkeyPatch
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from mixer.backend.django import mixer

import backend
from backend.error_responses import Unauthenticated
from backend.lnd.implementations import StartDaemonMutation
from backend.lnd.implementations.mutations.start_daemon import (
    StartDaemonInstanceIsAlreadyRunning, StartDaemonInstanceNotFound)
from backend.lnd.models import LNDWallet
from backend.lnd.utils import ChannelData
from backend.test_utils import utils

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_start_daemon(monkeypatch: MonkeyPatch):
    # patch the Popen function to avoid starting a
    # new LND instance everytime the test runs
    monkeypatch.setattr(
        backend.lnd.implementations.mutations.start_daemon.subprocess, "Popen",
        lambda *args, **kwargs: None)

    channel_data = ChannelData(
        channel=object(), macaroon="macaroon_data".encode(), error=None)
    monkeypatch.setattr(
        backend.lnd.implementations.mutations.start_daemon,
        "build_grpc_channel_manual",
        lambda rpc_server, rpc_port, cert_path, macaroon_path: channel_data)

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = utils.mock_resolve_info(req)
    wallet_password = "secure_pw"

    mut = StartDaemonMutation()
    ret = mut.mutate(resolve_info, False, wallet_password, 0)

    assert isinstance(
        ret, Unauthenticated), "Should be an instance of Unauthenticated"

    # "login" a user
    req.user = mixer.blend("auth.User")
    ret = mut.mutate(resolve_info, False, wallet_password, 0)

    # create a wallet by another user
    # the the logged in user doesn't have a wallet yet
    # so it should not return the other users wallet
    mixer.blend(LNDWallet, owner=mixer.blend("auth.User"))

    assert isinstance(ret, StartDaemonInstanceNotFound
                      ), "Should be an instance of StartDaemonInstanceNotFound"

    mixer.blend(LNDWallet, owner=req.user)

    # Fake lnd instance is running function to return True
    monkeypatch.setattr(backend.lnd.implementations.mutations.start_daemon,
                        "lnd_instance_is_running", lambda cfg: True)

    ret = mut.mutate(resolve_info, False, wallet_password, 0)

    assert isinstance(ret, StartDaemonInstanceIsAlreadyRunning
                      ), "Should throw a StartDaemonInstanceIsAlreadyRunning"

    # For the rest of the test we'll assume the wallet is not running
    monkeypatch.setattr(backend.lnd.implementations.mutations.start_daemon,
                        "lnd_instance_is_running", lambda cfg: False)
