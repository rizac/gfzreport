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

This is certainly due to very specific requirements and features we had.
However, as of November 2017 (with :ref:`spx` 1.5.1) when digging into :ref:`spx` code we observed many
weaknesses in the design or documentation not matching the given code.
This was particularly true when producing/customizing |latex| output.
Being :ref:`spx` mainly designed and used
for producing |html| documentations of software code, this is somehow not surprising. Except maybe
some too optimistic claims on their documentation which might have been better tested beforehand...

Anyway: current versions (1.6.+) of :ref:`spx` are improving a lot in the direction of customization / flexibility 
(especially for |latex|) and code design, but we did not upgrade to these new versions because we realised many
of those features were still in beta version.

Also, **consider that upgrading :ref:`spx` requires a lot of work to upgrade also the code in**
``gfzreport.sphinxbuild.core.extensions`` (which sits on top of it). :ref:`gfzr` started with :ref:`spx` 1.4.1 and we upgraded
it until the effort in code refactoring (+testing) was affordable in terms of time.

Note however that new :ref:`spx` versions might need to change the |rst|, breaking backward compatibility with older
reports: **an upgrade is therefore to be done, when no report is still to be finalized. And most likely,
older reports cannot be edited anymore**



