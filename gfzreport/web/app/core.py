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
from gfzreport.sphinxbuild.main import _run_sphinx, get_master_doc
import re
from datetime import datetime, timedelta
from math import ceil
import threading
from multiprocessing.pool import ThreadPool
import json


def gitkwargs(reportdirname):
    '''returns the dict to be passed as keyword arguments to any 
    subprocess.check_output or subprocess.call function
    invoking git. Basically, it changed the cwd of the subprocess and set shell=True.
    For any other common customization, edit keyword arguments here'''
    return dict(cwd=get_sourcedir(reportdirname), shell=False)


def get_sourcefile_content(reportdirname, commit_hash='HEAD', as_js=True):
    """
        Reads the source rst from the sphinx source file. If the argument is True, returns
        javascript formatted string (e.g., with newlines replaced by "\n" etcetera)
        :return: a UNICODE string denoting the source rst file (decoded with 'utf8')
    """
    filename = get_sourcefile(reportdirname)

    if not commit_hash == 'HEAD':
        kwargs = gitkwargs(reportdirname)
        content = subprocess.check_output(['git', 'show',
                                           '%s:%s' % (commit_hash,
                                                      os.path.basename(filename))], **kwargs)
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
    return os.path.join(get_sourcedir(reportdirname), master_doc(reportdirname) + ".rst")


def get_builddir(reportdirname, buildtype):
    return os.path.join(app.config['BUILD_PATH'],
                        reportdirname, 'latex' if buildtype == 'pdf' else buildtype)


def get_buildfile(reportdirname, buildtype):
    return os.path.join(get_builddir(reportdirname, buildtype), master_doc(reportdirname) +
                        ('.tex' if buildtype == 'latex' else "." + buildtype))


def get_sphinxlogfile(reportdirname, buildtype):
    return os.path.join(get_builddir(reportdirname, buildtype), '_sphinx_stderr.log')


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
    args = gitkwargs(reportdirname)
    gitcwd = args.get("cwd", os.getcwd())  # that's used only for printing

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
                         "Please contact the administrator" % gitcwd)

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
                                 "Please contact the administrator" % gitcwd)
        else:
            raise ValueError("Unable to run git -A . on the specified folder '%s'. "
                             "Please contact the administrator" % gitcwd)
    return True


def build_report(reportdirname, buildtype, user, buildinginfo=None, force=False):
    """Builds the given report according to the specified network. Returns
    the tuple reportfile (string), hasChanged (boolean)"""
    # we return reportfile, exit_status, has_changed
    if not needs_build(reportdirname, buildtype, user):
        if not force:
            return -1
    # sphinx puts warnings/ errors on the stderr
    # (http://www.sphinx-doc.org/en/stable/config.html#confval-keep_warnings)
    # capture it:
    with capturestderr(reportdirname, buildtype) as newstderr:
        sourcedir = get_sourcedir(reportdirname)
        builddir = get_builddir(reportdirname, buildtype)

        # this in principle never raises, but prints to stderr:
        ret = _run_sphinx(sourcedir, builddir, master_doc(reportdirname),
                          buildtype, buildinginfo, '-E')

    # pdflatex returns 1 in case of errors BUT document written. Toachieve the same with
    # sphinx, we need to check the ouptut for a ".*:###: ERROR: .*" message. If such a line
    # exists, and ret is zero, connvert it to 1 to be consistent with pdflatex output
    if buildtype != 'pdf' and ret == 0:
        reg = _ERR_REG[buildtype]
        for _ in reg.finditer(newstderr.getvalue()):
            ret = 1
            break

    # write to the last git commit the returned status. Note that in git we need to override completely
    # the notes, so in order to override only relevant stuff, first read the notes, if any:
    args = gitkwargs(reportdirname)
    notes = subprocess.check_output(["git", "log", "-1", "--pretty=format:%N"], **args).strip()
    # IMPORTANT: do NOT quote pretty format values (e.g.: "--pretty=format:%N", AVOID
    # "--pretty=format:'%N'"), otherwise the quotes
    # will appear in the output (if value has spaces, we did not test it,
    # so better avoid it)
    if notes:  # sometimes an empty string quoted is returned
        # we don't bother too much (shlex is suggested, too much effort) and we consider quoted
        # empty strings as empty strings
        notes_dict = json.loads(notes)
    else:
        notes_dict = {}
    if 'Report generation' not in notes_dict:
        notes_dict['Report generation'] = {}
    notes_dict['Report generation'][buildtype] = \
        ("Successful, no compilation errors{}" if ret == 0
         else "Successful, with compilation errors{}" if ret == 1 else
         "Failed{}" if ret == 2 else \
         "Unknown exit code, please contact the administrator{}"
         ).format(" (exit code: %s)" % str(ret))
    # write back to the notes, overriding it:
    subprocess.call(['git', 'notes', 'add', 'HEAD', '--force', '-m',
                     json.dumps(notes_dict)], **args)
    # git notes add HEAD --force -m "-Build report exit code: 1 (Successfull with  warnings/errors)"

    return ret
