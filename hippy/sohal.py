
# Copyright 2016-2019 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the sohal device.
"""

from hippy.hippyobject import HippyObject


class SoHal(HippyObject):
    """ The SoHal class allows the user to create a SoHal object.
    This object can be used to access high level methods and notifications
    for the SoHal application.
    """

    def __init__(self, host=None, port=None):
        """Creates a SoHal object.

        Args:
            host: A string indicating the ip address of the SoHal server. If
                this parameter is not included (or is set to None), the default
                address will be used. (default None)

            port: The port of the SoHal server. If this parameter is not
                included (or is set to None), the default port will be used.
                (default None)
        """
        super(SoHal, self).__init__(host=host, port=port)


    ####################################################################
    ###                       SOHAL PUBLIC API                       ###
    ####################################################################

    def exit(self):
        """
        Gets a list of supported devices connected to the system.

        Returns:
            A list containing dictionaries with the device info for each
            connected device.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def log(self, log=None):
        """
        Gets or sets the SoHal logging information.
        To set the values, provide a dictionary with a keys of 'file'
        and/or 'level'.  The 'file' key should have a string value with the
        full path indicating the file to write log messages into.  The 'level'
        key should have a value set to an integer for the logging level to use.
        Valid logging levels are:
            0 : Low level errors only
            1 : Data for analytics
            2 : Informational mesages
            3 : Debugging information
            4 : All messages

        If one of the keys is not included, the current setting for
        that item will not be modified.

        For example:
        {"file": "C:\\ProgramData\\HP\\Sprout\\SoHal\\sohal.log", "level": 1}

        Args:
            log: A dictionary indicating the location and level for SoHal's
                 log. If this parameter is not included (or is set to None),
                 this acts as a get request and returns the current valeus.

        Returns:
            The current logging information, as a dictionary.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=log)

    def version(self):
        """
        Gets the SoHal version.

        Returns:
            A string containing the version of SoHal.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()
