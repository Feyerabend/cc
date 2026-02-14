"""
Data manipulation commands for BASIC.
Implements LET and DIM commands.
"""
from typing import List, Tuple
from ..commands.base import ParsedCommand
from ..core.state import InterpreterState
from ..core.exceptions import ExecutionError, ArrayError, ParserError
from ..parsing.tokenizer import Tokenizer
from ..parsing.parser import ExpressionParser
from ..execution.evaluator import ExpressionEvaluator
from ..expressions.ast import ArrayExpression


class LetCommand(ParsedCommand):
    """
    LET command - assigns values to variables.
    
    Syntax: LET variable = expression
    or: variable = expression (implicit LET)
    
    Also handles array assignments: A(1,2) = value
    """

    def process(self, args: str) -> None:
        """Process LET statement."""
        # Remove leading "LET" if present
        if args.upper().startswith("LET "):
            args = args[4:].strip()

        # Find the assignment operator
        if "=" not in args:
            raise ExecutionError("LET requires an assignment (=)")

        # Split on first equals sign
        parts = args.split("=", 1)
        if len(parts) != 2:
            raise ExecutionError("Invalid assignment syntax")

        target = parts[0].strip()
        expression = parts[1].strip()

        # Evaluate the right-hand side
        try:
            value = self.parse_expression(expression)
        except Exception as e:
            raise ExecutionError(f"Error evaluating expression: {e}")

        # Handle array assignment vs variable assignment
        if "(" in target and target.endswith(")"):
            self._assign_to_array(target, value)
        else:
            self._assign_to_variable(target, value)

    def _assign_to_variable(self, name: str, value: any) -> None:
        """Assign value to a simple variable."""
        if not name.replace("_", "").replace("$", "").isalnum():
            raise ExecutionError(f"Invalid variable name: {name}")

        self.state.set_variable(name, value)
        self._log(f"Set {name} = {value}")

    def _assign_to_array(self, target: str, value: any) -> None:
        """Assign value to an array element."""
        try:
            # Parse as array expression
            tokenizer = Tokenizer(target)
            tokens = tokenizer.tokenize()
            
            parser = ExpressionParser(tokens)
            expr = parser.parse()

            if not isinstance(expr, ArrayExpression):
                raise ExecutionError(f"Invalid array assignment: {target}")

            # Evaluate indices
            evaluator = ExpressionEvaluator(self.state, self.debug)
            indices = [int(evaluator.evaluate(idx)) for idx in expr.indices]

            # Validate array exists
            if expr.name not in self.state.arrays:
                raise ArrayError(f"Array '{expr.name}' not declared")

            # Validate dimensions
            dims = self.state.array_dims.get(expr.name, ())
            if len(indices) != len(dims):
                raise ArrayError(
                    f"Array '{expr.name}' expects {len(dims)} indices, got {len(indices)}"
                )

            # Validate bounds (1-based indexing)
            for i, idx in enumerate(indices):
                if not (1 <= idx <= dims[i]):
                    raise ArrayError(
                        f"Index {idx} out of bounds for dimension {i} (1-{dims[i]})"
                    )

            # Convert to 0-based and store
            adjusted_indices = tuple(idx - 1 for idx in indices)
            self.state.set_array_value(expr.name, adjusted_indices, value)
            
            self._log(f"Set {expr.name}{indices} = {value}")

        except Exception as e:
            raise ExecutionError(f"Array assignment error: {e}")


class DimCommand(ParsedCommand):
    """
    DIM command - declares arrays with dimensions.
    
    Syntax: DIM array(size1)
    or: DIM array(size1, size2)
    or: DIM array1(10), array2(5,5)
    
    Arrays use 1-based indexing.
    Dimensions specify the maximum index (e.g., DIM A(10) creates indices 1-10).
    """

    def process(self, args: str) -> None:
        """Process DIM statement."""
        # Split multiple array declarations
        declarations = self._split_declarations(args)

        for decl in declarations:
            decl = decl.strip()
            if not decl:
                continue

            try:
                self._process_single_declaration(decl)
            except Exception as e:
                raise ExecutionError(f"Error in DIM declaration '{decl}': {e}")

    def _split_declarations(self, args: str) -> List[str]:
        """Split multiple array declarations (separated by commas outside parens)."""
        declarations = []
        current = []
        paren_count = 0
        in_string = False
        quote_char = None

        for char in args:
            # Handle strings
            if char in ('"', "'"):
                if not in_string:
                    in_string = True
                    quote_char = char
                elif char == quote_char:
                    in_string = False
                    quote_char = None
                current.append(char)

            # Handle parentheses
            elif char == '(' and not in_string:
                paren_count += 1
                current.append(char)

            elif char == ')' and not in_string:
                paren_count -= 1
                current.append(char)

            # Handle comma separator (outside parens)
            elif char == ',' and paren_count == 0 and not in_string:
                if current:
                    declarations.append(''.join(current).strip())
                    current = []

            else:
                current.append(char)

        # Add final declaration
        if current:
            declarations.append(''.join(current).strip())

        return declarations

    def _process_single_declaration(self, decl: str) -> None:
        """Process a single array declaration."""
        # Parse name and dimensions
        if '(' not in decl or not decl.endswith(')'):
            raise ParserError(f"Invalid DIM syntax: {decl}")

        parts = decl.split('(', 1)
        if len(parts) != 2:
            raise ParserError(f"Invalid DIM syntax: {decl}")

        name = parts[0].strip()
        dims_str = parts[1].rstrip(')').strip()

        # Validate name
        if not name:
            raise ParserError("Array name missing")
        
        if not name.replace("_", "").replace("$", "").isalnum():
            raise ParserError(f"Invalid array name: {name}")

        if name in self.state.arrays or name in self.state.variables:
            raise ExecutionError(f"'{name}' already declared")

        # Parse dimensions
        if not dims_str:
            raise ParserError("No dimensions specified")

        dim_strs = [d.strip() for d in dims_str.split(',') if d.strip()]
        
        if len(dim_strs) < 1 or len(dim_strs) > 2:
            raise ExecutionError("Arrays must have 1 or 2 dimensions")

        # Evaluate dimension expressions
        dim_values = []
        for dim_str in dim_strs:
            try:
                value = int(self.parse_expression(dim_str))
                if value < 1:
                    raise ExecutionError(f"Array dimension must be positive: {value}")
                dim_values.append(value)
            except Exception as e:
                raise ExecutionError(f"Invalid dimension '{dim_str}': {e}")

        # Create array (add 1 to dimensions for 1-based indexing)
        # E.g., DIM A(10) creates array with indices 1-10, stored as 0-9 internally
        adjusted_dims = tuple(d + 1 for d in dim_values)
        self.state.declare_array(name, adjusted_dims)
        
        self._log(f"Declared array {name} with dimensions {dim_values}")
