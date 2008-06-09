try:
    import psyco
    psyco.full() # make html5lib faster
except ImportError:
    pass

import sys
import html5lib
import html5lib.serializer
import html5lib.treewalkers
import re
from lxml import etree # requires lxml 2.0
from copy import deepcopy

print "HTML5 Spec Splitter"

absolute_uris = False
w3c = False
file_args = []

for arg in sys.argv[1:]:
    if arg == '--absolute':
        absolute_uris = True
    elif arg == '--w3c':
        w3c = True
    else:
        file_args.append(arg)

if len(file_args) != 2:
    print 'Run like "python [options] spec-splitter.py index multipage"'
    print '(The directory "multipage" must already exist)'
    print
    print 'Options:'
    print '  --absolute  convert relative URIs to absolute (e.g. for images)'
    print '  --w3c       use W3C variant instead of WHATWG'
    sys.exit()

if w3c:
    index_page = 'Overview'
else:
    index_page = 'index'

# The document is split on all <h2> elements, plus the following specific elements
# (which were chosen to split any pages that were larger than about 100-200KB, and
# may need to be adjusted as the spec changes):
split_exceptions = [
    'offline', 'history', 'structured',
    'the-root', 'text-level', 'embedded0', 'video', 'the-canvas', 'tabular', 'interactive-elements',
    'parsing', 'tokenisation', 'tree-construction', 'serializing', 'named',
]


print "Parsing..."

# Parse document
parser = html5lib.html5parser.HTMLParser(tree = html5lib.treebuilders.getTreeBuilder('lxml'))
doc = parser.parse(open(file_args[0]), encoding='utf-8')

print "Splitting..."

# Absolutise some references, so the spec can be hosted elsewhere
if absolute_uris:
    for a in ('href', 'src'):
        for t in ('link', 'script', 'img'):
            for e in doc.findall('//%s[@%s]' % (t, a)):
                if e.get(a)[0] == '/':
                    e.set(a, 'http://www.whatwg.org' + e.get(a))
                else:
                    e.set(a, 'http://www.whatwg.org/specs/web-apps/current-work/' + e.get(a))

# Extract the body from the source document
original_body = doc.find('body')

# Create an empty body, for the page content to be added into later
default_body = etree.Element('body')
if original_body.get('class'): default_body.set('class', original_body.get('class'))
if original_body.get('onload'): default_body.set('onload', 'fixBrokenLink(); %s' % original_body.get('onload'))
original_body.getparent().replace(original_body, default_body)

# Extract the header, so we can reuse it in every page
header = original_body.find('.//div[@class="head"]')

# Make a stripped-down version of it
short_header = deepcopy(header)
del short_header[3:]

# Prepare the link-fixup script
if not w3c:
    link_fixup_script = etree.XML('<script src="link-fixup.js"/>')
    doc.find('head')[-1].tail = '\n  '
    doc.find('head').append(link_fixup_script)
    link_fixup_script.tail = '\n  '

# Stuff for fixing up references:

def get_page_filename(name):
    return '%s.html' % name

# Finds all the ids and remembers which page they were on
id_pages = {}
def extract_ids(page, node):
    if node.get('id'):
        id_pages[node.get('id')] = page
    for e in node.findall('.//*[@id]'):
        id_pages[e.get('id')] = page

# Updates all the href="#id" to point to page#id
missing_warnings = []
def fix_refs(page, node):
    for e in node.findall('.//a[@href]'):
        if e.get('href')[0] == '#':
            id = e.get('href')[1:]
            if id in id_pages:
                if id_pages[id] != page: # only do non-local links
                    e.set('href', '%s#%s' % (get_page_filename(id_pages[id]), id))
            else:
                if id not in missing_warnings:
                    print "warning: can't find target for #%s" % id
                    missing_warnings.append(id)

pages = [] # for saving all the output, so fix_refs can be called in a second pass

# Iterator over the full spec's body contents
child_iter = original_body.iterchildren()

# Contents/intro page:

page = deepcopy(doc)
page_body = page.find('body')

