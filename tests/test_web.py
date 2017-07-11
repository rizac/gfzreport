'''
Created on Jul 8, 2017

@author: riccardo
'''
import unittest
from contextlib import contextmanager
from click.testing import CliRunner
import os

from gfzreport.templates.network.main import main as network_reportgen_main
from gfzreport.sphinxbuild.main import main as sphinxbuild_main
from datetime import datetime
import shutil
from gfzreport.web.app import get_app
from mock import patch
from io import BytesIO
import re

from gfzreport.web.app.core import reportbuild_run as _reportbuild_run_orig, get_sphinxlogfile
import tempfile



# global paths defined once
SOURCEREPORTDIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "testdata")
# SOURCEWEBDIR = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "tmp")

def _cleanup(testobj):
    os.chdir(testobj.cwd)
    try:
        shutil.rmtree(testobj.source)
    except:
        pass
    try:
        testobj.mock_urlopen.stop()
    except:
        pass
    try:
        testobj.mock_iterdcurl.stop()
    except:
        pass


def _get_urlopen_sideeffect(geofon_retval=None, others_retval=None):
    '''Returns a side_effect function for the urlopen.urlread mock
    :param geofon_retval: the string returned from urlopen.read when querying geofon network
    If None, defaults to "ZE.network.xml" content (file defined in testdata dir)
    If Exception, then it will be raised
    :param others_retval: the string returned from urlopen.read when querying NON geofon stations
    within the geofon network boundaries
    If None, defaults to "other_stations.xml" content (file defined in testdata dir)
    If Exception, then it will be raised
    '''
    def sideeffect(url, timeout=None):
        if "geofon" in url:
            if isinstance(geofon_retval, Exception):
                raise geofon_retval
            if geofon_retval is None:
                with open(os.path.join(SOURCEREPORTDIR, "ZE.network.xml")) as opn:
                    return BytesIO(opn.read())
            else:
                return BytesIO(geofon_retval)
        else:
            if isinstance(others_retval, Exception):
                raise others_retval
            if others_retval is None:
                with open(os.path.join(SOURCEREPORTDIR, "other_stations.xml")) as opn:
                    return BytesIO(opn.read())
            else:
                return BytesIO(others_retval)
    return sideeffect


def _getdatacenters(*a, **v):
    """returns the datacenters as the returned response that the eida routing service
    would give. The returned string is the datacenters.txt file in the testdata folder"""
    with open(os.path.join(SOURCEREPORTDIR, "datacenters.txt"), 'rb') as opn:
        ret = opn.read()

    for dc in ret.splitlines():
        if dc[:7] == 'http://':
            yield dc

class Test(unittest.TestCase):


    def setUp(self):
        self.cwd = os.getcwd()
        self.source = tempfile.mkdtemp()  #os.path.join(SOURCEWEBDIR, datetime.utcnow().isoformat())
        os.chdir(self.source)
        
        # os.makedirs(self.source)
        self.addCleanup(_cleanup, self)

        self.mock_urlopen = patch('gfzreport.templates.network.core.utils.urllib2.urlopen').start()
        self.mock_urlopen.side_effect = _get_urlopen_sideeffect()
        
        self.mock_iterdcurl = patch('gfzreport.templates.network.core.iterdcurl').start()
        self.mock_iterdcurl.side_effect=lambda *a, **v: _getdatacenters(*a, **v)

        args = ['ZE', '2012', '--noprompt', '--inst_uptimes', os.path.join(SOURCEREPORTDIR, 'inst_uptimes'),
                '--noise_pdf', os.path.join(SOURCEREPORTDIR, 'noise_pdf'),
                '-o', os.path.join(self.source, "source")
                ]
        runner = CliRunner()
        res = runner.invoke(network_reportgen_main, args, catch_exceptions=False)
        if res.exit_code != 0:
            raise unittest.SkipTest("Unable to generate test report:\n%s" % res.output)

        os.environ['DATA_PATH'] = self.source
        self.app = get_app()

    def tearDown(self):
        pass

    
    @patch('gfzreport.web.app.core.reportbuild_run', side_effect = _reportbuild_run_orig)
    def test_report_views(self, mock_reportbuild_run):
        with self.app.test_request_context():
            app = self.app.test_client()
            res = app.get("/")
            m = re.compile(r"ZE_2012</a>\s*</ul>", re.DOTALL | re.MULTILINE).search(res.data)
            assert m

        with self.app.test_request_context():
            app = self.app.test_client()
            # If we add routes with the slash at the end, we should 
            # add follow_redirect=True to app.get. See
            # http://flask.pocoo.org/docs/0.11/quickstart/#routing
            res = app.get("/ZE_2012")
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert "<html lang=\"en\">" in res.data
            assert "ng-app=\"MyApp\" ng-controller=\"MyController\"" in res.data
            j =9

        # now test the page content
        with self.app.test_request_context():
            app = self.app.test_client()
            # If we add routes with the slash at the end, we should 
            # add follow_redirect=True to app.get. See
            # http://flask.pocoo.org/docs/0.11/quickstart/#routing
            res = app.get("/ZE_2012/content/html")
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert mock_reportbuild_run.call_count == 1
            logfile = os.path.join(os.getcwd(),
                                                   'build',  'ZE_2012', 'html', '_sphinx_stderr.log')
            with open(logfile, 'r') as opn:
                logfilecontent = opn.read()
            
            #stupid test, we shouldhave warnings concerning images not found, check we have something
            # printed out
            assert len(logfilecontent) > 0
            g = 9
            
        mock_reportbuild_run.reset_mock()
        # now test the page content is not re-built:
        with self.app.test_request_context():
            app = self.app.test_client()
            # If we add routes with the slash at the end, we should 
            # add follow_redirect=True to app.get. See
            # http://flask.pocoo.org/docs/0.11/quickstart/#routing
            res = app.get("/ZE_2012/content/html")
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert mock_reportbuild_run.call_count == 0
            

    @patch('gfzreport.web.app.core.reportbuild_run', side_effect = _reportbuild_run_orig)
    def test_report_views_auth(self, mock_reportbuild_run):
        
        # test the page pdf. We are unauthorized, so this should give us error:
        with self.app.test_request_context():
            app = self.app.test_client()
            # If we add routes with the slash at the end, we should 
            # add follow_redirect=True to app.get. See
            # http://flask.pocoo.org/docs/0.11/quickstart/#routing
            res = app.get("/ZE_2012/content/pdf")
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert res.status_code == 401
            assert mock_reportbuild_run.call_count == 0
            
        # now add some user
            
#         mock_reportbuild_run.reset_mock()
#         # now test the page content is not re-built:
#         with self.app.test_request_context():
#             # If we add routes with the slash at the end, we should 
#             # add follow_redirect=True to app.get. See
#             # http://flask.pocoo.org/docs/0.11/quickstart/#routing
#             res = app.get("/ZE_2012/content/html")
#             # few stupid asserts, the main test is not raising
#             # we should ahve an html page:
#             assert mock_reportbuild_run.call_count == 0
#             
#         
#         mock_reportbuild_run.reset_mock()
#         # now test the page content is not re-built:
#         with self.app.test_request_context():
#             # If we add routes with the slash at the end, we should 
#             # add follow_redirect=True to app.get. See
#             # http://flask.pocoo.org/docs/0.11/quickstart/#routing
#             res = app.get("/ZE_2012/content/html")
#             # few stupid asserts, the main test is not raising
#             # we should ahve an html page:
#             assert mock_reportbuild_run.call_count == 0
            


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()