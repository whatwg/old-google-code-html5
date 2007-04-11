import xml.dom.minidom

# The XML parser is much faster than the html5lib parser, so this
# intermediate XHTML file is helpful
doc = xml.dom.minidom.parse(open('current-work.xhtml'))

# Convert from XHTML5 back to HTML5
doc.documentElement.removeAttribute('xmlns')
doc.documentElement.setAttribute('lang', doc.documentElement.getAttribute('xml:lang'))
doc.documentElement.removeAttribute('xml:lang')
head = doc.documentElement.getElementsByTagName('head')[0]
head.insertBefore(doc.createElement('meta'), head.firstChild).setAttribute('charset', 'UTF-8')

# Change the stylesheet, icon and image references to be non-relative
def make_absolute(uri):
	if uri[0] == '/':
		return 'http://www.whatwg.org' + uri
	else:
		return 'http://www.whatwg.org/specs/web-apps/current-work/' + uri
for e in doc.getElementsByTagName('link'):
	e.setAttribute('href', make_absolute(e.getAttribute('href')))
for img in doc.getElementsByTagName('img'):
	img.setAttribute('src', make_absolute(img.getAttribute('src')))

# Create an empty body, for the page content to be added into later
default_body = doc.createElement('body')
default_body.setAttribute('class', 'draft')

# Extract the body from the source document
original_body = doc.getElementsByTagName('body')[0]
original_body.parentNode.replaceChild(default_body, original_body)

# Extract the header, so we can reuse it in every page
head = original_body.getElementsByTagName('div')[0]
# Make a stripped-down version of it
short_head = head.cloneNode(True)
short_head.childNodes = short_head.childNodes[:6]

# Get the annotation script too
script = original_body.getElementsByTagName('script')[-1]
script.parentNode.removeChild(script)

# Stuff for fixing up references:

id_pages = {}
# Finds all the ids and remembers which page they were on
def extract_ids(page, node):
	if node.nodeType == node.ELEMENT_NODE and node.hasAttribute('id'):
		id_pages[node.getAttribute('id')] = page
	for n in node.childNodes:
		extract_ids(page, n)
# Updates all the href="#id" to point to page#id
def fix_refs(page, node):
	if node.nodeType == node.ELEMENT_NODE and node.hasAttribute('href') and node.getAttribute('href')[0] == '#':
		id = node.getAttribute('href')[1:]
		if id in id_pages:
			if id_pages[id] != page: # only do non-local links
				node.setAttribute('href', '%s.html#%s' % (id_pages[id], id))
		else:
			print "warning: can't find target for #%s" % id
	for n in node.childNodes:
		fix_refs(page, n)

pages = [] # for saving all the output, so fix_refs can be called in a second pass

# Contents/intro page:

page = doc.cloneNode(True)
page_body = page.getElementsByTagName('body')[0]
# Keep moving stuff from the front of the source document into this
# page, until we find the first heading that isn't class="no-toc"
while not (original_body.firstChild.nodeName == 'h2'
		and 'no-toc' not in original_body.firstChild.getAttribute('class').split(' ')):
	extract_ids('index', original_body.firstChild)
	page_body.appendChild(original_body.firstChild)
page_body.appendChild(script.cloneNode(True))
pages.append( ('index', page, 'Front cover') )


# Section/subsection pages:

def getNodeText(node):
	if node.nodeType == node.TEXT_NODE:
		return node.nodeValue
	return ''.join(getNodeText(n) for n in node.childNodes)

split_exceptions = ['video', 'the-canvas', 'the-command', 'tokenisation', 'tree-construction']

while original_body.firstChild:
	# Handle the heading for this section
	heading = original_body.firstChild
	assert(heading.nodeName[0] == 'h') # guaranteed by the other loops
	title = getNodeText(heading)
	name = 'section-%s' % heading.getAttribute('id')
	print name

	page = doc.cloneNode(True)
	page_body = page.getElementsByTagName('body')[0]

	# Add the header
	page_body.appendChild(short_head.cloneNode(True))

	# Add the page heading
	page_body.appendChild(heading)
	extract_ids(name, heading)

	# Keep moving stuff from the source, until we reach the end of the
	# document or find a header to split on
	while original_body.firstChild and not (
			original_body.firstChild.nodeType == doc.ELEMENT_NODE and (
				original_body.firstChild.nodeName == 'h2' or
				original_body.firstChild.nodeName == 'h3' or
				original_body.firstChild.getAttribute('id') in split_exceptions
			)):
		extract_ids(name, original_body.firstChild)
		page_body.appendChild(original_body.firstChild)

	# Add the annotation script
	page_body.appendChild(script.cloneNode(True))

	pages.append( (name, page, title) )

