#!/usr/bin/env python3
"""
Minimal Interpreter with Affine Types

Language syntax:
  let x = new(42)          # Create heap value (affine type)
  let y = x                # Move x to y (x consumed)
  let z = copy(x)          # Explicit copy (x not consumed)
  let r = &x               # Borrow x (x not consumed)
  print(x)                 # Use value
  drop(x)                  # Explicit drop
  x + y                    # Arithmetic

Shows:
- Affine type tracking
- Use-after-move detection
- Explicit copy vs move semantics
- Memory management
"""

from dataclasses import dataclass
from typing import Dict, Set, Optional, List, Any
from enum import Enum


# AST NODES

class Expr:
    pass

@dataclass
class Number(Expr):
    value: int

@dataclass
class Var(Expr):
    name: str

@dataclass
class New(Expr):
    """new(value) - allocate on heap (affine type)"""
    value: Expr

@dataclass
class Copy(Expr):
    """copy(var) - explicit copy"""
    var: str

@dataclass
class Borrow(Expr):
    """&var - borrow reference"""
    var: str

@dataclass
class Deref(Expr):
    """*ref - dereference"""
    ref: Expr

@dataclass
class BinOp(Expr):
    op: str  # '+', '-', '*'
    left: Expr
    right: Expr

class Stmt:
    pass

@dataclass
class Let(Stmt):
    """let x = expr"""
    var: str
    value: Expr

@dataclass
class Drop(Stmt):
    """drop(x) - explicit cleanup"""
    var: str

@dataclass
class Print(Stmt):
    """print(expr)"""
    expr: Expr

@dataclass
class ExprStmt(Stmt):
    """Expression as statement"""
    expr: Expr


# AFFINE TYPE SYSTEM

class TypeKind(Enum):
    VALUE = "value"      # Unrestricted (copyable)
    AFFINE = "affine"    # Use at most once
    REFERENCE = "ref"    # Borrowed reference

@dataclass
class Type:
    kind: TypeKind
    
    def is_affine(self):
        return self.kind == TypeKind.AFFINE
    
    def is_reference(self):
        return self.kind == TypeKind.REFERENCE

@dataclass
class VarInfo:
    """Information about a variable"""
    typ: Type
    consumed: bool = False
    consumed_at: Optional[int] = None  # Line number where consumed
    borrowed_by: Set[str] = None       # Set of references borrowing this
    
    def __post_init__(self):
        if self.borrowed_by is None:
            self.borrowed_by = set()

class AffineChecker:
    """
    This is the core of affine type checking!
    Tracks consumption state for each variable.
    """

    def __init__(self):
        self.vars: Dict[str, VarInfo] = {}
        self.line = 0
        self.errors: List[str] = []
    
    def declare(self, var: str, typ: Type):
        """Declare a new variable"""
        self.vars[var] = VarInfo(typ)
        self.log(f"DECLARE {var}: {typ.kind.value}")
    
    def consume(self, var: str) -> bool:
        """
        Mark variable as consumed (the key operation!)
        Returns True if successful, False if already consumed
        """
        if var not in self.vars:
            self.error(f"Variable '{var}' not found")
            return False
        
        info = self.vars[var]
        
        # Check if already consumed
        if info.consumed:
            self.error(f"Use after move: '{var}' was already consumed at line {info.consumed_at}")
            return False
        
        # Check if borrowed
        if len(info.borrowed_by) > 0:
            self.error(f"Cannot move '{var}' while borrowed by {info.borrowed_by}")
            return False
        
        # Consume it!
        if info.typ.is_affine():
            info.consumed = True
            info.consumed_at = self.line
            self.log(f"CONSUME {var} (affine type)")
        else:
            self.log(f"USE {var} (copyable type)")
        
        return True
    
    def borrow(self, var: str, ref_name: str) -> bool:
        """Create a borrow (reference)"""
        if var not in self.vars:
            self.error(f"Variable '{var}' not found")
            return False
        
        info = self.vars[var]
        
        if info.consumed:
            self.error(f"Cannot borrow consumed variable '{var}'")
            return False
        
        info.borrowed_by.add(ref_name)
        self.log(f"BORROW {var} by {ref_name}")
        return True
    
    def end_borrow(self, var: str, ref_name: str):
        """End a borrow"""
        if var in self.vars:
            self.vars[var].borrowed_by.discard(ref_name)
            self.log(f"END BORROW {var} by {ref_name}")
    
    def copy_var(self, var: str) -> bool:
        """Explicit copy - doesn't consume original"""
        if var not in self.vars:
            self.error(f"Variable '{var}' not found")
            return False
        
        info = self.vars[var]
        
        if info.consumed:
            self.error(f"Cannot copy consumed variable '{var}'")
            return False
        
        self.log(f"COPY {var} (original still valid)")
        return True
    
    def check_use(self, var: str) -> bool:
        """Check if variable can be used (for reading)"""
        if var not in self.vars:
            self.error(f"Variable '{var}' not found")
            return False
        
        info = self.vars[var]
        
        if info.consumed:
            self.error(f"Use after move: '{var}' was consumed at line {info.consumed_at}")
            return False
        
        self.log(f"READ {var}")
        return True
    
    def drop_var(self, var: str):
        """Explicitly drop variable"""
        if var in self.vars:
            if not self.vars[var].consumed:
                self.consume(var)
    
    def error(self, msg: str):
        self.errors.append(f"Line {self.line}: {msg}")
        print(f"  ERROR (line {self.line}): {msg}")
    
    def log(self, msg: str):
        print(f"  [{self.line}] {msg}")


