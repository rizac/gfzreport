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
from core.utils import regex
# from core.extensions.pdfimg import pdfimg
# def spec_float(argument):
#     """
#     Check for a float argument; raise ``ValueError`` if not.
#     (Directive option conversion function.)
#     """
#     return float(argument)


# def reg(arg):
#     """Returns a regular expression built by escaping str(arg). Note
#     that arg characters "?" and "*" will NOT be escaped but converted to "." and ".*".
#     Two exceptions: if if arg is None, the regexp ".*" (which matches all strings) will be returned
#     if arg is already a regular expression, it will be returned immediately without modifications
#     """
#     if arg is None:
#         return re.compile(".*")
# 
#     if isinstance(arg, re.compile(".").__class__):
#         return arg
# 
#     return re.compile(re.escape(str(arg)).replace("\\?", ".").replace("\\*", ".*"))


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


# class imgsgrid(nodes.General, nodes.Element):
#     pass


# FIXME: see sphinx extensions and arrange better this directive
class ImgsGridDirective(ListTable):
    own_option_spec = dict(columns=lambda arg: arg if arg is None else shlex.split(arg))

    option_spec = ListTable.option_spec.copy()  # @UndefinedVariable
    option_spec.update(own_option_spec)

    def toimgnode(self, file_path):
        options = self.options
        if not file_path:
            node = nodes.warning("'%s' not found")  # FIXME: Add admonitions.Warning!
        else:
            reference = directives.uri(file_path)
            options['uri'] = reference
            node = nodes.image(".. image: %s" % file_path, uri=options['uri'], width='100%')  # , **options)
        return node

    def run(self):
        if 'columns' not in self.options:
            self.options['columns'] = None

        # next two lines are taken from:
        # http://docutils.sourceforge.net/docs/howto/rst-directives.html#image
        reference = directives.uri(self.arguments[0])
        self.options['uri'] = reference  # FIXME: move to static method???

        files = get_files(reference, columns=self.options['columns'])
        table_data = []
        for f in files.iterrows():
            row_node = [self.toimgnode(value) for _, value in f[1].iteritems()]
            table_data.append(row_node)

        # Generate the table node from the given list of elements
        col_widths = self.get_column_widths(len(files.columns))
        # copied from the super run method
        # for an example, see here:
        # https://bitbucket.org/birkenfeld/sphinx-contrib/src/558d80ca46aa77bf7db20503d50b007db2c864e3/exceltable/sphinxcontrib/exceltable.py?at=default&fileviewer=file-view-default#exceltable.py-266
        table_node = self.build_table_from_list(table_data, col_widths, 0, 0)
        table_node['classes'] += self.options.get('class', [])
        # add custom class:
        if 'source_imggrid_directive' not in table_node['classes']:
            table_node['classes'] += ['source_imggrid_directive']
        self.add_name(table_node)
        return [table_node]


def setup(app):
    app.add_directive('imgages-grid', ImgsGridDirective)
