import smartcolspan

class HeadingMatcher(smartcolspan.HeadingMatcher):
    #XXX - Should share all this code with the colspan case
    def associateHeaders(self, table):
        rv = {}
        #For each cell at the top of the table
        for current_heading in table.iterCells((0, 0), axis="col", dir=1):
            if self.isHeading(table, current_heading):
                #For each col this cell covers
                for x in range(current_heading.anchor[0]+current_heading.rowspan, current_heading.anchor[0]):
                    row_headings = [current_heading]
                    #Have we found the first data cell
                    td_found = False
                    for current_cell in table.iterCells(
                        (x, current_heading.rowspan),
                        axis="row", dir=1):
                        if current_cell not in rv:
                            rv[current_cell] = []
                        #Go across the row
                        if self.isHeading(table, current_cell) and not td_found:
                            rv[current_cell].extend(row_headings)
                            row_headings.append(current_cell)
                        elif self.isHeading(table, current_cell):
                            for heading in row_headings[:]:
                                if heading.colspan == current_cell.colspan:
                                    row_headings.remove(heading)
                            rv[current_cell].extend(row_headings[:])
                            row_headings.append(current_cell)
                        else:
                            td_found = True
                            rv[current_cell].extend(row_headings[:])
        return rv