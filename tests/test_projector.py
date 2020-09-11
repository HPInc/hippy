
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy projector.
"""

from __future__ import division, absolute_import, print_function

import random
import re
import threading
import time
import pytest

from hippy import Projector
from hippy import PySproutError

import check_projector_types
import check_system_types
import check_device_types
from check_device_types import Devices


device_name = 'projector'
projector_serial_len = 14
notifications = []
condition = threading.Condition()


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_projector(request, index):
    """
    A pytest fixture to initialize and return the Projector object with
    the given index.
    """
    projector = Projector(index)
    try:
        projector.open()
    except RuntimeError:
        pytest.skip("Could not open projector connection")
    projector.off()
    time.sleep(0.25)

    def fin():
        time.sleep(0.25)
        projector.unsubscribe()
        projector.off()
        projector.close()
    request.addfinalizer(fin)

    return projector


def get_proj_fw_version(projector):
    """
    Returns a dictionary containing the parsed out firmware version info for
    the given projector. Note that so far this has only been tested on 1.6
    projectors and will need to be updated if it is used on Gen 1 devices.
    """
    info = projector.info()
    data = info['fw_version'].split(' ', 2)
    major, minor = data[0].split('.')
    version = {'major': int(major), 'minor': int(minor), 'git': data[1],
               'date': data[2]}
    return version


def turn_proj_on(projector, projector_model):
    """
    Sends a projector.on command and waits for a notification that the
    projector is in the 'on' state before returning.
    projector_model should be a check_device_types.Devices object indicating
    which model of projector this is.
    """
    projector.subscribe(callback)
    projector.on()
    notification = get_notification()
    notification = (re.sub(r"@\d+", "", notification[0]), notification[1])
    assert notification == ('projector.on_state',
                            Projector.State.transition_to_on)
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        notification = get_notification()
        notification = (re.sub(r"@\d+", "", notification[0]), notification[1])
        assert notification == ('projector.on_state',
                                Projector.State.on_no_source)
    notification = get_notification()
    notification = (re.sub(r"@\d+", "", notification[0]), notification[1])
    assert notification == ('projector.on_state', Projector.State.on)
    projector.unsubscribe()
    assert projector.state() == Projector.State.on


def test_info(get_projector):
    """
    Tests the projector's info method
    """
    projector = get_projector

    info = projector.info()
    check_device_types.check_DeviceInfo(info)

    serial = info['serial']
    #assert len(serial) == projector_serial_len

    vid_pid = (info['vendor_id'], info['product_id'])
    assert vid_pid in (Devices.projector_g1.value,
                       Devices.projector_g2.value,
                       Devices.projector_steele.value)


def test_device_specific_info(get_projector):
    """
    Tests the projector's device_specific_info method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    if projector_model == Devices.projector_g1:
        with pytest.raises(PySproutError) as execinfo:
            projector.device_specific_info()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    info = projector.device_specific_info()

    # check that each item is the correct type
    assert isinstance(info['column_serial'], str)
    assert len(info['column_serial']) == projector_serial_len
    assert isinstance(info['manufacturing_time'], str)
    assert len(info['manufacturing_time']) == projector_serial_len
    assert isinstance(info['eeprom_version'], int)
    assert isinstance(info['hw_version'], int)

    assert isinstance(info['asic_version']['patch_lsb'], int)
    assert isinstance(info['asic_version']['patch_msb'], int)
    assert isinstance(info['asic_version']['minor'], int)
    assert isinstance(info['asic_version']['major'], int)

    assert isinstance(info['flash_version']['patch_lsb'], int)
    assert isinstance(info['flash_version']['patch_msb'], int)
    assert isinstance(info['flash_version']['minor'], int)
    assert isinstance(info['flash_version']['major'], int)

    assert isinstance(info['geo_fw_version']['package'], str)
    assert isinstance(info['geo_fw_version']['major'], int)
    assert isinstance(info['geo_fw_version']['minor'], int)
    assert isinstance(info['geo_fw_version']['test_release'], int)


def test_calibration_data(get_projector):
    """
    Tests the projector's calibration_data method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    if projector_model == Devices.projector_g1:
        with pytest.raises(PySproutError) as execinfo:
            projector.calibration_data()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    cal = projector.calibration_data()
    check_projector_types.check_CalibrationData(cal)


def test_open_and_close(get_projector):
    """
    Tests the projector's open, open_count, and close methods.
    """
    projector = get_projector

    connected = projector.is_device_connected()
    assert connected is True

    assert projector.open_count() == 1
    count = projector.close()
    assert isinstance(count, int)
    assert count == 0
    assert projector.open_count() == 0
    with pytest.raises(PySproutError) as execinfo:
        # Any call should fail
        projector.on()
    assert 'Device is not open' in str(execinfo.value)
    count = projector.open()
    assert isinstance(count, int)
    assert count == 1
    assert projector.open_count() == 1
    # Any call should now work as well
    projector.on()


def test_hw_info(get_projector):
    """
    Tests the projector's hardware_info method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    hw_info = projector.hardware_info()
    if projector_model == Devices.projector_g1:
        assert hw_info['input_resolution'] == {'width': 1024, 'height': 768}
    else:
        assert hw_info['input_resolution'] == {'width': 1920, 'height': 1280}
    assert hw_info['pixel_density'] == 32
    assert hw_info['refresh_rate'] == 60


