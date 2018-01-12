
Overview
========

.. _rst:

reStructuredText
----------------

`reStructuredText <http://docutils.sourceforge.net/rst.html>`_
(referred also as |rst|) is an easy-to-read, what-you-see-is-what-you-get plaintext markup syntax
and parser system. It is useful for in-line program documentation (such as Python docstrings), for
quickly creating simple web pages, and for standalone documents.
This document is itself an example of reStructuredText (raw, if you are reading the text file, or
processed, if you are reading an |html| document, for example). The reStructuredText parser is a
component of `Docutils <http://docutils.sourceforge.net/>`_.

Summary of useful links about :ref:`rst` given also all across the document:

* `Home page <http://docutils.sourceforge.net/rst.html>`_
   
   * `Syntax, overview (sublink of the above) <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_

   * `Syntax, detailed (sublink of the above) <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html>`_

* `Syntax in Sphinx (see below), overview <http://www.sphinx-doc.org/en/stable/rest.html>`_

* `Syntax in Sphinx (see below), detailed <http://www.sphinx-doc.org/en/1.5.2/markup/>`_


.. _spx:

Sphinx
------

`Sphinx <http://www.sphinx-doc.org/en/stable/>`_ is a python tool that makes it (relatively) easy
to create documentation in different output formats: |html| (including Windows |html| Help), |latex|
(for printable |pdf| versions), ePub, Texinfo, manual pages, plain text. It uses :ref:`rst` as its
markup language, and uses Docutils as its parsing and translating suite.

Sphinx adds also a lot of `new directives and interpreted text roles <http://www.sphinx-doc.org/en/1.5.2/markup/>`_
to `standard |rst| markup <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html>`_.
It features different command-line 
`scripts <http://www.sphinx-doc.org/en/stable/invocation.html>`_, the most important of which is:

.. _sphinxbuild:

Sphinx-build
^^^^^^^^^^^^

The sphinx script that builds a Sphinx documentation set.The full documentation is available
`here <http://www.sphinx-doc.org/en/stable/invocation.html#invocation-of-sphinx-build>`_


.. _gfzr:

Gfzreport
---------

``Gfzreport`` is a python 2.7.+ program to create :ref:`spx` documentation at the  German Research
Centre for Geosciences (GFZ). Its aim is to facilitate several procedures that can be easily
automatised (e.g., producing standardised library layout, figures or tables fetching data from
EIDA), allowing authors to concentrate mainly on the content of their reports. It is built on top
of Sphinx and can be divided into three sub-programs: :ref:`gfzt`, :ref:`gfzb` and :ref:`gfzw`.

.. csv-table:: Pipeline schema of :ref:`gfzr` when run as command line application
   :widths: 50, 20, 50, 20, 50, 20, 50

   :ref:`gfzt`,  => , |DIR| :ref:`srcdir`, => , :ref:`gfzb`,  => , |DIR| :ref:`builddir`

.. csv-table:: Pipeline schema of :ref:`gfzr` when run as web application. Note the double arrow to indicate that the web application can also edit the source rst document
   :widths: 50, 20, 50, 20, 50, 20, 50, 20, 50

   :ref:`gfzt`,  => , |DIR| :ref:`srcdir`, <=> , :ref:`gfzw`,  => , :ref:`gfzb`,  =>  , |DIR| :ref:`builddir`

:ref:`gfzt`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:detailed section: :ref:`gfzt`

Generates templates (:ref:`spx` input directories) which can be fed into :ref:`gfzb`
after editing their pre-formatted :ref:`rst` document  

:ref:`gfzb`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:detailed section: :ref:`gfzb`

Produces (*builds*) |html| |latex| or |pdf| documents from :ref:`rst` files. It is basically :ref:`sphinxbuild`
with more features (e.g., `extensions <http://www.sphinx-doc.org/en/1.5.2/extdev/tutorial.html>`_)
included. :ref:`gfzb` and this tutorial use the same naming conventions of :ref:`sphinxbuild`:

.. _srcdir:

source directory
****************

The :ref:`gfzb` input directory, i.e. the root directory of a collection of :ref:`rst` document
sources. This directory also contains the :ref:`spx` configuration file ``conf.py``, where you can
configure all aspects of how Sphinx reads your sources and builds your documentation

.. _builddir:

build directory
***************

The :ref:`gfzb` output directory. It contains the |html| / |latex| / |pdf| output file(s) built from the
:ref:`srcdir`

:ref:`gfzw`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:detailed section: :ref:`gfzw`

A python Flask web application which, if this program is installed on a server, allows to:

 * edit online :ref:`rst` documents created via :ref:`gfzt`
 * build (via :ref:`gfzb`) and visualise online their |html| and |pdf| documents
