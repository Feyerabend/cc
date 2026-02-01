from dataclasses import dataclass
from typing import Dict, Set, Optional, List as PyList
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
    constructor: str
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

@dataclass
class RecursiveType(Type):
    """Recursive type: μα. τ (e.g., μα. 1 + α for natural numbers)"""
    type_var: str
    body: Type
    
    def __str__(self):
        return f"μ{self.type_var}. {self.body}"
    
    def __hash__(self):
        return hash(("mu", self.type_var, self.body))
    
    def __eq__(self, other):
        return (isinstance(other, RecursiveType) and 
                self.type_var == other.type_var and 
                self.body == other.body)



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
class LetRec(Term):
    """Recursive let binding: let rec f = e₁ in e₂"""
    var: str
    var_type: Optional[Type]  # Optional type annotation for recursion
    value: Term
    body: Term
    
    def __str__(self):
        type_str = f":{self.var_type}" if self.var_type else ""
        return f"(let rec {self.var}{type_str} = {self.value} in {self.body})"

@dataclass
class Fix(Term):
    """Fix-point operator: fix f. e"""
    var: str
    body: Term
    
    def __str__(self):
        return f"(fix {self.var}. {self.body})"

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
    """Data constructor: Cons, Nil, Some, None, Pair, Node, Leaf"""
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
    cases: PyList[tuple[str, PyList[str], Term]]
    
    def __str__(self):
        cases_str = " | ".join(
            f"{cons} {' '.join(vars)} -> {body}" 
            for cons, vars, body in self.cases
        )
        return f"(match {self.scrutinee} with {cases_str})"

@dataclass
class IntLit(Term):
    """Integer literal"""
    value: int
    
    def __str__(self):
        return str(self.value)

@dataclass
class BinOp(Term):
    """Binary operation: e₁ op e₂"""
    op: str  # "+", "-", "*", "=", "<", etc.
    left: Term
    right: Term
    
    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

@dataclass
class IfThenElse(Term):
    """Conditional: if e₁ then e₂ else e₃"""
    cond: Term
    then_branch: Term
    else_branch: Term
    
    def __str__(self):
        return f"(if {self.cond} then {self.then_branch} else {self.else_branch})"



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
            if typ.type_var in self.mapping:
                new_mapping = {k: v for k, v in self.mapping.items() 
                             if k != typ.type_var}
                return ForallType(typ.type_var, 
                                Substitution(new_mapping).apply(typ.body))
            return ForallType(typ.type_var, self.apply(typ.body))
        elif isinstance(typ, RecursiveType):
            if typ.type_var in self.mapping:
                new_mapping = {k: v for k, v in self.mapping.items() 
                             if k != typ.type_var}
                return RecursiveType(typ.type_var,
                                   Substitution(new_mapping).apply(typ.body))
            return RecursiveType(typ.type_var, self.apply(typ.body))
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
    elif isinstance(typ, RecursiveType):
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
            return False
        return occurs_check(var, typ.body, subst)
    elif isinstance(typ, RecursiveType):
        if typ.type_var == var:
            return False
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
        elif isinstance(typ, RecursiveType):
            if typ.type_var in fresh_vars:
                return RecursiveType(typ.type_var, subst_type(typ.body))
            return RecursiveType(typ.type_var, subst_type(typ.body))
        return typ
    
    return subst_type(scheme.typ)

