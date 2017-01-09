.. Network report template. Please fill your custom text here below.
   This is a RsT (ReStructuredText) file and also a comprehensive tutorial
   which might help you during editing.
   RsT is a lightweight markup language designed to be both
   (1) processable by documentation-processing software to produce html,
      latex or pdf output, and
   (2) easily readable and editable by human interaction.
   As already mentioned, you might just need to simply follow the instructions
   here. Links are provided below for a more detailed explanation
   about rst syntax
   
   Let alone inline syntax (e.g., section decorators, bold / italic text, urls)
   the only concept to know is Explicit Markup Blocks (EMB), defined as a text block:
   (a) whose first line begins with ".." followed by whitespace
       (the "explicit markup start", hereafter referred as EMS)
   (b) whose second and subsequent lines (if any) are indented relative to the first, and
   (c) which ends before an unindented line.
   EMB's are analogous to bullet list items, with ".." as the bullet. The text on the
   lines immediately after the EMS determines the indentation of the
   block body. The maximum common indentation is always removed from the second and
   subsequent lines of the block body. Therefore if the first construct fits in one
   line, and the indentation of the first and second constructs should differ,
   the first construct should not begin on the same line as the explicit markup start.
   IMPORTANT: Blank lines are required between explicit markup blocks and other elements,
   but are optional between explicit markup blocks where unambiguous.
   The explicit markup syntax is used for footnotes, citations, hyperlink targets,
   directives, substitution definitions, and comments. All discussed below
   
   For instance, this portion of text is a comment and will NOT be rendered
   in any output format (html, latex, pdf). A comment block is an EMB (thus
   obeying to (a)-(b)-(c) rules above) which does not match any of the other EMB's
   (discussed below). This definition is quite "fuzzy" because we need to define
   comment blocks before the other directives

.. Section titles (like the one below, which is the auto-generated document title) are
   set by decorating a SINGLE line of text with under- (and optionally over-)
   line characters WHICH MUST BE AT LEAST AS LONG AS the section title length.
   There is no rule about decoration characters. Just be consistent (same
   decoration for sections of the same "level").

{{ title }}

