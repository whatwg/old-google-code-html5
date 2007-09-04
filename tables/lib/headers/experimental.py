import html4

class HeadingMatcher(html4.HeadingMatcher):
    def __init__(self, useScopeAttr=True, useHeadersAttr=True,
                 useTdBHeadings=False, useTdStrongHeadings=False,):
        self.useScopeAttr = useScopeAttr
        self.useHeadersAttr = useHeadersAttr
        self.useTdBHeadings = useTdBHeadings
        self.useTdStrongHeadings = useTdStrongHeadings
    
    def implicitHeaders(self, table, cell):
        row_headers = []
        col_headers = []
        
        #In some cases with overlapping cells we might try to examine a cell
        #more than once to see if it is a heading
        cells_examined = []
        
        def checkAxis(axis, axis_headers, start_x, start_y):
            axis_all_headings = True
            
            #Check if the cell is in a row/column that is all headings; if it
            #is do not add other headers from along that axis
            if axis=="row":
                origin = (0, cell.anchor[1])
            else:
                assert axis == "col"
                origin = (cell.anchor[0],1)
            
            for current_cell in table.iterCells(origin,
                                                 axis=axis, dir=1):
                if not self.isHeading(table, current_cell):
                    axis_all_headings = False
                    break
            
            if not axis_all_headings:
                last_cell = None
                for current_cell in table.iterCells((start_x, start_y),
                                                    axis=axis, dir=-1):
                    if (self.isHeading(table, current_cell) and
                        current_cell not in axis_headers and
                        not "scope" in current_cell.element.attrib):
                        axis_headers.append(current_cell)
                        #If a header cell has the headers attribute set,
                        #then the headers referenced by this attribute are
                        #inserted into the list and the search stops for the
                        #current direction.
                        if (self.useHeadersAttr and
                            "headers" in current_cell.element.attrib):
                            axis_headers += self.headersAttrHeaders(table, current_cell)
                            break
                        #The search in a given direction stops when the edge of the
                        #table is reached or when a data cell is found after a
                        #header cell.
                        if last_cell in axis_headers:
                            break
                    last_cell == current_cell
        
        #Need to search over all rows and cols the cell covers
        
        #Start by searching up each column
        for x_cell in range(cell.anchor[0], cell.anchor[0] + cell.colspan):
            checkAxis("col", col_headers, x_cell, cell.anchor[1]-1)
        
        #Then search along the row
        for y_cell in range(cell.anchor[1], cell.anchor[1] + cell.rowspan):
            checkAxis("row", row_headers, cell.anchor[0]-1, y_cell)
        
        #Column headers are inserted after row headers, in the order
        #they appear in the table, from top to bottom.
        headers = row_headers[::-1] + col_headers[::-1]
        
        return headers
    
    def isHeading(self, table, cell):
        """HTML 4 defines cells with the axis attribute set to be headings"""
        heading = cell.isHeading 
        if (self.useTdBHeadings and not cell.element.text
            and cell.element.getchildren() and cell.element[0].tag == "b"):
            heading = True
        if (self.useTdStrongHeadings and not cell.element.text and
            cell.element.getchildren() and cell.element[0].tag == "strong"):
            heading = True
        return heading
    

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