'''
Created on Jul 8, 2017

@author: riccardo
'''
import unittest
from contextlib import contextmanager
from click.testing import CliRunner
import os

from gfzreport.cli import main as gfzreport_main
from gfzreport.sphinxbuild import get_logfilename
from datetime import datetime
import shutil
from gfzreport.web.app import get_app, initdbusers, initdb
from mock import patch
from io import BytesIO
import re

from gfzreport.web.app.core import _run as _reportbuild_run_orig, master_doc
import tempfile
from urllib2 import URLError
import json
from gfzreport.web.app import models
from StringIO import StringIO
import pytest


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
{"email": "user2_no@example.com", "path_restriction_reg": "/ZE_2012"},
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
        self.app = get_app(config_obj='gfzreport.web.config_example.BaseConfig')

    def tearDown(self):
        pass

    def get_buildir(self, buildtype):
        '''returns the buil directory. buildype can be 'pdf', 'latex' or 'html' (in the two
        first cases, the path is the same)'''
        return os.path.join(self.source, 'build', 'ZE_2012', 'latex' if buildtype=='pdf' else buildtype)


    @patch('gfzreport.web.app.core._run', side_effect = _reportbuild_run_orig)
    def test_uploadfile(self, mock_reportbuild_run):
        with self.app.test_request_context() as req:
            app = self.app.test_client()
            res = app.post("/ZE_2012/upload_file")
            # not authenitcated:
            assert res.status_code == 401
            
            # login:
            # now try to login:
            # with a registered email
            res = app.post("/ZE_2012/login", data={'email' :'user1_ok@example.com'})
            assert res.status_code == 200
            
            # this raises ValueError, returned code is 500
            res = app.post("/ZE_2012/upload_file")
            assert res.status_code == 400
            
            # with data, wrong extension:
            res = app.post("/ZE_2012/upload_file", data = {
                'file': (StringIO('my file contents'), 'hello world.txt'),
            })
            # no label and caption specified:
            assert res.status_code == 400
            
            res = app.post("/ZE_2012/upload_file", data = {
                'file': (StringIO('my file contents'), 'hello world.txt'),
                'label': 'bla', 'caption': ''
            })
            # wrong file extension
            assert res.status_code == 400
            
            
            # ok, now let's do a real one:
            # first check that the supposed upload file directory does not exist
            uploaddir = os.path.join(self.source, 'source', 'ZE_2012', self.app.config['UPLOAD_DIR_BASENAME'])
            uploaddir_tmp = os.path.join(self.source, 'build', 'ZE_2012', self.app.config['UPLOAD_DIR_BASENAME'])
            assert not os.path.isdir(uploaddir)
            assert not os.path.isdir(uploaddir_tmp)
            
            # define a "GOOD" filename (good extension):
            uploadfname = 'bla.png'
            figcaption = 'some weird caption which is not part of the rst klrg;jimovwjeowlhawrclghnsrgq'
            figlabel = 'some weird label not part of the rst vrguhreosvgjqo;acjglsevnghmqalmsvnd'
            res = app.post("/ZE_2012/upload_file", data = {
                'file': (StringIO('my file contents'), uploadfname),
                'label': figlabel, 'caption': figcaption
            })
            # test response was ok:
            assert res.status_code == 200
            # test we created the dir
            assert os.path.isdir(uploaddir_tmp)
            assert not os.path.isdir(uploaddir)
            # test we have the file:
            assert os.listdir(uploaddir_tmp) == [uploadfname]
            with open(os.path.join(uploaddir_tmp, uploadfname)) as fopn:
                content = fopn.read()
            assert content == 'my file contents'

            # assert the directive has been written in the document:
            # Note: the rst is NOT modified server side, the server SENDS the directive
            # to the client. So we do not need to check for the rst, which is at:
#             rstfile = os.path.join(self.source, 'source', 'ZE_2012', master_doc(self.app, 'ZE_2012') + ".rst")
            # but we just need to do
            content = json.loads(res.data)
            assert re.compile(r"\.\. figure:: .*"+re.escape(uploadfname)).search(content)
            assert ".. _%s:\n\n" % figlabel in content
            assert figcaption in content
            

            # now we need to call save to move the file
            res = app.post("/ZE_2012/save", data = json.dumps({
                'source_text': 'my rst contents'
            }),content_type='application/json')
            # test response was ok:
            assert res.status_code == 200
            # test we created the dir
            assert not os.path.isdir(uploaddir_tmp)
            assert os.path.isdir(uploaddir)
            # test we have the file:
            assert os.listdir(uploaddir) == [uploadfname]
            with open(os.path.join(uploaddir, uploadfname)) as fopn:
                content = fopn.read()
            assert content == 'my file contents'

            # define a "GOOD" filename ALREADY EXISTING:
            uploadfname = 'bla.png'
            figcaption = 'some weird caption which is not part of the rst klrg;jimovwjeowlhawrclghnsrgq'
            figlabel = 'some weird label not part of the rst vrguhreosvgjqo;acjglsevnghmqalmsvnd'
            res = app.post("/ZE_2012/upload_file", data = {
                'file': (StringIO('my file contents'), uploadfname),
                'label': figlabel, 'caption': figcaption
            })
            # test response was ok:
            assert res.status_code == 200
            # test we created the dir
            assert os.path.isdir(uploaddir_tmp)
            assert os.path.isdir(uploaddir)  # cause we created it few lines above
            # test we have the file:
            assert len(os.listdir(uploaddir_tmp)) == 1 and os.listdir(uploaddir_tmp) != [uploadfname]



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()