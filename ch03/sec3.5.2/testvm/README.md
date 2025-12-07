
## Test VM Engine

The Test VM Engine is a comprehensive virtual machine designed specifically for
test execution with advanced features, error handling, and extensible architecture.
It provides a stack-based execution model with built-in assertion capabilities,
making it ideal for automated testing scenarios.


### Features
- *Stack-based execution model* with comprehensive instruction set
- *Built-in assertion framework* with multiple assertion types
- *Extensible function system* for custom operations
- *Comprehensive error handling* with line numbers and stack traces
- *Test suite management* with tagging, filtering, and reporting
- *Timeout management* and execution control
- *State snapshots* for debugging and analysis
- *Variable interpolation* in messages and logs

## Architecture

### Core Components

```
 ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
 │   TestSuite     │───▶│     TestVM      │───▶│   Instruction   │
 │                 │    │                 │    │                 │
 │ - Test Cases    │    │ - Stack         │    │ - Opcode        │
 │ - Execution     │    │ - Variables     │    │ - Arguments     │
 │ - Reporting     │    │ - Functions     │    │ - Line Number   │
 └─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │     Value       │
                        │                 │
                        │ - Type          │
                        │ - Data          │
                        │ - Metadata      │
                        └─────────────────┘
```

### Execution Flow

1. *Parse* - Source code is tokenised and converted to instructions
2. *Label Collection* - Jump labels are identified and mapped
3. *Execute* - Instructions are executed sequentially with stack operations
4. *Assert* - Test assertions are evaluated and tracked
5. *Report* - Results are collected and formatted for output


### Basic Usage

```python
from test_vm_engine import EnhancedTestVM, TestSuite

# Create a VM instance
vm = EnhancedTestVM(debug=True)

# Simple program execution
program = """
    LOAD 10
    LOAD 5
    CALL add
    ASSERT_EQ result 15
    PASS
"""

result = vm.execute_program(program)
print(f"Test {'PASSED' if result.passed else 'FAILED'}")
```

### Using Test Suites

```python
# Create a test suite
suite = TestSuite("My Test Suite")

# Add test cases
suite.add_test(
    name="Addition Test",
    program="""
        LOAD 2
        LOAD 3
        CALL add
        ASSERT_EQ result 5
        PASS
    """,
    tags=["arithmetic", "basic"]
)

# Run tests
results = suite.run_all_tests()
print(suite.generate_report(results))
```

### Instructions

#### Stack Operations

| Instruction | Arguments | Description |
|-------------|-----------|-------------|
| `LOAD` | `<value>` | Push value onto stack |
| `LOAD_VAR` | `<name>` | Load variable value onto stack |
| `STORE_VAR` | `<name>` | Store top stack value in variable |
| `DUP` | | Duplicate top stack value |
| `SWAP` | | Swap top two stack values |
| `CLEAR_STACK` | | Clear the entire stack |

#### Function Calls

| Instruction | Arguments | Description |
|-------------|-----------|-------------|
| `CALL` | `<function_name>` | Call built-in or custom function |

#### Control Flow

| Instruction | Arguments | Description |
|-------------|-----------|-------------|
| `JUMP` | `<label>` | Unconditional jump to label |
| `JUMP_IF_TRUE` | `<var>` `<label>` | Jump if variable is true |
| `JUMP_IF_FALSE` | `<var>` `<label>` | Jump if variable is false |
| `JUMP_IF_FAIL` | `<label>` | Jump if last assertion failed |
| `LABEL` | `<name>` | Define a jump label |

#### Assertions

| Instruction | Arguments | Description |
|-------------|-----------|-------------|
| `ASSERT_EQ` | `<var>` `<expected>` | Assert variable equals expected value |
| `ASSERT_NE` | `<var>` `<unexpected>` | Assert variable not equals value |
| `ASSERT_TRUE` | `<var>` | Assert variable is true |
| `ASSERT_FALSE` | `<var>` | Assert variable is false |
| `ASSERT_CONTAINS` | `<var>` `<substring>` | Assert string contains substring |
| `ASSERT_MATCHES` | `<var>` `<regex>` | Assert string matches regex pattern |

#### Test Control

| Instruction | Arguments | Description |
|-------------|-----------|-------------|
| `PASS` | | Mark test as passed |
| `FAIL` | `<message>` | Mark test as failed with message |
| `EXIT` | | Stop execution immediately |

