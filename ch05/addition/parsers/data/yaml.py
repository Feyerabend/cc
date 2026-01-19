
class SimpleYAMLParser:
    def __init__(self):
        self.lines = []
        self.current_line = 0
        self.indentation_stack = []

    def parse(self, yaml_str):
        self.lines = yaml_str.splitlines()
        self.current_line = 0
        self.indentation_stack = []
        return self._parse_element()

    def _get_indent_level(self, line):
        if '\t' in line:
            raise ValueError("Tabs are not allowed in YAML indentation")
        return len(line) - len(line.lstrip(' '))

    def _parse_element(self):
        if self.current_line >= len(self.lines):
            return None

        line = self.lines[self.current_line].strip()
        if not line or line.startswith('#'):  # empty lines and comments
            self.current_line += 1
            return self._parse_element()

        indent_level = self._get_indent_level(self.lines[self.current_line])
        self._check_indentation(indent_level)

        if line.startswith('-'):
            return self._parse_sequence(indent_level)
        elif ':' in line:
            return self._parse_mapping(indent_level)
        else:
            return self._parse_scalar()

    def _check_indentation(self, indent_level):
        if not self.indentation_stack:
            self.indentation_stack.append(indent_level)
        elif indent_level > self.indentation_stack[-1]:
            self.indentation_stack.append(indent_level)
        elif indent_level < self.indentation_stack[-1]:
            while self.indentation_stack and indent_level < self.indentation_stack[-1]:
                self.indentation_stack.pop()
            if indent_level != self.indentation_stack[-1]:
                raise ValueError("Improper indentation")

    def _parse_sequence(self, indent_level):
        sequence = []
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].strip()
            current_indent = self._get_indent_level(self.lines[self.current_line])

            if not line or current_indent < indent_level or not line.startswith('-'):
                break

            item = line[1:].strip()  # leading '-' and whitespace
            if ':' in item:  # inline mapping inside sequence
                self.current_line += 1
                sequence.append(self._parse_mapping(indent_level + 1))
            else:
                sequence.append(self._parse_scalar(item))
                self.current_line += 1

        return sequence

    def _parse_mapping(self, indent_level):
        mapping = {}
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].strip()
            current_indent = self._get_indent_level(self.lines[self.current_line])

            if not line or current_indent < indent_level:
                break

            if ':' not in line:
                raise ValueError("Invalid mapping syntax")
            
            key, value = map(str.strip, line.split(':', 1))
            self.current_line += 1

            if value:  # inline
                mapping[key] = self._parse_scalar(value)
            else:  # indented value
                child_element = self._parse_element()
                mapping[key] = child_element if child_element is not None else None

        return mapping

    def _parse_scalar(self, value=None):
        if value is None:
            value = self.lines[self.current_line].strip()
            self.current_line += 1

        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        elif value.isdigit():
            return int(value)
        elif self._is_float(value):
            return float(value)
        elif value in {'true', 'false'}:
            return value == 'true'
        else:
            return value

    def _is_float(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False


yaml_str = """
key1: value1
key2: 
  nested_key1: 123
  nested_key2: 
    - item1
    - item2
key3: true
key4: 
  - seq_item1
  - seq_item2
"""

parser = SimpleYAMLParser()
parsed_data = parser.parse(yaml_str)
print(parsed_data)
