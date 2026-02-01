from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List
from copy import deepcopy



@dataclass
class Type:
    """Base class for types"""
    pass

@dataclass
class TypeVar(Type):
    """Type variable: α, β, γ"""
    name: str
    
    def __str__(self):
        return self.name
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return isinstance(other, TypeVar) and self.name == other.name

@dataclass
class TypeConst(Type):
    """Type constant: Int, Bool, String"""
    name: str
    
    def __str__(self):
        return self.name
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return isinstance(other, TypeConst) and self.name == other.name

@dataclass
class FunctionType(Type):
    """Function type: τ₁ → τ₂"""
    param_type: Type
    return_type: Type
    
    def __str__(self):
        param_str = f"({self.param_type})" if isinstance(self.param_type, FunctionType) else str(self.param_type)
        return f"{param_str} → {self.return_type}"
    
    def __hash__(self):
        return hash((self.param_type, self.return_type))
    
    def __eq__(self, other):
        return (isinstance(other, FunctionType) and 
                self.param_type == other.param_type and 
                self.return_type == other.return_type)

@dataclass
class TypeScheme:
    """Polymorphic type: ∀α₁...αₙ. τ"""
    type_vars: Set[str]
    typ: Type
    
    def __str__(self):
        if self.type_vars:
            vars_str = " ".join(sorted(self.type_vars))
            return f"∀{vars_str}. {self.typ}"
        return str(self.typ)



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
    """Abstraction: λx. e (no type annotation!)"""
    param: str
    body: Term
    
    def __str__(self):
        return f"(λ{self.param}. {self.body})"

@dataclass
class App(Term):
    """Application: e₁ e₂"""
    func: Term
    arg: Term
    
    def __str__(self):
        return f"({self.func} {self.arg})"

@dataclass
class Let(Term):
    """Let binding: let x = e₁ in e₂"""
    var: str
    value: Term
    body: Term
    
    def __str__(self):
        return f"(let {self.var} = {self.value} in {self.body})"



class TypeInferenceError(Exception):
    """Type inference error"""
    pass

class Substitution:
    """Type substitution: maps type variables to types"""
    def __init__(self, mapping: Dict[str, Type] = None):
        self.mapping = mapping or {}
    
    def apply(self, typ: Type) -> Type:
        """Apply substitution to a type"""
        if isinstance(typ, TypeVar):
            if typ.name in self.mapping:
                # Follow the chain of substitutions
                return self.apply(self.mapping[typ.name])
            return typ
        elif isinstance(typ, TypeConst):
            return typ
        elif isinstance(typ, FunctionType):
            return FunctionType(
                self.apply(typ.param_type),
                self.apply(typ.return_type)
            )
        return typ
    
    def compose(self, other: 'Substitution') -> 'Substitution':
        """Compose two substitutions"""
        new_mapping = {k: other.apply(v) for k, v in self.mapping.items()}
        new_mapping.update(other.mapping)
        return Substitution(new_mapping)
    
    def __str__(self):
        if not self.mapping:
            return "{}"
        items = [f"{k} ↦ {v}" for k, v in sorted(self.mapping.items())]
        return "{" + ", ".join(items) + "}"

class TypeEnvironment:
    """Type environment: maps variables to type schemes"""
    def __init__(self, bindings: Dict[str, TypeScheme] = None):
        self.bindings = bindings or {}
    
    def extend(self, var: str, scheme: TypeScheme) -> 'TypeEnvironment':
        """Create new environment with additional binding"""
        new_bindings = self.bindings.copy()
        new_bindings[var] = scheme
        return TypeEnvironment(new_bindings)
    
    def lookup(self, var: str) -> Optional[TypeScheme]:
        """Look up variable's type scheme"""
        return self.bindings.get(var)
    
    def free_type_vars(self) -> Set[str]:
        """Get all free type variables in the environment"""
        free_vars = set()
        for scheme in self.bindings.values():
            free_vars.update(free_type_vars(scheme.typ) - scheme.type_vars)
        return free_vars

def free_type_vars(typ: Type) -> Set[str]:
    """Get free type variables in a type"""
    if isinstance(typ, TypeVar):
        return {typ.name}
    elif isinstance(typ, TypeConst):
        return set()
    elif isinstance(typ, FunctionType):
        return free_type_vars(typ.param_type) | free_type_vars(typ.return_type)
    return set()

