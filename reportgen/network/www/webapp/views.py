'''
Created on Apr 3, 2016

@author: riccardo
'''
from reportgen.network.www.webapp import app
from core import get_root_page


@app.route('/')
def index():
    return get_root_page(app)
