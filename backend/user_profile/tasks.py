"""
Contains all recurring tasks relevant to the user.
This includes:
* Calculating user's net worth
* Calculating data necessary for the charts shown in UI
* Scheduling scans for new trades in his exchange and wallet accounts
* ...

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from backend.celery import app


@app.task
def test(arg):
    """Test task"""
    print(arg)
