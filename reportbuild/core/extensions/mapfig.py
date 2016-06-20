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
from StringIO import StringIO

_OVERWRITE_IMAGE_ = False  # set to True while debugging / testing to force map image creation
# (otherwise, it check if the image is already present according to the arguments given)

_DIRECTIVE_NAME = "map-figure"

csv_headers = {
               "lats": re.compile("lat(?:itude)?s?", re.IGNORECASE),
               "lons": re.compile("lon(?:gitude)?s?", re.IGNORECASE),
               "labels": re.compile("(?:names?|captions?|labels?)", re.IGNORECASE),
               "sizes": re.compile("sizes?", re.IGNORECASE),
               "colors": re.compile("colors?", re.IGNORECASE),
               "markers": re.compile("markers?", re.IGNORECASE)
               }


class mapnode(nodes.Element):
    # class dict mapping option specific map directives keys to
    # the map keywords

    def __init__(self, rawsource='', *children, **attributes):
        super(mapnode, self).__init__(rawsource, *children, **attributes)
        if self.attributes.get("__data__", None) is None:
            self.attributes["__data__"] = {c: [] for c in csv_headers.keys()}
        if self.attributes.get("__data_hash__", None) is None:
            self.attributes["__data_hash__"] = build_hash(self.attributes["__data__"])


def build_hash(map_date):
    """
    Builds the hash for the given map_date (a dict of lists of strings)
    and returns the hash (integer)
    """
    # Note also below: we provide ALL arguments as strings, as calculating the hash of big
    # value with mixed types (e.g. None and strings) seems NOT to be consistent
    # It's probably due to the nature of hash algorithms but we didn't find any
    # on the internet
    sio = StringIO()
    for key in csv_headers:
        sio.write(key)
        if key in map_date:
            sio.write(",")
            sio.write(",".join(map_date[key]))
        sio.write("\n")
    ret = hash(sio.getvalue())
    sio.close()
    return ret


class MapImgDirective(CsvFigureDirective):
    """
    Directive that builds plots using a csv file
    """

    own_option_spec = {
                      'margins_in_km': lambda arg: arg or None,
                      'epsg_projection': lambda arg: arg or None,
                      'arcgis_image_service': lambda arg: arg or None,
                      'arcgis_image_xpixels': lambda arg: arg or None,
                      'arcgis_image_dpi': lambda arg: arg or None,
                      'labels_h_offset_in_km': lambda arg: arg or None,
                      'labels_v_offset_in_km': lambda arg: arg or None,
                      }

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

        self.options["__data__"] = data
        map_node = mapnode(self.block_text, **self.options)
        self.get_table_node(nodez).replace_self(map_node)

        return nodez


def visit_map_node_html(self, node):
    """self seems to be the app Translator object. Source code of the Sphinx object here:
    http://www.sphinx-doc.org/en/stable/_modules/sphinx/application.html
    """

    # FIXME: add class support, add width and height support, add labels, colors and markers support

    data = node.attributes['__data__']  # FIXME: error!
    _uuid = get_hash(node)

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


def get_hash(node):
    lst = [node['__data_hash__']]
    for arg in MapImgDirective.own_option_spec:
        lst.append(node.attributes.get(arg, ""))
        # Note above: using None as default seems not to return an unique hash
        # hash calculation requires algorithms which are difficult to find on google
        # provide EVERYTHING as string and results seem to be consistent
    return hash(tuple(lst))


# from sphinx.writers.latex import LaTeXTranslator
def visit_map_node_latex(self, node):
    """
    self is the builder, although not well documented FIXME: setuo this doc!
    http://www.sphinx-doc.org/en/stable/_modules/sphinx/application.html
    """
    _uuid = get_hash(node)
    fname = 'map_plot-%s.png' % str(_uuid)
    outfn = os.path.join(self.builder.outdir, fname)

    if _OVERWRITE_IMAGE_ or not os.path.isfile(outfn):
        data = node.attributes['__data__']
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
