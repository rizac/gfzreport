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


# def isstr(val):
#     """
#     Returns if val is a string. Python 2-3 compatible function
#     :return: True if val denotes a string (`basestring` in python < 3 and `str` otherwise)
#     """
#     if ispy2():
#         return isinstance(val, basestring)
#     else:
#         return isinstance(val, str)


# def _ensure(filepath, mode, mkdirs=False, errmsgfunc=None):
#     """checks for filepath according to mode, raises an OSError if check is false
#     :param mode: either 'd', 'dir', 'r', 'fr', 'w', 'fw' (case insensitive). Checks if file_name is,
#         respectively:
#             - 'd' or 'dir': an existing directory
#             - 'fr', 'r': file for reading (an existing file)
#             - 'fw', 'w': file for writing (a file whose dirname exists)
#     :param mkdirs: boolean indicating, when mode is 'file_w' or 'dir', whether to attempt to
#         create the necessary path. Ignored when mode is 'r'
#     :param errmsgfunc: None by default, it indicates a custom function which returns the string
#         error to be displayed in case of OSError's. Usually there's no need to implement a custom
#         one, but in case the function accepts two arguments, filepath and mode (the latter is
#         either 'r', 'w' or 'd') and returns the relative error message as string
#     :raises: SyntaxError if some argument is invalid, or OSError if filepath is not valid according
#         to mode and mkdirs
#     """
#     # to see OsError error numbers, see here
#     # https://docs.python.org/2/library/errno.html#module-errno
#     # Here we use two:
#     # errno.EINVAL ' invalid argument'
#     # errno.errno.ENOENT 'no such file or directory'
#     if not isstr(filepath) or not filepath:
#         raise SyntaxError("{0}: '{1}' ({2})".format(strerror(errno.EINVAL),
#                                                     str(filepath),
#                                                     str(type(filepath))
#                                                     )
#                           )
# 
#     keys = ('fw', 'w', 'fr', 'r', 'd', 'dir')
# 
#     # normalize the mode argument:
#     if mode.lower() in keys[2:4]:
#         mode = 'r'
#     elif mode.lower() in keys[:2]:
#         mode = 'w'
#     elif mode.lower() in keys[4:]:
#         mode = 'd'
#     else:
#         raise SyntaxError('mode argument must be in ' + str(keys))
# 
#     if errmsgfunc is None:  # build custom errormsgfunc if None
#         def errmsgfunc(filepath, mode):
#             if mode == 'w' or (mode == 'r' and not os.path.isdir(os.path.dirname(filepath))):
#                 return "{0}: '{1}' ({2}: '{3}')".format(strerror(errno.ENOENT),
#                                                         os.path.basename(filepath),
#                                                         strerror(errno.ENOTDIR),
#                                                         os.path.dirname(filepath)
#                                                         )
#             elif mode == 'd':
#                 return "{0}: '{1}'".format(strerror(errno.ENOTDIR), filepath)
#             elif mode == 'r':
#                 return "{0}: '{1}'".format(strerror(errno.ENOENT), filepath)
# 
#     if mode == 'w':
#         to_check = os.path.dirname(filepath)
#         func = os.path.isdir
#         mkdir_ = mkdirs
#     elif mode == 'd':
#         to_check = filepath
#         func = os.path.isdir
#         mkdir_ = mkdirs
#     else:  # mode == 'r':
#         to_check = filepath
#         func = os.path.isfile
#         mkdir_ = False
# 
#     exists_ = func(to_check)
#     if not func(to_check):
#         if mkdir_:
#             os.makedirs(to_check)
#             exists_ = func(to_check)
# 
#     if not exists_:
#         raise OSError(errmsgfunc(filepath, mode))


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


# def ensurefiler(filepath):
#     """Checks that filepath denotes a valid file, raises an OSError if not.
#     In many cases it's more convenient to simply call the equivalent
#         os.path.isfile(filepath)
#     except that this function raises a meaningful OSError in case of non-existing parent directory
#     (hopefully saving useless browsing time)
#     :param filepath: a file path
#     :type filepath: string
#     :return: nothing
#     :raises: OSError if filepath does not denote an existing file
#     """
#     _ensure(filepath, 'r', False)  # last arg ignored, set to False for safety
# 
# 
# def ensuredir(filepath, mkdirs=True):
#     """Checks that filepath denotes a valid existing directory. Raises an OSError if not.
#     In many cases it's more convenient to simply call the equivalent
#         os.path.isdir(filepath)
#     except that this function has the optional mkdirs argument which will try to build filepath if
#     not existing
#     :param filepath: a file path
#     :type filepath: string
#     :param mkdirs: True by default, if D does not exists will try to build it via mkdirs before
#         re-checking again its existence
#     :return: nothing
#     :raises: OSError if filepath directory does not denote an existing directory
#     """
#     _ensure(filepath, 'd', mkdirs)

