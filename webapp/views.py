'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
from webapp import app

# NOTE: all paths relative to the build directory!!!
from core import serve_static_file, get_main_page


@app.route('/')
@app.route('/index')
def index():
    return get_main_page()


@app.route('/_static/<path:filename>')
def my_static(filename):
    return serve_static_file(app, "_static", filename)
 
 
@app.route('/_images/<path:filename>')
def my_images(filename):
    return serve_static_file(app, "_images", filename)
 
 
@app.route('/_sources/<path:filename>')
def my_sources(filename):
    return serve_static_file(app, "_sources", filename)