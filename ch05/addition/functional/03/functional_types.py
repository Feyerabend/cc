"""
Algebraic Data Types and Type Classes

This module adds:
- Sum types (tagged unions)
- Product types (records)
- Pattern matching
- Type classes (Functor, Applicative, Monad, etc.)
- Deriving mechanisms
"""

from typing import TypeVar, Generic, Callable, Any, Type, Protocol, runtime_checkable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import inspect


A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
F = TypeVar('F')  # Functor type
M = TypeVar('M')  # Monad type



# ALGEBRAIC DATA TYPES - Sum Types

class ADT(ABC):
    """
    Base class for Algebraic Data Types.
    Provides pattern matching and case analysis.
    """
    
    @classmethod
    def case(cls, **patterns):
        """
        Create a pattern matcher for this ADT.
        
        Example:
            match_shape = Shape.case(
                Circle=lambda r: f"Circle with radius {r}",
                Rectangle=lambda w, h: f"Rectangle {w}x{h}"
            )
        """
        def matcher(instance):
            variant_name = type(instance).__name__
            if variant_name in patterns:
                handler = patterns[variant_name]
                # Get the fields from the instance
                if hasattr(instance, '__dict__'):
                    fields = instance.__dict__
                    return handler(**fields) if fields else handler()
                return handler()
            elif '_' in patterns:  # Default case
                return patterns['_'](instance)
            else:
                raise ValueError(f"No pattern matched for {variant_name}")
        return matcher
    
    def match(self, **patterns):
        """Instance method for pattern matching."""
        return self.case(**patterns)(self)


def adt(name: str):
    """
    Decorator to create ADT variants.
    
    Usage:
        @adt('Shape')
        @dataclass(frozen=True)
        class Circle:
            radius: float
        
        @adt('Shape')
        @dataclass(frozen=True)
        class Rectangle:
            width: float
            height: float
    """
    def decorator(cls):
        # Create a new class that inherits from both ADT and the original class
        class ADTVariant(ADT, cls):
            _adt_name = name
            
            def match(self, **patterns):
                """Instance method for pattern matching."""
                variant_name = self.__class__.__name__
                if variant_name in patterns:
                    handler = patterns[variant_name]
                    # Get the fields from the instance
                    if hasattr(self, '__dict__'):
                        fields = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
                        return handler(**fields) if fields else handler()
                    return handler()
                elif '_' in patterns:  # Default case
                    return patterns['_'](self)
                else:
                    raise ValueError(f"No pattern matched for {variant_name}")
        
        # Copy over class attributes
        ADTVariant.__name__ = cls.__name__
        ADTVariant.__qualname__ = cls.__qualname__
        ADTVariant.__module__ = cls.__module__
        
        return ADTVariant
    return decorator



# TYPE CLASSES - Protocols

@runtime_checkable
class Functor(Protocol[F]):
    """
    Type class for types that can be mapped over.
    
    Laws:
    1. Identity: fmap(id, x) == x
    2. Composition: fmap(compose(f, g), x) == fmap(f, fmap(g, x))
    """
    
    def fmap(self, f: Callable[[A], B]) -> 'Functor[B]':
        """Map a function over the functor."""
        ...


@runtime_checkable
class Applicative(Functor[F], Protocol):
    """
    Type class for applicative functors.
    
    Laws:
    1. Identity: pure(id) <*> v == v
    2. Composition: pure(compose) <*> u <*> v <*> w == u <*> (v <*> w)
    3. Homomorphism: pure(f) <*> pure(x) == pure(f(x))
    4. Interchange: u <*> pure(y) == pure(lambda f: f(y)) <*> u
    """
    
    @classmethod
    def pure(cls, value: A) -> 'Applicative[A]':
        """Lift a value into the applicative context."""
        ...
    
    def ap(self, ff: 'Applicative[Callable[[A], B]]') -> 'Applicative[B]':
        """Apply a function in a context to a value in a context."""
        ...


@runtime_checkable  
class Monad(Applicative[M], Protocol):
    """
    Type class for monads.
    
    Laws:
    1. Left identity: pure(a).bind(f) == f(a)
    2. Right identity: m.bind(pure) == m
    3. Associativity: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """
    
    def bind(self, f: Callable[[A], 'Monad[B]']) -> 'Monad[B]':
        """Monadic bind (>>=)."""
        ...