#     if ret != 2:  # file is newly created or modified
#         mark_build_updated(reportdirname, buildtype)  # for safety, mark mtime of dest file

#    return ret


def master_doc(reportdirname):
    '''returns the master doc defined in the sphinx config, which acts as basename
    (without extension) for all source and dest files'''
    # Lazily create the variable if not stored. Remember that the variable is obtained
    # by parsing conf.py (copying code from sphinx) and might be relatively expensive.
    # Store the master_doc in a dict so to have the correct master_cod for any given reportdirname
    # and avoid conflicts (in principle. all the same string 'report', but it needs not to)
    try:
        dic = app.config['REPORT_BASENAMES']
    except KeyError:
        dic = {}
        app.config['REPORT_BASENAMES'] = dic

    try:
        return dic[reportdirname]
    except KeyError:
        mdoc = get_master_doc(os.path.join(get_sourcedir(reportdirname), "conf.py"))
        dic[reportdirname] = mdoc
        return mdoc


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


def is_build_updated(reportdirname, buildtype):
    '''Returns True if the built file exists and its modification time is greater
    than the rst source file'''
    sourcefile = get_sourcefile(reportdirname)
    destfile = get_buildfile(reportdirname, buildtype)
    return os.path.isfile(destfile) and os.stat(sourcefile).st_mtime < os.stat(destfile).st_mtime


# def mark_build_updated(reportdirname, buildtype):
#     # sets the modification time of the build file greater than the current source rst file,
#     # if not already. For safety.
#     if is_build_updated(reportdirname, buildtype):
#         return True
#     destfile = get_buildfile(reportdirname, buildtype)
#     os.utime(destfile, None)  # set to current time, which should be surely greater than
#     # sourcefile mtime. If not, we will run again later the build, too bad but not tragic
#     return is_build_updated(reportdirname, buildtype)


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
        yield new_stderr  # allow code to be run with the redirected stdout/stderr
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

_ERR_REG = {
    'html': re.compile(".+?:[0-9]+:\\s*ERROR\\s*:.+"),
    'latex': re.compile(".+?:[0-9]+:\\s*ERROR\\s*:.+"),
    'pdf': re.compile(".+?:[0-9]+:.+")
}


def save_sourcefile(reportdirname, unicode_text, user):
    """Save the source rst file and returns `get_commits()`
    :param user: the current User. It is up to the view check if the User is authenticated.
    This is not checked here
    :return: True if git commit was issued, False if nothing to commit
    """
    filepath = get_sourcefile(reportdirname)

    with open(filepath, 'w') as fopen:
        fopen.write(unicode_text.encode('utf8'))

    # return True if commits where saved, False if 'nothing to commit'
    return gitcommit(reportdirname, user)


