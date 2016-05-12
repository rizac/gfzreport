# -*- coding: utf-8 -*-
"""
    Implements the sphinx directive imggrid:
    .. imgages-grid:: folder
"""

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
from docutils.parsers.rst.directives.tables import ListTable
from docutils.parsers.rst.directives import images
from core.utils import regex
from docutils.utils import SystemMessagePropagation

def get_files(folder,
              columns=None,
              transpose=False):

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

    for file_ in listdir(folder):
        file_path = join(folder, file_)
        row = file_path
        col = "file_path"

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

        ret.loc[row, col] = file_path

    if ret.empty:
        raise OSError(errno.ENODATA, strerror(errno.ENODATA), folder)

    if transpose:
        ret = ret.transpose()

    # now replace NaNs with None. FIXME: check if it's possible to instantiate stuff with
    # None already to avoid this
    return ret.where((pd.notnull(ret)), None)


# FIXME: see sphinx extensions and arrange better this directive
class ImgsGridDirective(images.Figure):
    own_option_spec = {
                       'columns': lambda arg: arg if arg is None else shlex.split(arg),
                       'header-labels': lambda arg: arg if arg is None else shlex.split(arg)
                       }

    option_spec = images.Figure.option_spec.copy()  # @UndefinedVariable
    option_spec.update(own_option_spec)

    def toimgnode(self, file_path):
        options = self.options
        if not file_path:
            # we cannot set a leaf text node, we need to set a node to which classes are
            # "spreadable". so the workaround is:
            node = nodes.paragraph('', *[nodes.Text('')])
            # node = nodes.warning("'%s' not found")  # FIXME: Add admonitions.Warning!
        else:
            reference = directives.uri(file_path)
            options['uri'] = reference
            node = nodes.image(".. image: %s" % file_path, uri=options['uri'], width='100%')  # , **options)
        return node

    def run(self):
        if 'columns' not in self.options:
            self.options['columns'] = None

        nodes = images.Figure.run(self)

        # next two lines are taken from:
        # http://docutils.sourceforge.net/docs/howto/rst-directives.html#image
        reference = directives.uri(self.arguments[0])

        files = get_files(reference, columns=self.options['columns'])
        table_data = []

        for f in files.iterrows():
            row_node = [self.toimgnode(value) for _, value in f[1].iteritems()]
            table_data.append(row_node)

        columns = len(files.columns)

        header_rows = 0
        if 'header-labels' in self.options:
            header_rows = 1
            table_data.insert(0, self.options['header-labels'] +
                              ([''] * max(0, columns - len(self.options['header-labels'])))
                              )
        # Generate the table node from the given list of elements
        col_widths = self.get_column_widths(columns)
        # copied from the super run method
        # for an example, see here:
        # https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa77bf7db20503d50b007db2c864e3/exceltable/sphinxcontrib/exceltable.py?at=default&fileviewer=file-view-default#exceltable.py-266
        table_node = self.build_table_from_list(table_data, col_widths, header_rows, 0)

        # add custom class:
        if 'source_imggrid_directive' not in nodes[0]['classes']:
            nodes[0]['classes'] += ['source_imggrid_directive']

        nodes[0].children[0] = table_node
        return nodes

    def build_table_from_list(self, table_data, col_widths, header_rows, stub_columns):
        table = nodes.table()
        tgroup = nodes.tgroup(cols=len(col_widths))
        table += tgroup
        for col_width in col_widths:
            colspec = nodes.colspec(colwidth=col_width)
            if stub_columns:
                colspec.attributes['stub'] = 1
                stub_columns -= 1
            tgroup += colspec
        rows = []
        for row in table_data:
            row_node = nodes.row()
            for cell in row:
                entry = nodes.entry()
                entry += cell
                row_node += entry
            rows.append(row_node)
        if header_rows:
            thead = nodes.thead()
            thead.extend(rows[:header_rows])
            tgroup += thead
        tbody = nodes.tbody()
        tbody.extend(rows[header_rows:])
        tgroup += tbody
        return table

    def get_column_widths(self, max_cols):
        # copied from ListTable directive
        if 'widths' in self.options:
            col_widths = self.options['widths']
            if len(col_widths) != max_cols:
                error = self.state_machine.reporter.error(
                    '"%s" widths do not match the number of columns in table '
                    '(%s).' % (self.name, max_cols), nodes.literal_block(
                    self.block_text, self.block_text), line=self.lineno)
                raise SystemMessagePropagation(error)
        elif max_cols:
            col_widths = [100 // max_cols] * max_cols
        else:
            error = self.state_machine.reporter.error(
                'No table data detected in CSV file.', nodes.literal_block(
                self.block_text, self.block_text), line=self.lineno)
            raise SystemMessagePropagation(error)
        return col_widths
#     def make_title(self):
#         """Overrides make title to take the content instead of the first argument"""
#         if self.content:
#             title_text = self.content
#             text_nodes, messages = self.state.inline_text(title_text,
#                                                           self.lineno)
#             title = nodes.title(title_text, '', *text_nodes)
#         else:
#             title = None
#             messages = []
#         return title, messages


def setup(app):
    app.add_directive('imgages-grid', ImgsGridDirective)
