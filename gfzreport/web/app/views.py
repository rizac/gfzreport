'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
from datetime import datetime, timedelta

from flask.templating import render_template
from flask import abort, send_from_directory, request, jsonify, Blueprint, current_app, \
    session, make_response  # redirect, url_for
from flask_login import current_user
from flask_login.utils import login_user, logout_user

# from gfzreport.web.app import app
from gfzreport.web.app.core import get_reports, build_report, get_sourcefile_content, \
    get_builddir, save_sourcefile, get_commits, secure_upload_filepath,\
    get_fig_directive, get_sourcedir, get_buildfile, get_logs_, lastbuildexitcode, nocache,\
    get_git_diff
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


@mainpage.route('/<reportdirname>/<pagetype>/<path:static_file_path>')
def get_report_static_file(reportdirname, pagetype, static_file_path):
    '''views for the static content in iframes AND main page'''
    # So, we are here for two reasons: static files within sub-pages (html, pdf)
    # or static file within main page. We have this problem because the app static files
    # depth match our view depth:
    # /ZE_2012/html/_static/mystyle.css   # this is a static file for a subpage
    # /static/css/webapp.css             # this is a static file for the main page
    # The problem is not easy, we might solve it by specifying, as we did before,
    # a different path depth for our views, such as (see view below):
    # @mainpage.route('/<reportdirname>/content/<pagetype>')
    # and changing in myapp.js the 'src' properties of the iframes, or leave as it is
    # This way, we could get rid of the first if branch below, where we check if the path
    # is for static data.
    # We prefer the second because, even if more prone to errors, is documented here and we should
    # not have surprises if changing the urls views. For info see:
    # https://stackoverflow.com/questions/17135006/url-routing-conflicts-for-static-files-in-flask-dev-server

    if current_app.static_url_path == "/" + reportdirname:  # check for static path.
        # this relies on the fact that no pagetype is "static", which should be fine
        # (currently they are 'pdf' or 'html')
        return current_app.send_static_file(os.path.join(pagetype, static_file_path))

    # Note: pagetype might be also "_static"
    if pagetype != 'html' and not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)
    if pagetype in ('html', 'pdf'):
        filepath = os.path.join(get_builddir(current_app, reportdirname, pagetype), static_file_path)
        return send_from_directory(os.path.dirname(filepath), os.path.basename(filepath))


# slash at the end: this way the routes defined in the next view are pointing to the right location
# FIXME: why?!!!
@mainpage.route('/<reportdirname>/<pagetype>/')
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
        # force non cache. Note that get requests can be cached, whereas post requests are
        # never cached (unless we set the appropriate content headers). Thus, let's be sure
        # that we never cache "edit", "pdf" and "html" pages cause they are get requests
        # for all other views defined here, as they are post, we should be fine
        # Note that we need to use make_response cause render_template returns a string
        template = render_template("editor.html",
                                   source_data=get_sourcefile_content(current_app, reportdirname))
        return nocache(make_response(template))

    if pagetype in ('html', 'pdf'):
        try:
            ret = build_report(current_app, reportdirname, pagetype, current_user, force=False)
        except Exception as exc:
            # raises if gitcommit raises
            raise AppError(str(exc), 500)

        # session['last_build_exitcode'] = ret
        if ret == 2:
            return render_template("buildfailed.html", pagetype=pagetype)

        if pagetype == 'pdf':
            # this will render a page that will in turn call get_pdf_object
            # the nocache wrapper is set inthere
            return render_template("pdf.html", reportdirname=reportdirname)
        else:
            reportfilename = get_buildfile(current_app, reportdirname, pagetype)
            # force non cache. Note that get requests can be cached, whereas post requests are
            # never cached (unless we set the appropriate content headers). Thus, let's be sure
            # that we never cache "edit", "pdf" and "html" pages cause they are get requests
            # for all other views defined here, as they are post, we should be fine
            response = nocache(send_from_directory(os.path.dirname(reportfilename),
                                                   os.path.basename(reportfilename)))

        return response


