'''
Created on Jan 9, 2017

@author: riccardo
'''
from __future__ import print_function

import urllib2
import os
import re
from obspy import read_inventory
from io import BytesIO
from collections import OrderedDict
import csv

import numpy as np
import pandas as pd


def relpath(path, reference_path):
    """Almost the same as os.path.relpath but prepends a "./", so the returned value is
        usable in .rst relative paths"""
    return os.path.join(".", os.path.relpath(path, reference_path))


img_extensions = set(['jpg', 'png', 'jpeg', 'gif'])

expected_img_files = {'archive_1': 'Data archived by year of acquisition',
                      'archive_2': 'Cumulative size of the GEOFON archive',
                      'archive_3': 'Number of distinct user IDs provided for fdsnws and/or arclink on each day',
                      'eqinfo_1': 'Geographic distribution of the published events',
                      'eqinfo_2': 'Geographic distribution of the published Moment Tensors solutions',
                      'eqinfo_3': 'Event publication (grey dots) and alert delay (big green and xxl red) vs. magnitude',
                      'eqinfo_4': 'GEOFON alert delay vs. first automatic publication',
                      'eqinfo_5': 'Daily distinct visitors to geofon.gfz-potsdam.de'}


def get_img_filepaths(srcfolder):
    """Returns the files supposed to display the figures for the annual report
        (excluding pdfs figures).

        Raises Exception if some file is not found
    """
    existing_files = set(_ for _ in os.listdir(srcfolder)
                         if os.path.isfile(os.path.join(srcfolder, _)))
    files = []
    for fle in expected_img_files:
        fles = set("%s.%s" % (fle, ext) for ext in img_extensions)
        exist_files = existing_files & fles
        if not exist_files:
            raise Exception(('Image file "%s" '
                             'not found in "%s" (allowed formats: '
                             '%s)') % (fle, srcfolder,
                                       str(list(img_extensions))))
        else:
            fpath = list(exist_files)[0]
            if len(exist_files) > 1:
                print(("Conflict: found %s, '%s' only will be "
                       "displayed (random choice)") % (str(list(exist_files)),
                                                       fpath))

        fpath = os.path.join(srcfolder, fpath)
        files.append(fpath)

    return files


def get_pdfs_directive_content(img_filepaths, unique_network_station=True,
                               delimiter=" ", quotechar='"'):
    """Returns a list of lists of all pdfs found in srcfolder. File names
    must be image files with the format N.S.L.C.<whavever>.ext, where
    ext must be an image extension

    :param unique_network_station: if True (the default), only unique
        rows (based on the network and station) will be shown. Which is the
        location choosen to be shown (e.g. N.S.L1.* or N.S.L2.* ?),
        it depends on what comes first alphabetically. If False, everything
        will be shown
    """
    img_filepaths = sorted(img_filepaths)
    colnum = 3
    grid = []
    netstadone = set()
    for fle in img_filepaths:
        fname = os.path.basename(fle)
        if unique_network_station:
            netsta = '.'.join(fname.split('.')[:2])
            if netsta in netstadone:
                continue
        if not grid or (all(r for r in grid[-1])):  # last row full or grid empty
            row = ['', '', '']
            grid.append(row)
        if not row[0]:
            row[0] = fname
        elif not row[1]:
            row[1] = fname
        else:
            row[2] = fname
            if unique_network_station:
                netstadone.add(netsta)

    ret_df = pd.DataFrame(columns=list(xrange(colnum)), data=grid)
    return ret_df.to_csv(None, sep=delimiter, header=False, index=False,
                         na_rep='', encoding='utf-8', quotechar=quotechar,
                         line_terminator='\n', quoting=csv.QUOTE_MINIMAL)


def get_pdfs_files(srcfolder, do_check=True, extensions=img_extensions):
    for fle in os.listdir(srcfolder):
        fpath = os.path.join(srcfolder, fle)
        if os.path.isfile(fpath):
            if do_check:
                fname, ext = os.path.splitext(fle)
                if ext[1:] not in extensions:
                    print('Discarding "%s" in "%s": no image extension' % (fle, srcfolder))
                    continue
                nslc = fname.split('.')
                if (nslc) < 4 or len(nslc[-1]) != 3:
                    print('Discarding "%s" in "%s": name not in '
                          '<net>.<sta>.<loc>.<cha>.* format' % (fle, srcfolder))
                    continue
            yield fpath


csv_map_columns = ('Station', 'Latitude', 'Longitude', 'Availability',
                   'Maintenance', 'Hardware Shipment', 'Metadata Update')

directive_map_columns = ('Station', 'Latitude', 'Longitude', 'Marker', 'Color', 'Label')


