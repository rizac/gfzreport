# -*- coding: utf-8 -*-
"""
    Implements the sphinx directive imggrid:

    .. images-grid:: figure_caption
        :dir: folder

        data

    This directive has to be written and filled like a CSVTable BUT produces a "table" of figures.
    IT extends CsvFigureDirective, which in turn extends both CSVTable and Figure. It first parses
    the document as CSVTable,
    the returned table cell is replaced by images nodes first by joining the dir argument and the
    data provided. Then, the content is parsed as
    Figure directive, and we set the figure children as the table, followed by the caption (if any)
    Note that we need to process the image nodes inside the directive cause Sphinx understands that
    these images need to be copied to the build directory
    Thus the returned directive nodes are a simple figure wrapping a table of images, followed by
    all potential node messages that the super calls generated
    (appended as CSVTable + Figure messages).
    This lets previous labels written in the rst point to the figure (like 'see Fig...' and not
    'see Table...') and custom directives like tabularcolumns or tabularrows point to the wrapped
    table.

    If we had to generate html, that would be all we need. But there is latex, and sphinx pretending
    to support it. ;)

    Because images in a grid might overflow the page, and we need a reliable method to use
    longtables. And once we done that, we need to fix sphinx HARCODING headers and footers saying
    "Table # continued on next page" whereas we want "Figure # continued on next page".
    And now comes the BIG, BIG mess.
    First, Sphinx (1.4.1) claims it uses tabulary package for latex table. FALSE. It HARDCODES a
    rule that, if we provided a table class 'longtable' or, even worse, the table rows count exceeds
    30 (or 40, or whatever), then IT USES LONGTABLES.
    Ok, that's fine, we also want to use longtables, because we need latex to handle page overflow,
    which happens frequently, with a grid of images.
    So the class 'longtable' is appended to the returned table class by this directive.

    The second problem is to modify the longtable headers which print something like
    "Table # continued to next page", replacing that "Table" with "Figure" and # with the correct
    figure number. We do it via a hack (caused by a previous Sphinx hack) in
    depart_imggrid_node_latex function. Note that, as the figure will FOLLOW the table in latex,
    we use \addtocounter{figure}...

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
from docutils.parsers.rst.directives import path as directive_path_func
from gfzreport.sphinxbuild.core.extensions.csvfigure import CsvFigureDirective

# we define the directive option spec globally because it depends on the imports below:
_own_option_spec = {'dir': directive_path_func}

from gfzreport.sphinxbuild.core.extensions.lateximgs import img_node   # nopep8
from gfzreport.sphinxbuild.core.extensions.lateximgs import LATEX_OPT_SPEC   # nopep8
_own_option_spec.update(LATEX_OPT_SPEC)
# NOTE ON the THREE LINES ABOVE: lateximgs.img_node is a node which overwrites image
# and figure directives to account for the 'latex-includegraphics-opts' option. However, for the
# users who do not want to overwrite standard rst directives (like image and figure) or just want to
# import this module alone by copy/paste, REMOVE THE THREE LINES ABOVE AND UNCOMMENT
# the following:
# from docutils.nodes import image as img_node


_DIRECTIVE_NAME = 'images-grid'


class imggrid(Element):
    pass


class ImgsGridDirective(CsvFigureDirective):

    option_spec = CsvFigureDirective.option_spec.copy()  # @UndefinedVariable
    option_spec.update(_own_option_spec)

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

        # now replace each string given in the csv (file or table) with an image node
        # with the correct path:
        for row, col, is_row_header, is_stub_column, node, node_text in self.itertable(nodez):
            # node might be None, it is also the case when the csv "cell" was empty string
            if is_row_header or is_stub_column or not node:
                continue
            filename = node_text or "[no file name]"
            imgnode = img_node(**self.options)
            imgnode.attributes['uri'] = os.path.join(base_dir, filename)
            node.replace_self(imgnode)

        ret = imggrid(**self.options)
        nodez.append(ret)
        return nodez


def visit_imggrid_node_latex(self, node):
    # self.body has been built according to the returned nodes, i.e.
    # with a figure wrapping a table.
    # However, in latex we need to do two things more:
    # 1) The part of the wrapping figure code from its start until the table start is moved AFTER
    # the table (longtables inside a float environment seems not to split in latex)
    # 2) longtables in sphinx provide the so called headers, i.e portions of text to display at the
    # top and bottom when the table is splitted between pages. Something like e.g.
    # "table 3 continued from previous page". We want to render it as
    # e.g. "figure 4  continued from previous page", where that "4" is calculated considering that
    # our NEXT figure is our imggrid figure (so using latex \addtocounter{figure}{1},
    # \addtocounter{figure}{-1})

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
                                    # why sphinx does that and we don;t have time to investigate)
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
