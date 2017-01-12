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
# from lxml.etree import XMLSyntaxError
from collections import defaultdict as defdict, OrderedDict as odict
from reportgen.network.generator.core.utils import relpath, read_network, read_stations
from network.generator.core.utils import get_query, todf
from itertools import product, cycle, izip
from reportbuild.map import MapHandler
from lxml.etree import XMLSyntaxError
from collections import defaultdict
# from obspy.core.inventory.inventory import Inventory
# Inventory


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
            mydic['Name'] = sta.code
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

    dframe = todf(inv, func, funclevel='station', sortkey=lambda val: val['Name'])

    # add metadata:
    dframe.metadata = {'start_date': None, 'end_date': None, 'desc': ''}
    for net in inv:
        if net.code == network:
            dframe.metadata['start_date'] = net.start_date
            dframe.metadata['end_date'] = net.end_date
            dframe.metadata['desc'] = net.description
            break

    return dframe

#     try:
#         tree = read_network(network, start_after_year, **kwargs)
# 
# #         kwargs['format'] = 'text'
# #         tree2 = read_network(network, start_after_year, **kwargs)
# #         r = read_inventory(StringIO(tree2), format="STATIONXML")
# 
#         root = tree.getroot()
#         namespaces = {"x": "http://www.fdsn.org/xml/station/1"}
#         stations = root.findall("./x:Network/x:Station", namespaces=namespaces)
# 
#         def getchildtext(element, child_tag):
#             elm = element.find("x:%s" % child_tag, namespaces)
#             if elm is None:
#                 raise ValueError("XmlError: element '%s' has no child '%s'" % (element.tag,
#                                                                                child_tag))
#             return element.find("x:%s" % child_tag, namespaces).text
# 
#         def getatt(element, att):
#             try:
#                 return element.attrib[att]
#             except KeyError:
#                 raise ValueError("XML error: element '%s' has no attribute '%s'" % (element.tag,
#                                                                                     att))
# 
#         columns = ['Name', 'Lat', 'Lon', 'Ele', 'Azi', 'Rate', 'Sensor', 'ID', 'Logger', 'Id',
#                    'Start', 'End', 'Channels']
# 
#         reg = re.compile("\\s*,\\s*")  # regex for chacking if value is already in a column
# 
#         # Note that the "station" row is uniquely identified by station name, channel start date
#         # and channel end date. So build the identifier:
#         rows = {}
#         for sta in stations:
#             sta_name = getatt(sta, 'code')
#             chans = sta.findall("x:Channel", namespaces=namespaces)
# 
#             for cha in chans:
#                 date0 = getatt(cha, 'startDate')
#                 date1 = getatt(cha, 'endDate')
#                 tup = (sta_name, date0, date1)
# 
#                 row = ['']*len(columns)
#                 row[columns.index('Name')] = sta_name
#                 row[columns.index('Start')] = date0[:10]  # quick hack to remove time information
#                 row[columns.index('End')] = date1[:10]  # see above
#                 row[columns.index('Lat')] = getchildtext(cha, "Latitude")
#                 row[columns.index('Lon')] = getchildtext(cha, "Longitude")
#                 row[columns.index('Ele')] = getchildtext(cha, "Elevation")
#                 row[columns.index('Rate')] = getchildtext(cha, "SampleRate")
#                 row[columns.index('Azi')] = getchildtext(cha, "Azimuth")
# 
#                 datalogger = cha.find("x:DataLogger", namespaces=namespaces)
#                 row[columns.index('Id')] = getchildtext(datalogger, "SerialNumber")
#                 row[columns.index('Logger')] = getchildtext(datalogger, "Model")
#                 sensor = cha.find("x:Sensor", namespaces=namespaces)
#                 row[columns.index('ID')] = getchildtext(sensor, "SerialNumber")
#                 row[columns.index('Sensor')] = getchildtext(sensor, "Model")
#                 row[columns.index('Channels')] = getatt(cha, 'code')
# 
#                 row_orig = rows.get(tup, None)
#                 if row_orig is None:
#                     rows[tup] = row
#                 else:
#                     for i, val in enumerate(row_orig):
#                         vals = reg.split(val)
#                         if row[i] not in vals:
#                             row_orig[i] += ", " + row[i]
#                     # row[columns.index('Channels')] += ", " + cha_name
# 
#         net_df = pd.DataFrame(sorted(rows.values(), key=lambda val: val[columns.index('Name')]),
#                               columns=columns)
#         # attach attributes:
#         net_element = root.findall("./x:Network", namespaces=namespaces)[0]
#         atts = {k: net_element.attrib[k] for k in net_element.attrib}
#         # convert dates:
#         for key in atts.keys():  # use keys so that we can modify the dict values
#             if key in ('startDate', 'endDate'):
#                 atts[key] = datetime.strptime(atts[key], '%Y-%m-%dT%H:%M:%S')
#         # attach description
#         desc = root.findall("./x:Network/x:Description", namespaces=namespaces)[0].text
#         net_df.metadata = {'atts': atts, 'desc': desc}
#         return net_df
#     except (URLError, ValueError, XMLSyntaxError) as exc:
#         raise ValueError(exc.__class__.__name__ + ": " + str(exc))


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


