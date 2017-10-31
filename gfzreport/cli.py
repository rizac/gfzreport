#!/usr/bin/env ptatioython
# -*- coding: utf-8 -*-
'''
Created on Oct 23, 2017
@author: riccardo
'''
import click
import sys

from sphinx import build_main as sphinx_build_main
from gfzreport.sphinxbuild.map import parse_margins
from gfzreport.templates.network import run as networktemplate_run
from gfzreport.sphinxbuild import run as sphinxbuild_run
from gfzreport.sphinxbuild import _DEFAULT_BUILD_TYPE


@click.group()
def main():
    """gfzreport is a program to generate reports and report templates for the
    Helmholtz-Centre Potsdam - GFZ German Research Centre for Geosciences

    For details, type:

    \b
    gfzreport COMMAND --help

    \b
    where COMMAND is one of the commands listed below"""
    pass


def _validate_margins(ctx, param, value):
    """Does a check on the outdir: when it's None, it returns the dir specified in
    ```reportgen.network.www.config.SOURCE_PATH```
    """
    try:
        return parse_margins(value)
    except:
        raise click.BadParameter("invalid value for '%s': '%s'"
                                 % (param.human_readable_name, str(value)))


@main.command()
@click.argument('network')
@click.argument('start_after')  # , type=int)
@click.option('-a', '--area_margins', default=0.5,  callback=_validate_margins,
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
@click.option('-o', '--out_path', default=None,  # callback=validate_outdir,
              help=("The output path. The destination directory D (where files are written) "
                    "will be a sub-directory of out_path with name [network]_[start_after]. "
                    "D must *not* exist if -c is missing (the default), or the program will exit. "
                    "If -c is given, on the other hand, D must exist"))
@click.option('-n', '--noise_pdf', default=None, multiple=True,
              help=("The path (directory, file, glob pattern) of the "
                    "Noise Probability Density function images. "
                    "This option can be given multiple times. All images will be collected "
                    "from the given option(s) and displayed on a grid "
                    "(rows=stations, columns=channels). "
                    "The file names must be in the format [station]?[channel].[ext] "
                    "where ? indicates one or more non-alphanumeric characters and "
                    "[ext] is the image file extension (preferably png, or jpeg). "
                    "Example: AM01.HHZ.png , AM01__BH1.png "
                    "([channel] can be actually followed by any string starting with "
                    "a non alphanumeric character, but in case of conflicts the 'best' well "
                    "formed name will be chosen. E.g. AM01.HHZ_try2.png will work and "
                    "'_try2' will be ignored, but if a file named AM01.HHZ.png is found, "
                    "the latter will be chosen and the former discarded)"))
@click.option('-i', '--inst_uptimes', default=None, multiple=True,
              help=('The path (directory, file, glob pattern) '
                    'of the instrument uptimes image(s). If multiple files '
                    'are provided, the images will be displayed in a grid of one column '
                    'sorted alphabetically by name'))
@click.option("-m", "--mv_datafiles", is_flag=True, default=False,
              help=("Move all specified data files (-n and -i options) instead of copying"
                    "them (default False when missing)"))
@click.option("-c", "--conffiles_only", is_flag=True, default=False,
              help=("Copy only sphinx configuration files (conf dir + conf.py). "
                    "Useful for updating an already created directory after bug fixes/maintenance, "
                    "without changing rst and data files (-n and -i options). "
                    "After supplying the arguments network and start_after, if this flag is "
                    "given the only required option is -o (and the directory must exist). "
                    "Note that this option does not synchronize conf files: if any was added "
                    "or modified in the destination directory, it will be deleted"))
@click.option("--noprompt", is_flag=True, default=False, is_eager=True,  # <- exec it first. Used?
              help=("Do not ask before proceeding. "
                    "The default, when this flag is missing, is False"
                    "(always ask before writing)"))
@click.option('-nm', '--network_station_marker', default="^", type=str,
              help=('The marker used to display network stations on the map. Defaults to ^ '
                    '(Triangle)'))
@click.option('-NM', '--nonnetwork_station_marker', default="^", type=str,
              help=('The marker used to display non-network stations (within the network bbox) on '
                    'the map. Defaults to ^ (Triangle)'))
@click.option('-nc', '--network_station_color', default="#ffef10", type=str,
              help=('The color used to display network stations on the map. Defaults to "#ffef10" '
                    '(yellow-like color)'))
@click.option('-NC', '--nonnetwork_station_color', default="#dddddd", type=str,
              help=('The color used to display  non-network stations (within the network bbox) on '
                    'the map. Defaults to "#dddddd" (gray-like color)'))
def template_network(network, start_after, area_margins, out_path, noise_pdf, inst_uptimes,
                     mv_datafiles, conffiles_only, noprompt, network_station_marker,
                     nonnetwork_station_marker, network_station_color, nonnetwork_station_color):
    """
    Generates the report folder for the given network and year

    NETWORK: the network name, e.g.: ZE.\n
    START_AFTER: the start year, e.g.: 2012.\n

    -----------------------------------------

    The directory tree that will be created will look like the following:

    \b
    out_path:

    \b
        conf_files:       directory with sphinx
                          additional files (see conf.py)

    \b
        conf.py:          Sphinx configuration file

    \b
        report.rst:       ReStructuredText report. The file name
                          might change depending on the value of
                          'master_doc' in conf.py

    \b
        data:
    \b
            noise_pdf:    directory, populated with noise prob.
                          density functions

    \b
            inst_uptimes: directory, populated with a figure
                          of instrumental uptimes


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
        sys.exit(networktemplate_run(network, start_after, area_margins, out_path, noise_pdf,
                                     inst_uptimes, mv_datafiles, conffiles_only, not noprompt,
                                     network_station_marker, nonnetwork_station_marker,
                                     network_station_color, nonnetwork_station_color))
    except Exception as exc:
        print("Aborted: %s" % str(exc))
        sys.exit(1)


# as when we provide --sphinxhelp we should not check for sourcedir and outdir existence
# we cannot set the nargs=1 and required=True in @click.argument, so we implement this function
# that behaves as nargs=1+required=True
def check_dirs(ctx, param, value):
    if not value and "sphinxhelp" not in ctx.params:
        raise click.BadParameter("Missing argument", ctx=ctx, param=param)
    return value


@main.command(context_settings=dict(ignore_unknown_options=True,),
              options_metavar='[options]')
@click.argument('sourcedir', nargs=1, required=False, callback=check_dirs,
                metavar='sourcedir')  # @IgnorePep8
@click.argument('outdir', nargs=1, required=False, callback=check_dirs, metavar='outdir')
@click.option('-b', '--build',
              help=('builder to use. Default is ' + _DEFAULT_BUILD_TYPE + ' (in '
                    'sphinx-build is html). You can also type pdf: if this program is correctly '
                    'installed (with all latex libs) then `sphinx-build -b latex ...` is first '
                    'executed and then pdflatex is run on all .tex files in outdir which '
                    'did not exist before (or whose last-modified time changed during) this '
                    'program execution. This usually works fine but might compile also latex '
                    'additional files provided in conf.py, at least after the first build, as they '
                    'will be seen as new: to avoid this, put the string ".dontcompile." in the '
                    '.tex file names. Note that this program has been currently tested '
                    'only for sphinx builds generating a single .tex file in outdir'),
              default=_DEFAULT_BUILD_TYPE, type=click.Choice(['html', 'pdf', _DEFAULT_BUILD_TYPE]))
@click.argument('other_sphinxbuild_options', nargs=-1, type=click.UNPROCESSED,
                metavar='[other_sphinxbuild_options]')
@click.option('--sphinxhelp', is_flag=True, default=False, help='print out the sphinx-build help '
              'to know which options (except -b, --build) or arguments (except sourcedir, outdir) '
              'can be passed in [other_sphinxbuild_options]')
def build(sourcedir, outdir, build, other_sphinxbuild_options, sphinxhelp):
    """A wrapper around sphinx-build"""
    if sphinxhelp:
        sphinx_build_main(["", "--help"])
        return 0

    # for info see:
    # sphinx/cmdline.py, or
    # http://www.sphinx-doc.org/en/1.5.1/man/sphinx-build.html
    sys.exit(sphinxbuild_run(sourcedir, outdir, build, *list(other_sphinxbuild_options)))


if __name__ == '__main__':
    main()  # pylint:disable=no-value-for-parameter

