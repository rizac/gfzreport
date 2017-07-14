Creating a template sub-package
===============================

Creating a template sub-package is only needed, when the generation of a source directory
involves complex operations. In principle, for simple sphinx reports, you can write your
directory structure as follows, populating it manually with the files you need:
```
   + SOURCE_DIRECTORY (report type, e.g. network, annual, tutorial):
      + REPORT_NAME (e.g., in case of networks NETWORKNAME_YEAR):
         + conf.py (the shpinx config file)
         + report.rst (the report rst file)
         + whatever dir you want to add (edited in the conf.py file)
```
FIXME: Create a conf.py by default that the user can edit. Check the network conf.py and
remove specific stuff while keeping general ones. At best, one could be interested to generate a
source folder
 should have the package extensions so maybe create an empty one!!!

1. Navigate into gfzreport/templates, create a directory with the template name (e.g. 'MYTEMPLATE')
2. create a 'sphynx' folder (or whatever you want to) populated with sphinx config files and at least one .rst
   For info see 'network' or have a ook here: 
3. Create a main.py file: gfzreport/templates/main.py. Therein, implement the click command (if required)
   to create the source file to be built later with sphinx