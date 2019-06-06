'''
Created on Jun 19, 2016

@author: riccardo
'''
import os
import sys
import pytest
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
from gfzreport.templates.annual.core.utils import get_stationsmap_directive_content

# global paths defined once
DATADIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "testdata")

TEMPLATE_ANNUAL = ["template", "a"]
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
        if a == '-i' or a == '--input-dir':
            argz[i+1] = os.path.join(DATADIR, args[i+1])
    runner = CliRunner()

    with runner.isolated_filesystem():
        argz.extend(['-o', os.getcwd()])
        yield runner.invoke(gfzreport_main, TEMPLATE_ANNUAL + argz, catch_exceptions=False), os.getcwd(), argz


#@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
#@patch('gfzreport.templates.network.core.utils.urllib2.urlopen')
def test_netgen_ok_sphinxbuild_ok(): # mock_urlopen, mock_get_dcs):
    # set args, with wildcards
    # mock urllib returns our testdata files

    args = ['-y', '2016', '--input-dir', 'annual', "--noprompt"]
    with invoke(*args) as _:
        result, outpath, args = _
        assert result.exit_code == 0
        assert "2016" in os.listdir(outpath)
        datapath = os.path.join(outpath, '2016', 'data')
        filenames = ['archive_1.png', 'archive_2.png', 'archive_3.png',
                     'eqinfo_1.jpg', 'eqinfo_2.png',
                     'eqinfo_3.png', 'eqinfo_4.png', 'eqinfo_5.png']
        assert sorted(os.listdir(datapath)) == \
            sorted(filenames + ['PDF'])
        with open(os.path.join(outpath, "2016", "report.rst")) as opn:
            rst = opn.read()
        # assert figure files are copied:
        assert all(".. figure:: ./data/%s" % k in rst for k in filenames)
        assert rst.find('.. mapfigure::') > -1
        assert rst.find('.. gridfigure::') > rst.find('.. mapfigure::')
#         assert "Aborted: No files copied" in result.output
#         assert result.exit_code != 0

#         # Now try to run sphinx build:
#         # Now re-set our mock library to return an exception (the mock_url
#         # is intended to distinguish if 'geofon' is in the url or not, provide
#         # an exception for both cases to be sure)
#         # Our map module will handle silently the error by returning a map
#         # with coastal lines drawn
#         setupurlread(mock_urlopen, URLError('wat?'), URLError('wat?'))
# 
#         # while the dir is already open, test that we cannot override it:
#         runner = CliRunner()
# 
#         result = runner.invoke(gfzreport_main, TEMPLATE_NETWORK + args, catch_exceptions=False)
#         assert result.exit_code == 1
#         assert " already exists" in result.output
# 
#         runner = CliRunner()
# 
#         #with runner.isolated_filesystem():
#         args_ = [os.path.join(outpath, "ZE_2014"),
#                  os.path.join(outpath, "build"), "-b", ""]
#         for buildtype, expected_ext in {"": '.tex', "latex": '.tex', "pdf": '.pdf',
#                                         "html": '.html'}.iteritems():
#             btype = 'latex' if not buildtype else buildtype
#             outdir = os.path.join(args_[1], btype)
#             indir = os.path.join(outpath, "ZE_2014")
#             args_ = [indir, outdir]
#             if buildtype:
#                 args_.extend(['-b', buildtype])
#             if buildtype != 'latex':
#                 # if buildtype is latex, we already executed a build with no buyild arg
#                 # which defaults to latex, so the dir exists
#                 assert not os.path.isdir(outdir)
# 
#             result = runner.invoke(gfzreport_main, BUILD + args_, catch_exceptions=False)
#             assert os.path.isdir(outdir)
#             assert os.path.isfile(os.path.join(outdir, 'report%s' % expected_ext))
# 
#     # check if we deleted the temop dir:
#     assert not os.path.isdir(outpath)

def test_generate_csv():
    file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        "testdata",
                                        "AH_GEavailability_2018_err.csv"))
    with pytest.raises(Exception) as exc:
        get_stationsmap_directive_content(file)

    file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        "testdata",
                                        "AH_GEavailability_2018.csv"))
    with pytest.raises(Exception) as exc:
        get_stationsmap_directive_content(file)
        
    file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        "testdata",
                                        "AH_GEavailability_2017.csv"))
    get_stationsmap_directive_content(file)
    
    file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        "testdata",
                                        "AH_GEavailability_2017xrizac.csv"))
    get_stationsmap_directive_content(file)
    
    file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        "testdata",
                                        "AH_GEavailability_2018xrizac.csv"))
    get_stationsmap_directive_content(file)
        