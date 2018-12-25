"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
# pylint: skip-file
import pytest

import backend
from backend.lnd.models import IPAddress
from backend.lnd.tasks import request, update_wan_ip

pytestmark = pytest.mark.django_db


class FakeResponse():
    status = 200

    def read(type):
        return "38.34.19.119".encode("utf-8")


def test_update_wan_ip(monkeypatch):
    monkeypatch.setattr(backend.lnd.tasks.request, "urlopen",
                        lambda url: FakeResponse())

    addr = IPAddress()
    addr.ip_address = "1.2.3.4"
    addr.save()
    assert addr.pk == 1

    update_wan_ip()

    addr = IPAddress.objects.get(pk=1)
    assert addr.ip_address == "38.34.19.119"
