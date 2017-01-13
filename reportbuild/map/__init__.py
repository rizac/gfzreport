'''
This module implements the function `plotmap` which plots scattered points on a geographic
map. The function is highly customizable and is basically a wrapper around the
Basemap library (for the map background) plus matplotlib utilities (for plotting points, shapes,
labels and legend)

Created on Mar 10, 2016

@author: riccardo
'''
import numpy as np
import re
from itertools import izip
from urllib2 import URLError, HTTPError
import socket
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
from mpl_toolkits.basemap import Basemap


def parse_margins(obj, parsefunc=lambda margins: [float(val) for val in margins]):
    """Parses obj returning a 4 element numpy array denoting the top, right, bottom and left
    values.This function first converts obj to a 4 element list L, and then 
    calls `parsefunc`, which by default converts all L values into float
    :param obj: either None, a number, a list of numbers (allowed lengths: 1 to 4),
    a comma/semicolon/spaces separated string (e.g. "4deg 0.0", "1, 1.2", "2km,4deg", "1 ; 2")
    :param parsefunc: a function to be applied to obj converted to list. By default, returns
    float(v) for any v in L
    :return: a 4 element numpy array of floats denoting the top, right, bottom, left values of
    the margins. The idea is the same as css margins, as depicted in the table below.
    :Examples:
        Called f `parsefunc`, then:
        ============= =========================
        obj is     returns
        ============= =========================
        None          [0, 0, 0, 0]
        ------------- -------------------------
        string        the list obtained after
                      splitting string via
                      regexp where comma,
                      semicolon and spaces
                      are valid separators
        ------------- -------------------------
        x or [x]      parsefunc([x, x, x, x])
        ------------- -------------------------
        [x, y]        parsefunc([x, y ,x, y])
        ------------- -------------------------
        [x, y, z]     parsefunc([x, y, z, y])
        ------------- -------------------------
        [x, y, z, t]  parsefunc([x, y, z, t])
        ============= =========================
    """
    if obj is None:
        margins = [0] * 4
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        # is an iterable not string. Note the if above is py2 py3 compatible
        margins = list(obj)
    else:
        margins = re.compile("(?:\\s*,\\s*|\\s*;\\s*|\\s+)").split(obj)

    if len(margins) == 1:
        margins *= 4
    elif len(margins) == 2:
        margins *= 2
    elif len(margins) == 3:
        margins.append(margins[1])
    elif len(margins) != 4:
        raise ValueError("unable to parse margins on invalid value '%s'" % obj)

    return np.asarray(parsefunc(margins))
    # return margins


def parse_distance(dist, lat_0=None):
    """Returns the distance in degrees. If dist is in km or m, and lat_0 is not None,
    returns w2lon, else h2lat. dist None defaults to 0
    :param dist: float, int None, string. If string and has a unit, see above
    """
    try:
        return 0 if dist is None else float(dist)
    except ValueError:
        if dist[-3:].lower() == 'deg':
            return float(dist[:-3])
        elif dist[-2:] == 'km':
            dst = 1000 * float(dist[:-2])
        elif dist[-1:] == 'm':
            dst = float(dist[:1])
        else:
            raise

        return w2lon(dst, lat_0) if lat_0 is not None else h2lat(dst)


def get_lon0_lat0(min_lons, min_lats, max_lons, max_lats):
    """ Calculates lat_0, lon_0, i.e., the mid point of the bounding box denoted by the
    arguments
    :param min_lons: the minimum of longitudes
    :param min_lats: the maximum of latitudes
    :param max_lons: the minimum of longitudes
    :param max_lats: the maximum of latitudes
    :return: the 2-element tuple denoting the mid point lon_0, lat_0
    """
    lat_0 = max_lats / 2. + min_lats / 2.
    lon_0 = max_lons / 2. + min_lons / 2.
    if lon_0 > 180:  # FIXME: necessary?? see self.get_normalized... above
        lon_0 -= 360
    return lon_0, lat_0


