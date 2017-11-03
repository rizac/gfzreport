'''
Created on Oct 26, 2017

@author: riccardo
'''
import unittest
from contextlib import contextmanager
from click.testing import CliRunner
import os, sys

from gfzreport.cli import main as gfzreport_main
from gfzreport.sphinxbuild import get_logfilename, exitstatus2str
from datetime import datetime, timedelta
import shutil
from gfzreport.web.app import get_app, initdbusers, initdb
from mock import patch
from io import BytesIO
import re

from gfzreport.web.app.core import _run as _reportbuild_run_orig
import tempfile
from urllib2 import URLError
import json
from gfzreport.web.app import models
import time


# global paths defined once
SOURCEREPORTDIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "testdata")

TEMPLATE_NETWORK = ["template", "n"]
BUILD = ['build']
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

        # setup stuff in self.source:
        # the users txt file, and a config that will be loaded
        # 
        with open(os.path.join(os.getcwd(), 'users.txt'), 'w') as opn:
            opn.write("""[
{"email": "user1_ok@example.com", "path_restriction_reg": ".*"},
{"email": "user2_ok@example.com", "path_restriction_reg": "/ZE_2012"},
{"email": "user3_no@example.com", "path_restriction_reg": ".*/ZE2012$"},
{"email": "user4_ok@example.com", "path_restriction_reg": ".*/ZE2012$"}
]""")

        with open(os.path.join(os.getcwd(), 'users.txt'), 'r') as opn:
            _ = opn.read()

        with open(os.path.join(os.getcwd(), 'users.txt'), 'r') as opn:
            _ = opn.readline()

        # os.makedirs(self.source)
        self.addCleanup(_cleanup, self)

        self.mock_urlopen = patch('gfzreport.templates.network.core.utils.urllib2.urlopen').start()
        self.mock_urlopen.side_effect = _get_urlopen_sideeffect()

        self.mock_iterdcurl = patch('gfzreport.templates.network.core.iterdcurl').start()
        self.mock_iterdcurl.side_effect=lambda *a, **v: _getdatacenters(*a, **v)

        args = ['-n', 'ZE', '-s', '2012', '--noprompt', '--inst_uptimes', os.path.join(SOURCEREPORTDIR, 'inst_uptimes'),
                '--noise_pdf', os.path.join(SOURCEREPORTDIR, 'noise_pdf'),
                '-o', os.path.join(self.source, "source")
                ]
        runner = CliRunner()
        res = runner.invoke(gfzreport_main, TEMPLATE_NETWORK + args, catch_exceptions=False)
        if res.exit_code != 0:
            raise unittest.SkipTest("Unable to generate test report:\n%s" % res.output)

        os.environ['DATA_PATH'] = self.source
        os.environ['DB_PATH'] = self.source 
        self.app = get_app(config_obj='gfzreport.web.config_example.BaseConfig',
                           # set a time long enough to allow session to testing when session
                           # is active and short enough not to wait forever when testing
                           # expired session via time.sleep:
                           PERMANENT_SESSION_LIFETIME=timedelta(seconds=2))

    def tearDown(self):
        pass

    def get_buildir(self, buildtype):
        '''returns the buil directory. buildype can be 'pdf', 'latex' or 'html' (in the two
        first cases, the path is the same)'''
        return os.path.join(self.source, 'build', 'ZE_2012', 'latex' if buildtype=='pdf' else buildtype)


    @patch('gfzreport.web.app.core._run', side_effect = _reportbuild_run_orig)
    def test_report_remember_cookie_duration(self, mock_reportbuild_run):

        duration = self.app.config['PERMANENT_SESSION_LIFETIME']
        # test the page pdf. We are unauthorized, so this should give us error:
        with self.app.test_request_context():
            app = self.app.test_client()
            # If we add routes with the slash at the end, we should 
            # add follow_redirect=True to app.get. See
            # http://flask.pocoo.org/docs/0.11/quickstart/#routing
            res = app.get("/ZE_2012/pdf", follow_redirects=True)
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert res.status_code == 401
            assert mock_reportbuild_run.call_count == 0
        
            # now try to login:
            # with a non-registered email
            res = app.post("/ZE_2012/login", data={'email' :'abc'})
            assert res.status_code == 401
            # thus, we do not access the pdf creation:
            res = app.get("/ZE_2012/pdf", follow_redirects=True)
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert res.status_code == 401
            assert mock_reportbuild_run.call_count == 0

            # now try to login:
            # with a registered email and wrong permission
            res = app.post("/ZE_2012/login", data={'email' :'user3_no@example.com'})
            assert res.status_code == 403
            # thus, we do not access the pdf creation:
            res = app.get("/ZE_2012/pdf", follow_redirects=True)
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert res.status_code == 401
            assert mock_reportbuild_run.call_count == 0

            # now try to login:
            # with another non registered email
            res = app.post("/ZE_2012/login", data={'email' :'user2_ok@example.com'})
            assert res.status_code == 200

            # check that the current user has the fields written
            with models.session(self.app) as session:
                user = session.query(models.User).filter(models.User.email == 'user2_ok@example.com').first()
                assert user.editing_path is not None
                assert user.login_date is not None

            # sleep two seconds and see that we should have been logged out from the session
            # (we set REMEMBER_COOKIE_DURATION = 1 second)
            time.sleep(duration.total_seconds()+1)

            # Note that we need to setup urlread for the arcgis image, because we mocked it
            # (FIXME: we mocked in gfzreport.templates.network.core.utils.urllib2.urlopen,
            # why is it mocked in map module?!!!)
            # The signature is:
            # _get_urlopen_sideeffect(geofon_retval=None, others_retval=None):
            # Thus, we setup others_retval=URLError, which means that if 'geofon' is not in url
            # (which is the case for arcgis query) and URLException is raised.
            # This way, the map is generated with drawcostallines
            # and the pdf is created. Keep in mind that pdflatex will raise in any case
            self.mock_urlopen.side_effect = _get_urlopen_sideeffect(None, URLError('wat'))
            res = app.get("/ZE_2012/pdf", follow_redirects=True)
            # few stupid asserts, the main test is not raising
            # we should have an html page. But login session should have been expired!
            assert res.status_code == 401
            assert mock_reportbuild_run.call_count == 0


            # now try to login again:
            # with another non registered email
            usrname = 'user2_ok'
            res = app.post("/ZE_2012/login", data={'email' :'%s@example.com' % usrname})
            assert res.status_code == 200
            
            # now try to login with another user. This should fail as we are still in
            # the session duration:
            # with another non registered email
            res = app.post("/ZE_2012/login", data={'email' :'user1_ok@example.com'})
            assert res.status_code == 409  # conflict
            assert ("Conflict: user '%s' is editing the same report (or forgot to log out): "
                    "by default, his/her session will expire in 0:00:" % usrname) in json.loads(res.data)['message']
            # sleep two seconds and see that we should have been logged out from the session
            # (we set REMEMBER_COOKIE_DURATION = 1 second)
            time.sleep(duration.total_seconds()+1)
            # now try to login with the same user. As first user's session time expired,
            # we should be able to login:
            res = app.post("/ZE_2012/login", data={'email' :'user1_ok@example.com'})
            assert res.status_code == 200
            
            
            
