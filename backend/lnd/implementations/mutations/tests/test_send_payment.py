import pytest
from _pytest.monkeypatch import MonkeyPatch
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from mixer.backend.django import mixer

import backend
from backend.error_responses import Unauthenticated, WalletInstanceNotFound
from backend.lnd.implementations import SendPaymentMutation

from backend.lnd.models import LNDWallet
from backend.lnd.utils import ChannelData
from backend.test_utils import utils

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_send_payment(monkeypatch: MonkeyPatch):
    channel_data = ChannelData(
        channel=object(), macaroon="macaroon_data".encode(), error=None)
    monkeypatch.setattr(
        backend.lnd.implementations.mutations.start_daemon,
        "build_grpc_channel_manual",
        lambda rpc_server, rpc_port, cert_path, macaroon_path: channel_data)

    pay_req = "lntb15u1pd6wnd8pp5r40msee030q5asmd6nvffjhxxwr6cc69jmttz9mc43cazsexdwrqdq4xysyymr0vd4kzcmrd9hx7cqp2d9quy47hkjxq0e9yynjz5lkv2vkd8t5xs8uqguahgppkh80aeq9nqdh2qvu9zpkqgt3z7qwksj2709un3ejqnmz6hh0s6hcjs5nxdtsq8wf448"

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = utils.mock_resolve_info(req)

    mut = SendPaymentMutation()
    ret = mut.mutate(resolve_info, payment_request=pay_req)

    assert isinstance(
        ret.payment_result,
        Unauthenticated), "Should be an instance of Unauthenticated"

    # "login" a user
    req.user = mixer.blend("auth.User")
    ret = mut.mutate(resolve_info, payment_request=pay_req)

    # create a wallet by another user
    # the the logged in user doesn't have a wallet yet
    # so it should not return the other users wallet
    mixer.blend(LNDWallet, owner=mixer.blend("auth.User"))

    assert isinstance(ret.payment_result, WalletInstanceNotFound
                      ), "Should be an instance of WalletInstanceNotFound"
