#!/usr/bin/env ptatioython
# -*- coding: utf-8 -*-
'''
Created on May 18, 2016
@author: riccardo
'''

from __future__ import print_function

import os
import sys  # @UnusedImport

from gfzreport.templates.network.core.utils import relpath
from gfzreport.templates.network.core import get_noise_pdfs_content, gen_title,\
    get_net_desc, geofonstations_df, otherstations_df, get_map_df, get_figdirective_vars
from gfzreport.sphinxbuild.core.extensions import mapfigure
# from gfzreport.templates.utils import makedirs, copyfiles, validate_outdir,\
#     cleanup_onerr, setupdir, get_rst_template

from gfzreport.templates import utils
from collections import OrderedDict


def run(network, start_after, area_margins_in_deg, out_path, noise_pdf, inst_uptimes,
        move_data_files, update_config_only, confirm,
        network_station_marker, nonnetwork_station_marker, network_station_color,
        nonnetwork_station_color):
    templater = Templater(out_path, update_config_only, move_data_files, confirm)
    return templater(network, start_after, area_margins_in_deg, noise_pdf, inst_uptimes,
                     network_station_marker, nonnetwork_station_marker, network_station_color,
                     nonnetwork_station_color)


class Templater(utils.Templater):

    def getdestpath(self, out_path, network, start_after, area_margins_in_deg, noise_pdf, inst_uptimes,
                    network_station_marker, nonnetwork_station_marker, network_station_color,
                    nonnetwork_station_color):
        '''This method must return the *real* destination directory of this object.
        In the most simple scenario, it can also just return `out_path`

        :param out_path: initial output path (passed in the `__init__` call)
        :param args, kwargs: the arguments passed to this object when called as function and
            forwarded to this method
        '''
        return os.path.abspath(os.path.join(out_path,
                                            "%s_%s" % (str(network), str(start_after))))

    def getdatafiles(self, destpath, destdatapath, network, start_after, area_margins_in_deg,
                     noise_pdf, inst_uptimes,
                     network_station_marker, nonnetwork_station_marker, network_station_color,
                     nonnetwork_station_color):
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
        noise_pdf_destdir = os.path.join(destdatapath, "noise_pdf")
        inst_uptimes_destdir = os.path.join(destdatapath, "inst_uptimes")
        return OrderedDict([[inst_uptimes_destdir, inst_uptimes],  [noise_pdf_destdir, noise_pdf]])

    def getrstkwargs(self, destpath, destdatapath, datafiles, network, start_after,
                     area_margins_in_deg, noise_pdf, inst_uptimes,
                     network_station_marker, nonnetwork_station_marker, network_station_color,
                     nonnetwork_station_color):
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
        # get the destination data paths. Use getdatafiles implemented for
        # moving data files, and check that they are not empty
        # the two paths will also be used later
        inst_uptimes_dst, noise_pdf_dst = datafiles.keys()
        assert len(os.listdir(inst_uptimes_dst)), "'%s' empty" % inst_uptimes_dst
        assert len(os.listdir(noise_pdf_dst)), "'%s' empty" % noise_pdf_dst

        try:
            geofon_df = geofonstations_df(network, start_after)
        except Exception as exc:
            raise Exception(("error while fetching network stations ('%s')\n"
                             "check arguments and internet connection") % str(exc))

        try:
            others_df = otherstations_df(geofon_df, area_margins_in_deg)
        except Exception as exc:
            raise Exception(("error while fetching other stations within network "
                             "stations boundaries ('%s')\n"
                             "check arguments and internet connection") % str(exc))
        map_df = get_map_df(geofon_df, others_df)

        # convert area margins into plotmap map_margins arg:
        mymapdefaults = dict(mapmargins=", ".join("%sdeg" % str(m)
                                                  for m in area_margins_in_deg),
                             sizes=50, fontsize=8, figmargins="1,2,9,0", legend_ncol=2)
        # building template, see template.rst:
        return dict(
                    title=gen_title(network, geofon_df),
                    network_description=get_net_desc(geofon_df),
                    stations_table={'content': geofon_df.to_csv(sep=" ", quotechar='"',
                                                                na_rep=" ",  # this makes to_csv
                                                                # quoting it (otherwise it might
                                                                # result in row misalign)
                                                                index=False),
                                    },
                    stations_map={'content': map_df.to_csv(sep=" ", quotechar='"', index=False),
                                  'options': mapfigure.get_defargs(**mymapdefaults)
                                  },
                    noise_pdfs={'dirpath': relpath(noise_pdf_dst, destpath),
                                'content': get_noise_pdfs_content(noise_pdf_dst, geofon_df)
                                },
                    inst_uptimes=get_figdirective_vars(inst_uptimes_dst, destpath)
                    )
# if __name__ == '__main__':
#     main()  # pylint:disable=no-value-for-parameter
