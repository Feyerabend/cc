import re
from typing import Any, List, Union, Optional, Dict, Callable, Tuple
from functools import reduce as functools_reduce
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


# error handling with source location tracking for better debugging

class LispError(Exception):
    """Base exception for all Lisp errors"""
    pass

class ParseError(LispError):
    """Raised during parsing phase"""
    pass

class RuntimeError(LispError):
    """Raised during evaluation phase"""
    pass

class MacroExpansionError(LispError):
    """Raised during macro expansion"""
    pass

@dataclass
class SourceLocation:
    """Tracks source code location for better error messages"""
    line: int
    column: int
    file: Optional[str] = None
    
    def __str__(self):
        file_part = f"{self.file}:" if self.file else ""
        return f"{file_part}{self.line}:{self.column}"

class ErrorHandler:
    """Enhanced error handling with source location tracking"""
    
    @staticmethod
    def parse_error(message: str, token: Optional[str] = None, 
                   pos: Optional[int] = None, location: Optional[SourceLocation] = None) -> ParseError:
        context = ""
        if location:
            context = f" at {location}"
        elif token and pos is not None:
            context = f" at position {pos} near '{token}'"
        return ParseError(f"Parse error: {message}{context}")
    
    @staticmethod
    def runtime_error(message: str, location: Optional[SourceLocation] = None) -> RuntimeError:
        context = f" at {location}" if location else ""
        return RuntimeError(f"Runtime error: {message}{context}")
    
    @staticmethod
    def macro_error(message: str) -> MacroExpansionError:
        return MacroExpansionError(f"Macro expansion error: {message}")


# lexical scoping environment
class Environment:
    """
    Lexical scoping environment with proper closure support.
    This fixes the dynamic scoping issue mentioned in the critique.
    """
    def __init__(self, parent: Optional['Environment'] = None):
        self.bindings: Dict[str, Any] = {}
        self.parent = parent
    
    def define(self, name: str, value: Any) -> Any:
        """Define a new binding in this environment"""
        if not isinstance(name, str):
            raise ErrorHandler.runtime_error(f"Variable name must be a string, got {type(name)}")
        self.bindings[name] = value
        return value
    
    def get(self, name: str) -> Any:
        """Look up a variable, walking up the scope chain"""
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise ErrorHandler.runtime_error(f"Undefined variable: {name}")
    
    def set(self, name: str, value: Any) -> Any:
        """Set an existing variable, walking up the scope chain"""
        if name in self.bindings:
            self.bindings[name] = value
            return value
        if self.parent:
            return self.parent.set(name, value)
        raise ErrorHandler.runtime_error(f"Cannot set undefined variable: {name}")
    
    def exists(self, name: str) -> bool:
        """Check if a variable exists in the scope chain"""
        if name in self.bindings:
            return True
        if self.parent:
            return self.parent.exists(name)
        return False


# TCO, closures, and proper function representation with lexical scoping

class TailCall:
    """Represents a tail call to be optimised"""
    def __init__(self, func: Callable, args: Tuple[Any, ...]):
        self.func = func
        self.args = args

class Procedure:
    """
    Enhanced procedure with lexical closure and tail call optimisation.
    Now properly captures the defining environment (lexical scoping).
    """
    def __init__(self, params: List[str], body: Any, env: Environment, 
                 interpreter: 'Lisp', name: Optional[str] = None):
        self.params = params
        self.body = body
        self.env = env  # Captured at definition time (lexical scoping)
        self.interpreter = interpreter
        self.name = name or "<lambda>"
        
        if not isinstance(params, list):
            raise ErrorHandler.runtime_error("Function parameters must be a list")
        for param in params:
            if not isinstance(param, str):
                raise ErrorHandler.runtime_error(
                    f"Parameter names must be strings, got {type(param)}"
                )
    
    def __call__(self, *args) -> Any:
        """Execute the procedure with tail call optimization via trampoline"""
        if len(args) != len(self.params):
            raise ErrorHandler.runtime_error(
                f"Function {self.name} expects {len(self.params)} arguments, got {len(args)}"
            )
        
        # Initial call setup
        current_env = Environment(self.env)
        for param, arg in zip(self.params, args):
            current_env.define(param, arg)
        current_body = self.body
        
        # Trampoline loop - keep evaluating until we get a non-TailCall result
        while True:
            result = self.interpreter.eval(current_body, current_env, tail_context=True)
            
            # If not a tail call, we're done
            if not isinstance(result, TailCall):
                return result
            
            # Unpack the tail call - set up for next iteration
            # The TailCall contains the function and arguments
            next_func = result.func
            next_args = result.args
            
            # Only optimize if it's calling another Procedure
            if not isinstance(next_func, Procedure):
                # Call it normally and return
                return next_func(*next_args)
            
            # Check argument count
            if len(next_args) != len(next_func.params):
                raise ErrorHandler.runtime_error(
                    f"Function {next_func.name} expects {len(next_func.params)} arguments, got {len(next_args)}"
                )
            
            # Set up for next iteration of the trampoline
            current_env = Environment(next_func.env)
            for param, arg in zip(next_func.params, next_args):
                current_env.define(param, arg)
            current_body = next_func.body
    
    def __repr__(self):
        return f"<procedure {self.name}>"


