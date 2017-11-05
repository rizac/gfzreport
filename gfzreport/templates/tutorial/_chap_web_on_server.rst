
.. _webserver:

GfzReport-Web tutorial (on current server)
==========================================

The :ref:`gfzw` is currently installed at GFZ on `st161dmz`. This is a fast tutorial
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

      
Update the python package
-------------------------

When the package is modified, we need to update the server version. Firs :ref:`activatevirtualenv`.
Then:

.. code-block:: bash

   cd /var/www/html/gfz-reportgen
   git pull
   
The package is installed as editable, meaning that all modifications will take place without the
need to re-install :ref:`gfzr`. In some rare cases, when something in setup.py has changed,
you can re-install it via:

.. code-block:: bash

   cd /var/www/html/gfz-reportgen
   pip install -e .

and :ref:`restartserver`

.. _restartserver:

Restart the server
------------------

You need root privileges.

.. code-block:: bash

   su
   Password: [TYPE PASSWORD]
   service apache2 reload


.. _serverrootpath:

Root sata path
--------------

All :ref:`gfzr` data files are located at:

.. code-block:: bash
   
   /data2/gfzreport

The directory structure (see :ref:`webappdatapath`) is:
   
   * |DIR| /data2/gfzreport
  
         
      * |FILE| users.sqlite (the db storing users and sessions)
           
      * |FILE| users.txt (text json file where to add/remove/edit users)
      
      * |DIR| network (network report directory)
      
         * |DIR| source (:ref:`webappdatapath` for the network report)
         
            * |DIR| ZE_2012
            
            * |DIR| IQ_2009
            
            * |DIR| ...
            
         * |DIR| build  (:ref:`webappdatapath` for the network report)
            
            * |DIR| ZE_2012
            
            * |DIR| IQ_2009
            
            * |DIR| ...
                
      * |DIR| annual (annual report directory)
         * |DIR| source (:ref:`srcdir`)
         
            * |DIR| 2016
            
            * |DIR| 2017
            
            * |DIR| ...
            
         * |DIR| build  (:ref:`builddir` s)
            
            * |DIR| 2016
            
            * |DIR| 2017
            
            * |DIR| ...



.. _wsgisfiles:

Wsgis directory
---------------

All :ref:`gfzw` wsgis files are located at:

.. code-block:: bash
   
   /var/www/html/gfz-reportgen/wsgis/
   
Apache conf directory
---------------------

All Apache configuration files are located at:

.. code-block:: bash
   
   /etc/apache2/conf-available/

Create a new report template (network report)
---------------------------------------------

This is the same operation described in :ref:`createnewtemplate`, but specific the (semi-automatic)
creation of web-editable Gfz network reports.

We assume that a network name (e.g., 'ZE') and a network start year are given (e.g., 2012).
Ask the GEOFON responsible (currently Susanne) to produce the noise pdfs
and the instrument uptimes figure for you (this procedure could be in the future automatized and
implemented in :ref:`gfzt`)
Pdfs should have the format:

[station]-[channel].png

or, for stations with the same name:

[station]-[channel]-1.png, [station]-[channel]-1.png

(the number indicates the station start time, in increasing order).

Actually, "-" needs to be a sequence of one or more non-alphanumeric characters.

The instrument uptime figure can have any name.

Then choose a temp directory. Currently, we use directories of the type:

.. code-block:: bash
   
   /home/sysop/tmp_*

So for instance assuming the following data directories:

.. code-block:: bash
   
   /home/sysop/tmp_ZE
   /home/sysop/tmp_ZE/pdfs [directory of the noise pdfs]
   /home/sysop/tmp_ZE/uptime.png  [file of the instrument uptime]
   

You MUST :ref:`activatevirtualenv` and proceed as in :ref:`createnewtemplate` but with the
-o option pointing to the 'source' directory of the network :ref:`webappdatapath`,
:ref:`serverrootpath`/network/source:

.. code-block:: bash
   
   gfzreport template n -n ZE -s 2012 -p /home/sysop/tmp_ZE/pdfs -i /home/sysop/tmp_ZE/uptime.png \
      -o /data2/gfzreport/network/source

This creates the directory :ref:`serverrootpath`/network/source/ZE_2012

If there are users who need to edit the resport and do not have authorization, then
:ref:`modifydbusers`, otherwise :ref:`restartserver`.

Check that at http://st161dmz/gfzreport/network there is the button
corresponding to the newly created report


Notes: DO NOT USE WILDCARDS IN UNIX IT EXPANDS , OR escape them IN UNIX
SOLVE PROBLEM ‘’UserWarning: Matplotlib is building the font cache using fc-list. This may take a moment.”:
TODO: output template creation written to vim /data2/gfzreport/network/source/_template_gen_outputs.txt

.. _modifydbusers:

Modify users
------------

Go to :ref:`serverrootpath` and open with (e.g. vim), users.txt. There you will 
see :ref:`webappusers` for details) a json-like file. It is an array (list) of user, each
user being a json object (python dict). 

You normally want to add a user. Then add a line to the list such as:

.. code-block:: python

   [
     ...
     {"email": "tom@mysite.com", "path_restriction_reg": "/abc*$"}
   ]

Where "path_restriction_reg" indicates the authorization of the given user 'tom' (if missing, the user
has no restriction to editing). It is matched (using python `re.search` against each subdirectory
of each 'source' directory of each 'source' found in :ref:`datapath`.
You can also delete a line to delete the given user, or change "path_restriction_reg" for
an existing user.

To have the modification take effect, :ref:`restartserver` 

Install the web application on Apache
-------------------------------------

This should be the first section. However, as it was done once and should not be a problem
on the server, we collected some notes for future installations. Here what we did:

.. code-block:: bash
   
   install package as editable.
   Git pull on the gfzreport package to refresh new updates (restart apache in case)
   
   Create a folder wsgis (currently in the same git dir, untracked)
   Create the wsgis file you need by copying example.wsgi (and changing the paths accordingly), edit them
   current data path: /data2/gfzreport/network
   current db path: /data2/gfzreport  (users.sqlite will be created there)
   
   create users.txt in db path (see example.users.txt)
   
   
   Add apache cons files pointing to those wsgis
   
   Debug apache2 from the terminal:
   
   tail -f /var/log/apache2/error.log
   
   RESTART APACHE SERVER:
   service apache2 restart


Possible unused files
---------------------

The following files/ directories are not used anymore and should be deleted:

.. code-block:: bash

   /data2/gfz-reportgen_annual/
   /data2/gfz-reportgen/rizac  (but we should also remove the conf available. This I guess was the first report (not editable)
   /data2/gfz-report/  (old directory with the report data)
   /home/sysop/tmp_cesca_report/  (when simone report is done)
   /home/sysop/tmp_conffiles/  (or keep it, if we want to copy again conf_files and config.py in there from our sphinx directory)
   