def infer(term: Term, env: TypeEnvironment, gen: TypeVarGenerator) -> tuple[Substitution, Type]:
    """Infer the type of a term with recursion support"""
    
    if isinstance(term, Var):
        scheme = env.lookup(term.name)
        if scheme is None:
            raise TypeInferenceError(f"Unbound variable: {term.name}")
        typ = instantiate(scheme, gen)
        return Substitution(), typ
    
    elif isinstance(term, IntLit):
        return Substitution(), TypeConst("Int")
    
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
    
    elif isinstance(term, LetRec):
        # Create fresh type variable for recursive binding
        if term.var_type:
            rec_type = term.var_type
        else:
            rec_type = gen.fresh()
        
        # Add recursive variable to environment (monomorphic during inference)
        rec_scheme = TypeScheme(set(), rec_type)
        rec_env = env.extend(term.var, rec_scheme)
        
        # Infer value type in environment with recursive binding
        subst1, value_type = infer(term.value, rec_env, gen)
        
        # Unify inferred type with declared/assumed type
        subst2 = unify(subst1.apply(rec_type), value_type, subst1)
        
        # Generalize for use in body
        final_type = subst2.apply(rec_type)
        value_scheme = generalize(env, final_type)
        
        # Infer body with generalized recursive binding
        new_env = env.extend(term.var, value_scheme)
        subst3, body_type = infer(term.body, new_env, gen)
        
        return subst3.compose(subst2), body_type
    
    elif isinstance(term, Fix):
        # fix for fix
        # fix has type: (τ → τ) → τ
        # The body should be a function that takes something of type τ and returns τ
        # And fix returns a value of type τ
        
        # Generate fresh type variable for the fixed point
        fix_type = gen.fresh()
        
        # The variable f should have type τ
        fix_scheme = TypeScheme(set(), fix_type)
        fix_env = env.extend(term.var, fix_scheme)
        
        # Infer body type - it should be τ
        subst, body_type = infer(term.body, fix_env, gen)
        
        # Body type must equal fix_type
        subst = unify(subst.apply(fix_type), body_type, subst)
        
        return subst, subst.apply(fix_type)
    
    elif isinstance(term, BinOp):
        subst1, left_type = infer(term.left, env, gen)
        subst2, right_type = infer(term.right, env, gen)
        
        subst = subst2.compose(subst1)
        
        # Arithmetic operations
        if term.op in ["+", "-", "*", "/"]:
            subst = unify(left_type, TypeConst("Int"), subst)
            subst = unify(right_type, TypeConst("Int"), subst)
            return subst, TypeConst("Int")
        
        # Comparison operations
        elif term.op in ["=", "<", ">", "<=", ">="]:
            subst = unify(left_type, TypeConst("Int"), subst)
            subst = unify(right_type, TypeConst("Int"), subst)
            return subst, TypeConst("Bool")
        
        else:
            raise TypeInferenceError(f"Unknown operator: {term.op}")
    
    elif isinstance(term, IfThenElse):
        subst1, cond_type = infer(term.cond, env, gen)
        subst1 = unify(cond_type, TypeConst("Bool"), subst1)
        
        subst2, then_type = infer(term.then_branch, env, gen)
        subst3, else_type = infer(term.else_branch, env, gen)
        
        subst = subst3.compose(subst2).compose(subst1)
        subst = unify(subst.apply(then_type), subst.apply(else_type), subst)
        
        return subst, subst.apply(then_type)
    
    elif isinstance(term, TypeAbs):
        subst, body_type = infer(term.body, env, gen)
        return subst, ForallType(term.type_var, body_type)
    
    elif isinstance(term, TypeInstantiation):
        subst, term_type = infer(term.term, env, gen)
        
        if not isinstance(term_type, ForallType):
            raise TypeInferenceError(
                f"Type application requires polymorphic type, got {term_type}"
            )
        
        type_subst = Substitution({term_type.type_var: term.type_arg})
        result_type = type_subst.apply(term_type.body)
        
        return subst, result_type
    
    elif isinstance(term, Construct):
        scheme = env.lookup(term.name)
        if scheme is None:
            raise TypeInferenceError(f"Unknown constructor: {term.name}")
        
        cons_type = instantiate(scheme, gen)
        
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
        subst1, scrut_type = infer(term.scrutinee, env, gen)
        
        result_type = None
        final_subst = subst1
        
        for cons_name, vars, body in term.cases:
            cons_scheme = env.lookup(cons_name)
            if cons_scheme is None:
                raise TypeInferenceError(f"Unknown constructor: {cons_name}")
            
            cons_type = instantiate(cons_scheme, gen)
            
            case_env = env
            current = cons_type
            
            for var in vars:
                if not isinstance(current, FunctionType):
                    raise TypeInferenceError(
                        f"Constructor {cons_name} has wrong number of arguments"
                    )
                case_env = case_env.extend(var, TypeScheme(set(), current.param_type))
                current = current.return_type
            
            final_subst = unify(current, scrut_type, final_subst)
            
            case_subst, case_type = infer(body, case_env, gen)
            final_subst = final_subst.compose(case_subst)
            
            if result_type is None:
                result_type = case_type
            else:
                final_subst = unify(result_type, case_type, final_subst)
                result_type = final_subst.apply(result_type)
        
        if result_type is None:
            raise TypeInferenceError("Match must have at least one case")
        
        return final_subst, result_type
    
    raise TypeInferenceError(f"Unknown term type: {type(term)}")



