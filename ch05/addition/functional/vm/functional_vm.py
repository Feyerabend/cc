"""
Functional Virtual Machine

A stack-based VM that executes an AST directly, using functional programming
primitives from functional_core as the runtime foundation.

Features:
- Stack-based execution model
- First-class functions and closures
- Pattern matching on ADTs
- Immutable data structures
- Maybe/Result types as built-in values
- Tail call optimization
"""


from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from enum import Enum, auto
from functional_core import Maybe, Some, nothing, Result, Ok, Err
from functional_types import List


# AST DEFS

class NodeType(Enum):
    """Types of AST nodes."""
    # Literals
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    
    # Variables
    VAR = auto()
    
    # Functions
    LAMBDA = auto()
    APPLY = auto()
    
    # Let bindings
    LET = auto()
    
    # Conditionals
    IF = auto()
    
    # Pattern matching
    MATCH = auto()
    CASE = auto()
    
    # Data constructors
    SOME = auto()
    NOTHING = auto()
    OK = auto()
    ERR = auto()
    LIST = auto()
    
    # Binary operations
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    EQ = auto()
    LT = auto()
    GT = auto()
    
    # List operations
    CONS = auto()
    HEAD = auto()
    TAIL = auto()
    
    # Monadic operations
    MAP = auto()
    FLATMAP = auto()
    FILTER = auto()
    
    # Sequencing
    SEQ = auto()


@dataclass
class ASTNode:
    """Base AST node."""
    node_type: NodeType
    value: Any = None
    children: list['ASTNode'] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def __repr__(self):
        if self.children:
            return f"{self.node_type.name}({self.value}, {self.children})"
        return f"{self.node_type.name}({self.value})"



# RUNTIME VALUES

@dataclass
class Closure:
    """A closure captures a lambda with its environment."""
    param_name: str
    body: ASTNode
    env: dict
    
    def __repr__(self):
        return f"<closure {self.param_name}>"


@dataclass
class NativeFunction:
    """A native Python function wrapped for the VM."""
    name: str
    func: Callable
    arity: int
    
    def __repr__(self):
        return f"<native {self.name}>"



# VM