def test_manufacturing_data(get_projector):
    """
    Tests the projector's manufacturing_data method.
    """
    projector = get_projector

    data = projector.manufacturing_data()
    assert isinstance(data['exposure'], int)
    assert 1 <= data['exposure'] <= 3385
    assert isinstance(data['gain'], int)
    assert 0 <= data['gain'] <= 127
    assert isinstance(data['red'], int)
    assert 1024 <= data['red'] <= 4095
    assert isinstance(data['green'], int)
    assert 1024 <= data['green'] <= 4095
    assert isinstance(data['blue'], int)
    assert 1024 <= data['blue'] <= 4095

    corners = ('top_left', 'top_right', 'bottom_left', 'bottom_right')
    edges = ('top_middle', 'bottom_middle', 'left_middle', 'right_middle',
             'center')
    for corner in corners:
        assert isinstance(data['hires_corners'][corner]['x'], float)
        assert isinstance(data['hires_corners'][corner]['y'], float)
        assert isinstance(data['ir_corners'][corner]['x'], float)
        assert isinstance(data['ir_corners'][corner]['y'], float)

    keystone_type = data['keystone']['type']
    assert keystone_type in ['1d', '2d']
    value = data['keystone']['value']
    if keystone_type == '1d':
        assert isinstance(value['pitch'], float)
        assert -20.0 <= value['pitch'] <= 0.0
        assert isinstance(value['display_area']['x'], int)
        assert isinstance(value['display_area']['y'], int)
        assert isinstance(value['display_area']['width'], int)
        assert isinstance(value['display_area']['height'], int)
    else:
        for corner in corners:
            assert isinstance(value[corner]['x'], int)
            assert isinstance(value[corner]['y'], int)
        for edge in edges:
            assert isinstance(value[edge]['x'], int)
            assert isinstance(value[edge]['y'], int)


def test_monitor_coordinates(get_projector):
    """
    Tests the projector's monitor_coordinates method.
    """
    projector = get_projector

    coordinates = projector.monitor_coordinates()
    check_system_types.check_Rectangle(coordinates)


def test_on_off(get_projector):
    """
    Tests the projector's on and off methods.
    """
    projector = get_projector

    state = projector.state()
    assert isinstance(state, Projector.State)
    assert isinstance(state.value, str)

    projector.on()
    state = projector.state()
    assert state in (Projector.State.on, Projector.State.on_no_source)
    start = time.time()
    while state != Projector.State.on:
        # Make sure we haven't been waiting more than 5 seconds...
        assert (time.time() - start) < 5
        time.sleep(0.25)
        state = projector.state()
    assert projector.state() == Projector.State.on
    assert projector.state().value == 'on'

    projector.off()
    assert projector.state() == Projector.State.standby
    assert projector.state().value == 'standby'


def test_flash(get_projector):
    """
    Tests the projector's flash method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    with pytest.raises(PySproutError) as execinfo:
        # flash will fail if the projector isn't on
        projector.flash(True)
    assert execinfo.value.message == 'Device is in the wrong state'

    turn_proj_on(projector, projector_model)

    seconds = projector.flash(True)
    assert projector.state() == Projector.State.flashing
    time.sleep(3)
    new_seconds = projector.flash(True)
    assert new_seconds < seconds
    with pytest.raises(PySproutError) as execinfo:
        projector.flash(False)
    assert execinfo.value.message == 'Device is in the wrong state'

    projector.grayscale()
    assert projector.state() == Projector.State.grayscale
    projector.on()
    assert projector.state() == Projector.State.on
    seconds = projector.flash(False)
    assert projector.state() == Projector.State.flashing
    time.sleep(3)
    new_seconds = projector.flash(False)
    assert new_seconds < seconds
    with pytest.raises(PySproutError) as execinfo:
        projector.flash(True)
    assert execinfo.value.message == 'Device is in the wrong state'
    assert projector.state() == Projector.State.flashing

    projector.grayscale()
    assert projector.state() == Projector.State.grayscale
    projector.on()
    assert projector.state() == Projector.State.on
    seconds = projector.flash(True)
    assert seconds == 10
    time.sleep(10)
    assert projector.state() == Projector.State.on
    seconds = projector.flash(False)
    assert seconds == 10
    time.sleep(10)
    assert projector.state() == Projector.State.on

    # Test invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        projector.flash('moo')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.flash({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.flash(0)
    assert 'Invalid parameter' in execinfo.value.message


def test_grayscale(get_projector):
    """
    Tests the projector's grayscale method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    with pytest.raises(PySproutError) as execinfo:
        # Grayscale will fail if the projector isn't on
        projector.grayscale()
    assert execinfo.value.message == 'Device is in the wrong state'

    turn_proj_on(projector, projector_model)

    projector.grayscale()
    assert projector.state() == Projector.State.grayscale
    projector.flash(True)
    time.sleep(10)
    if projector_model == Devices.projector_g1:
        assert projector.state() == Projector.State.on
        projector.grayscale()
    else:
        assert projector.state() == Projector.State.grayscale
    projector.flash(False)
    time.sleep(10)
    if projector_model == Devices.projector_g1:
        assert projector.state() == Projector.State.on
    else:
        assert projector.state() == Projector.State.grayscale

    projector.on()
    assert projector.state() == Projector.State.on


