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
from jinja2 import Environment
from reportgen.core import utils
import shutil

def get_format(query_str):
    try:
        r = re.compile("[\\?\\&]format=(.*?)[\\&$]")
        return r.search(query_str).groups()[0]
    except IndexError:
        pass
    return 'xml'


def read(url):
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
                row = rows.get(tup, None)
                cha_name = cha.attrib['code']
                if row is None:
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
                    row[columns.index('Channels')] = cha_name
                    rows[tup] = row
                else:
                    row[columns.index('Channels')] += ", " + cha_name

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


def click_get_wildcard_iterator(ctx, param, value):
    try:
        return utils.split_wildcard(value)
    except OSError as oerr:
        raise click.BadParameter(str(oerr))


def click_get_outdir(ctx, param, value):
    """Does a check on the outdir: wither it does not exists, or it's empty. Returns it
    in these two cases, otherwise raises Click error"""
    if not os.path.isdir(value):
        if not os.path.isdir(os.path.dirname(value)):
            raise click.BadParameter("'%s' does not exists and cannot be created" % value)
        else:
            os.mkdir(value)
            if not os.path.isdir(value):
                raise click.BadParameter("Failed while calling mkdir on '%s'" % value)
    else:
        for _ in os.listdir(value):
            raise click.BadParameter("'%s' already exists and not empty. Please provide an empty directory or "
                                     "a directory than can be created via mkdir (i.e. whose parent exists).\n"
                                     "Putting content in an already existing non-empty directory "
                                     "is unsafe as we might have conflicts when building the report" %
                                     value)
    return value


@click.command()
@click.argument('network')
@click.argument('start_after', type=int)
@click.argument('out_path', callback=click_get_outdir)
@click.option('-p', '--noise_pdf', default=None, callback=click_get_wildcard_iterator,
              help=("The path to the DIRECTORY of the Noise Probability Density functions images. "
                    "You can provide wildcard such as ? and *. Example: -p /mypath/*.png"))
@click.option('-u', '--inst_uptimes', default=None, type=click_path_type(isdir=False),
              help='The path to the FILE of the instrument uptimes image')
@click.option('-a', '--data_aval', default=None, type=click_path_type(isdir=False),
              help='The path to the FILE of the data availability image')
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
def main(network, start_after, out_path, noise_pdf, inst_uptimes, data_aval,
         network_station_marker, nonnetwork_station_marker, network_station_color,
         nonnetwork_station_color):
    """NETWORK: the network name, e.g.: ZE. 
    START_AFTER: the start year, e.g.: 2012. 
    OUT_PATH: The output directory. It must not exist or be empty. If it does not exist, mkdir will be called.
    If mkdir fails, the program will stop."""
    # remember: the doc above is shown when calling --help. Arguments DO NOT ACCEPT HELP, THUS
    # IT MUST BE WRITTEN THERE!!
    try:
        print("Generating report template")
        sta_df, all_sta_df = get_stations_df(network, start_after, network_station_marker,
                                             network_station_color, nonnetwork_station_marker,
                                             nonnetwork_station_color)

        # defining paths:
        this_dir = os.path.dirname(__file__)
        data_outdir = os.path.join(out_path, "data")
        noise_pdf_outdir = os.path.join(data_outdir, "noise_pdf")  # noise_pdf is an object with dirname prop
        inst_uptimes_outfile = os.path.join(data_outdir, "instr_uptimes", os.path.basename(inst_uptimes))
        data_aval_outfile = os.path.join(data_outdir, "data_aval", os.path.basename(data_aval))
        template_inpath = os.path.abspath(os.path.join(this_dir, "template.rst"))
        template_outpath = os.path.join(out_path, "report.rst")
        config_src = os.path.abspath(os.path.join(this_dir, "config"))
        config_dst = out_path  # os.path.abspath(os.path.join(os.path.join(out_path, "config")))

        # building template:
        args = dict(
                    stations_table_csv_content=sta_df.to_csv(sep=",", quotechar='"', index=False),
                    stations_map_csv_content=all_sta_df.to_csv(sep=",", quotechar='"', index=False),
                    data_aval_fig_path=os.path.join(".", os.path.relpath(data_aval_outfile, out_path)),
                    instr_uptimes_fig_path=os.path.join(".", os.path.relpath(inst_uptimes_outfile, out_path)),
                    noise_pdfs_fig_path=os.path.join(".", os.path.relpath(noise_pdf_outdir, out_path)),
                    )

        if not os.path.isfile(template_inpath):
            raise IOError("No template.rst found at %s" % template_inpath)

        with open(template_inpath, 'r') as opn:
            txt = opn.read().decode('UTF8')
        reporttext = Environment().from_string(txt).render(**args)

        print("Writing report rst file in %s" % (template_outpath))
        with open(template_outpath, 'w') as opn:
            opn.write(reporttext.encode('UTF8'))

        # copying files:
        print("Copying file: %s in %s " % (inst_uptimes, inst_uptimes_outfile))
        os.makedirs(os.path.dirname(inst_uptimes_outfile))
        shutil.copy2(inst_uptimes, inst_uptimes_outfile)
        print("Copying file: %s in %s " % (data_aval, data_aval_outfile))
        os.makedirs(os.path.dirname(data_aval_outfile))
        shutil.copy2(data_aval, data_aval_outfile)
        print("Copying files: %s in %s " % (noise_pdf.path, noise_pdf_outdir))
        os.makedirs(noise_pdf_outdir)
        img_count = 0
        for img_path in noise_pdf.listdir():
            shutil.copy2(img_path, noise_pdf_outdir)
            img_count += 1
        print("(%d files copied) " % (img_count))

        print("Copying config dir: %s in %s " % (config_src, config_dst))
        utils.copytree(config_src, config_dst)
        print("===========================================")
        print("Generated report in '%s'" % os.path.abspath(out_path))
        print("Please edit the file %s in that directory and then create your build with:"
              % os.path.basename(template_outpath))
        print("    reportbuild %s OUTDIR%s -b latex -E"
              % (os.path.abspath(out_path),
                 " -c " + os.path.abspath(config_dst) if
                 os.path.abspath(config_dst) != os.path.abspath(out_path) else ""))
        print("Where OUTDIR is a selected output directory and -b can be either latex, html or pdf")
        return 0
    except (IOError, OSError) as exc:
        print("Aborted: %s" % str(exc))
        return 1

if __name__ == '__main__':
    sys.exit(main())
