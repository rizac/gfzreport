'''
Created on May 30, 2016

@author: riccardo
'''


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


# note: we override node cause nodes might be called also from a parent map-image
# so that some functionalities needs to be set here and not in the MapImdDirective below
class tableconfig(nodes.Element):
    # class dict mapping option specific map directives keys to
    # the map keywords

    def __init__(self, rawsource='', *children, **attributes):
        super(tableconfig, self).__init__(rawsource, *children, **attributes)


class TableConfigDirective(images.Image):  # FIXME: to be tested! SHOULD WE EVER CALL IT ACTUALLY??
    """
    Directive that builds plots using a csv file
    """

    own_option_spec = {
                      'tabularcolumns': lambda arg: arg or None,
                      'hlines-show': lambda arg: arg or None,
                      'hlines-hide': lambda arg: arg or None,
                      'header-font': lambda arg: arg or None,
                      'header-bg': lambda arg: arg or None
                      }

    option_spec = images.Image.option_spec.copy()  # @UndefinedVariable
    option_spec.update(own_option_spec)

    def run(self):
        ret = []
        if 'tabularcolumns' in self.options:
            ret.append(nodes.colspec('.. tabularcolumns:: %s' % self.options['tabularcolumns']))
        ret.append(tableconfig(self.block_text, **self.options))
        return ret


def visit_tc_node_html(self, node):
    pass


# from sphinx.writers.latex import LaTeXTranslator
def visit_tc_node_latex(self, node):
    pass


def depart_tc_node_latex(self, node):
    pass


def depart_tc_node_html(self, node):
    pass


def doctree_read(app, doctree):
    dictsubs = {}
    for tcf in doctree.traverse(tableconfig):
        siblings = tcf.parent().children()
        tbl = None
        for sbl in reversed(siblings):
            if isinstance(sbl, nodes.table):
                tbl = sbl
            elif sbl == tcf:
                break
        if tbl is not None:
            table.attributes['__tableconfig__'] = 
        


def setup(app):
    app.add_node(tableconfig,
                 html=(visit_tc_node_html, depart_tc_node_html),
                 latex=(visit_tc_node_latex, depart_tc_node_latex))
    app.add_directive('table-config', TableConfigDirective)
    app.connect('doctree-read', doctree_read)