# tokenizer with enhanced error messages and support for more token types (e.g. strings, comments, etc.)

class Token:
    def __init__(self, kind: str, value: str, pos: int, location: Optional[SourceLocation] = None):
        self.kind = kind
        self.value = value
        self.pos = pos
        self.location = location

class TokenFactory:
    """Enhanced tokenizer with better error messages"""
    TOKEN_REGEX = re.compile(r'''
        (?P<STRING>"(?:[^"\\]|\\.)*")                          |  # Strings with escape sequences
        (?P<COMMENT>;[^\n]*)                                   |  # Comments
        (?P<QUASIQUOTE>`)                                      |  # Quasiquote
        (?P<UNQUOTE>,@?)                                       |  # Unquote/unquote-splicing
        (?P<QUOTE>')                                           |  # Quote shorthand
        (?P<PAREN>[()[\]])                                     |  # Parentheses and brackets
        (?P<NUMBER>-?(?:\d+\.?\d*|\d*\.\d+)(?:[eE][+-]?\d+)?)  |  # Numbers with optional scientific notation
        (?P<SYMBOL>[^\s()[\]'"`;,]+)                           |  # Symbols
        (?P<WHITESPACE>\s+)                                       # Whitespace
    ''', re.VERBOSE)
    
    @classmethod
    def create_tokens(cls, text: str) -> List[Token]:
        tokens = []
        pos = 0
        line = 1
        column = 1
        
        while pos < len(text):
            match = cls.TOKEN_REGEX.match(text, pos)
            if not match:
                if text[pos] == '"':
                    end_pos = text.find('"', pos + 1)
                    if end_pos == -1:
                        location = SourceLocation(line, column)
                        raise ErrorHandler.parse_error(
                            "Unterminated string", text[pos:], pos, location
                        )
                    value = text[pos:end_pos + 1]
                    location = SourceLocation(line, column)
                    tokens.append(Token('STRING', value, pos, location))
                    pos = end_pos + 1
                    column += len(value)
                else:
                    location = SourceLocation(line, column)
                    raise ErrorHandler.parse_error(
                        "Invalid character", text[pos], pos, location
                    )
            else:
                kind = match.lastgroup
                value = match.group()
                start_pos = match.start()
                
                # Update line/column tracking
                for char in value:
                    if char == '\n':
                        line += 1
                        column = 1
                    else:
                        column += 1
                
                pos = match.end()
                
                if kind == 'WHITESPACE' or kind == 'COMMENT':
                    continue
                
                if kind == 'STRING' and not value.endswith('"'):
                    location = SourceLocation(line, column - len(value))
                    raise ErrorHandler.parse_error(
                        "Unterminated string", value, start_pos, location
                    )
                
                location = SourceLocation(line, column - len(value))
                tokens.append(Token(kind, value, start_pos, location))
        
        return tokens


# symbol and expression types with enhanced features (e.g. symbol interning, macro representation, etc.)

class Symbol:
    """Enhanced symbol with hash caching"""
    def __init__(self, name: str):
        self.name = name
        self._hash = hash(name)
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"Symbol({self.name})"
    
    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name
    
    def __hash__(self):
        return self._hash

class Macro:
    """Represents a macro (for future macro system)"""
    def __init__(self, params: List[str], body: Any, env: Environment):
        self.params = params
        self.body = body
        self.env = env
    
    def __repr__(self):
        return f"<macro>"


# parsing with enhanced error messages and support for more expression types (e.g. quasiquote, unquote, etc.)

