# -*- coding: utf-8 -*-
"""
   FIXME: write doc!!

    
"""

# NOTE: TEMPLATE TO BE USED. DOWNLOADEDFROM THE SPHINX EXTENSIONS HERE:
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa?at=default
# import re
import urllib
# import urllib2
# from xml.dom import minidom

from docutils import nodes  # , utils
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import images

from sphinx.util.compat import Directive
from core.extensions import mapimg
from sphinx.util import ensuredir #, relative_uri
# import posixpath
import os
from map import plotmap


class CsvMapDirective(mapimg.MapImgDirective, images.Figure):
    """
    Directive that builds plots using a csv file
    """
    def run(self):
        nodes = images.Figure.run(self)
        csv_img = mapimg.mapimg(".. image: %s" % self.arguments[0], **self.options)
        nodes[0].children[0] = csv_img
        return nodes

def setup(app):
#     app.add_node(map,
#                  html=(visit_csvmap_node_html, depart_csvmap_node),
#                  latex=(visit_csvmap_node_latex, depart_csvmap_node))
    app.add_directive('map-figure', CsvMapDirective)
