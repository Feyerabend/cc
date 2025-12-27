"""
Categorical LISP - A LISP interpreter built on category theory
Core idea: Everything is either an atom or a list (S-expressions)
Code is data (homoiconicity)
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, Generic
from dataclasses import dataclass


# LISP Data Structures (S-expressions)

class SExpr(ABC):
    """S-expression: the fundamental data type"""
    @abstractmethod
    def __repr__(self):
        pass

@dataclass
class Atom(SExpr):
    """Atomic value: number, symbol, boolean, nil"""
    value: Any
    
    def __repr__(self):
        if self.value is None:
            return "nil"
        if isinstance(self.value, bool):
            return "true" if self.value else "false"
        return str(self.value)
    
    def __eq__(self, other):
        return isinstance(other, Atom) and self.value == other.value

@dataclass
class Cons(SExpr):
    """Cons cell: (car . cdr) - the fundamental list constructor"""
    car: SExpr  # first element
    cdr: SExpr  # rest of list
    
    def __repr__(self):
        # Pretty print as (a b c) instead of (a . (b . (c . nil)))
        result = []
        current = self
        while isinstance(current, Cons):
            result.append(str(current.car))
            current = current.cdr
        
        if isinstance(current, Atom) and current.value is None:
            return f"({' '.join(result)})"
        else:
            return f"({' '.join(result)} . {current})"
    
    def __eq__(self, other):
        return (isinstance(other, Cons) and 
                self.car == other.car and 
                self.cdr == other.cdr)

# Convenient constructors
def nil():
    return Atom(None)

def symbol(name: str):
    return Atom(name)

def number(n: int | float):
    return Atom(n)

def boolean(b: bool):
    return Atom(b)

def make_list(*items):
    """Construct a proper list from items"""
    result = nil()
    for item in reversed(items):
        result = Cons(item, result)
    return result


# Environment (for variable bindings)

class Environment:
    """Environment for variable bindings"""
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent
    
    def define(self, name: str, value: SExpr):
        """Define a new binding"""
        self.bindings[name] = value
    
    def set(self, name: str, value: SExpr):
        """Set an existing binding"""
        if name in self.bindings:
            self.bindings[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise NameError(f"Undefined variable: {name}")
    
    def get(self, name: str) -> SExpr:
        """Get a binding"""
        if name in self.bindings:
            return self.bindings[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise NameError(f"Undefined variable: {name}")
    
    def extend(self):
        """Create a child environment"""
        return Environment(parent=self)


# Monad for Evaluation (handles errors and effects)

T = TypeVar('T')
U = TypeVar('U')

class EvalMonad(Generic[T]):
    """Monad for evaluation - handles success/failure"""
    def __init__(self, value: T | None, error: str | None = None):
        self.value = value
        self.error = error
        self.success = error is None
    
    @staticmethod
    def return_(value: T) -> 'EvalMonad[T]':
        """Monadic return"""
        return EvalMonad(value)
    
    @staticmethod
    def fail(error: str) -> 'EvalMonad[T]':
        """Create a failure"""
        return EvalMonad(None, error)
    
    def bind(self, f: Callable[[T], 'EvalMonad[U]']) -> 'EvalMonad[U]':
        """Monadic bind"""
        if not self.success:
            return EvalMonad(None, self.error)
        return f(self.value)
    
    def fmap(self, f: Callable[[T], U]) -> 'EvalMonad[U]':
        """Functor map"""
        if not self.success:
            return EvalMonad(None, self.error)
        return EvalMonad(f(self.value))
    
    def __repr__(self):
        if self.success:
            return f"Success({self.value})"
        return f"Error({self.error})"


# LISP Evaluator (Categorical)

class LispEvaluator:
    """LISP evaluator using categorical abstractions"""
    
    def __init__(self):
        self.global_env = Environment()
        self._define_primitives()
    
    def _define_primitives(self):
        """Define built-in functions"""
        # Arithmetic
        self.global_env.define("+", self._make_primitive(
            lambda args: number(sum(a.value for a in args))))
        self.global_env.define("-", self._make_primitive(
            lambda args: number(args[0].value - sum(a.value for a in args[1:]))))
        self.global_env.define("*", self._make_primitive(
            lambda args: number(self._product(a.value for a in args))))
        self.global_env.define("/", self._make_primitive(
            lambda args: number(args[0].value / args[1].value)))
        
        # Comparison
        self.global_env.define("=", self._make_primitive(
            lambda args: boolean(all(a.value == args[0].value for a in args))))
        self.global_env.define("<", self._make_primitive(
            lambda args: boolean(args[0].value < args[1].value)))
        self.global_env.define(">", self._make_primitive(
            lambda args: boolean(args[0].value > args[1].value)))
        
        # List operations
        self.global_env.define("car", self._make_primitive(
            lambda args: args[0].car if isinstance(args[0], Cons) else nil()))
        self.global_env.define("cdr", self._make_primitive(
            lambda args: args[0].cdr if isinstance(args[0], Cons) else nil()))
        self.global_env.define("cons", self._make_primitive(
            lambda args: Cons(args[0], args[1])))
        self.global_env.define("list", self._make_primitive(
            lambda args: make_list(*args)))
        
        # Type predicates
        self.global_env.define("atom?", self._make_primitive(
            lambda args: boolean(isinstance(args[0], Atom))))
        self.global_env.define("null?", self._make_primitive(
            lambda args: boolean(isinstance(args[0], Atom) and args[0].value is None)))
        self.global_env.define("number?", self._make_primitive(
            lambda args: boolean(isinstance(args[0], Atom) and isinstance(args[0].value, (int, float)))))
    
    def _make_primitive(self, func):
        """Wrap a Python function as a LISP primitive"""
        return Atom(('primitive', func))
    
    def _product(self, nums):
        result = 1
        for n in nums:
            result *= n
        return result
    
    def eval(self, expr: SExpr, env: Environment = None) -> EvalMonad[SExpr]:
        """
        Evaluate an S-expression (categorical evaluation)
        Uses the EvalMonad to handle errors functionally
        """
        if env is None:
            env = self.global_env
        
        # Self-evaluating atoms
        if isinstance(expr, Atom):
            if isinstance(expr.value, (int, float, bool)):
                return EvalMonad.return_(expr)
            elif expr.value is None:  # nil
                return EvalMonad.return_(expr)
            elif isinstance(expr.value, str):  # symbol - look up
                try:
                    return EvalMonad.return_(env.get(expr.value))
                except NameError as e:
                    return EvalMonad.fail(str(e))
            elif isinstance(expr.value, tuple) and expr.value[0] == 'primitive':
                return EvalMonad.return_(expr)
            elif isinstance(expr.value, tuple) and expr.value[0] == 'lambda':
                return EvalMonad.return_(expr)
            else:
                return EvalMonad.return_(expr)
        
        # Empty list
        if isinstance(expr, Cons) and isinstance(expr.car, Atom) and expr.car.value is None:
            return EvalMonad.return_(nil())
        
        # Special forms
        if isinstance(expr, Cons):
            op = expr.car
            
            # Quote
            if isinstance(op, Atom) and op.value == "quote":
                return EvalMonad.return_(expr.cdr.car if isinstance(expr.cdr, Cons) else nil())
            
            # If
            if isinstance(op, Atom) and op.value == "if":
                return self._eval_if(expr, env)
            
            # Define
            if isinstance(op, Atom) and op.value == "define":
                return self._eval_define(expr, env)
            
            # Lambda
            if isinstance(op, Atom) and op.value == "lambda":
                return self._eval_lambda(expr, env)
            
            # Begin (sequence)
            if isinstance(op, Atom) and op.value == "begin":
                return self._eval_begin(expr, env)
            
            # Function application
            return self._eval_application(expr, env)
        
        return EvalMonad.fail(f"Cannot evaluate: {expr}")
    
    def _eval_if(self, expr: Cons, env: Environment) -> EvalMonad[SExpr]:
        """Evaluate (if condition then else)"""
        args = self._list_to_python(expr.cdr)
        if len(args) < 2:
            return EvalMonad.fail("if requires at least 2 arguments")
        
        # Evaluate condition
        return self.eval(args[0], env).bind(lambda cond:
            self.eval(args[1], env) if self._is_truthy(cond) else
            self.eval(args[2], env) if len(args) > 2 else
            EvalMonad.return_(nil()))
    
    def _eval_define(self, expr: Cons, env: Environment) -> EvalMonad[SExpr]:
        """Evaluate (define name value)"""
        args = self._list_to_python(expr.cdr)
        if len(args) != 2:
            return EvalMonad.fail("define requires 2 arguments")
        
        name = args[0]
        if not isinstance(name, Atom) or not isinstance(name.value, str):
            return EvalMonad.fail("define requires a symbol")
        
        return self.eval(args[1], env).bind(lambda value:
            EvalMonad.return_(
                env.define(name.value, value) or symbol(name.value)))
    
    def _eval_lambda(self, expr: Cons, env: Environment) -> EvalMonad[SExpr]:
        """Evaluate (lambda (params) body)"""
        args = self._list_to_python(expr.cdr)
        if len(args) != 2:
            return EvalMonad.fail("lambda requires 2 arguments")
        
        params = self._list_to_python(args[0])
        body = args[1]
        
        # Create a closure
        return EvalMonad.return_(Atom(('lambda', params, body, env)))
    
    def _eval_begin(self, expr: Cons, env: Environment) -> EvalMonad[SExpr]:
        """Evaluate (begin expr1 expr2 ...)"""
        exprs = self._list_to_python(expr.cdr)
        if not exprs:
            return EvalMonad.return_(nil())
        
        result = EvalMonad.return_(nil())
        for e in exprs:
            result = self.eval(e, env)
            if not result.success:
                return result
        return result
    
    def _eval_application(self, expr: Cons, env: Environment) -> EvalMonad[SExpr]:
        """Evaluate function application"""
        # Evaluate operator
        return self.eval(expr.car, env).bind(lambda func:
            self._eval_args(expr.cdr, env).bind(lambda args:
            self._apply(func, args)))
    
    def _eval_args(self, args_expr: SExpr, env: Environment) -> EvalMonad[list[SExpr]]:
        """Evaluate all arguments"""
        if isinstance(args_expr, Atom) and args_expr.value is None:
            return EvalMonad.return_([])
        
        args = self._list_to_python(args_expr)
        results = []
        for arg in args:
            eval_result = self.eval(arg, env)
            if not eval_result.success:
                return eval_result
            results.append(eval_result.value)
        return EvalMonad.return_(results)
    
    def _apply(self, func: SExpr, args: list[SExpr]) -> EvalMonad[SExpr]:
        """Apply a function to arguments"""
        if not isinstance(func, Atom):
            return EvalMonad.fail(f"Cannot apply non-function: {func}")
        
        # Primitive function
        if isinstance(func.value, tuple) and func.value[0] == 'primitive':
            try:
                result = func.value[1](args)
                return EvalMonad.return_(result)
            except Exception as e:
                return EvalMonad.fail(str(e))
        
        # Lambda
        if isinstance(func.value, tuple) and func.value[0] == 'lambda':
            _, params, body, closure_env = func.value
            
            if len(params) != len(args):
                return EvalMonad.fail(f"Expected {len(params)} args, got {len(args)}")
            
            # Create new environment extending closure
            new_env = closure_env.extend()
            for param, arg in zip(params, args):
                if isinstance(param, Atom) and isinstance(param.value, str):
                    new_env.define(param.value, arg)
            
            return self.eval(body, new_env)
        
        return EvalMonad.fail(f"Cannot apply: {func}")
    
    def _is_truthy(self, expr: SExpr) -> bool:
        """Check if expression is truthy"""
        if isinstance(expr, Atom):
            if expr.value is None or expr.value is False:
                return False
        return True
    
    def _list_to_python(self, sexpr: SExpr) -> list[SExpr]:
        """Convert LISP list to Python list"""
        result = []
        current = sexpr
        while isinstance(current, Cons):
            result.append(current.car)
            current = current.cdr
        return result


# Simple Parser (S-expression reader)

class LispParser:
    """Parse text into S-expressions"""
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
    
    def parse(self) -> SExpr:
        """Parse one S-expression"""
        self._skip_whitespace()
        
        if self.pos >= len(self.text):
            raise SyntaxError("Unexpected end of input")
        
        char = self.text[self.pos]
        
        # List
        if char == '(':
            return self._parse_list()
        
        # Quote shorthand
        if char == "'":
            self.pos += 1
            quoted = self.parse()
            return make_list(symbol("quote"), quoted)
        
        # Atom
        return self._parse_atom()
    
    def _parse_list(self) -> SExpr:
        """Parse a list"""
        self.pos += 1  # skip '('
        self._skip_whitespace()
        
        items = []
        while self.pos < len(self.text) and self.text[self.pos] != ')':
            items.append(self.parse())
            self._skip_whitespace()
        
        if self.pos >= len(self.text):
            raise SyntaxError("Unclosed list")
        
        self.pos += 1  # skip ')'
        return make_list(*items)
    
    def _parse_atom(self) -> Atom:
        """Parse an atom"""
        start = self.pos
        
        while (self.pos < len(self.text) and 
               self.text[self.pos] not in ' \t\n\r()'):
            self.pos += 1
        
        token = self.text[start:self.pos]
        
        # Try to parse as number
        try:
            if '.' in token:
                return number(float(token))
            return number(int(token))
        except ValueError:
            pass
        
        # Special values
        if token == "true":
            return boolean(True)
        if token == "false":
            return boolean(False)
        if token == "nil":
            return nil()
        
        # Symbol
        return symbol(token)
    
    def _skip_whitespace(self):
        """Skip whitespace and comments"""
        while self.pos < len(self.text):
            if self.text[self.pos] in ' \t\n\r':
                self.pos += 1
            elif self.text[self.pos] == ';':
                # Comment until end of line
                while self.pos < len(self.text) and self.text[self.pos] != '\n':
                    self.pos += 1
            else:
                break


# REPL and Examples

def repl():
    """Read-Eval-Print Loop"""
    evaluator = LispEvaluator()
    
    print("=" * 60)
    print("CATEGORICAL LISP INTERPRETER")
    print("=" * 60)
    print("Type expressions to evaluate. Built on category theory!")
    print()
    
    test_programs = [
        # Basic arithmetic
        "(+ 1 2 3)",
        "(* 2 3 4)",
        "(- 10 3 2)",
        
        # Comparison
        "(= 5 5)",
        "(< 3 5)",
        
        # Lists
        "(list 1 2 3)",
        "(car (list 1 2 3))",
        "(cdr (list 1 2 3))",
        "(cons 0 (list 1 2 3))",
        
        # Variables
        "(define x 42)",
        "(+ x 8)",
        
        # Lambda
        "(define square (lambda (n) (* n n)))",
        "(square 7)",
        
        # Higher-order functions
        "(define make-adder (lambda (n) (lambda (x) (+ x n))))",
        "(define add5 (make-adder 5))",
        "(add5 10)",
        
        # Conditionals
        "(if (< 3 5) 100 200)",
        "(if (> 3 5) 100 200)",
        
        # Recursion (factorial)
        "(define factorial (lambda (n) (if (= n 0) 1 (* n (factorial (- n 1))))))",
        "(factorial 5)",
        
        # Map (higher-order)
        "(define map (lambda (f lst) (if (null? lst) nil (cons (f (car lst)) (map f (cdr lst))))))",
        "(map square (list 1 2 3 4))",
        
        # Quote
        "'(1 2 3)",
        "(car '(a b c))",
    ]
    
    for program in test_programs:
        print(f"λ> {program}")
        try:
            parser = LispParser(program)
            expr = parser.parse()
            result = evaluator.eval(expr)
            
            if result.success:
                print(f"   {result.value}")
            else:
                print(f"   Error: {result.error}")
        except Exception as e:
            print(f"   Parse Error: {e}")
        print()

if __name__ == "__main__":
    repl()
