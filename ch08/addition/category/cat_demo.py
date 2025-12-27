"""
A categorical programming language implementation in Python
Based on category theory primitives: objects, morphisms, functors, and monads
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, Generic
from dataclasses import dataclass


# Type System (Objects in Category)

class Type(ABC):
    """Base class for types (objects in our category)"""
    pass

@dataclass
class UnitType(Type):
    """Unit type (terminal object)"""
    def __repr__(self): return "Unit"

@dataclass
class BoolType(Type):
    """Boolean type"""
    def __repr__(self): return "Bool"

@dataclass
class ProductType(Type):
    """Product type A x B"""
    left: Type
    right: Type
    def __repr__(self): return f"({self.left} x {self.right})"

@dataclass
class FunctionType(Type):
    """Function type A -> B"""
    domain: Type
    codomain: Type
    def __repr__(self): return f"({self.domain} -> {self.codomain})"



# Values

@dataclass
class Value:
    """Runtime values"""
    type: Type
    data: Any
    
    def __repr__(self):
        return f"{self.data}: {self.type}"



# Morphisms (Arrows in Category)

class Morphism(ABC):
    """Base class for morphisms (arrows in our category)"""
    def __init__(self, domain: Type, codomain: Type):
        self.domain = domain
        self.codomain = codomain
    
    @abstractmethod
    def apply(self, value: Value) -> Value:
        """Apply morphism to a value"""
        pass

class Identity(Morphism):
    """Identity morphism: id_A : A -> A"""
    def __init__(self, typ: Type):
        super().__init__(typ, typ)
    
    def apply(self, value: Value) -> Value:
        return value
    
    def __repr__(self):
        return f"id_{self.domain}"

class Composition(Morphism):
    """Composition of morphisms: g o f"""
    def __init__(self, f: Morphism, g: Morphism):
        if f.codomain != g.domain:
            raise TypeError(f"Cannot compose: {f.codomain} != {g.domain}")
        super().__init__(f.domain, g.codomain)
        self.f = f
        self.g = g
    
    def apply(self, value: Value) -> Value:
        return self.g.apply(self.f.apply(value))
    
    def __repr__(self):
        return f"({self.g} o {self.f})"

class Fst(Morphism):
    """First projection: fst : A x B -> A"""
    def __init__(self, left: Type, right: Type):
        super().__init__(ProductType(left, right), left)
    
    def apply(self, value: Value) -> Value:
        if not isinstance(value.type, ProductType):
            raise TypeError(f"Expected product type, got {value.type}")
        return Value(self.codomain, value.data[0])
    
    def __repr__(self):
        return "fst"

class Snd(Morphism):
    """Second projection: snd : A x B -> B"""
    def __init__(self, left: Type, right: Type):
        super().__init__(ProductType(left, right), right)
    
    def apply(self, value: Value) -> Value:
        if not isinstance(value.type, ProductType):
            raise TypeError(f"Expected product type, got {value.type}")
        return Value(self.codomain, value.data[1])
    
    def __repr__(self):
        return "snd"

class Eval(Morphism):
    """Evaluation: eval : (A -> B) x A -> B"""
    def __init__(self, domain: Type, codomain: Type):
        func_type = FunctionType(domain, codomain)
        super().__init__(ProductType(func_type, domain), codomain)
    
    def apply(self, value: Value) -> Value:
        func, arg = value.data
        return func.apply(arg)
    
    def __repr__(self):
        return "eval"

class Lambda(Morphism):
    """Lambda abstraction (custom morphism)"""
    def __init__(self, domain: Type, codomain: Type, func: Callable):
        super().__init__(domain, codomain)
        self.func = func
    
    def apply(self, value: Value) -> Value:
        result = self.func(value.data)
        return Value(self.codomain, result)
    
    def __repr__(self):
        return f"λ: {self.domain} → {self.codomain}"



# Functor Implementation

T = TypeVar('T')
U = TypeVar('U')

class Functor(Generic[T], ABC):
    """Functor type class"""
    
    @abstractmethod
    def fmap(self, f: Callable[[Any], Any]) -> 'Functor':
        """Map a function over the functor"""
        pass

class Maybe(Functor[T]):
    """Maybe functor (Option type)"""
    def __init__(self, value: T | None = None):
        self.value = value
    
    def fmap(self, f: Callable[[T], U]) -> 'Maybe[U]':
        """Functor law: F(f)"""
        if self.value is None:
            return Maybe(None)
        return Maybe(f(self.value))
    
    def __repr__(self):
        return f"Just({self.value})" if self.value is not None else "Nothing"

class ListFunctor(Functor[T]):
    """List functor"""
    def __init__(self, items: list[T]):
        self.items = items
    
    def fmap(self, f: Callable[[T], U]) -> 'ListFunctor[U]':
        """Functor law: F(f)"""
        return ListFunctor([f(x) for x in self.items])
    
    def __repr__(self):
        return f"List{self.items}"



# Monad Implementation

class Monad(Functor[T], ABC):
    """Monad type class"""
    
    @staticmethod
    @abstractmethod
    def return_(value: T) -> 'Monad[T]':
        """Monad return (unit): a -> M a"""
        pass
    
    @abstractmethod
    def bind(self, f: Callable[[T], 'Monad[U]']) -> 'Monad[U]':
        """Monad bind (>>=): M a -> (a -> M b) -> M b"""
        pass

class MaybeMonad(Maybe[T], Monad[T]):
    """Maybe monad"""
    
    @staticmethod
    def return_(value: T) -> 'MaybeMonad[T]':
        """return a = Just a"""
        return MaybeMonad(value)
    
    def bind(self, f: Callable[[T], 'MaybeMonad[U]']) -> 'MaybeMonad[U]':
        """
        Monad bind satisfying laws:
        - Left unit: return a >>= f = f a
        - Right unit: m >>= return = m
        - Associativity: (m >>= f) >>= g = m >>= (λx -> f x >>= g)
        """
        if self.value is None:
            return MaybeMonad(None)
        return f(self.value)
    
    def __repr__(self):
        return f"Just({self.value})" if self.value is not None else "Nothing"

class ListMonad(ListFunctor[T], Monad[T]):
    """List monad"""
    
    @staticmethod
    def return_(value: T) -> 'ListMonad[T]':
        """return a = [a]"""
        return ListMonad([value])
    
    def bind(self, f: Callable[[T], 'ListMonad[U]']) -> 'ListMonad[U]':
        """Monad bind for lists (flatMap)"""
        result = []
        for x in self.items:
            result.extend(f(x).items)
        return ListMonad(result)
    
    def __repr__(self):
        return f"List{self.items}"



# VM and Examples

def demonstrate_category_laws():
    """Demonstrate category laws"""
    print("CATEGORY LAWS DEMONSTRATION")
    
    # Types
    bool_type = BoolType()
    unit_type = UnitType()
    
    # Create a value
    v = Value(bool_type, True)
    print(f"\nOriginal value: {v}")
    
    # Identity law: id o f = f = f o id
    id_bool = Identity(bool_type)
    print(f"\nIdentity: {id_bool.apply(v)}")
    
    # Composition
    f = Lambda(bool_type, bool_type, lambda x: not x)
    g = Lambda(bool_type, bool_type, lambda x: not x)
    
    # f o g
    composed = Composition(f, g)
    print(f"\nComposed (- o -): {composed.apply(v)}")
    
    # Product and projections
    prod_type = ProductType(bool_type, bool_type)
    pair = Value(prod_type, (True, False))
    print(f"\nProduct value: {pair}")
    
    fst_proj = Fst(bool_type, bool_type)
    snd_proj = Snd(bool_type, bool_type)
    print(f"fst: {fst_proj.apply(pair)}")
    print(f"snd: {snd_proj.apply(pair)}")

def demonstrate_functor_laws():
    """Demonstrate functor laws"""
    print("FUNCTOR LAWS DEMONSTRATION")
    
    # F(id) = id
    m = Maybe(42)
    id_func = lambda x: x
    print(f"\nOriginal: {m}")
    print(f"F(id): {m.fmap(id_func)}")
    
    # F(g o f) = F(g) o F(f)
    f = lambda x: x + 1
    g = lambda x: x * 2
    
    # Left side: F(g o f)
    left = m.fmap(lambda x: g(f(x)))
    
    # Right side: F(g) o F(f)
    right = m.fmap(f).fmap(g)
    
    print(f"\nF(g o f) = {left}")
    print(f"F(g) o F(f) = {right}")
    print(f"Equal: {left.value == right.value}")
    
    # List functor
    lst = ListFunctor([1, 2, 3])
    print(f"\nList: {lst}")
    print(f"fmap (+1): {lst.fmap(lambda x: x + 1)}")

def demonstrate_monad_laws():
    """Demonstrate monad laws"""
    print("MONAD LAWS DEMONSTRATION")
    
    # Define some monadic functions
    safe_div = lambda x: MaybeMonad(None) if x == 0 else MaybeMonad(10 / x)
    safe_sqrt = lambda x: MaybeMonad(None) if x < 0 else MaybeMonad(x ** 0.5)
    
    # Left unit: return a >>= f = f a
    a = 5
    left = MaybeMonad.return_(a).bind(safe_div)
    right = safe_div(a)
    print(f"\nLeft unit law:")
    print(f"  return {a} >>= safe_div = {left}")
    print(f"  safe_div {a} = {right}")
    print(f"  Equal: {left.value == right.value}")
    
    # Right unit: m >>= return = m
    m = MaybeMonad(42)
    left = m.bind(MaybeMonad.return_)
    print(f"\nRight unit law:")
    print(f"  {m} >>= return = {left}")
    print(f"  Equal: {left.value == m.value}")
    
    # Associativity: (m >>= f) >>= g = m >>= (λx -> f x >>= g)
    m = MaybeMonad(100)
    left = m.bind(safe_div).bind(safe_sqrt)
    right = m.bind(lambda x: safe_div(x).bind(safe_sqrt))
    print(f"\nAssociativity law:")
    print(f"  ({m} >>= safe_div) >>= safe_sqrt = {left}")
    print(f"  {m} >>= (λx -> safe_div x >>= safe_sqrt) = {right}")
    print(f"  Equal: {left.value == right.value}")
    
    # List monad example
    print(f"\nList monad example:")
    lst = ListMonad([1, 2, 3])
    result = lst.bind(lambda x: ListMonad([x, x * 10]))
    print(f"  {lst} >>= λx -> [x, x*10] = {result}")

def practical_example():
    """A practical example: safe computation pipeline"""
    print("PRACTICAL EXAMPLE: Safe Computation Pipeline")
    
    # Chain of operations that might fail
    def parse_int(s: str) -> MaybeMonad[int]:
        try:
            return MaybeMonad(int(s))
        except:
            return MaybeMonad(None)
    
    def safe_reciprocal(x: int) -> MaybeMonad[float]:
        return MaybeMonad(None) if x == 0 else MaybeMonad(1.0 / x)
    
    def double(x: float) -> MaybeMonad[float]:
        return MaybeMonad(x * 2)
    
    # Compose operations monadically
    inputs = ["10", "0", "not_a_number", "5"]
    
    for inp in inputs:
        result = (parse_int(inp)
                 .bind(safe_reciprocal)
                 .bind(double))
        print(f"  Process '{inp}': {result}")


# Natural Transformations

class NaturalTransformation(ABC):
    """Natural transformation between functors"""
    
    @abstractmethod
    def transform(self, fa: Functor[T]) -> Functor[T]:
        """Transform F[A] -> G[A]"""
        pass

class MaybeToList(NaturalTransformation):
    """Natural transformation: Maybe -> List"""
    
    def transform(self, ma: Maybe[T]) -> ListFunctor[T]:
        if ma.value is None:
            return ListFunctor([])
        return ListFunctor([ma.value])
    
    def __repr__(self):
        return "Maybe → List"


# Applicative Functor

class Applicative(Functor[T], ABC):
    """Applicative functor"""
    
    @staticmethod
    @abstractmethod
    def pure(value: T) -> 'Applicative[T]':
        """Lift a value into the applicative"""
        pass
    
    @abstractmethod
    def ap(self, ff: 'Applicative[Callable[[T], U]]') -> 'Applicative[U]':
        """Apply a wrapped function to a wrapped value"""
        pass

class MaybeApplicative(MaybeMonad[T], Applicative[T]):
    """Maybe as an applicative functor"""
    
    @staticmethod
    def pure(value: T) -> 'MaybeApplicative[T]':
        return MaybeApplicative(value)
    
    def ap(self, ff: 'MaybeApplicative[Callable[[T], U]]') -> 'MaybeApplicative[U]':
        if ff.value is None or self.value is None:
            return MaybeApplicative(None)
        return MaybeApplicative(ff.value(self.value))



# Monoid

class Monoid(ABC):
    """Monoid structure: (M, mempty, mappend)"""
    
    @staticmethod
    @abstractmethod
    def mempty() -> 'Monoid':
        """Identity element"""
        pass
    
    @abstractmethod
    def mappend(self, other: 'Monoid') -> 'Monoid':
        """Associative binary operation"""
        pass

class Sum(Monoid):
    """Sum monoid (integers under addition)"""
    def __init__(self, value: int):
        self.value = value
    
    @staticmethod
    def mempty() -> 'Sum':
        return Sum(0)
    
    def mappend(self, other: 'Sum') -> 'Sum':
        return Sum(self.value + other.value)
    
    def __repr__(self):
        return f"Sum({self.value})"

class Product(Monoid):
    """Product monoid (integers under multiplication)"""
    def __init__(self, value: int):
        self.value = value
    
    @staticmethod
    def mempty() -> 'Product':
        return Product(1)
    
    def mappend(self, other: 'Product') -> 'Product':
        return Product(self.value * other.value)
    
    def __repr__(self):
        return f"Product({self.value})"


# Free Monad (for building DSLs)

class Free(Generic[T]):
    """Free monad for building EDSLs"""
    pass

class Pure(Free[T]):
    """Pure value in free monad"""
    def __init__(self, value: T):
        self.value = value
    
    def __repr__(self):
        return f"Pure({self.value})"

class Impure(Free[T]):
    """Impure computation in free monad"""
    def __init__(self, functor: Functor, continuation: Callable):
        self.functor = functor
        self.continuation = continuation
    
    def __repr__(self):
        return f"Impure({self.functor}, ...)"


# Writer Monad (for logging)

class Writer(Monad[T]):
    """Writer monad for computations with logging"""
    def __init__(self, value: T, log: list[str]):
        self.value = value
        self.log = log
    
    @staticmethod
    def return_(value: T) -> 'Writer[T]':
        return Writer(value, [])
    
    def bind(self, f: Callable[[T], 'Writer[U]']) -> 'Writer[U]':
        result = f(self.value)
        return Writer(result.value, self.log + result.log)
    
    def fmap(self, f: Callable[[T], U]) -> 'Writer[U]':
        return Writer(f(self.value), self.log)
    
    def tell(self, message: str) -> 'Writer[T]':
        """Add a log message"""
        return Writer(self.value, self.log + [message])
    
    def __repr__(self):
        return f"Writer({self.value}, {self.log})"


# State Monad

class State(Monad[T]):
    """State monad for stateful computations"""
    def __init__(self, run_state: Callable[[Any], tuple[T, Any]]):
        self.run_state = run_state
    
    @staticmethod
    def return_(value: T) -> 'State[T]':
        return State(lambda s: (value, s))
    
    def bind(self, f: Callable[[T], 'State[U]']) -> 'State[U]':
        def new_state(s):
            value, new_s = self.run_state(s)
            return f(value).run_state(new_s)
        return State(new_state)
    
    def fmap(self, f: Callable[[T], U]) -> 'State[U]':
        return State(lambda s: (f(self.run_state(s)[0]), self.run_state(s)[1]))
    
    @staticmethod
    def get() -> 'State[Any]':
        """Get the current state"""
        return State(lambda s: (s, s))
    
    @staticmethod
    def put(new_state: Any) -> 'State[None]':
        """Set the state"""
        return State(lambda s: (None, new_state))
    
    def eval(self, initial_state: Any) -> T:
        """Run the stateful computation"""
        return self.run_state(initial_state)[0]
    
    def exec(self, initial_state: Any) -> Any:
        """Run and return final state"""
        return self.run_state(initial_state)[1]


# Extended Demonstrations

def demonstrate_natural_transformations():
    """Demonstrate natural transformations"""
    print("NATURAL TRANSFORMATIONS")
    
    nt = MaybeToList()
    
    m1 = Maybe(42)
    m2 = Maybe(None)
    
    print(f"\n{nt}")
    print(f"  {m1} → {nt.transform(m1)}")
    print(f"  {m2} → {nt.transform(m2)}")
    
    # Naturality condition: fmap f . transform = transform . fmap f
    f = lambda x: x * 2
    left = nt.transform(m1).fmap(f)
    right = nt.transform(m1.fmap(f))
    print(f"\nNaturality check:")
    print(f"  fmap f . transform = {left}")
    print(f"  transform . fmap f = {right}")

def demonstrate_applicative():
    """Demonstrate applicative functors"""
    print("APPLICATIVE FUNCTORS")
    
    # Apply a wrapped function to wrapped values
    add = lambda x: lambda y: x + y
    
    m1 = MaybeApplicative(5)
    m2 = MaybeApplicative(3)
    mf = MaybeApplicative(add)
    
    # <*> operator simulation
    result = m2.ap(m1.ap(mf))
    print(f"\nApplicative application:")
    print(f"  pure (+) <*> Just 5 <*> Just 3 = {result}")
    
    # With Nothing
    m_none = MaybeApplicative(None)
    result2 = m_none.ap(mf)
    print(f"  Nothing <*> pure (+) = {result2}")

def demonstrate_monoids():
    """Demonstrate monoids"""
    print("MONOIDS")
    
    # Sum monoid
    s1, s2, s3 = Sum(5), Sum(10), Sum(7)
    print(f"\nSum monoid:")
    print(f"  mempty = {Sum.mempty()}")
    print(f"  {s1} <> {s2} = {s1.mappend(s2)}")
    print(f"  ({s1} <> {s2}) <> {s3} = {s1.mappend(s2).mappend(s3)}")
    print(f"  {s1} <> ({s2} <> {s3}) = {s1.mappend(s2.mappend(s3))}")
    
    # Product monoid
    p1, p2, p3 = Product(2), Product(3), Product(4)
    print(f"\nProduct monoid:")
    print(f"  mempty = {Product.mempty()}")
    print(f"  {p1} <> {p2} <> {p3} = {p1.mappend(p2).mappend(p3)}")

def demonstrate_writer_monad():
    """Demonstrate writer monad for logging"""
    print("WRITER MONAD (Logging)")
    
    def add_with_log(x: int) -> Writer[int]:
        return Writer(x + 1, [f"Added 1 to {x}, got {x + 1}"])
    
    def multiply_with_log(x: int) -> Writer[int]:
        return Writer(x * 2, [f"Multiplied {x} by 2, got {x * 2}"])
    
    # Chain operations with logging
    result = (Writer.return_(5)
             .bind(add_with_log)
             .bind(multiply_with_log)
             .bind(add_with_log))
    
    print(f"\nComputation with logging:")
    print(f"  Final value: {result.value}")
    print(f"  Log:")
    for entry in result.log:
        print(f"    - {entry}")

def demonstrate_state_monad():
    """Demonstrate state monad"""
    print("STATE MONAD")
    
    # Stack operations using state monad
    def push(x: int) -> State[None]:
        return State.get().bind(lambda stack: 
               State.put(stack + [x]))
    
    def pop() -> State[int]:
        def pop_impl(stack):
            if not stack:
                return (None, stack)
            return (stack[-1], stack[:-1])
        return State(pop_impl)
    
    # Build a computation
    computation = (push(1)
                  .bind(lambda _: push(2))
                  .bind(lambda _: push(3))
                  .bind(lambda _: pop())
                  .bind(lambda x: State.return_(x)))
    
    result = computation.eval([])
    final_state = computation.exec([])
    
    print(f"\nStack operations:")
    print(f"  push 1, push 2, push 3, pop")
    print(f"  Popped value: {result}")
    print(f"  Final stack: {final_state}")


# Parser Combinators (using Applicative and Monad)

class Parser(Monad[T]):
    """Parser monad for building composable parsers"""
    def __init__(self, parse: Callable[[str], list[tuple[T, str]]]):
        self.parse = parse
    
    @staticmethod
    def return_(value: T) -> 'Parser[T]':
        """Parser that always succeeds without consuming input"""
        return Parser(lambda s: [(value, s)])
    
    def bind(self, f: Callable[[T], 'Parser[U]']) -> 'Parser[U]':
        """Monadic bind for parsers"""
        def parser(s):
            results = []
            for (value, rest) in self.parse(s):
                results.extend(f(value).parse(rest))
            return results
        return Parser(parser)
    
    def fmap(self, f: Callable[[T], U]) -> 'Parser[U]':
        """Map over parser result"""
        return Parser(lambda s: [(f(v), r) for (v, r) in self.parse(s)])
    
    def or_else(self, other: 'Parser[T]') -> 'Parser[T]':
        """Alternative combinator (choice)"""
        return Parser(lambda s: self.parse(s) + other.parse(s))
    
    def many(self) -> 'Parser[list[T]]':
        """Zero or more occurrences"""
        return self.some().or_else(Parser.return_([]))
    
    def some(self) -> 'Parser[list[T]]':
        """One or more occurrences"""
        return self.bind(lambda x: 
               self.many().bind(lambda xs: 
               Parser.return_([x] + xs)))
    
    def run(self, s: str) -> list[tuple[T, str]]:
        """Run the parser on input"""
        return self.parse(s)

# Basic parser primitives
def char(c: str) -> Parser[str]:
    """Parse a specific character"""
    def parse(s):
        if s and s[0] == c:
            return [(c, s[1:])]
        return []
    return Parser(parse)

def digit() -> Parser[int]:
    """Parse a digit"""
    def parse(s):
        if s and s[0].isdigit():
            return [(int(s[0]), s[1:])]
        return []
    return Parser(parse)

def satisfy(pred: Callable[[str], bool]) -> Parser[str]:
    """Parse a character satisfying a predicate"""
    def parse(s):
        if s and pred(s[0]):
            return [(s[0], s[1:])]
        return []
    return Parser(parse)

def string(target: str) -> Parser[str]:
    """Parse a specific string"""
    if not target:
        return Parser.return_("")
    return char(target[0]).bind(lambda c:
           string(target[1:]).bind(lambda cs:
           Parser.return_(c + cs)))

def spaces() -> Parser[str]:
    """Parse zero or more spaces"""
    return satisfy(lambda c: c.isspace()).many().fmap(lambda cs: ''.join(cs))


# Expression Language AST

class Expr(ABC):
    """Abstract expression"""
    @abstractmethod
    def eval(self, env: dict[str, int]) -> int:
        pass

@dataclass
class Num(Expr):
    """Numeric literal"""
    value: int
    
    def eval(self, env):
        return self.value
    
    def __repr__(self):
        return str(self.value)

@dataclass
class Var(Expr):
    """Variable reference"""
    name: str
    
    def eval(self, env):
        return env.get(self.name, 0)
    
    def __repr__(self):
        return self.name

@dataclass
class BinOp(Expr):
    """Binary operation"""
    op: str
    left: Expr
    right: Expr
    
    def eval(self, env):
        l, r = self.left.eval(env), self.right.eval(env)
        if self.op == '+': return l + r
        if self.op == '-': return l - r
        if self.op == '*': return l * r
        if self.op == '/': return l // r if r != 0 else 0
        return 0
    
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


# Expression Parser

def parse_number() -> Parser[Expr]:
    """Parse a number"""
    return digit().some().fmap(lambda ds: Num(int(''.join(map(str, ds)))))

def parse_var() -> Parser[Expr]:
    """Parse a variable (single letter)"""
    return satisfy(lambda c: c.isalpha()).fmap(lambda c: Var(c))

def parse_atom() -> Parser[Expr]:
    """Parse an atomic expression"""
    return parse_number().or_else(parse_var()).or_else(parse_parens())

def parse_parens() -> Parser[Expr]:
    """Parse parenthesized expression"""
    return (char('(').bind(lambda _:
            spaces().bind(lambda _:
            parse_expr().bind(lambda e:
            spaces().bind(lambda _:
            char(')').bind(lambda _:
            Parser.return_(e)))))))

def parse_term() -> Parser[Expr]:
    """Parse a term (handles * and /)"""
    def rest(left):
        op_parser = (spaces().bind(lambda _:
                     (char('*').or_else(char('/'))).bind(lambda op:
                     spaces().bind(lambda _:
                     parse_atom().bind(lambda right:
                     Parser.return_((op, right)))))))
        
        return op_parser.bind(lambda op_right:
               rest(BinOp(op_right[0], left, op_right[1]))).or_else(
               Parser.return_(left))
    
    return parse_atom().bind(rest)

def parse_expr() -> Parser[Expr]:
    """Parse a full expression (handles + and -)"""
    def rest(left):
        op_parser = (spaces().bind(lambda _:
                     (char('+').or_else(char('-'))).bind(lambda op:
                     spaces().bind(lambda _:
                     parse_term().bind(lambda right:
                     Parser.return_((op, right)))))))
        
        return op_parser.bind(lambda op_right:
               rest(BinOp(op_right[0], left, op_right[1]))).or_else(
               Parser.return_(left))
    
    return parse_term().bind(rest)


# Comonad

class Comonad(Generic[T], ABC):
    """Comonad - dual of Monad"""
    
    @abstractmethod
    def extract(self) -> T:
        """Extract the value (dual of return)"""
        pass
    
    @abstractmethod
    def extend(self, f: Callable[['Comonad[T]'], U]) -> 'Comonad[U]':
        """Extend (dual of bind)"""
        pass

class Stream(Comonad[T]):
    """Infinite stream comonad"""
    def __init__(self, head: T, tail: Callable[[], 'Stream[T]']):
        self.head = head
        self._tail = tail
    
    @property
    def tail(self) -> 'Stream[T]':
        return self._tail()
    
    def extract(self) -> T:
        return self.head
    
    def extend(self, f: Callable[['Stream[T]'], U]) -> 'Stream[U]':
        return Stream(f(self), lambda: self.tail.extend(f))
    
    def take(self, n: int) -> list[T]:
        """Take first n elements"""
        if n <= 0:
            return []
        return [self.head] + self.tail.take(n - 1)
    
    def __repr__(self):
        return f"Stream({self.take(5)}...)"

def fibonacci_stream() -> Stream[int]:
    """Create Fibonacci stream"""
    def fib(a: int, b: int) -> Stream[int]:
        return Stream(a, lambda: fib(b, a + b))
    return fib(0, 1)


# Advanced Demonstrations

def demonstrate_parser_combinators():
    """Demonstrate parser combinators"""
    print("PARSER COMBINATORS")
    
    # Parse simple expressions
    expressions = [
        "42",
        "3 + 4",
        "2 * 3 + 4",
        "(1 + 2) * 3",
        "x + y * 2"
    ]
    
    print("\nParsing expressions:")
    for expr_str in expressions:
        results = parse_expr().run(expr_str)
        if results:
            ast, remaining = results[0]
            print(f"  '{expr_str}' → {ast}")
            
            # Evaluate with environment
            if isinstance(ast, (Num, BinOp)):
                env = {'x': 10, 'y': 5}
                result = ast.eval(env)
                print(f"    Eval (x=10, y=5): {result}")
        else:
            print(f"  '{expr_str}' → Parse failed")

def demonstrate_comonad():
    """Demonstrate comonads"""
    print("COMONAD (Fibonacci Stream)")
    
    fib = fibonacci_stream()
    print(f"\nFibonacci stream: {fib}")
    print(f"extract: {fib.extract()}")
    
    # Extend with a function that sums the next 3 elements
    def sum_three(s: Stream[int]) -> int:
        return sum(s.take(3))
    
    summed = fib.extend(sum_three)
    print(f"\nExtend (sum of next 3): {summed}")
    print(f"First 10 sums: {summed.take(10)}")

def demonstrate_complete_pipeline():
    """Demonstrate a complete categorical pipeline"""
    print("COMPLETE CATEGORICAL PIPELINE")
    
    # Parse an expression using parser combinators (Applicative/Monad)
    expr_str = "10 + 20 * 2"
    print(f"\nInput: '{expr_str}'")
    
    # Step 1: Parse (using Parser monad)
    parse_result = parse_expr().run(expr_str)
    if not parse_result:
        print("  Parse failed!")
        return
    
    ast, _ = parse_result[0]
    print(f"  Parsed AST: {ast}")
    
    # Step 2: Evaluate with error handling (using Maybe monad)
    def safe_eval(expr: Expr, env: dict) -> MaybeMonad[int]:
        try:
            result = expr.eval(env)
            return MaybeMonad(result)
        except:
            return MaybeMonad(None)
    
    result = safe_eval(ast, {})
    print(f"  Evaluation result: {result}")
    
    # Step 3: Log the computation (using Writer monad)
    def eval_with_log(expr: Expr, env: dict) -> Writer[int]:
        val = expr.eval(env)
        return Writer(val, [f"Evaluated {expr} = {val}"])
    
    logged = eval_with_log(ast, {})
    print(f"  With logging: {logged}")
    
    # Step 4: Transform result (using Functor)
    doubled = result.fmap(lambda x: x * 2)
    print(f"  Doubled result: {doubled}")
    
    print("\n  Pipeline: Parser -> Maybe -> Writer -> Functor")
    print("  All categorical concepts working together!")

if __name__ == "__main__":
    demonstrate_category_laws()
    demonstrate_functor_laws()
    demonstrate_monad_laws()
    practical_example()
    demonstrate_natural_transformations()
    demonstrate_applicative()
    demonstrate_monoids()
    demonstrate_writer_monad()
    demonstrate_state_monad()
    demonstrate_parser_combinators()
    demonstrate_comonad()
    demonstrate_complete_pipeline()
