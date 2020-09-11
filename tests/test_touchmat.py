
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy touchmat.
"""

from __future__ import division, absolute_import, print_function

import random
import threading
import time
import pytest

import check_device_types
import check_system_types
from check_device_types import Devices

from hippy import TouchMat
from hippy import PySproutError


device_name = 'touchmat'
notifications = []
condition = threading.Condition()


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_touchmat(request, index):
    """
    A pytest fixture to initialize and return the TouchMat object with
    the given index.
    """
    touchmat = TouchMat(index)
    try:
        touchmat.open()
    except RuntimeError:
        pytest.skip("Could not open touchmat connection")
    def fin():
        touchmat.unsubscribe()
        touchmat.close()
    request.addfinalizer(fin)

    return touchmat


def test_info(get_touchmat):
    """
    Tests the touchmat's info method
    """
    touchmat = get_touchmat

    info = touchmat.info()
    check_device_types.check_DeviceInfo(info)

    vid_pid = (info['vendor_id'], info['product_id'])
    assert vid_pid in (Devices.touchmat_g1.value,
                       Devices.touchmat_g2.value)

    serial = info['serial']
    if Devices(vid_pid) == Devices.touchmat_g2:
        assert serial == "Not Available"
    else:
        assert len(serial) == 24


def test_hardware_info(get_touchmat):
    """
    Tests the touchmat's hardware_info method.
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    hw_info = touchmat.hardware_info()
    if touchmat_model == Devices.touchmat_g1:
        assert hw_info['size'] == {'width' : 16.0, 'height' : 12.0}
    else:
        assert hw_info['size'] == {'width' : 17.7, 'height' : 11.8}


def test_open_and_close(get_touchmat):
    """
    Tests the touchmat's open, open_count, and close methods.
    """
    touchmat = get_touchmat

    connected = touchmat.is_device_connected()
    assert connected is True

    assert touchmat.open_count() == 1
    count = touchmat.close()
    assert isinstance(count, int)
    assert count == 0
    assert touchmat.open_count() == 0
    with pytest.raises(PySproutError) as execinfo:
        # Any call should fail
        touchmat.state({'touch' : False})
    assert 'Device is not open' in str(execinfo.value)
    count = touchmat.open()
    assert isinstance(count, int)
    assert count == 1
    assert touchmat.open_count() == 1
    # Any call should work
    touchmat.state({'touch' : False})