def infer_and_print(term: Term, env: TypeEnvironment = None, title: str = None):
    """Helper to infer and print type"""
    if env is None:
        env = TypeEnvironment()
    
    if title:
        print(f"- {title} -")
    
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

def setup_env() -> TypeEnvironment:
    """Set up environment with standard types and constructors"""
    env = TypeEnvironment()
    
    # List constructors
    alpha = TypeVar("α")
    env = env.extend("Nil", TypeScheme(
        {"α"},
        TypeApplication("List", [alpha])
    ))
    
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
    
    # Tree constructors
    # Leaf : ∀α. α → Tree α
    env = env.extend("Leaf", TypeScheme(
        {"α"},
        FunctionType(alpha, TypeApplication("Tree", [alpha]))
    ))
    
    # Node : ∀α. Tree α → Tree α → Tree α
    env = env.extend("Node", TypeScheme(
        {"α"},
        FunctionType(
            TypeApplication("Tree", [alpha]),
            FunctionType(
                TypeApplication("Tree", [alpha]),
                TypeApplication("Tree", [alpha])
            )
        )
    ))
    
    return env

def main():
    print("Recursive Types and Functions\n")
    
    env = setup_env()
    
    # Example 1: Simple recursive function - factorial
    #    let rec fact = λn. if n = 0 then 1 else n * fact (n - 1) in fact
    factorial = LetRec(
        "fact",
        None,
        Abs("n", None,
            IfThenElse(
                BinOp("=", Var("n"), IntLit(0)),
                IntLit(1),
                BinOp("*", Var("n"),
                      App(Var("fact"), BinOp("-", Var("n"), IntLit(1))))
            )
        ),
        Var("fact")
    )
    infer_and_print(factorial, env, "Factorial Function")
    
    # Example 2: Fibonacci
    #    let rec fib = λn. if n < 2 then n else fib(n-1) + fib(n-2) in fib
    fibonacci = LetRec(
        "fib",
        None,
        Abs("n", None,
            IfThenElse(
                BinOp("<", Var("n"), IntLit(2)),
                Var("n"),
                BinOp("+",
                      App(Var("fib"), BinOp("-", Var("n"), IntLit(1))),
                      App(Var("fib"), BinOp("-", Var("n"), IntLit(2))))
            )
        ),
        Var("fib")
    )
    infer_and_print(fibonacci, env, "Fibonacci Function")
    
    # Example 3: Recursive list sum
    #    let rec sum = λxs. match xs with | Nil -> 0 | Cons h t -> h + sum t
    list_sum = LetRec(
        "sum",
        None,
        Abs("xs", None,
            Match(Var("xs"), [
                ("Nil", [], IntLit(0)),
                ("Cons", ["h", "t"], BinOp("+", Var("h"), App(Var("sum"), Var("t"))))
            ])
        ),
        Var("sum")
    )
    infer_and_print(list_sum, env, "List Sum Function")
    
    # Example 4: Polymorphic list length
    #    let rec length = λxs. match xs with | Nil -> 0 | Cons h t -> 1 + length t
    list_length = LetRec(
        "length",
        None,
        Abs("xs", None,
            Match(Var("xs"), [
                ("Nil", [], IntLit(0)),
                ("Cons", ["h", "t"], BinOp("+", IntLit(1), App(Var("length"), Var("t"))))
            ])
        ),
        Var("length")
    )
    infer_and_print(list_length, env, "Polymorphic List Length")
    
    # Example 5: Map function
    #    let rec map = λf. λxs. match xs with 
    #      | Nil -> Nil 
    #      | Cons h t -> Cons (f h) (map f t)
    map_func = LetRec(
        "map",
        None,
        Abs("f", None,
            Abs("xs", None,
                Match(Var("xs"), [
                    ("Nil", [], Construct("Nil", [])),
                    ("Cons", ["h", "t"], 
                     Construct("Cons", [
                         App(Var("f"), Var("h")),
                         App(App(Var("map"), Var("f")), Var("t"))
                     ]))
                ])
            )
        ),
        Var("map")
    )
    infer_and_print(map_func, env, "Polymorphic Map Function")
    
    # Example 6: Tree depth
    #    let rec depth = λt. match t with
    #      | Leaf x -> 1
    #      | Node l r -> 1 + (if depth l > depth r then depth l else depth r)
    tree_depth = LetRec(
        "depth",
        None,
        Abs("t", None,
            Match(Var("t"), [
                ("Leaf", ["x"], IntLit(1)),
                ("Node", ["l", "r"],
                 BinOp("+", IntLit(1),
                       IfThenElse(
                           BinOp(">", App(Var("depth"), Var("l")), 
                                      App(Var("depth"), Var("r"))),
                           App(Var("depth"), Var("l")),
                           App(Var("depth"), Var("r"))
                       )))
            ])
        ),
        Var("depth")
    )
    infer_and_print(tree_depth, env, "Tree Depth Function")
    
    # Example 7: Using fix combinator
    #    fix f. λn. if n = 0 then 1 else n * f (n - 1)
    fix_factorial = Fix(
        "f",
        Abs("n", None,
            IfThenElse(
                BinOp("=", Var("n"), IntLit(0)),
                IntLit(1),
                BinOp("*", Var("n"),
                      App(Var("f"), BinOp("-", Var("n"), IntLit(1))))
            )
        )
    )
    infer_and_print(fix_factorial, env, "Factorial with Fix Combinator")
    
    # Example 8: Mutually recursive functions (using let rec twice)
    #    let rec even = λn. if n = 0 then true else odd (n - 1) in
    #    let rec odd = λn. if n = 0 then false else even (n - 1) in
    #    even
    # Note: This is a simplified version; true mutual recursion would need special support
    
    # Example 9: Fold right on lists
    #    let rec foldr = λf. λacc. λxs. match xs with
    #      | Nil -> acc
    #      | Cons h t -> f h (foldr f acc t)
    foldr_func = LetRec(
        "foldr",
        None,
        Abs("f", None,
            Abs("acc", None,
                Abs("xs", None,
                    Match(Var("xs"), [
                        ("Nil", [], Var("acc")),
                        ("Cons", ["h", "t"],
                         App(App(Var("f"), Var("h")),
                             App(App(App(Var("foldr"), Var("f")), Var("acc")), Var("t"))))
                    ])
                )
            )
        ),
        Var("foldr")
    )
    infer_and_print(foldr_func, env, "Fold Right Function")
    
    # Example 10: Using recursive function
    #    let rec sum = ... in sum (Cons 1 (Cons 2 (Cons 3 Nil)))
    sum_usage = LetRec(
        "sum",
        None,
        Abs("xs", None,
            Match(Var("xs"), [
                ("Nil", [], IntLit(0)),
                ("Cons", ["h", "t"], BinOp("+", Var("h"), App(Var("sum"), Var("t"))))
            ])
        ),
        App(Var("sum"),
            Construct("Cons", [
                IntLit(1),
                Construct("Cons", [
                    IntLit(2),
                    Construct("Cons", [IntLit(3), Construct("Nil", [])])
                ])
            ])
        )
    )
    infer_and_print(sum_usage, env, "Using Recursive Sum")

if __name__ == "__main__":
    main()

