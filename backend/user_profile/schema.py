"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import graphene

from backend.user_profile.implementations import CreateUserMutation
from backend.user_profile.types import UserType


class Query(object):

    current_user = graphene.Field(UserType)

    def resolve_current_user(self, info):
        if not info.user.is_authenticated:
            return None
        return info.user


class UserMutations(graphene.ObjectType):
    class Meta:
        description = "Contains all mutations related to user management"

    create_user = CreateUserMutation.Field(
        description=CreateUserMutation.description())