#### Utility

| Instruction | Arguments | Description |
|-------------|-----------|-------------|
| `LOG` | `<message>` | Add message to execution log |
| `PRINT` | `<message>` | Print message to stdout |
| `SLEEP` | `<seconds>` | Pause execution (max 5 seconds) |
| `NOP` | | No operation (placeholder) |
| `CLEAR_VARS` | | Clear all variables |
| `CLEAR_ALL` | | Clear stack and variables |



### Built-in Functions

#### Mathematical Operations

| Function | Arguments | Return Type | Description |
|----------|-----------|-------------|-------------|
| `add` | `int, int` | `int` | Addition |
| `subtract` | `int, int` | `int` | Subtraction |
| `multiply` | `int, int` | `int` | Multiplication |
| `divide` | `int, int` | `float` | Division (returns inf for div by 0) |
| `modulo` | `int, int` | `int` | Modulo operation |
| `power` | `int, int` | `int` | Exponentiation |

#### String Operations

| Function | Arguments | Return Type | Description |
|----------|-----------|-------------|-------------|
| `concat` | `any, any` | `string` | String concatenation |
| `length` | `any` | `int` | Length of string representation |
| `substring` | `string, int, int` | `string` | Extract substring |
| `uppercase` | `string` | `string` | Convert to uppercase |
| `lowercase` | `string` | `string` | Convert to lowercase |
| `trim` | `string` | `string` | Remove whitespace |

#### Comparison Operations

| Function | Arguments | Return Type | Description |
|----------|-----------|-------------|-------------|
| `equals` | `any, any` | `bool` | Equality comparison |
| `not_equals` | `any, any` | `bool` | Inequality comparison |
| `greater_than` | `any, any` | `bool` | Greater than comparison |
| `less_than` | `any, any` | `bool` | Less than comparison |
| `greater_equal` | `any, any` | `bool` | Greater or equal comparison |
| `less_equal` | `any, any` | `bool` | Less or equal comparison |

#### Logical Operations

| Function | Arguments | Return Type | Description |
|----------|-----------|-------------|-------------|
| `and` | `any, any` | `bool` | Logical AND |
| `or` | `any, any` | `bool` | Logical OR |
| `not` | `any` | `bool` | Logical NOT |

#### List Operations

| Function | Arguments | Return Type | Description |
|----------|-----------|-------------|-------------|
| `list_create` | | `list` | Create empty list |
| `list_append` | `list, any` | `list` | Append item to list |
| `list_get` | `list, int` | `any` | Get item by index |
| `list_size` | `list` | `int` | Get list size |

#### Type Operations

| Function | Arguments | Return Type | Description |
|----------|-----------|-------------|-------------|
| `to_string` | `any` | `string` | Convert to string |
| `to_int` | `any` | `int` | Convert to integer |
| `to_float` | `any` | `float` | Convert to float |
| `typeof` | `any` | `string` | Get type name |


### Value Types

The VM supports the following value types:

| Type | Description | Example |
|------|-------------|---------|
| `INT` | Integer numbers | `42`, `-10` |
| `FLOAT` | Floating-point numbers | `3.14`, `-2.5` |
| `STRING` | Text strings | `"Hello World"` |
| `BOOL` | Boolean values | `true`, `false` |
| `LIST` | Arrays of values | `[1, 2, 3]` |
| `DICT` | Key-value pairs | `{"key": "value"}` |
| `NULL` | Null/empty value | `null` |
| `RESULT` | Function result | (internal) |

#### Type Conversion Rules

- *To Boolean*: Numbers convert to false if zero, strings if empty, lists if empty, null always false
- *To String*: All types can be converted to string representation
- *To Number*: Strings are parsed, booleans become 0/1, others may raise errors

### Test Case Management

#### TestCase Structure

```python
@dataclass
class TestCase:
    name: str                    # Test case name
    program: str                 # Main test program
    expected_result: str = None  # Expected result value
    timeout: float = 10.0        # Execution timeout in seconds
    setup: str = None           # Setup code (optional)
    teardown: str = None        # Cleanup code (optional)
    tags: List[str] = []        # Tags for filtering
```

#### Creating Test Cases

