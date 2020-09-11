
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the sbuttons device.
"""

import enum
import copy
import re
from hippy.hippydevice import HippyDevice


class SButtons(HippyDevice):
    """ The SButtons class allows the user to create a SButtons object which
    includes a method for each of the SoHal sbuttons commands. The user can
    call these methods to query and control the sbuttons hardware.
    """

    @enum.unique
    class ButtonID(enum.Enum):
        """ The ButtonID class enumerates the different sbuttons.
        """
        left = 'left'
        center = 'center'
        right = 'right'


    @enum.unique
    class LEDColor(enum.Enum):
        """ The LEDColor class enumerates the different colors allowed for
        each sbuttons LED.
        """
        orange = 'orange'
        white = 'white'
        white_orange = 'white_orange'


    @enum.unique
    class LEDMode(enum.Enum):
        """ The LEDMode class enumerates the different modes the sbuttons
        LEDs may be in.
        """
        off = 'off'
        on = 'on'
        pulse = 'pulse'
        controlled_on = 'controlled_on'
        controlled_off = 'controlled_off'
        breath = 'breath'


    @enum.unique
    class ButtonPressType(enum.Enum):
        """ The ButtonPressType class enumerates the different types of
        button press events.
        """
        tap = 'tap'
        hold = 'hold'


    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    # Override the HippyDevice method to convert the parameters
    # in the led_state and button press notifications to the enum values
    @classmethod
    def _convert_params(cls, method, params):
        method = re.sub(r"@\d+", "", method)
        if method == 'sbuttons.on_led_state':
            params[0] = SButtons.ButtonID(params[0])
            params[1]['color'] = SButtons.LEDColor(params[1]['color'])
            params[1]['mode'] = SButtons.LEDMode(params[1]['mode'])
        elif method == 'sbuttons.on_button_press':
            params = params[0]
            params['id'] = SButtons.ButtonID(params['id'])
            params['type'] = SButtons.ButtonPressType(params['type'])
        else:
            params = params[0]
        return params


    ####################################################################
    ###                     SBUTTONS PUBLIC API                      ###
    ####################################################################

    def hold_threshold(self, threshold=None):
        """
        Gets or sets the hold threshold.

        The hold threshold is used to differentiate between a short button
        press (tap) and a long button press (hold) event.

        Args:
            value: An int to set the hold threshold to. If this parameter
                is not included (or is set to None), this acts as a get
                request and returns the current value. (default None)

        Returns:
            The current hold threshold.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=threshold)

    def led_on_off_rate(self, rate=None):
        """
        Gets or sets the LED on off rate.

        Args:
            value: An int to set the LED on off rate to. If this parameter
                is not included (or is set to None), this acts as a get
                request and returns the current value. (default None)

        Returns:
            The current LED on off rate.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=rate)

    def led_pulse_rate(self, rate=None):
        """
        Gets or sets the LED pulse rate.

        The LED pulse rate is the rate the LEDs turn on and off at
        when in the pulse state.

        Args:
            value: An int to set the led pulse rate to. If this parameter
                is not included (or is set to None), this acts as a get
                request and returns the current value. (default None)

        Returns:
            The current LED pulse rate.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=rate)

    def led_state(self, led, led_state=None):
        """
        Gets or sets the current color and mode for the given LED.

        Args:
            led: A ButtonId indicating which LED to get or set the state for.
            state: A dictionary containing the color and mode values to set.
                If this parameter is not included (or is set to None), this
                acts as a get request and returns the current
                state. (default None)

                To set the values, the dictionary should contain two items:
                'color' with the value set to an LEDColor
                'mode' with the value set to an LEDMode

                Note that both the 'color' and 'mode' keys do not have to be
                provided. Any item that is not included will not be changed.

                For example:
                {'color' : SButtons.LEDColor.white,
                 'mode' : SButtons.LEDMode.on}
                or
                {'color' : 'white', 'mode' : 'on'}
                Will turn the given LED on in solid white.

                {'color' : SButtons.LEDColor.orange}
                Will set the color to orange and will not change the current
                mode for the given LED.

                {'mode' : 'off'}
                Will turn off any color that is currently on for the given LED.

        Returns:
            A dictionary containing the current state of the LED.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        if led_state is None:
            led = SButtons.ButtonID(led).value
            cur_state = self._send_msg(params=led)
        else:
            led = SButtons.ButtonID(led).value
            state = copy.deepcopy(led_state)
            if 'color' in state:
                state['color'] = SButtons.LEDColor(state['color']).value
            if 'mode' in state:
                state['mode'] = SButtons.LEDMode(state['mode']).value
            cur_state = self._send_msg('led_state', [led, state])
        cur_state['color'] = SButtons.LEDColor(cur_state['color'])
        cur_state['mode'] = SButtons.LEDMode(cur_state['mode'])
        return cur_state
