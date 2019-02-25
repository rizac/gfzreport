'''
Created on Jun 19, 2016

@author: riccardo
'''
import os
import sys
import glob
from click.testing import CliRunner
from gfzreport.cli import main as gfzreport_main
from gfzreport.sphinxbuild import get_logfilename as get_build_logfilename
from gfzreport.templates.utils import get_logfilename as get_template_logfilename
# from gfzreport.templates.network.__init__ import main as network_reportgen_main
# from gfzreport.sphinxbuild.__init__ import main as sphinxbuild_main, get_logfilename
import shutil
from contextlib import contextmanager
from obspy.core.inventory.inventory import read_inventory
from mock import patch, Mock
from _io import BytesIO
# from cStringIO import StringIO
from matplotlib.image import imread
from urllib2 import URLError
from shutil import rmtree

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

@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
@patch('gfzreport.templates.network.core.utils.urllib2.urlopen')
def test_netgen_configonly_flag(mock_urlopen, mock_get_dcs):
    # set args, with wildcards
    # mock urllib returns our testdata files
    setupurlread(mock_urlopen)
    # set args:
    args = ['-n', 'ZE', '-s' '2014', "--noprompt",  "-i", "inst_uptimes/*", "-p", "noise_pdf/*"]

    with invoke(*args) as _:
        result, outpath, args = _
        outpath_ = os.path.join(outpath, "ZE_2014")
        conf_files_dir = os.path.join(outpath_, 'conf_files')
        data_dir = os.path.join(outpath_, 'data')
        confiles_subdirs = sorted(os.listdir(conf_files_dir))
        logfile = os.path.join(outpath_, get_template_logfilename())
        assert os.path.isfile(logfile)
        #assert logfile content has something:
        with open(logfile) as opn:
            logcontent = opn.read()
        assert len(logcontent) > 0
        # store modification time 
        logmtime = os.stat(logfile).st_mtime
        shutil.rmtree(conf_files_dir)
        shutil.rmtree(data_dir)
        assert not os.path.isdir(conf_files_dir)
        assert not os.path.isdir(data_dir)

        confile_path = os.path.join(outpath_, 'conf.py') 
        # modify conf.py and assert later that we overwrote it:
        with open(confile_path) as opn_:
            text = "dummyvar='ert'" + opn_.read()
        with open(confile_path, 'w') as opn_:
            opn_.write(text)
        with open(confile_path) as opn_:
            assert "dummyvar='ert'" in opn_.read()

        rstreport_path = os.path.join(outpath_, 'report.rst') 
        # modify conf.py and assert later that we overwrote it:
        with open(rstreport_path) as opn_:
            text = opn_.read() + "\na simple text__"
        with open(rstreport_path, 'w') as opn_:
            opn_.write(text)
        with open(rstreport_path) as opn_:
            assert "\na simple text__" in opn_.read()

        # needs to run it inside the with statement otherwise the dest dir is removed
        runner = CliRunner()
        args += ['-c']
        result = runner.invoke(gfzreport_main, TEMPLATE_NETWORK + args, catch_exceptions=False)
        confiles_subdirs2 = sorted(os.listdir(conf_files_dir))
        # conf_files_dir was deleted, assert it has again the proper subdirs:
        assert confiles_subdirs == confiles_subdirs2
        # confile_path was modified, assert it has been overwritten:
        with open(confile_path) as opn_:
            assert "dummyvar='ert'" not in opn_.read()
        # rstreport_path was modified, assert it was NOT overwritten:
        with open(rstreport_path) as opn_:
            assert "\na simple text__" in opn_.read()
        # data dir has not been newly created in update config mode:
        assert not os.path.isdir(data_dir)
        # assert we did not modify logfile in -c mode:
        assert logmtime == os.stat(logfile).st_mtime

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