@runtime_checkable
class Foldable(Protocol[F]):
    """
    Type class for structures that can be folded.
    
    Laws:
    1. foldr(f, z, xs) behaves like reduce from right
    2. foldl(f, z, xs) behaves like reduce from left
    """
    
    def foldr(self, f: Callable[[A, B], B], initial: B) -> B:
        """Fold from the right."""
        ...
    
    def foldl(self, f: Callable[[B, A], B], initial: B) -> B:
        """Fold from the left."""
        ...


@runtime_checkable
class Traversable(Functor[F], Foldable[F], Protocol):
    """
    Type class for structures that can be traversed.
    """
    
    def traverse(self, f: Callable[[A], Applicative[B]]) -> Applicative['Traversable[B]']:
        """Map each element to an action and collect results."""
        ...
    
    def sequence(self) -> Applicative['Traversable[A]']:
        """Evaluate each action and collect results."""
        ...


@runtime_checkable
class Semigroup(Protocol):
    """
    Type class for types with an associative binary operation.
    
    Laws:
    1. Associativity: (x <> y) <> z == x <> (y <> z)
    """
    
    def append(self, other: 'Semigroup') -> 'Semigroup':
        """Associative binary operation (<>)."""
        ...


@runtime_checkable
class Monoid(Semigroup, Protocol):
    """
    Type class for monoids (semigroup with identity).
    
    Laws:
    1. Left identity: empty() <> x == x
    2. Right identity: x <> empty() == x
    3. Associativity: (inherited from Semigroup)
    """
    
    @classmethod
    def empty(cls) -> 'Monoid':
        """Identity element (mempty)."""
        ...



# CONCRETE TYPE CLASS INSTANCES

# Make our existing Maybe a proper Functor/Applicative/Monad
from functional_core import Maybe, Some, nothing


class MaybeFunctor:
    """Functor instance for Maybe."""
    
    @staticmethod
    def fmap(maybe: Maybe[A], f: Callable[[A], B]) -> Maybe[B]:
        return maybe.map(f)


class MaybeApplicative:
    """Applicative instance for Maybe."""
    
    @staticmethod
    def pure(value: A) -> Maybe[A]:
        return Some(value)
    
    @staticmethod
    def ap(maybe: Maybe[A], mf: Maybe[Callable[[A], B]]) -> Maybe[B]:
        """Apply a function in Maybe to a value in Maybe."""
        if mf.is_none() or maybe.is_none():
            return nothing()
        return maybe.map(lambda a: mf.get_or_else(lambda x: x)(a))


class MaybeMonad:
    """Monad instance for Maybe."""
    
    @staticmethod
    def pure(value: A) -> Maybe[A]:
        return Some(value)
    
    @staticmethod
    def bind(maybe: Maybe[A], f: Callable[[A], Maybe[B]]) -> Maybe[B]:
        return maybe.flat_map(f)



# LIST AS TYPE CLASS INSTANCE

