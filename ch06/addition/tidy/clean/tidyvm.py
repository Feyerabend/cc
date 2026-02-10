"""
TidyVM - A Clean Stack-Based Lisp Interpreter

This implementation demonstrates clean code principles:
- Clear, descriptive naming
- Small, focused functions with single responsibilities
- No magic numbers or strings
- Modular design with separated concerns
- Self-documenting code structure
"""

import sys
import traceback
from typing import Any, List, Tuple, Dict, Optional


# =============================================================================
# CONSTANTS - Avoid magic strings and numbers
# =============================================================================

DEFAULT_PROMPT = 'vm> '
EMPTY_LIST_MARKER = '[]'
COMMENT_CHAR = ';'
OPEN_PAREN = '('
CLOSE_PAREN = ')'
DEBUG_COMMAND = ':debug'


# =============================================================================
# TYPE ALIASES - Make types clear
# =============================================================================

Symbol = str
Expression = Any  # Can be Symbol, int, float, or list
Instruction = Any  # Can be string or tuple
Code = List[Instruction]


# =============================================================================
# ENVIRONMENT - Lexical scoping with outer environment chain
# =============================================================================

class Environment(dict):
    """
    An environment for variable bindings with lexical scoping.
    
    Each environment is a dict of {variable: value} pairs with an optional
    outer environment for scope chaining.
    """
    
    def __init__(self, parameters: Tuple = (), arguments: Tuple = (), outer: Optional['Environment'] = None):
        """Initialize environment with parameter bindings and outer scope."""
        super().__init__(zip(parameters, arguments))
        self.outer = outer
    
    def find_binding(self, variable: Symbol) -> 'Environment':
        """Find the innermost environment where variable is bound."""
        if variable in self:
            return self
        elif self.outer is not None:
            return self.outer.find_binding(variable)
        else:
            raise NameError(f"Undefined variable: '{variable}'")


# =============================================================================
# CLOSURE - First-class functions with captured environments
# =============================================================================

class Closure:
    """
    A closure: compiled code with captured lexical environment.
    
    Represents a lambda function with its body code, parameters, and
    the environment in which it was created.
    """
    
    def __init__(self, code: Code, environment: Environment, parameters: Tuple[Symbol, ...] = ()):
        self.code = code
        self.environment = environment
        self.parameters = parameters
    
    def __repr__(self) -> str:
        param_names = ', '.join(self.parameters) if self.parameters else 'no params'
        return f"<Closure({param_names})>"


# =============================================================================
# VIRTUAL MACHINE - Stack-based execution engine
# =============================================================================

