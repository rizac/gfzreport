#!/usr/bin/env ptatioython
# -*- coding: utf-8 -*-
'''
Created on May 18, 2016
@author: riccardo
'''

# from __future__ import print_function

import os
import sys
import shutil
import inspect
from glob import glob
from contextlib import contextmanager
import errno

from io import BytesIO

import click
from jinja2 import Environment, BaseLoader
from jinja2.loaders import FileSystemLoader

from gfzreport.sphinxbuild import get_master_doc


def makedirs(path):
    """Same as os.makedirs except that it silently exits if the path already exists
    Raises OSError in case the directory cannot be created"""
    if not os.path.isdir(path):
        os.makedirs(path)
        if not os.path.isdir(path):
            raise OSError(errno.ENOTDIR, "makedirs failed: " + os.strerror(errno.ENOTDIR), path)
    return path


def copyfiles(src, dst_dir, move=False):
    """
        Copies /move files recursively, extending shutil and allowing glob expressions
        in src
        :param src: a file/directory which MUST not be a system directory, denoting:
            * an existing file. In this case `shutil.copy2(src, dst)` will be called
              (If the destination file already exists under 'dst', it will be overridden)
            * a directory, in that case *all files and dirs within src* will be moved or copied.
              (if move=True and src is empty after the move, then src will be deleted)
            * a glob expression such as '/home/*pdf'. Then, all files matching the glob
                expression will be copied / moved
        :param dst: a destination DIRECTORY. If it does not exists, it will be created
        (os.makedirs, basically alias of 'mkdir -p').
    """
    files_count = 0

    if os.path.isdir(src):
        for fle in os.listdir(src):  # FIXME: use shutil.cptree?
            files_count += copyfiles(os.path.join(src, fle), dst_dir, move)
        # since we moved all files, we remove the dir if it's empty:
        if move and not os.listdir(src):
            shutil.rmtree(src, ignore_errors=True)

    elif os.path.isfile(src):
        dst_dir_exists = os.path.isdir(dst_dir)
        # copytree does not work if dest exists. So
        # for file in os.listdir(src):
        if not move:
            if not dst_dir_exists:
                # copy2 requires a dst folder to exist,
                makedirs(dst_dir)
            shutil.copy2(src, dst_dir)
        else:
            shutil.move(src, dst_dir)

        files_count = 1
    else:
        # in principle, if src denotes a non-existing file or dir, glb_list is empty, if it
        # denotes an existing file or dir, it has a single element equal to src.
        for srcf in glob(src):  # glob returns joined pathname, it's not os.listdir!
            files_count += copyfiles(srcf, dst_dir, move)

    return files_count


def setupdir(src_path, dest_path, confirm, update_config_only):
    """Creates a template report from `src_path` into `dest_path`.
    Returns the data directory:
    `os.path.join(dest_path, 'data')`
    which is guaranteed to exist if `update_config_only=False`. In this latter case,
    the user can then populate the returned directory with the template data
    """
    # NOTE: we will delete dest_path if this function raises and created it meanwhile
    # so first of all keep track if dest_path exists (should return always False)
    out_path_exists = os.path.isdir(dest_path)

    if not os.path.isdir(src_path):
        raise ValueError("sourcedir '%s': not a directory" % src_path)

    if out_path_exists and not update_config_only:
        # Putting content in an already existing non-empty directory is
        # unmaintainable. The user can only overwrite config files
        raise ValueError(("'%s' already exists.\n"
                          "Please provide a non-existing directory name") % dest_path)
    elif not out_path_exists and update_config_only:
        raise ValueError(("'%s' does not exist.\n"
                          "Please provide an existing directory name when "
                          "updating config only") % dest_path)

    if confirm:
        strmsg = """Report's config files will be written to:
%s%s
Continue?
""" % (dest_path, "\nThe directory path will be created (mkdir -p)" if not out_path_exists else "")
        if not click.confirm(strmsg):
            raise ValueError("Aborted by user")

    # make dest_dir first if it does not exist
    dest_path = makedirs(dest_path)

    confdirname = 'conf_files'
    conffilename = 'conf.py'
    dest_confdir = os.path.join(dest_path, confdirname)
    src_confdir = os.path.join(src_path, confdirname)
    src_conffile = os.path.join(src_path, conffilename)
    dest_conffile = os.path.join(dest_path, conffilename)

    if update_config_only and os.path.isdir(dest_confdir):
        print("Removing '%s'" % dest_confdir)
        shutil.rmtree(dest_confdir, ignore_errors=False)

    print("Copying recursively '%s' in '%s' " % (confdirname, dest_confdir))
    # copy sphinx configuration stuff:
    shutil.copytree(src_confdir, dest_confdir)
    print("Copying '%s' in '%s' " % (conffilename, dest_confdir))
    shutil.copy2(src_conffile, dest_conffile)


