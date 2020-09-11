
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy desklamp.
"""

from __future__ import division, absolute_import, print_function

import threading
import pytest

import check_device_types
import check_system_types

from hippy import DeskLamp
from hippy import PySproutError


device_name = 'desklamp'
notifications = []
condition = threading.Condition()


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_desklamp(request, index):
    """
    A pytest fixture to initialize and return the DeskLamp object with
    the given index.
    """
    desklamp = DeskLamp(index)
    try:
        desklamp.open()
    except RuntimeError:
        pytest.skip("Could not open desklamp connection")
    def fin():
        desklamp.unsubscribe()
        desklamp.off()
        desklamp.close()
    request.addfinalizer(fin)

    return desklamp


def test_info(get_desklamp):
    """
    Tests the desklamp's info method
    """
    desklamp = get_desklamp

    info = desklamp.info()
    check_device_types.check_DeviceInfo(info)

    vid_pid = (info['vendor_id'], info['product_id'])
    assert vid_pid == check_device_types.Devices.desklamp.value
    serial = info['serial']
    assert serial == "Not Available"


def test_open_and_close(get_desklamp):
    """
    Tests the desklamp's open, open_count, and close methods.
    """
    desklamp = get_desklamp

    connected = desklamp.is_device_connected()
    assert connected is True

    assert desklamp.open_count() == 1
    count = desklamp.close()
    assert isinstance(count, int)
    assert count == 0
    assert desklamp.open_count() == 0
    with pytest.raises(PySproutError) as execinfo:
        # Any call should fail
        desklamp.high()
    assert execinfo.value.message == 'Device is not open'
    count = desklamp.open()
    assert isinstance(count, int)
    assert count == 1
    assert desklamp.open_count() == 1
    # Any call should now work
    desklamp.high()


def test_state(get_desklamp):
    """
    Tests the desklamp's state, high, low, and off methods.
    """
    desklamp = get_desklamp

    desklamp.high()
    state = desklamp.state()
    assert isinstance(state, DeskLamp.State)
    assert state == DeskLamp.State.high
    assert state.value == 'high'

    desklamp.off()
    assert desklamp.state() == DeskLamp.State.off
    assert desklamp.state().value == 'off'

    desklamp.low()
    assert desklamp.state() == DeskLamp.State.low
    assert desklamp.state().value == 'low'


def test_factory_default(get_desklamp):
    """
    Tests the desklamp's factory_default method.
    """
    desklamp = get_desklamp

    desklamp.factory_default()
    assert desklamp.state() == DeskLamp.State.off


def test_temperatures(get_desklamp):
    """
    Tests the desklamp's temperatures method.
    """
    desklamp = get_desklamp

    temperatures = desklamp.temperatures()
    info = desklamp.info()
    check_system_types.check_TemperatureInfoList(temperatures, [info])


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


def test_notifications(get_desklamp):
    """
    This method tests the desklamp.on_*** notifications received from SoHal.
    """
    desklamp = get_desklamp

    val = desklamp.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    name = desklamp._object_name
    # Notifications are never sent as '@0' even if we sent the command with @0
    if '@0' in name:
        name = 'desklamp'

    # TODO(EB) We'll need a manual test for on_state (triggered by touch),
    # on_suspend, and on_resume

    desklamp.close()
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 0)
    notification = get_notification()
    assert notification == ('{}.on_close'.format(name), None)
    desklamp.open()
    notification = get_notification()
    assert notification == ('{}.on_open'.format(name), None)
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 1)

    desklamp.low()
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name), DeskLamp.State.low)

    desklamp.off()
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name), DeskLamp.State.off)

    desklamp.high()
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name), DeskLamp.State.high)

    desklamp.factory_default()
    notification = get_notification()
    assert notification == ('{}.on_factory_default'.format(name), None)

    val = desklamp.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Now make sure we aren't getting notification callbacks anymore...
    desklamp.factory_default()
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    # Verify hippy raises errors if we call subscribe with invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        desklamp.subscribe('string')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        desklamp.subscribe(desklamp)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        desklamp.subscribe({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        desklamp.subscribe(3)
    assert 'Invalid parameter' in execinfo.value.message
