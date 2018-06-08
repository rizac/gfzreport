.. tutorial of this app. Note that included files must start with _chap_ or whatever
   is implemented in exclude_patterns in conf.py.

.. PLEASE NOTE: Except fopr the title (see below), all section lavels are underlined only
   and they are: (we might use our customized titles as github markup?)
   
   ====================== chapter
   --------------------- section
   ^^^^^^^^^^^^^^^^^^^^^ sub-subsection
   ********************** paragraph


:tocdepth: 3

:subtitle: A program to create |html| / |latex| / |pdf| reports from |rst| source files

:subSubtitle: Tutorial

=========
GfzReport
=========

:author: Riccardo Zaccarelli (GFZ: German Research Centre for Geosciences)

.. raw:: html

   <a href='latex/gfzreport-tutorial.pdf'>PDF version</a>


.. |DIR| image:: ./sphinx/conf_files/img/24px-Icons8_flat_folder.svg.png

.. |FILE| image:: ./sphinx/conf_files/img/24px-File_alt_font_awesome.svg.png

.. |rst| replace:: RsT

.. |latex| replace:: LaTeX

.. |html| replace:: HTML

.. |pdf| replace:: PDF
   
.. include:: _overview.rst

.. include:: _installation.rst

.. include:: _gfzreport_template.rst

.. include:: _gfzreport_build.rst

.. include:: _gfzreport_web.rst

.. include:: _gfzreport_web_on_server.rst

.. include:: _gfzreport_template_create_report_type.rst

.. include:: _gfzreport_build_create_new_extensions.rst
   
