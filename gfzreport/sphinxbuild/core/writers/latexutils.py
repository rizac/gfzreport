'''
Latex writer utilities

Created on Oct 28, 2017

@author: riccardo
'''
import os
import json
import urllib2

_ROLE_NAME = "doi-citation"
_BASE_URL = "https://doi.org/"
# doi.org takes forever sometimes. Use a cache json file which we write into the dest directory
# its name is:
_CACHE_FILENAME = "doi_citations_cache.json"


def get_citation(app, doi):
    citation = get_citation_from_cache(app, doi)
    if citation is None:
        citation = get_citation_from_web(doi)
        outfn = os.path.join(app.builder.outdir, _CACHE_FILENAME)
        try:
            with open(outfn, 'r') as opn_:
                data = json.load(opn_)
        except (OSError, IOError, ValueError, TypeError):
            data = {}
        data[doi] = citation
        with open(outfn, 'w') as opn_:
            json.dump(data, opn_)
    return citation


def get_citation_from_cache(app, doi):
    outfn = os.path.join(app.builder.outdir, _CACHE_FILENAME)
    try:
        with open(outfn, 'r') as opn_:
            return json.load(opn_).get(doi, None)
    except (OSError, IOError, ValueError, TypeError):
        pass
    return None


def get_citation_from_web(doi):
    response = None
    try:
        if not doi:
            raise ValueError('empty')
        req = urllib2.Request(_BASE_URL + doi,
                              headers={'Accept': 'text/x-bibliography', 'style': 'apa',
                                       'locale': 'en-US'})
        response = urllib2.urlopen(req)
        cit = response.read()
        idx = cit.find(_BASE_URL)
        if idx > -1 and cit[idx:].strip().lower().endswith(doi.lower()):
            return cit[:idx].strip(), cit[idx:].strip()
        return cit.strip(), ""
    except Exception as exc:
        raise Exception("DOI error: %s" % str(exc))
    finally:
        if response is not None:
            try:
                response.close()
            except:
                pass

def parse_authors(authors_string):
    authors = []
    affiliations = []
    authors_with_affiliations = []

    inbrackets = False
    last_idx = 0
    authors_splitted = []
    for i in xrange(len(authors_string)):
        if inbrackets:
            if authors_string[i] == ')':
                inbrackets = False
            continue

        if authors_string[i] == '(':
            inbrackets = True
            continue

        if authors_string[i] in (',', ';'):
            auth = authors_string[last_idx:i].strip()
            if auth:
                authors_splitted.append(auth)
            last_idx = i+1

    last_auth = authors_string[last_idx:].strip()
    if last_auth:
        authors_splitted.append(last_auth)

    add_corresponding_author = False
    for a in authors_splitted:
        idx0 = a.find("(")
        affilindex = None
        if idx0 > -1:
            idx1 = a.find(")", idx0)
            if idx1 == -1:
                idx1 = len(a)
            affil = a[idx0+1:idx1].strip()
            a = a[:idx0].strip()
            if not a:
                continue
            if affil:
                try:
                    affilindex = affiliations.index(affil)
                except ValueError:
                    affilindex = len(affiliations)
                    affiliations.append(affil)
        corresponding_author = False
        if a[-1] == '*':
            corresponding_author = True
            add_corresponding_author = True
            a = a[:-1].strip()
            if not a:
                continue
        authors.append(a)
        if corresponding_author and affilindex is not None:
            authors_with_affiliations.append("%s$^{%d*}$" % (a, affilindex+1))
        elif corresponding_author:
            authors_with_affiliations.append("%s$^{*}$" % a)
        elif affilindex is not None:
            authors_with_affiliations.append("%s$^%d$" % (a, affilindex+1))
        else:
            authors_with_affiliations.append(a)

    affiliations = ["$^%d$ %s" % (i, a) for i, a in enumerate(affiliations, 1)]
    if add_corresponding_author:
        affiliations.append("$^{*}$ corresponding authors")

    # do not provide line breaks as they will be converted
    return ", ".join(authors), ", ".join(authors_with_affiliations), \
        " \\\\[\\baselineskip] ".join(affiliations)
