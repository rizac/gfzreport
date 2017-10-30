# -*- coding: utf-8 -*-
"""
   Implements a directive which behaves like a figure with a geomap background.
   The directive acts as a csv table (although it produces a figure).
   The csv content must have AT LEST the columns denoting:
    - latitudes (either denoted by the string 'lats', 'latitudes', 'lat' or 'latitude',
    case insensitive)
    - longitudes ('lons', 'longitudes', 'lon' or 'longitude', case insensitive)
    - labels ('name', 'names', 'label', 'labels', 'caption', 'captions', case insensitive)
   And optionally (only for pdf/latex rendering!):
    - sizes ('size' or 'sizes', case insensitive)
    - colors ('color' or 'colors', case insensitive)

    NOTES:

     - Html does not support marker type: network stations will be displayed via leaflet standard
         marker, non-network stations via circles
     - Html does not support all legend positions: 'bottom' will be displayed 'bottomright',
      'top' and 'right' will be displayed 'topright', 'left' will be displayed 'topleft'
     - Html sizes are the circle diameter in pixels^2, in pixels. In latex, in points ^2 (I guess
         the diameter but there is no mention).
       This is to render
       approximately the same in latex and html (tested with the default value)
     - You need to override the
        `sphinx templating<http://www.sphinx-doc.org/en/1.5.1/templating.html#script_files>`_
        with `these two lines of javascript:<http://esri.github.io/esri-leaflet/examples/>`_
"""

# NOTE: TEMPLATE TO BE USED. DOWNLOADEDFROM THE SPHINX EXTENSIONS HERE:
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa?at=default

from docutils import nodes
from sphinx.util import ensuredir
import os
import re
import inspect
from itertools import izip
from gfzreport.sphinxbuild.map import plotmap, torgba
from gfzreport.sphinxbuild.core.extensions.csvfigure import CsvFigureDirective
import math


_OVERWRITE_IMAGE_ = False  # set to True while debugging / testing to force map image creation
# (otherwise, it check if the image is already present according to the arguments given)

_DIRECTIVE_NAME = "mapfigure"

csv_headers = {
               "lats": re.compile("lat(?:itude)?s?", re.IGNORECASE),
               "lons": re.compile("lon(?:gitude)?s?", re.IGNORECASE),
               "labels": re.compile("(?:names?|captions?|labels?)", re.IGNORECASE),
               "sizes": re.compile("sizes?", re.IGNORECASE),
               "colors": re.compile("colors?", re.IGNORECASE),
               "markers": re.compile("markers?", re.IGNORECASE),
               "legendlabels": re.compile("legends?", re.IGNORECASE),
               }


class mapnode(nodes.Element):
    # class dict mapping option specific map directives keys to
    # the map keywords

    # IMPORTANT: __init__ must take exactly these arguments otherwise
    # sphinx.util.nodes._new_copy (used internally by sphinx) does not work
    def __init__(self, rawsource='', *children, **attributes):
        super(mapnode, self).__init__(rawsource, *children, **attributes)
        # create a custom attribute __plotmap__ in which we set all plotmap attributes:
        plotmapdata = dict(attributes["__parsed_content__"])  # copy it
        for key, val in attributes.iteritems():
            if key.startswith("map_"):
                plotmapdata[key[4:]] = val
        self.attributes["__plotmapargs__"] = plotmapdata

        # make a normalized string by replacing newlines:
        r = re.compile("\\s*\\n+\\s*")
        strhash = r.sub(' ', rawsource).strip()
        self._data_hash__ = hash(strhash)


