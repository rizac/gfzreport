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
from urllib2 import URLError, HTTPError
from jinja2 import Environment
# from lxml.etree import XMLSyntaxError
from collections import defaultdict as defdict, OrderedDict as odict
from gfzreport.templates.network.core.utils import relpath, read_network, read_stations, todf,\
    get_query
from itertools import product, cycle, izip
from lxml.etree import XMLSyntaxError
from collections import defaultdict
from gfzreport.sphinxbuild.map import getbounds


def get_network_stations_df(network, start_after_year):
    """
        Returns the dataframe representing the network stations table in rst.
        :param network: string. The network name (e.g., 'ZE')
        :param start_after_year (string or integer) The year denoting the network start time
        Only stations after that time will be displayed
    """

    inv = read_network(network, start_after_year)

    def int_(val):
        ival = int(val)
        return ival if ival == val else val

    def func(net, sta):
        retdict = defdict(odict)
        strfrmt = "%0.4d-%0.2d-%0.2d"
        for cha in sta.channels:
            start = strfrmt % (cha.start_date.year, cha.start_date.month, cha.start_date.day)
            end = strfrmt % (cha.end_date.year, cha.end_date.month, cha.end_date.day)
            # identify each row by its channel tuple:
            id_ = (sta.code, start, end)
            mydic = retdict[id_]  # add if does not exist
            mydic['Label'] = sta.code
            mydic['Lat'] = sta.latitude
            mydic['Lon'] = sta.longitude
            mydic['Ele'] = int_(cha.elevation)
            mydic['Azi'] = int_(max(mydic['Azi'], cha.azimuth) if 'Azi' in mydic else cha.azimuth)
            mydic['Rate'] = int_(cha.sample_rate)
            mydic['Sensor'] = cha.sensor.model
            mydic['ID'] = cha.sensor.serial_number
            mydic['Logger'] = cha.data_logger.model
            mydic['Id'] = cha.data_logger.serial_number
            mydic['Start'] = start
            mydic['End'] = end
            mydic['Channels'] = "%s %s" % (mydic['Channels'], cha.code) \
                if 'Channels' in mydic else cha.code

        return retdict.itervalues()

    dframe = todf(inv, func, funclevel='station', sortkey=lambda val: val['Label'])

    # add metadata:
    dframe.metadata = {'start_date': None, 'end_date': None, 'desc': ''}
    for net in inv:
        if net.code == network:
            dframe.metadata['start_date'] = net.start_date
            dframe.metadata['end_date'] = net.end_date
            dframe.metadata['desc'] = net.description
            break

    return dframe


def get_other_stations_df(network_stations_df, margins_in_deg):
    tonum = pd.to_numeric
    _, _, minlon, minlat, maxlon, maxlat = getbounds(tonum(network_stations_df['Lon']).min(),
                                                     tonum(network_stations_df['Lat']).min(),
                                                     tonum(network_stations_df['Lon']).max(),
                                                     tonum(network_stations_df['Lat']).max(),
                                                     margins_in_deg)

    meta = network_stations_df.metadata
    kwargs_live_stations = dict(minlat=minlat, maxlat=maxlat, minlon=minlon, maxlon=maxlon,
                                starttime=meta['start_date'].isoformat(),
                                endtime=meta['end_date'].isoformat(),
                                level='station',
                                format='xml')

    kwargs_dead_stations = dict(kwargs_live_stations)
    kwargs_dead_stations['endbefore'] = kwargs_dead_stations.pop('starttime')
    kwargs_dead_stations.pop('endtime')

    invs = []

    dcs = [d for d in get_datacenters() if not 'geofon' in d]
