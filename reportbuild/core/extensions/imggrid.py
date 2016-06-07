# -*- coding: utf-8 -*-
"""
    Implements the sphinx directive imggrid:
    .. images-grid:: folder

    History: the latex rendering is the trickiest part: we first implemented this directive as an
    extension of docutils.parsers.rst.directives.tables import ListTable. However, references to
    the table would appear as "Table #", whereas this directive is intended, as the name says, to
    display images in a grid. We then tried to return a figure wrapping a table, but this does not
    split if the table is too long (even with a longtable inside a figure). The final solution was
    to render this directive as a longtable followed by a "fake" figure without images but holding
    potential captions and allowing references within the text

    This directive extends figure and then checks the folder for all files specified with the 
    options. It returns a set of two nodes, the first is the "parent" figure (removing
    the image child, which points to folder and would raise problems in sphinx), and a imggrid
    node, which is just a collection of images sub-nodes representing the images to be displayed in
    the grid. We need to process the image nodes inside the directive cause Sphinx understands that
    these images need to be copied to the build directory

    When visiting the imggrid node in latex, we are then sure we just added a figure to the body.
    The figure holds the caption provided in the directive and potential references to it, if they
    are written just before the directive (in general, they work only if the next element
    is a container, a table or a figure). We remove from the body the portion of the text
    referring to that figure, and then we build a longtable with our images in the grid (we can
    sepcify different tables but longtable allows us to split big grids). Finally, the trick: we
    append the portion of text referncing the figure at the end, so that captions and href works for
    the table just added and they look like referncing the longtable.

    Supported options (the first four apply to EACH sub-image) BUT TO BE TESTED:
    width
    align
    figwidth (ovverrides width if given)
    figalign (overrides align if given)
    class
    figclass (appended to class)
"""
import os
import re
# import urllib
# import urllib2
# from xml.dom import minidom

from docutils import nodes  # , utils
from docutils.parsers.rst import directives  # , roles
import shlex
import pandas as pd
from os import strerror
from os import listdir
from os.path import join, isdir  # isfile, isdir, splitext, basename
import errno
# from docutils.parsers.rst.directives.tables import ListTable
from docutils.parsers.rst.directives import images
from reportbuild.core.utils import regex
from reportbuild.core.extensions.setup import relfn2path
from sphinx.writers.latex import UnsupportedError
from sphinx.locale import _  # WARNING: WTF IS THAT A FUNCTION NAME?!!! WE NEED TO IMPORT IT
from docutils.nodes import SkipNode
# FOR THE TABLE HEADER GENERATION (see below) WATCH OUT WHEN USING "_"!!!

_DIRECTIVE_NAME = 'images-grid'


class imggrid(nodes.Element):
    pass


def get_files(folder,
              columns=None,
              file_ext=None,
              transpose=False):

    orig_folder = folder
    folder = relfn2path(folder)
    columns_re = None if columns is None else [regex(c) for c in columns]
    # to see OsError error numbers, see here
    # https://docs.python.org/2/library/errno.html#module-errno
    # Here we use two:
    # errno.EINVAL ' invalid argument'
    # errno.errno.ENOENT 'no such file or directory'
    try:
        if not isdir(folder):
            # to build an OSError, see
            # http://stackoverflow.com/questions/8978057/raising-builtin-exception-with-default-message-in-python
            raise OSError(errno.ENOTDIR, strerror(errno.ENOTDIR), folder)
            # errno.ENOTDIR 'Not a directory'
            # Alternatively:
            # errno.ENOENT 'No such file or directory'
    except TypeError:
        raise OSError(errno.ENOTDIR, strerror(errno.ENOTDIR), str(folder)+" "+str(type(folder)))

    ret = pd.DataFrame(columns=['file_path'] if columns is None else columns)

    if file_ext and file_ext[0] != ".":
            file_ext = "." + file_ext

    for file_ in listdir(folder):
        file_path = join(folder, file_)
        row = file_path
        col = "file_path"

        if file_ext and os.path.splitext(file_)[1] != file_ext:
            continue

        if columns is not None:
            row = col = None
            for i, c in enumerate(columns_re):
                mobj = c.search(file_)
                if mobj:
                    col = columns[i]
                    row = file_[:mobj.start()] + file_[mobj.end():]
                    break
            if row is None:
                continue

        # Reminder:
        # for adding new columns to existing dataframe see:
        # http://stackoverflow.com/questions/12555323
        try:
            ret.loc[row]  # row not present? (by datafreme's index)
        except KeyError:
            ret = ret.append(pd.DataFrame(index=[row], columns=ret.columns, data=None))

        ret.loc[row, col] = os.path.join(orig_folder, file_)  # to preserve the path for sphinx
        # relative imports

    if ret.empty:
        raise OSError("Error in %s directive: no files found with given arguments found. Please"
                      "check arguments" % _DIRECTIVE_NAME)
        # raise OSError(errno.ENODATA, strerror(errno.ENODATA), folder)

    if transpose:
        ret = ret.transpose()

    # now replace NaNs with None. FIXME: check if it's possible to instantiate stuff with
    # None already to avoid this
    return ret.where((pd.notnull(ret)), None)


