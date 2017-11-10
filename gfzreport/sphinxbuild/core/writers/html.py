'''
Class extending sphinx.writers.html.SmartyPantsHTMLTranslator: it just parses
the field name 'authors' (if any) removing all asterixs, whichare intended for 'corresponding
author' in latex and will not be rendered here

Created on Mar 18, 2016

@author: riccardo
'''

import sphinx.writers.html as whtml
from docutils.nodes import SkipNode
from docutils import nodes

# DISPLAY_FIELDS = ("abstract", "author", "authors")  # FIXME: move to conf.py?


class HTMLTranslator(whtml.SmartyPantsHTMLTranslator):

    def visit_field_body(self, node):
        '''just replace all asterix in authors if present'''
        if getattr(self, "_isauthor__", False):
            try:
                node.rawsource = node.rawsource.replace('*', '')
                textnode = node.children[0].children[0]
                textnode.parent.children[0] = nodes.Text(textnode.rawsource.replace('*', ''))
            except Exception:
                pass
            del self._isauthor__
        whtml.SmartyPantsHTMLTranslator.visit_field_body(self, node)

    def visit_field_name(self, node):
        '''just mark an internal attribute if we are processing authors'''
        if node.rawsource.lower().strip() in ('author', 'authors'):
            self._isauthor__ = True
        whtml.SmartyPantsHTMLTranslator.visit_field_name(self, node)
#
#     def visit_field(self, node):
#         if node.children[0].rawsource == "abstract":
#             content = node.children[1].children
#             # Build a paragraph representing the abstract content, and process it in depart_field_list:
#             if len(content) != 1 or not isinstance(content[0], nodes.paragraph):
#                 self.abstract_reminder_paragraph_node = nodes.paragraph(node.children[1].rawsource,
#                                                                         children=content)
#             else:
#                 self.abstract_reminder_paragraph_node = content[0]
#             raise SkipNode()
# 
#         whtml.SmartyPantsHTMLTranslator.visit_field(self, node)
# 
#     def depart_field_list(self, node):
#         whtml.SmartyPantsHTMLTranslator.depart_field_list(self, node)
#         if hasattr(self, 'abstract_reminder_paragraph_node'):
#             title_node = nodes.TextElement("Abstract", "Abstract")
# #             body_node = nodes.TextElement(self.abstract_reminder_text,
# #                                           self.abstract_reminder_text)
#             self.visit_centered(title_node)
#             self.visit_Text(title_node)
#             self.depart_Text(title_node)
#             self.depart_centered(title_node)
#             self.visit_paragraph(self.abstract_reminder_paragraph_node)
#             self.depart_paragraph(self.abstract_reminder_paragraph_node)
