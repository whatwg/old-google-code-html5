#!/usr/bin/env python
import sys
import urlparse
import urllib2
import cgi
import cgitb
cgitb.enable()
import itertools

import html5lib
from html5lib import treewalkers
import lxml.etree
import genshi
from genshi.template import MarkupTemplate
from genshi.core import QName, Attrs
from genshi.core import START, END, TEXT, COMMENT, DOCTYPE
    
import tableparser
import headers
from headers import html4, html5, experimental, smartcolspan

template_filename = "table_output.html"

debug=True

#From the html5lib test suite; need to put this somewhere sensible
def GenshiAdapter(treewalker, tree):
    text = None
    for token in treewalker(tree):
        token_type = token["type"]
        if token_type in ("Characters", "SpaceCharacters"):
            if text is None:
                text = token["data"]
            else:
                text += token["data"]
        elif text is not None:
            assert type(text) in (unicode, None)
            yield TEXT, text, (None, -1, -1)
            text = None

        if token_type in ("StartTag", "EmptyTag"):
            yield (START,
                   (QName(token["name"]),
                    Attrs([(QName(attr),value) for attr,value in token["data"]])),
                   (None, -1, -1))
            if token_type == "EmptyTag":
                token_type = "EndTag"

        if token_type == "EndTag":
            yield END, QName(token["name"]), (None, -1, -1)

        elif token_type == "Comment":
            yield COMMENT, token["data"], (None, -1, -1)

        elif token_type == "Doctype":
            yield DOCTYPE, (token["name"], None, None), (None, -1, -1)

        else:
            pass # FIXME: What to do?

    if text is not None:
        yield TEXT, text, (None, -1, -1)

def parseDocument(document):
    if hasattr(document, "info"):
        charset = document.info().getparam("charset")
    else:
        charset="utf-8"
    parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("etree", lxml.etree))
    tree = parser.parse(document, encoding=charset)
    return tree

def extractTables(data):
    tree = parseDocument(data)
    return tree.xpath("//table")

def copySubtree(in_root, out_root):
    out_root.text = in_root.text
    out_root.tail = in_root.tail
    for element in in_root.iterchildren():
        if isinstance(element.tag, basestring):
            new_element = lxml.etree.SubElement(out_root, element.tag, attrib=element.attrib)
            copySubtree(element, new_element)

def addStringListAttr(attr_name, element, value):
    """Add a class name to an element""";
    if attr_name in element.attrib:
        element.attrib[attr_name] += " " + value
    else:
        element.attrib[attr_name] = value

def addClass(element, class_name):
    return addStringListAttr("class", element, class_name)

def annotateTable(table_tree, table, heading_parser, table_id):
    """Take an input table element and return the table with each cell annotated
    with its heading inforamtion"""
    all_headings = heading_parser.matchAll(table)
    out_tree = lxml.etree.Element("table")
    copySubtree(table_tree, out_tree)
    
    #Make dict mapping input tree elements to output elements tuples
    element_map = {}
    for in_element, out_element in itertools.izip(table_tree.iterdescendants(),
                                                  out_tree.iterdescendants()):
        if in_element.tag in ("td","th"):
            cell = table.getCellByElement(in_element)
            if not cell:
                continue
        element_map[in_element] = out_element
    
    #Add classnames to all headings
    heading_classnames = {}
    heading_ids = {}
    heading_counter = itertools.count()
    
    for in_element, out_element in element_map.iteritems():
        cell = table.getCellByElement(in_element)
        if not cell:
            continue
        headings = all_headings[cell]
        if headings:
            container = lxml.etree.Element("div", attrib={"class":"__tableparser_heading_container"})
            #Add a paragraph to the cell identifying the headings
            title = lxml.etree.SubElement(container, "p", attrib={"class":"__tableparser_heading_title"})
            title.text = "Headings:"
            heading_list = lxml.etree.SubElement(container, "ul", attrib={"class":"__tableparser_heading_list"})
            for heading in headings:
                #Check if the heading is one we have encountered before.
                #If not, add a unique identifier for it
                if heading not in heading_classnames:
                    i= heading_counter.next()
                    class_name = "__tableparser_heading_classname_%s_%i"%(table_id, i)
                    id = "__tableparser_heading_id_%s_%i"%(table_id, i)
                    heading_out_element = element_map[heading.element]
                    addClass(heading_out_element, class_name)
                    heading_out_element.attrib['id'] = id
                    heading_classnames[heading] = class_name
                    heading_ids[heading] = id
                #For each heading, copy the subelements of the heading to the cell
                heading_data = lxml.etree.Element("li", attrib={"class":"__tableparser_heading_listitem"})
                copySubtree(heading.element, heading_data)
                heading_list.append(heading_data)
                #Add a class to the cell to match the heading
                addClass(out_element, heading_classnames[heading]+"_ref")
                addStringListAttr("headers", out_element, heading_ids[heading])
            out_element.insert(0, container)
            container.tail = out_element.text
            out_element.text=""
        
    return out_tree

def tableToStream(table_tree, heading_parser, table_id):
    """Take a tree for a table and return a (table,stream) pair where
    table is a tableparser.Table and stream is a genshi stream"""
    table = tableparser.TableParser().parse(table_tree)
    annotated_tree = annotateTable(table_tree, table, heading_parser, table_id)
    tw = treewalkers.getTreeWalker("etree", lxml.etree)
    return (table, GenshiAdapter(tw, annotated_tree))

def main():
    print "content-type:text/html;charset=utf-8\n\n"
    form = cgi.FieldStorage()
    uri = True and form.getfirst("uri") or ""
    if not uri:
        source = form.getfirst("source")
    else:
        try:
            source = urllib2.urlopen(uri)
        except urllib2.URLError:
            error("CANT_LOAD", uri)

    if not source and urlparse.urlsplit(uri)[0] not in ("http", "https"):
        error("INVALID_URI", uri)
    
    tables = extractTables(source)
        
    try:
        use_algorithm = form.getfirst("algorithm")
        use_scope = bool(form.getfirst("scope") == "1")
        use_headers = bool(form.getfirst("headers") == "1")
        
        if use_algorithm == "html4":
            use_scope = bool(form.getfirst("scope") == "1")
            use_headers = bool(form.getfirst("headers") == "1")
            heading_parser = html4.HeadingMatcher(use_scope, use_headers)
        elif use_algorithm == "html5":
            heading_parser = html5.HeadingMatcher()
        elif use_algorithm == "experimental":
            use_scope = bool(form.getfirst("scope") == "1")
            use_headers = bool(form.getfirst("headers") == "1")
            use_td_b_headings = bool(form.getfirst("b_headings") == "1")
            use_td_strong_headings = bool(form.getfirst("strong_headings") == "1")
            heading_parser = experimental.HeadingMatcher(use_scope, use_headers,
                                                         use_td_strong_headings,
                                                         use_td_b_headings)
        elif use_algorithm == "smartcolspan":
            heading_parser = smartcolspan.HeadingMatcher()
        else:
            raise
    
        data = [tableToStream(table, heading_parser, str(i)) for i, table in enumerate(tables)]
        out_template = MarkupTemplate(open(template_filename))
        stream = out_template.generate(data=data)
        print stream.render('html', doctype=("html", "", ""))
    except:
        if debug:
            raise
        else:
            error("", uri)
    

def error(error_type, input_uri):
    out_template = MarkupTemplate(open("error.xml"))
    stream = out_template.generate(uri=input_uri, errorType=error_type)
    print stream.render('html', doctype=("html", "", ""))
    sys.exit(1)

if __name__ == "__main__":
    main()