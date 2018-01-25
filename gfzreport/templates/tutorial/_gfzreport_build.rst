.. _gfzb: 

gfzreport-build
===============

:package:           ``gfzreport.sphinxbuild``

:command: ``gfzreport build [options]``

:help:           ``gfzreport build --help``


:ref:`gfzb` is basically a wrapper around :ref:`sphinxbuild`. You might ask why to re-invent the wheel.
Because we needed a slightly different wheel.

.. _sphinxbuildfeatures:

Features
--------

:ref:`gfzb` features first of all a |pdf| builder callable by the python code: although :ref:`spx`
claim that :ref:`sphinxbuild` can build |pdf| documents, well... no, you can not.
As of mid 2016, when the :ref:`gfzr` project started, the available python extensions where buggy
and with very poor flexibility compared to ``pdflatex``.

:ref:`gfzb` also extends :ref:`spx` (which in turn extends :ref:`rst`) by adding new extensions and new
bibliographic fields behavior:

.. _sphinxbuildextensions:

New extensions
^^^^^^^^^^^^^^

:ref:`spx` features new `directives <http://www.sphinx-doc.org/en/1.5.2/extdev/tutorial.html>`_ and
interpreted text roles (e.g. '$' for math typing, as in |latex|) to match requirements for the Network reports generated with :ref:`gfzt`

.. _bibliographicfieldsbehaviour:

Bibliographic fields behaviour
*******************************

:ref:`gfzb` implements new default behaviours of the so-called
`bibliographic fields <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#bibliographic-fields>`_, i.e.
:ref:`rst` markup of the form:

.. code-block:: rst

   :name: value

placed **at the beginning** of the :ref:`rst` file.

By default (we will honour this behaviour in our program), bibliographic fields *before* the title are not rendered in the output [#tn1]_.
In addition to this, in :ref:`gfzb` each field will be available as ``\rst<field_name_with_first_letter_capitalized>`` in |latex|.
So for instance:

.. code-block:: rst
   
   doi: abc
   
will be available in |latex| as (note first capitalized letter):

.. code-block:: latex

   \newcommand{rstDoi}{abc}
   
A user might then implement a custom |latex| layout to include that command  (see :ref:`templatinglatexcustomization` for details).

By default, bibliographic fields *after* the title are rendered in the output. We honour this behaviour
in our program with some exceptions regarding |latex| output only:

- 'abstract' will be rendered inside a ``\begin{abstract}...\end{abstract}`` environment, and not as bibliographic field

- 'author' (or 'authors') will be parsed before being rendered and will create two new commands
  to be used in the |latex| customization if needed. E.g.:
  
  .. code-block:: latex
     
     \newcommand{\rstAuthorsWithAffiliations}{Tom Smith$^{1*}$, Frank Smith$^1$, John Smith$^2$}
	 
	 \newcommand{\rstAffiliations}{$^1$ insitute1 \\[\baselineskip] $^2$ institute2 \\[\baselineskip] $^{*}$ corresponding authors}

  In |html| no process is involved and they will be rendered by default as they are (except removing any asterix from the authors before
  rendering).
  
- 'citation' (or 'citations') will not be shown but stored inside the ``\rstCitations`` command

- 'revision' will not be shown but will update internally the ``release`` key of the :ref:`spx` ``app.elements`` object

.. [#tn1] Note for developers: Bibliographic fields before the title cannot contain markup nor can they
   have comments between them (Sphinx bug?). When implementing new extensions, they are available as     
   ``self.builder.app.env.metadata[self.builder.app.config.master_doc]``   
   in |latex| and |html| writers implemented in   
   ``gfzreport.sphinxbuild.writers`` or, from within a directive, as
   ``self.state.inliner.document.settings.env``


Overview of the package
-----------------------

The main function is:


.. code-block:: python

   def run(sourcedir, outdir, build=_DEFAULT_BUILD_TYPE, *other_sphinxbuild_options)


located at:

.. code-block:: python
   
   gfzreport.sphinxbuild.core.__init__.py:run 


The functions does what :ref:`sphinxbuild` does, it just calls ``pdflatex`` after :ref:`sphinxbuild`
if ``build='pdf'`` and writes a custom log file (currently ``__.gfzreport.__.log``) in the
:ref:`builddir`. The log has normalized :ref:`spx` and ``pdflatex`` errors (both with the format: 
:regexp:`.+?:[0-9]+:\\s*ERROR\\s*:.+`).
Note that those errors do not prevent in most cases the creation of the document; thus, they might be
regarded as warnings, excepts that :ref:`spx` uses already the word "WARNINGS" for other kind of
messages.
Nevertheless, they are useful especially in :ref:`gfzw` to show information to the users after
the build, in a formatted way (e.g., catch all error-like lines and show them in red)


Other packages are:

.. code-block:: python

   gfzreport.sphinxbuild.core.extensions
   
where we implemented the :ref:`rst` extensions for improving our markup syntax

.. code-block:: python

   gfzreport.sphinxbuild.core.writers
   
where we implemented the |latex| and |html| builders, i.e. the classes which render the document.
We needed this to correct some hard-coded features due to :ref:`spx` bad design but also
to implement the :ref:`bibliographicfieldsbehaviour` described above.

Note that if upgrading to newer :ref:`spx` versions (we use 1.5.1, as of October 2017 1.6.6 is the latest one)
we might probably look at the writers as, especially for |latex|, :ref:`spx` *is going* into a more
customizable direction and thus some patches might be useless (or buggy).

.. code-block:: python

   gfzreport.sphinxbuild.map
   
where we implemented the package creating a scatter map of stations (image, e.g. png). This is
used in one of our custom extensions

