"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import logging
import urllib.request
from urllib.error import HTTPError

from backend.celery import app
from backend.lnd.models import IPAddress

logger = logging.getLogger(__name__)


@app.task
def update_wan_ip():
    """Updates the ip under which we are reachable from the outside world.
    TODO: Check if ip is changed and notify all running LND instances
    """
    try:
        resp = urllib.request.urlopen(
            "https://api.ipify.org")  # type: HTTPResponse
    except HTTPError as error:
        logger.exception(error)

    if resp.status != 200:
        logger.exception("Status code not OK: {}".format(resp.status))

    addr = IPAddress.objects.get(pk=1)  # type: IPAddress
    addr.ip_address = resp.read().decode("utf-8")
    addr.save()
    logger.info("Updated ip: {}".format(addr.ip_address))
