.. _gfztreptype:

Appendix 1: Creating a new template type
========================================

When using :ref:`gfzt`, we might want to create a new report type available via the command line.
This appendix describes basically how to do: note that it is intended as an advanced tutorial for developers.

First of all, we suggest to *copy* and paste an existing package, e.g. the ``network`` package as it is the
most complex (thus you will probably not need to implement much stuff). This might be redundant
(e.g. for javascript files) but it's much more simple. In any case there should not be many new report types
in the future.
The package, as **any** :ref:`gfzt` package, is a directory with the following structure:

.. _gfztpackagedir:

Gfzreport template package directory:
-------------------------------------

Any new template package of :ref:`gfzt` should have the following structure:

   * |DIR| sphinx

      * |DIR| conf_files (the :ref:`sphinxconfdir`)

      * |FILE| conf.py (the :ref:`sphinxconffile`)
   
      * |FILE| report.rst (the :ref:`masterdoc`)
      
   * |FILE| __init__.py (where to implement the main function creating a :ref:`gfzsrcdir`)
      
   * |FILE| optional python file/package required in __init__.py

   * |FILE| optional python file /package required in __init__.py
   
   * ... 

The final output of invoking this package is a :ref:`gfzsrcdir` (i.e. basically the same directory
above without any python files but ``conf.py``). To achieve that, the steps are:

Step 1: |rst| file
-------------------

The first thing to have a look at is the :ref:`masterdoc`.
When editing, we recall that :ref:`gfzb` implements several :ref:`sphinxbuildextensions`.

* For directives, they are located in:

  .. code-block:: python

     gfzreport.sphinxbuild.core.extensions 

  (these extensions are loaded in ``conf.py``, see :ref:`sphinxconffile`). You can have a look
  at the :ref:`masterdoc` where we provided some help. Or inspect the
  documentation of the extensions python modules.

* For `bibliographic fields <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#bibliographic-fields>`_,
  when adding/ removing them remember also to provide the relative :ref:`templatinglatexcustomization`.

Step 2: :ref:`spx` config files
-------------------------------

Assuming you copied the ``network`` package, :ref:`spx` config files are already set up. However,
if you need to change them, here what to do. First of all, the root file is the file ``conf.py``. Therein
we defined the paths for |latex| and |html| configuration, which point to the directory ``sphinx/conf_files``:

|DIR| conf_files

  * |DIR| html
  
    * |DIR| static_path
    
      * |DIR| css
      * |DIR| img
      * |DIR| js
      
    * |DIR| templates
      
  * |DIR| latex
    
    * |DIR| additional_files


|html| customization
^^^^^^^^^^^^^^^^^^^^

In ``conf.py``, the directories of interest are ``html/static_path`` and ``html/templates``. They are
configured in ``conf.py`` with the following variables:

.. code-block:: python

   # Add any paths that contain templates here, relative to this directory.
   templates_path = ['conf_files/html/templates']
   
   # Add any paths that contain custom static files (such as style sheets) here,
   # relative to this directory. They are copied after the builtin static files,
   # so a file named "default.css" will overwrite the builtin "default.css".
   html_static_path = ['conf_files/html/static_path']

