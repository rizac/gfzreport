'''
Created on Jun 6, 2016
Flask config file
@author: riccardo
'''
# http://flask.pocoo.org/docs/0.12/config/#development-production
# The "base" class as base for any report type:
from datetime import timedelta
import os


class BaseConfig(object):
    DEBUG = False
    UPLOAD_ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    UPLOAD_DIR_BASENAME = "_www_uploaded_files"  # in principle, you don't need t change this
    # flask-login settings:
    REMEMBER_COOKIE_DURATION = timedelta(days=1)