class TypeVarGenerator:
    """Generate fresh type variables"""
    def __init__(self):
        self.counter = 0
    
    def fresh(self) -> TypeVar:
        """Generate a fresh type variable"""
        var = TypeVar(f"t{self.counter}")
        self.counter += 1
        return var

def occurs_check(var: str, typ: Type, subst: Substitution) -> bool:
    """Check if type variable occurs in type (prevents infinite types)"""
    typ = subst.apply(typ)
    if isinstance(typ, TypeVar):
        return typ.name == var
    elif isinstance(typ, FunctionType):
        return (occurs_check(var, typ.param_type, subst) or 
                occurs_check(var, typ.return_type, subst))
    return False

def unify(t1: Type, t2: Type, subst: Substitution) -> Substitution:
    """
    Unify two types, returning a substitution that makes them equal.
    This is the heart of Hindley-Milner type inference.
    """
    # Apply current substitution
    t1 = subst.apply(t1)
    t2 = subst.apply(t2)
    
    # Same type - nothing to do
    if t1 == t2:
        return subst
    
    # Type variable cases
    if isinstance(t1, TypeVar):
        if occurs_check(t1.name, t2, subst):
            raise TypeInferenceError(f"Infinite type: {t1} = {t2}")
        new_subst = Substitution({t1.name: t2})
        return subst.compose(new_subst)
    
    if isinstance(t2, TypeVar):
        if occurs_check(t2.name, t1, subst):
            raise TypeInferenceError(f"Infinite type: {t2} = {t1}")
        new_subst = Substitution({t2.name: t1})
        return subst.compose(new_subst)
    
    # Function type case
    if isinstance(t1, FunctionType) and isinstance(t2, FunctionType):
        subst = unify(t1.param_type, t2.param_type, subst)
        subst = unify(t1.return_type, t2.return_type, subst)
        return subst
    
    # Type constants must match
    if isinstance(t1, TypeConst) and isinstance(t2, TypeConst):
        if t1.name == t2.name:
            return subst
    
    raise TypeInferenceError(f"Cannot unify {t1} with {t2}")

def generalize(env: TypeEnvironment, typ: Type) -> TypeScheme:
    """
    Generalise a type to a type scheme.
    All type variables free in typ but not in env become quantified.
    """
    env_vars = env.free_type_vars()
    type_vars = free_type_vars(typ) - env_vars
    return TypeScheme(type_vars, typ)

def instantiate(scheme: TypeScheme, gen: TypeVarGenerator) -> Type:
    """
    Instantiate a type scheme with fresh type variables.
    This is where polymorphism happens!
    """
    if not scheme.type_vars:
        return scheme.typ
    
    # Create fresh type variables for each quantified variable
    fresh_vars = {var: gen.fresh() for var in scheme.type_vars}
    
    def subst_type(typ: Type) -> Type:
        if isinstance(typ, TypeVar) and typ.name in fresh_vars:
            return fresh_vars[typ.name]
        elif isinstance(typ, FunctionType):
            return FunctionType(
                subst_type(typ.param_type),
                subst_type(typ.return_type)
            )
        return typ
    
    return subst_type(scheme.typ)

def infer(term: Term, env: TypeEnvironment, gen: TypeVarGenerator) -> tuple[Substitution, Type]:
    """
    Infer the type of a term using Algorithm W (Hindley-Milner).
    Returns a substitution and the inferred type.
    """
    
    if isinstance(term, Var):
        # Look up variable in environment
        scheme = env.lookup(term.name)
        if scheme is None:
            raise TypeInferenceError(f"Unbound variable: {term.name}")
        # Instantiate polymorphic type with fresh variables
        typ = instantiate(scheme, gen)
        return Substitution(), typ
    
    elif isinstance(term, Abs):
        # Generate fresh type variable for parameter
        param_type = gen.fresh()
        
        # Add parameter to environment (monomorphic)
        param_scheme = TypeScheme(set(), param_type)
        new_env = env.extend(term.param, param_scheme)
        
        # Infer body type
        subst, body_type = infer(term.body, new_env, gen)
        
        # Function type is param → body
        func_type = FunctionType(subst.apply(param_type), body_type)
        return subst, func_type
    
    elif isinstance(term, App):
        # Infer function type
        subst1, func_type = infer(term.func, env, gen)
        
        # Infer argument type with updated environment
        env1 = TypeEnvironment({k: v for k, v in env.bindings.items()})
        subst2, arg_type = infer(term.arg, env1, gen)
        
        # Generate fresh type variable for result
        result_type = gen.fresh()
        
        # Unify function type with arg_type → result_type
        subst3 = unify(
            subst2.apply(func_type),
            FunctionType(arg_type, result_type),
            subst2.compose(subst1)
        )
        
        # Return composed substitution and result type
        return subst3, subst3.apply(result_type)
    
    elif isinstance(term, Let):
        # Infer value type
        subst1, value_type = infer(term.value, env, gen)
        
        # Generalize value type (this enables polymorphism!)
        env1 = TypeEnvironment({k: v for k, v in env.bindings.items()})
        value_scheme = generalize(env1, subst1.apply(value_type))
        
        # Infer body type with value bound
        new_env = env.extend(term.var, value_scheme)
        subst2, body_type = infer(term.body, new_env, gen)
        
        return subst2.compose(subst1), body_type
    
    raise TypeInferenceError(f"Unknown term type: {type(term)}")



