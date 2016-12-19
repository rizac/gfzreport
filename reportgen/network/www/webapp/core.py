'''
Created on Apr 3, 2016

Core functionalities for the network webapp
The network web app is a flask app with a config file where we set two variables:


@author: riccardo
'''
import os
from flask import render_template
from reportbuild.main import run as reportbuild_run
import shutil
from StringIO import StringIO
from flask.helpers import send_from_directory
from flask import Blueprint
from flask import request  # , Response
from flask import jsonify


def get_source_rst_content(app, network, as_js=True):
    """
        Reads the source rst from the sphinx source file. If the argument is True, returns
        javascript formatted string (e.g., with newlines replaced by "\n" etcetera)
        :return: a UNICODE string denoting the source rst file (decoded with 'utf8')
    """
    filename = get_source_rstfile_path(app, network)
    # json dump might do what we want, but it fails with e.g. "===" (rst headers, not javascript
    # equal sign. So this procedure might not be optimal but it works
    sio = StringIO()
    with open(filename, "r") as fpoint:
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


def get_root_page(app):
    """
        Returns the root page from where to navigate in the network sub-pages.
        FIXME: this is an old-style server-side way of creating the page, we might exploit
        angular (ng-repeat command) but for such a simple page it's fine
    """
    strio = StringIO()
    strio.write("""<!DOCTYPE html><html><head>
    <link rel="stylesheet" href="static/css/bootstrap/css/bootstrap.min.css" />
    </head><body style='padding:1em'>
    <div class="panel panel-primary">
    <div class="panel-heading">
      <h3 class="panel-title">NETWORK REPORTS</h3>
    </div>
    <div class="panel-body"><ul>
    """)
    data_root = app.config['SOURCE_PATH']
    str_ = "No network report currently loaded"
    if os.path.isdir(data_root):
        for filename in os.listdir(data_root):
            if not filename[0] in ("_", ".") and os.path.isdir(os.path.join(data_root, filename)):
                str_ = ""
                # path = os.path.join(data_root, dir_)
                strio.write("\n<li><a href='%s'>%s</a>" % (filename, filename))
    strio.write(str_)
    strio.write("""</ul>
    </div>
  </div>
    </body>
    </html>""")
    return strio.getvalue()


def get_source_rstfile_path(app, network):
    return get_source_path(app, network, app.config['REPORT_FILENAME'] + ".rst")


def get_source_path(app, network, *paths):
    return os.path.join(app.config['SOURCE_PATH'], network, *paths)


def get_build_path(app, network, *paths):
    return os.path.join(app.config['BUILD_PATH'], network, *paths)


def get_file_ext(build_type):
    if build_type == "latex":
        return ".tex"
    return "." + build_type


def needs_build(app, network, build='html', est_build_time_in_sec=0):
    """
        Returns True if the source rst file ha been modified AFTER the relative build file
        The source folder (with relative .rst) MUST EXIST, otherwise False is returned
        (we don't need a build for a non existing file). The build dir needs not to (returns True
        in that case)
        :param est_build_time_in_sec: a margin to set when comparing the last modified time
        assuming 30 seconds (the default) the source file has been modified in the 30 seconds
        BEFORE the destination last modified time, True is returned, too
    """
    sourcefile = get_source_path(app, network, app.config['REPORT_FILENAME'] + ".rst")
    destfile = get_build_path(app, network, 'latex' if build == 'pdf' else build,
                              app.config['REPORT_FILENAME'] +
                              get_file_ext(build))
    if not os.path.isfile(sourcefile):
        return False
    if not os.path.isfile(destfile):
        return True
    return os.stat(sourcefile).st_mtime > os.stat(destfile).st_mtime - est_build_time_in_sec