def test_state(get_touchmat):
    """
    Tests the touchmat's state method
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    if touchmat_model == Devices.touchmat_g2:
        state = touchmat.state()
        assert isinstance(state['touch'], bool)
        assert isinstance(state['active_pen'], bool)

    state = {'touch': True, 'active_pen': False}
    set_state = touchmat.state(state)
    assert set_state == state
    if touchmat_model == Devices.touchmat_g2:
        assert touchmat.state() == state

    set_state = touchmat.state({'touch' : False})
    state['touch'] = False
    assert set_state == state
    # TODO(EB) we need to verify the state for the 1.0 touchmat once it's
    # implemented in SoHal... for now check it for 1.6 only
    if touchmat_model == Devices.touchmat_g2:
        assert touchmat.state() == state

        set_state = touchmat.state({'active_pen' : True})
        state['active_pen'] = True
        assert set_state == state
        assert touchmat.state() == state

        state = {'touch' : True, 'active_pen' : True}
        set_state = touchmat.state(state)
        assert set_state == state
        assert touchmat.state() == state

        state = {'touch' : False, 'active_pen' : True}
        set_state = touchmat.state(state)
        assert set_state == state
        assert touchmat.state() == state

        set_state = touchmat.state({'active_pen' : False})
        state['active_pen'] = False
        assert set_state == state
        assert touchmat.state() == state

    else:
        with pytest.raises(PySproutError) as execinfo:
            touchmat.state({'active_pen' : True})
        assert 'functionality not available' in str(execinfo.value)

        set_state = touchmat.state({'active_pen' : False})
        assert set_state['active_pen'] is False

        state = {'touch' : True, 'active_pen' : False}
        set_state = touchmat.state(state)
        assert set_state == state

        state = {'touch' : False, 'active_pen' : False}
        set_state = touchmat.state(state)
        assert set_state == state

        with pytest.raises(PySproutError) as execinfo:
            touchmat.state({'touch' : False, 'active_pen' : True})
        assert 'functionality not available' in str(execinfo.value)

    # Test sending in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        touchmat.state('bad')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.state(7)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.state({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.state({'fake': True})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.state({'touch': 1})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.state({'touch': 'invalid'})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.state({'active_pen': {}})
    assert 'Invalid parameter' in execinfo.value.message


def test_active_area(get_touchmat):
    """
    Tests the touchmat's active_area method
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    if touchmat_model == Devices.touchmat_g1:
        with pytest.raises(PySproutError) as execinfo:
            touchmat.active_area()
        assert 'Functionality not available' in str(execinfo.value)

        with pytest.raises(PySproutError) as execinfo:
            touchmat.active_area({'enabled': True})
        assert 'Functionality not available' in str(execinfo.value)
        return

    x_min = 0
    y_min = 0
    x_max = 15360
    y_max = 8640

    cur_area = touchmat.active_area()
    assert isinstance(cur_area['enabled'], bool)
    assert isinstance(cur_area['top_left'], dict)
    assert isinstance(cur_area['bottom_right'], dict)
    assert isinstance(cur_area['top_left']['x'], int)
    assert x_min <= cur_area['top_left']['x'] <= x_max
    assert isinstance(cur_area['top_left']['y'], int)
    assert y_min <= cur_area['top_left']['y'] <= y_max
    assert isinstance(cur_area['bottom_right']['x'], int)
    assert x_min <= cur_area['bottom_right']['x'] <= x_max
    assert isinstance(cur_area['bottom_right']['y'], int)
    assert y_min <= cur_area['bottom_right']['y'] <= y_max
    assert cur_area['top_left']['x'] <= cur_area['bottom_right']['x']
    assert cur_area['top_left']['y'] <= cur_area['bottom_right']['y']

    tl_x = random.randint(x_min, x_max-1)
    tl_y = random.randint(y_min, y_max-1)
    br_x = random.randint(tl_x+1, x_max)
    br_y = random.randint(tl_y+1, y_max)
    area = {'enabled': True, 'top_left': {'x': tl_x, 'y': tl_y},
            'bottom_right': {'x': br_x, 'y': br_y}}
    set_area = touchmat.active_area(area)
    assert set_area == area
    assert touchmat.active_area() == area

    # Test only changing one key at a time
    set_area = touchmat.active_area({'enabled':False})
    area['enabled'] = False
    assert set_area == area
    assert touchmat.active_area() == area

    tl_x = random.randint(x_min, br_x)
    tl_y = random.randint(y_min, br_y)
    set_area = touchmat.active_area({'top_left': {'x': tl_x, 'y': tl_y}})
    area['top_left'] = {'x': tl_x, 'y': tl_y}
    assert set_area == area
    assert touchmat.active_area() == area

    br_x = random.randint(tl_x+1, x_max)
    br_y = random.randint(tl_y+1, y_max)
    set_area = touchmat.active_area({'bottom_right': {'x': br_x, 'y': br_y}})
    area['bottom_right'] = {'x': br_x, 'y': br_y}
    assert set_area == area
    assert touchmat.active_area() == area

    # Test the edge cases
    area = {'enabled': True, 'top_left': {'x': x_min, 'y': y_min},
            'bottom_right': {'x': x_max, 'y': y_max}}
    set_area = touchmat.active_area(area)
    assert set_area == area
    assert touchmat.active_area() == area

    # Verify that out of range values throw the appropriate errors
    err_msg = 'Valid range is {} <= top_left x <= {}'.format(x_min, x_max)
    # Test top_left x < min value
    bad_x = random.randint(x_min-1000, x_min-1)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'top_left': {'x': bad_x, 'y': tl_y}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area
    # Test top_left x > max value
    bad_x = random.randint(x_max+1, x_max+1000)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'top_left': {'x': bad_x, 'y': tl_y}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area

    err_msg = 'Valid range is {} <= bottom_right x <= {}'.format(x_min, x_max)
    # Test bottom_right x < min value
    bad_x = random.randint(x_min-1000, x_min-1)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'bottom_right': {'x': bad_x, 'y': br_y}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area
    # Test bottom_right x > max value
    bad_x = random.randint(x_max+1, x_max+1000)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'bottom_right': {'x': bad_x, 'y': br_y}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area

    err_msg = 'Valid range is {} <= top_left y <= {}'.format(y_min, y_max)
    # Test top_left y < min value
    bad_y = random.randint(y_min-1000, y_min-1)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'top_left': {'x': tl_x, 'y': bad_y}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area
    # Test top_left y > max value
    bad_y = random.randint(y_max+1, y_max+1000)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'top_left': {'x': tl_x, 'y': bad_y}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area

    err_msg = 'Valid range is {} <= bottom_right y <= {}'.format(y_min, y_max)
    # Test bottom_right y < min value
    bad_y = random.randint(y_min-1000, y_min-1)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'bottom_right': {'x': br_x, 'y': bad_y}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area
    # Test bottom_right y > max value
    bad_y = random.randint(y_max+1, y_max+1000)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'bottom_right': {'x': br_x, 'y': bad_y}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area

    # Test bottom_right y < top_left y
    br_y = random.randint(y_min, y_max-1)
    tl_y = random.randint(br_y+1, y_max)
    err_msg = 'top_left y ({}) must be less than bottom_right y ({})'.format(tl_y, br_y)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'top_left': {'x': x_min, 'y': tl_y},
                              'bottom_right': {'x': x_max, 'y': br_y}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area
    # Test bottom_right x < top_left x
    br_x = random.randint(x_min, x_max-1)
    tl_x = random.randint(br_x+1, x_max)
    err_msg = 'top_left x ({}) must be less than bottom_right x ({})'.format(tl_x, br_x)
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'top_left': {'x': tl_x, 'y': y_min},
                              'bottom_right': {'x': br_x, 'y': y_max}})
    assert err_msg in execinfo.value.message
    assert touchmat.active_area() == area

    # Test passing in the wrong types, empty dictionaries, etc...
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'top_left': 7})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'bottom_right': 'moo'})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'enabled': 'moo'})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({'enabled': 3})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area("test")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.active_area({})
    assert 'Invalid parameter' in execinfo.value.message

