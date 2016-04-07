'''
Simple sphinx extension which sets up all necessary extensions
Created on Apr 4, 2016

@author: riccardo
'''
import re
from core.writers.latex import LatexTranslator


def source_read_handler(app, docname, source):
    source[0] = normalize_sec_headers(source[0])


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


def setup(app):
    app.set_translator('latex', LatexTranslator)
    app.connect('source-read', source_read_handler)


#     app.add_node(nodes.field,
#                  # html=(visit_field_html, depart_field_html),
#                  latex=(visit_field_latex, depart_field_latex))
    # app.connect('doctree-read', render_abstract_node)
    # app.add_config_value('gnuplot_format', DEFAULT_FORMATS, 'html')