class VirtualMachine:
    """
    A stack-based virtual machine for executing compiled Lisp code.
    
    Executes instructions that manipulate a value stack and environment.
    Supports closures, conditionals, arithmetic, and list operations.
    """
    
    def __init__(self, environment: Environment, enable_debug: bool = False):
        self.stack: List[Any] = []
        self.environment = environment
        self.debug_enabled = enable_debug
    
    def execute_program(self, instructions: Code) -> Any:
        """Execute a sequence of instructions and return the final result."""
        program_counter = 0
        
        while program_counter < len(instructions):
            instruction = instructions[program_counter]
            
            if self.debug_enabled:
                self._print_debug_info(program_counter, instruction)
            
            self._execute_single_instruction(instruction)
            program_counter += 1
        
        return self._get_final_result()
    
    def _execute_single_instruction(self, instruction: Instruction) -> None:
        """Dispatch instruction to appropriate handler."""
        if isinstance(instruction, tuple):
            self._execute_compound_instruction(instruction)
        elif isinstance(instruction, str):
            self._execute_simple_instruction(instruction)
        else:
            raise ValueError(f"Invalid instruction type: {type(instruction)}")
    
    def _execute_compound_instruction(self, instruction: Tuple) -> None:
        """Execute tuple-based instructions (IF, CLOSURE)."""
        operation = instruction[0]
        
        if operation == 'IF':
            self._execute_conditional(instruction)
        elif operation == 'CLOSURE':
            self._execute_closure_creation(instruction)
        else:
            raise ValueError(f"Unknown compound instruction: {operation}")
    
    def _execute_simple_instruction(self, instruction: str) -> None:
        """Execute string-based instructions (PUSH, LOAD, ADD, etc)."""
        parts = instruction.split(maxsplit=1)
        opcode = parts[0]
        operand = parts[1] if len(parts) > 1 else None
        
        # Dispatch to appropriate handler
        handlers = {
            'PUSH': lambda: self._push_value(operand),
            'LOAD': lambda: self._load_variable(operand),
            'STORE': lambda: self._store_variable(operand),
            'CALL': lambda: self._call_function(operand),
            'ADD': lambda: self._binary_arithmetic(lambda a, b: a + b),
            'SUB': lambda: self._binary_arithmetic(lambda a, b: a - b),
            'MUL': lambda: self._binary_arithmetic(lambda a, b: a * b),
            'DIV': lambda: self._binary_arithmetic(lambda a, b: a / b),
            'GT': lambda: self._binary_comparison(lambda a, b: a > b),
            'LT': lambda: self._binary_comparison(lambda a, b: a < b),
            'GTE': lambda: self._binary_comparison(lambda a, b: a >= b),
            'LTE': lambda: self._binary_comparison(lambda a, b: a <= b),
            'EQ': lambda: self._binary_comparison(lambda a, b: a == b),
            'LIST': lambda: self._create_list(operand),
            'CAR': lambda: self._list_head(),
            'CDR': lambda: self._list_tail(),
            'CONS': lambda: self._list_cons(),
            'NULL?': lambda: self._is_null(),
            'ATOM?': lambda: self._is_atom(),
            'RET': lambda: None,  # Return leaves value on stack
            'POP': lambda: self._pop_value(),
        }
        
        handler = handlers.get(opcode)
        if handler:
            handler()
        else:
            raise ValueError(f"Unknown opcode: {opcode}")
    
    # -------------------------------------------------------------------------
    # Instruction Handlers - Each does one specific thing
    # -------------------------------------------------------------------------
    
    def _execute_conditional(self, instruction: Tuple) -> None:
        """Execute IF instruction: pop condition, run appropriate branch."""
        _, true_branch, false_branch = instruction
        condition = self.stack.pop()
        branch_code = true_branch if condition else false_branch
        result = VirtualMachine(self.environment, self.debug_enabled).execute_program(branch_code)
        self.stack.append(result)
    
    def _execute_closure_creation(self, instruction: Tuple) -> None:
        """Create a closure capturing the current environment."""
        _, code, parameters = instruction
        closure = Closure(code, self.environment, parameters)
        self.stack.append(closure)
    
    def _push_value(self, value_string: str) -> None:
        """Parse and push a literal value onto the stack."""
        value = self._parse_literal(value_string)
        self.stack.append(value)
    
    def _load_variable(self, variable_name: Symbol) -> None:
        """Load variable value from environment onto stack."""
        environment = self.environment.find_binding(variable_name)
        self.stack.append(environment[variable_name])
    
    def _store_variable(self, variable_name: Symbol) -> None:
        """Store top of stack into variable in current environment."""
        value = self.stack.pop()
        self.environment[variable_name] = value
    
    def _call_function(self, argument_count_string: Optional[str]) -> None:
        """Call function with N arguments from stack."""
        argument_count = int(argument_count_string) if argument_count_string else 0
        arguments = self._pop_arguments(argument_count)
        function = self.stack.pop()
        result = self._apply_function(function, arguments)
        self.stack.append(result)
    
    def _pop_arguments(self, count: int) -> List[Any]:
        """Pop N arguments from stack in correct order."""
        arguments = [self.stack.pop() for _ in range(count)]
        return list(reversed(arguments))
    
    def _apply_function(self, function: Any, arguments: List[Any]) -> Any:
        """Apply function (closure or built-in) to arguments."""
        if isinstance(function, Closure):
            return self._apply_closure(function, arguments)
        elif callable(function):
            return function(*arguments)
        else:
            raise ValueError(f"Cannot call non-function: {function}")
    
    def _apply_closure(self, closure: Closure, arguments: List[Any]) -> Any:
        """Execute closure with arguments bound to parameters."""
        new_environment = Environment(closure.parameters, tuple(arguments), closure.environment)
        new_vm = VirtualMachine(new_environment, self.debug_enabled)
        return new_vm.execute_program(closure.code)
    
    def _binary_arithmetic(self, operation) -> None:
        """Apply binary arithmetic operation to top two stack values."""
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        result = operation(left_operand, right_operand)
        self.stack.append(result)
    
    def _binary_comparison(self, operation) -> None:
        """Apply binary comparison to top two stack values."""
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        result = operation(left_operand, right_operand)
        self.stack.append(result)
    
    def _create_list(self, element_count_string: str) -> None:
        """Create list from N elements on stack."""
        element_count = int(element_count_string) if element_count_string else 0
        elements = [self.stack.pop() for _ in range(element_count)]
        self.stack.append(list(reversed(elements)))
    
    def _list_head(self) -> None:
        """Get first element of list (car)."""
        lst = self.stack.pop()
        self.stack.append(lst[0])
    
    def _list_tail(self) -> None:
        """Get rest of list (cdr)."""
        lst = self.stack.pop()
        self.stack.append(lst[1:])
    
    def _list_cons(self) -> None:
        """Construct list by prepending element."""
        tail = self.stack.pop()
        head = self.stack.pop()
        self.stack.append([head] + tail)
    
    def _is_null(self) -> None:
        """Check if value is empty list."""
        value = self.stack.pop()
        self.stack.append(value == [])
    
    def _is_atom(self) -> None:
        """Check if value is atomic (not a list)."""
        value = self.stack.pop()
        self.stack.append(not isinstance(value, list))
    
    def _pop_value(self) -> None:
        """Discard top of stack."""
        if self.stack:
            self.stack.pop()
    
    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    
    def _parse_literal(self, literal_string: str) -> Any:
        """Parse string literal into Python value."""
        if literal_string == 'True':
            return True
        elif literal_string == 'False':
            return False
        elif literal_string == EMPTY_LIST_MARKER:
            return []
        
        # Try parsing as number
        try:
            return int(literal_string)
        except ValueError:
            try:
                return float(literal_string)
            except ValueError:
                return literal_string
    
    def _get_final_result(self) -> Any:
        """Get final result from stack after execution."""
        if len(self.stack) == 1:
            return self.stack.pop()
        elif len(self.stack) == 0:
            return None
        else:
            raise RuntimeError(f"Expected 1 value on stack, found {len(self.stack)}")
    
    def _print_debug_info(self, program_counter: int, instruction: Instruction) -> None:
        """Print debug information during execution."""
        print(f"PC={program_counter} {instruction} | Stack={self.stack}")


