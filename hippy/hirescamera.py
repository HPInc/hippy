
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the hirescamera device.
"""

import copy
import enum
import re
from hippy.hippycamera import HippyCamera


class HiResCamera(HippyCamera):
    """ The HiResCamera class allows the user to create a HiResCamera object
    which includes a method for each of the SoHal hirescamera commands. The
    user can call these methods to query and control the hirescamera hardware.
    """

    @enum.unique
    class Mode(enum.Enum):
        """ The Mode class enumerates the possible modes of the camera.
        """
        full_res = '4416x3312'
        video = '2208x1656'
        high_fps = '1104x828'

    @enum.unique
    class LEDState(enum.Enum):
        """ The LEDState class enumerates the different states the
        HiResCamera LEDs support.
        """
        off = 'off'
        low = 'low'
        high = 'high'
        auto = 'auto'


    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    # Override the HippyObject method to convert the parameters
    # in the led_state notifications to the enum values
    @classmethod
    def _convert_params(cls, method, params):
        method = re.sub(r"@\d+", "", method)
        if method == 'hirescamera.on_led_state':
            params[0]['capture'] = HiResCamera.LEDState(params[0]['capture'])
            params[0]['streaming'] = HiResCamera.LEDState(
                params[0]['streaming'])

        return super(HiResCamera, cls)._convert_params(method, params)


    ####################################################################
    ###                    HIRESCAMERA PUBLIC API                    ###
    ####################################################################

    def auto_exposure(self, auto=None):
        """
        Gets or sets the camera's automatic exposure control mode.

        Args:
            auto: A boolean indicating if automatic exposure control
                mode should be enabled (True) or disabled (False).  If this
                parameter is not included (or is set to None), this acts as a
                get request and returns the current value. (default None)

        Returns:
            A bool indicating if the auto_exposure control mode is active.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=auto)

    def auto_gain(self, auto=None):
        """
        Gets or sets the camera's automatic gain control mode.

        Args:
            auto: A boolean indicating if automatic gain control mode should
                be enabled (True) or disabled (False). If this parameter
                is not included (or is set to None), this acts as a get
                request and returns the current value. (default None)

        Returns:
            A bool indicating if the auto_gain control mode is active.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=auto)

    def auto_white_balance(self, auto=None):
        """
        Gets or sets the camera's automatic white balance control mode.

        Args:
            auto: A boolean indicating if automatic white balance control
                mode should be enabled (True) or disabled (False).  If this
                parameter is not included (or is set to None), this acts as a
                get request and returns the current value. (default None)

        Returns:
            A bool indicating if the auto_gain control mode is active.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=auto)

    def brightness(self, brightness=None):
        """
        Gets or sets the camera's brightness setting.

        Args:
            brightness: An unsigned integer with the desired brightness value.
                If this parameter is not included (or is set to None), this
                acts as a get request and returns the current value.
                (default None)

        Returns:
            The current brightness value of the camera.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=brightness)

    def contrast(self, contrast=None):
        """
        Gets or sets the camera's contrast setting.

        Args:
            contrast: An unsigned integer with the desired contrast value.
                If this parameter is not included (or is set to None), this
                acts as a get request and returns the current value.
                (default None)

        Returns:
            The current contrast value of the camera.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=contrast)

    def camera_index(self):
        """
        Gets the camera's device index

        Returns:
            The device index for this camera

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def camera_settings(self, settings=None):
        """
        Sets all the camera settings in a single API call

        Args:
            settings: A dictionary containing the camera settings to change

        Returns:
            A dictionary containing all the camera settings

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=settings)

    def default_config(self, mode):
        """
        Returns the default camera configuration for the given mode.

        Args:
            mode: The camera mode to return the default values for

        Returns:
            A dictionary with the values set at the factory for exposure, gain,
            and white balance.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        config = self._send_msg(params=HiResCamera.Mode(mode).value)
        config['mode'] = HiResCamera.Mode(config['mode'])
        return config

    def device_status(self):
        """
        Returns the status of various aspects of the camera's hardware and
        firmware functionality. This method can be used to determine if the
        camera is in a thermal shutdown state. If so, the device needs to be
        disconnected and allowed to cool down in order to restore functionality.

        Returns:
            A dictionary with the that status for various items. For each one,
            the status can either be 'ok', 'busy', or 'error'.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def exposure(self, exposure=None):
        """
        Gets or sets the camera's exposure.

        Note that the camera will only retrieve the exposure setting
        if it is currently streaming.  If it is not streaming, the new
        exposure will not be applied, and a get command will return a
        default value.

        Args:
            exposure: An int to set the exposure to. If this parameter
                is not included (or is set to None), this acts as a get
                request and returns the current value. (default None)

        Returns:
            The current exposure value of the camera.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=exposure)

    def flip_frame(self, flip_frame=None):
        """
        Gets or sets the camera's flip frame value.

        The flip frame value controls if the image is flipped vertically
        (about the x axis).

        Args:
            flip_frame: A boolean indicating if the images should be flipped
                or not. If this parameter is not included (or is set to None),
                this acts as a get request and returns the current
                value. (default None)

        Returns:
            The camera's current flip frame value.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=flip_frame)

    def gain(self, gain=None):
        """
        Gets or sets the camera's gain.

        Note that the camera will only retrieve the gain setting
        if it is currently streaming.  If it is not streaming, the new
        gain will not be applied, and a get command will return a
        default value.

        Args:
            gain: An int to set the gain to. If this parameter
                is not included (or is set to None), this acts as a get
                request and returns the current value. (default None)

        Returns:
            The current gain value of the camera.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=gain)

    def gamma_correction(self, gamma_correction=None):
        """
        Gets or sets a value indicating if the the camera's gamma correction
        mode is on or off.

        Args:
            gamma_correction: A boolean indicating if the gamma correction mode
                should be on. If this parameter is not included (or is set to
                None), this acts as a get request and returns the current
                value. (default None)

        Returns:
            A boolean indicating if the gamma correction mode is currently on.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=gamma_correction)

    def keystone(self, keystone=None):
        """
        Gets or sets the hirescamera's keystone. This method should only be
        used while the camera is streaming frames. Values set using this method
        are not persistent: they will be overwritten the next time the camera
        starts streaming frames.

        Args:
            keystone: A dictionary containing the keystone values to set. If
                this parameter is not included (or is set to None), this
                acts as a get request and returns the current
                values. (default None)

        Returns:
            A dictionary with the hirescamera's current keystone values.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=keystone)

    def keystone_table(self, table=None):
        """
        Re-initializes the entire RAM keystone table with values from one of
        three tables: the `flash_max_fov` or `flash_fit_to_mat` tables which
        are stored in flash memory (and may be updated by clients using the
        `keystone_flash_table_entry` method), or the `default` table from the
        camera firmware.

        Args:
            table: Should be set to `flash_max_fov` or `flash_fit_to_mat` to
                use the values from one of those two user-defined keystone
                tables, or `default` to use the values from the default
                keystone table. If this parameter is set to 'ram' the method
                will succeed, but the RAM keystone table will not be updated.
                If this parameter is not included (or is set to None), this
                acts as a get request and returns a string indicating the
                current table. (default None)

        Returns:
            A string indicating what data is currently in the RAM keystone
            table. If the data in the RAM table matches one of the other
            keystone tables, the name of that table will be returned (i.e.
            'default', 'flash_max_fov', or 'flash_fit_to_mat'). If the
            data does not match any of the keystone tables, this method will
            return 'ram'.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=table)

    def keystone_table_entries(self, type, entries=None):
        """
        Gets or sets keystone values in the specified keystone table.
        This method can be used to get the keystone values for all resolutions,
        get the keystone values for only specified resolutions, or to set
        keystone values for one or more resolutions.  The value provided to
        the 'entries' argument determines which action SoHal will perform.

        Args:
            type: A string indicating which table SoHal should read the
                keystone entries from or write the keystone entries to.
            entries: This parameter should be set to either a list of values
                or None.
                If each item on the list is a dictionary indicating a new
                keystone setting (i.e. includes 'resolution', 'values', and
                'enabled' keys), this acts as a `Set` request and SoHal will
                update the keystone values for that resolution.
                If each item on the list is a resolution dictionary
                (i.e. includes 'fps', 'width', and 'height' keys), this acts
                as a `Get` request, and SoHal will return the keystone
                values for the specified resolutions.
                If this parameter is not included (or is set to None), this
                acts as a `Get` request and SoHal will return the current
                keystone values for all resolutions.

        Returns:
            A dictionary with the current values stored in memory for the
            specified table and resolutions.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=[type, entries])

    def led_state(self, led_state=None):
        """
        Gets or sets a dictionary indicating the desired state of the leds
        when the camera is streaming and when capturing a still image.
        The dictionary should have 'streaming' and 'capture' keys, and the
        values should be HiResCamera.LEDState objects (or the corresponding
        string values).  Note that the 'streaming' state can only be set
        to 'off' or 'low'.  SoHal will return an invalid parameter error if
        the 'streaming' LED state is set to 'high' or 'auto'.

        Args:
            led_state: A dictionary indicating the desired state for the leds.
                If this parameter is not included (or is set to
                None), this acts as a get request and returns the current
                value. (default None)

        Returns:
            A dictionary indicating the current LED state settings.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        state = copy.deepcopy(led_state)
        if state is not None:
            if 'streaming' in state:
                state['streaming'] = HiResCamera.LEDState(
                    state['streaming']).value
            if 'capture' in state:
                state['capture'] = HiResCamera.LEDState(state['capture']).value

        cur_state = self._send_msg(params=state)
        cur_state['streaming'] = HiResCamera.LEDState(cur_state['streaming'])
        cur_state['capture'] = HiResCamera.LEDState(cur_state['capture'])
        return cur_state


    def lens_color_shading(self, lens_color_shading=None):
        """
        Gets or sets a value indicating if the the camera's lens color shading
        mode is on or off.

        Args:
            lens_color_shading: A boolean indicating if the lens color shading
                mode should be on. If this parameter is not included (or is set
                to None), this acts as a get request and returns the current
                value. (default None)

        Returns:
            A bool indicating if the lens color shading mode is currently on.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=lens_color_shading)

    def lens_shading(self, lens_shading=None):
        """
        Gets or sets a value indicating if the the camera's lens shading
        mode is on or off.

        Args:
            lens_shading: A boolean indicating if the lens shading mode should
                be on. If this parameter is not included (or is set to
                None), this acts as a get request and returns the current
                value. (default None)

        Returns:
            A boolean indicating if the lens shading mode is currently on.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=lens_shading)

    def mirror_frame(self, mirror_frame=None):
        """
        Gets or sets the camera's mirror frame value.

        The mirror frame value controls if the image is flipped horizontally
        (about the y axis).

        Args:
            mirror_frame: A boolean indicating if the images should be mirrored
                or not. If this parameter is not included (or is set to None),
                this acts as a get request and returns the current
                value. (default None)

        Returns:
            The camera's current mirror frame value.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=mirror_frame)

    def parent_resolution(self, resolution=None):
        """
        For the HP Z 3D Camera high resolution camera, this method will return
        the parent resolution of either the current streaming resolution or the
        specified resolution. If the camera is not currently streaming and the
        resolution is not included, this will raise an error.

        Note that this method is not currently supported for Sprout high
        resolution cameras. Sprout cameras will raise a 'Functionality not
        available' error.

        Args:
            resolution: A dictionary indicating one of the camera's supported
                resolutions. If this parameter is not included (or is set to
                None), this method will return the parent resolution of the
                camera's current streaming resolution. (default None)

        Returns:
            A dictionary containing the parent resolution values.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=resolution)

    def power_line_frequency(self, frequency=None):
        """
        Gets or sets the camera's power line frequency.

        Args:
            frequency: An unsigned integer with the desired power line
                frequency value in Hz. Note that the only supported values
                are 50 and 60.
                If this parameter is not included (or is
                set to None), this acts as a get request and returns the
                current value.
                (default None)

        Returns:
            The current power_line_frequency value of the camera in Hz.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=frequency)

    def reset(self):
        """
        Reboots the hirescamera. This is  equivalent to physically unplugging
        the usb cable and then plugging it back in.
        As such, resetting the camera will cause SoHal to send
        `hirescamera.on_device_disconnected`,
        `system.on_device_disconnected`, `hirescamera.on_device_connected`,
        and `system.on_device_connected` notifications.

        Additionally, the behavior should be identical to when the
        hirescamera's usb cable is physically disconnected and reconnected.
        The device will be closed when the the `on_device_disconnected`
        notifications are sent.  By the time the `on_device_connected`
        notifications are sent, all settings will be restored to the
        hardware's startup values.  After the connected notifications, the
        touchmat will need to be opened and any desired settings will need to
        be set.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg()

    def saturation(self, saturation=None):
        """
        Gets or sets the camera's saturation.

        Args:
            saturation: An unsigned integer with the desired saturation value.
                If this parameter is not included (or is set to None), this
                acts as a get request and returns the current value.
                (default None)

        Returns:
            The current saturation value of the camera.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=saturation)

    def sharpness(self, sharpness=None):
        """
        Gets or sets the camera's sharpness.

        Args:
            sharpness: An unsigned integer with the desired sharpness value.
                If this parameter is not included (or is set to None), this
                acts as a get request and returns the current value.
                (default None)

        Returns:
            The current sharpness value of the camera.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=sharpness)

    def strobe(self, frames, gain, exposure):
        """
        This method sets a gpio from the hirescamera into the projector
        that triggers a high intensity flash for the given number of frames.
        It also temporarily changes the gain and exposure to the
        provided values.

        Args:
            frames: The number of camera frames to turn the flash on for.
            gain: A temporary gain value to use while flashing.
            exposure: A temporary exposure value to use while flashing.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        self._send_msg(params={'frames' : frames,
                               'gain' : gain,
                               'exposure' : exposure})

    def white_balance(self, rgb=None):
        """
        Gets or sets the camera's red, green, and blue white balance values.

        Note that if the camera is not streaming, the new white balance
        values will not be applied.

        Args:
            rgb: A dictionary containing the white balance values to set. If
                this parameter is not included (or is set to None), this
                acts as a get request and returns the current
                values. (default None)

        Returns:
            A dictionary with the camera's current white balance values.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=rgb)

    def white_balance_temperature(self, temperature=None):
        """
        Gets or sets the camera's white balance as a color temperature value
        in 100's of degrees Kelvin. For example, a return value of
        40 represents 4000 K.

        Note that this method is currently only supported for the HP Z 3D
        Camera high resolution camera.

        Args:
            temperature: An integer indicating the white balance temperature
                to set. If this parameter is not included (or is set to None),
                this acts as a get request and returns the current
                value. (default None)

        Returns:
            The camera's current white balance value in 100's of degrees
            Kelvin.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        return self._send_msg(params=temperature)
