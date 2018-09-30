"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import graphene

import backend.btc.schema_node
import backend.lnd.schema
import backend.stats.schema
import backend.user_profile.schema


class Configuration(graphene.ObjectType):
    testnet = graphene.Boolean(
        description="True if server runs in testnet mode")


class Query(backend.btc.schema_node.Query, backend.lnd.schema.Queries,
            backend.stats.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    get_configuration = graphene.Field(
        Configuration, description="Get the current server configuration")

    def resolve_get_configuration(self, info):
        # This one has not authentication
        return Configuration(testnet=True)


class Mutations(backend.lnd.schema.LnMutations,
                backend.user_profile.schema.UserMutations):
    pass


schema = graphene.Schema(
    query=Query,
    mutation=Mutations,
    subscription=backend.lnd.schema.LnSubscriptions)
