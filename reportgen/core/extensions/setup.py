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

# from docutils.transforms import references
# from docutils.utils import Reporter

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
    documentation root and absolute. This code is copied and modified from sphinx app environment
    to work for custom extension like this:
    In the rst, absolute filenames such as "/a/bcd" are taken as relative to the computer root
    (note: in rst image directive, they are relative to the source dir), while relative filenames
    are relative to the dir of the containing document (as in the image directive).
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
    return re.sub("\\$(.*?)\\$", ":math:`\\1`", source)  # flags=re.MULTILINE)


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
        This method resolves replacement due to bib fields
    """
    # a = app.builder.env

    bibfields = {}
    first_field_list_children_found = None
    doi_fields = []

    for obj in doctree.traverse(nodes.field_list):

        if first_field_list_children_found is None:
            first_field_list_children_found = obj.children

        for field in obj.children:
            try:
                par_element = field.children[1].children[0]
                field_name = field.children[0].rawsource
                bibfields[field_name] = par_element.children

                if len(par_element.children) == 1 and field_name == "doi":
                    field_value = par_element.children[0]
                    # If DOI, add two new fields doiStr and doiURL. The first is the DOI as string
                    # with two substring separated by "/", the latter is the full url
                    doi_str, doi_url = parse_doi(field_value)
                    doi_fields = [create_field_node("doiStr", doi_str),
                                  create_field_node("doiUrl", doi_url)]
            except IndexError:
                pass

    # append the two newly created fields (seems we cannot insert while looping):
    if first_field_list_children_found:
        first_field_list_children_found.extend(doi_fields)

    # try to fix problematic, and see iof they are references to bib fields
    _warn_ = True
    for obj in doctree.traverse(nodes.problematic):
        # Note: the doctree has a internal Logger like object (doctree.reporter) in which
        # you can print messages like doctree.reporter.error("..."), doctree.reporter.warning("...")
        # Apparently, the reporter prints all its messages (those with a severity at least warning
        # and error, but this might be dependent on the settings somewhere) AT THE END.
        # Thus, by writing to stdout and stderr directly, we are sure to write these messages BEFORE
        # they are printed out by sphinx
        if _warn_:
            sys.stdout.write("Trying to fix 'Undefined substitution referenced' errors\n")
            _warn_ = False

        rawsource = obj.rawsource
        if rawsource and rawsource[0] == rawsource[-1] == "|" and rawsource[1:-1] in bibfields:
            index = obj.parent.children.index(obj)
            repl_nodes = bibfields[rawsource[1:-1]]
            obj.parent.children.pop(index)
            for i, node in enumerate(repl_nodes, index):
                obj.parent.children.insert(i, node)

            sys.stderr.write(('Please ignore error message \'Undefined '
                              'substitution referenced: "%s"\': THE PROBLEM HAS BEEN FIXED\n')
                             % rawsource[1:-1])


def parse_doi(doi_str):
    """
        parses doi_str returning the tuple doi, doi_url.
    """
    r = re.compile("^(?:\\s*DOI\\s*:)*\\s*(https?://(?:.*/)*)?([^/]+/[^/]+)\\s*$", re.IGNORECASE)
    m = r.match(doi_str)
    if m is None:
        return (None, None)
    grp = m.groups()
    doi_str, doi_url = grp[1], None if (grp[0] is None or grp[1] is None) else grp[0] + grp[1]
    if not doi_url and doi_str:
        doi_url = "http://doi.org/" + doi_str
    return doi_str, doi_url


def create_field_node(field_name, field_value):
    fn_textnode = nodes.Text(field_name)  # nodes.field_name()
    fb_textnode = nodes.Text(field_value)
    # docutils (inspected by debugging) uses a paragraph wrapper for field bodies
    fb_parnode = nodes.paragraph('', fb_textnode)

    fn_fieldname_node = nodes.field_name('', fn_textnode)
    fn_fieldbody_node = nodes.field_body('', fb_parnode)

    return nodes.field('', fn_fieldname_node, fn_fieldbody_node)


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