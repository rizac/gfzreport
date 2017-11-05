.. _gfzb: 

Gfzreport-build
===============

:package: gfzreport.sphinxbuild

:command line: `gfzreport build [options]`


It is basically a wrapper around :ref:`sphinxbuild`. 
You might ask why to re-invent the wheel. Well, because we needed a slightly different wheel.
In particular, we needed:

* A PDF builder callable by the python code: although :ref:`spx` claim that :ref:`sphinxbuild` can build
  PDF documents, well... no, you can't. As of mid 2016, when the :ref:`gfzr` project started,
  the available python extensions where buggy and with very poor flexibility
  compared to `pdflatex`
  
* need to add new `directives <http://www.sphinx-doc.org/en/1.5.2/extdev/tutorial.html>`_ and
  interpreted text roles to match requirements for the Network reports generated with :ref:`gfzt`

You can invoke :ref:`gfzb` by running

.. code-block:: bash
   
   gfzreport build [options]
   
Or type for help:


.. code-block:: bash
   
   gfzreport build --help


Overview of the package / directory structure
-----------------------------------------------

The main function is:


.. code-block:: python

   def run(sourcedir, outdir, build=_DEFAULT_BUILD_TYPE, *other_sphinxbuild_options)


located at:

.. code-block:: python
   
   gfzreport.sphinxbuild.core.__init__.py:run 


The functions does what :ref:`sphinxbuild` does, it just calls `pdflatex` after :ref:`sphinxbuild`
if `build='pdf'` and writes a custom log file (currently "__.gfzreport.__.log") in the
:ref:`builddir`. The log has normalized :ref:`spx` and `pdflatex` errors, both with the format:
".+?:[0-9]+:\\s*ERROR\\s*:.+".
Note that those errors do not prevent in most cases the creation of the document; thus, they might be
regarded as warnings, excepts that :ref:`spx` uses already the word 'WARNINGS' for other kind of
messages.
Nevertheless, they are useful especially in :ref:`gfzw` to show information to the users after
the build, in a formatted way (e.g., catch all error-like lines and show them in red)


Other packages are:

.. code-block:: python

   gfzreport.sphinxbuild.core.extensions
   
where we implemented the :ref:`rst` extensions for improving our markup syntax

.. code-block:: python

   gfzreport.sphinxbuild.core.writers
   
where we implemented the LaTex and HTML builders, i.e. the classes which render the document.
We needed this to patch some custom functionalities that are not configurable. Note that
if upgrading to newer :ref:`spx` versions (we use 1.5.1, as of October 2017 1.6.6 is the latest one)
we might probably look at the writers as, especially for LaTex, :ref:`spx` *is going* into a more
customizable direction and thus some patches might be useless (or buggy).

.. code-block:: python

   gfzreport.sphinxbuild.map
   
where we implemented the package creating a scatter map of stations (image, e.g. png). This is
used in one of our custom extensions

