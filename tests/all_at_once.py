
# Copyright 2016-2017 HP Development Company, L.P.
# SPDX-License-Identifier: MIT
#

""" Runs the pytests for several of the hippy classes at once. Note that this
does not run the desklamp test.
"""

import os
import threading

# Note that this does not run the desklamp tests!
all_tests = [
    'test_capturestage.py',
    'test_depthcamera.py',
    'test_hirescamera.py',
    'test_sohal.py',
    'test_touchmat.py',
    'test_projector.py',
    'test_sbuttons.py',
    'test_system.py',
]


#
def run_pytest(test):
    cmd = 'python -m pytest -v --index=0 {}'.format(test)
    print(cmd)
    os.system(cmd)

#
if __name__ == '__main__':
    threads = []
    for tst in all_tests:
        thr = threading.Thread(target=run_pytest,
                               args=(tst,))
        thr.start()
        threads.append(thr)

    for thr in threads:
        thr.join()

    run_pytest('sohal_exit.py')
