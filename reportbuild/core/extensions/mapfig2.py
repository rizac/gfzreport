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
from docutils import nodes  # , utils
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import images
from docutils.parsers.rst.directives.tables import CSVTable
# from sphinx.util.compat import Directive
from uuid import uuid4  # FIXME: sphinx provides a self uuid!
from sphinx.util import ensuredir
import os
import re
import csv
from reportbuild.map import plotmap
import pandas as pd
import reportbuild.core.extensions.setup as stp
from docutils.nodes import Text
# from docutils.utils import SystemMessagePropagation
# from docutils.nodes import title as title_node
# from docutils.statemachine import StringList

_OVERWRITE_IMAGE_ = False  # set to True while debugging / testing to force map image creation
# (otherwise, it check if the image is already present according to the arguments given)

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
        if self.attributes.get("__csv_mod_time__", None) is None:
            self.attributes["__csv_mod_time__"] = hash("")


class MapImgDirective(CSVTable, images.Figure):
    """
    Directive that builds plots using a csv file
    """

    # these two members copied from CSVTable, needs to be set otherwise
    # seems that those of images.Figure are used. The result is that the title (caption)
    # is correctly parsed and whitespaces are not splitted
    required_arguments = CSVTable.required_arguments
    """Number of required directive arguments."""

    optional_arguments = CSVTable.optional_arguments
    """Number of optional arguments after the required arguments."""

    own_option_spec = {
                      'margins_in_km': lambda arg: arg or None,
                      'epsg_projection': lambda arg: arg or None,
                      'arcgis_image_service': lambda arg: arg or None,
                      'arcgis_image_xpixels': lambda arg: arg or None,
                      'arcgis_image_dpi': lambda arg: arg or None
                      }

    option_spec = images.Figure.option_spec.copy()  # @UndefinedVariable
    for opt in CSVTable.option_spec.copy():
        if opt not in ("header-rows", "widths", "stub-columns"):
            option_spec[opt] = CSVTable.option_spec.copy()[opt]
    # option_spec.update(CSVTable.option_spec.copy())  # @UndefinedVariable
    option_spec.update(own_option_spec)

    def run(self):
        # First, let the CSVTable constructor handle all kind of parsing, including errors
        # (e.g., when we disabled the feature to load from file in sphinx, if a :file: has been
        # provided)

        # first provide a header-rows argument, REMEMBER THAT THIS DIRECTIVE HAS THE HEADER
        # ARGUMENT BUT NO HEADER-ROWS ARGUMENT: IF THE FORMER IS MISSING, THE FIRST CSV ROW
        # IS TAKEN AS HEADER. TRANSLATED TO SPHINX DIRECTIVES, IT BECOMES:
        self.options['header-rows'] = 0 if "header" in self.options else 1

        # parse using superclass
        ret = CSVTable.run(self)  # run super CSV Table to catch potential errors
        # the first node is the table node, then potential messages (see superclass)
        table_node = ret[0]
        messages = ret[1:]

        # get an hash from the content. This means we read twice the data but it's more robust

        try:
            # superclass parses csv in order to normalize cells, so the table obtained
            # is already normalized and well formatted. Empty strings are added in case
            #
            table_body_rows = table_node.children[-1].children[-1].children
            table_head_rows = table_node.children[-1].children[-2].children
            if len(table_head_rows) != 1:
                raise IndexError("multiple table headers not allowed")
            data = table_head_rows + table_body_rows
            ret_data = []
            hash_list = []  # this is for the hash
            for row in data:
                row_data = []
                for entry in row.children:
                    text = ''
                    if entry.children:
                        # In principle, entry.children is a single paragraph node holding the
                        # cell text. But sometimes cells have more children, i.e. providing a "^"
                        # puts in the 
                        # cell a system_message warning that ^ is a reserved symbols for titles
                        # (or something so) preceeding the paragraph with the text as last element
                        # So get last element (index [-1])
                        text = entry.children[-1].rawsource
                    row_data.append(text)
                    hash_list.append(text)
                ret_data.append(row_data)
            self.options["__csv_mod_time__"] = hash(tuple(hash_list))
            print "hash %s" % str(self.options["__csv_mod_time__"])
            rt_data = {}
            # normalize columns and convert to dict
            for c, colname in enumerate(ret_data[0]):
                for normalized_col_name in csv_headers:
                    if csv_headers[normalized_col_name].match(colname):
                        ret_data[0][c] = normalized_col_name
                        break
                rt_data[ret_data[0][c]] = [ret_data[i][c] for i in xrange(1, len(ret_data))]
            self.options["__data__"] = rt_data

        except IndexError as ierr:
            error = self.state_machine.reporter.error(
                'Error with Map data in "%s" directive:\n%s'
                % (self.name, "check your csv data format (rows, columns, etcetera)"),
                nodes.literal_block(self.block_text, self.block_text), line=self.lineno)
            return [error]

        # table nodes is a list of two children: the title, and the table
        # the table is in turn a list of children, whose last element is the tbody,
        # and whose next-to-last element is the thead

        # Now execute the figure directive, re-structuring this directive, which in
        # principle is equal to the csv table directive, to match the figure one
        tmp_options = self.options
        self.options = {}
        for opt in tmp_options:
            if opt in ("width", "height", "class", "figwidth", "figclass"):
                self.options[opt] = tmp_options[opt]
        # self.content = self.arguments[0: 1] # if self.arguments else ''
        self.content = None  # the content will be translated as caption. Problem is, if we do not
        # have content we should add the caption anyways. So let's do it manually
        imgnodes = images.Figure.run(self)
        # replace image nodes (theoretically, at most one) with mapimg nodes
        # note that self.options has already been
        # worked out in the super constructor
        # important cause it does checks and modifications
        # remove the uri, being processed by the figure directive. We do not need it
        self.options = tmp_options
        imgnodes[0].children = [mapnode(self.block_text, **self.options)]

        if self.arguments and len(self.arguments[0]):
            txt = Text(self.arguments[0])
            caption = nodes.caption(self.arguments[0], '', *[txt])
            caption.parent = imgnodes[0]  # sphinx complains if we doi not set it ...
            imgnodes[0].children.append(caption)
        self.options = tmp_options
        # last nodes are errors
        messages += imgnodes[1:]
        return imgnodes + messages

        return imgnodes


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
        lst.append(node.attributes.get(arg, ""))
        # Note above: using None as default does not return an unique hash
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
    app.add_directive('map-figure', MapImgDirective)