```python
# Direct instantiation
test = TestCase(
    name="String Length Test",
    program="""
        LOAD "Hello"
        CALL length
        ASSERT_EQ result 5
        PASS
    """,
    tags=["string", "basic"]
)

# Using TestSuite convenience method
suite.add_test(
    name="Math Test",
    program="LOAD 2; LOAD 3; CALL multiply; ASSERT_EQ result 6; PASS",
    expected_result="6",
    timeout=5.0,
    tags=["math"]
)
```

#### Setup and Teardown

```python
suite.add_test(
    name="Database Test",
    setup="""
        # Initialize test data
        LOAD "test_db"
        STORE_VAR db_name
    """,
    program="""
        # Main test logic
        LOAD_VAR db_name
        CALL length
        ASSERT_EQ result 7
        PASS
    """,
    teardown="""
        # Cleanup
        CLEAR_VARS
    """
)
```

### Advanced Features

#### Variable Interpolation

Messages can include variable values using `{variable_name}` syntax:

```
STORE_VAR username "Alice"
LOG "Hello {username}!"
# Outputs: Hello Alice!
```

#### Custom Functions

```python
class CustomFunction(Function):
    def __call__(self, *args: Value) -> Value:
        # Custom logic here
        return Value(ValueType.STRING, "custom result")
    
    @property
    def arity(self) -> int:
        return 1
    
    @property
    def name(self) -> str:
        return "custom_func"

# Register with VM
vm.register_custom_function("custom_func", CustomFunction())
```

#### State Snapshots

```python
# Save current state
snapshot = vm.get_state_snapshot()

# Execute some operations
vm.execute_program("LOAD 42; STORE_VAR test")

# Restore previous state
vm.load_state_snapshot(snapshot)
```

#### Error Handling

The VM provides comprehensive error reporting:

```python
try:
    result = vm.execute_program(faulty_program)
except TestVMError as e:
    print(f"VM Error at line {e.line_number}: {e}")
    if e.instruction:
        print(f"Failed instruction: {e.instruction}")
```


### Examples

#### Complete Test Suite Example

```python
def create_comprehensive_test_suite():
    suite = TestSuite("Comprehensive Tests")
    
    # Math operations test
    suite.add_test(
        name="Mathematical Operations",
        program="""
            # Test addition
            LOAD 10
            LOAD 20
            CALL add
            ASSERT_EQ result 30
            
            # Test multiplication
            LOAD 5
            LOAD 6
            CALL multiply
            ASSERT_EQ result 30
            
            # Test division
            LOAD 15
            LOAD 3
            CALL divide
            ASSERT_EQ result 5.0
            
            PASS
        """,
        tags=["math", "comprehensive"]
    )
    
    # String processing test
    suite.add_test(
        name="String Processing",
        setup="""
            LOAD "  Hello World  "
            STORE_VAR raw_string
        """,
        program="""
            # Test trim and case operations
            LOAD_VAR raw_string
            CALL trim
            STORE_VAR clean_string
            
            LOAD_VAR clean_string
            CALL uppercase
            ASSERT_EQ result "HELLO WORLD"
            
            # Test substring extraction
            LOAD_VAR clean_string
            LOAD 0
            LOAD 5
            CALL substring
            ASSERT_EQ result "Hello"
            
            PASS
        """,
        tags=["string", "processing"]
    )
    
    # Conditional logic test
    suite.add_test(
        name="Conditional Logic Flow",
        program="""
            LOAD 10
            LOAD 5
            CALL greater_than
            STORE_VAR is_greater
            
            # Test conditional jump
            JUMP_IF_FALSE is_greater fail_case
            
            # Success path
            LOG "10 is greater than 5"
            JUMP end
            
            LABEL fail_case
            FAIL "Logic error: 10 should be greater than 5"
            
            LABEL end
            ASSERT_TRUE is_greater
            PASS
        """,
        tags=["logic", "control_flow"]
    )
    
    # List operations test
    suite.add_test(
        name="List Operations",
        program="""
            # Create and populate list
            CALL list_create
            STORE_VAR numbers
            
            LOAD_VAR numbers
            LOAD 1
            CALL list_append
            STORE_VAR numbers
            
            LOAD_VAR numbers
            LOAD 2
            CALL list_append
            STORE_VAR numbers
            
            LOAD_VAR numbers
            LOAD 3
            CALL list_append
            STORE_VAR numbers
            
            # Test list operations
            LOAD_VAR numbers
            CALL list_size
            ASSERT_EQ result 3
            
            LOAD_VAR numbers
            LOAD 0
            CALL list_get
            ASSERT_EQ result 1
            
            LOAD_VAR numbers
            LOAD 2
            CALL list_get
            ASSERT_EQ result 3
            
            PASS
        """,
        tags=["collections", "lists"]
    )
    
    return suite

# Run the comprehensive test suite
if __name__ == "__main__":
    suite = create_comprehensive_test_suite()
    results = suite.run_all_tests()
    
    print(suite.generate_report(results))
    
    # Run only math tests
    math_results = suite.run_all_tests(filter_tags=["math"])
    print("\nMath Tests Only:")
    print(suite.generate_report(math_results))
```


