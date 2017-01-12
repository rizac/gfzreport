'''
Created on Jan 9, 2017

@author: riccardo
'''
from obspy import read_inventory as rinv
from os.path import join, abspath, dirname
from cStringIO import StringIO
import pandas as pd
from collections import defaultdict as defdict, OrderedDict as odict


def read(filelike, func, funclevel='station', sortkey=None):
    """
        Readw the filelike (or url) stationxml into a dataframe
        :param: filelike: any object which can be passed to obspy.read_inventory: file-like object
        or string. In the latter case, if url, obspy 1.0.2 works as well but in this
        case it creates a temporary file which is quite inefficient, so maybe better to read
        the content beforehand and pass here StringIO(content)
        :param funclevel: string, either 'network', 'station' or 'channel' indicates at which
        level in the xml iteration `func` must be called. Depending on this argument
        `func` will acccept one/two three arguments (network object, network and station objects,
        network, station and channel objects)
        :param func: a function called on each network / station / channel (depending
        on the value of `funclevel`) returning one or more row of the resulting dataframe
        The function accepts a variable number of arguments depending on the `funclevel`
        argument (see above), and returns a list of dicts. Each list element is a row
        of the returned dataframe. Rows must be returned as lists of dicts. Each dict must have
        consistent columns (which will make up the dataframe columns) and relative values
        :param sortkey: an optional key to be used to each row to sort the rows of the resulting
        Dataframe. It is applied to each dict prior to its conversion to a DataFrame row
    """
    inv = rinv(file, format='STATIONXML')
    arr = []
    for net in inv:
        if funclevel == 'network':
            rows = func(net)
            if rows:
                arr.extend(rows)
            continue
        for sta in net:
            if funclevel == 'station':
                rows = func(net, sta)
                if rows:
                    arr.extend(rows)
                continue
            if funclevel == 'channel':
                for cha in sta:
                    rows = func(net, sta, cha)
                    if rows:
                        arr.extend(rows)

    return inv, pd.DataFrame(sorted(arr, key=sortkey))


if __name__ == '__main__':
    file = abspath(join(dirname(__file__), "..", "test-data", "tmp.network.xml"))
    sortfunc= lambda val: val['Name']

    def int_(val):
        ival = int(val)
        return ival if ival == val else val

    def func(net, sta):
        # identify each row by its channel tuple:
        retdict = defdict(odict)
        strfrmt = "%0.4d-%0.2d-%0.2d"
        for cha in sta.channels:
            start = strfrmt % (cha.start_date.year, cha.start_date.month, cha.start_date.day)
            end = strfrmt % (cha.end_date.year, cha.end_date.month, cha.end_date.day)
            id_ = (sta.code, start, end)
            mydic = retdict[id_]
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

    h = read(file, func, 'station', sortfunc)
    print h[1]
    v = 9