"""
Examples for Algebraic Data Types and Type Classes
"""

from dataclasses import dataclass
from functional_types import (
    # ADT
    adt, ADT,
    # Type classes
    List,
    # Monoids
    Sum, Product, All, Any, First, Last, mconcat,
    # Pattern matching
    PatternMatcher,
    # Do notation
    Do,
    # Lenses
    Lens, lens,
)
from functional_core import Some, nothing, Maybe



# ALGEBRAIC DATA TYPES - SUM TYPES

def example_adt_shapes():
    """Defining and using sum types."""
    print("Algebraic Data Types - Shapes:")
    
    # Define an ADT for shapes
    @adt('Shape')
    @dataclass(frozen=True)
    class Circle:
        radius: float
    
    @adt('Shape')
    @dataclass(frozen=True)
    class Rectangle:
        width: float
        height: float
    
    @adt('Shape')
    @dataclass(frozen=True)
    class Triangle:
        base: float
        height: float
    
    # Create instances
    shapes = [
        Circle(5.0),
        Rectangle(10.0, 20.0),
        Triangle(8.0, 12.0),
    ]
    
    # Pattern match using the case method
    def area(shape):
        return shape.match(
            Circle=lambda radius: 3.14159 * radius ** 2,
            Rectangle=lambda width, height: width * height,
            Triangle=lambda base, height: 0.5 * base * height,
        )
    
    for shape in shapes:
        print(f"{shape} -> area = {area(shape):.2f}")
    print()


def example_adt_expr():
    """Expression ADT with evaluation."""
    print("ADT - Expression Tree:")
    
    @adt('Expr')
    @dataclass(frozen=True)
    class Lit:
        """Literal number."""
        value: int
    
    @adt('Expr')
    @dataclass(frozen=True)
    class Add:
        """Addition."""
        left: 'Expr'
        right: 'Expr'
    
    @adt('Expr')
    @dataclass(frozen=True)
    class Mul:
        """Multiplication."""
        left: 'Expr'
        right: 'Expr'
    
    # Build expression: (2 + 3) * 4
    expr = Mul(
        Add(Lit(2), Lit(3)),
        Lit(4)
    )
    
    # Evaluate with pattern matching
    def eval_expr(expr):
        return expr.match(
            Lit=lambda value: value,
            Add=lambda left, right: eval_expr(left) + eval_expr(right),
            Mul=lambda left, right: eval_expr(left) * eval_expr(right),
        )
    
    print(f"Expression: (2 + 3) * 4")
    print(f"Result: {eval_expr(expr)}")
    print()


def example_adt_option():
    """Custom Option type using ADT."""
    print("ADT - Custom Option Type:")
    
    @adt('Option')
    @dataclass(frozen=True)
    class Nope:
        """No value."""
        pass
    
    @adt('Option')
    @dataclass(frozen=True)
    class Yep:
        """Has a value."""
        value: any
    
    def safe_divide(a, b):
        if b == 0:
            return Nope()
        return Yep(a / b)
    
    results = [
        safe_divide(10, 2),
        safe_divide(10, 0),
        safe_divide(20, 4),
    ]
    
    for result in results:
        output = result.match(
            Nope=lambda: "Error: Division by zero",
            Yep=lambda value: f"Result: {value}",
        )
        print(output)
    print()



# LIST AS FUNCTOR / APPLICATIVE / MONAD

def example_list_functor():
    """List as a Functor."""
    print("List Functor:")
    
    numbers = List.of(1, 2, 3, 4, 5)
    print(f"Original: {numbers}")
    
    # fmap (Functor)
    doubled = numbers.fmap(lambda x: x * 2)
    print(f"Doubled: {doubled}")
    
    squared = numbers.fmap(lambda x: x ** 2)
    print(f"Squared: {squared}")
    print()


def example_list_applicative():
    """List as an Applicative."""
    print("List Applicative:")
    
    # pure
    single = List.pure(42)
    print(f"Pure 42: {single}")
    
    # ap - apply functions to values
    values = List.of(1, 2, 3)
    functions = List.of(lambda x: x * 2, lambda x: x + 10)
    
    result = values.ap(functions)
    print(f"Values: {values}")
    print(f"Functions: [*2, +10]")
    print(f"Applied: {result}")
    print()


