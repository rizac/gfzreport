'''
Class extending sphinx.writers.html.SmartyPantsHTMLTranslator
 - It overrides images as pdf using iframes instead of img tags (NOT TESTED)
 - Sets which fields should be visible in the html (by default, author/authors only)
 - Makes the abstract field a centered div at the beginning of the document (if an abstract is set)
Created on Mar 18, 2016

@author: riccardo
'''

import sphinx.writers.html as whtml
from docutils.nodes import SkipNode
from docutils import nodes


# let alone the abstract, here a list of allowed fields for the html. Default: show authors only
_ALLOWED_FIELDS = set(['author', 'authors'])


class HTMLTranslator(whtml.SmartyPantsHTMLTranslator):

    def visit_field(self, node):
        if node.children[0].rawsource == "abstract":
            self.abstract_reminder_text = node.children[1].rawsource
            raise SkipNode()
        elif node.children[0].rawsource not in _ALLOWED_FIELDS:
            raise SkipNode()

        whtml.SmartyPantsHTMLTranslator.visit_field(self, node)

    def depart_field_list(self, node):
        whtml.SmartyPantsHTMLTranslator.depart_field_list(self, node)
        if hasattr(self, 'abstract_reminder_text'):
            title_node = nodes.TextElement("abstract", "abstract")
            body_node = nodes.TextElement(self.abstract_reminder_text,
                                          self.abstract_reminder_text)
            self.visit_centered(title_node)
            self.visit_Text(title_node)
            self.depart_Text(title_node)
            self.depart_centered(title_node)
            self.body.append(self.starttag(node, 'p', ''))
            self.visit_Text(body_node)
            self.depart_Text(body_node)
            self.body.append('</p>')
