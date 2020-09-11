
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy hirescamera.
"""

from __future__ import division, absolute_import, print_function

import asyncio
import copy
import math
import random
import threading
import time
import enum
import pytest

from hippy import HiResCamera
from hippy import PySproutError

import check_camera_types
import check_device_types
import check_hirescamera_types
import check_system_types
from check_device_types import Devices


device_name = 'hirescamera'
notifications = []
condition = threading.Condition()

# this enum has been copied from SoHal's python/pluto/flick.py file
@enum.unique
class Resolution(enum.IntEnum):
    """
    The supported resolutions.
    Note that this enum was copied from SoHal.
    """
    # parent resolution of 4352 x 3264
    r_4352_3264_6 = 0x6a
    # r_2176_1632_30 = 0x6b    # Hidden resolution for still image capture
    r_2176_1632_15 = 0x7a
    r_640_480_15 = 0x17
    r_4352_2896_6 = 0x84
    r_2176_1448_15 = 0x82
    r_3840_2160_10 = 0x54
    r_1920_1080_15 = 0x6f
    # parent resolution of 4224 x 3168
    r_4224_3168_6 = 0x77
    r_1056_792_15 = 0x7c
    r_1056_704_15 = 0x35
    r_960_540_15 = 0x52
    # parent resolution of 2176 x 1632
    r_2176_1632_25 = 0x79
    r_2176_1448_25 = 0x83
    r_1920_1080_30 = 0x28
    # parent resolution of 2112 x 1584
    r_2112_1584_25 = 0x74
    r_1056_792_30 = 0x7d
    r_1056_704_30 = 0x80
    r_960_540_30 = 0x7e
    # parent resolution of 1056 x 792
    r_1056_792_60 = 0x78
    r_1056_704_60 = 0x81
    r_960_540_60 = 0x7f
    r_640_480_60 = 0x2f
    # parent resolution of 1056 x 594
    r_416_234_60 = 0x73


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_camera(request, index):
    """
    A pytest fixture to initialize and return the HiResCamera object with
    the given index.
    """
    camera = HiResCamera(index)
    try:
        camera.open()
    except RuntimeError:
        pytest.skip("Could not open camera connection")
    def fin():
        camera.unsubscribe()
        camera.close()
    request.addfinalizer(fin)

    return camera


def test_info(get_camera):
    """
    Tests the hirescamera's info method
    """
    camera = get_camera

    info = camera.info()
    check_device_types.check_DeviceInfo(info)

    vid_pid = (info['vendor_id'], info['product_id'])
    assert vid_pid in (Devices.hirescamera.value,
                       Devices.hirescamera_z_3d.value)

    serial = info['serial']
    if Devices(vid_pid) == Devices.hirescamera:
        assert serial == "Not Available"


def test_open_and_close(get_camera):
    """
    Tests the hirescamera's open, open_count, and close methods.
    """
    camera = get_camera

    connected = camera.is_device_connected()
    assert connected is True

    assert camera.open_count() == 1
    count = camera.close()
    assert isinstance(count, int)
    assert count == 0
    assert camera.open_count() == 0
    with pytest.raises(PySproutError) as execinfo:
        # Any call should fail
        camera.white_balance()
    assert execinfo.value.message == 'Device is not open'
    count = camera.open()
    assert isinstance(count, int)
    assert count == 1
    assert camera.open_count() == 1
    # Any call should now work
    camera.white_balance()


def test_camera_index(get_camera):
    """
    Tests the hirescamera's camera_index method.
    """
    camera = get_camera

    index = camera.camera_index()
    assert isinstance(index, int)
    assert index >= 0


def test_exposure(get_camera):
    """
    Tests the hirescamera's exposure method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    if camera_model == Devices.hirescamera_z_3d:
        min_exposure = 1
        max_exposure = 20000
    else:
        min_exposure = 1
        max_exposure = 3385

    with CameraStreaming(camera):
        orig_auto = camera.auto_exposure()
        assert isinstance(orig_auto, bool)

        orig_exposure = camera.exposure()
        assert isinstance(orig_exposure, int)
        assert min_exposure <= orig_exposure <= max_exposure

        auto = camera.auto_exposure(True)
        assert auto is True
        assert camera.auto_exposure() is True
        auto = camera.auto_exposure(False)
        assert auto is False
        assert camera.auto_exposure() is False

        new_exposure = random.randint(min_exposure, max_exposure)
        exposure = camera.exposure(new_exposure)
        assert exposure == new_exposure
        time.sleep(.5)  # Takes a few frames for the new exposure to be set
        assert camera.exposure() == new_exposure

        # Ensure that setting an exposure turns off auto exposure
        auto = camera.auto_exposure(True)
        assert auto is True
        assert camera.auto_exposure() is True
        new_exposure = random.randint(min_exposure, max_exposure)
        exposure = camera.exposure(new_exposure)
        assert exposure == new_exposure
        time.sleep(.5)
        assert camera.exposure() == new_exposure
        assert camera.auto_exposure() is False

        # Test the edge values
        new_exposure = min_exposure
        exposure = camera.exposure(new_exposure)
        assert exposure == new_exposure
        time.sleep(.5)
        assert camera.exposure() == new_exposure
        new_exposure = max_exposure
        exposure = camera.exposure(new_exposure)
        assert exposure == new_exposure
        time.sleep(.5)
        assert camera.exposure() == new_exposure

        # Ensure that out of range values throw errors
        with pytest.raises(PySproutError) as execinfo:
            camera.exposure(max_exposure+1)
        assert 'Parameter out of range' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.exposure(min_exposure-1)
        assert 'Parameter out of range' in execinfo.value.message
        bad_exposure = random.randint(max_exposure+1, max_exposure+2000)
        with pytest.raises(PySproutError) as execinfo:
            camera.exposure(bad_exposure)
        assert 'Parameter out of range' in execinfo.value.message
        bad_exposure = random.randint(-100, 0)
        with pytest.raises(PySproutError) as execinfo:
            camera.exposure(bad_exposure)
        assert 'Parameter out of range' in execinfo.value.message

        # Test invalid values
        with pytest.raises(PySproutError) as execinfo:
            camera.exposure("bad")
        assert 'Invalid parameter' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.exposure({})
        assert 'Invalid parameter' in execinfo.value.message

        assert camera.exposure() == new_exposure

        # cameraMode and 'auto' parameters
        if camera_model == Devices.hirescamera:
            for mode in ['4416x3312', '1104x828', '2208x1656']:
                exposure = camera.exposure(mode)
                new_exposure = camera.default_config(mode)['exposure']
                assert exposure == new_exposure
                auto = camera.auto_exposure()
                assert auto is False

        new_exposure = 'auto'
        exposure = camera.exposure(new_exposure)
        assert exposure == new_exposure
        auto = camera.auto_exposure()
        assert auto is True

        # Set the original value back and confirm
        exposure = camera.exposure(orig_exposure)
        assert exposure == orig_exposure
        time.sleep(.5)
        assert camera.exposure() == orig_exposure
        auto = camera.auto_exposure(orig_auto)
        assert auto == orig_auto
        assert camera.auto_exposure() == orig_auto