# =============================================================================
# COMPILER - Translate Lisp expressions to VM instructions
# =============================================================================

class Compiler:
    """
    Compiles Lisp expressions into VM instruction sequences.
    
    Each expression type has a dedicated compilation method that returns
    a list of instructions for the VM to execute.
    """
    
    @staticmethod
    def compile_expression(expression: Expression) -> Code:
        """Main entry point: compile any expression to instructions."""
        if Compiler._is_variable_reference(expression):
            return Compiler._compile_variable(expression)
        
        elif Compiler._is_literal(expression):
            return Compiler._compile_literal(expression)
        
        elif Compiler._is_special_form(expression):
            return Compiler._compile_special_form(expression)
        
        else:
            return Compiler._compile_function_call(expression)
    
    # -------------------------------------------------------------------------
    # Type Checking Helpers
    # -------------------------------------------------------------------------
    
    @staticmethod
    def _is_variable_reference(expression: Expression) -> bool:
        """Check if expression is a variable name."""
        return isinstance(expression, Symbol)
    
    @staticmethod
    def _is_literal(expression: Expression) -> bool:
        """Check if expression is a literal value."""
        return not isinstance(expression, list)
    
    @staticmethod
    def _is_special_form(expression: Expression) -> bool:
        """Check if expression is a special form."""
        return isinstance(expression, list) and len(expression) > 0
    
    # -------------------------------------------------------------------------
    # Compilation Methods - One per expression type
    # -------------------------------------------------------------------------
    
    @staticmethod
    def _compile_variable(variable: Symbol) -> Code:
        """Compile variable reference into LOAD instruction."""
        return [f'LOAD {variable}']
    
    @staticmethod
    def _compile_literal(value: Any) -> Code:
        """Compile literal value into PUSH instruction."""
        return [f'PUSH {value}']
    
    @staticmethod
    def _compile_special_form(expression: List) -> Code:
        """Dispatch special forms to appropriate compiler."""
        form_name = expression[0]
        
        # If form_name is not a symbol, it's a function call
        if not isinstance(form_name, Symbol):
            return Compiler._compile_function_call(expression)
        
        special_forms = {
            'quote': Compiler._compile_quote,
            'q': Compiler._compile_quote,
            'if': Compiler._compile_if,
            'lambda': Compiler._compile_lambda,
            'define': Compiler._compile_define,
            'begin': Compiler._compile_begin,
            'car': Compiler._compile_car,
            'cdr': Compiler._compile_cdr,
            'cons': Compiler._compile_cons,
            'null?': Compiler._compile_null_check,
            'atom?': Compiler._compile_atom_check,
            '+': Compiler._compile_addition,
            '-': Compiler._compile_subtraction,
            '*': Compiler._compile_multiplication,
            '/': Compiler._compile_division,
            '>': Compiler._compile_greater_than,
            '<': Compiler._compile_less_than,
            '>=': Compiler._compile_greater_equal,
            '<=': Compiler._compile_less_equal,
            '=': Compiler._compile_equality,
        }
        
        compiler_function = special_forms.get(form_name)
        if compiler_function:
            return compiler_function(expression)
        else:
            return Compiler._compile_function_call(expression)
    
    @staticmethod
    def _compile_quote(expression: List) -> Code:
        """Compile quoted expression (returns expression unevaluated)."""
        if len(expression) != 2:
            raise SyntaxError(f"quote requires exactly 1 argument, got {len(expression) - 1}")
        
        _, quoted_value = expression
        
        if isinstance(quoted_value, list):
            if quoted_value == []:
                return [f'PUSH {EMPTY_LIST_MARKER}']
            else:
                # Build list at runtime
                code = []
                for element in reversed(quoted_value):
                    if isinstance(element, list):
                        code.extend(Compiler._compile_quote(['quote', element]))
                    else:
                        code.append(f'PUSH {element}')
                code.append(f'LIST {len(quoted_value)}')
                return code
        else:
            return [f'PUSH {quoted_value}']
    
    @staticmethod
    def _compile_if(expression: List) -> Code:
        """Compile conditional expression."""
        _, condition, true_branch, false_branch = expression
        
        condition_code = Compiler.compile_expression(condition)
        true_code = Compiler.compile_expression(true_branch)
        false_code = Compiler.compile_expression(false_branch)
        
        return condition_code + [('IF', true_code, false_code)]
    
    @staticmethod
    def _compile_lambda(expression: List) -> Code:
        """Compile lambda expression into closure creation."""
        _, parameters, body = expression
        
        # Normalize parameters to tuple
        if not isinstance(parameters, list):
            parameters = [parameters]
        
        body_code = Compiler.compile_expression(body) + ['RET']
        return [('CLOSURE', body_code, tuple(parameters))]
    
    @staticmethod
    def _compile_define(expression: List) -> Code:
        """Compile variable definition."""
        _, variable_name, value_expression = expression
        
        value_code = Compiler.compile_expression(value_expression)
        return value_code + [f'STORE {variable_name}', f'LOAD {variable_name}']
    
    @staticmethod
    def _compile_begin(expression: List) -> Code:
        """Compile sequence of expressions."""
        _, *body_expressions = expression
        
        code = []
        for i, expr in enumerate(body_expressions):
            code.extend(Compiler.compile_expression(expr))
            # Pop intermediate results except for last expression
            if i < len(body_expressions) - 1:
                code.append('POP')
        
        return code
    
    @staticmethod
    def _compile_car(expression: List) -> Code:
        """Compile list head operation."""
        _, list_expression = expression
        return Compiler.compile_expression(list_expression) + ['CAR']
    
    @staticmethod
    def _compile_cdr(expression: List) -> Code:
        """Compile list tail operation."""
        _, list_expression = expression
        return Compiler.compile_expression(list_expression) + ['CDR']
    
    @staticmethod
    def _compile_cons(expression: List) -> Code:
        """Compile list construction."""
        _, head_expr, tail_expr = expression
        return (Compiler.compile_expression(head_expr) + 
                Compiler.compile_expression(tail_expr) + 
                ['CONS'])
    
    @staticmethod
    def _compile_null_check(expression: List) -> Code:
        """Compile null check predicate."""
        _, value_expression = expression
        return Compiler.compile_expression(value_expression) + ['NULL?']
    
    @staticmethod
    def _compile_atom_check(expression: List) -> Code:
        """Compile atom check predicate."""
        _, value_expression = expression
        return Compiler.compile_expression(value_expression) + ['ATOM?']
    
    @staticmethod
    def _compile_addition(expression: List) -> Code:
        """Compile addition (supports multiple arguments)."""
        _, *operands = expression
        code = Compiler.compile_expression(operands[0])
        for operand in operands[1:]:
            code.extend(Compiler.compile_expression(operand))
            code.append('ADD')
        return code
    
    @staticmethod
    def _compile_subtraction(expression: List) -> Code:
        """Compile binary subtraction."""
        _, left, right = expression
        return (Compiler.compile_expression(left) + 
                Compiler.compile_expression(right) + 
                ['SUB'])
    
    @staticmethod
    def _compile_multiplication(expression: List) -> Code:
        """Compile multiplication (supports multiple arguments)."""
        _, *operands = expression
        code = Compiler.compile_expression(operands[0])
        for operand in operands[1:]:
            code.extend(Compiler.compile_expression(operand))
            code.append('MUL')
        return code
    
    @staticmethod
    def _compile_division(expression: List) -> Code:
        """Compile binary division."""
        _, numerator, denominator = expression
        return (Compiler.compile_expression(numerator) + 
                Compiler.compile_expression(denominator) + 
                ['DIV'])
    
    @staticmethod
    def _compile_greater_than(expression: List) -> Code:
        """Compile greater-than comparison."""
        _, left, right = expression
        return (Compiler.compile_expression(left) + 
                Compiler.compile_expression(right) + 
                ['GT'])
    
    @staticmethod
    def _compile_less_than(expression: List) -> Code:
        """Compile less-than comparison."""
        _, left, right = expression
        return (Compiler.compile_expression(left) + 
                Compiler.compile_expression(right) + 
                ['LT'])
    
    @staticmethod
    def _compile_greater_equal(expression: List) -> Code:
        """Compile greater-than-or-equal comparison."""
        _, left, right = expression
        return (Compiler.compile_expression(left) + 
                Compiler.compile_expression(right) + 
                ['GTE'])
    
    @staticmethod
    def _compile_less_equal(expression: List) -> Code:
        """Compile less-than-or-equal comparison."""
        _, left, right = expression
        return (Compiler.compile_expression(left) + 
                Compiler.compile_expression(right) + 
                ['LTE'])
    
    @staticmethod
    def _compile_equality(expression: List) -> Code:
        """Compile equality comparison."""
        _, left, right = expression
        return (Compiler.compile_expression(left) + 
                Compiler.compile_expression(right) + 
                ['EQ'])
    
    @staticmethod
    def _compile_function_call(expression: List) -> Code:
        """Compile general function application."""
        function_expr, *argument_exprs = expression
        
        code = Compiler.compile_expression(function_expr)
        for arg in argument_exprs:
            code.extend(Compiler.compile_expression(arg))
        code.append(f'CALL {len(argument_exprs)}')
        
        return code


