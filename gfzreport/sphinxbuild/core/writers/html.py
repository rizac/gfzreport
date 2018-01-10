'''
Class extending sphinx.writers.html.SmartyPantsHTMLTranslator: it just parses
the field name 'authors' (if any) removing all asterixs, whichare intended for 'corresponding
author' in latex and will not be rendered here

Created on Mar 18, 2016

@author: riccardo
'''
import os
from sphinx.writers.html import SmartyPantsHTMLTranslator
from docutils.nodes import SkipNode
from docutils import nodes

from gfzreport.sphinxbuild.core.writers import DOI_BASE_URL, touni

class HTMLTranslator(SmartyPantsHTMLTranslator):
    '''This class does basically two things: inserts the doi provided as field before the title
    (if present) as first field AFTER the title, and removes the asterix (if present) from
    the author(s) field body.
    As always with Sphinx, all procedures are quite hacky.
    '''

    def __init__(self, *args, **kwds):
        SmartyPantsHTMLTranslator.__init__(self, *args, **kwds)  # old style class...
        # set custom attributes:
        self._visiting_author_field__ = False
        self._doi_inserted__ = False
        
    def visit_field_body(self, node):
        '''just replace all asterix in authors if present'''
        if self._visiting_author_field__:
            try:
                node.rawsource = node.rawsource.replace('*', '')
                textnode = node.children[0].children[0]
                textnode.parent.children[0] = nodes.Text(textnode.rawsource.replace('*', ''))
            except Exception:
                pass
        SmartyPantsHTMLTranslator.visit_field_body(self, node)

    def visit_field_name(self, node):
        '''just mark an internal attribute if we are processing authors'''
        self._visiting_author_field__ = node.rawsource.lower().strip() in ('author', 'authors')
        SmartyPantsHTMLTranslator.visit_field_name(self, node)
        
    def visit_field_list(self, node):
        '''Insert DOI as first field, if provided. Note that we copy the raw html generated:
        Creating "fake" nodes might be more elegant but is IMPOSSIBLE due to the complex
        structure of sphinx. Therefore, remember that the inserted raw html text might
        need to be changed in future releases, if upgrading Sphinx'''
        if not self._doi_inserted__:
            self._doi_inserted__ = True
            doi = self.builder.app.env.metadata[self.builder.app.config.master_doc].get('doi', '')
            if doi:
                doiurl = os.path.join(DOI_BASE_URL, doi)
                rawhtml = touni('<table class="docutils field-list" frame="void" rules="none">'
                                '<colgroup><col class="field-name">'
                                '<col class="field-body">'
                                '</colgroup><tbody valign="top">'
                                '<tr class="field-odd field"><th class="field-name">DOI:</th>'
                                '<td class="field-body">'
                                '<a target="_blank" class="reference external" href="{0}">{0}</a>'
                                '</td></tr></tbody>'
                                '</table>').format(touni(doiurl))
                self.body.append(touni(rawhtml))
        return SmartyPantsHTMLTranslator.visit_field_list(self, node)

# Leave this old stuff here in case we want to play around with nodes (hint: waste of time)

#     @staticmethod
#     def copy_field(node, newname=None, newvalue=None):
#         '''copies the given field node, providing optional new name and new value
#         newvalue can also be an url, and will be rendered as anchor tag
#         '''
#         # copied and modified from docutils.nodes.Element.deepcopy and docutils.nodes.Element.copy:
#         copy = node.deepcopy()
#         # this does a deepcopy
#         if newname is not None:
#             textnode = copy.children[0].children[0]
#             # copied from docutils.nodes.Text.copy
#             copy.children[0].children[0] = textnode.__class__(touni(newname), rawsource=newname)
#         if newvalue is not None:
#             textnode = copy.children[1].children[0].children[0]
#             if newvalue.startswith("http://") or newvalue.startswith("https://"):
#                 # ok here it's tricky. First, we MUST provide refuri attribute to create 
#                 # an external reference node:
#                 newnode = nodes.reference(rawsource=touni(newvalue), refuri=touni(newvalue))
#                 # but THEN (see superclass) we need to have a TextNode as parent
#                 copy.children[1].children[0] = nodes.TextElement('', newnode)
#             else:
#                 newnode = textnode.__class__(touni(newvalue), rawsource=newvalue)
#                 # copied from docutils.nodes.Text.copy
#                 copy.children[1].children[0].children[0] = newnode
#                 
#         return copy        
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