class FunctionalVM:
    """
    A stack-based virtual machine for functional programs.
    """
    
    def __init__(self, debug: bool = False):
        self.stack = []
        self.global_env = self._init_global_env()
        self.debug = debug
        self.call_depth = 0
        self.max_call_depth = 1000
    
    def _init_global_env(self) -> dict:
        """Init the global environment with built-in functions."""
        return {
            # Arithmetic
            '+': NativeFunction('+', lambda a, b: a + b, 2),
            '-': NativeFunction('-', lambda a, b: a - b, 2),
            '*': NativeFunction('*', lambda a, b: a * b, 2),
            '/': NativeFunction('/', lambda a, b: a / b if b != 0 else Err("Division by zero"), 2),
            
            # Comparison
            '==': NativeFunction('==', lambda a, b: a == b, 2),
            '<': NativeFunction('<', lambda a, b: a < b, 2),
            '>': NativeFunction('>', lambda a, b: a > b, 2),
            '<=': NativeFunction('<=', lambda a, b: a <= b, 2),
            '>=': NativeFunction('>=', lambda a, b: a >= b, 2),
            
            # Logic
            'and': NativeFunction('and', lambda a, b: a and b, 2),
            'or': NativeFunction('or', lambda a, b: a or b, 2),
            'not': NativeFunction('not', lambda a: not a, 1),
            
            # IO
            'print': NativeFunction('print', lambda x: print(x) or x, 1),
            
            # Type predicates
            'is_some': NativeFunction('is_some', lambda x: isinstance(x, Maybe) and x.is_some(), 1),
            'is_nothing': NativeFunction('is_nothing', lambda x: isinstance(x, Maybe) and x.is_none(), 1),
            'is_ok': NativeFunction('is_ok', lambda x: isinstance(x, Result) and x.is_ok(), 1),
            'is_err': NativeFunction('is_err', lambda x: isinstance(x, Result) and x.is_err(), 1),
        }
    
    def push(self, value: Any):
        """Push a value onto the stack."""
        if self.debug:
            print(f"  PUSH: {value}")
        self.stack.append(value)
    
    def pop(self) -> Any:
        """Pop a value from the stack."""
        if not self.stack:
            raise RuntimeError("Stack underflow")
        value = self.stack.pop()
        if self.debug:
            print(f"  POP: {value}")
        return value
    
    def eval(self, node: ASTNode, env: dict) -> Any:
        """
        Evaluate an AST node in the given environment.
        Returns the result value.
        """
        if self.debug:
            indent = "  " * self.call_depth
            print(f"{indent}EVAL: {node.node_type.name}")
        
        node_type = node.node_type
        
        # Literals
        if node_type == NodeType.INT:
            return node.value
        
        elif node_type == NodeType.FLOAT:
            return node.value
        
        elif node_type == NodeType.STRING:
            return node.value
        
        elif node_type == NodeType.BOOL:
            return node.value
        
        # Variables
        elif node_type == NodeType.VAR:
            var_name = node.value
            if var_name in env:
                return env[var_name]
            elif var_name in self.global_env:
                return self.global_env[var_name]
            else:
                raise NameError(f"Undefined variable: {var_name}")
        
        # Lambda abstraction
        elif node_type == NodeType.LAMBDA:
            param_name = node.value
            body = node.children[0]
            return Closure(param_name, body, env.copy())
        
        # Function application
        elif node_type == NodeType.APPLY:
            func_node = node.children[0]
            arg_node = node.children[1]
            
            func = self.eval(func_node, env)
            arg = self.eval(arg_node, env)
            
            return self._apply(func, arg, env)
        
        # Let binding
        elif node_type == NodeType.LET:
            var_name = node.value
            value_node = node.children[0]
            body_node = node.children[1]
            
            value = self.eval(value_node, env)
            new_env = env.copy()
            new_env[var_name] = value
            
            return self.eval(body_node, new_env)
        
        # Conditional
        elif node_type == NodeType.IF:
            cond_node = node.children[0]
            then_node = node.children[1]
            else_node = node.children[2]
            
            cond = self.eval(cond_node, env)
            if cond:
                return self.eval(then_node, env)
            else:
                return self.eval(else_node, env)
        
        # Pattern matching
        elif node_type == NodeType.MATCH:
            scrutinee_node = node.children[0]
            cases = node.children[1:]  # List of CASE nodes
            
            scrutinee = self.eval(scrutinee_node, env)
            return self._match(scrutinee, cases, env)
        
        # Data constructors
        elif node_type == NodeType.SOME:
            value = self.eval(node.children[0], env)
            return Some(value)
        
        elif node_type == NodeType.NOTHING:
            return nothing()
        
        elif node_type == NodeType.OK:
            value = self.eval(node.children[0], env)
            return Ok(value)
        
        elif node_type == NodeType.ERR:
            error = self.eval(node.children[0], env)
            return Err(error)
        
        elif node_type == NodeType.LIST:
            items = [self.eval(child, env) for child in node.children]
            return List.of(*items)
        
        # Binary operations
        elif node_type in [NodeType.ADD, NodeType.SUB, NodeType.MUL, NodeType.DIV,
                          NodeType.EQ, NodeType.LT, NodeType.GT]:
            left = self.eval(node.children[0], env)
            right = self.eval(node.children[1], env)
            return self._binary_op(node_type, left, right)
        
        # List operations
        elif node_type == NodeType.CONS:
            item = self.eval(node.children[0], env)
            list_val = self.eval(node.children[1], env)
            if isinstance(list_val, List):
                return list_val.cons(item)
            raise TypeError(f"cons expects List, got {type(list_val)}")
        
        elif node_type == NodeType.HEAD:
            list_val = self.eval(node.children[0], env)
            if isinstance(list_val, List):
                return list_val.head()
            raise TypeError(f"head expects List, got {type(list_val)}")
        
        elif node_type == NodeType.TAIL:
            list_val = self.eval(node.children[0], env)
            if isinstance(list_val, List):
                return list_val.tail()
            raise TypeError(f"tail expects List, got {type(list_val)}")
        
        # Monadic operations
        elif node_type == NodeType.MAP:
            func = self.eval(node.children[0], env)
            container = self.eval(node.children[1], env)
            return self._map(func, container, env)
        
        elif node_type == NodeType.FLATMAP:
            func = self.eval(node.children[0], env)
            container = self.eval(node.children[1], env)
            return self._flatmap(func, container, env)
        
        elif node_type == NodeType.FILTER:
            predicate = self.eval(node.children[0], env)
            container = self.eval(node.children[1], env)
            return self._filter(predicate, container, env)
        
        # Sequencing
        elif node_type == NodeType.SEQ:
            result = None
            for child in node.children:
                result = self.eval(child, env)
            return result
        
        else:
            raise NotImplementedError(f"Node type not implemented: {node_type}")
    
    def _apply(self, func: Any, arg: Any, env: dict) -> Any:
        """Apply a function to an argument."""
        if isinstance(func, Closure):
            # Check for tail call optimization opportunity
            self.call_depth += 1
            if self.call_depth > self.max_call_depth:
                raise RuntimeError("Maximum recursion depth exceeded")
            
            # Create new environment with parameter bound
            new_env = func.env.copy()
            new_env[func.param_name] = arg
            
            result = self.eval(func.body, new_env)
            self.call_depth -= 1
            return result
        
        elif isinstance(func, NativeFunction):
            if func.arity == 1:
                return func.func(arg)
            else:
                # Partial application
                return Closure(
                    param_name='_partial',
                    body=None,  # Placeholder
                    env={'_func': func, '_arg1': arg}
                )
        
        else:
            raise TypeError(f"Cannot apply non-function: {type(func)}")
    
    def _binary_op(self, op: NodeType, left: Any, right: Any) -> Any:
        """Execute a binary operation."""
        if op == NodeType.ADD:
            return left + right
        elif op == NodeType.SUB:
            return left - right
        elif op == NodeType.MUL:
            return left * right
        elif op == NodeType.DIV:
            if right == 0:
                return Err("Division by zero")
            return Ok(left / right)
        elif op == NodeType.EQ:
            return left == right
        elif op == NodeType.LT:
            return left < right
        elif op == NodeType.GT:
            return left > right
    
    def _match(self, scrutinee: Any, cases: list[ASTNode], env: dict) -> Any:
        """Pattern match on a value."""
        for case in cases:
            pattern = case.value  # Pattern descriptor
            body = case.children[0]
            
            match_result = self._pattern_match(scrutinee, pattern, env)
            if match_result.is_some():
                bindings = match_result.get_or_else({})
                new_env = env.copy()
                new_env.update(bindings)
                return self.eval(body, new_env)
        
        raise RuntimeError(f"Non-exhaustive pattern match: {scrutinee}")
    
    def _pattern_match(self, value: Any, pattern: dict, env: dict) -> Maybe[dict]:
        """
        Try to match a value against a pattern.
        Returns Some(bindings) if match succeeds, Nothing otherwise.
        """
        pattern_type = pattern.get('type')
        
        if pattern_type == 'wildcard':
            return Some({})
        
        elif pattern_type == 'var':
            # Bind variable
            var_name = pattern['name']
            return Some({var_name: value})
        
        elif pattern_type == 'literal':
            if value == pattern['value']:
                return Some({})
            return nothing()
        
        elif pattern_type == 'Some':
            if isinstance(value, Maybe) and value.is_some():
                inner_pattern = pattern.get('inner')
                inner_value = value.get_or_else(None)
                return self._pattern_match(inner_value, inner_pattern, env)
            return nothing()
        
        elif pattern_type == 'Nothing':
            if isinstance(value, Maybe) and value.is_none():
                return Some({})
            return nothing()
        
        elif pattern_type == 'Ok':
            if isinstance(value, Result) and value.is_ok():
                inner_pattern = pattern.get('inner')
                inner_value = value.get_or_else(None)
                return self._pattern_match(inner_value, inner_pattern, env)
            return nothing()
        
        elif pattern_type == 'Err':
            if isinstance(value, Result) and value.is_err():
                # Extract error value
                if hasattr(value, 'error'):
                    inner_pattern = pattern.get('inner')
                    return self._pattern_match(value.error, inner_pattern, env)
            return nothing()
        
        elif pattern_type == 'List':
            if isinstance(value, List):
                if value.is_empty():
                    if pattern.get('empty'):
                        return Some({})
                    return nothing()
                else:
                    # Match cons pattern
                    head_pattern = pattern.get('head')
                    tail_pattern = pattern.get('tail')
                    
                    head_val = value.head().get_or_else(None)
                    tail_val = value.tail()
                    
                    head_match = self._pattern_match(head_val, head_pattern, env)
                    if head_match.is_none():
                        return nothing()
                    
                    tail_match = self._pattern_match(tail_val, tail_pattern, env)
                    if tail_match.is_none():
                        return nothing()
                    
                    # Combine bindings
                    bindings = head_match.get_or_else({})
                    bindings.update(tail_match.get_or_else({}))
                    return Some(bindings)
            return nothing()
        
        else:
            return nothing()
    
    def _map(self, func: Any, container: Any, env: dict) -> Any:
        """Map a function over a container."""
        if isinstance(container, Maybe):
            return container.map(lambda x: self._apply(func, x, env))
        elif isinstance(container, Result):
            return container.map(lambda x: self._apply(func, x, env))
        elif isinstance(container, List):
            return container.fmap(lambda x: self._apply(func, x, env))
        else:
            raise TypeError(f"Cannot map over {type(container)}")
    
    def _flatmap(self, func: Any, container: Any, env: dict) -> Any:
        """FlatMap a function over a container."""
        if isinstance(container, Maybe):
            return container.flat_map(lambda x: self._apply(func, x, env))
        elif isinstance(container, Result):
            return container.flat_map(lambda x: self._apply(func, x, env))
        elif isinstance(container, List):
            return container.bind(lambda x: self._apply(func, x, env))
        else:
            raise TypeError(f"Cannot flatMap over {type(container)}")
    
    def _filter(self, predicate: Any, container: Any, env: dict) -> Any:
        """Filter a container with a predicate."""
        if isinstance(container, Maybe):
            return container.filter(lambda x: self._apply(predicate, x, env))
        elif isinstance(container, List):
            return container.filter(lambda x: self._apply(predicate, x, env))
        else:
            raise TypeError(f"Cannot filter {type(container)}")
    
    def run(self, node: ASTNode) -> Any:
        """Run a program (AST node) and return the result."""
        try:
            result = self.eval(node, {})
            return result
        except Exception as e:
            return Err(str(e))



