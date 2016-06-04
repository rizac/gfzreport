# -*- coding: utf-8 -*-
"""
   Implements the map-image directive which behaves like an image. The file argument is a csv file,
   with the first row as header and AT LEST the columns denoting:
    - latitudes (either denoted by the string 'lats', 'latitudes', 'lat' or 'latitude', case insensitive)
    - longitudes ('lons', 'longitudes', 'lon' or 'longitude', case insensitive)
    - labels ('name', 'names', 'label', 'labels', 'caption', 'captions', case insensitive)
   And optionally (only for pdf/latex rendering!):
    - sizes ('size' or 'sizes', case insensitive)
    - colors ('color' or 'colors', case insensitive)
"""

# NOTE: TEMPLATE TO BE USED. DOWNLOADEDFROM THE SPHINX EXTENSIONS HERE:
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa?at=default
from docutils import nodes  # , utils
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import images
# from sphinx.util.compat import Directive
from uuid import uuid4  # FIXME: sphinx provides a self uuid!
from sphinx.util import ensuredir
import os
import re
from reportgen.map import plotmap
import pandas as pd
import reportgen.core.extensions.setup as stp

_OVERWRITE_IMAGE_ = False  # set to True while debugging / testing

csv_headers = {
               "lats": re.compile("lat(?:itude)?s?", re.IGNORECASE),
               "lons": re.compile("lon(?:gitude)?s?", re.IGNORECASE),
               "labels": re.compile("(?:names?|captions?|labels?)", re.IGNORECASE),
               "sizes": re.compile("sizes?", re.IGNORECASE),
               "colors": re.compile("colors?", re.IGNORECASE)
               }


def rename(dframe):
    "renames columns according to csv_headers defined above"
    newcols = {}
    for colname in dframe.columns:
        newcolname = colname
        for normalized_colname in csv_headers:
            if csv_headers[normalized_colname].match(colname):
                if normalized_colname not in newcols:
                    newcolname = normalized_colname
                break
        newcols[colname] = newcolname
    dframe.rename(columns=newcols, inplace=True)
    return dframe


# note: we override node cause nodes might be called also from a parent map-image
# so that some functionalities needs to be set here and not in the MapImdDirective below
class mapimg(nodes.image):
    # class dict mapping option specific map directives keys to
    # the map keywords

    def __init__(self, rawsource='', *children, **attributes):
        super(mapimg, self).__init__(rawsource, *children, **attributes)
        # parse the csv and store attributes here
        try:
            uri = directives.uri(attributes['uri'])
            filepath = stp.relfn2path(uri)
            self.attributes['__csv_mod_time__'] = os.stat(filepath)[8]
            pts_df = rename(pd.read_csv(filepath))
            # convert to a list of column_name: [value1, ... ] more suitable
            pts_dict = pts_df.to_dict('list')
            self.attributes['__data__'] = pts_dict
        except ValueError:
            pass  # FIXME: do something?
#             document = self.reporter.document
#             return [document.reporter.warning(str(verr), line=self.lineno)]
            # image_node.points_error_msg = str(verr)


class MapImgDirective(images.Image):  # FIXME: to be tested! SHOULD WE EVER CALL IT ACTUALLY??
    """
    Directive that builds plots using a csv file
    """

    own_option_spec = {
                      'margins_in_km': lambda arg: arg or None,
                      'epsg_projection': lambda arg: arg or None,
                      'arcgis_image_service': lambda arg: arg or None,
                      'arcgis_image_xpixels': lambda arg: arg or None,
                      'arcgis_image_dpi': lambda arg: arg or None
                      }

    option_spec = images.Image.option_spec.copy()  # @UndefinedVariable
    option_spec.update(own_option_spec)

    def run(self):
        imgnodes = images.Image.run(self)
        # replace image nodes (theoretically, at most one) with mapimg nodes
        # note that self.options has already been
        # worked out in the super constructor
        # important cause it does checks and modifications
        imgnodes[0] = mapimg(self.block_text, **self.options)
        return imgnodes


def visit_mapimg_node_html(self, node):
    """self seems to be the app Translator object. Source code of the Sphinx object here:
    http://www.sphinx-doc.org/en/stable/_modules/sphinx/application.html
    """

    data = node.attributes['__data__']  # FIXME: error!
    _uuid = get_hash(data)

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

#     url = baseurl + urllib.urlencode(params)
#     self.body.append(iframe % url)


def get_map_from_csv(**map_args):
    # FIXME: do float check BEFORE, to save time in case of error!
    try:
        f = plotmap.plot_basemap(**map_args)
        # see http://matplotlib.org/basemap/users/geography.html
        # from plot_map (which calls plot_basemap), we can access the bmap from fig.bmap:
        # f.bmap.shadedrelief()
        # f.bmap.etopo()
    except ImportError:
        import matplotlib.pyplot as plt
        f = plt.figure()

    return f


def get_hash(node):
    lst = [node['__csv_mod_time__']]
    for arg in MapImgDirective.own_option_spec:
        lst.append(node.attributes.get(arg, None))

    return hash(tuple(node))


# from sphinx.writers.latex import LaTeXTranslator
def visit_mapimg_node_latex(self, node):
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


def depart_mapimg_node_latex(self, node):
    self.depart_image(node)


def depart_mapimg_node_html(self, node):
    pass


def setup(app):
    app.add_node(mapimg,
                 html=(visit_mapimg_node_html, depart_mapimg_node_html),
                 latex=(visit_mapimg_node_latex, depart_mapimg_node_latex))
    app.add_directive('map-image', MapImgDirective)