def mapbounds(min_lon, min_lat, max_lon, max_lat, margins):
    """Calculates the bounds given the bounding box identified by the arguments and
    given optional margins
    :param min_lon: the minimum longitude (numeric, scalar)
    :param min_lat: the maximum latitude (numeric, scalar)
    :param max_lon: the minimum longitude (numeric, scalar)
    :param max_lat: the maximum latitude (numeric, scalar)
    :param margins: the margins as a css-like string (with units 'deg', 'km' or 'm'), or as
    a 1 to 4 element array of numeric values (in that case denoting degrees).
    As in css, a 4 element array denotes the [top, right, bottom, left] values.
    None defaults to [0, 0, 0, 0].
    :return: the 6-element tuple denoting lon_0, lat_0, min_lon, min_lat, max_lon, max_lat.
    where min_lon, min_lat, max_lon, max_lat are the new bounds and lon_0 and lat_0 are
    their midpoints (x and y, respectively)
    """

    def parsefunc(mrgns):
        """parses mrgns as array of strings into array of floats
        """
        return parse_distance(mrgns[0]), parse_distance(mrgns[1], max_lat), \
            parse_distance(mrgns[2]), parse_distance(mrgns[3], min_lat)

    top, right, btm, left = parse_margins(margins, parsefunc)
    min_lon, min_lat, max_lon, max_lat = min_lon-left, min_lat-btm, max_lon+right, max_lat+top

    if min_lon == max_lon:
        min_lon -= 10  # in degrees
        max_lon += 10  # in degrees

    if min_lat == max_lat:
        min_lat -= 10  # in degrees
        max_lat += 10  # in degrees

    # minima must be within bounds:
    min_lat = max(-90, min_lat)
    max_lat = min(90, max_lat)
    min_lon = max(-180, min_lon)
    max_lon = min(180, max_lon)

    lon_0, lat_0 = get_lon0_lat0(min_lon, min_lat, max_lon, max_lat)
    return lon_0, lat_0, min_lon, min_lat, max_lon, max_lat


# static constant converter (degree to meters and viceversa) for latitudes
DEG2M_LAT = 2 * np.pi * 6371 * 1000 / 360


def lat2h(distance_in_degrees):
    """converts latitude distance from degrees to height in meters
    :param distance_in_degrees: a distance (python scalar or numpy array) along the great circle
    espressed in degrees"""
    deg2m_lat = DEG2M_LAT  # 2 * np.pi * 6371 * 1000 / 360
    return distance_in_degrees * deg2m_lat


def h2lat(distance_in_meters):
    """converts latitude distance from height in meters to degrees
    :param distance_in_degrees: a distance  (python scalar or numpy array) along the great circle
    espressed in degrees"""
    deg2m_lat = DEG2M_LAT  # deg2m_lat = 2 * np.pi * 6371 * 1000 / 360
    return distance_in_meters / deg2m_lat


def lon2w(distance_in_degrees, lat_0):
    """converts longitude distance from degrees to width in meters
    :param distance_in_degrees: a distance  (python scalar or numpy array)
    along the lat_0 circle expressed in degrees
    :param lat_0: if missing or None, defaults to the internal lat_0, which is set as the mean
    of all points passed to this object. Otherwise, expresses the latitude of the circle along
    which the lon2w(distance_in_degrees) must be converted to meters"""
    deg2m_lat = DEG2M_LAT
    deg2m_lon = deg2m_lat * np.cos(lat_0 / 180 * np.pi)
    return distance_in_degrees * deg2m_lon


def w2lon(distance_in_meters, lat_0):
    """converts longitude distance from width in meters to degrees
    :param distance_in_meters: a distance  (python scalar or numpy array)
    along the lat_0 circle expressed in meters
    :param lat_0: if missing or None, defaults to the internal lat_0, which is set as the mean
    of all points passed to this object. Otherwise, expresses the latitude (in degrees) of the
    circle along which w2lon(distance_in_meters) must be converted to degrees"""
    deg2m_lat = DEG2M_LAT  # deg2m_lat = 2 * np.pi * 6371 * 1000 / 360
    deg2m_lon = deg2m_lat * np.cos(lat_0 / 180 * np.pi)
    return distance_in_meters / deg2m_lon