# =============================================================================
# PARSER - Convert text to S-expressions
# =============================================================================

class Parser:
    """
    Parses Lisp source code into S-expressions.
    
    Converts text → tokens → nested list structure.
    """
    
    @staticmethod
    def parse(source_code: str) -> Expression:
        """Parse source code string into expression."""
        tokens = Parser._tokenize(source_code)
        return Parser._parse_tokens(tokens)
    
    @staticmethod
    def _tokenize(source_code: str) -> List[str]:
        """Convert source code into list of tokens."""
        # Remove comments
        if COMMENT_CHAR in source_code:
            source_code = source_code[:source_code.index(COMMENT_CHAR)]
        
        # Add spaces around parentheses and split
        formatted = source_code.replace(OPEN_PAREN, f' {OPEN_PAREN} ')
        formatted = formatted.replace(CLOSE_PAREN, f' {CLOSE_PAREN} ')
        return formatted.split()
    
    @staticmethod
    def _parse_tokens(tokens: List[str]) -> Expression:
        """Build expression tree from tokens."""
        if not tokens:
            raise SyntaxError('Unexpected end of input')
        
        token = tokens.pop(0)
        
        if token == OPEN_PAREN:
            return Parser._parse_list(tokens)
        elif token == CLOSE_PAREN:
            raise SyntaxError('Unexpected closing parenthesis')
        else:
            return Parser._parse_atom(token)
    
    @staticmethod
    def _parse_list(tokens: List[str]) -> List:
        """Parse list of expressions."""
        result = []
        while tokens[0] != CLOSE_PAREN:
            result.append(Parser._parse_tokens(tokens))
        tokens.pop(0)  # Remove closing paren
        return result
    
    @staticmethod
    def _parse_atom(token: str) -> Any:
        """Parse atomic value (number or symbol)."""
        try:
            return int(token)
        except ValueError:
            try:
                return float(token)
            except ValueError:
                return Symbol(token)


