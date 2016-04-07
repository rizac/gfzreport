'''
Simple sphinx extension which sets up all necessary extensions
Created on Apr 4, 2016

@author: riccardo
'''
import re
from core.writers.latex import LatexTranslator


def source_read_handler(app, docname, source):
    normalize_sec_headers(source)


def normalize_sec_headers(string, list_of_under_and_overlines=[("#", "#"),
                                                               ("*", "*"),
                                                               (None,  "="),
                                                               (None, "-"),
                                                               (None, "^"),
                                                               (None, "\"")]):
    """Normalizes section titles of the string representing an rst document by adding rst
    decorations to them. Returns the normalized string.
    Long explanation (http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#sections):
    rst understands the nesting level of sections by means of clustering the same
    symbols, thus:

    title
    =====

    chapter
    -------

    another chapter
    ---------------

    But this is complex to organize when we provide a template file to be filled with the values of
    a config file (where we might in turn change title, chapter etcetera). Thus we make use in the
    template of the github markdown syntax with #:
    # title
    ## section
    ### subsection
    And we convert it here according to the following convention
    (as in http://www.sphinx-doc.org/en/stable/rest.html#sections)
    = with overline, for titles
    - with overline, for chapters
    = for sections
    - for subsections
    ^ for subsubsections
    " for paragraphs
    """
    reg = re.compile("^(#+)\\s(.*?)$", re.MULTILINE)
    decorators = [("=", "="), ("-", "-"), ("=", None), ("-", None), ("^", None), ('"', None)]
    for matchobj in list(reg.finditer(string))[::-1]:
        grp = matchobj.groups()
        if len(grp) == 2:  # groups count starts from group 0
            indx = len(grp[0])-1
            decorator = decorators[-1] if indx >= len(decorators) else decorators[indx]
            str_to_decorate = grp[1]
            start_ = matchobj.start()
            end_ = matchobj.end()
            string = string[:start_] + decorate_title(str_to_decorate, decorator) + string[end_:]

    return string


def decorate_title(string, tuple_of_under_and_overline):
    """
        Decorates a string title as in rst format
        :param string: the string represetning the title
        :param tuple_of_under_and_overline: a tuple or list of two 1-character strings, representing
        the decorator character for under (element 0) and overline (element 1). None is allowed (and
        it's self explanatory)

        :Examples:
        decorate_string("sea", ("=", None)) returns:
        ===
        sea

        decorate_string("abc", ("=", "-")) returns:
        ===
        sea
        ---
    """
    lens = len(string)
    if tuple_of_under_and_overline[0] is not None:
        string = (lens * tuple_of_under_and_overline[0] + "\n") + string
    if tuple_of_under_and_overline[1] is not None:
        string += "\n" + (lens * tuple_of_under_and_overline[0])
    return string

def replace_sec_headers(source, headers=[("#", "#"),
                                         ("*", "*"),
                                         (None,  "="),
                                         (None, "-"),
                                         (None, "^"),
                                         (None, "\"")]):
    reg = re.compile("^(#+) (.*)")
    i = 0   # external counter cause it will be modified in the loop
    for src in source:
        mobj = reg.match(src)
        if mobj and len(mobj.groups()) == 2:
            sectitle = mobj.group(2)
            source[i] = sectitle
            header = headers[min(6, len(mobj.group(1))) - 1]
            j = i
            if header[0]:
                source.insert(j-1, header[0] * len(sectitle))
                i += 1
            if header[1]:
                source.insert(j+1, header[1] * len(sectitle))
                i += 1
        i += 1


def setup(app):
    app.set_translator('latex', LatexTranslator)
    app.connect('source-read', source_read_handler)


#     app.add_node(nodes.field,
#                  # html=(visit_field_html, depart_field_html),
#                  latex=(visit_field_latex, depart_field_latex))
    # app.connect('doctree-read', render_abstract_node)
    # app.add_config_value('gnuplot_format', DEFAULT_FORMATS, 'html')