def check_keystone_1d(projector, keystone):
    """
    This method is part of the keystone test. It should be used for projectors
    that use the keystone1d type.
    """
    value = keystone['value']
    assert keystone['type'] == '1d'
    assert isinstance(value['pitch'], float)
    assert -20.0 <= value['pitch'] <= 0.0
    assert isinstance(value['display_area']['x'], int)
    assert value['display_area']['x'] >= 0
    assert isinstance(value['display_area']['y'], int)
    assert value['display_area']['y'] >= 0
    assert isinstance(value['display_area']['width'], int)
    assert (value['display_area']['width'] + value['display_area']['x']) <= 1500
    assert isinstance(value['display_area']['height'], int)
    assert (value['display_area']['height'] +
            value['display_area']['y']) <= 1000

    new_key = {'type' : '1d',
               'value' : {'pitch': -15.5,
                          'display_area': {'x' : 0, 'y': 0,
                                           'width' : 1000, 'height' : 800}}}
    set_key = projector.keystone(new_key)
    assert set_key == new_key
    assert projector.keystone() == new_key

    new_key['value']['pitch'] = -15.5
    new_key['value']['display_area'] = {'x' : 0, 'y': 0,
                                        'width' : 342, 'height' : 256}
    set_key = projector.keystone(new_key)
    assert set_key == new_key
    assert projector.keystone() == new_key

    # Test changing just one value in the keystone at a time
    pitch = {'type' : '1d', 'value' : {'pitch' : -18.25}}
    set_key = projector.keystone(pitch)
    new_key['value']['pitch'] = pitch['value']['pitch']
    assert set_key == new_key
    assert projector.keystone() == new_key

    area = {'type' : '1d', 'value' : {'display_area' : {'x': 10}}}
    set_key = projector.keystone(area)
    new_key['value']['display_area']['x'] = area['value']['display_area']['x']
    assert set_key == new_key
    assert projector.keystone() == new_key

    area = {'type' : '1d', 'value' : {'display_area' : {'y': 16}}}
    set_key = projector.keystone(area)
    new_key['value']['display_area']['y'] = area['value']['display_area']['y']
    assert set_key == new_key
    assert projector.keystone() == new_key

    area = {'type' : '1d', 'value' : {'display_area' : {'width': 964}}}
    set_key = projector.keystone(area)
    new_key['value']['display_area']['width'] = 964
    assert set_key == new_key
    assert projector.keystone() == new_key

    area = {'type' : '1d', 'value' : {'display_area' : {'height': 876}}}
    set_key = projector.keystone(area)
    new_key['value']['display_area']['height'] = 876
    assert set_key == new_key
    assert projector.keystone() == new_key

    # Pass in out of range parameters and verify it throws errors:
    new_key['value']['pitch'] = -20.1
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message
    new_key['value']['pitch'] = 0.1
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message

    new_key['value']['pitch'] = -15.0
    new_key['value']['display_area'] = {'x' : -1, 'y': 0,
                                        'width' : 342, 'height' : 256}
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message
    new_key['value']['display_area'] = {'x' : 0, 'y': -1,
                                        'width' : 342, 'height' : 256}
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message
    new_key['value']['display_area'] = {'x' : 0, 'y': 0,
                                        'width' : 341, 'height' : 256}
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message
    new_key['value']['display_area'] = {'x' : 0, 'y': 0,
                                        'width' : 342, 'height' : 255}
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message
    new_key['value']['display_area'] = {'x' : 0, 'y': 0,
                                        'width' : 1501, 'height' : 256}
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message
    new_key['value']['display_area'] = {'x' : 0, 'y': 0,
                                        'width' : 342, 'height' : 1001}
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message
    new_key['value']['display_area'] = {'x' : 15, 'y': 0,
                                        'width' : 1488, 'height' : 1000}
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message
    new_key['value']['display_area'] = {'x' : 0, 'y': 3,
                                        'width' : 342, 'height' : 998}
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_key)
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d', 'value': {'z':8}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d', 'value': {}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d', 'value': 7})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d', 'value': 'moo'})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d',
                            'bad': {'display_area': {'x': 8}}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d', 'pitch': {'x': 8}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d',
                            'value': {'display_area': {'x': 'y'}}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d',
                            'value': {'display_area': {}}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d',
                            'value': {'display_area': 'area'}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d',
                            'value': {'display_area': 13}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d', 'value': {'pitch': {}}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '1d', 'value': {'pitch': 'invalid'}})
    assert 'Invalid parameter' in execinfo.value.message


