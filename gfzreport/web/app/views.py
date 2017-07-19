'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
from itertools import izip

from flask.templating import render_template
from flask import abort, send_from_directory, request, jsonify, Blueprint, current_app, session  # redirect, url_for

from flask_login import current_user, login_required

# from gfzreport.web.app import app
from gfzreport.web.app.core import get_reports, build_report, get_sourcefile_content, \
    get_builddir, save_sourcefile, get_commits, secure_upload_filepath,\
    get_fig_directive, get_sourcedir, get_buildfile, get_logs_
from flask_login.utils import login_user, logout_user
import re
from gfzreport.web.app.models import User, session as dbsession
from gfzreport.sphinxbuild.main import get_master_doc
import threading
from multiprocessing.pool import ThreadPool

# http://flask.pocoo.org/docs/0.12/patterns/appfactories/#basic-factories:
mainpage = Blueprint('main_page', __name__)  # , template_folder='templates')


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
    # for this one? logout user. This is harsh, but a more detailed implementation would require
    # to copy code from login_user and match against the regexp, and if not redirect to an
    # unauthorized page. As the case where the user jumps from report to another is quite rare,
    # let's be strict and sure:
    if current_user.is_authenticated:
        logout_user()

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
        return render_template("editor.html", source_data=get_sourcefile_content(reportdirname))

    binfo = None  # NOT USED. it might be something like
    # session['buildinginfo'] = BuildingInfo("Building page")
    # but this functionality is not implemented yet

    if pagetype in ('html', 'pdf'):
        ret = build_report(reportdirname, pagetype, current_user, binfo, force=False)
        session['last_build_exitcode'] = ret
        if ret == 2:
            abort(500)  # FIXME: better handling!!
        # binfo('Serving page', None, 0, 0)
        reportfilename = get_buildfile(reportdirname, pagetype)
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


# @mainpage.route('/<reportdirname>/building_info', methods=['POST'])
# def get_building_info(reportdirname):
#     ret = []
#     if current_user.is_authenticated and 'buildinginfo' in session:
#         # calculate the remaining time in the second element, instead of the start time:
#         ret = session['buildinginfo'].tojson()
#     return jsonify(ret)
@mainpage.route('/<reportdirname>/last_build_exitcode', methods=['POST'])
def get_building_info(reportdirname):
    try:
        ret = session['last_build_exitcode']
    except:
        ret = -1
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
        abort(401)
    unicode_text = request.get_json()['source_text']
    result = save_sourcefile(reportdirname, unicode_text, current_user)
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
        abort(401)

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
        abort(401)

    buildtype = request.get_json()['buildtype']
    return jsonify(get_logs_(reportdirname, buildtype))


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
    with dbsession(current_app) as sess:
        user = sess.query(User).filter(User.email == email).first()

    if not user:
        # 403 Forbidden (e.g., logged in but no auth), 401: Unauthorized (not logged in)
        abort(401)

    matching_url = os.path.join(request.url_root, reportdirname)
    if not re.match(user.permission_regex, matching_url):
        abort(403)

    login_user(user, remember=False)
    return jsonify({})  # FIXME: what to return?


@mainpage.route("/<reportdirname>/logout", methods=["POST"])
def logout(reportdirname):
    """View to process login form data and login user in case.
    """
    # writing to files because it raises
    del session['last_build_exitcode']
    logout_user()
    return jsonify({})  # FIXME: what to return?
