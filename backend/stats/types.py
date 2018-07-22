"""Contains all types necessary for the Stats Server

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import graphene


class SystemStatusType(graphene.ObjectType):
    uptime = graphene.Float(description="System uptime in seconds")
    cpu_load = graphene.Float(description="System CPU load in percent")
    memory_used = graphene.Float(description="Systems used memory")
    memory_free = graphene.Float(description="Systems free memory")
    memory_available = graphene.Float(description="Systems available memory")
    memory_total = graphene.Float(description="Systems total memory")
    traffic_in = graphene.Float(
        description="System incoming traffic of the last 24h in bytes")
    traffic_out = graphene.Float(
        description="System outgoing traffic of the last 24h in bytes")

    def __init__(self,
                 uptime=-1,
                 cpu_load=0,
                 memory_used=0,
                 memory_free=0,
                 memory_available=0,
                 memory_total=0,
                 traffic_in=0,
                 traffic_out=0):
        self.uptime = uptime
        self.cpu_load = cpu_load
        self.memory_used = memory_used
        self.memory_free = memory_free
        self.memory_available = memory_available
        self.memory_total = memory_total
        self.traffic_in = traffic_in
        self.traffic_out = traffic_out
