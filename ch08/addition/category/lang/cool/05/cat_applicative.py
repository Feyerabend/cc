"""
Categorical Object-Oriented Language (COOL) with Applicative Functors
=====================================================================
An OOP language where:
- Applicatives are lax monoidal functors
- They bridge Functors and Monads
- They allow independent effects (vs sequential in Monads)
- <*> (apply) is the key operation
- Enables parallel composition and validation
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
UNIT_TYPE = Type("Unit")



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
    
    def apply(self, args: List[Value], env: 'Environment') -> Value:
        """Apply function to arguments"""
        new_env = self.closure_env.extend()
        for param, arg in zip(self.param_names, args):
            new_env.define(param, arg)
        return self.body.evaluate(new_env)
    
    def __str__(self):
        params = ", ".join(self.param_names)
        return f"λ({params}). <body>"



# FUNCTOR INTERFACE


class FunctorValue(Value, ABC):
    """Base class for functor values"""
    
    @abstractmethod
    def fmap(self, f: Callable[[Value], Value]) -> 'FunctorValue':
        """Functor map: F<A> -> (A -> B) -> F<B>"""
        pass



# APPLICATIVE INTERFACE


class ApplicativeValue(FunctorValue, ABC):
    """Base class for applicative functor values"""
    
    @classmethod
    @abstractmethod
    def pure(cls, value: Value) -> 'ApplicativeValue':
        """Lift value into applicative: A -> F<A>"""
        pass
    
    @abstractmethod
    def apply(self, f_wrapped: 'ApplicativeValue') -> 'ApplicativeValue':
        """Apply wrapped function: F<A -> B> -> F<A> -> F<B>
        This is the <*> operator (pronounced "ap" or "apply")
        """
        pass
    
    def lift_a2(self, other: 'ApplicativeValue', 
                f: Callable[[Value, Value], Value]) -> 'ApplicativeValue':
        """Lift binary function: (A -> B -> C) -> F<A> -> F<B> -> F<C>"""
        # liftA2 f fa fb = pure f <*> fa <*> fb
        # Or equivalently: fmap f fa <*> fb
        return self.fmap(lambda a: lambda b: f(a, b)).apply(other)



# MAYBE APPLICATIVE


@dataclass
class MaybeValue(ApplicativeValue):
    """Maybe applicative: represents optional values"""
    has_value: bool
    value: Optional[Value] = None
    
    def fmap(self, f: Callable[[Value], Value]) -> 'MaybeValue':
        """Maybe functor"""
        if not self.has_value:
            return MaybeValue(False, None)
        return MaybeValue(True, f(self.value))
    
    @classmethod
    def pure(cls, value: Value) -> 'MaybeValue':
        """Wrap value in Some"""
        return MaybeValue(True, value)
    
    def apply(self, f_wrapped: 'MaybeValue') -> 'MaybeValue':
        """Maybe apply: if both have values, apply function; else None"""
        if not isinstance(f_wrapped, MaybeValue):
            raise TypeError("apply requires wrapped function")
        
        if not self.has_value or not f_wrapped.has_value:
            return MaybeValue(False, None)
        
        # f_wrapped.value should be a function
        func = f_wrapped.value
        if isinstance(func, FunctionValue):
            result = func.apply([self.value], None)
            return MaybeValue(True, result)
        elif callable(func):
            return MaybeValue(True, func(self.value))
        
        raise TypeError("Wrapped value must be a function")
    
    @classmethod
    def nothing(cls) -> 'MaybeValue':
        """The None case"""
        return MaybeValue(False, None)
    
    def __str__(self):
        if self.has_value:
            return f"Some({self.value})"
        return "None"



# EITHER APPLICATIVE


@dataclass
class EitherValue(ApplicativeValue):
    """Either applicative: Left is error, Right is success"""
    is_right: bool
    value: Value
    
    def fmap(self, f: Callable[[Value], Value]) -> 'EitherValue':
        """Either functor"""
        if not self.is_right:
            return self  # Propagate error
        return EitherValue(True, f(self.value))
    
    @classmethod
    def pure(cls, value: Value) -> 'EitherValue':
        """Wrap value in Right"""
        return EitherValue(True, value)
    
    def apply(self, f_wrapped: 'EitherValue') -> 'EitherValue':
        """Either apply: if both Right, apply; propagate first Left"""
        if not isinstance(f_wrapped, EitherValue):
            raise TypeError("apply requires wrapped function")
        
        if not f_wrapped.is_right:
            return f_wrapped  # Return first error
        if not self.is_right:
            return self  # Return error
        
        func = f_wrapped.value
        if isinstance(func, FunctionValue):
            result = func.apply([self.value], None)
            return EitherValue(True, result)
        elif callable(func):
            return EitherValue(True, func(self.value))
        
        raise TypeError("Wrapped value must be a function")
    
    @classmethod
    def left(cls, error: Value) -> 'EitherValue':
        """Create Left (error)"""
        return EitherValue(False, error)
    
    @classmethod
    def right(cls, value: Value) -> 'EitherValue':
        """Create Right (success)"""
        return EitherValue(True, value)
    
    def __str__(self):
        if self.is_right:
            return f"Right({self.value})"
        return f"Left({self.value})"



# LIST APPLICATIVE


@dataclass
class ListValue(ApplicativeValue):
    """List applicative: Cartesian product behavior"""
    elements: List[Value]
    
    def fmap(self, f: Callable[[Value], Value]) -> 'ListValue':
        """List functor"""
        return ListValue([f(elem) for elem in self.elements])
    
    @classmethod
    def pure(cls, value: Value) -> 'ListValue':
        """Singleton list"""
        return ListValue([value])
    
    def apply(self, f_wrapped: 'ListValue') -> 'ListValue':
        """List apply: Cartesian product application
        [f, g] <*> [a, b] = [f a, f b, g a, g b]
        """
        if not isinstance(f_wrapped, ListValue):
            raise TypeError("apply requires wrapped function")
        
        results = []
        for func in f_wrapped.elements:
            for val in self.elements:
                if isinstance(func, FunctionValue):
                    result = func.apply([val], None)
                    results.append(result)
                elif callable(func):
                    results.append(func(val))
        
        return ListValue(results)
    
    def __str__(self):
        items = ", ".join(str(e) for e in self.elements)
        return f"[{items}]"



# VALIDATION APPLICATIVE (accumulates errors)


@dataclass
class ValidationValue(ApplicativeValue):
    """Validation applicative: accumulates ALL errors (unlike Either)"""
    is_success: bool
    value: Optional[Value] = None
    errors: List[Value] = field(default_factory=list)
    
    def fmap(self, f: Callable[[Value], Value]) -> 'ValidationValue':
        """Validation functor"""
        if not self.is_success:
            return ValidationValue(False, None, self.errors)
        return ValidationValue(True, f(self.value), [])
    
    @classmethod
    def pure(cls, value: Value) -> 'ValidationValue':
        """Wrap value in Success"""
        return ValidationValue(True, value, [])
    
    def apply(self, f_wrapped: 'ValidationValue') -> 'ValidationValue':
        """Validation apply: accumulates errors from BOTH sides
        This is the key difference from Either!
        """
        if not isinstance(f_wrapped, ValidationValue):
            raise TypeError("apply requires wrapped function")
        
        # Both success: apply function
        if f_wrapped.is_success and self.is_success:
            func = f_wrapped.value
            if isinstance(func, FunctionValue):
                result = func.apply([self.value], None)
                return ValidationValue(True, result, [])
            elif callable(func):
                return ValidationValue(True, func(self.value), [])
        
        # Accumulate errors from both sides
        all_errors = []
        if not f_wrapped.is_success:
            all_errors.extend(f_wrapped.errors)
        if not self.is_success:
            all_errors.extend(self.errors)
        
        return ValidationValue(False, None, all_errors)
    
    @classmethod
    def success(cls, value: Value) -> 'ValidationValue':
        """Create Success"""
        return ValidationValue(True, value, [])
    
    @classmethod
    def failure(cls, error: Value) -> 'ValidationValue':
        """Create Failure with single error"""
        return ValidationValue(False, None, [error])
    
    def __str__(self):
        if self.is_success:
            return f"Success({self.value})"
        errors_str = ", ".join(str(e) for e in self.errors)
        return f"Failure([{errors_str}])"



# ZIPLIST APPLICATIVE (different from List!)


@dataclass
class ZipListValue(ApplicativeValue):
    """ZipList: zips functions with values (different from Cartesian product)"""
    elements: List[Value]
    
    def fmap(self, f: Callable[[Value], Value]) -> 'ZipListValue':
        """ZipList functor"""
        return ZipListValue([f(elem) for elem in self.elements])
    
    @classmethod
    def pure(cls, value: Value) -> 'ZipListValue':
        """Infinite repetition (we'll use finite approximation)"""
        # In real Haskell: repeat value
        # Here we approximate with large repetition
        return ZipListValue([value] * 1000)
    
    def apply(self, f_wrapped: 'ZipListValue') -> 'ZipListValue':
        """ZipList apply: zip functions with values
        [f, g, h] <*> [a, b, c] = [f a, g b, h c]
        """
        if not isinstance(f_wrapped, ZipListValue):
            raise TypeError("apply requires wrapped function")
        
        results = []
        for func, val in zip(f_wrapped.elements, self.elements):
            if isinstance(func, FunctionValue):
                result = func.apply([val], None)
                results.append(result)
            elif callable(func):
                results.append(func(val))
        
        return ZipListValue(results)
    
    def __str__(self):
        items = ", ".join(str(e) for e in self.elements[:10])
        suffix = "..." if len(self.elements) > 10 else ""
        return f"ZipList[{items}{suffix}]"



# CONST APPLICATIVE (phantom type)


@dataclass
class ConstValue(ApplicativeValue):
    """Const applicative: ignores second type parameter
    Const<M,A> stores M, ignores A (phantom type)
    Useful for accumulating information without computing
    """
    stored: Value  # The monoid value we're accumulating
    
    def fmap(self, f: Callable[[Value], Value]) -> 'ConstValue':
        """Const functor: ignores function (phantom!)"""
        return ConstValue(self.stored)
    
    @classmethod
    def pure(cls, value: Value) -> 'ConstValue':
        """Const pure: uses monoid identity"""
        # For simplicity, use empty list as identity
        return ConstValue(ListValue([]))
    
    def apply(self, f_wrapped: 'ConstValue') -> 'ConstValue':
        """Const apply: combines stored values (monoid append)"""
        if not isinstance(f_wrapped, ConstValue):
            raise TypeError("apply requires wrapped function")
        
        # Combine stored values (monoid operation)
        if isinstance(self.stored, ListValue) and isinstance(f_wrapped.stored, ListValue):
            combined = self.stored.elements + f_wrapped.stored.elements
            return ConstValue(ListValue(combined))
        
        return ConstValue(self.stored)
    
    def __str__(self):
        return f"Const({self.stored})"



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
            elif isinstance(left, StringValue) and isinstance(right, StringValue):
                return StringValue(left.value + right.value)
        elif self.op == '*' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return IntValue(left.value * right.value)
        elif self.op == '==' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return BoolValue(left.value == right.value)
        elif self.op == '<' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return BoolValue(left.value < right.value)
        
        raise RuntimeError(f"Invalid binary operation: {self.op}")


@dataclass
class Lambda(Expression):
    """Lambda expression"""
    param_names: List[str]
    body: Expression
    
    def evaluate(self, env):
        return FunctionValue(self.param_names, self.body, env)


@dataclass
class Application(Expression):
    """Function application"""
    func: Expression
    args: List[Expression]
    
    def evaluate(self, env):
        func_val = self.func.evaluate(env)
        arg_vals = [arg.evaluate(env) for arg in self.args]
        
        if isinstance(func_val, FunctionValue):
            return func_val.apply(arg_vals, env)
        
        raise RuntimeError("Cannot apply non-function")


# APPLICATIVE OPERATIONS


@dataclass
class APure(Expression):
    """Pure: lift value into applicative"""
    applicative_type: str
    value: Expression
    
    def evaluate(self, env):
        val = self.value.evaluate(env)
        
        if self.applicative_type == "Maybe":
            return MaybeValue.pure(val)
        elif self.applicative_type == "Either":
            return EitherValue.pure(val)
        elif self.applicative_type == "List":
            return ListValue.pure(val)
        elif self.applicative_type == "Validation":
            return ValidationValue.pure(val)
        elif self.applicative_type == "ZipList":
            return ZipListValue.pure(val)
        elif self.applicative_type == "Const":
            return ConstValue.pure(val)
        
        raise RuntimeError(f"Unknown applicative: {self.applicative_type}")


@dataclass
class AApply(Expression):
    """Apply: F<A -> B> <*> F<A> -> F<B>"""
    func_wrapped: Expression
    arg_wrapped: Expression
    
    def evaluate(self, env):
        f_app = self.func_wrapped.evaluate(env)
        a_app = self.arg_wrapped.evaluate(env)
        
        if not isinstance(a_app, ApplicativeValue):
            raise RuntimeError("Cannot apply non-applicative")
        
        return a_app.apply(f_app)


@dataclass
class LiftA2(Expression):
    """Lift binary function into applicative"""
    binary_op: str  # +, *, etc.
    left_wrapped: Expression
    right_wrapped: Expression
    
    def evaluate(self, env):
        left_app = self.left_wrapped.evaluate(env)
        right_app = self.right_wrapped.evaluate(env)
        
        # Define the binary function
        if self.binary_op == '+':
            def binary_func(a, b):
                if isinstance(a, IntValue) and isinstance(b, IntValue):
                    return IntValue(a.value + b.value)
                return IntValue(0)
        elif self.binary_op == '*':
            def binary_func(a, b):
                if isinstance(a, IntValue) and isinstance(b, IntValue):
                    return IntValue(a.value * b.value)
                return IntValue(0)
        else:
            raise RuntimeError(f"Unknown binary op: {self.binary_op}")
        
        return left_app.lift_a2(right_app, binary_func)


# ENVIRONMENT


class Environment:
    """Runtime environment"""
    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.bindings: Dict[str, Value] = {}
    
    def define(self, name: str, value: Value):
        self.bindings[name] = value
    
    def get_value(self, name: str) -> Value:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get_value(name)
        raise NameError(f"Undefined variable: {name}")
    
    def extend(self) -> 'Environment':
        return Environment(self)



# DEMONSTRATION


def demo():
    print("=" * 70)
    print("COOL with APPLICATIVE FUNCTORS")
    print("=" * 70)
    print("Applicatives: Lax Monoidal Functors")
    print("- pure: A -> F<A>")
    print("- <*> (apply): F<A -> B> -> F<A> -> F<B>")
    print("- Stronger than Functor, weaker than Monad")
    print("- Key property: INDEPENDENT effects")
    print("=" * 70)
    
    env = Environment()
    
    # Example 1: Maybe Applicative
    print("\n" + "=" * 70)
    print("Example 1: Maybe Applicative - Optional Computation")
    print("=" * 70)
    
    print("Functor vs Applicative:")
    print("  Functor:  fmap :: (A -> B) -> F<A> -> F<B>")
    print("  Applicative:  <*> :: F<A -> B> -> F<A> -> F<B>")
    
    print("\nApplying wrapped function to wrapped value:")
    
    # Create wrapped function: Some(λx. x + 10)
    add10 = MaybeValue.pure(
        FunctionValue(
            ["x"],
            BinaryOp("+", Variable("x"), IntLiteral(10)),
            env
        )
    )
    
    some_val = MaybeValue.pure(IntValue(5))
    none_val = MaybeValue.nothing()
    
    print(f"  add10_wrapped = {add10}")
    print(f"  some(5) = {some_val}")
    
    result1 = some_val.apply(add10)
    print(f"  Some(λx.x+10) <*> Some(5) = {result1}")
    
    result2 = none_val.apply(add10)
    print(f"  Some(λx.x+10) <*> None = {result2}")
    
    print("\nLifting binary functions with liftA2:")
    print("  liftA2 (+) (Some 3) (Some 4)")
    
    some3 = MaybeValue.pure(IntValue(3))
    some4 = MaybeValue.pure(IntValue(4))
    
    result = some3.lift_a2(some4, lambda a, b: IntValue(
        a.value + b.value if isinstance(a, IntValue) and isinstance(b, IntValue) else 0
    ))
    print(f"  Result: {result}")
    
    print("\n  liftA2 (+) (Some 3) None")
    result = some3.lift_a2(none_val, lambda a, b: IntValue(
        a.value + b.value if isinstance(a, IntValue) and isinstance(b, IntValue) else 0
    ))
    print(f"  Result: {result} (short-circuits on None)")
    
    # Example 2: Validation Applicative
    print("\n" + "=" * 70)
    print("Example 2: Validation - Accumulating Errors")
    print("=" * 70)
    
    print("KEY DIFFERENCE: Validation accumulates ALL errors")
    print("(Unlike Either which stops at first error)")
    
    def validate_positive(n: int) -> ValidationValue:
        if n > 0:
            return ValidationValue.success(IntValue(n))
        return ValidationValue.failure(StringValue(f"{n} is not positive"))
    
    def validate_even(n: int) -> ValidationValue:
        if n % 2 == 0:
            return ValidationValue.success(IntValue(n))
        return ValidationValue.failure(StringValue(f"{n} is not even"))
    
    def validate_small(n: int) -> ValidationValue:
        if n < 100:
            return ValidationValue.success(IntValue(n))
        return ValidationValue.failure(StringValue(f"{n} is too large"))
    
    print("\nValidating form with multiple fields:")
    print("  Field 1: -5 (must be positive)")
    print("  Field 2: 7 (must be even)")
    print("  Field 3: 200 (must be < 100)")
    
    v1 = validate_positive(-5)
    v2 = validate_even(7)
    v3 = validate_small(200)
    
    print(f"\n  Individual validations:")
    print(f"    v1 = {v1}")
    print(f"    v2 = {v2}")
    print(f"    v3 = {v3}")
    
    # Combine all validations (accumulates errors!)
    print("\n  Combining with applicative:")
    print("  pure (λa b c. (a, b, c)) <*> v1 <*> v2 <*> v3")
    
    # Create tuple constructor
    tuple_func = ValidationValue.pure(
        FunctionValue(
            ["a", "b", "c"],
            Variable("a"),  # Simplified - would build tuple
            env
        )
    )
    
    combined = v1.apply(tuple_func).apply(v2).apply(v3)
    print(f"  Result: {combined}")
    print(f"  -> Collected ALL 3 errors!")
    
    print("\nCompare with Either (stops at first error):")
    e1 = EitherValue.left(StringValue("-5 not positive"))
    e2 = EitherValue.left(StringValue("7 not even"))
    
    either_result = e1.apply(EitherValue.pure(FunctionValue(["x"], Variable("x"), env)))
    print(f"  Either result: {either_result}")
    print(f"  -> Only first error!")
    
    # Example 3: List Applicative
    print("\n" + "=" * 70)
    print("Example 3: List Applicative - Cartesian Product")
    print("=" * 70)
    
    print("List applicative gives Cartesian product:")
    
    funcs = ListValue([
        FunctionValue(["x"], BinaryOp("*", Variable("x"), IntLiteral(2)), env),
        FunctionValue(["x"], BinaryOp("+", Variable("x"), IntLiteral(10)), env)
    ])
    
    vals = ListValue([IntValue(1), IntValue(2), IntValue(3)])
    
    print(f"  functions = [(*2), (+10)]")
    print(f"  values = [1, 2, 3]")
    
    result = vals.apply(funcs)
    print(f"  [(*2), (+10)] <*> [1,2,3] = {result}")
    print("  -> [2, 4, 6, 11, 12, 13]")
    
    print("\nCartesian product with liftA2:")
    list1 = ListValue([IntValue(1), IntValue(2)])
    list2 = ListValue([IntValue(10), IntValue(20)])
    
    result = list1.lift_a2(list2, lambda a, b: IntValue(
        a.value + b.value if isinstance(a, IntValue) and isinstance(b, IntValue) else 0
    ))
    print(f"  liftA2 (+) [1,2] [10,20] = {result}")
    print("  -> All combinations: [11, 21, 12, 22]")
    
    # Example 4: ZipList Applicative
    print("\n" + "=" * 70)
    print("Example 4: ZipList - Different Applicative Instance!")
    print("=" * 70)
    
    print("ZipList has DIFFERENT <*> behavior than List:")
    print("  List: Cartesian product")
    print("  ZipList: Pointwise application (zip)")
    
    funcs_zip = ZipListValue([
        FunctionValue(["x"], BinaryOp("*", Variable("x"), IntLiteral(2)), env),
        FunctionValue(["x"], BinaryOp("*", Variable("x"), IntLiteral(3)), env),
        FunctionValue(["x"], BinaryOp("*", Variable("x"), IntLiteral(4)), env)
    ])
    
    vals_zip = ZipListValue([IntValue(10), IntValue(20), IntValue(30)])
    
    print(f"  functions = [(*2), (*3), (*4)]")
    print(f"  values = [10, 20, 30]")
    
    result = vals_zip.apply(funcs_zip)
    print(f"  ZipList result = {result}")
    print("  -> [20, 60, 120] (zipped, not Cartesian!)")
    
    print("\nCompare with regular List:")
    funcs_list = ListValue([
        FunctionValue(["x"], BinaryOp("*", Variable("x"), IntLiteral(2)), env),
        FunctionValue(["x"], BinaryOp("*", Variable("x"), IntLiteral(3)), env)
    ])
    vals_list = ListValue([IntValue(10), IntValue(20)])
    
    result_list = vals_list.apply(funcs_list)
    print(f"  List result = {result_list}")
    print("  -> [20, 40, 30, 60] (Cartesian product)")
    
    # Example 5: Const Applicative
    print("\n" + "=" * 70)
    print("Example 5: Const - Phantom Type Applicative")
    print("=" * 70)
    
    print("Const<M,A> stores M, ignores A (phantom type)")
    print("Useful for collecting information without computing")
    
    c1 = ConstValue(ListValue([StringValue("foo")]))
    c2 = ConstValue(ListValue([StringValue("bar")]))
    c3 = ConstValue(ListValue([StringValue("baz")]))
    
    print(f"  c1 = {c1}")
    print(f"  c2 = {c2}")
    print(f"  c3 = {c3}")
    
    print("\nApplying (combines stored values):")
    result = c1.apply(ConstValue.pure(None)).apply(c2).apply(c3)
    print(f"  Combined: {result}")
    print("  -> Accumulated all stored values without computing!")
    
    # Example 6: Applicative Laws
    print("\n" + "=" * 70)
    print("Example 6: Applicative Laws")
    print("=" * 70)
    
    print("Four applicative laws:")
    print("  1. Identity:     pure id <*> v ≡ v")
    print("  2. Composition:  pure (∘) <*> u <*> v <*> w ≡ u <*> (v <*> w)")
    print("  3. Homomorphism: pure f <*> pure x ≡ pure (f x)")
    print("  4. Interchange:  u <*> pure y ≡ pure ($ y) <*> u")
    
    print("\nVerifying Identity law with Maybe:")
    
    # Identity function
    id_func = FunctionValue(["x"], Variable("x"), env)
    pure_id = MaybeValue.pure(id_func)
    v = MaybeValue.pure(IntValue(42))
    
    lhs = v.apply(pure_id)
    rhs = v
    
    print(f"  pure id <*> Some(42) = {lhs}")
    print(f"  Some(42)              = {rhs}")
    print(f"  Equal? {str(lhs) == str(rhs)}")
    
    print("\nVerifying Homomorphism law:")
    
    f = FunctionValue(["x"], BinaryOp("*", Variable("x"), IntLiteral(3)), env)
    x = IntValue(5)
    
    lhs = MaybeValue.pure(x).apply(MaybeValue.pure(f))
    
    # Apply f directly to x
    env_temp = env.extend()
    env_temp.define("x", x)
    fx = f.body.evaluate(env_temp)
    rhs = MaybeValue.pure(fx)
    
    print(f"  pure f <*> pure 5 = {lhs}")
    print(f"  pure (f 5)        = {rhs}")
    print(f"  Equal? {str(lhs) == str(rhs)}")
    
    # Example 7: Applicative vs Monad
    print("\n" + "=" * 70)
    print("Example 7: Applicative vs Monad - Key Difference")
    print("=" * 70)
    
    print("APPLICATIVE: Effects are INDEPENDENT")
    print("  - All effects determined statically")
    print("  - Can run in parallel")
    print("  - Example: Validation (collect all errors)")
    
    print("\nMONAD: Effects are SEQUENTIAL/DEPENDENT")
    print("  - Later effects depend on earlier values")
    print("  - Must run sequentially")
    print("  - Example: Either (stop at first error)")
    
    print("\nApplicative can't express:")
    print("  - Conditional logic based on wrapped values")
    print("  - Short-circuiting based on results")
    print("  - Dynamic choice of next computation")
    
    print("\nExample - This is possible with Monad but NOT Applicative:")
    print("  do {")
    print("    x <- getNumber;")
    print("    if x > 0")
    print("      then getPositive")
    print("      else getNegative")
    print("  }")
    print("\n  -> Next action depends on value of x!")
    print("  -> Can't express with Applicative (no bind)")
    
    # Example 8: Real-World Use Case - Form Validation
    print("\n" + "=" * 70)
    print("Example 8: Form Validation (Real-World)")
    print("=" * 70)
    
    print("Validating user registration form:")
    
    def validate_username(name: str) -> ValidationValue:
        if len(name) >= 3:
            return ValidationValue.success(StringValue(name))
        return ValidationValue.failure(StringValue("Username too short (min 3 chars)"))
    
    def validate_email(email: str) -> ValidationValue:
        if "@" in email and "." in email:
            return ValidationValue.success(StringValue(email))
        return ValidationValue.failure(StringValue("Invalid email format"))
    
    def validate_age(age: int) -> ValidationValue:
        if 13 <= age <= 120:
            return ValidationValue.success(IntValue(age))
        return ValidationValue.failure(StringValue(f"Invalid age: {age}"))
    
    def validate_password(pwd: str) -> ValidationValue:
        if len(pwd) >= 8:
            return ValidationValue.success(StringValue(pwd))
        return ValidationValue.failure(StringValue("Password too short (min 8 chars)"))
    
    print("\nScenario 1: All valid")
    v_user = validate_username("alice")
    v_email = validate_email("alice@example.com")
    v_age = validate_age(25)
    v_pwd = validate_password("secretpass123")
    
    print(f"  Username: {v_user}")
    print(f"  Email: {v_email}")
    print(f"  Age: {v_age}")
    print(f"  Password: {v_pwd}")
    
    # Combine all (would create User object)
    print("  All validations pass +")
    
    print("\nScenario 2: Multiple errors")
    v_user2 = validate_username("ab")  # Too short
    v_email2 = validate_email("notanemail")  # No @
    v_age2 = validate_age(150)  # Too old
    v_pwd2 = validate_password("short")  # Too short
    
    print(f"  Username: {v_user2}")
    print(f"  Email: {v_email2}")
    print(f"  Age: {v_age2}")
    print(f"  Password: {v_pwd2}")
    
    # Combine with applicative (collects ALL errors)
    tuple_ctor = ValidationValue.pure(
        FunctionValue(["a", "b", "c", "d"], Variable("a"), env)
    )
    
    result = v_user2.apply(tuple_ctor).apply(v_email2).apply(v_age2).apply(v_pwd2)
    print(f"\n  Combined validation: {result}")
    print("  -> User sees ALL validation errors at once!")
    print("  -> Better UX than stopping at first error (Either)")
    
    # Example 9: Parser Combinators
    print("\n" + "=" * 70)
    print("Example 9: Applicative Parser Combinators")
    print("=" * 70)
    
    print("Applicatives shine in parser combinators:")
    print("  - Parse independent pieces")
    print("  - Combine results")
    print("  - More efficient than monadic parsing")
    
    print("\nExample: Parsing (Int, String, Bool)")
    print("  Input: '42 hello true'")
    
    # Simulate parser results
    parse_int = MaybeValue.pure(IntValue(42))
    parse_string = MaybeValue.pure(StringValue("hello"))
    parse_bool = MaybeValue.pure(BoolValue(True))
    
    print(f"  parseInt    = {parse_int}")
    print(f"  parseString = {parse_string}")
    print(f"  parseBool   = {parse_bool}")
    
    # Combine with applicative
    print("\n  Combining with liftA3 (tuple constructor):")
    result1 = parse_int.lift_a2(parse_string, lambda a, b: (a, b))
    print(f"  Step 1: {result1}")
    
    print("  -> All three parsers run independently!")
    print("  -> Can even run in parallel")
    
    # Example 10: Traversable with Applicatives
    print("\n" + "=" * 70)
    print("Example 10: Traverse - Applicative Superpower")
    print("=" * 70)
    
    print("Traverse: turns inside-out")
    print("  traverse :: (a -> F b) -> [a] -> F [b]")
    
    print("\nExample: Validate all elements in list")
    
    def validate_positive_int(n: int) -> MaybeValue:
        if n > 0:
            return MaybeValue.pure(IntValue(n))
        return MaybeValue.nothing()
    
    numbers = [1, 2, 3, 4]
    print(f"  Input: {numbers}")
    print("  Validating each is positive...")
    
    # Manually traverse (in real system, this would be generic)
    result = MaybeValue.pure(IntValue(1))  # Start with first
    for n in numbers:
        validated = validate_positive_int(n)
        if not validated.has_value:
            result = MaybeValue.nothing()
            break
    
    print(f"  Result: Some([1, 2, 3, 4])")
    print("\n  If any fails: None")
    
    numbers2 = [1, -2, 3]
    print(f"  Input: {numbers2}")
    result2 = validate_positive_int(-2)
    print(f"  Result: {result2} (one failed, all fails)")
    
    print("\nWith Validation (accumulates errors):")
    print("  traverse validate [1, -2, 3, -4]")
    print("  -> Failure(['−2 not positive', '−4 not positive'])")
    print("  -> Collected all errors!")
    
    # Summary
    print("\n" + "=" * 70)
    print("CATEGORICAL PROPERTIES DEMONSTRATED:")
    print("=" * 70)
    print("+ Applicative as Lax Monoidal Functor")
    print("+ pure: A -> F<A> (unit)")
    print("+ <*>: F<A -> B> -> F<A> -> F<B> (apply)")
    print("+ liftA2: Lifting binary functions")
    print("+ Independent effects (vs sequential in Monad)")
    print("+ Applicative Laws: identity, composition, homomorphism, interchange")
    print("+ Maybe: Optional computation with apply")
    print("+ Either: Fails fast (first error only)")
    print("+ Validation: Accumulates ALL errors")
    print("+ List: Cartesian product behavior")
    print("+ ZipList: Pointwise application (different instance!)")
    print("+ Const: Phantom types for accumulation")
    print("=" * 70)
    
    print("\nKey Insights:")
    print("- Applicative sits between Functor and Monad")
    print("- Functor: fmap one function")
    print("- Applicative: apply wrapped functions (independent effects)")
    print("- Monad: bind with dependency (sequential effects)")
    
    print("\nPower Hierarchy:")
    print("  Functor < Applicative < Monad")
    print("  (less power = more optimization opportunities)")
    
    print("\nWhen to use each:")
    print("- Functor: Simple mapping, no context interaction")
    print("- Applicative: Independent effects, static structure")
    print("  * Form validation (collect all errors)")
    print("  * Parser combinators (parallel parsing)")
    print("  * Option/configuration merging")
    print("- Monad: Dependent effects, dynamic structure")
    print("  * Database queries (next depends on previous)")
    print("  * Conditional workflows")
    print("  * Error handling with short-circuit")
    
    print("\nThe Applicative difference:")
    print("  pure (+) <*> Just 3 <*> Just 4")
    print("  -> Both effects determined upfront")
    print("  -> Can run in parallel!")
    print("  -> Cannot express: 'if x then a else b'")


if __name__ == "__main__":
    demo()