@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
@patch('gfzreport.templates.network.core.utils.urllib2.urlopen')
def test_netgen_ok_sphinxbuild_err(mock_urlopen, mock_get_dcs):
    # set args, with wildcards
    # mock urllib returns our testdata files
    setupurlread(mock_urlopen)
    args = ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-p", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 0
        assert "ZE_2014" in os.listdir(outpath)
        with open(os.path.join(outpath, "ZE_2014", "report.rst")) as opn:
            rst = opn.read()
        # assert we have the network stations (just few):
        assert 'MS02 -23.34335 43.89449 s #980000' in rst
        assert 'AM01 -21.07725 48.23924 s #FF0000 L4-3D' in rst
        # assert we have the non-network stations:
        # Note that testing if we filtered out some stations baseed on the network boundary box
        # is hard as we should run a real test
        assert 'OUT_RANGE_LON_85 -22.47355 85.0 o #FFFFFF' in rst
        assert 'IN_RANGE -22.47355 45.56681 o #FFFFFF' in rst
        assert 'OUT_RANGE_LON_75 -22.47355 75.0 o #FFFFFF' in rst
        assert 'OUT_RANGE_LON_85 -22.47355 85.0 o #FFFFFF' in rst
        # assert we do have default margins:
        m = 0.5  # default margin when missing
        assert (':map_mapmargins: %sdeg, %sdeg, %sdeg, %sdeg') % (m, m, m, m) in rst
        # assert we copied the right files. For noise_pdf, everything except sta2.*
        assert all(not 'sta2' in filename for filename in
                   os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'noise_pdf')))
        # for inst_uptimes, everything (2 files):
        assert sorted(os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'inst_uptimes'))) == \
            ['ok1.png', 'ok2.jpg', 'x1.png', 'x2.png']

        # Now try to run sphinx build:

        # NOW, IMPORTANT: for some weird reason when querying for the map (arcgisimage)
        # the urllib called from within arcgisimage is our mock (??!!)
        # Our mock returns inventory objects, so
        # this will cause to return an inventory object instead of an image,
        # so we should get an error from every build EXCEPT FOR html,
        # as html does NOT USE arcgis images!!

        # while the dir is already open, test that we cannot override it:
        runner = CliRunner()
        result = runner.invoke(gfzreport_main, TEMPLATE_NETWORK + args, catch_exceptions=False)
        assert result.exit_code == 1
        assert " already exists" in result.output

        runner = CliRunner()
#         args_ = [os.path.join(outpath, "ZE_2014"),
#                  os.path.join(outpath, "build"), "-b", ""]
        for buildtype, expected_ext in [("", '.tex'), ("latex", '.tex'), ("pdf", '.pdf'),
                                        ("html", '.html')]:

            btype = 'latex' if buildtype != 'html' else buildtype
            outdir = os.path.join(os.path.join(outpath, "build"), btype)

            if buildtype in ('latex', 'pdf'):
                assert os.path.isdir(outdir)
            else:
                assert not os.path.isdir(outdir)

            indir = os.path.join(outpath, "ZE_2014")
            args_ = [indir, outdir]
            if buildtype:
                args_.extend(['-b', buildtype])

            result = runner.invoke(gfzreport_main, BUILD + args_, catch_exceptions=False)

            if '.html' == expected_ext:
                # html does not use arcgis images, so no error should be raised:
                assert os.path.isfile(os.path.join(outdir, 'report%s' % expected_ext))
                assert result.exit_code == 0
            else:
                # in the other cases no report:
                assert not os.path.isfile(os.path.join(outdir, 'report%s' % expected_ext))
                with open(os.path.join(outdir, get_build_logfilename())) as fopen:
                    logcontent = fopen.read()
                assert "ValueError: invalid PNG header" in logcontent
                assert result.exit_code == 2

        # Now re-set our mock library to return an exception (the mock_url
        # is intended to distinguish if 'geofon' is in the url or not, provide
        # an exception for both cases to be sure)
        # Our map module will handle silently the error by returning a map
        # with coastal lines drawn
        setupurlread(mock_urlopen, URLError('wat?'), URLError('wat?'))

        # and re-run:
        runner = CliRunner()
        # Set expected ret values as list, although the value is just one, for the cases
        # if we have more than one ret_val possible (some bug when running py.test from
        # the terminal)
        for buildtype, expected_ext, exp_exitcode in [("", '.tex', [0]),
                                                      ("latex", '.tex', [0]),
                                                      ("pdf", '.pdf', [0]),
                                                      ("html", '.html', [0]),
                                                      ]:
            btype = 'latex' if buildtype != 'html' else buildtype
            outdir = os.path.join(os.path.join(outpath, "build"), btype)

            assert os.path.isdir(outdir)  # we already created it above

            indir = os.path.join(outpath, "ZE_2014")
            args_ = [indir, outdir]
            if buildtype:
                args_.extend(['-b', buildtype])

            result = runner.invoke(gfzreport_main, BUILD + args_, catch_exceptions=False)
            assert os.path.isdir(outdir)
            assert os.path.isfile(os.path.join(outdir, 'report%s' % expected_ext))
            # assert "ValueError: invalid PNG header" in result.output