#### Error Handling Example

```python
def test_error_scenarios():
    vm = EnhancedTestVM(debug=True)
    
    # Test division by zero handling
    result = vm.execute_program("""
        LOAD 10
        LOAD 0
        CALL divide
        
        # Check if result is infinity
        LOAD_VAR result
        CALL to_string
        ASSERT_CONTAINS result "inf"
        PASS
    """)
    
    print(f"Division by zero test: {'PASSED' if result.passed else 'FAILED'}")
    
    # Test invalid function call
    result = vm.execute_program("""
        CALL nonexistent_function
        PASS
    """)
    
    print(f"Invalid function test: {'FAILED' if result.failed else 'UNEXPECTED'}")
    print(f"Error: {result.error_message}")
```


### API Reference

#### EnhancedTestVM Class

__Constructor__
```python
EnhancedTestVM(debug: bool = False)
```

__Core Methods__
- `execute_program(source: str, timeout: float = 30.0) -> TestResult`
- `execute_test_case(test_case: TestCase) -> TestResult`
- `execute_test_suite(test_cases: List[TestCase]) -> List[TestResult]`
- `register_custom_function(name: str, func: Function)`
- `reset()` - Reset VM state
- `get_state_snapshot() -> Dict[str, Any]`
- `load_state_snapshot(snapshot: Dict[str, Any])`

#### TestSuite Class

__Constructor__
```python
TestSuite(name: str = "Default Test Suite")
```

__Methods__
- `add_test_case(test_case: TestCase)`
- `add_test(name, program, expected_result=None, timeout=10.0, setup=None, teardown=None, tags=None)`
- `run_all_tests(filter_tags: Optional[List[str]] = None) -> List[TestResult]`
- `run_single_test(test_name: str) -> Optional[TestResult]`
- `generate_report(results: List[TestResult]) -> str`


#### TestResult Class

```python
@dataclass
class TestResult:
    name: str
    passed: bool
    failed: bool
    execution_time: float
    logs: List[str]
    error_message: str = ""
    stack_trace: str = ""
    assertions_count: int = 0
    assertions_passed: int = 0
```


### Best Practices

#### Writing Effective Tests

1. *Use Descriptive Names*: Give test cases clear, descriptive names that explain what is being tested.

2. *Keep Tests Focused*: Each test should verify a single aspect or functionality.

3. *Use Setup/Teardown*: Utilise setup and teardown for initialisation and cleanup.

4. *Tag Appropriately*: Use tags to organise tests by functionality, complexity, or execution time.

5. *Handle Edge Cases*: Include tests for boundary conditions and error scenarios.


#### Performance Optimisation

1. *Minimise Stack Operations*: Reduce unnecessary stack pushes/pops.

2. *Reuse Variables*: Store frequently used values in variables.

3. *Use Appropriate Timeouts*: Set realistic timeouts based on test complexity.

4. *Batch Related Tests*: Group related tests to benefit from shared setup.

#### Error Handling

1. *Validate Inputs*: Always validate input parameters and handle edge cases.

2. *Use Specific Assertions*: Choose the most specific assertion type for better error messages.

3. *Include Context*: Add logging and messages to provide context for failures.

4. *Test Error Paths*: Include tests that verify error handling behaviour.

#### Code Organisation

1. *Separate Test Logic*: Keep test setup, execution, and verification separate.

2. *Use Constants*: Define reusable values as constants or variables.

3. *Comment Complex Logic*: Add comments for complex test scenarios.

4. *Version Test Data*: Keep test data versioned and documented.

