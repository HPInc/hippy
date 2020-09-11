
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the capturestage device.
"""

import enum
import copy
import re
from hippy.hippydevice import HippyDevice


class CaptureStage(HippyDevice):
    """ The CaptureStage class allows the user to create a CaptureStage object
    which includes a method for each of the SoHal capture stage commands. The
    user can call these methods to query and control the capture stage hardware.
    """

    @enum.unique
    class LEDState(enum.Enum):
        """ The LEDState class enumerates the different states the
        capture stage LEDs support.
        """
        off = 'off'
        on = 'on'
        blink_in_phase = 'blink_in_phase'
        blink_off_phase = 'blink_off_phase'


    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    # Override the HippyObject method to convert the parameters
    # in the led_state notifications to the enum values
    @classmethod
    def _convert_params(cls, method, params):
        method = re.sub(r"@\d+", "", method)
        if method == 'capturestage.on_led_state':
            params[0]['amber'] = CaptureStage.LEDState(params[0]['amber'])
            params[0]['red'] = CaptureStage.LEDState(params[0]['red'])
            params[0]['white'] = CaptureStage.LEDState(params[0]['white'])

        params = params[0]
        return params


    ####################################################################
    ###                   CAPTURESTAGE PUBLIC API                    ###
    ####################################################################

    def device_specific_info(self):
        """
        Gets the port the device is currently using.

        Returns:
            A dictionary containing a 'port' key with the value set to
            a string representing the port the device is connect to.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def home(self):
        """
        This method must be called to calibrate the capture stage when items
        is first connected. Calling the tilt method will return errors if the
        device has not been calibrated.
        Calling home will cause the turntable to return to the untilted
        position.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def led_on_off_rate(self, rate=None):
        """
        This method controls the number of seconds the leds stay on and off
        for in the 'blink_in_phase' and 'blink_off_phase' states.

        Args:
            value: A dictionary containing a 'time_on' and/or 'time_off' key
                   with the values set to the number of milliseconds the LEDs
                   should stay on or off for.  If this parameter is not
                   included (or is set to None), this acts as a get request
                   and returns the current values. (default None)

        Returns:
            A dictionary with the capture stage's current values.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=rate)

    def led_state(self, led_state=None):
        """
        Gets or sets state of the three capture stage LEDs.

        Args:
            led_state: A dictionary containing the state for each LED. If this
                   parameter is not included (or is set to None), this
                   acts as a get request and returns the current
                   state. (default None)

                   To set the values, the dictionary should contain three items:
                   'amber' with the value set to the LEDState for the amber LED
                   'red' with the value set to the LEDState for the red LED
                   'white' with the value set to the LEDState for the white LED

                    Note that all three color keys do not have to be
                    provided. Any item that is not included will not be changed.

        Returns:
            A dictionary containing the current state of the LEDs.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        state = copy.deepcopy(led_state)
        if state is not None:
            if 'amber' in state:
                state['amber'] = CaptureStage.LEDState(state['amber']).value
            if 'red' in state:
                state['red'] = CaptureStage.LEDState(state['red']).value
            if 'white' in state:
                state['white'] = CaptureStage.LEDState(state['white']).value

        cur_state = self._send_msg(params=state)
        cur_state['amber'] = CaptureStage.LEDState(cur_state['amber'])
        cur_state['red'] = CaptureStage.LEDState(cur_state['red'])
        cur_state['white'] = CaptureStage.LEDState(cur_state['white'])
        return cur_state

    def rotate(self, degrees=None):
        """
        Rotates the top surface of the capture stage.

        Args:
            degrees: A floating point number with the number of degrees to
                     rotate. If this parameter is not included (or is set
                     to None), this acts as a get request and returns the
                     current value. (default None)

        Returns:
            The numer of degrees the capture stage rotated. Note that there
            is some variation when rotating the unit, so always check the
            return value.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=degrees)

    def rotation_angle(self):
        """
        Gets the current rotation angle for the capture stage in degrees.
        The rotation angle is the sum of all 'rotate' commands since the
        device was connected.

        Returns:
            The capture stage's current rotation angle in degrees.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def tilt(self, degrees=None):
        """
        Gets or sets the capture stage's tilt rotation angle in degrees.
        The capture stage tilts by rotating the bottom portion of the unit.
        When the tilt rotation angle is at 0, the top of the unit will be
        parallel to th bottom. When the tilt ration angle is at 180, the
        top of the unit will be at a 15 degree angle relative to the bottom.

        Args:
            degrees: A floating point number with the tilt rotation angle
                     to use. If this parameter is not included (or is set
                     to None), this acts as a get request and returns the
                     current value. (default None)

        Returns:
            The capture stage's current tilt rotation angle in degrees.
            Note that there is some variation when rotating the unit, so
            always check the return value.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=degrees)
