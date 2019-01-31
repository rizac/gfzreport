.. Annual report template. Please fill your custom text here below.
   This is a RsT (ReStructuredText) file and also a comprehensive tutorial
   which might help you during editing. RsT is a lightweight markup language designed to be both
   easily readable/editable and processable by documentation-processing software (Sphinx) to
   produce html, latex or pdf output

   This portion of text (".. " followed by INDENTED text) is a comment block and will not
   be rendered. The comment block ends at the first non-indented line found

.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. FIELD LIST (BEFORE THE TITLE)
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
 
.. Field lists are two-column table-like structures resembling database records. Each Field in a field
   list is in the form :name: value (note the space before value). E.g.:
   
   :Date: 2001-08-16
   :Version: 1
   
   In Sphinx, fields placed before the title, as the ones listed below, will never be rendered in
   any document and act as metadata.
   In this program, they define text variables which will be rendered in specific places
   of the document. The user has not to care about "where", just fill the relative values.
   
   As these bib. fields cannot have comments before or after (Sphinx bug?) we need to describe
   them all at once here, with the (theoretical) responsible in brackets:

   - doi (LIBRARY OR AUTHOR OR GIPP/GEOFON INPUT): the DOI of this report
   - subtitle (AUTHOR INPUT): self-explanatory. Filled automatically by default with the network description.
     Note: you should not specify newlines in it (same for subSubtitle below)
   - sub-sub-title (AUTHOR INPUT): self-explanatory. This is the (optional) sub-sub-subtitle (below the subtitle)
   - strNum (LIBRARY INPUT): the Scientific Technical Report (STR) number
   - strText (LIBRARY INPUT): the STR text, displayed in the bottom of the title and 2nd page
   - urn (LIBRARY INPUT): The urn, e.g.: urn:nbn:de:kobv:b103-xxxxx
     (side-note for developers: the sphinx builder might raise a
     warning if rst interprets it urn as URL. Please ignore the warning)
   - issn (LIBRARY INPUT): the issn. E.g.: 2190-7110
   - publicationYear (LIBRARY INPUT): the publication year. E.g., 2016
   - publicationMonth (LIBRARY INPUT): the publication month in plain english. E.g.: October

   Now you can fill their values (plain text only, no markup):

:doi: 10.14470/XXXXXXXXXXY

:subtitle:

:subSubtitle: 

:strNum: 

:strText: Scientific Technical Report

:urn: urn:nbn:de:kobv:b103-xxxxx

:issn: 

:publicationYear: 

:publicationMonth: 

:tocdepth: 3

.. ^^^^^^
.. TITLE:
.. ^^^^^^

.. Section titles are set by decorating a SINGLE line of text with under- (and optionally over-)
   line characters WHICH MUST BE AT LEAST AS LONG AS the section title length.
   There is no rule about which decoration characters to use, but equal decorations are interpreted
   as same "level": thus two chapter titles must have the same decorations, a chapter and a section
   must not

GEOFON Annual Report {{ year }}
=========================

.. ^^^^^^^^^^^^^^^^^^^^^^^^
.. FIELD LIST (AFTER TITLE)
.. ^^^^^^^^^^^^^^^^^^^^^^^^
 
.. In Sphinx, fields placed after the title will be rendered in all documents
   (developer note: they can have comments before or after and no markup in their value)  
   In this program they might be ignored, or pre-processed before rendering their value
   (for details see descriptions below)


.. authors (AUTHOR INPUT). Provide the author(s) as comma separated items. Affiliations should be
   included here if needed in round brackets after each author. Affiliations shared by more
   authors need to be re-typed. "corresponding author(s)" should be followed by an asterix.
   The program will parse and correctly layout of all these informations in latex/pdf (e.g., 
   avoiding repeated affiliations, and rendering "corresponding author" if an asterix is found).
   In html there is no such processing and the text below will be displayed
   as it is, after removing all asterixs.

:Authors: Author1* (Institute1), Author2 (Institute2), Author3 (Institute1)

.. The abstract (AUTHOR INPUT). In LaTeX, this will be rendered inside a \begin{abstract}\end{abstract}
   commands

:Abstract: write your abstract here, you can add newlines but remeber:
           you should indent
           any new line

