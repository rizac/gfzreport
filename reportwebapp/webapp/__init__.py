import os
from flask import Flask
# from flask import url_for
# from flask import request
# app = Flask(__name__, static_folder=None)  # static_folder=None DOES TELL FLASK NOT TO ADD ROUTE
# FOR STATIC FOLDEERS

app = Flask(__name__)
app.config.from_object('config')
if not os.environ['REPORT'] or not app.config['REPORTS'].get(os.environ['REPORT'], None):
    raise ValueError(("You need to set the environment variable REPORT "
                      "as a valid key of the REPORTS dict defined in config.py"))
else:
    app.config['DATA_PATH'] = app.config['REPORTS'][os.environ['REPORT']]
    if type(app.config['DATA_PATH']) in (list, tuple):
        app.config['REPORT_FILENAME'] = app.config['DATA_PATH'][1]
        app.config['DATA_PATH'] = app.config['DATA_PATH'][0]
    else:
        app.config['REPORT_FILENAME'] = "report"

    if not os.path.isdir(app.config['DATA_PATH']):
        raise ValueError(('"%s" (path mapped to "%s" env.var): '
                          'directory does not exist') % (app.config['DATA_PATH'],
                                                         os.environ['REPORT']))

app.config['BUILD_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "build"))
app.config['SOURCE_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "source"))
app.config['RST_VERSIONS_PATH'] = os.path.abspath(os.path.join(os.path.dirname(app.config['BUILD_PATH']), "_rst_versions"))
app.config['NETWORKS_TEMPLATES_PATH'] = os.path.abspath(os.path.join(os.path.dirname(app.config['BUILD_PATH']), "_templates"))


# this has to come AFTER app ABOVE
from reportwebapp.webapp import views  # nopep8


# from reportgen.network.www.webapp.core import register_blueprint  # nopep8
# # register blueprints for networks found:
# if os.path.isdir(app.config['SOURCE_PATH']):
#     for dir_ in os.listdir(app.config['SOURCE_PATH']):
#         if dir_[0] not in ('_', ".") and os.path.isdir(os.path.join(app.config['SOURCE_PATH'], dir_)):
#             register_blueprint(app, dir_)