def check_keystone_2d(projector, keystone):
    """
    This method is part of the keystone test. It should be used for projectors
    that use the keystone2d type.
    """
    value = keystone['value']
    assert keystone['type'] == '2d'
    corners = ('top_left', 'top_right', 'bottom_left', 'bottom_right')
    edges = ('top_middle', 'bottom_middle', 'left_middle', 'right_middle',
             'center')
    for corner in corners:
        assert isinstance(value[corner]['x'], int)
        assert isinstance(value[corner]['y'], int)
    for edge in edges:
        assert isinstance(value[edge]['x'], int)
        assert isinstance(value[edge]['y'], int)
    assert value['top_middle']['x'] == value['bottom_middle']['x']
    assert value['left_middle']['y'] == value['right_middle']['y']

    new_ks = projector.create_2d_keystone_dict(100, 200, 0, 40,
                                               0, 0, -200, -300)
    set_ks = projector.keystone(new_ks)
    assert set_ks == new_ks
    assert projector.keystone() == new_ks

    new_ks = projector.create_2d_keystone_dict(10, 50, -10, 100,
                                               30, -5, 0, -50,
                                               10, 20, 10, 9,
                                               -15, 30, 5, 30,
                                               12, -18)
    set_ks = projector.keystone(new_ks)
    assert set_ks == new_ks
    assert projector.keystone() == new_ks

    # Verify that updating only part of the keystone leaves the rest
    # unchanged
    prior_ks = projector.keystone()
    new_ks = {'type' : '2d',
              'value' : {'top_middle' : {'x' : 100, 'y' : 20},
                         'top_left' : {'x': 30, 'y': 60}}}
    set_ks = projector.keystone(new_ks)
    expected_ks = prior_ks.copy()
    expected_ks['value']['top_middle'] = new_ks['value']['top_middle']
    expected_ks['value']['top_left'] = new_ks['value']['top_left']
    top_bottom_x = new_ks['value']['top_middle']['x']
    expected_ks['value']['bottom_middle']['x'] = top_bottom_x
    assert set_ks == expected_ks
    assert projector.keystone() == expected_ks

    # Verify that it throws an error if the top_middle and bottom_middle
    # x values don't match
    new_ks = projector.create_2d_keystone_dict(10, 50, -10, 100,
                                               30, -5, 0, -50,
                                               10, 20, 15, 9, #x's differ
                                               -15, 30, 5, 30)
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_ks)
    assert ('top_middle x must equal bottom_middle x' in
            execinfo.value.message)

    # Verify that it throws an error if the left_middle and right_middle
    # y values don't match
    new_ks = projector.create_2d_keystone_dict(10, 50, -10, 100,
                                               30, -5, 0, -50,
                                               10, 20, 10, 9,
                                               -15, 30, 5, 11) #y's differ
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(new_ks)
    assert ('left_middle y must equal right_middle y' in
            execinfo.value.message)

    # Test that out of range parameters throw errors
    points = corners + edges
    for point in points:
        err_msg = 'Valid range is -32767 <= ' + point + ' x <= 32767'
        # Test x < min value
        x = random.randint(-100000, -32767)
        y = random.randint(-32767, 32768)
        new_ks = {'type' : '2d', 'value': {point : {'x' : x, 'y' : y}}}
        with pytest.raises(PySproutError) as execinfo:
            projector.keystone(new_ks)
        assert err_msg in execinfo.value.message
        # Test x > max value
        x = random.randint(32768, 1000000)
        y = random.randint(-32767, 32768)
        new_ks = {'type' : '2d', 'value': {point : {'x' : x, 'y' : y}}}
        with pytest.raises(PySproutError) as execinfo:
            projector.keystone(new_ks)
        assert err_msg in execinfo.value.message

        err_msg = 'Valid range is -32767 <= ' + point + ' y <= 32767'
        # Test y < min value
        x = random.randint(-32767, 32768)
        y = random.randint(-100000, -32767)
        new_ks = {'type' : '2d', 'value': {point : {'x' : x, 'y' : y}}}
        with pytest.raises(PySproutError) as execinfo:
            projector.keystone(new_ks)
        assert err_msg in execinfo.value.message
        # Test y > max value
        x = random.randint(-32767, 32768)
        y = random.randint(32768, 1000000)
        new_ks = {'type' : '2d', 'value': {point : {'x' : x, 'y' : y}}}
        with pytest.raises(PySproutError) as execinfo:
            projector.keystone(new_ks)
        assert err_msg in execinfo.value.message

    # Test invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '2d', 'value': {'z':8}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '2d', 'bad': {'top_left': {'x': 8}}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '2d', 'bad': {'top_left': {'x': 8}}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '2d',
                            'value': {'top_left': {'x': 'y'}}})
    assert 'Invalid parameter' in execinfo.value.message


