'''
Created on Mar 10, 2016

@author: riccardo
'''

import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
# from matplotlib.colorbar import Colorbar
from matplotlib.colors import Normalize
from matplotlib.dates import date2num, AutoDateLocator, AutoDateFormatter
import matplotlib.patheffects as PathEffects
from matplotlib.ticker import (FormatStrFormatter, Formatter, FuncFormatter,
                                MaxNLocator)

from obspy.imaging.maps import _BASEMAP_RESOLUTIONS
from obspy import UTCDateTime
# from obspy.core.util.base import get_basemap_version, get_cartopy_version

from future.utils import native_str

from matplotlib import patches


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


class LocalProjHandler(object):

    def __init__(self, lons, lats):
        self.lons = lons
        self.lats = lats
        self.max_lons, self.min_lons = self.get_normalized_lons_bounds_(lons)
        self.max_lats, self.min_lats = max(lats), min(lats)
        self.lon_0, self.lat_0 = self.get_lon0_lat0()
        self.deg2m_lon, self.deg2m_lat = self.deg2m(self.lat_0)

    @staticmethod
    def get_normalized_lons_bounds_(lons):
        if min(lons) < -150 and max(lons) > 150:
            max_lons = max(np.array(lons) % 360)
            min_lons = min(np.array(lons) % 360)
        else:
            max_lons = max(lons)
            min_lons = min(lons)

        return max_lons, min_lons

    def get_lon0_lat0(self):
        max_lons, min_lons = self.max_lons, self.min_lons
        max_lats, min_lats = self.max_lats, self.min_lats

        lat_0 = max_lats / 2. + min_lats / 2.
        lon_0 = max_lons / 2. + min_lons / 2.
        if lon_0 > 180:
            lon_0 -= 360
        return lon_0, lat_0

#     def get_lon0lat0(self, lons, lats, norm_max_lons=None, norm_min_lons=None):
#         max_lons, min_lons = norm_max_lons, norm_min_lons
#         if max_lons is None or min_lons is None:
#             max_lons, min_lons = self.get_normalized_lons_bounds(lons)
# 
#         lat_0 = max(lats) / 2. + min(lats) / 2.
#         lon_0 = max_lons / 2. + min_lons / 2.
#         if lon_0 > 180:
#             lon_0 -= 360
#         return lon_0, lat_0

    @staticmethod
    def deg2m(lat_0):
        deg2m_lat = 2 * np.pi * 6371 * 1000 / 360
        deg2m_lon = deg2m_lat * np.cos(lat_0 / 180 * np.pi)
        return deg2m_lon, deg2m_lat

    def get_map_dims(self):  # , fig_size_in_inches, colorbar=False):
        """Returns the map dimension width, height (in meters. FIXME: check)
        for a map in projection 'local'"""

        max_lons, min_lons = self.max_lons, self.min_lons
        # lon_0, lat_0 = self.lon_0, self.lat_0
        lat_0 = self.lat_0
        # lons, lats = self.lons, self.lats
        lats = self.lats
        deg2m_lon, deg2m_lat = self.deg2m(lat_0)

        if len(lats) > 1:
            height = (max(lats) - min(lats)) * deg2m_lat
            width = (max_lons - min_lons) * deg2m_lon
            margin = 0.2 * (width + height)
            height += margin
            width += margin
        else:
            height = 2.0 * deg2m_lat
            width = 5.0 * deg2m_lon

        return width, height

    @staticmethod
    def adjust_fig_dims(width, height, fig, colorbar=False):
        """Returns the fig dimensions
        :param width: the map width (in meters? check)
        :param height: the map height
        """
        # do intelligent aspect calculation for local projection
        # adjust to figure dimensions
        w, h = fig.get_size_inches()
        aspect = w / h
        if colorbar:
            aspect *= 1.2
        if width / height < aspect:
            width = height * aspect
        else:
            height = width / aspect

        return width, height

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

    def get_parallels(self, width, height):
        lat_0, deg2m_lat = self.lat_0, self.deg2m_lat
        N1 = int(np.ceil(height / max(width, height) * 8))
        # N2 = int(np.ceil(width / max(width, height) * 8))
        parallels = self.linspace(lat_0 - height / 2 / deg2m_lat,
                                  lat_0 + height / 2 / deg2m_lat, N1)
        return parallels

    def get_meridians(self, width, height):
        lon_0, deg2m_lon = self.lon_0, self.deg2m_lon
        N2 = int(np.ceil(width / max(width, height) * 8))
        meridians = self.linspace(lon_0 - width / 2 / deg2m_lon,
                                  lon_0 + width / 2 / deg2m_lon, N2)
        meridians[meridians > 180] -= 360
        return meridians


