heading_class_prefix = "__tableparser_heading_classname";
heading_ref_class_suffix = "_ref";
heading_classes = [];
current_displayed_element = null;

function toggle_heading_information(element) {
    toggle_class(element, "__tableparser_active_cell");
};

function toggle_highlight_heading(element) {
    toggle_class(element, "__tableparser_active_heading");
};

function is_heading_id_class(class_name) {
    rv = (class_name.indexOf(heading_class_prefix) == 0 & class_name.indexOf(heading_ref_class_suffix) != class_name.length-heading_ref_class_suffix.length);
    return rv;
};

function is_heading_ref_class(class_name) {
    rv = (class_name.indexOf(heading_class_prefix) == 0 & class_name.indexOf(heading_ref_class_suffix) == class_name.length-heading_ref_class_suffix.length);
    return rv;
};

function extract_heading_classes(elements) {
    for (var i=0; i<elements.length; i++) {
        var element = elements[i];
        if (element.hasAttribute("classes")) {
            var classes = element.getAttribute("class").split(" ");
            var heading_classes = [];
            for (var j=0; j<classes.length; j++) {
                if (is_heading_id_class(classes[j])) {
                    heading_classes.push(classes[j]);
                };
            };
        };
    };
    return heading_classes;
};

function heading_ref_classes(element) {
    if (element.hasAttribute("class")) {
        var classes = element.getAttribute("class").split(" ");
        var heading_classes = [];
        for (var j=0; j<classes.length; j++) {
                if (is_heading_ref_class(classes[j])) {
                    heading_classes.push(classes[j]);
                };
        };
    } else {
        var heading_classes = [];
    };
    return heading_classes;
};

function ref_class_to_id_class(class_name) {
    return class_name.substr(0, class_name.length - heading_ref_class_suffix.length);
};

function get_heading_classes() {
    var heading_elements = document.getElementsByTagName("th");
    var data_elements = document.getElementsByTagName("td");
    return extract_heading_classes(heading_elements) + extract_heading_classes(data_elements);    
};

function cell_identify_headings(element) {
    var headings = heading_ref_classes(element);
    var heading_elements = []
    for (var i=0; i<headings.length; i++) {
        var heading_class = ref_class_to_id_class(headings[i]);
        heading_elements.push(getElementsByClassName(heading_class)[0]);
      };
    return heading_elements;
};

function toggle_class(element, class_name) {

    var element_class = "";
    if (element.hasAttribute("class")) {
        element_class = element.getAttribute("class");
    };

    if (element_class.indexOf(class_name) != -1) {
        var new_class = element_class.substr(0, element_class.indexOf(class_name));
        new_class += element_class.substr(element_class.indexOf(class_name)+class_name.length);
        element_class = new_class;
    } else {
        //Need to add the classname
        if (element_class != "") {
            element_class += " ";
        };
        element_class += class_name;
    };
    element.setAttribute("class", element_class);
};

function cell_click(event) {
    var element = event.currentTarget;
    if (current_displayed_element != null) {
        toggle_heading_information(current_displayed_element);
        var headings = cell_identify_headings(current_displayed_element);
        for (var i=0; i<headings.length; i++) {
            toggle_highlight_heading(headings[i]);
        };
    };
    
    //Now add style to the displayed headings
    if (element != current_displayed_element) {
        var headings = cell_identify_headings(element);
        for (var i=0; i<headings.length; i++) {
            var heading_element = headings[i];
            toggle_highlight_heading(heading_element);
        };
        toggle_heading_information(element);
    };
        
    //Save a ref to the element currently being displayed
    current_displayed_element = element;
};

function load_page() {
    //Get a list of all heading classes
    heading_classes = get_heading_classes();
    
    //Attach event listeners to all td and th elements
    var heading_elements = document.getElementsByTagName("th");
    var data_elements = document.getElementsByTagName("td");
    for (var i=0; i<heading_elements.length; i++) {
        heading_elements[i].addEventListener("click", cell_click, false);
    };
    for (var i=0; i<data_elements.length; i++) {
        data_elements[i].addEventListener("click", cell_click, false);
    };

    add_display_options();
    toggle_view_all_headings();

};

function add_display_options() {
    var heading = document.createElement("h2");
    heading.appendChild(document.createTextNode("Display Options"));
    
    var label = document.createElement("label");
    label.appendChild(document.createTextNode("Display all headings"));
    
    var checkbox = document.createElement("input");
    checkbox.setAttribute("type", "checkbox");
    checkbox.setAttribute("id", "display_all_headings");
    //checkbox.setAttribute("checked", "checked");
    checkbox.addEventListener("change", function(event){toggle_view_all_headings();}, 
                              false);
    label.appendChild(checkbox);
    
    var p = document.createElement("p");
    p.appendChild(label);
    
    var div = document.createElement("div");
    div.setAttribute("class", "section");
    var form = document.createElement("form");
    form.appendChild(p);
    
    div.appendChild(heading);
    div.appendChild(form);
    
    var body = document.getElementsByTagName("body")[0];
    var h1 = document.getElementsByTagName("h1")[0];

    body.insertBefore(div, h1.nextSibling);
};

function toggle_view_all_headings() {
    var view_headings = document.getElementById("display_all_headings").checked;
    if (view_headings) {
        document.selectedStyleSheetSet = 'Headings Visible';
    } else {
        document.selectedStyleSheetSet = 'Headings Hidden';
    };
};

function getElementsByClassName(searchClass, node, tag) {
    if ( node == null )
        node = document;
    if ( tag == null )
        tag = '*';

    if (node.getElementsByClassName) {
        return node.getElementsByClassName(searchClass);
    };

    var classElements = new Array();
    var els = node.getElementsByTagName(tag);
    var elsLen = els.length;
    var pattern = new RegExp("(^|\\s)"+searchClass+"(\\s|$)");
    for (i = 0, j = 0; i < elsLen; i++) {
        if ( pattern.test(els[i].className) ) {
            classElements[j] = els[i];
            j++;
        }
    }
    return classElements;
};

