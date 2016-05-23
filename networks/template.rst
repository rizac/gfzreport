# Title Data Report

.. Network report template. Please fill your custom text here below. This is a rst 
   (ReStructuredText) file, which is a markup text format. Please visit [href] or type [??] for
   a short introduction. For instance, note that this portion of text (".. " followed
   by indented text) is an rst comment and not rendered in any output format (html, latex, pdf).
   Note also that section titles are prepended with # symbols ("#" indicating the
   report title, "##" the chapter title and so on, see below): fyi, this is not actually standard rst
   but we introduced it here because it's easier to use

:authors: provide author names here, separated by commas. This is a so-called
   "rst bibliographic field" (RBF). Note that this line is indented to tell rst that we are still in
   the "authors" RBF. RBF will be available commands in latex output for generating the report.

.. Note on RBF: if you want to reference them within this document write e.g.: |authors|

:revision:

:strNum: 

:doi: 

:urn: 

:issn: 

:subtitle: 

:subsubtitle: 

:citationInfo:

:citation: 

:supplDdatasets: 

:citationchapter: 

:supplementsto: 

:abstract: write your abstract here, you can add newlines but you should indent any new line:
  like this (the number of characters is irrelevant, just be consistent for readibility)
  In general, remember that for rst indented text is considered to be part of a special section
  and thus rendered accordingly
 
## Introduction

Write your section text here if any, or remove these lines until next section
Note: do not indented text as is interpreted as rst command (depending on what you type).
Newlines are actually not rendered, indentation is not allowed unless

But you can type a new paragraph by adding an empty line (as we just did)

## Data Acquisition

Write your section text here if any, or remove this line

### Experimental Design and Schedule

Write your section text here if any, or remove this line

### Site Descriptions and Possible Noise Sources

Write your section text here if any, or remove this line

### Instrumentation

Write your section text here if any, or remove this line

## Instrument Properties and Data Processing

Write your section text here if any, or remove this line

## Data Description

Write your section text here if any, or remove this line

### Data Completeness

Write your section text here if any, or remove this line

### File Format

Write your section text here if any, or remove this line

### Data Content and Structure

Write your text here if any, or remove this line

## Data Quality and Timing Accuracy

Write your text here if any, or remove this line

### Noise Estimation

Write your text here if any, or remove this line

### Timing Accuracy

Write your text here if any, or remove this line

## Data Availability/Access
The data is archived at the GIPP Experiment and Data Archive where it will be made freely available
for further use on March 1, 2019 under a “Creatve Commons Atributon-ShareAlike 4.0 Internatonal
License” (CC BY-SA). When using the data, please give reference to this data publicaton. Recommended
citaton for this publicaton is:
Lot, F.; Al-Qaryout, M.; Corsmeier, U.; Riter, J. (2016): Dead Sea Seismic Array, Jordan for DESERVE Project (Feb. 2014 - Feb. 2015) - Report. Scien  c Technical Report STR16/01 - Data; GIPP Experiment- and Data Archive, GFZ German Research Centre for Geosciences, Potsdam, Germany.
DOI: htp://doi.org/10.2312/GFZ.b103-16011.
The DOI number of the supplementary data is: htp://doi.org/10.5880/GIPP.201310.1
STR 16/01 - Data. GFZ German Research Centre for Geosciences.
DOI: 10.2312/GFZ.b103-16011 2
   
## Acknowledgments

Write your text here if any, or remove this line

## References

Write your text here if any, or remove this line

.. here the stations figure (NOTE: this and all indented text below is a comment). To reference the
   figure, type anywhere in the text:
   :numref:`stations_figure`
   To place the figure elsewhere, move simply the all text below until the next comment block (including the last blank line)
   
.. _stations_figure:

.. map-figure:: {{ stations_csv_path }}
   :name_key: Name
   :lat_key: Lat
   :lon_key: Lon 
   :align: center
   
   Write here the stations figure caption, if any (or remove this line)

.. here the stations table (NOTE: this and all indented text below is a comment). To reference the
   table, type anywhere in the text:
   :numref:`stations_table`
   To place the table elsewhere, move simply the text below (including the following blank line)
   
.. _stations_table:

.. csv-table:: Write here the data stations caption, or remove this line EXCEPT the directive name (.. csv-table::)
   :file: {{ stations_csv_path }}
