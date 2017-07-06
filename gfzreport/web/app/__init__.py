import os
from flask import Flask
from flask.templating import render_template
from flask import send_from_directory, request, jsonify  # redirect, url_for
from gfzreport.web.app.core import get_reports, build_report, get_sourcefile_content, \
    get_builddir, save_sourcefile, get_commits, secure_upload_filepath,\
    get_fig_directive, get_log_files_list
from itertools import izip
# from flask import url_for
# from flask import request
# app = Flask(__name__, static_folder=None)  # static_folder=None DOES TELL FLASK NOT TO ADD ROUTE
# FOR STATIC FOLDEERS


def get_app(data_path=None):
    if data_path is None:
        if 'DATA_PATH' not in os.environ or not os.environ['DATA_PATH']:
            raise ValueError(("You need to set the environment variable DATA_PATH "
                              "pointing to a valid folder where source and build files will "
                              "be processed"))
        data_path = os.environ['DATA_PATH']

    if not os.path.isdir(data_path):
        raise ValueError("Not a directory: DATA_PATH='%s'\n"
                         "Please change environment variable 'DATA_PATH'" % str(data_path))

    app = Flask(__name__)

    # Note: supply absolute module path. Apache complains tht a config is elsewhere defined
    # in the python path otherwise:
    app.config.from_object('gfzreport.web.config.BaseConfig')
    app.config['DATA_PATH'] = data_path
    app.config['BUILD_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "build"))
    app.config['SOURCE_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "source"))

    from gfzreport.web.app.views import mainpage
    app.register_blueprint(mainpage)

    return app
