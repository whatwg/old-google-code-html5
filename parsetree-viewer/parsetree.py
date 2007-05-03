#!/usr/bin/env python
import urllib
import httplib2
import urlparse
import cgi
import cgitb
cgitb.enable()

import html5lib
from html5lib.treebuilders import simpletree

from genshi.template import MarkupTemplate
from genshi.builder import tag

try:
    import psyco
    psyco.full()
except ImportError:
    pass

tagClasses = {"element":"markup element-name",
              "attr_name":"markup attribute-name",
              "attr_value":"markup attribute-value",
              "comment":"markup comment",
              "doctype":"markup doctype",
              "text":"text",
              "text_marker":"marker text_marker",
              "comment_marker":"marker comment_marker",
              "doctype_marker":"marker doctype_marker"}

class ParseTreeHighlighter(object):    
    def makeStream(self, node, indent=-2):
        if node.type not in (simpletree.Document.type,
                             simpletree.DocumentFragment.type):
            indent+=2
            rv = self.serializeNode(node, indent)
        else:
            rv = tag()
        for child in node.childNodes:
            rv.append(self.makeStream(child, indent))
        return rv

    def serializeNode(self, node, indent):
        rv = tag(" "*indent+"|")

        if node.type == simpletree.TextNode.type:
            text = node.value.split("\n")
            rv.append(tag(tag.code("#text: ", class_=tagClasses["text_marker"]),
                      tag.code(text[0], class_=tagClasses["text"])))
            for line in text[1:]:
                rv.append(tag(tag("\n" + " "*indent+"|"),
                              tag.code(line, class_=tagClasses["text"])))
        elif node.type == simpletree.Element.type:
            rv.append(tag.code(node.name, class_=tagClasses["element"]))
            if node.attributes:
                for key, value in node.attributes.iteritems():
                    rv.append(tag(" ", tag.code(key,
                                                class_=tagClasses["attr_name"]),
                              "=", tag.code("\""+value+"\"",
                                            class_=tagClasses["attr_value"])))
        elif node.type == simpletree.CommentNode.type:
            rv.append(tag(tag.code("#comment: ", class_=tagClasses["comment_marker"]),
                      tag.code(node.data, class_=tagClasses["comment"])))
        elif node.type == simpletree.DocumentType.type:
            rv.append(tag(tag.code("DOCTYPE: ", class_=tagClasses["doctype_marker"]),
                          tag.code(node.name, class_=tagClasses["doctype"])))
        rv.append(tag("\n"))
        return rv

class InnerHTMLHighlighter(object):
    def makeStream(self, node, indent=-2):
        if node.type == simpletree.Element.type:
            indent+=2
        if node.type not in (simpletree.Document.type,
                             simpletree.DocumentFragment.type):
            rv = self.serializeNode(node, indent)
        else:
            rv = tag()
        for child in node.childNodes:
            rv.append(self.makeStream(child, indent))
        if node.type == simpletree.Element.type:
            rv.append(tag.code("</" + node.name + ">",
                               class_=tagClasses["element"]))
        return rv
    
    def serializeNode(self, node, indent):
        if node.type == simpletree.TextNode.type:
            rv = tag.code(node.value, class_="text")
        elif node.type == simpletree.Element.type:
            rv = tag.code("<" + node.name, class_=tagClasses["element"])
            if node.attributes:
                for key, value in node.attributes.iteritems():
                    rv.append(tag(" ", tag.code(key,
                                                class_=tagClasses["attr_name"]),
                              "=", tag.code("\""+value+"\"",
                                            class_=tagClasses["attr_value"])))
            rv.append(tag.code(">", class_=tagClasses["element"]))    
        elif node.type == simpletree.CommentNode.type:
            rv = tag.code("<!--"+node.data+"-->", class_=tagClasses["comment"])
        elif node.type == simpletree.DocumentType.type:
            rv = tag.code("<!DOCTYPE " + node.name + ">", class_=tagClasses["doctype"])
        return rv

class Response(object):
    templateFilename = "output.xml"
    
    def __init__(self, uri, **kwargs):
        self.parser = html5lib.HTMLParser()    
        self.uri=uri
        self.args = kwargs
        
    def parse(self, source):
        return self.parser.parse(source)

    def responseString(self, source):
        raise NotImplementedError

class ParseTree(Response):
    def generateResponseStream(self, source, tree):
        template = MarkupTemplate(open(self.templateFilename).read())
        treeHighlighter = ParseTreeHighlighter()
        htmlHighlighter = InnerHTMLHighlighter()

        parseTree = treeHighlighter.makeStream(tree)
        innerHTML = htmlHighlighter.makeStream(tree)
        
        viewURL = self.viewUrl()
        
        stream = template.generate(inputDocument=source,
                                   parseTree = parseTree,
                                   innerHTML = innerHTML,
                                   parseErrors=self.parser.errors,
                                   viewURL = viewURL)
        return stream

    def responseString(self, source):
        self.source = source
        tree = self.parse(source)
        source = source.decode(self.parser.tokenizer.stream.charEncoding, "ignore")
        stream = self.generateResponseStream(source, tree)
        return stream.render('html', doctype=("html", "", ""))

    def viewUrl(self):
        parameters = urllib.urlencode({"uri":self.uri or "",
                                       "source":self.source or "",
                                       "loaddom":1})
        urlparts = ["", "", "parsetree.py", parameters, ""]
        return urlparse.urlunsplit(urlparts)

