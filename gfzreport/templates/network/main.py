#!/usr/bin/env ptatioython
# -*- coding: utf-8 -*-
'''
Created on May 18, 2016
@author: riccardo
'''

# from __future__ import print_function

import click
import os
import sys
import shutil
from jinja2 import Environment
from gfzreport.templates.network.core.utils import makedirs, copyfiles, relpath
from gfzreport.templates.network.core import get_noise_pdfs_content, gen_title,\
    get_net_desc, get_network_stations_df, get_other_stations_df, get_map_df, get_figdirective_vars
from gfzreport.sphinxbuild.map import parse_margins
from gfzreport.sphinxbuild.core.extensions import mapfigure
import datetime
import inspect


def click_path_type(isdir=False):
    return click.Path(exists=True, file_okay=not isdir, dir_okay=isdir, writable=False,
                      readable=True, resolve_path=True)


def click_get_outdir(ctx, param, value):
    """Does a check on the outdir: when it's None, it returns the dir specified in
    ```reportgen.network.www.config.SOURCE_PATH```
    """
    use_default_dir = value is None
    if use_default_dir:
        network = ctx.params.get('network', None)
        if network is None:
            raise click.BadParameter("optional '%s' missing, but no network specified"
                                     % param.human_readable_name)
        from gfzreport.web import config
        value = os.path.join(config.NETWORK.DATA_PATH, 'source')  # FIXME: better handling?!!

    return value


