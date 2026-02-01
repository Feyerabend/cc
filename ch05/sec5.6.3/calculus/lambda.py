from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum, auto


class TypeKind(Enum):
    BASE = auto()
    FUNCTION = auto()

@dataclass(frozen=True)
class Type:
    """Base class for types"""
    pass

@dataclass(frozen=True)
class BaseType(Type):
    """Base types like Int, Bool, String"""
    name: str
    
    def __str__(self):
        return self.name

@dataclass(frozen=True)
class FunctionType(Type):
    """Function types: τ₁ → τ₂"""
    param_type: Type
    return_type: Type
    
    def __str__(self):
        # Add parentheses if param is also a function
        param_str = f"({self.param_type})" if isinstance(self.param_type, FunctionType) else str(self.param_type)
        return f"{param_str} → {self.return_type}"


@dataclass
class Term:
    """Base class for lambda calculus terms"""
    pass

@dataclass
class Var(Term):
    """Variable: x"""
    name: str
    
    def __str__(self):
        return self.name

@dataclass
class Abs(Term):
    """Abstraction: λx:τ. e"""
    param: str
    param_type: Type
    body: Term
    
    def __str__(self):
        return f"(λ{self.param}:{self.param_type}. {self.body})"

@dataclass
class App(Term):
    """Application: e₁ e₂"""
    func: Term
    arg: Term
    
    def __str__(self):
        return f"({self.func} {self.arg})"



class TypeContext:
    """Typing context (Γ) - maps variables to their types"""
    def __init__(self):
        self.bindings: Dict[str, Type] = {}
    
    def extend(self, var: str, typ: Type) -> 'TypeContext':
        """Create new context with additional binding"""
        new_ctx = TypeContext()
        new_ctx.bindings = self.bindings.copy()
        new_ctx.bindings[var] = typ
        return new_ctx
    
    def lookup(self, var: str) -> Optional[Type]:
        """Look up variable's type"""
        return self.bindings.get(var)

class TypeError(Exception):
    """Type checking error"""
    pass

def typecheck(term: Term, context: TypeContext = None) -> Type:
    """
    Type check a lambda calculus term.
    Returns the type of the term if well-typed, raises TypeError otherwise.
    
    Typing rules:
      1. Γ ⊢ x : τ  if (x:τ) ∈ Γ                    (Variable)
      2. Γ, x:τ₁ ⊢ e:τ₂  ⟹  Γ ⊢ λx:τ₁.e : τ₁→τ₂    (Abstraction)
      3. Γ ⊢ e₁:τ₁→τ₂, Γ ⊢ e₂:τ₁  ⟹  Γ ⊢ e₁ e₂:τ₂  (Application)
    """
    if context is None:
        context = TypeContext()
    
    if isinstance(term, Var):
        # Rule 1: Variable
        typ = context.lookup(term.name)
        if typ is None:
            raise TypeError(f"Unbound variable: {term.name}")
        return typ
    
    elif isinstance(term, Abs):
        # Rule 2: Abstraction
        # Type check body in extended context
        extended_ctx = context.extend(term.param, term.param_type)
        body_type = typecheck(term.body, extended_ctx)
        return FunctionType(term.param_type, body_type)
    
    elif isinstance(term, App):
        # Rule 3: Application
        func_type = typecheck(term.func, context)
        arg_type = typecheck(term.arg, context)
        
        if not isinstance(func_type, FunctionType):
            raise TypeError(f"Expected function type, got {func_type}")
        
        if func_type.param_type != arg_type:
            raise TypeError(
                f"Type mismatch: expected {func_type.param_type}, "
                f"got {arg_type}"
            )
        
        return func_type.return_type
    
    else:
        raise TypeError(f"Unknown term type: {type(term)}")



def main():
    # Define some base types
    Int = BaseType("Int")
    Bool = BaseType("Bool")
    
    print("Simply Typed Lambda Calculus\n")
    
    # Example 1: Identity function
    #    λx:Int. x  :  Int → Int
    identity = Abs("x", Int, Var("x"))
    print(f"Term: {identity}")
    print(f"Type: {typecheck(identity)}")
    print()
    
    # Example 2: Constant function
    #    λx:Int. λy:Bool. x  :  Int → Bool → Int
    const_fn = Abs("x", Int, Abs("y", Bool, Var("x")))
    print(f"Term: {const_fn}")
    print(f"Type: {typecheck(const_fn)}")
    print()
    
    # Example 3: Function composition type
    #    λf:Int→Bool. λg:Bool→Int. λx:Int. g (f x)
    # Type: (Int→Bool) → (Bool→Int) → Int → Int
    compose = Abs(
        "f", FunctionType(Int, Bool),
        Abs(
            "g", FunctionType(Bool, Int),
            Abs(
                "x", Int,
                App(
                    Var("g"),
                    App(Var("f"), Var("x"))
                )
            )
        )
    )
    print(f"Term: {compose}")
    print(f"Type: {typecheck(compose)}")
    print()
    
    # Example 4: Application that type checks
    #    (λx:Int. x) applied to some variable y:Int
    ctx = TypeContext()
    ctx.bindings["y"] = Int
    
    app_term = App(identity, Var("y"))
    print(f"Term: {app_term}")
    print(f"Type: {typecheck(app_term, ctx)}")
    print()
    
    # Example 5: Type error - wrong argument type
    print("=== Type Error Example ===")
    try:
        # Try to apply Int→Int function to Bool argument
        ctx_bad = TypeContext()
        ctx_bad.bindings["z"] = Bool
        bad_app = App(identity, Var("z"))
        print(f"Term: {bad_app}")
        typecheck(bad_app, ctx_bad)
    except TypeError as e:
        print(f"Type Error: {e}")
    print()
    
    # Example 6: Curried function application
    #    ((λx:Int. λy:Int. x) 5) 10  should type check as Int
    print("=== Curried Application ===")
    ctx2 = TypeContext()
    ctx2.bindings["five"] = Int
    ctx2.bindings["ten"] = Int
    
    curried = Abs("x", Int, Abs("y", Int, Var("x")))
    partial = App(curried, Var("five"))
    full = App(partial, Var("ten"))
    
    print(f"Curried function: {curried}")
    print(f"Type: {typecheck(curried)}")
    print(f"Partial application: {partial}")
    print(f"Type: {typecheck(partial, ctx2)}")
    print(f"Full application: {full}")
    print(f"Type: {typecheck(full, ctx2)}")

if __name__ == "__main__":
    main()

