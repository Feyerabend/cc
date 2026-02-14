"""
User-defined function command for BASIC.
Implements DEF FN for creating custom functions.
"""
from ..commands.base import ParsedCommand
from ..core.state import InterpreterState
from ..core.exceptions import ExecutionError
from ..parsing.tokenizer import Tokenizer
from ..parsing.parser import ExpressionParser
from ..execution.evaluator import ExpressionEvaluator


class DefCommand(ParsedCommand):
    """
    DEF FN command - define user function.
    
    Syntax: DEF FNname(param) = expression
    or: DEF FNname(param1, param2, ...) = expression
    
    Examples:
        DEF FNA(Z) = 30 * EXP(-Z * Z / 100)
        DEF FNB(X, Y) = X * X + Y * Y
        DEF FNC(N) = N * (N + 1) / 2
    
    Usage:
        PRINT FNA(5)
        LET Y = FNB(3, 4)
    """

    def process(self, args: str) -> None:
        """Process DEF FN statement."""
        if not args.strip():
            raise ExecutionError("DEF requires function definition")
        
        # Must start with FN
        if not args.strip().upper().startswith("FN"):
            raise ExecutionError("DEF must be followed by FN (e.g., DEF FNA(X) = ...)")
        
        # Parse: FNname(params) = expression
        if '=' not in args:
            raise ExecutionError("DEF requires = in function definition")
        
        parts = args.split('=', 1)
        signature = parts[0].strip()
        expression = parts[1].strip()
        
        # Parse function name and parameters
        if '(' not in signature or ')' not in signature:
            raise ExecutionError("DEF requires parameter list in parentheses")
        
        paren_start = signature.index('(')
        paren_end = signature.rindex(')')
        
        func_name = signature[:paren_start].strip()
        params_str = signature[paren_start+1:paren_end].strip()
        
        # Validate function name (must be FN followed by letter(s))
        if not func_name.upper().startswith("FN"):
            raise ExecutionError("Function name must start with FN")
        
        if len(func_name) < 3:
            raise ExecutionError("Function name must be FN followed by at least one letter")
        
        # Parse parameters
        if params_str:
            params = [p.strip() for p in params_str.split(',')]
        else:
            params = []
        
        # Validate parameters are valid variable names
        for param in params:
            if not param.replace('_', '').replace('$', '').isalnum():
                raise ExecutionError(f"Invalid parameter name: {param}")
        
        # Store function definition in state
        if not hasattr(self.state, 'user_functions'):
            self.state.user_functions = {}
        
        self.state.user_functions[func_name.upper()] = {
            'params': params,
            'expression': expression
        }
        
        self._log(f"Defined function {func_name}({', '.join(params)}) = {expression}")
