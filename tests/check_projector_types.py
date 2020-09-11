#!/usr/bin/env python

# Copyright 2018-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" This file includes methods to check the various types defined in the SoHal
 Projector documentation. It is intended to aid in the type checking for the
 hippy tests. Each method in this file takes in a value and asserts that the
 value is up to spec with the type definition.  The methods names are
 `check_Type` where Type is the SoHal type.
"""

from xml.etree import ElementTree


def check_CalibrationData(value):
    """
    Asserts that the parameter provided matches the specification for a
    CalibrationData object as defined in the SoHal documentation.
    """
    assert isinstance(value, dict)
    # Make sure this dictionary contains only the expected keys
    assert set(value) == {'cam_cal', 'cam_cal_hd', 'proj_cal', 'proj_cal_hd'}

    assert isinstance(value['cam_cal'], str)
    assert isinstance(value['cam_cal_hd'], str)
    assert isinstance(value['proj_cal'], str)
    assert isinstance(value['proj_cal_hd'], str)

    # So the spec only says they are strings, but we know these should
    # actually be xml files. Let's double check that we can parse out each xml
    # file and that it contains the expected child nodes
    expected = ['version', 'camera_model', 'cx', 'cy', 'f', 'sx', 'kappa1',
                'resX', 'resY', 'MotionType', 'Pose']
    # Note we have to use a hack here where we wrap each file in a 'root' node.
    # This is because the calibration files aren't wrapped in one overall
    # element, which means the ElementTree is throwing 'junk after document'
    # errors when we try to parse without this. But since we're checking that
    # we get each expected child this shouldn't be a big deal.
    tree = ElementTree.fromstring("<root>" +value['cam_cal'] + "</root>")
    children = []
    for child in list(tree):
        children.append(child.tag)
    assert set(children) == set(expected)

    tree = ElementTree.fromstring("<root>" +value['cam_cal_hd'] + "</root>")
    children = []
    for child in list(tree):
        children.append(child.tag)
    assert set(children) == set(expected)

    expected = ['version', 'camera_model', 'cx', 'cy', 'f', 'sx', 'kappa1',
                'nx', 'ny', 'nz', 'ox', 'oy', 'oz', 'ax', 'ay', 'az',
                'px', 'py', 'pz', 'MotionType', 'Pose', 'phase_error']
    tree = ElementTree.fromstring("<root>" +value['proj_cal'] + "</root>")
    children = []
    for child in list(tree):
        children.append(child.tag)
    assert set(children) == set(expected)

    tree = ElementTree.fromstring("<root>" +value['proj_cal_hd'] + "</root>")
    children = []
    for child in list(tree):
        children.append(child.tag)
    assert set(children) == set(expected)
