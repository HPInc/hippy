#!/usr/bin/env python

#
# Copyright 2019 HP Development Company, L.P.
#    HP Confidential
#

""" A module to handle the base hippy camera.
"""

import asyncio
import copy
import enum
import struct
import re
from collections import namedtuple
import websockets
import hippy.hippyobject
from hippy.hippydevice import HippyDevice
from hippy import PySproutError


header_sohal = b'\x50\xa1'
# TODO EB we're going to need to change this part if we change it in SoHal
header_device = b'\xde\xca'
header_version = 1
frame_sync, frame_async = (0, 1)

MainHeader = namedtuple('Header',
                        ['magic', 'device', 'version', 'streams', 'error'])
FrameHeader = namedtuple('Frame',
                         ['width', 'height', 'index', 'stream', 'format',
                          'timestamp'])
Error = namedtuple('Error', ['code', 'file_id', 'git_id'])


class ImageClientProtocol(websockets.WebSocketClientProtocol):
    """
    WebSocket client protocol for large images
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_size'] = 2 ** 26
        super().__init__(*args, **kwargs)

class HippyCamera(HippyDevice):
    """ The HippyCamera class is the base object which contains the
    functionality that is available for all SoHal cameras (depthcamera,
    hirescamera, and uvccamera).
    """
    @enum.unique
    class ImageStream(enum.IntEnum):
        """
        The ImageStream class enumerates the different streams SoHal
        supports.
        """
        color = 0x1
        depth = 0x2
        ir = 0x4
        points = 0x8

    # Note: once we remove the points_mm field, set this enum as unique again
    #@enum.unique
    class ImageFormat(enum.IntEnum):
        """
        The ImageFormat class enumerates the different formats for the
        image frames. Each frame header will contain one byte indicating the
        format of that frame.

        Note: The points_mm field has been deprecated and is being replaced
        with the equivalent points_mm32f. Please update your software, as
        points_mm will be removed in a future release.
        """
        unknown = 0x0
        gray_16 = 0x1
        rgb_888 = 0x2
        yuv_422 = 0x3
        yuyv = 0x04     # it's a 4:2:2 format @ 16 bpp
        gray_8 = 0x5
        depth_mm = 0x6
        bgra_8888 = 0x7
        points_mm32f = 0x8
        # Note: as of 1/15/2019 this points_mm format is deprecated. Please use
        # the new points_mm32f instead.
        points_mm = 0x8 # deprecated
        yuy2 = 0x9,     # it's a 4:2:2 format @ 16 bpp
        uyvy = 0xa,     # it's a 4:2:2 format @ 16 bpp
        nv12 = 0xb,     # it's a 4:0:0 format @ 12 bpp


    def __init__(self, index=None, host=None, port=None):
        """Creates a HippyCamera object.

        Args:
            index: An integer indicating the device index to use when sending
                messages to SoHal. This index is used to specify which device
                when SoHal is controlling multiple devices of the same class.
                For example, if the camera is a depth camera and the
                index is set to 1, an 'open' command would be sent as
                'depthcamera@1.open' which would tell SoHal to open the depth
                camera with index=1. If SoHal does not have a depthcamera
                with an index of 1 when open is called, SoHal will return
                a 'Device Not Found' error. Note that a list of all connected
                devices and their indexes can be queried using the
                devices() method in the System class.

                If this parameter is not included (or is set to None), the
                index will not be included in the message sent to SoHal (e.g.
                'depthcamera.open', which is an alias for 'depthcamera@0.open').
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
        super(HippyCamera, self).__init__(index, host, port)
        self._wsd = None

    def __del__(self):
        try:
            self._disconnect_from_image_server()
        except AttributeError:
            pass
        finally:
            super(HippyCamera, self).__del__()


    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    @classmethod
    def _bits_per_pixel(cls, img_format):
        if HippyCamera.ImageFormat.gray_16.value == img_format:
            return 16
        elif HippyCamera.ImageFormat.rgb_888.value == img_format:
            return 24
        elif HippyCamera.ImageFormat.yuv_422.value == img_format:
            return 16
        elif HippyCamera.ImageFormat.yuyv.value == img_format:
            return 16
        elif HippyCamera.ImageFormat.gray_8.value == img_format:
            return 8
        elif HippyCamera.ImageFormat.depth_mm.value == img_format:
            return 16
        elif HippyCamera.ImageFormat.bgra_8888.value == img_format:
            return 32
        elif HippyCamera.ImageFormat.points_mm.value == img_format:
            return 12*8
        elif HippyCamera.ImageFormat.yuy2.value == img_format:
            return 16
        elif HippyCamera.ImageFormat.uyvy.value == img_format:
            return 16
        elif HippyCamera.ImageFormat.nv12.value == img_format:
            return 12
        raise PySproutError(0, '0',
                            'Unknown image format: {}'.format(img_format))

    def _connect_to_image_server(self, image_port):
        if image_port <= 0:
            return
        # Currently everything uses the same port number, so if we've already
        # opened the image websocket connection, we don't need to open again...
        if self._wsd is None or not self._wsd.open:
            address = 'ws://{}:{}'.format(self._host, image_port)
            # print('Connecting to image server on {}'.format(address))
            loop = asyncio.get_event_loop()
            try:
                self._wsd = loop.run_until_complete(
                    websockets.connect(address, klass=ImageClientProtocol))
                # print("Successfully connected to Image server")
            except Exception as e:
                # print("Error connecting to image server {}".format(e))
                pass

    # Override the HippyDevice method to convert the parameters
    # in some of the notifications to ImageStream objects
    @classmethod
    def _convert_params(cls, method, params):
        method = re.sub("@\d+", "", method)
        camera_name = cls.__name__.lower()
        if method in ('{}.on_enable_streams'.format(camera_name),
                      '{}.on_disable_streams'.format(camera_name)):
            # Versions of SoHal prior to 2.017.08.24 had a bug where the
            # parameter was just a list of strings, instead of a list inside
            # of a list... ie params=['color'] instead of params=[['color']]
            # so check if this is a list of lists...
            if len(params) > 0 and isinstance(params[0], list):
                params = params[0]
            streams = []
            for stream in params:
                streams.append(HippyCamera.ImageStream[stream])
            params = streams
        else:
            params = params[0]
        return params

    def _disconnect_from_image_server(self):
        if self._wsd is not None:
            # print('Closing connection with image server')
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(self._wsd.close())
            except ConnectionAbortedError as e:
                pass
            except Exception as e:
                # print("Error connecting to image server {}".format(e))
                pass
            self._wsd = None

    @classmethod
    def _frame_len_in_bytes(cls, frame_h):
        BITS_PER_BYTE = 8;
        return int(frame_h.height * frame_h.width *
                   HippyCamera._bits_per_pixel(frame_h.format) / BITS_PER_BYTE)

    async def _get_frame(self, cmd):
        if self._wsd is None:
            err = 'Error connecting to SoHal frame streaming server'
            raise PySproutError(0, '0', err)
        #t1 = time.clock()
        await self._wsd.send(cmd)
        frame = await self._wsd.recv()
        #t2 = time.clock()
        #print("  \\-> time: {:.6f}  fps: {:.3f}".format(t2-t1, (1/(t2-t1))))
        return frame

    def _grab_frame(self, streams, sync, filter_descriptor):
        """
        Gets an IR, depth, or color frame from the camera. Which frame it
        returns depends on the stream parameter. The specified stream needs
        to be enabled before calling this method.
        """
        if self._wsd is None:
            # Use the enable_streams method to try to get the port and
            # connect to the streaming server.
            self.enable_streams()

        stream_mask = HippyCamera._list_to_streams(streams)

        frame_cmd = struct.pack('2s2sBBBB', header_sohal, header_device,
                                header_version, sync | filter_descriptor,
                                stream_mask, 0x00)

        try:
            frame = asyncio.get_event_loop().run_until_complete(
                self._get_frame(frame_cmd))
        except (websockets.exceptions.ConnectionClosed,
                ConnectionAbortedError):
            # SoHal must have closed the connection... It could have closed
            # and reopened so we might just need to disconnect/reconnect
            try:
                self._disconnect_from_image_server()
                # Use the enable_streams method to try to get the port and
                # connect to the streaming server.
                self.enable_streams()
                frame = asyncio.get_event_loop().run_until_complete(
                    self._get_frame(frame_cmd))
            except (websockets.exceptions.ConnectionClosed,
                    ConnectionAbortedError):
                err = 'Unable to connect to SoHal frame streaming server'
                raise PySproutError(0, '0', err)

        #with open('C:\\depthCamFrame.raw', 'wb') as fp:
        #    fp.write(frame)

        # First 8 bytes are the header for the overall frame (set of streams):
        main_h = MainHeader(*struct.unpack('2s2sBBBx', frame[:8]))
        offset = 8

        if main_h.magic != header_sohal:
            raise PySproutError(0, '0', 'Invalid frame header received')
        if main_h.device != header_device:
            raise PySproutError(0, '0', 'Invalid frame header received')
        if main_h.version != header_version:
            raise PySproutError(0, '0', 'Invalid frame header received')
        if main_h.error:
            error = Error(*struct.unpack('II7s', frame[8:23]))
            raise PySproutError(0, '0',
                                'Frame header contained error code: '
                                '{}:{:08x}:{:08x}'.format(
                                    error.git_id.decode('ascii'),
                                    error.file_id,
                                    error.code))

        # multiple streams may be in this frame, so we need to split them
        f_streams = HippyCamera._streams_to_list(main_h.streams)
        img = []
        for _ in f_streams:
            frame_h = FrameHeader(*struct.unpack('HHHBBQ',
                                                 frame[offset:offset+16]))
            offset = offset + 16
            img_len = self._frame_len_in_bytes(frame_h)
            img.append(
                {'data' :  frame[offset : offset + img_len],
                 'header' : frame[:offset],
                 'format' : HippyCamera.ImageFormat(frame_h.format),
                 'height' : frame_h.height,
                 'index' : frame_h.index,
                 'stream' : HippyCamera.ImageStream(frame_h.stream),
                 'width' : frame_h.width,
                 'timestamp' : frame_h.timestamp})
            offset = offset + img_len
        #
        return img[0] if len(f_streams) == 1 else img

    # converts a list of HippyCamera.ImageStream objects (or strings) to a
    # stream bit mask
    @classmethod
    def _list_to_streams(cls, streams):
        if not isinstance(streams, list):
            streams = [streams]
        stream_mask = 0
        for stream in streams:
            try:
                stream_mask += HippyCamera.ImageStream[stream].value
            except KeyError:
                stream_mask += HippyCamera.ImageStream(stream).value
        return stream_mask

    # converts a stream bit mask to a list of HippyCamera.ImageStream objects
    @classmethod
    def _streams_to_list(cls, streams):
        stream_list = []
        i = 1
        while streams:
            if streams & i:
                stream_list.append(HippyCamera.ImageStream(i))
                streams = streams & (~i)
            i = i << 1
        return stream_list

    ####################################################################
    ###                       CAMERA PUBLIC API                      ###
    ####################################################################

    def available_resolutions(self):
        """
        Returns a list of all the resolutions this camera supports.

        Returns:
            A list detailing all of the resolutions the camera supports.
            Each item in the list is a dictionary with details on one
            supported resolution.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        resolutions = self._send_msg()
        for res in resolutions:
            res['stream'] = HippyCamera.ImageStream[res['stream']]
            res['format'] = HippyCamera.ImageFormat[res['format']]
        return resolutions


    def close(self):
        """
        Closes the connection to the device.
        If the streaming image websocket connection is open, this method will
        close it as well.

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
        self._disconnect_from_image_server()
        return self._send_msg()

    def disable_streams(self, streams=None):
        """
        Disables specified streams.

        Args:
            streams: A string, a HippyCamera.ImageStream object, or a list (of
                     strings or HippyCamera.ImageStream objects)
                     indicating which stream(s) should be disabled. For example,
                     to disable both the color and depth streams, call either:
                     disable_streams(['color', 'depth'])
                     or
                     disable_streams([HippyCamera.ImageStream.color,
                                      HippyCamera.ImageStream.depth])

                     If this parameter is not included (or is set to None),
                     this acts as a get request and returns a list with the
                     currently enabled streams. (default None)
        Returns:
            A list of currently enabled streams. Each item in the list is a
            HippyCamera.ImageStream object.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                           message.
        """
        streams_str = None
        if streams is not None:
            if not isinstance(streams, list):
                streams = [streams]
            streams_str = [[]]
            for stream in streams:
                try:
                    streams_str[0].append(HippyCamera.ImageStream[stream].name)
                except KeyError:
                    streams_str[0].append(HippyCamera.ImageStream(stream).name)

        result = self._send_msg(params=streams_str)
        # Versions of SoHal prior to 2.017.08.24 had a bug where
        # disable_streams was returning a dictionary instead of just the list
        if isinstance(result, dict):
            result = result['streams']
        image_streams = list(map(lambda x: getattr(HippyCamera.ImageStream, x),
                                 result))

        # If there aren't any streams enabled, we can close the websocket
        # connection to the streaming server
        if not image_streams and self._wsd is not None:
            self._disconnect_from_image_server()

        return image_streams

    def enable_streams(self, streams=None):
        """
        Enables the specified camera streams. A stream needs to be enabled
        before a frame from that stream can be returned (by the grab_frame
        method).
        Note: The the depth stream must be enabled in order to enable the
        points stream.
        Note: Because of hardware limitations on the Gen 1.6 depth camera, the
        color and IR streams can not be enabled at the same time. This is not
        an issue on Gen 1.0 and 1.55 depth cameras.

        Args:
            streams: A string, a HippyCamera.ImageStream object, or a list (of
                     strings or HippyCamera.ImageStream objects)
                     indicating which stream(s) should be enabled. For example,
                     to enable both the color and depth streams, call either:
                     enable_streams(['color', 'depth'])
                     or
                     enable_streams([HippyCamera.ImageStream.color,
                                     HippyCamera.ImageStream.depth])

                     If this parameter is not included (or is set to None),
                     this acts as a get request and returns a list with the
                     currently enabled streams. (default None)
        Returns:
            A list of currently enabled streams. Each item in the list is a
            HippyCamera.ImageStream object.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                           message.
        """
        streams_str = None
        if streams is not None:
            if not isinstance(streams, list):
                streams = [streams]
            streams_str = [[]]
            for stream in streams:
                try:
                    streams_str[0].append(HippyCamera.ImageStream[stream].name)
                except KeyError:
                    streams_str[0].append(HippyCamera.ImageStream(stream).name)
        result = self._send_msg(params=streams_str)
        image_port = int(result['port'])
        image_streams = list(map(lambda x: getattr(HippyCamera.ImageStream, x),
                                 result['streams']))
        self._connect_to_image_server(image_port)
        return image_streams

    def enable_filter(self, filter_name):
        """
        Enables the filter passed as parameter. This function returns an
        integer that should be used as filter descriptor. This descriptor
        has to be passed as parameter to the grab_frame or grab_frame_async
        functions in order to the filter to be applied for a given frame.

        Args:
            filter_name: A filter name describing the filter to enable.
                         Currently only 'ir_gamma' is supported

        Raises:
            PySproutError: If SoHal returned an invalid filter error.
        """
        return int(self._send_msg(params=filter_name))


    def grab_frame(self, streams, filter_descriptor=0):
        """
        Returns the latest frame available from the camera.  This will return
        an IR, depth, and/or color frame, depending on the stream parameter.
        The specified streams need to be enabled before calling this method.

        Args:
            stream: A string, a HippyCamera.ImageStream object, or a list (of
                    strings or HippyCamera.ImageStream objects)
                    indicating which image(s) to grab.
            filter_descriptor: The filter descriptor indicating the filter
                    to apply to the frame, or 0 if the frame should not be
                    filtered. (default 0)

        Raises:
            PySproutError: If SoHal returned a frame with an invalid header.
        """
        return self._grab_frame(streams, frame_sync, filter_descriptor)

    def grab_frame_async(self, streams, filter_descriptor=0):
        """
        Returns the latest frame received from the camera. Unlike grab_frame,
        this method does not wait for a new frame before returning.
        This will return an IR, depth, and/or color frame, depending
        on the stream parameter. The specified streams need to be enabled
        before calling this method.

        Args:
            stream: A string, a HippyCamera.ImageStream object, or a list (of
                    strings or HippyCamera.ImageStream objects)
                    indicating which image(s) to grab.
            filter_descriptor: The filter descriptor indicating the filter
                    to apply to the frame, or 0 if the frame should not be
                    filtered. (default 0)

        Raises:
            PySproutError: If SoHal returned a frame with an invalid header.
        """
        return self._grab_frame(streams, frame_async, filter_descriptor)

    def streaming_resolution(self, resolution=None):
        """
        Returns the current streaming resolution. If the camera is not
        currently streaming this will raise an error.

        Returns:
            A dictionary containing the resolution at which the camera is
            currently streaming.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.
        """
        # Make a copy so we don't modify the user's variable..
        res = copy.deepcopy(resolution)
        if resolution is not None:
            if 'stream' in res.keys():
                stream = res['stream']
                try:
                    res['stream'] = HippyCamera.ImageStream[stream].name
                except KeyError as e:
                    res['stream'] = HippyCamera.ImageStream(stream).name
            if 'format' in res.keys():
                format = res['format']
                try:
                    res['format'] = HippyCamera.ImageFormat[format].name
                except KeyError as e:
                    res['format'] = HippyCamera.ImageFormat(format).name
        result = self._send_msg(params=res)
        result['stream'] = HippyCamera.ImageStream[result['stream']]
        result['format'] = HippyCamera.ImageFormat[result['format']]
        return result
