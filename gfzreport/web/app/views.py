'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
from itertools import izip

from flask.templating import render_template
from flask import abort, send_from_directory, request, jsonify, Blueprint, current_app  # redirect, url_for

from flask_login import current_user, login_required

# from gfzreport.web.app import app
from gfzreport.web.app.core import get_reports, build_report, get_sourcefile_content, \
    get_builddir, save_sourcefile, get_commits, secure_upload_filepath,\
    get_fig_directive, get_log_files_list
from flask_login.utils import login_user
import re
from gfzreport.web.app.models import User, session

# http://flask.pocoo.org/docs/0.12/patterns/appfactories/#basic-factories:
mainpage = Blueprint('main_page', __name__)  # , template_folder='templates')


@mainpage.route('/')
def index():
    return render_template("reportslist.html",
                           title=current_app.config['DATA_PATH'],
                           reports=get_reports(current_app.config['SOURCE_PATH']))


@mainpage.route('/<reportdirname>')
def get_report(reportdirname):
    DEFAULT_START_BUILD_TYPE = 'html'  # FIME: move to config? WHAT IS THIS DOING??
    return render_template("report.html",
                           title=reportdirname,
                           report_id=reportdirname,
                           pagetype=DEFAULT_START_BUILD_TYPE)


@mainpage.route('/<reportdirname>/content/<pagetype>')
def get_report_type(reportdirname, pagetype):
    '''views for the iframes'''
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # This view is restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status. It is then the frontend which will handle
    # this
    if pagetype != 'html' and not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        return abort(401)
    if pagetype in ('html', 'pdf'):
        reportfilename, _ = build_report(reportdirname, pagetype, current_user, force=False)
        return send_from_directory(os.path.dirname(reportfilename),
                                   os.path.basename(reportfilename))
    elif pagetype == 'edit':
        return render_template("editor.html", source_data=get_sourcefile_content(reportdirname))


@mainpage.route('/<reportdirname>/content/<pagetype>/<path:static_file_path>')
def get_report_static_file(reportdirname, pagetype, static_file_path):
    '''views for the static content in iframes'''
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # This view is restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status. It is then the frontend which will handle
    # this
    if pagetype != 'html' and not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        return abort(401)
    if pagetype in ('html', 'pdf'):
        filepath = os.path.join(get_builddir(reportdirname, pagetype), static_file_path)
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
        return abort(401)
    unicode_text = request.get_json()['source_text']
    commits = save_sourcefile(reportdirname, unicode_text, current_user)
    # note that (editable_page.html) we do not actually make use of the returned response value
    return jsonify(commits)  # which converts to a Response


@mainpage.route('/<reportdirname>/get_commits', methods=['POST'])
def get_commits_list(reportdirname):  # do not name get_commits otherwise it overrides core.get_commits
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # This view is restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status. It is then the frontend which will handle
    # this
    if not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        return abort(401)

    commits = get_commits(reportdirname)
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
        return abort(401)

    commit_hash = request.get_json()['commit_hash']
    return jsonify(get_sourcefile_content(reportdirname, commit_hash, as_js=False))


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
        return abort(401)

    buildtype = request.get_json()['buildtype']
    # return a list of tuples to preserve order:
    lizt = [(k, v) for k, v in izip(['Sphinx log', 'PdfLatex log'],
                                    get_log_files_list(reportdirname, buildtype))]
    return jsonify(lizt)


@mainpage.route('/<reportdirname>/upload_file', methods=['POST'])
def upload_file(reportdirname):
    # instead of the decorator @login_required, which handles redirects and makes the view
    # disabled for non-logged-in users, we prefer a lower level approach. First, because
    # some views are restricted depending on pagetype, second because we do not want redirects,
    # but aborting with a 403 (Forbidden) status: it is then the frontend which will handle
    # this
    if not current_user.is_authenticated:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        return abort(401)

    # check if the post request has the file part
    if 'file' not in request.files:
        raise ValueError('No file part')
    upfile = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
    filepath = secure_upload_filepath(reportdirname, upfile.filename)
    upfile.save(filepath)
    if os.path.isfile(filepath):
        return jsonify(get_fig_directive(reportdirname, filepath,
                                         request.form['label'], request.form['caption']))
    else:
        raise ValueError('Error while saving "%s"' % upfile.filename)


@mainpage.route("/<reportdirname>/login", methods=["POST"])
def login(reportdirname):
    """View to process login form data and login user in case.
    """
    email = request.form['email']
    with session(current_app) as sess:
        user = sess.query(User).filter(User.email == email).first()

    if not user:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        return abort(401)
    matching_url = os.path.join(request.url_root, reportdirname)
    if not re.match(user.permission_regex, matching_url):
        return abort(403)
    login_user(user, remember=False)
    return jsonify({})  # FIXME: what to return?