@dataclass(frozen=True)
class List(Generic[A]):
    """
    Immutable list that implements Functor, Applicative, Monad.
    """
    items: tuple[A, ...] = field(default_factory=tuple)
    
    @classmethod
    def of(cls, *items: A) -> 'List[A]':
        """Create a List from items."""
        return cls(tuple(items))
    
    @classmethod
    def empty(cls) -> 'List[A]':
        """Empty list."""
        return cls(())
    
    def is_empty(self) -> bool:
        """Check if list is empty."""
        return len(self.items) == 0
    
    def head(self) -> Maybe[A]:
        """Get first element."""
        return Some(self.items[0]) if self.items else nothing()
    
    def tail(self) -> 'List[A]':
        """Get all but first element."""
        return List(self.items[1:]) if self.items else List.empty()
    
    def cons(self, item: A) -> 'List[A]':
        """Prepend an item."""
        return List((item,) + self.items)
    
    # Functor instance
    def fmap(self, f: Callable[[A], B]) -> 'List[B]':
        """Map function over list."""
        return List(tuple(f(x) for x in self.items))
    
    # Applicative instance
    @classmethod
    def pure(cls, value: A) -> 'List[A]':
        """Lift value into list context."""
        return cls.of(value)
    
    def ap(self, fs: 'List[Callable[[A], B]]') -> 'List[B]':
        """Apply functions in list to values in list."""
        result = []
        for f in fs.items:
            for x in self.items:
                result.append(f(x))
        return List(tuple(result))
    
    # Monad instance
    def bind(self, f: Callable[[A], 'List[B]']) -> 'List[B]':
        """Monadic bind for lists (flatMap)."""
        result = []
        for x in self.items:
            result.extend(f(x).items)
        return List(tuple(result))
    
    # Foldable instance
    def foldr(self, f: Callable[[A, B], B], initial: B) -> B:
        """Fold from right."""
        result = initial
        for x in reversed(self.items):
            result = f(x, result)
        return result
    
    def foldl(self, f: Callable[[B, A], B], initial: B) -> B:
        """Fold from left."""
        result = initial
        for x in self.items:
            result = f(result, x)
        return result
    
    # Semigroup instance
    def append(self, other: 'List[A]') -> 'List[A]':
        """Concatenate lists."""
        return List(self.items + other.items)
    
    # Monoid instance
    # (empty is already defined above)
    
    def __repr__(self) -> str:
        return f"List({list(self.items)})"
    
    def __iter__(self):
        return iter(self.items)
    
    def __len__(self):
        return len(self.items)



# COMMON MONOIDS

@dataclass(frozen=True)
class Sum:
    """Monoid for addition."""
    value: int | float
    
    def append(self, other: 'Sum') -> 'Sum':
        return Sum(self.value + other.value)
    
    @classmethod
    def empty(cls) -> 'Sum':
        return Sum(0)


@dataclass(frozen=True)
class Product:
    """Monoid for multiplication."""
    value: int | float
    
    def append(self, other: 'Product') -> 'Product':
        return Product(self.value * other.value)
    
    @classmethod
    def empty(cls) -> 'Product':
        return Product(1)


@dataclass(frozen=True)
class All:
    """Monoid for AND (all true)."""
    value: bool
    
    def append(self, other: 'All') -> 'All':
        return All(self.value and other.value)
    
    @classmethod
    def empty(cls) -> 'All':
        return All(True)


@dataclass(frozen=True)
class Any:
    """Monoid for OR (any true)."""
    value: bool
    
    def append(self, other: 'Any') -> 'Any':
        return Any(self.value or other.value)
    
    @classmethod
    def empty(cls) -> 'Any':
        return Any(False)


@dataclass(frozen=True)
class First(Generic[A]):
    """Monoid that keeps the first Some value."""
    value: Maybe[A]
    
    def append(self, other: 'First[A]') -> 'First[A]':
        if self.value.is_some():
            return self
        return other
    
    @classmethod
    def empty(cls) -> 'First[A]':
        return First(nothing())


@dataclass(frozen=True)
class Last(Generic[A]):
    """Monoid that keeps the last Some value."""
    value: Maybe[A]
    
    def append(self, other: 'Last[A]') -> 'Last[A]':
        if other.value.is_some():
            return other
        return self
    
    @classmethod
    def empty(cls) -> 'Last[A]':
        return Last(nothing())



# PATTERN MATCHING UTILS

class PatternMatcher:
    """Builder for pattern matching."""
    
    def __init__(self):
        self.patterns = {}
    
    def case(self, pattern, handler):
        """Add a case to the pattern matcher."""
        self.patterns[pattern] = handler
        return self
    
    def default(self, handler):
        """Add a default case."""
        self.patterns['_'] = handler
        return self
    
    def match(self, value):
        """Execute the pattern match."""
        # Try type-based matching first
        value_type = type(value).__name__
        if value_type in self.patterns:
            handler = self.patterns[value_type]
            if hasattr(value, '__dict__'):
                return handler(**value.__dict__)
            return handler(value)
        
        # Try value-based matching
        if value in self.patterns:
            return self.patterns[value](value)
        
        # Try default
        if '_' in self.patterns:
            return self.patterns['_'](value)
        
        raise ValueError(f"No pattern matched for {value}")


def match(value):
    """Create a pattern matcher for a value."""
    return PatternMatcher().match(value)



# TYPE CLASS DERIVATION

