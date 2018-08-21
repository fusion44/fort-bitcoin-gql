"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.test import RequestFactory
from mixer.backend.django import mixer

import backend
import backend.lnd.types as types
from backend.exceptions import ClientVisibleException
from backend.lnd import schema
from backend.test_utils.test_utils import mock_resolve_info

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_resolve_ln_decode_pay_req():
    """
    test if user is authenticated ✓
    """

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    query = schema.Query()
    with pytest.raises(ClientVisibleException) as excinfo:
        res = query.resolve_ln_decode_pay_req(resolveInfo)
    assert excinfo.value.code == 2, "Should be exception #2, unauthenticated"


def test_resolve_ln_get_info():
    """
    test if user is authenticated ✓
    """

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    query = schema.Query()
    with pytest.raises(ClientVisibleException) as excinfo:
        res = query.resolve_ln_get_info(resolveInfo)
    assert excinfo.value.code == 2, "Should be exception #2, unauthenticated"


def test_resolve_ln_get_channel_balance():
    """
    test if user is authenticated ✓
    """

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    query = schema.Query()
    with pytest.raises(ClientVisibleException) as excinfo:
        res = query.resolve_ln_get_channel_balance(resolveInfo)
    assert excinfo.value.code == 2, "Should be exception #2, unauthenticated"


def test_resolve_ln_get_wallet_balance():
    """
    test if user is authenticated ✓
    """

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    query = schema.Query()
    with pytest.raises(ClientVisibleException) as excinfo:
        res = query.resolve_ln_get_wallet_balance(resolveInfo)
    assert excinfo.value.code == 2, "Should be exception #2, unauthenticated"


def test_resolve_ln_get_transactions():
    """
    test if user is authenticated ✓
    """

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    query = schema.Query()
    with pytest.raises(ClientVisibleException) as excinfo:
        res = query.resolve_ln_get_transactions(resolveInfo)
    assert excinfo.value.code == 2, "Should be exception #2, unauthenticated"


def test_resolve_ln_list_payments():
    """
    test if user is authenticated ✓
    """

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)

    query = schema.Query()
    with pytest.raises(ClientVisibleException) as excinfo:
        res = query.resolve_ln_list_payments(resolve_info)
    assert excinfo.value.code == 2, "Should be exception #2, unauthenticated"


def test_send_payment_mutation():
    """
    test if user is authenticated ✓
    """

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)

    mut = schema.SendPayment()

    with pytest.raises(ClientVisibleException) as excinfo:
        res = mut.mutate(None, resolve_info, {})
    assert excinfo.value.code == 2, "Should be exception #2, unauthenticated"