# =============================================================================
# PRETTY PRINTER - Convert values back to readable strings
# =============================================================================

class PrettyPrinter:
    """Converts Python values back to Lisp-readable strings."""
    
    @staticmethod
    def to_string(value: Any) -> str:
        """Convert value to readable string representation."""
        if isinstance(value, bool):
            return 'True' if value else 'False'
        elif isinstance(value, list):
            return PrettyPrinter._list_to_string(value)
        else:
            return str(value)
    
    @staticmethod
    def _list_to_string(lst: List) -> str:
        """Convert list to S-expression string."""
        elements = [PrettyPrinter.to_string(elem) for elem in lst]
        return f"({' '.join(elements)})"


# =============================================================================
# EVALUATOR - High-level evaluation interface
# =============================================================================

def evaluate_expression(expression: Expression, 
                       environment: Environment,
                       enable_debug: bool = False) -> Any:
    """
    Evaluate a Lisp expression.
    
    Compiles the expression to VM code and executes it.
    """
    instructions = Compiler.compile_expression(expression)
    vm = VirtualMachine(environment, enable_debug)
    return vm.execute_program(instructions)


# =============================================================================
# GLOBAL ENVIRONMENT - Built-in bindings
# =============================================================================

def create_global_environment() -> Environment:
    """Create environment with built-in bindings."""
    environment = Environment()
    environment.update({
        'True': True,
        'False': False,
    })
    return environment


