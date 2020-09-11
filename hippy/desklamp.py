
# Copyright 2016-2019 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the desklamp device.
"""

import enum
import re
from hippy.hippydevice import HippyDevice


class DeskLamp(HippyDevice):
    """ The DeskLamp class allows the user to create a DeskLamp object
    which includes a method for each of the SoHal desklamp commands. The
    user can call these methods to query and control the desklamp hardware.
    """

    @enum.unique
    class State(enum.Enum):
        """ The State class enumerates the different states of the desk lamp.
        """
        high = 'high'
        low = 'low'
        off = 'off'


    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    # Override the HippyDevice method to convert the parameter
    # in the state notification to a DeskLamp.State object
    @classmethod
    def _convert_params(cls, method, params):
        params = params[0]
        method = re.sub(r"@\d+", "", method)
        if method == 'desklamp.on_state':
            params = DeskLamp.State(params)
        return params


    ####################################################################
    ###                       DESKLAMP PUBLIC API                    ###
    ####################################################################

    def high(self):
        """
        Turns the DeskLamp LEDs to high intensity.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        self._send_msg()

    def low(self):
        """
        Turns the DeskLamp LEDs to low intensity.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        self._send_msg()

    def off(self):
        """
        Turns the DeskLamp LEDs off.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        self._send_msg()

    def state(self):
        """
        Gets the current state of the DeskLamp.

        Returns:
            The current state of the DeskLamp, as a DeskLamp.State object.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        state = self._send_msg()
        return DeskLamp.State(state)
