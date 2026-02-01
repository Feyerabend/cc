from dataclasses import dataclass
from typing import Dict, Set, Optional, List as PyList
from copy import deepcopy

# ============== Enhanced Type Definitions ==============

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
        return hash(("var", self.name))
    
    def __eq__(self, other):
        return isinstance(other, TypeVar) and self.name == other.name

@dataclass
class TypeConst(Type):
    """Type constant: Int, Bool, String"""
    name: str
    
    def __str__(self):
        return self.name
    
    def __hash__(self):
        return hash(("const", self.name))
    
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
        return hash(("func", self.param_type, self.return_type))
    
    def __eq__(self, other):
        return (isinstance(other, FunctionType) and 
                self.param_type == other.param_type and 
                self.return_type == other.return_type)

@dataclass
class TypeApplication(Type):
    """Type application: T α (e.g., List Int, Maybe Bool)"""
    constructor: str  # e.g., "List", "Maybe", "Pair"
    args: PyList[Type]
    
    def __str__(self):
        if not self.args:
            return self.constructor
        args_str = " ".join(str(arg) if not isinstance(arg, (FunctionType, TypeApplication)) 
                           else f"({arg})" for arg in self.args)
        return f"{self.constructor} {args_str}"
    
    def __hash__(self):
        return hash(("app", self.constructor, tuple(self.args)))
    
    def __eq__(self, other):
        return (isinstance(other, TypeApplication) and 
                self.constructor == other.constructor and 
                self.args == other.args)

@dataclass
class ForallType(Type):
    """Universal quantification: ∀α. τ"""
    type_var: str
    body: Type
    
    def __str__(self):
        return f"∀{self.type_var}. {self.body}"
    
    def __hash__(self):
        return hash(("forall", self.type_var, self.body))
    
    def __eq__(self, other):
        return (isinstance(other, ForallType) and 
                self.type_var == other.type_var and 
                self.body == other.body)

# ============== Term Definitions ==============

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
    """Abstraction: λx:τ. e (with optional type annotation)"""
    param: str
    param_type: Optional[Type]
    body: Term
    
    def __str__(self):
        if self.param_type:
            return f"(λ{self.param}:{self.param_type}. {self.body})"
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

@dataclass
class TypeAbs(Term):
    """Type abstraction (System F): Λα. e"""
    type_var: str
    body: Term
    
    def __str__(self):
        return f"(Λ{self.type_var}. {self.body})"

@dataclass
class TypeInstantiation(Term):
    """Type application/instantiation: e [τ]"""
    term: Term
    type_arg: Type
    
    def __str__(self):
        return f"({self.term} [{self.type_arg}])"

@dataclass
class Construct(Term):
    """Data constructor: Cons, Nil, Some, None, Pair"""
    name: str
    args: PyList[Term]
    
    def __str__(self):
        if not self.args:
            return self.name
        args_str = " ".join(str(arg) for arg in self.args)
        return f"({self.name} {args_str})"

@dataclass
class Match(Term):
    """Pattern matching: match e with | p₁ -> e₁ | p₂ -> e₂"""
    scrutinee: Term
    cases: PyList[tuple[str, PyList[str], Term]]  # (constructor, variables, body)
    
    def __str__(self):
        cases_str = " | ".join(
            f"{cons} {' '.join(vars)} -> {body}" 
            for cons, vars, body in self.cases
        )
        return f"(match {self.scrutinee} with {cases_str})"

# ============== Type Inference with Polymorphism ==============

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
                return self.apply(self.mapping[typ.name])
            return typ
        elif isinstance(typ, TypeConst):
            return typ
        elif isinstance(typ, FunctionType):
            return FunctionType(
                self.apply(typ.param_type),
                self.apply(typ.return_type)
            )
        elif isinstance(typ, TypeApplication):
            return TypeApplication(
                typ.constructor,
                [self.apply(arg) for arg in typ.args]
            )
        elif isinstance(typ, ForallType):
            # Don't substitute bound variables
            if typ.type_var in self.mapping:
                # Create new substitution without this binding
                new_mapping = {k: v for k, v in self.mapping.items() 
                             if k != typ.type_var}
                return ForallType(typ.type_var, 
                                Substitution(new_mapping).apply(typ.body))
            return ForallType(typ.type_var, self.apply(typ.body))
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
    elif isinstance(typ, TypeApplication):
        result = set()
        for arg in typ.args:
            result.update(free_type_vars(arg))
        return result
    elif isinstance(typ, ForallType):
        return free_type_vars(typ.body) - {typ.type_var}
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
    elif isinstance(typ, TypeApplication):
        return any(occurs_check(var, arg, subst) for arg in typ.args)
    elif isinstance(typ, ForallType):
        if typ.type_var == var:
            return False  # Bound variable shadows
        return occurs_check(var, typ.body, subst)
    return False

