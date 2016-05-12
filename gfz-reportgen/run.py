#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Test module. Copied from sphinx-build.py in
https://github.com/sphinx-doc/sphinx
Created on Mar 14, 2016

@author: riccardo
'''

# we do want: an initial rst. A config file. We pass it to the build function by copying the system
# argv
from __future__ import print_function
import sys
import argparse
import os
import reportgen.preparser as pp
import shutil
import subprocess
from os import path
from sphinx import build_main as sphinx_build_main
from sphinx.util.console import nocolor, color_terminal
from sphinx.util.osutil import abspath
import core.utils.argparsetools as apt
from core.utils import ensurefiler, ensuredir
from sphinx.cmdline import MyFormatter
import optparse


# def get_default_config_dir():
#     return os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__), "../source")))


# build infile templatefile options outdir
# def parseargs(argv=sys.argv):
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-r', '--render_config',
#                         help='Sets a renderer config file which will pre-process the input rst.',
#                         default=None,
#                         type=apt.isfile)
#     parser.add_argument('-c', '--confdir', help='Sets the sphinx config directory.'
#                         '',  # FIXME: whatch out if we change the directory !!!
#                         default=None,
#                         type=apt.isdir)
#     parser.add_argument('input_rst',
#                         help='The input rst file',
#                         type=apt.isfile)
#     parser.add_argument('output_path',
#                         help='The output folder',
#                         type=apt.ensuredir)
#     parser.add_argument('-b',
#                         '--builder',
#                         default='html',
#                         help='builder to use; default is latex')
#     args = parser.parse_args(argv)
#     return args


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
    cmd = 'pdflatex \"'+texfile+"\""
    p = subprocess.Popen(cmd, cwd=texfolder, stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        print(line)
    p.stdout.close()
    p.wait()


# input rst => copy to source sphinx, delete it later?
# spurcedir: check for any of the following: conf.py, '_static' and '_templates', copy files if any
# if not specified, do not copy anything, but copy back conf.default.py into conf.py
# -r renderer: preprocess rst with this file via templating system

# Verbose comment but stuff are getting complex need to be documented:
# sphinx first gets two "positional"? arguments, indir, outdir. Anyway, not preceeded by --something
# or -s or whatever with minus.
# sphinx gets gets recursively all rst files in indir (unless specified in the exclude pattern flag
# in conf.py) and then processes them and puts everything in outdir
# Now, we have a configuration file and a rst template for pre-processing and creating our
# infile.rst. We might want to:
# 1) simply use indir in sphinx as the directory of infile. Problem: we need to copy there also
# conf.py, which can be done easily but PROBLEM: in conf.py are defined the extensions relative to
# the path our conf.py is, not the path our conf.py will be moved. Shit... So: copy conf.py by
# modifying the extension paths BUT in any case ALL paths specified in conf.py and in the arguments
# are relative to the source directory (e.g., templates dir etcetera). In one word: do not move
# conf.py
# So we go for another option: in the preprocess all variables ending with "_path" are paths which
# denote filenames. Change those paths and use relative paths (relative to the source directory) and
# build opur infile which we will put inside our indir, which stays the 'default' in config.py
#

# from __future__ import print_function

# def main2():
#     # wrap up arguments and check builder and project name, if supplied
#     # if latex builder, remember output path and run the corresponding pdf on that file when
#     # finished. Note also that default is latex, sphinx uses html
# 
#     # copied from sphinx cmdline:
# 
#     parser = optparse.OptionParser("", epilog="", formatter=MyFormatter())
#     parser.add_option('--version', action='store_true', dest='version',
#                       help='show version information and exit')
# 
#     group = parser.add_option_group('General options')
#     group.add_option('-b', metavar='BUILDER', dest='builder', default='html',
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
# 
#     # parse options
#     try:
#         opts, args = parser.parse_args(argv[1:])
#     except SystemExit as err:
#         return err.code
# 
#     # get paths (first and second positional argument)
#     try:
#         srcdir = abspath(args[0])
#         confdir = abspath(opts.confdir or srcdir)
#         if opts.noconfig:
#             confdir = None
#         if not path.isdir(srcdir):
#             print('Error: Cannot find source directory `%s\'.' % srcdir,
#                   file=sys.stderr)
#             return 1
#         if not opts.noconfig and not path.isfile(path.join(confdir, 'conf.py')):
#             print('Error: Config directory doesn\'t contain a conf.py file.',
#                   file=sys.stderr)
#             return 1
#         outdir = os.path.abspath(args[1])
#         if srcdir == outdir:
#             print('Error: source directory and destination directory are same.',
#                   file=sys.stderr)
#             return 1
#         ensuredir(outdir)  # added by me, ensure output dir exists
#     except IndexError:
#         parser.print_help()
#         return 1
#     except UnicodeError:
#         print(
#             'Error: Multibyte filename not supported on this filesystem '
#             'encoding (%r).' % fs_encoding, file=sys.stderr)
#         return 1
# 
#     confoverrides = {}
#     for val in opts.define:
#         try:
#             key, val = val.split('=')
#         except ValueError:
#             print('Error: -D option argument must be in the form name=value.',
#                   file=sys.stderr)
#             return 1
#         if likely_encoding and isinstance(val, binary_type):
#             try:
#                 val = val.decode(likely_encoding)
#             except UnicodeError:
#                 pass
#         if val == u'project'
#         confoverrides[key] = val
# 
#     parser = argparse.ArgumentParser()
#     parser.add_option('-D', metavar='setting=value', action='append',
#                      dest='define', default=[],
#                      help='override a setting in configuration file')
#     parser.add_argument('-p', '--project',
#                         help='Sets a renderer config file which will pre-process the input rst.',
#                         default=None,
#                         type=apt.isfile)
#     parser.add_argument('-c', '--confdir', help='Sets the sphinx config directory.'
#                         '',  # FIXME: whatch out if we change the directory !!!
#                         default=None,
#                         type=apt.isdir)
#     parser.add_argument('input_rst',
#                         help='The input rst file',
#                         type=apt.isfile)
#     parser.add_argument('output_path',
#                         help='The output folder')
#     parser.add_argument('-b',
#                         '--builder',
#                         default=None,
#                         help='builder to use; default is latex')
# 
#     args = parser.parse_args(argv)
#     
#     _dir = '../source'
#     args = parseargs([_dir + '/_templates/input_rsts/report_base.rst',
#                       '-r', _dir + '/report_base_conf.py',
#                       '/Users/riccardo/Public/report_test'])  # , '-b', 'latex'])  # '-s', '../source'
# 
#     args = vars(args)
# 
#     input_file = args.pop('input_rst')
#     with open(input_file, 'r') as ipt:
#         content = pp.render(ipt,
#                             **pp.read_config_and_normalize_paths(args.pop('render_config', None),
#                                                                  get_default_config_dir())
#                             )
# 
#     # write index.rst
#     indir = get_default_config_dir()
#     # copy files. first, content must be written as index.rst in confdir
#     sphinx_input_file = os.path.join(indir, 'index.rst')
#     with open(sphinx_input_file, 'w') as ifile:
#         ifile.write(content)
# 
#     confdir = args['confdir']
#     if confdir is not None:  # FIXME: remove!!!!
#         # copy relevant data:
#         # note that if confdir is not specified, none of these files is copied
#         # we add a check thought for safety
#         data = [('conf.py', 'f'), ('_static', 'd'), ('_templates', 'd')]
#         for d in data:
#             infile = os.path.abspath(os.path.join(confdir, d[0]))
#             outfile = os.path.abspath(os.path.join(indir, d[0]))
#             if d[1] == 'd' and infile != outfile and not os.path.isdir(outfile):
#                 shutil.copytree(infile, outfile)
#             elif d[1] == 'f' and infile != outfile and not os.path.isfile(outfile):
#                 shutil.copy2(infile, outfile)
# 
#     d = []
#     d.append(sys.argv[0])
#     d.append(indir)  # indir (searches for index.rst?)
#     outdir = args.pop('output_path')
#     d.append(outdir)  # outdir
#     # d.extend(['-c', '../source'])  #  path where the config.py is
#     what = args.pop('builder')
#     do_pdf = False
#     if what == 'pdf':
#         what = 'latex'
#         do_pdf = True
#     d.extend(['-b', what])  # ['-b', 'html'])  # or latex
# 
#     cwd = os.getcwd()
#     os.chdir(indir)
#     res = sphinx_build_main(d)
#     os.chdir(cwd)
#     if res == 0 and do_pdf:
#         try:
#             pdflatex("reportgen.tex", outdir)
#         except OSError as oserr:
#             # copied from sphinx, we want to preserve the same way of handling errors:
#             sys.stderr.write("Unable to run pdflatex " + str(oserr))
#             res = 1
#     sys.exit(res)

# import shlex
# def preparse_args(sysargv):
#     for i, var in enumerate(sysargv[1:]):
#         if var == '-c' or var == '--confdir':
#             if i+1 < len(sysargv):
#                 confdir = sysargv[i+1]
#                 if os.path.abspath(os.path.normpath(confdir)) != 
#                     get_default_config_dir():

def get_tex_files(path):
    ret = {}
    for file_ in os.listdir(path):
        absfile = os.path.abspath(os.path.join(path, file_))
        if os.path.splitext(file_)[1].lower() == '.tex':
            ret[absfile] = os.stat(absfile)[8]

    return ret


def main(sysargv):
    # wrap up arguments and check builder and project name, if supplied
    # if latex builder, remember output path and run the corresponding pdf on that file when
    # finished. Note also that default is latex, sphinx uses html
 
    # copied from sphinx cmdline:
 
    parser = optparse.OptionParser("", epilog="", formatter=MyFormatter())
    parser.add_option('--version', action='store_true', dest='version',
                      help='show version information and exit')

    group = parser.add_option_group('General options')
    group.add_option('-b', metavar='BUILDER', dest='builder', default=None,  # changed
                     help='builder to use; default is html')
    group.add_option('-a', action='store_true', dest='force_all',
                     help='write all files; default is to only write new and '
                     'changed files')
    group.add_option('-E', action='store_true', dest='freshenv',
                     help='don\'t use a saved environment, always read '
                     'all files')
    group.add_option('-d', metavar='PATH', default=None, dest='doctreedir',
                     help='path for the cached environment and doctree files '
                     '(default: outdir/.doctrees)')
    group.add_option('-j', metavar='N', default=1, type='int', dest='jobs',
                     help='build in parallel with N processes where possible')
    # this option never gets through to this point (it is intercepted earlier)
    # group.add_option('-M', metavar='BUILDER', dest='make_mode',
    #                 help='"make" mode -- as used by Makefile, like '
    #                 '"sphinx-build -M html"')

    group = parser.add_option_group('Build configuration options')
    group.add_option('-c', metavar='PATH', dest='confdir',
                     help='path where configuration file (conf.py) is located '
                     '(default: same as sourcedir)')
    group.add_option('-C', action='store_true', dest='noconfig',
                     help='use no config file at all, only -D options')
    group.add_option('-D', metavar='setting=value', action='append',
                     dest='define', default=[],
                     help='override a setting in configuration file')
    group.add_option('-A', metavar='name=value', action='append',
                     dest='htmldefine', default=[],
                     help='pass a value into HTML templates')
    group.add_option('-t', metavar='TAG', action='append',
                     dest='tags', default=[],
                     help='define tag: include "only" blocks with TAG')
    group.add_option('-n', action='store_true', dest='nitpicky',
                     help='nit-picky mode, warn about all missing references')
 
    group = parser.add_option_group('Console output options')
    group.add_option('-v', action='count', dest='verbosity', default=0,
                     help='increase verbosity (can be repeated)')
    group.add_option('-q', action='store_true', dest='quiet',
                     help='no output on stdout, just warnings on stderr')
    group.add_option('-Q', action='store_true', dest='really_quiet',
                     help='no output at all, not even warnings')
    group.add_option('-N', action='store_true', dest='nocolor',
                     help='do not emit colored output')
    group.add_option('-w', metavar='FILE', dest='warnfile',
                     help='write warnings (and errors) to given file')
    group.add_option('-W', action='store_true', dest='warningiserror',
                     help='turn warnings into errors')
    group.add_option('-T', action='store_true', dest='traceback',
                     help='show full traceback on exception')
    group.add_option('-P', action='store_true', dest='pdb',
                     help='run Pdb on exception')

    # parse options
    try:
        opts, args = parser.parse_args(sysargv[1:])
    except SystemExit as err:
        return err.code

    do_pdf = False
    old_tex_files = {}
    if opts.builder is None:  # set default builder to latex
        sysargv += ["-b", "latex"]
    elif opts.builder == 'pdf':
        for i, var in enumerate(sysargv):
            if var == '-b' or var == '--builder':
                sysargv[i+1] = 'latex'
                do_pdf = True
                # get all tex files in the dir and check their datetime
                old_tex_files = get_tex_files(args[1])
                break

    cwd = os.getcwd()
    os.chdir(args[0])

    res = sphinx_build_main(sysargv)

    if res == 0 and do_pdf:
        new_tex_files = get_tex_files(args[1])
        tex_files = []  # real list of tex files to pdf-process
        for fileabspath, file_mtime in new_tex_files.iteritems():
            if fileabspath not in old_tex_files or file_mtime > old_tex_files[fileabspath]:
                tex_files.append(fileabspath)

        for fileabspath in tex_files:
            try:
                pdflatex(fileabspath)
            except OSError as oserr:
                appendix = ""
                if oserr.errno == os.errno.ENOENT:
                    appendix = " (is pdflatex installed?)"
                # copied from sphinx, we want to preserve the same way of handling errors:
                sys.stderr.write("Unable to run 'pdflatex {0}': {1}{2}".format(fileabspath,
                                                                               str(oserr),
                                                                               appendix)
                                 )
                res = 1

    os.chdir(cwd)
    return res


if __name__ == '__main__':
    sys.exit(main(sys.argv))
