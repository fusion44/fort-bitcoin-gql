"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from django.db import models
from django.contrib.auth.models import User


class LNDWallet(models.Model):
    id = models.AutoField(primary_key=True)
    public_alias = models.CharField(max_length=128)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    testnet = models.BooleanField(default=False)
    initialized = models.BooleanField(default=False)
