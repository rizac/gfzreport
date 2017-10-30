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