'''
Latex translator overriding default sphinx one:
It provides latex commands for any bibliographic fields input at the start of the document
BEFORE the title
in the form '\newcommand{rst<FIELDNAME>}{<FIELDVALUE>}',
And it removes the hlines in longtable headers which sphinx 1.5.1

Created on Apr 4, 2016

@author: riccardo
'''
# import re
# from sphinx.util import nodes
# import sphinx.directives
# from docutils.nodes import SkipNode
from sphinx.writers.latex import LaTeXTranslator as LT  # , FOOTER, HEADER
import re
from gfzreport.sphinxbuild.core.writers.latexutils import get_citation


class LatexTranslator(LT):

#     def __init__(self, document, builder):
#         # Apparently, we are working with old-style classes, super does not work as expected, do
#         # this instead:
#         LT.__init__(self, document, builder)
# 
#         # Side note:
#         # If we want to add custom stuff to our latex, add in the config.py under 'latex_elements'
#         # the desired key, e.g., 'epilog', and then type here:
#         # self.elements.update({'epilog': builder.config.latex_elements.get("epilog", "")})
#         # then do something with that element key cause sphinx will ignore it (See e.g.
#         # self.astext() where sphinx sets up the doc)
#         self.field_list_start = []
#         self.rst_bib_fields = {}
#         # list of bib fields not to be included in latex \newcommand:
#         self.no_newcommand = set(['abstract', 'author', 'authors'])

    def visit_field_list(self, node):
        # set a flag telling that we enter the field list: all operations
        # will take place if this attribute is present
        self._inside_fieldlist = True 
        LT.visit_field_list(self, node)

    def visit_field(self, node):
        # flag telling the start of the field. If we are inside a field list,
        # and this attribute has to be deleted (e.g. author, abstract), fix the
        # starting point of the deletion
        self._bodylen_remainder0 = len(self.body)
        LT.visit_field(self, node)

    def visit_field_body(self, node):
        # flag telling the start of the field body. If we are inside a field list,
        # and this attribute has to be used somewhere (e.g. author, abstract),
        # let the super class do its work and we can
        # get the rendered formatted text later from this index on
        self._bodylen_remainder1 = len(self.body)
        LT.visit_field_body(self, node)

    def depart_field_body(self, node):
        LT.depart_field_body(self, node)
        field_name = str(node.parent.children[0].children[0])
        # is a particular field which has to be rendered somewhere else?
        if field_name.lower() in ('author', 'authors', 'abstract', 'revision'):
            field_value = "".join(self.body[self._bodylen_remainder1:]).strip()
            if field_name in ("author", "authors"):
                self.elements.update({'author': field_value})  # FIXME: raw text or field value??
            elif field_name == "revision":
                self.elements.update({'release': field_value})
            elif field_name == "abstract":
                self._abstract_text_reminder = field_value
            self.body = self.body[:self._bodylen_remainder0]

    def depart_field_list(self, node):
        LT.depart_field_list(self, node)
        # set a flag telling that we enter the field list: prevent all operations on fields
        # from here on
        delattr(self, '_inside_fieldlist')
        if hasattr(self, "_abstract_text_reminder"):
            self.body.extend([r'\begin{abstract}', '\n',
                              self._abstract_text_reminder, '\n', r'\end{abstract}'])

