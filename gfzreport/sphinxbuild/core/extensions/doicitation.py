"""
Implements the DOI citation role.
```
\:doicitation\:`doi`
\:doicitation\:`|doi|`
```
(the latter looks for a filed name before the title with name 'doi' and replaces the value
in the role)

The role will be rendered as the full text citation (with optional hyperlink, if found) by
querying "https://doi.org/" + [role_value]

See https://doughellmann.com/blog/2010/05/09/defining-custom-roles-in-sphinx/ for a tutorial
on how to implement Sphinx roles

Created on Jan 30, 2017

@author: riccardo
"""
import os
import json
import urllib2

from docutils import nodes

from gfzreport.sphinxbuild.core import touni

_ROLE_NAME = "doi-citation"

_CACHE_FILENAME = "doi_citations_cache_json.log"  # this file will be saved in the **source** dir
# to make it available from every builder, as sometimes doi.org takes forever.
# Log files should be safe to use. They can be disabled
# when searching for docs to scan in the conf.py, although that just prevents them to copy to the
# builddir apparently

URLOPEN_TIMEOUT_IN_SEC = 10

DOI_BASE_URL = "https://doi.org/"

# utilities: ==============================================================================

def get_citation(root_dir, doi):
    '''
    :return: the tuple (doi-citation, url) (both strings). The latter might be empty
    '''
    citation = get_citation_from_cache(root_dir, doi)
    if citation is None:
        citation = get_citation_from_web(doi)
        outfn = os.path.join(root_dir, _CACHE_FILENAME)
        try:
            with open(outfn, 'r') as opn_:
                data = json.load(opn_)
        except (OSError, IOError, ValueError, TypeError):
            data = {}
        data[doi] = citation
        with open(outfn, 'w') as opn_:
            json.dump(data, opn_)
    return citation


def get_citation_from_cache(root_dir, doi):
    outfn = os.path.join(root_dir, _CACHE_FILENAME)
    try:
        with open(outfn, 'r') as opn_:
            return json.load(opn_).get(doi, None)
    except (OSError, IOError, ValueError, TypeError):
        pass
    return None


def get_citation_from_web(doi):
    '''
    :return: the tuple (doi-citation, url) (both strings). The latter might be empty
    '''
    response = None
    try:
        if not doi:
            raise ValueError('empty')
        req = urllib2.Request(DOI_BASE_URL + doi,
                              headers={'Accept': 'text/x-bibliography', 'style': 'apa',
                                       'locale': 'en-US'})
        response = urllib2.urlopen(req, timeout=URLOPEN_TIMEOUT_IN_SEC)
        cit = response.read()
        idx = cit.find(DOI_BASE_URL)
        if idx > -1 and cit[idx:].strip().lower().endswith(doi.lower()):
            return cit[:idx].strip(), cit[idx:].strip()
        return cit.strip(), ""
    except Exception as exc:
        raise Exception("DOI error ('%s'): %s" % (doi, str(exc)))
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:  #pylint: disable=broad-except
                pass

# end utilities: ==============================================================================

class doicitnode(nodes.TextElement):
    '''This is, as always, a hack (thanks Sphinx). It is a no-op node
    whose children will be created when visiting the node later.
    As we want to support string replacements (e.g., ":doi-citation:`|doi|`" means: look at the
    bib.fields before the title named 'doi' and replace its value here, if any)
    we need to have bib fields before the title available
    Bib. fields before the title are available in
    ```app.env.metadata[app.config.master_doc]```
    BUT (and this is the weird thing) ONLY LATER, when visiting the node'''
    pass
#    def __init__(self, text, **attributes):


def doicitation_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Function registered in the app for the doi-citation role. Almost no-op, returns
    a ```doicitnode```. Code copied and modified from this tutorial
    https://doughellmann.com/blog/2010/05/09/defining-custom-roles-in-sphinx/ for a tutorial
    
    Returns 2 part tuple containing list of nodes to insert into the
    document and a list of system messages.  Both are allowed to be
    empty.

    :param name: The role name used in the document.
    :param rawtext: The entire markup snippet, with role.
    :param text: The text marked with the role.
    :param lineno: The line number where rawtext appears in the input.
    :param inliner: The inliner instance that called us.
    :param options: Directive options for customization.
    :param content: The directive content for customization.
    """
    return [doicitnode(text)], []
    

def visit_doicit_node(self, node):
    '''visits the doicitnode and creates its children after querying for the DOI citation
    to the web service. As this method does nothing the node will not be rendered,
    but its children (a text node plus an optional href) will be traversed and rendered
    accordingly
    :param node: the ```doicitnode```
    '''
    # setup the node properly, with substitutions if needed
    process_node(node, self.builder.app)  
    # as we built it, the rendering is fine. self will pass this node and process
    # its children correctly


def depart_doicit_node(self, node):
    # as we built it, the rendering is fine. self will pass this node and process
    # its children correctly
    pass


def process_node(node, app):
    '''Sets the children of node after querying the DOI web service. The children
    are a text node plus an optional href
    :param node: the ```doicitnode```
    '''
    text = node.rawsource
    metadata = app.env.metadata[app.config.master_doc]
    # check strings in the form "|.*|" and substitute them with
    # the field list before the title, available in metadata (it's a dict):
    # do a normal for-loop: strings substitution and regexp are equally expensive in terms of code
    # as we want to parse each sub-chunk wrapped "|":
    doitext = ''
    substitution_text = None
    for s in text:
        if s == '|':
            if substitution_text is None:
                s = substitution_text = ''
            else:
                # check the variable and substitue, if found, otherwise append the string
                # as it is (with "|" temporarily removed):
                s = metadata.get(substitution_text, "|" + substitution_text + "|")
                substitution_text = None
        elif substitution_text is not None:
            substitution_text += s
            s = ''
        doitext += s
    if substitution_text is not None:  # some chunk open and not closed with "|"? append it:
        doitext += "|" +substitution_text

    # prepare the doi
    source_dir = app.srcdir
    try:
        doi_text, doi_url = get_citation(source_dir, doitext)
    except Exception as exc:  #pylint: disable=broad-except
        doi_text  = str(exc)
        doi_url = ''
    nodez = [nodes.Text(touni(doi_text))]  # `touni` because Text nodes want unicode
    if doi_url:
        urlnode = nodes.reference('', '')
        urlnode['refuri'] = doi_url
        urlnode.append(nodes.Text(touni(doi_url)))  # `touni` because Text nodes want unicode
        nodez += [nodes.Text(touni(' ')), urlnode]  # `touni` because Text nodes want unicode
    # DONT DO THIS:
    # node.children = nodez
    # nodes.Element has to be assigned via indices, or append.
    # This does some settings like, e.g. assigning the parent to the child none
    # Thus setup the children array first:
    for child in nodez:
        node.append(child)
    # now we can return
    return node
    
def setup(app):
    '''setup the app for the doi-citation role'''
    app.add_node(doicitnode,
                 html=(visit_doicit_node, depart_doicit_node),
                 latex=(visit_doicit_node, depart_doicit_node))

    app.add_role('doi-citation', doicitation_role)
