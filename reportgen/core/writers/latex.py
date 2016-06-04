'''
Created on Apr 4, 2016

@author: riccardo
'''
# import re
# from sphinx.util import nodes
# import sphinx.directives
# from docutils.nodes import SkipNode
from sphinx.writers.latex import LaTeXTranslator as LT, FOOTER, HEADER
from collections import OrderedDict as odict
from sphinx.builders import latex


class LatexTranslator(LT):

    def __init__(self, document, builder):
        LT.__init__(self, document, builder)  # FIXME: check why new style super call does not work
        self.elements.update({'latex_epilog': builder.config.latex_elements.get("epilog", "")})
        self.field_list = odict()  # preserves order
        self.field_list_start = []
        self.rst_bib_fields = {}
        self._processing_imggrid = False

    def visit_field_list(self, node):
        self.field_list_start = len(self.body)
        LT.visit_field_list(self, node)

    def depart_field_list(self, node):
        LT.depart_field_list(self, node)
        # remove all biblio fields, they are handled below
        self.body = self.body[:self.field_list_start]

        if hasattr(self, "abstract_text_reminder"):
            self.body.extend([r'\begin{abstract}', '\n',
                              self.abstract_text_reminder, '\n', r'\end{abstract}'])

    def depart_field_name(self, node):
        LT.depart_field_name(self, node)
        field_name = str(node.children[0])  # be consistent with depart field_body
        # (use the same method!)
        self.rst_bib_fields[field_name] = len(self.body)

    def depart_field_body(self, node):
        LT.depart_field_body(self, node)
        field_name = str(node.parent.children[0].children[0])
        start = self.rst_bib_fields[field_name]
        field_value = "".join(self.body[start:]).strip()
        self.rst_bib_fields[field_name] = field_value
        if field_name in ("author", "authors"):
            self.elements.update({'author': field_value})  # FIXME: raw text or field value??
            # raise SkipNode()  # do not call the children node rendering, and do not call depart
            # node

        if field_name == "revision":
            self.elements.update({'release': field_value})
            # raise SkipNode()  # do not call the children node rendering, and do not call depart
            # node

        if field_name == "abstract":
            self.abstract_text_reminder = field_value

    def visit_Text(self, node):  # FIXME: remove this method???
        """
            Calls the super method, and then replaces invalid characters
            For the moment, it just replaces the tilde operator with
            \texttildelow
        """
        len_ = len(self.body)
        LT.visit_Text(self, node)
        for i in xrange(len_, len(self.body)):
            bdy = self.body[i]
            for bchar in bdy:
                # NOTE: the tilde we are interested in, and for which latex complains, is not the
                # ASCII TILDE, but a tilde operator whose ordinal is 8764
                # that's why this cumbersome way to do it:
                if ord(bchar) == 8764:
                    self.body[i] = self.body[i].replace(bchar, "\\texttildelow")
                    break

    def astext(self):
        # build a dict of bibliographic fields, and inject them as newcommand 
        # in the latex header
        commands = ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                    "%% AUTO-GENERATED COMMANDS FROM BIBLIOGRAPHIC FIELDS IN THE SOURCE RST:\n" +
                    "\n".join("\\newcommand{\\rst" + (name[0].title() + name[1:]) + "}" +
                              "{" + definition + "}"
                              for name, definition in self.rst_bib_fields.iteritems() if name) +
                    "\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                    "%% CUSTOM PREAMBLE DEFINED IN THE SOURCE RST CONFIG FILE:\n" +
                    "%(preamble)s\n"
                    "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                    )
        HEADER_ = HEADER.replace(r"%(preamble)s", commands)

        FOOTER_ = FOOTER.replace("\\end{document}", "%(latex_epilog)s\n\\end{document}")

        return (HEADER_ % self.elements +
                self.highlighter.get_stylesheet() +
                u''.join(self.body) +
                '\n' + self.elements['footer'] + '\n' +
                self.generate_indices() +
                FOOTER_ % self.elements)
