#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum, auto




class ValueType(Enum):
    INT = auto()
    STRUCT = auto()
    VTABLE = auto()
    CLOSURE = auto()
    NULL = auto()


@dataclass
class Value:
    type: ValueType
    data: Any
    
    @staticmethod
    def int_val(n: int):
        return Value(ValueType.INT, n)
    
    @staticmethod
    def struct_val(fields: Dict[str, 'Value']):
        return Value(ValueType.STRUCT, fields)
    
    @staticmethod
    def vtable_val(methods: Dict[str, 'Value']):
        return Value(ValueType.VTABLE, methods)
    
    @staticmethod
    def closure_val(params: List[str], body: 'Expr', env: Dict[str, 'Value']):
        return Value(ValueType.CLOSURE, {'params': params, 'body': body, 'env': env})
    
    @staticmethod
    def null_val():
        return Value(ValueType.NULL, None)
    
    def __repr__(self):
        if self.type == ValueType.INT:
            return f"{self.data}"
        elif self.type == ValueType.NULL:
            return "null"
        elif self.type == ValueType.CLOSURE:
            return f"<closure>"
        elif self.type == ValueType.VTABLE:
            return f"<vtable>"
        elif self.type == ValueType.STRUCT:
            fields = {k: v for k, v in self.data.items() if k != 'vptr'}
            return f"{{{', '.join(f'{k}: {v}' for k, v in fields.items())}}}"
        return "<unknown>"


# ============ AST ============

class ExprType(Enum):
    LITERAL = auto()
    VAR = auto()
    LET = auto()
    LAMBDA = auto()
    CALL = auto()
    ACCESS = auto()
    CREATE = auto()
    VCALL = auto()
    BINOP = auto()
    SEQ = auto()


@dataclass
class Expr:
    tag: ExprType
    data: Dict[str, Any]
    
    @staticmethod
    def literal(val: Value):
        return Expr(ExprType.LITERAL, {'value': val})
    
    @staticmethod
    def var(name: str):
        return Expr(ExprType.VAR, {'name': name})
    
    @staticmethod
    def let(name: str, value: 'Expr', body: 'Expr'):
        return Expr(ExprType.LET, {'name': name, 'value': value, 'body': body})
    
    @staticmethod
    def lambda_expr(params: List[str], body: 'Expr'):
        return Expr(ExprType.LAMBDA, {'params': params, 'body': body})
    
    @staticmethod
    def call(func: 'Expr', args: List['Expr']):
        return Expr(ExprType.CALL, {'func': func, 'args': args})
    
    @staticmethod
    def access(obj: 'Expr', field: str):
        return Expr(ExprType.ACCESS, {'obj': obj, 'field': field})
    
    @staticmethod
    def create(fields: Dict[str, 'Expr']):
        return Expr(ExprType.CREATE, {'fields': fields})
    
    @staticmethod
    def vcall(obj: 'Expr', method: str, args: List['Expr']):
        return Expr(ExprType.VCALL, {'obj': obj, 'method': method, 'args': args})
    
    @staticmethod
    def binop(op: str, left: 'Expr', right: 'Expr'):
        return Expr(ExprType.BINOP, {'op': op, 'left': left, 'right': right})
    
    @staticmethod
    def seq(exprs: List['Expr']):
        return Expr(ExprType.SEQ, {'exprs': exprs})


# ============ INTERPRETER ============

