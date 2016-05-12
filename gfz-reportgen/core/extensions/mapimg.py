# -*- coding: utf-8 -*-
"""
   FIXME: write doc!!

    
"""

# NOTE: TEMPLATE TO BE USED. DOWNLOADEDFROM THE SPHINX EXTENSIONS HERE:
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa?at=default
from docutils import nodes  # , utils
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import images
from sphinx.util.compat import Directive
from uuid import uuid4  # FIXME: sphinx provides a self uuid!
from sphinx.util import ensuredir
import os
from map import plotmap
import pandas as pd
import csv
import numpy as np
from core.utils.hash import get_hash as utils_get_hash
from core.extensions.setup import relfn2path

def read_csv(filepath, required_columns, additional_delimiters=[' ', ';']):
    """
        Reads filepath as csv file returning a list of rows. Each rows is a dict of fields:values,
        where fields is parsed from the csv header row (first row)
        :param required_columns: a list of strings denoting the required columns. A Value Error
        is raised if the csv file does not contain at least those columns. Set to None or the empty
        list for skipping the check
        :param additional_delimiters: (defaults to [' ', ';'] if missing). A list of strings
        denoting the additional delimiters between fields. The function iterates over all delimiters
        (attempting first of all to parse the csv with no delimiter, the default) and then iterating
        over additional_delimiters (if any). The function stops and returns the dict as soon as the
        csv file can be parsed (i.e., it can be read and has at least required_columns fields,
        see above)
        :raise ValueError: if for any reason the csv cannot be read or does not have the required
        columns
        :return: a list of dicts of the form {row1: value1, ..., rowN: valueN}
    """
    filepath = relfn2path(filepath)
    ret = None
    if not additional_delimiters:
        additional_delimiters = []
    additional_delimiters.insert(0, None)

    if not required_columns:
        required_columns = []
    try:
        with open(filepath) as csvfile:
            for i, delim in enumerate(additional_delimiters):
                if i > 0:
                    csvfile.seek(0)  # return to first byte

                reader = csv.DictReader(csvfile) if delim is None else \
                    csv.DictReader(csvfile, delimiter=delim)
                for row in reader:
                    if all(r in row for r in required_columns):
                        ret = [row]
                        for row in reader:  # NOTE: does NOT restart iteration from first item
                            ret.append(row)
                    break
                if ret is not None:
                    break
    except (csv.Error, IOError) as exc:
        raise ValueError(str(exc))

    if ret is None:
        raise ValueError("%s seems not to contain "
                         "all header fields: %s" % (filepath, ",".join(required_columns)))

    return ret


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
            self._custom_data = {}
            # FIXME: check hash
            # self._custom_data['id'] = get_hashid((attributes[key] for key in sorted(attributes)))
            pts = read_csv(uri, [attributes[k] for k in ('lat_key', 'lon_key', 'name_key')])
            pts = transpose_csv(pts)
            self._custom_data['data'] = pts
        except ValueError as verr:
            pass  # FIXME: do something?
#             document = self.reporter.document
#             return [document.reporter.warning(str(verr), line=self.lineno)]
            # image_node.points_error_msg = str(verr)


class MapImgDirective(images.Image):
    """
    Directive that builds plots using a csv file
    """
    own_option_spec = dict(
        lat_key=lambda arg: arg or 'lat',
        lon_key=lambda arg: arg or 'lon',
        name_key=lambda arg: arg or 'name',

    )

    option_spec = images.Figure.option_spec.copy()  # @UndefinedVariable
    option_spec.update(own_option_spec)

    def run(self):
        nodes = images.Image.run(self)
        # replace image nodes (theoretically, at most one) with mapimg nodes
        for i, nod in enumerate(nodes):
            if isinstance(nod, nodes.image):
                # note that self.options has already been
                # worked out in the super constructor
                # important cause it does checks and modifications
                nodes[i] = mapimg(self.block_text, **self.options)

        return nodes


def transpose_csv(csv_data):  # FIXME: use pandas read_csv
    """
        Transposes csv_data, from a list of dicts into a dict of lists
        :param csv_data: the output of read_csv
    """
    df = pd.DataFrame(csv_data)
    # given the nature of points_dict (a list of dicts)
    # the function above does all the trick
    return df.to_dict('list')


def get_data(node):
    """
        Returns the values id, lons, lats, labels (lists) for all points on a map
        id is an integer, lons, lats labels are lists of the same size
    """
    data = node._custom_data['data']
    opts = node.attributes

    lons = np.array(data[opts['lon_key']], dtype=float)
    lats = np.array(data[opts['lat_key']], dtype=float)
    labels = data[opts['name_key']]

    return dict(lons=lons, lats=lats, labels=labels)


def visit_mapimg_node_html(self, node):
    """self seems to be the app Translator object. Source code of the Sphinx object here:
    http://www.sphinx-doc.org/en/stable/_modules/sphinx/application.html
    """

    data = get_data(node)  # FIXME: error!
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


def get_hash(node_data):
    func = plotmap.plot_basemap
    args = func.func_code.co_varnames[:func.func_code.co_argcount]
    defvals = func.func_defaults
    params = {}
    # set what arguments need to be hashable. Orders does not matter, as the order in which they
    # are declared in func does
    hashableargs = ['lons',
                    'lats',
                    'margins_in_km',
                    'epsg_projection',
                    'arcgis_image_service'
                    'arcgis_image_xpixels',
                    'arcgis_image_dpi']
    for i, arg in enumerate(args):
        if arg not in hashableargs:
            continue
        if arg in node_data:
            params[arg] = node_data[arg]
        else:
            params[arg] = defvals[i-(len(args) - len(defvals))]
    try:
        return utils_get_hash(params)
    except TypeError:  # if something is not hashable, return an uuid. Chances that we already used
        # it are basically zero
        return uuid4()


# from sphinx.writers.latex import LaTeXTranslator
def visit_mapimg_node_latex(self, node):
    """self is the builder, although not well documented FIXME: setuo this doc!
    http://www.sphinx-doc.org/en/stable/_modules/sphinx/application.html
    """

    data = get_data(node)
    _uuid = get_hash(data)
    fname = 'map_plot-%s.png' % str(_uuid)
    outfn = os.path.join(self.builder.outdir, fname)

    if not os.path.isfile(outfn):
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
