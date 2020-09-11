#!/usr/bin/env python

# Copyright 2017-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" This file includes methods to check the various types defined in the SoHal
 HiResCamera documentation. It is intended to aid in the type checking for the
 hippy tests. Each method in this file takes in a value and asserts that the
 value is up to spec with the type definition.  The methods names are
 `check_Type` where Type is the SoHal type.
"""

import check_system_types

def check_CameraKeystone(value):
    """
    Asserts that the parameter provided matches the specification for a
    CameraKeystone object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'enabled', 'value'}

    assert isinstance(value['enabled'], bool)
    check_CameraQuadrilateral(value['value'])


def check_CameraKeystoneTableEntry(value):
    """
    Asserts that the parameter provided matches the specification for a
    CameraKeystoneTableEntry object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'enabled', 'value', 'resolution'}

    assert isinstance(value['enabled'], bool)
    check_CameraQuadrilateral(value['value'])
    check_CameraResolution(value['resolution'])


# If the expected_type field is included, this method will assert that the
# type matches the expected_type.
def check_CameraKeystoneTableEntries(value, expected_type=None):
    """
    Asserts that the parameter provided matches the specification for a
    CameraKeystoneTableEntries object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'type', 'entries'}

    assert isinstance(value['type'], str)
    assert value['type'] in ['default', 'flash_fit_to_mat',
                             'flash_max_fov', 'ram']
    if expected_type is not None:
        assert value['type'] == expected_type

    assert isinstance(value['entries'], list)
    for entry in value['entries']:
        check_CameraKeystoneTableEntry(entry)


def check_CameraQuadrilateral(value):
    """
    Asserts that the parameter provided matches the specification for a
    CameraQuadrilateral object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'top_left', 'top_right', 'bottom_left',
                          'bottom_right'}

    check_Point(value['top_left'])
    check_Point(value['top_right'])
    check_Point(value['bottom_left'])
    check_Point(value['bottom_right'])


def check_CameraResolution(value):
    """
    Asserts that the parameter provided matches the specification for a
    CameraResolution object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'width', 'height', 'fps'}

    assert isinstance(value['width'], int)
    assert isinstance(value['height'], int)
    assert isinstance(value['fps'], int)


def check_CameraDeviceStatus(value):
    """
    Asserts that the parameter provided matches the specification for a
    CameraDeviceStatus object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'generic_get', 'generic_set', 'isp_colorbar',
                          'isp_function', 'isp_fw_boot', 'isp_reset',
                          'isp_restore', 'isp_videostream',
                          'load_lenc_calibration',
                          'load_white_balance_calibration', 'special_get',
                          'special_set', 'thermal_sensor_error',
                          'thermal_shutdown'}
    for item in value:
        check_CameraStatus(value[item])


def check_CameraStatus(value):
    """
    Asserts that the parameter provided matches the specification for a
    CameraStatus object as defined in the SoHal documentation.
    """
    assert isinstance(value, str)
    assert value in ('ok', 'busy', 'error')


def check_Point(value):
    """
    Asserts that the parameter provided matches the specification for a
    Point object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'x', 'y'}

    assert isinstance(value['x'], int)
    assert isinstance(value['y'], int)
