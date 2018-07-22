"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from .settings import *  # NOQA

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher', )

DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
