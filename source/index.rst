# ZE 2012-2014 Madagascar Seismic Profile


:authors: F.Tilmann, X. Yuan, G. Rümpker, Elisa Rindraharisaona

:revision: 1.1

:abstract: The island of Madagascar occupies a key region in both the assembly and the multi-stage
 breakup of Gondwanaland, itself part of the super-continent Pangaea. Madagascar consists of an
 amalgamation of continental material, with the oldest rocks being of Archaean age. Its ancient
 fabric is characterised by several shear zones, some of them running oblique to the N-S trend,
 in particular in the south of the island. More recently during the Neogene, moderate volcanism
 has occurred in the Central and Northern part of the island, and there are indications of uplift
 throughout Eastern Madagascar over the last 10 Ma. Although Madagascar is now located within
 the interior of the African plate and far away from major plate boundaries (>1000 km from the
 East African rift system and even further from the Central and South-West Indian Ridges), its
 seismic activity indicates that some deformation is taking place, and present-day kinematic models
 based on geodetic data and earthquake moment tensors in the global catalogues identify a
 diffuse N-S-oriented minor boundary separating two microplates, which appears to pass through
 Madagascar. In spite of the presence of Archaean and Proterozoic rocks continent-wide scale studies
 indicate a thin lithosphere (<120 km) throughout Madagascar, but are based on sparse data
 and cannot resolve the difference between eastern and western Madagascar. We have operated an
 ENE-WSW oriented linear array of 25 broadband stations in southern Madagascar, extending from
 coast to coast and sampling the sedimentary basins in the west as well as the metamorphic rocks
 in the East, cutting geological boundaries seen at the surface at high angle. The array crosses the
 prominent Bongolava-Ranotsara shear zone which is thought to have been formed during Gondwanaland
 assembly. The array recorded the magnitude 5.3 earthquake of January 25, 2013 which
 occurred just off its western edge. In addition, in May 2013 we have deployed 25 short period sensors
 in the eastern part of the study area, where there is some so-far poorly characterised seismicity.


## Data acquisition

### Experiment design

**Basic Design** The station distribution is shown in :numref:`stations_figure` and 
:numref:`stations_table` summarises the most important information about each station.
Three different types of instruments were used in this experiment. The main profile had a nominal
average station spacing of 17 km and was equipped EDL dataloggers and mostly CMG-3ESPs sensors.
A few Trillium 240s were approximately equally spaced throughout the array. The power to these
stations was supplied by solar panels. The permanent GEOFON station VOI forms an integral part
of the array, and no temporary station was deployed in the immediate neighbourhood.
The areal array comprises Cube data loggers and Mark L4C 1 Hz sensors. These stations ran off
batteries without recharging.

.. _stations_figure:

.. map-figure:: ../test-data/source/stations_example.csv
   :name_key: Name
   :lat_key: Lat
   :lon_key: Lon 
   :align: center
   
   here the network figure caption

.. _stations_table:

.. csv-table:: 
   :file: ../test-data/source/stations_example.csv