def _read_csv(csvfile, separator):
    try:
        dfr = pd.read_csv(csvfile, sep=separator)
    except Exception as exc:
        raise Exception(('Malformed csv file "%s". Please check that the '
                         'file exists and in case read the '
                         'documentation in order to provide a valid '
                         'file') % os.path.basename(csvfile))

    # try to see if we have the correct columns:
    # "titlelize" the columns ('station' => 'Station', and so on):
    dfr.columns = map(str.title, dfr.columns)
    if len(set(csv_map_columns) & set(dfr.columns)) < len(csv_map_columns):
        raise Exception(('csv file "%s" must contain at least the columns '
                         '(case insensitive): %s') %
                        (os.path.basename(csvfile), str(csv_map_columns)))
    
    return dfr


def get_stationsmap_directive_content(csvfile, separator=None):
    try:
        dfr = _read_csv(csvfile, ',')
    except:
        dfr = _read_csv(csvfile, ';')

    # convert latitude and longitude to floats:
    for col in csv_map_columns[1:4]:   # ['Latitude', 'Longitude', 'Availability']:
        dfcol = pd.to_numeric(dfr[col], errors='coerce')
        nulls = pd.isnull(dfcol)
        if nulls.any():
            # try to parse commas as periods, and take the result with less NaNs:
            dfcol2 = pd.to_numeric(dfr[col].str.replace(',', '.', n=1), errors='coerce')
            nulls2 = pd.isnull(dfcol2)
            if nulls2.sum() < nulls.sum():
                nulls = nulls2
                dfcol = dfcol2
        if nulls.sum() == len(col):
            raise Exception('Csv column "%s" not numeric (float)' % col)
        elif nulls.any():
            if col == csv_map_columns[3]:  # 'Availability':
                dfcol[nulls] = 0
            else:
                raise Exception('Csv column "%s" not entirely numeric (float)' % col)
        dfr[col] = dfcol

    # From the report:
    # Symbols represent the level of corrective maintenance needed:
    # circle for "none",
    # square for "on site",
    # triangle (up) for "remote",
    # triangle (down) for "Remote incl. HW shipment"
    marker_col, maint_col, hard_ship_col = \
        directive_map_columns[3], csv_map_columns[4], csv_map_columns[5]
    dfr[marker_col] = 'o'
    dfr.loc[dfr[maint_col].str.lower() == 'os', marker_col] = 's'  # pylint: disable=no-member
    dfr.loc[dfr[maint_col].str.lower() == 'rs', marker_col] = '^'  # pylint: disable=no-member
    dfr.loc[(dfr[maint_col].str.lower() == 'rs')  # pylint: disable=no-member
            & ~pd.isnull(dfr[hard_ship_col]),  # pylint: disable=no-member
            marker_col] = 'v'

    aval_col, color_col = csv_map_columns[3], directive_map_columns[4]
    colors = []
    for val in mapvalue(dfr[aval_col], 0, 100, 0, 255, 'exp'):
        val = int(0.5 + val)  # convert to python as hex(numpy number) returns a trailing 'L'
        # red = hex(val)[2:].upper().zfill(2)
        greenblue = hex(255-val)[2:].upper().zfill(2)
        colors.append('#FF%s%s' % (greenblue, greenblue))
    dfr[color_col] = colors

    label_col, metadata_u_col = directive_map_columns[5], csv_map_columns[6]
    dfr[label_col] = dfr[metadata_u_col].copy()
    dfr.loc[pd.isnull(dfr[label_col]), label_col] = ''  # pylint: disable=no-member

    return dfr[list(directive_map_columns)].\
        to_csv(None, sep=' ', header=True, index=False,
               na_rep='', encoding='utf-8', quotechar='"',
               line_terminator='\n', quoting=csv.QUOTE_MINIMAL)


def mapvalue(x, xmin, xmax, ymin, ymax, scale=None):
    '''maps x in [xmin, xmax] into the relative value in [ymin, ymax]
       logarithmically if scale = 'log', exponentially if scale = 'exp', or
       linearly otherwise

       'log' basically means: more definition for values closer to `xmin` than 'xmax'
       'exp' basically means: more definition for values closer to `xmax` than 'xmin'
    '''
    if scale == 'log':
        # map values to 1 and 10, take the log:
        x = np.log10(mapvalue(x, xmin, xmax, 1, 10, None))
        xmin, xmax = 0, 1
    elif scale == 'exp':
        x = np.power(10, mapvalue(x, xmin, xmax, 0, 1, None))
        xmin, xmax = 1, 10

    return ymin + (ymax - ymin) * np.true_divide(x - xmin, xmax - xmin)
