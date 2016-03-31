'''
Created on Mar 10, 2016

@author: riccardo
'''

import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
# from obspy.imaging.maps import _BASEMAP_RESOLUTIONS
import inspect
import uuid


def parse_margins(values):
    """Parses margins as css values
    Returns top, right, bottom, left margins
    :param values: either None, a number, a list of numbers (allowed lengths: 1 to 4)
    :return: a 4 element tuple identifying the top, right, bottom, left values of the margins. The
        idea is the same as css margins.
        :Examples:
        value is     |    returns   |
        -----------------------------
        None,        | [0, 0, 0, 0] |
        x or [x]     | [x, x, x, x] |
        [x, t]       | [x, y ,x, y] |
        [x, y, z]    | [x, y, z, y] |
        [x, y, z, t] | [x, y, z, t] |
    """
    try:
        mmm = float(values)
        values = [mmm] * 4
    except TypeError:
        if values is None:
            values = [0] * 4
    lenm = len(values)
    if lenm < 1 or lenm > 4:
        raise ValueError("error in get_margin: specify a 1 to 4 length list of numeric values, "
                         "in km")
    if lenm == 3:
        values = [values[0], values[1], values[2], values[1]]
    elif lenm == 2:
        values = [values[0], values[1], values[0], values[1]]
    elif lenm == 1:
        values *= 4

    return values


def get_axes_dims(projection, colorbar=False):
    """ returns a tuple where the first element is the dimensions [x0,y0,width, height]
    of an axes on which and its second element is None if colorbar is not True, else
    the dimension of a colorbar we are about to plot a map.
    Dimensions are useful to set later, e.g., on a figure:
    map_ax_dims, _ = get_basemap_axes_dims('local')
    fig.add_axes(map_ax_dims)

    :param projection: a projection, three cases are possible: 'global', 'local' or anything else
    :param colorbar: if True, space will be reserved for a potential colorbar
    :return: a tuple of
    """
    cm_ax = None
    map_ax = None
    if projection == "local":
        ax_x0, ax_width = 0.10, 0.80
    elif projection == "global":
        ax_x0, ax_width = 0.01, 0.98
    else:
        ax_x0, ax_width = 0.05, 0.90

    if colorbar:
        map_ax = [ax_x0, 0.13, ax_width, 0.77]
        cm_ax = [ax_x0, 0.05, ax_width, 0.05]
    else:
        ax_y0, ax_height = 0.05, 0.85
        if projection == "local":
            ax_y0 += 0.05
            ax_height -= 0.05
        map_ax = [ax_x0, ax_y0, ax_width, ax_height]

    return map_ax, cm_ax


