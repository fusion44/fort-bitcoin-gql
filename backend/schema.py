"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import graphene

import backend.btc.schema_node
import backend.lnd.schema
import backend.stats.schema


class Query(backend.btc.schema_node.Query, backend.lnd.schema.Queries,
            backend.stats.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


schema = graphene.Schema(
    query=Query,
    mutation=backend.lnd.schema.LnMutations,
    subscription=backend.lnd.schema.InvoiceSubscription)