def plot_basemap(lons,
                 lats,
                 size,
                 color,
                 labels=None,
                 projection='global',
                 resolution='l',
                 continent_fill_color='0.8',
                 water_fill_color='1.0',
                 colormap=None,
                 # colorbar=None,
                 marker="o",
                 title=None,
                 colorbar_ticklabel_format=None,
                 show=True,
                 fig=None,
                 **kwargs):  # @UnusedVariable
    """
    Creates a basemap plot with a data point scatter plot.

    :type lons: list/tuple of floats
    :param lons: Longitudes of the data points.
    :type lats: list/tuple of floats
    :param lats: Latitudes of the data points.
    :type size: float or list/tuple of floats
    :param size: Size of the individual points in the scatter plot.
    :type color: list/tuple of floats (or objects that can be
        converted to floats, like e.g.
        :class:`~obspy.core.utcdatetime.UTCDateTime`)
    :param color: Color information of the individual data points to be
        used in the specified color map (e.g. origin depths,
        origin times).
    :type labels: list/tuple of str
    :param labels: Annotations for the individual data points.
    :type projection: str, optional
    :param projection: The map projection. Currently supported are
        * ``"global"`` (Will plot the whole world.)
        * ``"ortho"`` (Will center around the mean lat/long.)
        * ``"local"`` (Will plot around local events)
        Defaults to "global"
    :type resolution: str, optional
    :param resolution: Resolution of the boundary database to use. Will be
        based directly to the basemap module. Possible values are
        * ``"c"`` (crude)
        * ``"l"`` (low)
        * ``"i"`` (intermediate)
        * ``"h"`` (high)
        * ``"f"`` (full)
        Defaults to ``"l"``. For compatibility, you may also specify any of the
        Cartopy resolutions defined in :func:`plot_cartopy`.
    :type continent_fill_color: Valid matplotlib color, optional
    :param continent_fill_color:  Color of the continents. Defaults to
        ``"0.9"`` which is a light gray.
    :type water_fill_color: Valid matplotlib color, optional
    :param water_fill_color: Color of all water bodies.
        Defaults to ``"white"``.
    :type colormap: str, any matplotlib colormap, optional
    :param colormap: The colormap for color-coding the events as provided
        in `color` kwarg.
        The event with the smallest `color` property will have the
        color of one end of the colormap and the event with the highest
        `color` property the color of the other end with all other events
        in between.
        Defaults to None which will use the default matplotlib colormap.
    :type colorbar: bool, optional
    :param colorbar: When left `None`, a colorbar is plotted if more than one
        object is plotted. Using `True`/`False` the colorbar can be forced
        on/off.
    :type title: str
    :param title: Title above plot.
    :type colorbar_ticklabel_format: str or function or
        subclass of :class:`matplotlib.ticker.Formatter`
    :param colorbar_ticklabel_format: Format string or Formatter used to format
        colorbar tick labels.
    :type show: bool
    :param show: Whether to show the figure after plotting or not. Can be used
        to do further customization of the plot before showing it.
    :type fig: :class:`matplotlib.figure.Figure`
    :param fig: Figure instance to reuse, returned from a previous
        :func:`plot_basemap` call. If a previous basemap plot is reused, any
        kwargs regarding the basemap plot setup will be ignored (i.e.
        `projection`, `resolution`, `continent_fill_color`,
        `water_fill_color`). Note that multiple plots using colorbars likely
        are problematic, but e.g. one station plot (without colorbar) and one
        event plot (with colorbar) together should work well.
    """

    if fig is None:
        fig = plt.figure()

        # setup the axes dimensions
        map_ax_dims, cm_ax_dims = get_axes_dims(projection, colorbar=False)
        map_ax = fig.add_axes(map_ax_dims)
        if cm_ax_dims:
            cm_ax = fig.add_axes(cm_ax_dims)

        if projection == 'global':
            bmap = Basemap(projection='moll', lon_0=round(np.mean(lons), 4),
                           resolution=_BASEMAP_RESOLUTIONS[resolution],
                           ax=map_ax)
        elif projection == 'ortho':
            bmap = Basemap(projection='ortho',
                           resolution=_BASEMAP_RESOLUTIONS[resolution],
                           area_thresh=1000.0, lat_0=round(np.mean(lats), 4),
                           lon_0=round(np.mean(lons), 4), ax=map_ax)
        elif projection == 'local':

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

            handler = LocalProjHandler(lons, lats)
            width, height = handler.adjust_fig_dims(*handler.get_map_dims(),
                                                    fig=fig,
                                                    colorbar=False)

            lon_0, lat_0 = handler.lon_0, handler.lat_0

            bmap = Basemap(projection='aea',
                           resolution=_BASEMAP_RESOLUTIONS[resolution],
                           area_thresh=1000.0, lat_0=round(lat_0, 4),
                           lon_0=round(lon_0, 4),
                           width=width, height=height, ax=map_ax)
            # FIXME: not most elegant way to calculate some round lats/lons

            parallels = handler.get_parallels(width, height)

            # Old basemap versions have problems with non-integer parallels.
            try:
                bmap.drawparallels(parallels, labels=[0, 1, 1, 0])
            except KeyError:
                parallels = sorted(list(set(map(int, parallels))))
                bmap.drawparallels(parallels, labels=[0, 1, 1, 0])

            # THIS HAS BEEN SET IN get_lon0lat0
