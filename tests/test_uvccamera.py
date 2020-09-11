
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy UVCCamera.
"""

from __future__ import division, absolute_import, print_function

import threading
import pytest

import check_camera_types
import check_device_types
import check_system_types

from hippy import PySproutError
from hippy import UVCCamera


device_name = 'uvccamera'
notifications = []
condition = threading.Condition()


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_camera(request, index):
    """
    A pytest fixture to initialize and return the UVCCamera object with
    the given index.
    """
    camera = UVCCamera(index)
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
    Tests the uvccamera's info method
    """
    camera = get_camera

    info = camera.info()
    check_device_types.check_DeviceInfo(info)

    serial = info['serial']
    assert serial == "Not Available"


def test_open_and_close(get_camera):
    """
    Tests the uvccamera's open, open_count, and close methods.
    """
    camera = get_camera

    connected = camera.is_device_connected()
    assert connected is True

    orig_count = camera.open_count()
    assert isinstance(orig_count, int)
    count = camera.close()
    assert isinstance(count, int)
    assert camera.open_count() == (orig_count - 1)
    assert camera.open_count() == count
    # TODO(EB/SR) Update this when the uvccamera device has other methods
    # with pytest.raises(PySproutError) as execinfo:
    #     # Any call should fail
    #     camera.white_balance()
    # assert execinfo.value.message == 'Device is not open'
    new_count = camera.open()
    assert isinstance(new_count, int)
    assert new_count == orig_count
    assert camera.open_count() == (count + 1)
    # TODO(EB/SR) Update this when the uvccamera device has other methods
    # # Any call should now work
    # camera.white_balance()


def test_factory_default(get_camera):
    """
    Tests the uvccamera's factory_default method.
    """
    camera = get_camera

    camera.factory_default()


def test_temperatures(get_camera):
    """
    Tests the uvccamera's temperatures method.
    """
    camera = get_camera

    temperatures = camera.temperatures()
    info = camera.info()
    check_system_types.check_TemperatureInfoList(temperatures, [info])


def test_camera_index(get_camera):
    """
    Tests the uvccamera's camera_index method.
    """
    camera = get_camera

    index = camera.camera_index()
    assert isinstance(index, int)
    assert index >= 0


# EB TODO need to add tests for the generic camera functionality...
# enable/disable streams (+ the notifications), enable filter,
# and grabbing frames.

def test_available_resolutions(get_camera):
    """
    Tests the uvccamera's available_resolutions method.
    """
    camera = get_camera

    resolutions = camera.available_resolutions()
    assert isinstance(resolutions, list)

    for resolution in resolutions:
        check_camera_types.check_StreamingResolution(resolution)


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

    val = camera.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    name = camera._object_name
    # Notifications are never sent as '@0' even if we sent the command with @0
    if '@0' in name:
        name = 'uvccamera'

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

    camera.factory_default()
    notification = get_notification()
    assert notification == ('{}.on_factory_default'.format(name), None)

    val = camera.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Now make sure we aren't getting notification callbacks anymore...
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
