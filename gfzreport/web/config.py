'''
Created on Jun 6, 2016
Flask config file
@author: riccardo
'''
# http://flask.pocoo.org/docs/0.12/config/#development-production
# One class per report type. First the "base" class:


class BaseConfig(object):
    DEBUG = False
    REPORT_BASENAME = 'report'
    DATA_PATH = None  # where the sources are. Each subfolder not starting with "_" inside SOURCE_PATH will be taken as a report 
    UPLOAD_ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    UPLOAD_DIR_BASENAME = "_www_uploaded_files"  # in principle, you don't need t change this


# then the report types (one class per report type):
# Note that the environment variable REPORT must match exactly one of the following subclasses:


class NETWORK(BaseConfig):
    DEBUG = True
    DATA_PATH = '/Users/riccardo/work/gfz/data/gfzreport/test-data/webapp/network'
