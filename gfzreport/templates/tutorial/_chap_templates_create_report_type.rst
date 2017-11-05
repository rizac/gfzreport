.. _gfztreptype:

Appendix 1: Creating a new template type
========================================

When using :ref:`gfzt`, we might want to create a new report type available via the command line.
This appendix describes basically how to do: note that it is intended as reminder for developers
and it is not a full documentation for unexperienced users

First of all, we suggest to copy and paste an existing package, e.g. the 'network' package as it is the
most complex (thus you will probably need to **delete** stuff rather than **implement** it).
The package, as **any** :ref:`gfzt` package, is a directory with the following structure:

.. _gfztpackagedir:

Gfzreport template package directory:
-------------------------------------

This is a :ref:`srcdir` created by each template of :ref:`gfzt` with the following structure:

   * |DIR| sphinx

      * |DIR| conf_files (the :ref:`sphinxconfdir`)

      * |FILE| conf.py (the :ref:`sphinxconffile`)
   
      * |FILE| report.rst (the :ref:`masterdoc`)
      
   * |FILE| __init__.py (where to implement the main function creating a :ref:`gfzsrcdir`)
      
   * |FILE| optional python file/package required in __init__.py

   * |FILE| optional python file /package required in __init__.py
   
   * ... 

The final output of invoking this package should be a new template, i.e. a :ref:`gfzsrcdir`.
To achieve that, the steps are:

Steps 1: Rst file
-----------------

The first thing to have a look at is the :ref:`masterdoc`. :ref:`gfzb` implements several
extensions. An extension correspond to custom :ref:`rst` markup code (usually :ref:`rst` *directives*)
and to a module in:

.. code-block:: python

   gfzreport.sphinxbuild.core.extensions 

(these extensions are loaded in `conf.py`, see :ref:`sphinxconffile`). You can have a look
at the :ref:`masterdoc` where we provided some help. Or inspect the
documentation of the python modules 

Another feature of our :ref:`rst` syntax is how we process 
`bibliographic fields <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#bibliographic-fields>`_.
A bibliographic field (by the way, why "bibliographic"?) is :ref:`rst` markup of the form:

.. code-block:: rst

   :name: value

placed **at the beginning** of the :ref:`masterdoc`.

Fields before the title are not rendered in the output (this is standard :ref:`rst`)  [#tn1]_, 
their values cannot contain markup as it will not be rendered (Sphinx bug?), and will be
available in latex as latex commands:

.. code-block:: latex

   \rstName{value}


Steps 2: Latex files
--------------------

If you implemented new fields, or you want to change the tile/layout/position of those fields
in the latex title page (or last page) you will most likely need to have a look at two
files in  :ref:`sphinxconfdir`:

.. code-block:
   
   conf_files/latex/additional_files/latex.preamble.tex
   conf_files/latex/additional_files/latex.atendofbody.tex

and edit them. Again, since you have copied a pre-existing template, you might have some help
by looking at how those fields where implemented

Steps 3: Python code
--------------------

Got to the '__init__.py' module of the package. In there, you need to implement
the code creating :ref:`srcdir` for this template type. This is achieved by implementing the 
class:

.. code-block:: python

   class Templater(gfzreport.templates.utils.Templater):

      def getdestpath(self, out_path, *args, **kwargs):
    
      def getdatafiles(self, destpath, destdatapath, *args, **kwargs):

      def getrstkwargs(self, destpath, destdatapath, datafiles, *args, **kwargs):

where \*args and \*\*kwargs depends on the implementation, and are the template specific
arguments most of which you probably want to be passed from the command line.
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


Steps 4: Entry point (command line interface)
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

Sphinx adds several latex stuff, among which a sphinxhowto.cls and sphinx.sty file.
We chose NOT to touch those files in order not to break compatibility.
In sohinx.sty, sphinx defines text styling commands (with one argument):

.. code-block:: latex

   \sphinx<foo>
   
with <foo> being one of
strong, bfcode, email, tablecontinued, titleref, menuselection, accelerator, crossref, termref, optional.
By default and for backwards compatibility the \sphinx<foo> expands to \<foo> hence the user can
choose to customize rather the latter (the non-prefixed macros will be left undefined if option
latex_keep_old_macro_names is set to False in conf.py.)

Funny thing is, sphinx hardcoded generated output STILL uses the old names. So it is absolutely UNCLEAR
what would happen if latex_keep_old_macro_names=False


.. rubric:: template_notes

.. [#tn1] bibliographic fields before the title are available as

          .. code-block::python
            
             self.builder.app.env.metadata[self.builder.app.config.master_doc]
             
          in latex and html writers implemented in:
          
          .. code-block::python
             
             gfzreport.sphinxbuild.writers
             
           or as (you should debug, this is just an hint):
           
           .. code-block::python:
           
              self.state.inliner.document.settings.env

           from within a directive