def example_list_monad():
    """List as a Monad."""
    print("List Monad:")
    
    # bind (flatMap) - for list comprehensions
    numbers = List.of(1, 2, 3)
    
    # Each number generates a list, then flatten
    result = numbers.bind(lambda x: List.of(x, x * 10))
    print(f"Numbers: {numbers}")
    print(f"Bind (x -> [x, x*10]): {result}")
    
    # Cartesian product using bind
    letters = List.of('a', 'b')
    nums = List.of(1, 2)
    
    pairs = letters.bind(lambda letter:
        nums.fmap(lambda num: (letter, num))
    )
    print(f"\nCartesian product {letters} × {nums}:")
    print(f"Result: {pairs}")
    print()


def example_list_foldable():
    """List as Foldable."""
    print("List Foldable:")
    
    numbers = List.of(1, 2, 3, 4, 5)
    print(f"Numbers: {numbers}")
    
    # Fold left (sum)
    sum_result = numbers.foldl(lambda acc, x: acc + x, 0)
    print(f"Sum (foldl): {sum_result}")
    
    # Fold right (construct list in reverse)
    reversed_list = numbers.foldr(lambda x, acc: [x] + acc, [])
    print(f"Reverse (foldr): {reversed_list}")
    
    # Product
    product = numbers.foldl(lambda acc, x: acc * x, 1)
    print(f"Product: {product}")
    print()


# MONOIDS

def example_monoids():
    """Using monoids for combining values."""
    print("Monoids:")
    
    # Sum monoid
    sums = [Sum(1), Sum(2), Sum(3), Sum(4)]
    total = mconcat(sums)
    print(f"Sum: {sums} -> {total}")
    
    # Product monoid
    products = [Product(2), Product(3), Product(4)]
    total_product = mconcat(products)
    print(f"Product: {products} -> {total_product}")
    
    # All monoid (AND)
    conditions = [All(True), All(True), All(True)]
    all_true = mconcat(conditions)
    print(f"All: {conditions} -> {all_true}")
    
    conditions2 = [All(True), All(False), All(True)]
    has_false = mconcat(conditions2)
    print(f"All: {conditions2} -> {has_false}")
    
    # Any monoid (OR)
    flags = [Any(False), Any(False), Any(True)]
    any_true = mconcat(flags)
    print(f"Any: {flags} -> {any_true}")
    
    # First monoid
    firsts = [First(nothing()), First(Some(10)), First(Some(20))]
    first_some = mconcat(firsts)
    print(f"First: {[f.value for f in firsts]} -> {first_some}")
    
    # Last monoid
    lasts = [Last(Some(10)), Last(nothing()), Last(Some(20))]
    last_some = mconcat(lasts)
    print(f"Last: {[l.value for l in lasts]} -> {last_some}")
    print()


def example_list_monoid():
    """List as a Monoid (concatenation)."""
    print("List Monoid:")
    
    list1 = List.of(1, 2, 3)
    list2 = List.of(4, 5, 6)
    list3 = List.of(7, 8, 9)
    
    # Append (semigroup)
    combined = list1.append(list2).append(list3)
    print(f"{list1} + {list2} + {list3}")
    print(f"= {combined}")
    
    # Empty (monoid identity)
    empty = List.empty()
    with_empty = list1.append(empty)
    print(f"\n{list1} + empty = {with_empty}")
    print()



# PATTERN MATCHING

def example_pattern_matching():
    """Advanced pattern matching."""
    print("Pattern Matching:")
    
    @adt('Result')
    @dataclass(frozen=True)
    class Success:
        value: int
    
    @adt('Result')
    @dataclass(frozen=True)
    class Failure:
        error: str
    
    results = [
        Success(42),
        Failure("Network error"),
        Success(100),
    ]
    
    for result in results:
        message = result.match(
            Success=lambda value: f"✓ Success: {value}",
            Failure=lambda error: f"✗ Error: {error}",
        )
        print(message)
    print()



# DO NOTATION

def example_do_notation():
    """Do-notation for monadic composition."""
    print("Do Notation:")
    
    # Chain Maybe operations with do-notation
    result = (
        Do(Some(5))
        .bind(lambda x: Some(x * 2))
        .bind(lambda x: Some(x + 3))
        .bind(lambda x: Some(x ** 2))
        .result()
    )
    
    print(f"Do notation chain: {result}")
    
    # With lists
    result2 = (
        Do(List.of(1, 2))
        .bind(lambda x: List.of(x, x * 10))
        .bind(lambda x: List.of(x, x + 100))
        .result()
    )
    
    print(f"Do notation with lists: {result2}")
    print()


# LENSES

