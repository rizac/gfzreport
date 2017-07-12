'''
Created on Apr 3, 2016

Core functionalities for the network webapp
The network web app is a flask app with a config file where we set two variables:

Recall of the file structure:
Each web app is run
form a specified 'DATA_PATH' (one for each report type, e.g. 'network',) and a reportdirname
(a specific report of that type, e.g. 'ZE_2012'). In principle (but this might change),
reportdirname represents the address after the domain (e.g. www.mydomain/ZE_2012)
Each view endpoint gets `reportdirname` to identify a specifi file location, as follows:

    FILE STRUCTURE               IN THE CODE REFERRED WITH:

    + <data_path>                app.config['DATA_PATH']
        |
        +---- ./source           app.config['SOURCE_PATH']
        |        |
        |        + ./<dir1>      reportdirname (if this is the current report)
        |        | ...
        |        + ./<dirN>      reportdirname (if this is the current report)
        |
        +---- ./build            (app.config['BUILD_PATH'])
                 |
                 + ./<dir1>      reportdirname (if this is the current report)
                 | ...
                 + ./<dirN>      reportdirname (if this is the current report)

The ./source directory sub-directories identify a specific document/report to be built and hold
the necessary source files (.rst, images, sphinx config, upload directory ...).
The report is build in the directory with the same name under ./build
Note that each build directory is structured as follows:

        +---- ./build            (app.config['BUILD_PATH'])
                 |
                 + ./<dir1>      reportdirname (if this is the current report)
                      |
                      + ./html   stores the build of html page
                      + ./latex  stores the build of latex and pdf


@author: riccardo
'''
import os
import sys
import subprocess
from subprocess import CalledProcessError
# from cStringIO import StringIO
from cStringIO import StringIO
from itertools import count
from werkzeug.utils import secure_filename
from contextlib import contextmanager
from flask import current_app as app
from gfzreport.sphinxbuild.main import run as reportbuild_run


def get_sourcefile_content(reportdirname, commit_hash='HEAD', as_js=True):
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


def get_reports(basedir):
    ret = []
    for subdir in os.listdir(basedir):
        if subdir[0] != "_" and os.path.isdir(os.path.join(basedir, subdir)):
            ret.append('%s' % subdir)
    return ret


def get_sourcedir(reportdirname):
    return os.path.join(app.config['SOURCE_PATH'], reportdirname)


def get_sourcefile(reportdirname):
    return os.path.join(get_sourcedir(reportdirname), app.config['REPORT_BASENAME'] + ".rst")


def get_builddir(reportdirname, buildtype):
    return os.path.join(app.config['BUILD_PATH'],
                        reportdirname, 'latex' if buildtype == 'pdf' else buildtype)


def get_buildfile(reportdirname, buildtype):
    return os.path.join(get_builddir(reportdirname, buildtype), app.config['REPORT_BASENAME'] +
                        ('.tex' if buildtype == 'latex' else "." + buildtype))


def get_sphinxlogfile(reportdirname, buildtype):
    return os.path.join(get_builddir(reportdirname, buildtype), '_sphinx_stderr.log')


def is_build_updated(reportdirname, buildtype):
    '''Returns True if the current buildtype
    buildpath = get_builddir(reportdirname, buildtype)
    '''
    sourcefile = get_sourcefile(reportdirname)
    destfile = get_buildfile(reportdirname, buildtype)
    return os.path.isfile(destfile) and os.stat(sourcefile).st_mtime < os.stat(destfile).st_mtime


def mark_build_updated(reportdirname, buildtype):
    # sets the modification time of the build file greater than the current source rst file,
    # if not already. For safety.
    if is_build_updated(reportdirname, buildtype):
        return True
    destfile = get_buildfile(reportdirname, buildtype)
    os.utime(destfile, None)  # set to current time, which should be surely greater than
    # sourcefile mtime. If not, we will run again later the build, too bad but not tragic
    return is_build_updated(reportdirname, buildtype)


