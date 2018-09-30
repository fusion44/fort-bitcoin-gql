import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TransactionTestCase
from mixer.backend.django import mixer

from backend.test_utils import utils
from backend.user_profile.implementations import CreateUserMutation
from backend.user_profile.implementations.mutations.create_user import (
    EMAIL_NOT_UNIQUE, PASSWORD_TO_SHORT, USER_AUTHENTICATED,
    USERNAME_NOT_UNIQUE, USERNAME_TO_SHORT, CreateUserError, CreateUserSuccess)

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


class CreateUserMutationTestCase(TransactionTestCase):
    def test_create_user(self):
        # pylint: disable=E1101
        req = RequestFactory().get("/")
        req.user = mixer.blend("auth.User")
        resolve_info = utils.mock_resolve_info(req)

        mut = CreateUserMutation()
        ret = mut.mutate(resolve_info, username="123", password="12345678")

        assert isinstance(
            ret.create_user,
            CreateUserError), "Should be an instance of CreateUserError"
        assert ret.create_user.error_type == USER_AUTHENTICATED

        user = mixer.blend("auth.User")
        req.user = AnonymousUser()
        ret = mut.mutate(
            resolve_info,
            username="123",
            password="12345678",
            email=user.email)

        assert isinstance(
            ret.create_user, CreateUserError
        ), "Should be an instance of CreateUserError (email not unique)"
        assert ret.create_user.error_type == EMAIL_NOT_UNIQUE

        ret = mut.mutate(resolve_info, username="12", password="12345678")

        assert isinstance(
            ret.create_user, CreateUserError
        ), "Should be an instance of CreateUserError (username to shot)"
        assert ret.create_user.error_type == USERNAME_TO_SHORT

        ret = mut.mutate(resolve_info, username="123", password="1234567")

        assert isinstance(
            ret.create_user, CreateUserError
        ), "Should be an instance of CreateUserError (password to shot)"
        assert ret.create_user.error_type == PASSWORD_TO_SHORT

        ret = mut.mutate(
            resolve_info,
            username=user.username,
            password="12345678",
        )

        assert isinstance(
            ret.create_user, CreateUserError
        ), "Should be an instance of CreateUserError (username not unique)"
        assert ret.create_user.error_type == USERNAME_NOT_UNIQUE

        ret = mut.mutate(
            resolve_info,
            username="username",
            password="12345678",
            email="user.email@email.com")

        assert isinstance(
            ret.create_user,
            CreateUserSuccess), "Should be an instance of CreateUserSuccess"
        assert ret.create_user.user.username == "username"