# FIXME: see sphinx extensions and arrange better this directive
class ImgsGridDirective(images.Figure):
    own_option_spec = {
                       'transpose': lambda arg: arg if arg and arg.lower() in ('true', 'false', '0', '1') else '',
                       'file-ext': lambda arg: arg,
                       'columns': lambda arg: arg if arg is None else shlex.split(arg),
                       'header-labels': lambda arg: [] if arg is None else shlex.split(arg),
                       'latex-custom-graphics-opt': lambda arg: arg,
                       'latex-table': lambda arg: arg,
                       }

    option_spec = images.Figure.option_spec.copy()  # @UndefinedVariable
    option_spec.update(own_option_spec)

    def run(self):

        ret_nodes = images.Figure.run(self)
        # returns two child nodes , the first an image, the second (optional BUT MUST BE CHECKED)
        # a caption

        # next two lines are taken from:
        # http://docutils.sourceforge.net/docs/howto/rst-directives.html#image
        reference = directives.uri(self.arguments[0])
        ret = imggrid(**self.options)  # '', *ret_nodes[0].children, **ret_nodes[0].attributes)
        columns = self.options['columns']
        files = get_files(reference, columns=self.options.get('columns', None),
                          file_ext=self.options.get('file-ext', None),
                          transpose=self.options.get('transpose', False))
        ret['columns'] = columns
        header_labels = self.options.get('header-labels', [])
        ret['header-labels'] = header_labels if not header_labels else \
            header_labels[0: len(columns)] + (max(0, len(columns) - len(header_labels)) * [''])
        ret['latex-custom-graphics-opt'] = self.options.get('latex-custom-graphics-opt', '')
        ret['latex-table'] = self.options.get('latex-table', 'longtable')
        ret['row_count'] = len(files)

        # we need to build NOW a set of image nodes cause Sphinx understands that it must copy them
        # to the build folder
        image_nodes = []
        for row_name, row_series in files.iterrows():
            for i, filepath in enumerate(row_series):  # first element is the row "name"
                if filepath:
                    image = ret_nodes[0].children[0].copy()  # should also copy attributes, e.g. width
                    image['uri'] = filepath
                    image_nodes.append(image)
                else:
                    # in a former implementation, where we passed a ListTable node,
                    # we could not set a leaf text node, we need to set a node to which classes are
                    # "spreadable". We keep here this workaround although a simple nodes.Text
                    # might be sufficient:
                    image_nodes.append(nodes.paragraph('', *[nodes.Text('')]))

        ret.children = image_nodes

        # Remove the image child of the figure so that we do not have problems
        # (it points to the dir and later sphinx complains cause cannot copy a dir)
        ret_nodes[0].children = ret_nodes[0].children[1:]
        # NOW return the "fake" figure PLUS our node. The fake figure will be processed BEFORE
        # our node, so it will setup ALL references correctly, if any
        # Then we will process our "longtable" (or what we want as table)

        return ret_nodes + [ret]


