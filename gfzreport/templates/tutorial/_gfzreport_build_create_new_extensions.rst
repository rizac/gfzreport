.. _gfzbext: 

Appendix 2: Creating new :ref:`rst` extensions
==============================================

An extensive tutorial on how to implement new :ref:`spx` extensions is beyond the current scope of this tutorial.
You can browse the package and see the currently implemented extensions in:

.. code-block:: python
   
   gfzreport.sphinxbuild.core.extensions

For any new extension, write the corresponding module therein and add it in the :ref:`spx`  config file.
You can have a look also at the :ref:`spx` tutorial: http://www.sphinx-doc.org/en/1.5/extdev/tutorial.html 
(which unfortunately is not that detailed).

Disclaimer
----------

The interaction between :ref:`gfzr` and :ref:`spx` (e.g., when implementing new extensions) for
our specific use case (make an |rst| as parent root document for producing report output in |latex|, |pdf| and |html|)
*turned out to be more than challenging*.

This is certainly due to very specific requirements and features we had, but also to several
weaknesses of :ref:`spx`, not yet mature in version 1.4+ to produce |html|, |latex| and |pdf| output without efforts.

Although newer versions (1.6.+) are improving a lot, we stopped
to upgrade :ref:`spx` after version 1.5.1 (the currently used one) for several maintainability and backward compatibility issues:
first, **consider that upgrading**
:ref:`spx` **requires a lot of work to upgrade also the code in** ``gfzreport.sphinxbuild.core.extensions``
(which sits on top of it), and finally, new :ref:`spx` versions might need to change the |rst| syntax, breaking backward
compatibility with older reports:
**an upgrade is therefore to be done, when no report is still to be finalized.**
**And most likely, older reports cannot be edited anymore**