class MapHandler(object):
    """
        Class handling bounds of a map given points (lons and lats)
    """
    def __init__(self, lons, lats, margins_km):
        self.fig = None
        self.setup(lons, lats, margins_km)

    def setup(self, lons, lats, margins_km):
        self.lons = lons if len(lons) else [0]
        self.lats = lats if len(lats) else [0]
        self.max_lons, self.min_lons = self.get_normalized_lons_bounds_(self.lons)
        self.max_lats, self.min_lats = max(self.lats), min(self.lats)
        self.margins_in_m = map(lambda x: x * 1000, parse_margins(margins_km))
        # margins: top, right, bottom, left
        self.set_fig(self.fig)  # calls self._calc_bounds
        # and sets self.llcrnrlon, self.llcrnrlat, self.urcrnrlon, self.urcrnrlat

    @staticmethod
    def get_normalized_lons_bounds_(lons):
        if min(lons) < -150 and max(lons) > 150:
            max_lons = max(np.array(lons) % 360)
            min_lons = min(np.array(lons) % 360)
        else:
            max_lons = max(lons)
            min_lons = min(lons)

        return max_lons, min_lons

    @staticmethod
    def _calc_bounds(min_lons, min_lats, max_lons, max_lats, margins_in_m):
        """Calculates the bounds given the bounding box identified by the arguments and
        given optional margins
        :param min_lons: the minimum of longitudes
        :param min_lats: the maximum of latitudes
        :param max_lons: the minimum of longitudes
        :param max_lats: the maximum of latitudes
        :param margins_in_m: the margins in a 4 element list or tuple [top, right, bottom, left].
        Margins are given in meters and converted to degrees inside the method
        :return: the 6-element tuple denoting lon_0, lat_0, min_lons, min_lats, max_lons, max_lats.
        where min_lons, min_lats, max_lons, max_lats are the new bounds and lat_0 and lon_0 are
        their midpoint x and y, respectively)
        """
        top, right, bottom, left = margins_in_m

        h2lat = MapHandler.h2lat
        w2lon = MapHandler.w2lon

        vert_margin_low = h2lat(bottom)
        vert_margin_high = h2lat(top)

        horiz_margin_low = w2lon(left, min_lats)
        horiz_margin_high = w2lon(right, max_lats)

        min_lons, min_lats, max_lons, max_lats = min_lons-horiz_margin_low,\
            min_lats-vert_margin_low, max_lons+horiz_margin_high, max_lats+vert_margin_high

        if min_lons == max_lons:
            min_lons -= 10  # in degrees
            max_lons += 10  # in degrees

        if min_lats == max_lats:
            min_lats -= 10  # in degrees
            max_lats += 10  # in degrees

        lon_0, lat_0 = MapHandler.get_lon0_lat0(min_lons, min_lats, max_lons, max_lats)
        return lon_0, lat_0, min_lons, min_lats, max_lons, max_lats

    @staticmethod
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

    def set_fig(self, fig):
        """
            Sets the figure and re-calculates map bounds accordingly to take as most figure space
            as possible
            :param fig: the figure. Can be None, in that case map bounds are re-calculated according
            to the points passed in the constructor or in the setup function
            :return: self, so that this method can be chained to the constructor:
                m = MapHandler(...).set_gif(figure)
        """
        self.fig = fig

        # calculate bounds WITH the margins otherwise appending margins later should re-calculate
        # everything
        lon_0, lat_0, llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat =\
            MapHandler._calc_bounds(self.min_lons, self.min_lats, self.max_lons, self.max_lats,
                                    self.margins_in_m)

        if fig is not None:

            fig_w, fig_h = fig.get_size_inches()
            aspect = fig_w / fig_h

            map_w = MapHandler.lon2w(urcrnrlon - llcrnrlon, lat_0)
            map_h = MapHandler.lat2h(urcrnrlat - llcrnrlat)

            if map_w / map_h < aspect:
                new_map_w = map_h * aspect
                new_margin_in_deg = MapHandler.w2lon(new_map_w - map_w, lat_0) / 2
                llcrnrlon -= new_margin_in_deg
                urcrnrlon += new_margin_in_deg
            else:
                new_map_h = map_w / aspect
                new_margin_in_deg = MapHandler.h2lat(new_map_h - map_h) / 2
                llcrnrlat -= new_margin_in_deg
                urcrnrlat += new_margin_in_deg

            # re-calculate lon_0 and lat_0
            lon_0, lat_0 = MapHandler.get_lon0_lat0(llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat)

        self.lon_0, self.lat_0, self.llcrnrlon, self.llcrnrlat, self.urcrnrlon, self.urcrnrlat = \
            lon_0, lat_0, llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat

        return self

    def get_bb(self):  # EXPERIMENTAL. CALCULATE BBOX. LATER
        if self.fig is None:
            raise ValueError('no figure set. Call set_fig first')
