==============================================================================================================
a very very long title for testing purposes and inspecting alignment problems, if any. Hopefully none is found
==============================================================================================================



:authors:

W.Smith, G.B.Simons

:revision:

1.1

:abstract:

an abstract here
  with newlines characters to test

:copyright:

This document has been placed in the public domain. You
          may do with it as you wish. You may copy, modify,
          redistribute, reattribute, sell, buy, rent, lease,
          destroy, or improve it, quote it at length, excerpt,
          incorporate, collate, fold, staple, or mutilate it, or do
          anything else to it that your or anyone else's heart
          desires.

-------
Network
-------

.. map-figure:: ../test-data/source/stations_example.csv
   :name_key: Name
   :lat_key: Lat
   :lon_key: Lon 
   :align: center
   
   here the network figure caption


--------
Stations
--------

.. csv-table:: 
   :file: ../test-data/source/stations_example.csv

-----------------
Data Availability
-----------------

.. figure:: ../test-data/source/2012_2014_2_time.pdf
   :align: center
   :width: 100%

   gps timing quality caption


-----
PDF's
-----

.. imgages-grid:: ../test-data/source/pdfs
   :columns: "_HHE*.pdf" _HHN*.pdf _HHZ*.pdf

--------
Appendix
--------

Here the appendix, here a
.. _link: http://www.python.org/
here a newline, again for testing