class ExpressionFactory:
    """Enhanced expression factory with better number parsing"""
    
    @staticmethod
    def create_atom(token: Token) -> Any:
        if token.kind == 'STRING':
            content = token.value[1:-1]
            # Enhanced escape sequence handling
            escape_map = {
                '\\n': '\n',
                '\\t': '\t',
                '\\r': '\r',
                '\\"': '"',
                "\\'": "'",
                '\\\\': '\\'
            }
            for escape, char in escape_map.items():
                content = content.replace(escape, char)
            return content
        
        # Number parsing
        try:
            if '.' in token.value or 'e' in token.value.lower():
                return float(token.value)
            return int(token.value)
        except ValueError:
            pass
        
        # Boolean and nil
        if token.value.lower() == 'true':
            return True
        if token.value.lower() == 'false':
            return False
        if token.value == 'nil':
            return None
        
        # Symbol
        return Symbol(token.value)
    
    @staticmethod
    def create_list(elements: List[Any]) -> List[Any]:
        return elements

class Parser:
    """Enhanced parser with better error messages"""
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.expr_factory = ExpressionFactory()
    
    def parse(self) -> Any:
        if self.pos >= len(self.tokens):
            raise ErrorHandler.parse_error("Unexpected end of input")
        return self._parse_expression()
    
    def _parse_expression(self) -> Any:
        if self.pos >= len(self.tokens):
            raise ErrorHandler.parse_error("Unexpected end of input")
        
        token = self.tokens[self.pos]
        
        if token.value == '(':
            return self._parse_list()
        elif token.value == '[':
            return self._parse_list(end_token=']')
        elif token.value == "'":
            self.pos += 1
            quoted_expr = self._parse_expression()
            return ['quote', quoted_expr]
        elif token.value == '`':
            # Quasiquote support (for macro system)
            self.pos += 1
            quoted_expr = self._parse_expression()
            return ['quasiquote', quoted_expr]
        elif token.value == ',':
            # Unquote
            self.pos += 1
            unquoted = self._parse_expression()
            return ['unquote', unquoted]
        elif token.value == ',@':
            # Unquote-splicing
            self.pos += 1
            unquoted = self._parse_expression()
            return ['unquote-splicing', unquoted]
        elif token.value in (')', ']'):
            raise ErrorHandler.parse_error(
                f"Unexpected closing '{token.value}'", 
                token.value, 
                self.pos,
                token.location
            )
        else:
            self.pos += 1
            return self.expr_factory.create_atom(token)
    
    def _parse_list(self, end_token: str = ')') -> List[Any]:
        self.pos += 1
        elements = []
        while self.pos < len(self.tokens) and self.tokens[self.pos].value != end_token:
            elements.append(self._parse_expression())
        
        if self.pos >= len(self.tokens):
            expected = ']' if end_token == ']' else ')'
            raise ErrorHandler.parse_error(f"Missing closing '{expected}'")
        
        self.pos += 1
        return self.expr_factory.create_list(elements)


# special form evaluators with support for tail call optimisation and macro expansion

class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        pass

class QuoteEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) != 2:
            raise ErrorHandler.runtime_error("quote requires exactly 1 argument")
        return expr[1]

class QuasiquoteEvaluator(Evaluator):
    """Quasiquote evaluator (foundation for macros)"""
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) != 2:
            raise ErrorHandler.runtime_error("quasiquote requires exactly 1 argument")
        return self._process_quasiquote(expr[1], env, interpreter)
    
    def _process_quasiquote(self, expr: Any, env: Environment, interpreter: 'Lisp') -> Any:
        if not isinstance(expr, list):
            return expr
        
        if len(expr) > 0 and expr[0] == 'unquote':
            if len(expr) != 2:
                raise ErrorHandler.runtime_error("unquote requires exactly 1 argument")
            return interpreter.eval(expr[1], env)
        
        result = []
        for item in expr:
            if isinstance(item, list) and len(item) > 0 and item[0] == 'unquote-splicing':
                if len(item) != 2:
                    raise ErrorHandler.runtime_error("unquote-splicing requires exactly 1 argument")
                spliced = interpreter.eval(item[1], env)
                if not isinstance(spliced, list):
                    raise ErrorHandler.runtime_error("unquote-splicing requires a list")
                result.extend(spliced)
            else:
                result.append(self._process_quasiquote(item, env, interpreter))
        
        return result

class IfEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) < 3 or len(expr) > 4:
            raise ErrorHandler.runtime_error("if requires 2 or 3 arguments")
        
        # Condition is NEVER in tail position
        condition = interpreter.eval(expr[1], env, tail_context=False)
        # Then/else branches ARE in tail position if the if itself is
        if interpreter._is_truthy(condition):
            return interpreter.eval(expr[2], env, tail_context=tail_context)
        elif len(expr) == 4:
            return interpreter.eval(expr[3], env, tail_context=tail_context)
        return None

class CondEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) < 2:
            raise ErrorHandler.runtime_error("cond requires at least 1 clause")
        
        for clause in expr[1:]:
            if not isinstance(clause, list) or len(clause) < 2:
                raise ErrorHandler.runtime_error("cond clause must be a list with at least 2 elements")
            
            condition = clause[0]
            if isinstance(condition, Symbol) and condition.name == 'else':
                return interpreter._eval_begin(clause[1:], env)
            
            if interpreter._is_truthy(interpreter.eval(condition, env)):
                return interpreter._eval_begin(clause[1:], env)
        
        return None

class AndEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) == 1:
            return True
        
        result = True
        for arg in expr[1:]:
            result = interpreter.eval(arg, env)
            if not interpreter._is_truthy(result):
                return False
        return result

class OrEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) == 1:
            return False
        
        for arg in expr[1:]:
            result = interpreter.eval(arg, env)
            if interpreter._is_truthy(result):
                return result
        return False

class DefineEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) < 3:
            raise ErrorHandler.runtime_error("define requires at least 2 arguments")
        
        name = expr[1]
        
        # Function definition shorthand: (define (f x) body)
        if isinstance(name, list):
            if len(name) < 1:
                raise ErrorHandler.runtime_error("define: function name required")
            
            func_name = name[0]
            if not isinstance(func_name, Symbol):
                raise ErrorHandler.runtime_error("define: function name must be a symbol")
            
            params = [p.name if isinstance(p, Symbol) else str(p) for p in name[1:]]
            body = expr[2] if len(expr) == 3 else ['begin'] + expr[2:]
            
            proc = Procedure(params, body, env, interpreter, func_name.name)
            return env.define(func_name.name, proc)
        
        # Variable definition: (define x value)
        if not isinstance(name, Symbol):
            raise ErrorHandler.runtime_error("define: name must be a symbol")
        
        value = interpreter.eval(expr[2], env)
        return env.define(name.name, value)

class SetEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) != 3:
            raise ErrorHandler.runtime_error("set! requires exactly 2 arguments")
        
        name = expr[1]
        if not isinstance(name, Symbol):
            raise ErrorHandler.runtime_error("set!: name must be a symbol")
        
        value = interpreter.eval(expr[2], env)
        return env.set(name.name, value)

class LambdaEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) < 3:
            raise ErrorHandler.runtime_error("lambda requires at least 2 arguments")
        
        params_expr = expr[1]
        if not isinstance(params_expr, list):
            raise ErrorHandler.runtime_error("lambda: parameters must be a list")
        
        params = []
        for p in params_expr:
            if isinstance(p, Symbol):
                params.append(p.name)
            elif isinstance(p, str):
                params.append(p)
            else:
                raise ErrorHandler.runtime_error(f"lambda: parameter must be a symbol, got {type(p)}")
        
        body = expr[2] if len(expr) == 3 else ['begin'] + expr[2:]
        return Procedure(params, body, env, interpreter)

class LetEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) < 3:
            raise ErrorHandler.runtime_error("let requires at least 2 arguments")
        
        bindings = expr[1]
        if not isinstance(bindings, list):
            raise ErrorHandler.runtime_error("let: bindings must be a list")
        
        # Create new environment for let bindings
        let_env = Environment(env)
        
        for binding in bindings:
            if not isinstance(binding, list) or len(binding) != 2:
                raise ErrorHandler.runtime_error("let: each binding must be a list of 2 elements")
            
            name = binding[0]
            if not isinstance(name, Symbol):
                raise ErrorHandler.runtime_error("let: binding name must be a symbol")
            
            value = interpreter.eval(binding[1], env)
            let_env.define(name.name, value)
        
        # Evaluate body in the new environment
        return interpreter._eval_begin(expr[2:], let_env)

class BeginEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) < 2:
            return None
        return interpreter._eval_begin(expr[1:], env, tail_context=tail_context)

class WhileEvaluator(Evaluator):
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) < 3:
            raise ErrorHandler.runtime_error("while requires at least 2 arguments")
        
        condition = expr[1]
        body = expr[2:]
        
        result = None
        while interpreter._is_truthy(interpreter.eval(condition, env)):
            result = interpreter._eval_begin(body, env)
        
        return result

