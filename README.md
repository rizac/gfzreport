# gfzreport
A sphinx-based report generation for use at gfz

## Installation

### Install a python virtual environment

See notes here

	* [python virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/
	
	* [python virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/index.html)
	
Activate the virtual environment (see notes above). 

#### Note: on Mac, you might have the following error while executing the web app:

```
RuntimeError: Python is not installed as a framework. The Mac OS X backend will not be able to function correctly if Python is not installed as a framework. See the Python documentation for more information on installing Python as a framework on Mac OS X. Please either reinstall Python as a framework, or try one of the other backends. If you are Working with Matplotlib in a virtual enviroment see 'Working with Matplotlib in Virtual environments' in the Matplotlib FAQ
```

You can edit the [matplotlibrc file](http://matplotlib.org/users/customizing.html#the-matplotlibrc-file)
in your virtual environment, which you can also locate by typing 
```
python -c "import matplotlib;print matplotlib.matplotlib_fname()"
```
in the terminal. Then open it, locate the line `backend: ...`. Replace it with (or add the following if no such line was found):

```
backend: Agg
```

(To avoid coupling between code and configuration, we removed the matplotlibrc that was previously shipped
with this program)

### Install this python package

Download the reportgen git repository in a local folder, cd into it and install this package:


```pip install -r ./requirements.txt```

(or if you want to install also test packages `pip install -r ./requirements.dev.txt`)

and then:

```pip install .``` (with -e option as editable, if desired)

Now you should have all python packages installed, *except* [basemap](https://github.com/matplotlib/basemap) (python library to plot on map projections with	coastlines and political boundaries using matplotlib):

(Note, for problems installing the required python package `lxml`, `libxml2-dev libxslt-dev` are
required (see here: http://lxml.de/installation.html)

### Install basemap and dependencies

According to [basemap requirements](https://github.com/matplotlib/basemap#requirements): you should first make sure, if your python was installed via a package management system, that the corresponding "python-dev" package is also installed. Otherwise, you may not have the python header (Python.h), which is required to build python C extensions<sup>[1](#basemap_installation_notes)</sup>.

  1. Download basemap-1.0.7.tar.gz (*approx 100 mb*) from [here (see source code links in the page)](https://github.com/matplotlib/basemap/releases/tag/v1.0.7rel), unpack and cd to basemap-1.0.7:

  ```
  > cd <where you downloaded basemap basemap-1.0.7rel.tar.gz>
  > tar -zxvf basemap-1.0.7rel.tar.gz
  > cd basemap-1.0.7
  ```

  2. Install the GEOS library.  If you already have it on your system, just set the environment variable GEOS_DIR to point to the location of libgeos_c and geos_c.h (if libgeos_c is in /usr/local/lib and geos_c.h is in /usr/local/include, set GEOS_DIR to /usr/local):
  ```
  > export GEOS_DIR=<location of GEOS directory>
  ```
  Then go to next step.
  
  If you don't have it, you can build it from the source code included with basemap by following these steps:
  ```
  > cd geos-3.3.3
  > export GEOS_DIR=<where you want the libs and headers to go>
    A reasonable choice on a Unix-like system is /usr/local, or
    if you don't have permission to write there, your home directory.
  > ./configure --prefix=$GEOS_DIR 
  > make; make install
  ```

  3. cd back to the top level basemap directory (basemap-X.Y.Z) and run the usual 'python setup.py install'.  Check your installation by running "from mpl_toolkits.basemap import Basemap" at the python prompt.
	
  4. To test, cd to the examples directory and run 'python simpletest.py'. To run all the examples (except those that have extra dependencies or require an internet connection), execute 'python run_all.py'.
   
### Install tex packages

#### Ubuntu

Tex packages are required to run pdflatex for generating pdf output (we found it more robust and flexible than python sphinx plugins):

```
sudo apt-get install texlive-latex-base texlive-bibtex-extra texlive-latex-extra texlive-fonts-extra texlive-fonts-recommended texlive-humanities texlive-publishers
```

#### Mac OsX

Installation of latex in Mac is quite complex compared to Ubuntu, you have two choices:

  1. Install [MacTex](http://www.tug.org/mactex/index.html) (either on the link provided or
  via `brew cask install mactex`). This is by far the recommended way, although it might take times (gigabytes to be downloaded)

  2. Install BasicTex via homwbrew which is more lightweight:
  ```
    brew install basictex tex-live-utility
    tlmgr install install basictex
  ```
  and then install texlive utilities (but we cannot assure these are sufficient, therefore we discourage this installation procedure as it is up to the user to keep
  things updated. If a package is missing, then the report generation will fail with unreported missing packages)
  ```
    sudo tlmgr install collection-fontsrecommended titlesec fncychap tabulary framed threeparttable wrapfig capt-of needspace multirow eqparbox varwidth environ trimspaces
  ```

  Useful links:
   - [installing fontsrecommended in mac os](http://tex.stackexchange.com/questions/160176/usepackagescaledhelvet-fails-on-mac-with-basictex),
   - [installing latex on linux and mac os](https://docs.typo3.org/typo3cms/extensions/sphinx/AdministratorManual/RenderingPdf/InstallingLaTeXLinux.html))

---

<a name="basemap_installation_notes">1</a>: <sub>We skipped some of the basemap requirements ([pyproj](https://github.com/jswhit/pyproj) and [pyshp](https://github.com/GeospatialPython/pyshp)) as they do not seem to be mandatory for this program to run (keep it in mind in case of troubles though). Moreover, note that there are two optional packages which might be useful if you mean to use basemap outside this program:

  * <sub>[OWSLib](https://github.com/geopython/OWSLib) (optional) It is needed for the BaseMap.wmsimage function.</sub>

  * <sub>[Pillow](https://python-pillow.github.io/) (optional)  It is needed for Basemap warpimage, bluemarble, shadedrelief, and etop methods. PIL should work on Python 2.x.  Pillow is a maintained fork of PIL.</sub>
