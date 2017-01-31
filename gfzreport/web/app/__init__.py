import os
from flask import Flask
# from flask import url_for
# from flask import request
# app = Flask(__name__, static_folder=None)  # static_folder=None DOES TELL FLASK NOT TO ADD ROUTE
# FOR STATIC FOLDEERS

app = Flask(__name__)
# app.config.from_object('config')
if 'REPORT' not in os.environ or not os.environ['REPORT']:
    raise ValueError(("You need to set the environment variable REPORT "
                      "as a valid config class name defined in config.py"))
else:
    app.config.from_object('config.' + os.environ['REPORT'])
    if not os.path.isdir(app.config['DATA_PATH']):
        raise ValueError("Not a directory: DATA_PATH='%s'\nPlease change config.py " %
                         app.config['DATA_PATH'])

app.config['BUILD_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "build"))
app.config['SOURCE_PATH'] = os.path.abspath(os.path.join(app.config['DATA_PATH'], "source"))

# this has to come AFTER app ABOVE
from gfzreport.web.app import views  # nopep8
