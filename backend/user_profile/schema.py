"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import logging

import graphene

from backend.error_responses import ServerError, Unauthenticated
from backend.user_profile.implementations import CreateUserMutation
from backend.user_profile.types import UserType

LOGGER = logging.getLogger(__name__)


class GetCurrentUserError(graphene.ObjectType):
    error_message = graphene.String()


class GetCurrentUserSuccess(graphene.ObjectType):
    user = graphene.Field(UserType)


class GetCurrentUserResponse(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, GetCurrentUserError,
                 GetCurrentUserSuccess)


class Query(object):

    get_current_user = graphene.Field(
        GetCurrentUserResponse,
        description="Returns the user data for the supplied token.")

    def resolve_get_current_user(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            return Unauthenticated()
        return GetCurrentUserSuccess(user=info.context.user)


class UserMutations(graphene.ObjectType):
    class Meta:
        description = "Contains all mutations related to user management"

    create_user = CreateUserMutation.Field(
        description=CreateUserMutation.description())
