
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" This file includes methods to check the various types defined in the SoHal
 Device documentation. It is intended to aid in the type checking for the hippy
 tests. Each method in this file takes in a value and asserts that the value
 is up to spec with the type definition.  The methods names are `check_Type`
 where Type is the SoHal type.
"""

import enum
from hippy import System


class Devices(enum.Enum):
    """
    Enumerates the devices SoHal supports and the Vendor ID and Product ID
    for each device
    """
    capturestage = (0x0403, 0x7838)
    depthcamera_g1 = (0x8086, 0x0A66)
    depthcamera_g2 = (0x2BC5, 0x0405)
    depthcamera_z_3d = (0x2BC5, 0x0406)
    desklamp = (0x03F0, 0x0251)
    hirescamera = (0x05A9, 0xF580)
    hirescamera_z_3d = (0x05C8, 0xF582)
    projector_g1 = (0x03F0, 0x0651)
    projector_g2 = (0x03F0, 0x0751)
    projector_steele = (0x03F0, 0x0E68)
    sbuttons = (0x03F0, 0x0451)
    touchmat_g1 = (0x0596, 0x548)
    touchmat_g2 = (0x04DD, 0x99AC)
    uvccamera_hp_x_3d = (0x05C8, 0xF583)


def find_device_indexes(device_name):
    """
    Finds all instances of the device with the given device_name.
    """
    sys = System()
    ids = sys.device_ids()
    indexes = []
    for item in ids:
        if item['name'] == device_name:
            indexes.append(item['index'])
    if 0 in indexes:
        indexes.append(None)
    return indexes


def firmware_version_at_least(fw_version, major, minor):
    """
    Returns True if the firmware version is equal to or above the provided
    major and minor values.
    """
    if fw_version['major'] > major:
        return True
    if fw_version['major'] == major and fw_version['minor'] >= minor:
        return True
    return False


def get_device_model(device):
    """
    Takes in a HippyDevice object and returns the item from the Devices enum
    that corresponds to that device. Note that this currently does not handle
    general UVC Cameras.
    """
    info = device.info()
    vid_pid = (info['vendor_id'], info['product_id'])
    return Devices(vid_pid)


def get_device_temp_sensors(device):
    """
    Takes in a Devices object (i.e. an item off of the
    check_device_types.Devices enum) and returns a list with the names of the
    temperature sensors that device supports.
    """
    if device == Devices.depthcamera_g2:
        expected_sensors = ['depthcamera', 'depthcamera_tec']
    elif device == Devices.depthcamera_z_3d:
        expected_sensors = ['depthcamera_z_3d_tec']
    elif device == Devices.desklamp:
        expected_sensors = ['depthcamera', 'hirescamera']
    elif device == Devices.hirescamera_z_3d:
        expected_sensors = ['hirescamera_z_3d', 'hirescamera_z_3d_system']
    elif device == Devices.projector_g1:
        expected_sensors = ['formatter', 'heatsink', 'led']
    elif device == Devices.projector_g2:
        expected_sensors = ['green', 'hirescamera', 'led', 'red']
    elif device == Devices.projector_steele:
        expected_sensors = ['green', 'led', 'red']
    else:
        expected_sensors = []
    return expected_sensors


def check_DeviceID(value):
    """
    Asserts that the parameter provided matches the specification for a
    DeviceID object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'index', 'name', 'product_id', 'vendor_id'}

    assert isinstance(value['index'], int)
    assert value['index'] >= 0
    assert isinstance(value['name'], str)
    assert value['name'] in ('capturestage', 'depthcamera', 'desklamp',
                             'hirescamera', 'projector', 'sbuttons',
                             'touchmat', 'uvccamera')
    assert isinstance(value['product_id'], int)
    assert isinstance(value['vendor_id'], int)


def check_DeviceInfo(value):
    """
    Asserts that the parameter provided matches the specification for a
    DeviceInfo object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'fw_version', 'index', 'name', 'product_id',
                          'serial', 'vendor_id'}

    assert isinstance(value['fw_version'], str)
    assert isinstance(value['index'], int)
    assert value['index'] >= 0
    assert isinstance(value['name'], str)
    assert value['name'] in ('capturestage', 'depthcamera', 'desklamp',
                             'hirescamera', 'projector', 'sbuttons',
                             'touchmat', 'uvccamera')
    assert isinstance(value['product_id'], int)
    assert isinstance(value['serial'], str)
    assert isinstance(value['vendor_id'], int)
