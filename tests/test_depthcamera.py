
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy depthcamera.
"""

from __future__ import division, absolute_import, print_function

import asyncio
import threading
import time
import pytest

import check_camera_types
import check_device_types
import check_system_types
from check_device_types import Devices

from hippy import DepthCamera
from hippy import PySproutError


device_name = 'depthcamera'
notifications = []
condition = threading.Condition()


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_depthcamera(request, index):
    """
    A pytest fixture to initialize and return the DepthCamera object with
    the given index.
    """
    depthcamera = DepthCamera(index)
    try:
        depthcamera.open()
    except RuntimeError:
        pytest.skip("Could not open depthcamera connection")
    def fin():
        depthcamera.unsubscribe()
        depthcamera.close()
    request.addfinalizer(fin)

    return depthcamera


def test_info(get_depthcamera):
    """
    Tests the depthcamera's info method
    """
    depthcamera = get_depthcamera

    info = depthcamera.info()
    check_device_types.check_DeviceInfo(info)

    vid_pid = (info['vendor_id'], info['product_id'])
    assert vid_pid in (Devices.depthcamera_g1.value,
                       Devices.depthcamera_g2.value,
                       Devices.depthcamera_z_3d.value)

    serial = info['serial']
    if Devices(vid_pid) == Devices.depthcamera_g1:
        assert len(serial) != 0
    else:
        assert len(serial) == 14


def test_open_and_close(get_depthcamera):
    """
    Tests the depthcamera's open, open_count, and close methods.
    """
    depthcamera = get_depthcamera

    connected = depthcamera.is_device_connected()
    assert connected is True

    assert depthcamera.open_count() == 1
    count = depthcamera.close()
    assert isinstance(count, int)
    assert count == 0
    assert depthcamera.open_count() == 0
    with pytest.raises(PySproutError) as execinfo:
        # Any call should fail
        depthcamera.enable_streams([DepthCamera.ImageStream.color])
    assert execinfo.value.message == 'Device is not open'
    count = depthcamera.open()
    assert isinstance(count, int)
    assert count == 1
    assert depthcamera.open_count() == 1
    # Any call should now work
    depthcamera.enable_streams([DepthCamera.ImageStream.color])
    depthcamera.disable_streams([DepthCamera.ImageStream.color])


# EB TODO need to add tests for the generic camera functionality...
# enable/disable streams (+ the notifications), enable filter,
# and grabbing frames.

def test_available_resolutions(get_depthcamera):
    """
    Tests the depthcamera's available_resolutions method.
    """
    depthcamera = get_depthcamera

    resolutions = depthcamera.available_resolutions()
    assert isinstance(resolutions, list)

    for resolution in resolutions:
        check_camera_types.check_StreamingResolution(resolution)


def test_color_stream(get_depthcamera):
    """
    Tests enabling the depthcamera's color stream and grabbing frames from it.
    """
    depthcamera = get_depthcamera
    depthcamera_model = check_device_types.get_device_model(depthcamera)

    streams = depthcamera.enable_streams([DepthCamera.ImageStream.color])
    assert isinstance(streams, list)
    assert len(streams) == 1
    assert streams == [DepthCamera.ImageStream.color]
    frame = depthcamera.grab_frame(DepthCamera.ImageStream.color)
    assert isinstance(frame, dict)
    if depthcamera_model == Devices.depthcamera_g1:
        assert frame['format'] == DepthCamera.ImageFormat.bgra_8888
    else:
        assert frame['format'] == DepthCamera.ImageFormat.rgb_888
    assert frame['stream'] == DepthCamera.ImageStream.color
    assert frame['width'] == 640
    assert frame['height'] == 480
    frame2 = depthcamera.grab_frame(DepthCamera.ImageStream.color)
    assert frame2['index'] > frame['index']
    assert frame2['timestamp'] > frame['timestamp']
    streams = depthcamera.disable_streams([DepthCamera.ImageStream.color])
    assert isinstance(streams, list)
    assert len(streams) == 0
    assert not streams


def test_ir_stream(get_depthcamera):
    """
    Tests enabling the depthcamera's ir stream and grabbing frames from it.
    """
    depthcamera = get_depthcamera
    depthcamera_model = check_device_types.get_device_model(depthcamera)

    streams = depthcamera.enable_streams([DepthCamera.ImageStream.ir])
    assert isinstance(streams, list)
    assert len(streams) == 1
    assert streams == [DepthCamera.ImageStream.ir]
    gamma = depthcamera.enable_filter('ir_gamma')
    assert isinstance(gamma, int)
    frame = depthcamera.grab_frame(DepthCamera.ImageStream.ir)
    assert isinstance(frame, dict)
    if depthcamera_model == Devices.depthcamera_g1:
        assert frame['format'] == DepthCamera.ImageFormat.gray_8
    else:
        assert frame['format'] == DepthCamera.ImageFormat.gray_16
    assert frame['stream'] == DepthCamera.ImageStream.ir
    assert frame['width'] == 640
    assert frame['height'] == 480
    frame2 = depthcamera.grab_frame(DepthCamera.ImageStream.ir)
    assert frame2['index'] > frame['index']
    assert frame2['timestamp'] > frame['timestamp']
    frame3 = depthcamera.grab_frame(DepthCamera.ImageStream.ir, gamma)
    assert frame3['index'] > frame['index']
    assert frame3['timestamp'] > frame2['timestamp']
    streams = depthcamera.disable_streams([DepthCamera.ImageStream.ir])
    assert isinstance(streams, list)
    assert len(streams) == 0
    assert not streams


def test_depth_stream(get_depthcamera):
    """
    Tests enabling the depthcamera's depth stream and grabbing frames from it.
    """
    depthcamera = get_depthcamera

    streams = depthcamera.enable_streams([DepthCamera.ImageStream.depth])
    assert isinstance(streams, list)
    assert len(streams) == 1
    assert streams == [DepthCamera.ImageStream.depth]
    frame = depthcamera.grab_frame(DepthCamera.ImageStream.depth)
    assert isinstance(frame, dict)
    assert frame['format'] == DepthCamera.ImageFormat.depth_mm
    assert frame['stream'] == DepthCamera.ImageStream.depth
    assert frame['width'] == 640
    assert frame['height'] == 480
    frame2 = depthcamera.grab_frame(DepthCamera.ImageStream.depth)
    assert frame2['index'] > frame['index']
    assert frame2['timestamp'] > frame['timestamp']
    streams = depthcamera.disable_streams([DepthCamera.ImageStream.depth])
    assert isinstance(streams, list)
    assert len(streams) == 0
    assert not streams


def test_points_stream(get_depthcamera):
    """
    Tests enabling the depthcamera's points stream and grabbing frames from it.
    """
    depthcamera = get_depthcamera

    streams = depthcamera.enable_streams([DepthCamera.ImageStream.depth,
                                          DepthCamera.ImageStream.points,])
    assert isinstance(streams, list)
    assert len(streams) == 2
    assert streams == [DepthCamera.ImageStream.depth,
                       DepthCamera.ImageStream.points]
    frame = depthcamera.grab_frame(DepthCamera.ImageStream.points)
    assert isinstance(frame, dict)
    assert frame['format'] == DepthCamera.ImageFormat.points_mm
    assert frame['stream'] == DepthCamera.ImageStream.points
    assert frame['width'] == 640
    assert frame['height'] == 480
    frame2 = depthcamera.grab_frame(DepthCamera.ImageStream.points)
    assert frame2['index'] > frame['index']
    assert frame2['timestamp'] > frame['timestamp']
    streams = depthcamera.disable_streams([DepthCamera.ImageStream.depth,
                                           DepthCamera.ImageStream.points,])
    assert isinstance(streams, list)
    assert len(streams) == 0
    assert not streams


def test_enable_disable(get_depthcamera):
    """
    Tests the depthcamera's enable_streams and disable_streams methods.
    """
    depthcamera = get_depthcamera

    streams = depthcamera.enable_streams(DepthCamera.ImageStream.color)
    assert isinstance(streams, list)
    assert len(streams) == 1
    assert streams == [DepthCamera.ImageStream.color]
    assert depthcamera.enable_streams() == streams
    assert depthcamera.disable_streams() == streams

    streams = depthcamera.enable_streams([DepthCamera.ImageStream.depth])
    assert isinstance(streams, list)
    assert len(streams) == 2
    assert set(streams) == set([DepthCamera.ImageStream.depth,
                                DepthCamera.ImageStream.color])
    assert set(depthcamera.enable_streams()) == set(streams)
    assert set(depthcamera.disable_streams()) == set(streams)

    streams = depthcamera.disable_streams(DepthCamera.ImageStream.color)
    assert isinstance(streams, list)
    assert len(streams) == 1
    assert streams == [DepthCamera.ImageStream.depth]
    assert set(depthcamera.enable_streams()) == set(streams)
    assert set(depthcamera.disable_streams()) == set(streams)

    streams = depthcamera.enable_streams([DepthCamera.ImageStream.ir])
    assert isinstance(streams, list)
    assert len(streams) == 2
    assert set(streams) == set([DepthCamera.ImageStream.depth,
                                DepthCamera.ImageStream.ir])
    assert set(depthcamera.enable_streams()) == set(streams)
    assert set(depthcamera.disable_streams()) == set(streams)

    streams = depthcamera.disable_streams([DepthCamera.ImageStream.depth])
    assert isinstance(streams, list)
    assert len(streams) == 1
    assert streams == [DepthCamera.ImageStream.ir]
    assert set(depthcamera.enable_streams()) == set(streams)
    assert set(depthcamera.disable_streams()) == set(streams)

    streams = depthcamera.disable_streams([DepthCamera.ImageStream.ir])
    assert isinstance(streams, list)
    assert len(streams) == 0
    assert not streams
    assert depthcamera.enable_streams() == streams
    assert depthcamera.disable_streams() == streams
    ###################################################

    # Test using strings instead of ImageStream objects
    streams = depthcamera.enable_streams(['color', 'depth'])
    assert isinstance(streams, list)
    assert len(streams) == 2
    assert set(streams) == set([DepthCamera.ImageStream.depth,
                                DepthCamera.ImageStream.color])
    assert depthcamera.enable_streams() == streams
    assert depthcamera.disable_streams() == streams

    streams = depthcamera.disable_streams('color')
    assert isinstance(streams, list)
    assert len(streams) == 1
    assert streams == [DepthCamera.ImageStream.depth]
    assert depthcamera.enable_streams() == streams
    assert depthcamera.disable_streams() == streams

    streams = depthcamera.enable_streams(['ir', 'points'])
    assert isinstance(streams, list)
    assert len(streams) == 3
    assert set(streams) == set([DepthCamera.ImageStream.depth,
                                DepthCamera.ImageStream.ir,
                                DepthCamera.ImageStream.points])
    assert depthcamera.enable_streams() == streams
    assert depthcamera.disable_streams() == streams

    streams = depthcamera.disable_streams(['depth', 'ir', 'points'])
    assert isinstance(streams, list)
    assert len(streams) == 0
    assert not streams
    assert depthcamera.enable_streams() == streams
    assert depthcamera.disable_streams() == streams

    # Validate that sohal is sending the port number of -1 when no streams
    # are enabled.
    ret = depthcamera._send_msg('enable_streams') # pylint: disable=protected-access
    assert isinstance(ret, dict)
    assert -1 == ret['port']
    assert isinstance(ret['streams'], list)
    assert len(ret['streams']) == 0

    # Test enabling points when depth isn't enabled
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.enable_streams('points')
    assert 'Device is in the wrong state' in execinfo.value.message

    # Test passing in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.enable_streams([])
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.disable_streams([])
    assert 'Invalid parameter' in execinfo.value.message

    # Test passing in invalid parameters
    with pytest.raises(ValueError) as execinfo:
        depthcamera.enable_streams(['fake'])
    with pytest.raises(ValueError) as execinfo:
        depthcamera.enable_streams("abc")
    with pytest.raises(ValueError) as execinfo:
        depthcamera.enable_streams(13)

    with pytest.raises(ValueError) as execinfo:
        depthcamera.disable_streams(['invalid'])
    with pytest.raises(ValueError) as execinfo:
        depthcamera.disable_streams("abc")
    with pytest.raises(ValueError) as execinfo:
        depthcamera.disable_streams(21)

    # Send bad values to SoHal (bypassing the hippy enum check) and make
    # sure SoHal throws an error...
    with pytest.raises(PySproutError) as execinfo:
        depthcamera._send_msg('enable_streams', ['fake']) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera._send_msg('enable_streams', "abc") # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera._send_msg('enable_streams', 1) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera._send_msg('enable_streams', {}) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message

    with pytest.raises(PySproutError) as execinfo:
        depthcamera._send_msg('enable_streams', ['invalid']) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera._send_msg('disable_streams', "abc") # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera._send_msg('disable_streams', 1) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera._send_msg('disable_streams', {}) # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message

# TODO(EB) Need to add tests that check grab_frame and enable_filter throws
# errors with invalid values



def test_streaming(get_depthcamera):
    """
    Tests streaming frames at each resolution.
    """
    camera = get_depthcamera
    resolutions = camera.available_resolutions()
    # for i in range(3):
    for resolution in resolutions:
        streams = [resolution['stream']]
        if resolution['stream'] in ['points', DepthCamera.ImageStream.points]:
            streams.append('depth')
        with camera_streaming(camera, resolution, streams):
            print("EB Streaming resolution {}".format(resolution))
            time.sleep(10)

def test_laser_on(get_depthcamera):
    """
    Tests the depthcamera's laser_on method.
    """
    depthcamera = get_depthcamera
    depthcamera_model = check_device_types.get_device_model(depthcamera)

    if depthcamera_model == Devices.depthcamera_g1:
        with pytest.raises(PySproutError) as execinfo:
            depthcamera.laser_on(True)
        assert 'Functionality not available.' in str(execinfo.value)
        return

    depthcamera.laser_on(True)
    on = depthcamera.laser_on()
    assert on is True
    depthcamera.laser_on(False)
    on = depthcamera.laser_on()
    assert on is False

    # Test passing in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.laser_on("abc")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.laser_on(1)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.laser_on({})
    assert 'Invalid parameter' in execinfo.value.message


def test_ir_flood_on(get_depthcamera):
    """
    Tests the depthcamera's ir_flood_on method.
    """
    depthcamera = get_depthcamera
    depthcamera_model = check_device_types.get_device_model(depthcamera)

    if depthcamera_model == Devices.depthcamera_g1:
        with pytest.raises(PySproutError) as execinfo:
            depthcamera.ir_flood_on(True)
        assert 'Functionality not available.' in str(execinfo.value)
        return

    depthcamera.ir_flood_on(True)
    on = depthcamera.ir_flood_on()
    assert on is True
    depthcamera.ir_flood_on(False)
    on = depthcamera.ir_flood_on()
    assert on is False

    # Test passing in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.ir_flood_on("abc")
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.ir_flood_on(1)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.ir_flood_on({})
    assert 'Invalid parameter' in execinfo.value.message


def test_factory_default(get_depthcamera):
    """
    Tests the depthcamera's factory_default method.
    """
    depthcamera = get_depthcamera

    depthcamera.factory_default()


def test_temperatures(get_depthcamera):
    """
    Tests the depthcamera's temperatures method.
    """
    depthcamera = get_depthcamera

    temperatures = depthcamera.temperatures()
    camera_info = depthcamera.info()
    check_system_types.check_TemperatureInfoList(temperatures, [camera_info])


def test_multi_stream(get_depthcamera):
    """
    Tests enabling multiple image streams and grabbing frames.
    """
    depthcamera = get_depthcamera

    streams = depthcamera.enable_streams([DepthCamera.ImageStream.depth,
                                          DepthCamera.ImageStream.points,])
    assert isinstance(streams, list)
    assert len(streams) == 2
    assert streams == [DepthCamera.ImageStream.depth,
                       DepthCamera.ImageStream.points]
    frames = depthcamera.grab_frame([DepthCamera.ImageStream.points,
                                     DepthCamera.ImageStream.depth])
    assert len(frames) == 2

    assert (DepthCamera.ImageFormat.points_mm == frames[0]['format'] or
            DepthCamera.ImageFormat.points_mm == frames[1]['format'])
    assert (DepthCamera.ImageFormat.depth_mm == frames[0]['format'] or
            DepthCamera.ImageFormat.depth_mm == frames[1]['format'])
    assert frames[0]['format'] != frames[1]['format']

    assert (frames[0]['stream'] == DepthCamera.ImageStream.points  or
            frames[1]['stream'] == DepthCamera.ImageStream.points)
    assert (frames[0]['stream'] == DepthCamera.ImageStream.depth or
            frames[1]['stream'] == DepthCamera.ImageStream.depth)
    assert frames[0]['stream'] != frames[1]['stream']

    for frame in frames:
        assert frame['width'] == 640
        assert frame['height'] == 480

    frame2 = depthcamera.grab_frame('points')
    assert frame2['index'] > frames[0]['index']
    streams = depthcamera.disable_streams([DepthCamera.ImageStream.depth,
                                           DepthCamera.ImageStream.points,])
    assert isinstance(streams, list)
    assert len(streams) == 0
    assert not streams


def test_ir_to_rgb_calibration(get_depthcamera):
    """
    Tests the depthcamera's ir_to_rgb_calibration method.
    """
    depthcamera = get_depthcamera
    depthcamera_model = check_device_types.get_device_model(depthcamera)

    if depthcamera_model == Devices.depthcamera_g1:
        with pytest.raises(PySproutError) as execinfo:
            depthcamera.ir_to_rgb_calibration()
        assert 'Functionality not available.' in str(execinfo.value)
        return

    vendetta = depthcamera.ir_to_rgb_calibration()
    assert isinstance(vendetta, dict)
    assert "ir_intrinsics" in vendetta
    assert isinstance(vendetta['ir_intrinsics'], list)
    assert len(vendetta['ir_intrinsics']) == 4
    for item in vendetta['ir_intrinsics']:
        assert isinstance(item, float)

    assert "rgb_intrinsics" in vendetta
    assert isinstance(vendetta['rgb_intrinsics'], list)
    assert len(vendetta['rgb_intrinsics']) == 4
    for item in vendetta['rgb_intrinsics']:
        assert isinstance(item, float)

    assert "ir_distortion" in vendetta
    assert isinstance(vendetta['ir_distortion'], list)
    assert len(vendetta['ir_distortion']) == 5
    for item in vendetta['ir_distortion']:
        assert isinstance(item, float)

    assert "rgb_distortion" in vendetta
    assert isinstance(vendetta['rgb_distortion'], list)
    assert len(vendetta['rgb_distortion']) == 5
    for item in vendetta['rgb_distortion']:
        assert isinstance(item, float)

    assert "matrix_transformation" in vendetta
    assert isinstance(vendetta['matrix_transformation'], list)
    assert len(vendetta['matrix_transformation']) == 4
    for item in vendetta['matrix_transformation']:
        assert isinstance(item, list)
        assert len(item) == 4
        for value in item:
            assert isinstance(value, float)

    assert "mirror" in vendetta
    assert isinstance(vendetta['mirror'], bool)


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


def test_notifications(get_depthcamera):
    """
    This method tests the depthcamera.on_*** notifications received from SoHal.
    """
    depthcamera = get_depthcamera
    depthcamera_model = check_device_types.get_device_model(depthcamera)

    val = depthcamera.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    name = depthcamera._object_name
    # Notifications are never sent as '@0' even if we sent the command with @0
    if '@0' in name:
        name = 'depthcamera'

    # TODO(EB) We'll need a manual test for on_suspend and on_resume

    depthcamera.close()
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 0)
    notification = get_notification()
    assert notification == ('{}.on_close'.format(name), None)
    depthcamera.open()
    notification = get_notification()
    assert notification == ('{}.on_open'.format(name), None)
    # we no longer send this notification, but we'll leave the code here
    # if depthcamera_model in (Devices.depthcamera_g2,
    #                          Devices.depthcamera_z_3d):
    #     notification = get_notification()
    #     assert notification == ('{}.on_laser_on'.format(name), True)
    notification = get_notification()
    assert notification == ('{}.on_open_count'.format(name), 1)

    if depthcamera_model in (Devices.depthcamera_g2,
                             Devices.depthcamera_z_3d):
        # enable_streams only sends an on_laser_on notification if it wasn't
        # previously on, so we need to know if it was...
        laser_was_on = depthcamera.laser_on()

    streams = [DepthCamera.ImageStream.color]
    depthcamera.enable_streams(streams)
    notification = get_notification()
    assert notification == ('{}.on_enable_streams'.format(name), streams)
    # If the laser wasn't already on, enable streams will turn it on and
    # send a notification
    if depthcamera_model in (Devices.depthcamera_g2,
                             Devices.depthcamera_z_3d):
        if not laser_was_on:
            notification = get_notification()
            assert notification == ('{}.on_laser_on'.format(name), True)
    depthcamera.disable_streams([DepthCamera.ImageStream.color])
    notification = get_notification()
    # There shouldn't be any streams enabled now...
    assert notification == ('{}.on_disable_streams'.format(name), [])

    if depthcamera_model in (Devices.depthcamera_g2,
                             Devices.depthcamera_z_3d):
        notification = get_notification()
        assert notification == ('{}.on_laser_on'.format(name), False)
        depthcamera.ir_flood_on(True)
        notification = get_notification()
        assert notification == ('{}.on_ir_flood_on'.format(name), True)
        depthcamera.laser_on(False)
        notification = get_notification()
        assert notification == ('{}.on_laser_on'.format(name), False)
        depthcamera.laser_on(True)
        notification = get_notification()
        assert notification == ('{}.on_laser_on'.format(name), True)

    depthcamera.factory_default()
    notification = get_notification()
    assert notification == ('{}.on_factory_default'.format(name), None)

    # Make sure getter methods don't generate any notifications
    depthcamera.enable_streams()
    depthcamera.disable_streams()
    depthcamera.enable_filter('ir_gamma')
    if depthcamera_model in (Devices.depthcamera_g2,
                             Devices.depthcamera_z_3d):
        depthcamera.ir_flood_on()
        depthcamera.laser_on()
        depthcamera.ir_to_rgb_calibration()
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    val = depthcamera.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Now make sure we aren't getting notification callbacks anymore...
    depthcamera.factory_default()
    with pytest.raises(TimeoutError) as execinfo:
        notification = get_notification()
    assert 'Timed out while waiting for notification' in execinfo.value.args[0]

    # Verify hippy raises errors if we call subscribe with invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.subscribe('string')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.subscribe(depthcamera)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.subscribe({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        depthcamera.subscribe(3)
    assert 'Invalid parameter' in execinfo.value.message


# function that enables the camera's stream and reads frames
# continuously until asked to stop
def stream_frames(camera, resolution, streams, need_to_stop, streaming):
    asyncio.set_event_loop(asyncio.new_event_loop())
    # print('Initializing', camera_id, resolution)
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


# class that implements the functions to be used as a context
# manager 'with'
# EB maybe this class should go in the main hippy object directly???
class camera_streaming:
    def __init__(self, camera, resolution=None,
                 streams=[DepthCamera.ImageStream.depth]):
        # print('** 1', camera, resolution)
        streaming_flag = False
        self._need_to_stop = threading.Event()
        self._streaming = threading.Event()
        self._th = threading.Thread(target = stream_frames,
                                    args = (camera, resolution, streams,
                                            self._need_to_stop,
                                            self._streaming))

    def __enter__(self):
        # print('entering')
        self._th.start()
        while not self._streaming.is_set():
            # print('Not yet')
            time.sleep(0.1)
        return self

    def __exit__(self, type, value, traceback):
        # print('exiting', type, value)
        self._need_to_stop.set()
        self._th.join()
        # print('Finished')