# INTERPRETER WITH MEMORY MANAGEMENT

class Memory:
    """Simulated heap"""
    
    def __init__(self):
        self.heap: Dict[int, int] = {}
        self.next_addr = 1000
        self.allocations = 0
        self.deallocations = 0
    
    def allocate(self, value: int) -> int:
        """Allocate on heap, return address"""
        addr = self.next_addr
        self.heap[addr] = value
        self.next_addr += 1
        self.allocations += 1
        print(f"    ALLOC: address {addr} = {value}")
        return addr
    
    def read(self, addr: int) -> int:
        """Read from heap"""
        if addr not in self.heap:
            raise RuntimeError(f"Invalid memory access: {addr}")
        return self.heap[addr]
    
    def free(self, addr: int):
        """Free heap memory"""
        if addr in self.heap:
            value = self.heap[addr]
            del self.heap[addr]
            self.deallocations += 1
            print(f"     FREE: address {addr} (was {value})")
    
    def stats(self):
        print(f"\n Memory Stats:")
        print(f"   Allocations: {self.allocations}")
        print(f"   Deallocations: {self.deallocations}")
        print(f"   Leaked: {self.allocations - self.deallocations}")
        if len(self.heap) > 0:
            print(f"   Still allocated: {list(self.heap.keys())}")


class Interpreter:
    """Interpreter with affine type checking"""
    
    def __init__(self):
        self.checker = AffineChecker()
        self.memory = Memory()
        self.env: Dict[str, Any] = {}  # Variable -> value (addr or int)
    
    def eval_expr(self, expr: Expr) -> tuple[Any, Type]:
        """
        Evaluate expression, return (value, type)
        Key: tracks whether expression consumes its inputs!
        """
        
        if isinstance(expr, Number):
            return expr.value, Type(TypeKind.VALUE)
        
        elif isinstance(expr, Var):
            # Using a variable - check if consumed
            if not self.checker.check_use(expr.name):
                raise RuntimeError(f"Cannot use consumed variable")
            
            if expr.name not in self.env:
                raise RuntimeError(f"Variable {expr.name} not found")
            
            return self.env[expr.name], self.checker.vars[expr.name].typ
        
        elif isinstance(expr, New):
            # Allocate on heap - returns affine type!
            val, _ = self.eval_expr(expr.value)
            addr = self.memory.allocate(val)
            return addr, Type(TypeKind.AFFINE)
        
        elif isinstance(expr, Copy):
            # Explicit copy - doesn't consume
            if not self.checker.copy_var(expr.var):
                raise RuntimeError("Cannot copy")
            
            if expr.var not in self.env:
                raise RuntimeError(f"Variable {expr.var} not found")
            
            # Copy the heap value
            old_addr = self.env[expr.var]
            old_val = self.memory.read(old_addr)
            new_addr = self.memory.allocate(old_val)
            return new_addr, Type(TypeKind.AFFINE)
        
        elif isinstance(expr, Borrow):
            # Borrow - returns reference
            # Note: In real system would need lifetime tracking
            if expr.var not in self.env:
                raise RuntimeError(f"Variable {expr.var} not found")
            
            return self.env[expr.var], Type(TypeKind.REFERENCE)
        
        elif isinstance(expr, Deref):
            # Dereference
            addr, typ = self.eval_expr(expr.ref)
            if not typ.is_reference():
                raise RuntimeError("Can only deref references")
            return self.memory.read(addr), Type(TypeKind.VALUE)
        
        elif isinstance(expr, BinOp):
            # Arithmetic - consumes affine operands!
            left_val, left_type = self.eval_expr(expr.left)
            right_val, right_type = self.eval_expr(expr.right)
            
            # If operands are heap values, read them
            if left_type.is_affine():
                left_val = self.memory.read(left_val)
            if right_type.is_affine():
                right_val = self.memory.read(right_val)
            
            if expr.op == '+':
                result = left_val + right_val
            elif expr.op == '-':
                result = left_val - right_val
            elif expr.op == '*':
                result = left_val * right_val
            else:
                raise RuntimeError(f"Unknown op: {expr.op}")
            
            return result, Type(TypeKind.VALUE)
        
        raise RuntimeError(f"Unknown expr: {expr}")
    
    def exec_stmt(self, stmt: Stmt):
        """Execute statement"""
        
        if isinstance(stmt, Let):
            # Assignment - potentially consumes RHS
            val, typ = self.eval_expr(stmt.value)
            
            # If RHS is a variable with affine type, consume it
            if isinstance(stmt.value, Var):
                if self.checker.vars[stmt.value.name].typ.is_affine():
                    self.checker.consume(stmt.value.name)
            
            # Declare new variable
            self.checker.declare(stmt.var, typ)
            self.env[stmt.var] = val
        
        elif isinstance(stmt, Drop):
            # Explicit drop
            if stmt.var not in self.env:
                raise RuntimeError(f"Variable {stmt.var} not found")
            
            if self.checker.vars[stmt.var].typ.is_affine():
                addr = self.env[stmt.var]
                self.memory.free(addr)
            
            self.checker.drop_var(stmt.var)
        
        elif isinstance(stmt, Print):
            val, typ = self.eval_expr(stmt.expr)
            
            # If printing heap value, read it
            if typ.is_affine():
                val = self.memory.read(val)
            
            print(f"    OUTPUT: {val}")
        
        elif isinstance(stmt, ExprStmt):
            self.eval_expr(stmt.expr)
    
    def run(self, stmts: List[Stmt]):
        """Run program"""
        for i, stmt in enumerate(stmts):
            self.checker.line = i + 1
            print(f"\n  Line {i + 1}: {stmt}")
            
            try:
                self.exec_stmt(stmt)
            except RuntimeError as e:
                print(f"  RUNTIME ERROR: {e}")
                break
        
        # Check for memory leaks
        print("\n" + "-"*50)
        self.memory.stats()
        
        if self.checker.errors:
            print(f"\n  Found {len(self.checker.errors)} affine type errors")
        else:
            print(f"\n  No affine type errors!")


