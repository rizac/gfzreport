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
import shutil
from datetime import datetime, timedelta
import json
import re
from cStringIO import StringIO
from itertools import count
from werkzeug.utils import secure_filename

from gfzreport.sphinxbuild import _run, get_master_doc, get_logfilename, log_err_regexp,\
    exitstatus2str


def nocache(response):
    """makes the response non cacheable. Useful for GET requests only, as POST by default
    is not cacheable. We use it basically for the html pages 'pdf', 'html' and 'edit'"""
    # for info see:
    # https://arusahni.net/blog/2014/03/flask-nocache.html
    response.headers['Last-Modified'] = datetime.now()
    response.headers['Cache-Control'] = ('no-store, no-cache, must-revalidate, '
                                         'post-check=0, pre-check=0, max-age=0')
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


def gitkwargs(app, reportdirname):
    '''returns the dict to be passed as keyword arguments to any
    subprocess.check_output or subprocess.call function
    invoking git. Basically, it changed the cwd of the subprocess and set shell=True.
    For any other common customization, edit keyword arguments here'''
    return dict(cwd=get_sourcedir(app, reportdirname), shell=False)


def get_sourcefile_content(app, reportdirname, commit_hash='HEAD', as_js=True):
    """
        Reads the source rst from the sphinx source file. If the argument is True, returns
        javascript formatted string (e.g., with newlines replaced by "\n" etcetera)
        :return: a UNICODE string denoting the source rst file (decoded with 'utf8')
    """
    filename = get_sourcefile(app, reportdirname)

    if not commit_hash == 'HEAD':
        kwargs = gitkwargs(app, reportdirname)
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


def get_reports(app):
    '''returns all the report folders in `basedir`, sorted from most recent to
    oldest (i.e., sorted descending according to their
    modification time: max modification time of all files in the directory)

    :return: a list of tuples (report_directory_name, is_editable) where the first item is
    a string, the second one is a boolean telling if the report is editable

    '''
    basedir = get_sourceroot(app)
    ret = []
    for subdir in os.listdir(basedir):
        if subdir[0] == "_":
            continue
        dirpath = os.path.join(basedir, subdir)
        if not os.path.isdir(dirpath):
            continue
        mtime = None
        for fle in (os.path.join(dirpath, _) for _ in os.listdir(dirpath)):
            if os.path.isfile(fle):
                mtime_ = os.stat(fle).st_mtime
                if mtime is None or mtime_ < mtime:
                    mtime = mtime_
        if mtime is None:
            continue
        ret.append([subdir, is_editable(app, subdir), mtime])
    ret.sort(key=lambda obj: obj[-1], reverse=True)
    return [_[:-1] for _ in ret]


def _get_locked_file(app, reportdirname):
    '''returns a file indicating that the current report is locked (not editable)'''
    return get_sourcedir(app, reportdirname) + ".locked"


def is_editable(app, reportdirname):
    return not os.path.isfile(_get_locked_file(app, reportdirname))


def set_editable(app, reportdirname, value):
    iseditable = is_editable(app, reportdirname)
    if value is iseditable:
        return True
    locked_file = _get_locked_file(app, reportdirname)
    if value:
        os.remove(locked_file)
        return not os.path.isfile(locked_file)
    else:
        with open(_get_locked_file(app, reportdirname), 'w') as _:
            pass
        return os.path.isfile(locked_file)


def get_sourceroot(app):
    return app.config['SOURCE_PATH']


def get_sourcedir(app, reportdirname):
    return os.path.join(get_sourceroot(app), reportdirname)


def get_sourcefile(app, reportdirname):
    return os.path.join(get_sourcedir(app, reportdirname), master_doc(app, reportdirname) + ".rst")


def get_buildroot(app):
    return app.config['BUILD_PATH']


def get_builddir(app, reportdirname, buildtype):
    return os.path.join(get_buildroot(app),
                        reportdirname, 'latex' if buildtype == 'pdf' else buildtype)


def get_buildfile(app, reportdirname, buildtype):
    return os.path.join(get_builddir(app, reportdirname, buildtype),
                        master_doc(app, reportdirname) +
                        ('.tex' if buildtype == 'latex' else "." + buildtype))


def get_logfile(app, reportdirname, buildtype):
    return os.path.join(get_builddir(app, reportdirname, buildtype), get_logfilename())


