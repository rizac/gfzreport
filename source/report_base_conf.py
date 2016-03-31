# -*- coding: utf-8 -*-

#
# reportgen configuration used when building the input rst file for sphinx report generation
#
# This file is execfile()d with a custom rst template to substitute variables in the latter with
# values provided here

import os
import sys

# you can add custom python variables here. To avoid conflicts, you can name them with a leading
# underscore to ignore them during parsing:
_PATH = os.path.abspath('../test-data/source')

# conventions (in order of importance): 
# 1) variables with a leading underscore will be ignored during parsing (see above)
# 2) variables ending with "_path" (case insensitive) will denote file names. In the current
# implementation this is important because the preprocess modifies them to make them relative to
# the source sphinx input directory
# 3) variables ending with "_text" or "_caption" will denote texts. This has no effect on the
# preprocess but might lead to modifications in the future. Use the triple quotation mark
# e.g. variable="""some text""" to input newlines without the need to escape them using '\n'

# the gfz logo (upper left corner of the document's first page). Empty string: do not include
gfz_logo_path = ''  # ./images/GFZ_Logo_SVG_klein_de.svg

# the gfz wordmark logo (upper right corner of the document's first page). Empty string: do not include
gfz_wordmark_path = ''  # ./images/GFZ_Wortmarke_SVG_klein_de.svg

# the title text (in the first page)
title_text = "a very very long title for testing purposes and inspecting alignment problems, if any. Hopefully none is found"

# authors (below the title). Use semicolon or commas to separate them. Leave empty to skip it
authors_text = "W.Smith, G.B.Simons"

# revision. Leave empty to skip it
revision_text = "1.1"

# whether to include the current date (below the authors). FIXME: not implemented!!!
# include_date = True

# The text for the copyright. Use the triple quotation mark """some text""" to input newlines
# without the need to escape them using '\n'. Leave empty to skip it
copyright_text = """This document has been placed in the public domain. You
          may do with it as you wish. You may copy, modify,
          redistribute, reattribute, sell, buy, rent, lease,
          destroy, or improve it, quote it at length, excerpt,
          incorporate, collate, fold, staple, or mutilate it, or do
          anything else to it that your or anyone else's heart
          desires."""

# The text for the abstract. Use the triple quotation mark """some text""" to input newlines
# without the need to escape them using '\n'. Leave empty to skip it
abstract_text = """an abstract here
  with newlines characters to test"""

# the path for the map. It is a csv file
network_map_csv_path = _PATH + "/stations_example.csv"

# The caption for the map above
network_map_caption = "here the network figure caption"

# The table of the stations to be included as csv
stations_table_csv_path = _PATH + "/stations_example.csv"

# The data availability image path
data_availability_img_path = _PATH + "/2012_2014_2_time.pdf"

# the data availability image caption
data_availability_img_caption = "gps timing quality caption"

# the timing quality image path
gps_timing_quality_img_path = ""  # "./test-data/2012_2014_2_time.pdf" # "FIXME: ask Angelo"

# the timing quality image caption
gps_timing_quality_img_caption = "gps timing quality caption"

# the pdfs (probability density function, not .pdf) images path
pdfs_path = _PATH + "/pdfs"

# the appendix text
appendix_text = """Here the appendix, here a
.. _link: http://www.python.org/
here a newline, again for testing"""

# other options. FIXME TODO add other options
# Grid with: E N Z
# look at generating map with python probably input as csv with lon and lat
# station list/table...  is the csv file above
# data avaliability is a jpeg (see ...time.pdf)
# gps timing quality ???