#             if min(lons) < -150 and max(lons) > 150:
#                 lon_0 %= 360

            meridians = handler.get_meridians(width, height)
            bmap.drawmeridians(meridians, labels=[1, 0, 0, 1])
        else:
            msg = "Projection '%s' not supported." % projection
            raise ValueError(msg)

        # draw coast lines, country boundaries, fill continents.
        map_ax.set_axis_bgcolor(water_fill_color)
        # bmap.drawcoastlines(color="0.4")
        # bmap.drawcountries(color="0.75")
        # bmap.fillcontinents(color=continent_fill_color,
        #                    lake_color=water_fill_color)

        # draw the edge of the bmap projection region (the projection limb)
        bmap.drawmapboundary(fill_color=water_fill_color)
        # draw lat/lon grid lines every 30 degrees.
        # if local projection, we already did it
        if projection != 'local':
            bmap.drawmeridians(np.arange(-180, 180, 30))
            bmap.drawparallels(np.arange(-90, 90, 30))
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
    # plot labels
    if labels:
        if 100 > len(lons) > 1:
            for name, xpt, ypt, _colorpt in zip(labels, x, y, color):
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

    # scatter plot is removing valid x/y points with invalid color value,
    # so we plot those points separately.
    try:
        nan_points = np.isnan(np.array(color, dtype=np.float))
    except ValueError:
        # `color' was not a list of values, but a list of colors.
        pass
    else:
        if nan_points.any():
            x_ = np.array(x)[nan_points]
            y_ = np.array(y)[nan_points]
            size_ = np.array(size)[nan_points]
            scatter = bmap.scatter(x_, y_, marker=marker, s=size_, c="0.3",
                                   zorder=10, cmap=None)
    scatter = bmap.scatter(x, y, marker=marker, s=size, c=color,
                           zorder=10, cmap=colormap)

    if title:
        plt.suptitle(title)

    if show:
        plt.show()

    return fig