def get_defargs(exclude=['lons', 'lats', 'labels', 'legendlabels', 'markers', 'colors', 'show'],
                **overriden_defaults):
    """Returns a dict of arguments for the MapImgDirective mapped to their defaults
    These are automatically created according to the plotmap function (using inspect module).
    Only arguments whose default is string (py2-3 compatible), numeric or boolean are accepted
    **Note that the keys of the returned dict are prefixed with 'map_'**
    :param overriden_defaults: optional keyword argument that will override a default value of
    a plotmap argument. If a key is not present in the defaults it will be ignored
    """
    try:
        # we want to forward plotmap arguments as directive options. Only arguments
        # with string, numeric or boolean defaults are "optionable". Deal with py2/ py3 problem:
        _valid_classes = (str, unicode, float, int, bool)
    except NameError:
        _valid_classes = (str, float, int, bool)  # python 3

    # exclude plotmap args that are set into the directive body:
    no_opt_args = set(exclude)
    # get optional plotmap args and returns their defaults:
    insp = inspect.getargspec(plotmap)
    ret = {}
    for arg, val in izip(insp.args[-len(insp.defaults):], insp.defaults):
        if arg not in no_opt_args and type(val) in _valid_classes:
            ret[arg] = val
    # add also the following arguments for plotmap kwargs:
    ret['meridians_linewidth'] = 1
    ret['parallels_linewidth'] = 1

    for key, val in overriden_defaults.iteritems():
        if key in ret:
            ret[key] = val

    # make directive options prefixed with 'map_' to avoid confusion with other rst options
    # inherited from CsvFigureDirective
    return {('map_%s' % key): val for key, val in ret.iteritems()}


class MapImgDirective(CsvFigureDirective):
    """
    Directive that builds plots using a csv file
    """
    # we need to hardcode ownoptionspec dynamically generating them from plotmap
    # arguments is unfeasable
    own_option_spec = dict(map_sizes=lambda val: float(val),
                           map_fontsize=lambda val: val or None,
                           map_fontweight=lambda val: val,
                           map_fontcolor=lambda val: val,
                           map_labels_h_offset=lambda val: val or 0,
                           map_labels_v_offset=lambda val: val or 0,
                           map_mapmargins=lambda val: val or 0,
                           map_figmargins=lambda val: val or 0,
                           map_arcgis_service=lambda val: val,
                           map_arcgis_xpixels=lambda val: int(val),
                           map_urlfail=lambda val: val,
                           map_maxmeridians=lambda val: int(val),
                           map_maxparallels=lambda val: int(val),
                           map_meridians_linewidth=lambda val: float(val),
                           map_parallels_linewidth=lambda val: float(val),
                           map_legend_pos=lambda val: val,
                           map_legend_borderaxespad=lambda val: float(val),
                           map_legend_ncol=lambda val: int(val),
                           map_title=lambda val: val or None,)

    option_spec = CsvFigureDirective.option_spec.copy()  # @UndefinedVariable
    option_spec.update(own_option_spec)

    def run(self):

        nodez = CsvFigureDirective.run(self)

        data = {}
        column_indices = {}

        for row, col, is_row_header, is_col_stub, node, node_text in self.itertable(nodez):
            if is_col_stub:
                raise ValueError("Error in '%s' directive: option :stub-columns: not permitted"
                                 % _DIRECTIVE_NAME)
            if is_row_header:
                if row > 0:
                    raise ValueError("Error in '%s' directive: provide only one row header"
                                     "(see options :header: and :header-rows:)" % _DIRECTIVE_NAME)
                if node_text:
                    dict_key = node_text
                    for normalized_col_name in csv_headers:
                        if csv_headers[normalized_col_name].match(node_text):
                            dict_key = normalized_col_name  # which ADDS the key if not present!
                            break
                    column_indices[col] = dict_key
                    data[dict_key] = []
            else:
                if not data:
                    raise ValueError("Error in '%s' directive: provide one row header"
                                     "(see options :header: and :header-rows:)" % _DIRECTIVE_NAME)

                if col not in column_indices:
                    continue

                data[column_indices[col]].append(node_text or "")

        map_node = mapnode(self.block_text, __parsed_content__=data, **self.options)
        self.get_table_node(nodez).replace_self(map_node)

        return nodez


