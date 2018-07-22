"""Contains all Prometheus queries

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

SYSTEM_UPTIME_IN_SECONDS = "(node_time_seconds-node_boot_time_seconds)"
SYSTEM_CPU_USAGE_PERCENT_5M_AVG = "avg(node_load5)/count(count(node_cpu_seconds_total)by(cpu))*100"
SYSTEM_MEMORY_USED_BYTES = "node_memory_MemTotal_bytes-node_memory_MemFree_bytes-node_memory_Cached_bytes-node_memory_Buffers_bytes-node_memory_Slab_bytes"
SYSTEM_MEMORY_FREE_BYTES = "node_memory_MemFree_bytes"
SYSTEM_MEMORY_AVAILABLE_BYTES = "node_memory_MemAvailable_bytes"
SYSTEM_MEMORY_TOTAL_BYTES = "node_memory_MemTotal_bytes"
SYSTEM_TRAFFIC_IN_IN_BYTES_24H = "sum(increase(node_network_receive_bytes_total[24h]))"
SYSTEM_TRAFFIC_OUT_IN_BYTES_24H = "sum(increase(node_network_transmit_bytes_total[24h]))"
