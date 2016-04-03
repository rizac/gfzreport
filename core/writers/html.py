'''
Class extending sphinx.writers.html.SmartyPantsHTMLTranslator
It overrides images as pdf using iframes instead of img tags
Created on Mar 18, 2016

@author: riccardo
'''

import sphinx.writers.html as whtml
import re


class HTMLTranslator(whtml.SmartyPantsHTMLTranslator):

    imgre = re.compile(r"\s*<\s*img\s+(.*)\s*/\s*>", re.IGNORECASE)

    @staticmethod
    def is_pdf_node(node):
        """
            Returns True if the node is a node referencing a pdf document
            This includes e.g. img and anchor tags
        """
        uri_key = 'uri'
        if uri_key not in node.attributes:
            uri_key = 'refuri'  # anchors have refuri as key
            if uri_key not in node.attributes:
                return False
        return node.attributes.get(uri_key, '').lower()[-4:] == ".pdf"

    def visit_reference(self, node):
        """
            Calls the super method and removes the appended nodes in case of pdf anchor
            Note: Calling the super method seems to be mandatory
        """
        self.do_and_replace(node, whtml.SmartyPantsHTMLTranslator.visit_reference)

    def depart_reference(self, node):
        self.do_and_replace(node, whtml.SmartyPantsHTMLTranslator.depart_reference)

    def visit_image(self, node):
        whtml.SmartyPantsHTMLTranslator.visit_image(self, node)
        if self.is_pdf_node(node):
            # replace img tag just added via a regexp:
            matchobj = HTMLTranslator.imgre.match(self.body[-1])
            if matchobj and len(matchobj.groups()) == 1:
                self.body[-1] = "<iframe " + matchobj.group(1).strip() + "></iframe>"
                return

            raise ValueError("%s not matching, expected <img>" % self.body[-1])

    def depart_image(self, node):
        self.do_and_replace(node, whtml.SmartyPantsHTMLTranslator.depart_image)

    def do_and_replace(self, node, method):
        """Executes the given method and replaces nodes appended in case node is a pdf node"""
        oldlen = len(self.body)
        method(self, node)
        if self.is_pdf_node(node):
            self.body = self.body[:oldlen]

#     def __init__(self, *args, **kwds):
#         # call super method:
#         whtml.SmartyPantsHTMLTranslator.__init__(self, *args, **kwds)