def derive_functor(cls):
    """
    Automatically derive Functor instance for a class.
    Requires the class to have a map method.
    """
    if not hasattr(cls, 'fmap'):
        if hasattr(cls, 'map'):
            cls.fmap = cls.map
        else:
            raise TypeError(f"{cls.__name__} cannot derive Functor: no map method")
    return cls


def derive_monad(cls):
    """
    Automatically derive Monad instance for a class.
    Requires pure and bind methods (or flat_map).
    """
    if not hasattr(cls, 'bind'):
        if hasattr(cls, 'flat_map'):
            cls.bind = cls.flat_map
        else:
            raise TypeError(f"{cls.__name__} cannot derive Monad: no flat_map method")
    
    if not hasattr(cls, 'pure') and hasattr(cls, '__init__'):
        # Try to create a pure method
        @classmethod
        def pure(klass, value):
            return klass(value)
        cls.pure = pure
    
    return cls



# HIGHER-KINDED TYPES SIMULATION

class HKT(Generic[F, A]):
    """
    Higher-Kinded Type simulation.
    Represents F[A] where F is a type constructor.
    """
    
    def __init__(self, value):
        self.value = value
    
    @classmethod
    def lift(cls, value):
        """Lift a value into HKT."""
        return cls(value)
    
    def lower(self):
        """Extract the underlying value."""
        return self.value



# UTIL FUNCTIONS FOR TYPE CLASSES

def fmap(f: Callable[[A], B], functor: Functor[A]) -> Functor[B]:
    """Generic fmap for any Functor."""
    return functor.fmap(f)


def pure(applicative_class: Type[Applicative], value: A) -> Applicative[A]:
    """Generic pure for any Applicative."""
    return applicative_class.pure(value)


def ap(mf: Applicative[Callable[[A], B]], ma: Applicative[A]) -> Applicative[B]:
    """Generic ap for any Applicative."""
    return ma.ap(mf)


def bind(m: Monad[A], f: Callable[[A], Monad[B]]) -> Monad[B]:
    """Generic bind for any Monad."""
    return m.bind(f)


def mconcat(monoids: list[Monoid]) -> Monoid:
    """Concatenate a list of monoids."""
    if not monoids:
        return monoids[0].__class__.empty()
    
    result = monoids[0]
    for m in monoids[1:]:
        result = result.append(m)
    return result



# DO NOTATION SIMULATION

class DoNotation:
    """
    Simulate Haskell's do-notation for monadic computations.
    
    Usage:
        result = (
            Do(Some(5))
            .bind(lambda x: Some(x * 2))
            .bind(lambda y: Some(y + 1))
            .result()
        )
    """
    
    def __init__(self, monad):
        self.monad = monad
    
    def bind(self, f):
        """Bind operation."""
        self.monad = self.monad.flat_map(f) if hasattr(self.monad, 'flat_map') else self.monad.bind(f)
        return self
    
    def then(self, monad):
        """Sequence operations, discarding first result."""
        return self.bind(lambda _: monad)
    
    def result(self):
        """Get the final result."""
        return self.monad


def Do(monad):
    """Start a do-notation chain."""
    return DoNotation(monad)



# LENS / OPTICS (Basic)

@dataclass(frozen=True)
class Lens(Generic[A, B]):
    """
    A lens for accessing and updating nested immutable data.
    
    A Lens[A, B] focuses on a B inside an A.
    """
    getter: Callable[[A], B]
    setter: Callable[[A, B], A]
    
    def get(self, obj: A) -> B:
        """Get the focused value."""
        return self.getter(obj)
    
    def set(self, obj: A, value: B) -> A:
        """Set the focused value, returning new object."""
        return self.setter(obj, value)
    
    def modify(self, obj: A, f: Callable[[B], B]) -> A:
        """Modify the focused value with a function."""
        return self.set(obj, f(self.get(obj)))
    
    def compose(self, other: 'Lens[B, C]') -> 'Lens[A, C]':
        """Compose two lenses."""
        return Lens(
            getter=lambda a: other.get(self.get(a)),
            setter=lambda a, c: self.set(a, other.set(self.get(a), c))
        )


def lens(getter: Callable[[A], B], setter: Callable[[A, B], A]) -> Lens[A, B]:
    """Create a lens."""
    return Lens(getter, setter)
