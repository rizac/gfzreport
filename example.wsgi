#
# Riccardo's GFZ network report template wsgi. Change just the python virtualenv path and
# the environment variable report
#
# gfz-reportgen.wsgi
#
# Copyright (c) 2016 R. Zaccarelli
# <rizac@gfz-potsdam.de>
#
# -------------------------------------------------------------

# ~~~~~ VARIABLES TO CHANGE: ~~~~~~~~~~~~~
# python path (absolute):
_VIRTUALENV_PYTHONPATH = '/home/riccardo/gfz-reportgen/bin/activate_this.py'
# report type: in the config flask file, there must be a dict with _REPORT_TYPE name
# with a given source folder.
_DATA_PATH = '/data2/gfz-report/annual'
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# ~~~~~~~~DO NOT CHANGE THESE LINES: ~~~~~
activate_this = _VIRTUALENV_PYTHONPATH
execfile(activate_this, dict(__file__=activate_this))
import os
os.environ['DATA_PATH'] = _DATA_PATH
from gfzreport.web.app import get_app
application = get_app()
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
