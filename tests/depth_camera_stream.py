#!/usr/bin/env python

# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

"""
This script uses HP's hippy python module to capture frames from a
Sprout Pro G2 or HP Z 3D Camera depth camera. It shows how to use hippy to
open the depth camera, enable and disable the depth, ir, and color streams,
turn the camera's laser and ir flood light on and off, and grab frames from
one or multiple streams.

After grabbing multiple frames from the color, depth, and ir streams, this
script will display the last frame captured from each stream.
Please note that this requires the numpy and matplotlib open source packages
to display the captured frames.
"""

import numpy as np
from matplotlib import pyplot as plt

from hippy import DepthCamera

camera = DepthCamera()
camera.open()
camera.enable_streams([DepthCamera.ImageStream.color])

# Grab a few frames from the color stream
frames = 10
for i in range(frames):
    print('.', end='', flush=True)
    color_frame = camera.grab_frame(DepthCamera.ImageStream.color)

# Now enable the depth stream and grab frames from both the depth and the
# color streams
camera.enable_streams([DepthCamera.ImageStream.depth])
for i in range(frames):
    print('.', end='', flush=True)
    # Grab frames from each stream individually:
    color_frame = camera.grab_frame_async(DepthCamera.ImageStream.color)
    depth_frame = camera.grab_frame_async(DepthCamera.ImageStream.depth)
    # It's also valid to grab frames from both streams at once:
    frame_list = camera.grab_frame([DepthCamera.ImageStream.color,
                                    DepthCamera.ImageStream.depth])

camera.disable_streams([DepthCamera.ImageStream.color])
camera.enable_streams([DepthCamera.ImageStream.ir])
camera.laser_on(True)

# Grab a few frames from the depth and ir streams
for i in range(frames):
    print('.', end='', flush=True)
    depth_frame = camera.grab_frame(DepthCamera.ImageStream.depth)
    ir_frame = camera.grab_frame(DepthCamera.ImageStream.ir)

camera.laser_on(False)
camera.ir_flood_on(True)
for i in range(frames):
    print('.', end='', flush=True)
    ir_frame = camera.grab_frame(DepthCamera.ImageStream.ir)

camera.disable_streams([DepthCamera.ImageStream.depth,
                        DepthCamera.ImageStream.ir])
camera.ir_flood_on(False)
camera.close()

# Now display the last frame from each stream
if depth_frame:
    dtype = '<u2'
    buffer = np.frombuffer(depth_frame['data'],
                           dtype,
                           depth_frame['width'] * depth_frame['height'],
                           0)
    buffer = buffer.reshape((depth_frame['height'], depth_frame['width']))
    img = plt.imshow(buffer, plt.cm.gray)
    plt.show()
    #with open('depth.raw', 'wb') as fp:
    #    fp.write(depth_frame['data'])

if color_frame:
    buffer = np.frombuffer(color_frame['data'],
                           np.uint8,
                           color_frame['width'] * color_frame['height'] * 3,
                           0)
    buffer = buffer.reshape((color_frame['height'], color_frame['width'], 3))
    img = plt.imshow(buffer)
    plt.show()
    #with open('color.raw', 'wb') as fp:
    #    fp.write(color_frame['data'])

if ir_frame:
    dtype = '<u2'
    buffer = np.frombuffer(ir_frame['data'],
                           dtype,
                           ir_frame['width'] * ir_frame['height'],
                           0)
    buffer = buffer.reshape((ir_frame['height'], ir_frame['width']))
    img = plt.imshow(buffer, plt.cm.gray)
    plt.show()
    #with open('ir.raw', 'wb') as fp:
    #    fp.write(ir_frame['data'])

print('>>> Done!')