@contextmanager
def get_rst_template(src_path, dest_path):
    '''Yields an object wrapping the `template <http://jinja.pocoo.org/docs/2.9/api/#jinja2.Template>`_
    T of the rst report defined in src_path.
    Called R the returned object, the user has then to call `R.render(**args)`,
    where args is a set of keyword argument depending on the report type implemented.
    `R.render` basically calls `T.render` and writes `T` content to file into `dest_path`
    '''
    masterdoc = get_master_doc(os.path.join(src_path, 'conf.py'))
    rst_src_file = os.path.join(src_path, masterdoc + ".rst")

    class Wrapper(object):

        def __init__(self, filein, fileout):
            self.inpath = os.path.dirname(filein)
            self.filename = os.path.basename(filein)
            self.fileout = fileout

        def render(self, *args, **kwargs):
            template = Environment(loader=FileSystemLoader(self.inpath)).get_template(self.filename)
            # template = Environment(loader=BaseLoader()).from_string(self.content)
            template.stream(*args, **kwargs).dump(self.fileout, encoding='UTF8')

    rst_dest_file = os.path.join(dest_path, os.path.basename(rst_src_file))
    yield Wrapper(rst_src_file, rst_dest_file)


class Logger(object):
    '''class printing to stdout and to log'''

    def __init__(self):
        self._tmp_sysout = sys.stdout
        self.terminal = sys.stdout
        self.log = BytesIO()  # write everything in bytes to the stream

    def write(self, message):
        self.terminal.write(message)
        if not isinstance(message, bytes):
            message = message.encode('utf8')
        self.log.write(message)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # In the example here they pass:
        # https://stackoverflow.com/questions/14906764/how-to-redirect-stdout-to-both-file-and-console-with-scripting
        # here we forward the flush:
        self.terminal.flush()
        self.log.flush()

    def close(self, fileout=None):
        '''closes the streams, restores sys.stdout and write the content to fileout, if provided'''
        sys.stdout = self._tmp_sysout
        if fileout:
            with open(fileout, 'wb') as opn:
                opn.write(self.log.getvalue())
        try:
            self.log.close()
        except:
            pass


def get_logfilename():
    """Returns the name of the gfzreport sphinx log file when launching the tamplate creation
    """
    return "gfzreport.template.log"


