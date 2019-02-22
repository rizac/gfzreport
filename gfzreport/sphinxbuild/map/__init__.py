'''
This module implements the function `plotmap` which plots scattered points on a map
retrieved using ArgGIS Server REST API. The function is highly customizable and is basically a
wrapper around the `Basemap` library (for the map background)
plus matplotlib utilities (for plotting points, shapes, labels and legend)

Created on Mar 10, 2016

@author: riccardo
'''
import numpy as np
import re
from itertools import izip, chain
from urllib2 import URLError, HTTPError
import socket
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
from mpl_toolkits.basemap import Basemap
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams


def parse_margins(obj, parsefunc=lambda margins: [float(val) for val in margins]):
    """Parses obj returning a 4 element numpy array denoting the top, right, bottom and left
    values. This function first converts obj to a 4 element list L, and then 
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
        try:
            margins = [float(obj)] * 4
        except (TypeError, ValueError):
            margins = re.compile("(?:\\s*,\\s*|\\s*;\\s*|\\s+)").split(obj)

    if len(margins) == 1:
        margins *= 4
    elif len(margins) == 2:
        margins *= 2
    elif len(margins) == 3:
        margins.append(margins[1])
    elif len(margins) != 4:
        raise ValueError("unable to parse margins on invalid value '%s'" % obj)

    return np.asarray(parsefunc(margins) if hasattr(parsefunc, "__call__") else margins)
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


def getbounds(min_lon, min_lat, max_lon, max_lat, margins):
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
            getbounds(self.min_lons, self.min_lats, self.max_lons, self.max_lats, map_margins)

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


def _normalize(obj, size=None, dtype=None):
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
    """Converts html_str into a tuple of rgba colors all in [0, 1]
    Curiously, matplotlib color functions do not provide this functionality for
    '#RGBA' color formats

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


def _shapeargs(lons, lats, labels, sizes, colors, markers, legend_labels):
    lons = _normalize(lons, dtype=float)  # basically: convert to float array if scalar (size=0)
    lats = _normalize(lats, dtype=float)  # basically: convert to float array if scalar (size=0)
    if len(lons) != len(lats):
        raise ValueError('mismatch in lengths: lons (%d) and lats (%d)' % (len(lons), len(lats)))
    leng = len(lons)
    labels = _normalize(labels, size=leng)
    colors = _normalize(colors, size=leng)
    markers = _normalize(markers, size=leng)
    legend_labels = _normalize(legend_labels, size=leng)
    # colors[np.isnan(colors) | (colors <= 0)] = 1.0  # nan colors default to 1 (black?)
    sizes = _normalize(sizes, size=leng, dtype=float)
    valid_points = np.logical_not(np.isnan(lons) | np.isnan(lats) | (sizes <= 0))

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


def _joinargs(key_prefix, kwargs, **already_supplied_args):
    '''updates already_supplied_args with kwargs using a given prefix in kwargs to identify
    common keys. Used in plotmap for kwargs'''
    key_prefix += "_"
    len_prefix = len(key_prefix)
    already_supplied_args.update({k[len_prefix:]: v
                                  for k, v in kwargs.iteritems() if k.startswith(key_prefix)})
    return already_supplied_args


def _mp_set_custom_props(drawfunc_retval, lines_props, labels_props):
    """Sets custom properties on drawparallels or drawmeridians return function.
    drawfunc_retval is a dict of numbers mapped to tuples where the first element is a list of
    matplotlib lines, and the second element is a list of matplotlib texts"""
    _setprop(chain.from_iterable((lin for lin, lab in drawfunc_retval.itervalues())), lines_props)
    _setprop(chain.from_iterable((lab for lin, lab in drawfunc_retval.itervalues())), labels_props)


def _setprop(iterator_of_mp_objects, props):
    '''sets the given properties of an iterator of same type matplotlib objects'''
    if not props:
        return
    prp = {}
    for obj in iterator_of_mp_objects:
        if not prp:
            prp = {"set_%s" % name: val for name, val in props.iteritems()
                   if hasattr(obj, "set_%s" % name)}
        for name, val in prp.iteritems():
            getattr(obj, name)(val)


