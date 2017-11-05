.. _gfzt:

GfzReport-Template
==================

:package: gfzreport.templates

:command line: `gfzreport template [template_type] [options]`


:ref:`gfzr` can generate templates. A template is basically a :ref:`srcdir` with data and a
a pre-filled :ref:`rst` (called :ref:`masterdoc`) to be edited. After editing, the :ref:`srcdir`
can be built as usual by means of :ref:`gfzb` to create a HTML/ LaTex/PDF version of :ref:`masterdoc`.

The creation of a template can be invoked from the command line by typing:

.. code-block:: bash

   gfzreport template [TYPE] [options]

Where [TYPE] is a letter denoting the currently implemented template types:

- n: create a new network report
- a: create a new annual report (GEOFON report)
- e: create a new empty report

.. _createnewtemplate:


Output description
------------------

All templates generate the following :ref:`srcdir`

.. _gfzsrcdir:

Gfzreport source directory:
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a :ref:`srcdir` created by each template of :ref:`gfzt` with the following structure:

   * |DIR| conf_files (the :ref:`sphinxconfdir`)

   * |FILE| conf.py (the :ref:`sphinxconffile`)
   
   * |DIR| data (the :ref:`datadir`)
   
   * |FILE| report.rst (the :ref:`masterdoc`)


where:

.. _sphinxconffile:


Sphinx configuration file
*************************

The file, called `conf.py` containing the :ref:`gfzb` (or :ref:`sphinxbuild`)
`configuration file <http://www.sphinx-doc.org/en/1.5.1/config.html>`

.. _sphinxconfdir:

Sphinx configuration directory
******************************

The directory `config_files`, containing all additional files required in :ref:`sphinxconffile`

.. _masterdoc:

Master rst document
*******************

The file called `report.rst`, or whatever is implemented in `:ref:`sphinxconffile`:

.. code-block:: python

   master_doc: 'report'

which is the master :ref:`rst` document of the report.

.. _datadir:

Data directory
**************

The sub-directory 'data' of :ref:`gfzsrcdir`, holding all data files required in :ref:`masterdoc`


Creating a new template (network report example)
------------------------------------------------

To create a new network report you need the following mandatory options:

 - an output root folder $OUT
 - an existing network name (e.g. 'ZE')
 - a network start time (e.g. '2012')
 - a $NOISE_PDF_PATH folder with all station's noise probability density functions (pdf) images inside
 - a $INST_UPTIMES_PATH folder (or file) of the instrument uptimes

All command(s) below will create the :ref:`srcdir` '$OUT/ZE_2012' with all necessary files.

You can run for instance:

.. code-block:: bash
   
   gfzreport template n -n ZE -s 2012 -o $OUT -i $INST_UPTIMES_PATH -p $NOISE_PDF_PATH


Or you can also use wildcards in '-i' and '-n', but you need to escape wildcards in bash with the
backslash "\". For instance, assuming a common $PATH for all images and different extensions:

.. code-block:: bash
   
   gfzreport template n -n ZE -s 2012 -o $OUT -i $PATH/\*.png -p $PATH/\*.jpeg -p $NOISE_PDF_PATH2/*.png

Alternatively, you  can also type `-i` and `-p` multiple times if source files are coming from
different directories, for instance PATH1, PATH2 and PATH3:

.. code-block:: bash
   
   gfzreport template n -n ZE -s 2012 -o $OUT -i $PATH1 -p $PATH2 -p $PATH3

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