def get_commits(reportdirname):
    def prettify(jsonstr):
        return json.dumps(json.loads(jsonstr), indent=4).replace('"', "").replace("{", "").replace("}", "")
    try:
        commits = []
        args = gitkwargs(reportdirname)

        # get a separator which is most likely not present in each key:
        # please no spaces in sep!
        # Note according to git log, we could provide also %n for newlines in the command
        # maybe implement later ...
        sep = "_;<!>;_"
        pretty_format_arg = "%H{0}%an{0}%ad{0}%ae{0}%s{0}%N".format(sep)
        cmts = subprocess.check_output(["git", "log",
                                        "--pretty=format:%s" % (pretty_format_arg)], **args)
        # IMPORTANT: do NOT quote pretty format values (e.g.: "--pretty=format:%N", AVOID
        # "--pretty=format:'%N'"), otherwise the quotes
        # will appear in the output (if value has spaces, we did not test it,
        # so better avoid it)

        for commit in cmts.split("\n"):
            if commit:
                clist = commit.split(sep)
                # parse notes by removing curly brackets and quotes (")
                if clist[-1]:
                    clist[-1] = prettify(clist[-1]).strip()
                    # clist[-1].replace('"', "").replace("{", "").replace("}")
                commits.append({'hash': clist[0], 'author': clist[1], 'date': clist[2],
                                'email': clist[3], 'msg': clist[4], 'notes': clist[-1]})
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


def get_logs_(reportdirname, buildtype):
    '''Returns an array of:
    sphinx log file content (if buildtype='html') or
    sphinx log file content, pdflatex log file errors, pdflatex log file content (if buildtype
    is 'latex' or 'pdf')
    pdflatex log file errors is a substring of the pdflatex log file content, extracted
    via the pdflatex option that prints errors in the format .*:[0-9]:.*
    '''
    # the returned object is quite cumbersome but allows an easy implementation with angular
    # basically it is a one or two element array of elements in this form
    # [compiler_name, [log_file_content, list_of_lof_errors]]
    # For compatibility, log_file_cintent is in turn a list of a single element, the real log
    # file content

    def getlogs(srcfile, reg):
        '''reads a log and returns the structur used in the frontend'''
        if not os.path.isfile(srcfile):
            msg = 'No log file found. Please check your .rst syntax or contact the administrator'
            return msg, [msg]
        with open(srcfile, 'r') as fopen:
            fullog = fopen.read().decode('utf8')
        errs = []
        for m in reg.finditer(fullog):
            errs.append(m.group().strip())
#         if not errs:
#             errs = ['No error found']
        return fullog, errs

    sphinxlogfile = get_sphinxlogfile(reportdirname, buildtype)
    sphinxbuildtype = 'latex' if buildtype == 'pdf' else buildtype
    sphinxlog, sphinxerrs = getlogs(sphinxlogfile, _ERR_REG[sphinxbuildtype])
    ret = [['Sphinx (rst to %s)' % sphinxbuildtype, [[sphinxlog], sphinxerrs]]]

    if buildtype == 'pdf':
        pdflatexlog = get_buildfile(reportdirname, "pdf")
        fle, _ = os.path.splitext(pdflatexlog)
        pdflatexlog = fle + ".log"
        pdflog, pdferrs = getlogs(pdflatexlog, _ERR_REG['pdf'])
        ret.append(['Pdflatex (latex to pdf)', [[pdflog], pdferrs]])

    return ret


# this is a class NOT USED for the moment which might be passed to 
# _run_sphinx in build_report. But for that, we might need to launch the build in a separate
# thread RETURNING immediately from within the caller view, and then , after
# setting this object in a session variable and implement a progressbar forntend side
# querying the progress of the build.
# When finished, frontend side we should query for the page. Too much effort for the moment
# class BuildingInfo(object):
# 
#     def __init__(self, msg=None, estimated_end=None, step=0, steps=0):
#         self.__call__(msg, estimated_end, step, steps)
# 
#     def __call__(self, msg, estimated_end, step, steps):
#         self.msg = msg
#         self.estimated_end = estimated_end
#         self.step = step
#         self.steps = steps
#         return self
# 
#     def tojson(self):
#         arr = []
#         if not self.msg:
#             return arr
#         if self.steps > 0 and self.step > 0:
#             arr.append("Step %d of %d: " % (self.step, self.steps))
#         arr.append(self.msf)
#         if self.estimated_end is not None:
#             ers = self.estimated_end - datetime.utcnow()
#             if ers > 0:
#                 arr.append("Remaining time (estimation): %s" %
#                            str(timedelta(seconds=int(ceil(ers)))))
#         return arr


