import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from backend.exceptions import ClientVisibleException
from backend.lnd import schema
from backend.test_utils.utils import mock_resolve_info

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


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