#             # check commits:
#             res = app.post("/ZE_2012/get_commits",
#                            content_type='application/json')
# 
#             assert res.status_code == 200
#             commitz = json.loads(res.data)
#             assert len(commitz) == 1
#             commit = commitz[0]
#             assert commit['email'] == 'user1_ok@example.com'
#             assert "pdf: Build successful, with compilation errors" in commit['notes']
#             
#             
#             # check logs:
#             res = app.post("/ZE_2012/get_logs", data=json.dumps({'buildtype': 'pdf'}),
#                            content_type='application/json')
#             
#             assert res.status_code == 200
#             _data = json.loads(res.data)
#             # _data has two elements: the standard error (plus some titles added, such as
#             # 'Sphinx build') and the standard error showing only relevant errors/warnings: these
#             # are lines recognizable by a special format (using regexps) and that are more
#             # informative for the web user than the all standard error, which might be too verbose.
#             # (The the standard error showing only relevant errors/warnings can be shown by means
#             # of a checkobx on the GUI)
#             assert len(_data) == 2
#             # first string is the whole log file, must be greater than the second one (errors only):
#             assert len(_data[0]) > len(_data[1])
#             errlogcontent = _data[1]
#             # sphinx build (rst to latex) was successfull:
#             assert 'No compilation error found' in errlogcontent[:errlogcontent.find('Pdflatex')]
#             # pdflatex gave some error(s): if we fix this in the future, it might have no errors,
#             # in case check errlogcontent and assert something else or comment out the following assertion:
#             assert "ERROR:" in errlogcontent[errlogcontent.find('Pdflatex'):]
# 
#             mock_reportbuild_run.reset_mock()
#             # test that we do not call mock_reportbuild_run
#             # once again:
#             res = app.get("/ZE_2012/pdf", follow_redirects=True)
#             # few stupid asserts, the main test is not raising
#             # we should ahve an html page:
#             assert res.status_code == 200
#             # assert we did not call mock_reportbuild again:
#             assert mock_reportbuild_run.call_count == 0
#         
#             # If needed UNCOMMENT NEXT LINE AND reset url mock side effect (in case used afterwards)?
#             # self.mock_urlopen.side_effect = se

 
   

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()