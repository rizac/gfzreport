.. Network report template. Please fill your custom text here below.
   This is a RsT (ReStructuredText) file and also a comprehensive tutorial
   which might help you during editing. RsT is a lightweight markup language designed to be both
   easily readable/editable and processable by documentation-processing software (Sphinx) to
   produce html, latex or pdf output

   This portion of text (".. " followed by INDENTED text) is a comment block and will not
   be rendered. The comment block ends at the first non-indented line found

.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. FIELD LIST (LATEX METADATA)
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^
 
.. Field lists are two-column table-like structures resembling database records
   in the form :name: value (note the space before value). E.g.:
   
   :Date: 2001-08-16
   :Version: 1
   
   Fields in a Field list placed before the title:
   - Will never be rendered in any document
   - Can not have comments before or after (Sphinx bug?)
   - Must have values in plain text only, as markup in there will not be
     recognized (However, in this program newlines will be rendered)
   - Have to be considered as document metadata: their value will be placed in specific portions
     of the latex layout
   
   Here below a description of these fields:

   - doi (LIBRARY OR AUTHOR OR GIPP/GEOFON INPUT): the DOI of this report
   - doiDataset (LIBRARY INPUT): the DOI of the report dataset, if any
   - doiSupplementaryDataset (LIBRARY INPUT): the DOI of the report supplementary data, if any
   - subtitle (AUTHOR INPUT): self-explanatory. Filled automatically by default with the network description.
     Note: you should not specify newlines in it (same for subSubtitle below)
   - sub-sub-title (AUTHOR INPUT): self-explanatory. This this is the (optional) sub-sub-subtitle (below the subtitle)
   - strNum (LIBRARY INPUT): the Scientific Technical Report (STR) number
   - strText (LIBRARY INPUT): the STR text, displayed in the bottom of the title and 2nd page
   - strSeriesText (LIBRARY INPUT): the STR series text, displayed under the STR text (in smaller font) 
   - urn (LIBRARY INPUT): The urn, e.g.: urn:nbn:de:kobv:b103-xxxxx
     (side-note for developers: the sphinx builder might raise a
     warning if rst interprets it urn as URL. Please ignore the warning)
   - issn (LIBRARY INPUT): the issn. E.g.: 2190-7110
   - publicationYear (LIBRARY INPUT): the publication year. E.g., 2016
   - publicationMonth (LIBRARY INPUT): the publication month in plain english. E.g.: October
   - reportCitationPreamble (LIBRARY INPUT): the preamble text before the full bibliographic citation
     relative to the DOI of this report. The full text (preamble + DOI)
     will be rendered as the first paragraph in the back of the title page
   - datasetCitationPreamble (LIBRARY INPUT): the preamble text before the full bibliographic citation
     relative to the DOI of the dataset of this report
     The full text (preamble + DOI) will be rendered as the second paragraph in the back of the title page
     Note: If doiDataset is empty, nothing will be printed
   - supplementaryDataCitationPreamble (LIBRARY INPUT): the preamble text before the full bibliographic citation
     relative to the DOI of the supplementary dataset of this report.
     The full text (preamble + DOI) will be rendered as the third paragraph in the back of the title page.
     Note: If doiSupplementaryDataset is empty, nothing will be printed


:doi: 10.14470/XXXXXXXXXXY

:doiDataset: 10.14471/XXXXXXXXXXX

:doiSupplementaryData: 10.14472/XXXXXXXXXXX

:subtitle: {{ network_description }}

:subSubtitle: 

:strNum: 

:strText: Scientific Technical Report - Data

:strSeriesText: GIPP Experiment and Data Archive

:urn: urn:nbn:de:kobv:b103-xxxxx

:issn: 

:publicationYear: 

:publicationMonth: 
      
:reportCitationPreamble: Recommended citation for the data report:

:datasetCitationPreamble: If you use the dataset described in this report, please use the following citation:
   
:supplementaryDataCitationPreamble: The raw unprocessed data from cube data loggers and logfiles from
   EDL stations are archived as assembled dataset and should be cited as:


