'''
Created on Jan 9, 2017

@author: riccardo
'''
from __future__ import print_function

import pandas as pd
import urllib2
import os
import re
from obspy import read_inventory
from io import BytesIO
from collections import OrderedDict
import csv

def relpath(path, reference_path):
    """Almost the same as os.path.relpath but prepends a "./", so the returned value is
        usable in .rst relative paths"""
    return os.path.join(".", os.path.relpath(path, reference_path))


img_extensions = ('jpg', 'png', 'jpeg', 'gif')

expected_img_files = ('archive_1', 'archive_2', 'eqinfo_1', 'eqinfo_2',
                      'eqinfo_3', 'eqinfo_4', 'eqinfo_5', 'network_1')

def get_img_filepaths(srcfolder):
    """Returns the files supposed to display the figures for the annual report
        (excluding pdfs figures).

        Raises Exception if some file is not found
    """
    files = []
    for fle in expected_img_files:
        msg = 'Image file "%s" not found in "%s"' % (fle, srcfolder)
        for ext in img_extensions:
            fpath = os.path.join(srcfolder, "%s.%s" % (fle, ext))
            if os.path.isfile(fpath):
                files.append(fpath)
                break
            elif os.path.splitext(fle)[0] == fle:  # file found, bad extension
                msg = 'File "%s" in "%d" should have extension in %s' % str(img_extensions)
        else:
            raise Exception(msg)
    return files


def get_pdfs_csvstr(img_filepaths, delimiter=" ", quotechar='"'):
    """Returns a list of lists of all pdfs found in srcfolder. File names
    must be image files with the format N.S.L.C.<whavever>.ext, where
    ext must be an image extension

    """
    def _getkey(fname):
        nslc = fle.split('.')
        return nslc[:3] + nslc[3][:-1] + nslc[4:]

    # whatever is ok, the important is that is a 3-length string list:
    chacol_orders = ['a', 'b', 'c']
    filez = []
    index = OrderedDict()
    for fle in img_filepaths:
        index[_getkey(os.path.basename(fle))] = None

    ret_df = pd.DataFrame(columns=list(chacol_orders), index=list(index))
    for fpath in img_filepaths:
        fname = os.path.basename(fpath)
        key = _getkey(fname)
        vals = [_ for _ in ret_df.loc[key, :] if not pd.isnull(_)]
        if len(vals) == 3:
            print('Discarding "%s" in "%s": all orientation codes already found' %
                  (fname, os.path.dirname(fpath)))
            continue
        vals.append(fname)
        vals.sort()
        vals += [''] * max(0, len(chacol_orders) - len(vals))
        ret_df.loc[key, :] = vals

    return ret_df.to_csv(None, sep=delimiter, header=False, index=False,
                         na_rep='', encoding='utf-8', quotechar=quotechar,
                         line_terminator='\n', quoting=csv.QUOTE_MINIMAL)


def get_pdfs_df_old(img_files, delimiter=" ", quotechar='"'):
    """Returns a list of lists of all pdfs found in srcfolder. File names
    must be image files with the format N.S.L.C.<whavever>.ext, where
    ext must be an image extension

    """
    chacol_orders = OrderedDict()
    filez = []
    index = OrderedDict()
    for fle in img_files:
        nslc = fle.split('.')
        net, sta, loc, cha = nslc[0], nslc[1], nslc[2], nslc[3]
        chacol_orders[cha.lower()] = None
        filez.append(fle)
        index[("%s.%s.%s" % (net, sta, loc)).lower()] = None

    ret_df = pd.DataFrame(columns=list(chacol_orders), index=list(index))
    for fname in filez:
        nslc = fname.split('.')
        key = ("%s.%s.%s" % (net, sta, loc)).lower()
        cha = nslc[3].lower()
        if not pd.isnull(ret_df.loc[key, cha]):
            print('Discarding "%s" in "%s": duplicate name found (case insensitive)')
        else:
            ret_df.loc[key, cha] = fname

    for col in ret_df.columns:
        nulls = pd.isnull(ret_df[col])
        if not nulls.any():
            continue
        indices = ret_df[nulls]['index']
        ret_df.loc[indices, col] = ''

    return filez, ret_df.to_csv(None, sep=delimiter, header=False, index=False,
                                na_rep='', encoding='utf-8', quotechar=quotechar,
                                line_terminator='\n', quoting=csv.QUOTE_MINIMAL)


def get_pdfs_files(srcfolder, do_check=True, extensions=img_extensions):
    for fle in os.listdir(srcfolder):
        fpath = os.path.join(dir, fle)
        if os.path.isfile(fpath):
            if do_check:
                fname, ext = os.path.splitext(fle)
                if ext not in extensions:
                    print('Discarding "%s" in "%s": no image extension' % (fle, srcfolder))
                    continue
                nslc = fname.split('.')
                if (nslc) < 4 or len(nslc[-1]) != 3:
                    print('Discarding "%s" in "%s": name not in '
                          '<net>.<sta>.<loc>.<cha>.* format' % (fle, srcfolder))
                    continue
            yield fpath