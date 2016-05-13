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
app = None

def app_builder_inited(app_):
    global app
    app = app_

def relfn2path(filename):
    """Return paths to a file referenced from a document, relative to
    documentation root and absolute.

    In the input "filename", absolute filenames are taken as relative to the
    source dir, while relative filenames are relative to the dir of the
    containing document.
    """
    # We might use the function below, but it works the first N times
    # then fails cause app,end.docname has been set to None (??)
    # return app.env.relfn2path(filename, " ")[1]
    if os.path.isabs(filename):
        return filename
    else:
        try:
            # the path.abspath() might seem redundant, but otherwise artifacts
            # such as ".." will remain in the path
            return path.abspath(path.join(app.env.srcdir, filename))
        except UnicodeDecodeError:
            # the source directory is a bytestring with non-ASCII characters;
            # let's try to encode the rel_fn in the file system encoding
            enc_rel_fn = filename.encode(sys.getfilesystemencoding())
            return path.abspath(path.join(app.env.srcdir, enc_rel_fn))

def app_source_read(app, docname, source):
    source[0] = normalize_sec_headers(source[0])
    source[0] = replace_math_dollar(source[0])


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
    =============== ================= ===================================================================
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
    a= app.builder.env
    b = app.builder
    g = 9
#     print "\n\n\n"
#     for obj in doctree.traverse(nodes.section):
#         print "\n"
#         print str(obj.children[0]) + " " + str(len(obj.children)) + " children, parent " + str(type(obj.parent))
#         children = list(obj.children)
#         for par in children:
#             if isinstance(par, nodes.paragraph) and len(par.children) == 0:
#                 par.attributes['classes'].append("data-editable")
#         
#         print "\n"
#     print "\n\n\n"
    
#     for obj in doctree.traverse():
#         if obj.line and obj.rawsource:
#             try:
#                 obj.attributes['data-line'] = str(obj.line)
#                 obj.attributes['data-rawsource'] = str(obj.rawsource)
#             except UnicodeEncodeError as exc:
#                 p = 9

#     for obj in doctree.traverse(nodes.Text):
#         # if len(obj.children) == 0:
#         parent = obj.parent
#         if not isinstance(parent, nodes.paragraph):  # len(parent) > 1:
#             continue
#         parent.attributes['classes'].append("data-editable")

#         print "\n"
#         print str(obj.children[0]) + " " + str(len(obj.children)) + " children, parent " + str(type(obj.parent))
#         children = list(obj.children)
#         for par in children:
#             if isinstance(par, nodes.paragraph) and len(par.children) == 0:
#                 par.attributes['classes'].append("data-editable")


#     for img in doctree.traverse(nodes.image):
#         if not hasattr(img, 'gnuplot'):
#             continue
# 
#         text = img.gnuplot['text']
#         options = img.gnuplot['options']
#         try:
#             fname, outfn, hashid = render_gnuplot(app, text, options)
#             img['uri'] = fname
#         except GnuplotError, exc:
#             app.builder.warn('gnuplot error: ' + str(exc))
#             img.replace_self(nodes.literal_block(text, text))
#             continue
    pass

def setup(app):
    app.set_translator('latex', LatexTranslator)
    app.connect('source-read', app_source_read)
    app.connect('doctree-read', app_doctree_read)
    app.connect('builder-inited', app_builder_inited)

#     app.add_node(nodes.field,
#                  # html=(visit_field_html, depart_field_html),
#                  latex=(visit_field_latex, depart_field_latex))
    # app.connect('doctree-read', render_abstract_node)
    # app.add_config_value('gnuplot_format', DEFAULT_FORMATS, 'html')