def example_lenses():
    """Using lenses for nested immutable updates."""
    print("Lenses:")
    
    @dataclass(frozen=True)
    class Address:
        street: str
        city: str
    
    @dataclass(frozen=True)
    class Person:
        name: str
        age: int
        address: Address
    
    # Create lenses
    person_name = lens(
        getter=lambda p: p.name,
        setter=lambda p, n: dataclass.replace(p, name=n)
    )
    
    person_address = lens(
        getter=lambda p: p.address,
        setter=lambda p, a: dataclass.replace(p, address=a)
    )
    
    address_city = lens(
        getter=lambda a: a.city,
        setter=lambda a, c: dataclass.replace(a, city=c)
    )
    
    # Compose lenses to focus deep
    person_city = person_address.compose(address_city)
    
    # Create a person
    from dataclasses import replace as dataclass_replace
    
    # Manual lens implementation for dataclasses
    def make_lens(field_name):
        return lens(
            getter=lambda obj: getattr(obj, field_name),
            setter=lambda obj, val: dataclass_replace(obj, **{field_name: val})
        )
    
    name_lens = make_lens('name')
    age_lens = make_lens('age')
    
    alice = Person("Alice", 30, Address("123 Main St", "NYC"))
    
    print(f"Original: {alice}")
    
    # Update using lens
    older_alice = age_lens.modify(alice, lambda age: age + 1)
    print(f"After birthday: {older_alice}")
    
    # Get using lens
    current_age = age_lens.get(alice)
    print(f"Current age: {current_age}")
    print()


# TYPE CLASS POLYMORPHISM

def example_type_class_polymorphism():
    """Using type classes for polymorphic functions."""
    print("Type Class Polymorphism:")
    
    def double_all_list(functor):
        """Works with any Functor that has fmap."""
        return functor.fmap(lambda x: x * 2)
    
    def double_all_maybe(functor):
        """Works with Maybe using map."""
        return functor.map(lambda x: x * 2)
    
    # Works with Maybe
    maybe_nums = Some(5)
    doubled_maybe = double_all_maybe(maybe_nums)
    print(f"Maybe functor: {maybe_nums} -> {doubled_maybe}")
    
    # Works with List
    list_nums = List.of(1, 2, 3)
    doubled_list = double_all_list(list_nums)
    print(f"List functor: {list_nums} -> {doubled_list}")
    
    # Both are functors - just different method names
    print("\nBoth List and Maybe are Functors!")
    print("List uses: fmap")
    print("Maybe uses: map (aliased to fmap in type class instance)")
    print()


# REAL-WORLD EXAMPLE: VALIDATION

def example_validation_with_monoids():
    """Validation that accumulates errors using monoids."""
    print("Validation with Monoids:")
    
    @dataclass(frozen=True)
    class Validation:
        """Validation result - either success or list of errors."""
        errors: List[str]
        value: Maybe[any]
        
        def is_valid(self):
            return self.errors.is_empty()
        
        def append_error(self, error):
            return Validation(
                errors=self.errors.cons(error),
                value=nothing()
            )
        
        @classmethod
        def success(cls, value):
            return cls(List.empty(), Some(value))
        
        @classmethod
        def failure(cls, error):
            return cls(List.of(error), nothing())
    
    def validate_age(age):
        if age < 0:
            return Validation.failure("Age cannot be negative")
        if age > 150:
            return Validation.failure("Age too high")
        return Validation.success(age)
    
    def validate_name(name):
        if not name:
            return Validation.failure("Name cannot be empty")
        if len(name) < 2:
            return Validation.failure("Name too short")
        return Validation.success(name)
    
    # Validate
    test_cases = [
        (30, "Alice"),
        (-5, "Bob"),
        (200, ""),
        (25, "X"),
    ]
    
    for age, name in test_cases:
        age_val = validate_age(age)
        name_val = validate_name(name)
        
        # Combine validations
        errors = age_val.errors.append(name_val.errors)
        
        if errors.is_empty():
            print(f"✓ Valid: age={age}, name={name}")
        else:
            print(f"✗ Invalid: age={age}, name={name}")
            for error in errors:
                print(f"  - {error}")
    print()


# ALL

if __name__ == "__main__":
    example_adt_shapes()
    example_adt_expr()
    example_adt_option()
    example_list_functor()
    example_list_applicative()
    example_list_monad()
    example_list_foldable()
    example_monoids()
    example_list_monoid()
    example_pattern_matching()
    example_do_notation()
    example_lenses()
    example_type_class_polymorphism()
    example_validation_with_monoids()
    
    print("\nAll type class examples completed!:")