.. the citation section. Write here how the user should cite this report, and/or how to cite
   any data related to this report, if needed. The text below will be rendered in the title back page in LaTeX.
   In principle, you might need to just change or re-arrange the text. For more experienced users,
   note the use of the custom role :doi-citation: where you can reference
   also an already defined bib. field before the title by wrapping the field name in "|", e.g. :doi-citation:`|doi|`.

:Citations: Recommended citation for the report:

            :doi-citation:`|doi|`
            
            
Executive summary
~~~~~~~~~~~~~~~~~


.. raw:: latex

   \tableofcontents
   \newpage

Introduction
~~~~~~~~~~~~



The GEOFON global seismic network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Regular maintenance 
<<<<<<<<<<<<<<<<<<<


Technical developments
<<<<<<<<<<<<<<<<<<<<<<


Technical support to other networks
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


Annexes
<<<<<<<



The GEOFON Data Centre
~~~~~~~~~~~~~~~~~~~~~~


Services of interest in {{ year }} (service uptime)
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



Data and metadata requests made in {{ year }}
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



GEOFON Rapid Earthquake Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Event dissemination in {{ year }}
<<<<<<<<<<<<<<<<<<<<<<<<<<<



Event notification delays in {{ year }}
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



Monitoring connections to the GEOFON web pages
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



Software development
~~~~~~~~~~~~~~~~~~~~

httpmsgbus
<<<<<<<<<<


fdsnws
<<<<<<


fdsnws_fetch
............


fdsnws2sds
..........


WebDC3
<<<<<<


Routing service
<<<<<<<<<<<<<<<


SC3 releases and usage
<<<<<<<<<<<<<<<<<<<<<<



Outreach and Capacity Building
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


GEOFON Team (Human Resources, {{ year }})
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

======================= ======= ===== ======= ====== ========== ======== ==================  
 Name                   GE Net. GE DC EQ info GE op. Soft. Dev. Outreach Fin. Project 
----------------------- ------- ----- ------- ------ ---------- -------- ------------------
Name Surname            x       x     x       x                 x        GFZ
Name Surname[*]         x                                                EUDAT/GFZ
======================= ======= ===== ======= ====== ========== ======== ==================

[*] Not working full time for GEOFON.



GEOFON Advisory Committee Members ({{ year }})
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dr. Florian Haslinger, Chair	ETH Zurich	Zurich,CH

Dr. Christian Bönnemann,	BGR	Hannover, D

Prof. Dr. Wolfgang Friederich,	RU Bochum,	Bochum, D

Prof. Dr. Thomas Meier,	CAU	Kiel, D

Prof. Dr. Max Wyss	International Centre for Earth Simulation,	Geneva, CH

Dr. Jan Zednik,	GFU	Prague, CZ



Appendices
~~~~~~~~~~


.. ==============================================================================   