def gitcommit(reportdirname, user=None):
    """Issues a git commit and returns True if there where files untracked/modified
    which where added to the commit. False if the working directory was clean
    :pqram author: ignored if the path does not have uncommitted changes. Otherwise,
    specifies the commit author. **It should be in the format
    ```
    Name <email>
    ```
    (https://stackoverflow.com/questions/11579311/git-commit-as-different-user-without-email-or-only-email)
    if None or evaluates to False, no author argument will be provided for the commit
    """
    cwd = get_sourcedir(reportdirname)
    args = dict(cwd=cwd, shell=False)

    # user might be an AnonymousUserMixin user, i.e. what flask-login sets as default
    # In this case, it has no asgitauthor method
    try:
        gitauthor = user.asgitauthor if user else None
    except AttributeError:
        gitauthor = None

    gitinited = False
    k = subprocess.call(['git', 'status'], **args)
    if k == 128:
        k = subprocess.call(['git', 'init', '.'], **args)
        gitinited = True
        if k == 0:  # FIXME: why do we do this?
            k = subprocess.call(['git', 'status'], **args)

    if k != 0:
        raise ValueError("Unable to run git on the specified folder '%s'. "
                         "Please contact the administrator" % cwd)

    # check the output:
    k = subprocess.check_output(['git', 'status'], **args)
    if 'nothing to commit' in k or ' working directory clean' in k:
        # we might have nothing to commit BUT outdated build dir
        return False
    else:
        k = subprocess.call(['git', 'add', '-A', '.'], **args)
        # the dot is to commit only the working tree. We are on the source root, is just for safety
        if k == 0:
            commit_msg = '"%scommit from webapp"' % ('git-init and ' if gitinited else '')
            gitargs = ['git', 'commit']
            if gitauthor:
                gitargs.append("--author=\"%s\"" % gitauthor)
            gitargs.extend(['-am', commit_msg])
            k = subprocess.call(gitargs, **args)
            if k != 0:
                raise ValueError("Unable to run commit -am . on the specified folder '%s'. "
                                 "Please contact the administrator" % cwd)
        else:
            raise ValueError("Unable to run git -A . on the specified folder '%s'. "
                             "Please contact the administrator" % cwd)
    return True


def needs_build(reportdirname, buildtype, user, commit_if_needed=False):
    """
        Returns True if the git repo has uncommitted changes or the source rst file last
        modification time (LMT) is greater or equal than the destination file LMT
        (see `is_build_updated`).
        Calls `git` (via the `subprocess` module)
        :param reportdirname: the report dirrecotory name. Its full path will be retrieved
        via app config settings
        :param user: The User currently authenticated. It is up to the view restrict the access
        if the user is not authenticated, this is not checked here
        :param commit_if_needed: does what it says. If True (False by default) and no error is
        raised, then needs_build called again with the same arguments returns False.
        :raise: ValueError if git complains
    """
    committed = gitcommit(reportdirname, user)
    if committed:  # working directory was not clean
        return True
    # nothing to commit but we might have an outdated build dir. Check file last modification time:
    return not is_build_updated(reportdirname, buildtype)


def build_report(reportdirname, buildtype, user, force=False):
    """Builds the given report according to the specified network. Returns
    the tuple reportfile (string), hasChanged (boolean)"""
    if not needs_build(reportdirname, buildtype, user):
        if not force:
            return get_buildfile(reportdirname, buildtype), False
    # sphinx puts warnings/ errors on the stderr
    # (http://www.sphinx-doc.org/en/stable/config.html#confval-keep_warnings)
    # capture it:
    with capturestderr(reportdirname, buildtype):
        sourcedir = get_sourcedir(reportdirname)
        builddir = get_builddir(reportdirname, buildtype)
        # ret = reportbuild_run(["reportbuild", sourcedir, builddir, "-b", build, "-E"])
        ret = reportbuild_run(sourcedir, builddir, buildtype, "-E")
#     if ret != 0:
#         raise ValueError('Error building the report, please contact the administrator')
    mark_build_updated(reportdirname, buildtype)
    return get_buildfile(reportdirname, buildtype), True


@contextmanager
def capturestderr(reportdirname, buildtype):
    '''Captures standard error to a StrinIO and writes it to a file. Used in `build_report`
    '''
    # set the stderr to a StringIO. Yield, and after that get the sphinx log file path
    # The sphinx log file directory might not yet exist if this is the first build
    # After yielding, check if the sphinx logfile dir exists. If yes, write the content
    # of the captured stderr to that file
    # Restore the old stderr and exit
    stderr = sys.stderr
    new_stderr = StringIO()
    sys.stderr = new_stderr
    try:
        yield  # allow code to be run with the redirected stdout/stderr
    finally:
        # write to file, if the build was succesfull we should have the
        # directory in place:
        fileout = get_sphinxlogfile(reportdirname, buildtype)
        if os.path.isdir(os.path.dirname(fileout)):
            with open(fileout, 'w') as _:
                _.write(new_stderr.getvalue())
        # restore stderr. buffering and flags such as CLOEXEC may be different
        sys.stderr = stderr

