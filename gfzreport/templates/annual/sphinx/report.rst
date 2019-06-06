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
   :Version: 0.1
   
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
   - version (AUTHOR INPUT): a version number to be printed in latex second page

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

:version: 1.0

:date: {{ year + 1 }}-03-01


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

:Authors: Angelo Strollo, Peter Evans, Winfried Hanka, Andres Heinloo, Susanne Hemmleb, Karl-Heinz Jäckel, Javier Quinteros, Joachim Saul, Riccardo Zaccarelli, Thomas Zieke and Frederik Tilmann.


.. the citation section. Write here how the user should cite this report, and/or how to cite
   any data related to this report, if needed. The text below will be rendered in the title back page in LaTeX.
   In principle, you might need to just change or re-arrange the text. For more experienced users,
   note the use of the custom role :doi-citation: where you can reference
   also an already defined bib. field before the title by wrapping the field name in "|", e.g. :doi-citation:`|doi|`.

:Citations: Recommended citation for the report:

            :doi-citation:`|doi|`

.. raw:: latex

   \tableofcontents
   \newpage



Executive summary
~~~~~~~~~~~~~~~~~




.. raw:: latex

   \newpage



Introduction
~~~~~~~~~~~~



The GEOFON global seismic network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



Regular maintenance 
<<<<<<<<<<<<<<<<<<<


.. customize the includegraphics options (only for latex output) for the next figure or image
   found (in the former case, applies the includegraphics options to all images of the figure):

.. .. includegraphics:: angle=90,width=1\textwidth


.. map directive. Customize as you want, you can reference it via :numerf:`map_ge_stations`


.. _map_ge_stations:

.. mapfigure:: GEOFON stations in {{ year }}. Colours denote the data availability (white: 0% to red: 100% availability). Symbols represent the level of maintenance needed: circle for “none”, square for “on site”, triangle (up) for “remote”, triangle (down) for “Remote including HW shipment”. An “X” next to the symbol indicates metadata updates.
   :header-rows: 1
   :align: center
   :delim: space
   :quote: "
   :map_fontweight: regular
   :map_mapmargins: 0.5deg, 0.5deg, 0.5deg, 0.5deg
   :map_labels_h_offset: 0.005
   :map_legend_borderaxespad: 1.5
   :map_arcgis_service: World_Street_Map
   :map_urlfail: ignore
   :map_labels_v_offset: 0
   :map_sizes: 50
   :map_meridians_linewidth: 1
   :map_legend_pos: bottom
   :map_arcgis_xpixels: 1500
   :map_parallels_linewidth: 1
   :map_fontcolor: k
   :map_maxmeridians: 5
   :map_figmargins: 1,2,9,0
   :map_legend_ncol: 2
   :map_maxparallels: 5

   {{ mapfigure_directive_content|indent(3) }}



Technical developments
<<<<<<<<<<<<<<<<<<<<<<



Technical support to other GFZ groups (e.g. Observatories)
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


Annexes
<<<<<<<


The GEOFON Data Centre
~~~~~~~~~~~~~~~~~~~~~~

Archive Service Delivery
<<<<<<<<<<<<<<<<<<<<<<<<<


.. figure archive_1. You can reference it via :numerf:`archive_1`


.. _archive_1:

.. figure:: {{ archive_1_path }}
   :width: 100%
   :align: center

   Data archived by year of acquisition.


.. figure archive_2. You can reference it via :numerf:`archive_2`


.. _archive_2:

.. figure:: {{ archive_2_path }}
   :width: 100%
   :align: center

   Cumulative size of the GEOFON archive.
  


Requests by method and by type.

.. NOTE: the csv-table below allows captions and more customization than simple tables,
   but does not require the cells of the table body to be vertically aligned: below,
   the cells are aligned only to visually help the editor

.. tabularcolumns:: |l|r|r|r|r|

.. csv-table:: Requests by method and by type
   :header-rows: 1
   :delim: ;
   :align: center

   Request method     ; Requests    ; Timewindows ; Volume ; Users
   fdsnws (external)  ;             ;             ;        ; 
   fdsnws (GFZ)       ;             ;             ;        ; 
   arclink (external) ;             ;             ;        ; 
   arclink (GFZ)      ;             ;             ;        ; 
   Total              ;             ;             ;        ;


