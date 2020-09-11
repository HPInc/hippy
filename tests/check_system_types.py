#!/usr/bin/env python

# Copyright 2017-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" This file includes methods to check the various types defined in the SoHal
 System documentation. It is intended to aid in the type checking for the hippy
 tests. Each method in this file takes in a value and asserts that the value
 is up to spec with the type definition.  The methods names are `check_Type`
 where Type is the SoHal type.
"""

import check_device_types


def check_Camera3DMapping(value):
    """
    Asserts that the parameter provided matches the specification for a
    Camera3DMapping object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'from', 'matrix_transformation', 'to'}

    check_CameraParameters(value['from'])

    assert isinstance(value['matrix_transformation'], list)
    assert len(value['matrix_transformation']) == 4
    for item in value['matrix_transformation']:
        assert isinstance(item, list)
        assert len(item) == 4
        for num in item:
            # Values can be 0, which is an int not a float...
            # TODO(EB/SR) we should fix this in SoHal so it returns 0.0
            assert isinstance(num, (float, int))

    check_CameraParameters(value['to'])


def check_CameraParameters(value):
    """
    Asserts that the parameter provided matches the specification for a
    CameraParameters object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'calibration_resolution', 'camera', 'focal_length',
                          'lens_distortion'}

    check_Resolution(value['calibration_resolution'])
    check_CameraStream(value['camera'])
    check_PointFloats(value['focal_length'])
    check_LensDistortion(value['lens_distortion'])


def check_CameraStream(value):
    """
    Asserts that the parameter provided matches the specification for a
    CameraStream object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'index', 'name', 'stream'}

    assert isinstance(value['index'], int)
    assert isinstance(value['name'], str)
    assert value['name'] in ['depthcamera', 'hirescamera']
    assert isinstance(value['stream'], str)
    assert value['stream'] in ['rgb', 'ir', 'depth', 'points']


def check_DisplayInfo(value):
    """
    Asserts that the parameter provided matches the specification for a
    DisplayInfo object as defined in the SoHal documentation.
    """
    assert isinstance(value, list)

    for item in value:
        assert isinstance(item, dict)
        # Make sure this dictionary contains only the expected keys
        assert set(item) == {'hardware_id', 'coordinates', 'primary_display'}
        assert isinstance(item['hardware_id'], str)
        assert len(item['hardware_id']) == 7
        assert isinstance(item['primary_display'], bool)
        check_Rectangle(item['coordinates'])


def check_LensDistortion(value):
    """
    Asserts that the parameter provided matches the specification for a
    LensDistortion object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'center', 'kappa', 'p'}

    check_PointFloats(value['center'])

    assert isinstance(value['kappa'], list)
    for item in value['kappa']:
        assert isinstance(item, float)

    assert isinstance(value['p'], list)
    for item in value['p']:
        assert isinstance(item, float)


def check_PointFloats(value):
    """
    Asserts that the parameter provided matches the specification for a
    PointFloats object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'x', 'y'}

    assert isinstance(value['x'], float)
    assert isinstance(value['y'], float)


def check_Rectangle(value):
    """
    Asserts that the parameter provided matches the specification for a
    Rectangle object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'height', 'width', 'x', 'y'}

    assert isinstance(value['height'], int)
    assert isinstance(value['width'], int)
    assert isinstance(value['x'], int)
    assert isinstance(value['y'], int)


def check_Resolution(value):
    """
    Asserts that the parameter provided matches the specification for a
    Resolution object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'width', 'height'}

    assert isinstance(value['width'], int)
    assert isinstance(value['height'], int)


def check_TemperatureInfo(value):
    """
    Asserts that the parameter provided matches the specification for a
    TemperatureInfo object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'current', 'device', 'max', 'safe', 'sensor_name'}

    assert isinstance(value['current'], float)
    assert isinstance(value['max'], float)
    assert isinstance(value['safe'], float)
    check_TemperatureSensor(value['sensor_name'])


def check_TemperatureInfoList(temperatures, devices):
    """
    Validates that the provided list includes temperature information for all
    expected sensors for the given devices.
    temperatures should be a list of TemperatureInfo dictionaries, and devices
    should be a list of DeviceID (or DeviceInfo) dictionaries for all of the
    devices that we're expecting temp info for.
    """
    assert isinstance(temperatures, list)
    sensors_found = []
    for temp in temperatures:
        check_TemperatureInfo(temp)
        sensors_found.append((temp['sensor_name'], temp['device']))

    # Make sure we have all of the expected temperature sensors based on the
    # list of devices.
    for dev in devices:
        if dev['name'] == 'uvccamera':
            continue
        device = check_device_types.Devices((dev['vendor_id'],
                                             dev['product_id']))
        expected_sensors = check_device_types.get_device_temp_sensors(device)

        for item in expected_sensors:
            sensor = (item, '{}@{}'.format(dev['name'], dev['index']))
            assert sensor in sensors_found
            sensors_found.remove(sensor)

    assert len(sensors_found) == 0


def check_TemperatureSensor(value):
    """
    Asserts that the parameter provided matches the specification for a
    TemperatureSensor object as defined in the SoHal documentation.
    """
    assert isinstance(value, str)

    assert value in ('depthcamera', 'depthcamera_tec', 'depthcamera_z_3d_tec',
                     'formatter', 'green', 'heatsink', 'hirescamera',
                     'hirescamera_z_3d', 'hirescamera_z_3d_system', 'led',
                     'red')
