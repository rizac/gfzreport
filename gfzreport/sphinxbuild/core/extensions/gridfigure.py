# -*- coding: utf-8 -*-
"""
    Implements the sphinx directive to show a grid of images as a figure:

    .. gridfigure:: figure_caption
        :dir: folder

        data

    This directive has to be written and filled like a CSVTable BUT produces a "table" of figures.
    IT extends CsvFigureDirective, which in turn extends both CSVTable and Figure. It first parses
    the document as CSVTable,
    the returned table cell is replaced by images nodes first by joining the dir argument and the
    data provided. Then, the content is parsed as
    Figure directive. The returned nodes are a simple figure wrapping a table of images, followed by
    the caption (if any) and all potential node messages that the super calls generated
    (appended as CSVTable + Figure messages).
    This lets previous labels written in the rst point to the figure (like 'see Fig...' and not
    'see Table...') and custom directives like `tabularcolumns`, `tabularrows` or `includegraphics`
    point to the wrapped table / figure.

    If we had to generate html, that would be all we need. But there is latex, and sphinx pretending
    to support it. ;)

    The first problem is that we need to use longtables. Sphinx has a variety of hardcoded ways
    to decide what tabular environment to use. Fortunately, one is handy: Provide the class
    'longtable', which is done inside the directive

    The second problem is to modify the longtable headers which print something like
    "Table # continued to next page", replacing that "Table" with "Figure" and # with the correct
    figure number. We do it via a hack (caused by a previous Sphinx hack) in
    visit_imggrid_node_latex function.

    Possible drawbacks: when latex places spaces or some other stuff BETWEEN the generated table and
    the figure. The latter, having only a caption, NEEDS to stay IMMEDIATELY below the table for
    giving the "visual" impression it is the table caption. But
    this can be arranged by editing the source rst and placing the directive elsewhere, or
    issuing a ':raw:latex \clearpage' command or simply writing some text which re-arranges the
    layout

    FIXME: write supported options. In principle, all Figure and CSVTAble options, PLUS the dir,
    latex-includegraphics-opts

    --------

    Small implementation history (in case you think "hey why don't you do like this?): we first
    implemented this directive as an
    extension of docutils.parsers.rst.directives.tables.ListTable, because it has a nice method
    to create table from string content. However, references to
    the table would appeared as "Table #", whereas this directive is intended, as the name says, to
    be an images grid *figure*. We then tried to return a figure wrapping a table, but this does not
    split if the table is too long (even with a longtable inside a figure). We then passed to a
    solution where we rendered this directive as a longtable followed by a "fake" figure without
    images but holding potential captions and allowing references within the text. Finally, we
    merged the last two tries: the rendering is STILL rendered as as a longtable followed by a
    "fake" figure, but the directive itself behaves like a CSVTable, so that we can add file names
    also in the directive content
"""
import os
from docutils.nodes import Element
from docutils.parsers.rst import directives
from gfzreport.sphinxbuild.core.extensions.csvfigure import CsvFigureDirective
from docutils.nodes import image as img_node

_DIRECTIVE_NAME = 'gridfigure'


class imggrid(Element):
    pass


class ImgsGridDirective(CsvFigureDirective):

    option_spec = CsvFigureDirective.option_spec.copy()  # @UndefinedVariable
    option_spec.update({'dir': directives.path, 'errorsastext': directives.unchanged})

    def run(self):
        nodez = CsvFigureDirective.run(self)

        # add the 'longtable' class attribute to the table. This will force to display in the
        # LatexTranslator as latex longtable. This in turn is handy cause we let latex handle the
        # table width, (NOTE: if the table has images, we NEED to cause we cannot set an arbitrary
        # number of lines, as sphinx does)
        table_atts = nodez[0].children[0].attributes
        if 'longtable' not in table_atts['classes']:
            table_atts['classes'].append('longtable')

        base_dir = self.options['dir']

        if 'errorsastext' in self.options:
            errastext = self.options['errorsastext'].lower().strip() in ('yes', '1', 'true')
        else:
            errastext = False

        # base dir is relative to the source directory, so get root dir to check later
        # if file exists
        root_dir = os.path.abspath(os.path.join(self.state.inliner.document.settings.env.srcdir,
                                                base_dir))
        # now replace each string given in the csv (file or table) with an image node
        # with the correct path:
        for row, col, is_row_header, is_stub_column, node, node_text in self.itertable(nodez):
            # node might be None, it is also the case when the csv "cell" was empty string
            if is_row_header or is_stub_column or not node:
                continue
            filename = node_text
            fileexists = filename and os.path.isfile(os.path.join(root_dir, filename))
            if fileexists or not errastext:
                imgnode = img_node(**self.options)
                imgnode.attributes['uri'] = os.path.join(base_dir, filename)
                node.replace_self(imgnode)

        ret = imggrid(**self.options)
        nodez.append(ret)
        return nodez


