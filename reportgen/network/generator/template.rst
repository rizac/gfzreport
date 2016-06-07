.. Network report template. Please fill your custom text here below. This is a RsT 
   (ReStructuredText) file and also a comprehensive tutorial which might help you during editing.
   RsT is a lightweight markup language designed to be both
   (a) processable by documentation-processing software to produce html, latex or pdf output, and
   (b) easily readable and editable by human interaction.
   As already mentioned, you might just need to simply follow the instructions here. For a more detailed explanation
   about rst syntax, please visit [href] or type [??] for
   Note that this portion of text (".. " followed by INDENTED text) is an comment and will NOT be
   rendered in any output format (html, latex, pdf).

.. Section titles (like the one below, which is the document title) are recognized if
   decorated with under- (and optionally over-) line characters WHICH MUST BE AT LEAST AS LONG AS
   the section title length. There is no rule about decoration characters. Just be consistent (same
   decoration for sections of the same "level"). Section titles cannot span over multi-lines.

=============================================================
Report title here (on a single line, like ALL SECTION TITLES)
=============================================================

.. Here below the so-called "rst fields" (authors, revision, etcetera) in the form
   :fieldname: fieldvalue. 
   fieldvalue is a string which can span over several new lines, as long as they are INDENTED.
   In the reportgen program, these fields will be automatically rendered in special portions of the text
   (in latex), you have only to fill the text if you know its value (e.g., the DOI), or leave it empty.
   You can think of them as kind of parameters included here for simplicity, not as parts of rendered 
   text. Moreover, the reportgen program allows you to type the field value corresponding to a
   field name (e.g., authors), using the filedname between two "|" characters, e.g.
   |authors| will be replaced by the text you provide below for the authors field.
   
:authors: provide author names here, separated by commas.

:revision: 1.1 or whatever you want (a revision mechanism is not currently implemented)

:strNum: the str num

:doi: the doi number. Given a doi (e.g. A/B) you can write it here in the following formats:
      A/B
      http://www.doi.org/A/B
      DOI: A/B
      DOI: http://www.doi.org/A/B

:urn: type the urn here. IMPORTANT: to type semicolon, use "\:" instead of ":", so write e.g. abc\:cde\:def
      (techincally, escape semicolon with a slash) because as you can see semicolons are special characters in rst fields

:issn: type the issn here

:subtitle: subtitle. Will be appended below the title above

:subsubtitle: sub-subtitle. Will be appended below the subtitle above

:citationInfo: citation info

:citation: citation (FIXME: remove??)

:supplDdatasets: supplementary dataset (if any)

:citationchapter: citation chapter (if nay)

:supplementsto: supplements to

