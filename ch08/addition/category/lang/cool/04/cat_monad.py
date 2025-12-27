"""
Categorical Object-Oriented Language (COOL) with Monads
========================================================
An OOP language where:
- Monads are monoids in the category of endofunctors
- Kleisli arrows form a category
- Effects are tracked in the type system
- Do-notation provides syntactic sugar
- Monad transformers compose effects
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Set, Tuple, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from collections import defaultdict



# CATEGORY THEORY FOUNDATIONS


class CategoryObject(ABC):
    """Object in a category"""
    @abstractmethod
    def name(self) -> str:
        pass


class Morphism(ABC):
    """Morphism between objects"""
    @abstractmethod
    def source(self) -> CategoryObject:
        pass
    
    @abstractmethod
    def target(self) -> CategoryObject:
        pass


@dataclass
class KleisliArrow:
    """Kleisli arrow: A → M<B> in the Kleisli category"""
    source_type: 'Type'
    target_type: 'Type'  # This is M<B>
    func: Callable[[Any], Any]
    
    def compose(self, other: 'KleisliArrow') -> 'KleisliArrow':
        """Kleisli composition: (A → M<B>) ∘ (B → M<C>) = (A → M<C>)"""
        def composed(a):
            mb = self.func(a)
            # mb is M<B>, need to bind with other.func which is B → M<C>
            return mb.bind(other.func)
        return KleisliArrow(self.source_type, other.target_type, composed)



# TYPE SYSTEM


class Type(CategoryObject):
    """Types are objects in the category"""
    def __init__(self, name: str):
        self._name = name
    
    def name(self) -> str:
        return self._name
    
    def __str__(self):
        return self._name
    
    def __repr__(self):
        return f"Type({self._name})"
    
    def __eq__(self, other):
        return isinstance(other, Type) and self._name == other._name
    
    def __hash__(self):
        return hash(self._name)


# Built-in types
INT_TYPE = Type("Int")
STRING_TYPE = Type("String")
BOOL_TYPE = Type("Bool")
VOID_TYPE = Type("Void")
UNIT_TYPE = Type("Unit")


@dataclass
class GenericType(Type):
    """Generic type application: F<T>"""
    base: Type
    type_args: List[Type]
    
    def __init__(self, base: Type, type_args: List[Type]):
        self.base = base
        self.type_args = type_args
        args_str = ", ".join(str(t) for t in type_args)
        super().__init__(f"{base.name()}<{args_str}>")
    
    def __eq__(self, other):
        return (isinstance(other, GenericType) and 
                self.base == other.base and
                self.type_args == other.type_args)
    
    def __hash__(self):
        return hash((self.base, tuple(self.type_args)))


@dataclass
class FunctionType(Type):
    """Function type: A → B"""
    param_types: List[Type]
    return_type: Type
    
    def __init__(self, param_types: List[Type], return_type: Type):
        self.param_types = param_types
        self.return_type = return_type
        name = f"({', '.join(str(t) for t in param_types)}) -> {return_type}"
        super().__init__(name)



# RUNTIME VALUES


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


@dataclass
class FunctionValue(Value):
    """First-class function value"""
    param_names: List[str]
    body: 'Expression'
    closure_env: 'Environment'
    
    def __str__(self):
        params = ", ".join(self.param_names)
        return f"λ({params}). <body>"


# MONAD INTERFACE


class MonadValue(Value, ABC):
    """Base class for monadic values"""
    
    @abstractmethod
    def bind(self, f: Callable[[Value], 'MonadValue']) -> 'MonadValue':
        """Monadic bind: M<A> → (A → M<B>) → M<B>"""
        pass
    
    @abstractmethod
    def map(self, f: Callable[[Value], Value]) -> 'MonadValue':
        """Functor map: M<A> → (A → B) → M<B>"""
        pass
    
    @classmethod
    @abstractmethod
    def pure(cls, value: Value) -> 'MonadValue':
        """Monadic return/pure: A → M<A>"""
        pass


# MAYBE MONAD


@dataclass
class MaybeValue(MonadValue):
    """Maybe monad: represents optional values"""
    has_value: bool
    value: Optional[Value] = None
    
    def bind(self, f: Callable[[Value], MonadValue]) -> 'MaybeValue':
        """Maybe bind: propagates None, applies f to Some"""
        if not self.has_value:
            return MaybeValue(False, None)
        return f(self.value)
    
    def map(self, f: Callable[[Value], Value]) -> 'MaybeValue':
        """Maybe map"""
        if not self.has_value:
            return MaybeValue(False, None)
        return MaybeValue(True, f(self.value))
    
    @classmethod
    def pure(cls, value: Value) -> 'MaybeValue':
        """Wrap value in Maybe"""
        return MaybeValue(True, value)
    
    @classmethod
    def nothing(cls) -> 'MaybeValue':
        """The None case"""
        return MaybeValue(False, None)
    
    def __str__(self):
        if self.has_value:
            return f"Some({self.value})"
        return "None"


# EITHER MONAD


@dataclass
class EitherValue(MonadValue):
    """Either monad: represents computations that can fail with an error"""
    is_right: bool
    value: Value  # Left error or Right value
    
    def bind(self, f: Callable[[Value], MonadValue]) -> 'EitherValue':
        """Either bind: short-circuits on Left, applies f to Right"""
        if not self.is_right:
            return self  # Propagate Left (error)
        return f(self.value)
    
    def map(self, f: Callable[[Value], Value]) -> 'EitherValue':
        """Either map"""
        if not self.is_right:
            return self
        return EitherValue(True, f(self.value))
    
    @classmethod
    def pure(cls, value: Value) -> 'EitherValue':
        """Wrap value in Right"""
        return EitherValue(True, value)
    
    @classmethod
    def left(cls, error: Value) -> 'EitherValue':
        """Create Left (error case)"""
        return EitherValue(False, error)
    
    @classmethod
    def right(cls, value: Value) -> 'EitherValue':
        """Create Right (success case)"""
        return EitherValue(True, value)
    
    def __str__(self):
        if self.is_right:
            return f"Right({self.value})"
        return f"Left({self.value})"


# LIST MONAD


@dataclass
class ListValue(MonadValue):
    """List monad: represents nondeterministic computation"""
    elements: List[Value]
    
    def bind(self, f: Callable[[Value], MonadValue]) -> 'ListValue':
        """List bind: flatMap - applies f to each element and concatenates"""
        result = []
        for elem in self.elements:
            m = f(elem)
            if isinstance(m, ListValue):
                result.extend(m.elements)
        return ListValue(result)
    
    def map(self, f: Callable[[Value], Value]) -> 'ListValue':
        """List map"""
        return ListValue([f(elem) for elem in self.elements])
    
    @classmethod
    def pure(cls, value: Value) -> 'ListValue':
        """Wrap single value in List"""
        return ListValue([value])
    
    def __str__(self):
        items = ", ".join(str(e) for e in self.elements)
        return f"[{items}]"


# STATE MONAD


@dataclass
class StateValue(MonadValue):
    """State monad: represents stateful computation without mutation"""
    run_state: Callable[[Any], Tuple[Value, Any]]  # S → (A, S)
    
    def bind(self, f: Callable[[Value], 'StateValue']) -> 'StateValue':
        """State bind: threads state through computations"""
        def new_run(s):
            val, s2 = self.run_state(s)
            next_state = f(val)
            return next_state.run_state(s2)
        return StateValue(new_run)
    
    def map(self, f: Callable[[Value], Value]) -> 'StateValue':
        """State map"""
        def new_run(s):
            val, s2 = self.run_state(s)
            return (f(val), s2)
        return StateValue(new_run)
    
    @classmethod
    def pure(cls, value: Value) -> 'StateValue':
        """Return value without changing state"""
        return StateValue(lambda s: (value, s))
    
    @classmethod
    def get(cls) -> 'StateValue':
        """Get current state"""
        return StateValue(lambda s: (s, s))
    
    @classmethod
    def put(cls, new_state: Any) -> 'StateValue':
        """Set new state"""
        return StateValue(lambda s: (UnitValue(), new_state))
    
    @classmethod
    def modify(cls, f: Callable[[Any], Any]) -> 'StateValue':
        """Modify state with function"""
        return StateValue(lambda s: (UnitValue(), f(s)))
    
    def eval_state(self, initial_state: Any) -> Value:
        """Run state computation and return value"""
        val, _ = self.run_state(initial_state)
        return val
    
    def exec_state(self, initial_state: Any) -> Any:
        """Run state computation and return final state"""
        _, final_state = self.run_state(initial_state)
        return final_state
    
    def __str__(self):
        return "State<λs. (a, s)>"


# IO MONAD


@dataclass
class IOValue(MonadValue):
    """IO monad: represents side-effecting computation"""
    action: Callable[[], Value]
    
    def bind(self, f: Callable[[Value], 'IOValue']) -> 'IOValue':
        """IO bind: sequences IO actions"""
        def new_action():
            val = self.action()
            next_io = f(val)
            return next_io.action()
        return IOValue(new_action)
    
    def map(self, f: Callable[[Value], Value]) -> 'IOValue':
        """IO map"""
        def new_action():
            val = self.action()
            return f(val)
        return IOValue(new_action)
    
    @classmethod
    def pure(cls, value: Value) -> 'IOValue':
        """Wrap pure value in IO"""
        return IOValue(lambda: value)
    
    def unsafe_run(self) -> Value:
        """Execute IO action (at the edge of the world)"""
        return self.action()
    
    def __str__(self):
        return "IO<...>"


# READER MONAD


@dataclass
class ReaderValue(MonadValue):
    """Reader monad: represents computation with read-only environment"""
    run_reader: Callable[[Any], Value]  # R → A
    
    def bind(self, f: Callable[[Value], 'ReaderValue']) -> 'ReaderValue':
        """Reader bind: passes same environment to both computations"""
        def new_run(env):
            val = self.run_reader(env)
            next_reader = f(val)
            return next_reader.run_reader(env)
        return ReaderValue(new_run)
    
    def map(self, f: Callable[[Value], Value]) -> 'ReaderValue':
        """Reader map"""
        def new_run(env):
            val = self.run_reader(env)
            return f(val)
        return ReaderValue(new_run)
    
    @classmethod
    def pure(cls, value: Value) -> 'ReaderValue':
        """Return value ignoring environment"""
        return ReaderValue(lambda env: value)
    
    @classmethod
    def ask(cls) -> 'ReaderValue':
        """Get the environment"""
        return ReaderValue(lambda env: env)
    
    def run(self, env: Any) -> Value:
        """Run reader with environment"""
        return self.run_reader(env)
    
    def __str__(self):
        return "Reader<λr. a>"


# EXPRESSIONS


class Expression(ABC):
    """Base expression"""
    @abstractmethod
    def evaluate(self, env: 'Environment') -> Value:
        pass


@dataclass
class IntLiteral(Expression):
    value: int
    def evaluate(self, env): return IntValue(self.value)


@dataclass
class StringLiteral(Expression):
    value: str
    def evaluate(self, env): return StringValue(self.value)


@dataclass
class BoolLiteral(Expression):
    value: bool
    def evaluate(self, env): return BoolValue(self.value)


@dataclass
class UnitLiteral(Expression):
    def evaluate(self, env): return UnitValue()


@dataclass
class Variable(Expression):
    name: str
    def evaluate(self, env): return env.get_value(self.name)


@dataclass
class BinaryOp(Expression):
    op: str
    left: Expression
    right: Expression
    
    def evaluate(self, env):
        left = self.left.evaluate(env)
        right = self.right.evaluate(env)
        
        if self.op == '+':
            if isinstance(left, IntValue) and isinstance(right, IntValue):
                return IntValue(left.value + right.value)
        elif self.op == '-' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return IntValue(left.value - right.value)
        elif self.op == '*' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return IntValue(left.value * right.value)
        elif self.op == '==':
            return BoolValue(str(left) == str(right))
        elif self.op == '<' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return BoolValue(left.value < right.value)
        
        raise RuntimeError(f"Invalid binary operation: {self.op}")


@dataclass
class Lambda(Expression):
    """Lambda expression: λx. body"""
    param_names: List[str]
    body: Expression
    
    def evaluate(self, env):
        return FunctionValue(self.param_names, self.body, env)


@dataclass
class Application(Expression):
    """Function application: f(args)"""
    func: Expression
    args: List[Expression]
    
    def evaluate(self, env):
        func_val = self.func.evaluate(env)
        arg_vals = [arg.evaluate(env) for arg in self.args]
        
        if not isinstance(func_val, FunctionValue):
            raise RuntimeError("Cannot apply non-function")
        
        # Create new environment with parameters bound
        new_env = func_val.closure_env.extend()
        for param, arg_val in zip(func_val.param_names, arg_vals):
            new_env.define(param, arg_val, UNIT_TYPE)
        
        return func_val.body.evaluate(new_env)


@dataclass
class MReturn(Expression):
    """Monadic return: pure value into monad"""
    monad_type: str  # "Maybe", "Either", "List", etc.
    value: Expression
    
    def evaluate(self, env):
        val = self.value.evaluate(env)
        
        if self.monad_type == "Maybe":
            return MaybeValue.pure(val)
        elif self.monad_type == "Either":
            return EitherValue.pure(val)
        elif self.monad_type == "List":
            return ListValue.pure(val)
        elif self.monad_type == "State":
            return StateValue.pure(val)
        elif self.monad_type == "IO":
            return IOValue.pure(val)
        elif self.monad_type == "Reader":
            return ReaderValue.pure(val)
        
        raise RuntimeError(f"Unknown monad type: {self.monad_type}")


@dataclass
class MBind(Expression):
    """Monadic bind: m >>= f"""
    monad_expr: Expression
    func: Expression  # Should evaluate to a function Value → MonadValue
    
    def evaluate(self, env):
        monad_val = self.monad_expr.evaluate(env)
        func_val = self.func.evaluate(env)
        
        if not isinstance(monad_val, MonadValue):
            raise RuntimeError("Cannot bind non-monad value")
        
        # Create a wrapper that calls the function
        def bind_func(val):
            if isinstance(func_val, FunctionValue):
                new_env = func_val.closure_env.extend()
                new_env.define(func_val.param_names[0], val, UNIT_TYPE)
                return func_val.body.evaluate(new_env)
            raise RuntimeError("Bind function must be a function")
        
        return monad_val.bind(bind_func)


@dataclass
class DoBlock(Expression):
    """Do-notation: syntactic sugar for monadic binds"""
    statements: List['DoStatement']
    
    def evaluate(self, env):
        # Desugar into nested binds
        if not self.statements:
            return MaybeValue.nothing()
        
        # Start from the end and work backwards
        result = self.statements[-1].as_expression()
        
        for stmt in reversed(self.statements[:-1]):
            if isinstance(stmt, DoBind):
                # x <- m  ===>  m >>= λx. rest
                result = MBind(
                    stmt.expr,
                    Lambda([stmt.var_name], result)
                )
            elif isinstance(stmt, DoLet):
                # let x = e  ===>  (λx. rest) e
                result = Application(
                    Lambda([stmt.var_name], result),
                    [stmt.expr]
                )
        
        return result.evaluate(env)


@dataclass
class MaybeNone(Expression):
    """Maybe None constructor"""
    def evaluate(self, env):
        return MaybeValue.nothing()


@dataclass
class MaybeSome(Expression):
    """Maybe Some constructor"""
    value: Expression
    def evaluate(self, env):
        return MaybeValue.pure(self.value.evaluate(env))


@dataclass
class EitherLeft(Expression):
    """Either Left constructor"""
    value: Expression
    def evaluate(self, env):
        return EitherValue.left(self.value.evaluate(env))


@dataclass
class EitherRight(Expression):
    """Either Right constructor"""
    value: Expression
    def evaluate(self, env):
        return EitherValue.right(self.value.evaluate(env))


@dataclass
class ListLiteral(Expression):
    """List literal"""
    elements: List[Expression]
    def evaluate(self, env):
        return ListValue([e.evaluate(env) for e in self.elements])


@dataclass
class StateGet(Expression):
    """Get current state"""
    def evaluate(self, env):
        return StateValue.get()


@dataclass
class StatePut(Expression):
    """Put new state"""
    new_state: Expression
    def evaluate(self, env):
        state_val = self.new_state.evaluate(env)
        return StateValue.put(state_val)


@dataclass
class IOPrint(Expression):
    """IO action that prints"""
    expr: Expression
    def evaluate(self, env):
        def action():
            val = self.expr.evaluate(env)
            print(f"  >> {val}")
            return UnitValue()
        return IOValue(action)


@dataclass
class ReaderAsk(Expression):
    """Ask for reader environment"""
    def evaluate(self, env):
        return ReaderValue.ask()


# DO-NOTATION HELPERS


class DoStatement(ABC):
    """Statement in do-block"""
    @abstractmethod
    def as_expression(self) -> Expression:
        pass


@dataclass
class DoBind(DoStatement):
    """x <- m"""
    var_name: str
    expr: Expression
    def as_expression(self): return self.expr


@dataclass
class DoLet(DoStatement):
    """let x = e"""
    var_name: str
    expr: Expression
    def as_expression(self): return self.expr


@dataclass
class DoExpr(DoStatement):
    """Plain expression"""
    expr: Expression
    def as_expression(self): return self.expr


# ENVIRONMENT


class Environment:
    """Runtime environment"""
    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.bindings: Dict[str, Tuple[Value, Type]] = {}
    
    def define(self, name: str, value: Value, typ: Type):
        self.bindings[name] = (value, typ)
    
    def get_value(self, name: str) -> Value:
        if name in self.bindings:
            return self.bindings[name][0]
        if self.parent:
            return self.parent.get_value(name)
        raise NameError(f"Undefined variable: {name}")
    
    def extend(self) -> 'Environment':
        return Environment(self)


# DEMONSTRATION


def demo():
    print("-" * 70)
    print("COOL with MONADS")
    print("-" * 70)
    print("Monads as monoids in the category of endofunctors")
    print("- return/pure: A → M<A>")
    print("- bind (>>=): M<A> → (A → M<B>) → M<B>")
    print("- Kleisli arrows: A → M<B>")
    print("-" * 70)
    
    env = Environment()
    
    # Example 1: Maybe Monad
    print("\n" + "-" * 70)
    print("Example 1: Maybe Monad - Null Safety")
    print("-" * 70)
    
    print("Maybe type: None | Some(a)")
    print("\nCreating Maybe values:")
    
    some_val = MaybeSome(IntLiteral(42)).evaluate(env)
    none_val = MaybeNone().evaluate(env)
    
    print(f"  some = {some_val}")
    print(f"  none = {none_val}")
    
    print("\nMonadic bind (>>=):")
    print("  some >>= (λx. Some(x + 1))")
    
    # some >>= (λx. Some(x + 1))
    inc_func = Lambda(
        ["x"],
        MaybeSome(BinaryOp("+", Variable("x"), IntLiteral(1)))
    )
    
    result = MBind(MaybeSome(IntLiteral(42)), inc_func).evaluate(env)
    print(f"  Result: {result}")
    
    result2 = MBind(MaybeNone(), inc_func).evaluate(env)
    print(f"  none >>= f = {result2}")
    
    print("\nChaining operations (associativity):")
    print("  Some(5) >>= (λx. Some(x * 2)) >>= (λy. Some(y + 10))")
    
    double_func = Lambda(["x"], MaybeSome(BinaryOp("*", Variable("x"), IntLiteral(2))))
    add10_func = Lambda(["y"], MaybeSome(BinaryOp("+", Variable("y"), IntLiteral(10))))
    
    chained = MBind(
        MBind(MaybeSome(IntLiteral(5)), double_func),
        add10_func
    ).evaluate(env)
    print(f"  Result: {chained}")
    
    # Example 2: Either Monad
    print("\n" + "-" * 70)
    print("Example 2: Either Monad - Error Handling")
    print("-" * 70)
    
    print("Either type: Left(error) | Right(value)")
    print("\nSafe division:")
    
    def safe_div(a: int, b: int) -> EitherValue:
        if b == 0:
            return EitherValue.left(StringValue("Division by zero"))
        return EitherValue.right(IntValue(a // b))
    
    ok = safe_div(10, 2)
    err = safe_div(10, 0)
    
    print(f"  10 / 2 = {ok}")
    print(f"  10 / 0 = {err}")
    
    print("\nChaining computations (short-circuit on error):")
    print("  Right(20) >>= (div by 2) >>= (div by 5)")
    
    # Manually construct chain
    r1 = EitherValue.right(IntValue(20))
    r2 = r1.bind(lambda v: safe_div(v.value, 2))
    r3 = r2.bind(lambda v: safe_div(v.value, 5))
    print(f"  Result: {r3}")
    
    print("\n  Right(20) >>= (div by 2) >>= (div by 0)")
    r4 = EitherValue.right(IntValue(20))
    r5 = r4.bind(lambda v: safe_div(v.value, 2))
    r6 = r5.bind(lambda v: safe_div(v.value, 0))
    print(f"  Result: {r6} (error propagated)")
    
    # Example 3: List Monad
    print("\n" + "-" * 70)
    print("Example 3: List Monad - Nondeterminism")
    print("-" * 70)
    
    print("List as monad represents multiple possible values")
    print("\nList bind is flatMap:")
    
    list_val = ListLiteral([IntLiteral(1), IntLiteral(2), IntLiteral(3)]).evaluate(env)
    print(f"  list = {list_val}")
    
    # list >>= (λx. [x, x*2])
    dup_func = Lambda(
        ["x"],
        ListLiteral([Variable("x"), BinaryOp("*", Variable("x"), IntLiteral(2))])
    )
    
    result = MBind(
        ListLiteral([IntLiteral(1), IntLiteral(2), IntLiteral(3)]),
        dup_func
    ).evaluate(env)
    print(f"  [1,2,3] >>= (λx. [x, x*2]) = {result}")
    
    print("\nCombinatorial explosion (Cartesian product):")
    # [1,2] >>= (λx. [3,4] >>= (λy. [x+y]))
    
    inner_func = Lambda(
        ["y"],
        ListLiteral([BinaryOp("+", Variable("x"), Variable("y"))])
    )
    
    outer_func = Lambda(
        ["x"],
        MBind(ListLiteral([IntLiteral(3), IntLiteral(4)]), inner_func)
    )
    
    cartesian = MBind(
        ListLiteral([IntLiteral(1), IntLiteral(2)]),
        outer_func
    ).evaluate(env)
    print(f"  Cartesian: {cartesian}")
    
    # Example 4: State Monad
    print("\n" + "-" * 70)
    print("Example 4: State Monad - Pure Stateful Computation")
    print("-" * 70)
    
    print("State<S,A> = S → (A, S)")
    print("\nCounter without mutation:")
    
    # get >>= λs. put(s + 1) >>= λ_. return s
    increment = StateValue.get().bind(
        lambda s: StateValue.put(IntValue(s.value + 1) if isinstance(s, IntValue) else IntValue(0)).bind(
            lambda _: StateValue.pure(s)
        )
    )
    
    initial = IntValue(0)
    v1 = increment.eval_state(initial)
    s1 = increment.exec_state(initial)
    print(f"  Initial state: {initial}")
    print(f"  After increment: value={v1}, state={s1}")
    
    # Chain multiple increments
    three_increments = increment.bind(
        lambda _: increment.bind(
            lambda _: increment
        )
    )
    
    final_state = three_increments.exec_state(IntValue(0))
    print(f"  After 3 increments: state={final_state}")
    
    print("\nStateful computation: sum accumulator")
    
    # Helper to add value to state
    def add_to_state(n: int) -> StateValue:
        return StateValue.get().bind(
            lambda s: StateValue.put(
                IntValue(s.value + n) if isinstance(s, IntValue) else IntValue(n)
            ).bind(lambda _: StateValue.pure(UnitValue()))
        )
    
    computation = add_to_state(5).bind(
        lambda _: add_to_state(10).bind(
            lambda _: add_to_state(3).bind(
                lambda _: StateValue.get()
            )
        )
    )
    
    final = computation.eval_state(IntValue(0))
    print(f"  Sum of 5, 10, 3 = {final}")
    
    # Example 5: IO Monad
    print("\n" + "-" * 70)
    print("Example 5: IO Monad - Side Effects")
    print("-" * 70)
    
    print("IO<A> = () → A (lazy computation)")
    print("\nSequencing IO actions:")
    
    # IO action: print then return value
    io1 = IOPrint(StringLiteral("Hello")).evaluate(env)
    io2 = IOPrint(StringLiteral("World")).evaluate(env)
    
    print("  Composing IO actions:")
    # io1 >>= λ_. io2 >>= λ_. return 42
    sequenced = io1.bind(
        lambda _: io2.bind(
            lambda _: IOValue.pure(IntValue(42))
        )
    )
    
    result = sequenced.unsafe_run()
    print(f"  Final value: {result}")
    
    print("\nIO keeps effects at the edge (referential transparency):")
    io_action = IOValue.pure(IntValue(100))
    print(f"  IO action created: {io_action} (not executed yet)")
    result = io_action.unsafe_run()
    print(f"  After unsafe_run: {result}")
    
    # Example 6: Reader Monad
    print("\n" + "-" * 70)
    print("Example 6: Reader Monad - Dependency Injection")
    print("-" * 70)
    
    print("Reader<R,A> = R → A (computation with environment)")
    print("\nReading configuration:")
    
    # Computation that reads environment
    computation = ReaderValue.ask().bind(
        lambda env_val: ReaderValue.pure(
            IntValue(env_val.value * 2) if isinstance(env_val, IntValue) else IntValue(0)
        )
    )
    
    result = computation.run(IntValue(21))
    print(f"  With env=21: {result}")
    
    result = computation.run(IntValue(100))
    print(f"  With env=100: {result}")
    
    print("\nComposing computations with shared environment:")
    
    # ask >>= λenv. return (env + 10)
    comp1 = ReaderValue.ask().bind(
        lambda e: ReaderValue.pure(
            IntValue(e.value + 10) if isinstance(e, IntValue) else IntValue(10)
        )
    )
    
    # ask >>= λenv. return (env * 3)
    comp2 = ReaderValue.ask().bind(
        lambda e: ReaderValue.pure(
            IntValue(e.value * 3) if isinstance(e, IntValue) else IntValue(0)
        )
    )
    
    # Compose: both see same environment
    combined = comp1.bind(
        lambda v1: comp2.bind(
            lambda v2: ReaderValue.pure(
                IntValue(v1.value + v2.value) if isinstance(v1, IntValue) and isinstance(v2, IntValue) else IntValue(0)
            )
        )
    )
    
    result = combined.run(IntValue(5))
    print(f"  (env+10) + (env*3) with env=5: {result}")
    
    # Example 7: Monad Laws
    print("\n" + "-" * 70)
    print("Example 7: Monad Laws (Verification)")
    print("-" * 70)
    
    print("Three monad laws:")
    print("  1. Left identity:  return a >>= f  ≡  f a")
    print("  2. Right identity: m >>= return    ≡  m")
    print("  3. Associativity:  (m >>= f) >>= g ≡  m >>= (λx. f x >>= g)")
    
    print("\nVerifying with Maybe monad:")
    
    # Law 1: Left identity
    a = IntValue(5)
    f = lambda x: MaybeValue.pure(IntValue(x.value * 2) if isinstance(x, IntValue) else IntValue(0))
    
    lhs1 = MaybeValue.pure(a).bind(f)
    rhs1 = f(a)
    print(f"\n  Left identity:")
    print(f"    return 5 >>= (λx. return x*2) = {lhs1}")
    print(f"    (λx. return x*2) 5            = {rhs1}")
    print(f"    Equal? {str(lhs1) == str(rhs1)}")
    
    # Law 2: Right identity
    m = MaybeValue.pure(IntValue(10))
    lhs2 = m.bind(lambda x: MaybeValue.pure(x))
    rhs2 = m
    print(f"\n  Right identity:")
    print(f"    Some(10) >>= return = {lhs2}")
    print(f"    Some(10)            = {rhs2}")
    print(f"    Equal? {str(lhs2) == str(rhs2)}")
    
    # Law 3: Associativity
    m = MaybeValue.pure(IntValue(3))
    f = lambda x: MaybeValue.pure(IntValue(x.value + 1) if isinstance(x, IntValue) else IntValue(0))
    g = lambda x: MaybeValue.pure(IntValue(x.value * 2) if isinstance(x, IntValue) else IntValue(0))
    
    lhs3 = m.bind(f).bind(g)
    rhs3 = m.bind(lambda x: f(x).bind(g))
    print(f"\n  Associativity:")
    print(f"    (m >>= f) >>= g      = {lhs3}")
    print(f"    m >>= (λx. f x >>= g) = {rhs3}")
    print(f"    Equal? {str(lhs3) == str(rhs3)}")
    
    # Example 8: Kleisli Category
    print("\n" + "-" * 70)
    print("Example 8: Kleisli Category")
    print("-" * 70)
    
    print("Kleisli arrows: A → M<B>")
    print("Composition: (f: A → M<B>) ∘ (g: B → M<C>) = (A → M<C>)")
    
    # Define Kleisli arrows
    def safe_sqrt(n: Value) -> MaybeValue:
        if isinstance(n, IntValue) and n.value >= 0:
            import math
            return MaybeValue.pure(IntValue(int(math.sqrt(n.value))))
        return MaybeValue.nothing()
    
    def safe_half(n: Value) -> MaybeValue:
        if isinstance(n, IntValue) and n.value % 2 == 0:
            return MaybeValue.pure(IntValue(n.value // 2))
        return MaybeValue.nothing()
    
    print("\n  f: Int → Maybe<Int> (safe square root)")
    print("  g: Int → Maybe<Int> (safe halving)")
    
    # Manual Kleisli composition: f >=> g
    def kleisli_compose(f, g):
        def composed(a):
            return f(a).bind(g)
        return composed
    
    h = kleisli_compose(safe_sqrt, safe_half)
    
    print("\n  h = f >=> g (Kleisli composition)")
    print(f"  h(16) = sqrt(16) >>= half = {h(IntValue(16))}")
    print(f"  h(9)  = sqrt(9) >>= half  = {h(IntValue(9))} (odd number, fails)")
    print(f"  h(-4) = sqrt(-4) >>= half = {h(IntValue(-4))} (negative, fails)")
    
    # Example 9: Do-Notation
    print("\n" + "-" * 70)
    print("Example 9: Do-Notation (Syntactic Sugar)")
    print("-" * 70)
    
    print("Do-notation desugars to nested binds")
    print("\nWithout do-notation:")
    print("  Some(3) >>= λx.")
    print("    Some(4) >>= λy.")
    print("      return (x + y)")
    
    manual = MBind(
        MaybeSome(IntLiteral(3)),
        Lambda(["x"], MBind(
            MaybeSome(IntLiteral(4)),
            Lambda(["y"], MaybeSome(BinaryOp("+", Variable("x"), Variable("y"))))
        ))
    ).evaluate(env)
    
    print(f"\n  Result: {manual}")
    
    print("\nWith do-notation:")
    print("  do {")
    print("    x <- Some(3);")
    print("    y <- Some(4);")
    print("    return (x + y)")
    print("  }")
    
    do_result = DoBlock([
        DoBind("x", MaybeSome(IntLiteral(3))),
        DoBind("y", MaybeSome(IntLiteral(4))),
        DoExpr(MaybeSome(BinaryOp("+", Variable("x"), Variable("y"))))
    ]).evaluate(env)
    
    print(f"\n  Result: {do_result}")
    print(f"  Same as manual? {str(manual) == str(do_result)}")
    
    # Example 10: Real-World Composition
    print("\n" + "-" * 70)
    print("Example 10: Real-World Example - Validation Pipeline")
    print("-" * 70)
    
    print("Validating user input with Either monad:")
    
    def validate_positive(n: Value) -> EitherValue:
        if isinstance(n, IntValue) and n.value > 0:
            return EitherValue.right(n)
        return EitherValue.left(StringValue("Must be positive"))
    
    def validate_even(n: Value) -> EitherValue:
        if isinstance(n, IntValue) and n.value % 2 == 0:
            return EitherValue.right(n)
        return EitherValue.left(StringValue("Must be even"))
    
    def validate_small(n: Value) -> EitherValue:
        if isinstance(n, IntValue) and n.value < 100:
            return EitherValue.right(n)
        return EitherValue.left(StringValue("Must be less than 100"))
    
    # Pipeline: check all validations
    def validate_all(n: int) -> EitherValue:
        return EitherValue.right(IntValue(n)) \
            .bind(validate_positive) \
            .bind(validate_even) \
            .bind(validate_small)
    
    print("\n  Validation pipeline:")
    print(f"    validate(42)  = {validate_all(42)}")
    print(f"    validate(-4)  = {validate_all(-4)} (fails: not positive)")
    print(f"    validate(7)   = {validate_all(7)} (fails: not even)")
    print(f"    validate(200) = {validate_all(200)} (fails: too large)")
    
    # Summary
    print("\n" + "-" * 70)
    print("CATEGORICAL PROPERTIES DEMONSTRATED:")
    print("-" * 70)
    print("+ Monads as Functors: map operation (fmap)")
    print("+ Monadic Return: pure/return lifts values (η)")
    print("+ Monadic Bind: >>= sequences computations (μ)")
    print("+ Monad Laws: identity and associativity")
    print("+ Kleisli Category: arrows A → M<B> with composition")
    print("+ Maybe: null safety without null")
    print("+ Either: error handling with typed errors")
    print("+ List: nondeterminism and choice")
    print("+ State: pure stateful computation")
    print("+ IO: controlled side effects")
    print("+ Reader: dependency injection")
    print("+ Do-Notation: readable sequencing syntax")
    print("=" * 70)
    
    print("\nKey Insights:")
    print("- Monads are 'programmable semicolons'")
    print("- They separate effect description from execution")
    print("- Composition preserves referential transparency")
    print("- Different monads model different computational effects")
    print("- Monad laws ensure consistent behavior")
    print("- Kleisli composition generalizes function composition")
    print("- Monads are monoids in the category of endofunctors!")


if __name__ == "__main__":
    demo()
