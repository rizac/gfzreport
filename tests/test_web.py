'''
Created on Jul 8, 2017

@author: riccardo
'''
import unittest
from contextlib import contextmanager
from click.testing import CliRunner
import os

from gfzreport.templates.network.main import main as network_reportgen_main
from gfzreport.sphinxbuild.main import main as sphinxbuild_main, get_logfilename, exitstatus2str
from datetime import datetime
import shutil
from gfzreport.web.app import get_app, initdbusers, initdb
from mock import patch
from io import BytesIO
import re

from gfzreport.web.app.core import _run_sphinx as _reportbuild_run_orig
import tempfile
from urllib2 import URLError
import json
from gfzreport.web.app import models


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

        args = ['ZE', '2012', '--noprompt', '--inst_uptimes', os.path.join(SOURCEREPORTDIR, 'inst_uptimes'),
                '--noise_pdf', os.path.join(SOURCEREPORTDIR, 'noise_pdf'),
                '-o', os.path.join(self.source, "source")
                ]
        runner = CliRunner()
        res = runner.invoke(network_reportgen_main, args, catch_exceptions=False)
        if res.exit_code != 0:
            raise unittest.SkipTest("Unable to generate test report:\n%s" % res.output)

        os.environ['DATA_PATH'] = self.source
        os.environ['DB_PATH'] = self.source 
        self.app = get_app(config_obj='gfzreport.web.config_example.BaseConfig')

    def tearDown(self):
        pass

    def get_buildir(self, buildtype):
        '''returns the buil directory. buildype can be 'pdf', 'latex' or 'html' (in the two
        first cases, the path is the same)'''
        return os.path.join(self.source, 'build', 'ZE_2012', 'latex' if buildtype=='pdf' else buildtype)


    def test_change_users_settings_file(self):
        with models.session(self.app) as session:
            users = session.query(models.User).all()

        # assert user with total
        for u in users:
            if u.email == "user1_ok@example.com":
                assert u.path_restriction_reg == ".*"

        assert len(users) == 4
        with open(os.path.join(self.source, 'users.txt'), 'w') as opn:
            opn.write("""[
{"email": "user1_ok@example.com"},
{"email": "user2_no@example.com", "path_restriction_reg": "/ZE_2012"}
]""")
        initdbusers(self.app)

        with models.session(self.app) as session:
            users2 = session.query(models.User).all()

        assert len(users2) == 2
        # check that we updated user1:
        with models.session(self.app) as session:
            users = session.query(models.User).all()
            for u in users:
                if u.email == "user1_ok@example.com":
                    assert u.path_restriction_reg is None

    @patch('gfzreport.web.app.core._run_sphinx', side_effect = _reportbuild_run_orig)
    def test_report_views(self, mock_reportbuild_run):
        with self.app.test_request_context():
            app = self.app.test_client()
            res = app.get("/")
            m = re.compile(r">ZE_2012</a>", re.DOTALL | re.MULTILINE).search(res.data)
            assert m

        with self.app.test_request_context():
            app = self.app.test_client()
            # If we add routes with the slash at the end, we should 
            # add follow_redirect=True to app.get. See
            # http://flask.pocoo.org/docs/0.11/quickstart/#routing
            res = app.get("/ZE_2012", follow_redirects=True)
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
            res = app.get("/ZE_2012/content/html", follow_redirects=True)
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert mock_reportbuild_run.call_count == 1
            logfile = os.path.join(os.getcwd(), 'build',  'ZE_2012', 'html', get_logfilename())
            with open(logfile, 'r') as opn:
                logfilecontent = opn.read()

            #stupid test, we shouldhave warnings concerning images not found, check we have something
            # printed out
            assert len(logfilecontent) > 0 and "WARNING" in logfilecontent
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
            

    @patch('gfzreport.web.app.core._run_sphinx', side_effect = _reportbuild_run_orig)
    def test_report_views_auth(self, mock_reportbuild_run):
        
        # test the page pdf. We are unauthorized, so this should give us error:
        with self.app.test_request_context():
            app = self.app.test_client()
            # If we add routes with the slash at the end, we should 
            # add follow_redirect=True to app.get. See
            # http://flask.pocoo.org/docs/0.11/quickstart/#routing
            res = app.get("/ZE_2012/content/pdf", follow_redirects=True)
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert res.status_code == 401
            assert mock_reportbuild_run.call_count == 0
        
            # now try to login:
            # with a non-registered email
            res = app.post("/ZE_2012/login", data={'email' :'abc'})
            assert res.status_code == 401
            # thus, we do not access the pdf creation:
            res = app.get("/ZE_2012/content/pdf", follow_redirects=True)
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert res.status_code == 401
            assert mock_reportbuild_run.call_count == 0

            # now try to login:
            # with a registered email and wrong permission
            res = app.post("/ZE_2012/login", data={'email' :'user3_no@example.com'})
            assert res.status_code == 403
            # thus, we do not access the pdf creation:
            res = app.get("/ZE_2012/content/pdf", follow_redirects=True)
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

            # now try to login with another user:
            res = app.post("/ZE_2012/login", data={'email' :'user1_ok@example.com'})
            assert res.status_code == 409

            # now logout
            res = app.post("/ZE_2012/logout")
            # check that the current user has the fields written
            with models.session(self.app) as session:
                user = session.query(models.User).filter(models.User.email == 'user2_ok@example.com').first()
                assert user.editing_path is None
                assert user.login_date is None

            # and re-login with user1:
            res = app.post("/ZE_2012/login", data={'email' :'user1_ok@example.com'})
            assert res.status_code == 200

            # trying to re-login with the same user has no effect:
            res = app.post("/ZE_2012/login", data={'email' :'user1_ok@example.com'})
            assert res.status_code == 200

            
            # but w need to setup urlread for the arcgis image, because we mocked it
            # (FIXME: we mocked in gfzreport.templates.network.core.utils.urllib2.urlopen,
            # why is it mocked in map module?!!!)
            # we setup an URLError if 'geofon' is not in url (which is the case for
            # arcgis query). This way, the map is generated with drawcostallines
            # and the pdf is created
            se = self.mock_urlopen.side_effect
            self.mock_urlopen.side_effect = _get_urlopen_sideeffect(None, URLError('wat'))
            res = app.get("/ZE_2012/content/pdf", follow_redirects=True)
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert res.status_code == 200
            assert mock_reportbuild_run.call_count == 1

            # check commits:
            res = app.post("/ZE_2012/get_commits",
                           content_type='application/json')

            assert res.status_code == 200
            commitz = json.loads(res.data)
            assert len(commitz) == 1
            commit = commitz[0]
            assert commit['email'] == 'user1_ok@example.com'
            assert "pdf: Build successful, with compilation errors" in commit['notes']
            
            
            # check logs:
            res = app.post("/ZE_2012/get_logs", data=json.dumps({'buildtype': 'pdf'}),
                           content_type='application/json')
            
            assert res.status_code == 200
            # res.data is a 3element list of two elements: the log name, and the log file
            # content. The files are two: the sphinx log and the pdf log. So assert:
            _data = json.loads(res.data)
            assert len(_data) == 2
            # first string is the whole log file, must be greater than the second one (errors only):
            assert len(_data[0]) > len(_data[1])
            errlogcontent = _data[1]
            # sphinx build (rst to latex) was successfull:
            assert 'No error found' in errlogcontent[:errlogcontent.find('Pdflatex')]
            # pdflatex gave some error(s): if we fix this in the future, it might have no errors,
            # in case check errlogcontent and assert something else or comment out the following assertion:
            assert "ERROR:" in errlogcontent[errlogcontent.find('Pdflatex'):]

            mock_reportbuild_run.reset_mock()
            # test that we do not call mock_reportbuild_run
            # once again:
            res = app.get("/ZE_2012/content/pdf", follow_redirects=True)
            # few stupid asserts, the main test is not raising
            # we should ahve an html page:
            assert res.status_code == 200
            # assert we did not call mock_reportbuild again:
            assert mock_reportbuild_run.call_count == 0
        
            # If needed UNCOMMENT NEXT LINE AND reset url mock side effect (in case used afterwards)?
            # self.mock_urlopen.side_effect = se
            

    @patch('gfzreport.web.app.core._run_sphinx', side_effect = _reportbuild_run_orig)
    @patch('gfzreport.sphinxbuild.main.pdflatex', side_effect = Exception('!wow!'))
    def test_report_views_build_failed(self, mock_pdflatex, mock_reportbuild_run):
        
        # test the page pdf. We are unauthorized, so this should give us error:
        with self.app.test_request_context():
            app = self.app.test_client()

            # login:
            # now try to login:
            # with a registered email and good write permission
            res = app.post("/ZE_2012/login", data={'email' :'user1_ok@example.com'})
            assert res.status_code == 200
            # thus, we DO access the pdf creation:

            # but w need to setup urlread for the arcgis image, because we mocked it
            # (FIXME: we mocked in gfzreport.templates.network.core.utils.urllib2.urlopen,
            # why is it mocked in map module?!!!)
            # we setup an URLError if 'geofon' is not in url (which is the case for
            # arcgis query). This way, the map is generated with drawcostallines
            # and the pdf is created
            se = self.mock_urlopen.side_effect
            self.mock_urlopen.side_effect = _get_urlopen_sideeffect(None, URLError('wat'))
            res = app.get("/ZE_2012/content/pdf", follow_redirects=True)
            # status code is still 200, as we redirect to the error page
            assert res.status_code == 200
            # raw check: the title of the error page. If we change it in the future, fix this test accordingly:
            assert "Build failed" in res.data
            # if we try to get the log:
            logfile = os.path.join(self.get_buildir('pdf'), get_logfilename())
            with open(logfile) as fopen:
                logcontent = fopen.read()

            assert "!wow!" in logcontent   # the exception message (see mock above)
            # but if we get the commits, we registered that pdflatex was wrong:
            res = app.post("/ZE_2012/get_commits",
                           content_type='application/json')

            assert res.status_code == 200
            commitz = json.loads(res.data)
            commit = commitz[0]
            assert commit['email'] == 'user1_ok@example.com'
            assert ("pdf: %s" % exitstatus2str(2)) in commit['notes']
            
            res1 = app.post("/ZE_2012/last_build_exitcode",
                           data=json.dumps({'buildtype': "html"}),
                           content_type='application/json')
            
            res2 = app.post("/ZE_2012/last_build_exitcode",
                           data=json.dumps({'buildtype': "pdf"}),
                           content_type='application/json')

            assert res1.status_code == 200 and res2.status_code == 200
            assert int(res1.data) == -1
            assert int(res2.data) == 2
            
            # assert we do not have a html file:
            htmlfile = os.path.join(self.get_buildir('html'), 'report.html')
            assert not os.path.isfile(htmlfile)
            # compile html
            res = app.get("/ZE_2012/content/html", follow_redirects=True)
            # status code is still 200, as we redirect to the error page
            assert res.status_code == 200
            # re-query the exit code:
            res1 = app.post("/ZE_2012/last_build_exitcode",
                           data=json.dumps({'buildtype': "html"}),
                           content_type='application/json')
            assert res.status_code == 200
            assert int(res1.data) == 0
            assert os.path.isfile(htmlfile)
            


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()