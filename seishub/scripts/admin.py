# -*- coding: utf-8 -*-

import sys
import os
from seishub.daemon import createApplication
from seishub.env import Environment


def main():
    """
    SeisHub administration script.
    """
    args = sys.argv
    if len(args) == 3:
        if args[1] == 'initenv':
            print('Initializing new SeisHub environment')
            path = args[2]
            if os.path.isdir(path):
                print('Error: path %s already exists!' % path)
            else:
                createApplication(path, create=True)