class DefmacroEvaluator(Evaluator):
    """Define macro evaluator (foundation for macro system)"""
    def evaluate(self, expr: List[Any], env: Environment, interpreter: 'Lisp', tail_context: bool = False) -> Any:
        if len(expr) < 3:
            raise ErrorHandler.runtime_error("defmacro requires at least 2 arguments")
        
        name = expr[1]
        if not isinstance(name, Symbol):
            raise ErrorHandler.runtime_error("defmacro: name must be a symbol")
        
        params_expr = expr[2]
        if not isinstance(params_expr, list):
            raise ErrorHandler.runtime_error("defmacro: parameters must be a list")
        
        params = [p.name if isinstance(p, Symbol) else str(p) for p in params_expr]
        body = expr[3] if len(expr) == 4 else ['begin'] + expr[3:]
        
        macro = Macro(params, body, env)
        return env.define(name.name, macro)


# built-in functions with enhanced error handling and support for more operations (e.g. list manipulation, comparison, etc.)

class BuiltInCommand(ABC):
    @abstractmethod
    def execute(self, *args: Any) -> Any:
        pass

# Arithmetic operations
class AddCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if not args:
            return 0
        return sum(args)

class SubtractCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) == 0:
            raise ErrorHandler.runtime_error("- requires at least 1 argument")
        if len(args) == 1:
            return -args[0]
        result = args[0]
        for arg in args[1:]:
            result -= arg
        return result

class MultiplyCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if not args:
            return 1
        result = args[0]
        for arg in args[1:]:
            result *= arg
        return result

class DivideCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) == 0:
            raise ErrorHandler.runtime_error("/ requires at least 1 argument")
        if len(args) == 1:
            return 1.0 / args[0]
        result = args[0]
        for arg in args[1:]:
            if arg == 0:
                raise ErrorHandler.runtime_error("Division by zero")
            result /= arg
        return float(result)

class ModCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 2:
            raise ErrorHandler.runtime_error("mod requires exactly 2 arguments")
        return args[0] % args[1]

class AbsCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("abs requires exactly 1 argument")
        return abs(args[0])

class MaxCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if not args:
            raise ErrorHandler.runtime_error("max requires at least 1 argument")
        return max(args)

class MinCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if not args:
            raise ErrorHandler.runtime_error("min requires at least 1 argument")
        return min(args)

# Comparison operations
class EqualCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) < 2:
            return True
        first = args[0]
        return all(arg == first for arg in args[1:])

class NotEqualCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 2:
            raise ErrorHandler.runtime_error("!= requires exactly 2 arguments")
        return args[0] != args[1]

class LessCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) < 2:
            return True
        return all(args[i] < args[i + 1] for i in range(len(args) - 1))

class GreaterCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) < 2:
            return True
        return all(args[i] > args[i + 1] for i in range(len(args) - 1))

class LessEqualCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) < 2:
            return True
        return all(args[i] <= args[i + 1] for i in range(len(args) - 1))

class GreaterEqualCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) < 2:
            return True
        return all(args[i] >= args[i + 1] for i in range(len(args) - 1))

class NotCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("not requires exactly 1 argument")
        return not args[0]

# List operations
class ConsCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 2:
            raise ErrorHandler.runtime_error("cons requires exactly 2 arguments")
        if not isinstance(args[1], list):
            raise ErrorHandler.runtime_error("cons: second argument must be a list")
        return [args[0]] + args[1]

class CarCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("car requires exactly 1 argument")
        if not isinstance(args[0], list) or not args[0]:
            raise ErrorHandler.runtime_error("car: argument must be a non-empty list")
        return args[0][0]

class CdrCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("cdr requires exactly 1 argument")
        if not isinstance(args[0], list) or not args[0]:
            raise ErrorHandler.runtime_error("cdr: argument must be a non-empty list")
        return args[0][1:]

class ListCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        return list(args)

class AppendCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        result = []
        for arg in args:
            if not isinstance(arg, list):
                raise ErrorHandler.runtime_error("append: all arguments must be lists")
            result.extend(arg)
        return result

class LengthCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("length requires exactly 1 argument")
        if not isinstance(args[0], list):
            raise ErrorHandler.runtime_error("length: argument must be a list")
        return len(args[0])

class ReverseCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("reverse requires exactly 1 argument")
        if not isinstance(args[0], list):
            raise ErrorHandler.runtime_error("reverse: argument must be a list")
        return list(reversed(args[0]))

class NullCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("null? requires exactly 1 argument")
        return args[0] is None or (isinstance(args[0], list) and len(args[0]) == 0)

class EmptyCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("empty? requires exactly 1 argument")
        return isinstance(args[0], list) and len(args[0]) == 0

# Type predicates
class NumberCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("number? requires exactly 1 argument")
        return isinstance(args[0], (int, float))

class StringCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("string? requires exactly 1 argument")
        return isinstance(args[0], str)

class SymbolCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("symbol? requires exactly 1 argument")
        return isinstance(args[0], Symbol)

class ListPredCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("list? requires exactly 1 argument")
        return isinstance(args[0], list)

class ProcedureCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 1:
            raise ErrorHandler.runtime_error("procedure? requires exactly 1 argument")
        return isinstance(args[0], (Procedure, BuiltInCommand)) or callable(args[0])

# Higher-order functions
class MapCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 2:
            raise ErrorHandler.runtime_error("map requires exactly 2 arguments")
        func, lst = args
        if not isinstance(lst, list):
            raise ErrorHandler.runtime_error("map: second argument must be a list")
        if not callable(func):
            raise ErrorHandler.runtime_error("map: first argument must be a function")
        return [func(item) for item in lst]

class FilterCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 2:
            raise ErrorHandler.runtime_error("filter requires exactly 2 arguments")
        func, lst = args
        if not isinstance(lst, list):
            raise ErrorHandler.runtime_error("filter: second argument must be a list")
        if not callable(func):
            raise ErrorHandler.runtime_error("filter: first argument must be a function")
        return [item for item in lst if func(item)]

class ReduceCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) < 2 or len(args) > 3:
            raise ErrorHandler.runtime_error("reduce requires 2 or 3 arguments")
        func = args[0]
        lst = args[1]
        if not isinstance(lst, list):
            raise ErrorHandler.runtime_error("reduce: second argument must be a list")
        if not callable(func):
            raise ErrorHandler.runtime_error("reduce: first argument must be a function")
        if len(args) == 3:
            return functools_reduce(func, lst, args[2])
        return functools_reduce(func, lst)

class ApplyCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        if len(args) != 2:
            raise ErrorHandler.runtime_error("apply requires exactly 2 arguments")
        func, lst = args
        if not isinstance(lst, list):
            raise ErrorHandler.runtime_error("apply: second argument must be a list")
        if not callable(func):
            raise ErrorHandler.runtime_error("apply: first argument must be a function")
        return func(*lst)

# I/O operations
class PrintCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        formatted_args = [arg.name if isinstance(arg, Symbol) else arg for arg in args]
        print(*formatted_args)
        return None

class DisplayCommand(BuiltInCommand):
    def execute(self, *args: Any) -> Any:
        formatted_args = [arg.name if isinstance(arg, Symbol) else arg for arg in args]
        print(*formatted_args, end='')
        return None


# result formatting with support for more types and better readability (e.g. pretty-printing lists, etc.)

class ResultFormatter:
    """Format evaluation results for display"""
    def format(self, result: Any) -> str:
        return self.visit(result)
    
    def visit(self, result: Any) -> str:
        if isinstance(result, str):
            return f'"{result}"'
        elif isinstance(result, Symbol):
            return result.name
        elif isinstance(result, Procedure):
            return repr(result)
        elif isinstance(result, Macro):
            return repr(result)
        elif isinstance(result, list):
            formatted_items = [self.visit(item) for item in result]
            return f"({' '.join(formatted_items)})"
        elif result is None:
            return "nil"
        elif isinstance(result, bool):
            return "true" if result else "false"
        else:
            return str(result)



