"""
Advanced Patterns and Use Cases for Functional Core

This file demonstrates more sophisticated functional
programming patterns and real-world use cases.
"""

from functional_core import (
    Some, nothing, maybe,
    Ok, Err,
    compose, pipe,
    safe_parse_int, safe_divide,
    foldl
)
from typing import List, Dict, Any



# PATTERN 1: Railway-Oriented Programming

def railway_example():
    """
    Railway-oriented programming treats success and failure as two tracks.
    Operations stay on the success track until an error occurs, then switch
    to the error track and stay there.
    """
    print("Railway-Oriented Programming")
    
    # Define a series of validation steps
    def validate_not_empty(s: str):
        return Ok(s) if s.strip() else Err("String is empty")
    
    def validate_length(s: str):
        return Ok(s) if len(s) <= 50 else Err("String too long")
    
    def validate_no_special_chars(s: str):
        return Ok(s) if s.isalnum() else Err("Contains special characters")
    
    def to_uppercase(s: str):
        return Ok(s.upper())
    
    # Build the railway
    def process_input(user_input: str):
        return (
            validate_not_empty(user_input)
            .flat_map(validate_length)
            .flat_map(validate_no_special_chars)
            .flat_map(to_uppercase)
        )
    
    # Test cases
    test_cases = [
        "hello",           # Valid
        "",                # Empty
        "a" * 100,         # Too long
        "hello@world",     # Special chars
    ]
    
    for test in test_cases:
        result = process_input(test)
        print(f"Input: {test!r:20} → {result}")
    print()



# PATTERN 2: Validation Accumulation

def validation_accumulation():
    """
    Sometimes you want to collect ALL validation errors, not just the first.
    This pattern shows how to do that.
    """
    print("Validation Accumulation")
    
    class ValidationErrors:
        def __init__(self):
            self.errors: List[str] = []
        
        def add_error(self, error: str):
            self.errors.append(error)
            return self
        
        def is_valid(self):
            return len(self.errors) == 0
        
        def __repr__(self):
            return f"Errors({self.errors})" if self.errors else "Valid"
    
    def validate_user(data: dict):
        errors = ValidationErrors()
        
        # Check all fields and accumulate errors
        if not data.get("name"):
            errors.add_error("Name is required")
        elif len(data.get("name", "")) < 2:
            errors.add_error("Name too short")
        
        if not data.get("email"):
            errors.add_error("Email is required")
        elif "@" not in data.get("email", ""):
            errors.add_error("Email invalid")
        
        age_result = safe_parse_int(data.get("age", ""))
        if age_result.is_err():
            errors.add_error("Age must be a number")
        elif age_result.get_or_else(-1) < 18:
            errors.add_error("Must be 18 or older")
        
        if errors.is_valid():
            return Ok(data)
        return Err(errors)
    
    # Test cases
    test_users = [
        {"name": "Alice", "email": "alice@example.com", "age": "30"},
        {"name": "B", "email": "invalid", "age": "17"},
        {},
    ]
    
    for user in test_users:
        result = validate_user(user)
        print(f"User: {user}")
        print(f"Result: {result}\n")



# PATTERN 3: Option Chaining for Nested Data

def nested_data_access():
    """
    Safe access to deeply nested data structures without null checks.
    """
    print("Nested Data Access")
    
    # Complex nested structure
    data = {
        "users": {
            "alice": {
                "profile": {
                    "address": {
                        "city": "New York"
                    }
                }
            },
            "bob": {
                "profile": {}  # Missing address
            }
        }
    }
    
    def get_user_city(data: dict, username: str):
        """Safely navigate nested structure"""
        return (
            maybe(data.get("users"))
            .flat_map(lambda users: maybe(users.get(username)))
            .flat_map(lambda user: maybe(user.get("profile")))
            .flat_map(lambda profile: maybe(profile.get("address")))
            .flat_map(lambda address: maybe(address.get("city")))
        )
    
    alice_city = get_user_city(data, "alice")
    bob_city = get_user_city(data, "bob")
    charlie_city = get_user_city(data, "charlie")
    
    print(f"Alice's city: {alice_city}")
    print(f"Bob's city: {bob_city}")
    print(f"Charlie's city: {charlie_city}")
    print()



