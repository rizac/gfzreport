# -*- coding: utf-8 -*-
"""
   FIXME: write doc!!

    
"""

# NOTE: SEE SPHINX EXTENSIONS HERE:
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa?at=default
from docutils.parsers.rst.directives import images
from reportgen.core.extensions import mapimg


class CsvMapDirective(mapimg.MapImgDirective, images.Figure):
    """
    Directive that builds a map using a csv file
    """
    def run(self):
        nodes = images.Figure.run(self)
        csv_img = mapimg.mapimg(".. image: %s" % self.arguments[0], **self.options)
        nodes[0].children[0] = csv_img
        return nodes


def setup(app):
    app.add_directive('map-figure', CsvMapDirective)
