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


def run(network, start_after, area_margins_in_deg, out_path, noise_pdf, inst_uptimes,
        move_data_files, update_config_only, confirm,
        network_station_marker, nonnetwork_station_marker, network_station_color,
        nonnetwork_station_color):
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sphinx")
    dest_path = os.path.abspath(os.path.join(out_path, "%s_%s" % (str(network), str(start_after))))

    with utils.cleanup_onerr(dest_path):
        dest_data_path = utils.setupdir(src_path, dest_path, confirm, update_config_only)
        if update_config_only:
            return 0

        # from here on, implement the custom template dir creation for a new report:
        noise_pdf_dst = utils.makedirs(os.path.join(dest_data_path, "noise_pdf"))
        inst_uptimes_dst = utils.makedirs(os.path.join(dest_data_path, "inst_uptimes"))

        datafilescopied = 0
        for src in inst_uptimes:
            datafilescopied = utils.copyfiles(src, inst_uptimes_dst, move_data_files)
        if not datafilescopied:
            raise IOError(("No data file found to copy in '%s'") % inst_uptimes_dst)
        print("%s %d data files to '%s'" % ('Moved' if move_data_files else 'Copied',
                                            datafilescopied, inst_uptimes_dst))

        datafilescopied = 0
        for src in noise_pdf:
            datafilescopied = utils.copyfiles(src, noise_pdf_dst, move_data_files)
        if not datafilescopied:
            raise IOError(("No data file found to copy in '%s'") % noise_pdf_dst)
        print("%s %d data files to '%s'" % ('Moved' if move_data_files else 'Copied',
                                            datafilescopied, noise_pdf_dst))

        print("Rendering report template with jinja2")
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
        # when possible, we put everything in the rst.
        args = dict(
                    title=gen_title(network, geofon_df),
                    network_description=get_net_desc(geofon_df),
                    stations_table={'content': geofon_df.to_csv(sep=" ", quotechar='"',
                                                                index=False),
                                    },
                    stations_map={'content': map_df.to_csv(sep=" ", quotechar='"', index=False),
                                  'options': mapfigure.get_defargs(**mymapdefaults)
                                  },
                    noise_pdfs={'dirpath': relpath(noise_pdf_dst, dest_path),
                                'content': get_noise_pdfs_content(noise_pdf_dst)
                                },
                    inst_uptimes=get_figdirective_vars(inst_uptimes_dst, dest_path)
                    )

        with utils.get_rst_template(src_path, dest_path) as template:
            template.render(**args)
        
        return 0



# if __name__ == '__main__':
#     main()  # pylint:disable=no-value-for-parameter