.. figure archive_3. You can reference it via :numerf:`archive_3`

.. _archive_3:

.. figure:: {{ archive_3_path }}
   :width: 100%
   :align: center

   Number of distinct user IDs provided for fdsnws and/or arclink on each day in {{ year }}.


  

New networks (embargo period end reports or any other change)
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



Real-time data export via seedlink:
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



Service uptime
<<<<<<<<<<<<<<

.. tabularcolumns:: |l|c|c|

===================  =========  ============
Service               Up        Down/Problem
-------------------  ---------  ------------
WebDC                 99.825%	    0.175%
EIDA Master Table     94.864%       5.136%
fdsnws-dataselect     98.371%		1.629%
fdsnws-station        98.212%		1.789%
routingsvc            99.749%		0.251%
-------------------  ---------  ------------
geofon-proc           99.982%		0.018%
geofon (ping)         99.980%		0.020%
geofon (Web pages)    99.813%       0.187%
geofon (eqinfo)       99.163%		0.837%
geofon (Seedlink)     99.411%       0.589%
===================  =========  ============



GEOFON Rapid Earthquake Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. Following the trend from last year the Earthquake Information system has got less manual interaction and more automatic  solutions. 


Published earthquake locations and moment tensor solutions
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



.. figure eqinfo_1. Reference it throughout the document via :numref:`eqinfo_1`

.. _eqinfo_1:

.. figure:: {{ eqinfo_1_path }}
   :width: 100%
   :align: center

   Geographic distribution of the published events in 2018.


.. figure eqinfo_2. Reference it throughout the document via :numref:`eqinfo_1`

.. _eqinfo_2:

.. figure:: {{ eqinfo_2_path }}
   :width: 100%
   :align: center

   Geographic distribution of the published Moment Tensors solutions in 2018.


.. tabularcolumns:: |r|r|

.. csv-table:: Events by magnitude classes in {{ year }}
   :header-rows: 1
   :delim: ;
   :align: center

   Mag             ; Num. events
   :math:`\geq7.5` ; 
   :math:`\geq6.5` ;
   :math:`\geq5.5` ;
   :math:`\geq4.5` ;
   All             ;


Removed "Fake" events are usually characterized by unfavorable azimuthal station
coverage or even strongly clustered stations (IPOC, parts of Central Europe, Taiwan). 

.. The number of published fake events could be reduced significantly compared to previous years by introducing additional publication criteria such as the maximum "sum of the largest two azimuthal gaps".


.. tabularcolumns:: |l|r|r|r|

.. csv-table:: Event dissemination
   :header-rows: 1
   :delim: ;
   :align: center

   Events    ; No MT ; Has MT ; Total
   Published ;       ;        ; 
   Status A  ;       ;        ; 
   Status C  ;       ;        ; 
   Status M  ;       ;        ; 
   Removed   ;       ;        ; 


Event notification delays are shown in :numref:`eqinfo_3` and :numref:`eqinfo_4` .


.. figure eqinfo_3. Reference it throughout the document via :numref:`eqinfo_3`

.. _eqinfo_3:

.. figure:: {{ eqinfo_3_path }}
   :width: 100%
   :align: center

   Event publication (grey dots) and alert delay (big green and xxl red) vs. magnitude in {{ year }}. Alert delay for GEOFON events in {{ year }} resulting in SMS alerts. Magnit
   ude is the magnitude reported at the time of the alert. Also shown are events with only an automatic detection (status 'A'). Please note that numbers are incomplete due to hardware upgrade/migration during the year.


.. tabularcolumns:: |l|r|r|r|r|

.. csv-table:: Alerts issued by type for each quarter
   :header-rows: 1
   :delim: ;
   :align: center

   {{ year }}  ;  xxl  ;  big  ; Other ; All classes
   Q1    ;       ;       ;       ; 
   Q2    ;       ;       ;       ;  
   Q3    ;       ;       ;       ; 
   Q4    ;       ;       ;       ; 
   Total ;       ;       ;       ; 

