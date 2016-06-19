'''
Created on Jun 6, 2016
Flask config file
@author: riccardo
'''
import os


DEBUG = True  # Turns on debugging features in Flask

# the root path to the data directory. Herein we will store sources rst, builds (html/latex/pdf)
# web templates, old rst versions etcetera. Basically, ALL
# IN PRINCIPLE, FOR DEPLOYMENT YOU HAVE TO MODIFY THIS VARIABLE ONLY (AND set to False THE DEBUG
# VARIABLE DEFINED ABOVE)
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))

# the main file denoting the generated report. I.e., for all build folders, it is assumed that the
# sphinx-generated file will have this name. Its extension will be retrieved according to the
# use-case (e.g., locate the pdf oputput of sphinx with:
# BUILD_PATH + "/latex/" + app.config['REPORT_FILENAME'] + ".pdf"
# This might be automated in the future by parsing each sphinx config file. Just remember that
# changing the build filename in the config file must be changed also here
REPORT_FILENAME = "report"

# these are the NAMES of the folder where to store specific data
# the build folder under DATA_PATH: here are ouput the sphinx builds
BUILD_PATH = os.path.abspath(os.path.join(DATA_PATH, "build"))
SOURCE_PATH = os.path.abspath(os.path.join(DATA_PATH, "source"))
RST_VERSIONS_PATH = os.path.abspath(os.path.join(os.path.dirname(BUILD_PATH), "_rst_versions"))
NETWORKS_TEMPLATES_PATH = os.path.abspath(os.path.join(os.path.dirname(BUILD_PATH), "_templates"))

# this is the path to the file defining the APP template path
# For each sphinx html build, when we query the html page, the html is parsed INTO A jinja
# TEMPLATE (by using some comments produced in the network report generation and converting
# them to jinja blocks) which acts as a BASE template. The file stored here below will
# INHERIT from that base template and both templates will be put into NETWORKS_TEMPLATES_PATH
# defined above
# The purpose of all this mess is that, by editing the file located below, we can setup
# with a templating system how all html pages are displayed (for instance, angular and ace editor
# are implemented in the file below, not in the original sphinx-generated html, which is not
# supposed to be editable)
APP_TEMPLATE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "webapp",
                                                 "templates",
                                                 "editable_page.html"))

# last check about paths conflicts: FIXME: maybe better handling?
if os.path.samefile(NETWORKS_TEMPLATES_PATH, os.path.dirname(APP_TEMPLATE_PATH)):
    raise ValueError("Error in config.py: 'NETWORKS_TEMPLATES_PATH' equals to "
                     "'APP_TEMPLATE_PATH' dirname. "
                     "\nPlease change 'NETWORKS_TEMPLATES_PATH' in '%s'" % str(__file__))

# other stuff (unused, google for info if needed)
# BCRYPT_LEVEL = 12  # Configuration for the Flask-Bcrypt extension
# MAIL_FROM_EMAIL = "robert@example.com" # For use in application emails
# EXPLAIN_TEMPLATE_LOADING = True
