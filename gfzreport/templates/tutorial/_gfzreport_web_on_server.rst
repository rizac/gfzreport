
.. _webserver:

gfzreport-web (on current server)
=================================

The :ref:`gfzw` is currently installed at GFZ on ``st161dmz``. This is a fast tutorial
explaining how to do most common operations

.. _logintoserver:

Login to server
---------------

Assuming you have `generated an ssh key <https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2>`_

.. code-block:: bash
   
   ssh sysop@st161dmz

.. _activatevirtualenv:

Activate virtualenv
-------------------

:ref:`gfzr` runs in an isolated python virtual environment. That is, the necessary python packages
(with needed versions) are not installed system wide to not create conflicts.
To Activate the virtualenv:

.. code-block:: bash
   
   source /home/sysop/gfz-reportgen/bin/activate


.. _updatepythonpackage:

Update the python package
-------------------------

When the package is modified, we need to update the server version. Firs :ref:`activatevirtualenv`.
Then:

.. code-block:: bash

   cd /var/www/html/gfz-reportgen
   git pull

Before checking modifications in the browser, remember to :ref:`restartserver`


Notes
^^^^^

1. If you get a error: "insufficient permission for adding an object to repository..."
after issuing the ``git pull``, it might be that a ``git pull`` has been previosuly issued with root privileges
(which might happen when restarting the server without exiting afterwards).
In that case, first :ref:`gainrootprivileges` and then issue a:

.. code-block:: bash

   chown -R sysop:sysop .
   exit
   git pull

2. After issuing ``git pull``, as the package has been installed as editable all modifications will take place without the
need to re-install :ref:`gfzr`, unless something in ``setup.py`` has changed. In this case
you need to re-install it:

.. code-block:: bash

   pip install -e .

.. _gainrootprivileges:

Gain root privileges
--------------------

For certain operations, you might need to gain root privileges. Provided you know the root password (otherwise
ask), then type:

.. code-block:: bash

   su
   Password: [TYPE PASSWORD]

do your stuff and **eventually type ``exit`` to restore the ``sysop`` user**.

.. _restartserver:

Restart the server
------------------

You need to :ref:`gainrootprivileges` first, and then:

.. code-block:: bash

   service apache2 reload


Debug from terminal (View Apache error log)
-------------------------------------------

.. code-block:: bash

   tail -f /var/log/apache2/error.log
   
(Ctrl+C to exit)


.. raw:: latex

   \clearpage

.. _serverrootpath:

Root data path
--------------

All :ref:`gfzr` data files are located at:

.. code-block:: bash
   
   /data2/gfzreport

The directory structure is:
   
|DIR| /data2/gfzreport

+ |FILE| users.sqlite (the db storing users and sessions)
     
+ |FILE| users.txt (text json file where to add/remove/edit users)

+ |DIR| network (network report :ref:`webappdatapath`)

  - |DIR| source
  
    * |DIR| ZE_2012 (:ref:`srcdir` of report ZE_2012)
    
    * |DIR| ...
     
  - |DIR| build
     
    * |DIR| ZE_2012
    
      + |DIR| html  (the |html| :ref:`builddir` of report ZE_2012)

      + |DIR| latex (the |latex| and |pdf| :ref:`builddir` of report ZE_2012)
      
    * |DIR| ... 
          
+ |DIR| annual (annual report :ref:`webappdatapath`)

  - |DIR| source
   
    * |DIR| 2016 (:ref:`srcdir` of report 2016)

    * |DIR| ... 
      
  - |DIR| build
      
    * |DIR| 2016
    
      + |DIR| html  (the |html| :ref:`builddir` of report 2016)
       
      + |DIR| latex (the |latex| and |pdf| :ref:`builddir` of report 2016)
      
    * |DIR| ... 