:ref:`spx` will use the |html| files defined in ``templates_path`` to customize the |html| layout.
Therein, there is a single file, ``layout.html``. There might be reasons to implement more than one layout,
but that goes beyond the discussion here (for info see http://www.sphinx-doc.org/en/1.5/templating.html).

If we want to add / delete a static file (css, js, ...), we first need to add it / remove it inside ``html_static_path``.
Then, we need to include it by editing ``layout.html``. Note that :ref:`spx`
will rename ``html_static_path`` to a ``_static`` folder in the |html| root directory, thus
a file named ``[html_static_path]/css/mystyle.css`` needs to be included in the layout as
``_static/css/mystyle.css``.

.. _templatinglatexcustomization:

|latex| customization
^^^^^^^^^^^^^^^^^^^^^

In ``conf.py``, the directory of interest is ``latex/additional_files``. It is
configured in ``conf.py`` with the following variables:

.. code-block:: python

   # A list of file names, relative to the configuration directory, to copy to the build directory
   # when building LaTeX output. (Note: changed in version 1.2: This overrides the files which is
   # provided from Sphinx such as sphinx.sty):
   latex_additional_files = [os.path.join('conf_files/latex/additional_files', c)
                             for c in os.listdir("conf_files/latex/additional_files")]
   
   latex_elements = {
       # not toc:
       'tableofcontents': u'',
       # The paper size ('letterpaper' or 'a4paper'):
       'papersize': 'a4paper',
       # The font size ('10pt', '11pt' or '12pt'):
       'pointsize': '12pt',
       # Latex figure (float) alignment
       'figure_align': '!ht',
       'geometry': r'\usepackage[left=2cm,right=2cm,top=2cm,bottom=2cm]{geometry}',
       # Sphinx has too fancy stuff: titles as \sfseries\bfseries,
       # and title colors (which applies to ALL section titles) a sort of blue
       # set the former as normal bfseries, and the latter as black
       # (NOTE THAT Title Color applies to ALL section/chapter titles in sphinx 1.5.1):
       'sphinxsetup': "HeaderFamily=\\bfseries,TitleColor={rgb}{0,0,0}",
       # sphinx preamble (http://www.sphinx-doc.org/en/stable/config.html#confval-latex_elements):
       'preamble': r'\makeatletter\input{latex.preamble.tex}\makeatother',
       # latex epilog (http://www.sphinx-doc.org/en/stable/config.html#confval-latex_elements):
       'atendofbody': r'\makeatletter\input{latex.atendofbody.tex}\makeatother',
   }

:ref:`spx` will copy all ``latex_additional_files`` in the |latex| :ref:`builddir`, thus be careful about names.
``latex_additional_files`` might contain also two special files, ``sphinx.sty`` and ``sphinxhowto.cls`` which
will override the defaults copied therein by :ref:`spx`. We decided not to override those files as
they might break the |latex| layout.

The first thing to look at for easy to set customiations is the variable ``latex_elements``
(for a detailed explanation, see http://www.sphinx-doc.org/en/1.5/latex.html).
For more complex customizations (e.g., you implemented new bibliographic fields in the |rst| and want to render them in the |latex| layout,
or you want to change the tile/layout/position of those fields
in the |latex| document) you will most likely need to have a look at two
files pointed by ``latex_additional_files``:

.. code-block:: latex
   
   conf_files/latex/additional_files/latex.preamble.tex
   conf_files/latex/additional_files/latex.atendofbody.tex

and edit them. Again, since you have copied a pre-existing template, you might have some help
by looking at how those fields where implemented

Step 3: Python code
--------------------

Got to the ``__init__.py`` module of the package. In there, you need to implement
the code creating :ref:`srcdir` for this template type. This is achieved by implementing the 
class Templater which must always be initialized (from the command line) with the following arguments:

.. code-block:: python

   class Templater:
   
      def __init__(self, out_path, update_config_only, mv_data_files, confirm):
        '''Initializes an (abstract class) Templater
        
        :param out_path: the *initial* destination directory. This is usually a destination root
            and the real destination path must be implemented in `self.getdestpath` (which might return
            self._out_path, it depends on the implementation)
        :param update_config_only: weather the real destination path should update the sphinx
            config files only when this object is called as function
        :param mv_data_files: ignored if `update_config_only=True`, tells weather the real
            destination path should have files moved therein
            when `update_config_only=False`. The files to move or copy are those returned by
            `self.getdatafiles` (to be sub-classed)
        :param confirm: weather to confirm, when this object is called as function, before
            setting all up
        ''' 

Templater is callable. The user has to choose which optional specific arguments \*args and \*\*kwargs
to be passed to the object `__call__` method (most likely, from the command line).
Then, the followinf three methods need to be overridden:

.. code-block:: python

   class Templater(gfzreport.templates.utils.Templater):

      def getdestpath(self, out_path, *args, **kwargs):
          '''This method must return the *real* destination directory of this object.
          In the most simple scenario, it can also just return `out_path`
      
          :param out_path: initial output path (passed in the `__init__` call)
		  :param args, kwargs: the arguments passed to this object when called as function and
              forwarded to this method
          '''
      
      def getdatafiles(self, destpath, destdatapath, *args, **kwargs):
          '''This method must return the data files to be copied into `destdatapath`. It must
          return a dict of
      
          `{destdir: files, ...}`
      
          where:
      
          * `destdir` is a string, usually `destdatapath` or a sub-directory of it,
             denoting the destination directory where to copy the files
      
          * `files`: a list of files to be copied in the corresponding `destdir`. It can
            be a list of strings denoting each a single file, a directory or a glob pattern.
            If string, it will be converted to the 1-element list `[files]`
      
          Use `collections.OrderedDict` to preserve the order of the keys
      
          For each item `destdir, files`, and for each `filepath` in `files`, the function
          will call:
      
          :ref:`gfzreport.templates.utils.copyfiles(filepath, destdir, self._mv_data_files)`
      
          Thus `filepath` can be a file (copy/move that file into `destdir`) a directory
          (copy/move each file into `destdir`) or a glob expression (copy/move each matching
          file into `destdir`)
      
          :param destpath: the destination directory, as returned from `self.getdestpath`
          :param destdatapath: the destination directory for the data files, currently
              the subdirectory 'data' of `destpath` (do not rely on it as it might change in the
              future)
          :param args, kwargs: the arguments passed to this object when called as function and
              forwarded to this method

          :return: a dict of destination paths (ususally sub-directories of `self.destdatapath`
              mapped to lists of strings (files/ directories/ glob patterns). An empty dict or
              None (or pass) are valid (don't copy anything into `destdatadir`)
      
          This function can safely raise as Exceptions will be caught and displayed in their
          message displayed printed
          '''
      
      def getrstkwargs(self, destpath, destdatapath, datafiles, *args, **kwargs):
          '''This method accepts all arguments passed to this object when called as function and
          should return a dict of keyword arguments used to render the rst
          template, if the latter has been implemented as a jinja template.
      
          You can return an empty dict or None (or pass) if the rst in the current source folder
          is "fixed" and not variable according to the arguments. Note that at this
          point you can access `self.destpath`, `self.destdatapath` and `self.datafiles`
      
          :param destpath: the destination directory, as returned from `self.getdestpath`
          :param destdatapath: the destination directory for the data files, currently
              the subdirectory 'data' of `destpath` (do not rely on it as it might change in the
              future)
          :param datafiles: a dict as returned from self.getdatafiles`, where each key
              represents a data destination directory and each value is a list of files that have
              been copied or moved inthere. The keys of the dict are surely existing folders and are
              usually sub-directories of `destdatapath` (or equal to `destdatapath`)
          :param args, kwargs: the arguments passed to this object when called as function and
              forwarded to this method
      
          :return: a dict of key-> values to be used for rendering the rst if the latter is a
              jinja template.
      
          This function can safely raise as Exceptions will be caught and displayed in their
              message displayed printed
          '''

For detailed info on the above methods to be sub-classed, have a look at the doc of the
super-class:

.. code-block:: python
   
   gfzreport.templates.utils.Templater
   
When implementing those method, remember that the output of a template package is always be a
:ref:`gfzsrcdir` (see link for details), i.e. a directory containing:

  * the :ref:`sphinxconffile`
  
  * the :ref:`sphinxconfdir`
  
  * the :ref:`datadir`
  
  * the :ref:`masterdoc`
  

Basically, a Templater tells what to write in :ref:`datadir` via:

.. code-block:: python

   Templater.getdatafiles

and if :ref:`masterdoc` needs to
be modified according to the arguments provided. For that, you can implement a :ref:`masterdoc`
which is also a `jinja template <http://jinja.pocoo.org/docs/2.9/templates/>`_ and
render it with the returned values of 

.. code-block:: python

   Templater.getrstkwargs


Step 4: Entry point (command line interface)
---------------------------------------------

Now you just have to implement the "bridge" between the command line and the
Templater class you just created. For that, you need to know
the `click package <http://click.pocoo.org/5/commands/#callback-invocation>`_ which
is preferable for `various reasons <http://click.pocoo.org/5/why/>`_. We suggest to
copy the command of the template folder relative to the package we copied for building
our template package, and have a look at it. Teh command should have the form:

.. code-block:: python

   @templatecommand(short_help="Generates the report folder for the given network and year",
                 context_settings=dict(max_content_width=TERMINAL_HELP_WIDTH))
   @option("-n", '--network', required=True, help="the network name, e.g.: ZE")
   @option("-s", '--start_after', required=True, help="the start year, e.g.: 2012"))
   @option...
   def commandname(out_path, conffiles_only, mv_datafiles, noprompt, network, start_after, ...):
    """
       doc here...
    """
    try:
        runner = mytemplatepackage.Templater(out_path, conffiles_only, mv_datafiles, not noprompt)
        sys.exit(runner(network, start_after, ...))
    except Exception as exc:
        print("Aborted: %s" % str(exc))
        sys.exit(1)

Note that 'network', 'start_after', ... in the example need to be the same 'args' and 'kwargs' in
the Templater class methods above. The function name 'commandname' is the command which must be
given from the terminal. To test it, try once done:

.. code-block:: bash
   
   gfzreport template commandname --help

Finally, we **strongly** suggest to write tests in the test folder


Problems/ issues
----------------

Sphinx adds several |latex| stuff, among which a ``sphinxhowto.cls`` and ``sphinx.sty`` file.
We chose NOT to touch those files in order not to break compatibility.

In ``sphinx.sty``, :ref:`spx` defines text styling commands (with one argument):

.. code-block:: latex

   \sphinx<foo>
   
with <foo> being one of (quoting from their docs):
strong, bfcode, email, tablecontinued, titleref, menuselection, accelerator, crossref, termref, optional.
By default and for backwards compatibility the \sphinx<foo> expands to \<foo> hence the user can
choose to customize rather the latter (the non-prefixed macros will be left undefined if option
``latex_keep_old_macro_names`` is set to False in conf.py.)

This is absolutely unclear, as :ref:`spx` generated |latex| output still uses the old names, which
would then break if ``latex_keep_old_macro_names=False`` (have a look at ``conf.py`` implemented for the network template, 
we might put some extra notes there)




    