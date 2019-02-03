"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from mixer.backend.django import mixer

from backend.error_responses import Unauthenticated
from backend.test_utils.utils import mock_resolve_info

from .. import schema

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_user_type():
    instance = schema.UserType()
    assert instance, "Should instantiate a UserType object"


def test_resolve_get_current_user():
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)

    q = schema.Query()
    ret = q.resolve_get_current_user(resolve_info)
    assert isinstance(
        ret, Unauthenticated), "Should be an instance of Unauthenticated"

    user = mixer.blend("auth.User")
    req.user = user
    ret = q.resolve_get_current_user(resolve_info)
    assert ret.user == user, "Should return the current user if authenticated"
