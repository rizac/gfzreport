'''
Created on Jan 9, 2017

@author: riccardo
'''
import pandas as pd
import urllib2
import shutil
from glob import glob
import os
import re
from obspy import read_inventory
from cStringIO import StringIO


def relpath(path, reference_path):
    """Almost the same as os.path.relpath but prepends a dot, so the returned value is
        usable in .rst relative paths"""
    return os.path.join(".", os.path.relpath(path, reference_path))


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


def read_network(network, start_after_year, **kwargs):
    """
        Returns all stations  of given network (starting from the specified year)
        from the geofon datacenter in the form of an obspy inventory object
        :param kwargs: keyword arguments optionally to be passed to the query string. Provide any
        fdsn standard *except* 'format', which by default will be set to 'xml', 'level' (which
        will be set to 'channel'), 'network' and 'startafter' (which are mandatory arguments of this
        function)
    """
    kwargs['network'] = network
    kwargs['level'] = 'channel'
    kwargs['startafter'] = start_after_year
    kwargs['format'] = 'xml'
    return read_stations(get_query("http://geofon.gfz-potsdam.de/fdsnws/station/1/query",
                                   **kwargs))


def get_format(query_str):
    """Returns the format argument of query_str (a query in string format), or 'xml' if
    such argument is not found (xml being the FDSN default)"""
    try:
        match = re.compile("[\\?\\&]format=(.*?)(?:\\&|$)").search(query_str)
        if not match:
            return 'text'
        return match.groups()[0]
    except IndexError:
        pass
    return 'xml'


def read_stations(url):
    """Returns an inventory object representing the stations xml file downloaded from url
    if ''format=xml' in url, otherwise a string representing the content read
    (in text format)
    """
    format_ = get_format(url)
    response = None
    try:
        response = urllib2.urlopen(url)
        # Note obspy's read_inventory does not use StringIO's but saves to file
        # (quite inefficient)
        return response.read() if format_ == 'text' else read_inventory(StringIO(response.read()),
                                                                        format='STATIONXML')
    finally:
        if response:
            response.close()
#     if format_ == 'text':
#         response = urllib2.urlopen(url)
#         text = response.read()
#         return text
#     else:
#         return etree.parse(url)


def todf(stations_xml, func, funclevel='station', sortkey=None):
    """
        Converts stations_xml to pandas DataFrame: Loops through the `stations_xml`'s
        network(s), station(s) and channel(s) and executes
        func at the given funclevel
        :param: stations_xml: An obspy station inventory object returned from
        module functions `read_stations` and `read_network`, or, in general, from:
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
        The function accepts a variable number of arguments depending on the `funclevel`
        argument:
          - funclevel='network': `func(network_obj)`,
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
        :param sortkey: Behaves like the python `sorted` 'key` argument: an optional key to be used
        to sort the rows of the resulting Dataframe. It is applied to each dict prior to its
        conversion to a DataFrame row
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
    if sortkey:
        arr.sort(key=sortkey)

    return pd.DataFrame(arr)


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
