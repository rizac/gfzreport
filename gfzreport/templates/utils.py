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
import datetime
import inspect
from glob import glob
from contextlib import contextmanager
import errno
import click
from jinja2 import Environment, BaseLoader
from gfzreport.sphinxbuild.__init__ import get_master_doc
from jinja2.loaders import FileSystemLoader


# def validate_outdir(ctx, param, value):
#     """Function to be passed as callback arguments for click options denoting an output directory.
#     Creates outdir if it does not exist. If its parent does not exist, raises, as this
#     might most likely due to typos
#     """
#     if not os.path.isdir(value):
#         if not os.path.isdir(os.path.dirname(value)):
#             raise click.BadParameter('"%s" parent dir does not exist' % value)
#         try:
#             os.mkdir(value)
#             if not os.path.isdir(value):
#                 raise Exception()
#         except Exception:
#             raise click.BadParameter('Unable to mkdir "%s"' % value)
#     return value


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


@contextmanager
def cleanup_onerr(dest_path):
    """Context manager which removes `dest_path` if it did not exist prior to this call and
    an exception is raised in its with statement
    """
    # NOTE: we will delete dest_path if this function raises and created it meanwhile
    # so first of all keep track if dest_path exists (should return always False)
    out_path_exists = os.path.isdir(dest_path)
    cleanup = False  # used if we got exceptions and the dir did not exist (so clean it up)
    try:
        yield
    except:
        cleanup = not out_path_exists and os.path.isdir(dest_path)  # for finally (see below)
        raise
#    else:
#        print("Done")
    finally:
        if cleanup:
            shutil.rmtree(dest_path, ignore_errors=True)


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

    datadir = os.path.join(dest_path, "data")
    if not update_config_only:
        makedirs(datadir)
    return datadir


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



# @contextmanager
# def cp_template_tree(src_path, dest_path, confirm, update_config_only):
#     """Copies recursively `src_path` into `dest_path`, creates `dest_path`/data and yields the latter
#     to be populated with custom data by a caller. `dest_path` needs **NOT** to exist
#     Usually, src_path is the sphinx subfolder of a
#     package with all sphinx config files and at least one rst file
# 
#     This function can be used in a with statement from within a caller:
#     ```
#     with cp_template_tree(indir, dest_path, confirm=True) as data_dir:
# 
#         ... copy data files in data_dir ...
# 
#     return 0
#     ```
#     This function can raise (OsError, IOError, ValueError). If it raises, and
#     `dest_path` was newly created inside this function, it deletes `dest_path` before raising
#     """
#     # NOTE: we will delete dest_path if this function raises and created it meanwhile
#     # so first of all keep track if dest_path exists (should return always False)
#     out_path_exists = os.path.isdir(dest_path)
#     cleanup = False  # used if we got exceptions and the dir did not exist (so clean it up)
#     try:
#         if not os.path.isdir(src_path):
#             raise ValueError("sourcedir '%s': not a directory" % src_path)
# 
#         if out_path_exists and not update_config_only:
#             # Putting content in an already existing non-empty directory is
#             # unmaintainable. The user can only overwrite config files
#             raise ValueError(("'%s' already exists.\n"
#                               "Please provide a non-existing directory name") % dest_path)
#         elif not out_path_exists and update_config_only:
#             raise ValueError(("'%s' does not exist.\n"
#                               "Please provide an existing directory name in "
#                               "'update config only' mode") % dest_path)
# 
#         if confirm:
#             strmsg = """Report's config files will be written to:
# %s%s
# Continue?
# """ % (dest_path, "\nThe directory path will be created (mkdir -p)" if not out_path_exists else "")
#             if not click.confirm(strmsg):
#                 raise ValueError("Aborted by user")
# 
#         if not update_config_only:
#             # then copy conf dir, as copytree calls mkdirs(config_dst) and requires the dst not to
#             # exist (so for any other operation on config_dst, this must be the first operation)
#             print("Copying recursively content of '%s' in '%s' " % (src_path, dest_path))
#             # copy the CONTENT of config_src into config_dst
#             shutil.copytree(src_path, dest_path)
#         else:
#             confdirname = 'conf_files'
#             outconfdir = os.path.join(dest_path, confdirname)
#             if os.path.isdir(outconfdir):
#                 shutil.rmtree(outconfdir, ignore_errors=False)
#             shutil.copytree(os.path.join(src_path, confdirname), outconfdir)
#             shutil.copy2(os.path.join(src_path, 'conf.py'), dest_path)
# 
#         # if path didn't exist, and it doesn't now, something went wrong:
#         if not out_path_exists and not os.path.isdir(dest_path):
#             raise ValueError("Unable to create '%s'" % dest_path)
# 
#         _data_outdir = os.path.join(dest_path, "data")
#         if not update_config_only:
#             # copy data dir if it does not exist, so the caller can write therein:
#             makedirs(_data_outdir)
#             print("Generated empty folder '%s'" % _data_outdir)
# 
#         yield _data_outdir  # execute wrapped code
# 
#     except:
#         cleanup = not out_path_exists and os.path.isdir(dest_path)  # for finally (see below)
#         raise
#     else:
#         print("Done")
#     finally:
#         if cleanup:
#             shutil.rmtree(dest_path, ignore_errors=True)



# if __name__ == '__main__':
#     main()  # pylint:disable=no-value-for-parameter
