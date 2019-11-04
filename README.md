Hippy Python Module
==================

Hippy is a Python® module designed to communicate with SoHal.  The devices and
methods in hippy mirror the SoHal spec, but hippy handles all of the websocket
communication for the user.

Note that the objects in the hippy module are not thread safe.

Using hippy, the user can create simple Python scripts to communicate with
the devices.  For example, to turn on the projector:

```
from hippy import Projector

p = Projector()
p.open()
p.on()
p.close()
```

## Installation ##

### Python ###
To install hippy, you first need to install the 64 bit version of Python 3.7.1
from https://www.python.org/downloads/release/python-371/
> <B>Note</B>: When installing Python, it is helpful if you select the "Add
> Python to environment variables" option.


### Hippy ###
Next you need to install the hippy module using the provided
`Hippy-x.x.x.x-py3-none-any.whl` wheel package (where `x.x.x.x` represents the
current version number).

To install hippy, open a command prompt and run
> pip install Hippy-x.x.x.x-py3-none-any.whl

Note that hippy requires the websockets Python package. If this dependency is
not already installed, it will be installed automatically.

> <B>Note</B>: If you're using `pip` from a company network and you see an error
> such as `No matching distribution found`, you may need to provide the proxy
> using:
> <BR>  `pip install Hippy-x.x.x.x-py3-none-any.whl --proxy=your_proxy_here `


Once all three items are installed, you're ready to start using hippy.  First
launch the soHal.exe and then run your Python script or start sending
commands from a Python Prompt.

You can use Python's `dir` function to see a list of all methods a device
includes:
```
from hippy import Projector
dir(Projector)
```

and the `help` function to see information on a particular method:
```
from hippy import Projector
help(Projector.open)
```

## Notices ##

"Python" is a registered trademark of the Python Software Foundation.
