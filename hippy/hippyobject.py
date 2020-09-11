
# Copyright 2016-2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" A module to handle the base hippy object.
"""

import json
import enum
import inspect
import asyncio
#import socket
import time
import uuid
import threading
import concurrent
import weakref
import queue
import websockets

from hippy import PySproutError

msg_queue_interval = 0.5
default_host = 'localhost'
default_port = 20641
port_range = 10


def _comm_thread(hippyobj, host, port):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    with hippyobj._task_lock:
        hippyobj._thread_loop = loop

    loop.run_until_complete(_comm_loop(hippyobj, host, port))

async def _comm_loop(hippyobj, host, port):
    tasks = []
    error = None

    read_task = None
    send_task = None

    try:
        validation_key = str(uuid.uuid4())
        validation_cmd = {'id': 0, 'jsonrpc': '2.0',
                          'method': 'system.echo',
                          'params' : [validation_key]}
        all_ports = list(range(port, port+port_range))
        # we put it just after the default one for performance reasons
        all_ports.insert(1, 8765)
        for cur_port in all_ports:
            try:
                address = 'ws://' + host + ':' + str(cur_port)
                b64_factor = 1.34    # base64 data expansion ratio
                async with websockets.connect(
                        address, max_size=500*1024*1024*b64_factor,
                        read_limit=500*1024*1024*b64_factor) as websocket:

                    # Make sure it's actually sohal on this port
                    await websocket.send(json.dumps(validation_cmd))
                    try:
                        msg = json.loads(await websocket.recv())
                    except Exception:
                        msg = {}
                    # we may need to improve this one day
                    if 'result' not in msg or msg['result'] != validation_key:
                        # continue to the next port in the range
                        continue

                    hippyobj._port = cur_port

                    # Notify the main thread that we've connected
                    hippyobj._connected = True
                    hippyobj._local_address = websocket.local_address
                    hippyobj._connected_event.set()

                    # Use one websockets connection to read and write messages
                    # This is based on the example at
                    # https://websockets.readthedocs.io/en/stable/intro.html#both
                    # Note that while the example cancels the pending tasks
                    # after the wait, here that was causing messages to be lost
                    # under certain conditions (if a new message was received
                    # while handling the prior response)
                    while hippyobj._running:
                        if send_task is None:
                            send_task = asyncio.ensure_future(
                                _get_msg_to_send(hippyobj))
                        if read_task is None:
                            read_task = asyncio.ensure_future(websocket.recv())

                        tasks = [send_task, read_task]
                        with hippyobj._task_lock:
                            hippyobj._tasks = tasks

                        await asyncio.wait(tasks,
                                           return_when=asyncio.FIRST_COMPLETED)

                        if read_task.done():
                            message = json.loads(read_task.result())
                            await _handle_msg_received(hippyobj, message)
                            read_task = None

                        if send_task.done():
                            message = send_task.result()
                            await websocket.send(message)
                            send_task = None
            except OSError:
                # If we couldn't connect to SoHal on this port, try the next one
                continue

        # Couldn't connect to SoHal on any of the ports in the range...
        error = PySproutError(0x200, '200', 'Unable to connect to SoHal')

    except websockets.ConnectionClosed as err:
        #print('<<< Connection closed')
        error = err
    except concurrent.futures.CancelledError as err:
        error = err
        #print("Caught cancelled error in _comm_loop {}".format(err))
    except ReferenceError as err:
        #print("Caught reference error in _comm_loop {}".format(err))
        error = err
    except Exception as err:
        #print("Caught exception in comm loop {}".format(err))
        error = err
    finally:
        try:
            hippyobj._connected = False
            hippyobj._local_address = None
            hippyobj._comm_error = error
            hippyobj._connected_event.set()

            # Send a dummy item over the response queue so we don't get
            # stuck in _send_msg_async
            hippyobj._response_queue.put(None)
        except ReferenceError:
            pass

        for task in tasks:
            cancelled = task.cancel()

            if not cancelled:
                # This should fix that annoying "Task exception was never
                # retrieved" error that would show up sometimes when running
                # the tests. Note that this may just be a workaround for
                # something that was a python issue in the first place. Not
                # sure if this is exactly the same:
                # https://bugs.python.org/issue30508
                try:
                    task.exception()
                # Do we need to catch other exceptions here?
                except concurrent.futures.CancelledError:
                    pass

async def _get_msg_to_send(hippyobj):
    loop = asyncio.get_event_loop()

    # Poll in a loop with a timeout so this doesn't block.
    msg = None
    while msg is None:
        try:
            msg = await loop.run_in_executor(None,
                                             hippyobj._msg_queue.get,
                                             True, msg_queue_interval)
            hippyobj._msg_queue.task_done()
        except queue.Empty:
            pass

    return msg

# auxiliary function to create asyncio's loop
def _send_notification(callback, method, params):
    asyncio.set_event_loop(asyncio.new_event_loop())
    callback(method, params)


async def _handle_msg_received(hippyobj, msg):

    if 'id' in msg:
        # This is a response to a message
        hippyobj._response_queue.put(msg)
    else:
        # This is a notification
        # If there is a callback method registered, call it on a
        # separate thread
        with hippyobj._callback_lock:
            callback = hippyobj._subscribe_callback
        if callback is not None:
            method = msg['method']
            params = None
            if 'params' in msg:
                params = hippyobj._convert_params(method,
                                                  msg['params'])
            thr = threading.Thread(target=_send_notification,
                                   args=(callback, method, params),
                                   daemon=True)
            thr.start()


#
#
class StatusJsonEncoder(json.JSONEncoder):
    """ Extend the basic JSONEncoder class to handle enums and bytearrays
    """
    def default(self, obj):
        if isinstance(obj, enum.IntEnum):
            return obj.value
        if isinstance(obj, enum.Enum):
            return obj.name
        if isinstance(obj, (bytearray, bytes)):
            # this will need to be converted back to bytearray with
            # something like: bytearray(input_.encode('latin-1'))
            return obj.decode('latin-1')
        return json.JSONEncoder.default(self, obj)


#
#
class HippyObject:
    """ The HippyObject class is the base object which contains the
    functionality that is available for all objects within hippy. This
    includes the ability to open a connection and communicate with SoHal
    through JSONRPC messages.
    """
    def __init__(self, host=None, port=None):
        """Creates a base class hippy object.

        Args:
            host: A string indicating the ip address of the SoHal server. If
                this parameter is not included (or is set to None), the default
                address will be used. (default None)

            port: The port of the SoHal server. If this parameter is not
                included (or is set to None), the default port will be used.
                (default None)
        """

        if host is None:
            host = default_host
        if port is None:
            port = default_port
        self._host = host
        self._port = port

        # Note: hippydevice child classes may update this _object_name to
        # include @index at the end (e.g. 'projector@0' instead of 'projector')
        self._object_name = self.__class__.__name__.lower()
        self._connected = False
        self._local_address = None
        self._connected_event = threading.Event()
        self._running = True
        self._task_lock = threading.Lock()
        self._tasks = []
        self._callback_lock = threading.Lock()
        self._subscribe_callback = None
        self._comm_error = None
        self._thread_loop = None

        self._msg_queue = queue.Queue()
        self._response_queue = queue.Queue()

        self._rpc_id = {'current_id' : 0}
        self._open_connection(self._host, self._port)

    def __del__(self):
        try:
            self._close_connection()
        except AttributeError:
            pass
        except TypeError:
            pass


    ####################################################################
    ###                       PRIVATE METHODS                        ###
    ####################################################################

    def _close_connection(self):
        self._running = False

        with self._task_lock:
            for task in self._tasks:
                self._thread_loop.call_soon_threadsafe(task.cancel)

        #if self._comm_th.isAlive():
            #self._comm_th.join(1.)

    # derived classes can override this to implement some
    # custom behavior (such as converting a value in a particular
    # notification to an enum)
    @classmethod
    def _convert_params(cls, method, params):
        return params[0]

    def _get_jsonrpc(self, method, params=None):
        msg = {'jsonrpc' : '2.0',
               'id' : self._get_msg_id(),
               'method' : method, }
        if params is not None:
            if isinstance(params, list):
                msg['params'] = params
            else:
                # jsonrpc spec forces us to send params inside a 1-element list
                msg['params'] = [params]
        return msg

    def _get_msg_id(self):
        msg_id = self._rpc_id['current_id']
        self._rpc_id['current_id'] = msg_id + 1
        try:
            new_id = "{}:{}".format(self._local_address[1],
                                    self._rpc_id['current_id'])
        except TypeError:
            # _local_address is None (if we aren't connected)
            new_id = "None:{}".format(self._rpc_id['current_id'])
        return new_id

    # This should only be called if the connection isn't already open. If
    # it is, use reconnect() or call _close_connection first
    def _open_connection(self, host, port):
        self._connected_event.clear()
        self._running = True

        # Start a separate read thread to handle the websocket communication
        self._comm_th = threading.Thread(target=_comm_thread,
                                         args=(weakref.proxy(self), host, port),
                                         daemon=True)
        self._comm_th.start()

        # Wait for indication that the connection with SoHal is open
        # Do this with a timeout so we can still catch control-c interrupts
        while not self._connected_event.wait(0.5):
            pass

        if not self._connected:
            raise self._comm_error

    def _send_msg(self, function_name=None, params=None):
        if function_name is None:
            function_name = inspect.getouterframes(
                inspect.currentframe(), 2)[1][3]
        method = self._object_name + '.' + function_name
        ret = self._send_msg_async(method, params)
        return ret

    def _send_msg_async(self, method, params=None):
        msg = self._get_jsonrpc(method, params)
        #print("> {}".format(msg))

        # Clear out any old data on the response queue
        while not self._response_queue.empty():
            resp = self._response_queue.get()
            #print("Clearing data off of the response queue: {}".format(resp))
            self._response_queue.task_done()

        if not self._connected:
            raise self._comm_error

        self._msg_queue.put(json.dumps(msg, cls=StatusJsonEncoder,
                                       sort_keys=True))

        resp = self._response_queue.get()
        self._response_queue.task_done()

        # If the connection with SoHal was lost, the response could be None
        if resp is None:
            raise self._comm_error

        #print("< {}".format(resp))
        if 'error' in resp:
            raise PySproutError(**resp['error'])

        if 'id' not in resp or resp['id'] != msg['id']:
            raise PySproutError(0x204, '204',
                                'Response message id did not match command id')
        return resp['result']


    ####################################################################
    ###                    HIPPY OBJECT METHODS                      ###
    ####################################################################

    @staticmethod
    def default_callback(method, params):
        """
        This is a static function which prints the passed in method and
        params. It can be used as a parameter for the 'subscribe' method,
        to provide an easy way to print all notifications received. To
        enable this, call:
            deviceName.subscribe(deviceClass.default_callback)
        For example:
            proj = Projector()
            proj.subscribe(Projector.default_callback)
        """
        print("Received {} params: {} ".format(method, params), flush=True)

    def reconnect(self):
        """
        Opens the connection with SoHal. This should only be called if the
        initial connection is lost and a new connection needs to be established
        (for example, if SoHal is restarted).
        Note that the device will need to be opened again after calling
        this method. If you were previously subscribed, you'll need to
        subscribe again after reconnecting.

        Raises:
            PySproutError: If SoHal responded to the request with an error
                message.

        """
        self._close_connection()
        time.sleep(0.1)
        self._open_connection(self._host, self._port)

    def subscribe(self, callback):
        """
        Registers a callback function to receive SoHal notifications.

        The parameter passed in as 'callback' should be a function that
        takes in two parameters.
        For example:
            def my_callback(method, params):
                # do something here

            deviceName.subscribe(my_callback)

        When a notification is received, the provided callback method will be
        called, with the first parameter set to the 'method' field from the
        notification and the second parameter set to the 'params' (or
        None if the notification did not contain a 'params' field).
        For example:
            {"jsonrpc": "2.0", "method": "projector.on_state",
             "params": ["off"]}
        will call
            my_callback("projector.on_state", Projector.State.off)

        The default_callback method, which prints received notifications, may be
        used as a parameter to this method:
            deviceName.subscribe(deviceClass.default_callback)

        Args:
            callback: The method to call when a notification is received.

        Raises:
            PySproutError: If the parameter passed in is not callable.
        """
        if not callable(callback):
            raise PySproutError(0x204, '204', 'Invalid parameter')
        with self._callback_lock:
            self._subscribe_callback = callback
        return self._send_msg()

    def unsubscribe(self):
        """
        Deregisters the currently registered callback function so it stops
        receiving SoHal notifications.
        """
        ret = self._send_msg()
        with self._callback_lock:
            self._subscribe_callback = None
        return ret