.. ^^^^^^
.. TITLE:
.. ^^^^^^

.. Section titles are set by decorating a SINGLE line of text with under- (and optionally over-)
   line characters WHICH MUST BE AT LEAST AS LONG AS the section title length.
   There is no rule about which decoration characters to use, but equal decorations are interpreted
   as same "level": thus two chapter titles must have the same decorations, a chapter and a section
   must not

{{ title }}

.. ^^^^^^^^^^^^^^^^^^^^^^^^
.. FIELD LIST (AFTER TITLE)
.. ^^^^^^^^^^^^^^^^^^^^^^^^
 
.. Fields in a Field list placed after the title:
   - Will be rendered in all documents (where and how, it depends on the output, e.g. LaTex vs HTML)  
   - Can have comments before or after
   - Can have values in rst syntax, as markup in there will be recognized. Thus remember to escape
     special characters with a backslash, if needed (e.g. to render ":abc:def:" as it is
     you need to input "\:abc\:def\:")


.. authors (AUTHOR INPUT). Provide the authors as comma separated items. Affiliations should be
   included here if needed, e.g. in round brackets after the author:

:authors: Author1, author2, author3

.. The abstract (AUTHOR INPUT):

:Abstract: write your abstract here, you can add newlines but remeber:
           you should indent
           any new line


.. From here on the document content. Section titles are underlined (or under+overlined)
   Provide always at least an empty line above and below each section title


Introduction
============

.. (AUTHOR INPUT) Describe the overall motivation for the experiment, its scientific objectives,
   and general statements about the conduct of the experiment, overall evaluation etc. 


Data Acquisition
================

Experimental Design and Schedule
--------------------------------

.. (AUTHOR INPUT) Describe here the overall design and design goals, the schedule of deployment,
   recovery and service trips, any major reorganisations of array geometry 

The station distribution is shown in :numref:`stations_figure`, and :numref:`stations_table`
summarises the most important information about each station.

Site Descriptions
-----------------

.. (AUTHOR INPUT) Describe in what environments stations were deployed (free field, urban etc.,
   in houses or outside etc). Upload pictures of a typical installation. 

Instrumentation
---------------

.. (AUTHOR INPUT) What instruments were used in the experiment, to whom do they belong.
   Any special issues? What version of firmware did they run.  Any particular technical issues
   (malfunctioning equipment)

Sensor orientation
------------------

.. (AUTHOR INPUT) Were stations aligned to magnetic north or true north.  How were
   they aligned (in case of true north Gyrocompass or magnetic compass
   with correction). If magnetic compass was used, what was the magnetic
   declination at the time of the experiment and how was it
   determined. Note that GFZ provides a declination calculator at
   http://www.gfz-potsdam.de/en/section/earths-magnetic-field/data-products-services/igrf-declination-calculator/
   Please verify that the sensor orientation in the GEOFON database (see table below)
   matches the actual orientation. (If not please send an email to geofon@gfz-potsdam.de to
   correct this)


Data Description
================

Data Completeness
-----------------

.. (AUTHOR INPUT) What proportion of the data were recovered. What were the reasons for data loss

:numref:`inst_uptimes_figure` shows the uptime of each stations.

Data Processing
---------------

.. (AUTHOR INPUT) Describe the steps resulting in generating the miniseed file finally submitted
   to GEOFON
 
Data quality and Noise Estimation
---------------------------------

