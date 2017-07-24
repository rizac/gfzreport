#!/usr/bin/env ptatioython
# -*- coding: utf-8 -*-
'''
Created on May 18, 2016
@author: riccardo
'''

# from __future__ import print_function

import os
import sys
# import shutil
# import datetime
# import inspect
import click
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader

from gfzreport.templates.network.core.utils import relpath
from gfzreport.templates.network.core import get_noise_pdfs_content, gen_title,\
    get_net_desc, geofonstations_df, otherstations_df, get_map_df, get_figdirective_vars
from gfzreport.sphinxbuild.map import parse_margins
from gfzreport.sphinxbuild.core.extensions import mapfigure
from gfzreport.templates.utils import cp_template_tree, makedirs, copyfiles, validate_outdir


def _validate_margins(ctx, param, value):
    """Does a check on the outdir: when it's None, it returns the dir specified in
    ```reportgen.network.www.config.SOURCE_PATH```
    """
    try:
        return parse_margins(value)
    except:
        raise click.BadParameter("invalid value for '%s': '%s'"
                                 % (param.human_readable_name, str(value)))


@click.command()
@click.argument('network')
@click.argument('start_after')  # , type=int)
@click.option('-a', '--area_margins', default=None,  callback=_validate_margins,
              help=("The search margins (in degrees) relative to the bounding box calculated "
                    "from the network station locations. The new square area (bbox + margins) "
                    "will be used to search for non-network stations to be displayed on the "
                    "map and will set the map image margins (later editable in the "
                    ".rst file). "
                    "Specify 1 to 4 values separated by commas (no spaces allowed) denoting "
                    "top,left,bottom,right (4 values), "
                    "top,left_and_right, bottom (3 values), "
                    "top_and_bottom, left_and_right (2 values), "
                    "or a single value that will be applied to all directions. "
                    "Negative values will shrink the box, positive will "
                    "expand it"))
@click.option('-o', '--out_path', default=None, callback=validate_outdir,
              help=("The output path. The destination directory "
                    "will be a directory in this path with name [NETWORK]_[STATION]. "
                    "The destination directory must *not* exist, or the program will exit. "
                    "If this program is deployed on a web server, this is the DATA_DIR "
                    "environment variable provided for the network report (if deployed on "
                    "Apache, see relative .wsgi file)"))
@click.option('-n', '--noise_pdf', default=None, multiple=True,
              help=("The path (directory, file) of the "
                    "Noise Probability Density function images. "
                    "The images will be displayed on a grid. The grid is built by determining "
                    "each file position (row and column) from its name. File "
                    "names must thus start with the format 'station_channel': "
                    "the station (determining the row placement) can be any sequence of characters "
                    "(even underscores) and the channel (column) can be either HHZ, HHN or HHE. "
                    "Columns by default are HHZ HHN HHE (displayed in this order in the grid). "
                    "Example: AM01_HHZ.png and "
                    "AM01_2_HHZ.png: different rows but same column. AM03_HHN.png and "
                    "AM03_HHE.png: same row on different columns. "
                    "Note that everything following the channel will "
                    "not be parsed, so you should NOT have files like "
                    "AM01_HHZ.jpg, AM01_HHZ.whatever.jpg, AM01_HHZ_HHE.jpg as they will be "
                    "considered the same image (which file will be taken, it "
                    "depends on the inverse order the files are returned from the OS). "
                    "The rows of the resulting image grid will be sorted alphabetically according "
                    "to the station name"))
@click.option('-i', '--inst_uptimes', default=None, multiple=True,
              help=('The path (directory, file) '
                    'of the instrument uptimes image(s). If multiple files '
                    'are provided, the images will be displayed in a grid of one column '
                    'sorted alphabetically by name'))
@click.option("--mv", is_flag=True, default=False,
              help=("Move all specified files instead of copying"
                    "them (default False, i.e. missing)"))
@click.option("--noprompt", is_flag=True, default=False, is_eager=True,  # <- exec it first. Used?
              help=("Do not ask before proceeding if the user wants to write to out_path. "
                    "The default, when this flag is missing, is False"
                    "(always ask before writing)"))
@click.option('-m', '--network_station_marker', default="^", type=str,
              help=('The marker used to display network stations on the map. Defaults to ^ '
                    '(Triangle)'))
@click.option('-M', '--nonnetwork_station_marker', default="^", type=str,
              help=('The marker used to display non-network stations (within the network bbox) on '
                    'the map. Defaults to ^ (Triangle)'))
@click.option('-c', '--network_station_color', default="#ffef10", type=str,
              help=('The color used to display network stations on the map. Defaults to "#ffef10" '
                    '(yellow-like color)'))
@click.option('-C', '--nonnetwork_station_color', default="#dddddd", type=str,
              help=('The color used to display  non-network stations (within the network bbox) on '
                    'the map. Defaults to "#dddddd" (gray-like color)'))
