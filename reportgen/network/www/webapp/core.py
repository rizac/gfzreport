'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
from reportbuild.main import run as reportbuild_run
from glob import iglob
import shutil
from StringIO import StringIO
from flask.helpers import send_from_directory
from flask import Blueprint
# specify here an absolute path RELATIVE TO THE APP DIRECTORY (app.root_dir)
STATICDIR = '../../test-data/build'


def serve_static_file(app, network, filepath):
    builddir = get_builddir(app, network, build='html')
    dirname = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    return send_from_directory(os.path.join(builddir, dirname), filename)


def get_source_rst(filename, as_js=True):
    """
        Reads the source rst from the sphinx source file. If the argument is True, returns
        javascript formatted string (e.g., with newlines replaced by "\n" etcetera)
    """

    # FIXME: FIX PATHS!!! FIXME: FIX UNICODE ISSUE (ARE THERE??)
    with open(filename, "r") as fpoint:
        filecont = fpoint.read()  # .encode('utf8')

    # json dump might do what we want, but it fails with e.g. "===" (rst headers, not javascript
    # equal sign
    sio = StringIO()
    for c in filecont:
        if c == '\n' or c == '\r':
            sio.write("\\")
            c = 'n' if c == '\n' else 'r'
        elif c == '\\' or c == '"':
            sio.write("\\")
        sio.write(c)
    return sio.getvalue()


def get_root_page(app):
    strio = StringIO()
    strio.write("<!DOCTYPE html><html><body>NETWORK REPORTS:<ul>")
    data_root = app.config['NETWORK_DATA_DIR']
    str_ = "No networks currently loaded, if needed please report it to the site administrator"
    if os.path.isdir(data_root):
        for dir_ in os.listdir(data_root):
            if not dir_[0] == "_":
                str_ = ""
                # path = os.path.join(data_root, dir_)
                strio.write("\n<li><a href='/%s'>%s</a>" % (dir_, dir_))
    strio.write(str_)
    strio.write("\n</body>\n</html>")
    return strio.getvalue()


def get_report_last_rst(app, network):
    network_rst_dir = os.path.join(app.config['NETWORK_DATA_DIR'], network, "build", "rst")
    versions = {}
    for filename in os.listdir(network_rst_dir):
        if filename[:-4] == ".rst":
            try:
                vernum = int(filename[:-4])
                versions[vernum] = os.path.join(network_rst_dir, filename)
            except ValueError:
                pass
    return versions[max(versions.keys())]


def get_sourcedir(app, network):
    return os.path.join(app.config['NETWORK_DATA_DIR'], network, "source")


def get_builddir(app, network, build='html'):
    return os.path.join(app.config['NETWORK_DATA_DIR'], network, "build", build)


def buildreport(app, network, build_str='html'):
    sourcedir = get_sourcedir(app, network)
    builddir = get_builddir(app, network, "html")
    return reportbuild_run(["reportbuild", sourcedir, builddir, "-b", build_str, "-E"])
    # FIXME: capture stdout and stderr!!!!


def get_network_page(app, network):
    sourcedir = get_sourcedir(app, network)
    if not os.path.isdir(sourcedir):  # FIXME: better handling!
        return "Network not found"

    builddir = get_builddir(app, network, "html")
    report_rst_filename = os.path.join(sourcedir, app.config['REPORT_FILENAME'] + ".rst")
    report_html_filename = os.path.join(builddir, app.config['REPORT_FILENAME'] + ".html")

    build_report = not os.path.isfile(report_rst_filename) or \
        not os.path.isfile(report_html_filename)

    if not os.path.isfile(report_rst_filename):
        new_report_filename = get_report_last_rst()
        shutil.copy2(new_report_filename, report_rst_filename)

    if build_report:
        ret = buildreport(app, network, "html")
        if ret != 0:
            return "Build failed, please report to the administrator"  # FIXME: better handling!

    builddir = os.path.join(app.config['NETWORK_DATA_DIR'], network, "build", "html")
    report_html = os.path.join(builddir, app.config['REPORT_FILENAME'] + ".html")

    with open(report_html, 'r') as opn:
        main_page = opn.read()

    rst_source = os.path.join(builddir, "_sources", app.config['REPORT_FILENAME'] + ".txt")

    main_page = main_page.replace("$scope.isEditable = false;", "$scope.isEditable = true;")

    main_page = main_page.replace('editor.setValue("");',
                                  'editor.setValue("{0}", 0);'.format(get_source_rst(rst_source)))

    return main_page
    # return re.sub("<\\s*p(\\s|>)", "<p contenteditable=\"true\"\\1", main_page)


def register_blueprint(app, network):
    netw_bp = Blueprint(network, __name__, url_prefix='/'+network)

    @netw_bp.route('')
    @netw_bp.route('/')
    def index():
        return get_network_page(app, network)
    # netw_bp.add_url_rule("/", 'index', index)

    @netw_bp.route('/<path:filepath>')
    def static(filepath):
        return serve_static_file(app, network, filepath)

    app.register_blueprint(netw_bp)

