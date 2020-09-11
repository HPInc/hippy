
# Copyright 2017 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

import check_device_types


def pytest_addoption(parser):
    parser.addoption("--index", action="append", default=None,
        help="list of indexes to pass to test functions")


def pytest_generate_tests(metafunc):
    if 'index' in metafunc.fixturenames:
        cmd_line_indexes = metafunc.config.getoption('index')
        if cmd_line_indexes is not None:
            # If the user passed in one or more --index command line arguments,
            # use those values for the device index to test
            indexes = []
            # Convert the string command line params to either None or an int
            for item in cmd_line_indexes:
                if item != 'None':
                    indexes.append(int(item))
                else:
                    indexes.append(None)
            metafunc.parametrize("index", indexes)
        else:
            # If there were no --index command line arguments, determine all
            # connected indexes for each device and generate a test for each
            # one. Note that this requires each test file to have a
            # 'device_name' variable defined that we read here.
            dev_name = metafunc.module.device_name
            indexes = check_device_types.find_device_indexes(dev_name)
            metafunc.parametrize("index", indexes)
