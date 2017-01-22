'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
from reportwebapp.webapp import app
from flask.templating import render_template
from flask import send_from_directory, request, jsonify  # redirect, url_for
from reportwebapp.webapp.core import get_reports, build_report, get_sourcefile_content, \
    get_builddir, save_sourcefile, get_commits, secure_upload_filepath,\
    get_fig_directive


@app.route('/')
def index():
    return render_template("reportslist.html",
                           title=app.config['DATA_PATH'],
                           reports=get_reports(app.config['SOURCE_PATH']))


@app.route('/<reportdirname>')
@app.route('/<reportdirname>/')
def get_report(reportdirname):
    DEFAULT_START_BUILD_TYPE = 'html'  # FIME: move to config?
    return render_template("report.html",
                           title=reportdirname,
                           report_id=reportdirname,
                           pagetype=DEFAULT_START_BUILD_TYPE)


@app.route('/<reportdirname>/content/<pagetype>')
@app.route('/<reportdirname>/content/<pagetype>/')
def get_report_type(reportdirname, pagetype):
    if pagetype in ('html', 'pdf'):
        reportfilename, _ = build_report(reportdirname, pagetype, force=False)
        return send_from_directory(os.path.dirname(reportfilename),
                                   os.path.basename(reportfilename))
    elif pagetype == 'edit':
        return render_template("editor.html", source_data=get_sourcefile_content(reportdirname))


@app.route('/<reportdirname>/content/<pagetype>/<path:static_file_path>')
def get_report_static_file(reportdirname, pagetype, static_file_path):
    if pagetype in ('html', 'pdf'):
        filepath = os.path.join(get_builddir(reportdirname, pagetype), static_file_path)
        return send_from_directory(os.path.dirname(filepath), os.path.basename(filepath))


@app.route('/<reportdirname>/save', methods=['POST'])
def save_report(reportdirname):
    unicode_text = request.get_json()['source_text']
    commits = save_sourcefile(reportdirname, unicode_text)
    # note that (editable_page.html) we do not actually make use of the returned response value
    return jsonify(commits)  # which converts to a Response


@app.route('/<reportdirname>/get_commits', methods=['POST'])
def get_commits_list(reportdirname):
    commits = get_commits(reportdirname)
    # note that (editable_page.html) we do not actually make use of the returned response value
    return jsonify(commits)  # which converts to a Response


@app.route('/<reportdirname>/get_source_rst', methods=['POST'])
def get_source_rst(reportdirname):
    commit_hash = request.get_json()['commit_hash']
    return jsonify(get_sourcefile_content(reportdirname, commit_hash, as_js=False))


@app.route('/<reportdirname>/upload_file', methods=['POST'])
def upload_file(reportdirname):
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