#         r = self.fig.canvas.get_renderer()
#         t = plt.text(0.5, 0.5, 'test')
#         bb = t.get_window_extent(renderer=r)
#         width = bb.width
#         height = bb.height

        return self

    @staticmethod
    def linspace(val1, val2, N):
        """
        returns around N 'nice' values between val1 and val2
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

    def _get_map_dims(self):  # , fig_size_in_inches, colorbar=False):
        """Returns the map dimension width, height, in meters"""

        max_lons, min_lons = self.urcrnrlon, self.llcrnrlon
        max_lats, min_lats = self.urcrnrlat, self.llcrnrlat
        height = MapHandler.lat2h(max_lats - min_lats)
        width = MapHandler.lon2w(max_lons - min_lons, self.lat_0)

        return width, height

    def get_parallels(self, max_labels_count=8):
        width, height = self._get_map_dims()
        lat_0 = self.lat_0
        N1 = int(np.ceil(height / max(width, height) * max_labels_count))
        h2lat = MapHandler.h2lat
        parallels = self.linspace(lat_0 - h2lat(height / 2),
                                  lat_0 + h2lat(height / 2), N1)
        return parallels

    def get_meridians(self, max_labels_count=8):
        width, height = self._get_map_dims()
        lon_0 = self.lon_0
        lat_0 = self.lat_0
        w2lon = MapHandler.w2lon
        N2 = int(np.ceil(width / max(width, height) * max_labels_count))
        meridians = self.linspace(lon_0 - w2lon(width / 2, lat_0),
                                  lon_0 + w2lon(width / 2, lat_0), N2)
        meridians[meridians > 180] -= 360
        return meridians

    # static constant converter (degree to meters and viceversa) for latitudes
    DEG2M_LAT = 2 * np.pi * 6371 * 1000 / 360

    @staticmethod
    def lat2h(distance_in_degrees):
        """converts latitude distance from degrees to height in meters
        :param distance_in_degrees: a distance along the great circle espressed in degrees"""
        deg2m_lat = MapHandler.DEG2M_LAT  # 2 * np.pi * 6371 * 1000 / 360
        return distance_in_degrees * deg2m_lat

    @staticmethod
    def h2lat(distance_in_meters):
        """converts latitude distance from height in meters to degrees
        :param distance_in_degrees: a distance along the great circle espressed in degrees"""
        deg2m_lat = MapHandler.DEG2M_LAT  # deg2m_lat = 2 * np.pi * 6371 * 1000 / 360
        return distance_in_meters / deg2m_lat

    @staticmethod
    def lon2w(distance_in_degrees, lat_0):
        """converts longitude distance from degrees to width in meters
        :param distance_in_degrees: a distance along the lat_0 circle expressed in degrees
        :param lat_0: if missing or None, defaults to the internal lat_0, which is set as the mean
        of all points passed to this object. Otherwise, expresses the latitude of the circle along
        which the lon2w(distance_in_degrees) must be converted to meters"""
        deg2m_lat = MapHandler.DEG2M_LAT  # deg2m_lat = 2 * np.pi * 6371 * 1000 / 360
        deg2m_lon = deg2m_lat * np.cos(lat_0 / 180 * np.pi)
        return distance_in_degrees * deg2m_lon

    @staticmethod
    def w2lon(distance_in_meters, lat_0):
        """converts longitude distance from width in meters to degrees
        :param distance_in_meters: a distance along the lat_0 circle expressed in meters
        :param lat_0: if missing or None, defaults to the internal lat_0, which is set as the mean
        of all points passed to this object. Otherwise, expresses the latitude (in degrees) of the
        circle along which w2lon(distance_in_meters) must be converted to degrees"""
        deg2m_lat = MapHandler.DEG2M_LAT  # deg2m_lat = 2 * np.pi * 6371 * 1000 / 360
        deg2m_lon = deg2m_lat * np.cos(lat_0 / 180 * np.pi)
        return distance_in_meters / deg2m_lon


def ensurelen(obj, size, dtype=None):
    """"Casts" obj to a numpy array of the given size and optional dtype, and returns it.
    If size is lower or equal than zero, returns the array. Otherwise, resizes the array to the
    specified size (this is done only if the array has length 1), otherwise raises an exception
    Note: obj=None will be converted to the array [None], apparently in the current version of numpy
    this wouldn't be the default (see argument ndmin=1)
    :return an numpy array resulting to the coinversion of obj into array
    :Examples:
    """
    x = np.array(obj, ndmin=1) if dtype is None else np.array(obj, ndmin=1, dtype=dtype)
    if size <= 0:
        return np.array([]) if obj is None else x  # if obj is None x is [None], return [] instead
    try:
        if len(x) == 1:
            x = np.resize(x, size)
        elif len(x) != size:
            raise ValueError("invalid array length: %d. Expected %d" % (len(x), size))
    except (ValueError, TypeError) as _err:
        raise ValueError(str(_err))

    return x


def parseargs(lons, lats, labels, sizes, colors, markers):
    lons = ensurelen(lons, 0, float)  # basically: convert to float array if scalar (size=0)
    lats = ensurelen(lats, 0, float)  # basically: convert to float array if scalar (size=0)
    if len(lons) != len(lats):
        raise ValueError('mismatch in lengths: lons (%d) and lats (%d)' % (len(lons), len(lats)))
    leng = len(lons)
    labels = ensurelen(labels, leng)  # ensure either 'scalar' or array of len=leng
    colors = ensurelen(colors, leng)
    # colors[np.isnan(colors) | (colors <= 0)] = 1.0  # nan colors default to 1 (black?)
    sizes = ensurelen(sizes, leng, float)
    sizes[sizes <= 0] = np.nan  # sizes non positive to nan
    markers = ensurelen(markers, len(lons))
    nan_points = np.isnan(lons) | np.isnan(lats) | np.isnan(sizes)  # | np.isnan(colors)
    valid_points = np.logical_not(nan_points)
    # return all points whose corresponding numeric values are not nan:
    return (lons[valid_points],
            lats[valid_points],
            labels[valid_points],
            sizes[valid_points],
            colors[valid_points],
            markers[valid_points])


def plot_basemap(lons,
                 lats,
                 labels=None,
                 sizes=100,  # can be scalar (including None or nan) or array
                 colors="#EEC100",  # can be scalar (including None or nan) or array
                 markers="^",
                 margins_in_km=100,
                 epsg_projection='4326',  # 4326,  # 3395,  # 3857,
                 arcgis_image_service='ESRI_Imagery_World_2D',  # 'ESRI_StreetMap_World_2D'
                 arcgis_image_xpixels=1500,
                 arcgis_image_dpi=96,
                 num_max_meridians=5,
                 num_max_parallels=5,
                 title=None,
                 show=False,
                 fig=None,
                 **kwargs):  # @UnusedVariable
    """
    Creates a basemap plot with a data point scatter plot.

    :param lons: Longitudes of the data points.
    :type lons: list/tuple of floats, or a single scalar number (will be converted to a single
        point list)
    :param lats: Latitudes of the data points. Must be the same length as lons
    :type lats: list/tuple of floats, or a single scalar number (1 point only)
    :param labels: Annotations for the individual data points. Defaults to None if missing.
        If labels is a "scalar" (i.e. something not tuple/list etcetera) will be converted to the
        list [labels, labels, ... ] of the same length as len(lons)
    :type labels: list/tuple of str
    :param sizes: Sizes of the individual points in the scatter plot. Defaults to None if missing.
        If sizes is a "scalar" (i.e. something not tuple/list etcetera) will be converted to the
        list [sizes, sizes, ... ] of the same length as len(lons).
    :type sizes: float or list/tuple of floats
    :param colors: list/tuple of strings dentoting html colors. Defaults to "#EEC00" if missing.
        If colors is a "scalar" (i.e. something not tuple/list etcetera) will be converted to the
        list [colors, colors, ... ] of the same length as len(lons)
    :type colors: string or list/tuple of strings
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
    lons, lats, labels, sizes, colors, markers =\
        parseargs(lons, lats, labels, sizes, colors, markers)

    if fig is None:
        fig = plt.figure()

        # setup the axes dimensions
        map_ax_dims, cm_ax_dims = get_axes_dims('local', colorbar=False)
        map_ax = fig.add_axes(map_ax_dims)
        if cm_ax_dims:
            cm_ax = fig.add_axes(cm_ax_dims)

        # TEST: add global world to indicate the map location