def test_active_pen_range(get_touchmat):
    """
    Tests the touchmat's active_pen_range method
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    if touchmat_model == Devices.touchmat_g1:
        with pytest.raises(PySproutError) as execinfo:
            touchmat.active_pen_range()
        assert 'Functionality not available' in str(execinfo.value)

        with pytest.raises(PySproutError) as execinfo:
            touchmat.active_pen_range("ten_mm")
        assert 'Functionality not available' in str(execinfo.value)
        return

    cur_range = touchmat.active_pen_range()
    assert isinstance(cur_range, touchmat.ActivePenRange)
    assert isinstance(cur_range.value, str)

    for item in TouchMat.ActivePenRange:
        pen_range = touchmat.active_pen_range(item)
        assert pen_range == item
        assert touchmat.active_pen_range() == item
        pen_range = touchmat.active_pen_range(item.value)
        assert pen_range == item
        assert touchmat.active_pen_range() == item

    ranges = ["five_mm", "ten_mm", "fifteen_mm", "twenty_mm"]
    for item in ranges:
        pen_range = touchmat.active_pen_range(item)
        assert pen_range.value == item
        assert touchmat.active_pen_range().value == item

    # Verify incorrect values return errors
    with pytest.raises(ValueError) as execinfo:
        touchmat.active_pen_range("thirty_mm")
    assert 'is not a valid ActivePenRange' in str(execinfo.value)
    with pytest.raises(ValueError) as execinfo:
        touchmat.active_pen_range(3)
    assert 'is not a valid ActivePenRange' in str(execinfo.value)

    # Send a bad value to SoHal (bypassing the hippy enum check) and makes
    # sure SoHal throws an error...
    with pytest.raises(PySproutError) as execinfo:
        touchmat._send_msg('active_pen_range', 1) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat._send_msg('active_pen_range', 'moo') # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat._send_msg('active_pen_range', {}) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message


def test_calibrate(get_touchmat):
    """
    Tests the touchmat's calibrate method
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    if touchmat_model == Devices.touchmat_g1:
        with pytest.raises(PySproutError) as execinfo:
            touchmat.calibrate()
        assert 'Functionality not available' in str(execinfo.value)
        return

    touchmat.calibrate()


