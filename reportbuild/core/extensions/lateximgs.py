'''
Overrides images and figures directives and nodes to account for the "latex-includegraphics-opts"
option
Created on Jun 13, 2016

@author: riccardo
'''
from docutils.nodes import image as img_node
from docutils.parsers.rst.directives.images import Image  # , Figure
# figure seems to be overridden by sphinx, import sphinx direcrtive
from sphinx.directives.patches import Figure
# EXPERIMENTAL: REPLACE IMAGE AND FIGURE NODES WITH
import re


LATEX_OPT_NAME = "latex-includegraphics-opts"
LATEX_OPT_SPEC = {LATEX_OPT_NAME: lambda arg: arg}

# the new image node
class imgnode2(img_node):
    pass


class LatexImageDirective(Image):
    option_spec = Figure.option_spec.copy()  # @UndefinedVariable
    option_spec.update(LATEX_OPT_SPEC)

    def run(self):
        nodes = Image.run(self)
        for subnode in nodes:
            if isinstance(subnode, img_node):
                subnode.replace_self(imgnode2(self.block_text, **subnode.attributes))
        return nodes


class LatexFigureDirective(Figure):
    option_spec = Figure.option_spec.copy()  # @UndefinedVariable
    option_spec.update(LATEX_OPT_SPEC)

    def run(self):
        nodes = Figure.run(self)
        for subnode in nodes[0].children:
            if isinstance(subnode, img_node):
                subnode.replace_self(imgnode2(self.block_text, **subnode.attributes))
        return nodes


def visit_lateximg_node_latex(self, node):
    if node.attributes.get(LATEX_OPT_NAME, None):
        # set variable to know what we are about to append:
        self.__current_image_start = len(self.body)
    self.visit_image(node)


def depart_lateximg_node_latex(self, node):
    self.depart_image(node)
    latex_opts = node.attributes.get(LATEX_OPT_NAME, None)
    if not latex_opts:
        return
    # here the "hack: if the latex includegraphics options are specified,
    # remove the options set with our custom one. Use regexp for that
    # Note that from sphinx 1.5 the command sphinxincludegraphics is used
    reg = re.compile("^\\s*\\\\(?:sphinx)?includegraphics(\\[.*\\]|)\\{.*\\}\\s*$")
    start = self.__current_image_start
    for idx in xrange(start, len(self.body)):
        m = reg.match(self.body[idx])
        if m:
            repl_str = "%s%s%s" % (self.body[idx][:m.start(1)],
                                   ("[%s]" % latex_opts),
                                   self.body[idx][m.end(1):])
            self.body[idx] = repl_str
            return


def visit_lateximg_node_html(self, node):
    self.visit_image(node)


def depart_lateximg_node_html(self, node):
    self.depart_image(node)


def setup(app):
    app.add_directive("image", LatexImageDirective)
    app.add_directive("figure", LatexFigureDirective)
    app.add_node(imgnode2,
                 latex=(visit_lateximg_node_latex, depart_lateximg_node_latex),
                 html=(visit_lateximg_node_html, depart_lateximg_node_html))
