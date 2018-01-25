'''
Latex writer utilities

Created on Oct 28, 2017

@author: riccardo
'''


def parse_authors(authors_string):
    '''Parses the author_string (as input in the rst) and returns three tuples for latex documents:
    authors, authors_with_affiliations, affiliations.
    
    Example:

    ===========================  =========================================
    Input authors_string is:     Me* (abc), Myself(abc), John Smith (H)
    ===========================  =========================================
    authors                      Me, Myself, John Smith
    authors_with_affiliations    Me$^{1*}$, Mysrelf$^1$, John Smith$^2$
    affiliations                 $^1$ abc \\[\baselineskip] $^2$ H \\[\baselineskip] $^{*}$ corresponding authors
    ===========================  =========================================
    
    :param suthors_string: the string as inoput in the rst
    '''
    
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