# values below CAN be None but CANNOT be arrays containing None's
def plotmap(lons,
            lats,
            labels=None,
            legendlabels=None,
            markers="o",
            colors="#FF4400",
            sizes=20,
            cmap=None,
            fontsize=None,
            fontweight='regular',
            fontcolor='k',
            labels_h_offset=0,
            labels_v_offset=0,
            mapmargins='0.5deg',
            figmargins=2,
            arcgis_service='World_Street_Map',
            arcgis_xpixels=1500,
            arcgis_dpi=96,
            urlfail='ignore',
            maxmeridians=5,
            maxparallels=5,
            legend_pos='bottom',
            legend_borderaxespad=1.5,
            legend_ncol=1,
            title=None,
            show=False,
            **kwargs):  # @UnusedVariable
    """
    Makes a scatter plot of points on a map background using ArcGIS REST API.

    :param lons: (array-like of length N or scalar) Longitudes of the data points, in degreee
    :param lats: (array-like of length N or scalar) Latitudes of the data points, in degree
    :param labels: (array-like of length N or string. Default: None, no labels) Annotations
    (labels) for the individual data points on the map. If non-array (e.g. string), the same value
    will be applied to all points
    :param legendlabels: (array-like of length N or string. Default: None, no legend)
    Annotations (labels) for the legend. You can supply a sparse array where only some points
    will be displayed on the legend. All points with no legend label will not show up in the
    legend
    :param sizes: (array-like of length N or number. Default: 20) Sizes (in points^2) of the
    individual points in the scatter plot.
    :param markers: (array-like of length N,
    `MarkerStyle<http://matplotlib.org/api/markers_api.html#matplotlib.markers.MarkerStyle>`_  or
    string. Default: 'o' - circle) The markers (shapes) to be drawn for each point on the map.
    See `markers <http://matplotlib.org/api/markers_api.html#module-matplotlib.markers>`_ for
    more information on the different styles of markers scatter supports. Marker can be either
    an instance of the class or the text shorthand for a particular marker.
    :param colors:  (array-like of length N,
    `matplotlib color <http://matplotlib.org/api/colors_api.html>`_, e.g. string.
    Default: "#FF4400")
    Colors for the markers (fill color). You can type color transparency by supplying string of 9
    elements where the last two characters denote the transparency ('00' fully transparent,
    'ff' fully opaque). Note that this is a feature not implemented in `matplotlib` colors, where
    transparency is given as the last element of the numeric tuple (r, g, b, a)
    :param fontsize: (numeric or None. Default: None) The fontsize for all texts drawn on the
    map (labels, axis tick labels, legend). None uses the default figure font size for all. Custom
    values for the individual text types (e.g. legend texts vs labels texts) can be supplied
    via the `kwargs` argument and a given prefix (see below)
    :param fontweight: (string or number. Default: 'regular') The font weight for all texts drawn
    on the map (labels, axis tick labels, legend). Accepts the values (see
    http://matplotlib.org/api/text_api.html#matplotlib.text.Text.set_weight):
    ```
    [a numeric value in range 0-1000 | 'ultralight' | 'light' |
    'normal' | 'regular' | 'book' | 'medium' | 'roman' | 'semibold' | 'demibold' | 'demi' |
    'bold' | 'heavy' | 'extra bold' | 'black' ]
    ```
    Custom
    values for the individual text types (e.g. legend texts vs labels texts) can be supplied
    via the `kwargs` argument and a given prefix (see below)
    :param fontcolor: (`matplotlib color <http://matplotlib.org/api/colors_api.html>`_ or
    string. Default: 'k', black) The font color for all texts drawn on the
    map (labels, axis tick labels, legend). Custom
    values for the individual text types (e.g. legend texts vs labels texts) can be supplied
    via the `kwargs` argument and a given prefix (see below)
    :param labels_h_offset: (string, number. Defaults None=0) The horizontal offset to be applied
    to each label on the map relative to its point coordinates. Negative values will shift the
    labels westward, positive values eastward. Useful for not overlapping
    markers and labels.
    If numeric, it is assumed to be the expressed in degrees. Otherwise, you can supply a string
    with a number followed by one of the units 'm', 'km' or 'deg' (e.g., '5km', '0.5deg').
    Note that this value affects the
    `horizontalalignment` and `multialignment` properties of the labels
    (for info see http://matplotlib.org/api/text_api.html#matplotlib.text.Text). Supplying
    `labels_horizontalalignment` or `labels_ha` as optional argument will override
    this behaviour (see `kwargs` below)
    :param labels_v_offset: (string, number. Defaults None=0) The vertical offset to be applied
    to each label on the map relative to its point coordinates. Negative values will shift the
    labels southhward, positive values northward. See notes on `labels_h_offset` for details
    Note that this value affects the
    `verticalalignment` property of the labels
    (for info see http://matplotlib.org/api/text_api.html#matplotlib.text.Text). Supplying
    `labels_verticalalignment` or `labels_va` as optional argument will override
    this behaviour (see `kwargs` below)
    :param mapmargins: (array-like of 1,2,3,4 elements, numeric or string, or None=0.
    Default: '0.5deg').
    The map margins, i.e. how much the map has to 'expand/shrink' in any direction, relative
    to the bounding box calculated to include all points.
    If array-like, it behaves like the css 'margin' property of html: 4 elements will denote
    [top, right, bottom, left], two elements will denote [top/bottom, left/right], three
    elements [top, right/left, bottom], a single element array (or a single number or a string)
    applies the value to all directions.
    Finally, elements of the array must be expressed as the arguments `labels_h_offset` or
    `labels_v_offset`: numbers denoting degrees or strings with units 'm', 'km', 'deg'. Negative
    values will shrink the map.
    If string, the argument will be first splitted using commas, semicolon or spaces as delimiters
    (if no delimiter is found, the string is taken as a single chunk) and converted to an array-like
    object.
    :param figmargins: (array-like of 1,2,3,4 elements, number or None=0. Default:2) The
    figure margins *in font height units* (e.g., 2 means: twice the font height). This argument
    behaves exactly as `mapmargins` but expands/shrinks the distances between map and figure
    (image) bounds. Useful to include axis tick labels or legend, if they overflow.
    Note also that strings
    are allowed only if they are parsable to float (e.g. "5,6; -12  1")
    :param arcgis_service: (string, default:  'World_Street_Map'). The map image type, or
    more technically the service for the map
    hosted on ArcGIS server. Other values are 'ESRI_Imagery_World_2D'
    (default in
    `Basemap.arcgisimage <http://matplotlib.org/basemap/api/basemap_api.html#mpl_toolkits.basemap.Basemap.arcgisimage>`_),
    'World_Topo_Map', 'World_Terrain_Base'. For details, see:
    http://server.arcgisonline.com/arcgis/rest/services.
    :param arcgis_xpixels: (numeric, default: 3000). Requested number of image pixels
    in x-direction (default is 400 in
    `Basemap.arcgisimage <http://matplotlib.org/basemap/api/basemap_api.html#mpl_toolkits.basemap.Basemap.arcgisimage>`_).
    The documentation is quite unclear but this parameter seems to set the zoom of the image. From
    this `link <http://basemaptutorial.readthedocs.io/en/latest/backgrounds.html#arcgisimage>`_:
    A bigger number will ask a bigger image, so the image will have more detail.
    So when the zoom is bigger, `xsize` must be bigger to maintain the resolution
    :param urlfail: (string, 'raise' or 'ignore'. Default: 'ignore'). Tells what to do if the
    ArcGIS requet fails (URLError, no internet connection etcetera). By default, on failure a raw
    map with continents contour, and oceans will be plotted (good for
    debug). Otherwise, the exception resulting from the web request is raised
    :param maxmeridians: (numeric default: 5). The number of maximum meridians to be drawn. Set to
    <=0 to hide meridians. Note that also x-axis labels are drawn.
    To further manipulate meridians display, use any argument starting with
    'mlabels_', 'mlines_' or 'meridians' (see `kwargs` below). E.g., to show only the labels and not
    the lines, supply as argument `meridians_linewidth=0` or 'mlines_linewidth=0'.
    :param maxparallels: (numeric default: 5). The number of maximum parallels to be drawn. Set to
    <=0 to hide parallels. Note that also y-axis labels are drawn.
    To further manipulate parallels display, use any argument starting with
    'plabels_', 'plines_' or 'parallels' (see `kwargs` below). E.g., to show only the labels and not
    the lines, supply as argument `parallels_linewidth=0` or 'plines_linewidth=0'.
    :param legend_pos: (string in ['top'. 'bottom', 'right', 'left'], default='bottom'). The legend
    location with respect to the map. It also adjusts the bounding box that the legend will be
    anchored to.
    For
    customizing entirely the legend placement overriding this parameter, provide `legend_loc`
    (and optionally `legend_bbox_to_anchor`) in `kwargs` (see below)
    :param legend_borderaxespad: (numeric, default 1.5) The pad between the axes and legend border,
    in font units
    :param legend_ncol: (integer, default=1) The legend number of columns
    :param title (string or None. Default: None): Title above plot (Note: not tested)
    :param show (boolean, default: False): Whether to show the figure after plotting or not
    (Note: not tested). Can be used to do further customization of the plot before showing it.
    :param fig: (matplotlib figure or None, default: None). Note: deprecated, pass None as
    supplying an already existing figure with other axes might break the figure layout
    :param kwargs: any kind of additional argument passed to `matplotlib` and `Basemap` functions
    or objects.
    The name of the argument must be of the form
    ```
    prefix_propertyname=propertyvalue
    ```
    where prefix indicates the function/object to be called with keyword argument:
    ```
    propertyname=propertyvalue
    ```

    Current supported prefixes are (for available property names see links):

    Prefix        Passes `propertyname` to
    ============ ==================================================================================
    arcgis       `Basemap.arcgisimage <http://matplotlib.org/basemap/api/basemap_api.html#mpl_toolkits.basemap.Basemap.arcgisimage>_
                 used to retrieve the background map using ArgGIS Server REST API. See also
                 http://basemaptutorial.readthedocs.io/en/latest/backgrounds.html#arcgisimage
    basemap      `Basemap <http://matplotlib.org/basemap/api/basemap_api.html#mpl_toolkits.basemap.Basemap>`_
                 the object responsible of drawing and managing the map. Note that
                 `basemap_resolution=h` and `basemap_epsg=4326` by default.
    labels       All `texts <http://matplotlib.org/api/text_api.html#matplotlib.text.Text>`_
                 used to display the point labels on the map
    legend       The `legend <http://matplotlib.org/api/legend_api.html#matplotlib.legend.Legend>`_.
                 See the already implemented arguments `legend_borderaxespad`,
                 `legend_ncol`
    legendlabels All `texts <http://matplotlib.org/api/text_api.html#matplotlib.text.Text>`_
                 used to display the text labels of the legend
    meridians    `Basemap.drawmeridians`. For more detailed settings on meridians, see
                 `mlines` and `mlabels`
    parallels    `Basemap.drawparallels`. For more detailed settings on parallels, see
                 `plines` and `plabels`
    plines       All `lines <http://matplotlib.org/api/lines_api.html#matplotlib.lines.Line2D>`_
                 used to display the parallels
    plabels      All `texts <http://matplotlib.org/api/text_api.html#matplotlib.text.Text>`_
                 used to display the parallels labels on the y axis
    mlines       All `lines <http://matplotlib.org/api/lines_api.html#matplotlib.lines.Line2D>`_
                 used to display the meridians
    mlabels      All `texts <http://matplotlib.org/api/text_api.html#matplotlib.text.Text>`_
                 used to display the meridians labels on the x axis
    ============ ==================================================================================

    Examples
    --------

    - `legend_title='abc'` will call `legend(..., title='abc', ...)`
    - `labels_path_effects=[PathEffects.withStroke(linewidth=2, foreground='white')]` will set the
      a white contour around each label text
    - `meridians_labelstyle="+/-"` will call `Basemap.drawmeridians(..., labelstyle="+/-", ...)`

    Notes:
    ------
    The objects referenced by `plines`, `plabels`, `mlines`, `mlabels` and `legendlabels`
    cannot be initialized directly with the given properties, which will be set after they are
    created assuming that for any property `foo` passed as keyword argument in their constructor
    there exist a method `set_foo(...)` (which will be called with the given propertyvalue).
    This is most likely always true according to matplotlib api, but we cannot assure it works
    100% of the times
    """
    lons, lats, labels, sizes, colors, markers, legendlabels =\
        _shapeargs(lons, lats, labels, sizes, colors, markers, legendlabels)

    # convert html strings to tuples of rgba values in [0.1] if the former are in string format,
    # because (maybe too old matplotlib version?) colors in the format '#RGBA' are not supported
    # Also, if cmap is provided, basemap.scatter calls matplotlib.scatter which
    # wants float sequenes in case of color map
    if colors.dtype.char in ('U', 'S'):  # pylint: disable=no-member
        colors = np.array([torgba(c) for c in colors])

    fig = plt.figure()
    map_ax = fig.add_axes([0, 0, 1, 1])  # set axes size the same as figure

    # setup handler for managing basemap coordinates and meridians / parallels calculation:
    handler = MapHandler(lons, lats, mapmargins)

    kwa = _joinargs('basemap', kwargs,
                    llcrnrlon=handler.llcrnrlon,
                    llcrnrlat=handler.llcrnrlat,
                    urcrnrlon=handler.urcrnrlon,
                    urcrnrlat=handler.urcrnrlat,
                    epsg='4326',  # 4326,  # 3395,  # 3857,
                    resolution='i', # 'h',
                    ax=map_ax)
    bmap = Basemap(**kwa)

    try:
        kwa = _joinargs("arcgis", kwargs, service=arcgis_service, xpixels=arcgis_xpixels,
                        dpi=arcgis_dpi)
        # set the map image via a map service. In case you need the returned values, note that
        # This function returns an ImageAxis (or AxisImage, check matplotlib doc)
        bmap.arcgisimage(**kwa)
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

    # draw meridians and parallels. From basemap.drawmeridians / drawparallels doc:
    # returns a dictionary whose keys are the meridian values, and
    # whose values are tuples containing lists of the
    # matplotlib.lines.Line2D and matplotlib.text.Text instances
    # associated with each meridian. Deleting an item from the
    # dictionary removes the correpsonding meridian from the plot.
    if maxparallels > 0:
        kwa = _joinargs("parallels", kwargs, linewidth=1, fontsize=fontsize,
                        labels=[0, 1, 1, 0], fontweight=fontweight)
        parallels = handler.get_parallels(maxparallels)
        # Old basemap versions have problems with non-integer parallels.
        try:
            # Note: the method below # returns a list of text object
            # represeting the tick labels
            _dict = bmap.drawparallels(parallels, **kwa)
        except KeyError:
            parallels = sorted(list(set(map(int, parallels))))
            _dict = bmap.drawparallels(parallels, **kwa)

        # set custom properties:
        kwa_lines = _joinargs("plines", kwargs)
        kwa_labels = _joinargs("plabels", kwargs, color=fontcolor)
        _mp_set_custom_props(_dict, kwa_lines, kwa_labels)

    if maxmeridians > 0:
        kwa = _joinargs("meridians", kwargs, linewidth=1, fontsize=fontsize,
                        labels=[1, 0, 0, 1], fontweight=fontweight)
        meridians = handler.get_meridians(maxmeridians)
        _dict = bmap.drawmeridians(meridians, **kwa)

        # set custom properties:
        kwa_lines = _joinargs("mlines", kwargs)
        kwa_labels = _joinargs("mlabels", kwargs, color=fontcolor)
        _mp_set_custom_props(_dict, kwa_lines, kwa_labels)

    # fig.get_axes()[0].tick_params(direction='out', length=15)  # does not work, check basemap
    fig.bmap = bmap

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
        # Set alignments which control also the corner point reference when placing labels
        # from (FIXME: add ref?)
        # horizontalalignment controls whether the x positional argument for the text indicates
        # the left, center or right side of the text bounding box.
        # verticalalignment controls whether the y positional argument for the text indicates
        # the bottom, center or top side of the text bounding box.
        # multialignment, for newline separated strings only, controls whether the different lines
        # are left, center or right justified
        ha = 'left' if hoffset[0] > 0 else 'right' if hoffset[0] < 0 else 'center'
        va = 'bottom' if voffset[0] > 0 else 'top' if voffset[0] < 0 else 'center'
        ma = ha
        kwa = _joinargs("labels", kwargs, fontweight=fontweight, color=fontcolor,
                        zorder=100, fontsize=fontsize, horizontalalignment=ha,
                        verticalalignment=va, multialignment=ma)

        for name, xpt, ypt in zip(labels, xlbl, ylbl):
            # Check if the point can actually be seen with the current bmap
            # projection. The bmap object will set the coordinates to very
            # large values if it cannot project a point.
            if xpt > 1e25:
                continue
            map_ax.text(xpt, ypt, name, **kwa)

    # plot points
    x, y = bmap(lons, lats)
    # store handles to points, and relative labels, if any
    leg_handles, leg_labels = [], []
    # bmap.scatter accepts all array-like args except markers. Avoid several useless loops
    # and do only those for distinct markers:
    # unique markers (sorted according to their index in markers, not their value):
    mrks = markers[np.sort(np.unique(markers, return_index=True)[1])]
    for mrk in mrks:
        # Note using masks with '==' (numpy==1.11.3):
        #
        # >>> a = np.array([1,2,3])
        # >>> a == 3
        # array([False, False,  True], dtype=bool)  # OK
        # >>> a == None
        # False                                     # NOT AS EXPECTED!
        # >>> np.equal(a, None)
        # array([False, False, False], dtype=bool)  # OK
        #
        # (Note also that a == None issues:
        # FutureWarning: comparison to `None` will result in an elementwise object
        # comparison in the future.)
        #
        # So the correct way is to write
        # mask = np.equal(array, val) if val is None else (a == val)

        m_mask = np.equal(markers, mrk) if mrk is None else markers == mrk  # see above
        __x = x[m_mask]
        __y = y[m_mask]
        __m = mrk
        __s = sizes[m_mask]
        __c = colors[m_mask]
        __l = legendlabels[m_mask]
        # unique legends (sorted according to their index in __l, not their value):
        for leg in __l[np.sort(np.unique(__l, return_index=True)[1])]:
            l_mask = np.equal(__l, leg) if leg is None else __l == leg  # see above
            _scatter = bmap.scatter(__x[l_mask],
                                    __y[l_mask],
                                    marker=mrk,
                                    s=__s[l_mask],
                                    c=__c[l_mask],
                                    cmap=cmap,
                                    zorder=10)
            if leg:
                leg_handles.append(_scatter)
                leg_labels.append(leg)

    if leg_handles:
        # if we provided `legend_loc`, use that:
        loc = kwargs.get('legend_loc', None)
        bbox_to_anchor = None  # defaults in matplotlib legend
        # we do have legend to show. Adjust legend reference corner:
        if loc is None:
            if legend_pos == 'bottom':
                loc = 'upper center'
                bbox_to_anchor = (0.5, -0.05)
            elif legend_pos == 'top':
                loc = 'lower center'
                bbox_to_anchor = (0.5, 1.05)
            elif legend_pos == 'left':
                loc = 'center right'
                bbox_to_anchor = (-0.05, 0.5)
            elif legend_pos == 'right':
                loc = 'center left'
                bbox_to_anchor = (1, 0.5)
            else:
                raise ValueError('invalid legend_pos value:"%s"' % legend_pos)

        # The plt.legend has the prop argument which sets the font properties:
        # family, style, variant, weight, stretch, size, fname. See
        # http://matplotlib.org/api/font_manager_api.html#matplotlib.font_manager.FontProperties
        # However, that property does not allow to set font color. So we
        # use the get_text method of Legend. Note that we pass font size *now* even if
        # setting it later works as well (the legend frame is resized accordingly)
        kwa = _joinargs("legend", kwargs, scatterpoints=1, ncol=legend_ncol, loc=loc,
                        bbox_to_anchor=bbox_to_anchor, borderaxespad=legend_borderaxespad,
                        fontsize=fontsize)
        # http://stackoverflow.com/questions/17411940/matplotlib-scatter-plot-legend
        leg = map_ax.legend(leg_handles, leg_labels, **kwa)
        # set properties supplied via 'legend_'
        _setprop(leg.get_texts(), _joinargs("legendlabels", kwargs, color=fontcolor))

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
    marginz = parse_margins(figmargins)  # margins are in fontheight units. Get font height:
    fontsize_inch = 0
    if len(np.nonzero(marginz)[0]):
        # Calculate the font size in pixels.
        # We want to be consistent with matplotlib way of getting fontsize.
        # inspecting matplotlib.legend.Legend.draw we end up with:
        # 1. Get the renderer
        rend = fig.canvas.get_renderer()
        # 2. get the fontsize in points. We might use `fontsize` but it might be None and we want
        # the default in case. There are several 'defaults' (rcParams['font.size'],
        # rcParams["legend.fontsize"])... we don't care for now, use the first. How to get
        # rcParams['font.size'] ? Either this: (see at matplotlib.Legend.__init__):
        # fontsize_pt = FontProperties(size=fontsize, weight=fontweight).get_size_in_points()
        # or simply do:
        fontsize_pt = fontsize or rcParams['font.size']
        # Now use renderer to convert to pixels:
        # For info see matplotlib.text.Text.get_window_extent
        fontsize_px = rend.points_to_pixels(fontsize_pt)
        # finally inches:
        fontsize_inch = pix2inch(rend.points_to_pixels(fontsize_px), fig)

    # calculate insets in inches (top right bottom left)
    insets_inch = marginz * fontsize_inch

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
