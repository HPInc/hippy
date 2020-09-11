
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy sohal object.
"""

from __future__ import division, absolute_import, print_function

import threading
import time
import pytest

from hippy import SoHal
from hippy import PySproutError


notifications = []
condition = threading.Condition()

# pylint: disable=redefined-outer-name
@pytest.fixture
def get_sohal(request):
    """
    A pytest fixture to initialize and return the SoHal object with
    the given index.
    """
    sohal = SoHal()
    return sohal


def test_version(get_sohal):
    """
    Tests the sohal device's version method.
    """
    sohal = get_sohal

    version = sohal.version()
    assert isinstance(version, str)
    assert len(version) == 19


def test_log(get_sohal):
    """
    Tests the sohal device's log method.
    """
    sohal = get_sohal

    log = sohal.log()
    assert isinstance(log['level'], int)

    set_log = {'level': 3}
    get_log = sohal.log(set_log)
    assert set_log == get_log
    assert sohal.log() == set_log

    for level in range(5):
        get_log = sohal.log({'level': level})
        set_log['level'] = level
        assert set_log == get_log
        get_log = sohal.log()
        assert set_log == get_log

    # Test values that are out of range
    with pytest.raises(PySproutError) as execinfo:
        sohal.log({'level': -1})
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        sohal.log({'level': 5})
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid values
    with pytest.raises(PySproutError) as execinfo:
        sohal.log(10)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        sohal.log({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        sohal.log("invalid")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        sohal.log({'level': "a"})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        sohal.log({'file': 3})
    assert 'Invalid parameter' in execinfo.value.message

    # Set the original log level back
    set_log = sohal.log(log)
    assert set_log == log
    assert sohal.log() == log


# Note that this test closes SoHal, which causes all remaining tests to fail,
# so by default mark it as a test to skip.
@pytest.mark.skipif()
def test_exit(get_sohal):
    """
    Tests the sohal device's exit method.
    """
    sohal = get_sohal
    sohal.exit()

    time.sleep(1)
    # Verify that sending another command fails
    with pytest.raises(ConnectionResetError):
        sohal.version()


def callback(method, params):
    """
    This callback method is registered to receive notifications from SoHal
    as part of the notifications test. For each notification, hippy calls this
    method from a new thread.  To ensure thread safety, this method acquires
    the condition lock and then appends the notification to the end of the
    notifications list.
    """
    condition.acquire()
    notifications.append((method, params))
    condition.notify()
    condition.release()


def get_notification():
    """
    This is a helper method used by test_notifications. This method returns
    a notification off of the notifications list (and removes that notice
    from the list).  If the list is empty, it waits for up to 2 seconds to
    receive a notification.
    """
    condition.acquire()
    if not notifications:
        ret = condition.wait(2)
        if not ret:
            condition.release()
            raise TimeoutError("Timed out while waiting for notification")

    notice = notifications.pop(0)
    condition.release()
    return notice


def test_notifications(get_sohal):
    """
    This method tests the sohal.on_*** notifications received from SoHal.
    """
    sohal = get_sohal

    val = sohal.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    log_param = {'level': 3}
    sohal.log(log_param)
    notification = get_notification()
    assert notification == ('sohal.on_log', log_param)

    # TODO(EB) We'll need to test on_exit(). Maybe in the manual test, or add
    # it in the sohal_exit test?

    val = sohal.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Now make sure we aren't getting notification callbacks anymore...
    sohal.log({'level':4})
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    # Verify hippy raises errors if we call subscribe with invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        sohal.subscribe('string')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        sohal.subscribe(sohal)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        sohal.subscribe({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        sohal.subscribe(3)
    assert 'Invalid parameter' in execinfo.value.message
