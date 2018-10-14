import pytest
from _pytest.monkeypatch import MonkeyPatch
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from faker import Faker
from mixer.backend.django import mixer

from backend.error_responses import Unauthenticated, WalletInstanceNotFound
from backend.lnd.implementations import DisconnectPeerMutation
from backend.lnd.models import LNDWallet
from backend.test_utils import utils

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_disconnect_peer():
    fake = Faker()
    pubkey = fake.sha256()  # pylint: disable=E1101

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = utils.mock_resolve_info(req)

    mut = DisconnectPeerMutation()
    ret = mut.mutate(resolve_info, pubkey=pubkey)
    assert isinstance(
        ret, Unauthenticated), "Should be an instance of Unauthenticated"

    req.user = mixer.blend("auth.User")
    ret = mut.mutate(resolve_info, pubkey=pubkey)

    mixer.blend(LNDWallet, owner=mixer.blend("auth.User"))

    assert isinstance(ret, WalletInstanceNotFound
                      ), "Should be an instance of WalletInstanceNotFound"
