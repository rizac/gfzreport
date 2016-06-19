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
from reportbuild.core.utils import load_module

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
            return element.find("x:%s" % child_tag, namespaces).text

        columns = ['Name', 'Lat', 'Lon', 'Ele', 'Azi', 'Rate', 'Sensor', 'ID', 'Logger', 'Id',
                   'Start', 'End', 'Channels']

        reg = re.compile("\\s*,\\s*")  # regex for chacking if value is already in a column

        # Note that the "station" row is uniquely identified by station name, channel start date
        # and channel end date. So build the identifier:
        rows = {}
        for sta in stations:
            sta_name = sta.attrib['code']
            chans = sta.findall("x:Channel", namespaces=namespaces)

            for cha in chans:
                date0 = cha.attrib['startDate']
                date1 = cha.attrib['endDate']
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
                row[columns.index('Channels')] = cha.attrib['code']

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
    except (URLError, ValueError, TypeError) as exc:
        raise ValueError(exc.__class__.__name__ + ": " + str(exc))


def get_all_stations(network, start_after_year, **kwargs):
    """
        Retutrns all stations froma  given network.
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
    """Does a check on the outdir: wither it does not exists, or it's empty. Returns it
    in these two cases, otherwise raises Click error"""
    use_default_dir = value is None
    if use_default_dir:
        network = ctx.params.get('network', None)
        if network is None:
            raise click.BadParameter("optional '%s' missing, but no network specified"
                                     % param.human_readable_name)
        from reportgen.network.www import config
        path = config.SOURCE_PATH
        value = os.path.join(path, network)
        # make parent dir if it does not exist:
        if not os.path.isdir(os.path.dirname(value)):
            os.makedirs(os.path.dirname(value))

    if not os.path.isdir(value):
        if not os.path.isdir(os.path.dirname(value)):
            raise click.BadParameter("'%s' does not exists and cannot be created" % value)
    elif not ctx.params['update']:
        raise click.BadParameter(("'%s' %salready exists. Please provide a non-existing dir name"
                                  "whose path exists (i.e. than can be created via `mkdir`).\n"
                                  "Putting content in an already existing non-empty directory "
                                  "is unsafe as we might have conflicts when building the report") %
                                 (value, "(default directory for web page) " if use_default_dir
                                  else ""))
    return value


def makedirs(path):
    """Same as os.makedirs except that it silently exits if the path already exists"""
    if not os.path.isdir(path):
        os.makedirs(path)


def copyfiles(src, dst, move=False):
    """
        Extended version which allows to copy files, form local or remote machines
        :param src: a which MUST not be a system directory, denoting:
            * an existing file. In this case `shutil.copy2(src, dst)` will be called (dst can be
              either a file or a directory. If file, it will be overridden)
            * a string starting with 'scp ' or 'rsync ', followed by the remote path to copy files
              from. In this case, the argument password must be provided if no ssh key is
        :param dst: a destination file, or directory
    """
    if os.path.isdir(src):
        raise OSError("cannot copy a directory '%s', please provide a file or a glob expression"
                      % src)

    dst_is_dir = os.path.isdir(dst)
    if os.path.isfile(src):
        # copytree does not work if dest exists. So
        # for file in os.listdir(src):
        if not move:
            if not dst_is_dir:
                # copy2 requires a dst folder to exist,
                makedirs(dst)
            shutil.copy2(src, dst)
        else:
            shutil.move(src, dst)
    else:
        glb_list = glob(src)
        if len(glb_list) and glb_list[0] != src:
            # in principle, if src denotes a non-existing file or dir, glb_list is empty, if it
            # denotes an existing file or dir, it has a single element equal to src. This latter
            # case is a problem as we might have an error when copying a dir
            # In principle copy2 below raises the exception but for safety we repeat
            # the test here
            for srcf in glob(src):  # glob returns joined pathname, it's not os.listdir!
                copyfiles(srcf, dst)


def get_noise_pdfs_content(dst_dir, reg="^(?P<row>.*?)_(?P<col>[a-zA-Z]+).*$",
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
@click.argument('start_after', type=int)
@click.option('-o', '--out_path', default=None, callback=click_get_outdir,
              help=("The output directory. If missing, it defaults to the directory specified in "
                    "the web config file (config.py) so that the report first draft can be edited "
                    "in the web application. In any case, if update is set to False (default when "
                    "missing), it must NOT exist"))
@click.option('-n', '--noise_pdf', default=None, multiple=True,
              help=("The path to the DIRECTORY of the Noise Probability Density functions images. "
                    "The file names are supposed to be in the format "
                    "station_channel"
                    "E.g., AM01_HHZ.pdf will be "
                    "recognized as being the image of station AM01 on channel HHZ. As channels "
                    "consist of alphabetic characters only, also the file "
                    "AM01_HHZ.whatever.somestring.png is valid and will recognized. "
                    "The rows of the resulting image grid will be sorted alphabetically according "
                    "to the station name"))
@click.option('-i', '--inst_uptimes', default=None, multiple=True,
              help=('The path to the FILE of the instrument uptimes image. If multiple files '
                    'are provided, the images will be displayed in a grid of one column'))
@click.option('-d', '--data_aval', default=None, multiple=True,
              help=('The path to the FILE of the data availability image. If multiple files '
                    'are provided, the images will be displayed in a grid of one column'))
@click.option('-u', '--update', is_flag=True, default=False, is_eager=True,  # <- exec it first
              help=("Flag denoting if the  output directory OUT_PATH has to be updated. If false,"
                    "(the default) then OUT_PATH must not exist. If True, and OUT_PATH exists, "
                    "only options input paths (see NOTE above) will be copied in the "
                    "program-defined sub-directories of OUT_PATH: any other file, e.g., an RsT file "
                    "directly under OUT_PATH and currently being edited, will not be modified. "
                    "It is then up to the user to modify the rst file to include newly added files,"
                    " if any"))
@click.option("--mv", is_flag=True, default=False,
              help=("Set to true (false by default) to move all specified files instead of copying"
                    "them."))
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
def main(network, start_after, out_path, noise_pdf, inst_uptimes, data_aval, update, mv,
         network_station_marker, nonnetwork_station_marker, network_station_color,
         nonnetwork_station_color):
    """
    Generates the report folder for the given network and year

    NETWORK: the network name, e.g.: ZE.\n
    START_AFTER: the start year, e.g.: 2012.\n

    -----------------------------------------

    NOTE: Options input paths 'noise_pdf', 'inst_uptimes' and 'data_aval' must denote one or
    more files. They can be typed ONE OR MORE TIMES, where each file path is a local system paths
    (with or without wildcards):
    \b
    [program_name] --noise_pdf /home/my_images/myfile.png --noise_pdf /home/other_images/*.jpg
    """

    # defining paths:
    _this_dir = os.path.dirname(__file__)
    template_src = os.path.abspath(os.path.join(_this_dir, "template.rst"))
    config_src = os.path.abspath(os.path.join(_this_dir, "config"))

    _data_outdir = os.path.join(out_path, "data")
    noise_pdf_dst = os.path.join(_data_outdir, "noise_pdf")
    # noise_pdf is an object with dirname prop
    inst_uptimes_dst = os.path.join(_data_outdir, "instr_uptimes")
    data_aval_dst = os.path.join(_data_outdir, "data_aval")
    template_dst = os.path.join(out_path, "report.rst")
    config_dst = out_path  # os.path.abspath(os.path.join(os.path.join(out_path, "config")))

    # remember: the doc above is shown when calling --help. Arguments DO NOT ACCEPT HELP, THUS
    # IT MUST BE WRITTEN THERE!!
    out_path_exists = os.path.isdir(out_path)
    try:
        create_rst_and_config = not update or not out_path_exists
        if create_rst_and_config:
            # some check to avoid copying files if useless:
            if not os.path.isfile(template_src):
                raise IOError("No template.rst found at %s" % template_src)

            # then copy conf dir, as copytree calls mkdirs(config_dst) and requires the dst not to
            # exist (so if we config_dst == out_path, this must be the first operation)
            print("Copying config dir: %s in %s " % (config_src, config_dst))
            shutil.copytree(config_src, config_dst)

        # copy the images files:

        # 1) instrumental uptimes
        for inst_uptime in inst_uptimes:
            print("Copying file: %s in %s " % (inst_uptime, inst_uptimes_dst))
            copyfiles(inst_uptime, inst_uptimes_dst, mv)

        # 2) data availability
        for data_ava in data_aval:
            print("Copying file: %s in %s " % (data_ava, data_aval_dst))
            copyfiles(data_ava, data_aval_dst, mv)

        # 3) pdfs
        for noise_ppd in noise_pdf:
            print("Copying files: %s in %s " % (noise_ppd, noise_pdf_dst))
            copyfiles(noise_ppd, noise_pdf_dst, mv)

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
            args.update(get_fig_jinja_vars("instr_uptimes", inst_uptimes_dst, out_path))

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
    sys.exit(main())