def test_device_palm_rejection(get_touchmat):
    """
    Tests the touchmat's device_palm_rejection method
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    if touchmat_model == Devices.touchmat_g1:
        with pytest.raises(PySproutError) as execinfo:
            touchmat.device_palm_rejection()
        assert 'Functionality not available' in str(execinfo.value)

        with pytest.raises(PySproutError) as execinfo:
            touchmat.device_palm_rejection(True)
        assert 'Functionality not available' in str(execinfo.value)
        return

    cur_val = touchmat.device_palm_rejection()
    assert isinstance(cur_val, bool)

    new_val = touchmat.device_palm_rejection(True)
    assert new_val is True
    assert touchmat.device_palm_rejection() is True

    new_val = touchmat.device_palm_rejection(False)
    assert new_val is False
    assert touchmat.device_palm_rejection() is False

    # Verify invalid parameters throw errors
    with pytest.raises(PySproutError) as execinfo:
        touchmat.device_palm_rejection("moo")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.device_palm_rejection(7)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.device_palm_rejection({})
    assert 'Invalid parameter' in execinfo.value.message


def test_palm_rejection_timeout(get_touchmat):
    """
    Tests the touchmat's palm_rejection_timeout method.
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    if touchmat_model == Devices.touchmat_g1:
        with pytest.raises(PySproutError) as execinfo:
            touchmat.palm_rejection_timeout()
        assert 'Functionality not available' in str(execinfo.value)

        with pytest.raises(PySproutError) as execinfo:
            touchmat.palm_rejection_timeout(150)
        assert 'Functionality not available' in str(execinfo.value)
        return

    original_timeout = touchmat.palm_rejection_timeout()

    new_timeout = random.randint(150, 2000)
    timeout = touchmat.palm_rejection_timeout(new_timeout)
    assert timeout == new_timeout
    assert touchmat.palm_rejection_timeout() == new_timeout

    # Test the edge cases
    timeout = touchmat.palm_rejection_timeout(2000)
    assert timeout == 2000
    assert touchmat.palm_rejection_timeout() == 2000
    timeout = touchmat.palm_rejection_timeout(150)
    assert timeout == 150
    assert touchmat.palm_rejection_timeout() == 150

    # Test out of range values
    with pytest.raises(PySproutError) as execinfo:
        touchmat.palm_rejection_timeout(149)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.palm_rejection_timeout(2001)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.palm_rejection_timeout(3000)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.palm_rejection_timeout(15)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.palm_rejection_timeout(-150)
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        touchmat.palm_rejection_timeout("abc")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.palm_rejection_timeout({})
    assert 'Invalid parameter' in execinfo.value.message

    # Set the original value back
    timeout = touchmat.palm_rejection_timeout(original_timeout)
    assert timeout == original_timeout
    assert touchmat.palm_rejection_timeout() == original_timeout


