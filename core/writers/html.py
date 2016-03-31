'''
Created on Mar 18, 2016

@author: riccardo
'''

import sphinx.writers.html as whtml
import re


class HTMLTranslator(whtml.SmartyPantsHTMLTranslator):

    # regexp tags. Actually FIXME: modify them for images only!!!
    regpdf = re.compile(r"\s*<\s*(a|img)\s+(.*)\s*(/\s*|>\s*<\s*/\1\s*)>",
                        re.IGNORECASE)
    regtag = re.compile(r"(?<!\w)(?:alt|href)\s*=\s*(['" + r'"' + r"])(.*?)\1(?!\w)",
                        re.IGNORECASE)

    def visit_image(self, node):

        whtml.SmartyPantsHTMLTranslator.visit_image(self, node)
        if node.attributes.get('uri', '').lower()[-4:] != ".pdf":
            return

        # NOTE: super class PUTS images inside anchors. Therefore, we need to modify image tag
        # if pdf, BUT ALSO remove anchors before and later.
        # use a flag to set it in depart_reference later
        self._pdf_image_in_progress = True

        string = HTMLTranslator.regpdf.sub(r"\2", self.body[-1])
        if string != self.body[-1]:
            mobj = self.regtag.match(string)
            if mobj:
                string = string[:mobj.start()] + string[mobj.end():]

        self.body[-1] = "<iframe " + string + "></iframe>"
        # return ret

    def depart_reference(self, node):
        # FIXME: is this executed in the same thread as visit_image?
        # are we sure that setting an attribute works? probably yes
        if not hasattr(self, '_pdf_image_in_progress') or not self._pdf_image_in_progress:
            whtml.SmartyPantsHTMLTranslator.depart_reference(self, node)
            return

        self._pdf_image_in_progress = False

        # sphinx might append empty nodes:
        while len(self.body) and not self.body[-1]:
            self.body.pop(-1)
        # empty self.body. Should not be the case. However, call super method
        # and return
        if not len(self.body):
            whtml.SmartyPantsHTMLTranslator.depart_reference(self, node)
            return

        img_tag = self.body.pop(-1)

        # again, jumpt to the first nonemtp node:
        while len(self.body) and not self.body[-1]:
            self.body.pop(-1)

        self.body[-1] = img_tag


if __name__ == "__main__":
    h = HTMLTranslator.regpdf.match("<a href='er'>< / a>")
    assert h
    h = HTMLTranslator.regpdf.match("<img src='er'/>")
    assert h