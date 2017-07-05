#
# Riccardo's GFZ network report generation
#
# gfz-reportgen.wsgi
#
# Copyright (c) 2016 R. Zaccarelli
# <rizac@gfz-potsdam.de>
#
# -------------------------------------------------------------

# virtualenv incantation:
activate_this = '/home/riccardo/gfz-reportgen/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import os
import sys

# print sys.path

# sys.path.insert(0, '/var/www/html/gfz-reportgen')
# sys.path.insert(0, '/var/www/html/gfz-reportgen/gfzreport/web')

os.environ['REPORT'] = 'ANNUAL'

# from gfzreport.web.app import app as application
from gfzreport.web.app import get_app
application = get_app()
