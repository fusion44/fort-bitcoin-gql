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
import logging

import backend.stats.prom_queries as prom_queries
from backend.exceptions import ClientVisibleException

logger = logging.getLogger(__name__)

CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")


def gen_error_string(msg: str, reason: str):
    if msg != "" and reason != "":
        return "Message: {} Reason: {}".format(msg, reason)
    elif msg != "":
        return "Message: {}".format(msg)
    else:
        return "Reason: {}".format(reason)


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
        if code == 200:
            # only parse if query was successful
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
        url = "{}/api/v1/query?query={}".format(config["prom_api_url"], query)
        logger.debug(url)
        output = request.urlopen(
            url, timeout=10)  # type: http.client.HTTPResponse
    except urllib.error.HTTPError as error:
        logger.exception(error)
        resp = PrometheusResponse(error.code, None, error.msg, error.reason)
        return resp
    except urllib.error.URLError as error:
        logger.exception(error)
        resp = PrometheusResponse(500, None, "Prometheus API not reachable.",
                                  error.reason)
        return resp
    except ValueError as error:
        logger.exception(error)
        resp = PrometheusResponse(500, None, error.args[0])
        return resp
    except Exception as error:
        logger.exception(error)
        resp = PrometheusResponse(500, None, "Internal Server Error")
        return resp

    resp = PrometheusResponse(output.code, output.read(), output.msg,
                              output.reason)
    return resp


def get_system_uptime() -> float:
    """Query for the node system uptime in seconds"""
    output = query_prometheus(prom_queries.SYSTEM_UPTIME_IN_SECONDS)
    if output.code == 200:
        uptime = float(output.data["result"][0]["value"][1])
        return uptime
    else:
        raise ClientVisibleException(
            output.code, gen_error_string(output.message, output.reason))


def get_system_cpu_load() -> float:
    """Query for the current system CPU load 5m average"""
    output = query_prometheus(prom_queries.SYSTEM_CPU_USAGE_PERCENT_5M_AVG)
    if output.code == 200:
        cpu_load = float(output.data["result"][0]["value"][1])
        return cpu_load
    else:
        raise ClientVisibleException(
            output.code, gen_error_string(output.message, output.reason))


def get_system_mem_used() -> int:
    """Query for the systems current used memory"""
    output = query_prometheus(prom_queries.SYSTEM_MEMORY_USED_BYTES)
    if output.code == 200:
        mem_used = int(output.data["result"][0]["value"][1])
        return mem_used
    else:
        raise ClientVisibleException(
            output.code, gen_error_string(output.message, output.reason))


def get_system_mem_free() -> int:
    """Query for the systems current free memory"""
    output = query_prometheus(prom_queries.SYSTEM_MEMORY_FREE_BYTES)
    if output.code == 200:
        mem_free = int(output.data["result"][0]["value"][1])
        return mem_free
    else:
        raise ClientVisibleException(
            output.code, gen_error_string(output.message, output.reason))


def get_system_mem_available() -> int:
    """Query for the systems current available memory"""
    output = query_prometheus(prom_queries.SYSTEM_MEMORY_AVAILABLE_BYTES)
    if output.code == 200:
        mem_available = int(output.data["result"][0]["value"][1])
        return mem_available
    else:
        raise ClientVisibleException(
            output.code, gen_error_string(output.message, output.reason))


def get_system_mem_total() -> int:
    """Query for the systems current total memory"""
    output = query_prometheus(prom_queries.SYSTEM_MEMORY_TOTAL_BYTES)
    if output.code == 200:
        mem_total = int(output.data["result"][0]["value"][1])
        return mem_total
    else:
        raise ClientVisibleException(
            output.code, gen_error_string(output.message, output.reason))


def get_system_traffic_out() -> float:
    """Query for the system outgoing traffic of the last 24h"""
    output = query_prometheus(prom_queries.SYSTEM_TRAFFIC_OUT_IN_BYTES_24H)
    if output.code == 200:
        traffic_out = float(output.data["result"][0]["value"][1])
        return traffic_out
    else:
        raise ClientVisibleException(
            output.code, gen_error_string(output.message, output.reason))


def get_system_traffic_in() -> float:
    """Query for the system incoming traffic of the last 24h"""
    output = query_prometheus(prom_queries.SYSTEM_TRAFFIC_IN_IN_BYTES_24H)
    if output.code == 200:
        traffic_in = float(output.data["result"][0]["value"][1])
        return traffic_in
    else:
        raise ClientVisibleException(
            output.code, gen_error_string(output.message, output.reason))
