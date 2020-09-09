from __future__ import print_function

from gfzreport.templates.network.core import utils
from itertools import product
# Using multiprocessing shouldn't really be needed for this testing:
from multiprocessing.pool import ThreadPool

import unittest


def fetch_inv(tup):
    querystr = 'unknown url'
    try:
        dc, kwargs = tup
        querystr = utils.get_query(dc, **kwargs)
        return utils.read_stations(querystr, timeout=60), querystr, None
    except Exception as exc:
        print('Trouble with', querystr)
        raise
        return None, querystr, exc


class TestUtils(unittest.TestCase):

    def test1(self):
        self.assertTrue(1)

    def testRelpath(self):
        result = utils.relpath('a', 'b')
        expected = './../a'
        self.assertEqual(expected, result)

    def testIterdcurl1(self):
        '''
        Expect a list of fdsnws-station service endpoint URLs.
        '''
        count = 0
        for item in utils.iterdcurl(starttime='2018-01-01T00:00:00'):
            if item.startswith('http'):
                count += 1
            else:
                print('Unexpected:', item)
        self.assertTrue(count > 10)

    def testIterdcurl2(self):
        '''
        Get some meaningful URLs and query them.
        Must continue past any node returning No Data.
        '''

        # Region should include stations hosted at Orfeus and other DCs,
        # but not all DCs...
        case = 3
        if (case == 1):
            # e.g. [10W .. 20E, 30S .. 60N] has nothing at KOERI
            minlon = -10.0
            minlat = 30.0
            maxlon = 20.0
            maxlat = 60.0

        elif (case == 2):
            # 5M_2015 - fails at Orfeus, *if* endbefore="2015-01-01T00:00:00"
            maxlon = -23.8
            minlon = -61.7
            minlat = -64.1
            maxlat = 15.5

        elif (case == 3):
            # Who would have a station here?
            minlon = -10.0
            minlat = 30.0
            maxlon = -9.0
            maxlat = 31.0

        kwargs_some_stations = dict(minlat=minlat, maxlat=maxlat,
                                    minlon=minlon, maxlon=maxlon,
                                    level='station',
                                    starttime="2018-01-01T00:00:00")

        fetch_args = (args for args in product(utils.iterdcurl(minlon=minlon,
                                                               minlat=minlat,
                                                               maxlon=maxlon,
                                                               maxlat=maxlat),
                                               [kwargs_some_stations, ]))
        results = ThreadPool(5).imap_unordered(fetch_inv, fetch_args)
        # for f in fetch_args:
        #     inv, url, error = fetch_inv(f)
        for inv, url, error in results:
            if error is None:
                print('Good result:', url)
                if inv:
                    print(len(inv), end='')
                    print(': ', ' '.join(i.code for i in inv))
                else:
                    print('Nothing')
            else:
                print('Error fetching inventory (%s)\n   url: %s' % (error, url))


if __name__ == '__main__':
    unittest.main()