def unify(t1: Type, t2: Type, subst: Substitution) -> Substitution:
    """Unify two types"""
    t1 = subst.apply(t1)
    t2 = subst.apply(t2)
    
    if t1 == t2:
        return subst
    
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
    
    if isinstance(t1, FunctionType) and isinstance(t2, FunctionType):
        subst = unify(t1.param_type, t2.param_type, subst)
        subst = unify(t1.return_type, t2.return_type, subst)
        return subst
    
    if isinstance(t1, TypeApplication) and isinstance(t2, TypeApplication):
        if t1.constructor != t2.constructor or len(t1.args) != len(t2.args):
            raise TypeInferenceError(f"Cannot unify {t1} with {t2}")
        for arg1, arg2 in zip(t1.args, t2.args):
            subst = unify(arg1, arg2, subst)
        return subst
    
    if isinstance(t1, TypeConst) and isinstance(t2, TypeConst):
        if t1.name == t2.name:
            return subst
    
    raise TypeInferenceError(f"Cannot unify {t1} with {t2}")

def generalize(env: TypeEnvironment, typ: Type) -> TypeScheme:
    """Generalize a type to a type scheme"""
    env_vars = env.free_type_vars()
    type_vars = free_type_vars(typ) - env_vars
    return TypeScheme(type_vars, typ)

def instantiate(scheme: TypeScheme, gen: TypeVarGenerator) -> Type:
    """Instantiate a type scheme with fresh type variables"""
    if not scheme.type_vars:
        return scheme.typ
    
    fresh_vars = {var: gen.fresh() for var in scheme.type_vars}
    
    def subst_type(typ: Type) -> Type:
        if isinstance(typ, TypeVar) and typ.name in fresh_vars:
            return fresh_vars[typ.name]
        elif isinstance(typ, FunctionType):
            return FunctionType(
                subst_type(typ.param_type),
                subst_type(typ.return_type)
            )
        elif isinstance(typ, TypeApplication):
            return TypeApplication(typ.constructor, [subst_type(arg) for arg in typ.args])
        elif isinstance(typ, ForallType):
            if typ.type_var in fresh_vars:
                return ForallType(typ.type_var, subst_type(typ.body))
            return ForallType(typ.type_var, subst_type(typ.body))
        return typ
    
    return subst_type(scheme.typ)