class TreeToJS(object):
    def serialize(self, tree):
        rv = []
        rv.append("var node = document.getElementsByTagName('html')[0];")
        #Remove the <html> node
        rv.append("var currentNode = node.parentNode;")
        rv.extend(["currentNode.removeChild(node);"])
        for node in tree:
            if node.name == "html":
                rv.extend(self.buildSubtree(node))
                break
        return "\n".join(rv)
    
    def buildSubtree(self, node):
        rv = []
        rv.extend(self.serializeNode(node))
        for i, child in enumerate(node.childNodes):
            rv.extend(self.buildSubtree(child))
        #Set the current node back to the node constructed when we were called
        rv.append("currentNode = currentNode.parentNode;")    
        return rv
    
    def serializeNode(self, node):
        rv = []
        if node.type == simpletree.TextNode.type:
            rv.append("node = document.createTextNode('%s');"%self.escape(node.value))
        elif node.type == simpletree.Element.type:
            rv.append("node = document.createElement('%s');"%self.escape(node.name))
            if node.attributes:
                for key, value in node.attributes.iteritems():
                    rv.append("attr = node.setAttribute('%s', '%s')"%(key,self.escape(value)))
        elif node.type == simpletree.CommentNode.type:
            rv.append("node = document.createComment('%s')"%self.escape(node.data))
    
        rv.append("currentNode.appendChild(node)")
        #Set the current node to the node we just inserted
        rv.append("currentNode = currentNode.childNodes[currentNode.childNodes.length-1];")
        return rv
    
    def escape(self, str):
        replaces = (
            ("\\", "\\\\"),
            ("\b", "\\b"),
            ("\f", "\\f"),
            ("\n", "\\n"),
            ("\r", "\\r"),
            ("\t", "\\t"),
            ("\v", "\\v"),
            ("\"",  "\\\""),
            ("'", "\\'")
            )
        for key, value in replaces:
            str = str.replace(key, value)
        return str

class LoadSource(Response):
    attr_val_is_uri=('href', 'src', 'action', 'longdesc')

    def rewriteLinks(self, tree):
        if not self.uri:
            return
        baseUri = urlparse.urlsplit(self.uri)
        for node in tree:
            if node.type == simpletree.Element.type and node.attributes:
                for key, value in node.attributes.iteritems():
                    if key in self.attr_val_is_uri:
                        node.attributes[key] = urlparse.urljoin(self.uri, value)

    def insertHtml5Doctype(self, tree):
        doctype = simpletree.DocumentType("html")
        tree.insertBefore(doctype, tree.childNodes[0])

    def parse(self, source):
        return self.parser.parse(source)

    def generateResponseStream(self, tree):
        template = MarkupTemplate("""<html xmlns="http://www.w3.org/1999/xhtml"
                                xmlns:py="http://genshi.edgewall.org/">
                                <head><script>${jsCode}</script></head>
                                <body></body>
                                </html>""")
        jsGenerator = TreeToJS()
        jsCode = jsGenerator.serialize(tree)
        stream = template.generate(jsCode = jsCode)
        return stream

    def responseString(self, source):
        tree = self.parse(source)
        self.rewriteLinks(tree)
        stream = self.generateResponseStream(tree)
        doctype=None
        for node in tree.childNodes:
            if node.type == simpletree.DocumentType.type:
                doctype = (tree.childNodes[0].name, "", "")
                break
        
        return stream.render('html', doctype=doctype)

class Document(object):
    def __init__(self, uri=None, source=None, ua=None):
        self.uri = uri
        self.source = source
        self.ua = ua
        self.http = httplib2.Http()
        self.error=None
        if not source and uri:
            self.source = self.load()
        
    def load(self):
        uri = self.uri
        response=None
        content=None
        if uri.startswith("http://") or uri.startswith("https://"):
            response, content = self.http.request(uri, headers={"User-Agent":self.ua})
        else:
            self.error = "Invalid http URI %s"%self.uri
        if content:
            return content
        else:
            self.error = "%s \n %n"%(str(response.code), response.reason)
            return None

def cgiMain():
    print "Content-type: text/html; charset=utf-8\n\n"
    try:
        form = cgi.FieldStorage()
        uri = form.getvalue("uri")
        source = form.getvalue("source")
        ua = form.getvalue("ua")
        if source:
            uri=None
        loadDOM = form.getvalue("loaddom")
        document = Document(uri=uri, source=source, ua=ua)
    except:
        raise

    if document.source is None:
        print document.error
        return
    else:
        if loadDOM:
            resp = LoadSource(uri)
        else:
            resp = ParseTree(uri)
        respStr = resp.responseString(document.source)
    print respStr

if __name__ == "__main__":
    cgiMain()
