#!/usr/bin/env python
import glob

import lxml.etree
import html5lib
import simplejson

import tableparser
import headers

headers_algorithms = {"html4":headers.html4.HeadingMatcher,
                       "html5":headers.html5.HeadingMatcher}

def parseDocument(document):
    parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("etree", lxml.etree))
    tree = parser.parse(document)
    return tree

def compareHeaders(expected, actual):
    assert len(expected) == len(actual)
    for cell, headers in actual.iteritems():
        if headers is not None:
            actual_headers_text = [item.element.text for item in headers]
            actual_headers_text.sort()
            expected_headers_text = expected[cell.element.text]
            expected_headers_text.sort()
            assert expected_headers_text == actual_headers_text
        else:
            
            assert expected[cell.element.text] == []

def runTest(test_data):
    input_html = test_data["data"]
    table = parseDocument(input_html).xpath("//table")[0]
    tparser = tableparser.TableParser()
    table_data = tparser.parse(table)
    
    for algorithm, options, expected in test_data["expect"]:
        actual = headers_algorithms[algorithm](**options).matchAll(table_data)
        print actual
        compareHeaders(expected, actual)
    
    
def testHeadersMatcher():
    for testfile in glob.glob("headers/testdata/*.test"):
        print open(testfile).read()
        tests = simplejson.load(open(testfile))
        for test in tests["tests"]:
            yield runTest, test