class Templater(object):
    '''
    Base skeleton class implementation of what a
    gfzreport template should do. As any template creates destination directories
    (sources for `sphinx build`) with shared tree structure, this class handles common operation
    (e.g. cp, mv, mkdir) allowing DRY code. The source directory of a template package
    must be of the form:

        * conf_files [DIR]

        * conf.py

        * report.rst

    The destination directories that a `Templater` should create all have this structure:

        * conf_files [DIR]

        * conf.py

        * report.rst

        * data [DIR]

    So, basically, by looking at the two structures it is just all about copying a directory
    tree and `mkdir` 'data' in it.
    Well.. almost: `conf_files` and `conf.py` are in fact copied from the source to the destination,
    and the 'data' directory is actually created with `makedirs` (alias for mkdir -p). On the other
    hand, what is the destination directory, what to put in 'data' and how to write `report.rst`
    (which is a rst document but might be a jinja template, if desired) have to be provided by the
    user by sub-classing the following methods, which should tell:

        * what is the destination path (implement `self.getdestpath`): this can be `self._out_path`
          or whatever sub-directory in it according to the arguments

        * what to copy / move into `data` directory (implement `self.getdatafiles`) or in its
          sub-directories. The user has just to return a dict where the keys are the 'data' dir
          or any sub-direcotory of it, and the values are lists of files to be put there.
          The user has not to handle file-system operations (copy or move, mkdir) which is done
          by the super-class

        * which arguments to pass to the `render` method of the jinja template created from
          `reporst.rst` (implement `self.getrstkwargs`). You can just return None/empty dict or
          pass if `report.rst` is a simple "unmodifiable" rst
    '''

    def __init__(self, out_path, update_config_only, mv_data_files, confirm):
        '''Initializes an (abstract class) Templater
        :param out_path: the *initial* destination directory. This is usually a destination root
        and the real destination path must be implemented in `self.getdestpath` (which might return
        self._out_path, it depends on the implementation)
        :param update_config_only: weather the real destination path should update the sphinx
        config files only when this object is called as function
        :param mv_data_files: ignored if `update_config_only=True`, tells weather the real
        destination path should have files moved therein
        when `update_config_only=False`. The files to move or copy are those returned by
        `self.getdatafiles` (to be sub-classed)
        :param: weather to confirm, when this function is called as function, before
        setting all up
        '''
        self._out_path = out_path
        self._update_config_only = update_config_only
        self._mv_data_files = mv_data_files
        self._confirm = confirm

    @property
    def srcpath(self):
        '''
        :return: the source directory. This is a directory called 'sphinx' which must exist
        in the current package path, next to the module implementing this class'''
        return os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "sphinx")

    def __call__(self, *args, **kwargs):
        '''
        Calls this object as function with the specified arguments. You need to override

        .. code-block: python

            self.getdestpath
            self.getdatafiles
            self.getrstkwargs

        to make this function work.

        On success `self.destpath` will be an existing directory. On failure, `self.destpath`
        will be removed if it was created inside this function

        :return: 0 on success, or raises to indicate failure
        '''
        src_path = self.srcpath
        destpath = self.getdestpath(self._out_path, *args, **kwargs)
        destdatapath = os.path.join(destpath, 'data')
        destpath_existed = os.path.isdir(destpath)
        raised = False  # used if we got exceptions and the dir did not exist (so clean it up)
        logger = Logger()
        sys.stdout = logger
        update_config_only = self._update_config_only
        try:
            confirm = self._confirm
            setupdir(src_path, destpath, confirm, update_config_only)
            if not update_config_only:
                print("%s data files" % ("Moving" if self._mv_data_files else "Copying"))
                makedirs(destdatapath)
                datafiles = self.getdatafiles(destpath, destdatapath, *args, **kwargs) or []
                for dest, files in datafiles.iteritems():
                    makedirs(dest)
                    if not hasattr(files, "__iter__") or isinstance(files, (bytes, str)):
                        files = [files]
                    for src in files:
                        copyfiles(src, dest, self._mv_data_files)
                print("Creating '%s' in '%s'" % (self.masterdoc, destpath))
                self.render_rst(destpath, self.getrstkwargs(destpath, destdatapath, datafiles,
                                *args, **kwargs) or {})
            print("Done")
            return 0
        except:
            raised = True  # for finally (see below)
            raise
        finally:
            if not update_config_only:
                destpath_exists = os.path.isdir(destpath)
                if raised and not destpath_existed and destpath_exists:
                    shutil.rmtree(destpath, ignore_errors=True)
                logfile = os.path.join(destpath, get_logfilename()) \
                    if not raised and destpath_exists else None
                logger.close(logfile)
                if logfile and os.path.isfile(logfile):
                    print("\nOutput written to '%s'" % logfile)

    def getdestpath(self, out_path, *args, **kwargs):
        '''
            This method must return the *real* destination directory of this object.
            In the most simple scenario, it can also just return `out_path`

            :param out_path: initial output path (passed in the `__init__` call)
            :param args, kwargs: the arguments passed to this object when called as function and
            forwarded to this method
            '''
        raise NotImplemented(('`getdestpath` not implemented in %s: '
                              'you must return a valid path (usually self.out_path or '
                              'a sub-directory of it according to the method arguments)') %
                             self.__class__.__name__)

    def getdatafiles(self, destpath, destdatapath, *args, **kwargs):
        '''
            This method must return the data files to be copied into `destdatapath`. It must
            return a dict of

            `{destdir: files, ...}`

            where:

            * `destdir` is a string, usually `destdatapath` or a sub-directory of it,
               denoting the destination directory where to copy the files

            * `files`: a list of files to be copied in the corresponding `destdir`. It can
              be a list of strings denoting each a single file, a directory or a glob pattern.
              If string, it will be converted to the 1-element list `[files]`

            Use `collections.OrderedDict` to preserve the order of the keys

            For each item `destdir, files`, and for each `filepath` in `files`, the function
            will call:

            :ref:`gfzreport.templates.utils.copyfiles(filepath, destdir, self._mv_data_files)`

            Thus `filepath` can be a file (copy/move that file into `destdir`) a directory
            (copy/move each file into `destdir`) or a glob expression (copy/move each matching
            file into `destdir`)

            :param destpath: the destination directory, as returned from `self.getdestpath`
            :param destdatapath: the destination directory for the data files, currently
            the subdirectory 'data' of `destpath` (do not rely on it as it might change in the
            future)
            :param args, kwargs: the arguments passed to this object when called as function and
            forwarded to this method

            :return: a dict of destination paths (ususally sub-directories of `self.destdatapath`
            mapped to lists of strings (files/ directories/ glob patterns). An empty dict or
            None (or pass) are valid (don't copy anything into `destdatadir`)

            This function can safely raise as Exceptions will be caught and displayed in their
            message displayed printed
        '''

        raise NotImplemented(('`getdatafiles` not implemented in %s: '
                              'you should return two lists: the first a list of destination '
                              'directories subdirs of `self.destdatadir`, and the second a list of '
                              'files, directories or glob patterns denoting the files to be '
                              'copied or moved in the '
                              'corresponding destination directory') %
                             self.__class__.__name__)

    def getrstkwargs(self, destpath, destdatapath, datafiles, *args, **kwargs):
        '''
            This method accepts all arguments passed to this object when called as function and
            should return a dict of keyword arguments used to render the rst
            template, if the latter has been implemented as a jinja template.

            You can return an empty dict or None (or pass) if the rst in the current source folder
            is "fixed" and not variable according to the arguments. Note that at this
            point you can access `self.destpath`, `self.destdatapath` and `self.datafiles`

            :param destpath: the destination directory, as returned from `self.getdestpath`
            :param destdatapath: the destination directory for the data files, currently
            the subdirectory 'data' of `destpath` (do not rely on it as it might change in the
            future)
            :param datafiles: a dict as returned from self.getdatafiles`, where each key
            represents a data destination directory and each value is a list of files that have
            been copied or moved inthere. The keys of the dict are surely existing folders and are
            usually sub-directories of `destdatapath` (or equal to `destdatapath`)
            :param args, kwargs: the arguments passed to this object when called as function and
            forwarded to this method

            :return: a dict of key-> values to be used for rendering the rst if the latter is a
            jinja template.

            This function can safely raise as Exceptions will be caught and displayed in their
            message displayed printed
        '''
        raise NotImplemented(('`getrstkwargs` not implemented in %s: '
                              'you should return the arguments as dict for rendering the rst.'
                              'You can also pass if there is nothing rst is not a jinja template') %
                             self.__class__.__name__)

    def render_rst(self, destpath, *args, **kwargs):
        rst_filename = self.masterdoc + ".rst"
        template = Environment(loader=FileSystemLoader(self.srcpath)).get_template(rst_filename)
        rst_dest_file = os.path.join(destpath, rst_filename)
        # template = Environment(loader=BaseLoader()).from_string(self.content)
        template.stream(*args, **kwargs).dump(rst_dest_file, encoding='UTF8')

    @property
    def masterdoc(self):
        return get_master_doc(os.path.join(self.srcpath, 'conf.py'))
