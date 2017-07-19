#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Mar 14, 2016

@author: riccardo
'''

import sys
import os
import subprocess
from sphinx import build_main as sphinx_build_main
# from reportbuild.core.utils import ensurefiler
import click
import six
from collections import OrderedDict
from contextlib import contextmanager
from sphinx.util.pycompat import execfile_
from sphinx.util.osutil import cd
from datetime import datetime

_DEFAULT_BUILD_TYPE = 'latex'


def pdflatex(texfile, texfolder=None):
    """
    Runs pdflatex with the given texfile as input
    :param texfile the input tex file
    :param texfolder: the texfile location directory. The pdflatex process will be run inside it.
        If None (default if missing), then it is texfile directory. Otherwise, texfile denotes the
        file name which must exist inside texfolder
    :return: the tuple return_status, out_pdf, new_or_modified
    :raise: OsError in case of file not found, pdflatex not installed etcetera.
    """
    texexists = False
    if texfolder is None:
        texexists = os.path.isfile(texfile)
        texfolder = os.path.dirname(texfile)
        texfile = os.path.basename(texfile)
    else:
        texexists = os.path.isfile(os.path.join(texfolder, texfile))

    if not texexists:
        raise OSError(os.errno.ENOENT, "'%s' does not exist")

    # seems that we need to call subprocess.call according to this post:
    # http://stackoverflow.com/questions/4230926/pdflatex-in-a-python-subprocess-on-mac
    # for interaction options, see here:
    # http://tex.stackexchange.com/questions/91592/where-to-find-official-and-extended-documentation-for-tex-latexs-commandlin
    # for -file-line-error, see:
    # https://tex.stackexchange.com/questions/27878/pdflatex-bash-script-to-supress-all-output-except-error-messages
    popenargs = ['pdflatexx', "-interaction=nonstopmode", "-file-line-error", texfile]
    kwargs = dict(cwd=texfolder, shell=False)
    try:
        # SIDE NOTE FOR DEVELOPERS: IF RUN FROM WITHIN ECLIPSE (AND POTENTIALLY ANY
        # OTHER EDITOR), AS os.environ['PATH'] is different than the shell $PATH
        # THE COMMAND BELOW MIGHT RAISE OSError

        ret = subprocess.call(popenargs, **kwargs)
    except OSError as oserr:
        appendix = " (is pdflatex installed?)" if oserr.errno == os.errno.ENOENT else ""
        # copied from sphinx, we want to preserve the same way of handling errors:
        raise OSError(oserr.errno, ("Unable to run 'pdflatex {0}': "
                                    "{1}{2}\n").format(texfile, os.strerror(oserr.errno), appendix))

    return ret


# def get_tex_files(path):
#     """Returns a dict of tex files directly under 'path' (no recursive search). The dict
#     keys are the tex files absolute path, the values are the relative last modified timestamps"""
#     ret = {}
#     if os.path.isdir(path):
#         for file_ in os.listdir(path):
#             if ".dontcompile." in file_:
#                 continue
#             absfile = os.path.abspath(os.path.join(path, file_))
#             if os.path.splitext(file_)[1].lower() == '.tex':
#                 ret[absfile] = os.stat(absfile)[8]
#
#     return ret


def _run_sphinx(sourcedir, outdir, master_doc, build=_DEFAULT_BUILD_TYPE,
                listener=None, *other_sphinxbuild_options):
    """Runs sphinx-build (with build either 'latex' or 'html' or 'pdf') returning the integer
    result:
    ```
        0 # ok, output file modified or newly created
        1 #errors/warnings, However, output file modified or newly created
          # (this is mainly used for pdflatex, as it's run with "-interaction=nonstopmode"
          # a return status != 0 does not mean the pdf file is missing, nor that is "visually"
          # valid. The webapp for instance will refresh its view in this case)
        2 #errors/warnings, output file NEITHER modified NOR newly created
    ```
    :param sourcedir: the source input directory
    :param outdir: the output build directory
    :param build: either 'latex', 'html' or 'pdf'
    :param listener: a callback accepting four arguments:
        current_process_msg (string), e.g., 'Building html report', 'Running pdflatex'
        endtime: UTC datetime denoting when the process should end (or None if no such info
            available. Actually, this is non-None only in the
            second pdflatex step, if build = 'pdf', and it represents an estimation based on
            the previous run
        current_step: array of two elements: the current step, integer (starting from 1)
        total_steps_number (integer). The total number of steps. It is > 1 only if build == 'pdf'
    :param other_sphinxbuild_options: positional command line argument to be forwarded to
    sphinx-build
    :return: 0 on success, 1 on success with error (this holds only for build='pdf'
    meaning that pdflatex returned nonzero, but the pdf file was written), 2 on failure
    (no output written)
    :raise: OsError (returned from pdflatex) or any exception raised by sphinx build (FIXME: check)
    FIXME: does it raises with contextmanager???
    """
    if listener is None:
        def listener(*a, **v):
            pass

    steps = 3 if build == 'pdf' else 1
    # call sphinx:
    sphinxbuild = 'latex' if build == 'pdf' else build
    argv = ["", sourcedir, outdir, "-b", sphinxbuild] + list(other_sphinxbuild_options)

    with checkfilechanged(outdir, master_doc, sphinxbuild) as checker:
        listener('Building %s report' % sphinxbuild, None, 1, steps)
        res = sphinx_build_main(argv)

    res1 = res2 = 0  # results for pdflatex (if set)
    if checker.modified and build == 'pdf':
        texfilepath = checker.filepath
        with checkfilechanged(outdir, master_doc, build) as checker:
            start_ = datetime.utcnow()
            listener('Running pdflatex (1st step)', None, 2, steps)
            duration_ = datetime.utcnow() - start_
            res1 = pdflatex(texfilepath, None)
        if checker.modified:
            listener('Running pdflatex (2nd step)', datetime.utcnow() + duration_, 3, steps)
            with checkfilechanged(outdir, master_doc, build) as checker:
                res2 = pdflatex(texfilepath, None)

    if not checker.modified:
        res = 2
    elif (res != 0 or res1 != 0 or res2 != 0):
        res = 1
    return res


def run(sourcedir, outdir, build=_DEFAULT_BUILD_TYPE, *other_sphinxbuild_options):
    """Runs sphinx-build from command line
    :param sourcedir: the source input directory
    :param outdir: the output build directory
    :param build: the build type (string). Currently supported are 'latex' (default), 'html', 'pdf'
    If 'pdf', then pdflatex and relative libraries must be installed
    :param other_sphinxbuild_options: positional command line argument to be forwarded to
    sphinx-build
    :raise: OsError (returned from pdflatex) or any exception raised by sphinx build (FIXME: check)
    Example
    -------

    run('/me/my/path', '/me/another/path', 'pdf', '-E')
    """
    confdir = sourcedir
    # get conf dir, if any (copied from sphinx cmdline):
    for i, a in enumerate(other_sphinxbuild_options):
        if a == '-c' and i < len(other_sphinxbuild_options) - 1:
            confdir = other_sphinxbuild_options[i + 1]
            break
    conf_file = os.path.join(confdir, 'conf.py')

    return _run_sphinx(sourcedir, outdir, get_master_doc(conf_file), build, None,
                       *other_sphinxbuild_options)


def get_master_doc(conf_file):
    '''returns the master_doc' variable stored in the given config file'''
    if not os.path.isfile(conf_file):
        raise ValueError("Not conf  file found: '%s'" % conf_file)

    # execute conf file to get the master document
    # Copied from sphinx.util.pycompat.py
    _globals = {"__file__": conf_file}  # the namespace where toe xec stuff with six
    with cd(os.path.dirname(conf_file)):
        execfile_("conf.py", _globals)

    if 'master_doc' not in _globals:
        raise ValueError("'master_doc' undefined in '%s'" % conf_file)

    return _globals['master_doc']


