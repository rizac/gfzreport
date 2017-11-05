.. _gfzbext: 

Appendix 2: Creating new :ref:`rst` extensions
==============================================

:ref:`spx` is a highly `customizable <http://www.sphinx-doc.org/en/1.5.2/extdev/tutorial.html>`_.
That's the only claim they had which is actually 100% true. The sphinx extensions we implemented
are in 

.. code-block:: python
   
   gfzreport.sphinxbuild.core.extensions
   
Where each package corresponds to an extension type:



First of all: Sphinx is a poorly designed program for what we achieved (let alone rst limitations,
but that goes beyond the discussion here): as of October 2017, it is
perfect for documenting Python code and produce html. The possibility to turn rst
into both html and latex, which is the main reason why we built our program
on top of it, turned out to be really theoretical when it comes to provide customized output. All
in all, the patches, hacks and code smells are almost everywhere, especially in the package
`gfzreport.sphinxbuild`: that's is not our fault.
Current versions (1.6.+) of Sphinx are improving a lot this flexibility (apparently, we were not the only
one using sphinx in different scenarios). We did not upgrade to these new versions (we have 1.5.2 I guess)
because we realised some features which might be useful are still in beta version. If in a far
future one does need to upgrade, there will be most likely several tests to fix. Let alone the case
that a visual test is always a good idea (we cannot test bad pdf layout for instance). Note also
that new sphinx versions might need to change the rst breaking backward compatibility with older
reports (unless we close them in the online version)