def click_get_margins(ctx, param, value):
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
@click.option('-a', '--area_margins', default=None,  callback=click_get_margins,
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
@click.option('-o', '--out_path', default=None, callback=click_get_outdir,
              help=("The output directory. If missing, it defaults to the directory specified in "
                    "the web config file (config.py) PLUS the network and the start_after "
                    "arguments. In this case the report can be edited in the web application. "
                    "The destination directory "
                    "must *not* exist, or the program will exit (unless --update is "
                    "explicitly specified, in that case only data is copied. See --update "
                    "option)"))
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
@click.option('-u', '--update', is_flag=True, default=False, is_eager=True,  # <- exec it first. Used?
              help=("Flag denoting if the output directory out_path has to be updated. If false,"
                    "(the default) then out_path must not exist, and data + config files (template "
                    ".rst + sphinx config dir) will be copied. If True, "
                    "only data files (see NOTE above) will be copied in the specific directories "
                    "(see above). This option is useful if we need to update or add some images "
                    "but we already "
                    "edited our .rst file (so we do not want to overwrite the latter): "
                    "However, it is then up to the user to modify the rst file to include newly "
                    "added files, if any"))
@click.option("--mv", is_flag=True, default=False,
              help=("Move all specified files instead of copying"
                    "them (default False, i.e. missing)"))
@click.option("--no_prompt", is_flag=True, default=False, is_eager=True,  # <- exec it first. Used?
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
def main(network, start_after, area_margins, out_path, noise_pdf, inst_uptimes, update, mv, no_prompt,
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
    sys.exit(run(network, start_after, area_margins, out_path, noise_pdf, inst_uptimes, update, mv,
                 no_prompt, network_station_marker, nonnetwork_station_marker,
                 network_station_color, nonnetwork_station_color))


def run(network, start_after, area_margins_in_deg, out_path, noise_pdf, inst_uptimes, update,
        mv, no_prompt,
        network_station_marker, nonnetwork_station_marker, network_station_color,
        nonnetwork_station_color):
    localz = dict(locals())  # copy values NOW cause locals() will change size!
    # first build the path. out_path is not None (see click_get_outdir function)
    out_path = os.path.abspath(os.path.join(out_path, "%s_%s" % (str(network), str(start_after))))
    out_path_exists = os.path.isdir(out_path)
    cleanup = False  # used if we got exceptions and the dir did not exist (so clean it up)
    try:

        if out_path_exists and not update:
            # Putting content in an already existing non-empty directory is
            # unmaintainable as we might have conflicts when building the report:
            raise ValueError(("'%s' already exists.\nPlease provide a non-existing directory path "
                              "or supply the '--update' argument to copy data files only "
                              "(no sphinx config and rst files)") % out_path)

        if not no_prompt:  # FIXME: click has a prompt function but how to deal with the case update
            # or not? (see http://click.pocoo.org/5/options/#prompting)
            print("Data %s will be written to:" %
                  ("only (no config files) " if update else "and config files "))
            print("%s" % out_path)
            if not out_path_exists:
                print("The directory path will be created (mkdir -p)")
            print("Continue? (y for yes, anything else for abort)")
            l = sys.stdin.readline()
            if l.strip() != 'y':
                raise ValueError("aborted by user")

        # Ok. No need to call makedirs(out_path), because either
        # 1) update is False: then out_path does not exist (see above). We will create the dir
        # when copying the config file, or
        # 2) update is True: then we will make out_path when copying the data files (we will skip
        # config dir and rst files, not copied)

        # defining paths:
        _this_dir = os.path.dirname(__file__)
        template_src = os.path.abspath(os.path.join(_this_dir, "template.rst"))
        config_src = os.path.abspath(os.path.join(_this_dir, "sphinx"))

        _data_outdir = os.path.join(out_path, "data")
        noise_pdf_dst = os.path.join(_data_outdir, "noise_pdf")
        # noise_pdf is an object with dirname prop
        inst_uptimes_dst = os.path.join(_data_outdir, "inst_uptimes")
        template_dst = os.path.join(out_path, "report.rst")
        config_dst = out_path  # os.path.abspath(os.path.join(os.path.join(out_path, "config")))

        create_rst_and_config = not update
        if create_rst_and_config:
            # some check to avoid copying files if useless:
            if not os.path.isfile(template_src):
                raise IOError("No template.rst found at %s" % template_src)

            # then copy conf dir, as copytree calls mkdirs(config_dst) and requires the dst not to
            # exist (so if we config_dst == out_path, this must be the first operation)
            print("Copying config dir: %s in %s " % (config_src, config_dst))
            shutil.copytree(config_src, config_dst)

        # copy the images files:
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
                # raise Error if no files are in the folder. Sphinx complains afterwards for bad
                # formed code (e.g. csv tables with no content). If update, skip the check cause we
                # cannot determine if we actually want to copy files or not
                if not os.listdir(dst__):
                    raise IOError("No files copied. Please check '%s'" % src__)

        if create_rst_and_config:
            print("Generating report template")
            sta_df = get_network_stations_df(network, start_after)
            all_sta_df = get_other_stations_df(sta_df, area_margins_in_deg)
            map_df = get_map_df(sta_df, all_sta_df)

            # convert area margins into plotmap map_margins arg:
            mymapdefaults = dict(mapmargins=", ".join("%sdeg" % str(m)
                                                      for m in area_margins_in_deg),
                                 sizes=50, fontsize=8, figmargins="1,2,9,0", legend_ncol=2)
            # building template, see template.rst:
            # when possible, we put everything in the rst.
            args = dict(
                        title=gen_title(network, sta_df),
                        network_description=get_net_desc(sta_df),
                        stations_table={'content': sta_df.to_csv(sep=" ", quotechar='"',
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

            with open(template_src, 'r') as opn:
                txt = opn.read().decode('UTF8')
            reporttext = Environment().from_string(txt).render(**args)

            # copying the report.rst file
            print("Writing report rst file in %s" % (template_dst))
            with open(template_dst, 'w') as opn:
                opn.write(reporttext.encode('UTF8'))

            print("Writing command line arguments to README.txt")
            with open(os.path.join(out_path, 'README.txt'), 'w') as opn:
                opn.write(u'Source folder generated automatically on %s\n' %
                          (datetime.datetime.utcnow()))
                opn.write(u"from within:\n")
                opn.write(u"%s:%s\n" % (__file__, inspect.stack()[0][3]))  # current module:function
                opn.write(u'and the following arguments:\n')
                for key, val in localz.iteritems():
                    opn.write(u'%s = %s\n' % (str(key), str(val)))

        # printing info stuff:

        print("===========================================")
        print("Generated report in '%s'" % os.path.abspath(out_path))
        print("Please edit the file %s in that directory and then create your build with:"
              % os.path.basename(template_dst))
        print("    reportbuild %s OUTDIR%s -b latex -E"
              % (os.path.abspath(out_path),
                 "" if
                 os.path.samefile(config_dst, out_path) else " -c " + os.path.abspath(config_dst)))
        print("Where OUTDIR is a selected output directory and -b can be either latex, html or pdf")
        return 0
    except (IOError, OSError, ValueError) as exc:
        cleanup = not out_path_exists and os.path.isdir(out_path)
        print("Aborted: %s" % str(exc))
        return 1
    except:
        cleanup = not out_path_exists and os.path.isdir(out_path)
        raise
    finally:
        if cleanup:
            shutil.rmtree(out_path, ignore_errors=True)


if __name__ == '__main__':
    main()  # pylint:disable=no-value-for-parameter
