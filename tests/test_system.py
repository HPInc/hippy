
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Pytests for the Hippy system object.
"""

from __future__ import division, absolute_import, print_function

import threading
import copy
import random
import pytest

from hippy import System
from hippy import PySproutError

import check_system_types
import check_device_types
from check_device_types import Devices


notifications = []
condition = threading.Condition()


# pylint: disable=redefined-outer-name
@pytest.fixture
def get_system(request):
    """
    A pytest fixture to initialize and return the System object with
    the given index.
    """
    system = System()
    return system


def test_devices(get_system):
    """
    This method tests the system device's devices() method.
    """
    system = get_system
    devices = system.devices()

    assert isinstance(devices, list)
    connected_devices = []
    depthcameras = []
    for dev in devices:
        check_device_types.check_DeviceInfo(dev)
        if dev['name'] != 'uvccamera':
            device = Devices((dev['vendor_id'], dev['product_id']))
            connected_devices.append(device)
            if dev['name'] == 'depthcamera':
                depthcameras.append(device)

    # Use the depthcameras to determine what other devices should be present
    for camera in depthcameras:
        if camera == Devices.depthcamera_g1:
            expected_devices = [Devices.depthcamera_g1,
                                Devices.desklamp,
                                Devices.hirescamera,
                                Devices.projector_g1,
                                Devices.sbuttons,
                                Devices.touchmat_g1,
                               ]
        elif camera == Devices.depthcamera_g2:
            expected_devices = [Devices.depthcamera_g2,
                                Devices.hirescamera,
                                Devices.projector_g2,
                                Devices.sbuttons,
                                Devices.touchmat_g2,
                               ]
        elif camera == Devices.depthcamera_z_3d:
            expected_devices = [Devices.depthcamera_z_3d,
                                Devices.hirescamera_z_3d,
                               ]

        for item in expected_devices:
            assert item in connected_devices
            connected_devices.remove(item)

    # We didn't add uvccameras to the list, so capturestage should be the
    # only other device that could be present.
    for item in connected_devices:
        assert item == Devices.capturestage


def test_device_ids(get_system):
    """
    This method tests the system device's device_ids() method.
    """
    system = get_system
    devices = system.device_ids()

    connected_devices = []
    depthcameras = []
    for dev in devices:
        check_device_types.check_DeviceID(dev)
        if dev['name'] != 'uvccamera':
            device = Devices((dev['vendor_id'], dev['product_id']))
            connected_devices.append(device)
            if dev['name'] == 'depthcamera':
                depthcameras.append(device)

    # Use the depthcameras to determine what other devices should be present
    for camera in depthcameras:
        if camera == Devices.depthcamera_g1:
            expected_devices = [Devices.depthcamera_g1,
                                Devices.desklamp,
                                Devices.hirescamera,
                                Devices.projector_g1,
                                Devices.sbuttons,
                                Devices.touchmat_g1,
                               ]
        elif camera == Devices.depthcamera_g2:
            expected_devices = [Devices.depthcamera_g2,
                                Devices.hirescamera,
                                Devices.projector_g2,
                                Devices.sbuttons,
                                Devices.touchmat_g2,
                               ]
        elif camera == Devices.depthcamera_z_3d:
            expected_devices = [Devices.depthcamera_z_3d,
                                Devices.hirescamera_z_3d,
                               ]

        for item in expected_devices:
            assert item in connected_devices
            connected_devices.remove(item)

    # We didn't add uvccameras to the list, so capturestage should be the
    # only other device that could be present.
    for item in connected_devices:
        assert item == Devices.capturestage


def test_echo(get_system):
    """
    This method tests the system device's echo method.
    """
    system = get_system

    param = "Marco"
    assert system.echo(param) == param

    param2 = {"Polo" : True}
    assert system.echo(param2) == param2

    assert system.echo("test") == "test"
    assert system.echo(567) == 567

def test_hardware_ids(get_system):
    """
    This method tests the system device's hardware_ids method.
    """
    system = get_system

    hardware_ids = system.hardware_ids()

    assert isinstance(hardware_ids, dict)
    assert 'sprout_projector' in hardware_ids
    assert 'sprout_touchscreen' in hardware_ids
    assert len(hardware_ids['sprout_projector']) == 2
    assert len(hardware_ids['sprout_touchscreen']) == 5

def test_is_locked(get_system):
    """
    This method tests the system device's is_locked method.
    """
    system = get_system

    state = system.is_locked()

    assert isinstance(state, str)
    assert state in ['locked', 'unlocked', 'unknown']

def test_list_displays(get_system):
    """
    This method tests the system device's list_displays method.
    """
    system = get_system

    displays = system.list_displays()
    # While not necessarily required, in our cases we should always have at
    # least one display.
    assert len(displays) > 0
    check_system_types.check_DisplayInfo(displays)

def test_session_id(get_system):
    """
    This method tests the system device's session_id method.
    """

    system = get_system

    session_id = system.session_id()

    assert isinstance(session_id, int)
    assert (session_id > 0 and session_id < 0xFFFFFFFF)

def test_supported_devices(get_system):
    """
    This method tests the system device's supported_devices method.
    """
    system = get_system

    supported = system.supported_devices()

    assert isinstance(supported, list)
    dev_names = ['capturestage', 'depthcamera', 'desklamp', 'hirescamera',
                 'projector', 'sbuttons', 'touchmat']
    assert all(dev in supported for dev in dev_names)


def test_temperatures(get_system):
    """
    This method tests the system device's temperatures method.
    """
    system = get_system

    temperatures = system.temperatures()
    # Make sure we have all of the expected temperature sensors based on the
    # connected devices.
    devices = system.device_ids()
    check_system_types.check_TemperatureInfoList(temperatures, devices)

    # Now test passing in the devices one at a time and verify we only get
    # sensor info for that device.
    for dev in devices:
        dev_name = '{}@{}'.format(dev['name'], dev['index'])
        temperatures = system.temperatures(dev_name)
        check_system_types.check_TemperatureInfoList(temperatures, [dev])
        temperatures = system.temperatures([dev_name])
        check_system_types.check_TemperatureInfoList(temperatures, [dev])

    # Test invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        system.temperatures(['moo'])
    assert 'Invalid device' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.temperatures([30, 40])
    assert 'Invalid device' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.temperatures([{'depthcamera': 0}])
    assert 'Invalid device' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.temperatures('fake')
    assert 'Invalid device' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.temperatures([['hirescamera']])
    assert 'Invalid device' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.temperatures({'hirescamera': 1})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.temperatures(42)
    assert 'Invalid parameter' in execinfo.value.message
    # hippy auto converts a single string to a list, so use _send_msg to
    # send a string and validate the error
    with pytest.raises(PySproutError) as execinfo:
        system._send_msg('temperatures', 'meow')  # pylint: disable=protected-access
    assert 'Invalid parameter' in execinfo.value.message


def test_camera_3d_mapping(get_system):
    """
    This method tests the system device's camera_3d_mapping method.
    """
    system = get_system

    devices = system.device_ids()
    for dev in devices:
        if dev['name'] == 'depthcamera' and dev['index'] == 0:
            depthcamera = dev
            break
    depthcam = Devices((depthcamera['vendor_id'],
                        depthcamera['product_id']))

    allowed = [('depthcamera', 'rgb', 'hirescamera', 'rgb'),
               ('depthcamera', 'ir', 'depthcamera', 'rgb')]
    if depthcam == Devices.depthcamera_g2:
        allowed.append(('hirescamera', 'rgb', 'depthcamera', 'rgb'))
    else:
        allowed.append(('depthcamera', 'ir', 'hirescamera', 'rgb'))
    # TODO Fix this so it doesn't always assume both indexes are 0
    params = [{"from": {"index": 0, "name": item[0], "stream": item[1]},
               "to": {"index": 0, "name": item[2], "stream": item[3]}}
              for item in allowed]

    # If we have a realsense camera, the camera_3d_mapping method isn't
    # available
    if depthcam == Devices.depthcamera_g1:
        for param in params:
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            assert 'not supported' in str(execinfo.value)
        return

    # Test the valid cases...
    for param in params:
        map_3d = system.camera_3d_mapping(param)
        check_system_types.check_Camera3DMapping(map_3d)
        assert map_3d['from']['camera'] == param['from']
        assert map_3d['to']['camera'] == param['to']

    # Now lets test error cases...
    with pytest.raises(TypeError):
        system.camera_3d_mapping()
    # Test passing in invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        system.camera_3d_mapping('fake')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.camera_3d_mapping(30)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.camera_3d_mapping({})
    assert 'Invalid parameter' in execinfo.value.message

    # Test dictionaries that don't include all required fields
    param = {"from": {"index": 0, "name": 'depthcamera', "stream": 'rgb'}}
    with pytest.raises(PySproutError) as execinfo:
        system.camera_3d_mapping({})
    assert 'Invalid parameter' in execinfo.value.message
    param = {"to": {"index": 0, "name": 'depthcamera', "stream": 'rgb'}}
    with pytest.raises(PySproutError) as execinfo:
        system.camera_3d_mapping({})
    assert 'Invalid parameter' in execinfo.value.message

    # Test sending a valid input minus one required key...
    for item in params:
        for direction in ['from', 'to']:
            for key in ['index', 'name', 'stream']:
                param = copy.deepcopy(item)
                # Remove this item from the dictionary!
                del param[direction][key]
                with pytest.raises(PySproutError) as execinfo:
                    system.camera_3d_mapping(param)
                assert 'Invalid parameter' in execinfo.value.message

    for item in params:
        for direction in ['from', 'to']:
            # Test an out of range 'from' index... (this assumes there aren't
            # 20+ hires/depth cameras connected)
            param = copy.deepcopy(item)
            param[direction]['index'] = random.randint(20, 999)
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            err = 'Device {}@{} not found'.format(param[direction]['name'],
                                                  param[direction]['index'])
            assert err in execinfo.value.message

            # Test sending invalid indexes
            param = copy.deepcopy(item)
            param[direction]['index'] = 'test'
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            assert 'invalid index' in execinfo.value.message
            param = copy.deepcopy(item)
            param[direction]['index'] = {}
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            assert 'invalid index' in execinfo.value.message

            # Test invalid names
            param = copy.deepcopy(item)
            param[direction]['name'] = 'fake'
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            err = '"{}" device {} not supported'.format(direction, 'fake')
            assert err in execinfo.value.message
            param = copy.deepcopy(item)
            param[direction]['name'] = {}
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            err = '"{}" device {} not supported'.format(direction, {})
            assert err in execinfo.value.message
            param = copy.deepcopy(item)
            param[direction]['name'] = 0
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            err = '"{}" device {} not supported'.format(direction, 0)
            assert err in execinfo.value.message
            param = copy.deepcopy(item)
            param[direction]['name'] = None
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            err = '"{}" device {} not supported'.format(direction, None)
            assert err in execinfo.value.message

            # Test invalid streams
            param = copy.deepcopy(item)
            param[direction]['stream'] = 'fake'
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            assert 'not supported' in execinfo.value.message
            param = copy.deepcopy(item)
            param[direction]['stream'] = 27
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            assert 'not supported' in execinfo.value.message
            param = copy.deepcopy(item)
            param[direction]['stream'] = None
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            assert 'not supported' in execinfo.value.message
            param[direction]['stream'] = {}
            with pytest.raises(PySproutError) as execinfo:
                system.camera_3d_mapping(param)
            assert 'not supported' in execinfo.value.message

    # Test all of the invalid camera stream combinations to be sure they raise
    # errors.
    names = ['depthcamera', 'hirescamera']
    streams = ['rgb', 'ir', 'depth', 'points']
    for from_name in names:
        for from_stream in streams:
            for to_name in names:
                for to_stream in streams:
                    param = {"from": {"index": 0, "name": from_name,
                                      "stream": from_stream},
                             "to": {"index": 0, "name": to_name,
                                    "stream": to_stream}}
                    if param not in params:
                        with pytest.raises(PySproutError) as execinfo:
                            system.camera_3d_mapping(param)
                        assert 'not supported' in execinfo.value.message

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


def test_notifications(get_system):
    """
    This method tests the system device's subscribe and unsubscribe methods.
    """
    system = get_system

    val = system.subscribe(callback)
    assert isinstance(val, int)
    assert val == 1

    # TODO(EB) We'll need a manual test for on_device_connected,
    # on_device_disconnected, and on_power_state

    val = system.unsubscribe()
    assert isinstance(val, int)
    assert val == 0

    # Verify hippy raises errors if we call subscribe with invalid parameters
    with pytest.raises(PySproutError) as execinfo:
        system.subscribe('string')
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.subscribe(system)
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.subscribe({})
    assert 'Invalid parameter' in execinfo.value.message
    with pytest.raises(PySproutError) as execinfo:
        system.subscribe(3)
    assert 'Invalid parameter' in execinfo.value.message