def get_updloaddir(app, reportdirname, tmp=True, mkdir=True):
    basedir = os.path.join(get_buildroot(app), reportdirname) if tmp else \
        get_sourcedir(app, reportdirname)
    upload_dir = os.path.join(basedir, app.config['UPLOAD_DIR_BASENAME'])
    if not os.path.isdir(upload_dir) and mkdir:
        os.makedirs(upload_dir)
        if not os.path.isdir(upload_dir):
            raise Exception("Unable to create upload directory '%s/%s'"
                            % (os.path.basename(upload_dir), os.path.basename(basedir)))
    return upload_dir


def gitcommit(app, reportdirname, user=None):
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
    args = gitkwargs(app, reportdirname)
    gitcwd = args.get("cwd", os.getcwd())  # that's used only for exc messages (see below)

    # user might be an AnonymousUserMixin user, i.e. what flask-login sets as default
    # In this case, it has no asgitauthor method
    try:
        gitauthor = user.asgitauthor if user else None
    except AttributeError:
        gitauthor = None

    if gitauthor is None:
        # if author is anonymous (e.g., we are compiling the html for which authorization is
        # not needed) we want to provide an anonymous author otherwise git user whatever
        # author is in the list. For server applications, this is misleading as the author
        # shown from the list did not commit anything in fact. Provide an "anonymous user name.
        # IMPORTANT: that git wants 'name <email>' format, 'name <>' seems to work
        gitauthor = "anonymous user <>"

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


def build_report(app, reportdirname, buildtype, user, force=False):
    """Builds the given report according to the specified network. Returns
    the tuple reportfile (string), hasChanged (boolean)"""
    # we return reportfile, exit_status, has_changed
    if not needs_build(app, reportdirname, buildtype, user):
        if not force:
            return -1

    sourcedir = get_sourcedir(app, reportdirname)
    builddir = get_builddir(app, reportdirname, buildtype)
    # _run should never raise as a context manager catches exceptions printing to stderr,
    # which is temporary set to a StringIO. The StringIO will be written to our out directory
    # See get_logs
    ret = _run(sourcedir, builddir, master_doc(app, reportdirname), buildtype, False, '-E')

    # write to the last git commit the returned status. Note that in git we need to override
    # completely the notes, so in order to override only relevant stuff, first read the notes,
    # if any:
    args = gitkwargs(app, reportdirname)
    notes = subprocess.check_output(["git", "log", "-1", "--pretty=format:%N"], **args).strip()
    # IMPORTANT: do NOT quote pretty format values (e.g.: "--pretty=format:%N", AVOID
    # "--pretty=format:'%N'"), otherwise the quotes
    # will appear in the output (if value has spaces, we did not test it,
    # so better avoid it)
    if notes:
        notes_dict = json.loads(notes)
    else:
        notes_dict = {}
    if 'Report generation' not in notes_dict:
        notes_dict['Report generation'] = {}
    notes_dict['Report generation'][buildtype] = exitstatus2str(ret)

    # write back to the notes, overriding it:
    subprocess.call(['git', 'notes', 'add', 'HEAD', '--force', '-m',
                     json.dumps(notes_dict)], **args)
    # git notes add HEAD --force -m "-Build report exit code: 1 (Successfull with  warnings/errors)"

    return ret


def master_doc(app, reportdirname):
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
        mdoc = get_master_doc(os.path.join(get_sourcedir(app, reportdirname), "conf.py"))
        dic[reportdirname] = mdoc
        return mdoc


def needs_build(app, reportdirname, buildtype, user, commit_if_needed=False):
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
    committed = gitcommit(app, reportdirname, user)
    if committed:  # working directory was not clean
        return True
    # nothing to commit but we might have an outdated build dir. Check file last modification time:
    return not is_build_updated(app, reportdirname, buildtype)


def is_build_updated(app, reportdirname, buildtype):
    '''Returns True if the built file exists and its modification time is greater
    than the rst source file'''
    sourcefile = get_sourcefile(app, reportdirname)
    destfile = get_buildfile(app, reportdirname, buildtype)
    return os.path.isfile(destfile) and os.stat(sourcefile).st_mtime < os.stat(destfile).st_mtime


