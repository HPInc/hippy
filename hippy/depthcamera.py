
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the depthcamera device.
"""

import enum
import struct
import re
from hippy.hippycamera import HippyCamera
from hippy import PySproutError


class DepthCamera(HippyCamera):
    """
    The DepthCamera class allows the user to create a DepthCamera object
    which includes a method for each of the SoHal depthcamera commands. The
    user can call these methods to query and control the depth camera hardware.
    """

    def __init__(self, index=None, host=None, port=None):
        """Creates a DepthCamera object.

        Args:
            index: An integer indicating the device index to use when sending
                messages to SoHal. This index is used to specify which device
                when SoHal is controlling multiple devices of the same class.
                For example, if the index is set to 1, an 'open' command would
                be sent as 'depthcamera@1.open' which would tell SoHal to open
                the depth camera with index=1. If SoHal does not have a camera
                with an index of 1 when open is called, SoHal will return
                a 'Device Not Found' error. Note that a list of all connected
                devices and their indexes can be queried using the
                devices() method in the System class.

                If this parameter is not included (or is set to None), the
                index will not be included in the message sent to SoHal (e.g.
                'depthcamera.open', which is an alias for 'depthcamera@0.open').
                In typical circumstances there will only be one device of each
                type connected, so this index will not be required.
                (default None)

            host: A string indicating the ip address of the SoHal server. If
                this parameter is not included (or is set to None), the default
                address will be used. (default None)

            port: The port of the SoHal server. If this parameter is not
                included (or is set to None), the default port will be used.
                (default None)
        """
        super(DepthCamera, self).__init__(index, host, port)


    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    # # Override the HippyDevice method to convert the parameters
    # # in some of the notifications to ImageStream objects
    # @classmethod
    # def _convert_params(cls, method, params):
        # return super(DepthCamera, cls)._convert_params(method, params)


    ####################################################################
    ###                    DEPTHCAMERA PUBLIC API                    ###
    ####################################################################

    def ir_flood_on(self, ir_flood_on=None):
        """
        Gets or sets the state of the camera's infrared flood light.

        Note that this method is only supported for the 1.6 depth camera.

        Args:
            ir_flood_on: A boolean indicating if the ir flood light should be
                turned on or off. If this parameter is not included
                (or is set to None), this acts as a get request and
                returns a boolean with the current value. (default None)

        Raises:
            PySproutError: If SoHal responded to the request with an error
                           message.
        """
        return self._send_msg(params=ir_flood_on)

    def laser_on(self, laser_on=None):
        """
        Gets or sets the state of the camera's laser.

        Note that this method is only supported for the 1.6 depth camera.

        Args:
            laser_on: A boolean indicating if the laser should be turned
                on or off. If this parameter is not included (or is
                set to None), this acts as a get request and returns
                a boolean with the current value. (default None)

        Raises:
            PySproutError: If SoHal responded to the request with an error
                           message.
        """
        return self._send_msg(params=laser_on)

    def ir_to_rgb_calibration(self):
        """
        Gets the IR to RGB depthcamera calibration

        Note that this method is only supported for the 1.6 depth camera.

        Returns:
            The IrRGBCalibration dictionary

        Raises:
            PySproutError: If SoHal responded to the request with an error
                           message.
        """
        return self._send_msg()

    def mirror_frame(self, mirror_frame=None):
        """
        Gets or sets the camera's mirror frame value.

        The mirror frame value controls if the image is flipped horizontally
        (about the y axis).

        Args:
            mirror_frame: A dictionary containing some or all of the active
                camera streams as keys and True or False as values,
                indicating if the images should be mirrored or not.
                If this parameter is not included (or is set to None),
                this acts as a get request and returns the current
                value. (default None)

        Returns:
            The camera's current mirror frame value for each active
            camera stream

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=mirror_frame)
