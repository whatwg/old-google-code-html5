/**
 * Author: Charl van Niekerk <charlvn@charlvn.za.net>
 * Contributor: Simon Pieters <zcorpan@gmail.com>
 */

function annotateLoad(data) {
	var sections = data.getElementsByTagName("section");
	for (var i = 0; i < sections.length; i++) {
		var id = sections[i].getAttribute("id");
		var status = sections[i].getAttribute("status");
		var e = document.getElementById(id);
		if (e) {
			var spans = e.getElementsByTagName("span");
			if (spans && spans.length > 0 && spans[0].nextSibling) {
				var span = document.createElement("span");
				span.setAttribute("title", status);
				span.appendChild(document.createTextNode("[" + status + "]"));
				e.insertBefore(span, spans[0].nextSibling);
			}
			var div = document.createElement("div");
			div.className = status;
			e.parentNode.insertBefore(div, e);
			var level = e.tagName.split("H")[1];
			var current = div.nextSibling
			div.appendChild(current);
			while (current = div.nextSibling) {
				var tag = current.tagName;
				if (tag == "DIV" && /^H\d$/.test(current.firstChild.tagName))
					tag = current.firstChild.tagName;
				if (/^H(\d)$/.test(tag) && RegExp.$1 <= level)
					break;
				div.appendChild(current);
			}
		}
	}
}

function annotateHandle() {
	if (req.readyState == 4 && req.status == 200 && req.responseXML) {
		annotateLoad(req.responseXML);
	}
}

var req = new XMLHttpRequest();
req.onreadystatechange = annotateHandle;
req.open("GET", "annotate-data.xml", true); // xhr is relative to the document, not where the script was found
req.send(null);

var style = document.createElement("style");
style.type = "text/css"; // required in html4...
var styleText = document.createTextNode("\
 .TBW, .WIP, .SCS { margin-left:-2em; border-left:.2em solid; padding-left:1.8em; }\
 .TBW { border-color:red; }\
 .WIP { border-color:orange; }\
 .SCS { border-color:green; }\
 ");
var an3err
try { style.appendChild(styleText) } 
catch(an3err) { 
if(an3err.number == -0x7FFF0001) style.styleSheet.cssText =
styleText.nodeValue 
else throw an3err } 
document.getElementsByTagName("head")[0].appendChild(style);

/*
 * Author: Lachlan Hunt - http://lachy.id.au/
 * Date: 2007-08-15
 *
 * getElementsByClassName was wrtten by Tino Zijdel
 * http://therealcrisp.xs4all.nl/blog/2007/08/13/getelementsbyclassname-re-re-re-visited/
 */
 
var getElementsByClassName = function()
{
    // native
    if (document.getElementsByClassName)
    {
        return function(className, nodeName, parentElement)
        {
            var s = (parentElement || document).getElementsByClassName(className);

            if (nodeName && nodeName != '*')
            {
                nodeName = nodeName.toUpperCase();
                return Array.filter(s, function(el) { return el.nodeName == nodeName; });
            }
            else
                return [].slice.call(s, 0);
        }
    }

    // xpath
    if (document.evaluate)
    {
        return  function(className, nodeName, parentElement)
        {
            if (!nodeName) nodeName = '*';
            if (!parentElement) parentElement = document;

            var results = [], s, i = 0, element;

            s = document.evaluate(
                ".//" + nodeName + "[contains(concat(' ', @class, ' '), ' " + className + " ')]",
                parentElement,
                null,
                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                null
            );

            while ((element = s.snapshotItem(i++)))
                results.push(element);

            return results;
        }
    }

    // generic
    return function(className, nodeName, parentElement)
    {
        if (!nodeName) nodeName = '*';
        if (!parentElement) parentElement = document;

        var results = [], s, i = 0, element;
        var re = new RegExp('(^|\s)' + className + '(\s|$)'), elementClassName;

        s = parentElement.getElementsByTagName(nodeName);

        while ((element = s[i++]))
        {
            if (    (elementClassName = element.className) &&
                (elementClassName == className || re.test(elementClassName))
            )
                results.push(element);
        }

        return results;
    }
}();

function markIssue(issue) {
	var marker = document.createElement("strong");
	marker.innerHTML = "Big Issue: ";
	issue.insertBefore(marker, issue.firstChild);
}

var issues = getElementsByClassName("big-issue");
for (var i = 0; i < issues.length; i++) {
	markIssue(issues[i]);
}