def test_keystone(get_projector):
    """
    Tests the projector's keystone method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    turn_proj_on(projector, projector_model)
    keystone = projector.keystone()
    assert isinstance(keystone, dict)
    assert isinstance(keystone['type'], str)
    assert keystone['type'] in ['1d', '2d']
    assert isinstance(keystone['value'], dict)

    if projector_model == Devices.projector_g1:
        check_keystone_1d(projector, keystone)
    else:
        check_keystone_2d(projector, keystone)

    # Getting/Setting the keystone should also work when the projector is off
    projector.off()
    if projector_model == Devices.projector_g1:
        new_ks = {'type' : '1d', 'value' : {'pitch': -17.0,
                                            'display_area': {'x' : 10,
                                                             'y': 20,
                                                             'width' : 1026,
                                                             'height' : 840}}}
        set_ks = projector.keystone(new_ks)
        assert set_ks == new_ks
        assert projector.keystone() == new_ks
    else:
        new_ks = {'type' : '2d',
                  'value' : {'top_left': {'x': 80, 'y': 15},
                             'top_right': {'x': 0, 'y': 20},
                             'bottom_left': {'x': 10, 'y': 0},
                             'bottom_right': {'x': -25, 'y': -30},
                             'top_middle': {'x': 0, 'y': 0},
                             'bottom_middle': {'x': 0, 'y': 0},
                             'left_middle': {'x': 0, 'y': 0},
                             'right_middle': {'x': 0, 'y': 0},
                             'center': {'x': 0, 'y': 0}}}
        set_ks = projector.keystone(new_ks)
        assert set_ks == new_ks
        assert projector.keystone() == new_ks

    # Test invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone('bad')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone(0)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'type': '4d', 'value': {'x': 7}})
    assert 'not supported' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.keystone({'test': 43})
    assert 'Invalid parameter' in execinfo.value.message

    # set the keystone back to the original values
    set_ks = projector.keystone(keystone)
    assert set_ks == keystone
    assert projector.keystone() == keystone


def test_brightness(get_projector):
    """
    Tests the projector's brightness method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    original_brightness = projector.brightness()

    # Test the brightness methods when the projector is off
    new_brightness = random.randint(30, 100)
    brightness = projector.brightness(new_brightness)
    assert brightness == new_brightness
    assert projector.brightness() == new_brightness

    # Turn on the projector and make sure the brightness still works
    turn_proj_on(projector, projector_model)
    assert projector.brightness() == new_brightness

    new_brightness = random.randint(30, 100)
    brightness = projector.brightness(new_brightness)
    assert brightness == new_brightness
    assert projector.brightness() == new_brightness

    # Test the edge cases
    brightness = projector.brightness(100)
    assert brightness == 100
    assert projector.brightness() == 100
    brightness = projector.brightness(30)
    assert brightness == 30
    assert projector.brightness() == 30

    # Test out of range values
    with pytest.raises(PySproutError) as execinfo:
        projector.brightness(29)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.brightness(101)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.brightness(1020)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.brightness(-2)
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        projector.brightness("abc")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.brightness({})
    assert 'Invalid parameter' in execinfo.value.message

    # Set the original value back
    brightness = projector.brightness(original_brightness)
    assert brightness == original_brightness
    assert projector.brightness() == original_brightness


