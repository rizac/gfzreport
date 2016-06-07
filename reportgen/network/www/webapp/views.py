'''
Created on Apr 3, 2016

@author: riccardo
'''
# import os
from flask import request
from reportgen.network.www.webapp import app

# NOTE: all paths relative to the build directory!!!
from core import serve_static_file, get_root_page, get_network_page


@app.route('/')
def index():
    return get_root_page(app)


# @app.route('/<network>')
# def network(network):
#     return get_network_page(app, network)
# 
# 
# # handle static files, redirecting to the correct location
# @app.route('/<path:dirname>/<path:filename>')
# def my_images(dirname, filename):
#     try:
#         network = request.referrer[request.referrer.rfind("/")+1:]
#     except AttributeError as aerr:
#         g = 9
#     return serve_static_file(app, network, dirname, filename)



