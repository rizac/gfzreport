'''
Created on Oct 30, 2017

@author: riccardo
'''
import unittest, pytest
from gfzreport.templates.network.core.utils import sortchannels


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


@pytest.mark.parametrize("test_input, expected", [
    (['HHE', 'HHZ', 'HHN'], ['HHZ', 'HHN', 'HHE']),
    # weird case: test we sort by has of first two digits first (hash('blabl') < hash('HH'))
    (['HHE', 'HHZ', 'HHN', 'blabla'], ['blabla', 'HHZ', 'HHN', 'HHE']),
    # mixed case1: test we sort by hash of first two digits first (hash('VN') > hash('HH'))
    (['HHE', 'HHZ', 'HHN', 'VNT', 'VNR'], ['HHZ', 'HHN', 'HHE', 'VNT', 'VNR']),
    # mixed case2:
    (['HHE', 'HHZ', 'HHN', 'BHE', 'BHZ', 'BHN'], ['BHZ', 'BHN', 'BHE', 'HHZ', 'HHN', 'HHE']),

    ])
def testSortChannels(test_input, expected):
    inplace = [True, False]
    for in_ in inplace:
        # test that works with sets
        scha = sortchannels(set(test_input), inplace)
        assert scha == expected
        # but inplace argument is ignored with sets:
        assert scha is not test_input
        # test that works with lists:
        scha = sortchannels(test_input, inplace=in_)
        assert scha == expected
        # test that inplace works
        if in_:
            assert scha is test_input
        else:
            assert scha is not test_input

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()