#             if result.exit_code == 2:
#                 with open(os.path.join(outdir, get_logfilename())) as fopen:
#                     logcontent = fopen.read()
#                 print("\n\n\nWTF")
#                 print(logcontent)
#                 print("\n\nWTF")
            assert result.exit_code in exp_exitcode

            if buildtype == 'pdf':
                # if we are running pdf, test a particular thing:
                # replace ":errorsastext: yes" in gridfigure directive with ":errorsastext: no"
                # what does it means? that for grid figures we create images also on errors
                # (file not found). Now, the current grid figure for the current network and
                # start_after
                # has a lot of stations, thus a lot of pdfs images. Pdflatex breaks
                # and does not create the pdf if there are more than 100 includegraphics errors
                # (the 100 is hard-coded in latex and cannot be changed)
                # Test this case
                reporttext = os.path.join(indir, 'report.rst')
                with open(reporttext, 'r') as opn_:
                    content = opn_.read()
                content = content.replace(":errorsastext: yes", ":errorsastext: no")
                with open(reporttext, 'w') as opn_:
                    opn_.write(content)

                rmtree(outdir)
                result = runner.invoke(gfzreport_main, BUILD + args_, catch_exceptions=False)
                assert result.exit_code == 2
                assert not os.path.isfile(os.path.join(outdir, 'report%s' % expected_ext))

    # check if we deleted the temop dir:
    assert not os.path.isdir(outpath)

@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
@patch('gfzreport.templates.network.core.utils.urllib2.urlopen')
def test_netgen_ok_sphinxbuild_ok(mock_urlopen, mock_get_dcs):
    # set args, with wildcards
    # mock urllib returns our testdata files
    setupurlread(mock_urlopen)
    args = ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes/ok*", "-p",
            "noise_pdf/ok*.png"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 0
        assert "ZE_2014" in os.listdir(outpath)
        with open(os.path.join(outpath, "ZE_2014", "report.rst")) as opn:
            rst = opn.read()
        # assert we copied the right files. For noise_pdf, everything except sta2.*
        assert sorted(os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'noise_pdf'))) \
            == ['ok1_HHE.png', 'ok1_HHN.png', 'ok1_HHZ.png']
        # for inst_uptimes, everything (2 files):
        assert sorted(os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'inst_uptimes'))) \
            == ['ok1.png', 'ok2.jpg']
#         assert "Aborted: No files copied" in result.output
#         assert result.exit_code != 0

        # Now try to run sphinx build:
        # Now re-set our mock library to return an exception (the mock_url
        # is intended to distinguish if 'geofon' is in the url or not, provide
        # an exception for both cases to be sure)
        # Our map module will handle silently the error by returning a map
        # with coastal lines drawn
        setupurlread(mock_urlopen, URLError('wat?'), URLError('wat?'))

        # while the dir is already open, test that we cannot override it:
        runner = CliRunner()

        result = runner.invoke(gfzreport_main, TEMPLATE_NETWORK + args, catch_exceptions=False)
        assert result.exit_code == 1
        assert " already exists" in result.output

        runner = CliRunner()

        #with runner.isolated_filesystem():
        args_ = [os.path.join(outpath, "ZE_2014"),
                 os.path.join(outpath, "build"), "-b", ""]
        for buildtype, expected_ext in {"": '.tex', "latex": '.tex', "pdf": '.pdf',
                                        "html": '.html'}.iteritems():
            btype = 'latex' if not buildtype else buildtype
            outdir = os.path.join(args_[1], btype)
            indir = os.path.join(outpath, "ZE_2014")
            args_ = [indir, outdir]
            if buildtype:
                args_.extend(['-b', buildtype])
            if buildtype != 'latex':
                # if buildtype is latex, we already executed a build with no buyild arg
                # which defaults to latex, so the dir exists
                assert not os.path.isdir(outdir)

            result = runner.invoke(gfzreport_main, BUILD + args_, catch_exceptions=False)
            assert os.path.isdir(outdir)
            assert os.path.isfile(os.path.join(outdir, 'report%s' % expected_ext))

    # check if we deleted the temop dir:
    assert not os.path.isdir(outpath)

