#!/usr/bin/env python

# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A script that uses hippy to grab depth and points frames from the
depthcamera and then saves them to files.
"""

import struct
from hippy import DepthCamera


HEADER_SOHAL = b'\x50\xa1'
HEADER_DEPTHCAMERA = b'\xde\xca'
HEADER_VERSION = 1
NO_ERROR = 0

# Header = namedtuple('Header',
#                     ['magic', 'device', 'version', 'streams', 'error'])
# Frame = namedtuple('Frame', ['width', 'height', 'index',
#                              'stream', 'format', 'timestamp'])

def save_as_raw_image(image):
    """
    Saves the raw image data (including the header and frame) to a file
    """
    header = struct.pack('2s2sBBBx', HEADER_SOHAL, HEADER_DEPTHCAMERA,
                         HEADER_VERSION, image['stream'].value, NO_ERROR)
    frame = struct.pack('HHHBBQ', image['width'], image['height'],
                        0, image['stream'].value, image['format'].value, 0)
    file_name = '{}.raw'.format(image['stream'].name)
    print('*** saving file {}'.format(file_name))
    with open(file_name, 'wb') as file:
        file.write(header)
        file.write(frame)
        file.write(image['data'])


if __name__ == '__main__':

    camera = DepthCamera()
    camera.open()
    depth = DepthCamera.ImageStream.depth
    points = DepthCamera.ImageStream.points
    camera.enable_streams([depth, points])

    data = camera.grab_frame([points, depth])
    # data = camera.grab_frame([depth])
    # data = camera.grab_frame(depth)

    if not isinstance(data, list):
        save_as_raw_image(data)
    else:
        for x in data:
            save_as_raw_image(x)
