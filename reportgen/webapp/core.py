'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
import json
from StringIO import StringIO
import re
from flask.helpers import send_from_directory
# specify here an absolute path RELATIVE TO THE APP DIRECTORY (app.root_dir)
STATICDIR = '../../test-data/build'


def serve_ace(app, dirname, filename):
    abs_path = os.path.abspath(os.path.join(app.root_path, "../../", "ace-builds", dirname))
    return send_from_directory(abs_path, filename)


def serve_static_file(app, dirbasename, filename):
    # print "Ssf: " + os.getcwd()
    if "ace" in filename:
        f = 9
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


def get_source_rst(as_js=True):
    """
        Reads the source rst from the sphinx source file. If the argument is True, returns
        javascript formatted string (e.g., with newlines replaced by "\n" etcetera)
    """

    # FIXME: FIX PATHS!!! FIXME: FIX UNICODE ISSUE (ARE THERE??)
    with open("../test-data/build/_sources/index.txt", "r") as fpoint:
        filecont = fpoint.read()  # .encode('utf8')

    # json dump might do what we want, but it fails with e.g. "===" (rst headers, not javascript
    # equal sign
    sio = StringIO()
    for c in filecont:
        if c == '\n' or c == '\r':
            sio.write("\\")
            c = 'n' if c == '\n' else 'r'
        elif c == '\\' or c == '"':
            sio.write("\\")
        sio.write(c)
    return sio.getvalue()


def get_main_page():
    # print "mp:" + os.getcwd()

    main_page = open("../test-data/build/index.html").read()

    # all this stuff might be achieved via templating systems like jinja2, but unfortunately
    # sphinx is not so flexible. Moreover, we want to preserve the original sphinx html output
    # and modify it only here

    # replace source link with a button
#     main_page = re.sub("<a href=(['\"])_sources/index.txt\\1\\s.*?>Show Source</a>",
#                        "<button class=\"btn btn-primary\">Edit source</button>",
#                        main_page, re.DOTALL)

    # include ace editor:
    # add the editor div inside the body wrapper:
#     main_page = re.sub("<\\s*div\\s+class\\s*=\\s*(['\"]*)bodywrapper\\1\\s*>",
#                        "<div class=\"bodywrapper\">\n<div id=\"editor\"></div>\n",
#                        main_page, re.DOTALL)

    main_page = main_page.replace("$scope.isEditable = false;", "$scope.isEditable = true;")

    main_page = main_page.replace('editor.setValue("");',
                                  'editor.setValue("{0}", 0);'.format(get_source_rst()))

    return main_page
    # return re.sub("<\\s*p(\\s|>)", "<p contenteditable=\"true\"\\1", main_page)
