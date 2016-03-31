'''
ArgParse utilities. Currently implemented:
- utilities for checking if arguments are valid files, including:
    - files for reading (existing files, warning if the file dirname does not exists, helping
      possible typos to be retrieved immediately)
    - existing directories (with option to make the directory tree)
    - files for writing (with option to make the directory tree)
  Note that the argparse builti FileWriter returns a file object already opened, which is not what
  the user always want, these functions returns simply the absolute path of the argument value,
  if the relative check function is ok
Created on Mar 29, 2016

@author: riccardo
'''
import os
import argparse
from . import _ensure, ensurefiler


def _os(filepath, **args):
    """function calling _ensure defined in utils and raising the appropriate ArgParse error"""
    try:
        _ensure(filepath, **args)
        return os.path.abspath(filepath)
    except OSError as oerr:
        raise argparse.ArgumentTypeError(str(oerr))


def isdir(arg):
    """
        Utility function for `ArgumentParser's add_argument
        <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument>`_
        type keyword. Checks if the argument is an existing directory, returns the absolute path in
        case and raises the appropriate ArgumentParser error otherwise
        :Example:
            import utils.argparsetools as apt
            parser = argparse..ArgumentParser()
            parser.add_argument(..., type=apt.isdir)
    """
    return _os(arg, mode='d', mkdirs=False)


def isfile(arg):
    """
        Utility function for `ArgumentParser's add_argument
        <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument>`_
        type keyword. Checks if the argument is an existing file, returns the absolute path in case
        and raises the appropriate ArgumentParser error otherwise.
        Note that this function raises a meaningful OSError in case of non-existing parent directory
        (hopefully saving useless browsing time)
        :Example:
            import utils.argparsetools as apt
            parser = argparse..ArgumentParser()
            parser.add_argument(..., type=apt.isfile)
    """
    return ensurefiler(arg)


def ensuredir(arg):
    """
        Utility function for `ArgumentParser's add_argument
        <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument>`_
        type keyword.
        Checks if the argument is an existing dir, attempts to create the directory tree in case,
        and eventually returns the absolute path if the directory exists. Raises
        the appropriate ArgumentParser error otherwise
        :Example:
            import utils.argparsetools as apt
            parser = argparse..ArgumentParser()
            parser.add_argument(..., type=apt.ensuredir)
    """
    return _os(arg, mode='d', mkdirs=True)


def ensurefilew(arg):
    """
        Utility function for `ArgumentParser's add_argument
        <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument>`_
        type keyword.
        Checks if the argument is an existing file FOR WRITING, so it attempts to create the
        directory tree in case, and eventually returns the absolute path if the directory exists.
        Raises the appropriate ArgumentParser error otherwise
        :param arg: the argument to be parsed, usually provided by a command line option
        :type arg: string
        :return: os.path.abspath(arg) if arg can be used as file for writing
        :rtype: string
        :raises: argparse.ArgumentTypeError
        :Example:
            import utils.argparsetools as apt
            parser = argparse..ArgumentParser()
            parser.add_argument(..., type=apt.ensurefilew)
    """
    return _os(arg, mode='fw', mkdirs=True)


# def get_parser(*args):
#     """
#         Returns an ArgumentParser object by parsing the given arguments
#         :param args: The arguments to be parsed, as a list of arguments. Each argument is a dict
#             that will be passed to `ArgumentParser's add_argument
#             <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument>`_
#     """
#     parser = argparse.ArgumentParser()
#     for arg in args:
#         parser.add_argument(**arg)

# # build infile templatefile options outdir
# def parseargs(argv=sys.argv):
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-r', '--render_config',
#                         help='Sets a renderer config file which will pre-process the input rst.',
#                         default=None,
#                         type=argcheck_isfile)
#     parser.add_argument('-c', '--confdir', help='Sets the sphinx config directory.'
#                         '',  # FIXME: whatch out if we change the directory !!!
#                         default=None,
#                         type=lambda x: argcheck_isdir(x, False))
#     parser.add_argument('input_rst',
#                         help='The input rst file',
#                         type=argcheck_isfile)
#     parser.add_argument('output_path',
#                         help='The output folder',
#                         type=lambda x: argcheck_isdir(x, True))
#     parser.add_argument('-b',
#                         '--builder',
#                         default='html',
#                         help='builder to use; default is latex')
#     args = parser.parse_args(argv)
#     return args


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path',
                        help='The output folder',
                        type=os.path.isdir)
    args = parser.parse_args(['--output_path', '/adfnenv/rnjcenrvknrv/cnjrenv'])
    print str(args)