def test_gain(get_camera):
    """
    Tests the hirescamera's gain method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    if camera_model == Devices.hirescamera_z_3d:
        min_gain = 0
        max_gain = 255
    else:
        min_gain = 0
        max_gain = 127

    with CameraStreaming(camera):
        auto = camera.auto_gain()
        assert isinstance(auto, bool)
        orig_gain = camera.gain()
        assert isinstance(orig_gain, int)
        assert min_gain <= orig_gain <= max_gain

        camera.auto_gain(True)
        assert camera.auto_gain() is True
        auto_gain = camera.auto_gain(False)
        assert auto_gain is False
        assert camera.auto_gain() is False

        new_gain = random.randint(min_gain, max_gain)
        gain = camera.gain(new_gain)
        assert gain == new_gain
        time.sleep(.5)  # Takes a few frames for the new gain to be set
        assert camera.gain() == new_gain

        # Ensure that setting a gain turns off auto gain
        auto_gain = camera.auto_gain(True)
        assert auto_gain is True
        assert camera.auto_gain() is True
        new_gain = random.randint(min_gain, max_gain)
        gain = camera.gain(new_gain)
        assert gain == new_gain
        time.sleep(.5)
        assert camera.gain() == new_gain
        assert camera.auto_gain() is False

        # Test the edge values
        new_gain = min_gain
        gain = camera.gain(new_gain)
        assert gain == new_gain
        time.sleep(.5)
        assert camera.gain() == new_gain
        new_gain = max_gain
        gain = camera.gain(new_gain)
        assert gain == new_gain
        time.sleep(.5)
        assert camera.gain() == new_gain

        # Ensure that out of range values throw errors
        with pytest.raises(PySproutError) as execinfo:
            camera.gain(-1)
        assert 'Parameter out of range' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.gain(max_gain+1)
        assert 'Parameter out of range' in execinfo.value.message
        bad_gain = random.randint(max_gain+1, max_gain+300)
        with pytest.raises(PySproutError) as execinfo:
            camera.gain(bad_gain)
        assert 'Parameter out of range' in execinfo.value.message
        bad_gain = random.randint(min_gain-300, min_gain-1)
        with pytest.raises(PySproutError) as execinfo:
            camera.gain(bad_gain)
        assert 'Parameter out of range' in execinfo.value.message

        # Test invalid values
        with pytest.raises(PySproutError) as execinfo:
            camera.gain("moo")
        assert 'Invalid parameter' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.gain({})
        assert 'Invalid parameter' in execinfo.value.message

        assert camera.gain() == new_gain

        # cameraMode and 'auto' parameters
        if camera_model == Devices.hirescamera:
            for mode in ['4416x3312', '1104x828', '2208x1656']:
                gain = camera.gain(mode)
                new_gain = camera.default_config(mode)['gain']
                assert gain == new_gain
                auto = camera.auto_gain()
                assert auto is False

        new_gain = 'auto'
        gain = camera.gain(new_gain)
        assert gain == new_gain
        auto = camera.auto_gain()
        assert auto is True

        # Set the original value back and confirm
        gain = camera.gain(orig_gain)
        assert gain == orig_gain
        time.sleep(.5)
        assert camera.gain() == orig_gain


def _validate_white_balance_dict(white_balance, min_wb, max_wb):
    """
    Takes in a white_balance object and validates that it's a dictionary with
    the correct parameters.
    """
    red = white_balance['red']
    green = white_balance['green']
    blue = white_balance['blue']
    assert isinstance(red, int)
    assert isinstance(green, int)
    assert isinstance(blue, int)
    assert min_wb <= red <= max_wb
    assert min_wb <= green <= max_wb
    assert min_wb <= blue <= max_wb


def test_white_balance(get_camera):
    """
    Tests the hirescamera's white_balance method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    if camera_model == Devices.hirescamera_z_3d:
        min_wb = 0
        max_wb = 2047
    else:
        min_wb = 1024
        max_wb = 4095

    with CameraStreaming(camera):
        auto = camera.auto_white_balance()
        assert isinstance(auto, bool)
        orig_white_balance = camera.white_balance()
        _validate_white_balance_dict(orig_white_balance, min_wb, max_wb)

        auto = camera.auto_white_balance(True)
        assert auto is True
        assert camera.auto_white_balance() is True
        auto = camera.auto_white_balance(False)
        assert auto is False
        assert camera.auto_white_balance() is False

        # Ensure that setting in range values does not throw an error
        new_white_balance = ({'red' : random.randint(min_wb, max_wb),
                              'green' : random.randint(min_wb, max_wb),
                              'blue' : random.randint(min_wb, max_wb)})
        white_balance = camera.white_balance(new_white_balance)
        assert white_balance == new_white_balance
        time.sleep(.75)  # Takes a few frames for the new white balance to be set
        assert camera.white_balance() == new_white_balance

        # Ensure that setting a white balance turns off auto white balance
        auto = camera.auto_white_balance(True)
        assert auto is True
        assert camera.auto_white_balance() is True
        new_white_balance = ({'red' : random.randint(min_wb, max_wb),
                              'green' : random.randint(min_wb, max_wb),
                              'blue' : random.randint(min_wb, max_wb)})
        white_balance = camera.white_balance(new_white_balance)
        assert white_balance == new_white_balance
        time.sleep(.75)
        assert camera.white_balance() == new_white_balance
        assert camera.auto_white_balance() is False

        # Test the edge cases
        new_white_balance = ({'red' : min_wb, 'green' : min_wb, 'blue' : min_wb})
        white_balance = camera.white_balance(new_white_balance)
        assert white_balance == new_white_balance
        time.sleep(.75)
        assert camera.white_balance() == new_white_balance
        new_white_balance = ({'red' : max_wb, 'green' : max_wb, 'blue' : max_wb})
        white_balance = camera.white_balance(new_white_balance)
        assert white_balance == new_white_balance
        time.sleep(.75)
        assert camera.white_balance() == new_white_balance

        # Ensure that out of range values throw errors
        # below the min
        bad_white_balance = ({'red' : min_wb-1,
                              'green' : random.randint(min_wb, max_wb),
                              'blue' : random.randint(min_wb, max_wb)})
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance(bad_white_balance)
        assert 'Parameter out of range' in execinfo.value.message
        bad_white_balance = ({'red' : random.randint(min_wb, max_wb),
                              'green' : min_wb-1,
                              'blue' : random.randint(min_wb, max_wb)})
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance(bad_white_balance)
        assert 'Parameter out of range' in execinfo.value.message
        bad_white_balance = ({'red' : random.randint(min_wb, max_wb),
                              'green' : random.randint(min_wb, max_wb),
                              'blue' : min_wb-1})
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance(bad_white_balance)
        assert 'Parameter out of range' in execinfo.value.message
        # Above the max
        bad_white_balance = ({'red' : max_wb+1,
                              'green' : random.randint(min_wb, max_wb),
                              'blue' : random.randint(min_wb, max_wb)})
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance(bad_white_balance)
        assert 'Parameter out of range' in execinfo.value.message
        bad_white_balance = ({'red' : random.randint(min_wb, max_wb),
                              'green' : max_wb+1,
                              'blue' : random.randint(min_wb, max_wb)})
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance(bad_white_balance)
        assert 'Parameter out of range' in execinfo.value.message
        bad_white_balance = ({'red' : random.randint(min_wb, max_wb),
                              'green' : random.randint(min_wb, max_wb),
                              'blue' : max_wb+1})
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance(bad_white_balance)
        assert 'Parameter out of range' in execinfo.value.message

        # Blue is a random value above the max
        bad_white_balance = ({'red' : random.randint(min_wb, max_wb),
                              'green' : random.randint(min_wb, max_wb),
                              'blue' : random.randint(max_wb+1, max_wb+1000)})
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance(bad_white_balance)
        assert 'Parameter out of range' in execinfo.value.message
        # Red is a random value below the min
        bad_white_balance = ({'red' : random.randint(min_wb-1000, min_wb-1),
                              'green' : random.randint(min_wb, max_wb),
                              'blue' : random.randint(min_wb, max_wb)})
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance(bad_white_balance)
        assert 'Parameter out of range' in execinfo.value.message

        # Test invalid values
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance("bad")
        assert 'Invalid parameter' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance({})
        assert 'Invalid parameter' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance({'fake': 2000})
        assert 'Invalid parameter' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance(15)
        assert 'Invalid parameter' in execinfo.value.message

        # Verify the bad/invalid parameters didn't change the setting
        assert camera.white_balance() == new_white_balance

        # cameraMode and 'auto' parameters
        if camera_model == Devices.hirescamera:
            for mode in ['4416x3312', '1104x828', '2208x1656']:
                white_bal = camera.white_balance(mode)
                new_wb = camera.default_config(mode)['white_balance']
                assert white_bal == new_wb
                auto = camera.auto_white_balance()
                assert auto is False

        new_wb = 'auto'
        white_bal = camera.white_balance(new_wb)
        assert white_bal == new_wb
        auto = camera.auto_white_balance()
        assert auto is True

        # Set the original value back and confirm
        white_balance = camera.white_balance(orig_white_balance)
        assert white_balance == orig_white_balance
        time.sleep(.75)
        assert camera.white_balance() == orig_white_balance


def test_white_balance_temperature(get_camera):
    """
    Tests the hirescamera's white_balance_temperature method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    if camera_model != Devices.hirescamera_z_3d:
        with pytest.raises(PySproutError) as execinfo:
            camera.white_balance_temperature()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    min_temp = 25
    max_temp = 125
    temp = random.randint(min_temp, max_temp)
    set_temp = camera.white_balance_temperature(temp)
    assert isinstance(set_temp, int)
    assert set_temp == temp
    assert temp == camera.white_balance_temperature()

    # Edge cases
    set_temp = camera.white_balance_temperature(min_temp)
    assert set_temp == min_temp
    assert min_temp == camera.white_balance_temperature()
    set_temp = camera.white_balance_temperature(max_temp)
    assert set_temp == max_temp
    assert max_temp == camera.white_balance_temperature()

    # Put the camera in auto white balance, ensure that query throws the
    # expected error, and then ensure that setting a temp turns off auto.
    auto = camera.auto_white_balance(True)
    assert auto is True
    assert camera.auto_white_balance() is True
    with pytest.raises(PySproutError) as execinfo:
        camera.white_balance_temperature()
    assert 'Device is in the wrong state' in execinfo.value.message
    temp = 75
    set_temp = camera.white_balance_temperature(temp)
    assert isinstance(set_temp, int)
    assert set_temp == temp
    assert temp == camera.white_balance_temperature()
    auto = camera.auto_white_balance(False)
    assert auto is False
    assert camera.auto_white_balance() is False

    # Check that we get the expected error if we query temp when in RGB mode.
    rgb = {'red': 1050, 'green': 1070, 'blue': 2000}
    white_bal = camera.white_balance(rgb)
    assert white_bal == rgb
    with pytest.raises(PySproutError) as execinfo:
        camera.white_balance_temperature()
    assert 'Device is in the wrong state' in execinfo.value.message

    # Verify out of range values don't change the current setting
    test = 42
    set_temp = camera.white_balance_temperature(test)
    assert set_temp == test
    with pytest.raises(PySproutError) as execinfo:
        set_temp = camera.white_balance_temperature(min_temp-1)
    assert 'Parameter out of range' in execinfo.value.message
    assert test == camera.white_balance_temperature()
    with pytest.raises(PySproutError) as execinfo:
        set_temp = camera.white_balance_temperature(max_temp+1)
    assert 'Parameter out of range' in execinfo.value.message
    assert test == camera.white_balance_temperature()
    too_low = random.randint(min_temp-500, min_temp-2)
    with pytest.raises(PySproutError) as execinfo:
        set_temp = camera.white_balance_temperature(too_low)
    assert 'Parameter out of range' in execinfo.value.message
    assert test == camera.white_balance_temperature()
    too_high = random.randint(max_temp+2, max_temp+500)
    with pytest.raises(PySproutError) as execinfo:
        set_temp = camera.white_balance_temperature(too_high)
    assert 'Parameter out of range' in execinfo.value.message
    assert test == camera.white_balance_temperature()

    # invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        camera.white_balance_temperature(33.5)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.white_balance_temperature({'white_balance_temperature': 36})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.white_balance_temperature("temperatures")
    assert 'Invalid parameter' in execinfo.value.message


def test_default_config(get_camera):
    """
    Tests the hirescamera's default_config method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    if camera_model == Devices.hirescamera_z_3d:
        with pytest.raises(PySproutError) as execinfo:
            camera.default_config('4416x3312')
        assert 'Functionality not available.' in str(execinfo.value)
        return

    for mode in HiResCamera.Mode:
        config = camera.default_config(mode)
        assert isinstance(config['mode'], HiResCamera.Mode)
        assert isinstance(config['mode'].value, str)
        assert config['mode'] == mode
        assert isinstance(config['exposure'], int)
        assert 1 <= config['exposure'] <= 3385
        assert isinstance(config['fps'], int)
        assert isinstance(config['gain'], int)
        assert 0 <= config['gain'] <= 127
        _validate_white_balance_dict(config['white_balance'], 1024, 4095)

    # Validate it works if we just pass in the strings instead of the enum
    for mode in ['4416x3312', '1104x828', '2208x1656']:
        config = camera.default_config(mode)
        assert isinstance(config['mode'], HiResCamera.Mode)
        assert config['mode'].value == mode
        assert isinstance(config['exposure'], int)
        assert 1 <= config['exposure'] <= 3385
        assert isinstance(config['fps'], int)
        assert isinstance(config['gain'], int)
        assert 0 <= config['gain'] <= 127
        _validate_white_balance_dict(config['white_balance'], 1024, 4095)

    with pytest.raises(ValueError):
        camera.default_config('1105x828')
    with pytest.raises(ValueError):
        camera.default_config('fake')
    with pytest.raises(ValueError):
        camera.default_config({})
    with pytest.raises(ValueError):
        camera.default_config(3)