def infer(term: Term, env: TypeEnvironment, gen: TypeVarGenerator) -> tuple[Substitution, Type]:
    """Infer the type of a term with polymorphism support"""
    
    if isinstance(term, Var):
        scheme = env.lookup(term.name)
        if scheme is None:
            raise TypeInferenceError(f"Unbound variable: {term.name}")
        typ = instantiate(scheme, gen)
        return Substitution(), typ
    
    elif isinstance(term, Abs):
        if term.param_type:
            param_type = term.param_type
        else:
            param_type = gen.fresh()
        
        param_scheme = TypeScheme(set(), param_type)
        new_env = env.extend(term.param, param_scheme)
        
        subst, body_type = infer(term.body, new_env, gen)
        
        func_type = FunctionType(subst.apply(param_type), body_type)
        return subst, func_type
    
    elif isinstance(term, App):
        subst1, func_type = infer(term.func, env, gen)
        env1 = TypeEnvironment({k: v for k, v in env.bindings.items()})
        subst2, arg_type = infer(term.arg, env1, gen)
        
        result_type = gen.fresh()
        
        subst3 = unify(
            subst2.apply(func_type),
            FunctionType(arg_type, result_type),
            subst2.compose(subst1)
        )
        
        return subst3, subst3.apply(result_type)
    
    elif isinstance(term, Let):
        subst1, value_type = infer(term.value, env, gen)
        
        env1 = TypeEnvironment({k: v for k, v in env.bindings.items()})
        value_scheme = generalize(env1, subst1.apply(value_type))
        
        new_env = env.extend(term.var, value_scheme)
        subst2, body_type = infer(term.body, new_env, gen)
        
        return subst2.compose(subst1), body_type
    
    elif isinstance(term, TypeAbs):
        # System F style type abstraction
        # Infer body type (type variable is in scope but unconstrained)
        subst, body_type = infer(term.body, env, gen)
        # Return ∀α. τ
        return subst, ForallType(term.type_var, body_type)
    
    elif isinstance(term, TypeInstantiation):
        # Type application: instantiate polymorphic type
        subst, term_type = infer(term.term, env, gen)
        
        if not isinstance(term_type, ForallType):
            raise TypeInferenceError(
                f"Type application requires polymorphic type, got {term_type}"
            )
        
        # Substitute type argument for type variable
        type_subst = Substitution({term_type.type_var: term.type_arg})
        result_type = type_subst.apply(term_type.body)
        
        return subst, result_type
    
    elif isinstance(term, Construct):
        # Look up constructor type
        scheme = env.lookup(term.name)
        if scheme is None:
            raise TypeInferenceError(f"Unknown constructor: {term.name}")
        
        cons_type = instantiate(scheme, gen)
        
        # Apply constructor to arguments
        subst = Substitution()
        current_type = cons_type
        
        for arg in term.args:
            if not isinstance(current_type, FunctionType):
                raise TypeInferenceError(
                    f"Constructor {term.name} applied to too many arguments"
                )
            
            arg_subst, arg_type = infer(arg, env, gen)
            subst = subst.compose(arg_subst)
            
            subst = unify(current_type.param_type, arg_type, subst)
            current_type = subst.apply(current_type.return_type)
        
        return subst, current_type
    
    elif isinstance(term, Match):
        # Infer scrutinee type
        subst1, scrut_type = infer(term.scrutinee, env, gen)
        
        # Infer each case
        result_type = None
        final_subst = subst1
        
        for cons_name, vars, body in term.cases:
            # Look up constructor type
            cons_scheme = env.lookup(cons_name)
            if cons_scheme is None:
                raise TypeInferenceError(f"Unknown constructor: {cons_name}")
            
            cons_type = instantiate(cons_scheme, gen)
            
            # Extract argument types from constructor
            case_env = env
            arg_types = []
            current = cons_type
            
            for var in vars:
                if not isinstance(current, FunctionType):
                    raise TypeInferenceError(
                        f"Constructor {cons_name} has wrong number of arguments"
                    )
                arg_types.append(current.param_type)
                case_env = case_env.extend(var, TypeScheme(set(), current.param_type))
                current = current.return_type
            
            # Unify constructor result with scrutinee type
            final_subst = unify(current, scrut_type, final_subst)
            
            # Infer case body
            case_subst, case_type = infer(body, case_env, gen)
            final_subst = final_subst.compose(case_subst)
            
            # All cases must have same type
            if result_type is None:
                result_type = case_type
            else:
                final_subst = unify(result_type, case_type, final_subst)
                result_type = final_subst.apply(result_type)
        
        if result_type is None:
            raise TypeInferenceError("Match must have at least one case")
        
        return final_subst, result_type
    
    raise TypeInferenceError(f"Unknown term type: {type(term)}")

# ============== Examples ==============

def infer_and_print(term: Term, env: TypeEnvironment = None, title: str = None):
    """Helper to infer and print type"""
    if env is None:
        env = TypeEnvironment()
    
    if title:
        print(f"=== {title} ===")
    
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

