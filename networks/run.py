#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on May 18, 2016
@author: riccardo
'''

# we do want: an initial rst. A config file. We pass it to the build function by copying the system
# argv
# from __future__ import print_function
import sys
import re
import os
# import reportgen.preparser as pp
import subprocess
from sphinx import build_main as sphinx_build_main
from reportgen.core.utils import ensurefiler
from reportgen import run as run_general_report
import argparse
import pandas as pd
from reportgen.run import run as reportgen_run


def run(network, noise_pdf_folder, instr_uptimes_file_path, data_availability_file_path):
    networks_df = get_stations(network)
    dscan = DirScanner(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/{0}")
    outpath = 
    
    # os.chdir(cwd)
    return res




def get_stations(network, datacenter="?"):
    # returns a pandas dataframe
    return pd.DataFrame()


def main():
    """ --noise-pdfs --instr-uptimes --data-aval
    preprocess_stations
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--noise-pdf', default='')
    parser.add_argument('--instr-uptimes', default='')
    parser.add_argument('--data-aval', default='')
    nsp = parser.parse_known_args(sys.argv[1:])
    args = vars(nsp)
    sys.exit(reportgen_run(sys.argv))

if __name__ == '__main__':
    main()