# Keep copying stuff from the front of the source document into this
# page, until we find the first heading that isn't class="no-toc"
for e in child_iter:
    if e.getnext().tag == 'h2' and 'no-toc' not in (e.getnext().get('class') or '').split(' '):
        break
    page_body.append(e)

pages.append( (index_page, page, 'Front cover') )

# Section/subsection pages:

def getNodeText(node):
    return re.sub('\s+', ' ', etree.tostring(node, method='text').strip())

for heading in child_iter:
    # Handle the heading for this section
    title = getNodeText(heading)
    name = heading.get('id')
    if name == index_page: name = 'section-%s' % name
    print '  %s' % name

    page = deepcopy(doc)
    page_body = page.find('body')

    # Add the header
    page_body.append(deepcopy(short_header))

    # Add the page heading
    page_body.append(deepcopy(heading))
    extract_ids(name, heading)

    # Keep copying stuff from the source, until we reach the end of the
    # document or find a header to split on
    e = heading
    while e.getnext() is not None and not (
            e.getnext().tag == 'h2' or e.getnext().get('id') in split_exceptions
        ):
        e = child_iter.next()
        extract_ids(name, e)
        page_body.append(deepcopy(e))

    pages.append( (name, page, title) )

# Fix the links, and add some navigation:

for i in range(len(pages)):
    name, doc, title = pages[i]

    fix_refs(name, doc)

    if name == index_page: continue # don't add nav links to the TOC page

    head = doc.find('head')

    if w3c:
        nav = etree.Element('div') # HTML 4 compatibility
    else:
        nav = etree.Element('nav')
    nav.text = '\n   '
    nav.tail = '\n\n  '

    if i > 1:
        href = get_page_filename(pages[i-1][0])
        title = pages[i-1][2]
        a = etree.XML(u'<a href="%s">\u2190 %s</a>' % (href, title))
        a.tail = u' \u2013\n   '
        nav.append(a)
        link = etree.XML('<link href="%s" title="%s" rel="prev"/>' % (href, title))
        link.tail = '\n  '
        head.append(link)

    a = etree.XML('<a href="%s.html#contents">Table of contents</a>' % index_page)
    a.tail = '\n  '
    nav.append(a)
    link = etree.XML('<link href="%s.html#contents" title="Table of contents" rel="index"/>' % index_page)
    link.tail = '\n  '
    head.append(link)

    if i != len(pages)-1:
        href = get_page_filename(pages[i+1][0])
        title = pages[i+1][2]
        a = etree.XML(u'<a href="%s">%s \u2192</a>' % (href, title))
        a.tail = '\n  '
        nav.append(a)
        a.getprevious().tail = u' \u2013\n   '
        link = etree.XML('<link href="%s" title="%s" rel="next"/>' % (href, title))
        link.tail = '\n  '
        head.append(link)

    doc.find('body').insert(1, nav) # after the header

print "Outputting..."

# Output all the pages
for name, doc, title in pages:
    f = open('%s/%s' % (file_args[1], get_page_filename(name)), 'w')
    if w3c:
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN">\n')
    else:
        f.write('<!DOCTYPE HTML>\n')
    tokens = html5lib.treewalkers.getTreeWalker('lxml')(doc)
    serializer = html5lib.serializer.HTMLSerializer(quote_attr_values=True, inject_meta_charset=False)
    for text in serializer.serialize(tokens, encoding='us-ascii'):
        f.write(text)

# Generate the script to fix broken links
f = open('%s/fragment-links.js' % (file_args[1]), 'w')
f.write('var fragment_links = { ' + ','.join("'%s':'%s'" % (k,v) for (k,v) in id_pages.items()) + ' };\n')
f.write("""
var fragid = window.location.hash.substr(1);
if (!fragid) { /* handle section-foo.html links from the old multipage version, and broken foo.html from the new version */
    var m = window.location.pathname.match(/\/(?:section-)?([\w\-]+)\.html/);
    if (m) fragid = m[1];
}
var page = fragment_links[fragid];
if (page) {
    window.location.replace(page+'.html#'+fragid);
}
""")

print "Done."