class checkfilechanged(object):
    '''class which takes sphinx vars and used within a with statement returns two members:
    filepath and modified
    that return the output file path and if the file was modified. Modified means
    that the file is newly created OR its modification time is greater than the modification time
    it had before entering this object''' 
    def __init__(self, outdir, master_doc, buildtype):
        ext = 'tex' if buildtype == 'latex' else buildtype
        self.filepath = os.path.join(outdir, master_doc + "." + ext)
        self.mtime = float('-inf')
        if os.path.isfile(self.filepath):
            self.mtime = os.stat(self.filepath).st_mtime
        self._modified = False

    @property
    def modified(self):
        return self._modified

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:  # we raised an exception
            # python exception: Although is neither a sphinx error nor a pdflatex error,
            # Format the exception as a sphinx exception:
            fname = os.path.split(traceback.tb_frame.f_code.co_filename)[1]
            sys.stderr.write("%s:%d: ERROR: %s: %s" % (fname, traceback.tb_lineno,
                                                       str(exc_value.__class__.__name__),
                                                       str(exc_value)))

        # If the context was exited without an exception, all three arguments will be None
        if os.path.isfile(self.filepath) and os.stat(self.filepath).st_mtime > self.mtime:
            self._modified = True

        # If an exception is supplied, and the method wishes to suppress the exception
        # (i.e., prevent it from being propagated), it should return a true value
        return True