class MapHandler(object):
    """
        Class handling bounds of a map given points (lons and lats)
    """
    def __init__(self, lons, lats, map_margins):
        """Initializes a new MapHandler. If figure here is None, you **MUST**
        call self.set_fig(fig) to calculate bounds and other stuff
        when you have a ready figure"""
        self.lons = lons if len(lons) else [0]  # FIXME: use numpy arrays!!
        self.lats = lats if len(lats) else [0]
        self.max_lons, self.min_lons = max(self.lons), min(self.lons)
        self.max_lats, self.min_lats = max(self.lats), min(self.lats)
        self.lon_0, self.lat_0, self.llcrnrlon, self.llcrnrlat, self.urcrnrlon, self.urcrnrlat = \
            mapbounds(self.min_lons, self.min_lats, self.max_lons, self.max_lats, map_margins)

    def _get_map_dims(self):  # , fig_size_in_inches, colorbar=False):
        """Returns the map dimension width, height, in meters"""

        max_lons, min_lons = self.urcrnrlon, self.llcrnrlon
        max_lats, min_lats = self.urcrnrlat, self.llcrnrlat
        height = lat2h(max_lats - min_lats)
        width = lon2w(max_lons - min_lons, self.lat_0)
        return width, height

    def get_parallels(self, max_labels_count=8):
        width, height = self._get_map_dims()
        lat_0 = self.lat_0
        N1 = int(np.ceil(height / max(width, height) * max_labels_count))
        parallels = MapHandler._linspace(lat_0 - h2lat(height / 2),
                                         lat_0 + h2lat(height / 2), N1)
        return parallels

    def get_meridians(self, max_labels_count=8):
        width, height = self._get_map_dims()
        lon_0 = self.lon_0
        lat_0 = self.lat_0
        N2 = int(np.ceil(width / max(width, height) * max_labels_count))
        meridians = MapHandler._linspace(lon_0 - w2lon(width / 2, lat_0),
                                         lon_0 + w2lon(width / 2, lat_0), N2)
        meridians[meridians > 180] -= 360
        return meridians

    @staticmethod
    def _linspace(val1, val2, N):
        """
        returns around N 'nice' values between val1 and val2. Copied from obspy.plot_map
        """
        dval = val2 - val1
        round_pos = int(round(-np.log10(1. * dval / N)))
        # Fake negative rounding as not supported by future as of now.
        if round_pos < 0:
            factor = 10 ** (abs(round_pos))
            delta = round(2. * dval / N / factor) * factor / 2
        else:
            delta = round(2. * dval / N, round_pos) / 2
        new_val1 = np.ceil(val1 / delta) * delta
        new_val2 = np.floor(val2 / delta) * delta
        N = (new_val2 - new_val1) / delta + 1
        return np.linspace(new_val1, new_val2, N)


def normalize_arg(obj, size=None, dtype=None):
    """"Casts" obj to a numpy array of the given optional size and optional dtype, and returns it.
    If size is not None, the array must have length size. If not, and has length 1, it will be
    resized to the specified size. Otherwise a ValueError is raised
    If size is None, no resize will be in place and the array is returend as it is
    Note: obj=None will be converted to the array [None], apparently in the current version of numpy
    this wouldn't be the default (see argument ndmin=1)
    :return an numpy array resulting to the coinversion of obj into array
    :Examples:
    """
    x = np.array(obj, ndmin=1) if dtype is None else np.array(obj, ndmin=1, dtype=dtype)
    if size is None:
        return np.array([]) if obj is None else x  # if obj is None x is [None], return [] instead
    try:
        if len(x) == 1:
            x = np.resize(x, size)
        elif len(x) != size:
            raise ValueError("invalid array length: %d. Expected %d" % (len(x), size))
    except (ValueError, TypeError) as _err:
        raise ValueError(str(_err))

    return x


