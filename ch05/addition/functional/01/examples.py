"""
Examples demonstrating the functional programming core
"""

from functional_core import (
    Some, nothing, maybe,
    Ok, Err,
    compose, pipe, curry,
    safe_divide, safe_get, safe_parse_int, safe_head,
    traverse_maybe, sequence_maybe,
    foldl, identity
)


def example_maybe_basics():
    """Basic Maybe/Option usage"""
    print("Maybe Basics")
    
    # Creating Maybe values
    some_value = Some(42)
    no_value = nothing()
    
    print(f"some_value: {some_value}")
    print(f"no_value: {no_value}")
    print(f"some_value.is_some(): {some_value.is_some()}")
    print(f"no_value.is_none(): {no_value.is_none()}")
    
    # Getting values
    print(f"some_value.get_or_else(0): {some_value.get_or_else(0)}")
    print(f"no_value.get_or_else(0): {no_value.get_or_else(0)}")
    print()


def example_maybe_chaining():
    """Demonstrating Maybe chaining with map and flat_map"""
    print("Maybe Chaining")
    
    # Map transforms the value inside
    result = Some(5).map(lambda x: x * 2).map(lambda x: x + 1)
    print(f"Some(5).map(*2).map(+1): {result}")
    
    # Map on Nothing does nothing
    result = nothing().map(lambda x: x * 2)
    print(f"nothing().map(*2): {result}")
    
    # flat_map for operations that return Maybe
    def safe_sqrt(x):
        return Some(x ** 0.5) if x >= 0 else nothing()
    
    result = Some(16).flat_map(safe_sqrt)
    print(f"Some(16).flat_map(safe_sqrt): {result}")
    
    result = Some(-4).flat_map(safe_sqrt)
    print(f"Some(-4).flat_map(safe_sqrt): {result}")
    
    # Filter
    result = Some(10).filter(lambda x: x > 5)
    print(f"Some(10).filter(>5): {result}")
    
    result = Some(3).filter(lambda x: x > 5)
    print(f"Some(3).filter(>5): {result}")
    print()


def example_result_basics():
    """Basic Result/Either usage"""
    print("Result Basics")
    
    # Success and failure
    success = Ok(100)
    failure = Err("Something went wrong")
    
    print(f"success: {success}")
    print(f"failure: {failure}")
    print(f"success.is_ok(): {success.is_ok()}")
    print(f"failure.is_err(): {failure.is_err()}")
    
    # Safe division
    result = safe_divide(10, 2)
    print(f"safe_divide(10, 2): {result}")
    
    result = safe_divide(10, 0)
    print(f"safe_divide(10, 0): {result}")
    print()


def example_result_chaining():
    """Demonstrating Result chaining"""
    print("Result Chaining")
    
    # Chain multiple operations
    result = (
        safe_parse_int("42")
        .flat_map(lambda x: safe_divide(100, x))
        .map(lambda x: x * 2)
    )
    print(f"Parse '42', divide 100 by it, multiply by 2: {result}")
    
    # Error propagation
    result = (
        safe_parse_int("not a number")
        .flat_map(lambda x: safe_divide(100, x))
        .map(lambda x: x * 2)
    )
    print(f"Parse 'not a number', then divide: {result}")
    
    # Handle errors with map_err
    result = (
        safe_parse_int("xyz")
        .map_err(lambda e: f"ERROR: {e}")
    )
    print(f"Parse error with custom message: {result}")
    print()


def example_function_composition():
    """Function composition and piping"""
    print("Function Composition")
    
    # Compose (right to left)
    add_one = lambda x: x + 1
    double = lambda x: x * 2
    square = lambda x: x ** 2
    
    composed = compose(add_one, double, square)
    print(f"compose(+1, *2, ^2)(5) = {composed(5)}")  # (5^2 * 2) + 1 = 51
    
    # Pipe (left to right) - more intuitive
    piped = pipe(square, double, add_one)
    print(f"pipe(^2, *2, +1)(5) = {piped(5)}")  # ((5^2) * 2) + 1 = 51
    
    # With Maybe
    process = pipe(
        lambda x: Some(x),
        lambda m: m.map(lambda x: x * 2),
        lambda m: m.filter(lambda x: x < 100)
    )
    
    print(f"Maybe pipeline with 10: {process(10)}")
    print(f"Maybe pipeline with 60: {process(60)}")
    print()


def example_currying():
    """Currying examples"""
    print("Currying")
    
    def add(a, b, c):
        return a + b + c
    
    curried_add = curry(add)
    
    print(f"curry(add)(1)(2)(3): {curried_add(1)(2)(3)}")
    print(f"curry(add)(1, 2)(3): {curried_add(1, 2)(3)}")
    
    # Partial application
    add_5 = curried_add(5)
    add_5_and_10 = add_5(10)
    
    print(f"add_5_and_10(3): {add_5_and_10(3)}")
    print()


