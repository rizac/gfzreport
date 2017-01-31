try:
    import numpy as np

    def isnumpy(val):
        """
        :return: True if val is a numpy object (regarldess of its shape and dimension)
        """
        return type(val).__module__ == np.__name__
except ImportError as ierr:
    def isnumpy(val):
        raise ierr

import shutil
import sys
import datetime as dt
import re
import errno
from os import strerror
import os
import time
import bisect

# Python 2 and 3: alternative 4
# see here:
# http://python-future.org/compatible_idioms.html
try:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError

if 2 <= sys.version_info[0] < 3:
    def ispy2():
        """:return: True if the current python version is 2"""
        return True

    def ispy3():
        """:return: True if the current python version is 3"""
        return False
elif 3 <= sys.version_info[0] < 4:
    def ispy2():
        """:return: True if the current python version is 2"""
        return False

    def ispy3():
        """:return: True if the current python version is 3"""
        return True
else:
    def ispy2():
        """:return: True if the current python version is 2"""
        return False

    def ispy3():
        """:return: True if the current python version is 3"""
        return False


def load_module(filepath, name=None):
    """
        Loads a python module indicated by filepath, returns an object where global variables
        and classes can be accessed as attributes
        See: http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
        :param filepath: the path of the module
        :param name: defaults to None (implying that the filepath basename, without extension, will
            be taken) and it's only used to set the .__name__ of the returned module. It doesn't
            affect loading
    """
    if name is None:
        name = os.path.splitext(os.path.basename(filepath))[0]
    # name only sets the .__name__ of the returned module. it doesn't effect loading

    if ispy2():  # python 2
        import imp
        return imp.load_source(name, filepath)
    elif ispy3() and sys.version_info[1] >= 5:  # Python 3.5+:
        import importlib.util  # @UnresolvedImport
        spec = importlib.util.spec_from_file_location(name, filepath)
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        return modul
    else:  # actually, for Python 3.3 and 3.4, but we assume is the case also for 3.2 3.1 etcetera
        from importlib.machinery import SourceFileLoader  # @UnresolvedImport
        return SourceFileLoader(name, filepath).load_module()
        # (Although this has been deprecated in Python 3.4.)

    # raise SystemError("unsupported python version: "+ str(sys.version_info))