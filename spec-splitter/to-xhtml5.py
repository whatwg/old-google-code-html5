import html5lib

parser = html5lib.html5parser.HTMLParser(tree=html5lib.treebuilders.dom.TreeBuilder)
doc = parser.parse(open('current-work'), encoding='utf-8')

doc.documentElement.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
doc.documentElement.setAttribute('xml:lang', doc.documentElement.getAttribute('lang'))
doc.removeChild(doc.firstChild) # remove the DOCTYPE

open('current-work.xhtml', 'w').write(doc.toxml(encoding = 'UTF-8'))

