'''
Created on Jun 6, 2016

@author: riccardo
'''
import os, sys

DEBUG = True  # Turns on debugging features in Flask
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
NETWORK_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
REPORT_FILENAME = "report"
# BCRYPT_LEVEL = 12  # Configuration for the Flask-Bcrypt extension
# MAIL_FROM_EMAIL = "robert@example.com" # For use in application emails