def save_sourcefile(app, reportdirname, unicode_text, user):
    """Save the source rst file and returns `get_commits()`
    :param user: the current User. It is up to the view check if the User is authenticated.
    This is not checked here
    :return: True if git commit was issued, False if nothing to commit
    """
    if not is_editable(app, reportdirname):
        raise ValueError('The report is not editable')

    filepath = get_sourcefile(app, reportdirname)

    with open(filepath, 'w') as fopen:
        fopen.write(unicode_text.encode('utf8'))

    # copy uploaded files, if any:
    srcdir = get_updloaddir(app, reportdirname, tmp=True, mkdir=False)
    if os.path.isdir(srcdir):
        destdir = get_updloaddir(app, reportdirname, tmp=False, mkdir=True)
        for fle in os.listdir(srcdir):
            filesrc = os.path.join(srcdir, fle)
            filedest = os.path.join(destdir, fle)
            shutil.copy2(filesrc, filedest)
        shutil.rmtree(srcdir)
    # return True if commits where saved, False if 'nothing to commit'
    needsRefresh = gitcommit(app, reportdirname, user)
    return {'needs_refresh': needsRefresh,
            'commit_hash': get_commits(app, reportdirname, -1)[0]['hash']}


def get_commits(app, reportdirname, revision_range=None):
    ''':param revision_range: None => include all commits. Otherwise works like git 'revison_range'
        (e.g.: -1 for the last one only)
    '''
    def prettify(jsonstr):
        if not jsonstr:
            return jsonstr
        return json.dumps(json.loads(jsonstr), indent=4).replace('"', "").replace("{", "").replace("}", "")
    try:
        commits = []
        kwargs = gitkwargs(app, reportdirname)

        # get a separator which is most likely not present in each key:
        # please no spaces in sep!
        # Note according to git log, we could provide also %n for newlines in the command
        # maybe implement later ...
        sep = "_;<!>;_"
        pretty_format_arg = "%H{0}%an{0}%ad{0}%ae{0}%s{0}%N".format(sep)
        args = ["git", "log", "--pretty=format:%s" % (pretty_format_arg)]
        if revision_range:
            args.append(str(revision_range))
        cmts = subprocess.check_output(args, **kwargs)
        # IMPORTANT: do NOT quote pretty format values (e.g.: "--pretty=format:%N", NOT
        # "--pretty=format:'%N'"), otherwise the quotes
        # will appear in the output (if value has spaces, we did not test it,
        # so better avoid it)

        for commit in cmts.split("\n"):
            if commit:
                clist = [_.rstrip() for _ in commit.split(sep)]
                # parse notes by removing curly brackets and quotes (")
                clist[-1] = prettify(clist[-1]).rstrip()
                commits.append({'hash': clist[0], 'author': clist[1], 'date': clist[2],
                                'email': clist[3], 'msg': clist[4], 'notes': clist[-1]})
        return commits
    except (OSError, CalledProcessError):
        return []


def get_git_diff(app, reportdirname, hash1, hash2):
    '''returns the git diff between hash1 and hash2'''
    masterdoc = os.path.basename(get_sourcefile(app, reportdirname))
    args = gitkwargs(app, reportdirname)
    cmts = subprocess.check_output(["git", "diff", str(hash1), str(hash2), masterdoc], **args)
    reg = re.compile("^\\@\\@\\s+.+\\s+\\@\\@\\s*$", re.MULTILINE)
    val = reg.split(cmts)[1:]
    return [_.strip("\r\n") for _ in val]


def secure_upload_filepath(app, reportdirname, upfile):
    '''saves the given file name. Raises ValueError for client side errors (4xx) and general
    exception otherwise. Returns the file path where the file will be saved AFTER
    saving the report (`save_sourcefile`). The file is saved inside the build directory
    under the folder app.config['UPLOAD_DIR_BASENAME']
    '''
    filename = upfile.filename
    if filename == '':
        raise ValueError('No selected file')
    if not allowed_upload_file(app, filename):
        raise ValueError("Cannot save '%s': invalid extension" % filename)
    s_filename = secure_filename(filename)

    # copy file to app.config['UPLOAD_DIR_BASENAME'] in the build dir (dest). This is a tmp
    # directory whose content will be moved inside the source dir when saving. this prevents
    # git to see the directory tree changed also when we insert a figure and we do not save the rst

    upload_dir_tmp = get_updloaddir(app, reportdirname, tmp=True, mkdir=True)
    upload_dir_src = get_updloaddir(app, reportdirname, tmp=False, mkdir=False)

    now = datetime.utcnow()
    newfilename = s_filename
    tdelta = timedelta(microseconds=1)
    # assure file does not exist (for safety):
    while True:
        filepath1 = os.path.join(upload_dir_src, newfilename)
        filepath2 = os.path.join(upload_dir_tmp, newfilename)
        if not os.path.exists(filepath1) and not os.path.exists(filepath2):
            break
        f, e = os.path.splitext(s_filename)
        now += tdelta
        newfilename = "%s_%s%s" % (f, now.isoformat(), e)

    upfile.save(filepath2)
    if not os.path.isfile(filepath2):
        raise Exception("Unable to save '%s/%s'" % (os.path.basename(os.path.dirname(filepath2)),
                                                    os.path.basename(filepath2)))
    # return the path relative to the source directory. THIS FILE DOES NOT YET EXISTS,
    # WE NEED TO SAVE THE REPORT TO MOVE THE FILE SAVED TO filepath!
    return filepath1