Each :ref:`webappdatapath` (e.g. ``/data2/gfzreport/network``) denotes a report type directory and
is currently associated to a specific url. When the url is typed in a browser, :ref:`gfzw` shows the report type
homepage by scanning the ``source`` sub-directory (e.g. ``/data2/gfzreport/network/source``): therein,
*each folder whose name does not start with "_"* is associated to a report :ref:`srcdir` and shown as a button in the homepage.
Clicking the button you have access to the report for visualization or editing (if you are authorized)

.. _wsgisfiles:

Wsgis directory
---------------

All :ref:`gfzw` wsgis files are located at:

.. code-block:: bash
   
   /var/www/html/gfz-reportgen/wsgis/


.. _apacheconfavaldir:

Apache conf directory
---------------------

All Apache configuration files are located at:

.. code-block:: bash
   
   /etc/apache2/conf-available/

Create a new report template (network report)
---------------------------------------------

This is the same operation described in :ref:`createnewtemplate`, but specific for 
the application installed on the GEOFON server. It can be subdivided into three steps:

1. Preparation (image files)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assuming the network name is "ZE" and the start year is 2012 (these information are mandatory to
create a new network report), you first have to create the report default figures, i.e. the
noise probability density functions (pdfs)
and the instrument uptimes figure (if it's not you, ask the GEOFON person responsible to produce them). 

Please note that, being all pdfs arranged in the document as a grid of images, :ref:`gfzt`
expects their file names to be in the format:

``[station]-[channel].png``

or, for stations with the same name:

``[station]-[channel]-1.png, [station]-[channel]-2.png``

where the number should match the station start time, e.g. between "AW-HHZ-1" and "AW-HHZ-5", the latter is more recent.
Actually, "-" can be any sequence of one or more non-alphanumeric characters (use what you want).

The input figures can be created in any directory with any tree structure.
By convention, we use directories of the type "`/home/sysop/tmp_*`". 
Assuming, e.g., the following input figures directory:

.. code-block:: bash
   
   /home/sysop/tmp_ZE/pdfs [directory of the noise pdfs]
   /home/sysop/tmp_ZE/uptime.png  [file of the instrument uptime]

2. Create document
^^^^^^^^^^^^^^^^^^

 (please remember that for any detailed help you can always
:ref:`activatevirtualenv` and then type `gfzreport template n --help` on the terminal)

In order to create a new empty network report (with the image files created and other meta-data
fetched automatically) you **MUST first** :ref:`activatevirtualenv` and then run:

.. code-block:: bash
   
   gfzreport template n -n ZE -s 2012 -p /home/sysop/tmp_ZE/pdfs -i /home/sysop/tmp_ZE/uptime.png -o /data2/gfzreport/network/source

The command above creates the directory "/data2/gfzreport/network/source/ZE_2012" (note that the output ``-o`` option points
to the parent folder of the directory).

**Please remember that a detailed help is always available from the terminal by typing**: `gfzreport template n --help` [#wcrd]_.

3. Checks
^^^^^^^^^

* Read the output of the program on the terminal while creating the template:
  it is intended to be a first check for capturing errors which
  prevent the template creation correctly (e.g. internet connection
  while retrieving all network stations metadata for the maps and tables).
  The output of the program is in any case written to ``gfzreport.template.log`` (inside the output directory)
 
* Check visually the result. Go at http://st161dmz/gfzreport/network and check that
  there is the button corresponding to the newly created report. Then click on that button and check
  the report template (e.g., all pdfs figures are correctly in the grid, the station map and table correctly
  display the stations, and so on). You should not need to :ref:`restartserver`. However, if something is wrong, try
  that and check again in the browser before reporting the error.

* If there are users who need to edit the report and do not have authorization, remember to
  :ref:`modifydbusers`, 

.. [#wcrd] As specified in the terminal help, the program ``-p`` and ``-i`` options accept wildcards
   Note however that UNIX expands wildcards into the list of matching files
   before calling our program, and that breaks the program functionality. Solution:
   Escape wildcards with backslash, or avoid wildcards at all

.. _modifydbusers:

Modify users
------------

Go to :ref:`serverrootpath` and open with (e.g. vim) :ref:`webappusers`.
It is an json-like array (list) of user, each
user being a json object (python dict). 

You normally want to add a user. Then add a line to the list such as:

.. code-block:: python

   [
     ...
     {"email": "tom@mysite.com", "path_restriction_reg": "/abc*$"}
   ]

Where "path_restriction_reg" is a regular expression pattern indicating the authorization of the given
user 'tom': for a given report, when the
user tries to log in for editing, it will be authorized if its "path_restriction_reg" matches
(using python `re.search`) against the report :ref:`srcdir` (e.g. '/data2/gfzreport/network/source/ZE_2012'.
See :ref:`serverrootpath` for the program root directory structure).
If "path_restriction_reg" is missing, the user is authorized to edit any report (no restriction).

You can also delete a line to delete a given user, or change "path_restriction_reg" for
an existing user.

To have the modification take effect, :ref:`restartserver` 

Update config only
------------------

Sometimes, after a bug fix or whatever, we want to update the configuration files only, not overriding
any data file (including the source |rst|). Then run :ref:`gfzt` with the -c option, e.g.: 

.. code-block:: bash

   gfzreport template n -n ZE -s 2012 -c -o /data2/gfzreport/network/source/


Cp source directory
------------------------

For each report, you can always navigate into the :ref:`serverrootpath` and copy a :ref:`srcdir`.
This will create a new report on the web page. This operation is a hack but might be useful
to copy a report and working on it for debugging. To do that, for instance to copy the annual
report '2016' into '2016_TEST':

.. code-block:: bash
   
   cp -r /data2/gfzreport/annual/source/2016 /data2/gfzreport/annual/source/2016_TEST 
   cd /data2/gfzreport/annual/source/2016_TEST/
   rm -rf .git

If you executed the above operations as root, remember to:
   
.. code-block:: bash
   
   cd /data2/gfzreport/annual/source
   chown -R sysop:sysop 2016_TEST


Toggle report editability
-------------------------

From within the gui, a report can be "locked", i.e. the report cannot be edited anymore. This
function has no particular consequence or security requirement, it is simply a feature requested
from the library. As such, we made a very simple implementation: for any report directory,
if a file with the same name and the suffix ".locked" exists, the report will be non-editable from within
the GUI. For instance, ZE_2012 is non -editable:

* |DIR| source 

   - |DIR| ZE_2012
   
   - |FILE| ZE_2012.locked
   
   - |DIR| IQ_2009
   
   - |DIR| ...

(see :ref:`serverrootpath` for details).

This makes relatively easy to un-lock a report after has been set non-editable (simply remove the relative .locked file).


Updating this tutorial
----------------------

To update this tutorial online you need to :ref:`updatepythonpackage` first
(do not restart the server yet). Then :ref:`gainrootprivileges`, :ref:`activatevirtualenv` and execute:

.. code-block:: bash

   gfzreport tutorial /var/www/gfzreport/tutorial/html

:ref:`restartserver` and ``exit`` as root user.

Note: the apache configuration file is ``gfzreport-tutorial.conf`` under :ref:`apacheconfavaldir`:

.. code-block:: apache

   Alias /gfzreport/tutorial "/var/www/gfzreport/tutorial/html"
   <Directory "/var/www/gfzreport/tutorial/html">
        Order allow,deny
        Allow from all
   </Directory>

(there is a .htaccess file created by the build process, but it's currently not used.
We use a simple redirection page)

Possible unused files
---------------------

As of November 2017, the following files and directories are not used anymore and should be deleted:

.. code-block:: bash

   /data2/gfz-reportgen_annual/
   /data2/gfz-reportgen/rizac  (but we should also remove the conf available. This I guess was the first report (not editable)
   /data2/gfz-report/  (old directory with the report data)
   /home/sysop/tmp_cesca_report/  (IQ 2009 report source data files)
   /home/sysop/tmp_conffiles/  (or keep it, if we want to copy again conf_files and config.py in there from our sphinx directory)
   





