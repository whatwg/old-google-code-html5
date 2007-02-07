/**
 * Author: Charl van Niekerk <charlvn@charlvn.za.net>
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
req.open("GET", "annotate-data.xml", true);
req.send(null);
