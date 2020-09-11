
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the camera device.
"""

from hippy.hippycamera import HippyCamera


class UVCCamera(HippyCamera):
    """ The UVCCamera class allows the user to create a UVCCamera object
    which includes a method for each of the SoHal uvccamera commands. The
    user can call these methods to query and control the camera hardware.
    """

    ####################################################################
    ###                    UVCCAMERA PUBLIC API                      ###
    ####################################################################

    def camera_index(self):
        """
        Gets the camera's device index

        Returns:
            The index for this camera

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()