@mainpage.route('/<reportdirname>/pdf/document')
def get_pdf_object(reportdirname):
    '''This is called from the embed or object tag within the pdf.html page to load the pdf'''
    # Copied and modified from:
    # https://stackoverflow.com/questions/18281433/flask-handling-a-pdf-as-its-own-page
    pagetype = 'pdf'  # keep pagetype as variable, although it is useless
    reportfilename = get_buildfile(current_app, reportdirname, pagetype)
    # force non cache. Note that get requests can be cached, whereas post requests are
    # never cached (unless we set the appropriate content headers). Thus, let's be sure
    # that we never cache "edit", "pdf" and "html" pages cause they are get requests
    # for all other views defined here, as they are post, we should be fine
    response = nocache(send_from_directory(os.path.dirname(reportfilename),
                                           os.path.basename(reportfilename)))
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


@mainpage.route('/<reportdirname>/get_git_diff', methods=['POST'])
def get_git_diffs(reportdirname):
    if not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)

    rjson = request.get_json()
    commits = get_git_diff(current_app, reportdirname, rjson['commit1'], rjson['commit2'])
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
            raise AppError("User '%s' not registered" % email, 401)

        sourcepath = os.path.abspath(get_sourcedir(current_app, reportdirname))
        if not user.is_authorized(sourcepath):
            raise AppError("User '%s' not authorized to access this report" % email, 403)

        dbuser = sess.query(User).filter((User.email != email) &
                                         (User.login_date != None) &  # @IgnorePep8
                                         (User.editing_path == sourcepath)).first()

        if dbuser:
            msg = ''
            rem_timedelta = current_app.config['PERMANENT_SESSION_LIFETIME'] - \
                (datetime.utcnow() - dbuser.login_date)
            if rem_timedelta.total_seconds() <= 0:
                try:
                    _logout(dbuser.id)
                except Exception as exc:
                    msg = ("Conflict: user '%s' is editing the same report, his/her session"
                           "expired but could not log him/her out: "
                           "%s") % (dbuser.gitname, str(exc))
            else:
                tdstr = timedelta(seconds=round(rem_timedelta.total_seconds()))
                msg = ("Conflict: user '%s' is editing the same report (or forgot "
                       "to log out): by default, his/her session will expire in "
                       "%s") % (dbuser.gitname, str(tdstr))
            if msg:
                raise AppError(msg, 409)  # 409: conflict

        if login_user(user, remember=False):
            # now write data to the db (user active on current page).
            # THIS IS AFTER LOGIN so if login failed we do not write anything
            user.login_date = datetime.utcnow()
            user.editing_path = sourcepath
            sess.commit()
        else:
            msg = ("User '%s' is inactive. Possible reasons: user not authenticated, user "
                   "account not activated or rejected (e.g., user suspended) ") % (email)
            raise AppError(msg, 401)  # 401: Unauthorized

    return jsonify({})  # FIXME: what to return?


@mainpage.route("/<reportdirname>/logout", methods=["POST"])
def logout(reportdirname):
    """View to process login form data and login user in case.
    """
    try:
        _logout(current_user.id)
    except:
        pass  # FIXME: better handling?
    finally:
        logout_user()

    return jsonify({})  # FIXME: what to return?


def _logout(user_id):
    """Sets the attributes to the user identified by user_id to be recognized later as
    not logged in. Raises SqlAlchemy error in case of db errors.
    :return: True if the user with `user_id` was found and the db session has been succesfully
    committed, False if the user with `user_id` was not found
    """
    # writing to files because it raises
    with dbsession(current_app) as sess:
        dbuser = sess.query(User).filter(User.id == user_id).first()
        if dbuser:
            # should be already abspath, however for safety (we will use the path for comparison
            # with other users logging in, so better be safe):
            dbuser.editing_path = None
            dbuser.login_date = None
            sess.commit()
            return True
        else:
            return False
