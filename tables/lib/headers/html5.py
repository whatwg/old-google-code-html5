
class HeadingMatcher(object):
    def matchAll(self, table):
        rv = {}
        scope_map = scopeAttrHeaders(table)
        for slot in table:
            for cell in slot:
                rv[cell] = self.scopeAttrHeaders(table, cell, scope_map)
        return rv
    
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
        return cell.isHeading

def scopeAttrHeaders(table):
    """Return a dict matching a heading to a list of cells to which it is
    assosiated"""
    rv = {}
    for heading_cell in table.headings:
        heading_element = heading_cell.element
        if "scope" in heading_element.attrib:
            scope = heading_element.attrib["scope"]
        else:
            scope = None
        x,y = heading_cell.anchor
        if scope == "row":
            #The cell != heading cell thing is not in the spec
            rv[heading_cell] = [item for item in table.iterCells((x+1, y), "row") if not item.isHeading]
        elif scope == "col":
            rv[heading_cell] = [item for item in table.iterCells((x, y+1), axis="col") if not item.isHeading]
        elif scope == "rowgroup":
            cells = []
            for rowgroup in table.rowgroups:
                if heading_cell in rowgroup.iterCells():
                    cells += [item for item in rowgroup.iterCells() if not item.isHeading]
            rv[heading_cell] = cells
        elif scope == "colgroup":
            cells = []
            for colgroup in table.colgroups:
                if heading_cell in colgroup.iterCells():
                    cells += [item for item in colgroup.iterCells() if not item.isHeading]
            rv[heading_cell] = cells
        else:
            if x>0 and y>0:
                #Do not assign the heading to any cells
                continue
            elif y == 0:
                rv[heading_cell] = [item for item in table.iterCells((x, y+1), axis="col") if not item.isHeading]
            elif x == 0:
                rv[heading_cell] = [item for item in table.iterCells((x+1, y), "row") if not item.isHeading]
    return rv
