"""
Utility functions for the BASIC interpreter.
Common helpers used across different modules.
"""
from typing import List, Tuple, Any


def split_statements(line: str) -> List[str]:
    """
    Split a line into multiple statements separated by colons.
    Respects string literals and doesn't split within them.
    """
    statements = []
    current = []
    in_string = False
    quote_char = None
    i = 0

    while i < len(line):
        char = line[i]

        # Handle quote characters
        if char in ('"', "'") and (not in_string or quote_char == char):
            if in_string:
                in_string = False
                quote_char = None
            else:
                in_string = True
                quote_char = char
            current.append(char)

        # Handle escaped quotes
        elif char == '\\' and i + 1 < len(line) and line[i + 1] in ('"', "'") and in_string:
            current.append(char)
            current.append(line[i + 1])
            i += 1

        # Statement separator (colon)
        elif char == ':' and not in_string:
            statement = ''.join(current).strip()
            if statement:
                statements.append(statement)
            current = []

        else:
            current.append(char)

        i += 1

    # Add final statement
    statement = ''.join(current).strip()
    if statement:
        statements.append(statement)

    return statements


def split_on_delimiter(text: str, delimiter: str, respect_parens: bool = False) -> List[str]:
    """
    Split text on delimiter while respecting string literals and optionally parentheses.
    
    Args:
        text: Text to split
        delimiter: Delimiter character to split on
        respect_parens: If True, don't split within parentheses
    
    Returns:
        List of split parts
    """
    parts = []
    current = []
    in_string = False
    quote_char = None
    paren_count = 0
    i = 0

    while i < len(text):
        char = text[i]

        # Handle quotes
        if char in ('"', "'") and (not in_string or quote_char == char):
            if in_string:
                in_string = False
                quote_char = None
            else:
                in_string = True
                quote_char = char
            current.append(char)

        # Handle parentheses (if respecting them)
        elif char == '(' and not in_string and respect_parens:
            paren_count += 1
            current.append(char)

        elif char == ')' and not in_string and respect_parens:
            paren_count -= 1
            current.append(char)

        # Handle delimiter
        elif char == delimiter and not in_string and (not respect_parens or paren_count == 0):
            part = ''.join(current).strip()
            if part:
                parts.append(part)
            current = []

        else:
            current.append(char)

        i += 1

    # Add final part
    part = ''.join(current).strip()
    if part:
        parts.append(part)

    return parts


def parse_line_number(line: str) -> Tuple[int, str]:
    """
    Parse a BASIC line into line number and content.
    
    Args:
        line: BASIC line (e.g., "10 PRINT 'Hello'")
    
    Returns:
        Tuple of (line_number, remaining_content)
    
    Raises:
        ValueError: If line doesn't start with a valid line number
    """
    parts = line.split(maxsplit=1)
    
    if not parts or not parts[0].isdigit():
        raise ValueError("Line must start with a line number")
    
    line_number = int(parts[0])
    content = parts[1] if len(parts) > 1 else ""
    
    return line_number, content


def is_numeric(value: str) -> bool:
    """Check if a string represents a numeric value."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int with a default."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float with a default."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default