'''
Created on Jun 19, 2016

@author: riccardo
'''
import os
import sys
import glob
from click.testing import CliRunner
from gfzreport.templates.network.main import main as network_reportgen_main
from gfzreport.sphinxbuild.main import run as reportbuild_run
import shutil
from contextlib import contextmanager
from obspy.core.inventory.inventory import read_inventory
from mock import patch
# from cStringIO import StringIO

CURRENT_ERR_MSG = ""


@contextmanager
def invoke(*args):
    '''creates a click runner, invokes with runner.invoke(args)
    and yields the returned result
    The runner is run in an isolated file system dir that will be deleted (rmtree) at the end
    The dir is the output path which does NOT need to be specified in *args. To access the dir, use:
        os.getcwd()
    :param args: any argument passed to network.main.run EXCEPT the -o option
    '''
    sourcedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "testdata")
    argz = list(args)
    for i, a in enumerate(args):
        if a == '-i' or a == '--inst_uptimes' or a == '-n' or a == '--noise_pdf':
            argz[i+1] = os.path.join(sourcedir, args[i+1])
    runner = CliRunner()

    with runner.isolated_filesystem():
        argz.extend(['-o', os.getcwd()])
        yield runner.invoke(network_reportgen_main, argz, catch_exceptions=False), os.getcwd()


def test_netgen_bad_path():
    # set args:
    args_ = [
        # -i points to a non existing path name, -n too
        ['ZE', '2014', "--noprompt",  "-i", "instr_uptimes-/*", "-n", "noise_pdf/sta1*.pdf"],
        # -i points to a non existing path name, -n is ok
        ['ZE', '2014', "--noprompt",  "-i", "instr_uptimes-/*", "-n", "noise_pdf/sta1*"],
        # -i points to an existing path name, -n no
        ['ZE', '2014', "--noprompt",  "-i", "instr_uptimes/*", "-n", "noise_pdf/sta1*.pdf"]]
    for args in args_:
        with invoke(*args) as _:
            result, outpath = _
            assert "ZE_2014" not in os.listdir(outpath)
            assert "Aborted: No files copied" in result.output
            assert result.exit_code != 0


def _getZEnet(*a, **v):
    """returns ZE network as inventory xml. The inventory
    is stored in the testdata folder"""
    return read_inventory(os.path.join(os.path.abspath(os.path.dirname(__file__)), "testdata",
                                       "ZE.network.xml"), format='STATIONXML')


def _getdatacenters(*a, **v):
    """returns the datacenters as the returned response that the eida routing service
    would give. The returned string is the datacenters.txt file in the testdata folder"""
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "testdata",
                                       "datacenters.txt"), 'rb') as opn:
        ret = opn.read()

    for dc in ret.splitlines():
        if dc[:7] == 'http://':
            yield dc


def _get_other_stations(*a, **v):
    """
    """
    return read_inventory(os.path.join(os.path.abspath(os.path.dirname(__file__)), "testdata",
                                       "other_stations.xml"), format='STATIONXML')


@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
@patch('gfzreport.templates.network.core.read_network', side_effect=lambda *a, **v: _getZEnet(*a, **v))
@patch('gfzreport.templates.network.core.read_stations', side_effect=lambda *a, **v: _get_other_stations(*a, **v))
def test_netgen_wildcardpaths(mock_read_sta, mock_read_net, mock_get_dcs):
    # set args, with wildcards
    args = ['ZE', '2014', "--noprompt",  "-i", "instr_uptimes/*", "-n", "noise_pdf/sta1*"]
#             ['??', 2012, "instr_uptimes-/*", "noise_pdf/sta1*.pdf", 1],
#             ['??', 2014, "instr_uptimes/*", "noise_pdf/sta1*.pdf", 1],
#             ['ZE', 2012, "instr_uptimes/*", "noise_pdf/sta1*.pdf", 1],
#             ['ZE', 2012, "instr_uptimes-/*", "noise_pdf/*", 1],
#             ['ZE', 2012, "instr_uptimes/x1.png", "noise_pdf/sta1*.png", 0],

    with invoke(*args) as _:
        result, outpath = _
        assert result.exit_code == 0
        assert "ZE_2014" in os.listdir(outpath)
        with open(os.path.join(outpath, "ZE_2014", "report.rst")) as opn:
            rst = opn.read()
        assert "a" in rst
#         assert "Aborted: No files copied" in result.output
#         assert result.exit_code != 0