def torgba(html_str):
    """Converts html_str into a tuple of rgba colors in 0, 255 if alpha channel is not
    specified, or [0,1] otherwise
    :param html_str: a valid html string in hexadecimal format.
    Can have length 4, 7 or 9 such as #F1a, #fa98e3, #fc456a09
    :return: a rgba vector, i.e. a 4-element numpy array of values in [0,1] denoting `html_str`
    :raise: ValueError if html_str is invalid
    """
    if len(html_str) not in (4, 7, 9) or not html_str[0] == '#':
        raise ValueError("'%s' invalid html string" % html_str)
    elif len(html_str) == 4:
        rgb = [html_str[i:i+1]*2 for i in xrange(1, len(html_str))]
    else:
        rgb = [html_str[i:i+2] for i in xrange(1, len(html_str), 2)]

    if len(rgb) == 3:
        rgb += ['FF']

    return np.true_divide(np.array([int(r, 16) for r in rgb]), 255)


def parseargs(lons, lats, labels, sizes, colors, markers, legend_labels):
    lons = normalize_arg(lons, dtype=float)  # basically: convert to float array if scalar (size=0)
    lats = normalize_arg(lats, dtype=float)  # basically: convert to float array if scalar (size=0)
    if len(lons) != len(lats):
        raise ValueError('mismatch in lengths: lons (%d) and lats (%d)' % (len(lons), len(lats)))
    leng = len(lons)
    labels = normalize_arg(labels, size=leng)
    colors = normalize_arg(colors, size=leng)
    markers = normalize_arg(markers, size=leng)
    legend_labels = normalize_arg(legend_labels, size=leng)
    # colors[np.isnan(colors) | (colors <= 0)] = 1.0  # nan colors default to 1 (black?)
    sizes = normalize_arg(sizes, size=leng, dtype=float)
    valid_points = np.logical_not(np.isnan(lons) | np.isnan(lats) | (sizes <= 0))

    # convert html strings to rgba if the former are in string format:
    # the loop below is quite inefficient but we cannot help it, unless vectorization on string
    # is possible (but then we would return arrays, and this raises ValueError
    if colors.dtype.char in ('U', 'S'):
        colors = np.array([torgba(c) for c in colors])

    # return all points whose corresponding numeric values are not nan:
    return (lons[valid_points],
            lats[valid_points],
            labels[valid_points],
            sizes[valid_points],
            colors[valid_points],
            markers[valid_points],
            legend_labels[valid_points])


# def get_ax_size(ax, fig):
#     bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
#     return bbox.width, bbox.height

def pix2inch(pix, fig):
    """Converts pixel to inches on a given matplotlib figure"""
    return pix / fig.dpi


def inch2pix(inch, fig):
    """Converts inches to pixel on a given matplotlib figure"""
    return inch * fig.dpi 


