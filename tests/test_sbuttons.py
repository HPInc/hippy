
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy sbuttons.
"""

from __future__ import division, absolute_import, print_function

import random
import threading
import pytest

from hippy import SButtons
from hippy import PySproutError

import check_device_types
import check_system_types


device_name = 'sbuttons'
notifications = []
condition = threading.Condition()


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_buttons(request, index):
    """
    A pytest fixture to initialize and return the SButtons object with
    the given index.
    """
    buttons = SButtons(index)
    try:
        buttons.open()
    except RuntimeError:
        pytest.skip("Could not open SButtons connection")
    def fin():
        buttons.unsubscribe()
        buttons.close()
    request.addfinalizer(fin)

    return buttons


def test_info(get_buttons):
    """
    Tests the sbuttons' info method
    """
    buttons = get_buttons

    info = buttons.info()
    check_device_types.check_DeviceInfo(info)

    vid_pid = (info['vendor_id'], info['product_id'])
    assert vid_pid == check_device_types.Devices.sbuttons.value
    serial = info['serial']
    assert serial == "Not Available"


def test_open_and_close(get_buttons):
    """
    Tests the sbuttons' open, open_count, and close methods.
    """
    buttons = get_buttons

    connected = buttons.is_device_connected()
    assert connected is True

    assert buttons.open_count() == 1
    count = buttons.close()
    assert isinstance(count, int)
    assert count == 0
    assert buttons.open_count() == 0
    with pytest.raises(PySproutError) as execinfo:
        # Any call should fail
        buttons.led_on_off_rate()
    assert execinfo.value.message == 'Device is not open'
    count = buttons.open()
    assert isinstance(count, int)
    assert count == 1
    assert buttons.open_count() == 1
    # Any call should now work
    buttons.led_on_off_rate()


def test_led_state(get_buttons):
    """
    Tests the sbuttons' led_state method.
    """
    buttons = get_buttons

    orig_states = {}
    # Store original values
    for led in SButtons.ButtonID:
        orig_states[led] = buttons.led_state(led)
        assert isinstance(orig_states[led]['color'], SButtons.LEDColor)
        assert isinstance(orig_states[led]['mode'], SButtons.LEDMode)
        assert isinstance(orig_states[led]['color'].value, str)
        assert isinstance(orig_states[led]['color'].value, str)

    # Test setting each LED to each mode and each color
    for led in SButtons.ButtonID:
        for mode in SButtons.LEDMode:
            for color in SButtons.LEDColor:
                state = {'color': color, 'mode': mode}
                set_state = buttons.led_state(led, state)
                assert set_state == state
                assert buttons.led_state(led) == state

    # Test setting by the string values rather than the enum
    for led in ['left', 'center', 'right']:
        for mode in ['breath', 'controlled_off', 'controlled_on', 'off',
                     'on', 'pulse']:
            for color in ['white_orange', 'orange', 'white']:
                state = {'color': color, 'mode': mode}
                set_state = buttons.led_state(led, state)
                assert set_state['color'].value == color
                assert set_state['mode'].value == mode
                get_state = buttons.led_state(led)
                assert get_state['color'].value == color
                assert get_state['mode'].value == mode

    # Test only passing in the mode or the color
    for led in SButtons.ButtonID:
        state = buttons.led_state(led)
        for mode in SButtons.LEDMode:
            set_state = buttons.led_state(led, {'mode': mode})
            state['mode'] = mode
            assert set_state == state
            assert buttons.led_state(led) == state
        for color in SButtons.LEDColor:
            set_state = buttons.led_state(led, {'color': color})
            state['color'] = color
            assert set_state == state
            assert buttons.led_state(led) == state

    # Verify invalid parameters throw the proper errors
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_state('left', 'bad')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_state('left', {'fake': SButtons.LEDColor.orange})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_state('left', {})
    assert 'Invalid parameter' in execinfo.value.message

    with pytest.raises(ValueError):
        buttons.led_state(33)
    with pytest.raises(ValueError):
        buttons.led_state('moo')
    with pytest.raises(ValueError):
        buttons.led_state('right', {'mode': 'fake_value'})
    with pytest.raises(ValueError):
        buttons.led_state('right', {'color': 'on'})

    # Send a bad value to SoHal (bypassing the hippy enum check) and makes
    # sure SoHal throws an error...
    with pytest.raises(PySproutError) as execinfo:
        buttons._send_msg('led_state', 33)  # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons._send_msg('led_state', 'moo')  # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons._send_msg('led_state', ['left', {'fake': 'orange'}])  # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons._send_msg('led_state', ['left', {'mode': 'orange'}])  # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons._send_msg('led_state', ['left', {'mode': 2}])  # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons._send_msg('led_state', ['left', {'color': 12}])  # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons._send_msg('led_state', ['left', {'color': 'green'}])  # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons._send_msg('led_state', ['left', 10])  # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message

    # Reset original values
    for led in SButtons.ButtonID:
        buttons.led_state(led, {'color': orig_states[led]['color'],
                                'mode': orig_states[led]['mode']})

    # Check that values were reset
    for led in SButtons.ButtonID:
        state = buttons.led_state(led)
        assert state['color'] == orig_states[led]['color']
        assert state['mode'] == orig_states[led]['mode']


def test_led_pulse_rate(get_buttons):
    """
    Tests the sbuttons' led_pulse_rate method.
    """
    buttons = get_buttons

    # Store original value
    orig_rate = buttons.led_pulse_rate()
    assert isinstance(orig_rate, int)

    # Valid pulse_rate range is 1 to 20
    for rate in range(1, 21):
        set_rate = buttons.led_pulse_rate(rate)
        assert set_rate == rate
        assert buttons.led_pulse_rate() == rate

    # Test out of range values
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_pulse_rate(0)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_pulse_rate(21)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_pulse_rate(random.randint(22, 100))
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_pulse_rate(random.randint(-100, -1))
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_pulse_rate('moo')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_pulse_rate({})
    assert 'Invalid parameter' in execinfo.value.message

    # Reset value and confirm
    set_rate = buttons.led_pulse_rate(orig_rate)
    assert set_rate == orig_rate
    assert buttons.led_pulse_rate() == orig_rate


def test_led_on_off_rate(get_buttons):
    """
    Tests the sbuttons' led_on_off_rate method.
    """
    buttons = get_buttons

    # Store original value
    orig_rate = buttons.led_on_off_rate()
    assert isinstance(orig_rate, int)

    # Valid pulse_rate range is 1 to 20
    for rate in range(1, 21):
        set_rate = buttons.led_on_off_rate(rate)
        assert set_rate == rate
        assert buttons.led_on_off_rate() == rate

    # Test out of range values
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_on_off_rate(0)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_on_off_rate(21)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_on_off_rate(random.randint(22, 100))
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_on_off_rate(random.randint(-100, -1))
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid values
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_on_off_rate('bad')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.led_on_off_rate({})
    assert 'Invalid parameter' in execinfo.value.message

    # Reset value and confirm
    set_rate = buttons.led_on_off_rate(orig_rate)
    assert set_rate == orig_rate
    assert buttons.led_on_off_rate() == orig_rate


def test_hold_threshold(get_buttons):
    """
    Tests the sbuttons' hold_threshold method.
    """
    buttons = get_buttons

    # Store original value
    orig_count = buttons.hold_threshold()
    assert isinstance(orig_count, int)

    # Set new valid value
    new_hold_count = random.randint(10, 255)
    set_count = buttons.hold_threshold(new_hold_count)
    assert set_count == new_hold_count
    assert buttons.hold_threshold() == new_hold_count

    # Test the edge cases
    set_count = buttons.hold_threshold(10)
    assert set_count == 10
    assert buttons.hold_threshold() == 10
    set_count = buttons.hold_threshold(255)
    assert set_count == 255
    assert buttons.hold_threshold() == 255

    # Test out of range values
    with pytest.raises(PySproutError) as execinfo:
        buttons.hold_threshold(9)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.hold_threshold(256)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.hold_threshold(random.randint(-10, 8))
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.hold_threshold(random.randint(257, 500))
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid values
    with pytest.raises(PySproutError) as execinfo:
        buttons.hold_threshold('bad')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.hold_threshold({})
    assert 'Invalid parameter' in execinfo.value.message

    # Reset the original value
    set_count = buttons.hold_threshold(orig_count)
    assert set_count == orig_count
    assert buttons.hold_threshold() == orig_count


def test_factory_default(get_buttons):
    """
    Tests the sbuttons' factory_default method.
    """
    buttons = get_buttons

    buttons.factory_default()
    assert buttons.hold_threshold() == 121
    assert buttons.led_on_off_rate() == 2
    assert buttons.led_pulse_rate() == 4
    for led in SButtons.ButtonID:
        state = buttons.led_state(led)
        assert state['color'] == SButtons.LEDColor.white_orange
        assert state['mode'] == SButtons.LEDMode.off


def test_temperatures(get_buttons):
    """
    Tests the sbuttons' temperatures method.
    """
    buttons = get_buttons

    temperatures = buttons.temperatures()
    info = buttons.info()
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


def test_notifications(get_buttons):
    """
    This method tests the sbuttons.on_*** notifications received from SoHal.
    """
    buttons = get_buttons

    val = buttons.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    name = buttons._object_name
    # Notifications are never sent as '@0' even if we sent the command with @0
    if '@0' in name:
        name = 'sbuttons'

    # TODO(EB) We'll need a manual test for on_button_press, on_suspend,
    # on_resume, on_device_connected, and on_device_disconnected

    buttons.close()
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 0)
    notification = get_notification()
    assert notification == ('{}.on_close'.format(name), None)
    buttons.open()
    notification = get_notification()
    assert notification == ('{}.on_open'.format(name), None)
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 1)

    buttons.hold_threshold(50)
    notification = get_notification()
    assert notification == ('{}.on_hold_threshold'.format(name), 50)

    buttons.led_on_off_rate(15)
    notification = get_notification()
    assert notification == ('{}.on_led_on_off_rate'.format(name), 15)

    buttons.led_pulse_rate(12)
    notification = get_notification()
    assert notification == ('{}.on_led_pulse_rate'.format(name), 12)

    button = SButtons.ButtonID.center
    state = {'color': SButtons.LEDColor.orange, 'mode': SButtons.LEDMode.pulse}
    buttons.led_state(button, state)
    notification = get_notification()
    assert notification == ('{}.on_led_state'.format(name), [button, state])

    buttons.factory_default()
    notification = get_notification()
    assert notification == ('{}.on_factory_default'.format(name), None)

    val = buttons.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Now make sure we aren't getting notification callbacks anymore...
    buttons.hold_threshold(30)
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    # Verify hippy raises errors if we call subscribe with invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        buttons.subscribe('string')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.subscribe(buttons)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.subscribe({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        buttons.subscribe(3)
    assert 'Invalid parameter' in execinfo.value.message