:abstract: write your abstract here, you can add newlines but you should indent any new line:
  like this (respect the same indentation but just for readibility, it's not mandatory)
  In general, remember that for rst indented text is considered to be part of a special section
  and thus rendered accordingly

.. From here on, you can start typing "body text" anywhere you want by simply writing NON-INDENTED text
   which is not a comment (like this one)

Introduction
============

This is an example of "normal" body text. It's not in a comment block so that you might try to build
this document and see the rendered results of the commands explained in the following.
Most certainly, you'll need to remove this text sooner or later.
Remeber that indentation is a special rst command and that newlines are actually not rendered (this
is a newline for instance)

But you can type a new paragraph by adding an empty line above it (like in this case)

Most commonly used commands:

*italic* words are wrapped in two aterixs, **bold** words in two double-asterixs.

References / Hyperlinks / Labels
--------------------------------

General rule: an underscore in front of text denotes a LABEL, an underscore at the end denotes
a REFERENCE (to a given label, an url, a section title, etcetera...)

Reference to figures, providing a label (see at the bottom for the relative labels)
To figures or tables, first write

   .. _label::
   
   this text is labelled

and then reference it with :numref:`label`
See for instance :numref:`stations_table` (see at the bottom for the relative labels)

Hyperlinks:

Inline urls are automatically linked, like: http://www.python.org/

Inline urls with subsitution text (e.g., show Python instead of the address), simply
write `Python <http://www.python.org/>`_

References to urls (hrefs), not inline, write Python_. Providing that you wrote somewhere:

.. _Python: http://www.python.org/


Substitutions are the same except that there is no hyperlinke, the text is simply replaced

.. |RsT| replace:: ReStructuredText

Now you should see "ReStructuredText": this is |RsT|. Remeber that, for this program *only*, also 
fields defined above behaves assusbtitutions, so you can type here the doi as  |doi|, and the text
in \|doi\| should be rplace with the value of the doi field specified above.

Math formulae can be typed in two ways. Either inline like this: :math:`\alpha > \beta` or, for more
complex expressions:

.. math::

    n_{\mathrm{offset}} = \sum_{k=0}^{N-1} s_k n_k

We implemented for this program also a third variant with dollar sign (as in latex), which will default to 
the \:math\: command above. So these expressions should be the same:  :math:`(\alpha > \beta)` and $(\alpha > \beta)$

Footnotes (autonumbering):
  
.. [#] First footnote, should be numbered as 1

.. [#] First footnote, should be numbered as 2

Here a ref to the first footnote [#]_ and here to the second [#]_.

Footnotes (autonsymbols). DEPRECATED: It has a  bad rendering in Latex (if you are looking a latex build look by yourself):
  
.. [*] First footnote, should use the "first" autogenerated symbol

.. [*] First footnote, should use the "second" autogenerated symbol

Here a ref to the first footnote [*]_ and here to the second [*]_.


Citation. Define the citation:

.. [CIT2002] Deep India meets deep Asia: Lithospheric indentation, delamination and break-off under
   Pamir and Hindu Kush (Central Asia). http://doi.org/10.1016/j.epsl.2015.11.046

And then you can reference it like this: [CIT2002]_. And here another referrence to it ([CIT2002]_)

External links (Note the following will be rendered as a list):
  # Quick tutorials:
    * About RsT syntax:
      * https://pythonhosted.org/an_example_pypi_project/sphinx.html#restructured-text-rest-resources (and links therein)
      * http://docutils.sourceforge.net/docs/user/rst/quickref.html
    * About Sphinx syntax (RsT with some commands added)
      * http://www.sphinx-doc.org/en/stable/rest.html#rst-primer
  # More detailed tutorials:
    * About RsT syntax:
      * http://docutils.sourceforge.net/rst.html 
    * About Sphinx:
      * http://www.sphinx-doc.org/en/stable/markup/index.html#sphinxmarkup

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

Write your text here if any, or remove this line

.. We place in the bottom of the document (see below) the so-called rst "directives". 
   Basically, directives are the way to tell rst to include objects such as figures and tables:
   Directives begin with an explicit markup start (two periods and a space), followed by the
   directive type, two colons and a whitespace (collectively, the "directive marker").
   Example of typical directive marker (.. image:: ) which includes the image mylogo.jpeg:

   .. image:: mylogo.jpeg
   
   Two colons are used after the directive type for several reasons, the first of which is distinguish
   comment blocks (like e.g., this one) and directives.

   The directive block begins immediately after the directive marker, and includes all subsequent
   indented lines. The directive block is divided into arguments, options (a field list),
   and content (in that order), any of which may appear.
   For instance to include a figure displaying the file ./larch.png with caption "abc" and width
   equal to 33% of its container (usually, the page width) type:
   
   .. figure:: ./larch.png
      :width: 33%

      abc
    
   in the example above, the directive argument is './larch.png', the only directive option is 'width', and the
   directive content is represented by its caption ('abc').

   Important notes:
   ---------------

   a) all relative paths in the document (like ./larch.png) are relative to this file.
   Absolute paths are discouraged especially because it seems that sphinx (the python program on top of which we
   generate thie report) is quite confusing and not consistent in that case
   
   b) you can move a directive anywhere in the text by copying and pasting the directive marker and
   its block (including the last blank line) anywhere in the text. Any object returned by a directive
   (figures, tables,...) is in principle displayed where they appear here

   c) You can reference directives (e.g., figures, tables) by placing IMMEDIATELY BEFORE the directive
   the reference label. The label begins with an explicit markup start
   (two periods and a space), followed by an underscore, the label name, and a semicolon. E.g:
   
   .. _myreflabel:
   
   The directive can thus be referenced anywhere in the text by typing:
   :numref:`myreflabel`
   and will be properly rendered in both latex, pdf or html. See examples in the directives implemented
   below
   
   
.. 1) The first directive is the directive to display the stations information in a table. It's the
   so called 'csv-table' directive (http://docutils.sourceforge.net/docs/ref/rst/directives.html#id4):
   There are several ways to display tables, the csv-table has the advantage that it can
   be more easily edited.
   Note in this case the presence of a first directive, tabularcolumns
   (http://www.sphinx-doc.org/en/latest/markup/misc.html#directive-tabularcolumns): this directive
   gives a “column spec” for the next table occurring in the source file. The spec is the second argument
   to the LaTeX tabulary package’s environment (which Sphinx uses to translate tables):

.. raw:: latex

   \small

.. tabularcolumns:: |lllllllllllll|

.. _stations_table:

.. csv-table:: This is the table caption, if any (otherwise, or remove this line EXCEPT the directive marker)
   :delim: ,
   :quote: "
   :header-rows: 1
   
   {{ stations_table_csv_content|indent(3) }}

.. raw:: latex

   \normalsize

.. 2) The second directive below is the directive to display the station map figure. It is a non-standard
   directive implemented in this program only, whose syntax is similar to the csv-table directive
   (ses above) BUT produces an image instead.
   In principle, there is no need to modify the directive argument (the path to the csv file whose
   data needs to be plotted), but you can edit the csv file in an editor like Excel (c) or LibreOffice
   
   As described above, first there is the directive label (which you can reference by typing
   :numref:`stations_figure`
   anywhere in the text, then its body, and eventually its caption:

.. _stations_figure:

.. map-figure:: This is the figure caption, if any (otherwise, or remove this line EXCEPT the directive marker) 
   :align: center
   :delim: ,
   :quote: "
   
   {{ stations_map_csv_content|indent(3)  }}

.. 3) The third directive is the directive to display the data availability and instrumental uptimes. 
   They are the so-called 'figure' directives (http://docutils.sourceforge.net/docs/ref/rst/directives.html#figure).
   Note that, contrarily to the csv-table directive, the directive argument is the file path of the
   figure (we suggest to use relative path, relative to this file), and the directive content is the
   figure caption

.. _data_aval_figure:

.. figure:: {{ data_aval_fig_path }}
   :align: center
   :width: 100%

   This is the figure caption (remove this line to hide caption)
   
.. _instr_uptimes_figure:

.. figure:: {{ instr_uptimes_fig_path }}
   :align: center
   :width: 100%

   This is the figure caption (remove this line to hide caption)

.. 4) The fourth directive is the directive to display the noise pdfs. It is a non-standard
   directive implemented in this program only, whose syntax is similar to the figure directive
   (ses above) BUT produces an grid of images.
   Note also in this case the presence of a first directive, tabularcolumns. Tou might ask why we
   need it as the output is a figure. The reason is that in latex this directive is rendered as
   a longtable "wrapped" into a figure element
   Note also the option 'latex-custom-graphics-opt' which customizes, if needed, the argument to each
   image inside the grid

.. raw:: latex

   \clearpage

.. tabularcolumns:: ccc
   
.. _noise_pdfs_figure:

.. images-grid:: {{ noise_pdfs_fig_path }}
   :columns: "_HHE*.png" _HHN*.png _HHZ*.png
   :header-labels: **A** B C
   :latex-custom-graphics-opt: trim=8 30 76 0,width=0.33\textwidth,clip

   here the grid caption. Remember to keep an empty line before this line


   