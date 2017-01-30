'''
Extension to specify which rows to be shown in the next latex tabular environment (
like sphinx's `.. tabularcolumns`). The extension assumes that sphinx generates hlines
**always** for any table. In principle, works also for more complex tables with multicolumns.
Note: As it has been tested with csv-table's only, and the extension works by hacking and parsing
the generated LateX (sphinx does not provide any other solution) we cannot guarantee that this
extension works 100% of the times.
Example: place before the table you want to customize:

\.\. tabularrows\:\:
     \:hline-hide\: -1 1:2 4 5 6

(replace `hide` with `show` if needed, but do not use both options)
Created on Apr 4, 2016

@author: riccardo
'''
import re
import sys
from docutils import nodes
from docutils.parsers.rst import Directive
# import numpy as np

_TR_ID = "TABULAR_ROWS_ARG"
_CHUNKS_RE = re.compile(r"\s*,\s*|\s*;\s*|\s+")


class tabularrows_node(nodes.Element):
    pass


def _check_arg(arg):
    """returns the string in chunks and does a preliminary check"""
    arr_test = range(10)  # @UnusedVariable
    chunks = _CHUNKS_RE.split(arg.strip())
    for sss in chunks:
        try:
            eval("arr_test[%s]" % sss)
        except IndexError:
            pass
    return chunks


class TabularRowsDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
                    # the lambda function verifies the arg by running
                    # indexiter and and see if no error is raised:
                    'hline-show': _check_arg,
                    'hline-hide':  _check_arg,
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
    """Visits this node in latex.
    Note that this node has already been put AFTER the next table in the document
    (doctree_read)"""
    # hline_indices is in principle a list of integers, each integer I denoting
    # the index of self.body there the I-th "\hline" is (so that we might remove the \hline,
    # or keep it). *BUT*: in longtable's, the first and last hlines might be set
    # for all pages, all pages except the first, all pages except the last. Thus, we might have
    # two indices denoting the first hline, or the last. that's why hline_indices is a list
    # of iterables, each iterable returning the indices in self.body of the I-th hline
    hline_indices = []
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
                # See above: longtable has, in current sphinx version (1.5.1), some lines inside
                # the begin{longtable} body which set up the headers when we continue a table
                # either from a previous page or to the following page.
                # This means that there are TWO lines of self.body which
                # reference the first table line. That's why each element of hline_indices is
                # in turn a list of indices. Look at the method LAtexTranslator.depart_table
                # located in [current_python_path]/site-packages/sphinx/writers/latex.py
                if bodyline.strip() == '\\endfirsthead':
                    # we still have tableheaders
                    idx0 = i - 1 - len(self.tableheaders)
                    idx1 = i - 1
                    if idx0 >= 0 and idx1 >= 0 and \
                        self.body[idx0].strip() == HLINE and \
                            self.body[idx1].strip() == HLINE:
                        hline_indices[-2].append(idx1)
                        hline_indices[-1].append(idx0)
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
                        hline_indices.append([idx1])
                        hline_indices.append([idx0])
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
                hline_indices.append([i])

    if not parse_was_good:
        sys.stderr.write("ERROR: tabularrows skipped : encountered a problem in parsing next table")
        return

    # restore correct order as hline_indices is built "reversed" (see loop above)
    hline_indices.reverse()

    chunks = node.attributes['indices']
    rng = range(len(hline_indices))  # @UnusedVariable
    indices = []
    for chunk in chunks:
        try:
            ind = eval("rng[%s]" % chunk)
            if not hasattr(ind, '__iter__'):
                ind = [ind]
            indices.extend(int(_) for _ in ind)
        except IndexError:
            pass
    indices.sort()
    indices = set(indices)
    if node.attributes['what'] == 'show':
        indices = set(rng) - indices

    for index in indices:  # sets do not preserve order, like dicts iterations. But should be fine
        for i in hline_indices[index]:  # remember, we might have more indices mapped to a hline...
            self.body[i] = ""


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
