'''
Extension to specify a latex includegraphics options for the *next* figure or image
in the document. In the former case, the option will be applied to all images in the figure
Example: place before the figure/image you want to customize:

\.\. includegraphics\:\:  trim=8 30 76 0,width=0.33\textwidth,clip

Created on Jan 30, 2017

@author: riccardo
'''
import re
from docutils import nodes
from docutils.parsers.rst import Directive


class includegraphics_node(nodes.Element):
    pass


class IncludeGraphicsDirective(Directive):

    # setup things in order to make the argument passed to the 'content' attribute:
    required_arguments = 0
    has_content = True

    # this are copied as default (we should check what does the second means sometime...):
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        # So, it seems that if I specify required_arguments to 0 then the argument is passed
        # to the content
        return [includegraphics_node(latex_options=",".join(f for f in self.content))]


def visit_ig_node_html(self, node):
    pass


def depart_ig_node_html(self, node):
    pass


def visit_ig_node_latex(self, node):
    """Visits this node in latex.
    Note that this node has already been put AFTER the next table in the document
    (doctree_read)"""
    # hline_indices is in principle a list of integers, each integer I denoting
    # the index of self.body there the I-th "\hline" is (so that we might remove the \hline,
    # or keep it). *BUT*: in longtable's, the first and last hlines might be set
    # for all pages, all pages except the first, all pages except the last. Thus, we might have
    # two indices denoting the first hline, or the last. that's why hline_indices is a list
    # of iterables, each iterable returning the indices in self.body of the I-th hline
    latex_opts = node['latex_options']
    reg_fig = re.compile(r"^\s*\\begin\{figure\}\s*.*$", re.DOTALL), \
        re.compile(r"^.*\\end\{figure\}\s*$", re.DOTALL)
    reg_img = re.compile(r"^\s*\\(?:sphinx)?includegraphics(\[.*\]|)\{.*\}\s*$", re.DOTALL)
    infig = False
    for i in xrange(len(self.body)-1, 0, -1):
        bodyline = self.body[i]
        if not infig:
            m = reg_fig[1].match(bodyline)
            if m:
                infig = True
        else:
            m = reg_fig[0].match(bodyline)
            if m:
                break
            m = reg_img.match(bodyline)
            if m:
                repl_str = "%s%s%s" % (bodyline[:m.start(1)],
                                       ("[%s]" % latex_opts),
                                       bodyline[m.end(1):])
                self.body[i] = repl_str
                if not infig:
                    break


def depart_ig_node_latex(self, node):
    pass


def doctree_read(app, doctree):
    """
        This method moves all includegraphics AFTER the referenced images/figures, so that we can
        use the visit methods above.
    """
    # a = app.builder.env
    if app.buildername != 'latex':
        return

    def condition(node):
        return isinstance(node, nodes.image) or isinstance(node, nodes.figure) or \
            isinstance(node, includegraphics_node)

    pending_includegraphics_node = None
    for obj in doctree.traverse(condition):
        if isinstance(obj, includegraphics_node):
            obj.parent.children.remove(obj)
            pending_includegraphics_node = obj
        elif pending_includegraphics_node is not None:
            obj.parent.children.insert(obj.parent.children.index(obj) + 1,
                                       pending_includegraphics_node)
            pending_includegraphics_node = None


def setup(app):
    app.add_node(includegraphics_node,
                 html=(visit_ig_node_html, depart_ig_node_html),
                 latex=(visit_ig_node_latex, depart_ig_node_latex))
    app.add_directive('includegraphics', IncludeGraphicsDirective)
    app.connect('doctree-read', doctree_read)
