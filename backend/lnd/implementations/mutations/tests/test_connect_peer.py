import pytest
from _pytest.monkeypatch import MonkeyPatch
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from faker import Faker
from mixer.backend.django import mixer

import backend
from backend.error_responses import Unauthenticated, WalletInstanceNotFound
from backend.lnd.implementations import ConnectPeerMutation
from backend.lnd.models import LNDWallet
from backend.lnd.utils import ChannelData
from backend.test_utils import utils

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_connect_peer(monkeypatch: MonkeyPatch):
    channel_data = ChannelData(
        channel=object(), macaroon="macaroon_data".encode(), error=None)
    monkeypatch.setattr(
        backend.lnd.implementations.mutations.start_daemon,
        "build_grpc_channel_manual",
        lambda rpc_server, rpc_port, cert_path, macaroon_path: channel_data)

    fake = Faker()
    pubkey = fake.sha256()  # pylint: disable=E1101
    host = "1.2.3.4:9735"

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = utils.mock_resolve_info(req)

    mut = ConnectPeerMutation()
    ret = mut.mutate(resolve_info, pubkey=pubkey, host=host, perm=False)
    assert isinstance(
        ret, Unauthenticated), "Should be an instance of Unauthenticated"

    req.user = mixer.blend("auth.User")
    ret = mut.mutate(resolve_info, pubkey=pubkey, host=host, perm=False)

    mixer.blend(LNDWallet, owner=mixer.blend("auth.User"))

    assert isinstance(ret, WalletInstanceNotFound
                      ), "Should be an instance of WalletInstanceNotFound"
