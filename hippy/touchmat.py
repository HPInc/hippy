
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the touchmat device.
"""

import enum
import re
from hippy.hippydevice import HippyDevice


class TouchMat(HippyDevice):
    """ The TouchMat class allows the user to create a TouchMat object which
    includes a method for each of the SoHal touchmat commands. The user can
    call these methods to query and control the touchmat hardware.
    """

    @enum.unique
    class ActivePenRange(enum.Enum):
        """ The ActivePenRange class enumerates the allowed options for the
        touchmat's active_pen_range.
        """
        five_mm = 'five_mm'
        ten_mm = 'ten_mm'
        fifteen_mm = 'fifteen_mm'
        twenty_mm = 'twenty_mm'

    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    # Override the HippyDevice method to convert the parameters
    # in the on_active_pen_range notifications to the enum values
    @classmethod
    def _convert_params(cls, method, params):
        method = re.sub(r"@\d+", "", method)
        if method == 'touchmat.on_active_pen_range':
            params = TouchMat.ActivePenRange(params[0])
        else:
            params = params[0]
        return params


    ####################################################################
    ###                     TOUCHMAT PUBLIC API                      ###
    ####################################################################

    def active_area(self, active_area=None):
        """
        Gets or sets the TouchMat's active area.
        The active area is dictionary with 'enabled', 'start', and 'end'
        key/value pairs. If one of these items is not included, the current
        setting for that item will not be modified.

        {'enabled': boolean, 'start': {'x': int, 'y': int}, 'end': {'x': int,
        'y': int}}

        'enabled': If this is true, input will only be accepted in the
        region between the start and end points. If it is false, input will be
        accepted from the entire touchmat, regardless of the start and end
        point values.

        'start': a dictionary detailing the point on the TouchMat where input
        should start being accepted. Any input to the left of 'x' or above 'y'
        will be ignored whenever the active area is enabled. The 'x' value can
        be between 0 and 15360 and the 'y' value can be between 0 and 8640.

        'end': a dictionary detailing the point on the TouchMat where input
        should stop being accepted. Any input to the right of 'x' or below 'y'
        will be ignored whenever the active area is enabled. The 'x' value can
        be between 0 and 15360 and the 'y' value can be between 0 and 8640.
        However, the 'end' values must be greater than the 'start' values.

        Note that this active_area method is not available on all models of the
        Sprout.

        Args:
            active_area: A dictionary with the values to set the TouchMat's
                         active area to. If this parameter is not included
                         (or is set to None), this acts as a get request and
                         returns the TouchMat's current active area.

        Returns:
            The current active area of the TouchMat, as a dictionary.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=active_area)

    def active_pen_range(self, active_pen_range=None):
        """
        Gets or sets the height where the TouchMat starts detecting the
        active pen.

        Note that this active_pen_range method is not available on all models
        of the Sprout.

        Args:
            active_pen_range: A TouchMat.ActivePenRange value indicating the
                              threshold height where the active pen should
                              go into or out of range.
                              If this parameter is not included (or is set
                              to None), this acts as a get request and returns
                              the current value.

        Returns:
            The current active pen range, as a TouchMat.ActivePenRange value.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        pen_range = None
        if active_pen_range is not None:
            pen_range = TouchMat.ActivePenRange(active_pen_range).value
        new_range = self._send_msg(params=pen_range)
        return TouchMat.ActivePenRange(new_range)

    def calibrate(self):
        """
        Calibrates the touchmat. Note that this refers to calibrating the
        thresholds at which signals are considered input. This is not related
        to xy position calibration.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def device_palm_rejection(self, device_palm_rejection=None):
        """
        Gets or sets the boolean indicating if the TouchMat's internal
        palm rejection is enabled.  A value of true means the TouchMat will
        only send either the touch or the active pen signal to the operating
        system at a given time. A value of false means the touchmat will send
        both the touch and active pen signals to the operating system
        simultaneously, and the operating system will determine which signal
        to accept input from at a given time.

        Note that the TouchMat's palm rejection is only active when both
        touch and active pen are enabled (i.e. the state is
        {'touch': True, 'active_pen': True}).

        Args:
            device_palm_rejection: A boolean indicating if the device's
                                   internal palm rejection should be enabled.
                                   If this parameter is not included (or is
                                   set to None), this acts as a get request and
                                   returns the current value.

        Returns:
            If the TouchMat's internal palm rejection is currently enabled,
            as a boolean.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=device_palm_rejection)

    def hardware_info(self):
        """
        Gets information on the touchmat's hardware. The dictionary this
        method returns includes a 'size' item which details the physical width
        and height, in inches, of the touch-sensitive area of the touchmat
        (the white portion of the mat, not including the darker border).

        Returns:
            A dictionary containing the touchmat's hardware information.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def palm_rejection_timeout(self, palm_rejection_timeout=None):
        """
        This setting is used when the touchmat is handling palm rejection.
        When the touchmat is ignoring touch input in favor of active pen input,
        all input must stop for `palm_rejection_timeout` milliseconds before
        the mat will begin accepting touch input again.  If the touchmat
        receives any input (touch or pen) before the full timeout has elapsed,
        the clock is reset and the timeout starts over.

        The `palm_rejection_timeout` will return to the default value whenever
        the touchmat loses power (when the touchmat is disconnected or when the
        system restarts). By default the `palm_rejection_timeout` is set to
        500 ms, but this may change in a future firmware update.

        Args:
            palm_rejection_timeout: An integer indicating the number of
                                    milliseconds that must pass with no input
                                    before the touchmat starts accepting touch
                                    input again.
                                    If this parameter is not included (or is
                                    set to None), this acts as a get request and
                                    returns the current value.

        Returns:
            The touchmat's current palm_rejection_timeout value in milliseconds.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=palm_rejection_timeout)

    def reset(self):
        """
        Reboots the touchmat. This is  equivalent to physically undocking and
        redocking the device.
        As such, it will cause SoHal to send `touchmat.on_device_disconnected`,
        `system.on_device_disconnected`, `touchmat.on_device_connected`,
        and `system.on_device_connected` notifications.

        Additionally, the behavior should be identical to when the touchmat
        is physically undocked and redocked. The device will be closed when the
        the `on_device_disconnected` notifications are sent.  By the time the
        `on_device_connected` notifications are sent, all settings will be
        restored to the hardware's default values.  After the connected
        notifications, the touchmat will need to be opened and any desired
        settings will need to be set.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def state(self, state=None):
        """
        Gets or sets the current state of the TouchMat.
        To set the state, provide a dictionary with keys of 'touch'
        and/or 'active_pen' and boolean values.  A value of True indicates
        that the TouchMat should accept input from that source, and a value
        of False indicates that the TouchMat should ignore input from that
        source.  If one of the keys is not included, the current setting for
        that source will not be modified.

        For example, setting the state to:
        {'touch' : True, 'active_pen' : False}
        would enable touch input and disable input from the active pen.

        Note that active_pen mode is not available on all models of the Sprout.

        Args:
            state: A dictionary indicating which input sources the TouchMat
                   should enable. If this parameter is not included (or is set
                   to None), this acts as a get request and returns the
                   TouchMat's current state.

        Returns:
            The current state of the TouchMat, as a dictionary.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=state)