#             map_ax2 = fig.add_axes([0.7, 0.8, 0.19, 0.19])
#             bmap_ = Basemap(projection='ortho',
#                             resolution=_BASEMAP_RESOLUTIONS[resolution],
#                             area_thresh=1000.0, lat_0=round(np.mean(lats), 4),
#                             lon_0=round(np.mean(lons), 4), ax=map_ax2)

#             Y, X = np.meshgrid([0, max(lons)], [0, max(lats)])
#             bmap_.etopo()
#             bmap_.contourf(
#                            X,
#                            Y,
#                            np.array([[1 , 1],[1 , 1]]),
#                            alpha=0.5)
        # done

        handler = MapHandler(lons, lats, margins_in_km).set_fig(fig)
        bmap = Basemap(llcrnrlon=handler.llcrnrlon,
                       llcrnrlat=handler.llcrnrlat,
                       urcrnrlon=handler.urcrnrlon,
                       urcrnrlat=handler.urcrnrlat,
                       epsg=epsg_projection,
                       ax=map_ax)
#         bmap.arcgisimage(service='ESRI_Imagery_World_2D', xpixels=1500, verbose= True)
        # services here: http://server.arcgisonline.com/arcgis/rest/services
        bmap.arcgisimage(service=arcgis_image_service, xpixels=arcgis_image_xpixels,
                         dpi=arcgis_image_dpi, verbose=True)

        if num_max_parallels:
            parallels = handler.get_parallels(num_max_parallels)
            # Old basemap versions have problems with non-integer parallels.
            try:
                bmap.drawparallels(parallels, labels=[0, 1, 1, 0])
            except KeyError:
                parallels = sorted(list(set(map(int, parallels))))
                bmap.drawparallels(parallels, labels=[0, 1, 1, 0])

        if num_max_meridians:
            meridians = handler.get_meridians(num_max_meridians)
            bmap.drawmeridians(meridians, labels=[1, 0, 0, 1])

        fig.bmap = bmap
    else:
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

    # from the docs:
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
    x, y = bmap(lons, lats)

    # setup color array

    # plot labels
    if len(labels):
        if 100 > len(lons) > 1:
            for name, xpt, ypt in zip(labels, x, y):
                # Check if the point can actually be seen with the current bmap
                # projection. The bmap object will set the coordinates to very
                # large values if it cannot project a point.
                if xpt > 1e25:
                    continue
                map_ax.text(xpt, ypt, name, weight="heavy",
                            color="k", zorder=100,
                            path_effects=[
                                PathEffects.withStroke(linewidth=3,
                                                       foreground="white")])
        elif len(lons) == 1:
            map_ax.text(x[0], y[0], labels[0], weight="heavy", color="k",
                        path_effects=[
                            PathEffects.withStroke(linewidth=3,
                                                   foreground="white")])

    # bmap.scatter accepts all array-like args except markers. Avoid several useless loops
    # and do only those for distinct markers:
    mrks = np.unique(markers)
    for mrk in mrks:
        _scatter = bmap.scatter(x[markers == mrk],
                                y[markers == mrk],
                                marker=mrk,
                                s=sizes[markers == mrk],
                                c=colors[markers == mrk],
                                zorder=10)

    if title:
        plt.suptitle(title)

    if show:
        plt.show()

    return fig


if __name__ == "__main__":
    lons = [88, 77.5, 85]
    lats = [2.5, -2.6, 5]  # [83.5, 72.6]

    # fig = plot_basemap(lons, lats,
    #                    sizes=100, labels=['?? something very LONG!'] * len(lons), show=True,)
    # plt.show()