@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
@patch('gfzreport.templates.network.core.utils.urllib2.urlopen')
def test_netgen_errors(mock_urlopen, mock_get_dcs):

    # test that help works (without raising)
    args = ["--help"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 0
        assert os.listdir(outpath) == []

    setupurlread(mock_urlopen)
    # first test some edge cases, e.g. responses are empty:
    setupurlread(mock_urlopen, '')
    args = ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-p", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 1
        assert 'error while fetching network stations' in result.output

    # first test some edge cases, e.g. responses are empty:
    setupurlread(mock_urlopen, None, '')
    args = ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-p", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 1
        # FIXME: we print all errors for all stations, should we? or just an error at the end?
        assert 'error while fetching other stations within network stations boundaries' in result.output

    # responses raise:
    setupurlread(mock_urlopen, Exception('wat?'))
    args = ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-p", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 1
        assert 'error while fetching network stations' in result.output

    # set args,one a directory, the other one file
    # mock urllib returns our testdata files
    setupurlread(mock_urlopen)
    args = ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes", "-p", "noise_pdf/sta1_HHE.png"]
    with invoke(*args) as _:
        result, outpath, args = _
        # assert we copied the right files. For noise_pdf, everything except sta2.*
        assert [filename for filename in
                   os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'noise_pdf'))] == ['sta1_HHE.png']
        # for inst_uptimes, everything (2 files):
        assert sorted(os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'inst_uptimes'))) == \
            ['ok1.png', 'ok2.jpg', 'x1.png', 'x2.png']

    # The same as above but with more than one arg:
    setupurlread(mock_urlopen)
    args = ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes", "-p", "noise_pdf/sta1_HHE.png",
            "-p", "noise_pdf/sta2*.png"]
    with invoke(*args) as _:
        result, outpath, args = _
        # assert we copied the right files. For noise_pdf, everything except sta2.*
        assert sorted([filename for filename in
                   os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'noise_pdf'))]) == \
                    ['sta1_HHE.png', 'sta2_HHE.png']
        # for inst_uptimes, everything (2 files):
        assert sorted(os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'inst_uptimes'))) == \
            ['ok1.png', 'ok2.jpg', 'x1.png', 'x2.png']
#         assert "Aborted: No files copied" in result.output
#         assert result.exit_code != 0

    # test the mv option:
    # create two temp files:
    tmpfiles = [os.path.join(DATADIR, "noise_pdf", "xxx.png"),
                os.path.join(DATADIR, "inst_uptimes", "XXX.png")]
    for file_ in tmpfiles:
        open(file_, 'a').close()

    try:
        args = ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes/XXX*", "-p", "noise_pdf/xxx*", "-m"]
        with invoke(*args) as _:
            result, outpath, args = _
            assert not os.path.isfile(os.path.join(DATADIR, "noise_pdf", "xxx.png"))
            assert not os.path.isfile(os.path.join(DATADIR, "inst_uptimes", "xxx.png"))
            assert os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'noise_pdf')) == ['xxx.png']
            assert os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'inst_uptimes')) == ['XXX.png']
    except Exception as exc:
        for file_ in tmpfiles:
            try:
                if os.path.isfile(file_):
                    os.remove(file_)
            except:
                pass
        raise exc

# 
#     setupurlread(mock_urlopen)
#     args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes/xxx*", "-n", "noise_pdf/xxx*"]
#     with invoke(*args) as _:
#         result, outpath, args = _
#         assert result.exit_code == 0

    # now change margins. Expected margins are top, right, bottom, left
    # (see parse_margins in gfzreport.sphinxbuild.core.map.__init__.py):
    # keys of the dict (given margins as command line) are:
    #
#                     "top,left,bottom,right (4 values), "
#                     "top,left_and_right, bottom (3 values), "
#                     "top_and_bottom, left_and_right (2 values), "
#                     "or a single value that will be applied to all directions. "
#   (see main in network package)

    for margins, expected_rst_val in {'0.125': ':map_mapmargins: 0.125deg, 0.125deg, 0.125deg, 0.125deg',
                                  '0.3 0.4 0.1': ':map_mapmargins: 0.3deg, 0.4deg, 0.1deg, 0.4deg',
                                  '0.3 0.4': ':map_mapmargins: 0.3deg, 0.4deg, 0.3deg, 0.4deg'}.iteritems():

        args = ['-n', 'ZE', '-s', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-p", "noise_pdf/sta1*",
                '-a', margins]
        with invoke(*args) as _:
            result, outpath, args = _
            assert result.exit_code == 0
            with open(os.path.join(outpath, "ZE_2014", "report.rst")) as opn:
                rst = opn.read()
            # assert we do not have margins:
            assert expected_rst_val in rst