def visit_imggrid_node_latex(self, node):
    # Note that the directive above is built in order to delegate sphinx for everything:
    # build a figure wrapping a longtable. This also assures that custom commands
    # referencing the figure or the table (e.g. labels, or `includegraphics` custom command) work.
    # So why we appended this node? Because:
    # 1) longtables inside a float environment (the figure) seem not to split across pages.
    # Therefore, move the figure AFTER the longtable (more specifically, move the text
    # from \begin{figure} to \begin{longtable} before \end{figure}
    # 2) rename the longtable headers "table continued from..to previous page" which are
    # automatically printed for multi-page tables: replace "table" with "figure" and also account
    # for the fact that the figure number is the *next* figure (see point 1): this is achieved via
    # latex \addtocounter{figure}{1}, \addtocounter{figure}{-1})

    # final note: maybe in the
    # future we need some code in between which forces us to move this code to depart_imggrid...

    # iterate reversed to parse content just added:
    for i in xrange(len(self.body)-1, -1, -1):
        # find end of longtable:
        if self.body[i].strip() == "\\end{longtable}":
            # re-iterate from the end of longtable:
            for j in xrange(i-1, -1, -1):
                # find start of longtable:
                if self.body[j].strip() == "\\begin{longtable}":
                    # re-iterateo from the start of longtable
                    for k in xrange(j-1, -1, -1):
                        # find start of wrapping figure
                        if self.body[k].strip().startswith("\\begin{figure}"):
                            # set the fig_start list of strings which have to be moved AFTER
                            # the longtable:
                            fig_start = self.body[k: j]
                            # set the table list of strings:
                            table = self.body[j: i+1]
                            # set the remaining figure:
                            fig_end = self.body[i+1:]
                            # replace the longtable header line where we write references to the
                            # current table number. The reference is to the NEXT figure number
                            # (use \thefigure providing \addtocounter later)
                            for x in xrange(len(table)):
                                if table[x].strip().startswith(r'{{\tablecontinued{\tablename\ '
                                                               r'\thetable{} '):
                                    table[x] = table[x].replace(r'\tablename\ \thetable{}',
                                                                r'\figurename\ \thefigure{}')
                                    # we added \thefigure{} (Why curly brakets?
                                    # why sphinx does that and we don't have time to investigate)
                                    # but \thefigure needs to point to our NEXT figure. So
                                    # add counter:
                                    table = ["\n\n\\addtocounter{figure}{1}\n\n"] + table + \
                                        ["\n\n\\addtocounter{figure}{-1}\n\n"]
                                    break
                            # move the figure up of a \textfloatsep length, so to give the
                            # impression it's the caption
                            self.body = self.body[:k] + table + \
                                ["\n\\vspace{-\\textfloatsep}\n"] + \
                                fig_start + fig_end
                            return


def depart_imggrid_node_latex(self, node):
    pass


def visit_imggrid_node_html(self, node):
    # as we built it, the rendering is fine. self will pass this node and process
    # its children correctly
    pass


def depart_imggrid_node_html(self, node):
    # as we built it, the rendering is fine. self will pass this node and process
    # its children correctly
    pass


def setup(app):
    app.add_directive(_DIRECTIVE_NAME, ImgsGridDirective)
    app.add_node(imggrid, latex=(visit_imggrid_node_latex, depart_imggrid_node_latex),
                 html=(visit_imggrid_node_html, depart_imggrid_node_html))
    # there is an options which might be handy: return a custom node and add it as enumerable
    # Fine, BUT: in latex the label is appended before the node, thus we should make a
    # workaround to put it inside the figure. And in html, the figure inside the custom node
    # is anyway counted also so that references are messed up. Leave here the syntax to add
    # enumerable node, although it's useless here
#     app.add_enumerable_node(imggrid, "figure", title_getter=None, latex=..., html=...)
