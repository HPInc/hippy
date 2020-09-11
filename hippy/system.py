
# Copyright 2016-2019 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the system device.
"""

import enum
import re
from hippy.hippyobject import HippyObject


class System(HippyObject):
    """ The System class allows the user to create a System object which
    includes a method for each of the SoHal system commands. The user can
    use this class to access methods and notifications that include information
    on several devices or apply to the system as a whole.
    """

    @enum.unique
    class PowerState(enum.Enum):
        """ The PowerState class enumerates the different power states that
        may be sent in the system.on_power_state notifications.
        """
        display_on = 'display_on'
        display_off = 'display_off'
        display_dimmed = 'display_dimmed'
        log_off = 'log_off'
        resume = 'resume'
        shut_down = 'shut_down'
        suspend = 'suspend'

    @enum.unique
    class SessionChangeEvent(enum.Enum):
        """ The SessionChangeEvent class enumerates the different events
        that may cause a system.on_session_change notification.
        The notification's parameter will include an 'event' field with one
        of the items from this enum.
        For example, an on_session_change notification could have a paramter
        such as:
        {'event': System.SessionChangeEvent.session_lock, 'session_id': 4}
        """
        console_connect = 'console_connect'
        console_disconnect = 'console_disconnect'
        session_logon = 'session_logon'
        session_logoff = 'session_logoff'
        session_lock = 'session_lock'
        session_unlock = 'session_unlock'

    def __init__(self, host=None, port=None):
        """Creates a System object.

        Args:
            host: A string indicating the ip address of the SoHal server. If
                this parameter is not included (or is set to None), the default
                address will be used. (default None)

            port: The port of the SoHal server. If this parameter is not
                included (or is set to None), the default port will be used.
                (default None)
        """
        super(System, self).__init__(host=host, port=port)


    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    # Override the HippyDevice method to convert the parameter
    # in the power notification to a System.PowerState object
    @classmethod
    def _convert_params(cls, method, params):
        params = params[0]
        method = re.sub(r"@\d+", "", method)
        if method == 'system.on_power_state':
            params = System.PowerState(params)
        elif method == 'system.on_session_change':
            params['event'] = System.SessionChangeEvent(params['event'])
        return params


    ####################################################################
    ###                      SYSTEM PUBLIC API                       ###
    ####################################################################

    def camera_3d_mapping(self, mapping):
        """
        Gets the 3D transformation between two device streams.
        Note that only the following transformations are supported:
        `depthcamera` `rgb` to `hirescamera` `rgb`,
        `depthcamera` `ir` to `depthcamera` `rgb`, and
        `hirescamera` `rgb` to `depthcamera` `rgb`

        Args:
            mapping: A dictionary indicating the origin and destination
                devices. This dictionary should contain 'to' and 'from' keys.
                The value for each of these should be a dictionary with
                'name', 'index', and 'stream' fields.
                For example:
                {"from": {"index": 0, "name": "depthcamera", "stream": "rgb"},
                 "to": {"index": 0, "name": "hirescamera", "stream": "rgb"}}

        Returns:
            A dictionary containing the requested 3D transformation
        """
        return self._send_msg(params=mapping)

    def devices(self):
        """
        Gets a list of supported devices connected to the system.
        If fw_version & serial number is not needed, device_ids() can
        be called to get a list of connected devices in less time.

        Returns:
            A list containing dictionaries with the device info for each
            connected device.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def device_ids(self):
        """
        Gets a list of supported devices connected to the system containing
        the most basic information of each device.

        Returns:
            A list containing dictionaries with the device ID info for each
            connected device.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def echo(self, echo):
        """
        Sends an arbitrary item to SoHal, which then echoes the parameter
        back.

        This method can be useful for testing the connection with SoHal.

        Args:
            value: The item to send to SoHal.

        Returns:
            The item SoHal echoed.  This should match the paramter
            passed in.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=echo)

    def hardware_ids(self):
        """
        Gets a dictionary containing hardware ID information, where the keys
        are the hardware component names and the key-value is a list containing
        its respective hardware IDs.

        Returns:
            A dictionary containing the ID information of certain hardware
            components.
        """
        return self._send_msg()

    def is_locked(self):
        """
        Determines the state of the current console session.

        Returns:
            A string indicating the session state. This may be any one of the
            following strings: ['locked', 'unlocked', 'unknown'].
        """
        return self._send_msg()

    def list_displays(self):
        """
        Gets information on all connected displays.

        Returns:
            A list where each item in the list is a dictionary containing the
            hardware id, the coordinates for one display, and whether or not
            that display is also the primary display.
        """
        return self._send_msg()

    def session_id(self):
        """
        Gets the current active console session ID.

        Returns:
            The current active console session ID.
        """
        return self._send_msg()

    def supported_devices(self):
        """
        Gets a list with the names of all devices SoHal supports.

        Returns:
            A list with the names of the supported devices.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def temperatures(self, devices=None):
        """
        Gets a list of the temperature sensor information for some or all
        of the devices connected to the system.

        Args:
            value: A list of device names from which to query the temperature
                information. If this parameter is not included (or is set to
                None), this method will return the temperature information for
                all connected devices. (default None)

        Returns:
            A list containing dictionaries with the temperature information
            for sensors on each requested device.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        # Allow the user to pass in a string for just one device
        if isinstance(devices, str):
            devices = [devices]
        dev_list = None
        if devices is not None:
            # The parameter we send out needs to be a list inside of a list,
            # because it's a list of parameters and the first parameter is a
            # list object.
            dev_list = [devices]
        return self._send_msg(params=dev_list)
