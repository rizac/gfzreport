import os
import shutil
import re
from reportgen.run import run as reportgen_run
from datetime import datetime
from networks.core import filesync
import json

def get_config():
    with open(os.path.join(os.path.dirname(__file__), "config.json")) as opn:
        return json.load(opn)


class RootManager(object):
    _str_format = "{network}__{version:03d}"  # "{version:003d}".format(network='abc', version=5)
    _re_format = re.compile("^(.*)__(\\d\\d\\d)$")

    def __init__(self, path):
        self.rootpath = os.path.abspath(path)

    def format(self, network, version):
        return RootManager._str_format.format(network=network, version=version)

    def get_path(self, network, version=None):
        return os.path.join(self.rootpath, network) if version is None else \
            os.path.join(self.rootpath, RootManager.format(network=network, version=version))

    def build_managerk(self, network, on_exist='raise'):
        """on_exists=raise: raise error. 'append':append version"""
        path = self.get_path(network)
        if on_exist == 'append':
            ver = 0
            while os.path.exists(path):
                ver += 1
                path = self.get_path(network, ver)
        elif os.path.exists(path):
            raise ValueError("newtork directory ('%s') already exists" % network)

        return BuildManager(path)


class BuildManager(object):

    def __init__(self, path, versioning_enabled_for=[], mkdirs=True):
        self.path = path

        # storing relevant subdirs in custom attributes:
        # first declare two private paths (source and build):
        sdir = os.path.join(self.path, "source")
        bdir = os.path.join(self.path, "build")
        # then create attrs:
        self.config_dir = os.path.join(self.path, "config")
        self.source_dir = sdir
        self.sourcedata_dir = os.path.join(sdir, "data")
        self.html_dir = os.path.join(bdir, "html")
        self.latex_dir = os.path.join(bdir, "latex")
        self.pdf_dir = os.path.join(bdir, "pdf")
        self.version_dir = os.path.join(self.path, "version")

        self.versioning_enabled_for = versioning_enabled_for

        if mkdirs:
            self.makedirs()

    def get_run_args(self, build_option):
        """Returns the arguments used by reportgen to run the specific build according to build_option
        You can call reportgen.run(*get_run_args[build_option])
        :param build_option: either "latex", "html" or "pdf"
        """
        # from http://www.sphinx-doc.org/en/stable/man/sphinx-build.html#options:
        # -a    Generate output for all files; without this option only output for new and changed
        # files is generated.
        # -E    Ignore cached files, forces to re-read all source files from disk.
        ret_list = [self.source_dir, self.get_build_dir(build_option), "-E", "-b", build_option,
                    "-c", self.config_dir]
        if build_option in ("latex", "pdf"):
            ret_list.append("-a")
        return ret_list

    def get_build_dir(self, build_option):
        if build_option == "html":
            return self.html_dir
        elif build_option == "pdf":
            return self.pdf_dir
        elif build_option == "latex":
            return self.latex_dir
        else:
            raise ValueError("Unknown build option (-b): '%s'" % build_option)

    def run(self, build_option):
        build_dir = self.get_build_dir(build_option)
        opts = self.get_run_args(build_option)
        if build_option in self.versioning_enabled_for:
            old_files = filesync.freeze(build_dir)
        ret = reportgen_run(opts)
        if ret == 0 and build_option in self.versioning_enabled_for and old_files:
            new_files = filesync.get_new_files(build_dir, old_files)
            outdir = self.get_next_versioned_dir(build_option, mkdirs=True)
            for fle in new_files:
                outfile = os.path.join(outdir,
                                       os.path.relpath(fle, build_dir))
                outfile_dir = os.path.dirname(outfile)
                if not os.path.isdir(outfile_dir):
                    os.makedirs(outfile_dir)
                shutil.copy2(fle, outfile)
        if ret == 0 and build_option == 'pdf':
            latex_dir = self.get_build_dir("latex")
            for file_ in latex_dir:
                if os.path.splitext(file_)[1] == '.pdf':
                    newfile = os.path.join(build_dir, file_)
                    if os.path.isfile(newfile):
                        os.remove(newfile)
                    os.rename(os.path.join(latex_dir, file_), newfile)
        return ret

    def get_next_versioned_dir(self, build_option, mkdirs=True):
        bdir = self.get_build_dir(build_option)
        outdir = os.path.join(self.version_dir, os.path.basename(bdir))
        versions = []
        re_ = re.compile("^\\d\\d\\d\\d\\d$")
        if os.path.isdir(outdir):
            for fle in os.listdir(outdir):
                if re_.match(file) and os.path.isdir(os.path.join(outdir, file)):
                    versions.append(int(fle))
        dirname = "00000" if not versions else "{0:05d}".format(max(versions) + 1)
        path = os.path.join(outdir, dirname)
        if mkdirs:
            os.makedirs(path)
        return path

    def makedirs(self):
        # path MUST NOT exist !!!!!!
        try:
            # copy config dir.This will create also the existing directory
            # the destination directory must NOT already exist
            shutil.copytree(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../config"),
                            self.config_dir)
            os.makedirs(self.source_data_dir)  # creates also self.source_dir
            os.makedirs(self.html_dir)
            os.makedirs(self.latex_dir)
            os.makedirs(self.pdf_dir)
            os.makedirs(self.version_dir)
        except (IOError, OSError, os.error) as ioerr:
            # IOError is a superclass of OSError, and os.error is an alias of OSEeeor.
            # but let's stay safe...
            raise OSError("Error creating network '%s' tree: %s" % (self.network, str(ioerr)))
