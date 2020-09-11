#!/usr/bin/env python

#
# Copyright 2019 HP Development Company, L.P.
#    HP Confidential
#

""" This file includes methods to check the various types defined in the SoHal
 Camera documentation. It is intended to aid in the type checking for the
 hippy tests. Each method in this file takes in a value and asserts that the
 value is up to spec with the type definition.  The methods names are
 `check_Type` where Type is the SoHal type.
"""

from hippy.hippycamera import HippyCamera


def check_EnableStream(value):
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'port', 'streams'}

    assert isinstance(value['port'], int)
    assert isinstance(value['streams'], list)
    for stream in value['streams']:
        assert isinstance(stream, str)
        assert stream in ['color', 'depth', 'ir', 'points']


def check_StreamingResolution(value):
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'format', 'width', 'height', 'fps', 'stream'}

    assert isinstance(value['width'], int)
    assert isinstance(value['height'], int)
    assert isinstance(value['fps'], int)
    assert isinstance(value['stream'], HippyCamera.ImageStream)
    assert isinstance(value['format'], HippyCamera.ImageFormat)


# EB does it make sense to put the depthcamera steraming function in here???
