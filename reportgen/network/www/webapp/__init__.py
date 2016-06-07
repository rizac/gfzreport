import os
from flask import Flask
# from flask import url_for
# from flask import request
# app = Flask(__name__, static_folder=None)  # static_folder=None DOES TELL FLASK NOT TO ADD ROUTE
# FOR STATIC FOLDEERS

app = Flask(__name__)
app.config.from_object('config')

# this has to come AFTER app ABOVE
from reportgen.network.www.webapp import views  # nopep8


from reportgen.network.www.webapp.core import register_blueprint # nopep8
# register blueprints for networks found:
for dir_ in os.listdir(app.config['NETWORK_DATA_DIR']):
    if dir_[0] != '_' and os.path.isdir(os.path.join(app.config['NETWORK_DATA_DIR'], dir_)):
        register_blueprint(app, dir_)