def example_safe_operations():
    """Safe operations that return Maybe"""
    print("Safe Operations")
    
    # Safe dictionary lookup
    user_data = {"name": "Alice", "age": 30}
    
    name = safe_get(user_data, "name")
    email = safe_get(user_data, "email")
    
    print(f"safe_get 'name': {name}")
    print(f"safe_get 'email': {email}")
    
    # Safe head and tail
    numbers = [1, 2, 3, 4, 5]
    empty_list = []
    
    print(f"safe_head([1,2,3,4,5]): {safe_head(numbers)}")
    print(f"safe_head([]): {safe_head(empty_list)}")
    
    # Chain safe operations
    result = (
        safe_head(numbers)
        .map(lambda x: x * 10)
        .filter(lambda x: x > 5)
    )
    print(f"Get head, multiply by 10, filter > 5: {result}")
    print()


def example_traverse_and_sequence():
    """Traverse and sequence operations"""
    print("Traverse and Sequence")
    
    # Parse a list of strings to integers
    strings = ["1", "2", "3", "4"]
    results = traverse_maybe(
        lambda s: maybe(int(s)) if s.isdigit() else nothing(),
        strings
    )
    print(f"Parse valid strings: {results}")
    
    # With invalid data
    bad_strings = ["1", "2", "bad", "4"]
    results = traverse_maybe(
        lambda s: maybe(int(s)) if s.isdigit() else nothing(),
        bad_strings
    )
    print(f"Parse with invalid string: {results}")
    
    # Sequence - convert list of Maybes to Maybe of list
    maybes = [Some(1), Some(2), Some(3)]
    print(f"sequence_maybe([Some(1), Some(2), Some(3)]): {sequence_maybe(maybes)}")
    
    maybes_with_nothing = [Some(1), nothing(), Some(3)]
    print(f"sequence_maybe([Some(1), Nothing, Some(3)]): {sequence_maybe(maybes_with_nothing)}")
    print()


def example_real_world_validation():
    """Real-world validation example"""
    print("Real-World Validation")
    
    def validate_age(age_str):
        """Validate age string and convert to int"""
        return (
            safe_parse_int(age_str)
            .flat_map(lambda age: Ok(age) if 0 <= age <= 150 else Err("Age out of range"))
        )
    
    def validate_email(email):
        """Simple email validation"""
        if "@" in email and "." in email:
            return Ok(email)
        return Err("Invalid email format")
    
    def create_user(name, age_str, email):
        """Create user with validation"""
        age_result = validate_age(age_str)
        email_result = validate_email(email)
        
        if age_result.is_err():
            return age_result
        if email_result.is_err():
            return email_result
        
        return Ok({
            "name": name,
            "age": age_result.get_or_else(0),
            "email": email_result.get_or_else("")
        })
    
    # Valid user
    user1 = create_user("Alice", "30", "alice@example.com")
    print(f"Valid user: {user1}")
    
    # Invalid age
    user2 = create_user("Bob", "200", "bob@example.com")
    print(f"Invalid age: {user2}")
    
    # Invalid email
    user3 = create_user("Charlie", "25", "not-an-email")
    print(f"Invalid email: {user3}")
    print()


def example_data_pipeline():
    """Example of a data processing pipeline"""
    print("Data Pipeline")
    
    # Simulated data processing
    def fetch_user_id(username):
        """Simulate database lookup"""
        users = {"alice": 1, "bob": 2}
        return safe_get(users, username)
    
    def fetch_user_score(user_id):
        """Simulate fetching user score"""
        scores = {1: 95, 2: 87}
        return safe_get(scores, user_id)
    
    def grade_score(score):
        """Convert score to grade"""
        if score >= 90:
            return Some("A")
        elif score >= 80:
            return Some("B")
        else:
            return Some("C")
    
    # Complete pipeline
    def get_user_grade(username):
        return (
            fetch_user_id(username)
            .flat_map(fetch_user_score)
            .flat_map(grade_score)
        )
    
    print(f"Grade for 'alice': {get_user_grade('alice')}")
    print(f"Grade for 'bob': {get_user_grade('bob')}")
    print(f"Grade for 'unknown': {get_user_grade('unknown')}")
    print()


def example_fold_operations():
    """Fold (reduce) operations"""
    print("Fold Operations")
    
    numbers = [1, 2, 3, 4, 5]
    
    # Sum using foldl
    sum_result = foldl(lambda acc, x: acc + x, 0, numbers)
    print(f"Sum of {numbers}: {sum_result}")
    
    # Product
    product = foldl(lambda acc, x: acc * x, 1, numbers)
    print(f"Product of {numbers}: {product}")
    
    # Build a Maybe chain
    maybe_sum = foldl(
        lambda acc, x: acc.map(lambda a: a + x),
        Some(0),
        numbers
    )
    print(f"Maybe sum: {maybe_sum}")
    print()


if __name__ == "__main__":
    example_maybe_basics()
    example_maybe_chaining()
    example_result_basics()
    example_result_chaining()
    example_function_composition()
    example_currying()
    example_safe_operations()
    example_traverse_and_sequence()
    example_real_world_validation()
    example_data_pipeline()
    example_fold_operations()
    
    print("\nAll examples completed!")
