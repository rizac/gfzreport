'''
Created on Apr 3, 2016

@author: riccardo
'''
from reportwebapp.webapp import app
from flask.templating import render_template
from flask import send_from_directory, url_for, request, jsonify
import os
from cStringIO import StringIO


@app.route('/')
def index():
    return render_template("reportslist.html",
                           title=app.config['DATA_PATH'],
                           reports=_get_reports(app.config['SOURCE_PATH']))


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
        reportfilename, _ = buildreport(reportdirname, pagetype, force=False)
        return send_from_directory(os.path.dirname(reportfilename),
                                   os.path.basename(reportfilename))
    elif pagetype == 'edit':
        return render_template("editor.html", source_data=get_source_rst_content(reportdirname))


@app.route('/<reportdirname>/content/<pagetype>/<path:static_file_path>')
def get_report_static_file(reportdirname, pagetype, static_file_path):
    if pagetype in ('html', 'pdf'):
        filepath = os.path.join(get_builddir(reportdirname, pagetype), static_file_path)
        return send_from_directory(os.path.dirname(filepath), os.path.basename(filepath))


@app.route('/<reportdirname>/save', methods=['POST'])
def save_report(reportdirname):
    unicode_text = request.get_json()['source_text']
    needs_build = save_rst(reportdirname, unicode_text)
    # note that (editable_page.html) we do not actually make use of the returned response value
    return jsonify({"needs_build": needs_build})  # which converts to a Response
        # return Response({"result": last_file_name}, status=200, mimetype='application/json')


@app.route('/<reportdirname>/get_commits', methods=['POST'])
def get_commits_list(reportdirname):
    commits = get_commits(reportdirname)
    # note that (editable_page.html) we do not actually make use of the returned response value
    return jsonify(commits)  # which converts to a Response
        # return Response({"result": last_file_name}, status=200, mimetype='application/json')


@app.route('/<reportdirname>/get_source_rst', methods=['POST'])
def get_source_rst(reportdirname):
    commit_hash = request.get_json()['commit_hash']
    return jsonify(get_source_rst_content(reportdirname, commit_hash, as_js=False))


# ============ THIS WILL BE MOVED TO core.py: ================================
from reportbuild.main import run as reportbuild_run
import subprocess


def get_source_rst_content(reportdirname, commit_hash='HEAD', as_js=True):
    """
        Reads the source rst from the sphinx source file. If the argument is True, returns
        javascript formatted string (e.g., with newlines replaced by "\n" etcetera)
        :return: a UNICODE string denoting the source rst file (decoded with 'utf8')
    """
    filename = get_sourcefile(reportdirname)

    if not commit_hash == 'HEAD':
        cwd = get_sourcedir(reportdirname)
        args = dict(cwd=cwd, shell=False)
        content = subprocess.check_output(['git', 'show',
                                           '%s:%s' % (commit_hash,
                                                      os.path.basename(filename))], **args)
        fpoint = StringIO(content)
        fpoint.seek(0)
    else:
        fpoint = open(filename, "r")

    # json dump might do what we want, but it fails with e.g. "===" (rst headers, not javascript
    # equal sign. So this procedure might not be optimal but it works:
    sio = StringIO()
    try:
        if not as_js:
            return fpoint.read().decode('utf8')
        while True:
            c = fpoint.read(1)
            if not c:
                break
            elif c == '\n' or c == '\r':
                sio.write("\\")
                c = 'n' if c == '\n' else 'r'
            elif c == '\\' or c == '"':
                sio.write("\\")
            sio.write(c)
        return sio.getvalue().decode('utf8')
    finally:
        if hasattr(fpoint, 'close'):
            fpoint.close()


def _get_reports(basedir):
    ret = []
    for subdir in os.listdir(basedir):
        if subdir[0] != "_" and os.path.isdir(os.path.join(basedir, subdir)):
            ret.append('/%s' % subdir)
    return ret


def get_sourcedir(reportdirname):
    return os.path.join(app.config['SOURCE_PATH'], reportdirname)


def get_sourcefile(reportdirname):
    return os.path.join(get_sourcedir(reportdirname), app.config['REPORT_FILENAME'] + ".rst")


def get_builddir(reportdirname, buildtype):
    return os.path.join(app.config['BUILD_PATH'],
                        reportdirname, 'latex' if buildtype == 'pdf' else buildtype)


def get_buildfile(reportdirname, buildtype):
    return os.path.join(get_builddir(reportdirname, buildtype), app.config['REPORT_FILENAME'] +
                        ('.tex' if buildtype == 'latex' else "." + buildtype))


def get_last_commit(reportdirname):
    cwd = get_sourcedir(reportdirname)
    args = dict(cwd=cwd, shell=False)
    try:
        return str(subprocess.check_output(['git', 'log', '-1', '--pretty=format:"%H"'], **args))
    except OSError:
        return None  # on error, return needs_refresh for safety


