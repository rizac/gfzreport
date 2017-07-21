import os
from itertools import izip

import shlex

from flask import Flask
from flask.templating import render_template
from flask import send_from_directory, request, jsonify  # redirect, url_for
from flask_login.login_manager import LoginManager

from sqlalchemy import create_engine, MetaData, Table

# from gfzreport.web.app.core import get_reports, build_report, get_sourcefile_content, \
#     get_builddir, save_sourcefile, get_commits, secure_upload_filepath,\
#     get_fig_directive, get_log_files_list

from gfzreport.web.app.models import Base, User, session
import json

# from flask import url_for
# from flask import request
# app = Flask(__name__, static_folder=None)  # static_folder=None DOES TELL FLASK NOT TO ADD ROUTE
# FOR STATIC FOLDEERS


def get_app(config_obj='gfzreport.web.config.BaseConfig', data_path=None,
            db_path=None):
    '''
    initializes the app and setups the blueprint on it
    :param config: string, A valid argument for `app.config.from_object`.
    Specifying other paths allows us to run tests with a given external python file
    :param data_path: the data source path. The directory should have a 'source' subdirectory
    where any folder not starting with "_" will be interpreted as a report and accessible
    trhough an endpoint url. If None, the environment variable 'DATA_PATH' must be set, otherwise
    an Exception is raised
    :param db_path: the path for the Users database. It must denote a directory where the db
    will be retrieved or created. If the file 'users.txt' is also present inside the directory,
    it will be used to set/update/delete database users. If this argument is missing (None), and
    the environment variable DB_PATH is set, the latter will be used.
    If this argument is None or does not point to any existing directory, no database will be
    created
    '''
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
    app.secret_key = os.urandom(24)

    # Note: supply absolute module path. Apache complains tht a config is elsewhere defined
    # in the python path otherwise:
    app.config.from_object(config_obj)
    app.config['REPORT_BASENAMES'] = {}  # will be populatedwhen querying pages

    app.config['DATA_PATH'] = data_path
    app.config['BUILD_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "build"))
    app.config['SOURCE_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "source"))

    # we should look at ini file or whatever
    if db_path is None and 'DB_PATH' in os.environ:
        db_path = os.environ['DB_PATH']
    app.config['DB_PATH'] = db_path
    initdb(app)
    initdbusers(app)

    # Flask-Login Login Manager
    login_manager = LoginManager()
    # Tell the login manager where to redirect users to display the login page
    # login_manager.login_view = "/login/"
    # Setup the login manager.
    login_manager.setup_app(app)
    # https://github.com/maxcountryman/flask-login/blob/master/docs/index.rst#session-protection:
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):
        with session(app) as sess:
            return sess.query(User).filter(User.id == int(user_id)).first()

    from gfzreport.web.app.views import mainpage
    app.register_blueprint(mainpage)

    return app


# def get_db_dir():
#     me = os.path.abspath(os.path.realpath(__file__))
#     dir_ = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(me)))),
#                         'tmp')
#     if not os.path.isdir(dir_):
#         os.mkdir(dir_)
#     return dir_

def _dbpath(app):
    try:
        dbpath = app.config['DB_PATH']
        if os.path.isdir(dbpath):
            return dbpath
    except KeyError:
        return None


def initdb(app):
    """Initializes the program db with users and permissions as regex objects
    """
    dbpath = _dbpath(app)
    if not dbpath:
        return
    # config the db. Make the tmp dir (or data?) if not existing, on the app path
    # tmp and data are gitignored.
    # Note: follow a simple approach because we need db storage for simple email configs
    # For info, see (third approach, the simplest):
    # http://flask.pocoo.org/docs/0.12/patterns/sqlalchemy/
    app.engine = create_engine('sqlite:///' + os.path.join(dbpath, "users.sqlite"),
                               convert_unicode=True)
    Base.metadata.create_all(bind=app.engine)


def initdbusers(app):
    """Initializes the users according to the json uers file
    Users will be updated/ added /removed according to the file
    """
    dbpath = _dbpath(app)
    if not dbpath:
        return
    file_ = os.path.join(dbpath, "users.txt")
    if not os.path.isfile(file_):
        return
    with session(app) as sess:
        jsonfile_emails = []
        jsonlines = []
        with open(file_, "r") as opn:
            for line in opn:
                if not line.strip().startswith('#'):
                    jsonlines.append(line)
        users = json.loads("\n".join(jsonlines))
        docommit = False
        for jsonuser in users:
            user = User(**jsonuser)
            email = user.email
            if not email or '@' not in email[1:-1]:
                continue
            jsonfile_emails.append(email)
            dbuser = sess.query(User).filter(User.email == email).first()
            if dbuser and user.path_restriction_reg != dbuser.path_restriction_reg:
                dbuser.path_restriction_reg = user.path_restriction_reg
                sess.commit()  # need to commit now otherwise dbuser instance might be replaced?
            elif not dbuser:  # new user
                docommit = True
                sess.add(user)
        if docommit:
            sess.commit()  # commit once now
            docommit = False
        # now delete unused users:
        if jsonfile_emails:
            jsonfile_emails = set(jsonfile_emails)
            for dbuser in sess.query(User):
                if dbuser.email not in jsonfile_emails:
                    docommit = True
                    sess.delete(dbuser)
        if docommit:
            sess.commit()  # commit once now
