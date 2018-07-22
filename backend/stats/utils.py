"""Various utility functions for this project

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import configparser
import json
import urllib.request as request
import urllib.error
import http.client

import backend.stats.prom_queries as prom_queries

CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")


class PrometheusResponse(object):
    code: int = 0
    message = ""
    reason = ""
    data: object = ""

    def __init__(self,
                 code: int,
                 data: str,
                 message: str = "",
                 reason: str = ""):
        self.code = code
        self.message = message
        self.reason = reason
        self.data = json.loads(data)["data"]


def query_prometheus(query: str) -> PrometheusResponse:
    """Queries the Promethus API

    How to handle basic auth in Python:
    https://docs.python.org/3.1/howto/urllib2.html#id6

    Returns:
        str -- The complete URL
    """
    config = CONFIG["PROMETHEUS"]

    pw_mgr = request.HTTPPasswordMgrWithDefaultRealm()
    url = config["prom_api_url"]
    pw_mgr.add_password(None, url, config["prom_user_name"],
                        config["prom_user_password"])
    handler = request.HTTPBasicAuthHandler(pw_mgr)
    opener = request.build_opener(handler)
    request.install_opener(opener)

    try:
        output = request.urlopen("{}/api/v1/query?query={}".format(
            config["prom_api_url"], query))  # type: http.client.HTTPResponse
    except urllib.error.HTTPError as error:
        resp = PrometheusResponse(error.code, None, error.msg, error.reason)
        return resp
    except urllib.error.URLError as error:
        resp = PrometheusResponse(500, None, "", error.reason)
        return resp
    except Exception:
        resp = PrometheusResponse(500, None, "Internal Server Error")
        return resp

    resp = PrometheusResponse(output.code, output.read(), output.msg,
                              output.reason)
    return resp


def get_system_uptime() -> float:
    """Query for the node system uptime in seconds"""
    output = query_prometheus(prom_queries.SYSTEM_UPTIME_IN_SECONDS)
    uptime = float(output.data["result"][0]["value"][1])
    return uptime


def get_system_cpu_load() -> float:
    """Query for the current system CPU load 5m average"""
    output = query_prometheus(prom_queries.SYSTEM_CPU_USAGE_PERCENT_5M_AVG)
    cpu_load = float(output.data["result"][0]["value"][1])
    return cpu_load


def get_system_mem_used() -> int:
    """Query for the systems current used memory"""
    output = query_prometheus(prom_queries.SYSTEM_MEMORY_USED_BYTES)
    mem_used = int(output.data["result"][0]["value"][1])
    return mem_used


def get_system_mem_free() -> int:
    """Query for the systems current free memory"""
    output = query_prometheus(prom_queries.SYSTEM_MEMORY_FREE_BYTES)
    mem_free = int(output.data["result"][0]["value"][1])
    return mem_free


def get_system_mem_available() -> int:
    """Query for the systems current available memory"""
    output = query_prometheus(prom_queries.SYSTEM_MEMORY_AVAILABLE_BYTES)
    mem_available = int(output.data["result"][0]["value"][1])
    return mem_available


def get_system_mem_total() -> int:
    """Query for the systems current total memory"""
    output = query_prometheus(prom_queries.SYSTEM_MEMORY_TOTAL_BYTES)
    mem_total = int(output.data["result"][0]["value"][1])
    return mem_total


def get_system_traffic_out() -> float:
    """Query for the system outgoing traffic of the last 24h"""
    output = query_prometheus(prom_queries.SYSTEM_TRAFFIC_OUT_IN_BYTES_24H)
    traffic_out = float(output.data["result"][0]["value"][1])
    return traffic_out


def get_system_traffic_in() -> float:
    """Query for the system incoming traffic of the last 24h"""
    output = query_prometheus(prom_queries.SYSTEM_TRAFFIC_IN_IN_BYTES_24H)
    traffic_in = float(output.data["result"][0]["value"][1])
    return traffic_in
