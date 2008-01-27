import cgi
class HeadingMatcher(object):
    def __init__(self, no_headings_if_spans_data_col = False):
        self.no_headings_if_spans_data_col = no_headings_if_spans_data_col

    def matchAll(self, table):
        rv = {}
        self.table = table
        #Create a header -> cells mapping
        headers = {}
        for cell in table.iterCells():
            if self.isHeading(cell):
                headers[cell] = self.associateCellsWithHeader(cell)
        #Invert the headers -> cells mapping to a cell -> headers mapping
        headers_dict = {}
        for k, v in headers.iteritems():
            if v is None:
                continue
            for cell in v:
                if cell not in headers_dict:
                    headers_dict[cell] = [k]
                else:
                    headers_dict[cell].append(k)
        
        for cell in table.iterCells():
            headers_attr_headers = self.headersAttrHeaders(table, cell)
            #If the cell has a headers attribute add those headers and no others
            if headers_attr_headers:
                rv[cell] = headers_attr_headers
            elif cell in headers_dict:
                rv[cell] = headers_dict[cell]
            else:
                rv[cell] = None
        return rv

    def isHeading(self, cell):
        return cell.isHeading
    
    def associateCellsWithHeader(self, header):
        scope = None
        if "scope" in header.element.attrib:
            scope = header.element.attrib["scope"]
        if scope is None or scope not in ("row", "col", "rowgroup", "colgroup"):
            scope = "auto"
        
        cells = []
        
        if scope == "auto":
            cells = self.getCellsFromAxes(header, ("row", "col"))
        elif scope == "row":
            cells = self.getCellsFromAxes(header, ("row",), skip_heading_only_axes=False)
        elif scope == "col":
            cells = self.getCellsFromAxes(header, ("col",), skip_heading_only_axes=False)
        elif scope == "rowgroup":
            groups = self.getHeaderGroups(header, "row")
            assert len(groups) == 1
            cells = self.getCellsFromGroup(header, groups[0])
        elif scope == "colgroup":
            groups = self.getHeaderGroups(header, "col")
            for group in groups:
                cells.extend([item for item in
                              self.getCellsFromGroup(header, group) if item not in cells])
        return cells
    
    def getCellsFromAxes(self, header, axes, skip_heading_only_axes=True):
        cells = []
        for axis in axes:
            if axis == "row":
                min_index = header.anchor[1]
                max_index = header.anchor[1] + header.rowspan
            else:
                min_index = header.anchor[0]
                max_index = header.anchor[0] + header.colspan
            span = axis + "span"
            for axis_index in xrange(min_index, max_index):
                prev_cell = header
                heading_span = getattr(header, span)
                if axis == "row":
                    start_index = (header.anchor[0]+header.colspan, axis_index)
                else:
                    start_index = (axis_index, header.anchor[1]+header.rowspan)
                
                current_headings = []
                
                #If all the cells in the row/col are headings, none apply to each other
                if skip_heading_only_axes:
                    all_headings = True
                    for cell in self.table.iterAxis(start_index, axis=axis, dir=1):
                        all_headings = self.isHeading(cell)
                        if not all_headings:
                            break
                    if all_headings:
                        continue
                    
                for cell in self.table.iterAxis(start_index, axis=axis, dir=1):
                    if self.isHeading(cell) and self.isHeading(prev_cell):
                        current_span = getattr(cell, span)
                        if heading_span >= current_span:
                            cells.append(cell)
                    elif self.isHeading(cell) and not self.isHeading(prev_cell):
                        current_span = getattr(cell, span)
                        if current_span == heading_span:
                            break
                        else:
                            cells.append(cell)
                    elif not self.isHeading(cell):
                        cells.append(cell)
                    prev_cell = cell
        return cells
    
    def getCellsFromGroup(self, header, group):
        rv = []
        for cell in group:
            if cell.anchor[0] >= header.anchor[0] and cell.anchor[1] >= header.anchor[1]:
                rv.append(cell)
        return rv
    
    def getHeaderGroups(self, cell, axis):
        property_map = {"col":(0, "colgroups"),
            "row":(1, "rowgroups")}
        rv = []
        idx, group_type = property_map[axis]
        for group in getattr(self.table, group_type):
            if group.anchor[idx] <= cell.anchor[idx]:
                if cell.anchor[idx] <= group.anchor[idx] + group.span - 1:    
                    rv.append(group)
            else:
                if group.anchor[idx] <= cell.anchor[idx] + getattr(cell, axis + "span"):
                    rv.append(group)
        return rv
       
    def associateHeaders(self, table):
        #The algorithm is this:
        #For each column in the table, then each row in the table:
        #  Create an empty list h of headers to apply
        #  For each cell in the axis, running from top to bottom (for columns)
        #  then in the text direction (for rows):
        #    If the cell is a heading cell and the previous cell was a heading
        #    cell, or if there was no previous cell:
        #        Add all the cells in l which are in scope and have a span
        #        greater than or equal to cell's span as headers for cell
        #        Add the cell to l
        #    If the cell is a heading cell and the previous cell was a data cell
        #        Remove all the cells from l that have a span equal to cell's span
        #        Add all the cells in l which are in scope as headers for cell
        #        Add cell to l
        #    If the cell is a data cell
        #        Add all the cells from l that are in scope as headings for cell
        #
        #A header is said to be /in scope/ for a particular cell if
        #  - The scope of the header is auto
        #  - The scope of the header is row and the cell spans a row also spanned by the header
        #  - The scope of the header is col and the cell spans a column also spanned by the header
        #  - The scope of the header is rowgroup and the cell is in the same rowgroup as the header
        #  - The scope of the header is colgroup and the cell and the header are in one or more of the same
        #    column groups 
    
        rv = {}
        axes = ("row", "col")
    
        for axis in axes:
            if axis == "row":
                max_index = table.y_max+1
            else:
                max_index = table.x_max+1
            span = axis + "span"
            for axis_index in xrange(max_index):
                prev_cell = None
                if axis == "row":
                    start_index = (0, axis_index)
                else:
                    start_index = (axis_index, 0)
                
                current_headings = []
                
                #If all the cells in the row/col are headings, none apply to each other
                for cell in table.iterAxis(start_index, axis=axis, dir=1):
                    all_headings = self.isHeading(table, cell)
                    if not all_headings:
                        break
                if all_headings:
                    continue
                    
                for cell in table.iterAxis(start_index, axis=axis, dir=1):
                    if cell not in rv:
                        rv[cell] = []
                    if self.isHeading(table, cell) and (not prev_cell or self.isHeading(table, prev_cell)):
                        current_span = getattr(cell, span)
                        wider_headings = [heading for heading in current_headings
                                          if getattr(heading, span) >= current_span]
                        rv[cell] += self.inScopeHeadings(cell, wider_headings)
                        current_headings.append(cell)
                    elif self.isHeading(table, cell) and not self.isHeading(table, prev_cell):
                        current_span = getattr(cell, span)
                        current_headings = [heading for heading in
                                            current_headings
                                            if getattr(heading, span) != current_span]
                        rv[cell] += self.inScopeHeadings(cell, current_headings)
                        current_headings.append(cell)
                    elif not self.isHeading(table, cell):
                        rv[cell] += self.inScopeHeadings(cell, current_headings)
                    prev_cell = cell
        return rv
    
    def inScopeHeadings(self, cell, current_headings):
        rv = []
        for heading in current_headings:
            if self.inScope(cell, heading):
                rv.append(heading)
        return rv
    
    def inScope(self, header, cell):
        if "scope" in header.element.attrib:
            header_scope = header.element.attrib["scope"]
        else:
            header_scope = "auto"
        if header_scope == "auto":
            return True
        for idx, scope in enumerate(("row", "col")):
            span = scope + "span"
            o_idx = (1+idx)%2
            if header_scope == scope:
                #XXX - gt sign not appropriate for rows in rtl
                if (cell.anchor[idx] >= header.anchor[idx] and
                    (cell.anchor[o_idx] >= heading.anchor[o_idx] and
                     cell.anchor[o_idx] <= heading.anchor[o_idx]+getattr(heading, span))):
                    return True
                else:
                    return False
        if header_scope == "colgroup":
            for colgroup in table.colgroups:
                if colgroup.anchor[0] <= cell.anchor[0]:
                    if cell.anchor[0] <= colgroup.anchor[0] + colgroup.span - 1:    
                        return True
                else:
                    if cell.anchor[0] <= colgroup.anchor[0]:
                        if colgroup.anchor[0] <= cell.anchor[0] + cell.colspan - 1:
                            return True
        if header_scope == "rowgroup":
            for rowgroup in table.rowgroups:
                if rowgroup.anchor[1] <= cell.anchor[1]:
                    if cell.anchor[1] <= colgroup.anchor[1] + rowgroup.span - 1:    
                        return True
                else:
                    if cell.anchor[1] <= colgroup.anchor[1]:
                        if colgroup.anchor[1] <= cell.anchor[1] + cell.rowspan - 1:
                            return True
        return False
    
    def headersAttrHeaders(self, table, cell):
        #What to do if an item is missing or is not a header?
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