def allowed_upload_file(app, filename):
    return os.path.splitext(filename)[1][1:].lower() in app.config['UPLOAD_ALLOWED_EXTENSIONS']


def get_fig_directive(app, reportdirname, fig_filepath, fig_label=None, fig_caption=None):
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
    fname = os.path.relpath(fig_filepath, get_sourcedir(app, reportdirname))
    return "%s.. figure:: ./%s\n\n   %s" % (fig_label, fname, fig_caption)


def get_logs_(app, reportdirname, buildtype):
    """Returns two utf8 text arrays: the first, with the full gfxreport log file,
    the second, with the only the errors (if any)
    Returns two empty strings if file not found
    """
    FILENOTFOUND = 'Log file not found'
    logfilecontent = [FILENOTFOUND]
    logfileerrors = [FILENOTFOUND]
    logerrreg = log_err_regexp()
    logfileiter = _logiter(app, reportdirname, buildtype)
    exit_status = next(logfileiter)
    NOERRFOUND = '   No compilation error found'
    if exit_status == 2:
        NOERRFOUND += " (critical errors or exceptions are reported in the full log)"
    firstline = True
    for line in logfileiter:
        if firstline:  # file found, remove first line
            del logfileerrors[-1]
            del logfilecontent[-1]
            firstline = False
        logfilecontent.append(line)
        if line.startswith("*** Sphinx ") or line.startswith("*** Pdflatex "):
            logfileerrors.append(line)
            logfileerrors.append(NOERRFOUND)
        elif logerrreg.match(line):
            if logfileerrors[-1] == NOERRFOUND:
                del logfileerrors[-1]
            # if it's the first error, remove the last line 'No error found'
            logfileerrors.append(line)
    # we should dig into python2 to understand why sometimes the file gives us
    # unicode / decode erros. Probably it's due to how we write it, However this is
    # just for showing logs so 'errors=ignore' might be ok. Moreover, we are stuck to python2
    # but let's not try to solve again this problem again in 2018. This has been solved already
    # in py3:
    return "\n".join(logfilecontent).decode('utf8', errors='replace'), \
        "\n".join(logfileerrors).decode('utf8', errors='replace')


def lastbuildexitcode(app, reportdirname, buildtype):
    """This function takes the report log and parses its first line to return the buid
    exit status.
    :return: the exit code, -1 (unkwnown), 0 (ok, no errors), 1 (ok, compilation errors), 2 faile
    (no file created)
    """
    # try to make a regexp which is general and accounts for potential changes in the
    # output string msg:
    for line in _logiter(app, reportdirname, buildtype):
        return line  # first element is the exit status


def _logiter(app, reportdirname, buildtype):
    ''' returns an iterator over each line of the log file of a given buildtype. The first
    element is an integer indicating the exit status (-1,0,1,2), then each line (stripped)'''
    logfile = get_logfile(app, reportdirname, buildtype)
    firstline = True
    exitstatusreg = re.compile(r"(?<![\w\s])\s*\d+\s*(?![\w\s])")
    if os.path.isfile(logfile):
        with open(logfile) as fopen:
            for line in fopen:
                if firstline:
                    try:
                        yield int(exitstatusreg.search(line).group().strip())
                    except (AttributeError, ValueError):
                        yield -1
                    firstline = False
                line = line.strip()
                yield line
    else:
        yield -1
