#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Mar 14, 2016

@author: riccardo
'''

# we do want: an initial rst. A config file. We pass it to the build function by copying the system
# argv
# from __future__ import print_function
import sys
import re
import os
# import reportbuild.preparser as pp
import subprocess
from sphinx import build_main as sphinx_build_main
from reportbuild.core.utils import ensurefiler


def pdflatex(texfile, texfolder=None):
    """
    Runs pdflatex with the given texfile as input
    :param texfile the input tex file
    :param texfolder: the texfile location directory. The pdflatex process will be run inside it.
        If None (default if missing), then it is texfile directory. Otherwise, texfile denotes the
        file name which must exist inside texfolder
    :raise: OsError in case of file not founds, pdflatex not installed etcetera.
    """
    if texfolder is None:
        texfolder = os.path.dirname(texfile)
        texfile = os.path.basename(texfile)
    ensurefiler(os.path.join(texfolder, texfile))

    # seems that we need to call subprocess.call according to this post:
    # http://stackoverflow.com/questions/4230926/pdflatex-in-a-python-subprocess-on-mac
    # for interaction options, see here:
    # http://tex.stackexchange.com/questions/91592/where-to-find-official-and-extended-documentation-for-tex-latexs-commandlin
    popenargs = ['pdflatex', "-interaction=nonstopmode", texfile]
    kwargs = dict(cwd=texfolder, shell=False)
    ret = subprocess.call(popenargs, **kwargs)
    # run twice for references:

    if ret != 0:
        sys.stdout.write("WARNING: pdflatex returned an exit status {0:d} (0=Ok)".format(ret))

    ret = subprocess.call(popenargs, **kwargs)

    return ret

    # ret = subprocess.call(['pdflatex', "-interaction=nonstopmode", texfile], cwd=texfolder,
    #                       shell=False)
def get_tex_files(path):
    ret = {}
    for file_ in os.listdir(path):
        absfile = os.path.abspath(os.path.join(path, file_))
        if os.path.splitext(file_)[1].lower() == '.tex':
            ret[absfile] = os.stat(absfile)[8]

    return ret


def run(sysargv):
    # wrap up arguments and check builder and project name, if supplied
    # if latex builder, remember output path and run the corresponding pdf on that file when
    # finished. Note also that default is latex, sphinx uses html
    config_dir_specified = False
    use_config = not ("-C" in sysargv or "--noconfig" in sysargv)
    skipthis = False  # used in the loop below
    do_pdf = False
    build_specified = False
    indir = None
    outdir = None
    old_tex_files = {}
    for i, c in enumerate(sysargv[1:], 1):
        if skipthis:
            skipthis = False
            continue
        if not re.match("^-\\w$", c) and not re.match("^--\\w+$", c):
            if indir is None:
                indir = c
            elif outdir is None:
                outdir = c
            continue
        if use_config and (c == "-c" or c == "--confdir"):
            config_dir_specified = True
            skipthis = True
        elif c == "-b" or c == "--builder":
            build_specified = True
            do_pdf = sysargv[i+1] == 'pdf'
            if do_pdf:
                sysargv[i+1] = 'latex'
            skipthis = True

    # change default config if NOT specified:
#     if not config_dir_specified and use_config:
#         sysargv.append('-c')
#         sysargv.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
#                                                     "../configs/default")))

    if do_pdf:
        old_tex_files = get_tex_files(outdir)
    elif not build_specified:
        sysargv.append('-b')
        sysargv.append("latex")

    # cwd = os.getcwd()
    # curiously, sphinx does NOT change cwd. We must do it
    # most probably we miss something here. FIXME: check that!
    # os.chdir(indir)

    res = sphinx_build_main(sysargv)

    if res == 0 and do_pdf:
        new_tex_files = get_tex_files(outdir)
        tex_files = []  # real list of tex files to pdf-process
        for fileabspath, file_mtime in new_tex_files.iteritems():
            if fileabspath not in old_tex_files or file_mtime > old_tex_files[fileabspath]:
                tex_files.append(fileabspath)

        for fileabspath in tex_files:
            try:
                res = pdflatex(fileabspath)
            except OSError as oserr:
                appendix = ""
                if oserr.errno == os.errno.ENOENT:
                    appendix = " (is pdflatex installed?)"
                # copied from sphinx, we want to preserve the same way of handling errors:
                sys.stderr.write("Unable to run 'pdflatex {0}': {1}{2}\n".format(fileabspath,
                                                                                 str(oserr),
                                                                                 appendix)
                                 )
                res = 1

    # os.chdir(cwd)
    return res


def main():
    sys.exit(run(sys.argv))

if __name__ == '__main__':
    main()


###  sphinx command line (will be removed):
#     parser = optparse.OptionParser("", epilog="", formatter=MyFormatter())
#     parser.add_option('--version', action='store_true', dest='version',
#                       help='show version information and exit')
# 
#     group = parser.add_option_group('General options')
#     group.add_option('-b', metavar='BUILDER', dest='builder', default=None,  # changed
#                      help='builder to use; default is html')
#     group.add_option('-a', action='store_true', dest='force_all',
#                      help='write all files; default is to only write new and '
#                      'changed files')
#     group.add_option('-E', action='store_true', dest='freshenv',
#                      help='don\'t use a saved environment, always read '
#                      'all files')
#     group.add_option('-d', metavar='PATH', default=None, dest='doctreedir',
#                      help='path for the cached environment and doctree files '
#                      '(default: outdir/.doctrees)')
#     group.add_option('-j', metavar='N', default=1, type='int', dest='jobs',
#                      help='build in parallel with N processes where possible')
#     # this option never gets through to this point (it is intercepted earlier)
#     # group.add_option('-M', metavar='BUILDER', dest='make_mode',
#     #                 help='"make" mode -- as used by Makefile, like '
#     #                 '"sphinx-build -M html"')
# 
#     group = parser.add_option_group('Build configuration options')
#     group.add_option('-c', metavar='PATH', dest='confdir',
#                      help='path where configuration file (conf.py) is located '
#                      '(default: same as sourcedir)')
#     group.add_option('-C', action='store_true', dest='noconfig',
#                      help='use no config file at all, only -D options')
#     group.add_option('-D', metavar='setting=value', action='append',
#                      dest='define', default=[],
#                      help='override a setting in configuration file')
#     group.add_option('-A', metavar='name=value', action='append',
#                      dest='htmldefine', default=[],
#                      help='pass a value into HTML templates')
#     group.add_option('-t', metavar='TAG', action='append',
#                      dest='tags', default=[],
#                      help='define tag: include "only" blocks with TAG')
#     group.add_option('-n', action='store_true', dest='nitpicky',
#                      help='nit-picky mode, warn about all missing references')
#  
#     group = parser.add_option_group('Console output options')
#     group.add_option('-v', action='count', dest='verbosity', default=0,
#                      help='increase verbosity (can be repeated)')
#     group.add_option('-q', action='store_true', dest='quiet',
#                      help='no output on stdout, just warnings on stderr')
#     group.add_option('-Q', action='store_true', dest='really_quiet',
#                      help='no output at all, not even warnings')
#     group.add_option('-N', action='store_true', dest='nocolor',
#                      help='do not emit colored output')
#     group.add_option('-w', metavar='FILE', dest='warnfile',
#                      help='write warnings (and errors) to given file')
#     group.add_option('-W', action='store_true', dest='warningiserror',
#                      help='turn warnings into errors')
#     group.add_option('-T', action='store_true', dest='traceback',
#                      help='show full traceback on exception')
#     group.add_option('-P', action='store_true', dest='pdb',
#                      help='run Pdb on exception')
