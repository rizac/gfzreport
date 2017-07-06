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


def makedirs(path):
    """Same as os.makedirs except that it silently exits if the path already exists
    Raises OSError in case the directory cannot be created"""
    if not os.path.isdir(path):
        os.makedirs(path)
        if not os.path.isdir(path):
            raise OSError(errno.ENOTDIR, "makedirs failed: " + os.strerror(errno.ENOTDIR), path)


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
        for fle in os.listdir(src):
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
        glb_list = glob(src)
        if len(glb_list) and glb_list[0] != src:
            # in principle, if src denotes a non-existing file or dir, glb_list is empty, if it
            # denotes an existing file or dir, it has a single element equal to src. This latter
            # case is a problem as we might have an error when copying a dir
            # In principle copy2 below raises the exception but for safety we repeat
            # the test here
            for srcf in glob(src):  # glob returns joined pathname, it's not os.listdir!
                files_count += copyfiles(srcf, dst_dir, move)

    return files_count


@contextmanager
def cp_template_tree(in_path, out_path, confirm):
    """Copies recursively `in_path` into `out_path`, creates `out_path`/data and yields the latter
    to be populated with custom data by a caller. `out_path` needs **NOT** to exist
    Usually, in_path is the sphinx subfolder of a
    package with all sphinx config files and at least one rst file

    This function can be used in a with statement from within a caller:
    ```
    with cp_template_tree(indir, out_path, confirm=True) as data_dir:

        ... copy data files in data_dir ...

    return 0
    ```
    This function can raise (OsError, IOError, ValueError). If it raises, and
    `out_path` was newly created inside this function, it deletes `out_path` before raising
    """
    # NOTE: we will delete out_path if this function raises and created it meanwhile
    # so first of all keep track if out_path exists (should return always False)
    out_path_exists = os.path.isdir(out_path)
    cleanup = False  # used if we got exceptions and the dir did not exist (so clean it up)
    try:
        if not os.path.isdir(in_path):
            raise ValueError("sourcedir '%s': not a directory" % in_path)

        if out_path_exists:
            # Putting content in an already existing non-empty directory is
            # unmaintainable as we might have conflicts when building the report:
            # Note that we still need `out_path_exists` above because we MUST NOT
            # delete out_path in the finally below!
            raise ValueError(("'%s' already exists.\nPlease provide a non-existing directory "
                              "path or supply the '--update' argument to copy data files only "
                              "(no sphinx config and rst files)") % out_path)

        if confirm:
            strmsg = """Sphinx files %s will be written to:
%s%s
Continue?
""" % (out_path, "\nThe directory path will be created (mkdir -p)" if not out_path_exists else "")
            if not click.confirm(strmsg):
                raise ValueError("Aborted by user")

        # then copy conf dir, as copytree calls mkdirs(config_dst) and requires the dst not to
        # exist (so for any other operation on config_dst, this must be the first operation)
        print("Copying recursively content of '%s' in '%s' " % (in_path, out_path))
        # copy the CONTENT of config_src into config_dst
        shutil.copytree(in_path, out_path)

        # if path didn't exist, and doesn't, something went wrong:
        if not out_path_exists and not os.path.isdir(out_path):
            raise ValueError("Unable to create '%s'" % out_path)

        # copy data dir if it does not exist, so the caller can write therein:
        _data_outdir = os.path.join(out_path, "data")
        makedirs(_data_outdir)
        print("Generated empty folder '%s'" % _data_outdir)

        # write info from the caller:
#         print("Writing caller info to README.txt")
#         with open(os.path.join(out_path, 'README.txt'), 'w') as opn:
#             opn.write(u'Source folder generated automatically on %s\n' %
#                       (datetime.datetime.utcnow()))
#             opn.write(u'in current stack (from inner to outer caller):\n')
#             for stack in inspect.stack()[1:]:
#                 filename, funcname, localz = str(stack[1]), str(stack[3]), stack[0].f_locals
#                 opn.write(u"%s:%s" % (filename, funcname))
#                 opn.write(u'   with %d local variables:\n' % len(localz))
#                 for key, val in localz.items():
#                     opn.write(u'   %s = %s\n' % (str(key), str(val)))

        yield _data_outdir  # execute wrapped code

    except:
        cleanup = not out_path_exists and os.path.isdir(out_path)  # for finally (see below)
        raise
    finally:
        if cleanup:
            shutil.rmtree(out_path, ignore_errors=True)


# if __name__ == '__main__':
#     main()  # pylint:disable=no-value-for-parameter