#     def visit_field_list(self, node):
#         self.field_list_start = len(self.body)
#         LT.visit_field_list(self, node)
# 
#     def depart_field_list(self, node):
#         LT.depart_field_list(self, node)
#         # remove all biblio fields, they are handled below
#         self.body = self.body[:self.field_list_start]
# 
#         if hasattr(self, "abstract_text_reminder"):
#             self.body.extend([r'\begin{abstract}', '\n',
#                               self.abstract_text_reminder, '\n', r'\end{abstract}'])
# 
#     def depart_field_name(self, node):
#         LT.depart_field_name(self, node)
#         field_name = str(node.children[0])  # be consistent with depart field_body
#         # (use the same method!)
#         self.rst_bib_fields[field_name] = len(self.body)
# 
#     def depart_field_body(self, node):
#         LT.depart_field_body(self, node)
#         field_name = str(node.parent.children[0].children[0])
#         start = self.rst_bib_fields[field_name]
#         field_value = "".join(self.body[start:]).strip()
#         self.rst_bib_fields[field_name] = field_value
#         if field_name in ("author", "authors"):
#             self.elements.update({'author': field_value})  # FIXME: raw text or field value??
# 
#         if field_name == "revision":
#             self.elements.update({'release': field_value})
#             # raise SkipNode()  # do not call the children node rendering, and do not call depart
#             # node
# 
#         if field_name == "abstract":
#             self.abstract_text_reminder = field_value

    def depart_table(self, node):
        """
            Horrible hack which removes the TERRIBLE (and HARD CODED) frame in the
            bottom of longtable saying "continued on next page". WHY Sphinx does that? WHY??!!!??
        """
        # get the current body length. Tables in sphinx writer superclass work weirdly.
        # The real body is allocated as last element of self.bodystack. self.body at this point
        # is the table body (which we are about to include in self.,body in the method
        # LT.depart_table)
        strt = len(self.bodystack[-1])
        LT.depart_table(self, node)
        if self.body[-1].strip() == "\\end{longtable}":
            for i in xrange(strt, len(self.body)):
                if self.body[i].strip() == '\\endlastfoot':
                    break
                elif self.body[i].startswith(r'\hline \multicolumn{'):
                    self.body[i] = self.body[i].replace("\\hline", "").replace("{|r|}", "{r}")

    def astext(self):
        # build a dict of bibliographic fields, and inject them as newcommand
        # in the latex header
        # for commands starting with doi-, build also the citation command with suffix "Citation"

        latexcommands = {}
        data = self.builder.app.env.metadata[self.builder.app.config.master_doc]
        for name, value in data.iteritems():
            # doiCommand will also have a doiCommandCitation which represents the bib citation
            # of that doi
            isdoi = name.lower().startswith("doi")
            latex_command_name = "\\rst" + (name[0].upper() + name[1:])
            # value should be already formatted for latex.The only thing is that we want to
            # preserve also rst newlines so we replace \n with \\ (which becomes \\\\ after
            # escaping, plus a final \n to preserve "visually" the newlines in latex, although it
            # won't be rendered in latex output):
            latexcommands[latex_command_name] = str(value).replace("\n", '\\\\\n')

            # note above: value moght not be a string. eg. supplying :tocdepth: 3, the 3 is passed
            # as int to the env

            if isdoi:
                try:
                    text, url = get_citation(self.builder.app, value)
                except Exception as exc:
                    text, url = "error getting DOI from '%s': %s" % (value, str(exc)), ""
                latexcommands[latex_command_name + "Citation"] = text if not url else \
                    text + " \href{%s}{%s}" % (url, url)

        # we try to be python 2-3 compliant: first of all, jinja (used in LT.astext(self) below)
        # wants unicodes, so we need to put unicode variables in self.elements['preamble']
        # But we want also to avoid u'' or whatever is not python3, so we won't have headaches if
        # moving to py3. As bytes are non unicode in python2, and non strings in python3,
        # provide a general function _str and pass every string/bytes
        # to it before each string operation:
        def _str(obj):
            return obj.decode('utf8') if isinstance(obj, bytes) else obj

        preamble_wrapper = _str("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                                "%% NEWCOMMANDS FROM RST BIB.FIELDS GENERATED IN LatexTranslator:\n"
                                "{}\n"
                                "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                                "%% PREAMBLE DEFINED IN conf.py (if any):\n" +
                                "%(preamble)s\n"
                                "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                                ).format("\n".join("\\newcommand{%s}{%s}" % (_str(n), _str(v))
                                                   for n, v in latexcommands.iteritems()))

        self.elements.update({
            # merge existing preamble:
            'preamble': preamble_wrapper % {'preamble': _str(self.elements.get("preamble", ""))},
        })

        return LT.astext(self)