def test_flip_frame(get_camera):
    """
    Tests the hirescamera's flip_frame method.
    """
    camera = get_camera

    orig_flipped = camera.flip_frame()
    assert isinstance(orig_flipped, bool)

    flipped = camera.flip_frame(True)
    assert flipped is True
    assert camera.flip_frame() is True
    flipped = camera.flip_frame(False)
    assert flipped is False
    assert camera.flip_frame() is False

    # Test sending in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        camera.flip_frame("abc")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.flip_frame(1)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.flip_frame({})
    assert 'Invalid parameter' in execinfo.value.message

    # Set the original value back and confirm
    flipped = camera.flip_frame(orig_flipped)
    assert flipped == orig_flipped
    assert camera.flip_frame() == orig_flipped


def test_gamma_correction(get_camera):
    """
    Tests the hirescamera's gamma_correction method.
    """
    camera = get_camera

    orig_gamma = camera.gamma_correction()
    assert isinstance(orig_gamma, bool)

    gamma = camera.gamma_correction(True)
    assert gamma is True
    assert camera.gamma_correction() is True
    gamma = camera.gamma_correction(False)
    assert gamma is False
    assert camera.gamma_correction() is False

    # Test sending in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        camera.gamma_correction("test")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.gamma_correction(0)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.gamma_correction({})
    assert 'Invalid parameter' in execinfo.value.message

    # Set the original value back and confirm
    gamma = camera.gamma_correction(orig_gamma)
    assert gamma == orig_gamma
    assert camera.gamma_correction() == orig_gamma


def test_lens_color_shading(get_camera):
    """
    Tests the hirescamera's lens_color_shading method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    if camera_model == Devices.hirescamera_z_3d:
        with pytest.raises(PySproutError) as execinfo:
            camera.lens_color_shading()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    orig_shading = camera.lens_color_shading()
    assert isinstance(orig_shading, bool)

    shading = camera.lens_color_shading(True)
    assert shading is True
    assert camera.lens_color_shading() is True
    shading = camera.lens_color_shading(False)
    assert shading is False
    assert camera.lens_color_shading() is False

    # Test sending in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        camera.lens_color_shading("bad")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.lens_color_shading(25)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.lens_color_shading({})
    assert 'Invalid parameter' in execinfo.value.message

    # Set the original value back and confirm
    shading = camera.lens_color_shading(orig_shading)
    assert shading == orig_shading
    assert camera.lens_color_shading() == orig_shading


def test_lens_shading(get_camera):
    """
    Tests the hirescamera's lens_shading method.
    """
    camera = get_camera

    orig_shading = camera.lens_shading()
    assert isinstance(orig_shading, bool)

    shading = camera.lens_shading(True)
    assert shading is True
    assert camera.lens_shading() is True
    shading = camera.lens_shading(False)
    assert shading is False
    assert camera.lens_shading() is False

    # Test sending in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        camera.lens_shading("moo")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.lens_shading(-5)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.lens_shading({})
    assert 'Invalid parameter' in execinfo.value.message

    # Set the original value back and confirm
    shading = camera.lens_shading(orig_shading)
    assert shading == orig_shading
    assert camera.lens_shading() == orig_shading


def test_mirror_frame(get_camera):
    """
    Tests the hirescamera's mirror_frame method.
    """
    camera = get_camera

    orig_mirror = camera.mirror_frame()
    assert isinstance(orig_mirror, bool)

    mirror = camera.mirror_frame(True)
    assert mirror is True
    assert camera.mirror_frame() is True
    mirror = camera.mirror_frame(False)
    assert mirror is False
    assert camera.mirror_frame() is False

    # Test sending in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        camera.mirror_frame("fake")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.mirror_frame(15)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.mirror_frame({})
    assert 'Invalid parameter' in execinfo.value.message

    # Set the original value back and confirm
    mirror = camera.mirror_frame(orig_mirror)
    assert mirror == orig_mirror
    assert camera.mirror_frame() == orig_mirror


def test_factory_default(get_camera):
    """
    Tests the hirescamera's factory_default method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    camera.factory_default()
    assert camera.auto_gain() is True
    assert camera.auto_exposure() is True
    assert camera.auto_white_balance() is True
    if camera_model == Devices.hirescamera:
        assert camera.lens_color_shading() is False
        assert camera.gamma_correction() is False
        assert camera.flip_frame() is False
        assert camera.lens_shading() is False
    else:
        assert camera.gamma_correction() is True
        assert camera.flip_frame() is True
        assert camera.lens_shading() is True
    assert camera.mirror_frame() is False

    # EB TODO update this method to check the flick keystone tables


def test_strobe(get_camera):
    """
    Tests the hirescamera's strobe method.
    """
    camera = get_camera

    frames = random.randint(1, 254)
    gain = random.randint(0, 127)
    exposure = random.randint(1, 3385)
    fps = 60

    with CameraStreaming(camera):
        camera.strobe(frames, gain, exposure)
        time.sleep(math.ceil((1.*frames)/fps))
        # Test edge cases
        frames = 1
        camera.strobe(frames, 0, 1)
        time.sleep(math.ceil((1.*frames)/fps))
        frames = 254
        camera.strobe(frames, 127, 3385)
        time.sleep(math.ceil((1.*frames)/fps))

        frames = random.randint(1, 254)
        #Verify out of range gain values throw errors
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(frames, -1, exposure)
        assert 'Parameter out of range' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(frames, 128, exposure)
        assert 'Parameter out of range' in execinfo.value.message
        bad_gain = random.randint(-100, -1)
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(frames, bad_gain, exposure)
        assert 'Parameter out of range' in execinfo.value.message
        bad_gain = random.randint(128, 500)
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(frames, bad_gain, exposure)
        assert 'Parameter out of range' in execinfo.value.message

        #Verify out of range exposure values throw errors
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(frames, gain, 0)
        assert 'Parameter out of range' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(frames, gain, 3386)
        assert 'Parameter out of range' in execinfo.value.message
        bad_exp = random.randint(-100, 0)
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(frames, gain, bad_exp)
        assert 'Parameter out of range' in execinfo.value.message
        bad_exp = random.randint(3385, 4096)
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(frames, gain, bad_exp)
        assert 'Parameter out of range' in execinfo.value.message

        #Verify out of range frames values throw errors
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(0, gain, exposure)
        assert 'Parameter out of range' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(256, gain, exposure)
        assert 'Parameter out of range' in execinfo.value.message
        bad_frames = random.randint(-100, 0)
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(bad_frames, gain, exposure)
        assert 'Parameter out of range' in execinfo.value.message
        bad_frames = random.randint(3385, 4096)
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(bad_frames, gain, exposure)
        assert 'Parameter out of range' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe(255, gain, exposure)
        assert 'Parameter out of range' in execinfo.value.message

        # Test sending in invalid parameters
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe("fake", "bad", "test")
        assert 'Invalid parameter' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.strobe({}, {}, {})
        assert 'Invalid parameter' in execinfo.value.message


def test_temperatures(get_camera):
    """
    Tests the hirescamera's temperatures method.
    """
    camera = get_camera

    temperatures = camera.temperatures()
    camera_info = camera.info()
    check_system_types.check_TemperatureInfoList(temperatures, [camera_info])


