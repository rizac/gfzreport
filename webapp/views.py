'''
Created on Apr 3, 2016

@author: riccardo
'''

from webapp import app

@app.route('/')
@app.route('/index')
def index():
    return open()