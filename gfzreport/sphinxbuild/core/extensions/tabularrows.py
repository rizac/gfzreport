'''
Extension to specify which rows to be shown in latex tabular environment
Works by hacking and parsing the generated LateX, for complex tables with multicolumns
or rows might not work
Example: place before the table you want to customize:

\.\. tabularrows\:\:
     \:hline-hide\: -1 1:2 4 5 6

(replace hide with show if needed, but do not use both options)
Created on Apr 4, 2016

@author: riccardo
'''
import re
import sys
from docutils import nodes
from docutils.parsers.rst import Directive
import numpy as np

TR_ID = "TABULAR_ROWS_ARG"


def int_list(arg):
    """
    Converts a space-, semicolon- or comma-separated list of values into a Python list
    of integers.
    (Directive option conversion function.)

    Raises ValueError for non-positive-integer values.
    """
    if not arg.strip():
        return []

    semicolon_re = re.compile(r"(\-?\d+)\s*\:\s*(\-?\d+)")
    try:
        while True:
            match = semicolon_re.search(arg)
            if not match:
                break
            val1 = int(match.group(1))
            val2 = int(match.group(2))
            if not val2 > val1:
                raise ValueError()
            newval = " ".join(str(i) for i in xrange(val1, val2))
            arg = arg[:match.start(1)] + newval + arg[match.end(2):]

        return map(int, map(int, re.split(r"\s*,\s*|\s*;\s*|\s+", arg)))

    except (IndexError, ValueError):
        raise ValueError("malformed option in tabularrows: %s " % arg)


class tabularrows_node(nodes.Element):
    pass


class TabularRowsDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
                   'hline-show': int_list,
                   'hline-hide': int_list,
                   }
    has_content = False

    def run(self):
        hide = self.options.pop('hline-hide', [])
        show = self.options.pop('hline-show', [])
        if not show and not hide:
            return []
        elif show and hide:
            raise ValueError("You can't specify both :show: and :hide: in tabularrows options")
        elif hide:
            node = tabularrows_node(indices=hide, what="hide")
        else:
            node = tabularrows_node(indices=show, what="show")
        return [node]


def visit_tr_node_html(self, node):
    pass


def depart_tr_node_html(self, node):
    pass


def visit_tr_node_latex(self, node):

    table_hline_indices = []
    parse_was_good = False
    in_table = False
    is_longtable = False
    in_longtable_header = False
    expected_start = ""
    HLINE = "\\hline"
    i = len(self.body)
    endings = ("\\end{tabulary}", "\\end{tabular}", "\\end{longtable}")
    startings = ("\\begin{tabulary}", "\\begin{tabular}", "\\begin{longtable}")
    for bodyline in reversed(self.body):
        i -= 1
        if not in_table and bodyline.strip() in endings:
            expected_start = startings[endings.index(bodyline.strip())]
            in_table = True
            is_longtable = "\\begin{longtable}" in expected_start
        elif in_table:
            if in_longtable_header:
                # longtable has, in current sphinx version, some lines inside the begin{longtable}
                # body which set up the headers when we continue a table either from a previous page
                # or to the following page. This means that there are TWO lines of self.body which
                # reference the first table line. That's why each element of table_hline_indices is
                # in turn a list of indices. Look at the method LAtexTranslator.depart_table
                # located in [current_python_path]/site-packages/sphinx/writers/latex.py
                if bodyline.strip() == '\\endfirsthead':
                    # we still have tableheaders
                    idx0 = i - 1 - len(self.tableheaders)
                    idx1 = i - 1
                    if idx0 >= 0 and idx1 >= 0 and \
                        self.body[idx0].strip() == HLINE and \
                            self.body[idx1].strip() == HLINE:
                        table_hline_indices[-2].append(idx1)
                        table_hline_indices[-1].append(idx0)
                        parse_was_good = True
                        break  # exit, we already parsed all hlines
                    else:
                        break
                elif bodyline.strip() == '\\endhead':
                    idx0 = i - 1 - len(self.tableheaders)
                    idx1 = i - 1
                    if idx0 >= 0 and idx1 >= 0 and \
                        self.body[idx0].strip() == HLINE and \
                            self.body[idx1].strip() == HLINE:
                        table_hline_indices.append([idx1])
                        table_hline_indices.append([idx0])
                    else:
                        break
            elif is_longtable and bodyline.strip() == '\\endlastfoot':
                in_longtable_header = True
            elif bodyline.strip().startswith(expected_start):
                parse_was_good = True
                break
            elif HLINE == bodyline.strip() or \
                    (bodyline.strip().startswith('\\cline{') and bodyline.strip()[-1] == '}'):
                # why do we append a list? see comment above for longtable (if in_longtable_header:)
                table_hline_indices.append([i])

    if not parse_was_good:
        sys.stderr.write("ERROR: tabularrows skipped : encountered a problem in parsing next table")
        return

    table_hline_indices.reverse()

    indices = get_indices(node.attributes['indices'], len(table_hline_indices))
    if node.attributes['what'] == 'show':
        vals = np.zeros(len(table_hline_indices), dtype=np.bool)
        vals[indices] = True
        indices_to_hide = np.where(~vals)[0]  # np where returns tuple of a single element
        # with the arguments given
    else:
        indices_to_hide = indices

    for index in indices_to_hide:
        for i in table_hline_indices[index]:
            self.body[i] = ""


def get_indices(indices, hlines_count):
    indices_normalized = []
    for i in indices:
        i_normalized = hlines_count + i if i < 0 else i
        if i_normalized >= 0 and i_normalized < hlines_count:
            indices_normalized.append(i_normalized)
    return np.unique(indices_normalized)


def depart_tr_node_latex(self, node):
    pass


def doctree_read(app, doctree):
    """
        This method moves all tabularrows AFTER the referenced table, so that we can use
        the visit methods above.
    """
    # a = app.builder.env
    if app.buildername != 'latex':
        return

    def condition(node):
        return isinstance(node, nodes.table) or isinstance(node, tabularrows_node)

    last_known_tr_node = None
    for obj in doctree.traverse(condition):
        if isinstance(obj, tabularrows_node):
            obj.parent.children.remove(obj)
            last_known_tr_node = obj
        elif last_known_tr_node is not None:
            obj.parent.children.insert(obj.parent.children.index(obj) + 1, last_known_tr_node)
            last_known_tr_node = None


def setup(app):
    app.add_node(tabularrows_node,
                 html=(visit_tr_node_html, depart_tr_node_html),
                 latex=(visit_tr_node_latex, depart_tr_node_latex))
    app.add_directive('tabularrows', TabularRowsDirective)
    app.connect('doctree-read', doctree_read)
