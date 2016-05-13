# gfz-reportgen
A sphinx-based report generation for use at gfz

## Installation

a. Install numpy first:
	
	```
	pip install numpy
	```

b. Then download the git repo, cd into it and install this package:
	
	```
	pip install .
	```

	Now you should have all python packages installed, *except* 
	[basemap](https://github.com/matplotlib/basemap) (python library to plot on map projections with
	coastlines and political boundaries using matplotlib):

c. Install basemap and dependencies (if something goes wrong, see point d. below)

	Along the lines of the [basemap requirements](https://github.com/matplotlib/basemap#requirements),
	we already have at this point Python 2.6 (or higher), matplotlib, numpy and GEOS. Note that
	
	0. On linux, if your python was installed via a package management system, make sure the
	corresponding "python-dev" package is also installed.  Otherwise, you may not have the python
	header (Python.h), which is required to build python C extensions.
	Note also that [pyproj](https://github.com/jswhit/pyproj) and [pyshp](https://github.com/GeospatialPython/pyshp)
	are required, but they do not seem to be mandatory for this program to run (keep it in mind
	in case of troubles though)

	1. Download basemap-1.0.7.tar.gz (*approx 100 mb*) from [here (see source code links in the page)](https://github.com/matplotlib/basemap/releases/tag/v1.0.7rel), unpack and cd to basemap-1.0.7:

	```
	 > cd <where you downloaded basemap basemap-1.0.7rel.tar.gz>
	 > tar -zxvf basemap-1.0.7rel.tar.gz
	 > cd basemap-1.0.7
	```

	2. Install the GEOS library.  If you already have it on your system, just set the
	environment variable GEOS_DIR to point to the location of libgeos_c and geos_c.h
	(if libgeos_c is in /usr/local/lib and geos_c.h is in /usr/local/include, set GEOS_DIR to
	/usr/local). Then go to step (3). 
	If you don't have it, you can build it from the source code included with basemap by
	following these steps:

	```
	 > cd geos-3.3.3
	 > export GEOS_DIR=<where you want the libs and headers to go>
	   A reasonable choice on a Unix-like system is /usr/local, or
	   if you don't have permission to write there, your home directory.
	 > ./configure --prefix=$GEOS_DIR 
	 > make; make install
	```

	3. cd back to the top level basemap directory (basemap-X.Y.Z) and
	run the usual 'python setup.py install'.  Check your installation
	by running "from mpl_toolkits.basemap import Basemap" at the python
	prompt.
	
	4. To test, cd to the examples directory and run 'python simpletest.py'.
	To run all the examples (except those that have extra dependencies
	or require an internet connection), execute 'python run_all.py'.

4. Notes: In case something goes wrong you can follow the complete (or if you want to know what might be also optionally installed).
The requirements displayed in the basemap main page and in several links (supposing those
links didn't do I simple copy and paste without testing, which I suspect...) apart from Python 2.6
(or higher), matplotlib, numpy and GEOS (all already installed, see above)

* [pyproj](https://github.com/jswhit/pyproj)

* [pyshp](https://github.com/GeospatialPython/pyshp)


* 



###Optional

* [OWSLib](https://github.com/geopython/OWSLib) (optional) It is needed
for the BaseMap.wmsimage function.

* [Pillow](https://python-pillow.github.io/) (optional)  It is
needed for Basemap warpimage, bluemarble, shadedrelief, and etop methods.
PIL should work on Python 2.x.  Pillow is a maintained fork of PIL.
	

-----------------------


<!--- FIXME: do we need to setup postactivate in virtualenv? seems not so. Moreover, we do NOT need the following:
   pyproj pyshp -->

-----------

