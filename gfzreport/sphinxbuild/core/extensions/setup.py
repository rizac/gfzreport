'''
Simple sphinx extension which sets up the necessary translators (html, latex) and other stuff
It is also a collection of trial and errors mostly commented and left here as a reminder in order
Created on Apr 4, 2016

@author: riccardo
'''
import re
import sys
import os
from os import path
from gfzreport.sphinxbuild.core.writers.latex import LatexTranslator
from gfzreport.sphinxbuild.core.writers.html import HTMLTranslator
from docutils import nodes
# from docutils import nodes


# the sphinx environment, saved here for access from other extensions
# FIXME!!! if in sphinx config you add:
# sys.path.insert(0, os.path.abspath("../../reportbuild/core"))
# and then extensions = ['extensions.setup', ...]
# GLOBAL VARIABLES BELOW ARE NOT SET! One should inspect if it is a problem with sys.path.insert
# or due to the fact that the package reportbuild is already installed
# However, the problem has been fixed by removing sys.path.insert and by sepcifying the full path
# in extensions dict (see conf.py)
sphinxapp = None


def app_builder_inited(app_):
    global sphinxapp
    sphinxapp = app_


# this keyword is used to replace any | in e.g., |bibname| so that we do not issue a reference
# warning. Later, we will replace any literal bibfieldreplkwd + bibname + bibfieldreplkwd
# PLEASE SUPPORT ONLY CHARS THAT DO NOT NEED TO BE REGEX ESCAPED!!
bibfieldreplkwd = "___bfrt___"


def relfn2path(filename):
    """Returns a relative path normalized and relative to the app srcdir, unless
    the path is already absolute (in the sense of os.path.isabspath) in that case returns
    the argument as it is.
    Sphinx is quite confusing about paths, first
    in the definition of "relative" vs "absolute" paths, second in the consistency
    (I suspect that images paths do not follow the same rules than other directives path)
    All in all, that NEEDS A FIXME and a CHECK.
    This method is imported and used by our custom directives of this package
    """
    # We might use the function below, but it works the first N times
    # then fails cause app.env.docname has been set to None (??)
    # return sphinxapp.env.relfn2path(filename, " ")[1]
    # As we have no control over it. From the sphinx doc:
    # we do another approach: if absolute, it's absolute. If relative, is relative to the source
    # dir. Stop

    if os.path.isabs(filename):
        return filename
    else:
        try:
            # the path.abspath() might seem redundant, but otherwise artifacts
            # such as ".." will remain in the path
            return path.abspath(path.join(sphinxapp.env.srcdir, filename))
        except UnicodeDecodeError:
            # the source directory is a bytestring with non-ASCII characters;
            # let's try to encode the rel_fn in the file system encoding
            enc_rel_fn = filename.encode(sys.getfilesystemencoding())
            return path.abspath(path.join(sphinxapp.env.srcdir, enc_rel_fn))


def app_source_read(app, docname, source):
    source[0] = normalize_sec_headers(source[0])
    source[0] = replace_math_dollar(source[0])
    # Note that we cannot handle the warning (printed to stdout) of referenced bib. fields (if any)
    # but we will try to fix it in the next listener called (app_doctree_read)
    # We might also try to fix those errors now, and we actually did it in a previous version, BUT
    # it's a less robust method (we should use regexp which behave like rst-parsers) and involves
    # much more code for not a big advantage. Simply warn "trying to fix... " with a meaningful
    # message the user


def replace_math_dollar(source):
    return re.sub("(?<!\\\\)\\$(.*?)(?<!\\\\)\\$", " :math:`\\1` ", source)  # flags=re.MULTILINE)


