
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy 3d capture stage.
"""

from __future__ import division, absolute_import, print_function

import math
import random
import threading
import pytest

import check_device_types
import check_system_types

from hippy import CaptureStage
from hippy import PySproutError


device_name = 'capturestage'
notifications = []
condition = threading.Condition()


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_capturestage(request, index):
    """
    A pytest fixture to initialize and return the CaptureStage object with
    the given index.
    """
    capturestage = CaptureStage(index)
    try:
        capturestage.open()
    except RuntimeError:
        pytest.skip("Could not open CaptureStage connection")
    def fin():
        capturestage.unsubscribe()
        capturestage.close()
    request.addfinalizer(fin)

    return capturestage


def test_info(get_capturestage):
    """
    Tests the capturestage's info method
    """
    capturestage = get_capturestage

    info = capturestage.info()
    check_device_types.check_DeviceInfo(info)

    vid_pid = (info['vendor_id'], info['product_id'])
    assert vid_pid == check_device_types.Devices.capturestage.value


def test_open_and_close(get_capturestage):
    """
    Tests the capturestage's open, open_count, and close methods.
    """
    capturestage = get_capturestage

    connected = capturestage.is_device_connected()
    assert connected is True

    assert capturestage.open_count() == 1
    count = capturestage.close()
    assert isinstance(count, int)
    assert count == 0
    assert capturestage.open_count() == 0
    with pytest.raises(PySproutError) as execinfo:
        # Any call should fail
        capturestage.led_on_off_rate()
    assert execinfo.value.message == 'Device is not open'
    count = capturestage.open()
    assert isinstance(count, int)
    assert count == 1
    assert capturestage.open_count() == 1
    # Any call should now work
    capturestage.led_on_off_rate()


def test_device_specific_info(get_capturestage):
    """
    Tests the capturestage's device_specific_info method.
    """
    capturestage = get_capturestage

    dev_info = capturestage.device_specific_info()
    assert isinstance(dev_info['port'], str)


def test_home_tilt(get_capturestage):
    """
    Tests the capturestage's home and tilt methods.
    """
    capturestage = get_capturestage

    capturestage.home()

    set_tilt = 56.89
    new_tilt = capturestage.tilt(set_tilt)
    assert isinstance(new_tilt, float)
    assert math.isclose(set_tilt, new_tilt, abs_tol=1)
    new_tilt = capturestage.tilt()
    assert isinstance(new_tilt, float)
    assert math.isclose(set_tilt, new_tilt, abs_tol=1)

    # Verify that home sets the tilt back to 0
    capturestage.home()
    new_tilt = capturestage.tilt()
    assert math.isclose(0, new_tilt, abs_tol=1)

    # Valid tilt is 0 <= tilt <= 180
    # Test the edge values
    new_tilt = capturestage.tilt(180)
    assert math.isclose(180, new_tilt, abs_tol=1)
    new_tilt = capturestage.tilt()
    assert math.isclose(180, new_tilt, abs_tol=1)

    new_tilt = capturestage.tilt(0)
    assert math.isclose(0, new_tilt, abs_tol=1)
    new_tilt = capturestage.tilt()
    assert math.isclose(0, new_tilt, abs_tol=1)

    # Test outside of the valid range
    with pytest.raises(PySproutError) as execinfo:
        capturestage.tilt(-0.1)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.tilt(random.randint(-180, -1))
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.tilt(180.1)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.tilt(random.randint(181, 500))
    assert 'Parameter out of range' in execinfo.value.message

    # Verify invalid parameters throw the proper errors
    with pytest.raises(PySproutError) as execinfo:
        capturestage.tilt({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.tilt('moo')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.tilt({'fake_key': 500})
    assert 'Invalid parameter' in execinfo.value.message


def test_led_on_off_rate(get_capturestage):
    """
    Tests the capturestage's led_on_off_rate method.
    """
    capturestage = get_capturestage

    # Store original value
    rate = capturestage.led_on_off_rate()
    assert isinstance(rate, dict)
    assert isinstance(rate['time_on'], int)
    assert isinstance(rate['time_off'], int)

    set_rate = {'time_on' : random.randint(10, 65535),
                'time_off' : random.randint(10, 65535)}
    new_rate = capturestage.led_on_off_rate(set_rate)
    assert new_rate == set_rate
    assert capturestage.led_on_off_rate() == set_rate

    # Test changing just one value at a time
    new_rate = capturestage.led_on_off_rate({'time_on': 42})
    set_rate['time_on'] = 42
    assert new_rate == set_rate
    assert capturestage.led_on_off_rate() == set_rate

    new_rate = capturestage.led_on_off_rate({'time_off': 16})
    set_rate['time_off'] = 16
    assert new_rate == set_rate
    assert capturestage.led_on_off_rate() == set_rate

    # Valid range is 10 <= time_on or time_off <= 65535
    # Test the edge values
    set_rate = {'time_on' : 10, 'time_off' : 65535}
    new_rate = capturestage.led_on_off_rate(set_rate)
    assert new_rate == set_rate
    assert capturestage.led_on_off_rate() == set_rate

    set_rate = {'time_on' : 65535, 'time_off' : 10}
    new_rate = capturestage.led_on_off_rate(set_rate)
    assert new_rate == set_rate
    assert capturestage.led_on_off_rate() == set_rate

    # Verify out of range values throw errors
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_on_off_rate({'time_on' : 9, 'time_off' : 500})
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_on_off_rate({'time_on' : 500, 'time_off' : 9})
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_on_off_rate({'time_on' : 65536, 'time_off' : 500})
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_on_off_rate({'time_on' : 500, 'time_off' : 65536})
    assert 'Parameter out of range' in execinfo.value.message

    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_on_off_rate({'time_on': random.randint(-10, 9)})
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_on_off_rate({'time_off': random.randint(-100, 0)})
    assert 'Parameter out of range' in execinfo.value.message

    # Verify invalid parameters throw the proper errors
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_on_off_rate(17)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_on_off_rate('moo')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_on_off_rate({'fake_key': 500})
    assert 'Invalid parameter' in execinfo.value.message

    # Reset the original value and confirm
    new_rate = capturestage.led_on_off_rate(rate)
    assert new_rate == rate
    assert capturestage.led_on_off_rate() == rate


def test_led_state(get_capturestage):
    """
    Tests the capturestage's led_state method.
    """
    capturestage = get_capturestage

    # Store original value
    state = capturestage.led_state()
    assert isinstance(state['amber'], CaptureStage.LEDState)
    assert isinstance(state['red'], CaptureStage.LEDState)
    assert isinstance(state['white'], CaptureStage.LEDState)
    assert isinstance(state['amber'].value, str)
    assert isinstance(state['red'].value, str)
    assert isinstance(state['white'].value, str)

    cur_state = {'amber': CaptureStage.LEDState.blink_in_phase,
                 'red': CaptureStage.LEDState.on,
                 'white': CaptureStage.LEDState.blink_off_phase}
    set_state = capturestage.led_state(cur_state)
    assert set_state == cur_state
    assert capturestage.led_state() == cur_state

    # Test setting each LED individually
    for led in ['amber', 'red', 'white']:
        for state in CaptureStage.LEDState:
            set_state = capturestage.led_state({led: state})
            cur_state[led] = state
            assert cur_state == set_state
            assert capturestage.led_state() == cur_state

    # Test setting by the name rather than the enum
    for led in ['amber', 'red', 'white']:
        for state in ['off', 'on', 'blink_in_phase', 'blink_off_phase']:
            set_state = capturestage.led_state({led: state})
            cur_state[led] = CaptureStage.LEDState(state)
            assert cur_state == set_state
            assert capturestage.led_state() == cur_state

    # Verify invalid parameters throw the proper errors
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_state('moo')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_state({'fake_key': CaptureStage.LEDState.on})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        state = capturestage.led_state({})
    assert 'Invalid parameter' in execinfo.value.message

    with pytest.raises(TypeError):
        capturestage.led_state(33)
    with pytest.raises(ValueError):
        capturestage.led_state({'amber': 'fake_value'})

    # Send bad values to SoHal (bypassing the hippy enum check) and make
    # sure SoHal throws an error...
    with pytest.raises(PySproutError) as execinfo:
        capturestage._send_msg('led_state', 33) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage._send_msg('led_state', 33) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message


def test_rotate(get_capturestage):
    """
    Tests the capturestage's rotate and rotation_angle methods.
    """
    capturestage = get_capturestage

    angle = capturestage.rotation_angle()
    assert isinstance(angle, float)

    rotated = capturestage.rotate(50.3)
    assert isinstance(rotated, float)
    assert math.isclose(50.3, rotated, abs_tol=1)
    new_angle = capturestage.rotation_angle()
    assert math.isclose(new_angle, angle + 50.3, abs_tol=1)
    angle = new_angle

    rotated = capturestage.rotate(-100)
    assert math.isclose(-100, rotated, abs_tol=1)
    new_angle = capturestage.rotation_angle()
    assert math.isclose(new_angle, angle - 100, abs_tol=1)
    angle = new_angle

    # test edge cases
    rotated = capturestage.rotate(-360)
    assert math.isclose(-360, rotated, abs_tol=1)
    new_angle = capturestage.rotation_angle()
    assert math.isclose(new_angle, angle - 360, abs_tol=1)
    angle = new_angle

    rotated = capturestage.rotate(360)
    assert math.isclose(360, rotated, abs_tol=1)
    new_angle = capturestage.rotation_angle()
    assert math.isclose(new_angle, angle + 360, abs_tol=1)
    angle = new_angle

    # test out of range values
    with pytest.raises(PySproutError) as execinfo:
        rotated = capturestage.rotate(-360.1)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        rotated = capturestage.rotate(360.1)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        rotated = capturestage.rotate(random.randint(-1000, -361))
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        rotated = capturestage.rotate(random.randint(361, 1000))
    assert 'Parameter out of range' in execinfo.value.message

    # test inavlid parameters
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_state('moo')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.led_state({'angle': 300})
    assert 'Invalid parameter' in execinfo.value.message


def test_factory_default(get_capturestage):
    """
    Tests the capturestage's factory_default method.
    """
    capturestage = get_capturestage

    capturestage.factory_default()

    rate = capturestage.led_on_off_rate()
    assert rate['time_on'] == 500
    assert rate['time_off'] == 500

    tilt = capturestage.tilt()
    assert math.isclose(0, tilt, abs_tol=1)

    led_state = capturestage.led_state()
    assert led_state['amber'] == CaptureStage.LEDState.off
    assert led_state['red'] == CaptureStage.LEDState.off
    assert led_state['white'] == CaptureStage.LEDState.off


def test_temperatures(get_capturestage):
    """
    Tests the capturestage's temperatures method.
    """
    capturestage = get_capturestage

    temperatures = capturestage.temperatures()
    info = capturestage.info()
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


def test_notifications(get_capturestage):
    """
    This method tests the capturestage.on_*** notifications received from SoHal.
    """
    capturestage = get_capturestage

    val = capturestage.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    name = capturestage._object_name
    # Notifications are never sent as '@0' even if we sent the command with @0
    if '@0' in name:
        name = 'capturestage'

    # TODO(EB) We'll need a manual test for on_device_connected,
    # on_device_disconnected, on_suspend, and on_resume

    capturestage.close()
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 0)
    notification = get_notification()
    assert notification == ('{}.on_close'.format(name), None)
    capturestage.open()
    notification = get_notification()
    assert notification == ('{}.on_open'.format(name), None)
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 1)

    capturestage.home()
    notification = get_notification()
    assert notification == ('{}.on_home'.format(name), None)

    rate = {'time_off': 500, 'time_on': 500}
    capturestage.led_on_off_rate(rate)
    notification = get_notification()
    assert notification == ('{}.on_led_on_off_rate'.format(name), rate)

    state = {"amber": CaptureStage.LEDState.on,
             "red": CaptureStage.LEDState.off,
             "white": CaptureStage.LEDState.blink_off_phase}
    capturestage.led_state(state)
    notification = get_notification()
    assert notification == ('{}.on_led_state'.format(name), state)

    angle = 20
    capturestage.rotate(angle)
    notification = get_notification()
    assert notification[0] == '{}.on_rotate'.format(name)
    assert math.isclose(notification[1], angle, abs_tol=1)

    angle = 15
    capturestage.tilt(angle)
    notification = get_notification()
    assert notification[0] == '{}.on_tilt'.format(name)
    assert math.isclose(notification[1], angle, abs_tol=1)

    capturestage.factory_default()
    notification = get_notification()
    assert notification == ('{}.on_factory_default'.format(name), None)

    val = capturestage.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Now make sure we aren't getting notification callbacks anymore...
    capturestage.home()
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    # Verify hippy raises errors if we call subscribe with invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        capturestage.subscribe('string')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.subscribe(capturestage)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.subscribe({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        capturestage.subscribe(3)
    assert 'Invalid parameter' in execinfo.value.message