.. (AUTHOR INPUT) Describe the noise levels, describe possible noise sources (day/night
   variability if this information is available and describe any other issues with the data
   quality, e.g. stuck components

Fig. :numref:`noise_pdfs_figure` shows noise probability density functions for all channels.

Timing Accuracy
---------------

.. (AUTHOR INPUT) How well did the GPS clocks run. Are there any stations with significant GPS
   outages? Be specific by providing tables or figures showing exactly which stations are
   trustworthy. What is your best estimate for the timing accuracy - note that for EDL you can
   upload plots 


Data Access
===========

File format and access tools
----------------------------

.. Normally nothing to be added by the PI here

The data are stored in the GEOFON database, and selected time windows can be requested by EIDA
access tools as documented on http://geofon.gfz-potsdam.de/waveform/ . Normally the data are
delivered in miniseed format. 
The current data access possibilities can always be found by resolving the DOI of the dataset.

Structure and file formats of supplementary datasets
----------------------------------------------------

.. (OPTIONAL AUTHOR INPUT) Describe here briefly the supplementary datasets downloaded if applicable
 
Availability
------------
.. (AUTHOR INPUT) Are data open or restricted. Until what time does an embargo last
   (for GIPP experiments normally 4 years after the end of data acquisition)
 

Conclusions and recommendations
===============================

.. (AUTHOR INPUT) If a colleague were to do an experiment in the same or similar area, what
   recommendations would you make to maximise data recovery. Are there any other general lessons
   learned on deployment procedures or data pre-processing worth passing on to other users or the
   instrument pool.
 
   
Acknowledgments
===============

.. (AUTHOR INPUT) 


References
==========

.. Example: [RYBERG14] Trond Ryberg. Cube timing errors introduced by long periods without gps
   reception, 2014. URL http://www.gfz-potsdam.de/fileadmin/gfz/sec22/pdf_doc/GIPP/cube/Cube_timing_errors_no_gps.pdf .


.. end of the document content. Below figures and tables added by means of rst directives

.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. DIRECTIVES:
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. Rst "directives" are explicit markup blocks for generating special document objects, like
   figures and tables. They are in the form ".. directivetype::" and includes all subsequent
   INDENTED lines (see e.g. the ".. math::" directive above). A typical example to include a
   figure is:
   
   .. _figure-label:
   
   .. figure:: ./larch.png
      :width: 33%
      :align: center

      caption
   
   ".. _figure-label:" is the figure label, used to reference the figure via :numerf:`figure_label`
   - "./larch.png" is called the directive argument
   - ":width: 33%" and ":align: center" are directive options in the form :name: value
   - "caption" is called the directive content
   (For details, see http://docutils.sourceforge.net/docs/ref/rst/directives.html#figure)

   **IMPORTANT**:
   1. In the following, with "directive block" (or simply block) we will denote the directive AND
   its label (if any).
   2. A directive block must be always preceeded and followed by a blank line. Always.
   3. Only a blank line, not even comments, can be input between a label and
   its directive
   4. From within the web application only, NEVER edit:
      - file paths as they are relative to this document path on the server.
      - option names, as they might break the document build.
      Everything else (non-file argument, non-file content, option values) can be editable
   
   You can always delete / move / copy a directive BLOCK anywhere in the text.
   Non-standard Rst directives (i.e., implemented and working in this program only) are marked as
   (NonStandard) below


.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. CUSTOM DIRECTIVES (FIGURES AND TABLES)
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. 1) The first directive is the directive to display the stations information in a
   table. It's the so called 'csv-table' directive
   (http://docutils.sourceforge.net/docs/ref/rst/directives.html#id4):
   There are several ways to display tables in RsT. Curiously, none of them is free from drawbacks
   and limitations. Csv-tables have the advantage to be easily editable here.

.. first of all, we show the "raw" directive, which might comes handy to put
   html or latex specific commands: in this case we decrease the size of the table
   to avoid page horizontal overflow. Remove the directive or change '\scriptsize' if you need it.
   
.. raw:: latex

   \scriptsize
   
.. we use the tabularcolumns directive
   (http://www.sphinx-doc.org/en/latest/markup/misc.html#directive-tabularcolumns):
   this directive gives a “column spec” for the next table occurring in the source file.
   The spec is the second argument to the LaTeX tabulary package’s environment, although,
   sphinx might use different tabular environment:

.. tabularcolumns:: |@{\ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ \ }l@{\ \ }|


.. customize the table horizontal lines via the tabularrows directive (implemented in this
   project onyl, as of July 2017 it's not implemented in Sphinx) which applies to the next
   generated table (latex output only). You can remove the whole block to show all hlines
   (default in sphinx).
   The directive can have two options, 'hline-show' or 'hline-hide' (*either* one *or* the other)
   specifying the indices of the hlines to show/hide, separeted by spaces (first index is 0).
   You can also provide python slice notations in the format 'start:end' or 'start:end:step'
   (http://stackoverflow.com/questions/509211/explain-pythons-slice-notation).
   The command might not work in some edge cases (e.g. for tables spanning over multiple pages)
   as it is a hack around a poor sphinx implementation, and might
   need some trial-and-errors for working as expected.
   Here we want  to show the first (0) and the last (-1) hlines, and each fourth hline starting
   from the second one (1::4 which means indices 1,5,9,...)
   
.. tabularrows::
   :hline-show: 0 1::4 -1

.. finally, the table directive (preceeded by its label so you can reference it via
   :numref:`stations_table`). You can edit the
   directive content[1] or the directive argument[2], as any csv file.
   [1] To provide empty strings quote them like this: "".
   [2] Text can span over several lines (providing as always the correct indentation)
   
.. _stations_table:

.. csv-table:: Station table. Note that start and end times represent the maximum validity of the
   corresponding configurations, not the actual data availability or time in the field.
   Azi: Azimuth of north or '1' component.
   :delim: space
   :quote: "
   :header-rows: 1
   
   {{ stations_table.content|indent(3) }}

.. restore normal size in latex only:

.. raw:: latex

   \normalsize


.. ==============================================================================   

.. 2) The second directive below is the (NonStandard) directive to display the station map figure.
   The syntax is similar to the csv-table directive (ses above) BUT produces an image instead.
   After the label definition (so you can reference the map figure via
   :numref:`stations_figure`), in the directive you can edit the argument (the map caption, keep
   indentation for newlines), the content as any csv file, or the directive option **values** 
   to customize the map: a full documentation of all option names is in preparation, we tried to
   make them as much self-explanatory as possible

.. _stations_figure:

.. mapfigure:: Station distribution in experiment (red symbols). If present, white-filled symbols
   show permanent stations and other temporary experiments archived at EIDA or IRIS-DMC,
   whose activity period overlapped at least partially with the time of the experiment.
   If present, open symbols show station sites which were no longer active at the time
   of the experiment, e.g. prior temporary experiments.
   :header-rows: 1
   :align: center
   :delim: space
   :quote: "
   {% for opt_name in stations_map.options -%}
   :{{ opt_name }}: {{ stations_map.options[opt_name] | safe }}
   {% endfor %}
   {{ stations_map.content|indent(3)  }}


.. ==============================================================================   

.. 3) The third directive is the (NonStandard) directive 'gridfigure' to display the noise pdfs.
   The syntax is similar to the csv-table directive (see above) BUT produces a grid of images.
   Note that in latex this will be rendered with a longtable followed by an
   empty figure with only the caption inside. This is a workaround to produce something that
   looks like a figure spanning over several pages (if needed) BUT it might need some arrangment
   as the figure caption might be placed on a different page. Being a table and a figure, all
   figure + table options, as well as all figure + table latex pre-customization (e.g.
   'tabularcolumns', 'includegraphics') apply also to a 'gridfigure'

.. first issue a raw latex command (You can remove the lines if the layout does not need a clear
   page):

.. raw:: latex

   \clearpage
   
.. customize latex tabularcolumns:
   
.. tabularcolumns::  @{}c@{}c@{}c@{}

.. customize the includegraphics options (only for latex output) for the next figure or image
   found (in the former case, applies the includegraphics options to all images of the figure):
   
.. includegraphics:: trim=8 30 76 0,width=0.33\textwidth,clip

.. customize also horizontal lines when rendering to latex. As usual, remove the block below to
   show all hlines. The block is mainly used as another example of the use of python slice
   notations: "a:b" means "from a until b-1". If a is missing it default to zero, if b is missing
   it defaults to the index after the last element. Thus ":" means all elements and the directive
   below hides all hlines:

.. tabularrows::
   :hline-hide: :

.. finally, the gridfigure directive (preceeded by its label so you can reference it via
   :numref:`noise_pdfs_figure`). The directive argument is the figure caption, the directive
   content holds the auto-generated pdfs placed on the server in the :dir: option
   (**do not change it!!**)

.. _noise_pdfs_figure:

.. gridfigure:: Noise probability density functions for all stations for database holdings
   :dir: {{ noise_pdfs.dirpath | safe  }}
   :delim: space
   :align: center
   :header-rows: 1
   :errorsastext: yes

   {{ noise_pdfs.content|indent(3) }}
   

.. ==============================================================================   

.. 4) The fourth directive is the directive to display the instrumental uptimes.
   Depending on the number of files uploaded when generating this template, it's either a
   'figure' or a (NonStandard) 'gridfigure' directive, in any case it will be rendered as figure
   in html and latex).

.. customize the includegraphics options (only for latex output) for the next figure or image
   found (in the former case, applies the includegraphics options to all images of the figure):

{% if inst_uptimes.directive == 'gridfigure' -%}
.. includegraphics:: width=\textwidth
{% else -%}
.. includegraphics:: angle=-90,width=\textwidth
{% endif -%}

.. here the directive (preceeded by its label so you can reference it via
   :numerf:`inst_uptimes_figure`). Note that the directive type is dynamically auto generated:
   if it's a 'figure' type, you can change the directive content which is the figure
   caption. If it's a 'gridfigure' type, remember that the directive *argument*
   is the figure caption

.. _inst_uptimes_figure:

{% if inst_uptimes.directive == 'gridfigure' -%}
.. gridfigure:: Overview of uptimes of all stations generated with `obspy-scan`
   {% for opt_name in inst_uptimes.options -%}
   :{{ opt_name }}: {{ inst_uptimes.options[opt_name] | safe }}
   {% endfor -%}
   :align: center
   
   {{ inst_uptimes.content|indent(3)  }}
{% else -%}
.. figure:: {{ inst_uptimes.arg  }}
   {% for opt_name in inst_uptimes.options -%}
   :{{ opt_name }}: {{ inst_uptimes.options[opt_name] | safe }}
   {% endfor -%}
   :width: 100%
   :align: center
   
   Overview of uptimes of all stations generated with `obspy-scan`
{% endif %}


.. ==============================================================================   


..  RST syntax help
    ===============
    
    (delete this section when no longer needed / after completion of editing)
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. TEXT FORMATTING:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    This is an example of "normal" body text. It's not in a comment block.
    Remeber that indentation is a special RsT command and that newlines are actually not rendered
    (this is a newline and you shouldn't see any difference in html or latex)
    
    But you can type a new paragraph by adding an empty line above it (like in
    this case)
    
    .. italic can be rendered by wrapping text within two asterix, bold by wrapping
       text within two couples of asterix:
       
    *This is rendered in italic*, **this is rendered in bold**
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. HYPERLINKS:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Hyperlink (inline): simply type them: Urls are automatically recognized and linked:
    
    Hyperlink (inline): http://www.python.org/
    
    .. Hyperlink with substitution text: point to the same url as above but render 'Python' as text:
    
    Hyperlink with subsitution text: `Python <http://www.python.org/>`_
    
    .. Hyperlink with substitution text, if it has to be referenced more than once.
       Define the hyperlink as follows (note that the line below is NOT rendered but is NOT
       a comment):
       
    .. _Wikipedia: https://www.wikipedia.org/
    
    Hyperlinks with subsitution text referenced more than once: Wikipedia_, and again, Wikipedia_ 
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. TEXT SUBSTITUTIONS:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. When the a text is repeated many times throughout one or more documents,
       especially if it may need to change later
       (note that the line below is NOT rendered but is NOT a comment):
    
    .. |RsT| replace:: ReStructuredText
    
    Text substitution: |RsT|
    
    .. Note that by placing a backslash before a character, you render that character
       literally. E.g., concerning the text substitution just descirbed:
    
    |RsT| was obtained by typing \|RsT\|
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. MATH FORMULAE:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Inline math formulae, use :math:`...` or latext dollar sign with latex syntax inside
       (the latter is not standard rst, but is implemented in this report):
    
    Here an inline math expression: :math:`(\alpha > \beta)` = $(\alpha > \beta)$
    
    .. More complex math formulae, use ..math:: then new empty line and INDENTED text:
    
    Here a more complex math expression:
    
    .. math::
    
       n_{\mathrm{offset}} = \sum_{k=0}^{N-1} s_k n_k
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. FOOTNOTES:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Footnotes with manual numbering:
    
    .. [1] First footnote
    
    .. [2] Second footnote, note that
       newlines which must be indented
    
    Here a ref to the first footnote [1]_ and here to the second [2]_.
    
    .. Footnotes with auto numbering (newlines must be INDENTED of at least three spaces):
    
    .. [#] First footnote (autonumbered)
    
    .. [#] Second footnote (autonumbered), note that
       newlines which must be indented
    
    Here a ref to the first footnote [#]_ and here to the second [#]_.
    
    .. Footnotes with auto numbering, referenced more than once (newlines must be INDENTED of at
       least three spaces):
    
    .. [#firstnote] First footnote (autonumbered, referenced more than once)
    
    .. [#secondnote] Second footnote (autonumbered, referenced more than once), note that
       newlines which must be indented
    
    Here a ref to the first footnote [#firstnote]_, again [#firstnote]_ and here to the second [#secondnote]_.
    
    .. Footnotes with auto symbols. DEPRECATED: seems they are buggy in latex:
    
    .. [*] First footnote (autosymbol)
    
    .. [*] Second footnote (autosymbol), note that
       newlines which must be indented
    
    Here a ref to the first footnote [*]_, and here to the second [*]_.
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. CITATIONS:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Citations are identical to footnotes except that their labels
       must be case-insensitive single words of alphanumerics plus internal hyphens,
       underscores, and periods. No whitespace, no numeric only. E.g., CIT2002:
    
    .. [CIT2002] Deep India meets deep Asia: Lithospheric indentation, delamination and break-off
       under Pamir and Hindu Kush (Central Asia). http://doi.org/10.1016/j.epsl.2015.11.046
    
    Here a reference to a publication: [CIT2002]_. And here another reference to it ([CIT2002]_)
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. NUMERIC REFERENCES TO FIGURES AND TABLES:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Providing a label to a specific directive (e.g. figure, table, see below):
       .. _labelname
       you can reference it in the text with:
       :numref:`labelname`
       
       For instance, here you can reference the auto-generated figures and tables
       (more on this below, if you are interested)
    
    Here a reference to :numref:`stations_table`. Here a reference to :numref:`stations_figure`.
    Here a reference to :numref:`inst_uptimes_figure`. Here a reference to :numref:`noise_pdfs_figure`
       
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. LIST ITEMS:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. bullet lists (blank line before and after the list):
    
    - This is a bullet list.
    
    - Bullets can be "*", "+", or "-".
    
    .. enumerated lists (blank line before and after the list):
    
    1. This is an enumerated list.
    
    2. Enumerators may be arabic numbers, letters, or roman
       numerals.
       
    .. nested lists (blank lines are optional between items on the same level):
    
    * About RsT syntax:
    
      - https://pythonhosted.org/an_example_pypi`_project/sphinx.html#restructured-text-rest-resources
        (and links therein)
      - http://docutils.sourceforge.net/docs/user/rst/quickref.html
     
    * About Sphinx syntax (RsT with some commands added)
    
      - http://www.sphinx-doc.org/en/stable/rest.html#rst-primer
        
    **More detailed tutorials**:
    
    - About RsT syntax:
      
      + http://docutils.sourceforge.net/rst.html 
        
    - About Sphinx:
      
      + http://www.sphinx-doc.org/en/stable/markup/index.html#sphinxmarkup
