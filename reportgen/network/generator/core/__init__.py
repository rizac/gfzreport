'''
Created on Jan 9, 2017

Core utilities for the network-generator program

@author: riccardo
'''

import sys
import os
import shutil
from glob import glob
import numpy as np
import csv
from datetime import datetime
import re
import pandas as pd
# from obspy import read_inventory
from lxml import etree
import urllib2
from cStringIO import StringIO
from urllib2 import URLError
from jinja2 import Environment
from lxml.etree import XMLSyntaxError
from reportgen.network.generator.core.utils import read, relpath, read_network
from network.generator.core.utils import get_query
from itertools import product
from reportbuild.map import MapHandler


def get_network_stations(network, start_after_year, **kwargs):
    """
        Retutrns all stations from a given network.
        :param kwargs: keyword arguments optionally to be passed to the query string. Provide any
        fdsn standard *except* 'format' and 'level', which by default will be set to 'text' and
        'channel'
        #FIXME: USE OBSPY read_inventory!!
    """
    try:
        tree = read_network(network, start_after_year, **kwargs)

#         kwargs['format'] = 'text'
#         tree2 = read_network(network, start_after_year, **kwargs)
#         r = read_inventory(StringIO(tree2), format="STATIONXML")

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

        net_df = pd.DataFrame(sorted(rows.values(), key=lambda val: val[columns.index('Name')]),
                              columns=columns)
        # attach attributes:
        net_element = root.findall("./x:Network", namespaces=namespaces)[0]
        atts = {k: net_element.attrib[k] for k in net_element.attrib}
        # convert dates:
        for key in atts.keys():  # use keys so that we can modify the dict values
            if key in ('startDate', 'endDate'):
                atts[key] = datetime.strptime(atts[key], '%Y-%m-%dT%H:%M:%S')
        # attach description
        desc = root.findall("./x:Network/x:Description", namespaces=namespaces)[0].text
        net_df.metadata = {'atts': atts, 'desc': desc}
        return net_df
    except (URLError, ValueError, XMLSyntaxError) as exc:
        raise ValueError(exc.__class__.__name__ + ": " + str(exc))


# def get_all_stations(network, start_after_year, **kwargs):
#     """
#         Returns all stations from a  given network.
#         :param kwargs: keyword arguments optionally to be passed to the query string. Provide any
#         fdsn standard *except* 'format' and 'level', which by default will be set to 'text' and
#         'station'
#     """
#     kwargs['level'] = 'station'
#     # returns a pandas dataframe
#     text = read_network(network, start_after_year, "text", **kwargs)
#     df = pd.read_csv(StringIO(text.replace("|", ",")), index_col=False, dtype={'Location': str})
#     # FIXME: dtype above does NOT WORK!!
#     return df


def get_all_stations_within(network_stations_df, margins_in_km=100):
    tonum = pd.to_numeric
    _, _, minlon, minlat, maxlon, maxlat = \
        MapHandler._calc_bounds(tonum(network_stations_df['Lon']).min(),
                                tonum(network_stations_df['Lat']).min(),
                                tonum(network_stations_df['Lon']).max(),
                                tonum(network_stations_df['Lat']).max(),
                                np.array(4*[margins_in_km]) * 1000)

    atts = network_stations_df.metadata['atts']
    kwargs_live_stations = dict(minlat=minlat, maxlat=maxlat, minlon=minlon, maxlon=maxlon,
                                starttime=atts['startDate'].isoformat(),
                                endtime=atts['endDate'].isoformat(),
                                format='xml')

    kwargs_dead_stations = dict(kwargs_live_stations)
    kwargs_dead_stations['endbefore'] = kwargs_dead_stations.pop('starttime')
    kwargs_dead_stations.pop('endtime')

    dfs = []
    dcs = ['http://service.iris.edu/fdsnws/station/1/query',
           'http://www.orfeus-eu.org/fdsnws/station/1/query']

    for dc, kwargs in product(dcs, [kwargs_live_stations, kwargs_dead_stations]):
        print get_query(dc, **kwargs)
        try:
            text = read(get_query(dc, **kwargs))
            if not text:
                continue
            # r = read_inventory(StringIO(text), format="STATIONXML")
            
            df = pd.read_csv(StringIO(text), delimiter='|', index_col=False)
            dfs.append(df)
        except XMLSyntaxError as _:
            text = ""
            pass
        if not text:
            continue


    raise AttributeError('wat?')
    # return stations active in the relative timespan:
    return pd.concat(dfs, axis=0, ignore_index=True, copy=False)


def get_stations():

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


def gen_title(stations_df):
    """Generates the title for the .rst file from a pandas DataFrame returned by 
    get_network_stations"""
    # template:
    # =============================================================
    # {{ network_code }} {{ network_start_date }}-{{ network_end_date }}
    # =============================================================
    atts = getattr(stations_df, 'metadata', {}).get('atts', {})
    start = atts.get('startDate', None)
    end = atts.get('endDate', None)
    code = atts.get('code', None)

    if not start:
        raise ValueError("startDate not found in xml")
    if not end:
        raise ValueError("endDate not found in xml")
    if not code:
        raise ValueError("(network) code not found in xml")

    title = "%s %d-%d" % (code, start.year, end.year)
    decorator = "=" * len(title)
    return "%s\n%s\n%s" % (decorator, title, decorator)


def get_net_desc(stations_df):
    """Returns the network description for the .rst file from a pandas DataFrame returned by 
    get_network_stations"""
    return getattr(stations_df, 'metadata', {}).get('desc', "")