# PATTERN 4: Parser Combinators (Simple)

def simple_parser_combinators():
    """
    Build parsers by combining simple parsers.
    """
    print("Simple Parser Combinators")
    
    def parse_prefix(prefix: str, text: str):
        """Parse a specific prefix"""
        if text.startswith(prefix):
            return Ok((prefix, text[len(prefix):]))
        return Err(f"Expected prefix '{prefix}'")
    
    def parse_digits(text: str):
        """Parse one or more digits"""
        digits = ""
        rest = text
        while rest and rest[0].isdigit():
            digits += rest[0]
            rest = rest[1:]
        
        if digits:
            return Ok((int(digits), rest))
        return Err("Expected digits")
    
    def parse_email_pattern(email: str):
        """Parse email into parts"""
        # Simple parser: username@domain
        parts = email.split("@")
        if len(parts) != 2:
            return Err("Invalid email format")
        
        username, domain = parts
        if not username or not domain:
            return Err("Missing username or domain")
        
        return Ok({"username": username, "domain": domain})
    
    # Test parsing
    email_tests = [
        "alice@example.com",
        "bob@",
        "@example.com",
        "invalid"
    ]
    
    for email in email_tests:
        result = parse_email_pattern(email)
        print(f"Parse {email!r:25} → {result}")
    print()



# PATTERN 5: Async-like Error Handling

def async_style_error_handling():
    """
    Chain operations that might fail, similar to async/await error handling.
    """
    print("Async-Style Error Handling")
    
    class Database:
        """Mock database"""
        def __init__(self):
            self.users = {
                1: {"name": "Alice", "balance": 100},
                2: {"name": "Bob", "balance": 50}
            }
        
        def get_user(self, user_id: int):
            user = self.users.get(user_id)
            if user:
                return Ok(user)
            return Err(f"User {user_id} not found")
        
        def update_balance(self, user_id: int, new_balance: float):
            if user_id in self.users:
                self.users[user_id]["balance"] = new_balance
                return Ok(self.users[user_id])
            return Err(f"User {user_id} not found")
    
    db = Database()
    
    def transfer_money(from_id: int, to_id: int, amount: float):
        """Transfer money between users"""
        # Get source user
        source_result = db.get_user(from_id)
        if source_result.is_err():
            return source_result
        
        source = source_result.get_or_else({})
        
        # Check balance
        if source["balance"] < amount:
            return Err("Insufficient funds")
        
        # Get destination user
        dest_result = db.get_user(to_id)
        if dest_result.is_err():
            return dest_result
        
        dest = dest_result.get_or_else({})
        
        # Update balances
        update1 = db.update_balance(from_id, source["balance"] - amount)
        if update1.is_err():
            return update1
        
        update2 = db.update_balance(to_id, dest["balance"] + amount)
        if update2.is_err():
            return update2
        
        return Ok({
            "from": from_id,
            "to": to_id,
            "amount": amount,
            "new_balances": {
                from_id: source["balance"] - amount,
                to_id: dest["balance"] + amount
            }
        })
    
    # Test transfers
    print("Initial state:", db.users)
    
    result1 = transfer_money(1, 2, 30)
    print(f"\nTransfer 30 from user 1 to 2: {result1}")
    print("After transfer:", db.users)
    
    result2 = transfer_money(2, 1, 200)
    print(f"\nTransfer 200 from user 2 to 1: {result2}")
    
    result3 = transfer_money(1, 999, 10)
    print(f"\nTransfer to non-existent user: {result3}")
    print()



# PATTERN 6: Memoization with Maybe

