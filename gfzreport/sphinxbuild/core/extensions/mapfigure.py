# -*- coding: utf-8 -*-
"""
   Implements a directive which behaves like a figure representing scatter plot of shapes
   on a geomap background.
   The directive acts as a csv table (although it produces a figure).
   The csv content must have *AT LEAST* these columns (OTHER COLUMNS ARE FINE
   THEY WILL JUST NOT BE RENDERED):

    - latitudes (either denoted by the string 'lats', 'latitudes', 'lat' or 'latitude',
    case insensitive)
    - longitudes ('lons', 'longitudes', 'lon' or 'longitude', case insensitive)
    - labels ('name', 'names', 'label', 'labels', 'caption', 'captions', case insensitive)
    - legend labels ('legend' or 'legends', case insensitive): Every non-empty string
      in a row will display an item in the legend with the row marker and label. If all rows
      legend labels are empty, no legend is displayed
    - markers ('marker' or 'markers', a value in 'o' 's' 'v' '^' '<' '>' 'd' 'D' (without quotes,
      where s=square, D=diamond, d=thin diamond). See `SUPPORTED_MARKERS`
    - colors ('color' or 'colors', case insensitive) in HTML format '#RGB' or '#RGBA'

   And OPTIONALLY:
    - sizes ('size' or 'sizes', case insensitive) in pixels^2, because matplotlib uses that unit.
        (therefore, in html we use sqrt, as our function draw SVG icons with width and height
        dimensions)

      IMPORTANT: For each row whose value under 'sizes' is empty,
        of for all rows if 'sizes' is not specified at all as column,
        the value will default to the global directive option ':map_sizes:'
        Empty values are missing values (if the column is the last one)
        or columns whose value is ""

    NOTES:

     - Html supports the marker types: 'd', 'D' (both diamond), '^' 'V', 's', 'o'.
       (rendered via leaflet SVG icons). Everything else will be rendered with a circle in HTML.
       The pdf supports all matplotlib markers. Thus for consistent rendering only the compatible
       shapes above should be provided

    - For the same reason (compatibility between matplotlib and HTML) colors can be given only in
      the two formats above (hex strings)

    - All directive options are supported in LaTEX/PDF. Conversely, the ONLY supported options
      in HTML are:

        * ':map_legend_pos:' (partial support) will be converted to leaflet's:
            'topright' if leg_pos in ('top', 'right') else 'bottomleft' if leg_pos == 'left'
            else 'bottomright'

    ,   * :map_labels_h_offset: and :map_labels_v_offset: in HTML, only the sign is
          considered (lower / equal / greater than zero) to place the label left/right/top
          (and so on...) relative to the symbol. In Latex /PDF, they are the distances
          in degrees from the symbol (positive zero or negative)
"""

# NOTE: TEMPLATE TO BE USED. DOWNLOADEDFROM THE SPHINX EXTENSIONS HERE:
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa?at=default

from docutils import nodes
from sphinx.util import ensuredir
import os
import re
import inspect
from itertools import izip
from gfzreport.sphinxbuild.map import plotmap, torgba, _shapeargs
from gfzreport.sphinxbuild.core.extensions.csvfigure import CsvFigureDirective
import math
import numpy as np

_OVERWRITE_IMAGE_ = False  # set to True while debugging / testing to force map image creation
# (otherwise, it check if the image is already present according to the arguments given)

_DIRECTIVE_NAME = "mapfigure"

SUPPORTED_MARKERS = ('o', 's', '^', 'v', 'D', '<', '>', 'h', 'H', 'd')

