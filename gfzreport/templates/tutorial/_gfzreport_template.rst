.. _gfzt:

gfzreport-template
==================

:package: ``gfzreport.templates``

:command line: ``gfzreport template [template_type] [options]``

:command line help: ``gfzreport template --help``

:command line help (specific template type, e.g. ``n``): ``gfzreport template n --help``


:ref:`gfzr` can generate templates. A template is basically a :ref:`srcdir` with data and a
a pre-filled :ref:`rst` (called :ref:`masterdoc`) to be edited. After editing, the :ref:`srcdir`
can be built as usual by means of :ref:`gfzb` to create a |html| / |latex| / |pdf| version of :ref:`masterdoc`.

The creation of a template can be invoked from the command line by typing:

.. code-block:: bash

   gfzreport template [TYPE] [options]

Where [TYPE] is a letter denoting, as of November 2017, the only currently implemented template type:

- n: create a new network report

(we might implement new types in the future, such as e.g.: ``a`` for creating new annual GEOFON report templates,
see :ref:`gfztreptype` for details)


I/O Directory structure
-----------------------

All templates generate the following :ref:`srcdir`

.. _gfzsrcdir:

Gfzreport source directory:
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a :ref:`srcdir` created by each template of :ref:`gfzt` with the following structure:

   * |DIR| conf_files (the :ref:`sphinxconfdir`)

   * |FILE| conf.py (the :ref:`sphinxconffile`)
   
   * |DIR| data (the :ref:`datadir`)
   
   * |FILE| report.rst (the :ref:`masterdoc`)


.. _sphinxconffile:


Sphinx configuration file
*************************

The file, called ``conf.py`` containing the :ref:`gfzb` (or :ref:`sphinxbuild`)
`configuration file <http://www.sphinx-doc.org/en/1.5.1/config.html>`_

.. _sphinxconfdir:

Sphinx configuration directory
******************************

The directory ``config_files``, containing all additional files required in :ref:`sphinxconffile`

.. _masterdoc:

Master |rst| document
*********************

The master :ref:`rst` document inside the :ref:`srcdir`. It is usually a
file called ``report.rst``, or whatever is implemented in :ref:`sphinxconffile` (without extension):

.. code-block:: python

   master_doc: 'report'

.. _datadir:

Data directory
**************

The sub-directory ``data`` of :ref:`gfzsrcdir`, holding all data files required in :ref:`masterdoc`

.. _createnewtemplate:

Creating a new template (network report example)
------------------------------------------------

To create a new network report you need the following mandatory options:

 - an output root folder (e.g. ``/out``. Note that this is the *parent directory* of the template folder which will be created)
 - an existing network name (e.g. ``ZE``)
 - a network start time (e.g. ``2012``)
 - a folder with all station's noise probability density functions (pdfs) images inside  (e.g. ``/in/pdfs``)
 - a folder (or file) of the instrument uptimes   (e.g. ``/in/uptime.png``)

and run:

.. code-block:: bash
   
   gfzreport template n -n ZE -s 2012 -o /out -i /in/uptime.png -p /in/pdfs

The command above will create the :ref:`srcdir` ``/out/ZE_2012`` with all necessary files.

Or you can also use wildcards in ``-i`` and ``-n``, but you need to escape wildcards in UNIX with the
backslash "\". For instance, assuming a common path ``/in`` for all images and different extensions:

.. code-block:: bash
   
   gfzreport template n -n ZE -s 2012 -o /out -i /in/\*.png -p /in/\*.jpeg

Alternatively, you  can also type ``-i`` and ``-p`` multiple times if source files are coming from
different directories, for instance pdfs from ``/in/pdfs1`` and ``/in/pdfs2``:

.. code-block:: bash
   
   gfzreport template n -n ZE -s 2012 -o /out -i /in/uptime.png -p /in/pdfs1 -p /in/pdfs2

For detailed help, type:

.. code-block:: bash
   
   gfzreport template n --help


Overview of the package / directory structure
-----------------------------------------------

Each template type specified by the [TYPE] letter from the command line above is associated
to a specific python package in:

.. code-block:: python

   gfzreport.templates

Have a look at :ref:`gfztpackagedir` for details on the package structure.

