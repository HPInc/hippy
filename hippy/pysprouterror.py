
# Copyright 2016 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module for the hippy error types.
"""

class PySproutError(Exception):
    """ A PySproutError is raised if there is an error communicating with
    SoHal, or if SoHal responds to a request with an error message.
    """
    def __init__(self, code, data, message):
        super(PySproutError, self).__init__()
        self.code = code
        self.data = data
        self.message = message

    def __str__(self):
        return self.message  + " (" + self.data + ")"