# =============================================================================
# REPL - Read-Eval-Print Loop
# =============================================================================

def start_repl(prompt: str = DEFAULT_PROMPT, enable_debug: bool = False) -> None:
    """
    Start an interactive Read-Eval-Print Loop.
    
    Reads user input, evaluates it, and prints the result.
    """
    environment = create_global_environment()
    print("TidyVM - A Clean Stack-Based Lisp")
    print(f"Type '{DEBUG_COMMAND}' to toggle debug mode\n")
    
    while True:
        try:
            user_input = input(prompt)
            
            if not user_input.strip():
                continue
            
            if user_input.strip() == DEBUG_COMMAND:
                enable_debug = not enable_debug
                status = 'ON' if enable_debug else 'OFF'
                print(f"Debug mode: {status}")
                continue
            
            expression = Parser.parse(user_input)
            result = evaluate_expression(expression, environment, enable_debug)
            
            if result is not None:
                print(PrettyPrinter.to_string(result))
        
        except (KeyboardInterrupt, EOFError):
            print("\nExiting TidyVM\n")
            sys.exit(0)
        except Exception:
            print_error()


# =============================================================================
# FILE LOADER - Execute programs from files
# =============================================================================

def load_and_execute_file(filename: str, 
                          enable_debug: bool = False,
                          start_repl_after: bool = False) -> None:
    """
    Load and execute a TidyVM program from a file.
    
    Handles multi-line expressions by tracking parenthesis balance.
    """
    print(f"Loading and executing {filename}")
    
    with open(filename, 'r') as file:
        program_lines = file.readlines()
    
    environment = create_global_environment()
    parenthesis_balances = calculate_parenthesis_balances(program_lines)
    
    current_expression = ""
    
    for balance, line in zip(parenthesis_balances, program_lines):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith(COMMENT_CHAR):
            continue
        
        current_expression += line + " "
        
        # Execute when parentheses are balanced
        if balance == 0 and current_expression.strip():
            try:
                expression = Parser.parse(current_expression)
                result = evaluate_expression(expression, environment, enable_debug)
                
                if result is not None:
                    print(PrettyPrinter.to_string(result))
            
            except Exception:
                print_error()
                print(f"\nError in expression:\n{current_expression}")
                break
            
            current_expression = ""
    
    if start_repl_after:
        start_repl(enable_debug=enable_debug)


def calculate_parenthesis_balances(lines: List[str]) -> List[int]:
    """
    Calculate running balance of parentheses for each line.
    
    Returns list where each element is the cumulative balance at that line.
    A balance of 0 indicates complete expression.
    """
    balances = []
    total = 0
    
    for line in lines:
        open_count = line.count(OPEN_PAREN)
        close_count = line.count(CLOSE_PAREN)
        total += open_count - close_count
        balances.append(total)
    
    return balances


# =============================================================================
# ERROR HANDLING
# =============================================================================

def print_error() -> None:
    """Print error information with stack trace."""
    print("An error occurred:\n")
    traceback.print_exc()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        should_start_repl = '--repl' in sys.argv or '-i' in sys.argv
        load_and_execute_file(filename, start_repl_after=should_start_repl)
    else:
        start_repl()
