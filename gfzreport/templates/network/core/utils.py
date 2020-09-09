'''
Created on Jan 9, 2017

@author: riccardo
'''
import pandas as pd
import urllib2
import os
import re
from obspy import read_inventory
from io import BytesIO

def relpath(path, reference_path):
    """Almost the same as os.path.relpath but prepends a "./", so the returned value is
        usable in .rst relative paths"""
    return os.path.join(".", os.path.relpath(path, reference_path))


def read_geofonstations(network, start_after_year, **kwargs):
    """Returns an inventory object representing the stations xml file of a given **geofon**
        network
       :param network: string, denoting the network
       :param start_after_year: an integer denoting the year to start from when
       searching for the network stations
       :param kwargs: keyword arguments optionally to be passed to the query string. Provide any
       fdsn standard *except* 'format', which by default will be set to 'xml', 'level' (which
       will be set to 'channel'), 'network' and 'startafter' (which are mandatory arguments of this
       function)
    """
    kwargs['network'] = network
    kwargs['level'] = 'channel'
    kwargs['startafter'] = start_after_year
    return read_stations(get_query("http://geofon.gfz-potsdam.de/fdsnws/station/1/query",
                                   **kwargs))


def read_stations(url, timeout=None):
    """Returns an inventory object representing the stations xml file downloaded from the
    given url
    :param timeout: the value of the timeout passed to `urllib2`. None defaults to the
    library default
    """
    # format_ = get_format(url)
    response = None
    try:
        response = urllib2.urlopen(url) if timeout is None else \
            urllib2.urlopen(url, timeout=timeout)
        got = response.read()
        if ((response.code == 204) and (len(got) == 0)):
            return None  # Or what???
        return read_inventory(BytesIO(got), format='STATIONXML')
#         return response.read() if format_ == 'text' else read_inventory(BytesIO(response.read()),
#                                                                         format='STATIONXML')
    finally:
        if response:
            response.close()


def todf(stations_xml, func, funclevel='station', sortby=None):
    """
        Converts stations_xml to pandas DataFrame: Loops through the `stations_xml`'s
        network(s), station(s) and channel(s) and executes
        func at the given funclevel
        :param: stations_xml: An obspy inventory object returned from
        module functions `read_stations` and `read_geofonstations`, or, in general, from:
        ```
            obspy.read_inventory(..., format='STATIONSXML')
        ```
        :param func: a function called on each network / station / channel (depending
        on the value of `funclevel`) returning a row of the resulting dataframe as dictionary
        (the dictionary keys will make up the DataFrame columns).
        Everything not instance of `dict` will be interpreted as an iterable of
        `dict`s, so that one can return e.g. a list of N `dict`s to add new N rows.
        Everything evaluating to False (empty dict, empty iterable, empty dicts of an iterable)
        will be skipped and not added to the DataFrame.
        The `func` argument accepts a variable number of arguments depending on the `funclevel`
        argument:
          - funclevel='network': `func(network_obj)`
          - funclevel='station': `func(network_obj, station_obj)`
          - funclevel='channel': `func(network_obj, station_obj, channel_obj)`
        Note: if you want to preserve the column orders as declared in each returned dict,
        you can use and return `collections.OrderedDict`'s).
        No error should be raised if the number of columns is inconsistent across dict's or their
        order differs, but the result has not been tested (please have a look at pandas DataFrame).
        :param funclevel: string, either 'network', 'station' or 'channel' indicates at which
        level in the xml iteration `func` must be called. Depending on this argument
        `func` will acccept one/two/three arguments:
          - funclevel='network': `func(network_obj)`,
          - funclevel='station': `func(network_obj, station_obj)`
          - funclevel='channel': `func(network_obj, station_obj, channel_obj)`
        :param sortkey (str or list of str): Behaves like the pandas 'by` argument to sort the
        dataframe before returning it: its the name(s) of the column(s) to sort by. If None
        (default when missing) no sort takes place
    """
    arr = []

    def add(val):
        """Function executing `list.add` or `list.extend` depending on `val` argument"""
        if not val:
            return
        if isinstance(val, dict):
            arr.append(val)
        else:
            arr.extend((v for v in val if v))

    for net in stations_xml:
        if funclevel == 'network':
            add(func(net))
            continue
        for sta in net:
            if funclevel == 'station':
                add(func(net, sta))
                continue
            if funclevel == 'channel':
                for cha in sta:
                    add(func(net, sta, cha))

    ret_df = pd.DataFrame(arr)
    if sortby:
        ret_df.sort_values(by=sortby, inplace=True)

    return ret_df