class Lisp:
    """
    Lisp interpreter with:
    - Lexical scoping
    - Tail call optimisation TCO
    - Error handling with source locations
    - Foundation for macro system (quasiquote, defmacro)
    - Standard library
    """
    def __init__(self):
        self.global_env = Environment()
        self.special_forms: Dict[str, Evaluator] = {}
        self.formatter = ResultFormatter()
        self._setup_special_forms()
        self._setup_builtins()
    
    def _setup_special_forms(self):
        """Register all special forms"""
        self.special_forms = {
            'quote': QuoteEvaluator(),
            'quasiquote': QuasiquoteEvaluator(),
            'if': IfEvaluator(),
            'cond': CondEvaluator(),
            'and': AndEvaluator(),
            'or': OrEvaluator(),
            'define': DefineEvaluator(),
            'set!': SetEvaluator(),
            'lambda': LambdaEvaluator(),
            'let': LetEvaluator(),
            'begin': BeginEvaluator(),
            'while': WhileEvaluator(),
            'defmacro': DefmacroEvaluator(),
        }
    
    def _setup_builtins(self):
        """Register all built-in functions"""
        env = self.global_env
        
        # Arithmetic
        env.define('+', AddCommand())
        env.define('-', SubtractCommand())
        env.define('*', MultiplyCommand())
        env.define('/', DivideCommand())
        env.define('mod', ModCommand())
        env.define('abs', AbsCommand())
        env.define('max', MaxCommand())
        env.define('min', MinCommand())
        
        # Comparison
        env.define('=', EqualCommand())
        env.define('==', EqualCommand())
        env.define('!=', NotEqualCommand())
        env.define('<', LessCommand())
        env.define('>', GreaterCommand())
        env.define('<=', LessEqualCommand())
        env.define('>=', GreaterEqualCommand())
        env.define('not', NotCommand())
        
        # List operations
        env.define('cons', ConsCommand())
        env.define('car', CarCommand())
        env.define('cdr', CdrCommand())
        env.define('list', ListCommand())
        env.define('append', AppendCommand())
        env.define('length', LengthCommand())
        env.define('reverse', ReverseCommand())
        env.define('null?', NullCommand())
        env.define('empty?', EmptyCommand())
        
        # Type predicates
        env.define('number?', NumberCommand())
        env.define('string?', StringCommand())
        env.define('symbol?', SymbolCommand())
        env.define('list?', ListPredCommand())
        env.define('procedure?', ProcedureCommand())
        
        # Higher-order functions
        env.define('map', MapCommand())
        env.define('filter', FilterCommand())
        env.define('reduce', ReduceCommand())
        env.define('apply', ApplyCommand())
        
        # I/O
        env.define('print', PrintCommand())
        env.define('display', DisplayCommand())
        
        # Constants
        env.define('true', True)
        env.define('false', False)
        env.define('nil', None)
    
    def parse(self, text: str) -> Any:
        """Parse text into an expression"""
        try:
            tokens = TokenFactory.create_tokens(text)
            if not tokens:
                raise ErrorHandler.parse_error("Empty input")
            parser = Parser(tokens)
            return parser.parse()
        except (ParseError, LispError) as e:
            raise
        except Exception as e:
            raise ErrorHandler.parse_error(str(e))
    
    def parse_all(self, text: str) -> Any:
        """Parse all top-level expressions from text, wrapping multiple expressions in begin"""
        try:
            tokens = TokenFactory.create_tokens(text)
            if not tokens:
                raise ErrorHandler.parse_error("Empty input")
            
            parser = Parser(tokens)
            expressions = []
            
            # Parse all expressions until we run out of tokens
            while parser.pos < len(parser.tokens):
                # Skip any unexpected closing parens (for compatibility)
                while (parser.pos < len(parser.tokens) and 
                       parser.tokens[parser.pos].value in (')', ']')):
                    parser.pos += 1
                
                # If we've consumed all tokens, break
                if parser.pos >= len(parser.tokens):
                    break
                    
                expressions.append(parser.parse())
            
            # If only one expression, return it directly
            if len(expressions) == 1:
                return expressions[0]
            
            # Multiple expressions: wrap in begin
            return [Symbol('begin')] + expressions
            
        except (ParseError, LispError) as e:
            raise
        except Exception as e:
            raise ErrorHandler.parse_error(str(e))
    
    def eval(self, expr: Any, env: Optional[Environment] = None, tail_context: bool = False) -> Any:
        """Evaluate an expression in the given environment"""
        if env is None:
            env = self.global_env
        try:
            return self._eval_expr(expr, env, tail_context)
        except (RuntimeError, LispError):
            raise
        except Exception as e:
            raise ErrorHandler.runtime_error(str(e))
    
    def _eval_expr(self, expr: Any, env: Environment, tail_context: bool = False) -> Any:
        """Internal evaluation implementation"""
        # Self-evaluating expressions
        if isinstance(expr, (int, float, str, bool)) or expr is None:
            return expr
        
        # Symbol lookup
        if isinstance(expr, Symbol):
            return env.get(expr.name)
        
        # Handle string as symbol for compatibility
        if isinstance(expr, str):
            return env.get(expr)
        
        # List evaluation
        if isinstance(expr, list):
            return self._eval_list(expr, env, tail_context)
        
        raise ErrorHandler.runtime_error(
            f"Cannot evaluate expression of type {type(expr)}: {expr}"
        )
    
    def _eval_list(self, expr: List[Any], env: Environment, tail_context: bool = False) -> Any:
        """Evaluate a list expression (function call or special form)"""
        if not expr:
            return []
        
        first = expr[0]
        
        # Check for special forms
        first_name = first.name if isinstance(first, Symbol) else str(first) if isinstance(first, str) else None
        
        if first_name in self.special_forms:
            return self.special_forms[first_name].evaluate(expr, env, self, tail_context)
        
        # Evaluate function and arguments
        func = self.eval(first, env, tail_context=False)
        
        # Check if it's a macro and expand it
        if isinstance(func, Macro):
            return self._expand_and_eval_macro(func, expr[1:], env)
        
        # Evaluate arguments
        args = [self.eval(arg, env, tail_context=False) for arg in expr[1:]]
        
        # Apply function
        if isinstance(func, BuiltInCommand):
            return func.execute(*args)
        
        if callable(func):
            # KEY FIX: If in tail position and calling a Procedure, return TailCall
            if tail_context and isinstance(func, Procedure):
                return TailCall(func, tuple(args))
            return func(*args)
        
        raise ErrorHandler.runtime_error(
            f"'{first}' is not a function: {type(func)} {func}"
        )
    
    def _expand_and_eval_macro(self, macro: Macro, args: List[Any], env: Environment) -> Any:
        """Expand and evaluate a macro call"""
        if len(args) != len(macro.params):
            raise ErrorHandler.macro_error(
                f"Macro expects {len(macro.params)} arguments, got {len(args)}"
            )
        
        # Create environment for macro expansion
        macro_env = Environment(macro.env)
        for param, arg in zip(macro.params, args):
            macro_env.define(param, arg)
        
        # Expand macro
        expanded = self.eval(macro.body, macro_env)
        
        # Evaluate the expansion
        return self.eval(expanded, env)
    
    def _eval_begin(self, exprs: List[Any], env: Environment, tail_context: bool = False) -> Any:
        """Evaluate a sequence of expressions, returning the last result"""
        if not exprs:
            return None
        result = None
        # All expressions except the last are NOT in tail position
        for i, expr in enumerate(exprs):
            is_last = (i == len(exprs) - 1)
            result = self.eval(expr, env, tail_context=(tail_context and is_last))
        return result
    
    def _is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy (not False or None)"""
        return value is not False and value is not None
    
    def run(self, source: str) -> Any:
        """Parse and evaluate a source string"""
        try:
            expr = self.parse_all(source)  # Use parse_all to handle multiple expressions
            return self.eval(expr)
        except (ParseError, RuntimeError, LispError) as e:
            raise e
        except Exception as e:
            raise ErrorHandler.runtime_error(f"Unexpected error: {e}")


class LispREPL:
    """
    REPL with:
    - Multiline input support
    - Error messages
    - Command history
    """
    def __init__(self):
        self.lisp = Lisp()
        self.multiline_buffer = []
        self.paren_count = 0
    
    def start(self):
        """Start the REPL"""
        print("Lisp REPL v2.0")
        print("Type 'exit', 'quit', or press Ctrl+C to quit")
        print("Type '(help)' for built-in functions")
        print()
        
        while True:
            try:
                prompt = ".. " if self.multiline_buffer else ">> "
                line = input(prompt).strip()
                
                if line.lower() in ("exit", "quit"):
                    break
                
                if not line:
                    continue
                
                # Handle help command
                if line == "(help)":
                    self._print_help()
                    continue
                
                self.multiline_buffer.append(line)
                self.paren_count += line.count('(') + line.count('[')
                self.paren_count -= line.count(')') + line.count(']')
                
                if self.paren_count == 0:
                    source = ' '.join(self.multiline_buffer)
                    self.multiline_buffer = []
                    
                    try:
                        result = self.lisp.run(source)
                        if result is not None:
                            print(self.lisp.formatter.format(result))
                    except (ParseError, RuntimeError, LispError) as e:
                        print(f"Error: {e}")
                
                elif self.paren_count < 0:
                    print("Error: Unmatched closing parenthesis")
                    self.multiline_buffer = []
                    self.paren_count = 0
            
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
    
    def _print_help(self):
        """Print help message"""
        print("""
Available built-in functions:

Arithmetic:    +, -, *, /, mod, abs, max, min
Comparison:    =, ==, !=, <, >, <=, >=, not
Lists:         cons, car, cdr, list, append, length, reverse, null?, empty?
Type checks:   number?, string?, symbol?, list?, procedure?
Higher-order:  map, filter, reduce, apply
I/O:           print, display
Special forms: quote, if, cond, and, or, define, set!, lambda, let, begin, while
Macros:        defmacro, quasiquote, unquote

Example:
  (define (factorial n)
    (if (<= n 1)
        1
        (* n (factorial (- n 1)))))
  
  (factorial 5)  ; => 120
        """)



if __name__ == '__main__':
    repl = LispREPL()
    repl.start()
