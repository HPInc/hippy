
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the projector device.
"""

import enum
import copy
import re
from hippy.hippydevice import HippyDevice


#
#
class Projector(HippyDevice):
    """ The Projector class allows the user to create a Projector object which
    includes a method for each of the SoHal projector commands. The user can
    call these methods to query and control the projector hardware.
    """

    @enum.unique
    class State(enum.Enum):
        """ The State class enumerates the different states the projector
        may be in.
        """
        off = 'off'
        standby = 'standby'
        on = 'on'
        overtemp = 'overtemp'
        flashing = 'flashing'
        transition_to_on = 'transition_to_on'
        transition_to_st = 'transition_to_st'
        hw_fault = 'hw_fault'
        initializing = 'initializing'
        on_no_source = 'on_no_source'
        transition_to_flash = 'transition_to_flash'
        transition_to_grayscale = 'transition_to_grayscale'
        grayscale = 'grayscale'
        fw_upgrade = 'fw_upgrade'
        burn_in = 'burn_in'
        solid_color = 'solid_color'

    @enum.unique
    class SolidColor(enum.Enum):
        """ The SolidColor class enumerates the solid colors the projector
        can project (using the projector.solid_color method).
        """
        off = 'off'
        black = 'black'
        red = 'red'
        green = 'green'
        blue = 'blue'
        cyan = 'cyan'
        magenta = 'magenta'
        yellow = 'yellow'
        white = 'white'

    @enum.unique
    class Illuminant(enum.Enum):
        """ The Illuminant class enumerates the names of the target
        white points the projector supports.
        """
        d50 = 'd50'
        d65 = 'd65'
        d75 = 'd75'
        custom = 'custom'


    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    # Override the HippyDevice method to convert the parameter
    # in the state notification to a Projector.State object
    @classmethod
    def _convert_params(cls, method, params):
        params = params[0]
        method = re.sub(r"@\d+", "", method)
        if method == 'projector.on_state':
            params = Projector.State(params)
        elif method == 'projector.on_solid_color':
            params = Projector.SolidColor(params)
        elif method == 'projector.on_white_point':
            params['name'] = Projector.Illuminant(params['name'])
        return params


    ####################################################################
    ###                     PROJECTOR PUBLIC API                     ###
    ####################################################################

    def brightness(self, brightness=None):
        """
        Gets or sets the projector's brightness.

        Args:
            brightness: An int to set the brightness to. If this parameter
                is not included (or is set to None), this acts as a get
                request and returns the current value. (default None)

        Returns:
            The projector's current brightness value.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=brightness)

    def calibration_data(self):
        """
        Gets the projector's 3d calibration data.

        Returns:
            A dictionary containing the projector's 3d calibration data.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    @classmethod
    def create_2d_keystone_dict(cls, top_left_x, top_left_y, top_right_x,
                                top_right_y, bottom_left_x, bottom_left_y,
                                bottom_right_x, bottom_right_y,
                                top_middle_x=0, top_middle_y=0,
                                bottom_middle_x=0, bottom_middle_y=0,
                                left_middle_x=0, left_middle_y=0,
                                right_middle_x=0, right_middle_y=0,
                                center_x=0, center_y=0):
        """
        A convenience method to create a 2d keystone dictionary.
        Takes in the corner values and optionally takes
        in the middle values which are used to set the edge curvature and
        the center point(if not provided, the middle points and center point
        default to 0's), and creates a full keystone 2d dictionary.

        Returns:
            A keystone_2d dictionary with the provided corner values.
        """
        return {'type' : '2d',
                'value' :
                    {'top_left' : {'x' : top_left_x, 'y' : top_left_y},
                     'top_right' : {'x' : top_right_x, 'y' : top_right_y},
                     'bottom_left' : {'x' : bottom_left_x, 'y' : bottom_left_y},
                     'bottom_right' : {'x' : bottom_right_x,
                                       'y' : bottom_right_y},
                     'top_middle' : {'x' : top_middle_x, 'y' : top_middle_y},
                     'bottom_middle' : {'x' : bottom_middle_x,
                                        'y' : bottom_middle_y},
                     'left_middle' : {'x' : left_middle_x, 'y' : left_middle_y},
                     'right_middle' : {'x' : right_middle_x,
                                       'y' : right_middle_y},
                     'center' : {'x' : center_x, 'y': center_y}}}

    def device_specific_info(self):
        """
        Gets supplementary information about the device such as
        additional version numbers, the manufacturing time, and the
        column serial number.

        Note that this method is only supported for the 1.6 projector.

        Returns:
            A dictionary containing information about the device.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def flash(self, content):
        """
        Puts the projector in flash mode.

        When in flash mode, the projector displays at full brightness with
        no keystone applied.  This mode is time limited with a maximum
        duration of 10 seconds.  If that limit is reached, the projector
        will go back to the on state.  Calling flash again before the limit
        is reached will not add additional time, it will simply return the
        number of seconds remaining.

        Args:
            content: A boolean indicating if content should be displayed. If
                this is True, the actual display content will be shown in
                black and white. If it is False, no content will be shown
                and the flash will be completely white.

        Returns:
            The number of seconds remaining before the flash times out.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=content)

    def grayscale(self):
        """
        Puts the projector in grayscale mode.

        When in grayscale mode, the projector displays at the maximum
        sustainable brightness with the normal keystone applied. The
        projected content is displayed in grayscale.  This mode is not
        time limited.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        self._send_msg()

    def hardware_info(self):
        """
        Gets information on the projector's hardware

        Returns:
            A dictionary containing the projector's hardware information,
            including the input_resolution, refresh_rate, and pixel_density.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def keystone(self, keystone=None):
        """
        Gets or sets the projector's keystone.

        Args:
            keystone: A dictionary containing the keystone values to set. If
                this parameter is not included (or is set to None), this
                acts as a get request and returns the current
                values. (default None)

        Returns:
            A dictionary with the projector's current keystone values.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=keystone)

    def led_times(self):
        """
        Gets the total amount of time (in minutes) the projector has been in
        certain states.

        Note that this method is only supported for the 1.6 projector.

        Returns:
            A dictionary containing keys for specific projector states and
            values set to the number of minutes the projector has been in
            that state.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def manufacturing_data(self):
        """
        Gets the projector's manufacturing data

        Returns:
            A dictionary containing the manufacturing data.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def monitor_coordinates(self):
        """
        Gets the projector's current monitor settings for size and position
        and returns this data as a Rectangle object.

        Returns:
            A dictionary containing the projector's current monitor settings
            for size and position.

        Raises:
            PySproutError: If the projector's rectangle information was not
                found.
        """
        return self._send_msg()

    def on(self):
        """
        Turns the projector on.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        self._send_msg()

    def off(self):
        """
        Turns the projector off (to the standby state).

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        self._send_msg()

    def state(self):
        """
        Gets the current state of the projector

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return Projector.State(self._send_msg())

    def solid_color(self, solid_color=None):
        """
        Turns the projector's solid foreground color on or off. If solid
        color is on, the projector will display the color specified instead
        of the operating system's display information.

        Args:
            solid_color: A SolidColor indicating which color to display.
                         If this parameter is not included (or is set to None),
                         this acts as a get request and returns the current
                         value. (default None)

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        color = None
        if solid_color is not None:
            color = Projector.SolidColor(solid_color).value
        return Projector.SolidColor(self._send_msg(params=color))

    def structured_light_mode(self, structured_light_mode=None):
        """
        Turns the projector's structured light mode on or off. If structured
        light mode is on, the projector will map the top 1920x1080 display
        pixels to the projection with no scaling.

        Note that this method is only supported for the 1.6 projector.

        Args:
            structured_light_mode: A boolean indicating if structured light
                mode should be enabled. If this parameter is not included
                (or is set to None), this acts as a get request and returns
                the current value. (default None)
        Returns:
            A boolean indicating if the projector is in structured light mode.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=structured_light_mode)

    def white_point(self, white_point=None):
        """
        Gets or sets the projector's target white point. When setting the
        white point, this method accepts a dictionary. The dictionary must
        have a 'name' key with the value set to one of the Projector.Illuminant
        values ('d50', 'd65', 'd75', or 'custom').
        The dictionary can optionally have a 'value' key.  This provides a
        way to set a custom white point coordinate.  The 'value' should be set
        to a dictionary with 'x' and 'y' keys detailing the desired chromaticity
        coordinate in the CIE 1931 color space.
        Note that SoHal only uses the 'value' field when the 'name' is set
        to 'custom'.

        For example:
        {'name': 'custom', 'value': {'x': 0.33242, 'y': 0.34743}}

        Note that this method is only supported for the 1.6 projector.

        Args:
            white_point: A dictionary indicating the target white point the
                projector should use.
                If this parameter is not included (or is set to
                None), this acts as a get request and returns the current
                value. (default None)
        Returns:
            A dictionary indicating the projector's current target white point.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        set_wp = copy.deepcopy(white_point)
        if white_point is not None:
            set_wp['name'] = Projector.Illuminant(white_point['name']).value
        new_white_point = self._send_msg(params=set_wp)
        new_white_point['name'] = Projector.Illuminant(new_white_point['name'])
        return new_white_point