def test_reset(get_touchmat):
    """
    Tests the touchmat's reset method.
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    touchmat.state({'active_pen':False, 'touch': True})
    touchmat.reset()
    time.sleep(0.5)
    # The touchmat should disconnect and then reconnect. Loop for up to 5
    # seconds checking if it's connected
    count = 0
    while not touchmat.is_device_connected():
        assert count < 10
        time.sleep(0.5)
        count += 1

    assert touchmat.open_count() == 0
    touchmat.open()

    if touchmat_model == Devices.touchmat_g2:
        assert touchmat.state() == {'active_pen': True, 'touch': True}


def test_factory_default(get_touchmat):
    """
    Tests the touchmat's factory_default method.
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    if touchmat_model == Devices.touchmat_g2:
        # Set the values so we can verify that factory default resets them
        touchmat.state({'active_pen': True, 'touch': True})
        touchmat.active_area({'enabled': True, 'top_left': {'x': 100, 'y': 200},
                              'bottom_right': {'x': 1510, 'y': 800}})
        touchmat.active_pen_range(TouchMat.ActivePenRange.twenty_mm)

    touchmat.factory_default()

    if touchmat_model == Devices.touchmat_g2:
        assert touchmat.state() == {'active_pen': False, 'touch': False}
        assert touchmat.active_area() == {'enabled': False,
                                          'top_left': {'x': 0, 'y': 0},
                                          'bottom_right': {'x': 15360,
                                                           'y': 8640}}
        assert touchmat.active_pen_range() == TouchMat.ActivePenRange.ten_mm
        assert touchmat.device_palm_rejection() is False


def test_temperatures(get_touchmat):
    """
    Tests the touchmat's temperatures method.
    """
    touchmat = get_touchmat

    temperatures = touchmat.temperatures()
    info = touchmat.info()
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


def test_notifications(get_touchmat):
    """
    This method tests the touchmat.on_*** notifications received from SoHal.
    """
    touchmat = get_touchmat
    touchmat_model = check_device_types.get_device_model(touchmat)

    val = touchmat.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    name = touchmat._object_name
    # Notifications are never sent as '@0' even if we sent the command with @0
    if '@0' in name:
        name = 'touchmat'

    # TODO(EB) We'll need a manual test for on_suspend, on_resume,
    # on_device_connected, and on_device_disconnected

    touchmat.close()
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 0)
    notification = get_notification()
    assert notification == ('{}.on_close'.format(name), None)
    touchmat.open()
    notification = get_notification()
    assert notification == ('{}.on_open'.format(name), None)
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 1)

    if touchmat_model == Devices.touchmat_g2:
        area = {"enabled": True, "bottom_right": {"x": 12680, "y": 7650},
                "top_left": {"x": 4000, "y": 3000}}
        touchmat.active_area(area)
        notification = get_notification()
        assert notification == ('{}.on_active_area'.format(name), area)

        pen_range = TouchMat.ActivePenRange.five_mm
        touchmat.active_pen_range(pen_range)
        notification = get_notification()
        assert notification == ('{}.on_active_pen_range'.format(name),
                                pen_range)

        touchmat.device_palm_rejection(True)
        notification = get_notification()
        assert notification == ('{}.on_device_palm_rejection'.format(name),
                                True)

        touchmat.palm_rejection_timeout(242)
        notification = get_notification()
        assert notification == ('{}.on_palm_rejection_timeout'.format(name),
                                242)

        touchmat.calibrate()
        notification = get_notification()
        assert notification == ('{}.on_calibrate'.format(name), None)

    state = {"active_pen": False, "touch": True}
    touchmat.state(state)
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name), state)

    touchmat.factory_default()
    notification = get_notification()
    assert notification == ('{}.on_factory_default'.format(name), None)

    touchmat.reset()
    expected = [('{}.on_reset'.format(name), None),
                ('{}.on_device_disconnected'.format(name), None),
                ('{}.on_device_connected'.format(name), None)]
    for dummy in range(len(expected)):
        notification = get_notification()
        assert notification in expected
        expected.remove(notification)

    val = touchmat.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Now make sure we aren't getting notification callbacks anymore...
    touchmat.open()
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    touchmat.factory_default()
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    # Verify hippy raises errors if we call subscribe with invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        touchmat.subscribe('string')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.subscribe(touchmat)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.subscribe({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        touchmat.subscribe(3)
    assert 'Invalid parameter' in execinfo.value.message