#     dcs = ['http://service.iris.edu/fdsnws/station/1/query',
#            'http://www.orfeus-eu.org/fdsnws/station/1/query']

    for dc, kwargs in product(dcs, [kwargs_live_stations, kwargs_dead_stations]):
        querystr = get_query(dc, **kwargs)
        try:
            invs.append(read_stations(querystr))
            print "%s [OK]" % querystr
        except (URLError, HTTPError, XMLSyntaxError) as exc:
            print "%s [%s]" % (querystr, str(exc))
            pass
        # r = read_inventory(StringIO(text), format="STATIONXML")
        # df = pd.read_csv(StringIO(text), delimiter='|', index_col=False)
        # dfs.append(df)

    symbols = cycle([
                     # '.',  # point
                     # ',',  # pixel
                     'o',  # circle
                     '^',  # triangle_up
                     'v',  # triangle_down
                     '<',  # triangle_left
                     '>',  # triangle_right
                     # '1',  # tri_down
                     # '2',  # tri_up
                     # '3',  # tri_left
                     # '4',  # tri_right
                     '8',  # octagon
                     # 's',  # square
                     'p',  # pentagon
                     '*',  # star
                     'h',  # hexagon1
                     'H',  # hexagon2
                     # '+',  # plus
                     # 'x',  # x
                     'D',  # diamond
                     'd',  # thin_diamond
                     # '|',  # vline
                     # '_',  # hline
    ])

    net2markers = defaultdict(lambda: next(symbols))

    # parse all inventories and return dataframes
    def func(net, sta):
        retdict = defdict(odict)
        # Code: # net.code
        if net.code == 'SY':  # ignore synthetic data
            return retdict

        # get symbols (cycle iterates on infinity and returns to top)
        marker = net2markers[net.code]
        # get caption (using restricted, year range and network code):
        if net.restricted_status == 'open':
            restricted = ""
        else:
            restricted = " (restr.)"
        # for temporary networks additional quote years of operation
        if net.code[0] in 'XYZ0123456789':
            yearrng = " %d-%d" % (net.start_date.year, net.end_date.year)
        else:
            yearrng = ""
        caption = "%s%s%s" % (net.code, yearrng, restricted)

        color = '#FFFFFF00' if not net.end_date or not network_stations_df.metadata['end_date'] or \
            net.end_date > network_stations_df.metadata['end_date'] else '#FFFFFF00'  # transparent

        mydic = odict()
        mydic['Label'] = sta.code
        mydic['Lat'] = sta.latitude
        mydic['Lon'] = sta.longitude
        mydic['Network'] = net.code
        mydic['Marker'] = marker
        mydic['Legend'] = caption
        mydic['Color'] = color
        return mydic

    dfs = []
    for inv in invs:
        dframe = todf(inv, func, funclevel='station')  # , sortkey=lambda val: val['Name'])
        if not dframe.empty:
            dfs.append(dframe)

    # return stations active in the relative timespan:
    return pd.concat(dfs, axis=0, ignore_index=True, copy=False)


def get_datacenters(**query_args):
    """Queries all datacenters and returns the local db model rows correctly added
    Rows already existing (comparing by datacenter station_query_url) are returned as well,
    but not added again
    :param query_args: any key value pair for the query. Note that 'service' and 'format' will
    be overiidden in the code with values of 'station' and 'format', repsecively
    """
    empty_result = {}  # Create once an empty result consistent with the excpetced return value
    query_args['service'] = 'station'
    query_args['format'] = 'post'
    query = get_query('http://geofon.gfz-potsdam.de/eidaws/routing/1/query', **query_args)

    urlo = urllib2.urlopen(query)
    dc_result = urlo.read().decode('utf8')
    urlo.close()

    if not dc_result:
        return empty_result
    # add to db the datacenters read. Two little hacks:
    # 1) parse dc_result string and assume any new line starting with http:// is a valid station
    # query url
    # 2) When adding the datacenter, the table column dataselect_query_url (when not provided, as
    # in this case) is assumed to be the same as station_query_url by replacing "/station" with
    # "/dataselect". See https://www.fdsn.org/webservices/FDSN-WS-Specifications-1.1.pdf
    return [dcen for dcen in dc_result.split("\n") if dcen[:7] == "http://"]


