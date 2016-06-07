# -*- coding: utf-8 -*-
"""
   FIXME: write doc!!

    
"""

# NOTE: SEE SPHINX EXTENSIONS HERE:
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa?at=default
from docutils.parsers.rst.directives import images
from reportbuild.core.extensions import mapimg


class MapFigureDirective(mapimg.MapImgDirective, images.Figure):
    """
    Directive that builds a map using a csv file
    """
    def run(self):
        nodes_fig = images.Figure.run(self)
        nodes_mapimg = mapimg.MapImgDirective.run(self)
#        csv_img = mapimg.mapimg(".. image: %s" % self.arguments[0], **self.options)
#         nodes[0].children[0] = csv_img
#         return nodes
        nodes_fig[0].children[0] = nodes_mapimg[0]
        return nodes_fig

def setup(app):
    app.add_directive('map-figure-fig', MapFigureDirective)