def test_led_state(get_camera):
    """
    Tests the hirescamera's led_state method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.led_state()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    # Store original value
    state = camera.led_state()
    assert isinstance(state['capture'], HiResCamera.LEDState)
    assert isinstance(state['streaming'], HiResCamera.LEDState)
    assert isinstance(state['capture'].value, str)
    assert isinstance(state['streaming'].value, str)

    cur_state = {'capture': HiResCamera.LEDState.off,
                 'streaming': HiResCamera.LEDState.low}
    set_state = camera.led_state(cur_state)
    assert set_state == cur_state
    assert camera.led_state() == cur_state

    # Test all of the possible values
    for capture_state in HiResCamera.LEDState:
        for streaming_state in [HiResCamera.LEDState.off,
                                HiResCamera.LEDState.low]:
            new_state = {'capture': capture_state, 'streaming': streaming_state}
            set_state = camera.led_state(new_state)
            assert set_state == new_state
            assert camera.led_state() == new_state
        for streaming_state in [HiResCamera.LEDState.high,
                                HiResCamera.LEDState.auto]:
            new_state = {'capture': capture_state, 'streaming': streaming_state}
            with pytest.raises(PySproutError) as execinfo:
                camera.led_state(new_state)
            assert 'Invalid parameter' in execinfo.value.message

    # Test setting by the name rather than the enum
    for capture_state in ['off', 'low', 'high', 'auto']:
        for streaming_state in ['off', 'low']:
            new_state = {'capture': capture_state, 'streaming': streaming_state}
            set_state = camera.led_state(new_state)
            assert set_state['capture'].value == new_state['capture']
            assert set_state['streaming'].value == new_state['streaming']
            assert camera.led_state() == set_state
        # Streaming mode only alows the 'off' and 'low' parameters. Verify we
        # throw an error for the other two values
        for streaming_state in ['high', 'auto']:
            new_state = {'capture': capture_state, 'streaming': streaming_state}
            with pytest.raises(PySproutError) as execinfo:
                camera.led_state(new_state)
            assert 'Invalid parameter' in execinfo.value.message

    # Verify invalid parameters throw the proper errors
    with pytest.raises(PySproutError) as execinfo:
        camera.led_state('moo')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.led_state({'fake_key': HiResCamera.LEDState.off})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        new_state = camera.led_state({})
    assert 'Invalid parameter' in execinfo.value.message

    with pytest.raises(TypeError):
        camera.led_state(33)
    with pytest.raises(ValueError):
        camera.led_state({'capture': 'fake_value', 'streaming': 'off'})
    with pytest.raises(ValueError):
        camera.led_state({'capture': 'off', 'streaming': 'bad'})

    # Send bad values to SoHal (bypassing the hippy enum check) and make
    # sure SoHal throws an error...
    with pytest.raises(PySproutError) as execinfo:
        camera._send_msg('led_state', 33) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera._send_msg('led_state', 33) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera._send_msg('led_state', {'capture': 'off', 'streaming': 'moo'}) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message

    # Set the original value back
    set_state = camera.led_state(state)
    assert set_state == state
    assert camera.led_state() == state


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


def test_notifications(get_camera):
    """
    This method tests the camera.on_*** notifications received from SoHal.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    resolutions = camera.available_resolutions()
    streams = [HiResCamera.ImageStream.color]

    val = camera.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    name = camera._object_name
    # Notifications are never sent as '@0' even if we sent the command with @0
    if '@0' in name:
        name = 'hirescamera'

    # TODO(EB) We'll need a manual test for on_suspend and on_resume

    camera.close()
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 0)
    notification = get_notification()
    assert notification == ('{}.on_close'.format(name), None)
    camera.open()
    notification = get_notification()
    assert notification == ('{}.on_open'.format(name), None)
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 1)

    streams = [HiResCamera.ImageStream.color]
    with CameraStreaming(camera, streams=streams):
        notification = get_notification()
        assert notification == ('{}.on_enable_streams'.format(name), streams)

        camera.exposure(300)
        notification = get_notification()
        assert notification == ('{}.on_exposure'.format(name), 300)
        camera.auto_exposure(True)
        notification = get_notification()
        assert notification == ('{}.on_exposure'.format(name), 'auto')

        camera.gain(20)
        notification = get_notification()
        assert notification == ('{}.on_gain'.format(name), 20)
        camera.auto_gain(True)
        notification = get_notification()
        assert notification == ('{}.on_gain'.format(name), 'auto')

        white_balance = ({'red' : 1548, 'green' : 1024, 'blue' : 1574})
        camera.white_balance(white_balance)
        notification = get_notification()
        assert notification == ('{}.on_white_balance'.format(name), white_balance)
        camera.auto_white_balance(True)
        notification = get_notification()
        assert notification == ('{}.on_white_balance'.format(name), 'auto')

        camera.flip_frame(True)
        notification = get_notification()
        assert notification == ('{}.on_flip_frame'.format(name), True)

        camera.gamma_correction(True)
        notification = get_notification()
        assert notification == ('{}.on_gamma_correction'.format(name), True)

        strobe = {'frames': 10, 'gain': 12, 'exposure': 800}
        camera.strobe(**strobe)
        notification = get_notification()
        assert notification == ('{}.on_strobe'.format(name), strobe)
        fps = 60
        time.sleep(math.ceil((1.*strobe['frames'])/fps))
    notification = get_notification()
    assert notification == ('{}.on_disable_streams'.format(name), [])

    if camera_model == Devices.hirescamera:
        camera.lens_color_shading(True)
        notification = get_notification()
        assert notification == ('{}.on_lens_color_shading'.format(name), True)

    camera.lens_shading(True)
    notification = get_notification()
    assert notification == ('{}.on_lens_shading'.format(name), True)

    camera.mirror_frame(True)
    notification = get_notification()
    assert notification == ('{}.on_mirror_frame'.format(name), True)

    if camera_model == Devices.hirescamera_z_3d:
        camera.brightness(100)
        notification = get_notification()
        assert notification == ('{}.on_brightness'.format(name), 100)

        camera.contrast(5)
        notification = get_notification()
        assert notification == ('{}.on_contrast'.format(name), 5)

        camera.saturation(40)
        notification = get_notification()
        assert notification == ('{}.on_saturation'.format(name), 40)

        camera.sharpness(2)
        notification = get_notification()
        assert notification == ('{}.on_sharpness'.format(name), 2)

        camera.power_line_frequency(50)
        notification = get_notification()
        assert notification == ('{}.on_power_line_frequency'.format(name), 50)

    camera.factory_default()
    notification = get_notification()
    assert notification == ('{}.on_factory_default'.format(name), None)

    isp = {
        'exposure' : 'auto',
        'gain' : 10,
        'white_balance': {'red': 1733, 'green': 1024, 'blue': 1926},#'1104x828',
        'flip_frame' : True,
        'gamma_correction' : True,
        'lens_shading' : True,
        'lens_color_shading' : False,
        'mirror_frame' : True,
    }
    if camera_model == Devices.hirescamera:
        isp['lens_color_shading'] = True
        isp['white_balance'] = '1104x828'
    camera.camera_settings(isp)
    notifications = []
    for dummy in range(len(isp)):
        notifications.append(get_notification()[0])
    assert notifications.count('{}.on_exposure'.format(name)) == 1
    assert notifications.count('{}.on_gain'.format(name)) == 1
    assert notifications.count('{}.on_white_balance'.format(name)) == 1
    assert notifications.count('{}.on_flip_frame'.format(name)) == 1
    assert notifications.count('{}.on_gamma_correction'.format(name)) == 1
    assert notifications.count('{}.on_lens_color_shading'.format(name)) == 1
    assert notifications.count('{}.on_lens_shading'.format(name)) == 1
    assert notifications.count('{}.on_mirror_frame'.format(name)) == 1

    notifications = []
    camera.camera_settings({'gain':'auto'})
    for dummy in range(1):
        notifications.append(get_notification()[0])
    assert notifications.count('{}.on_gain'.format(name)) == 1


    if camera_model == Devices.hirescamera_z_3d:
        # EB TODO still need a camera.keystone() test here

        types = ['default', 'flash_max_fov', 'flash_fit_to_mat']
        for table_type in types:
            camera.keystone_table(table_type)
            notification = get_notification()
            assert notification == ('{}.on_keystone_table'.format(name),
                                    table_type)

        # Can't set entries in the 'default' table, so remove it from the
        # list for this next test
        types.remove('default')
        x = 1
        y = 1
        for table_type in types:
            keys = []
            for res in resolutions:
                resolution = {'width': res['width'], 'height': res['height'],
                              'fps': res['fps']}
                key = {'enabled' : True,
                       'resolution' : resolution,
                       'value' : {'top_left' : {'x':x, 'y':y},
                                  'top_right' :  {'x':-x, 'y':y},
                                  'bottom_left' :  {'x':x, 'y':-y},
                                  'bottom_right' :  {'x':-x, 'y':-y}}}
                keys.append(key)
            camera.keystone_table_entries(table_type, keys)
            notification = get_notification()
            assert notification[0] == ('{}.on_keystone_table_entries'.
                                       format(name))
            assert set(notification[1]) == set(('type', 'entries'))
            # assert sorted(notification[1]['entries']) == sorted(keys)
            assert len(keys) == len(notification[1]['entries'])
            assert all(keys.count(i) == notification[1]['entries'].count(i)
                       for i in keys)
                # {'type': table_type, 'entries':keys})
            # assert notification[0] ==
            x += 1
            y += 1

    if camera_model == Devices.hirescamera_z_3d:
        camera.reset()
        expected = [('{}.on_reset'.format(name), None),
                    ('{}.on_device_disconnected'.format(name), None),
                    ('{}.on_device_connected'.format(name), None)]
        for dummy in range(len(expected)):
            notification = get_notification()
            assert notification in expected
            expected.remove(notification)
        # Keep in mind that the camera is closed now!

    val = camera.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Now make sure we aren't getting notification callbacks anymore...
    camera.open()
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]
    camera.factory_default()
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    # Verify hippy raises errors if we call subscribe with invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        camera.subscribe('string')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.subscribe(camera)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.subscribe({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.subscribe(3)
    assert 'Invalid parameter' in execinfo.value.message