**Sensor orientation** All stations were oriented along magnetic north. The declination at the location
of station MS13 approximately at the centre of the array at the time of deployment (May 11, 2012) was
19°19' W, changing by 1'/year in west direction) (Source: http://www.ngdc.noaa.gov/geomag-web/
#declination). The azimuth of the nominal North components is thus ∼ 341°. This value is recorded
in the station metadata information in the GEOFON database; the variation of the magnetic field
through Madagascar has not been taken into account, though, but should be small compared to the
random orientation error.


## Data pre-processing

The Cube data were converted to miniseed format using the c2m code written by Trond Ryberg 1 [X].
This code interpolates linearly between the raw data samples in order to ensure an even sampling rate
of the output file. It assumes a linear drift between GPS fixes, when GPS reception is temporarily
lost.


## Data Quality

An overview of instrument uptimes is given in :numref:`timing_accuracy` and the noise levels for all stations and components
are shown in :numref:`pdfs-images`.

.. _pdfs-images:

.. imgages-grid:: ../test-data/source/pdfs
   :columns: "_HHE*.pdf" _HHN*.pdf _HHZ*.pdf

### Data recovery

A relatively large amount of data was lost due to vandalism ranging from loss of power because of
theft of the solar panels due to complete loss of data loggers. Some data was lost to technical issues,
probably related to high humidity at selected station sites. A recurring problem were GPS gaps at a
few of the Cube stations.
The security issues made it necessary to relocate some of the stations (MS06 and MS18, MS25
and AM16) and change the sensor type mid-experiment at some others (MS01, MS02, MS03, MS17,
MS25).

### Timing accuracy

An overview of the timing accuracy is given for the broadband stations in :numref:`timing_accuracy`.
In spite of a large number of gaps without GPS for station MS09, MS24 and other stations, particularly in 2014, the
timing is thought to be correct for this station for standard seismological purposes.
However, based on inspections of the symmetry of the noise-correlation day stacks, the timing for
station MS05 was found to be off by 60 s between 02/10/2012 and 05/02/2013, such that the indicated
time is delayed with respect to the real time (equivalently seismic traces are apparently shifted to

.. _timing_accuracy:

.. figure:: ../test-data/source/2012_2014_2_time.pdf
   :align: center
   :width: 100%

   gps timing quality caption

earlier time). Data recorded in the period from 12/07/2012 to 29/09/2012 and from 06/02/2013 to
28/04/2013 only showed noise with no discernible seismic signals or ambient displacement noise. There
is no indication in the log files of any problem. Such errant behaviour in the EDL is rare but a known
phenomenon (T. Ryberg, pers. comm.). The timing of data in the GEOFON database was corrected
for the indicated time period and the bad data removed but it still appears on the noise power density
plots for station MS05 (:numref:`pdfs-images`).
The following short period stations had no GPS at the time of service, and last GPS fix was more
than 2 days in the past. The time after the last GPS fix cannot be corrected, and absolute timing
information should not be used between the last fix and indicated station service time; expected daily
drift is up to ∼ 10 ms/day [Ryberg, 2014]. [X]

======= ========== ==========
Station Last fix   Service
======= ========== ==========
AM04    2013-05-09 2013-11-02
AM11    2013-10-26 2013-10-31
AM12    2013-10-27 2013-11-01
AM17    2013-10-30 2013-11-05
AM20    2014-01-01 2014-05-15
MS25A   2013-05-10 2013-09-13
======= ========== ==========

The following short period stations had gaps in excess of 20 days, but a linear correction through the
gap could be carried out. Timing errors will be largest in the centre of the gap. The values given
in the last column represent these expected and maximum ‘largest errors’ based on the statistical
distribution of cube sensors during an experiment in Namibia [Ryberg, 2014] [X]. Gaps shorter than 20
days had expected errors of 5 ms and errors never exceeded 20 ms. No data exist on the likely timing
errors beyond 40 days. Actual errors encountered in the Madagascar experiment might differ.

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


## Aknowledgments

We thank Prof. G´erard Rambolamana (Institute and Observatory of Geophysics in Antananarivo
- IOGA) for supporting this initiative and letting us use storage space at the institute and Mirana
Rakotoarisoa for various support in particular related to shipping and custom clearance. Andriamiranto
Raveloson helped to set up this collaboration and helped with the organisation. Martina
Gassenmeier, Michael Gummert, Ben Heit, Miriam Reiss, Felix Schneider, Ingo W¨olbern, Rasoanaivo
Christo, Rabeatoandro Johnson, and Andrianaivoarisoa Jean Bernardo are thanked for supporting
the fieldwork. We also thank landowners in Madagascar for hosting our stations, and the Isalo Ranch
lodge for providing intermediate storage space.
The funding for this experiment was provided by the expedition fund of the GFZ. Analysis of the
data is funded by the DFG. The data are additionally being used in the context of a DAAD sponsored
postdoctoral fellowhip to one of us (E. R.). Most of the instrumentation was provided by the GIPP
(Geophysical Instrument Pool Potsdam); the University of Potsdam loaned us solar panels.

TODO: bib citations, footnotes, abstract (both html and latex)