class Interpreter:
    def __init__(self):
        self.output = []
    
    def eval(self, expr: Expr, env: Optional[Dict[str, Value]] = None) -> Value:
        if env is None:
            env = {}
        
        if expr.tag == ExprType.LITERAL:
            return expr.data['value']
        
        elif expr.tag == ExprType.VAR:
            name = expr.data['name']
            if name not in env:
                raise RuntimeError(f"Unbound variable: {name}")
            return env[name]
        
        elif expr.tag == ExprType.LET:
            name = expr.data['name']
            val = self.eval(expr.data['value'], env)
            new_env = dict(env)
            new_env[name] = val
            return self.eval(expr.data['body'], new_env)
        
        elif expr.tag == ExprType.LAMBDA:
            params = expr.data['params']
            body = expr.data['body']
            return Value.closure_val(params, body, dict(env))
        
        elif expr.tag == ExprType.CALL:
            func = self.eval(expr.data['func'], env)
            args = [self.eval(arg, env) for arg in expr.data['args']]
            
            if func.type != ValueType.CLOSURE:
                raise RuntimeError("Cannot call non-function")
            
            closure_data = func.data
            call_env = dict(closure_data['env'])
            
            for i, param in enumerate(closure_data['params']):
                call_env[param] = args[i] if i < len(args) else Value.null_val()
            
            return self.eval(closure_data['body'], call_env)
        
        elif expr.tag == ExprType.ACCESS:
            obj = self.eval(expr.data['obj'], env)
            field = expr.data['field']
            
            if obj.type != ValueType.STRUCT:
                raise RuntimeError("Can only access fields on structs")
            
            return obj.data.get(field, Value.null_val())
        
        elif expr.tag == ExprType.CREATE:
            fields = {}
            for k, v in expr.data['fields'].items():
                fields[k] = self.eval(v, env)
            return Value.struct_val(fields)
        
        elif expr.tag == ExprType.VCALL:
            obj = self.eval(expr.data['obj'], env)
            method_name = expr.data['method']
            
            if obj.type != ValueType.STRUCT or 'vptr' not in obj.data:
                raise RuntimeError("Object must have vptr for virtual call")
            
            vtable = obj.data['vptr']
            if vtable.type != ValueType.VTABLE:
                raise RuntimeError("vptr must point to VTable")
            
            if method_name not in vtable.data:
                raise RuntimeError(f"Method {method_name} not found in vtable")
            
            method = vtable.data[method_name]
            if method.type != ValueType.CLOSURE:
                raise RuntimeError(f"Method {method_name} is not a closure")
            
            args = [obj] + [self.eval(arg, env) for arg in expr.data['args']]
            
            closure_data = method.data
            call_env = dict(closure_data['env'])
            
            for i, param in enumerate(closure_data['params']):
                call_env[param] = args[i] if i < len(args) else Value.null_val()
            
            return self.eval(closure_data['body'], call_env)
        
        elif expr.tag == ExprType.BINOP:
            left = self.eval(expr.data['left'], env)
            right = self.eval(expr.data['right'], env)
            op = expr.data['op']
            
            if left.type == ValueType.INT and right.type == ValueType.INT:
                l, r = left.data, right.data
                if op == '+':
                    return Value.int_val(l + r)
                elif op == '-':
                    return Value.int_val(l - r)
                elif op == '*':
                    return Value.int_val(l * r)
                elif op == '/':
                    return Value.int_val(l // r)
                elif op == '==':
                    return Value.int_val(1 if l == r else 0)
                elif op == '<':
                    return Value.int_val(1 if l < r else 0)
            
            raise RuntimeError(f"Invalid binop: {op}")
        
        elif expr.tag == ExprType.SEQ:
            result = Value.null_val()
            for e in expr.data['exprs']:
                result = self.eval(e, env)
            return result
        
        raise RuntimeError(f"Unknown expression type: {expr.tag}")


# ============ EXAMPLES ============

def example_closure():
    """Closure capturing environment"""
    make_adder = Expr.lambda_expr(
        ['n'],
        Expr.lambda_expr(
            ['x'],
            Expr.binop('+', Expr.var('x'), Expr.var('n'))
        )
    )
    
    prog = Expr.let(
        'makeAdder', make_adder,
        Expr.let(
            'add10', Expr.call(Expr.var('makeAdder'), [Expr.literal(Value.int_val(10))]),
            Expr.call(Expr.var('add10'), [Expr.literal(Value.int_val(32))])
        )
    )
    
    interp = Interpreter()
    result = interp.eval(prog)
    print(f"Closure example: {result}")


def example_int_object():
    """Integer object with virtual dispatch"""
    int_vtable = Value.vtable_val({
        'print': Value.closure_val(
            ['self'],
            Expr.access(Expr.var('self'), 'value'),
            {}
        ),
        'add': Value.closure_val(
            ['self', 'other'],
            Expr.binop(
                '+',
                Expr.access(Expr.var('self'), 'value'),
                Expr.access(Expr.var('other'), 'value')
            ),
            {}
        )
    })
    
    make_int = Expr.lambda_expr(
        ['n'],
        Expr.create({
            'vptr': Expr.literal(int_vtable),
            'value': Expr.var('n')
        })
    )
    
    prog = Expr.let(
        'makeInt', make_int,
        Expr.let(
            'obj1', Expr.call(Expr.var('makeInt'), [Expr.literal(Value.int_val(42))]),
            Expr.let(
                'obj2', Expr.call(Expr.var('makeInt'), [Expr.literal(Value.int_val(8))]),
                Expr.vcall(Expr.var('obj1'), 'add', [Expr.var('obj2')])
            )
        )
    )
    
    interp = Interpreter()
    result = interp.eval(prog)
    print(f"Int object example: {result}")


def example_polymorphic():
    """Polymorphism via different vtables"""
    int_vtable = Value.vtable_val({
        'get': Value.closure_val(
            ['self'],
            Expr.access(Expr.var('self'), 'value'),
            {}
        )
    })
    
    pair_vtable = Value.vtable_val({
        'get': Value.closure_val(
            ['self'],
            Expr.binop(
                '+',
                Expr.access(Expr.var('self'), 'first'),
                Expr.access(Expr.var('self'), 'second')
            ),
            {}
        )
    })
    
    make_int = Expr.lambda_expr(
        ['n'],
        Expr.create({
            'vptr': Expr.literal(int_vtable),
            'value': Expr.var('n')
        })
    )
    
    make_pair = Expr.lambda_expr(
        ['a', 'b'],
        Expr.create({
            'vptr': Expr.literal(pair_vtable),
            'first': Expr.var('a'),
            'second': Expr.var('b')
        })
    )
    
    prog = Expr.let(
        'makeInt', make_int,
        Expr.let(
            'makePair', make_pair,
            Expr.let(
                'obj1', Expr.call(Expr.var('makeInt'), [Expr.literal(Value.int_val(42))]),
                Expr.let(
                    'obj2', Expr.call(Expr.var('makePair'), [
                        Expr.literal(Value.int_val(10)),
                        Expr.literal(Value.int_val(20))
                    ]),
                    Expr.seq([
                        Expr.vcall(Expr.var('obj1'), 'get', []),
                        Expr.vcall(Expr.var('obj2'), 'get', [])
                    ])
                )
            )
        )
    )
    
    interp = Interpreter()
    result = interp.eval(prog)
    print(f"Polymorphic example: {result}")


def example_counter():
    """Stateful counter object (immutable style)"""
    counter_vtable = Value.vtable_val({
        'get': Value.closure_val(
            ['self'],
            Expr.access(Expr.var('self'), 'count'),
            {}
        ),
        'inc': Value.closure_val(
            ['self'],
            Expr.create({
                'vptr': Expr.access(Expr.var('self'), 'vptr'),
                'count': Expr.binop(
                    '+',
                    Expr.access(Expr.var('self'), 'count'),
                    Expr.literal(Value.int_val(1))
                )
            }),
            {}
        )
    })
    
    make_counter = Expr.lambda_expr(
        ['n'],
        Expr.create({
            'vptr': Expr.literal(counter_vtable),
            'count': Expr.var('n')
        })
    )
    
    prog = Expr.let(
        'makeCounter', make_counter,
        Expr.let(
            'c1', Expr.call(Expr.var('makeCounter'), [Expr.literal(Value.int_val(0))]),
            Expr.let(
                'c2', Expr.vcall(Expr.var('c1'), 'inc', []),
                Expr.let(
                    'c3', Expr.vcall(Expr.var('c2'), 'inc', []),
                    Expr.vcall(Expr.var('c3'), 'get', [])
                )
            )
        )
    )
    
    interp = Interpreter()
    result = interp.eval(prog)
    print(f"Counter example: {result}")


if __name__ == '__main__':
    print("=== Minimal OOP Language Interpreter ===\n")
    
    print("Core semantics:")
    print("- Objects = structs with vptr field")
    print("- VTables = method name -> closure")
    print("- Methods take 'self' as first param")
    print("- Dynamic dispatch via vtable lookup")
    print("- Closures capture environment\n")
    
    example_closure()
    example_int_object()
    example_polymorphic()
    example_counter()
    
    print("\nAll examples executed successfully!")



"""
Minimal OOP Language - Core Semantics

Key Ideas:
- Objects are structs with vptr as first field
- VTables are maps from method names to closures
- Methods take 'self' as first parameter
- Dynamic dispatch via vtable lookup
- Closures capture environment
"""