def setup_polymorphic_env() -> TypeEnvironment:
    """Set up environment with polymorphic data types"""
    env = TypeEnvironment()
    
    # Basic types
    env = env.extend("0", TypeScheme(set(), TypeConst("Int")))
    env = env.extend("1", TypeScheme(set(), TypeConst("Int")))
    env = env.extend("true", TypeScheme(set(), TypeConst("Bool")))
    env = env.extend("false", TypeScheme(set(), TypeConst("Bool")))
    
    # List constructors
    # Nil : ∀α. List α
    alpha = TypeVar("α")
    env = env.extend("Nil", TypeScheme(
        {"α"},
        TypeApplication("List", [alpha])
    ))
    
    # Cons : ∀α. α → List α → List α
    env = env.extend("Cons", TypeScheme(
        {"α"},
        FunctionType(
            alpha,
            FunctionType(
                TypeApplication("List", [alpha]),
                TypeApplication("List", [alpha])
            )
        )
    ))
    
    # Maybe constructors
    # None : ∀α. Maybe α
    env = env.extend("None", TypeScheme(
        {"α"},
        TypeApplication("Maybe", [alpha])
    ))
    
    # Some : ∀α. α → Maybe α
    env = env.extend("Some", TypeScheme(
        {"α"},
        FunctionType(alpha, TypeApplication("Maybe", [alpha]))
    ))
    
    # Pair constructor
    # Pair : ∀α β. α → β → Pair α β
    beta = TypeVar("β")
    env = env.extend("Pair", TypeScheme(
        {"α", "β"},
        FunctionType(
            alpha,
            FunctionType(
                beta,
                TypeApplication("Pair", [alpha, beta])
            )
        )
    ))
    
    return env

def main():
    print("=== Parametric Polymorphism (Generics) ===\n")
    
    env = setup_polymorphic_env()
    
    # Example 1: Polymorphic identity (System F style)
    # Λα. λx:α. x  :  ∀α. α → α
    poly_id = TypeAbs("α", Abs("x", TypeVar("α"), Var("x")))
    infer_and_print(poly_id, env, "System F Polymorphic Identity")
    
    # Example 2: Type application
    # (Λα. λx:α. x) [Int]  :  Int → Int
    poly_id_int = TypeInstantiation(poly_id, TypeConst("Int"))
    infer_and_print(poly_id_int, env, "Type Application to Int")
    
    # Example 3: Empty list (polymorphic)
    # Nil : List α
    nil = Construct("Nil", [])
    infer_and_print(nil, env, "Empty List")
    
    # Example 4: List of integers
    # Cons 1 (Cons 0 Nil) : List Int
    int_list = Construct("Cons", [
        Var("1"),
        Construct("Cons", [Var("0"), Construct("Nil", [])])
    ])
    infer_and_print(int_list, env, "List of Integers")
    
    # Example 5: Maybe Some value
    # Some 42 : Maybe Int
    maybe_int = Construct("Some", [Var("1")])
    infer_and_print(maybe_int, env, "Maybe Int")
    
    # Example 6: Pair of different types
    # Pair 1 true : Pair Int Bool
    pair_mixed = Construct("Pair", [Var("1"), Var("true")])
    infer_and_print(pair_mixed, env, "Heterogeneous Pair")
    
    # Example 7: Polymorphic function on lists
    # λxs. match xs with | Nil -> 0 | Cons h t -> h
    # This should infer: List Int → Int (if we use 0 as default)
    head_or_zero = Abs(
        "xs",
        None,
        Match(
            Var("xs"),
            [
                ("Nil", [], Var("0")),
                ("Cons", ["h", "t"], Var("h"))
            ]
        )
    )
    infer_and_print(head_or_zero, env, "Head or Zero Function")
    
    # Example 8: Polymorphic const function with explicit types
    # Λα. Λβ. λx:α. λy:β. x  :  ∀α β. α → β → α
    poly_const = TypeAbs("α", 
        TypeAbs("β",
            Abs("x", TypeVar("α"),
                Abs("y", TypeVar("β"), Var("x"))
            )
        )
    )
    infer_and_print(poly_const, env, "Polymorphic Const (System F)")
    
    # Example 9: Pattern matching on Maybe
    # λm. match m with | None -> 0 | Some x -> x
    # Type: Maybe Int → Int
    unwrap_or_zero = Abs(
        "m",
        None,
        Match(
            Var("m"),
            [
                ("None", [], Var("0")),
                ("Some", ["x"], Var("x"))
            ]
        )
    )
    infer_and_print(unwrap_or_zero, env, "Unwrap Maybe or Zero")
    
    # Example 10: Let polymorphism with polymorphic data
    # let empty = Nil in (Cons 1 empty, Cons true empty)
    # Shows Nil can be used at multiple types
    poly_nil_usage = Let(
        "empty",
        Construct("Nil", []),
        Construct("Pair", [
            Construct("Cons", [Var("1"), Var("empty")]),
            Construct("Cons", [Var("true"), Var("empty")])
        ])
    )
    infer_and_print(poly_nil_usage, env, "Let Polymorphism with Nil")

if __name__ == "__main__":
    main()
