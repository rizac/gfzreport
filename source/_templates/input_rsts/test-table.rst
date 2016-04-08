=======================================
Testing tables, it's so bad!!
=======================================

Normal table.
Note the indentation (no directive found, so 
indentation is rendered)

   =====  =====
     A    not A and B
   =====  =====
   False  True
   True   False
   =====  =====
   
Same table with the table directive.
Inspect latex code to see the difference with
the previous one
NOTE: LEAVE A NEWLINE BEFORE EACH DIRECTIVE!
LEAVE A NEWLINE BEFORE EACH DIRECTIVE CONTENT (no options, content)

.. table:: Truth table for "not"

   =====  =====
     A    not A and B
   =====  =====
   False  True
   True   False
   =====  =====
   
Normal table with reference to :numref:`l1`
Inspect what is put in the latex file 

.. _l1:

   =====  =====
     A    not A and B
   =====  =====
   False  True
   True   False
   =====  =====
   
Same table with the table directive and reference :numref:`l2`

.. _l2:

.. table:: Truth table for "not"

   =====  =====
     A    not A and B
   =====  =====
   False  True
   True   False
   =====  =====

This is a csv table

.. csv-table:: data stations (FIXME: caption?)
   :file: ../test-data/source/stations_example.csv


This is a csv table with file and content specified
What happens?
.. csv-table:: data stations (FIXME: caption?)
   :file: ../test-data/source/stations_example.csv

   "if you see this content has been parsed" 5.5
   -0.1 "ok"
   
this is a long table

.. table::
   :class: longtable 

   +---------+------------+------------+----------+-------------------+
   | Station | Start gap  | End gap    | Gap days | Expected/max (ms) |
   +=========+============+============+==========+===================+
   | AM01    | 2013-11-25 | 2013-12-28 | 33       | 13/36             |
   +         +------------+------------+----------+-------------------+
   |         | 2014-01-13 | 2014-05-10 | 117      | unreliable        |
   +---------+------------+------------+----------+-------------------+
   | AM12    | 2013-11-23 | 2013-12-18 | 25       | 8/27              |
   +         +------------+------------+----------+-------------------+
   |         | 2014-01-28 | 2014-02-20 | 23       | 7/26              |
   +         +------------+------------+----------+-------------------+
   |         | 2014-02-20 | 2014-04-26 | 65       | unreliable        |
   +---------+------------+------------+----------+-------------------+
   | AM16A   | 2014-01-12 | 2014-02-11 | 30       | 16/40             |
   +---------+------------+------------+----------+-------------------+

   
this is a long table with reference to it: :numref:`l3`

.. _l3:

.. table::
   :class: longtable 

   +---------+------------+------------+----------+-------------------+
   | Station | Start gap  | End gap    | Gap days | Expected/max (ms) |
   +=========+============+============+==========+===================+
   | AM01    | 2013-11-25 | 2013-12-28 | 33       | 13/36             |
   +         +------------+------------+----------+-------------------+
   |         | 2014-01-13 | 2014-05-10 | 117      | unreliable        |
   +---------+------------+------------+----------+-------------------+
   | AM12    | 2013-11-23 | 2013-12-18 | 25       | 8/27              |
   +         +------------+------------+----------+-------------------+
   |         | 2014-01-28 | 2014-02-20 | 23       | 7/26              |
   +         +------------+------------+----------+-------------------+
   |         | 2014-02-20 | 2014-04-26 | 65       | unreliable        |
   +---------+------------+------------+----------+-------------------+
   | AM16A   | 2014-01-12 | 2014-02-11 | 30       | 16/40             |
   +---------+------------+------------+----------+-------------------+
   