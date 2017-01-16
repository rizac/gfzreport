# -*- coding: utf-8 -*-
"""
   Implements the map-figure directive which behaves like an image. The directive acts as acsv
   table (although it produces a figure). The csv content must have AT LEST the columns denoting:
    - latitudes (either denoted by the string 'lats', 'latitudes', 'lat' or 'latitude',
    case insensitive)
    - longitudes ('lons', 'longitudes', 'lon' or 'longitude', case insensitive)
    - labels ('name', 'names', 'label', 'labels', 'caption', 'captions', case insensitive)
   And optionally (only for pdf/latex rendering!):
    - sizes ('size' or 'sizes', case insensitive)
    - colors ('color' or 'colors', case insensitive)
"""

# NOTE: TEMPLATE TO BE USED. DOWNLOADEDFROM THE SPHINX EXTENSIONS HERE:
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa?at=default

from reportbuild.core.extensions.csvfigure import CsvFigureDirective
from docutils import nodes
from sphinx.util import ensuredir
import os
import re
from reportbuild.map import plotmap
import inspect
from itertools import izip


_OVERWRITE_IMAGE_ = False  # set to True while debugging / testing to force map image creation
# (otherwise, it check if the image is already present according to the arguments given)

_DIRECTIVE_NAME = "map-figure"

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

    # FIXME: add class support, add width and height support, add labels, colors and markers support

    data = node.attributes['__plotmapargs__']  # FIXME: error!
    _uuid = node._data_hash__

    markers = []
    for lon, lat, labl in zip(data['lons'], data['lats'], data['labels']):
        markers.append('[' + str(lat) + ',' + str(lon) + ']')

    add_to_map_js = "        \n".join("markersArray.push(L.marker(" + mrk + ").addTo(map));"
                                      for mrk in markers)

    html = """
        <div id='map{0}' class=map></div>
        <script>
        /*L.mapbox.accessToken = '{0}';
        var snapshot = document.getElementById('snapshot');*/

        var map = L.map('map{0}');

        var layer = L.esri.basemapLayer('Topographic').addTo(map);

        var markersArray = [];

        {1}

        // fit bounds according to markers:

        var group = new L.featureGroup(markersArray);
        map.fitBounds(group.getBounds());

        /*document.getElementById('snap').addEventListener('click', function() {{
            leafletImage(map, doImage);
        }});

        function doImage(err, canvas) {{
            var img = document.createElement('img');
            var dimensions = map.getSize();
            img.width = dimensions.x;
            img.height = dimensions.y;
            img.src = canvas.toDataURL();
            snapshot.innerHTML = '';
            snapshot.appendChild(img);
        }}*/
        </script>
        """.format(str(_uuid), add_to_map_js)

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
    self is the builder, although not well documented FIXME: setuo this doc!
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
