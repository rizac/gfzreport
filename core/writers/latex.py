'''
Created on Apr 4, 2016

@author: riccardo
'''
from docutils.nodes import SkipNode
from sphinx.writers.latex import LaTeXTranslator as LT
from collections import OrderedDict as odict
import re

class LatexTranslator(LT):

    def __init__(self, document, builder):
        LT.__init__(self, document, builder)  # FIXME: check why new style super call does not work
        self.field_list = odict()  # preserves order
        self.field_list_start = []

    def visit_field_list(self, node):
        self.field_list_start = len(self.body)
        LT.visit_field_list(self, node)

    def depart_field_list(self, node):
        LT.depart_field_list(self, node)
        if len(self.body) == self.field_list_start+2:
            # remove field list stuff
            self.body = self.body[:-2]

        if hasattr(self, "abstract_text_reminder"):
            self.body.extend([r'\begin{abstract}', '\n',
                              self.abstract_text_reminder, '\n', r'\end{abstract}'])

    def visit_field(self, node):
        field_name = node.children[0].rawsource
        field_text = node.children[1].rawsource
        if field_name in ("author", "authors"):
            self.elements.update({'author': field_text.strip()})
            raise SkipNode()  # do not call the children node rendering, and do not call depart node

        if field_name == "revision":
            self.elements.update({'release': field_text.strip()})
            raise SkipNode()  # do not call the children node rendering, and do not call depart node

        if field_name == "abstract":
            self.abstract_text_reminder = field_text.strip()
            raise SkipNode()  # do not call the children node rendering, and do not call depart node

        LT.visit_field(self, node)

    def depart_field(self, node):
        LT.depart_field(self, node)  # superclass simply passes

#     def visit_table(self, node):
#         # set here the actual length of the body
#
#         self._body_len_before_table = len(self.body)
#         LT.visit_table(self, node)
#         if 'source_imggrid_directive' in node['classes']:
#             self._tmp_caption = self.table.caption
#             self.table.caption = None

    def depart_table(self, node):
        if 'source_imggrid_directive' not in node['classes']:
            LT.depart_table(self, node)
            return

        # we have an imagesgrid, which must be rendered as figure 
        # the code below is copied from the super-method for the case at hand
        # (\begin{tabulary}{\linewidth}{LLL})
        self.popbody()
        # images-grid case: add a figure before and after:
        align = '\\centering'
        self.body.append('\n\\begin{figure}[%s]\n%s\n' % \
                         (self.elements['figure_align'], align))

        if self.table.has_verbatim:
            self.body.append('\n\\begin{tabular}')
            endmacro = '\\end{tabular}\n\n'
        elif self.table.has_problematic and not self.table.colspec:
            # if the user has given us tabularcolumns, accept them and use
            # tabulary nevertheless
            self.body.append('\n\\begin{tabular}')
            endmacro = '\\end{tabular}\n\n'
        else:
            self.body.append('\n\\begin{tabulary}{\\linewidth}')
            endmacro = '\\end{tabulary}\n\n'
        if self.table.colspec:  # FIXME: what's that??
            self.body.append(self.table.colspec)
        else:
            if self.table.has_problematic:
                colwidth = 0.95 / self.table.colcount
                colspec = ('p{%.3f\\linewidth}' % colwidth) * \
                    self.table.colcount
                self.body.append('{' + colspec + '}\n')
            else:
                self.body.append('{' + ('L' * self.table.colcount) + '}\n')
        if self.table.caption is not None:
            self.body.append(u'\\caption{')
            for caption in self.table.caption:
                self.body.append(caption)
            self.body.append('}')
            for id_ in self.next_table_ids:
                self.body.append(self.hypertarget(id_, anchor=False))
            self.next_table_ids.clear()
            self.body.append(u'\\\\\n')

        self.body.extend(self.tableheaders)
        for line in self.tablebody:
            if line != "\\hline":  # remove horizontal lines
                self.body.append(line)
        self.body.append(endmacro)
        self.unrestrict_footnote(node)
        self.table = None
        self.tablebody = None
        self.body.append("\\end{figure}")

#
#
#         if self.table.rowcount > 30:
#             self.table.longtable = True
#         self.popbody()
#         if not self.table.longtable and self.table.caption is not None:
#             # this is the part of code I modified for gfz-reportgen:
#             # add catpion at the end
#             self.body.append('\n\n\\begin{table}[h!]\n'
#                              '\\capstart\n')
# 
#             for id in self.next_table_ids:
#                 self.body.append(self.hypertarget(id, anchor=False))
#             if node['ids']:
#                 self.body.append(self.hypertarget(node['ids'][0], anchor=False))
#             self.next_table_ids.clear()
#         if self.table.longtable:
#             self.body.append('\n\\begin{longtable}')
#             endmacro = '\\end{longtable}\n\n'
#         elif self.table.has_verbatim:
#             self.body.append('\n\\begin{tabular}')
#             endmacro = '\\end{tabular}\n\n'
#         elif self.table.has_problematic and not self.table.colspec:
#             # if the user has given us tabularcolumns, accept them and use
#             # tabulary nevertheless
#             self.body.append('\n\\begin{tabular}')
#             endmacro = '\\end{tabular}\n\n'
#         else:
#             self.body.append('\n\\begin{tabulary}{\\linewidth}')
#             endmacro = '\\end{tabulary}\n\n'
#         if self.table.colspec:
#             self.body.append(self.table.colspec)
#         else:
#             if self.table.has_problematic:
#                 colwidth = 0.95 / self.table.colcount
#                 colspec = ('p{%.3f\\linewidth}|' % colwidth) * \
#                     self.table.colcount
#                 self.body.append('{|' + colspec + '}\n')
#             elif self.table.longtable:
#                 self.body.append('{|' + ('l|' * self.table.colcount) + '}\n')
#             else:
#                 self.body.append('{|' + ('L|' * self.table.colcount) + '}\n')
#         if self.table.longtable and self.table.caption is not None:
#             self.body.append(u'\\caption{')
#             for caption in self.table.caption:
#                 self.body.append(caption)
#             self.body.append('}')
#             for id in self.next_table_ids:
#                 self.body.append(self.hypertarget(id, anchor=False))
#             self.next_table_ids.clear()
#             self.body.append(u'\\\\\n')
#         if self.table.longtable:
#             self.body.append('\\hline\n')
#             self.body.extend(self.tableheaders)
#             self.body.append('\\endfirsthead\n\n')
#             self.body.append('\\multicolumn{%s}{c}%%\n' % self.table.colcount)
#             self.body.append(r'{{\textsf{\tablename\ \thetable{} -- %s}}} \\'
#                              % _('continued from previous page'))
#             self.body.append('\n\\hline\n')
#             self.body.extend(self.tableheaders)
#             self.body.append('\\endhead\n\n')
#             self.body.append(r'\hline \multicolumn{%s}{|r|}{{\textsf{%s}}} \\ \hline'
#                              % (self.table.colcount,
#                                 _('Continued on next page')))
#             self.body.append('\n\\endfoot\n\n')
#             self.body.append('\\endlastfoot\n\n')
#         else:
#             self.body.append('\\hline\n')
#             self.body.extend(self.tableheaders)
#         self.body.extend(self.tablebody)
#         self.body.append(endmacro)
#         if not self.table.longtable and self.table.caption is not None:
#             # add captions NOW:
#             self.body.append('\\caption{')
#             for caption in self.table.caption:
#                 self.body.append(caption)
#             self.body.append('}')
# 
#             self.body.append('\\end{table}\n\n')
#         self.unrestrict_footnote(node)
#         self.table = None
#         self.tablebody = None
                
                
                