def test_factory_default(get_projector):
    """
    Tests the projector's factory_default method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    projector.factory_default()
    assert projector.brightness() == 100
    assert projector.manufacturing_data()['keystone'] == projector.keystone()
    assert Projector.State.standby == projector.state()
    if projector_model == Devices.projector_g2:
        white_point = projector.white_point()
        assert white_point['name'] == Projector.Illuminant.d65
        d65 = {'name': 'd65', 'value': {'x': 0.31271, 'y': 0.32902}}
        assert round(white_point['value']['x'], 5) == d65['value']['x']
        assert round(white_point['value']['y'], 5) == d65['value']['y']
        assert white_point['name'].value == d65['name']


def test_temperatures(get_projector):
    """
    Tests the projector's temperatures method.
    """
    projector = get_projector

    temperatures = projector.temperatures()
    info = projector.info()
    check_system_types.check_TemperatureInfoList(temperatures, [info])


def test_solid_color(get_projector):
    """
    Tests the projector's solid_color method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    if projector_model == Devices.projector_g1:
        with pytest.raises(PySproutError) as execinfo:
            projector.solid_color()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    with pytest.raises(PySproutError) as execinfo:
        # solid_color will fail if the projector isn't on
        projector.solid_color()
    assert execinfo.value.message == 'Device is in the wrong state'

    with pytest.raises(PySproutError) as execinfo:
        # solid_color will fail if the projector isn't on
        projector.solid_color('green')
    assert execinfo.value.message == 'Device is in the wrong state'

    turn_proj_on(projector, projector_model)

    fw_version = get_proj_fw_version(projector)

    color = projector.solid_color()
    assert isinstance(color, Projector.SolidColor)
    for color in Projector.SolidColor:
        if color != Projector.SolidColor.off:
            new_color = projector.solid_color(color)
            assert new_color == color
            assert isinstance(new_color.value, str)
            assert color == projector.solid_color()
            if check_device_types.firmware_version_at_least(fw_version, 5, 9):
                assert Projector.State.solid_color == projector.state()
            else:
                assert Projector.State.on == projector.state()

    new_color = projector.solid_color('off')
    assert new_color == Projector.SolidColor.off
    assert Projector.SolidColor.off == projector.solid_color()

    if check_device_types.firmware_version_at_least(fw_version, 5, 9):
        assert Projector.State.on == projector.state()
        # Now that we're in the 'on' state, sending a solid_color 'off' should
        # raise a wrong state error.
        with pytest.raises(PySproutError) as execinfo:
            projector.solid_color('off')
        assert execinfo.value.message == 'Device is in the wrong state'

        color = projector.solid_color('yellow')
        assert Projector.SolidColor.yellow == color
        assert Projector.SolidColor.yellow == projector.solid_color()
        assert Projector.State.solid_color == projector.state()
        projector.on()
        assert Projector.State.on == projector.state()
        assert Projector.SolidColor.off == projector.solid_color()

        # When flash times out it should go back to solid color
        color = projector.solid_color('blue')
        assert Projector.SolidColor.blue == color
        assert Projector.SolidColor.blue == projector.solid_color()
        assert Projector.State.solid_color == projector.state()
        projector.flash(True)
        assert Projector.State.flashing == projector.state()
        time.sleep(10)
        assert Projector.State.solid_color == projector.state()
        assert Projector.SolidColor.blue == projector.solid_color()
        projector.flash(False)
        assert Projector.State.flashing == projector.state()
        time.sleep(10)
        assert Projector.State.solid_color == projector.state()
        assert Projector.SolidColor.blue == projector.solid_color()

        projector.flash(True)
        assert Projector.State.flashing == projector.state()
        # solid_color 'off' fails if we're in the 'flashing' state
        with pytest.raises(PySproutError) as execinfo:
            projector.solid_color('off')
        assert execinfo.value.message == 'Device is in the wrong state'
        # flash(True) -> solid_color -> solid_color(off) should put us in
        # the 'on' state
        color = projector.solid_color('cyan')
        assert Projector.SolidColor.cyan == color
        assert Projector.SolidColor.cyan == projector.solid_color()
        assert Projector.State.solid_color == projector.state()
        color = projector.solid_color('off')
        assert Projector.SolidColor.off == color
        assert Projector.SolidColor.off == projector.solid_color()
        assert Projector.State.on == projector.state()

        projector.flash(False)
        assert Projector.State.flashing == projector.state()
        # solid_color 'off' fails if we're in the 'flashing' state
        with pytest.raises(PySproutError) as execinfo:
            projector.solid_color('off')
        assert execinfo.value.message == 'Device is in the wrong state'
        # flash(False) -> solid_color -> solid_color(off) should put us in
        # the 'on' state
        color = projector.solid_color('magenta')
        assert Projector.SolidColor.magenta == color
        assert Projector.SolidColor.magenta == projector.solid_color()
        assert Projector.State.solid_color == projector.state()
        color = projector.solid_color('off')
        assert Projector.SolidColor.off == color
        assert Projector.SolidColor.off == projector.solid_color()
        assert Projector.State.on == projector.state()

        projector.grayscale()
        assert Projector.State.grayscale == projector.state()
        # solid_color 'off' fails if we're in the 'grayscale' state
        with pytest.raises(PySproutError) as execinfo:
            projector.solid_color('off')
        assert execinfo.value.message == 'Device is in the wrong state'
        # grayscale -> solid_color -> solid_color(off) should put us back in
        # the 'grayscale' state
        color = projector.solid_color('green')
        assert Projector.SolidColor.green == color
        assert Projector.SolidColor.green == projector.solid_color()
        assert Projector.State.solid_color == projector.state()
        color = projector.solid_color('off')
        assert Projector.SolidColor.off == color
        assert Projector.SolidColor.off == projector.solid_color()
        assert Projector.State.grayscale == projector.state()

    # Verify invalid values are rejected (by hippy)
    with pytest.raises(ValueError) as execinfo:
        projector.solid_color('fake')
    with pytest.raises(ValueError) as execinfo:
        projector.solid_color(3)
    with pytest.raises(ValueError) as execinfo:
        projector.solid_color({})
    with pytest.raises(ValueError) as execinfo:
        projector.solid_color('gray')

    # Send bad values to SoHal (bypassing the hippy enum check) and make
    # sure SoHal throws an error...
    with pytest.raises(PySproutError) as execinfo:
        projector._send_msg('solid_color', 'fake') # pylint: disable=protected-access
    with pytest.raises(PySproutError) as execinfo:
        projector._send_msg('solid_color', 2) # pylint: disable=protected-access
    with pytest.raises(PySproutError) as execinfo:
        projector._send_msg('solid_color', {}) # pylint: disable=protected-access


def test_led_times(get_projector):
    """
    Tests the projector's led_times method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    if projector_model == Devices.projector_g1:
        with pytest.raises(PySproutError) as execinfo:
            projector.led_times()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    times = projector.led_times()
    assert isinstance(times, dict)
    assert isinstance(times['grayscale'], float)
    assert isinstance(times['on'], float)
    assert isinstance(times['flash'], float)

    assert times['grayscale'] > 0
    assert times['on'] > 0
    assert times['flash'] > 0


def test_structured_light_mode(get_projector):
    """
    Tests the projector's structured_light_mode method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    if projector_model == Devices.projector_g1:
        with pytest.raises(PySproutError) as execinfo:
            projector.led_times()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    with pytest.raises(PySproutError) as execinfo:
        projector.structured_light_mode()
    assert execinfo.value.message == 'Device is in the wrong state'

    turn_proj_on(projector, projector_model)

    slm = projector.structured_light_mode()
    assert isinstance(slm, bool)
    assert slm is False

    slm = projector.structured_light_mode(True)
    assert slm is True
    assert projector.structured_light_mode() is True

    slm = projector.structured_light_mode(False)
    assert slm is False
    assert projector.structured_light_mode() is False

    # Turn on structured_light_mode, then turn the projector off and then
    # on again. When it comes on, structured_light_mode should always be false,
    # regardless of what it was previously.
    slm = projector.structured_light_mode(True)
    assert slm is True
    assert projector.structured_light_mode() is True
    projector.off()
    assert Projector.State.standby == projector.state()
    projector.on()
    assert projector.state() in (Projector.State.on,
                                 Projector.State.on_no_source)
    assert projector.structured_light_mode() is False

    # Verify that non-boolean values raise errors
    with pytest.raises(PySproutError) as execinfo:
        projector.structured_light_mode(0)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.structured_light_mode('fake')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.structured_light_mode({})
    assert 'Invalid parameter' in execinfo.value.message


