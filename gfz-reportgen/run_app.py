'''
Created on Apr 3, 2016

@author: riccardo
'''
import os
import sys
import argparse
import random
import threading
import webbrowser
from webapp import app


def parseargs(args):
    apr = argparse.ArgumentParser()
    apr.add_argument("-d", "--debug", type=bool, help="Run in debug mode", default=False)
    apr.add_argument("-p", "--port", type=int, help="Use specific port (defaults to random port)",
                     default=5000)
    return apr.parse_args(args)

if __name__ == '__main__':
    args = parseargs(sys.argv[1:])
    debug = args.debug
    port = args.port  # if args.port is not None else 5000 + random.randint(0, 999)
#     if debug:
#         debug = False
#         url = "http://127.0.0.1:{0}".format(args.port)
#         threading.Timer(1.25, lambda: webbrowser.open(url)).start()
    if debug:
        app.run(port=port, debug=debug)  # , use_reloader=False)  # avoid debugger starting twice
    else:
        app.run(port=port, debug=debug)