def visit_map_node_html(self, node):
    """self seems to be the app Translator object. Source code of the Sphinx object here:
    http://www.sphinx-doc.org/en/stable/_modules/sphinx/application.html
    """

    def esc(string):
        """escapes quotes"""
        return string.replace('"', '\\"')

    # FIXME: add class support, add width and height support, add labels, colors and markers support

    data = node.attributes['__plotmapargs__']  # FIXME: error!
    _uuid = node._data_hash__

    bordercolor = "#000000"
    pt_size = math.sqrt(data['sizes'])
    markers = []
    for lon, lat, label, color in izip(data['lons'], data['lats'], data['labels'],
                                       data['colors']):
        try:
            lat = float(lat)
            lon = float(lon)
            _, _, _, alpha = torgba(color)
            # for info on options, see:
            # http://leafletjs.com/reference-1.0.0.html#path
            markers.append(('L.circleMarker([%f, %f], '
                            '{radius: %f, fillColor: "%s", fillOpacity: %f, weight: 1, '
                            'opacity: 0.5, color: "%s"}).'
                            'bindPopup("%s<br>lat: %f<br>lon: %f")') %
                           (lat, lon, pt_size, str(color[:7]), alpha, bordercolor,
                            esc(str(label)), lat, lon))
        except (TypeError, ValueError):
            pass

    add_to_map_js = "    \n".join("markersArray.push(%s.addTo(map));" % mrk for mrk in markers)

    legends_js = []
    for leg, color in izip(data['legendlabels'], data['colors']):
        if leg:
            try:
                r, g, b, alpha = torgba(color)
                # pt_size in css is the diameter, multiply times two:
                # Moreover, we need to set rgba colors to support fill opacity only
                rgba = "rgba(%d, %d, %d, %f)" % (r * 255, g * 255, b * 255, alpha)
                legends_js.append(("<i style='display:inline-block; border:1px solid %s;"
                                   "background:%s;width:%fpx;height:%fpx;"
                                   "border-radius:%fpx'></i>&nbsp;%s")
                                  % (bordercolor, rgba, 2*pt_size, 2*pt_size, pt_size, esc(leg)))
            except (TypeError, ValueError):
                pass

    legend_js = ""
    if legends_js:
        leg_pos = data['legend_pos']
        # leaflet supports only 'bottomleft' 'bottomright', 'topleft' 'topright', so:
        leg_pos = 'topright' if leg_pos in ('top', 'right') else 'topleft' \
            if leg_pos == 'left' else 'bottomright'

        legend_js = """var legend = L.control({position: '%s'});
    legend.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');
        div.innerHTML = "%s";
        return div;
    };
    legend.addTo(map);""" % (leg_pos, "<br>".join(l for l in legends_js))

    html = """
<div id='map{0}' class=map></div>
<script>
    var map = L.map('map{0}');
    var layer = L.esri.basemapLayer('Topographic').addTo(map);
    var markersArray = [];
    {1}
    // fit bounds according to markers:
    var group = new L.featureGroup(markersArray);
    map.fitBounds(group.getBounds());
    var rect = L.rectangle(group.getBounds(), {{color: 'black', fill: false, dashArray: "1, 3", weight: .5}}).addTo(map);
    group.bringToFront();
    {2}
</script>
""".format(str(_uuid), add_to_map_js, legend_js)

    self.body.append(html)


def get_map_from_csv(**map_args):
    # FIXME: do float check BEFORE, to save time in case of error!
    try:
        f = plotmap(**map_args)
        # see http://matplotlib.org/basemap/users/geography.html
        # from plot_map (which calls plot_basemap), we can access the bmap from fig.bmap:
        # f.bmap.shadedrelief()
        # f.bmap.etopo()
    except ImportError:
        import matplotlib.pyplot as plt
        f = plt.figure()

    return f


def visit_map_node_latex(self, node):
    """
    self is the app, although not well documented FIXME: setuo this doc!
    http://www.sphinx-doc.org/en/stable/_modules/sphinx/application.html
    """
    _uuid = node._data_hash__
    fname = 'map_plot-%s.png' % str(_uuid)
    outfn = os.path.join(self.builder.outdir, fname)

    if _OVERWRITE_IMAGE_ or not os.path.isfile(outfn):
        data = node.attributes['__plotmapargs__']
        fig = get_map_from_csv(**data)
        ensuredir(os.path.dirname(outfn))
        fig.savefig(outfn)

    node['uri'] = fname
    self.visit_image(node)


def depart_map_node_latex(self, node):
    self.depart_image(node)


def depart_map_node_html(self, node):
    pass


def setup(app):
    app.add_node(mapnode,
                 html=(visit_map_node_html, depart_map_node_html),
                 latex=(visit_map_node_latex, depart_map_node_latex))
    app.add_directive(_DIRECTIVE_NAME, MapImgDirective)