def get_map_df(sta_df, all_sta_df):
    """Returns a DataFrame for the rst map. 
    """
    # current captions are:
    columns = ['Label', 'Lat', 'Lon', 'Marker', 'Color', 'Legend']
    # The first three are common to both dataframes. all_sta_df has all five columns

    # make a new sta_df, it will be a view of the original sta_df. But this way we do not
    # pollute the original
    _sta_df = sta_df[columns[:3]]
    # avoid pandas settingwithcopy warnings (we know what we are doing):
    _sta_df.is_copy = False

    _sta_df['Marker'] = 's'  # square
    _sta_df['Legend'] = ''
    sensors = pd.unique(sta_df['Sensor'])

    # create a variable color scale
    step = 255.0 / (len(sensors)+1)
    # set a scale of reds in html. Use "#00%s00" for scale of green, "#%s%s00" for yellow scale, etc
    colors = ["#%s0000" % hex(int(step*(i+1)))[2:].upper().zfill(2) for i in xrange(len(sensors))]

    _sta_df['Color'] = ''
    for sens, col in izip(sensors, colors):
        _sta_df.loc[sta_df['Sensor'] == sens, 'Color'] = col
        _sta_df.loc[sta_df['Sensor'] == sens, 'Legend'] = sens

    ret_df = pd.concat([_sta_df, all_sta_df], axis=0, ignore_index=True, copy=False)[columns]
    # mark all duplicated Legends as empty except the first(s):
    ret_df.loc[ret_df['Legend'].duplicated(), 'Legend'] = ''
    return ret_df


def get_noise_pdfs_content(dst_dir, regex="^(?P<row>.*)_(?P<col>[A-Z][A-Z][A-Z]).*$",
                           columns=["HHZ", "HHN", "HHE"]):
    from collections import defaultdict as ddict
    reg = re.compile(regex)
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


def get_figdirective_vars(src_path, src_rst_path):
    """
    Returns a dict D with keys
    'directive', 'arg', 'options', 'content'
    to be used in a jinja template:
    The returned dict directive will be 'figure' or 'images-grid' if only one
    file is found in `src_rst` or more, repsectively (if no file, ValueError is raised).
    """
    filenames = [f for f in os.listdir(src_path)]

    if len(filenames) == 0:
        raise ValueError("No file found in '%s' while building figure directive" % src_path)
    elif len(filenames) == 1:
        dic = {'directive': 'figure',
               'arg': relpath(os.path.join(src_path, filenames[0]), src_rst_path),
               'content': ''  # not used, but jinja won't complain. Supply a string not None
               }
    elif len(filenames) > 1:
        filenames = sorted(filenames)
        dic = {'directive': 'images-grid',
               'content': "\n".join('"%s"' % f if " " in f else f for f in filenames),
               'options': {'dir': relpath(src_path, src_rst_path)},
               'arg': ''  # not used, but jinja won't complain. Supply a string not None
               }
    return dic


def gen_title(networkname, network_stations_df):
    """Generates the title for the .rst file from a pandas DataFrame returned by
    get_network_stations"""
    # template:
    # =============================================================
    # {{ network_code }} {{ network_start_date }}-{{ network_end_date }}
    # =============================================================
    meta = network_stations_df.metadata
    start = meta['start_date'].year if 'start_date' in meta else None
    end = meta['end_date'].year if 'end_date' in meta else None
    timerange = " %d-%d" % (start, end) if start and end else ""
    title = "%s%s" % (networkname, timerange)
    decorator = "=" * len(title)
    return "%s\n%s\n%s" % (decorator, title, decorator)


def get_net_desc(stations_df):
    """Returns the network description for the .rst file from a pandas DataFrame returned by 
    get_network_stations"""
    return stations_df.metadata['desc']
