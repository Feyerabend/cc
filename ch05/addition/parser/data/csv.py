import re

class SimpleCSVParser:
    def __init__(self, delimiter=",", quote_char='"'):
        self.delimiter = delimiter
        self.quote_char = quote_char

    def parse(self, csv_string):
        rows = []
        current_row = []
        buffer = ""
        in_quotes = False

        for char in csv_string:
            if char == self.quote_char:  # toggle quoted field "
                in_quotes = not in_quotes
            elif char == self.delimiter and not in_quotes:  # end of field
                current_row.append(buffer)
                buffer = ""
            elif char in "\r\n" and not in_quotes:  # end of row: return, newline
                if buffer or current_row:  # do not add empty rows
                    current_row.append(buffer)
                    rows.append(current_row)
                buffer = ""
                current_row = []
            else:  # part of field
                buffer += char

        # add last field and row, if any
        if buffer or current_row:
            current_row.append(buffer)
            rows.append(current_row)

        return rows


# example
csv_data = """name,computer,price
"John Foo","",30
"Alice Baz","Apple I",2000
"Bob Bar",,23
"No one",,
"""

parser = SimpleCSVParser()
parsed_csv = parser.parse(csv_data)
for row in parsed_csv:
    print(row)
