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

from gfzreport.sphinxbuild.core.writers import touni
from gfzreport.sphinxbuild.core.writers.latexutils import get_citation, parse_authors


class LatexTranslator(LT):

    def __init__(self, document, builder):
        LT.__init__(self, document, builder)
        # define our variables:
        self._abstract_text_reminder__ = None
        self._current_field_start__ = -1
        self._current_fieldbody_start__ = -1
        self._current_field_name__ = ''
        self._ignored_fieldnames__ = {'author', 'authors', 'abstract', 'revision'}

    def visit_field(self, node):
        # set flags and call super
        self._current_field_name__ = str(node.children[0].children[0])
        self._current_field_start__ = len(self.body)
        LT.visit_field(self, node)
        
    def depart_field(self, node):
        # call super and reset flags (removing field if in ignore list)
        LT.depart_field(self, node)
        if self._current_field_name__ in self._ignored_fieldnames__:
            self.body = self.body[:self._current_field_start__]
        self._current_field_name__ = ''
        self._current_field_start__ = -1

    def visit_field_body(self, node):
        # set flags and call super
        self._current_fieldbody_start__ = len(self.body)
        LT.visit_field_body(self, node)

    def depart_field_body(self, node):
        LT.depart_field_body(self, node)
        field_name = self._current_field_name__
        # is a particular field which has to be rendered somewhere else?
        field_value = "".join(self.body[self._current_fieldbody_start__:]).strip()
        if field_name in ("author", "authors"):
            auth, auth_affil, affil = parse_authors(field_value)
            envdict = self.builder.app.env.metadata[self.builder.app.config.master_doc]
            envdict['authorsWithAffiliations'] = auth_affil
            envdict['affiliations'] = affil
            self.elements.update({'author': auth})  # FIXME: raw text or field value??
        elif field_name == "revision":
            self.elements.update({'release': field_value})
        elif field_name == "abstract":
            self._abstract_text_reminder__ = field_value
           

    def depart_field_list(self, node):
        LT.depart_field_list(self, node)
        if self._abstract_text_reminder__ is not None:
            self.body.extend([r'\begin{abstract}', '\n',
                              self._abstract_text_reminder__, '\n', r'\end{abstract}'])
            self._abstract_text_reminder__ = None

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

        # The final string should be unicode, as jinja (used by sphinx later) expects unicodes
        # So perfect, let's work with unicode. But we make use of
        # "%s%s" % (A, B) and "{}{}".format(A, B) here, and "%s%s" are bytes in py2 and str in py3
        # So we should convert them as well to unicode
        # All in all, we use the touni function which is py2 and py3 compatible
        LATEX_COMMAND = touni("\\rst{}{}")
        LATEX_COMMAND_DOICITATION = touni("%sCitation")
        LATEX_HREF = touni(" \\href{%s}{%s}")
        # value should be already formatted for latex.The only thing is that we want to
        # preserve also rst newlines so we replace \n with \\ (which becomes \\\\ after
        # escaping, plus a final \n to preserve "visually" the newlines in latex, although it
        # won't be rendered in latex output):
        NEWLINE = touni("\n")
        LATEX_NEWLINE = touni('\\\\\n')
        DOI = touni("doi")
        A, Z = touni("A"), touni("Z")

        def isdoi(uni_str):
            """ return True if uni_str = 'doi', 'DOI' or is of the form 'doi[A-Z].*'"""
            return uni_str.lower() == DOI or \
                (uni_str.startswith(DOI) and uni_str[len(DOI)] >= A and uni_str[len(DOI)] <= Z)

        DOI_ERR_MSG = touni("error getting DOI from '%s': %s")
        EMPTY_STR = touni("")

        latexcommands = {}
        data = self.builder.app.env.metadata[self.builder.app.config.master_doc]
        for name, value in data.iteritems():
            name, value = touni(name), touni(value)
            # doiCommand will also have a doiCommandCitation which represents the bib citation
            # of that doi
            isdoi_ = isdoi(name)
            latex_command_name = LATEX_COMMAND.format(name[0].upper(), name[1:])
            try:
                value = value.replace(NEWLINE, LATEX_NEWLINE)
            except AttributeError:
                # not a string? stringify it:
                value = touni(str(value))
            latexcommands[latex_command_name] = value

            # note above: value moght not be a string. eg. supplying :tocdepth: 3, the 3 is passed
            # as int to the env
            if isdoi_:
                text, url = EMPTY_STR, EMPTY_STR
                if value:
                    try:
                        text, url = get_citation(self.builder.app, value)
                        text, url = touni(text), touni(url)
                    except Exception as exc:
                        exc_msg = touni(str(exc))
                        text, url = DOI_ERR_MSG % (value, exc_msg), EMPTY_STR
                latexcommands[LATEX_COMMAND_DOICITATION % latex_command_name] = \
                    text if not url else text + LATEX_HREF % (url, url)

        LATEX_NEWCOMMAND = touni("\\newcommand{%s}{%s}")
        newcommands = NEWLINE.join(LATEX_NEWCOMMAND % (n, v) for n, v in latexcommands.iteritems())

        preamble_wrapper = \
            touni("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                  "%% Newcommands converted from rst fields before the title:\n"
                  "{}\n"
                  "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                  "%% Content of latex_elements['preamble'] in conf.py (if defined):\n"
                  "%(preamble)s\n"
                  "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                  ).format(newcommands)

        # merge existing preamble:
        preamble = preamble_wrapper % {touni('preamble'): touni(self.elements.get("preamble", ""))}
        # update object elements:
        self.elements.update({
            'preamble': preamble,
        })

        return LT.astext(self)
