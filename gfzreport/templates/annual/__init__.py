#!/usr/bin/env ptatioython
# -*- coding: utf-8 -*-
'''
Created on May 18, 2016
@author: riccardo
'''

from __future__ import print_function

import os
import sys  # @UnusedImport

from collections import OrderedDict

from gfzreport.templates.network.core.utils import relpath
from gfzreport.templates.network.core import get_noise_pdfs_content, gen_title,\
    get_net_desc, geofonstations_df, otherstations_df, get_map_df, get_figdirective_vars
from gfzreport.sphinxbuild.core.extensions import mapfigure
# from gfzreport.templates.utils import makedirs, copyfiles, validate_outdir,\
#     cleanup_onerr, setupdir, get_rst_template

from gfzreport.templates import utils
from gfzreport.templates.annual.core.utils import get_img_filepaths, get_pdfs_files,\
    get_pdfs_csvstr



def run(year, input_dir, out_path, move_data_files, update_config_only, confirm):
    templater = Templater(out_path, update_config_only, move_data_files, confirm)
    return templater(year, input_dir)


class Templater(utils.Templater):

    def getdestpath(self, out_path, year, input_dir):
        '''This method must return the *real* destination directory of this object.
        In the most simple scenario, it can also just return `out_path`

        :param out_path: initial output path (passed in the `__init__` call)
        :param args, kwargs: the arguments passed to this object when called as function and
            forwarded to this method
        '''
        return os.path.abspath(os.path.join(out_path, "%s" % str(year)))

    def getdatafiles(self, destpath, destdatapath, year, input_dir):
        '''This method must return the data files to be copied into `destdatapath`. It must
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
        img_files = get_img_filepaths(input_dir)

        dirs = [d for d in os.listdir(input_dir) if os.path.isdir(d)]
        if len(dirs) != 1:
            raise Exception('Expecting 1 PDFs directory in "%s", found %d' % (input_dir, len(dirs)))

        pdfs = get_pdfs_files(input_dir)
        return {destdatapath: img_files, os.path.join(destdatapath, 'PDF'): pdfs}

    def getrstkwargs(self, destpath, destdatapath, datafiles, year, input_dir):
        '''This method accepts all arguments passed to this object when called as function and
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
        noise_pdf_dest = os.path.join(destdatapath, 'PDF')
        pdf_dir = relpath(noise_pdf_dest, destpath)
        imgs_dest = destdatapath
        imgs_dir = relpath(imgs_dest, destpath)

        return dict(year=str(year), pdf_dir=pdf_dir, imgs_dir=imgs_dir,
                    pdfs=get_pdfs_csvstr(datafiles[noise_pdf_dest]), images_dir=destdatapath,
                    imas=[os.path.basename(_) for _ in datafiles[destdatapath]]
                    )
