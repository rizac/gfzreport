'''
Created on Jun 19, 2016

@author: riccardo
'''
from __future__ import print_function
import os
import sys
import glob
from click.testing import CliRunner
# from gfzreport.templates.network import main as network_reportgen_main
# from gfzreport.sphinxbuild import main as sphinxbuild_main, get_logfilename
from gfzreport.cli import main as gfzreport_main
import shutil
from contextlib import contextmanager
from obspy.core.inventory.inventory import read_inventory
from mock import patch, Mock
from _io import BytesIO
# from cStringIO import StringIO
from matplotlib.image import imread
from urllib2 import URLError
from StringIO import StringIO
import time
from gfzreport.sphinxbuild import get_logfilename

# global paths defined once
DATADIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "testdata")


TEMPLATE_NETWORK = ["template", "n"]
BUILD = ['build']

@contextmanager
def invoke(*args):
    '''creates a click runner,
    converts args to parsed_args (basically, converting all paths argument to be relative to DATADIR)
    invokes with runner.invoke(parsed_args) in an isolated file system (i.e. in a
    tmp directory `current_dir`) that will be deleted (rmtree) at the end
    `current_dir` is where the output is written and does NOT need to be specified in *args.
    Called result the click result object, this function needs to be invoked in a with
    statement:
    ```
    with invoke(*args) as _:
        result, current_dir, parsed_args = _
        ... test your stuff
    ```
    '''
    argz = list(args)
    for i, a in enumerate(args):
        if a == '-i' or a == '--inst_uptimes' or a == '-p' or a == '--noise_pdf':
            argz[i+1] = os.path.join(DATADIR, args[i+1])
    runner = CliRunner()

    with runner.isolated_filesystem():
        argz.extend(['-o', os.getcwd()])
        yield runner.invoke(gfzreport_main, TEMPLATE_NETWORK + argz, catch_exceptions=False), os.getcwd(), argz


