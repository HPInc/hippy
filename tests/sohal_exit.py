
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy sohal.exit command.
"""

from __future__ import division, absolute_import, print_function

import time
import pytest

from hippy import SoHal
from hippy import PySproutError


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_sohal(request):
    sohal = SoHal()
    return sohal


def test_exit(get_sohal):
    sohal = get_sohal
    sohal.exit()

    time.sleep(1)
    # Verify that sending another command fails
    with pytest.raises(PySproutError):
        sohal.version()
