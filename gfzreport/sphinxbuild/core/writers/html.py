'''
Class extending sphinx.writers.html.SmartyPantsHTMLTranslator: it just parses
the field name 'authors' (if any) removing all asterixs, which are interpreted as 'corresponding
author' in latex (and rendered accordingly) but will not be rendered here

Created on Mar 18, 2016

@author: riccardo
'''
import os

from docutils.nodes import SkipNode
from docutils import nodes
from sphinx.writers.html import SmartyPantsHTMLTranslator

from gfzreport.sphinxbuild.core import touni

class HTMLTranslator(SmartyPantsHTMLTranslator):
    '''This class does basically one thing removes the asterix (if present) from
    the author(s) field body.
    As always with Sphinx, all procedures are quite hacky.
    '''

    def __init__(self, *args, **kwds):
        SmartyPantsHTMLTranslator.__init__(self, *args, **kwds)  # old style class...
        # set custom attributes:
        self._visiting_author_field__ = False
        
    def visit_field_body(self, node):
        '''just replace all asterix in authors if present'''
        if self._visiting_author_field__:
            try:
                node.rawsource = node.rawsource.replace('*', '')
                textnode = node.children[0].children[0]
                # replace asterix. Use touni cause Text nodes want unicode:
                textnode.parent.children[0] = nodes.Text(textnode.rawsource.replace(touni('*'),
                                                                                    touni('')))
            except Exception:  #pylint: disable=broad-except
                pass
        SmartyPantsHTMLTranslator.visit_field_body(self, node)

    def visit_field_name(self, node):
        '''just mark an internal attribute if we are processing authors'''
        self._visiting_author_field__ = node.rawsource.lower().strip() in ('author', 'authors')
        SmartyPantsHTMLTranslator.visit_field_name(self, node)