# values below CAN be None but CANNOT be arrays containing None's
def plotmap(lons,
            lats,
            labels=None,
            legend_labels=None,
            sizes=20,
            colors="#FF4400",  # can be scalar (including None or nan) or array. Note can also be rgba in html format. matplotlib does support this only for 4 elements arrays, but we will convert it
            markers="^",
            fontsize=None,
            fig_margins="2",  # nunmeric None (=0) or float-parsable string, in font height units!!
            labels_text_weight='regular',
            labels_text_color='k',
            labels_text_contour_width=0,  # set to zero for no contour
            labels_text_contour_color='white',
            labels_h_offset=None,  # None defaults to 0, type a string with units as 'm', 'km' or 'deg'. No unit (or number) defaults to deg
            labels_v_offset=None,  # None defaults to 0, type a string with units as 'm', 'km' or 'deg'. No unit (or number) defaults to deg
            map_margins='0.5deg',  # None defaults to [0,0,0,0], is like css margins but units are km, m or deg. (no unit defaults to deg)
            epsg_projection='3857',  # 4326,  # 3395,  # 3857,
            arcgis_image_service='World_Street_Map',  # 'ESRI_Imagery_World_2D', 'World_Topo_Map', 'World_Terrain_Base'
            arcgis_image_xpixels=1500,
            arcgis_image_dpi=96,
            urlfail='ignore',  # ignore or raise
            num_max_meridians=5,  # set to 0 to disable meridians AND tick labels
            meridians_linewidth=1.,  # set to 0 to disable meridians (tick labels shown)
            num_max_parallels=5,  # set to 0 to disable parallels AND tick labels
            parallels_linewidth=1.,  # set to 0 to disable parallels (tick labels shown)
            legend_loc='bottom',  # top bottom right left
            legend_fancybox=True,
            legend_shadow=True,
            legend_borderaxespad=1.5,  # in font units
            title=None,
            show=False,
            fig=None,
            **kwargs):  # @UnusedVariable
    """
    Plots a map with optional scatter points. In the following, with the term 'array' we denote
    either a numpy array or a list/tuple.
    Scatter points will be identified by the arrays `lons` and `lats`, whose length L must be equal.
    If numeric, they will be converted to a single element array.
    All other arguments related to scatter points (`labels`, `legend_labels`, `sizes`, `colors`,
    `markers`) behave as many matplotlib arguments, i.e. they are supposed to be arrays of length
    L or, if they denote a single value, they will be internally converted to an array with the
    value repeated L times.
    :param lons: (numeric array or scalar) Longitudes of the data points
    :param lats: (numeric array or scalar) Latitudes of the data points.
    Must be the same length as lons
    :param labels: (array of strings or string. Default: None, no labels) Annotations (labels)
    for the individual data points on the map
    :param legend_labels: (array of strings or string. Default: None, no legend) Annotations
    (labels) for the legend. You can supply a sparse array where only some points (will relative
    marker and color) will be displayed on the legend. All other values can be None or empty string
    :param sizes: (numeric array or scalar. Default: 10) Sizes of the
    individual points in the scatter plot.
    :param colors: (array of strings, string, or array of 3-4 element tuples. Default: "#FF4400")
    Colors for the scatter points (fill color). The argument is the same as `matplotlib.scatter`
    color argument. You can type color transparency by supplying string of 9 elements wher
    the last two characters denote the transparency ('00' fully transparent, 'ff' fully opaque).
    Note that this is a feature not implemented in current `matplotlib`
    :param markers: (array of strings or string. Default "^"): The markers (shapes) of the scatter
    point. Please have a look at `matplotlib` documentation for available symbols
    
    :param labels_text_weight: string (default: 'normal'). A numeric value in range 0-1000 or
        'ultralight' or 'light' or 'normal' or 'regular' or 'book' or 'medium' or 'roman' or
        'semibold' or 'demibold' or 'demi' or 'bold' or 'heavy' or 'extra bold' or 'black'
    :param labels_text_color: (default 'k'). Single letters ('b', 'g', 'r', 'c', 'm', 'y',
        'k'=black, 'w'), rgb tuple (1, 0.6, 0), html colors ('#EEFF65' but also legal html names
        for colors, like 'red', 'burlywood', or an integer in [0,1] to specify gray shades (0=black)
    :param labels_text_contour_width: (default: 1). Width in points, 0 avoids painting it
    :param labels_text_contour_color: (default 'white'). The labels contour color. Set to None
        to skip painting contour. For the options, see ref:`labels_text_colors`
    :param margins_in_km: (default 50km) the margins in km of the map bbox, calculated according to
        the points lats and lons. Can be specified as css margin property, separating values
        with commas or spaces, and with units which can be 'deg', 'm' or 'km'
    :param epsg_projection: (default: '4326') the map projection. FIXME: see?  # 4326,# 3395,# 3857,
    :param arcgis_image_service: (default 'ESRI_Imagery_World_2D'). FIXME: see?  # 'ESRI_StreetMap_World_2D'
    :param arcgis_image_xpixels: (default 1500). FIXME: see?
    :param arcgis_image_dpi: (default 96). FIXME: see?
    :param num_max_meridians: (default: 5). Set to zero to avoid plotting meridians at all
        (including axis ticks)
    :param meridians_linewidth: (default 1.). Set to zero to avoid showing meridians lines on the
        map
    :param num_max_parallels: (default: 5). Set to zero to avoid plotting meridians at all
        (including axis ticks)
    :param parallels_linewidth: (default: 1.). Set to zero to avoid showing parallels lines on the
        map
    :param title: Title above plot
    :type title: str
    :param show: Whether to show the figure after plotting or not. Can be used
        to do further customization of the plot before showing it.
    :type show: bool
    :param fig: Figure instance to reuse, returned from a previous
        :func:`plot_basemap` call. If a previous basemap plot is reused, any
        kwargs regarding the basemap background will be ignored.
        In other words, only points will be printed. This functionality has not been tested yet
    :type fig: :class:`matplotlib.figure.Figure`. You can access the basemap with fig.bmap

    """
    lons, lats, labels, sizes, colors, markers, legend_labels =\
        parseargs(lons, lats, labels, sizes, colors, markers, legend_labels)

    if fig is None:
        fig = plt.figure()
        map_ax = fig.add_axes([0, 0, 1, 1])  # set axes size the same as figure

        # setup handler for managing basemap coordinates and meridians / parallels calculation:
        handler = MapHandler(lons, lats, map_margins)
        bmap = Basemap(llcrnrlon=handler.llcrnrlon,
                       llcrnrlat=handler.llcrnrlat,
                       urcrnrlon=handler.urcrnrlon,
                       urcrnrlat=handler.urcrnrlat,
                       epsg=epsg_projection,
                       resolution='i',
                       ax=map_ax)

        try:
            # set the map image via a map service. In case you need the returned values, note that
            # This function returns an ImageAxis (or AxisImage, check matplotlib doc)
            bmap.arcgisimage(service=arcgis_image_service, xpixels=arcgis_image_xpixels,
                             dpi=arcgis_image_dpi, verbose=True)
        except (URLError, HTTPError, socket.error) as exc:
            # failed, maybe there is not internet connection
            if urlfail == 'ignore':
                # Print a simple map offline
                bmap.drawcoastlines()
                watercolor = '#4444bb'
                bmap.fillcontinents(color='#eebb66', lake_color=watercolor)
                bmap.drawmapboundary(fill_color=watercolor)
            else:
                raise

        if num_max_parallels:
            parallels = handler.get_parallels(num_max_parallels)
            # Old basemap versions have problems with non-integer parallels.
            try:
                bmap.drawparallels(parallels, labels=[0, 1, 1, 0], linewidth=parallels_linewidth,
                                   fontsize=fontsize)
            except KeyError:
                parallels = sorted(list(set(map(int, parallels))))
                bmap.drawparallels(parallels, labels=[0, 1, 1, 0], linewidth=parallels_linewidth,
                                   fontsize=fontsize)

        if num_max_meridians:
            meridians = handler.get_meridians(num_max_meridians)
            bmap.drawmeridians(meridians, labels=[1, 0, 0, 1], linewidth=meridians_linewidth,
                               fontsize=fontsize)

        fig.get_axes()[0].tick_params(direction='out', length=15)
        fig.bmap = bmap
    else:  # FIXME: branch not tested!!!
        error_message_suffix = (
            ". Please provide a figure object from a previous call to the "
            ".plot() method of e.g. an Inventory or Catalog object.")
        try:
            map_ax = fig.axes[0]
        except IndexError as e:
            e.args = tuple([e.args[0] + error_message_suffix] +
                           list(e.args[1:]))
            raise
        try:
            bmap = fig.bmap
        except AttributeError as e:
            e.args = tuple([e.args[0] + error_message_suffix] +
                           list(e.args[1:]))
            raise

    # compute the native bmap projection coordinates for events.

    # from the docs (this is kind of outdated, however leave here for the moment):
    # Calling a Basemap class instance with the arguments lon, lat will
    # convert lon/lat (in degrees) to x/y map projection
    # coordinates (in meters).  If optional keyword ``inverse`` is
    # True (default is False), the inverse transformation from x/y
    # to lon/lat is performed.

    # For cylindrical equidistant projection (``cyl``), this
    # does nothing (i.e. x,y == lon,lat).

    # For non-cylindrical projections, the inverse transformation
    # always returns longitudes between -180 and 180 degrees. For
    # cylindrical projections (self.projection == ``cyl``,
    # ``cea``, ``mill``, ``gall`` or ``merc``)
    # the inverse transformation will return longitudes between
    # self.llcrnrlon and self.llcrnrlat.

    # Input arguments lon, lat can be either scalar floats,
    # sequences, or numpy arrays.

    # parse hoffset and voffset and assure they are at least arrays of 1 elements
    # (for aligning text labels, see below)
    hoffset = np.array(parse_distance(labels_h_offset, lats), copy=False, ndmin=1)
    voffset = np.array(parse_distance(labels_v_offset), copy=False, ndmin=1)
    lbl_lons = lons + hoffset
    lbl_lats = lats + voffset

    # convert labels coordinates:
    xlbl, ylbl = bmap(lbl_lons, lbl_lats)

    # plot point labels
    max_points = -1  # negative means: plot all
    if max_points < 0 or len(lons) < max_points:

        # set arguments
        kwargs = {
                  "weight": labels_text_weight,
                  "color": labels_text_color,
                  }
        if labels_text_contour_width > 0 and labels_text_contour_color is not None:
            kwargs['path_effects'] = [PathEffects.withStroke(linewidth=labels_text_contour_width,
                                                             foreground=labels_text_contour_color)]

        # this is copied from obspy code. There is no mention about the reason though
        if len(lons) > 1:
            kwargs['zorder'] = 100

        kwargs['fontsize'] = fontsize

        # adjust text ref. corner:
        # from (FIXME: add ref?)
        # horizontalalignment controls whether the x positional argument for the text indicates
        # the left, center or right side of the text bounding box.
        # verticalalignment controls whether the y positional argument for the text indicates
        # the bottom, center or top side of the text bounding box.
        # multialignment, for newline separated strings only, controls whether the different lines
        # are left, center or right justified
        kwargs['horizontalalignment'] = 'left' if hoffset[0] > 0 else 'right' if \
            hoffset[0] < 0 else 'center'
        kwargs['multialignment'] = kwargs['horizontalalignment']
        kwargs['verticalalignment'] = 'top' if voffset[0] > 0 else 'bottom' if \
            voffset[0] < 0 else 'center'

        for name, xpt, ypt in zip(labels, xlbl, ylbl):
            # Check if the point can actually be seen with the current bmap
            # projection. The bmap object will set the coordinates to very
            # large values if it cannot project a point.
            if xpt > 1e25:
                continue
            map_ax.text(xpt, ypt, name, **kwargs)

    # plot points
    x, y = bmap(lons, lats)
    # store handles to points, and relative labels, if any
    leg_handles, leg_labels = [], []
    # bmap.scatter accepts all array-like args except markers. Avoid several useless loops
    # and do only those for distinct markers:
    mrks = np.unique(markers)
    for mrk in mrks:
        # markers == mrk fails if mrk is None. np.equal fails on non numeric data. So:
        m_mask = np.equal(markers, mrk) if mrk is None else markers == mrk
        __x = x[m_mask]
        __y = y[m_mask]
        __m = mrk
        __s = sizes[m_mask]
        __c = colors[m_mask]
        __l = legend_labels[m_mask]
        if not __l.any():
            __l = np.array([None])  # use all of them in a run
        for leg in np.unique(__l):
            l_mask = np.equal(__l, leg) if leg is None else __l == leg  # see note on m_mask above
            _scatter = bmap.scatter(__x[l_mask],
                                    __y[l_mask],
                                    marker=mrk,
                                    s=__s[l_mask],
                                    c=__c[l_mask],
                                    zorder=10)
            if leg:
                leg_handles.append(_scatter)
                leg_labels.append(leg)

    if leg_handles:
        # we do have legend to show. Adjust legend reference corner:
        if legend_loc == 'bottom':
            loc = 'upper center'
            bbox_to_anchor = (0.5, -0.05)
        elif legend_loc == 'top':
            loc = 'lower center'
            bbox_to_anchor = (0.5, 1.05)
        elif legend_loc == 'left':
            loc = 'center right'
            bbox_to_anchor = (-0.05, 0.5)
        elif legend_loc == 'right':
            loc = 'center left'
            bbox_to_anchor = (1, 0.5)

        # http://stackoverflow.com/questions/17411940/matplotlib-scatter-plot-legend
        leg = map_ax.legend(leg_handles, leg_labels, scatterpoints=1, ncol=2,
                            loc=loc, bbox_to_anchor=bbox_to_anchor, fancybox=legend_fancybox,
                            shadow=legend_shadow, borderaxespad=legend_borderaxespad,
                            fontsize=fontsize)

    # re-position the axes. The REAL map aspect ratio seems to be this:
    realratio_h_w = bmap.aspect
    fig_w, fig_h = fig.get_size_inches()
    figratio_h_w = np.true_divide(fig_h, fig_w)

    if figratio_h_w >= realratio_h_w:
        # we have margins (blank space) above and below
        # thus, we assume:
        map_w = fig_w
        # and we calculate map_h
        map_h = map_w * realratio_h_w
        # assume there is the same amount of space above and below:
        vpad = (fig_h - map_h) / 2.0
        # hpad is zero:
        hpad = 0
    else:
        # we have margins (blank space) left and right
        # thus, we assume:
        map_h = fig_h
        # and consequently:
        map_w = map_h / realratio_h_w
        # assume there is the same amount of space above and below:
        hpad = (fig_w - map_w) / 2.0
        # wpad is zero:
        vpad = 0

    # calculate new fig dimensions EXACTLY as contour of the map
    new_fig_w = fig_w - 2 * hpad
    new_fig_h = fig_h - 2 * vpad

    # now margins:
    marginz = parse_margins(fig_margins)  # margins are in fontheight units. Get font height:
    fontw, fonth = 0, 0
    if len(np.nonzero(marginz)[0]):
        rend = fig.canvas.get_renderer()
        txt = map_ax.text(0, 0, 'm', fontsize=fontsize)
        bbx = txt.get_window_extent(renderer=rend)
        fonth = pix2inch(bbx.height, fig)  # in pixels I guess
        fontw = fonth  # dont set it to bb.width, use height.Check em maybe to see if we are right
        txt.remove()

    # calculate insets in inches (top right bottom left)
    insets_inch = marginz * [fonth, fontw, fonth, fontw]

    # set to fig dimensions
    new_fig_w += insets_inch[1] + insets_inch[3]
    new_fig_h += insets_inch[0] + insets_inch[2]

    fig.set_size_inches(new_fig_w, new_fig_h, forward=True)
    # (forward necessary if fig is in GUI, let's set for safety)

    # now the axes which are relative to the figure. Thus first normalize inches:
    insets_inch /= [fig_h, fig_w, fig_h, fig_w]

    # pos1 = map_ax.get_position()  # get the original position
    # NOTE: it seems that pos[0], pos[1] indicate the x and y of the LOWER LEFT corner, not
    # upper left!
    pos2 = [insets_inch[3], insets_inch[2],
            1 - (insets_inch[1] + insets_inch[3]),
            1 - (insets_inch[0] + insets_inch[2])]
    map_ax.set_position(pos2)

    if title:
        plt.suptitle(title)

    if show:
        plt.show()

    return fig