JS_SVG_FUNC = '''function getSvgURL(marker, size, fillColor, fillOpacity, strokeColor, strokeOpacity){
    // set a width and height so we are already compatible with different dimensions
    var [width, height] = [size, size];

    var attrs = `fill='${fillColor}' fill-opacity='${fillOpacity}' stroke='${strokeColor}' stroke-opacity='${strokeOpacity}'`;

    var txt = '';
    if (marker == 's'){
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><path ${attrs} d='M 1,1 L 1,${height-1} L ${width-1},${height-1} L ${width-1},1 Z'/></svg>`;
    }else if (marker == 'v'){
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><path ${attrs} d='M 1,1 L ${width-1},1 L ${width/2},${height-1} Z'/></svg>`;
    }else if (marker == '^'){
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><path ${attrs} d='M 1,${height-1} L ${width-1},${height-1} L ${width/2},1 Z'/></svg>`;
    }else if (marker == '<'){
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><path ${attrs} d='M 1,${height/2} L ${width-1},${height-1} L ${width-1},1 Z'/></svg>`;
    }else if (marker == '>'){
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><path ${attrs} d='M 1,1 L ${width-1},${height/2} L 1,${height-1} Z'/></svg>`;
    }else if (marker == 'D'){
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><path ${attrs} d='M ${width/2},1 L ${width-1},${height/2} L ${width/2},${height-1} L 1,${height/2} Z'/></svg>`;
    }else if (marker == 'd'){
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><path ${attrs} d='M ${width/2},1 L ${(3*width/4)-1},${height/2} L ${width/2},${height-1} L ${1 + width/4},${height/2} Z'/></svg>`;
    }else if (marker == 'h'){
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><path ${attrs} d='M ${width/2},1 L ${1+0.933*(width-2)},${height/4} L ${1+0.933*(width-2)},${3*height/4} L ${width/2},${height-1} L ${1+.067*(width-2)},${-1+3*height/4} L ${1+.067*(width-2)},${1+height/4} Z'/></svg>`;
    }else if (marker == 'H'){
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><path ${attrs} d='M 1, ${height/2} L ${width/4},${1+0.933*(height-2)} L ${3*width/4},${1+0.933*(height-2)} L ${width-1},${height/2} L ${-1+3*width/4},${1+.067*(height-2)} L ${1+width/4},${1+.067*(height-2)} Z'/></svg>`;
    }else{
        //use ellipse to support different width / height in the future:
        txt = `<svg xmlns='http://www.w3.org/2000/svg' version='1.1' width='${width}' height='${height}'><ellipse ${attrs} cx='${width/2}' cy='${height/2}' rx='${-1+width/2}' ry='${-1+height/2}' /></svg>`;
    }

    // here's the trick, base64 encode the URL (https://groups.google.com/forum/#!topic/leaflet-js/GSisdUm5rEc)
    // var svgURL = "data:image/svg+xml;base64," + btoa(icon);

    // But here they suggest to do this to account for firefox problems (it works):
    return encodeURI("data:image/svg+xml," + txt).replace(/#/g,'%23');
}'''

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
        # plotmapdata values are lists of strings, they will be converted later
        # Note that scalars are allowed, they will be converted and broadcasted
        # (see `_shapeargs` imported function)
        for key, val in attributes.iteritems():
            if key.startswith("map_"):
                newkey = key[4:]
                if newkey == 'sizes':
                    if newkey not in plotmapdata:
                        plotmapdata[newkey] = val  # set as scalar
                    else:
                        # replace only falsy values (being strings, empty strings):
                        plotmapdata[newkey] = [val if not _ else _ for _ in plotmapdata[newkey]]
                else:
                    # setdefault for safety, because the directive option does not have to
                    # override a column value, if specified:
                    plotmapdata.setdefault(newkey, val)
        self.attributes["__plotmapargs__"] = plotmapdata

        # make a normalized string by replacing newlines:
        reg = re.compile("\\s*\\n+\\s*")
        strhash = reg.sub(' ', rawsource).strip()
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
                           map_arcgis_dpi=lambda val: int(val),
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

    data = node.attributes['__plotmapargs__']  # FIXME: error!
    _uuid = node._data_hash__

    bordercolor, borderopacity = "#000000", 0.8

    _lons, _lats, _labels, _sizes, _colors, _markers, _legend_labels = \
        _shapeargs(data['lons'], data['lats'], data.get('labels', ''),
                   data['sizes'],
                   data.get('colors', '#FFFFFF00'), data.get('markers', 'o'),
                   data.get('legendlabels', ''))

    # basemap forwards to matplotlib.scatter which accept sizes in pt^2 (wtf?!!):
    _sizes = np.sqrt(np.array(_sizes).astype(float))
    # But that's not all: he html rendering seems to be too small *compared* with the latex
    # rendering. Two "hacks":
    # 1: assure points are even (convert 5 to 6, 5.5. to 6, keep 6 as 6):
    _sizes = 2 * np.ceil(np.array(_sizes).astype(float)/2)
    # 2: add 2 because the stroke takes up space (stroke width=1, therefore add 2)
    # also, as we have ints in form of floats, convert to int (not necessary though):
    _sizes = (2 + _sizes).astype(int)

    markers = []
    for lon, lat, label, color, marker, pt_size in izip(_lons, _lats, _labels,
                                                        _colors, _markers, _sizes):
        try:
            _, _, _, alpha = torgba(color)

            # svgMarker is defined below and injected as js code
            markers.append(('svgMarker(%f, %f, "%s", %f, "%s", %f, "%s", %f)') %
                           (lat, lon, marker, pt_size, str(color[:7]), alpha, bordercolor,
                            borderopacity))
            if label:
                h_offset, v_offset = float(data['labels_h_offset']), float(data['labels_v_offset'])
                tooltip_direction = \
                    'left' if h_offset < 0 else 'right' if h_offset > 0 else 'center'
                tooltip_v_offset = -pt_size if v_offset < 0 else pt_size if v_offset > 0 else 0
                # add a div label. Same behaviour of
                # Add labels as tooltip
                # https://gis.stackexchange.com/questions/59571/how-to-add-text-only-labels-on-leaflet-map-with-no-icon
                markers[-1] += ('.bindTooltip("%s",'
                                '{permanent: true, className: "map-tooltip", direction:\'%s\', '
                                'offset: [0, %f] })') % (esc(str(label)), tooltip_direction,
                                                         tooltip_v_offset)
        except (TypeError, ValueError):
            pass

    add_to_map_js = "    \n".join("markersArray.push(%s.addTo(map));" % mrk for mrk in markers)

    legends_js = []
    for leg, color, marker in izip(_legend_labels, _colors, _markers):
        if leg:
            try:
                _, _, _, alpha = torgba(color)

                leg_icon = ('getSvgURL("%s", %f, "%s", %f, "%s", %f)' %
                            (marker, pt_size, str(color[:7]), alpha, bordercolor, borderopacity))

                # pt_size in css is the diameter, multiply times two:
                # Moreover, we need to set rgba colors to support fill opacity only
                # rgba = "rgba(%d, %d, %d, %f)" % (r * 255, g * 255, b * 255, alpha)
                legends_js.append(('''"<div style='display:flex;align-items:center'><img src=\\"" + %s + "\\"/>&nbsp;%s</div>"''')
                                  % (leg_icon, esc(leg)))
            except (TypeError, ValueError):
                pass

    legend_js = ""
    if legends_js:
        leg_pos = data['legend_pos']
        # leaflet supports only 'bottomleft' 'bottomright', 'topleft' 'topright', so:
        leg_pos = 'topright' if leg_pos in ('top', 'right') else 'bottomleft' \
            if leg_pos == 'left' else 'bottomright'

        legend_js = """var legend = L.control({position: '%s'});
    legend.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');
        div.innerHTML = %s;
        return div;
    };
    legend.addTo(map);""" % (leg_pos, "+".join(l for l in legends_js))

    # define a svg marker function to inject as js:
    svg_marker_func = '''%s

    function svgMarker(lat, lon, marker, size, fillColor, fillOpacity, strokeColor, strokeOpacity){

    var svgURL = getSvgURL(marker, size, fillColor, fillOpacity, strokeColor, strokeOpacity);

    // set a width and height so we are already compatible with different dimensions
    var [width, height] = [size, size];

    // create icon
    var mySVGIcon = L.icon( {
        iconUrl: svgURL,
        iconSize: [width, height],
        // shadowSize: [12, 10],
        iconAnchor: [width/2, height/2],
        popupAnchor: [width/2, 0]
    });

    // return marker 
    return L.marker([ lat, lon], { icon: mySVGIcon }); //.addTo(mymap);
}''' % JS_SVG_FUNC

    html = """
<div id='map{0}' class=map></div>
<script>

    {1}
    var map = L.map('map{0}');
    var layer = L.esri.basemapLayer('Topographic').addTo(map);
    var markersArray = [];
    {2}
    // fit bounds according to markers:
    var group = new L.featureGroup(markersArray);
    map.fitBounds(group.getBounds());
    var rect = L.rectangle(group.getBounds(), {{color: 'black', fill: false, dashArray: "1, 3", weight: .5}}).addTo(map);
    group.bringToFront();
    {3}
</script>
""".format(str(_uuid), svg_marker_func, add_to_map_js, legend_js)

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
    self is the app, although not well documented
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
