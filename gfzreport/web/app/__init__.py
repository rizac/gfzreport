import os
from itertools import izip

from flask import Flask
from flask.templating import render_template
from flask import send_from_directory, request, jsonify  # redirect, url_for
from sqlalchemy import create_engine, MetaData, Table

from gfzreport.web.app.core import get_reports, build_report, get_sourcefile_content, \
    get_builddir, save_sourcefile, get_commits, secure_upload_filepath,\
    get_fig_directive, get_log_files_list

from gfzreport.web.app.models import Base
from gfzreport.web.app.models import User
from flask_login.login_manager import LoginManager
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
    app.secret_key = os.urandom(24)

    # we should look at ini file or whatever
    initdb(app)
    initdbusers(app)

    # Note: supply absolute module path. Apache complains tht a config is elsewhere defined
    # in the python path otherwise:
    app.config.from_object('gfzreport.web.config.BaseConfig')
    app.config['DATA_PATH'] = data_path
    app.config['BUILD_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "build"))
    app.config['SOURCE_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "source"))

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
        return User.query.get(int(user_id)) or None  # @UndefinedVariable

    from gfzreport.web.app.views import mainpage
    app.register_blueprint(mainpage)

    return app


def get_db_dir():
    me = os.path.abspath(os.path.realpath(__file__))
    dir_ = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(me)))),
                        'tmp')
    if not os.path.isdir(dir_):
        os.mkdir(dir_)
    return dir_


def initdb(app):
    """Initializes the program db with users and permissions as regex objects
    """
    # config the db. Make the tmp dir (or data?) if not existing, on the app path
    # tmp and data are gitignored.
    # Note: follow a simple approach because we need db storage for simple email configs
    # For info, see (third approach, the simplest):
    # http://flask.pocoo.org/docs/0.12/patterns/sqlalchemy/
    app.engine = create_engine('sqlite:///' + os.path.join(get_db_dir(), "users.sqlite"),
                               convert_unicode=True)
    Base.metadata.create_all(bind=app.engine)


def initdbusers(app):
    """Initializes the users according to the defaultusers in the /tmp directory, if any
    Users will be updated/ added /removed according to the defaultusers.txt file
    """
    con = app.engine.connect()
    file_ = os.path.join(get_db_dir(), "defaultusers.txt")
    if os.path.isfile(file_):
        emails = []
        update = User.update  # @UndefinedVariable
        delete = User.delete  # @UndefinedVariable
        insert = User.insert  # @UndefinedVariable
        select = User.select  # @UndefinedVariable
        email_col = User.c.email  # @UndefinedVariable
        with open(file_, "rb") as opn:
            lne = opn.readline().strip()
            if lne[0] != '#':
                email, perm = lne.split()
                emails.append(email)
                _ = select(email_col == email).execute().first()
                if _ and _.permission_regex != perm:
                    cond = User.permission_regex = perm
                    stmt = update().values(cond).where(User.email == email)
                    con.execute(stmt)
                elif not _:
                    con.execute(insert(), email=email, permission_regex=perm)
        if emails:
            emails = set(emails)
            db_emails = app.engine.execute(select(User.email)).all()
            for email in db_emails:
                if email not in emails:
                    con.execute(delete().where(email_col == email))