The definitions of these alert types are:
 * 'xxl' events are those with magnitude larger than 6.5 worldwide, or larger than 5.5 in or near Europe, or 5.0 in central Europe.
 * 'big' events have magnitude above 5.5 in most of the world, or above 5.0 in the wider Europe/Mediterranean area and M>=4.5 in central Europe.
 *  the 'Other' category includes internal alerts and some regional notifications.
 

.. figure eqinfo_4. Reference it throughout the document via :numref:`eqinfo_4`

.. _eqinfo_4:

.. figure:: {{ eqinfo_4_path }}
   :width: 100%
   :align: center

   GEOFON alert delay vs. first automatic publication. Note irregular spacing of x-axis. Please note that numbers are incomplete due to hardware upgrade/migration during the year.


Impact of the GEOFON web pages
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


.. figure eqinfo_5. Reference it throughout the document via :numref:`eqinfo_5`

.. _eqinfo_5:

.. figure:: {{ eqinfo_5_path }}
   :width: 100%
   :align: center

   Daily distinct visitors to geofon.gfz-potsdam.de during 2016. Also shown is the magnitude of the *largest* event recorded on each day, when this exceeds 6.4. (The threshold for 'xxl' alerts is 6.5 in most of the world).


Ongoing cooperation with EMSC
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



Software development
~~~~~~~~~~~~~~~~~~~~



Impact, Outreach and Capacity Building
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




GEOFON running projects
~~~~~~~~~~~~~~~~~~~~~~~



Publications by GEOFON staff
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



GEOFON Team (Human Resources)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

======================= ======= ===== ======= ====== ========== ======== ================== 
 Name                   GE Net. GE DC EQ info GE op. Soft. Dev. Outreach Funding 
======================= ======= ===== ======= ====== ========== ======== ==================
Angelo Strollo          x       x     x       x                 x        GFZ
Thomas Zieke            x                                                GFZ     
Karl-Heinz Jäckel[*]    x                                                GFZ     
Javier Quinteros                x                    x          x        EOSC-hub/GDN/GFZ
Susanne Hemmmleb                x                                        GFZ 
Riccardo Zaccarelli[*]          x                    x                   EPOS-IP/GFZ
Joachim Saul[*]                 x     x              x          x        GFZ
Winfried Hanka[*]                     x                                  GFZ
Andres Heinloo          x       x     x       x      x                   GFZ
Peter Evans             x       x     x       x      x          x        GFZ
======================= ======= ===== ======= ====== ========== ======== ==================

[*] Not working full time for GEOFON.


GEOFON Advisory Committee Members
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dr. Florian Haslinger, Chair, ETH Zurich, Zurich,CH

Dr. Christian Bönnemann, BGR Hannover, D

Prof. Dr. Wolfgang Friederich, RU Bochum, Bochum, D

Prof. Dr. Thomas Meier,	CAU	Kiel, D

Prof. Dr. Max Wyss	International Centre for Earth Simulation, Geneva, CH

Dr. Jan Zednik,	GFU	Prague, CZ


Acknowledgements
~~~~~~~~~~~~~~~~


Appendices
~~~~~~~~~~

Probability Density Functions (PDF) for operational GEOFON stations 01.{{ year }} - 12.{{ year }}
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

The PDF displayed in this appendix have been calculated with PQLX
(reference to software version) only for the primary channels,
that is generally a Broad-Band sensor at 20 Hz.
Only operational stations during the year have been included,
stations that were offline for most of time are not included in this appendix

.. note that the :width: option is buggy (does not render the same in LaTex and HTML).
   The solution is to issue a includegraphics directive to force each column in the next
   `gridfigure` directive to be 33% (1/the number of columns)

.. includegraphics:: width=.33\textwidth

.. gridfigure:: GE Network PSDs ({{ year }})
   :dir: {{ pdfs_dir }}
   :delim: space
   :header-rows: 0
   :errorsastext: true

   {{ pdfs_directive_content|indent(3) }}


Annexes
~~~~~~~~

Summary of GE maintenance team activities
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


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
    
    Hyperlink with substitution text: point to the same url as above but display 'Python' in the built document:
    
    `Python <http://www.python.org/>`_
    
    Hyperlink with substitution text, if it has to be referenced more than once.
    Define the hyperlink as follows:
       
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
    
      - https://pythonhosted.org/an_example_pypi`_project/sphinx.html
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