def buildreport(app, network, build='html', force=False):
    """Builds the given report according to the specified network. Returns 0 on success,
    anything else otherwise. Note that if build_str is 'html', some post-processing is
    made on the generated file to let jinja2 templating work"""
    if not force and not needs_build(app, network, build):
        return 0
    sourcedir = get_source_path(app, network)
    builddir = get_build_path(app, network, 'latex' if build == 'pdf' else build)
    ret = reportbuild_run(["reportbuild", sourcedir, builddir, "-b", build, "-E"])
    if build == 'html':
        get_jinja_template(app, network, True)
    return ret


def get_jinja_template(app, network, force_rebuild=False):
    """
        Returns the template path to be rendered with render_template
        for a given network.
        The function first creates a base template (html) from sphinx built html page. The latter
        has custom hidden commands that are converted to jinja blocks
        Then we create a report template, based on a pre-defined app template, that will act as
        child of the base template created above
        The function returns the report template path, as argument of render_template
        :param force_rebuild: if False (defaults to True), then the report template path is just
        returned (relative to
        withour creating / overwriting any new file (the file must exist of course, and that's not
        checked for in case)
    """

    report_template_name = "%s.html" % network
    if not force_rebuild:
        return report_template_name

    # CREATE THE BASE TEMPLATE FOR THE GIVEN NETWORK:
    # read the sphinx html page, and replace custom comments with jinja blocks:
    sphinx_html_path = get_build_path(app, network, "html",
                                      app.config['REPORT_FILENAME'] + get_file_ext("html"))
    # replace custom comments with jinja blocks:
    buf = StringIO()
    str_start = "<!--EDITABLE_PAGE %"
    str_end = "% EDITABLE_PAGE-->"
    with open(sphinx_html_path, 'r') as opn:
        for line in opn:
            if str_start in line:
                # use the in operator, faster, and then "waste" time only if its' true (seldom)
                line = line.strip()
                id0, id1 = line.find(str_start), line.rfind(str_end)
                if id0 == 0 and id1 == len(line) - len(str_end):
                    line = "{%" + line[len(str_start):id1] + "%}"
            buf.write(line)

    # write templates to file (create dir if it does not exist):
    # we will write a
    # 1) base template
    # 2) report template, inheriting from base
    # 1) was just created, 2) is copied with a slight modification from the app template
    networks_templates_path = app.config['NETWORKS_TEMPLATES_PATH']
    if not os.path.isdir(networks_templates_path):
        os.makedirs(networks_templates_path)

    # write buf to the "base" template for the given network
    base_template_name = "%s.base.html" % network
    base_template_path = os.path.join(networks_templates_path, base_template_name)
    with open(base_template_path, 'w') as fd:
        buf.seek(0)
        shutil.copyfileobj(buf, fd)

    # now copy the app template path to our report template html.
    # child template, from this dir (or whatever) to the templates dir
    report_template_path = os.path.join(networks_templates_path, report_template_name)

    # NOTE: as we assigned a particular templates folder in each blueprint (see
    # register_blueprint) the first header {% extends [base_template_name] %} in report
    # template path MUST point to the correct path, i.e. relative to networks_templates_path.
    # BUT this is simply report_template_name.
    # So, copy file:
    app_template_path = app.config["APP_TEMPLATE_PATH"]
    with open(app_template_path, 'r') as _src:
        with open(report_template_path, 'w') as _dst:
            _dst.write("{% extends \"" + base_template_name + "\" %}\n")
            _dst.write(_src.read())

    return report_template_name


def copy_source_rst_to_version_folder(app, network):
    source_file = get_source_rstfile_path(app, network)
    if not os.path.isfile(source_file):
        return False
    dest_path = os.path.join(app.config['RST_VERSIONS_PATH'], network)
    if not os.path.isdir(dest_path):
        os.makedirs(dest_path)
    dest_file = os.path.join(dest_path, "%s.rst" % str(os.stat(source_file).st_mtime))
    shutil.copy2(source_file, dest_file)
    return os.path.basename(dest_file)


