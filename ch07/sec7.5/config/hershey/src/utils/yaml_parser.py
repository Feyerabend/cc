# src/utils/yaml_parser.py
# standalone lightweight YAML parser for basic configurations
from typing import Dict, Any

class SimpleYAMLParser:
    @staticmethod
    def parse(yaml_text: str) -> Dict:
        """Parse a YAML string into a nested dictionary"""
        result = {}
        lines = yaml_text.splitlines()
        stack = [(0, result)]  # Stack of (indent_level, current_dict)
        
        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()
            if not line or line.strip().startswith('#'):  # Skip empty lines and comments
                continue
                
            # Calculate indentation level (assuming 2 spaces per level)
            indent = len(line) - len(line.lstrip())
            if indent % 2 != 0:
                raise ValueError(f"Invalid indentation at line {line_num}: expected multiple of 2 spaces")
            
            level = indent // 2
            line = line.strip()
            
            # Split on first colon-space combo for key-value
            if ': ' in line:
                key, value = line.split(': ', 1)
            elif ':' in line:
                key, value = line.split(':', 1)
                value = value.strip()
            else:
                raise ValueError(f"Invalid YAML format at line {line_num}: expected 'key: value'")
            
            key = key.strip()
            if not key:
                raise ValueError(f"Empty key at line {line_num}")
            
            # Parse the value
            value = SimpleYAMLParser._parse_value(value.strip())
            
            # Find the correct dictionary to insert into based on indentation
            while stack and stack[-1][0] >= level:
                stack.pop()
            if not stack:
                raise ValueError(f"Invalid indentation at line {line_num}: too deep")
            current_dict = stack[-1][1]
            
            # Add to dictionary and push new level if value will be nested
            current_dict[key] = value
            if value == {}:  # If value is empty dict, expect nested content
                stack.append((level + 1, value))
        
        return result
    
    @staticmethod
    def _parse_value(value: str) -> Any:
        """Convert a string value to appropriate type"""
        if not value:  # Empty value becomes empty dict for nesting
            return {}
        value = value.lower()
        if value == 'true':
            return True
        elif value == 'false':
            return False
        elif value == 'null' or value == '':
            return None
        try:
            # Try integer
            return int(value)
        except ValueError:
            try:
                # Try float
                return float(value)
            except ValueError:
                # Handle quoted strings
                if value.startswith('"') and value.endswith('"'):
                    return value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    return value[1:-1]
                # Return as string
                return value
    
    @staticmethod
    def dump(data: Dict) -> str:
        """Convert a dictionary to a simple YAML string"""
        def dict_to_yaml(d, indent=0):
            lines = []
            for key, value in d.items():
                if isinstance(value, dict):
                    lines.append('  ' * indent + f"{key}:")
                    lines.extend(dict_to_yaml(value, indent + 1))
                else:
                    if isinstance(value, str) and ' ' in value:
                        value = f'"{value}"'
                    elif value is None:
                        value = 'null'
                    lines.append('  ' * indent + f"{key}: {value}")
            return lines
        return '\n'.join(dict_to_yaml(data)) + '\n'
