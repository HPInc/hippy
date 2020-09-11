from setuptools import setup
import os, subprocess, datetime

gitIdCmd = 'git log -1 --format="%h"'

if __name__ == '__main__':

    gitId = subprocess.check_output(gitIdCmd).decode('utf-8').rstrip()
    print('gitId: ', gitId)

    today = datetime.date.today()
    # It would be nice to include the git id, but it causes
    # setuptools to print an 'invalid version' warning
    today_str = '{}.{:03d}.{:02d}.{:02d}'#.{}'
    today_str = today_str.format(today.year//1000,
                                 today.year%1000,
                                 today.month,
                                 today.day) #, gitId)

    setup(
        name='Hippy',
        version=today_str,
        description='HP Sprout Python Client',
        packages=['hippy'],
        install_requires=['websockets'],
        )
