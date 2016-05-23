'''
Simple sphinx extension which sets up all necessary extensions
Created on Apr 4, 2016

@author: riccardo
'''
import re
import sys
import os
from os import path
from reportgen.core.writers.latex import LatexTranslator
from docutils import nodes

# the sphinx environment, saved here for access from other extensions
# FIXME!!! if in sphinx config you add:
# sys.path.insert(0, os.path.abspath("../../reportgen/core"))
# and then extensions = ['extensions.setup', ...]
# GLOBAL VARIABLES BELOW ARE NOT SET! One should inspect if it is a problem with sys.path.insert
# or due to the fact that the package reportgen is already installed
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
    """Return paths to a file referenced from a document, relative to
    documentation root and absolute.

    In the input "filename", absolute filenames are taken as relative to the
    source dir, while relative filenames are relative to the dir of the
    containing document.
    """
    # We might use the function below, but it works the first N times
    # then fails cause app,end.docname has been set to None (??)
    # return sphinxapp.env.relfn2path(filename, " ")[1]
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
    # now we need to replace references to bib-fields. we do it here cause from here to the next
    # listener (doctree-resolved) a warning is printed and we want to avoid it
    # the drawback is that we might be less robust (we need to use regexp)
    source[0] = resolve_bibfield_refs_with_tmp_hack(source[0])


def replace_math_dollar(source):
    return re.sub("\\$(.*?)\\$", ":math:`\\1`", source)  # flags=re.MULTILINE)


def resolve_bibfield_refs_with_tmp_hack(source):
    reg = re.compile("^:(\\w+):.*?$", flags=re.MULTILINE)
    bibnames = []
    for match in reg.finditer(source):  # note: we need to use search, not match! see
        # https://docs.python.org/2/library/re.html#search-vs-match
        bibnames.append(match.group(1))

    for bib in bibnames:
        source = re.sub("\\|" + bib + "\\|",
                        # makes it a literal node with bibfieldreplkwd to be recognized later
                        "``" + bibfieldreplkwd + bib + bibfieldreplkwd + "``",
                        source,
                        flags=re.MULTILINE)
    return source


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
        This method is here only as a reminder of how to add listeners to events
        It is empty
        For info, see 
    """
    # a = app.builder.env

    bibfields = {}

    for obj in doctree.traverse(nodes.field_list):
        for field in obj.children:
            try:
                par_element = field.children[1].children[0]
                if len(par_element.children) == 1 and isinstance(par_element.children[0],
                                                                 nodes.Text):
                    bibfields[field.children[0].rawsource] = par_element.children[0]
            except IndexError:
                pass

    for obj in doctree.traverse(nodes.literal):
        if len(obj.children) == 1 and isinstance(obj.children[0], nodes.Text):
            txt = obj.children[0]
            #  bibfieldreplkwd is global
            mtc = re.match("^" + bibfieldreplkwd + "(\\w+)" + bibfieldreplkwd + "$", str(txt))
            if mtc:
                bibname = mtc.group(1)
                if bibname in bibfields:
                    # attributes must be empty, otherwise docutils complains that a
                    # text node cannot replace a node with attributes
                    # if this is a bibfield replacement, it should be the case
                    no_bib_ref = False
                    for att in obj.attributes:
                        if obj.attributes[att]:
                            no_bib_ref = True
                            break
                    if no_bib_ref is False:
                        obj.replace_self(bibfields[bibname])


def missing_reference(app, env, node, contnode):
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
    pass


def setup(app):
    app.set_translator('latex', LatexTranslator)
    app.connect('source-read', app_source_read)
    app.connect('doctree-read', app_doctree_read)
    app.connect('builder-inited', app_builder_inited)
    app.connect("missing-reference", missing_reference)
    app.connect("doctree-resolved", doctree_resolved)