def get_query(*urlpath, **query_args):
    """Joins urls and appends to it the query string obtained by kwargs
    Note that this function is intended to be simple and fast: No check is made about white-spaces
    in strings, no encoding is done, and if some value of `query_args` needs special formatting
    (e.g., "%1.1f"), that needs to be done before calling this function
    :param urls: portion of urls which will build the query url Q. For more complex url functions
    see `urlparse` library: this function builds the url path via a simple join stripping slashes:
    ```'/'.join(url.strip('/') for url in urlpath)```
    So to preserve slashes (e.g., at the beginning) pass "/" or "" as arguments (e.g. as first
    argument to preserve relative paths).
    :query_args: keyword arguments which will build the query string
    :return: a query url built from arguments

    :Example:
    ```
    >>> get_query("http://www.domain", start='2015-01-01T00:05:00', mag=5.455559, arg=True)
    'http://www.domain?start=2015-01-01T00:05:00&mag=5.455559&arg=True'

    >>> get_query("http://www.domain", "data", start='2015-01-01T00:05:00', mag=5.455559, arg=True)
    'http://www.domain/data?start=2015-01-01T00:05:00&mag=5.455559&arg=True'

    # Note how slashes are handled in urlpath. These two examples give the same url path:

    >>> get_query("http://www.domain", "data")
    'http://www.domain/data?'

    >>> get_query("http://www.domain/", "/data")
    'http://www.domain/data?'

    # leading and trailing slashes on each element of urlpath are removed:

    >>> get_query("/www.domain/", "/data")
    'www.domain/data?'

    # so if you want to preserve them, provide an empty argument or a slash:

    >>> get_query("", "/www.domain/", "/data")
    '/www.domain/data?'

    >>> get_query("/", "/www.domain/", "/data")
    '/www.domain/data?'
    ```
    """
    # http://stackoverflow.com/questions/1793261/how-to-join-components-of-a-path-when-you-are-constructing-a-url-in-python
    return "{}?{}".format('/'.join(url.strip('/') for url in urlpath),
                          "&".join("{}={}".format(k, v) for k, v in query_args.iteritems()))


def iterdcurl(**query_args):
    """Returns an iterator over all datacenter urls found in the eida routing service, plus
    iris station ws url
    :param query_args: optional set of **eida routing service keyword arguments** which will be
    appended to the query url. Note that the arguments are not 100% the same as the fdsn arguments
    (for instance, endbefore is not supported), so please use only arguments valid in both cases.
    Note also that 'service' and 'format' keyword arguments, if supplied, will be overridden with
    values 'station' and 'post', respectively.
    For IRIS, due to a bug in the eida routing service, the arguments will be forwarded to the IRIS
    station web service, so they need to be
    valid fdsn arguments. The IRIS datacenter is yielded if the station web service response
    returns at least one byte, otherwise not
    """
    query_args['service'] = 'station'
    query_args['format'] = 'post'
    query = get_query('http://geofon.gfz-potsdam.de/eidaws/routing/1/query', **query_args)

    url_open = urllib2.urlopen(query)
    try:
        dc_result = url_open.read().decode('utf8') or u''
    finally:
        url_open.close()

    # 1) parse dc_result string and assume any new line starting with http:// is a valid station
    # query url
    # do not use split so we do not create an array but let's yield it
    last_idx = 0
    lastcharidx = len(dc_result) - 1
    for i, char in enumerate(dc_result):
        if char in (u'\n', u'\r') or i == lastcharidx:
            if dc_result[last_idx:last_idx+7] == u"http://":
                yield dc_result[last_idx:i]
            last_idx = i + 1

    # return IRIS manually. Do a simple query as long as we get one byte, stop the connection
    # and return the url
    iris_url = "http://service.iris.edu/fdsnws/station/1/query"
    # delete / modify eida routing service specific arguments
    del query_args['service']
    query_args['format'] = 'text'
    query_args['level'] = 'station'
    query = get_query(iris_url, **query_args)
    url_open = urllib2.urlopen(query)
    try:
        dc_result = url_open.read(1)
        if dc_result:
            yield iris_url
    finally:
        url_open.close()
    # (fix bug in eida routing service when querying without network arguments):


def sortchannels(channels, inplace=False):
    # sort according to http://www.fdsn.org/seed_manual/SEEDManual_V2.4_Appendix-A.pdf (pag.124):
    orientations = ['Z', 'N', 'E', 'A', 'B', 'C', 'T', 'R', '1', '2', '3', 'U', 'V', 'W']
    dct = {o: i for i, o in enumerate(orientations)}
    max_ = len(dct)

    def keyfunc(channel):
        return hash(channel[:-1]) + dct.get(channel[-1], max_)

    if inplace and isinstance(channels, list):
        channels.sort(key=keyfunc)
    else:
        channels = sorted(channels, key=keyfunc)
    return channels

