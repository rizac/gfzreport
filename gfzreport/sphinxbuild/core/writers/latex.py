'''
Latex translator overriding default sphinx one:

1. It provides latex commands for any bibliographic fields input at the start of the document
BEFORE the title in the form '\newcommand{rst<FIELDNAME>}{<FIELDVALUE>}',
2. Processes the 'author' bib. field by parsing its content and making available the commands:
```
'rstAuthorsWithAffiliations'
'rstAffiliations' 
```
2. Removes the hlines in longtable headers which sphinx 1.5.1 adds by default (thanks...)

Created on Apr 4, 2016

@author: riccardo
'''
# import re
# from sphinx.util import nodes
# import sphinx.directives
# from docutils.nodes import SkipNode
from sphinx.writers.latex import LaTeXTranslator as LT  # , FOOTER, HEADER

from gfzreport.sphinxbuild.core import touni
from gfzreport.sphinxbuild.core.writers.latexutils import parse_authors


class LatexTranslator(LT):

    _ignored_fieldnames__ = {'author', 'authors', 'abstract', 'revision', 'citation', 'citations'}
    '''fields that will not be rendered (NOTE: case insensitive). Some of them might be processed
    (e.g., usually added to the app metadata dict) other completely ignored'''

    def __init__(self, document, builder):
        LT.__init__(self, document, builder)
        # define our variables:
        self._abstract_text_reminder__ = None
        self._current_field_start__ = -1
        self._current_fieldbody_start__ = -1
        self._current_field_name__ = ''
        self._current_field_body__ = ''

    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # Bib. Fields management methods (in "chronological" order)
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    def visit_field(self, node):
        '''Simply stores informations here about the current field in order to remove it
        later in `depart_field`, if the current field has not to be rendered,
        and then calls the super method
        '''
        self._current_field_name__ = str(node.children[0].children[0])
        self._current_field_start__ = len(self.body)
        LT.visit_field(self, node)
        
    def visit_field_body(self, node):
        '''Stores the length of self.body in order to retrieve the
        rendered field body, if needed for processing it, and then calls the super method'''
        # set flags and call super
        self._current_fieldbody_start__ = len(self.body)
        LT.visit_field_body(self, node)

    def depart_field_body(self, node):
        '''Simply calls the super method and then stores the rendered field body for later use'''
        LT.depart_field_body(self, node)
        self._current_field_body__ = "".join(self.body[self._current_fieldbody_start__:]).strip()
           

    def depart_field(self, node):
        '''Simply calls the super method and then
        simply removes the just rendered field if it should be ignored
        '''
        # call super and reset flags (removing field if in ignore list)
        LT.depart_field(self, node)
        
        # process fbib field if something has to be done:
        field_name = self._current_field_name__.lower()
        field_value = self._current_field_body__
        # is a particular field which has to be rendered somewhere else?
        if field_name in ("author", "authors"):
            auth, auth_affil, affil = parse_authors(field_value)
            envdict = self.builder.app.env.metadata[self.builder.app.config.master_doc]
            envdict['authorsWithAffiliations'] = auth_affil
            envdict['affiliations'] = affil
            self.elements.update({'author': auth})
        elif field_name == "revision":
            self.elements.update({'release': field_value})
        elif field_name == "citations" or field_name == 'citation':
            envdict = self.builder.app.env.metadata[self.builder.app.config.master_doc]
            envdict['citations'] = field_value
        elif field_name == "abstract":
            self._abstract_text_reminder__ = field_value

        # remove field from built document if it has to be ignored
        if field_name in self._ignored_fieldnames__ and \
            self._current_field_start__ > -1:
            self.body = self.body[:self._current_field_start__]

        # reset values:
        self._current_field_name__ = self._current_field_body__ =''
        self._current_field_start__ = -1

    def depart_field_list(self, node):
        '''Calls the super method nd then, if a bib.field named abstract has been found, puts the
        abstract by appending latex's '\begin{abstract}' (... and so on) to `self.body`'''
        LT.depart_field_list(self, node)
        if self._abstract_text_reminder__ is not None:
            self.body.extend([r'\begin{abstract}', '\n',
                              self._abstract_text_reminder__, '\n', r'\end{abstract}'])
            self._abstract_text_reminder__ = None

    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # end fields management methods
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
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
        # value should be already formatted for latex.The only thing is that we want to
        # preserve also rst newlines so we replace \n with \\ (which becomes \\\\ after
        # escaping, plus a final \n to preserve "visually" the newlines in latex, although it
        # won't be rendered in latex output):
        NEWLINE = touni("\n")
        LATEX_NEWLINE = touni('\\\\\n')

        latexcommands = {}
        data = self.builder.app.env.metadata[self.builder.app.config.master_doc]
        for name, value in data.iteritems():
            name, value = touni(name), touni(value)
            latex_command_name = LATEX_COMMAND.format(name[0].upper(), name[1:])
            try:
                value = value.replace(NEWLINE, LATEX_NEWLINE)
            except AttributeError:
                # not a string? stringify it:
                value = touni(str(value))
            latexcommands[latex_command_name] = value

        # Convert the  dict latexcommands into a latex string, newline-separated
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
