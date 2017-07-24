'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
from datetime import datetime

from flask.templating import render_template
from flask import abort, send_from_directory, request, jsonify, Blueprint, current_app, \
    session  # redirect, url_for
from flask_login import current_user
from flask_login.utils import login_user, logout_user

# from gfzreport.web.app import app
from gfzreport.web.app.core import get_reports, build_report, get_sourcefile_content, \
    get_builddir, save_sourcefile, get_commits, secure_upload_filepath,\
    get_fig_directive, get_sourcedir, get_buildfile, get_logs_, lastbuildexitcode
from gfzreport.web.app.models import User, session as dbsession


# http://flask.pocoo.org/docs/0.12/patterns/appfactories/#basic-factories:
mainpage = Blueprint('main_page', __name__)  # , template_folder='templates')


# define a custom exception that will be forwarded as a response with a given message
# parameter. This is the exception that we control, i.e. that we deliberately raise
# For info see (code mostly copied from there):
# http://flask.pocoo.org/docs/0.12/patterns/apierrors/
class AppError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload  # what is this for? see link above

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@mainpage.errorhandler(AppError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

# Now we can raise AppError with our given message


@mainpage.route('/')
def index():
    return render_template("reportslist.html",
                           title=current_app.config['DATA_PATH'],
                           reports=get_reports(current_app.config['SOURCE_PATH']))


# FIXME: WITH THIS ROUTE /reportdirname is redirected here, AND ALSO
# ALL angular endpoints do not need the /reportdirname/. That is issuing a 
# content/<pagetype> from within angular redirects to the view below, without the need
# of specifying /reportdirname/ before. Tests on the other hand must be written
# with follow_redirects=True
@mainpage.route('/<reportdirname>/')
def get_report(reportdirname):
    # what if the user moved from a link to another and it had permission for the first but not
    # for this one? Well, it turns out that we do not need to care about it,
    # (probably due to login_user(...remember=False), but doc is inconistent:
    # https://flask-login.readthedocs.io/en/latest/#flask_login.login_user VS
    # https://flask-login.readthedocs.io/en/latest/#remember-me)

    # return the normal way
    return render_template("report.html",
                           title=reportdirname,
                           report_id=reportdirname,
                           pagetype="html")


# slash at the end: this way the routes defined in the next view are pointing to the right location
# FIXME: why?!!!
@mainpage.route('/<reportdirname>/content/<pagetype>/')
def get_report_type(reportdirname, pagetype):
    '''views for the iframes'''
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # This view is restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status. It is then the frontend which will handle
    # this
    if pagetype != 'html' and not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)

    if pagetype == 'edit':
        return render_template("editor.html", source_data=get_sourcefile_content(current_app,
                                                                                 reportdirname))

    binfo = None  # NOT USED. it might be something like
    # session['buildinginfo'] = BuildingInfo("Building page")
    # but this functionality is not implemented yet

    if pagetype in ('html', 'pdf'):
        try:
            ret = build_report(current_app, reportdirname, pagetype, current_user, binfo, force=False)
        except Exception as exc:
            # raises if gitcommit raises
            raise AppError(str(exc), 500)

        # session['last_build_exitcode'] = ret
        if ret == 2:
            return render_template("buildfailed.html", pagetype=pagetype)

        # binfo('Serving page', None, 0, 0)
        reportfilename = get_buildfile(current_app, reportdirname, pagetype)
        response = send_from_directory(os.path.dirname(reportfilename),
                                       os.path.basename(reportfilename))
        if pagetype == 'pdf':
            # https://stackoverflow.com/questions/18281433/flask-handling-a-pdf-as-its-own-page
            response.headers['Content-Type'] = 'application/pdf'
            # 'inline' to 'attachment' if you want the file to download rather than display
            # in the browser:
            response.headers['Content-Disposition'] = \
                'inline; filename=%s.pdf' % reportdirname

        return response


@mainpage.route('/<reportdirname>/last_build_exitcode', methods=['POST'])
def get_last_build_exitcode(reportdirname):
    buildtype = request.get_json()['buildtype']
    ret = lastbuildexitcode(current_app, reportdirname, buildtype)
    return jsonify(ret)


@mainpage.route('/<reportdirname>/content/<pagetype>/<path:static_file_path>')
def get_report_static_file(reportdirname, pagetype, static_file_path):
    '''views for the static content in iframes'''
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # This view is restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status. It is then the frontend which will handle
    # this

    # Note: pagetype might be also "_static"
    if pagetype != 'html' and not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)
    if pagetype in ('html', 'pdf'):
        filepath = os.path.join(get_builddir(current_app, reportdirname, pagetype), static_file_path)
        return send_from_directory(os.path.dirname(filepath), os.path.basename(filepath))