def test_camera_settings(get_camera):
    """
    Tests the hirescamera's camera_settings method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    isp = {'exposure' : 128,   # 'auto',
           'gain' : 'auto',   # '4416x3312',   # 'auto',
           'white_balance' : 'auto', #'1104x828', #'4416x3312',
           'flip_frame' : True,
           'gamma_correction' : True,
           'lens_shading' : True,
           'lens_color_shading' : False,
           'mirror_frame' : True,
          }
    if camera_model == Devices.hirescamera:
        isp['white_balance'] = '1104x828'

    ret = camera.camera_settings()
    for k in isp:
        assert k in ret
    ret = camera.camera_settings(isp)
    for k in isp:
        assert k in ret
    isp2 = {'exposure': 'auto'}
    ret = camera.camera_settings(isp2)
    for k in isp:
        assert k in ret
    isp3 = {'exposure': 'auto_off',
            'gain': 'auto_off',
            'white_balance': 'auto_off'}
    ret = camera.camera_settings(isp3)
    for k in isp:
        assert k in ret

    if camera_model == Devices.hirescamera_z_3d:
        with pytest.raises(PySproutError) as execinfo:
            camera.camera_settings({'lens_color_shading': True})
        assert 'functionality not available' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.camera_settings({'white_balance': '1104x828'})
        assert 'Invalid parameter' in execinfo.value.message

    with pytest.raises(PySproutError) as execinfo:
        camera.camera_settings('bad')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.camera_settings(7)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.camera_settings({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.camera_settings({'fake': True})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.camera_settings({'lens_color_shading': 7})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.camera_settings({'exposure': "manual"})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.camera_settings({'gain': "manual_gain"})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.camera_settings({'white_balance': "manual_wb"})
    assert 'Invalid parameter' in execinfo.value.message

# function that enables the camera's stream and reads frames
# continuously until asked to stop
def stream_frames(camera, resolution, streams, need_to_stop, streaming):
    asyncio.set_event_loop(asyncio.new_event_loop())
    print('Initializing', camera, resolution)
    if resolution:
        camera.streaming_resolution(resolution)
    # print('ready!')
    camera.enable_streams(streams)
    streaming.set()
    while not need_to_stop.is_set():
        frame = camera.grab_frame(streams)
    #     print('stream_frames', frame['index'])
    camera.disable_streams(streams)
    # print('exiting thread')


# EB maybe this class should go in the main hippy object directly???
class CameraStreaming:
    """
    A class that implements the functions to be used as a context manager 'with'
    """
    def __init__(self, camera, resolution=None,
                 streams=[HiResCamera.ImageStream.color]):
        # print('** 1', camera, resolution)
        streaming_flag = False
        camera_model = check_device_types.get_device_model(camera)
        if camera_model == Devices.hirescamera_z_3d:
            try:
                camera.streaming_resolution()
                streaming_flag = True
            except PySproutError:
                streaming_flag = False
        else:
            if camera.exposure() != 65535:
                streaming_flag = True
            else:
                streaming_flag = False
        assert not streaming_flag, "The camera is already streaming."

        self._need_to_stop = threading.Event()
        self._streaming = threading.Event()
        self._th = threading.Thread(target=stream_frames,
                                    args=(camera, resolution, streams,
                                          self._need_to_stop,
                                          self._streaming))

    def __enter__(self):
        # print('entering')
        self._th.start()
        while not self._streaming.is_set():
            # print('Not yet')
            time.sleep(0.1)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        # print('exiting', exception_type, exception_value)
        self._need_to_stop.set()
        self._th.join()
        # print('Finished')


def test_keystone(get_camera):
    """
    Tests the hirescamera's keystone method.
    """

    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    zeros = {'value' : {'top_left': {'x': 0, 'y': 0},
                        'top_right':  {'x': 0, 'y': 0},
                        'bottom_left':  {'x': 0, 'y': 0},
                        'bottom_right':  {'x': 0, 'y': 0}},
             'enabled': True}

    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone()
        assert 'Functionality not available.' in str(execinfo.value)
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone(zeros)
        assert 'Functionality not available.' in str(execinfo.value)
        return

    resolutions = camera.available_resolutions()
    for resolution in resolutions:
        time.sleep(1.5)
        with CameraStreaming(camera, resolution):
            time.sleep(5)
            print("Resolution is {}".format(resolution))
            # we can call the APIs that require streaming here
            # first we get the parent resolution of the current streaming mode
            parent_resolution = camera.parent_resolution()
            # this creates a centered zoom effect from 0 to 90% in 15% steps
            for i in range(0, 46, 15):
                x = i*parent_resolution['width']//100
                y = i*parent_resolution['height']//100
                key = {'enabled' : True,
                       'value' : {'top_left' : {'x':x, 'y':y},
                                  'top_right' :  {'x':-x, 'y':y},
                                  'bottom_left' :  {'x':x, 'y':-y},
                                  'bottom_right' :  {'x':-x, 'y':-y}}}
                new_key = camera.keystone(key)
                check_hirescamera_types.check_CameraKeystone(new_key)
                assert camera.keystone() == new_key
                assert new_key == key
                time.sleep(0.050)
                time.sleep(5)

            # Test invalid resolutions throw errors
            for item in parent_resolution:
                # Test the current resolution but missing one item
                invalid_res = copy.deepcopy(parent_resolution)
                invalid_res.pop(item)
                with pytest.raises(PySproutError) as execinfo:
                    camera.keystone({'resolution': invalid_res})
                assert ("Unexpected item found 'resolution'" in
                        execinfo.value.message)

            # Test sending in non-convex quadrilaterals and validate the errors
            half_width = parent_resolution['width']//2
            half_height = parent_resolution['height']//2
            errors = ['Invalid parameter', 'not a convex quadrilateral']
            # Top left x > top right x
            bad_top = copy.deepcopy(zeros)
            bad_top['value']['top_left']['x'] = half_width + 1
            bad_top['value']['top_right']['x'] = 1 - half_width
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone(bad_top)
            err_strings = errors + ['top_left.x', 'top_right.x', 'width']
            for item in err_strings:
                assert item in execinfo.value.message
            # Bottom left x > Bottom right x
            bad_bottom = copy.deepcopy(zeros)
            bad_bottom['value']['bottom_left']['x'] = half_width + 1
            bad_bottom['value']['bottom_right']['x'] = 1 - half_width
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone(bad_bottom)
            err_strings = errors + ['bottom_left.x', 'bottom_right.x', 'width']
            for item in err_strings:
                assert item in execinfo.value.message
            # Top left y > Bottom left y
            bad_left = copy.deepcopy(zeros)
            bad_left['value']['top_left']['y'] = half_height + 1
            bad_left['value']['bottom_left']['y'] = 1 - half_height
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone(bad_left)
            err_strings = errors + ['top_left.y', 'bottom_left.y', 'height']
            for item in err_strings:
                assert item in execinfo.value.message
            # Top right y > Bottom right y
            bad_right = copy.deepcopy(zeros)
            bad_right['value']['top_right']['y'] = half_height + 1
            bad_right['value']['bottom_right']['y'] = 1 - half_height
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone(bad_right)
            err_strings = errors + ['top_right.y', 'bottom_right.y', 'height']
            for item in err_strings:
                assert item in execinfo.value.message

    # Now test various bad parameters (only need to test these once, so don't
    # need to combine into the above loop)
    with CameraStreaming(camera):
        time.sleep(0.5)
        # Verify invalid parameters throw errors
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone('invalid')
        assert 'Invalid parameter' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone(23)
        assert 'Invalid parameter' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({"fake": 32})
        assert 'Invalid parameter' in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({})
        assert 'Invalid parameter' in execinfo.value.message
        # Test 'type' key
        for table in ['default', 'ram', 'flash_max_fov', 'flash_fit_to_mat']:
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone({'type': table})
            assert "Unexpected item found 'type'" in execinfo.value.message
        # Test 'resolution' key
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'resolution': {}})
        assert "Unexpected item found 'resolution'" in execinfo.value.message
        # Test invalid 'value'
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': 33})
        assert "Invalid parameter 'value'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': 'cat'})
        assert "Invalid parameter 'value'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': {}})
        assert "Invalid parameter 'value'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': {'bad':0, 'top_left':{'x':0, 'y':0}}})
        assert "Invalid parameter 'value'" in execinfo.value.message
        assert "Unexpected item found 'bad'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': {'top_left':45}})
        assert "Invalid parameter 'value.top_left'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': {'top_left':'x'}})
        assert "Invalid parameter 'value.top_left'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': {'top_left':{}}})
        assert "Invalid parameter 'value.top_left'" in execinfo.value.message
        assert "Missing items ['x', 'y']" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': {'top_left':{'x':0, 'y':0, 'boo':0}}})
        assert "Invalid parameter 'value.top_left'" in execinfo.value.message
        assert "Unexpected item found 'boo'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': {'top_left':{'x':0}}})
        assert "Invalid parameter 'value.top_left'" in execinfo.value.message
        assert "Missing item 'y'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': {'top_left':{'x':0, 'y':{}}}})
        assert "Invalid parameter 'value.top_left.y'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'value': {'top_left':{'x':0, 'y':'pickles'}}})
        assert "Invalid parameter 'value.top_left.y'" in execinfo.value.message
        # Test invalid 'enabled' values
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'enabled': 7})
        assert "Invalid parameter 'enabled'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'enabled': {'test': 64}})
        assert "Invalid parameter 'enabled'" in execinfo.value.message
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone({'enabled': 'enabled'})
        assert "Invalid parameter 'enabled'" in execinfo.value.message

    # Verify we get the expected error if the camera isn't streaming
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone()
    assert 'The camera is not streaming' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone(
            {'enabled' : True,
             'value' : {'top_left' : {'x':0, 'y':0},
                        'top_right' :  {'x':0, 'y':0},
                        'bottom_left' :  {'x':0, 'y':0},
                        'bottom_right' :  {'x':0, 'y':0}}})
    assert 'The camera is not streaming' in str(execinfo.value)


def test_keystone_table_entries(get_camera):
    """
    Tests the hirescamera's keystone_table_entries method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)

    types = ['default', 'ram', 'flash_max_fov', 'flash_fit_to_mat']

    if camera_model == Devices.hirescamera:
        for table in types:
            # 'get' all entries
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone_table_entries(table)
            assert 'Functionality not available.' in str(execinfo.value)
            # 'get' specific entries
            res1 = {'width': 640, 'height': 480, 'fps': 60}
            res2 = {'width': 4352, 'height': 3264, 'fps': 6}
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone_table_entries(table, [res1, res2])
            assert 'Functionality not available.' in str(execinfo.value)
            # 'set' entries
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone_table_entries(
                    table,
                    [{'resolution': res1,
                      'enabled' : True,
                      'value' : {'top_left' : {'x':0, 'y':0},
                                 'top_right' :  {'x':0, 'y':0},
                                 'bottom_left' :  {'x':0, 'y':0},
                                 'bottom_right' :  {'x':0, 'y':0}}},
                     {'resolution': res2,
                      'enabled' : True,
                      'value' : {'top_left' : {'x':1, 'y':1},
                                 'top_right' :  {'x':-1, 'y':1},
                                 'bottom_left' :  {'x':1, 'y':-1},
                                 'bottom_right' :  {'x':-1, 'y':-1}}}])
            assert 'Functionality not available.' in str(execinfo.value)
        return

    supported_resolutions = []
    for res in Resolution:
        width, height, fps = tuple(map(lambda x: int(x),
                                       res.name.split('_')[1:]))
        supported_resolutions.append({'width': width, 'height': height,
                                      'fps': fps})

    for table in types:
        # Get current values for all resolutions
        table_entries = camera.keystone_table_entries(table)
        check_hirescamera_types.check_CameraKeystoneTableEntries(
            table_entries, table)
        requested = copy.deepcopy(supported_resolutions)
        for entry in table_entries['entries']:
            requested.remove(entry['resolution'])
        assert len(requested) == 0

        # Get current values for one resolution at a time
        for res in supported_resolutions:
            requested = [res]
            table_entries = camera.keystone_table_entries(table, requested)
            check_hirescamera_types.check_CameraKeystoneTableEntries(
                table_entries, table)
            for entry in table_entries['entries']:
                requested.remove(entry['resolution'])
            assert len(requested) == 0

        # Get current values for more than one resolution at once.
        # Test this by sending a random number of random items off of the
        # list of supported_resolutions
        max_len = len(supported_resolutions)
        requested = random.sample(
            list(supported_resolutions[i] for i in range(0, max_len)),
            random.randint(1, max_len))
        table_entries = camera.keystone_table_entries(table, requested)
        check_hirescamera_types.check_CameraKeystoneTableEntries(
            table_entries, table)
        for entry in table_entries['entries']:
            requested.remove(entry['resolution'])
        assert len(requested) == 0

        # Test setting values one at a time
        for resolution in supported_resolutions:
            # Use this index to make sure the values change for each table so
            # we are sure we aren't just matching with data for another table
            # and thinking everything is working
            index = types.index(table)
            x = width//(3 + index)
            y = height//(3 + index)
            key = [{'resolution': resolution,
                    'value' : {'top_left' : {'x':x, 'y':y},
                               'top_right' :  {'x':-x, 'y':y},
                               'bottom_left' :  {'x':x, 'y':-y},
                               'bottom_right' :  {'x':-x, 'y':-y}},
                    'enabled': True}]

            if table == 'default':
                # Make sure we can't set values in the default table
                err_msg = "Setting 'default' keystone table is not supported"
                with pytest.raises(PySproutError) as execinfo:
                    camera.keystone_table_entries(table, key)
                assert err_msg == execinfo.value.message
            else:
                keystone = camera.keystone_table_entries(table, key)
                check_hirescamera_types.check_CameraKeystoneTableEntries(
                    keystone, table)
                assert keystone['entries'] == key
                new_key = camera.keystone_table_entries(table, [resolution])
                check_hirescamera_types.check_CameraKeystoneTableEntries(
                    new_key, table)
                assert new_key['entries'] == key

        # Set current values for more than one resolution at once.
        # Test this by sending a random number of random items off of the
        # list of supported_resolutions
        if table != 'default':
            max_len = len(supported_resolutions)
            requested = random.sample(
                list(supported_resolutions[i] for i in range(0, max_len)),
                random.randint(1, max_len))
            to_set = []
            x = 0
            y = 0
            for res in requested:
                to_set.append({'enabled': True,
                               'resolution': res,
                               'value': {'top_left' : {'x':x, 'y':y},
                                         'top_right' :  {'x':-x, 'y':y},
                                         'bottom_left' :  {'x':x, 'y':-y},
                                         'bottom_right' :  {'x':-x, 'y':-y}}})
                x = x + 1
                y = y + 1
            table_entries = camera.keystone_table_entries(table, to_set)
            check_hirescamera_types.check_CameraKeystoneTableEntries(
                table_entries, table)
            for entry in to_set:
                table_entries['entries'].remove(entry)
            assert len(table_entries['entries']) == 0

    # Test sending in non-convex quadrilaterals and validate the errors
    for resolution in supported_resolutions:
        for table in ['flash_fit_to_mat', 'flash_max_fov', 'ram']:
            zeros = {'resolution': resolution,
                     'value' : {'top_left' : {'x':0, 'y':0},
                                'top_right' :  {'x':-0, 'y':0},
                                'bottom_left' :  {'x':0, 'y':-0},
                                'bottom_right' :  {'x':-0, 'y':-0}},
                     'enabled': True}
            # Keystone is based on the parent resolution
            parent_res = camera.parent_resolution(resolution)
            half_width = parent_res['width']//2
            half_height = parent_res['height']//2

            errors = ['Invalid parameter', 'not a convex quadrilateral']

            # Top left x > top right x
            bad_top = copy.deepcopy(zeros)
            bad_top['value']['top_left']['x'] = half_width + 1
            bad_top['value']['top_right']['x'] = 1 - half_width
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone_table_entries(table, [bad_top])
            err_strings = errors + ['top_left.x', 'top_right.x', 'width']
            for item in err_strings:
                assert item in execinfo.value.message

            # Bottom left x > Bottom right x
            bad_bottom = copy.deepcopy(zeros)
            bad_bottom['value']['bottom_left']['x'] = half_width + 1
            bad_bottom['value']['bottom_right']['x'] = 1 - half_width
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone_table_entries(table, [bad_bottom])
            err_strings = errors + ['bottom_left.x', 'bottom_right.x', 'width']
            for item in err_strings:
                assert item in execinfo.value.message

            # Top left y > Bottom left y
            bad_left = copy.deepcopy(zeros)
            bad_left['value']['top_left']['y'] = half_height + 1
            bad_left['value']['bottom_left']['y'] = 1 - half_height
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone_table_entries(table, [bad_left])
            err_strings = errors + ['top_left.y', 'bottom_left.y', 'height']
            for item in err_strings:
                assert item in execinfo.value.message

            # Top right y > Bottom right y
            bad_right = copy.deepcopy(zeros)
            bad_right['value']['top_right']['y'] = half_height + 1
            bad_right['value']['bottom_right']['y'] = 1 - half_height
            with pytest.raises(PySproutError) as execinfo:
                camera.keystone_table_entries(table, [bad_right])
            err_strings = errors + ['top_right.y', 'bottom_right.y', 'height']
            for item in err_strings:
                assert item in execinfo.value.message

    # Now test other error conditions...
    table = 'ram'
    val = {'value' : {'top_left' : {'x':0, 'y':0},
                      'top_right' :  {'x':0, 'y':0},
                      'bottom_left' :  {'x':0, 'y':0},
                      'bottom_right' :  {'x':0, 'y':0}}}
    resolution = supported_resolutions[0]
    # Invalid resolution
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table,
                                      [resolution,
                                       {'width':1, 'height':2, 'fps':6}])
    assert 'Invalid resolution' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table, [{'type': table}])
    assert 'Invalid parameter' in execinfo.value.message
    assert "Unexpected item found 'type'" in execinfo.value.message

    # Missing items
    enabled = [{'resolution': resolution,
                'enabled': False}]
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table, enabled)
    assert 'Invalid parameter' in execinfo.value.message
    assert "Missing item 'value'" in execinfo.value.message
    value = [{'resolution': resolution,
              'value': val}]
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table, value)
    assert 'Invalid parameter' in execinfo.value.message
    assert "Missing item 'enabled'" in execinfo.value.message
    value = [{'enabled': True,
              'value': val}]
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table, value)
    assert 'Invalid parameter' in execinfo.value.message
    assert "Missing item 'resolution'" in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table, [{'resolution': resolution}])
    assert "Invalid parameter 'entry'" in execinfo.value.message
    assert "Missing items ['enabled', 'value']" in execinfo.value.message
    for item in resolution.keys():
        with pytest.raises(PySproutError) as execinfo:
            res = copy.deepcopy(resolution)
            res.pop(item)
            camera.keystone_table_entries(table, [{'value': val,
                                                   'enabled': True,
                                                   'resolution': res}])
    assert "Invalid parameter 'resolution'" in execinfo.value.message
    assert "Missing item '{}'".format(item) in execinfo.value.message

    # And finally verify completely invalid parameters throw errors
    # Test the first param
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(None)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries('invalid')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(23)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries({"fake": 32})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries({})
    assert 'Invalid parameter' in execinfo.value.message
    # And now the second param
    table = 'ram'
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table, 'invalid')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table, 23)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table, {"fake": 32})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table_entries(table, {})
    assert 'Invalid parameter' in execinfo.value.message


