# -*- coding: utf-8 -*-
"""
    sphinxcontrib.googlemaps
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2012 by Takeshi KOMIYA
    :license: BSD, see LICENSE for details.
"""

# NOTE: TEMPLATE TO BE USED. DOWNLOADEDFROM THE SPHINX EXTENSIONS HERE:
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa?at=default
import re
import urllib
import urllib2
from xml.dom import minidom

from docutils import nodes, utils
from docutils.parsers.rst import directives

from sphinx.util.compat import Directive
from __builtin__ import None
from uuid import uuid4  # FIXME: sphinx provides a self uuid!
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha
from sphinx.util import ensuredir, relative_uri
import posixpath
import os
from .map import map

def get_hashid(options):
    hashkey = str(options)
    hashid = sha(hashkey).hexdigest()
    return hashid

# from sphinx.writers.html import HTMLTranslator
# from sphinx.writers.latex import LatexTranslator
import csv


def read_csv(filepath, required_columns, delimiters=[' ', ';']):
    ret = None
    if not delimiters:
        delimiters = [None]
    else:
        delimiters.insert(0, None)

    if not required_columns:
        required_columns = []
    try:
        with open(filepath) as csvfile:
            for delim in delimiters:  # FIXME: check if file pointer resets for next call to DictReader!!!
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


class csvmap(nodes.General, nodes.Element):
    pass


class CsvMapDirective(Directive):
    """
    Directive that builds plots using a csv file
    """
    # copied from Image directive:
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    # has_content = True
    # required_arguments = 0
    own_option_spec = dict(
        lat_key=lambda arg: arg or 'lat',
        lon_key=lambda arg: arg or 'lon',
        name_key=lambda arg: arg or 'name',

    )

    option_spec = directives.images.Image.option_spec.copy()  # @UndefinedVariable
    option_spec.update(own_option_spec)

    def run(self):
        # self.arguments = ['']
        # gnuplot_options = dict([(k, v) for k, v in self.options.items()
        #                         if k in self.own_option_spec])

#         (image_node,) = directives.images.Figure.run(self)
#         if isinstance(image_node, nodes.system_message):
#             return [image_node]
        # text = '\n'.join(self.content)
        # image_node.gnuplot = dict(text=text,options=gnuplot_options)
        node = csvmap()
        node.hash = str(uuid4())[:4] + str(uuid4())[-4:]

        # TODO: test value error. From youtube sphinx extension they do so
        # apparently, it is cought from the caller. Test it
        try:
            opts = CsvMapDirective.own_option_spec
            pts = read_csv(self.options['uri'], self.options[k] for k in opts)
            node['options'] = self.options
            node['_points'] = pts
        except ValueError as verr:
            document = self.reporter.document
            return [document.reporter.warning(str(verr), line=self.lineno)]
            # image_node.points_error_msg = str(verr)
        return [node]


def visit_csvmap_node_html(self, node):
    """self seems to be the app Translator object. Source code of the Sphinx object here:
    http://www.sphinx-doc.org/en/stable/_modules/sphinx/application.html
    """
    if not isinstance(node, csvmap):
        return

    # TODO: append leaflet script and div
    lang = 'ja'
    params = dict(f='q',
                  hl=lang,
                  t='m',
                  om=0,
                  ie='UTF8',
                  oe='UTF8',
                  output='embed')

    if 'query' in node:
        params['q'] = node['query'].encode('utf-8')
    else:
        params['ll'] = "%f,%f" % (node['latitude'], node['longtitude'])

    if 'zoom' in node:
        params['z'] = str(node['zoom'])

    if 'balloon' not in node:
        params['iwloc'] = 'B'

    baseurl = "http://maps.google.co.jp/maps?"
    iframe = """<iframe width="600" height="350" frameborder="0"
                        scrolling="no" marginheight="0"
                        marginwidth="0" src="%s">
                </iframe>"""

    url = baseurl + urllib.urlencode(params)
    self.body.append(iframe % url)


def get_map_from_csv(points, options):

    try:
        f = map.plot_basemap(lats=[p[options['lat_key']] for p in points],
                             lons=[p[options['lon_key']] for p in points],
                             labels=[p[options['name_key']] for p in points],
                             color=[0.5] * len(points),
                             size=[20] * len(points),
                             projection="local",  # "ortho",
                             show=False)
        # see http://matplotlib.org/basemap/users/geography.html
        # from plot_map (which calls plot_basemap), we can access the bmap from fig.bmap:
        f.bmap.shadedrelief()
        # f.bmap.etopo()
    except ImportError:
        import matplotlib.pyplot as plt
        f = plt.figure()

    return f


def visit_csvmap_node_latex(self, node):
    """FIXME: self is what?!!!
    http://www.sphinx-doc.org/en/stable/_modules/sphinx/application.html
    """
#     if not isinstance(node, csvmap):
#         return

    fname = 'plot-%s.png' % (get_hashid(node['options']))  # FIXME: not TRUE! what if we changed csv??
    # HTML
    imgpath = relative_uri(self.builder.env.docname, '_images')
    relfn = posixpath.join(imgpath, fname)  # FIXME: why posix and not os.path??
    outfn = os.path.join(self.builder.outdir, '_images', fname)

    if not os.path.isfile(outfn):
        ensuredir(os.path.dirname(outfn))
        fig = get_map_from_csv(self, node.get('_points', []), node['options'])
        fig.savefig(outfn)

    image_node = nodes.image(".. image: %s" % relfn, node['options'])
    node.replace_self(image_node)  # FIXME: not replace self!! append after, what if node is
    # a warning??


def depart_csvmap_node(self, node):
    pass


def setup(app):
    app.add_node(csvmap,
                 html=(visit_csvmap_node_html, depart_csvmap_node),
                 latex=(visit_csvmap_node_latex, depart_csvmap_node))
    app.add_directive('csvmap', CsvMapDirective)