#     fileout = get_sphinxlogfile(reportdirname, buildtype)
#     with open(fileout, 'w') as new_stderr:
#         sys.stderr = new_stderr
#         try:
#             yield  # allow code to be run with the redirected stdout/stderr
#         finally:
#             # restore stderr. buffering and flags such as CLOEXEC may be different
#             sys.stderr = stderr


def save_sourcefile(reportdirname, unicode_text, user):
    """Save the source rst file and returns `get_commits()`
    :param user: the current User. It is up to the view check if the User is authenticated.
    This is not checked here
    """
    filepath = get_sourcefile(reportdirname)

    with open(filepath, 'w') as fopen:
        fopen.write(unicode_text.encode('utf8'))

    gitcommit(reportdirname, user)
    # we return the new commits
    return get_commits(reportdirname)


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
        pretty_format_arg = "%H{0}%an{0}%ad{0}%ae{0}%s".format(sep)
        cmts = subprocess.check_output(["git", "log",
                                        "--pretty=format:%s" % (pretty_format_arg)], **args)

        for commit in cmts.split("\n"):
            if commit:
                clist = commit.split(sep)
                commits.append({'hash': clist[0], 'author': clist[1], 'date': clist[2],
                                'email': clist[3], 'msg': clist[4]})
        return commits
    except (OSError, CalledProcessError):
        return []


def secure_upload_filepath(reportdirname, filename):
    if filename == '':
        raise ValueError('No selected file')
    if allowed_upload_file(filename):
        s_filename = secure_filename(filename)
        # create upload dir if it does not exists:
        upload_dir = os.path.join(app.config['SOURCE_PATH'], reportdirname,
                                  app.config['UPLOAD_DIR_BASENAME'])
        if not os.path.isdir(upload_dir):
            os.makedirs(upload_dir)
            if not os.path.isdir(upload_dir):
                raise ValueError(("Unable to create upload directory $SOURCE_PATH/"
                                  "%s/%s") % (reportdirname, app.config['UPLOAD_DIR_BASENAME']))
        # assure file does not exist:
        for cnt in count(start=1):
            filepath = os.path.join(upload_dir, s_filename)
            if not os.path.exists(filepath):
                break
            f, e = os.path.splitext(s_filename)
            s_filename = "%s_%d%s" % (f, cnt, e)
        return filepath
    raise ValueError("Cannot save '%s': invalid extension" % filename)


def allowed_upload_file(filename):
    return os.path.splitext(filename)[1][1:].lower() in app.config['UPLOAD_ALLOWED_EXTENSIONS']


def get_fig_directive(reportdirname, fig_filepath, fig_label=None, fig_caption=None):
    """Returns the figure directive text from a given report directory name identifying the
    current report, a figure filepath, optional label and caption
    :param reportdirname: (string) the basename of the directory identifying the report
    name.
    :param fig_filepath: (string) the path of the figure to be displayed. This method does not
    check for existence of the file. The directive will have a file path relative to the Rst file
    (whose path is set according to the current Flask app configuration)
    :param fig_label:  (string or None) an optional label for referncing the figure via
    sphinx `:numerf:`. None, empty or only space strings will be ignored (no label)
    :param fig_caption:  (string or None) an optional caption. Indentation will be automatically
    added to the caption in the directive. None, empty or only space strings will be ignored
    (no label)
    """
    if fig_caption:  # indent:
        fig_caption = fig_caption.strip()
        if fig_caption:
            fig_caption = fig_caption.replace("\n", "\n   ")
    if fig_label:  # newlines:
        fig_label = fig_label.strip()
        if fig_label:
            fig_label = ".. _%s:\n\n" % fig_label
    fname = os.path.relpath(fig_filepath, get_sourcedir(reportdirname))
    return "%s.. figure:: ./%s\n\n   %s" % (fig_label, fname, fig_caption)


def get_log_files_list(reportdirname, buildtype):
    sphinxlogfile = get_sphinxlogfile(reportdirname, buildtype)
    ret = []  # preserve order!
    if os.path.isfile(sphinxlogfile):
        with open(sphinxlogfile, 'r') as fopen:
            ret.append(fopen.read().decode('utf8'))
    if buildtype == 'pdf':
        pdflatexlog = get_buildfile(reportdirname, "pdf")
        fle, _ = os.path.splitext(pdflatexlog)
        pdflatexlog = fle + ".log"
        if os.path.isfile(pdflatexlog):
            with open(pdflatexlog, 'r') as fopen:
                ret.append(fopen.read().decode('utf8'))
    return ret