def test_keystone_table(get_camera):
    """
    Tests the hirescamera's keystone_table method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone_table()
        assert 'Functionality not available.' in str(execinfo.value)
        with pytest.raises(PySproutError) as execinfo:
            camera.keystone_table('default')
        assert 'Functionality not available.' in str(execinfo.value)
        return

    tables = ['default', 'ram', 'flash_max_fov', 'flash_fit_to_mat']

    new_table = camera.keystone_table()
    assert isinstance(new_table, str)
    assert new_table in tables

    for table in tables:
        # Update values in ram just to be sure ram doesn't match any of the
        # other tables. Otherwise if we set 'ram' and then do a 'get' we could
        # get the name of the table that was set previously.
        x = 7
        y = 8
        key = {'resolution': {'width': 640, 'height': 480, 'fps': 60},
               'value' : {'top_left' : {'x':x, 'y':y},
                          'top_right' :  {'x':-x, 'y':y},
                          'bottom_left' :  {'x':x, 'y':-y},
                          'bottom_right' :  {'x':-x, 'y':-y}},
               'enabled': True}
        camera.keystone_table_entries('ram', [key])

        set_table = camera.keystone_table(table)
        assert isinstance(new_table, str)
        assert set_table == table
        new_table = camera.keystone_table()
        assert new_table == table

    # Test invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table("default1")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table(12)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.keystone_table({'type' : 'default'})
    assert 'Invalid parameter' in execinfo.value.message


# TODO EB we should add another 'smarter' test that makes sure things interact
# as expected (ie set the keystone_table and then check that ram values changed
# to what we expected, try restarting the device and check the ram values, etc)

def test_available_resolutions(get_camera):
    """
    Tests the hirescamera's available_resolutions method.
    """
    camera = get_camera

    resolutions = camera.available_resolutions()
    assert isinstance(resolutions, list)

    for resolution in resolutions:
        check_camera_types.check_StreamingResolution(resolution)


def test_streaming_resolution(get_camera):
    """
    Tests the hirescamera's streaming_resolution method.
    """
    camera = get_camera
    resolutions = camera.available_resolutions()

    for resolution in resolutions:
        with CameraStreaming(camera, resolution):
            streaming_res = camera.streaming_resolution()
            check_camera_types.check_StreamingResolution(streaming_res)
            assert streaming_res == resolution

    # Verify we get an error if the camera isn't streaming frames
    with pytest.raises(PySproutError) as execinfo:
        camera.streaming_resolution()
    assert 'The camera is not streaming' in str(execinfo.value)


def test_parent_resolution(get_camera):
    """
    Tests the hirescamera's parent_resolution method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.parent_resolution()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    # this dictionary has been copied from SoHal's python/pluto/flick.py file
    parent_resolution = {
        Resolution.r_4352_3264_6 : (4352, 3264),
        # Hidden resolution for still image capture
        # flick.Resolution.r_2176_1632_30 : (4352, 3264),
        Resolution.r_2176_1632_15 : (4352, 3264),
        Resolution.r_640_480_15 : (4352, 3264),
        Resolution.r_4352_2896_6 : (4352, 3264),
        Resolution.r_2176_1448_15 : (4352, 3264),
        Resolution.r_3840_2160_10 : (4352, 3264),
        Resolution.r_1920_1080_15 : (4352, 3264),
        Resolution.r_4224_3168_6 : (4224, 3168),
        Resolution.r_1056_792_15 : (4224, 3168),
        Resolution.r_1056_704_15 : (4224, 3168),
        Resolution.r_960_540_15 : (4224, 3168),
        Resolution.r_2176_1632_25 : (2176, 1632),
        Resolution.r_2176_1448_25 : (2176, 1632),
        Resolution.r_1920_1080_30 : (2176, 1632),
        Resolution.r_2112_1584_25 : (2112, 1584),
        Resolution.r_1056_792_30 : (2112, 1584),
        Resolution.r_1056_704_30 : (2112, 1584),
        Resolution.r_960_540_30 : (2112, 1584),
        Resolution.r_1056_792_60 : (1056, 792),
        Resolution.r_1056_704_60 : (1056, 792),
        Resolution.r_960_540_60 : (1056, 792),
        Resolution.r_640_480_60 : (1056, 792),
        Resolution.r_416_234_60 : (1056, 594),
    }

    resolutions = camera.available_resolutions()
    for resolution in resolutions:
        with CameraStreaming(camera, resolution):
            parent_res = camera.parent_resolution()
            check_hirescamera_types.check_CameraResolution(parent_res)
            res_string = "r_{}_{}_{}".format(resolution['width'],
                                             resolution['height'],
                                             resolution['fps'])
            res_enum = Resolution[res_string]
            assert parent_resolution[res_enum] == (parent_res['width'],
                                                   parent_res['height'])

    # checks querying parent resolution for a given resolution
    for resolution in resolutions:
        parent_res = camera.parent_resolution({'width': resolution['width'],
                                               'height': resolution['height'],
                                               'fps': resolution['fps']})
        check_hirescamera_types.check_CameraResolution(parent_res)
        res_string = "r_{}_{}_{}".format(resolution['width'],
                                         resolution['height'],
                                         resolution['fps'])
        res_enum = Resolution[res_string]
        assert parent_resolution[res_enum] == (parent_res['width'],
                                               parent_res['height'])

    # Verify we get an error if the camera isn't streaming frames
    with pytest.raises(PySproutError) as execinfo:
        camera.parent_resolution()
    assert 'The camera is not streaming' in str(execinfo.value)

    # checks for invalid params
    with pytest.raises(PySproutError) as execinfo:
        camera.parent_resolution({})
    assert 'Invalid parameter' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        camera.parent_resolution("parent resolution")
    assert 'Invalid parameter' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        camera.parent_resolution(42)
    assert 'Invalid parameter' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        camera.parent_resolution({'width': 4352, 'height': 3264})
    assert 'Invalid parameter' in str(execinfo.value)
    assert "Missing item 'fps'" in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.parent_resolution({'width': 4352, 'height': 3264, 'fps': 15,
                                  'additional': 42})
    assert 'Invalid parameter' in str(execinfo.value)
    assert "Unexpected item found 'additional'" in execinfo.value.message