# Fix the links, and add some navigation:

for i in range(len(pages)):
	name, doc, title = pages[i]

	fix_refs(name, doc)

	if name == 'index': continue # don't add nav links to the TOC page

	head = doc.getElementsByTagName('head')[0]

	nav = page.createElement('nav')
	nav.setAttribute('id', 'nav-bar')

	if i != 0:
		href = '%s.html#nav-bar' % pages[i-1][0]
		title = pages[i-1][2]
		a = page.createElement('a')
		a.setAttribute('href', href)
		a.appendChild(page.createTextNode('< %s' % title))
		nav.appendChild(a)
		nav.appendChild(page.createTextNode(u' \u2013 '))
		link = page.createElement('link')
		link.setAttribute('href', href)
		link.setAttribute('title', title)
		link.setAttribute('rel', 'prev')
		head.appendChild(link)

	a = page.createElement('a')
	a.setAttribute('href', 'index.html#contents')
	a.appendChild(page.createTextNode('Table of contents'))
	nav.appendChild(a)
	link = page.createElement('link')
	link.setAttribute('href', 'index.html#contents')
	link.setAttribute('title', 'Table of contents')
	link.setAttribute('rel', 'index')
	head.appendChild(link)

	if i != len(pages)-1:
		href = '%s.html#nav-bar' % pages[i+1][0]
		title = pages[i+1][2]
		a = page.createElement('a')
		a.setAttribute('href', href)
		a.appendChild(page.createTextNode('%s >' % title))
		nav.appendChild(page.createTextNode(u' \u2013 '))
		nav.appendChild(a)
		link = page.createElement('link')
		link.setAttribute('href', href)
		link.setAttribute('title', title)
		link.setAttribute('rel', 'next')
		head.appendChild(link)

	body = doc.getElementsByTagName('body')[0]
	body.insertBefore(nav, body.childNodes[1]) # after the header


def html5Serializer(element):
	element.normalize()
	rv = []
	specialtext = ['style', 'script', 'xmp', 'iframe', 'noembed', 'noframes', 'noscript']
	empty = ['area', 'base', 'basefont', 'bgsound', 'br', 'col', 'embed', 'frame',
			 'hr', 'img', 'input', 'link', 'meta', 'param', 'spacer', 'wbr']

	def escapeHTML(str):
		return str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

	def serializeElement(element):
		if element.nodeType == element.DOCUMENT_TYPE_NODE:
			rv.append("<!DOCTYPE %s>" % element.name)
		elif element.nodeType == element.DOCUMENT_NODE:
			for child in element.childNodes:
				serializeElement(child)
		elif element.nodeType == element.COMMENT_NODE:
			rv.append("<!--%s-->" % element.nodeValue)
		elif element.nodeType == element.TEXT_NODE:
			unescaped = False
			n = element.parentNode
			while n is not None:
				if n.nodeName in specialtext:
					unescaped = True
					break
				n = n.parentNode
			if unescaped:
				rv.append(element.nodeValue)
			else:
				rv.append(escapeHTML(element.nodeValue))
		else:
			rv.append("<%s" % element.nodeName)
			if element.hasAttributes():
				for name, value in element.attributes.items():
					rv.append(' %s="%s"' % (name, escapeHTML(value)))
			rv.append(">")
			if element.nodeName not in empty:
				for child in element.childNodes:
					serializeElement(child)
				rv.append("</%s>" % element.nodeName)
	serializeElement(element)
	return '<!DOCTYPE HTML>\n' + ''.join(rv)


# Output all the pages
for name, doc, title in pages:
	open('extract/%s.html' % name, 'w').write(html5Serializer(doc).encode('utf-8'))