def get_network_page(app, network, force_build=False, force_templating=True):
    sourcedir = get_source_path(app, network)
    if not os.path.isdir(sourcedir):  # FIXME: better handling!
        return "Network not found"

    ret = buildreport(app, network, "html", force=force_build)
    if ret != 0:
        return "Build failed, please report to the administrator"  # FIXME: better handling!

    # if needsbuild we already updated templates
    jinja_template_path = get_jinja_template(app, network,
                                             force_rebuild=force_templating)

    # note that we set the template dir in register blueprint!
    #     ret = render_template(app.config['REPORT_FILENAME'] + ".html",
    #                           source_data=get_source_rst(app, network))

    ret = render_template(jinja_template_path, source_data=get_source_rst_content(app, network),
                          network_name=network)
    return ret


def save_rst(app, network, unicode_text):
    last_file_name = copy_source_rst_to_version_folder(app, network)

    with open(get_source_rstfile_path(app, network), 'w') as fopen:
        fopen.write(unicode_text.encode('utf8'))

    return last_file_name


def get_pdf(app, network):
    ret = buildreport(app, network, "pdf", force=False)
    # FIXME: ret seems to return 1 if pdf raises exceptions
    # However, we run pdf with interaction=False, so in most cases we might
    # want to just know if the pdf is there
    # This has to be fixed somehow in the future
    # (e.g., show pdf BUT warn if pdflatex did not return 0)
    ret = 0  # FIXME: horrible hack (for the moment) in order to proceed
    if ret == 0:
        builddir = get_build_path(app, network, "latex")
        buildfile = os.path.join(builddir, app.config['REPORT_FILENAME'] + ".pdf")
    if ret != 0 or not os.path.isfile(buildfile):
        raise ValueError("Unable to locate pdf file. Probably this is due to an "
                         "internal server error")
    return buildfile


def register_blueprint(app, network):
    # from http://flask.pocoo.org/docs/0.11/blueprints/:
    # If you want the blueprint to expose templates you can do that by providing the
    # template_folder parameter to the Blueprint constructor:

    # templates_dir = os.path.join(app.config['NETWORK_DATA_DIR'])

    # wait! ... templates_dir is NOT the templates directory! in principle, we could
    # and then call render_template with just the html name. PROBLEM is, that we have the
    # same name in the templates_dir within all network folders, so Flask actually will
    # mess up the rendering cause for render_template('index.html',..) will search the first file
    # matching index.html, which might be that of network N1 or N2 etcetera.
    # So we need to put templates_dir as the root of all networks folder
    # and then call render_template('NETWORK/path/to/index.html')
    netw_bp = Blueprint(network, __name__, url_prefix='/'+network,
                        template_folder=app.config['NETWORKS_TEMPLATES_PATH'])

    @netw_bp.route('')
    @netw_bp.route('/')
    def index():
        return get_network_page(app, network)
    # netw_bp.add_url_rule("/", 'index', index)

    @netw_bp.route('/<path:root>/<path:filepath>')
    def static(root, filepath):
        if root == "static":
            filepath = os.path.join(app.static_folder, filepath)
            return send_from_directory(os.path.dirname(filepath), os.path.basename(filepath))
        return send_from_build_directory(app, network, os.path.join(root, filepath))

    @netw_bp.route('/save', methods=['POST'])
    def save():
        unicode_text = request.get_json()['text']
        last_file_name = save_rst(app, network, unicode_text)
        # note that (editable_page.html) we do not actually make use of the returned response value
        return jsonify({"last_version_filename": last_file_name})  # which converts to a Response
        # return Response({"result": last_file_name}, status=200, mimetype='application/json')

    @netw_bp.route('/pdf', methods=['GET'])
    def return_pdf():
        buildfile = get_pdf(app, network)
        return send_from_directory(os.path.dirname(buildfile), os.path.basename(buildfile),
                                   cache_timeout=0)

    app.register_blueprint(netw_bp)


def send_from_build_directory(app, network, filepath):
    builddir = get_build_path(app, network, 'html')
    dirname = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    return send_from_directory(os.path.join(builddir, dirname), filename)