.. Here below the so-called "rst bibliographic fields" (authors, revision, etcetera)
   in the form semicolon + fieldname + semicolon + whitespace + fieldbody
   The field body may contain multiple body elements. HOWEVER, it is strongly
   recommended to input text (i.e. no special rst markup) or urls ONLY.

   The first line after the field name marker determines the indentation of the field body.
   DO NOT REMOVE THE FIELDS BELOW, RATHER SET THEIR FIELDBODY EMPTY. IF EMPTY, 
   REMEMBER TO LEAVE A WHITESPACE AFTER THE LAST SEMICOLON (:) OF THE FIELD NAME
   
   Certain registered field names have a special meaning in rst which are beyond
   the scope of this program
   (for details, see http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#bibliographic-fields)
   On the other hand, they will be automatically rendered in
   special portions of the latex layout (which you don't have to care about),
   You have only to fill the text if you know its value (e.g., the DOI),
   or leave it empty.

.. provide the authors as comma separated items:

:authors: Author1, author2, author3

.. subtitle. Filled automatically by default with the network description. Note: you
   should not specify newlines in it (same for subSubtitle below)

:subtitle: {{ network_description }}

.. this this is the (optional) sub-sub-subtitle (below the subtitle)

:subSubtitle: 

.. a revision mechanism from within the rst is currently not implemented,
   this field can be left as it is:

:revision: 1.0

.. the Scientific Technical Report (STR) number. Fill in if you know it

:strNum: 

.. the doi. Fill in if you know it. For info on the doi format see
   https://en.wikipedia.org/wiki/Digital_object_identifier#Nomenclature
   Example: http://doi.org/10.2312/GFZ.b103-xxxxx
      
:doi: 

.. The urn. Fill in if you know it.
   Example: urn:nbn:de:kobv:b103-xxxxx
   Just a side-note for developers the sphinx builder will raise a
   warning as rst interprets it urn as URL. Please ignore the warning

:urn: 

.. the issn. Fill in if you know it (e.g.: 2190-7110)

:issn: 

.. the publication year. Fill in if you know it (e.g., 2016)

:publicationYear: 

.. the publication year. Fill in if you know it (e.g., October)

:publicationMonth: 

.. this field is optional and will be rendered (in latex only) under the section
   "Supplementary datasets:" in the back of the cover page. Fill it with
   a bibliographic citation to a publication (if any)

:supplDatasets: 

.. this field is optional and will be rendered (in latex only) under the section
   "Recommended citation for chapter:" in the back of the cover page. Fill it with
   a bibliographic citation to a publication (if any)

:citationChapter: 

.. this field is optional and will be rendered (in latex only) under the section
   "The report and the datasets are supplements to:" in the back of the cover page.
   Fill it with a bibliographic citation to a publication (if any)

:supplementsTo: 

.. this is the abstract and will be rendered in latex within the 
   abstract environment (\begin{abstract} ... \end{abstract}):

:abstract: write your abstract here, you can add newlines but remeber:
  you should indent
  any new line
  (as we just did).

.. From here on, you can start typing "body text" anywhere you want by simply
   writing NON-INDENTED text which is not a comment

Introduction
============

This is an example of "normal" body text. It's not in a comment block so that,
before removing it, you might try to build this document
(build = generate html, latex or pdf) and see the rendered results.
Remeber that indentation is a special rst command and that newlines are
actually not rendered (this is a newline and you shouldn't see any difference
in html or latex)

But you can type a new paragraph by adding an empty line above it (like in
this case)


.. italic can be rendered by wrapping text within two asterix, bold by wrapping
   text within two couples of asterix:
   
*This is rendered in italic*

**This is rendered in bold**

.. Numeric Reference to figures or tables are discussed in the bottom of this
   document. In general, to define a label pointing to a EMB, e.g. a label named
   "stations_table" pointing to a figure directive (discussed below), you write a single
   EMB IMMEDIATELY BEFORE the figure directive that you wanto to reference.
   Putting even comment blocks between the label and the figure directive will make
   the label point to the comment block, and thus not working as expected.
   So, supposing you have somewhere an EMB (e.g. a figure directive), to label it you write
   IMMEDIATELY BEFORE the explicit markup start EMS (".." followed by whitespace)
   followed by an underscore and the label name (and a blank line afterwards, as always):
      
    .. _stations_table
      
    Now you can reference to it with :numref:`stations_table`. Example (you should
    see the reference now in latex/html): 

An example of numeric reference: see :numref:`stations_table`
   
.. Inline hyperlink. Urls are automatically linked, like: http://www.python.org/

Normal inline hyperlink: http://www.python.org/

.. Inline hyperlink with substitution text: write substitution text + space + url,
   all wrapped within a leading ` and a trailing `_

Inline hyperlink with subsitution text: `Python <http://www.python.org/>`_

.. Hyperlink with substitution text, if it has to be referenced more than once
   Write the label by providing an EMB as follows:
   EMS (as always) followed by an underscore and the label name, followed
   by a semicolon, a space and, finally, the referenced url
   Example (note that the line below is NOT a comment, but being a label definition
   it won't be rendered in latex/html):
   
.. _Wikipedia: https://www.wikipedia.org/

.. Then, you can reference it anywhere by typing label name + underscore, e.g.:
   Wikipedia_. Example:

Normal hyperlinks with label definition
can be referenced more than once: Wikipedia_, and again, Wikipedia_ 
   
.. When the replacement text is repeated many times throughout one or more documents,
   especially if it may need to change later, you can define a 
   replacement text. Replacement texts are a special case of Substitution
   definitions, which are EMB: thus they start with EMS (".. ")
   followed by a vertical bar, the substitution text, another vertical bar, whitespace,
   and the definition block. The latter contains an embedded inline-compatible directive
   (without the leading ".. "), such as "image"(not discussed here) or "replace".
   Example.:

.. |RsT| replace:: ReStructuredText

.. (Substitution text may not begin or end with whitespace)
   Now you should see "Text substitution: ReStructuredText" in latex/html/pdf:

Text substitution: |RsT|

.. Note that by placing a backslash before a character, you render that character
   literally. E.g., concerning the text substitution just descirbed:

|RsT| was obtained by typing \|RsT\|

.. Math formulae: Math can be typed in two ways. Either inline like this:
   semicolon + math + semicolon + ` wrapping the math expression:
   
   :math:`alpha > beta`
   
   or, for more complex expressions, the math directive (directives are EMB, more
   about them at the bottom of the document):
   
   .. math::

      n_{\mathrm{offset}} = \sum_{k=0}^{N-1} s_k n_k

Here a math expression: :math:`alpha > beta`

Here a more complex math expression:

.. math::

   n_{\mathrm{offset}} = \sum_{k=0}^{N-1} s_k n_k

.. Note that we implemented for this program also a third variant with dollar
   sign (as in latex), which will default to the :math: command above. So:
   
these expressions should be the same:  :math:`(\alpha > \beta)` = $(\alpha > \beta)$

.. Footnotes are EMBE thus consists of an EMS (".. "), a left square bracket,
   the footnote label, a right square bracket, and whitespace, followed by indented body elements.
   A footnote label can be:
      - a whole decimal number consisting of one or more digits,
      - a single "#" (denoting auto-numbered footnotes),
      - a "#" followed by a simple reference name (an autonumber label), or
      - a single "*" (denoting auto-symbol footnotes).
  
.. [#] First footnote, should be numbered as 1

.. [#] First footnote, should be numbered as 2

.. Each footnote reference consists of a square-bracketed label followed by a
   trailing underscore:

Here a ref to the first footnote [#]_ and here to the second [#]_.

.. NOTE: auto-symbols footnotes are deprecated as they seem not to work properly
   in latex. Check out yourself:
  
.. [*] First footnote, should use the "first" autogenerated symbol. Buggy in Latex

.. [*] First footnote, should use the "second" autogenerated symbol. Buggy in Latex

Here a ref to the first footnote [*]_ and here to the second [*]_.

.. Citations are defined by writing two periods + space, followed by
   a square-bracketed label, a whitespace and then the publication (indenting
   newlines if needed, as always). For instance (in latex it's automaticallys
   put in the reference section at the end of the document):

.. [CIT2002] Deep India meets deep Asia: Lithospheric indentation, delamination and break-off under
   Pamir and Hindu Kush (Central Asia). http://doi.org/10.1016/j.epsl.2015.11.046

.. Each citation reference consists of a square-bracketed label followed by a trailing 
   underscore. Citation labels are simple reference names (case-insensitive single
   words, consisting of alphanumerics plus internal hyphens, underscores, and periods;
   no whitespace):

Here a reference to a publication: [CIT2002]_. And here another reference to it ([CIT2002]_)

.. Finally, bullet lists are obtained by starting each list item with the characters
   "-", "*" or "+"
   followed by a whitespace. You can span the item text on several lines, but
   newlines text must be aligned after the bullet and whitespace.
   Nested levels are permitted. Within items on the same level, a blank line is
   required before the first item and after the last, but is optional
   between items. Example:

**If you want to know more**:

* About RsT syntax:

  - https://pythonhosted.org/an_example_pypi_project/sphinx.html#restructured-text-rest-resources
    (and links therein)
  - http://docutils.sourceforge.net/docs/user/rst/quickref.html
 
* About Sphinx syntax (RsT with some commands added)

  - http://www.sphinx-doc.org/en/stable/rest.html#rst-primer
    
**More detailed tutorials**:

- About RsT syntax:
  
  + http://docutils.sourceforge.net/rst.html 
    
- About Sphinx:
  
  + http://www.sphinx-doc.org/en/stable/markup/index.html#sphinxmarkup

Data Acquisition
================

Write your section text here if any, or remove this line

Experimental Design and Schedule
--------------------------------

Write your section text here if any, or remove this line

Site Descriptions and Possible Noise Sources
--------------------------------------------

Write your section text here if any, or remove this line

Instrumentation
---------------

Write your section text here if any, or remove this line

Instrument Properties and Data Processing
=========================================

Write your section text here if any, or remove this line

Data Description
================

Write your section text here if any, or remove this line

Data Completeness
-----------------

Write your section text here if any, or remove this line

File Format
-----------

Write your section text here if any, or remove this line

Data Content and Structure
--------------------------

Write your text here if any, or remove this line

Data Quality and Timing Accuracy
================================

Write your text here if any, or remove this line

Noise Estimation
----------------

Write your text here if any, or remove this line

Timing Accuracy
---------------

Write your text here if any, or remove this line

   
Acknowledgments
===============

Write your text here if any, or remove this line. To show how references work, have a look at
the text and how is rendered in latex / html:

Here a reference to :numref:`stations_table`

Here a reference to :numref:`stations_figure`

Here a reference to :numref:`inst_uptimes_figure`

Here a reference to :numref:`noise_pdfs_figure`

.. ==============
   Rst Directives
   ==============

.. We place in the bottom of the document (see below) the so-called rst "directives".
   Directives are explicit markup blocks (EMB) which are used to render special
   objects, in particular figures and tables.
   Directives begin, as always, with an explicit markup start EMS (two periods and a space),
   followed by the directive type, two colons and a whitespace (collectively, the
   "directive marker").
   Example of typical directive marker (.. image:: ) which includes the image
   mylogo.jpeg:

   .. image:: mylogo.jpeg
   
   Two colons are used after the directive type for several reasons, the first of
   which is distinguish comment blocks (like e.g., this one) and directives.

   The directive block begins immediately after the directive marker, and includes
   all subsequent INDENTED lines. The directive block is divided into arguments,
   options (a field list), and content (in that order), any of which may appear.
   For instance to include a figure displaying the file ./larch.png with caption
   "abc" and width equal to 33% of its container (usually, the page width) type:
   
   .. figure:: ./larch.png
      :width: 33%

      abc
    
   in the example above, the directive argument is './larch.png', the only directive
   option is 'width', and the directive content is represented by its caption ('abc').
   (For a detailed guide on the figure directive, see
   http://docutils.sourceforge.net/docs/ref/rst/directives.html#figure)

   Important notes:
   ---------------

   a) all relative paths in the document (like ./larch.png) are relative to this file.
   Absolute paths are discouraged especially because it seems that sphinx (the python
   program on top of which we generate thie report) is quite confusing and not consistent
   in that case
   
   b) you can move a directive anywhere in the text by copying and pasting the directive
   marker and its block (including the last blank line) anywhere in the text.
   Any object returned by a directive (figures, tables,...) is in principle displayed
   where it appears here

   c) You can reference directives (e.g., figures, tables) by placing IMMEDIATELY BEFORE
   the directive the reference label, followed by a blank line. The label begins with an
   explicit markup start (two periods and a space), followed by an underscore,
   the label name, and a semicolon. E.g:
   
   .. _myreflabel:
   
   The directive can thus be referenced anywhere in the text by typing:
   :numref:`myreflabel`
   and will be properly rendered in both latex, pdf or html. See examples in the directives
   implemented below
   
.. =======================  
   Custom figures / tables
   =======================

.. 1) The first directive is the directive to display the stations information in a
   table. It's the so called 'csv-table' directive
   (http://docutils.sourceforge.net/docs/ref/rst/directives.html#id4):
   There are several ways to display tables, all of them have several drawbacks
   (rst + sphinx limitations). We use csv-tables because they have the advantage to
   be easily editable.

.. first of all, we show the "raw" directive, which might comes handy to put
   html or latex specific commands: in this case we decrease the size of the table
   to avoid page overflow:
   
.. raw:: latex

   \scriptsize
   
.. Second, we use the tabularcolumns directive
   (http://www.sphinx-doc.org/en/latest/markup/misc.html#directive-tabularcolumns):
   this directive gives a “column spec” for the next table occurring in the source file.
   The spec is the second argument to the LaTeX tabulary package’s environment, although,
   contrarily to what stated in the doc, sphinx might use different tabular environment
   which are hard coded and impossible to configure (e.g., longtables):

.. tabularcolumns:: |@{\ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ }|

.. third, the figure label (.. _stations_table:) before the csv-table directive.
   Remeber: the label must be placed IMMEDIATELY BEFORE the directive and can be
   referenced via  :numref:`stations_table`. It must start with two dots and a space
   (as all directives), plus an underscore, the label name (stations_table) and a semicolon
   DO NOT PUT ANYTHING, NOT EVEN COMMENT BLOCKS, between a label and the EMB that the label
   should point to!

.. _stations_table:

.. csv-table:: This is the table caption
   :delim: ,
   :quote: "
   :header-rows: 1
   
   {{ stations_table_csv_content|indent(3) }}

.. restore normal size in latex only:

.. raw:: latex

   \normalsize

.. ==============================================================================   

.. 2) The second directive below is the directive to display the station map figure.
   It is a non-standard directive implemented in this program only, whose syntax is
   similar to the csv-table directive (ses above) BUT produces an image instead.
   In principle, there is no need to modify the directive argument (the path to the
   csv file whose data needs to be plotted), but you can edit the csv file in an editor
   like Excel (c) or LibreOffice
   
   As described above, first there is the directive label (which you can reference by typing
   :numref:`stations_figure`
   anywhere in the text, then its body, and eventually its caption:

.. _stations_figure:

.. map-figure:: This is the figure caption
   :header-rows: 1
   :align: center
   :delim: ,
   :quote: "
   
   {{ stations_map_csv_content|indent(3)  }}

.. ==============================================================================   

.. 3) The third directive is the directive to display the noise pdfs. You can
   see the already described directives for raw latex input, for latex tabularcolumns
   and the relative label

.. raw:: latex

   \clearpage
   
.. tabularcolumns:: @{}m{.33\textwidth}@{}m{.33\textwidth}@{}m{.33\textwidth}@{}
   
.. The images-grid-directive is a non-standard directive implemented
   in this program only, whose syntax is similar to the csv-table directive (ses above)
   BUT produces an grid of images.
   Note that in latex this will be rendered with a longtable followed by an
   empty figure (i.e., with no image inside) holding the caption provided here. This
   is a workaround to produce something that looks like a figure spanning over several
   pages (if needed) BUT it might need some arrangment here because the figure might be
   "detached" from the table, not being the same latex element

.. _noise_pdfs_figure:

.. images-grid:: here the figure caption
   :dir: {{ noise_pdfs_dir_path | safe  }}
   :align: center
   :header-rows: 1
   :latex-includegraphics-opts: trim=8 30 76 0,width=0.33\textwidth,clip

   {{ noise_pdfs_content|indent(3) }}
   

.. ==============================================================================   

.. 4) The fourth directive is the directive to display the instrumental uptimes
   (depending on the number of files uploaded when generating
   this template, it's either a 'figure' or 'images-grid' directive, in any
   case it will be rendered as figure in html and latex).
   Remember that, contrarily to the csv-table directive, the figure directive
   argument is the file path of the figure (we suggest to use relative path starting
   with the dot ".", relative to this file), and the directive content is the figure
   caption
   
.. _inst_uptimes_figure:

.. {{ inst_uptimes_directive }}:: {{ inst_uptimes_arg }}
   {% for opt_name in inst_uptimes_options -%}
   :{{ opt_name }}: {{ inst_uptimes_options[opt_name] | safe }}
   {% endfor -%}
   {% if inst_uptimes_directive == "figure" -%}
   :latex-includegraphics-opts: angle=-90,width=\textwidth
   :width: 100%
   {% else -%}
   :latex-includegraphics-opts: width=\textwidth
   {% endif -%}
   :align: center

   {{ inst_uptimes_content|indent(3)  }}
