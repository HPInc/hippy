
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

#
# Copyright 2016, 2017, 2018 HP Development Company, L.P.
#    HP Confidential
#

""" A module to handle the base hippy device.
"""

from hippy.hippyobject import HippyObject

#
#
class HippyDevice(HippyObject):
    """ The HippyDevice class is the base object which contains the
    functionality that is available for all SoHal devices.
    """

    def __init__(self, index=None, host=None, port=None):
        """Initializes a base class HippyDevice object.

        Args:
            index: An integer indicating the device index to use when sending
                messages to SoHal. This index is used to specify which device
                when SoHal is controlling multiple devices of the same class.
                For example, if the index is set to 1, an 'open' command could
                be sent as 'touchmat@1.open' which would tell SoHal to open
                the touchmat with index=1. If SoHal does not have a touchmat
                with an index of 1 when open is called, SoHal will return a
                'Device Not Found' error. Note that a list of all connected
                devices and their indexes can be queried using the
                devices() method in the System class.

                If this parameter is not included (or is set to None), the
                index will not be included in the message sent to SoHal (e.g.
                'touchmat.open', which is an alias for 'touchmat@0.open').
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
        if index is not None and not isinstance(index, int):
            raise TypeError("Index must be either an integer or 'None'")
        super(HippyDevice, self).__init__(host, port)
        if index is not None:
            # If the user provided an index, update the object name so it
            # includes the @index at the end (eg 'hirescamera@1')
            self._object_name = "{}@{}".format(self._object_name, index)

    def __enter__(self):
        """Together with __exit__ below, it enables the 'with' context manager.
        This allows the following code for any given hippy 'Device':
        with Device() as d:
            # any command that requires an opened 'Device' here
            d.info()
        and the deice will be created and automatically opened before
        entering the block and closed after finishing the block
        """
        self.open()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Together with __enter__ above, it enables the 'with' context manager
        for all devices. Refer to '__enter__' documentation for detailed info
        """
        self.close()

    ####################################################################
    ###                    HIPPY DEVICE METHODS                      ###
    ####################################################################

    def close(self):
        """
        Closes the connection to the device.

        As many clients can be using the same device and open and close
        are expensive functions, SoHal uses a reference counter of clients
        that have the device open. The device will be open when the first
        call to open arrives and will be closed when the last client closes
        it or disconnects.

        Returns:
            The number of clients that have the device open.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def factory_default(self):
        """
        Restores the device to its default settings. The specifics of what
        this includes is device dependent.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        self._send_msg()

    def info(self):
        """
        Gets basic information about the device including the
        firmware version, vendor id, product id, and serial number.

        Returns:
            A dictionary containing information about the device.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def is_device_connected(self):
        """
        This method can be used to query if the device is currently connected.

        Returns:
            True if the device is currently connected, and False if it is not.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def open(self):
        """
        Opens the connection with the device.

        As many clients can be using the same device and open and close
        are expensive functions, SoHal uses a reference counter of clients
        that have the device open. The device will be open when the first
        call to open arrives and will be closed when the last client closes
        it or desconnects.

        Returns:
            The number of clients that have the device open.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def open_count(self):
        """
        Returns the number of clients that have this device open.
        If the open_count is greater than 0, the device is open.

        Returns:
            The number of clients that have the device open.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def temperatures(self):
        """
        Gets a list of the temperatures for any sensors connected to this
        device. If this device does not have any temperature sensors, this
        method will return an empty list.

        Returns:
            A list containing dictionaries with the temperature info for each
            connected sensor.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()