def infer_and_print(term: Term, env: TypeEnvironment = None):
    """Helper to infer and print type"""
    if env is None:
        env = TypeEnvironment()
    
    gen = TypeVarGenerator()
    try:
        subst, typ = infer(term, env, gen)
        final_type = subst.apply(typ)
        print(f"Term: {term}")
        print(f"Type: {final_type}")
        if subst.mapping:
            print(f"Substitution: {subst}")
        print()
    except TypeInferenceError as e:
        print(f"Term: {term}")
        print(f"Error: {e}")
        print()

def main():
    print("=== Hindley-Milner Type Inference ===\n")
    
    # Example 1: Identity function
    #    λx. x  infers as  α → α
    identity = Abs("x", Var("x"))
    infer_and_print(identity)
    
    # Example 2: Self-application (should fail!)
    #    λx. x x  - this creates infinite type
    print("=== Infinite Type Example ===")
    self_app = Abs("x", App(Var("x"), Var("x")))
    infer_and_print(self_app)
    
    # Example 3: Const function
    #    λx. λy. x  infers as  α → β → α
    const = Abs("x", Abs("y", Var("x")))
    infer_and_print(const)
    
    # Example 4: Function composition
    #    λf. λg. λx. f (g x)  infers as  (β → γ) → (α → β) → α → γ
    compose = Abs("f", 
        Abs("g", 
            Abs("x", 
                App(Var("f"), App(Var("g"), Var("x")))
            )
        )
    )
    infer_and_print(compose)
    
    # Example 5: Let polymorphism!
    #    let id = λx. x in (id id)
    # The id function gets generalized to ∀α. α → α
    # So it can be used at multiple types
    let_poly = Let(
        "id",
        Abs("x", Var("x")),
        App(Var("id"), Var("id"))
    )
    print("=== Let Polymorphism ===")
    infer_and_print(let_poly)
    
    # Example 6: Let polymorphism with multiple uses
    #    let id = λx. x in let y = id 5 in id true
    # Here id is used at type Int → Int and Bool → Bool
    env = TypeEnvironment()
    env = env.extend("5", TypeScheme(set(), TypeConst("Int")))
    env = env.extend("true", TypeScheme(set(), TypeConst("Bool")))
    
    let_multi = Let(
        "id",
        Abs("x", Var("x")),
        Let(
            "y",
            App(Var("id"), Var("5")),
            App(Var("id"), Var("true"))
        )
    )
    infer_and_print(let_multi, env)
    
    # Example 7: Curried application
    #    let f = λx. λy. x in f
    curried = Let(
        "f",
        Abs("x", Abs("y", Var("x"))),
        Var("f")
    )
    infer_and_print(curried)
    
    # Example 8: Demonstrating type inference with concrete types
    #    let add = (+ : Int → Int → Int) in
    #    let double = λx. add x x in
    #    double 5
    env2 = TypeEnvironment()
    env2 = env2.extend("add", TypeScheme(
        set(),
        FunctionType(TypeConst("Int"), 
                    FunctionType(TypeConst("Int"), TypeConst("Int")))
    ))
    env2 = env2.extend("5", TypeScheme(set(), TypeConst("Int")))
    
    double_example = Let(
        "double",
        Abs("x", App(App(Var("add"), Var("x")), Var("x"))),
        App(Var("double"), Var("5"))
    )
    print("Type Inference with Concrete Types")
    infer_and_print(double_example, env2)

if __name__ == "__main__":
    main()