# Samples

def example_basic():
    """Basic affine types"""
    print("-"*50)
    print("EXAMPLE 1: Basic Affine Types")
    print("-"*50)
    
    program = [
        Let("x", New(Number(42))),       # x owns heap value
        Let("y", Var("x")),              # Move x to y (x consumed!)
        Print(Var("y")),                 # OK - y is valid
        # Print(Var("x")),               # Would error: x consumed!
        Drop("y"),                       # Explicit cleanup
    ]
    
    interp = Interpreter()
    interp.run(program)

def example_use_after_move():
    """Demonstrates use-after-move error"""
    print("\n" + "-"*50)
    print("EXAMPLE 2: Use After Move (ERROR)")
    print("-"*50)
    
    program = [
        Let("x", New(Number(100))),
        Let("y", Var("x")),              # x moved to y
        Print(Var("y")),                 # OK
        Print(Var("x")),                 # ERROR: x was moved!
    ]
    
    interp = Interpreter()
    interp.run(program)

def example_copy():
    """Explicit copy"""
    print("\n" + "-"*50)
    print("EXAMPLE 3: Explicit Copy")
    print("-"*50)
    
    program = [
        Let("x", New(Number(42))),
        Let("y", Copy("x")),             # Copy x (x still valid!)
        Print(Var("x")),                 # OK - x not consumed
        Print(Var("y")),                 # OK - y is separate
        Drop("x"),
        Drop("y"),
    ]
    
    interp = Interpreter()
    interp.run(program)

def example_arithmetic():
    """Arithmetic with affine types"""
    print("\n" + "-"*50)
    print("EXAMPLE 4: Arithmetic")
    print("-"*50)
    
    program = [
        Let("x", New(Number(10))),
        Let("y", New(Number(20))),
        Let("sum", BinOp("+", Var("x"), Var("y"))),
        Print(Var("sum")),
        # x and y still valid here (we only read them)
        Drop("x"),
        Drop("y"),
    ]
    
    interp = Interpreter()
    interp.run(program)

def example_no_cleanup():
    """Shows memory leak without cleanup"""
    print("\n" + "-"*50)
    print("EXAMPLE 5: Memory Leak (no drop)")
    print("-"*50)
    
    program = [
        Let("x", New(Number(42))),
        Print(Var("x")),
        # Forgot to drop x - memory leak!
    ]
    
    interp = Interpreter()
    interp.run(program)

if __name__ == "__main__":
    example_basic()
    example_use_after_move()
    example_copy()
    example_arithmetic()
    example_no_cleanup()
    
    print("\n" + "-"*50)
    print("Key Concepts Demonstrated:")
    print("-"*50)
    print("+ Affine types: values used at most once")
    print("+ Move semantics: assignment consumes source")
    print("+ Use-after-move detection at 'runtime' (would be compile-time)")
    print("+ Explicit copy vs implicit move")
    print("+ Memory management tied to ownership")
    print("+ Memory leak detection")
