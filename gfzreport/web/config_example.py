'''
Created on Jun 6, 2016
Flask config file
@author: riccardo
'''
# http://flask.pocoo.org/docs/0.12/config/#development-production
# The "base" class as base for any report type:
from datetime import timedelta
# import os


class BaseConfig(object):
    DEBUG = False
    UPLOAD_ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    UPLOAD_DIR_BASENAME = "_www_uploaded_files"  # in principle, you don't need t change this
    # flask-login settings:
    # ~~~~~~~~~~~~~~~~~~~~~
    # currently not used (login_user(user, remember=False) in views), but let's implement anyway:
    REMEMBER_COOKIE_DURATION = timedelta(days=1)
    # this sets the lifetime of a session when logged in. Note that the
    # the session cookie is set to expire when browser closes. If we want different behaviour
    # we should set session.permanent = True after login. For info see:
    # https://stackoverflow.com/questions/13831251/flask-login-chrome-ignoring-cookie-expiration
    # https://stackoverflow.com/questions/34118093/flask-permanent-session-where-to-define-them
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