def is_build_updated(reportdirname, buildtype):
    '''Returns True if the current buildtype
    buildpath = get_builddir(reportdirname, buildtype)
    '''
    sourcefile = get_sourcefile(reportdirname)
    destfile = get_buildfile(reportdirname, buildtype)
    return os.stat(sourcefile).st_mtime < os.stat(destfile).st_mtime


def mark_build_updated(reportdirname, buildtype):
    # sets the modification time of the build file greater than the current source rst file,
    # if not already. For safety.
    if is_build_updated(reportdirname, buildtype):
        return True
    destfile = get_buildfile(reportdirname, buildtype)
    os.utime(destfile, None)  # set to current time, which should be surely greater than
    # sourcefile mtime. If not, we will run again later the build, too bad but not tragic
    return is_build_updated(reportdirname, buildtype)


def needs_build(reportdirname, buildtype, commit_if_needed=False):
    """
        Returns True if the git repo has uncommitted changes or the source rst file last
        modification time (LMT) is greater or equal than the destination file LMT
        (see `is_build_updated`).
        Calls `git` (via the `subprocess` module)
        :param reportdirname: the report dirrecotory name. Its full path will be retrieved
        via app config settings
        :param commit_if_needed: does what it says. If True (False by default) and no error is
        raised, then needs_build called again with the same arguments returns False.
        :raise: ValueError if git complains
    """
    cwd = get_sourcedir(reportdirname)
    args = dict(cwd=cwd, shell=False)

    k = subprocess.call(['git', 'status'], **args)
    if k == 128:
        k = subprocess.call(['git', 'init', '.'], **args)
        if k == 0:
            k = subprocess.call(['git', 'status'], **args)

    if k != 0:
        raise ValueError("Unable to run git on the specified folder '%s'. "
                         "Please contact the administrator" % cwd)

    # check the output:
    k = subprocess.check_output(['git', 'status'], **args)
    if 'nothing to commit' in k or ' working directory clean' in k:
        # we might have nothing to commit BUT outdated build dir
        return not is_build_updated(reportdirname, buildtype)
    elif commit_if_needed:
        k = subprocess.call(['git', 'add', '-A', '.'], **args)
        # the dot is to commit only the working tree. We are on the source root, is just for safety
        if k == 0:
            k = subprocess.call(['git', 'commit', '-am', '"committed from webapp"'], **args)
            if k != 0:
                raise ValueError("Unable to run commit -am . on the specified folder '%s'. "
                                 "Please contact the administrator" % cwd)
        else:
            raise ValueError("Unable to run git -A . on the specified folder '%s'. "
                             "Please contact the administrator" % cwd)
    return True


def buildreport(reportdirname, buildtype, force=False):
    """Builds the given report according to the specified network. Returns
    the tuple reportfile (string), hasChanged (boolean)"""
    if not needs_build(reportdirname, buildtype, True):
        if not force:
            return get_buildfile(reportdirname, buildtype), False
    sourcedir = get_sourcedir(reportdirname)
    builddir = get_builddir(reportdirname, buildtype)
    # ret = reportbuild_run(["reportbuild", sourcedir, builddir, "-b", build, "-E"])
    ret = reportbuild_run(sourcedir, builddir, buildtype, "-E")
#     if ret != 0:
#         raise ValueError('Error building the report, please contact the administrator')
    mark_build_updated(reportdirname, buildtype)
    return get_buildfile(reportdirname, buildtype), True


def save_rst(reportdirname, unicode_text):
    filepath = get_sourcefile(reportdirname)

    with open(filepath, 'w') as fopen:
        fopen.write(unicode_text.encode('utf8'))

    # we return if the build process must be run again. A better check might be feasible
    # but we skip for the moment. Next time we call buildreport git should see that we need
    # a new build
    return True


def get_commits(reportdirname):
    try:
        commits = []
        cwd = get_sourcedir(reportdirname)
        args = dict(cwd=cwd, shell=False)

        # get a separator which is most likely not present in each key:
        # please no spaces in sep!
        # Note according to git log, we could provide also %n for newlines in the command
        # maybe implement later ...
        sep = "_;<!>;_"
        pretty_format_arg = "%H{0}%an{0}%ad{0}%s".format(sep)
        cmts = subprocess.check_output(["git", "log",
                                        "--pretty=format:%s" % (pretty_format_arg)], **args)

        for commit in cmts.split("\n"):
            if commit:
                clist = commit.split(sep)
                commits.append({'hash': clist[0], 'author': clist[1], 'date':clist[2],
                                'msg':clist[3]})
        return commits
    except OSError:
        return []