@patch('gfzreport.templates.network.core.iterdcurl', side_effect=lambda *a, **v: _getdatacenters(*a, **v))
@patch('gfzreport.templates.network.core.read_network', side_effect='')
@patch('gfzreport.templates.network.core.read_stations', side_effect='')
def test_netgen_empty_responses(mock_read_sta, mock_read_net, mock_get_dcs):
    # set args, with wildcards
    args = ['ZE', '2014', "--noprompt",  "-i", "instr_uptimes/*", "-n", "noise_pdf/sta1*"]
#             ['??', 2012, "instr_uptimes-/*", "noise_pdf/sta1*.pdf", 1],
#             ['??', 2014, "instr_uptimes/*", "noise_pdf/sta1*.pdf", 1],
#             ['ZE', 2012, "instr_uptimes/*", "noise_pdf/sta1*.pdf", 1],
#             ['ZE', 2012, "instr_uptimes-/*", "noise_pdf/*", 1],
#             ['ZE', 2012, "instr_uptimes/x1.png", "noise_pdf/sta1*.png", 0],

    with invoke(*args) as _:
        result, outpath = _
        assert result.exit_code == 0
        assert "ZE_2014" in os.listdir(outpath)
        with open(os.path.join(outpath, "ZE_2014", "report.rst")) as opn:
            rst = opn.read()
        assert "a" in rst
#         assert "Aborted: No files copied" in result.output
#         assert result.exit_code != 0



def tst_rgen(outdir, network, year, inst_uptimes, data_aval, noise_pdf, expected_exit_code,
             cli_runner=None):
    # expected_exit_code: 0 for success, 1 for failure (or something else than zero)

    print "Generating a test report"
    print "outdir '%s'" % outdir
    
    runner = CliRunner() if cli_runner is None else cli_runner
    ddd = os.path.abspath(os.path.dirname(__file__))
    opts = {
            "--inst_uptimes": os.path.join(ddd, inst_uptimes),
            "--data_aval": os.path.join(ddd, data_aval),
            "--noise_pdf": os.path.join(ddd, noise_pdf),
           }

    def_args = [network, str(year)]  # FIXME: with 2014 IS EMPTY! TEST IT!

    args = []
    args.extend(item
                for pair in opts.iteritems()
                for item in pair)

    args.append("--out_path")
    args.append(outdir)
    if os.path.isdir(outdir):
        raise ValueError("'%s' already exist, please delete directory")

    args.extend(def_args)

    global CURRENT_ERR_MSG
    CURRENT_ERR_MSG = str(network_reportgen_run) + " " + str(args)
    result = runner.invoke(network_reportgen_run, args, catch_exceptions=False)

    ext_code = result.exit_code
    print "Expecting exit code %d" % expected_exit_code
    assert ext_code == expected_exit_code

    if ext_code == 0:
        assert os.path.isdir(outdir)
        for opt in opts:
            assert os.path.isdir(os.path.join(outdir, "data", opt[2:]))

        for opt in opts:
            assert filelen(os.path.join(outdir, "data", opt[2:])) == filelen(opts[opt])
    
    CURRENT_ERR_MSG = ""
    print "Generating a test report: Ok"
    return outdir


def filelen(arg):
    if os.path.isfile(arg):
        return 1
    elif os.path.isdir(arg):
        return len(os.listdir(arg))
    else:
        return len(glob.glob(arg))


def tst_rbuild(sourcedir, builddir, expected_exit_status):
    print "Building a test report"
    print "srcdir '%s'" % sourcedir
    print "builddir '%s'" % builddir
    global CURRENT_ERR_MSG
    # builddir = os.path.join(os.path.dirname(sourcedir), os.path.basename(sourcedir)+"_build")
    if os.path.isdir(builddir):
        raise ValueError("'%s' already exists, cannot build in there")
    # os.makedirs(builddir)
    for build in ("html", "latex", "pdf"):
        bdir = os.path.join(builddir, build)
        print "   Building test report for '%s'" % build
        args_ = ["reportbuild", sourcedir, bdir, "-b", build]
        CURRENT_ERR_MSG = str(args_)
        ret = reportbuild_run(args_)
        assert ret == expected_exit_status
        if expected_exit_status == 0:  # success
            assert os.path.isdir(bdir)
            ext = "tex" if build == 'latex' else build
            assert len(glob.glob(os.path.join(bdir, "*.%s" % ext))) > 0
        CURRENT_ERR_MSG = ""
    print "Building a test report: Ok"
    return builddir

if __name__ == '__main__':
    test_all()
