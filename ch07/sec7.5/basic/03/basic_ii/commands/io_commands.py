"""
Input/Output commands for BASIC.
Implements PRINT and INPUT commands.
"""
from typing import List
from ..commands.base import ParsedCommand
from ..core.state import InterpreterState
from ..core.exceptions import ExecutionError
from ..utils.helpers import split_on_delimiter
from .data_commands import LetCommand


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

        # Parse variable names; A(I, J) counts as one
        var_names = [v.strip() for v in split_on_delimiter(variables, ',', respect_parens=True) if v.strip()]

        if not var_names:
            raise ExecutionError("INPUT requires at least one variable")

        # As in classic BASIC: string variables ($) take the text as it is,
        # numeric variables need a number or the whole input is asked again,
        # and missing values are asked for with "??"
        values = self._read_values(var_names, prompt + " " if prompt else "? ")
        for var_name, value in zip(var_names, values):
            if "(" in var_name and var_name.endswith(")"):
                LetCommand(self.state, self.debug)._assign_to_array(var_name, value)
            else:
                self.state.set_variable(var_name, value)

    def _read_values(self, var_names: List[str], prompt: str) -> List:
        while True:
            fields = [f.strip() for f in input(prompt).split(',')]
            while len(fields) < len(var_names):
                fields += [f.strip() for f in input("?? ").split(',')]
            values = []
            for var_name, field in zip(var_names, fields):
                if self._is_string_variable(var_name):
                    if len(field) >= 2 and field[0] == field[-1] and field[0] in ('"', "'"):
                        field = field[1:-1]
                    values.append(field)
                    continue
                try:
                    number = float(field)
                except ValueError:
                    break
                values.append(int(number) if number == int(number) else number)
            if len(values) == len(var_names):
                if len(fields) > len(var_names):
                    print("?EXTRA IGNORED")
                return values
            print("?REDO FROM START")

    @staticmethod
    def _is_string_variable(var_name: str) -> bool:
        return var_name.split("(")[0].strip().endswith("$")


class RemCommand(ParsedCommand):
    """
    REM command - comment (remark).
    
    Syntax: REM any text here
    Does nothing - just for documentation.
    """

    def process(self, args: str) -> None:
        """Process REM statement - do nothing."""
        pass  # Comments are ignored
