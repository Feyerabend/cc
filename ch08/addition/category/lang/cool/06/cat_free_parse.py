"""
COOL with Free Monads + Integrated Parser
==========================================
The ultimate integration:
- Parser combinators as Free Monads
- Parse COOL source into Free Monad programs
- Execute parsed programs with multiple interpreters
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass, field
import re
from functools import reduce



# FREE MONAD CORE (from cat_free.py)


@dataclass
class Value(ABC):
    """Base runtime value"""
    pass


@dataclass
class IntValue(Value):
    value: int
    def __str__(self): return str(self.value)


@dataclass
class StringValue(Value):
    value: str
    def __str__(self): return f'"{self.value}"'


@dataclass
class BoolValue(Value):
    value: bool
    def __str__(self): return str(self.value).lower()


@dataclass
class UnitValue(Value):
    def __str__(self): return "()"


class Free(ABC):
    """Free monad"""
    
    @abstractmethod
    def bind(self, f: Callable[[Value], 'Free']) -> 'Free':
        pass
    
    @abstractmethod
    def interpret(self, interpreter: 'Interpreter') -> Value:
        pass


@dataclass
class Pure(Free):
    """Pure value"""
    value: Value
    
    def bind(self, f: Callable[[Value], Free]) -> Free:
        return f(self.value)
    
    def interpret(self, interpreter: 'Interpreter') -> Value:
        return self.value
    
    def __str__(self):
        return f"Pure({self.value})"


@dataclass
class Impure(Free):
    """Impure computation"""
    functor: 'FunctorF'
    
    def bind(self, f: Callable[[Value], Free]) -> Free:
        return Impure(self.functor.fmap_free(lambda free: free.bind(f)))
    
    def interpret(self, interpreter: 'Interpreter') -> Value:
        return interpreter.run(self.functor)
    
    def __str__(self):
        return f"Impure({self.functor})"


class FunctorF(ABC):
    """Base functor for Free monad"""
    
    @abstractmethod
    def fmap_free(self, f: Callable[[Free], Free]) -> 'FunctorF':
        pass


class Interpreter(ABC):
    """Interpreter for a functor"""
    
    @abstractmethod
    def run(self, functor: FunctorF) -> Value:
        pass



# PARSER COMBINATORS (Enhanced from cat_parse.py)


T = TypeVar('T')
U = TypeVar('U')


@dataclass
class ParseResult(ABC):
    """Parse result - using ADT pattern"""
    pass


@dataclass 
class ParseSuccess(ParseResult):
    value: Any
    remaining: str
    
    def is_ok(self) -> bool: return True
    def is_err(self) -> bool: return False


@dataclass
class ParseFailure(ParseResult):
    error: str
    remaining: str
    
    def is_ok(self) -> bool: return False
    def is_err(self) -> bool: return True


class Parser:
    """Parser as a functor"""
    
    def __init__(self, parse_fn: Callable[[str], ParseResult]):
        self.parse_fn = parse_fn
    
    def parse(self, input_str: str) -> ParseResult:
        return self.parse_fn(input_str)
    
    def fmap(self, f: Callable[[Any], Any]) -> 'Parser':
        def new(s):
            res = self.parse(s)
            if isinstance(res, ParseSuccess):
                return ParseSuccess(f(res.value), res.remaining)
            return res
        return Parser(new)
    
    def __rshift__(self, other):
        if callable(other):
            return self.fmap(other)
        else:
            return self.bind(lambda _: other)
    
    def __lshift__(self, other: 'Parser') -> 'Parser':
        return self.bind(lambda x: other.fmap(lambda _: x))
    
    def bind(self, f: Callable[[Any], 'Parser']) -> 'Parser':
        def new(s):
            res = self.parse(s)
            if isinstance(res, ParseFailure):
                return res
            return f(res.value).parse(res.remaining)
        return Parser(new)
    
    def or_else(self, other: 'Parser') -> 'Parser':
        def new(s):
            res = self.parse(s)
            if isinstance(res, ParseSuccess):
                return res
            return other.parse(s)
        return Parser(new)
    
    def __or__(self, other: 'Parser') -> 'Parser':
        return self.or_else(other)
    
    def many(self) -> 'Parser':
        def new(s):
            results = []
            rem = s
            while True:
                res = self.parse(rem)
                if isinstance(res, ParseFailure):
                    break
                results.append(res.value)
                rem = res.remaining
            return ParseSuccess(results, rem)
        return Parser(new)
    
    def optional(self) -> 'Parser':
        return self.fmap(lambda x: x) | pure_parser(None)
    
    def sep_by(self, sep: 'Parser') -> 'Parser':
        return self.bind(lambda x: (sep >> self).many().fmap(lambda xs: [x] + xs)) | pure_parser([])


def pure_parser(v: Any) -> Parser:
    return Parser(lambda s: ParseSuccess(v, s))


def string(lit: str) -> Parser:
    def p(s):
        if s.startswith(lit):
            return ParseSuccess(lit, s[len(lit):])
        return ParseFailure(f"Expected '{lit}'", s)
    return Parser(p)


def regex(pattern: str) -> Parser:
    comp = re.compile(pattern)
    def p(s):
        m = comp.match(s)
        if m:
            return ParseSuccess(m.group(0), s[len(m.group(0)):])
        return ParseFailure(f"Pattern '{pattern}'", s)
    return Parser(p)


def whitespace() -> Parser:
    return regex(r'\s*')


def token(p: Parser) -> Parser:
    return p << whitespace()


def keyword(kw: str) -> Parser:
    return token(string(kw))


def symbol(sym: str) -> Parser:
    return token(string(sym))


class Delayed:
    """Delayed parser for mutual recursion"""
    def __init__(self, thunk: Callable[[], Parser]):
        self.thunk = thunk
        self._parser: Optional[Parser] = None
    
    def get(self) -> Parser:
        if self._parser is None:
            self._parser = self.thunk()
        return self._parser
    
    def parse(self, s: str) -> ParseResult:
        return self.get().parse(s)
    
    def many(self) -> Parser:
        return Parser(lambda s: self.get().many().parse(s))
    
    def optional(self) -> Parser:
        return Parser(lambda s: self.get().optional().parse(s))
    
    def __lshift__(self, other: Parser):
        return Parser(lambda s: self.get().__lshift__(other).parse(s))
    
    def __rshift__(self, other):
        if callable(other):
            return self.get().__rshift__(other)
        return Parser(lambda s: self.get().__rshift__(other).parse(s))
    
    def bind(self, f): return self.get().bind(f)
    def __or__(self, other): return self.get().__or__(other)
    def sep_by(self, sep): return self.get().sep_by(sep)
    def fmap(self, f): return self.get().fmap(f)



# FREE MONAD AST (parsed programs become Free Monads!)


# Console operations
@dataclass
class PrintLineF(FunctorF):
    """Print operation"""
    message: str
    next_computation: Free
    
    def fmap_free(self, f: Callable[[Free], Free]) -> FunctorF:
        return PrintLineF(self.message, f(self.next_computation))
    
    def __str__(self):
        return f"Print({self.message})"


@dataclass
class ReadLineF(FunctorF):
    """Read operation"""
    continuation: Callable[[str], Free]
    
    def fmap_free(self, f: Callable[[Free], Free]) -> FunctorF:
        return ReadLineF(lambda s: f(self.continuation(s)))
    
    def __str__(self):
        return "ReadLine"


# Arithmetic operations
@dataclass
class BinaryOpF(FunctorF):
    """Binary operation"""
    op: str
    left: Free
    right: Free
    continuation: Callable[[Value], Free]
    
    def fmap_free(self, f: Callable[[Free], Free]) -> FunctorF:
        return BinaryOpF(
            self.op,
            self.left,
            self.right,
            lambda v: f(self.continuation(v))
        )
    
    def __str__(self):
        return f"BinOp({self.op})"


# Variable operations
@dataclass
class VarDeclF(FunctorF):
    """Variable declaration"""
    name: str
    value: Free
    next_computation: Free
    
    def fmap_free(self, f: Callable[[Free], Free]) -> FunctorF:
        return VarDeclF(self.name, self.value, f(self.next_computation))
    
    def __str__(self):
        return f"VarDecl({self.name})"


@dataclass
class VarGetF(FunctorF):
    """Variable access"""
    name: str
    continuation: Callable[[Value], Free]
    
    def fmap_free(self, f: Callable[[Free], Free]) -> FunctorF:
        return VarGetF(self.name, lambda v: f(self.continuation(v)))
    
    def __str__(self):
        return f"VarGet({self.name})"


# Smart constructors
def print_free(msg: str) -> Free:
    return Impure(PrintLineF(msg, Pure(UnitValue())))


def var_decl(name: str, value: Free) -> Free:
    return Impure(VarDeclF(name, value, Pure(UnitValue())))


def var_get(name: str) -> Free:
    return Impure(VarGetF(name, lambda v: Pure(v)))


def binary_op(op: str, left: Free, right: Free) -> Free:
    return Impure(BinaryOpF(op, left, right, lambda v: Pure(v)))



# COOL PARSER -> FREE MONAD COMPILER


class COOLParser:
    """Parser that compiles COOL source to Free Monad programs"""
    
    def __init__(self):
        self.expr: Optional[Parser] = None
        self.statement: Optional[Parser] = None
        self.program: Optional[Parser] = None
        self._build_parsers()
    
    def _build_parsers(self):
        ws = whitespace()
        identifier = token(regex(r'[a-zA-Z_][a-zA-Z0-9_]*'))
        
        # Literals compile directly to Pure values
        integer = token(regex(r'-?\d+')) >> (lambda s: Pure(IntValue(int(s))))
        string_lit = token(regex(r'"(?:[^"\\]|\\.)*"')) >> (lambda s: Pure(StringValue(s[1:-1])))
        bool_lit = (keyword("true") >> pure_parser(Pure(BoolValue(True)))) | \
                   (keyword("false") >> pure_parser(Pure(BoolValue(False))))
        
        expr_delayed = Delayed(lambda: self.expr)
        stmt_delayed = Delayed(lambda: self.statement)
        
        # Variable access compiles to VarGet
        variable = identifier >> (lambda name: var_get(name))
        
        paren_expr = symbol("(") >> expr_delayed << symbol(")")
        
        primary = integer | string_lit | bool_lit | variable | paren_expr
        
        # Binary operations compile to BinaryOpF
        def op_parser(ops: List[str]) -> Parser:
            return reduce(lambda a, b: a | b, [symbol(o) for o in ops])
        
        mul_op = op_parser(["*", "/"])
        add_op = op_parser(["+", "-"])
        cmp_op = op_parser(["==", "<", ">"])
        
        def left_assoc(base_p: Parser, op_p: Parser, next_p: Parser) -> Parser:
            def rec(left: Free) -> Parser:
                return (op_p.bind(lambda op: next_p >> (lambda right: binary_op(op, left, right))).bind(rec)) | pure_parser(left)
            return base_p.bind(rec)
        
        mul_expr = left_assoc(primary, mul_op, primary)
        add_expr = left_assoc(mul_expr, add_op, mul_expr)
        self.expr = left_assoc(add_expr, cmp_op, add_expr)
        
        # Variable declaration compiles to VarDeclF
        var_decl_stmt = keyword("var") >> identifier.bind(lambda name:
            symbol("=") >> expr_delayed.bind(lambda val:
                symbol(";") >> pure_parser(var_decl(name, val))
            )
        )
        
        # Print statement compiles to PrintLineF
        # We need to evaluate the expression first, then print
        print_stmt = keyword("print") >> symbol("(") >> expr_delayed.bind(lambda expr:
            symbol(")") >> symbol(";") >> pure_parser(
                expr.bind(lambda v: print_free(str(v)))
            )
        )
        
        # Block statement sequences Free monads
        block = symbol("{") >> stmt_delayed.many() << symbol("}") >> (lambda stmts: self._sequence_free(stmts))
        
        self.statement = var_decl_stmt | print_stmt | block
        
        self.program = ws >> self.statement.many() << ws >> (lambda stmts: self._sequence_free(stmts))
    
    def _sequence_free(self, programs: List[Free]) -> Free:
        """Sequence multiple Free programs"""
        if not programs:
            return Pure(UnitValue())
        
        first = programs[0]
        rest = programs[1:]
        
        if not rest:
            return first
        
        return first.bind(lambda _: self._sequence_free(rest))
    
    def parse_program(self, source: str) -> ParseResult:
        """Parse source into Free Monad program"""
        return self.program.parse(source)
    
    def parse_expr(self, source: str) -> ParseResult:
        """Parse expression into Free Monad"""
        return (whitespace() >> self.expr << whitespace()).parse(source)




# INTERPRETERS FOR FREE MONAD PROGRAMS


class StandardInterpreter(Interpreter):
    """Standard interpreter - actually executes"""
    
    def __init__(self):
        self.env: Dict[str, Value] = {}
    
    def run(self, functor: FunctorF) -> Value:
        if isinstance(functor, PrintLineF):
            print(f"  >> {functor.message}")
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, VarDeclF):
            # Evaluate value first
            val = functor.value.interpret(self)
            self.env[functor.name] = val
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, VarGetF):
            val = self.env.get(functor.name, UnitValue())
            return functor.continuation(val).interpret(self)
        
        elif isinstance(functor, BinaryOpF):
            left_val = functor.left.interpret(self)
            right_val = functor.right.interpret(self)
            
            if functor.op == '+' and isinstance(left_val, IntValue) and isinstance(right_val, IntValue):
                result = IntValue(left_val.value + right_val.value)
            elif functor.op == '-' and isinstance(left_val, IntValue) and isinstance(right_val, IntValue):
                result = IntValue(left_val.value - right_val.value)
            elif functor.op == '*' and isinstance(left_val, IntValue) and isinstance(right_val, IntValue):
                result = IntValue(left_val.value * right_val.value)
            elif functor.op == '==' and isinstance(left_val, IntValue) and isinstance(right_val, IntValue):
                result = BoolValue(left_val.value == right_val.value)
            else:
                result = UnitValue()
            
            return functor.continuation(result).interpret(self)
        
        raise RuntimeError(f"Unknown operation: {functor}")


class TracingInterpreter(Interpreter):
    """Tracing interpreter - logs all operations"""
    
    def __init__(self):
        self.trace = []
        self.env: Dict[str, Value] = {}
    
    def run(self, functor: FunctorF) -> Value:
        self.trace.append(str(functor))
        
        if isinstance(functor, PrintLineF):
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, VarDeclF):
            val = functor.value.interpret(self)
            self.env[functor.name] = val
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, VarGetF):
            val = self.env.get(functor.name, UnitValue())
            return functor.continuation(val).interpret(self)
        
        elif isinstance(functor, BinaryOpF):
            left_val = functor.left.interpret(self)
            right_val = functor.right.interpret(self)
            
            if functor.op == '+' and isinstance(left_val, IntValue) and isinstance(right_val, IntValue):
                result = IntValue(left_val.value + right_val.value)
            elif functor.op == '*' and isinstance(left_val, IntValue) and isinstance(right_val, IntValue):
                result = IntValue(left_val.value * right_val.value)
            else:
                result = UnitValue()
            
            return functor.continuation(result).interpret(self)
        
        return UnitValue()


class OptimizingInterpreter(Interpreter):
    """Optimizing interpreter - constant folding"""
    
    def __init__(self):
        self.env: Dict[str, Value] = {}
        self.optimizations = 0
    
    def run(self, functor: FunctorF) -> Value:
        if isinstance(functor, BinaryOpF):
            # Try to evaluate operands
            left_val = functor.left.interpret(self)
            right_val = functor.right.interpret(self)
            
            # Constant folding optimization
            if isinstance(left_val, IntValue) and isinstance(right_val, IntValue):
                self.optimizations += 1
                if functor.op == '+':
                    result = IntValue(left_val.value + right_val.value)
                elif functor.op == '*':
                    result = IntValue(left_val.value * right_val.value)
                else:
                    result = UnitValue()
                return functor.continuation(result).interpret(self)
        
        # Delegate to standard behavior
        if isinstance(functor, PrintLineF):
            print(f"  >> {functor.message}")
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, VarDeclF):
            val = functor.value.interpret(self)
            self.env[functor.name] = val
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, VarGetF):
            val = self.env.get(functor.name, UnitValue())
            return functor.continuation(val).interpret(self)
        
        return UnitValue()





def demo():
    print("\nCOOL: FREE MONADS + PARSER INTEGRATION\n")
    print("Combination:")
    print("  Source Code -> Parser -> Free Monad AST -> Interpreter -> Result\n\n")
    
    parser = COOLParser()
    
    # Example 1: Simple expression
    print("\n" + "-" * 70)
    print("Example 1: Parse Expression to Free Monad")
    print("-" * 70)
    
    source1 = "3 + 4 * 5"
    print(f"Source: {source1}")
    
    result = parser.parse_expr(source1)
    if isinstance(result, ParseSuccess):
        free_prog = result.value
        print(f"\nParsed to Free Monad: {free_prog}")
        
        print("\nExecuting with StandardInterpreter:")
        interp = StandardInterpreter()
        val = free_prog.interpret(interp)
        print(f"Result: {val}")
    
    # Example 2: Variable declaration
    print("\n" + "-" * 70)
    print("Example 2: Variables and Printing")
    print("-" * 70)
    
    source2 = """
    var x = 42;
    print(x);
    """
    
    print(f"Source:")
    print(source2)
    
    result2 = parser.parse_program(source2.strip())
    if isinstance(result2, ParseSuccess):
        free_prog2 = result2.value
        print(f"\nExecuting program:")
        interp2 = StandardInterpreter()
        free_prog2.interpret(interp2)
    
    # Example 3: Complex computation
    print("\n" + "-" * 70)
    print("Example 3: Complex Computation")
    print("-" * 70)
    
    source3 = """
    var a = 10;
    var b = 20;
    var sum = 30;
    print(sum);
    """
    
    print(f"Source:")
    print(source3)
    
    result3 = parser.parse_program(source3.strip())
    if isinstance(result3, ParseSuccess):
        free_prog3 = result3.value
        
        print("\nInterpreter 1: Standard Execution")
        standard = StandardInterpreter()
        free_prog3.interpret(standard)
        
        print("\nInterpreter 2: Tracing Execution")
        tracer = TracingInterpreter()
        free_prog3.interpret(tracer)
        print(f"Trace: {tracer.trace}")
        
        print("\nInterpreter 3: Optimising Execution")
        optimizer = OptimizingInterpreter()
        free_prog3.interpret(optimizer)
        print(f"Optimisations performed: {optimizer.optimizations}")
    
    # Example 4: Multiple interpreters same program
    print("\n" + "-" * 70)
    print("Example 4: Same Program, Three Interpretations")
    print("-" * 70)
    
    source4 = "var result = 2 * 3 + 4 * 5; print(result);"
    print(f"Source: {source4}")
    
    result4 = parser.parse_program(source4)
    if isinstance(result4, ParseSuccess):
        prog = result4.value
        
        print("\n1. Standard Interpreter:")
        interp1 = StandardInterpreter()
        prog.interpret(interp1)
        
        print("\n2. Tracing Interpreter:")
        interp2 = TracingInterpreter()
        prog.interpret(interp2)
        for i, op in enumerate(interp2.trace, 1):
            print(f"   Step {i}: {op}")
        
        print("\n3. Optimising Interpreter:")
        interp3 = OptimizingInterpreter()
        prog.interpret(interp3)
        print(f"   Constant folds: {interp3.optimizations}")
    
    # Summary
    print("\n" + "-" * 70)
    print("COMPLETE CIRCLE:")
    print("-" * 70)
    print("+ Parser combinators parse source code")
    print("+ Compilation directly to Free Monad AST")
    print("+ Free Monad separates structure from meaning")
    print("+ Multiple interpreters for same program")
    print("+ Standard: Real execution")
    print("+ Tracing: Debugging and logging")
    print("+ Optimising: Performance improvements")
    print("-" * 70)
        
    print("\nConclusions:")
    print("  Text -> AST -> Free Monad -> Value")
    print("  ↑                            ↓")
    print("  └─── Interpreter Choice ─────┘")
    print("\nCategory theory from parse to execution!")


if __name__ == "__main__":
    demo()