def main(network, start_after, area_margins, out_path, noise_pdf, inst_uptimes, mv, noprompt,
         network_station_marker, nonnetwork_station_marker, network_station_color,
         nonnetwork_station_color):
    """
    Generates the report folder for the given network and year

    NETWORK: the network name, e.g.: ZE.\n
    START_AFTER: the start year, e.g.: 2012.\n

    -----------------------------------------

    The directory tree that will be created will look like the following:

    out_path

     +- config           [directory: Sphinx configuration stuff]

     +- report.rst       [generated file]

     +- data              [directory]

         +- noise_pdf     [directory]

         +- inst_uptimes  [directory]

    NOTE: Data files specified by 'noise_pdf' and 'inst_uptimes' must denote one or
    more files or directories. They can be typed ONE OR MORE TIMES, where each file path is
    a local system path (with or without wildcards). They will be copied recursively in the
    relative output directory under 'data' (see above)

    Example:

    [program_name] --noise_pdf /home/my_images/myfile.png --noise_pdf /home/other_images/*.jpg
    """
    # remember: the doc above is shown when calling --help. Arguments DO NOT ACCEPT HELP, THUS
    # IT MUST BE WRITTEN THERE!!

    # FIXME: IMPORTANT: unix shell expands wildcards automatically, so we might avoid the glob
    # module. Fine, BUT CLICK DOES NOT SUPPORT MULTIPLE (UNDEFINED) OPTIONS
    # So for the moment we DISABLE that option
    #
    # Moreover, if we ever re-implement it in the futre, remember that windows does not expand
    # wildcards
    # (http://stackoverflow.com/questions/12501761/passing-multple-files-with-asterisk-to-python-shell-in-windows)

    # Note also that area margins are in degree because we want to make life easier
    # If you want to support 'm' and 'km', be aware that we need to convert margins back to string
    # to pass these to the initial map settings (supporting only degrees makes life easier,
    # just write in the map figure rst option:
    # ", ".join(str(m) for m in area_margins)
    try:
        sys.exit(run(network, start_after, area_margins, out_path, noise_pdf, inst_uptimes,
                     mv, not noprompt, network_station_marker, nonnetwork_station_marker,
                     network_station_color, nonnetwork_station_color))
    except Exception as exc:
        print("Aborted: %s" % str(exc))
        sys.exit(1)


def run(network, start_after, area_margins_in_deg, out_path, noise_pdf, inst_uptimes,
        mv, confirm,
        network_station_marker, nonnetwork_station_marker, network_station_color,
        nonnetwork_station_color):
    in_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sphinx")
    out_path = os.path.abspath(os.path.join(out_path, "%s_%s" % (str(network), str(start_after))))
    with cp_template_tree(in_path, out_path, confirm) as _data_outdir:

        # OKAY, we copied all relevant sphinx stuff. Now we have to copy the
        # template specific files, noise_pdf and inst_uptimes:
        noise_pdf_dst = os.path.join(_data_outdir, "noise_pdf")
        inst_uptimes_dst = os.path.join(_data_outdir, "inst_uptimes")
        # copy the data files:
        # Note: create the sub-directories first, as copyfiles below creates them
        # only if there are files to copy
        for path in [inst_uptimes_dst, noise_pdf_dst]:
            makedirs(path)

        # copy data files: inst_uptimes, data_aval, noise_pdf
        # note that the first elements of each tuple are LISTS as the arguments have the
        # flag multiple=True
        for arg__ in [(inst_uptimes, inst_uptimes_dst),
                      (noise_pdf, noise_pdf_dst)]:
            dst__ = arg__[1]
            for src__ in arg__[0]:
                print("Copying file: '%s' in '%s'" % (src__, dst__))
                copyfiles(src__, dst__, mv)
                # raise Error if no files are in the folder (Sphinx complains afterwards for bad
                # formed code, e.g. csv tables with no content):
                if not os.listdir(dst__):
                    raise IOError("No files copied. Please check '%s'" % src__)

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
                    noise_pdfs={'dirpath': relpath(noise_pdf_dst, out_path),
                                'content': get_noise_pdfs_content(noise_pdf_dst)
                                },
                    inst_uptimes=get_figdirective_vars(inst_uptimes_dst, out_path)
                    )

        rstfilename = "report.rst"
        template = Environment(loader=FileSystemLoader(out_path)).get_template(rstfilename)
        reporttext = template.render(**args)

        template_dst = os.path.join(out_path, rstfilename)
        # writing back to report.rst file
        print("Writing report rst file in %s" % (template_dst))
        with open(template_dst, 'w') as opn:
            opn.write(reporttext.encode('UTF8'))

    return 0


if __name__ == '__main__':
    main()  # pylint:disable=no-value-for-parameter
