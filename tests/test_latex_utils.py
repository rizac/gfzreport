'''
Created on Nov 9, 2017

@author: riccardo
'''
import unittest
from gfzreport.sphinxbuild.core.writers.latexutils import parse_authors


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testName(self):
        pass


def test_parse_authors():
    a1, a2, a3 = parse_authors("author1, author2")
    assert a1 == "author1, author2" and a2 == "author1, author2" and not a3

    a1, a2, a3 = parse_authors("author1      , author2     ")
    assert a1 == "author1, author2" and a2 == "author1, author2" and not a3

    a1, a2, a3 = parse_authors("author1      , author2*     ")
    assert a1 == "author1, author2" and a2 == "author1, author2$^{*}$" and a3 == "$^{*}$ corresponding authors"

    a1, a2, a3 = parse_authors("author1*      , author2*     ")
    assert a1 == "author1, author2" and a2 == "author1$^{*}$, author2$^{*}$" and a3 == "$^{*}$ corresponding authors"

    a1, a2, a3 = parse_authors("author1*   *   ,, author2*     ")
    assert a1 == "author1*, author2" and a2 == "author1*$^{*}$, author2$^{*}$" and a3 == "$^{*}$ corresponding authors"

    a1, a2, a3 = parse_authors("author1     (org1   )  ,, author2 ")
    assert a1 == "author1, author2" and a2 == "author1$^1$, author2" and a3 == "$^1$ org1"
    
    a1, a2, a3 = parse_authors("author1     (org1   ),,author2(org2) ")
    assert a1 == "author1, author2" and a2 == "author1$^1$, author2$^2$" and \
        a3 == "$^1$ org1 \\\\[\\baselineskip] $^2$ org2"  # note that we need to escape \\ so it becomes \\\\

    a1, a2, a3 = parse_authors("     author1     (  org1   )   ,, author2 (   org1) ")
    assert a1 == "author1, author2" and a2 == "author1$^1$, author2$^1$" and \
        a3 == """$^1$ org1"""

    # unclosed bracket closes it automatically, the result is weird but check anyway:
    a1, a2, a3 = parse_authors("author1     (org1      ,, author2(org1 ")
    assert a1 == "author1" and a2 == "author1$^1$" and \
        a3 == """$^1$ org1      ,, author2(org1"""

    # now check a complete case:
    a1, a2, a3 = parse_authors("Tom Smith (Institute of Physics), Angel OOh* (Institute of Mathematics), Ay Yan (Institute of Physics)")
    assert a1 == "Tom Smith, Angel OOh, Ay Yan"
    assert a2 == "Tom Smith$^1$, Angel OOh$^{2*}$, Ay Yan$^1$"
    assert a3 == "$^1$ Institute of Physics \\\\[\\baselineskip] $^2$ Institute of Mathematics \\\\[\\baselineskip] $^{*}$ corresponding authors" 

    # another common case:
    a1, a2, a3 = parse_authors("Tom Smith * (Institute of Physics), Angel OOh* (Institute of Mathematics), Ay Yan (Institute of Physics)")
    assert a1 == "Tom Smith, Angel OOh, Ay Yan"
    assert a2 == "Tom Smith$^{1*}$, Angel OOh$^{2*}$, Ay Yan$^1$"
    assert a3 == "$^1$ Institute of Physics \\\\[\\baselineskip] $^2$ Institute of Mathematics \\\\[\\baselineskip] $^{*}$ corresponding authors" 

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()