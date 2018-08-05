"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

class ClientVisibleException(Exception):
    """Last exception raised when the API can't return useful data 
    because of errors. Use this to indicate that the error message
    can safely be returned to the client.
    
    Attributes:
        code -- http status code
        message -- explanation of the error
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message