def test_white_point(get_projector):
    """
    Tests the projector's white_point method.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    if projector_model == Devices.projector_g1:
        with pytest.raises(PySproutError) as execinfo:
            projector.led_times()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    orig_wp = projector.white_point()
    assert isinstance(orig_wp, dict)
    assert isinstance(orig_wp['name'], Projector.Illuminant)
    assert isinstance(orig_wp['value'], dict)
    assert isinstance(orig_wp['value']['x'], float)
    assert isinstance(orig_wp['value']['y'], float)

    # Test passing in just the name
    for name in Projector.Illuminant:
        new_wp = projector.white_point({'name': name.value})
        assert new_wp['name'] == name
        new_wp = projector.white_point()
        assert new_wp['name'] == name

    d50 = {'name': 'd50', 'value': {'x': 0.34567, 'y': 0.35850}}
    d65 = {'name': 'd65', 'value': {'x': 0.31271, 'y': 0.32902}}
    d75 = {'name': 'd75', 'value': {'x': 0.29902, 'y': 0.31485}}
    # This one is d55
    custom = {'name': 'custom', 'value': {'x': 0.33242, 'y': 0.34743}}

    # Test passing in the whole dictionary
    for item in [d50, d65, d75, custom]:
        new_wp = projector.white_point(item)
        assert round(new_wp['value']['x'], 5) == item['value']['x']
        assert round(new_wp['value']['y'], 5) == item['value']['y']
        assert new_wp['name'].value == item['name']

        new_wp = projector.white_point()
        assert round(new_wp['value']['x'], 5) == item['value']['x']
        assert round(new_wp['value']['y'], 5) == item['value']['y']
        assert new_wp['name'].value == item['name']

    # Verify parameters that are out of range raise errors
    with pytest.raises(PySproutError) as execinfo:
        projector.white_point({'name' : 'custom',
                               'value' : {'x' : 0.4, 'y' : 0.34743}})
    assert 'Parameter out of range' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        projector.white_point({'name' : 'custom',
                               'value' : {'x' : 0.2, 'y' : 0.34743}})
    assert 'Parameter out of range' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        projector.white_point({'name' : 'custom',
                               'value' : {'x' : 0.33242, 'y' : 0.4}})
    assert 'Parameter out of range' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        projector.white_point({'name' : 'custom',
                               'value' : {'x' : 0.33242, 'y' : 0.2}})
    assert 'Parameter out of range' in str(execinfo.value)

    # Verify that Invalid parameters raise errors
    with pytest.raises(PySproutError) as execinfo:
        projector.white_point({'name' : 'custom',
                               'value' : {'x' : 'bad', 'y' : 0.34743}})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.white_point({'name' : 'custom',
                               'value' : {'x' : 0.33242, 'y' : 'moo'}})
    assert 'Invalid parameter' in execinfo.value.message

    # Hippy should reject strings that aren't one of the Illuminant items...
    with pytest.raises(ValueError) as execinfo:
        projector.white_point({'name' : 'fake'})
    with pytest.raises(ValueError) as execinfo:
        projector.white_point({'name' : 'bad',
                               'value' : {'x' : 0.33242, 'y' : 0.34743}})
    # Hippy should also reject dictionaries without a 'name' key
    with pytest.raises(KeyError) as execinfo:
        projector.white_point({'fake' : 5})

    # Send a bad value to SoHal (bypassing the hippy enum check) and make
    # sure SoHal throws an error...
    with pytest.raises(PySproutError) as execinfo:
        projector._send_msg('white_point', 'fake') # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector._send_msg('white_point', {'fake' : 5}) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector._send_msg('white_point', {'name' : 5}) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message

    # Set the default value back
    new_wp = projector.white_point({'name' : Projector.Illuminant.d65})
    assert new_wp['name'] == Projector.Illuminant.d65
    assert projector.white_point()['name'] == Projector.Illuminant.d65


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


def test_notifications(get_projector):
    """
    This method tests the projector.on_*** notifications received from SoHal.
    """
    projector = get_projector
    projector_model = check_device_types.get_device_model(projector)

    val = projector.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    name = projector._object_name
    # Notifications are never sent as '@0' even if we sent the command with @0
    if '@0' in name:
        name = 'projector'

    # TODO(EB) We need to test for on_suspend and on_resume

    projector.close()
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 0)
    notification = get_notification()
    assert notification == ('{}.on_close'.format(name), None)
    projector.open()
    notification = get_notification()
    assert notification == ('{}.on_open'.format(name), None)
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 1)

    projector.on()
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name),
                            Projector.State.transition_to_on)
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        notification = get_notification()
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.on_no_source)
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name), Projector.State.on)

    projector.brightness(67)
    notification = get_notification()
    assert notification == ('{}.on_brightness'.format(name), 67)

    if projector_model == Devices.projector_g1:
        key = {"type": "1d",
               "value": {"pitch": -16.0,
                         "display_area": {"height": 818, "width": 1168,
                                          "x": 58, "y": 22}}}
    else:
        # Adding a sleep here seems to help avoid the "device was not able to
        # complete the request" error the firmware is returning sometimes.
        time.sleep(1)
        key = {"type": "2d",
               "value": {"bottom_left": {"x": 157, "y": -29},
                         "bottom_middle": {"x": 0, "y": 0},
                         "bottom_right": {"x": -177, "y": -45},
                         "center": {"x": 0, "y": 0},
                         "left_middle": {"x": 0, "y": 0},
                         "right_middle": {"x": 0, "y": 0},
                         "top_left": {"x": 64, "y": 27},
                         "top_middle": {"x": 0, "y": 0},
                         "top_right": {"x": -88, "y": 22}}}

    projector.keystone(key)
    notification = get_notification()
    assert notification == ('{}.on_keystone'.format(name), key)

    projector.flash(True)
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        notification = get_notification()
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_flash)
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name),
                            Projector.State.flashing)

    projector.on()
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        notification = get_notification()
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_on)
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name), Projector.State.on)

    projector.flash(False)
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        notification = get_notification()
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_flash)
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name),
                            Projector.State.flashing)

    projector.on()
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        notification = get_notification()
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_on)
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name), Projector.State.on)

    projector.grayscale()
    notification = get_notification()
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_grayscale)
        notification = get_notification()
    assert notification == ('{}.on_state'.format(name),
                            Projector.State.grayscale)

    projector.flash(True)
    notification = get_notification()
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_flash)
        notification = get_notification()
    assert notification == ('{}.on_state'.format(name),
                            Projector.State.flashing)

    projector.grayscale()
    notification = get_notification()
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_grayscale)
        notification = get_notification()
    assert notification == ('{}.on_state'.format(name), Projector.State.grayscale)

    projector.flash(False)
    notification = get_notification()
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_flash)
        notification = get_notification()
    assert notification == ('{}.on_state'.format(name), Projector.State.flashing)

    projector.grayscale()
    notification = get_notification()
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_grayscale)
        notification = get_notification()
    assert notification == ('{}.on_state'.format(name),
                            Projector.State.grayscale)

    projector.on()
    notification = get_notification()
    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        assert notification == ('{}.on_state'.format(name),
                                Projector.State.transition_to_on)
        notification = get_notification()
    assert notification == ('{}.on_state'.format(name), Projector.State.on)


    if projector_model in [Devices.projector_g2, Devices.projector_steele]:
        fw_version = get_proj_fw_version(projector)
        projector.solid_color(Projector.SolidColor.blue)
        if check_device_types.firmware_version_at_least(fw_version, 5, 9):
            notification = get_notification()
            assert notification == ('{}.on_state'.format(name),
                                    Projector.State.solid_color)
        notification = get_notification()
        assert notification == ('{}.on_solid_color'.format(name),
                                Projector.SolidColor.blue)
        projector.solid_color(Projector.SolidColor.off)
        if check_device_types.firmware_version_at_least(fw_version, 5, 9):
            notification = get_notification()
            assert notification == ('{}.on_state'.format(name),
                                    Projector.State.on)
        notification = get_notification()
        assert notification == ('{}.on_solid_color'.format(name),
                                Projector.SolidColor.off)

        projector.structured_light_mode(True)
        notification = get_notification()
        assert notification == ('{}.on_structured_light_mode'.format(name),
                                True)
        projector.structured_light_mode(False)
        notification = get_notification()
        assert notification == ('{}.on_structured_light_mode'.format(name),
                                False)

        white_point = {"name": Projector.Illuminant.custom,
                       "value": {"x": 0.33242, "y": 0.34743}}
        projector.white_point(white_point)
        notification = get_notification()
        notification[1]['value']['x'] = round(notification[1]['value']['x'], 5)
        notification[1]['value']['y'] = round(notification[1]['value']['y'], 5)
        assert notification == ('{}.on_white_point'.format(name), white_point)

    projector.off()
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name),
                            Projector.State.transition_to_st)
    notification = get_notification()
    assert notification == ('{}.on_state'.format(name), Projector.State.standby)

    projector.factory_default()
    notification = get_notification()
    assert notification == ('{}.on_factory_default'.format(name), None)

    val = projector.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Now make sure we aren't getting notification callbacks anymore...
    projector.factory_default()
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    # Verify hippy raises errors if we call subscribe with Invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        projector.subscribe('string')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.subscribe(projector)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.subscribe({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        projector.subscribe(3)
    assert 'Invalid parameter' in execinfo.value.message