def get_other_stations_df(network_stations_df, margins=5):
    tonum = pd.to_numeric
    _, _, minlon, minlat, maxlon, maxlat = \
        MapHandler._calc_bounds(tonum(network_stations_df['Lon']).min(),
                                tonum(network_stations_df['Lat']).min(),
                                tonum(network_stations_df['Lon']).max(),
                                tonum(network_stations_df['Lat']).max(),
                                margins)

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
    dcs = ['http://service.iris.edu/fdsnws/station/1/query',
           'http://www.orfeus-eu.org/fdsnws/station/1/query']

    for dc, kwargs in product(dcs, [kwargs_live_stations, kwargs_dead_stations]):
        print get_query(dc, **kwargs)
        try:
            invs.append(read_stations(get_query(dc, **kwargs)))
        except XMLSyntaxError as exc:
            pass
        # r = read_inventory(StringIO(text), format="STATIONXML")
        # df = pd.read_csv(StringIO(text), delimiter='|', index_col=False)
        # dfs.append(df)

    symbols = cycle([
                     # '.',  # point
                     # ',',  # pixel
                     'o',  # circle
                     'v',  # triangle_down
                     '^',  # triangle_up
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
        mydic['Name'] = sta.code
        mydic['Lat'] = sta.latitude
        mydic['Lon'] = sta.longitude
        mydic['Network'] = net.code
        mydic['Marker'] = marker
        mydic['Caption'] = caption
        mydic['Color'] = color
        return mydic

    dfs = []
    for inv in invs:
        dframe = todf(inv, func, funclevel='station')  # , sortkey=lambda val: val['Name'])
        if not dframe.empty:
            dfs.append(dframe)

    # return stations active in the relative timespan:
    return pd.concat(dfs, axis=0, ignore_index=True, copy=False)


def get_map_df(sta_df, all_sta_df):
    """Returns a DataFrame for the rst map. 
    """
    # current captions are:
    columns = ['Name', 'Lat', 'Lon', 'Marker', 'Color']
    # The first three are common to both dataframes. all_sta_df has all five columns

    # make a new sta_df, it will be a view of the original sta_df. But this way we do not
    # pollute the original
    _sta_df = sta_df[columns[:3]]
    # avoid pandas settingwithcopy warnings (we know what we are doing):
    _sta_df.is_copy = False

    _sta_df['Marker'] = 's'  # square
    sensors = pd.unique(sta_df['Sensor'])

    # create a variable color scale
    step = 255.0 / (len(sensors)+1)
    # set a scale of reds in html. Use "#00%s00" for scale of green, "#%s%s00" for yellow scale, etc
    colors = ["#%s0000" % hex(int(step*(i+1)))[2:].upper().zfill(2) for i in xrange(len(sensors))]

    _sta_df['Color'] = ''
    for sens, col in izip(sensors, colors):
        _sta_df.loc[sta_df['Sensor'] == sens, 'Color'] = col

    return pd.concat([_sta_df, all_sta_df], axis=0, ignore_index=True, copy=False)[columns]


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
