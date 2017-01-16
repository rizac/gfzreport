'''
Created on Jan 15, 2017

@author: riccardo
'''
import unittest
import pytest
from reportbuild.map import parse_margins
import numpy as np

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass

@pytest.mark.parametrize("test_input, parsefunc, expected", [
("3", None, [3,3,3,3]),
("2, 4", None, [2, 4, 2, 4]),
("6, 2, -1", None, [6, 2, -1, 2]),
("6, 2, -1, 3.57", None, [6, 2, -1, 3.57]),
([3], None, [3,3,3,3]),
([2, 4], None, [2, 4, 2, 4]),
([6, 2, -1], None, [6, 2, -1, 2]),
([6, 2, -1, 3.57], None, [6, 2, -1, 3.57]),
])
def testParseMargins(test_input, parsefunc, expected):
    if isinstance(expected, Exception):
        with pytest.raises(expected):
            parse_margins(test_input, parsefunc)
    else:
        result = parse_margins(test_input, parsefunc) if parsefunc else parse_margins(test_input)
        assert np.array_equal(result, expected)
    pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testParseMargins']
    unittest.main()