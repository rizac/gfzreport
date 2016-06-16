'''
Created on Jun 6, 2016

@author: riccardo
'''
import os
# import sys

DEBUG = True  # Turns on debugging features in Flask
# FIXME: what do we use ROOT_DIR for?
# ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
BUILD_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "build"))
SOURCE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "source"))
RST_VERSIONS_PATH = os.path.abspath(os.path.join(os.path.dirname(BUILD_PATH), "_rst_versions"))
RST_VERSIONS_FILENAMES_FORMAT = "{0:05d}"
NETWORKS_TEMPLATES_PATH = os.path.abspath(os.path.join(os.path.dirname(BUILD_PATH), "_templates"))
APP_TEMPLATE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "webapp",
                                                 "templates",
                                                 "editable_page.html"))
REPORT_FILENAME = "report"
# BCRYPT_LEVEL = 12  # Configuration for the Flask-Bcrypt extension
# MAIL_FROM_EMAIL = "robert@example.com" # For use in application emails

EXPLAIN_TEMPLATE_LOADING = True

if os.path.samefile(NETWORKS_TEMPLATES_PATH, os.path.dirname(APP_TEMPLATE_PATH)):
    raise ValueError("Error in config.py: 'NETWORKS_TEMPLATES_PATH' equals to "
                     "'APP_TEMPLATE_PATH' dirname. "
                     "\nPlease change 'NETWORKS_TEMPLATES_PATH' in '%s'" % str(__file__))