def test_brightness(get_camera):
    """
    Tests the hirescamera's brightness method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.brightness()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    min_bright = 16
    max_bright = 255
    bright = camera.brightness()
    assert isinstance(bright, int)
    assert min_bright <= bright <= max_bright

    bright = random.randint(min_bright, max_bright)
    set_bright = camera.brightness(bright)
    assert set_bright == bright
    assert camera.brightness() == bright

    # Test the edge values
    bright = min_bright
    set_bright = camera.brightness(bright)
    assert set_bright == bright
    assert camera.brightness() == bright
    bright = max_bright
    set_bright = camera.brightness(bright)
    assert set_bright == bright
    assert camera.brightness() == bright

    # Ensure that out of range values throw errors
    with pytest.raises(PySproutError) as execinfo:
        camera.brightness(min_bright-1)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.brightness(max_bright+1)
    assert 'Parameter out of range' in execinfo.value.message
    bad_bright = random.randint(max_bright+1, max_bright+300)
    with pytest.raises(PySproutError) as execinfo:
        camera.brightness(bad_bright)
    assert 'Parameter out of range' in execinfo.value.message
    bad_bright = random.randint(min_bright-300, min_bright-1)
    with pytest.raises(PySproutError) as execinfo:
        camera.brightness(bad_bright)
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid values
    with pytest.raises(PySproutError) as execinfo:
        camera.brightness("rainbow")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.brightness({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.brightness({'brightness':42})
    assert 'Invalid parameter' in execinfo.value.message

    assert camera.brightness() == bright


def test_contrast(get_camera):
    """
    Tests the hirescamera's contrast method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.contrast()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    min_contrast = 0
    max_contrast = 10
    contrast = camera.contrast()
    assert isinstance(contrast, int)
    assert min_contrast <= contrast <= max_contrast

    contrast = random.randint(min_contrast, max_contrast)
    set_contrast = camera.contrast(contrast)
    assert set_contrast == contrast
    assert camera.contrast() == contrast

    # Test the edge values
    contrast = min_contrast
    set_contrast = camera.contrast(contrast)
    assert set_contrast == contrast
    assert camera.contrast() == contrast
    contrast = max_contrast
    set_contrast = camera.contrast(contrast)
    assert set_contrast == contrast
    assert camera.contrast() == contrast

    # Ensure that out of range values throw errors
    with pytest.raises(PySproutError) as execinfo:
        camera.contrast(min_contrast-1)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.contrast(max_contrast+1)
    assert 'Parameter out of range' in execinfo.value.message
    bad_contrast = random.randint(max_contrast+1, max_contrast+300)
    with pytest.raises(PySproutError) as execinfo:
        camera.contrast(bad_contrast)
    assert 'Parameter out of range' in execinfo.value.message
    bad_contrast = random.randint(min_contrast-300, min_contrast-1)
    with pytest.raises(PySproutError) as execinfo:
        camera.contrast(bad_contrast)
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid values
    with pytest.raises(PySproutError) as execinfo:
        camera.contrast("similarity")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.contrast({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.contrast({'contrast':42})
    assert 'Invalid parameter' in execinfo.value.message

    assert camera.contrast() == contrast


def test_saturation(get_camera):
    """
    Tests the hirescamera's saturation method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.saturation()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    min_sat = 0
    max_sat = 63
    sat = camera.saturation()
    assert isinstance(sat, int)
    assert min_sat <= sat <= max_sat

    sat = random.randint(min_sat, max_sat)
    set_sat = camera.saturation(sat)
    assert set_sat == sat
    assert camera.saturation() == sat

    # Test the edge values
    sat = min_sat
    set_sat = camera.saturation(sat)
    assert set_sat == sat
    assert camera.saturation() == sat
    sat = max_sat
    set_sat = camera.saturation(sat)
    assert set_sat == sat
    assert camera.saturation() == sat

    # Ensure that out of range values throw errors
    with pytest.raises(PySproutError) as execinfo:
        camera.saturation(min_sat-1)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.saturation(max_sat+1)
    assert 'Parameter out of range' in execinfo.value.message
    bad_sat = random.randint(max_sat+1, max_sat+300)
    with pytest.raises(PySproutError) as execinfo:
        camera.saturation(bad_sat)
    assert 'Parameter out of range' in execinfo.value.message
    bad_sat = random.randint(min_sat-300, min_sat-1)
    with pytest.raises(PySproutError) as execinfo:
        camera.saturation(bad_sat)
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid values
    with pytest.raises(PySproutError) as execinfo:
        camera.saturation("soaked")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.saturation({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.saturation({'saturation':42})
    assert 'Invalid parameter' in execinfo.value.message

    assert camera.saturation() == sat


def test_sharpness(get_camera):
    """
    Tests the hirescamera's sharpness method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.sharpness()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    min_sharp = 0
    max_sharp = 4
    sharp = camera.sharpness()
    assert isinstance(sharp, int)
    assert min_sharp <= sharp <= max_sharp

    sharp = random.randint(min_sharp, max_sharp)
    set_sharp = camera.sharpness(sharp)
    assert set_sharp == sharp
    assert camera.sharpness() == sharp

    # Test the edge values
    sharp = min_sharp
    set_sharp = camera.sharpness(sharp)
    assert set_sharp == sharp
    assert camera.sharpness() == sharp
    sharp = max_sharp
    set_sharp = camera.sharpness(sharp)
    assert set_sharp == sharp
    assert camera.sharpness() == sharp

    # Ensure that out of range values throw errors
    with pytest.raises(PySproutError) as execinfo:
        camera.sharpness(min_sharp-1)
    assert 'Parameter out of range' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.sharpness(max_sharp+1)
    assert 'Parameter out of range' in execinfo.value.message
    bad_sharp = random.randint(max_sharp+1, max_sharp+300)
    with pytest.raises(PySproutError) as execinfo:
        camera.sharpness(bad_sharp)
    assert 'Parameter out of range' in execinfo.value.message
    bad_sharp = random.randint(min_sharp-300, min_sharp-1)
    with pytest.raises(PySproutError) as execinfo:
        camera.sharpness(bad_sharp)
    assert 'Parameter out of range' in execinfo.value.message

    # Test invalid values
    with pytest.raises(PySproutError) as execinfo:
        camera.sharpness("dull")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.sharpness({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.sharpness({'sharpness':42})
    assert 'Invalid parameter' in execinfo.value.message

    assert camera.sharpness() == sharp


def test_device_status(get_camera):
    """
    Tests the hirescamera's device_status method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.device_status()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    status = camera.device_status()
    check_hirescamera_types.check_CameraDeviceStatus(status)
    for item in status:
        assert status[item] == 'ok'


def test_power_line_frequency(get_camera):
    """
    Tests the hirescamera's power_line_frequency method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.power_line_frequency()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    frequency = camera.power_line_frequency()
    assert isinstance(frequency, int)
    assert frequency in (50, 60)
    for frequency in (50, 60):
        set_frequency = camera.power_line_frequency(frequency)
        assert set_frequency == frequency
        assert frequency == camera.power_line_frequency()

    # Now test invalid parameters
    for invalid in (59, 61, 49, 51, -50, -60):
        with pytest.raises(PySproutError) as execinfo:
            camera.power_line_frequency(invalid)
        assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.power_line_frequency("50")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.power_line_frequency("moo")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.power_line_frequency({'frequency':60})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        camera.power_line_frequency([[50]])
    assert 'Invalid parameter' in execinfo.value.message


def test_reset(get_camera):
    """
    Tests the hirescamera's reset method.
    """
    camera = get_camera
    camera_model = check_device_types.get_device_model(camera)
    if camera_model == Devices.hirescamera:
        with pytest.raises(PySproutError) as execinfo:
            camera.power_line_frequency()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    camera.reset()
    # Short sleep just so the device has time to disconnect before we get
    # to the next block.
    time.sleep(0.1)
    # The camera should disconnect and then reconnect. Loop for up to 5
    # seconds checking if it's connected
    count = 0
    while not camera.is_device_connected():
        assert count < 10
        time.sleep(0.5)
        count += 1

    # double check that we can talk to it again
    assert camera.open_count() == 0
    camera.open()
    assert camera.auto_gain() == True


def test_enable_filter(get_camera):
    """
    Tests the hirescamera's enble_filter method.
    """
    camera = get_camera

    with pytest.raises(PySproutError) as execinfo:
        camera.enable_filter('ir_gamma')
    assert 'Invalid parameter' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        camera.enable_filter('fake')
    assert 'Invalid parameter' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        camera.enable_filter(0)
    assert 'Invalid parameter' in str(execinfo.value)


def test_enable_disable_streams(get_camera):
    """
    Tests the enble_streams and disable_streams methods.
    """
    camera = get_camera

    streams = camera.enable_streams(HiResCamera.ImageStream.color)
    assert isinstance(streams, list)
    assert len(streams) == 1
    assert streams == [HiResCamera.ImageStream.color]
    assert camera.enable_streams() == streams
    assert camera.disable_streams() == streams

    streams = camera.disable_streams(HiResCamera.ImageStream.color)
    assert isinstance(streams, list)
    assert len(streams) == 0
    assert streams == []
    assert camera.enable_streams() == streams
    assert camera.disable_streams() == streams

    # Test using strings instead of ImageStream objects
    streams = camera.enable_streams('color')
    assert streams == [HiResCamera.ImageStream.color]
    assert camera.enable_streams() == streams
    assert camera.disable_streams() == streams

    streams = camera.disable_streams('color')
    assert streams == []
    assert camera.enable_streams() == streams
    assert camera.disable_streams() == streams

    # Test outside of the hippy method, so we can be sure SoHal is
    # returning the expected type
    ret = camera._send_msg('enable_streams', [['color']])
    check_camera_types.check_EnableStream(ret)

    # Test invalid streams to be sure we get the expected error
    for stream in ('ir', 'depth', 'points', 'fake'):
        with pytest.raises(PySproutError) as execinfo:
            camera._send_msg('enable_streams', [[stream]])
        assert 'Invalid parameter' in str(execinfo.value)
        with pytest.raises(PySproutError) as execinfo:
            camera._send_msg('disable_streams', [[stream]])
        assert 'Invalid parameter' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        camera._send_msg('enable_streams', 'color')
    assert 'Invalid parameter' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        camera._send_msg('enable_streams', [[0]])
    assert 'Invalid parameter' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        camera._send_msg('enable_streams', 0)
    assert 'Invalid parameter' in str(execinfo.value)
    with pytest.raises(PySproutError) as execinfo:
        camera._send_msg('enable_streams', {'streams': 'color'})
    assert 'Invalid parameter' in str(execinfo.value)


def test_streaming(get_camera):
    """
    Tests streaming frames at each resolution.
    """
    camera = get_camera
    resolutions = camera.available_resolutions()
    # for i in range(3):
    for resolution in resolutions:
        with CameraStreaming(camera, resolution):
            # print("Streaming resolution {}".format(resolution))
            time.sleep(10)
