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