'''
Created on Apr 4, 2016

@author: riccardo
'''
from docutils.nodes import SkipNode
from sphinx.writers.latex import LaTeXTranslator as LT
from collections import OrderedDict as odict
import re

class LatexTranslator(LT):

    def __init__(self, document, builder):
        LT.__init__(self, document, builder)  # FIXME: check why new style super call does not work
        self.field_list = odict()  # preserves order
        self.field_list_start = []

    def visit_field_list(self, node):
        self.field_list_start = len(self.body)
        LT.visit_field_list(self, node)

    def depart_field_list(self, node):
        LT.depart_field_list(self, node)
        if len(self.body) == self.field_list_start+2:
            # remove field list stuff
            self.body = self.body[:-2]

        if hasattr(self, "abstract_text_remonder"):
            self.body.extend([r'\begin{abstract}', '\n',
                              self.abstract_text_remonder, '\n', r'\end{abstract}'])

    def visit_field(self, node):
        field_name = node.children[0].rawsource
        field_text = node.children[1].rawsource
        if field_name in ("author", "authors"):
            self.elements.update({'author': field_text.strip()})
            raise SkipNode()  # do not call the children node rendering, and do not call depart node

        if field_name == "revision":
            self.elements.update({'release': field_text.strip()})
            raise SkipNode()  # do not call the children node rendering, and do not call depart node

        if field_name == "abstract":
            self.abstract_text_remonder = field_text.strip()
            raise SkipNode()  # do not call the children node rendering, and do not call depart node

        LT.visit_field(self, node)

    def depart_field(self, node):
        LT.depart_field(self, node)  # superclass simply passes
