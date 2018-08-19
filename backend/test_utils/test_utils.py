"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import pytest

from graphql.execution.base import ResolveInfo

pytestmark = pytest.mark.django_db


def mock_resolve_info(req) -> ResolveInfo:
    return ResolveInfo(None, None, None, None, None, None, None, None, None,
                       req)