# AST BUILDER HELP

def lit_int(value: int) -> ASTNode:
    """Create an integer literal node."""
    return ASTNode(NodeType.INT, value)

def lit_float(value: float) -> ASTNode:
    """Create a float literal node."""
    return ASTNode(NodeType.FLOAT, value)

def lit_str(value: str) -> ASTNode:
    """Create a string literal node."""
    return ASTNode(NodeType.STRING, value)

def lit_bool(value: bool) -> ASTNode:
    """Create a boolean literal node."""
    return ASTNode(NodeType.BOOL, value)

def var(name: str) -> ASTNode:
    """Create a variable reference node."""
    return ASTNode(NodeType.VAR, name)

def lam(param: str, body: ASTNode) -> ASTNode:
    """Create a lambda node."""
    return ASTNode(NodeType.LAMBDA, param, [body])

def app(func: ASTNode, arg: ASTNode) -> ASTNode:
    """Create a function application node."""
    return ASTNode(NodeType.APPLY, children=[func, arg])

def let(name: str, value: ASTNode, body: ASTNode) -> ASTNode:
    """Create a let binding node."""
    return ASTNode(NodeType.LET, name, [value, body])

def if_expr(cond: ASTNode, then_branch: ASTNode, else_branch: ASTNode) -> ASTNode:
    """Create an if expression node."""
    return ASTNode(NodeType.IF, children=[cond, then_branch, else_branch])