@mainpage.route('/<reportdirname>/save', methods=['POST'])
def save_report(reportdirname):
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # This view is restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status. It is then the frontend which will handle
    # this
    if not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)
    unicode_text = request.get_json()['source_text']
    try:
        result = save_sourcefile(current_app, reportdirname, unicode_text, current_user)
    except Exception as exc:
        # raises if gitcommit raises
        appendix = ("This is an unexpected server error: we suggest you to select the editor "
                    "text and copy it to keep your changes, log out and log in again. "
                    "If the problem persists, please contact the administrator")
        raise AppError("%s. %s" % (str(exc), appendix), 500)

    # note that (editable_page.html) we do not actually make use of the returned response value
    return jsonify(result)  # which converts to a Response


@mainpage.route('/<reportdirname>/get_commits', methods=['POST'])
def get_commits_list(reportdirname):  # dont use get_commits otherwise it overrides core.get_commits
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # This view is restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status. It is then the frontend which will handle
    # this
    if not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)

    commits = get_commits(current_app, reportdirname)
    # note that (editable_page.html) we do not actually make use of the returned response value
    return jsonify(commits)  # which converts to a Response


@mainpage.route('/<reportdirname>/get_source_rst', methods=['POST'])
def get_source_rst(reportdirname):
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # This view is restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status. It is then the frontend which will handle
    # this
    if not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)

    commit_hash = request.get_json()['commit_hash']
    return jsonify(get_sourcefile_content(current_app, reportdirname, commit_hash, as_js=False))


@mainpage.route('/<reportdirname>/get_logs', methods=['POST'])
def get_logs(reportdirname):
    '''returns a list of (name, content) tuples, where name is the log name and
    content is the relative log content. The tuples are two, representing
    the sphinx log file and the pdflatex log file, respectively'''
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # This view is restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status. It is then the frontend which will handle
    # this
    if not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)

    buildtype = request.get_json()['buildtype']
    return jsonify(get_logs_(current_app, reportdirname, buildtype))


@mainpage.route('/<reportdirname>/upload_file', methods=['POST'])
def upload_file(reportdirname):
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # some views are restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status: it is then the frontend which will handle
    # this
    if not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)

    # check if the post request has the file part
    if 'file' not in request.files:
        raise AppError('No file part')
    upfile = request.files['file']

    for txt in ('label', 'caption'):
        if txt not in request.form:
            raise AppError("'%s' not specified")

    # if user does not select file, browser also
    # submit a empty part without filename
    try:
        filepath = secure_upload_filepath(current_app, reportdirname, upfile)
    except ValueError as vexc:
        raise AppError(str(vexc), 400)
    except Exception as exc:
        raise AppError(str(exc), 500)

    return jsonify(get_fig_directive(current_app, reportdirname, filepath,
                                     request.form['label'], request.form['caption']))


@mainpage.route("/<reportdirname>/login", methods=["POST"])
def login(reportdirname):
    """View to process login form data and login user in case.
    """
    email = request.form['email']
    with dbsession(current_app) as sess:
        user = sess.query(User).filter(User.email == email).first()

        if not user:
            # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
            raise AppError("'%s' not registered" % email, 401)

        sourcepath = os.path.abspath(get_sourcedir(current_app, reportdirname))
        if not user.is_authorized(sourcepath):
            raise AppError("'%s' registered but not authorized to access this report" % email, 403)

        dbuser = sess.query(User).filter((User.email != email) &
                                         (User.login_date != None) &  # @IgnorePep8
                                         (User.editing_path == sourcepath)).first()
        if dbuser:
            msg = ("'%s' registered but conflict detected: user '%s' (logged in on %s) is "
                   "currently editing the same report "
                   "(or forgot to log out)") % (email, dbuser.gitname, dbuser.login_date)
            raise AppError(msg, 409)  # 409: conflict

        login_user(user, remember=False)

        # now write data to the db (user active on current page).
        # THIS IS AFTER LOGIN so if login failed we do not write anything
        user.login_date = datetime.utcnow()
        user.editing_path = sourcepath
        sess.commit()

    return jsonify({})  # FIXME: what to return?


@mainpage.route("/<reportdirname>/logout", methods=["POST"])
def logout(reportdirname):
    """View to process login form data and login user in case.
    """
    try:
        # writing to files because it raises
        with dbsession(current_app) as sess:
            dbuser = sess.query(User).filter(User.id == current_user.id).first()
            if dbuser:
                # should be already abspath, however for safety (we will use the path for comparison
                # with other users logging in, so better be safe):
                dbuser.editing_path = None
                dbuser.login_date = None
                sess.commit()
    except:
        pass  # FIXME: better handling?
    finally:
        logout_user()

    return jsonify({})  # FIXME: what to return?
