
# Copyright 2016-2019 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Hippy is a python module designed to communicate with SoHal.  The
devices and methods in hippy mirror the SoHal spec, but hippy handles all
of the websocket communication for the user.
"""
from __future__ import division, absolute_import, print_function

from .pysprouterror import PySproutError
from .capturestage import CaptureStage
from .depthcamera import DepthCamera
from .desklamp import DeskLamp
from .hirescamera import HiResCamera
from .projector import Projector
from .sbuttons import SButtons
from .sohal import SoHal
from .system import System
from .touchmat import TouchMat
from .uvccamera import UVCCamera