def visit_imggrid_node_latex(self, node):
    # raise error if within a table (consistent with sphinx latex default writer)
    # self is a Latex translator
    if self.table:
        raise UnsupportedError(
            '%s:%s: nested tables are not yet implemented.' %
            (self.curfilestack[-1], node.line or ''))

    # as the directive above returned a figure and an imggrid node, the figure has been added
    # to the doc with the (potential) labels properly set. Move this at the end of the table
    # we are up to build
    figure_at_end = True  # this might be a param in future releases
    tmp_fig_body = []
    if figure_at_end:
        i = -1
        while "\\begin{figure}" not in self.body[i]:
            i -= 1
        tmp_fig_body = self.body[i:]
        self.body = self.body[:i]

    # build the table (longtable probably. FIXME: do we need other tables than that?)
    cols, rows = len(node['columns']), node['row_count']
    header_labels = node['header-labels']
    lcgo = node['latex-custom-graphics-opt']
    latextable = node['latex-table']

    alg = node.attributes.get('align', None) or 'center'
    alg = alg[0] if alg in ("left", "right") else "c"
    # FIXME: check different options!

    if self.next_table_colspec:  # supports for the .. tabularcolumns:: sphinx directive
        tabularcolumns = self.next_table_colspec
        self.next_table_colspec = None
    else:
        tabularcolumns = alg * cols

    self.body.append("\n")
    self.body.append(r"\begin{" + latextable+"}{" + tabularcolumns + "}\n")

    # append header labels, if any. FIXME: only raw text with ASCI chars supported!
    header_labels_str = ""
    if header_labels:
        header_labels_str = "\n&\n".join(header_labels)

    self.body.append(header_labels_str)

    if latextable == "longtable":
        # try to find a reference to the figure we just removed from the body (and will
        # re-append later)
        fig_ref = ""  # by default, it is "Fig." or whatever we set as default
        for line in tmp_fig_body:
            mtc = re.search(r"\\label\{(.*?:.*?)\}", line)
            if mtc:
                fig_ref = r"\hyperref[%s]{\figurename\ \ref{%s}} " % (mtc.group(1), mtc.group(1))
                break

        self.body.append('\\endfirsthead\n\n')
        self.body.append('\\multicolumn{%s}{c}%%\n' % cols)
        self.body.append(r'{{\footnotesize \tablecontinued{%s(%s)}}} \\'
                         % (fig_ref, _('continued from previous page')))
        self.body.append('\n')
        # self.body.append('\\hline\n')
        self.body.append(header_labels_str)
        self.body.append('\\endhead\n\n')
        self.body.append('\\multicolumn{%s}{c}%%\n' % cols)
        self.body.append(r'{{\footnotesize \tablecontinued{%s(%s)}}}'  # \\ \hline'
                         % (fig_ref, _('Continued on next page')))
        self.body.append('\n\\endfoot\n\n')
        self.body.append('\\endlastfoot\n\n')
    else:
        self.body.append(r'\\\n\n')

    # Table body:
    len_ = len(self.body)  # remember where we are NOW
    # FIXME: check if figure options are propagated!
    for i in xrange(rows):
        for j in xrange(cols):
            if j > 0:
                self.body.append("\n&")
            image = node.children[i*cols + j]
            # in principle (should be tested) the width attribute of node is propagated through
            # all its children. So we might want to calculate it once. FIXME
            if not node.attributes.get('width', None):
                image.attributes['width'] = str(int(100.0 / cols)) + "%"
            if isinstance(image, nodes.image):
                self.visit_image(image)
                self.depart_image(image)
        self.body.append("\n\\\\\n")
    self.body.append(r'\end{' + latextable + '}')

    # override custom graphics options, if any:
    if lcgo:
        reg = re.compile("\\\\includegraphics(?:\\[.*?\\])?\\{")
        for i in xrange(len_, len(self.body)):
            m = reg.search(self.body[i])
            if m:
                self.body[i] = self.body[i][0:m.start()] + r"\includegraphics[" + \
                    lcgo + "]{" + self.body[i][m.end():]

    # The trick here is that if we wrapped all the table above inside a figure
    # (which was what we did at the beginning) the figure is NOT splitted in multi pages
    # if it overflows. Now it does, BUT: we want people referencing that longtable to
    # actually reference a figure! So we doi the trick: write here an empty figure
    # If we want to add the caption OVER the table, place this code BEFORE we generate the
    # table (should be tested though)

    # remove the space that a figure has at the top:
    # See here:
    # http://tex.stackexchange.com/questions/26521/how-to-change-the-spacing-between-figures-tables-and-text
    if tmp_fig_body:
        self.body.append("\n\\vspace{-\\textfloatsep}\n")
        self.body.extend(tmp_fig_body)
    raise SkipNode()  # do not call the children node rendering, and do not call depart


def depart_imggrid_node_latex(self, node):
    # self is a Latex translator
    pass


def visit_imggrid_node_html(self, node):
    # self is a Latex translator
    cols, rows = len(node['columns']), node['row_count']
    self.body.append("\n<table class='img_grid' border=0>")
    wdt = node.attributes.pop("width", None)
    if not wdt:
        wdt = str(int(100.0 / cols)) + "%"

    self.body.append("\n<colgroup>")
    for _ in xrange(cols):
        self.body.append("\n<col style='width:%s'>" % wdt)
    self.body.append("\n</colgroup>")

    self.body.append("\n<tbody>")
    for i in xrange(rows):
        self.body.append("\n<tr>")
        for j in xrange(cols):
            image = node.children[i*cols + j]
            image.attributes.pop('width', None)  # we already defined in colgroup
            # Moreover, on Cjrome the percentage width refers to the width of the containing td
            self.body.append("\n<td>")
            if isinstance(image, nodes.image):
                self.visit_image(image)
                self.depart_image(image)
            self.body.append("</td>")
        self.body.append("\n</tr>")
    self.body.append("\n</tbody>")
    self.body.append("\n</table>")
    raise SkipNode()  # do not call the children node rendering, and do not call depart

def depart_imggrid_node_html(self, node):
    # self is a Latex translator
    pass

def setup(app):
    app.add_directive(_DIRECTIVE_NAME, ImgsGridDirective)
    app.add_node(imggrid,
                 latex=(visit_imggrid_node_latex, depart_imggrid_node_latex),
                 html=(visit_imggrid_node_html, depart_imggrid_node_html))
