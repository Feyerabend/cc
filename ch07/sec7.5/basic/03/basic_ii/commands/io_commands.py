"""
Input/Output commands for BASIC.
Implements PRINT and INPUT commands.
"""
from typing import List
from ..commands.base import ParsedCommand
from ..core.state import InterpreterState
from ..core.exceptions import ExecutionError
from ..utils.helpers import split_on_delimiter


class PrintCommand(ParsedCommand):
    """
    PRINT command - outputs values to console.
    
    Syntax: PRINT expr1; expr2, expr3
    - Semicolon (;): concatenate without space
    - Comma (,): tab to next 8-character boundary
    - Trailing semicolon: no newline after output
    """

    def __init__(self, state: InterpreterState, debug: bool = False):
        super().__init__(state, debug)
        self.current_pos = 0
        self.output_parts = []

    def process(self, args: str) -> None:
        """Process PRINT statement."""
        # Empty PRINT just outputs newline
        if not args.strip():
            print()
            return

        self.current_pos = 0
        self.output_parts = []

        # Check for trailing semicolon (suppresses newline)
        trailing_semicolon = args.rstrip().endswith(";")
        if trailing_semicolon:
            args = args.rstrip()[:-1]  # Remove trailing semicolon

        # Split on semicolons and commas
        parts = self._split_print_parts(args)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            try:
                if part == ",":
                    # Comma: tab to next boundary
                    self._tab_to_boundary()
                else:
                    # Evaluate and print expression
                    value = self.parse_expression(part)
                    output = str(value)
                    self.output_parts.append(output)
                    self.current_pos += len(output)
            except Exception as e:
                self._log(f"Error evaluating '{part}': {e}")
                self.output_parts.append("?")
                self.current_pos += 1

        # Output everything
        final_output = "".join(self.output_parts)
        if trailing_semicolon:
            print(final_output, end="")
        else:
            print(final_output)

    def _split_print_parts(self, args: str) -> List[str]:
        """Split PRINT arguments on semicolons and commas."""
        parts = []
        current = []
        in_string = False
        quote_char = None
        paren_depth = 0  # Track parentheses depth

        for char in args:
            # Handle quotes
            if char in ('"', "'"):
                if not in_string:
                    in_string = True
                    quote_char = char
                elif char == quote_char:
                    in_string = False
                    quote_char = None
                current.append(char)
            
            # Handle parentheses (for function calls)
            elif char == '(' and not in_string:
                paren_depth += 1
                current.append(char)
            
            elif char == ')' and not in_string:
                paren_depth -= 1
                current.append(char)

            # Handle separators outside strings and parentheses
            elif char in (';', ',') and not in_string and paren_depth == 0:
                if current:
                    parts.append(''.join(current))
                    current = []
                if char == ',':
                    parts.append(',')  # Preserve comma as marker

            else:
                current.append(char)

        # Add remaining
        if current:
            parts.append(''.join(current))

        return parts

    def _tab_to_boundary(self) -> None:
        """Tab to next 8-character boundary."""
        spaces_needed = 8 - (self.current_pos % 8)
        if spaces_needed == 0:
            spaces_needed = 8
        self.output_parts.append(" " * spaces_needed)
        self.current_pos += spaces_needed


class InputCommand(ParsedCommand):
    """
    INPUT command - reads values from user.
    
    Syntax: INPUT "prompt"; var1, var2, ...
    or: INPUT var1, var2, ...
    """

    def process(self, args: str) -> None:
        """Process INPUT statement."""
        # Parse optional prompt
        prompt = ""
        variables = args

        # Check for string literal prompt
        if args.strip().startswith('"') or args.strip().startswith("'"):
            quote_char = args.strip()[0]
            end_quote = args.find(quote_char, 1)
            
            if end_quote != -1:
                prompt = args[1:end_quote]
                remainder = args[end_quote + 1:].strip()
                
                # Skip semicolon or comma after prompt
                if remainder and remainder[0] in (';', ','):
                    remainder = remainder[1:].strip()
                
                variables = remainder

        # Parse variable names
        var_names = [v.strip() for v in variables.split(',') if v.strip()]

        if not var_names:
            raise ExecutionError("INPUT requires at least one variable")

        # Get input from user
        if prompt:
            user_input = input(prompt + " ")
        else:
            user_input = input("? ")

        # Parse input values
        input_values = [v.strip() for v in user_input.split(',')]

        # Assign to variables
        for i, var_name in enumerate(var_names):
            if i < len(input_values):
                # Try to parse as number, otherwise treat as string
                value_str = input_values[i]
                try:
                    # Try as number
                    value = float(value_str)
                    # Use int if it's a whole number
                    if value == int(value):
                        value = int(value)
                except ValueError:
                    # Keep as string (remove quotes if present)
                    value = value_str.strip('"').strip("'")
                
                self.state.set_variable(var_name, value)
            else:
                # Not enough values provided
                self.state.set_variable(var_name, 0)


class RemCommand(ParsedCommand):
    """
    REM command - comment (remark).
    
    Syntax: REM any text here
    Does nothing - just for documentation.
    """

    def process(self, args: str) -> None:
        """Process REM statement - do nothing."""
        pass  # Comments are ignored
