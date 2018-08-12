"""A simple GraphQL API for the Bitcoin Core Node software
For a full description of all available API"s see https://bitcoin.org/en/developer-reference

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import graphene
import graphql

import backend.stats.types as types
import backend.stats.utils as utils
import backend.exceptions as exceptions


class Query(graphene.ObjectType):
    """Contains all system status related queries"""

    get_system_status = graphene.Field(types.SystemStatusType)

    def resolve_get_system_status(
            self, info: graphql.execution.base.ResolveInfo, **kwargs):
        """Resolves info about current system status"""

        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        field: graphene.Field = info.field_asts[0]
        selections = field.selection_set.selections

        sys_info = types.SystemStatusType()
        try:
            for selection in selections:  # type: graphene.Field
                name = selection.name.value
                if name == "uptime":
                    sys_info.uptime = utils.get_system_uptime()
                elif name == "cpuLoad":
                    sys_info.cpu_load = utils.get_system_cpu_load()
                elif name == "trafficIn":
                    sys_info.traffic_in = utils.get_system_traffic_in()
                elif name == "trafficOut":
                    sys_info.traffic_out = utils.get_system_traffic_out()
                elif name == "memoryUsed":
                    sys_info.memory_used = utils.get_system_mem_used()
                elif name == "memoryFree":
                    sys_info.memory_free = utils.get_system_mem_free()
                elif name == "memoryAvailable":
                    sys_info.memory_available = utils.get_system_mem_available() # yapf: disable
                elif name == "memoryTotal":
                    sys_info.memory_total = utils.get_system_mem_total()
        except exceptions.ClientVisibleException as error:
            raise exceptions.custom(error.message)
        except Exception as error:
            raise exceptions.unknown()

        return sys_info
