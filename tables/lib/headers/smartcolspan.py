class HeadingMatcher(object):
    def __init__(self):
        pass

    def matchAll(self, table):
        rv = {}
        headers_dict = self.associateHeaders(table)
        for slot in table:
            for cell in slot:
                rv[cell] = headers_dict.get(cell)
        return rv

    def isHeading(self, table, cell):
        """HTML 4 defines cells with the axis attribute set to be headings"""
        return cell.isHeading
    
    def associateHeaders(self, table):
        rv = {}
        #For each cell at the top of the table
        for current_heading in table.iterCells((0, 0), axis="row", dir=1):
            if self.isHeading(table, current_heading):
                #For each col this cell covers
                for x in range(current_heading.anchor[0], current_heading.anchor[0] + current_heading.colspan):
                    column_headings = [current_heading]
                    #Have we found the first data cell
                    td_found = False
                    for current_cell in table.iterCells(
                        (x, current_heading.rowspan),
                        axis="col", dir=1):
                        if current_cell not in rv:
                            rv[current_cell] = []
                        #Go down the column
                        if self.isHeading(table, current_cell) and not td_found:
                            rv[current_cell].extend(column_headings)
                            column_headings.append(current_cell)
                        elif self.isHeading(table, current_cell):
                            for heading in column_headings[:]:
                                if heading.colspan == current_cell.colspan:
                                    column_headings.remove(heading)
                            rv[current_cell].extend(column_headings[:])
                            column_headings.append(current_cell)
                        else:
                            td_found = True
                            rv[current_cell].extend(column_headings[:])
        return rv