..  RST syntax help
    ===============
    
    (you can delete this section when no longer needed / after completion of editing)
    
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    TEXT FORMATTING:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    This is an example of "normal" body text. It's not in a comment block.
    Remeber that indentation is a special RsT command and that newlines are actually not rendered
    (this is a newline and you shouldn't see any difference in html or latex)
    
    But you can type a new paragraph by adding an empty line above it (like in
    this case)
    
    Italic can be rendered by wrapping text within two asterix, bold by wrapping
    text within two couples of asterix:
       
    *This is rendered in italic*, **this is rendered in bold**
    
    
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    HYPERLINKS:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    Hyperlink (inline): simply type them: Urls are automatically recognized and linked:
    
    http://www.python.org/
    
    Hyperlink with substitution text: point to the same url as above but render 'Python' as text:
    
    `Python <http://www.python.org/>`_
    
    Hyperlink with substitution text, if it has to be referenced more than once.
    Define the hyperlink as follows (note that the line below is NOT rendered but is NOT
    a comment):
       
    .. _Wikipedia: https://www.wikipedia.org/
    
    And then reference them like this: Wikipedia_, and again, Wikipedia_ 
    
    
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    TEXT SUBSTITUTIONS:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    When the a text is repeated many times throughout one or more documents,
    especially if it may need to change later, define a text substitution like this
    (note that the line below is NOT rendered but is NOT a comment):
    
    .. |RsT| replace:: ReStructuredText
    
    Then, to see "ReStructuredText", type: |RsT|
    
    Note that by placing a backslash before a character, you render that character
    literally. To see "|RsT|", type "\|RsT\|", e.g.:
    
    |RsT| was obtained by typing \|RsT\|
    
    
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    MATH FORMULAE:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    Inline math formulae, use :math:`...` or latext dollar sign with latex syntax inside
    (the latter is not standard rst, but is implemented in this report):
    
    Here an inline math expression: :math:`(\alpha > \beta)` = $(\alpha > \beta)$
    
    More complex math formulae, use ..math:: then new empty line and INDENTED text, e.g.:
    
    .. math::
    
       n_{\mathrm{offset}} = \sum_{k=0}^{N-1} s_k n_k
    
    
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    FOOTNOTES:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    Footnotes with manual numbering:
    
    .. [1] First footnote
    
    .. [2] Second footnote, note that
       newlines which must be indented
    
    Here a ref to the first footnote [1]_ and here to the second [2]_.
    
    Footnotes with auto numbering (newlines must be INDENTED of at least three spaces):
    
    .. [#] First footnote (autonumbered)
    
    .. [#] Second footnote (autonumbered), note that
       newlines which must be indented
    
    Here a ref to the first footnote [#]_ and here to the second [#]_.
    
    Footnotes with auto numbering, referenced more than once (newlines must be INDENTED of at
       least three spaces):
    
    .. [#firstnote] First footnote (autonumbered, referenced more than once)
    
    .. [#secondnote] Second footnote (autonumbered, referenced more than once), note that
       newlines which must be indented
    
    Here a ref to the first footnote [#firstnote]_, again [#firstnote]_ and here to the second [#secondnote]_.
    
    Footnotes with auto symbols. DEPRECATED: seems they are buggy in latex:
    
    .. [*] First footnote (autosymbol)
    
    .. [*] Second footnote (autosymbol), note that
       newlines which must be indented
    
    Here a ref to the first footnote [*]_, and here to the second [*]_.
    
    
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    CITATIONS:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    Citations are identical to footnotes except that their labels
    must be case-insensitive single words of alphanumerics plus internal hyphens,
    underscores, and periods. No whitespace, no numeric only. E.g.:
          
    .. [CIT2002] Deep India meets deep Asia: Lithospheric indentation, delamination and break-off
       under Pamir and Hindu Kush (Central Asia). http://doi.org/10.1016/j.epsl.2015.11.046
    
    Here a reference to a publication: [CIT2002]_. And here another reference to it ([CIT2002]_)
    
    IMPORTANT NOTE: Citations are automatically placed in latex in a "References" section at the
    end of the document, regardless of where they are input. Conversely, in HTML they are
    rendered where they are input.

    
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    NUMERIC REFERENCES TO FIGURES AND TABLES:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    Providing a label placed IMMEDIATELY BEFORE a specific directive (e.g. figure, table, see below):

    .. _labelname

    you can reference it in the text with
    
    :numref:`labelname`
      
    
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    LIST ITEMS:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    Bullet lists (blank line before and after the list):
    
    - This is a bullet list.
    
    - Bullets can be "*", "+", or "-".
    
    Enumerated lists (blank line before and after the list):
    
    1. This is an enumerated list.
    
    2. Enumerators may be arabic numbers, letters, or roman
       numerals.
       
    Nested lists (blank lines are optional between items on the same level):
    
    * About RsT syntax:
    
      - https://pythonhosted.org/an_example_pypi`_project/sphinx.html#restructured-text-rest-resources
        (and links therein)
      - http://docutils.sourceforge.net/docs/user/rst/quickref.html
     
    * About Sphinx syntax (RsT with some commands added)
    
      - http://www.sphinx-doc.org/en/stable/rest.html#rst-primer
        
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    FOR DETAILS:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    - About RsT syntax:
      
      + http://docutils.sourceforge.net/rst.html 
        
    - About Sphinx:
      
      + http://www.sphinx-doc.org/en/stable/markup/index.html#sphinxmarkup