def memoization_with_maybe():
    """
    Use Maybe for caching with explicit cache misses.
    """
    print("Memoization with Maybe")
    
    class MemoCache:
        def __init__(self):
            self.cache: Dict[str, Any] = {}
            self.hits = 0
            self.misses = 0
        
        def get(self, key: str):
            if key in self.cache:
                self.hits += 1
                return Some(self.cache[key])
            self.misses += 1
            return nothing()
        
        def set(self, key: str, value: Any):
            self.cache[key] = value
        
        def stats(self):
            return f"Hits: {self.hits}, Misses: {self.misses}"
    
    cache = MemoCache()
    
    def expensive_computation(n: int) -> int:
        """Simulate expensive operation"""
        print(f"  Computing {n}...")
        return n ** 2
    
    def cached_computation(n: int) -> int:
        """Computation with caching"""
        key = f"square_{n}"
        
        # Try cache first
        cached = cache.get(key)
        if cached.is_some():
            print(f"  Cache hit for {n}")
            return cached.get_or_else(0)
        
        # Compute and cache
        result = expensive_computation(n)
        cache.set(key, result)
        return result
    
    # Test caching
    for num in [5, 10, 5, 15, 10, 5]:
        result = cached_computation(num)
        print(f"Result: {result}")
    
    print(f"\n{cache.stats()}")
    print()



# PATTERN 7: Builder Pattern with Validation

def builder_pattern_with_validation():
    """
    Use Result to build complex objects with validation at each step.
    """
    print("Builder Pattern with Validation")
    
    class Config:
        def __init__(self):
            self.host = None
            self.port = None
            self.timeout = None
            self.max_connections = None
        
        def __repr__(self):
            return (
                f"Config(host={self.host}, port={self.port}, "
                f"timeout={self.timeout}, max_connections={self.max_connections})"
            )
    
    class ConfigBuilder:
        def __init__(self):
            self.config = Config()
        
        def with_host(self, host: str):
            if not host or len(host) < 3:
                return Err("Invalid host")
            self.config.host = host
            return Ok(self)
        
        def with_port(self, port: int):
            if not (1 <= port <= 65535):
                return Err("Port must be between 1 and 65535")
            self.config.port = port
            return Ok(self)
        
        def with_timeout(self, timeout: int):
            if timeout <= 0:
                return Err("Timeout must be positive")
            self.config.timeout = timeout
            return Ok(self)
        
        def with_max_connections(self, max_conn: int):
            if max_conn <= 0:
                return Err("Max connections must be positive")
            self.config.max_connections = max_conn
            return Ok(self)
        
        def build(self):
            if not all([self.config.host, self.config.port, 
                       self.config.timeout, self.config.max_connections]):
                return Err("Missing required configuration")
            return Ok(self.config)
    
    # Build valid config
    result = (
        ConfigBuilder()
        .with_host("example.com")
        .flat_map(lambda b: b.with_port(8080))
        .flat_map(lambda b: b.with_timeout(30))
        .flat_map(lambda b: b.with_max_connections(100))
        .flat_map(lambda b: b.build())
    )
    
    print(f"Valid config: {result}")
    
    # Build invalid config
    result = (
        ConfigBuilder()
        .with_host("x")  # Too short
        .flat_map(lambda b: b.with_port(8080))
        .flat_map(lambda b: b.build())
    )
    
    print(f"Invalid config: {result}")
    print()



# PATTERN 8: Retry Logic with Result

def retry_with_result():
    """
    Implement retry logic using Result types.
    """
    print("Retry Logic with Result")
    
    class UnreliableService:
        def __init__(self):
            self.attempt = 0
        
        def call(self):
            self.attempt += 1
            if self.attempt < 3:
                return Err(f"Service unavailable (attempt {self.attempt})")
            return Ok("Success!")
    
    def retry(operation, max_attempts: int):
        """Retry an operation up to max_attempts times"""
        last_error = None
        
        for attempt in range(max_attempts):
            result = operation()
            if result.is_ok():
                return result
            last_error = result
        
        return last_error or Err("Max retries exceeded")
    
    service = UnreliableService()
    result = retry(service.call, max_attempts=5)
    
    print(f"Result after retries: {result}")
    print(f"Total attempts made: {service.attempt}")
    print()



# ALL

if __name__ == "__main__":
    railway_example()
    validation_accumulation()
    nested_data_access()
    simple_parser_combinators()
    async_style_error_handling()
    memoization_with_maybe()
    builder_pattern_with_validation()
    retry_with_result()
    
    print("\nAll advanced patterns completed!")
