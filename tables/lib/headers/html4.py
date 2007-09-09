
class HeadingMatcher(object):
    def __init__(self, useScopeAttr=True, useHeadersAttr=True):
        self.useScopeAttr = useScopeAttr
        self.useHeadersAttr = useHeadersAttr
    
    def matchAll(self, table):
        """Return a dict mapping each cell to a heading cell"""
        rv = {}
        if self.useScopeAttr:
            scope_map = scopeAttributeHeaders(table)
        for slot in table:
            for cell in slot:
                #If the cell has a rowspan or colspan > 1 it will be
                #in multiple slots. In this case we only want to
                #process the cell once
                if cell in rv:
                    continue
                if self.useHeadersAttr:
                    rv[cell] = self.headersAttrHeaders(table, cell)
                    if rv[cell] is not None:
                        continue
                if self.useScopeAttr:
                    rv[cell] = self.scopeAttrHeaders(table, cell, scope_map)
                    if rv[cell] is not None:
                        continue
                rv[cell] = self.implicitHeaders(table, cell)
                if cell not in rv:
                    rv[cell] = None
        return rv
    
    def implicitHeaders(self, table, cell):
        row_headers = []
        col_headers = []
        
        #In some cases with overlapping cells we might try to examine a cell
        #more than once to see if it is a heading
        cells_examined = []
        
        def checkAxis(axis, axis_headers, start_x, start_y):
            last_cell = None
            for current_cell in table.iterCells((start_x, start_y),
                                                axis=axis, dir=-1):
                if (self.isHeading(table, current_cell) and
                    current_cell not in axis_headers and
                    (not self.useScopeAttr or
                     not "scope" in cell.element.attrib)):
                    
                    axis_headers.append(current_cell)
                    #If a header cell has the headers attribute set,
                    #then the headers referenced by this attribute are
                    #inserted into the list and the search stops for the
                    #current direction.
                    if (self.useHeadersAttr and
                        "headers" in current_cell.element.attrib):
                        axis_headers += self.headersAttrHeaders(table, current_cell)
                        break
                else:
                    #The search in a given direction stops when the edge of the
                    #table is reached or when a data cell is found after a
                    #header cell.
                    if last_cell in axis_headers:
                        break
                last_cell = current_cell
        
        #Need to search over all rows and cols the cell covers
        
        #Start by searching up each column 
        for x_cell in range(cell.anchor[0], cell.anchor[0] + cell.colspan):
            checkAxis("col", col_headers, x_cell, cell.anchor[1]-1)
            
        for y_cell in range(cell.anchor[1], cell.anchor[1] + cell.rowspan):
            checkAxis("row", row_headers, cell.anchor[0]-1, y_cell)
        
        #Column headers are inserted after row headers, in the order
        #they appear in the table, from top to bottom.
        headers = row_headers[::-1] + col_headers[::-1]
        
        return headers
    
    def headersAttrHeaders(self, table, cell):
        headers = []
        if not "headers" in cell.element.attrib:
            return None
        attr = cell.element.attrib["headers"]
        #The value of this attribute is a space-separated list of cell names
        for id in attr.split(" "):
            headerElements = table.element.xpath("//*[@id='%s']"%id)
            for item in headerElements:
                cell = table.getCellByElement(item)
                if cell is not None:
                    headers.append(cell)
        return headers
    
    def scopeAttrHeaders(self, table, cell, scopeMap=None):
        if scopeMap is None:
            scopeMap = scopeAttrHeaders(table)
        headers = []
        for header, cells in scopeMap.iteritems():
            if cell in cells:
                headers.append(header)
        if not headers:
            headers = None
        return headers
    
    def isHeading(self, table, cell):
        """HTML 4 defines cells with the axis or scope attribute set to be headings"""
        return (cell.isHeading or "axis" in cell.element.attrib
                or "scope" in cell.element.attrib)
    

def scopeAttributeHeaders(table):
    """Return a dict matching a heading to a list of cells to which it is
    assosiated"""
    rv = {}
    for heading_cell in table.headings:
        heading_element = heading_cell.element
        if not "scope" in heading_element.attrib:
            continue
        scope = heading_element.attrib["scope"]
        x,y = heading_cell.anchor
        if scope == "row":
            rv[heading_cell] = [item for item in table.iterCells((x+heading_cell.colspan, y), axis="row")]
        elif scope == "col":
            rv[heading_cell] = [item for item in table.iterCells((x, y+heading_cell.rowspan), axis="col")]
        elif scope == "rowgroup":
            cells = []
            for rowgroup in table.rowgroups:
                if heading_cell in rowgroup.iterCells():
                    cells += [item for item in rowgroup.iterCells() if item != heading_cell]
            rv[heading_cell] = cells
        elif scope == "colgroup":
            cells = []
            for colgroup in table.colgroups:
                if heading_cell in colgroup.iterCells():
                    cells += [item for item in colgroup.iterCells() if item != heading_cell]
            rv[heading_cell] = cells
    return rv
