'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
import re
from flask.helpers import send_from_directory
# specify here an absolute path RELATIVE TO THE APP DIRECTORY (app.root_dir)
STATICDIR = '../build'


def serve_static_file(app, dirbasename, filename):
    # Let's work with absolute paths: send_from_directory checks if the file exists
    # RELATIVE to the running module (usually run.py or whatever), and then calls
    # helpers.send_file. HOWEVER, if the file path is not absolute, the latter NORMALIZES
    # it RELATIVE TO THE ROOT APPLICATION (app.root_path)
    # see flask.helpers line 496
    path = os.path.join(STATICDIR, dirbasename)
    abs_path = os.path.abspath(os.path.join(app.root_path, path))
    # copied from flask.app.send_static_file:
    # *actually commented out, as the default is to do it in send_from_directory
    # cache_timeout = app.get_send_file_max_age(filename)

    return send_from_directory(abs_path, filename)  # , cache_timeout=cache_timeout)


def get_main_page():
    main_page = open("build/index.html").read()
    return main_page
    # return re.sub("<\\s*p(\\s|>)", "<p contenteditable=\"true\"\\1", main_page)