def normalize_sec_headers(string, list_of_under_and_overlines=[("#", "#"),
                                                               ("*", "*"),
                                                               "=",
                                                               "-",
                                                               "^",
                                                               "\""]):
    """Normalizes section titles by replacing all github markdown section title symbols (#) with the
    corresponding rst one. Note that contrarily to the github markdown style, rst understands the
    nesting level of sections by means of clustering the same symbols. If not otherwise specified
    in list_of_under_and_overlines, the correspondence is:

    Markdown symbol rst symbol        coventionally assigned for
    =============== ================= ============================================================
    #               # (with overline) parts
    ##              * (with overline) chapters
    ###             =                 sections
    ####            -                 subsections
    #####           ^                 subsubsections
    ######          "                 paragraphs

    * Note: that's a convention, it does not correspond to the latex keyword

    For info see
    - http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#sections
    - http://www.sphinx-doc.org/en/stable/rest.html#sections
    :param: string the string to be searched and substituted
    :param: list_of_under_and_overlines a list of 6 elements specifying the rst decorators. If
    missing defaults to the list representing the table above. Otherwise each element is either a
    character string, denoting the underline symbol, or a list/tuple ot 2 character strings,
    denoting under- and overline symbols, respectuvely. Note that for each element ("^", None)
    equals "^"
    """
    reg = re.compile("^(#+)\\s(.*?)$", re.MULTILINE)
    for matchobj in list(reg.finditer(string))[::-1]:
        grp = matchobj.groups()
        if len(grp) == 2:  # groups count starts from group 0
            indx = len(grp[0])
            decorator = list_of_under_and_overlines[min(6, indx) - 1]
            str_to_decorate = grp[1]
            rst_str = decorate_title(str_to_decorate,
                                     *(list(decorator) if hasattr(decorator, "__iter__")
                                       else [decorator]))
            string = string[:matchobj.start()] + rst_str + string[matchobj.end():]

    return string


def decorate_title(string, underline_symbol, overline_symbol=None):
    """
        Decorates a string title as in rst format
        :param string: the string represetning the title
        :param underline_symbol: A 1-character string, representing the decorator character for
            underline
        :param overlline_symbol: A 1-character string, representing the decorator character for
            overline

        :Examples:
        decorate_string("sea", "=") returns:

        sea
        ===

        decorate_string("abc", "=", "-") returns:

        ---
        sea
        ===
    """
    lens = len(string)
    string = "{0}\n{1}".format(string, lens * underline_symbol)
    if overline_symbol:
        string = "{0}\n{1}".format(lens * overline_symbol, string)
    return string


def app_doctree_read(app, doctree):
    """
        This method resolved replacement due to bib fields.
        This feature is dropped as it is highly unmantainable and not
        yet required. Leave the method here for future doctree modifications.
        Remember that you can use:
        for obj in doctree.traverse(nodes.problematic):
            .. your code here
    """
    for _ in doctree.traverse(nodes.problematic):
        __ = 9
        
    for _ in doctree.traverse(nodes.Element):
        __ = 9


def missing_reference(app, env, node, contnode):
    """This method does nothing as it was a test to see if it handled missing text substitution
    references, but it doesn't
    Will be removed in the future
    """
    pass
    # Emitted when a cross-reference to a Python module or object cannot be resolved. If the event
    # handler can resolve the reference, it should return a new docutils node to be inserted in the
    # document tree in place of the node node. Usually this node is a reference node containing
    # contnode
    # as a child.

    # Parameters:
    # env - The build environment (app.builder.env).
    # node - The pending_xref node to be resolved. Its attributes reftype, reftarget, modname and
    # classname attributes determine the type and target of the reference.
    # contnode - The node that carries the text and formatting inside the future reference and
    # should be a child of the returned reference node.


def doctree_resolved(app, doctree, docname):
    """Not used, will be removed in the future"""
    pass


def setup(app):
    app.set_translator('html', HTMLTranslator)
    app.set_translator('latex', LatexTranslator)
    app.connect('source-read', app_source_read)
    app.connect('doctree-read', app_doctree_read)
    app.connect('builder-inited', app_builder_inited)
    app.connect("missing-reference", missing_reference)
    app.connect("doctree-resolved", doctree_resolved)


# REMINDER: all Element nodes (docutils.nodes) have constructors like this:
# def __init__(self, rawsource='', *children, **attributes):
#         self.rawsource = rawsource
#         """The raw text from which this element was constructed."""
#
#         self.children = []
#         """List of child nodes (elements and/or `Text`)."""
#
#         self.extend(children)           # maintain parent info
#
#         self.attributes = {}
#         """Dictionary of attribute {name: value}."""
#         ...