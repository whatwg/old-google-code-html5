function fixBrokenLink() {
    if (window.location.hash.length < 1)
        return;

    var fragid = window.location.hash.substr(1);
    if (document.getElementById(fragid))
        return;

    var script = document.createElement('script');
    script.src = 'fragment-links.js';
    document.body.appendChild(script);
}
