#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on May 18, 2016
@author: riccardo
'''
from __future__ import print_function
import click
import re
import pandas as pd
from lxml import etree
import urllib2
from StringIO import StringIO
from urllib2 import URLError
import os
import sys
import shutil
from glob import glob
import csv
from jinja2 import Environment
from lxml.etree import XMLSyntaxError


def get_format(query_str):
    """Returns the format argument of query_str (a query in string format), or 'xml' if
    such argument is not found (xml being the FDSN default)"""
    try:
        r = re.compile("[\\?\\&]format=(.*?)[\\&$]")
        return r.search(query_str).groups()[0]
    except IndexError:
        pass
    return 'xml'


def read(url):
    """Reads the specific url, returning a string if 'format=text' is within the url
    query, or a etree object otherwise"""
    try:
        format_ = get_format(url)
        if format_ == 'text':
            response = urllib2.urlopen(url)
            text = response.read()
            return text
        else:
            return etree.parse(url)
    except (URLError, ValueError, TypeError) as exc:
        raise ValueError(exc.__class__.__name__ + ": " + str(exc))


def get_query_str(network, start_after_year, format_, **kwargs):
    """Returns the query string from a given network and a given start_after argument
    and a specific format_ ("xml" or "text"). All other FDSN arguments to be appended to the query
    can be specified via kwargs
    """
    dc_str = ("http://geofon.gfz-potsdam.de/fdsnws/station/1/query?"
              "network=%s&startafter=%s&format=%s") % (network, start_after_year, format_)
    for key, val in kwargs.iteritems():
        dc_str += "&%s=%s" % (str(key), str(val))
    return dc_str


def read_network(network, start_after_year, format_, **kwargs):
    """
        Retutrns all stations froma  given network.
        :param kwargs: keyword arguments optionally to be passed to the query string. Provide any
        fdsn standard *except* 'format', which by default will be set to 'text'
    """
    querystr = get_query_str(network, start_after_year, format_, **kwargs)
    return read(querystr)


def get_network_stations(network, start_after_year, **kwargs):
    """
        Retutrns all stations froma  given network.
        :param kwargs: keyword arguments optionally to be passed to the query string. Provide any
        fdsn standard *except* 'format' and 'level', which by default will be set to 'text' and
        'channel'
    """
    try:
        kwargs['level'] = 'channel'
        tree = read_network(network, start_after_year, "xml", **kwargs)
        root = tree.getroot()
        namespaces = {"x": "http://www.fdsn.org/xml/station/1"}
        stations = root.findall("./x:Network/x:Station", namespaces=namespaces)

        def getchildtext(element, child_tag):
            elm = element.find("x:%s" % child_tag, namespaces)
            if elm is None:
                raise ValueError("XmlError: element '%s' has no child '%s'" % (element.tag,
                                                                               child_tag))
            return element.find("x:%s" % child_tag, namespaces).text

        def getatt(element, att):
            try:
                return element.attrib[att]
            except KeyError:
                raise ValueError("XML error: element '%s' has no attribute '%s'" % (element.tag,
                                                                                    att))

        columns = ['Name', 'Lat', 'Lon', 'Ele', 'Azi', 'Rate', 'Sensor', 'ID', 'Logger', 'Id',
                   'Start', 'End', 'Channels']

        reg = re.compile("\\s*,\\s*")  # regex for chacking if value is already in a column

        # Note that the "station" row is uniquely identified by station name, channel start date
        # and channel end date. So build the identifier:
        rows = {}
        for sta in stations:
            sta_name = getatt(sta, 'code')
            chans = sta.findall("x:Channel", namespaces=namespaces)

            for cha in chans:
                date0 = getatt(cha, 'startDate')
                date1 = getatt(cha, 'endDate')
                tup = (sta_name, date0, date1)

                row = ['']*len(columns)
                row[columns.index('Name')] = sta_name
                row[columns.index('Start')] = date0[:10]  # quick hack to remove time information
                row[columns.index('End')] = date1[:10]  # see above
                row[columns.index('Lat')] = getchildtext(cha, "Latitude")
                row[columns.index('Lon')] = getchildtext(cha, "Longitude")
                row[columns.index('Ele')] = getchildtext(cha, "Elevation")
                row[columns.index('Rate')] = getchildtext(cha, "SampleRate")
                row[columns.index('Azi')] = getchildtext(cha, "Azimuth")

                datalogger = cha.find("x:DataLogger", namespaces=namespaces)
                row[columns.index('Id')] = getchildtext(datalogger, "SerialNumber")
                row[columns.index('Logger')] = getchildtext(datalogger, "Model")
                sensor = cha.find("x:Sensor", namespaces=namespaces)
                row[columns.index('ID')] = getchildtext(sensor, "SerialNumber")
                row[columns.index('Sensor')] = getchildtext(sensor, "Model")
                row[columns.index('Channels')] = getatt(cha, 'code')

                row_orig = rows.get(tup, None)
                if row_orig is None:
                    rows[tup] = row
                else:
                    for i, val in enumerate(row_orig):
                        vals = reg.split(val)
                        if row[i] not in vals:
                            row_orig[i] += ", " + row[i]
                    # row[columns.index('Channels')] += ", " + cha_name

        return pd.DataFrame(sorted(rows.values(), key=lambda val: val[columns.index('Name')]),
                            columns=columns)
    except (URLError, ValueError, XMLSyntaxError) as exc:
        raise ValueError(exc.__class__.__name__ + ": " + str(exc))


def get_all_stations(network, start_after_year, **kwargs):
    """
        Returns all stations from a  given network.
        :param kwargs: keyword arguments optionally to be passed to the query string. Provide any
        fdsn standard *except* 'format' and 'level', which by default will be set to 'text' and
        'station'
    """
    kwargs['level'] = 'station'
    # returns a pandas dataframe
    text = read_network(network, start_after_year, "text", **kwargs)
    df = pd.read_csv(StringIO(text.replace("|", ",")), index_col=False, dtype={'Location': str})
    # FIXME: dtype above does NOT WORK!!
    return df


def get_all_stations_within(network_stations_df, network, start_after):

    tonum = pd.to_numeric
    lat_min = tonum(network_stations_df['Lat']).min()
    lat_max = tonum(network_stations_df['Lat']).max()
    lon_min = tonum(network_stations_df['Lon']).min()
    lon_max = tonum(network_stations_df['Lon']).max()

    return get_all_stations("*", start_after, level='station', minlat=lat_min, maxlat=lat_max,
                            minlon=lon_min, maxlon=lon_max)


def get_stations_df(network, start_after, network_station_marker, network_station_color,
                    nonnetwork_station_marker, nonnetwork_station_color):

    network_stations = get_network_stations(network, start_after)
    all_stations = get_all_stations_within(network_stations, network, start_after)

    # add columns
    all_stations['Marker'] = nonnetwork_station_marker
    all_stations['Color'] = nonnetwork_station_color
    # write markers for network stations:
    all_stations.loc[all_stations['#Network'] == network, 'Marker'] = network_station_marker
    all_stations.loc[all_stations['#Network'] == network, 'Color'] = network_station_color

    # rename nonnetwork stations to the names provided in network stations:
    new_cols = ['Name', 'Lat', 'Lon', 'Marker', 'Color']
    all_stations = all_stations.rename(columns={'Station': new_cols[0],
                                                'Latitude': new_cols[1],
                                                'Longitude': new_cols[2],
                                                })[new_cols]

    return network_stations, all_stations


def click_path_type(isdir=False):
    return click.Path(exists=True, file_okay=not isdir, dir_okay=isdir, writable=False,
                      readable=True, resolve_path=True)


def click_get_outdir(ctx, param, value):
    """Does a check on the outdir: when it's None, called D the dir specified in config.py
    return D/network"""
    use_default_dir = value is None
    if use_default_dir:
        network = ctx.params.get('network', None)
        if network is None:
            raise click.BadParameter("optional '%s' missing, but no network specified"
                                     % param.human_readable_name)
        from reportgen.network.www import config
        path = config.SOURCE_PATH
        value = os.path.abspath(os.path.join(path, network))

    return value


def makedirs(path):
    """Same as os.makedirs except that it silently exits if the path already exists"""
    if not os.path.isdir(path):
        os.makedirs(path)


def copyfiles(src, dst_dir, move=False):
    """
        Copies /move files recursively, extending shutil and allowing glob expressions
        in src
        :param src: a which MUST not be a system directory, denoting:
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


def get_noise_pdfs_content(dst_dir, reg="^(?P<row>.*)_(?P<col>[A-Z][A-Z][A-Z]).*$",
                           columns=["HHZ", "HHN", "HHE"]):
    from collections import defaultdict as ddict
    reg = re.compile(reg)
    dct = ddict(lambda: [''] * len(columns))
    for fl in os.listdir(dst_dir):
        mat = reg.match(fl)
        if mat and len(mat.groups()) == 2:
            row = mat.group('row')
            col = mat.group('col')
            if col in columns:
                dct[row][columns.index(col)] = fl

    ret = [columns] + [dct[k] for k in sorted(dct)]

    sio = StringIO()
    spamwriter = csv.writer(sio, delimiter=',', quotechar='"')  # , quoting=csv.QUOTE_MINIMAL)
    for line in ret:
        spamwriter.writerow(line)
    ret = sio.getvalue()
    sio.close()
    return ret


def get_fig_jinja_vars(fig_name, src_path, src_rst_path, **options):
    """
    Returns the variables to be passed to our template.rst for the figure identified by
    fig_name when building a report.rst
    Basically, these variables change if the src_path has one image or more than one
    """
    filenames = [f for f in os.listdir(src_path)]
    caption_str = 'here the figure caption'

    if len(filenames) == 0:
        raise ValueError("No file found in '%s' while building directive for '%s'" % (src_path,
                                                                                      fig_name))
    elif len(filenames) == 1:
        dic = {fig_name+'_directive': 'figure',
               fig_name+'_content': caption_str,
               fig_name+'_arg': relpath(os.path.join(src_path, filenames[0]), src_rst_path),
               fig_name+'_options': options,
               }
    elif len(filenames) > 1:
        filenames = sorted(filenames)
        options.update({'dir': relpath(src_path, src_rst_path)})
        dic = {fig_name+'_directive': 'images-grid',
               fig_name+'_content':
               "\n".join('"%s"' % f if " " in f else f for f in filenames),
               fig_name+'_arg': caption_str,
               fig_name+'_options': options
               }
    return dic


def relpath(path, reference_path):
    """Almost the same as os.path.relpath but prepends a dot, so the returned value is
        usable in .rst relative paths"""
    return os.path.join(".", os.path.relpath(path, reference_path))


@click.command()
@click.argument('network')
@click.argument('start_after')  # , type=int)
@click.option('-o', '--out_path', default=None, callback=click_get_outdir,
              help=("The output directory. If missing, it defaults to the directory specified in "
                    "the web config file (config.py) PLUS the network name. In this case the "
                    "report can be edited in the web application. The destination directory "
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
                    "depends on the inversed order the files are returned from the OS). "
                    "The rows of the resulting image grid will be sorted alphabetically according "
                    "to the station name"))
@click.option('-i', '--inst_uptimes', default=None, multiple=True,
              help=('The path (directory, file) '
                    'of the instrument uptimes image(s). If multiple files '
                    'are provided, the images will be displayed in a grid of one column '
                    'sorted alphabetically by name'))
@click.option('-d', '--data_aval', default=None, multiple=True,
              help=('The path (directory, file) '
                    'of the data availability image(s). If multiple files '
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
def main(network, start_after, out_path, noise_pdf, inst_uptimes, data_aval, update, mv, no_prompt,
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

         +- data_aval     [directory]

    NOTE: Data files specified by 'noise_pdf', 'inst_uptimes' and 'data_aval' must denote one or
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

    sys.exit(run(network, start_after, out_path, noise_pdf, inst_uptimes, data_aval, update, mv,
                 no_prompt, network_station_marker, nonnetwork_station_marker,
                 network_station_color, nonnetwork_station_color))


def run(network, start_after, out_path, noise_pdf, inst_uptimes, data_aval, update, mv, no_prompt,
        network_station_marker, nonnetwork_station_marker, network_station_color,
        nonnetwork_station_color):

    # first a check on the path. Note that it is not None (see click_get_outdir function)
    out_path_exists = os.path.isdir(out_path)
    try:

        if out_path_exists and not update:
            raise ValueError(("'%s' already exists. Please provide a non-existing dir name "
                              "or supply the '--update' argument to copy data files only.\n"
                              "Putting content in an already existing non-empty directory "
                              "is unsafe as we might have conflicts when building the report") %
                             out_path)

        if not no_prompt:  # FIXME: click has a prompt function but how to deal with the case update
            # or not? (see http://click.pocoo.org/5/options/#prompting)
            print("Data %s up to be written to:" %
                  ("(only) is " if update else "and config files are "))
            print("%s" % out_path)
            if not out_path_exists:
                print("The directory path will be created (mkdir -p)")
            print("Continue? (y for yes, anything else for abort)")
            l = sys.stdin.readline()
            if l.strip() != 'y':
                raise ValueError("aborted by user")

        # now we have two scenarios:
        # 1) update is False: then out_path does not exist (see above). We will create the dir
        # when copying the config file
        # 2) update is True: then we will make out_path when copying the data files (we will skip
        # config dir and rst files, not copied)

        # defining paths:
        _this_dir = os.path.dirname(__file__)
        template_src = os.path.abspath(os.path.join(_this_dir, "template.rst"))
        config_src = os.path.abspath(os.path.join(_this_dir, "config"))

        _data_outdir = os.path.join(out_path, "data")
        noise_pdf_dst = os.path.join(_data_outdir, "noise_pdf")
        # noise_pdf is an object with dirname prop
        inst_uptimes_dst = os.path.join(_data_outdir, "inst_uptimes")
        data_aval_dst = os.path.join(_data_outdir, "data_aval")
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
        for path in [inst_uptimes_dst, data_aval_dst, noise_pdf_dst]:
            makedirs(path)

        # copy data files: inst_uptimes, data_aval, noise_pdf
        # note that the first elements of each tuple are LISTS as the arguments have the
        # flag multiple=True
        for arg__ in [(inst_uptimes, inst_uptimes_dst),
                      (data_aval, data_aval_dst),
                      (noise_pdf, noise_pdf_dst)]:
            dst__ = arg__[1]
            for src__ in arg__[0]:
                print("Copying file: '%s' in '%s'" % (src__, dst__))
                copyfiles(src__, dst__, mv)
                # raise Error if no files are in the folder. Sphinx complains afterwards for bad
                # formed code (e.g. csv tables with no content). If update, skip the check cause we
                # cannot determine if we actually want to copy files or not
                if not os.listdir(dst__):
                    raise IOError("'%s' is empty: no files copied" % dst__)

        if create_rst_and_config:
            print("Generating report template")
            sta_df, all_sta_df = get_stations_df(network, start_after, network_station_marker,
                                                 network_station_color, nonnetwork_station_marker,
                                                 nonnetwork_station_color)

            # building template, see template.rst:
            args = dict(
                        stations_table_csv_content=sta_df.to_csv(sep=",", quotechar='"',
                                                                 index=False),
                        stations_map_csv_content=all_sta_df.to_csv(sep=",", quotechar='"',
                                                                   index=False),
                        noise_pdfs_dir_path=relpath(noise_pdf_dst, out_path),
                        noise_pdfs_content=get_noise_pdfs_content(noise_pdf_dst),
                        )

            args.update(get_fig_jinja_vars("data_aval", data_aval_dst, out_path))
            args.update(get_fig_jinja_vars("inst_uptimes", inst_uptimes_dst, out_path))

            with open(template_src, 'r') as opn:
                txt = opn.read().decode('UTF8')
            reporttext = Environment().from_string(txt).render(**args)

            # copying the report.rst file
            print("Writing report rst file in %s" % (template_dst))
            with open(template_dst, 'w') as opn:
                opn.write(reporttext.encode('UTF8'))

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
        if not out_path_exists and os.path.isdir(out_path):
            shutil.rmtree(out_path, ignore_errors=True)
        print("Aborted: %s" % str(exc))
        return 1

if __name__ == '__main__':
    main()