# use a commandline ability to forward to sphinx-build with some pre- and post-processing on
# the --build argument:

# as when we provide --sphinxhelp we should not check for sourcedir and outdir existence
# we cannot set the nargs=1 and required=True in @click.argument, so we implement this function
# that behaves as nargs=1+required=True
def check_dirs(ctx, param, value):
    if not value and "sphinxhelp" not in ctx.params:
        raise click.BadParameter("Missing argument", ctx=ctx, param=param)
    return value


@click.command(context_settings=dict(ignore_unknown_options=True,),
               options_metavar='[options]')
@click.argument('sourcedir', nargs=1, required=False, callback=check_dirs,
                metavar='sourcedir')  # @IgnorePep8
@click.argument('outdir', nargs=1, required=False, callback=check_dirs, metavar='outdir')
@click.option('-b', '--build',
              help=('builder to use. Default is ' + _DEFAULT_BUILD_TYPE + ' (in '
                    'sphinx-build is html). You can also type pdf: if this program is correctly '
                    'installed (with all latex libs) then `sphinx-build -b latex ...` is first '
                    'executed and then pdflatex is run on all .tex files in outdir which '
                    'did not exist before (or whose last-modified time changed during) this '
                    'program execution. This usually works fine but might compile also latex '
                    'additional files provided in conf.py, at least after the first build, as they '
                    'will be seen as new: to avoid this, put the string ".dontcompile." in the '
                    '.tex file names. Note that this program has been currently tested '
                    'only for sphinx builds generating a single .tex file in outdir'),
              default=_DEFAULT_BUILD_TYPE, type=click.Choice(['html', 'pdf', _DEFAULT_BUILD_TYPE]))
@click.argument('other_sphinxbuild_options', nargs=-1, type=click.UNPROCESSED,
                metavar='[other_sphinxbuild_options]')
@click.option('--sphinxhelp', is_flag=True, default=False, help='print out the sphinx-build help '
              'to know which options (except -b, --build) or arguments (except sourcedir, outdir) '
              'can be passed in [other_sphinxbuild_options]')
def main(sourcedir, outdir, build, other_sphinxbuild_options, sphinxhelp):
    """A wrapper around sphinx-build"""
    if sphinxhelp:
        sphinx_build_main(["", "--help"])
        return 0

    # for info see:
    # sphinx/cmdline.py, or
    # http://www.sphinx-doc.org/en/1.5.1/man/sphinx-build.html
    sys.exit(run(sourcedir, outdir, build, *list(other_sphinxbuild_options)))


if __name__ == '__main__':
    main()  # pylint:disable=no-value-for-parameter
