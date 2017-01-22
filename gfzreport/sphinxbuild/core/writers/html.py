'''
Class extending sphinx.writers.html.SmartyPantsHTMLTranslator
It overrides images as pdf using iframes instead of img tags
Created on Mar 18, 2016

@author: riccardo
'''

import sphinx.writers.html as whtml
import re
from docutils.nodes import SkipNode
from docutils import nodes


try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup


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
            # see:
            # http://stackoverflow.com/questions/2104608/hiding-the-toolbars-surrounding-an-embedded-pdf
            newtag = edittag(self.body[-1],
                             "<iframe>",
                             src=lambda val: val+"#view=fit&toolbar=0&navpanes=0&scrollbar=0",
                             alt=None)

            self.body[-1] = newtag

#             new_str = replace(self.body[-1], '')
#             # replace img tag just added via a regexp:
#             matchobj = HTMLTranslator.imgre.match(self.body[-1])
#             if matchobj and len(matchobj.groups()) == 1:
#                 self.body[-1] = ("<iframe {0}>"
#                                  "</iframe>").format(matchobj.group(1).strip())
#                 return
#
#             raise ValueError("%s not matching, expected <img>" % self.body[-1])

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

    def visit_field(self, node):
        if node.children[0].rawsource == "abstract":
            self.abstract_reminder_text = node.children[1].rawsource
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


def get(html_tag_str):
    """
        Returns a html object obtained by parsing the argument
        :param html_str_tag: a string tag denoting an html element, e.g. "<img src='a' />"
        :return an bs4.element.Tag object (bs stands for beautifulsoap. For info see FIXME: add ref)
    """
    parsed_html = BeautifulSoup(html_tag_str, "lxml")
    children = list(parsed_html.body.children)
    if len(children) != 1:
        raise ValueError("expected an html tag denoting"
                         " a single element, {0} found".format(str(len(children))))
    return children[0]


def edittag(html_tag_str, __new_tag=None, **attributes):
    """
        Edits an html tag given in string form by changing its name and its attributes
        :param html_tag_str: the input (as string) to be modified.
            E.g. "<img src='/path/to/image.gif' />
        :param __new_tag: a string for converting the inpiut string to a new tag. E.g. "<iframe>"
            Note that the method is aware of tags closure so:
            edittag("<img src='a' />", "<iframe>") returns "<iframe src='a'></iframe>"
        :param attributes: a dict set of keys (attributes names) and relative values to change
            html_tag_str attributes. The values can be:
            - None: do not consider that attribute (remove it)
            - a function(att_name_str, att_value_str) returning the new attribute value (None means:
                remove the attribute, see above)
            - anything else: str(value) will be set as new attribute value (note: boolean will be
            lower-cased)
        :return: the new html_tag_str edited
        :rtype: string
        :Examples:
            edittag("<img src='a' alt='b'/>") returns itself:
                "<img src='a' alt='b'/>"
            edittag("<img src='a' alt='b'/>", alt=None) returns:
                "<img src='a'/>"
            edittag("<img src='a' alt='b'/>", alt=lambda a,v: a+v) returns:
                "<img src='a' alt='altb'/>"
            edittag("<img src='a' alt='b'/>", "<iframe>") returns:
                "<iframe src='a' alt='b'></iframe>"
    """
    if __new_tag is None and not attributes:
        return html_tag_str

    tag = get(html_tag_str)
    attrs = tag.attrs
    new_attrs = {}
    for att, val in attrs.iteritems():
        func = attributes[att] if att in attributes else val
        val = func(tag.attrs[att]) if hasattr(func, "__call__") else func
        if val is not None:
            new_attrs[att] = str(val).lower() if val in (True, False) else str(val)

    if __new_tag is not None:
        tag = get(__new_tag)

    tag.attrs = new_attrs
    return tag.prettify(formatter=None)  # avoid escaping characters. See
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#output-formatters

