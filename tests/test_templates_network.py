'''
Created on Jun 19, 2016

@author: riccardo
'''
import os
import sys
import glob
from click.testing import CliRunner
from gfzreport.templates.network.main import main as network_reportgen_main
from gfzreport.sphinxbuild.main import main as sphinxbuild_main, get_logfilename
import shutil
from contextlib import contextmanager
from obspy.core.inventory.inventory import read_inventory
from mock import patch, Mock
from _io import BytesIO
# from cStringIO import StringIO
from matplotlib.image import imread
from urllib2 import URLError

# global paths defined once
DATADIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "testdata")


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
        if a == '-i' or a == '--inst_uptimes' or a == '-n' or a == '--noise_pdf':
            argz[i+1] = os.path.join(DATADIR, args[i+1])
    runner = CliRunner()

    with runner.isolated_filesystem():
        argz.extend(['-o', os.getcwd()])
        yield runner.invoke(network_reportgen_main, argz, catch_exceptions=False), os.getcwd(), argz


def test_netgen_bad_path():
    # set args:
    args_ = [
        # -i points to a non existing path name, -n too
        ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes-/*", "-n", "noise_pdf/sta1*.pdf"],
        # -i points to a non existing path name, -n is ok
        ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes-/*", "-n", "noise_pdf/sta1*"],
        # -i points to an existing path name, -n no
        ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-n", "noise_pdf/sta1*.pdf"]]
    for args in args_:
        with invoke(*args) as _:
            result, outpath, args = _
            assert "ZE_2014" not in os.listdir(outpath)
            assert "Aborted: No files copied" in result.output
            assert result.exit_code != 0


def _getdatacenters(*a, **v):
    """returns the datacenters as the returned response that the eida routing service
    would give. The returned string is the datacenters.txt file in the testdata folder"""
    with open(os.path.join(DATADIR, "datacenters.txt"), 'rb') as opn:
        ret = opn.read()

    for dc in ret.splitlines():
        if dc[:7] == 'http://':
            yield dc


def setupurlread(mock_urlopen, geofon_retval=None, others_retval=None):
    '''sets up urlopen.urlread mock
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
                with open(os.path.join(DATADIR, "ZE.network.xml")) as opn:
                    return BytesIO(opn.read())
            else:
                return BytesIO(geofon_retval)
        else:
            if isinstance(others_retval, Exception):
                raise others_retval
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
    args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-n", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 0
        assert "ZE_2014" in os.listdir(outpath)
        with open(os.path.join(outpath, "ZE_2014", "report.rst")) as opn:
            rst = opn.read()
        # assert we have the network stations (just few):
        assert 'MS02 -23.34335 43.89449 s #7F0000' in rst 
        assert 'AM01 -21.07725 48.23924 s #3F0000 L4-3D' in rst
        # assert we have the non-network stations:
        # Note that testing if we filtered out some stations baseed on the network boundary box
        # is hard as we should run a real test
        assert 'OUT_RANGE_LON_85 -22.47355 85.0 o #FFFFFF' in rst 
        assert 'IN_RANGE -22.47355 45.56681 o #FFFFFF' in rst 
        assert 'OUT_RANGE_LON_75 -22.47355 75.0 o #FFFFFF' in rst 
        assert 'OUT_RANGE_LON_85 -22.47355 85.0 o #FFFFFF' in rst 
        # assert we do not have margins:
        assert ':map_mapmargins: 0.0deg, 0.0deg, 0.0deg, 0.0deg' in rst
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
        result = runner.invoke(network_reportgen_main, args, catch_exceptions=False)
        assert result.exit_code == 1
        assert " already exists" in result.output


        runner = CliRunner()
        args_ = [os.path.join(outpath, "ZE_2014"),
                 os.path.join(outpath, "build"), "-b", ""]
        for buildtype, expected_ext in [("", '.tex'), ("latex", '.tex'), ("pdf", '.pdf'),
                                        ("html", '.html')]:
            btype = 'latex' if not buildtype else buildtype
            outdir = os.path.join(args_[1], btype)
            indir = os.path.join(outpath, "ZE_2014")
            args_ = [indir, outdir]
            if buildtype:
                args_.extend(['-b', buildtype])
            if buildtype != 'latex':
                # if buildtype is latex, we already executed a build with no build arg
                # which defaults to latex, so the dir exists
                assert not os.path.isdir(outdir)

            result = runner.invoke(sphinxbuild_main, args_, catch_exceptions=False)
            # in any build, sphinx builds anyway something in the dir:
            assert os.path.isdir(outdir)

            if '.html' == expected_ext:
                # html does not use arcgis images, so no error should be raised:
                assert os.path.isfile(os.path.join(outdir, 'report%s' % expected_ext))
                assert result.exit_code == 0
            else:
                # in the other cases no report:
                assert not os.path.isfile(os.path.join(outdir, 'report%s' % expected_ext))
                with open(os.path.join(outdir, get_logfilename())) as fopen:
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
        args_ = [os.path.join(outpath, "ZE_2014"),
                 os.path.join(outpath, "build"), "-b", ""]
        # Set expected ret values as list, although the value is just one, for the cases
        # if we have more than one ret_val possible (some bug when running py.test from the terminal)
        for buildtype, expected_ext, exp_exitcode in [("", '.tex',[0]),
                                                      ("latex", '.tex',[0]),
                                                      ("pdf", '.pdf', [1]),
                                                      ("html", '.html', [0]),
                                                      ]:
            btype = 'latex' if not buildtype else buildtype
            outdir = os.path.join(args_[1], btype)
            indir = os.path.join(outpath, "ZE_2014")
            args_ = [indir, outdir]
            if buildtype:
                args_.extend(['-b', buildtype])
 
            # if buildtype is html, WE CREATED THE FILE. This is an interesting test
            # as sphinx DOES NOT MODIFY THE FILE BUT IS SUCCESSFUL. THEREFORE, ANY WRAPPER WE
            # MIGHT IMPLEMENT THAT RELIES ON THE FILE MODIFIED FOR SUCCESS IS WRONG
            # assert that we do have this particular case
            if buildtype == 'html':
                assert os.path.isfile(os.path.join(outdir, 'report%s' % expected_ext))
            elif buildtype == 'pdf':
                sdf = 9

            result = runner.invoke(sphinxbuild_main, args_, catch_exceptions=False)
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
        
    # check if we deleted the temop dir:
    assert not os.path.isdir(outpath)



@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
@patch('gfzreport.templates.network.core.utils.urllib2.urlopen')
def test_netgen_ok_sphinxbuild_ok(mock_urlopen, mock_get_dcs):
    # set args, with wildcards
    # mock urllib returns our testdata files
    setupurlread(mock_urlopen)
    args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes/ok*", "-n", "noise_pdf/ok*.png"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 0
        assert "ZE_2014" in os.listdir(outpath)
        with open(os.path.join(outpath, "ZE_2014", "report.rst")) as opn:
            rst = opn.read()
        # assert we copied the right files. For noise_pdf, everything except sta2.*
        assert sorted(os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'noise_pdf'))) == ['ok1_HHE.png', 'ok1_HHN.png', 'ok1_HHZ.png']
        # for inst_uptimes, everything (2 files):
        assert sorted(os.listdir(os.path.join(outpath, 'ZE_2014', 'data', 'inst_uptimes'))) == ['ok1.png', 'ok2.jpg']
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

        result = runner.invoke(network_reportgen_main, args, catch_exceptions=False)
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
            
            result = runner.invoke(sphinxbuild_main, args_, catch_exceptions=False)
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
    args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-n", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 1
        assert 'error while fetching network stations' in result.output
        
    # first test some edge cases, e.g. responses are empty:
    setupurlread(mock_urlopen, None, '')
    args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-n", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 1
        # FIXME: we print all errors for all stations, should we? or just an error at the end?
        assert 'error while fetching other stations within network stations boundaries' in result.output

    # responses raise:
    setupurlread(mock_urlopen, Exception('wat?'))
    args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-n", "noise_pdf/sta1*"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 1
        assert 'error while fetching network stations' in result.output

    
    
    # set args,one a directory, the other one file
    # mock urllib returns our testdata files
    setupurlread(mock_urlopen)
    args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes", "-n", "noise_pdf/sta1_HHE.png"]
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
    args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes", "-n", "noise_pdf/sta1_HHE.png",
            "-n", "noise_pdf/sta2*.png"]
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
        args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes/XXX*", "-n", "noise_pdf/xxx*", "--mv"]
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
                                  
        args = ['ZE', '2014', "--noprompt",  "-i", "inst_uptimes/*", "-n", "noise_pdf/sta1*",
                '-a', margins]
        with invoke(*args) as _:
            result, outpath, args = _
            assert result.exit_code == 0
            with open(os.path.join(outpath, "ZE_2014", "report.rst")) as opn:
                rst = opn.read()
            # assert we do not have margins:
            assert expected_rst_val in rst
        