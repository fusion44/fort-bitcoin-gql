import pytest
from _pytest.monkeypatch import MonkeyPatch
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from mixer.backend.django import mixer

from backend.error_responses import Unauthenticated, WalletInstanceNotFound
from backend.lnd.implementations import ListPeersQuery
from backend.lnd.models import LNDWallet
from backend.test_utils import utils

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_list_peers(monkeypatch: MonkeyPatch):
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = utils.mock_resolve_info(req)

    query = ListPeersQuery()
    ret = query.resolve_ln_list_peers(resolve_info)

    assert isinstance(
        ret, Unauthenticated), "Should be an instance of Unauthenticated"

    # "login" a user
    req.user = mixer.blend("auth.User")
    ret = query.resolve_ln_list_peers(resolve_info)

    # create a wallet by another user
    # the the logged in user doesn't have a wallet yet
    # so it should not return the other users wallet
    mixer.blend(LNDWallet, owner=mixer.blend("auth.User"))

    assert isinstance(ret, WalletInstanceNotFound
                      ), "Should be an instance of WalletInstanceNotFound"