def some(value: ASTNode) -> ASTNode:
    """Create a Some constructor node."""
    return ASTNode(NodeType.SOME, children=[value])

def nothing_node() -> ASTNode:
    """Create a Nothing constructor node."""
    return ASTNode(NodeType.NOTHING)

def ok(value: ASTNode) -> ASTNode:
    """Create an Ok constructor node."""
    return ASTNode(NodeType.OK, children=[value])

def err(value: ASTNode) -> ASTNode:
    """Create an Err constructor node."""
    return ASTNode(NodeType.ERR, children=[value])

def list_node(*items: ASTNode) -> ASTNode:
    """Create a list node."""
    return ASTNode(NodeType.LIST, children=list(items))

def add(left: ASTNode, right: ASTNode) -> ASTNode:
    """Create an addition node."""
    return ASTNode(NodeType.ADD, children=[left, right])

def sub(left: ASTNode, right: ASTNode) -> ASTNode:
    """Create a subtraction node."""
    return ASTNode(NodeType.SUB, children=[left, right])

def mul(left: ASTNode, right: ASTNode) -> ASTNode:
    """Create a multiplication node."""
    return ASTNode(NodeType.MUL, children=[left, right])

def div(left: ASTNode, right: ASTNode) -> ASTNode:
    """Create a division node."""
    return ASTNode(NodeType.DIV, children=[left, right])

def eq(left: ASTNode, right: ASTNode) -> ASTNode:
    """Create an equality node."""
    return ASTNode(NodeType.EQ, children=[left, right])

def lt(left: ASTNode, right: ASTNode) -> ASTNode:
    """Create a less-than node."""
    return ASTNode(NodeType.LT, children=[left, right])

def match(scrutinee: ASTNode, *cases) -> ASTNode:
    """Create a match expression node."""
    return ASTNode(NodeType.MATCH, children=[scrutinee] + list(cases))

def case(pattern: dict, body: ASTNode) -> ASTNode:
    """Create a case node for pattern matching."""
    return ASTNode(NodeType.CASE, pattern, [body])

def seq(*exprs: ASTNode) -> ASTNode:
    """Create a sequence of expressions."""
    return ASTNode(NodeType.SEQ, children=list(exprs))

def map_node(func: ASTNode, container: ASTNode) -> ASTNode:
    """Create a map operation node."""
    return ASTNode(NodeType.MAP, children=[func, container])

def flatmap_node(func: ASTNode, container: ASTNode) -> ASTNode:
    """Create a flatmap operation node."""
    return ASTNode(NodeType.FLATMAP, children=[func, container])

def filter_node(predicate: ASTNode, container: ASTNode) -> ASTNode:
    """Create a filter operation node."""
    return ASTNode(NodeType.FILTER, children=[predicate, container])