def test_netgen_bad_path():
    # set args:
    args_ = [
        # -i points to a non existing path name, -p too
        ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes-/*", "-p", "noise_pdf/sta1*.pdf"],
        # -i points to a non existing path name, -p is ok
        ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes-/*", "-p", "noise_pdf/sta1*"],
        # -i points to an existing path name, -p no
        ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-p", "noise_pdf/sta1*.pdf"]]
    for args in args_:
        with invoke(*args) as _:
            result, outpath, args = _
            assert "ZE_2014" not in os.listdir(outpath)
            assert "ERROR:" in result.output and " empty" in result.output
            assert result.exit_code != 0


def _getdatacenters(*a, **v):
    """returns the datacenters as the returned response that the eida routing service
    would give. The returned string is the datacenters.txt file in the testdata folder"""
    with open(os.path.join(DATADIR, "datacenters.txt"), 'rb') as opn:
        ret = opn.read()

    for dc in ret.splitlines():
        if dc[:7] == 'http://':
            yield dc


def setupurlread(mock_urlopen, geofon_retval=None, others_retval=None, doicit_retval=None):
    '''sets up urlopen.urlread mock
    :param geofon_retval: the string returned from urlopen.read when querying geofon network
    If None, defaults to "ZE.network.xml" content (file defined in testdata dir)
    If Exception, then it will be raised
    :param others_retval: the string returned from urlopen.read when querying NON geofon stations
    within the geofon network boundaries
    If None, defaults to "other_stations.xml" content (file defined in testdata dir)
    If Exception, then it will be raised
     :param doicit_retval: the string returne from urlopen.read when querying for a DOI citation
    defaults is a string formatted as a doi citation according to the input doi url
    If Exception, then it will be raised
    '''
    def sideeffect(url_, timeout=None):
        try:
            url = url_.get_full_url()
        except AttributeError:
            url = url_
        if "geofon" in url:
            if isinstance(geofon_retval, Exception):
                raise geofon_retval  # pylint: disable=raising-bad-type
            if geofon_retval is None:
                with open(os.path.join(DATADIR, "ZE.network.xml")) as opn:
                    return BytesIO(opn.read())
            else:
                return BytesIO(geofon_retval)
        elif 'doi.org' in url:
            if isinstance(doicit_retval, Exception):
                raise doicit_retval  # pylint: disable=raising-bad-type
            if doicit_retval is None:
                return BytesIO("Marc Smith (2002): A Paper. %s" % url.encode('utf8'))
            return BytesIO(doicit_retval)
        else:
            if isinstance(others_retval, Exception):
                raise others_retval  # pylint: disable=raising-bad-type
            if others_retval is None:
                with open(os.path.join(DATADIR, "other_stations.xml")) as opn:
                    return BytesIO(opn.read())
            else:
                return BytesIO(others_retval)
    mock_urlopen.side_effect = sideeffect


def printl(title, buildtype):
    line = "gfzreport.sphinxbuild (build type=%s): %s" % (buildtype, title)
    print("\n\n%s" % ('=' * len(line)))
    print(line)
    print("%s\n" % ('=' * len(line)))

@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
@patch('gfzreport.templates.network.core.utils.urllib2.urlopen')
def test_netgen_ok_sphinxbuild_retval(mock_urlopen, mock_get_dcs):
    # set args, with wildcards
    # mock urllib returns our testdata files
    setupurlread(mock_urlopen)
    args = ['-n', 'ZE', '-s', '2012', "--noprompt",  "-i", "inst_uptimes/*", "-p", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        # Now re-set our mock library to return an exception (the mock_url
        # is intended to distinguish if 'geofon' is in the url or not, provide 
        # an exception for both cases to be sure)
        # Our map module will handle silently the error by returning a map
        # with coastal lines drawn
        setupurlread(mock_urlopen, URLError('wat?'), URLError('wat?'))
        # and re-run:
        runner = CliRunner()

        RSTDIR = os.path.join(outpath, 'ZE_2012')
        # modify the rst with an error, and see the return exit_status:
        with open(os.path.join(RSTDIR, "report.rst"), "r") as _opn:
            rst_text = _opn.read()

        # TRY TO TYPO DIRECTIVE: NO ERROR
        # change a directive to something it does not exist (mock typo)
        _tmp_rst_text = rst_text.replace(".. gridfigure::", ".. bridfigure::")
        assert _tmp_rst_text != rst_text
        # write to file
        with open(os.path.join(RSTDIR, "report.rst"), "w") as _opn:
            _opn.write(_tmp_rst_text)

        # run sphinx and see the output code:
        # with runner.isolated_filesystem():
        btype = 'html'
        printl("Testing rst typo", btype)
        args_ = [RSTDIR,
                 os.path.join(outpath, "build"), "-b", btype]

        result = runner.invoke(gfzreport_main, BUILD + args_, catch_exceptions=False)
        with open(os.path.join(args_[1], get_logfilename()), "r") as _opn:
            _log_out = _opn.read()

        # SPHINX IS OK WITH UNKNOWN DIRECTIVE TYPES, SHIT!
        assert 'Unknown directive type "bridfigure"' in _log_out
        assert result.exit_code == 1
        print(result.output)


        # TRY TO MISALIGN A INDENTATION
        # change a directive to something it does not exist (mock typo)
        _tmp_rst_text = rst_text.replace(" :align: center", "\n:align: center")
        assert _tmp_rst_text != rst_text
        # write to file
        with open(os.path.join(RSTDIR, "report.rst"), "w") as _opn:
            _opn.write(_tmp_rst_text)
        # run sphinx and see the output code:
        # with runner.isolated_filesystem():
        btype = 'html'
        printl("Testing mis-alignement of :align:", btype)
        args_ = [RSTDIR,
                 os.path.join(outpath, "build"), "-b", btype]
        result = runner.invoke(gfzreport_main, BUILD + args_, catch_exceptions=False)
        with open(os.path.join(args_[1], get_logfilename()), "r") as _opn:
            _log_out = _opn.read()
        assert result.exit_code == 2
        assert 'Exception occurred:' in _log_out
        print(result.output)

        
    # check if we deleted the temop dir:
    assert not os.path.isdir(outpath)
    
    
@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
@patch('gfzreport.templates.network.core.utils.urllib2.urlopen')
def test_netgen_ok_sphinxbuild_output(mock_urlopen, mock_get_dcs):
    # set args, with wildcards
    # mock urllib returns our testdata files
    setupurlread(mock_urlopen)
    args = ['-n', 'ZE', '-s', '2012', "--noprompt",  "-i", "inst_uptimes/*", "-p", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        # Now re-set our mock library to return an exception (the mock_url
        # is intended to distinguish if 'geofon' is in the url or not, provide 
        # an exception for both cases to be sure)
        # Our map module will handle silently the error by returning a map
        # with coastal lines drawn
        setupurlread(mock_urlopen, URLError('wat?'), URLError('wat?'))
        # and re-run:
        runner = CliRunner()

        RSTDIR = os.path.join(outpath, 'ZE_2012')

        btype = 'html'
        printl("Testing normal build with no rst syntax errors", btype)
        args_ = [RSTDIR,
                 os.path.join(outpath, "build"), "-b", btype]
        result = runner.invoke(gfzreport_main, BUILD + args_)
        assert result.exit_code == 0
        print(result.output)

        btype = 'pdf'
        printl("Testing normal build with no rst syntax errors", btype)
        args_ = [RSTDIR,
                 os.path.join(outpath, "build"), "-b", btype]
        result = runner.invoke(gfzreport_main, BUILD + args_)
        assert result.exit_code == 0
        print(result.output)

        