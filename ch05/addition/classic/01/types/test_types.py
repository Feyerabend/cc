# Unit tests for VM implementation

from vm import VM

# Test basic arithmetic operations
def test_arithmetic_operations():
    vm = VM()

    # Test ADD operation
    vm.execute(['SET', 2, 'SET', 3, 'ADD'])
    assert vm.stack.pop() == 5, "ADD operation failed"

    # Test SUB operation
    vm.execute(['SET', 10, 'SET', 4, 'SUB'])
    assert vm.stack.pop() == 6, "SUB operation failed"

    # Test MUL operation
    vm.execute(['SET', 3, 'SET', 4, 'MUL'])
    assert vm.stack.pop() == 12, "MUL operation failed"

    # Test DIV operation
    vm.execute(['SET', 20, 'SET', 5, 'DIV'])
    assert vm.stack.pop() == 4, "DIV operation failed"

# Test bitwise operations
def test_bitwise_operations():
    vm = VM()

    # Test AND operation
    vm.execute(['SET', 6, 'SET', 3, 'AND'])
    assert vm.stack.pop() == 2, "AND operation failed"

    # Test OR operation
    vm.execute(['SET', 4, 'SET', 1, 'OR'])
    assert vm.stack.pop() == 5, "OR operation failed"

# Test logical operations
def test_logical_operations():
    vm = VM()

    # Test LOGICAL_AND operation
    vm.execute(['SET', 1, 'SET', 1, 'LOGICAL_AND'])
    assert vm.stack.pop() == 1, "AND operation failed"

    vm.execute(['SET', 1, 'SET', 0, 'LOGICAL_AND'])
    assert vm.stack.pop() == 0, "AND operation failed"

    vm.execute(['SET', 0, 'SET', 0, 'LOGICAL_AND'])
    assert vm.stack.pop() == 0, "AND operation failed"

    # Test LOGICAL_OR operation
    vm.execute(['SET', 1, 'SET', 1, 'LOGICAL_OR'])
    assert vm.stack.pop() == 1, "OR operation failed"

    vm.execute(['SET', 1, 'SET', 0, 'LOGICAL_OR'])
    assert vm.stack.pop() == 1, "OR operation failed"

    vm.execute(['SET', 0, 'SET', 0, 'LOGICAL_OR'])
    assert vm.stack.pop() == 0, "OR operation failed"

# Test comparison operations
def test_comparison_operations():
    vm = VM()

    # Test GT (greater than)
    vm.execute(['SET', 7, 'SET', 3, 'GT'])
    assert vm.stack.pop() == 1, "GT operation failed"

    # Test LT (less than)
    vm.execute(['SET', 2, 'SET', 5, 'LT'])
    assert vm.stack.pop() == 1, "LT operation failed"

    # Test EQ (equal)
    vm.execute(['SET', 4, 'SET', 4, 'EQ'])
    assert vm.stack.pop() == 1, "EQ operation failed"

# Test function definitions and calls
def test_function_calls():
    vm = VM()

    # Define a simple function
    vm.define_function('add_five', 1, [
        'LOAD', 'ARG1', 'SET', 5, 'ADD', 'RET'
    ])

    # Test function call
    vm.execute(['SET', 10, 'CALL', 'add_five', 1])
    assert vm.stack.pop() == 15, "Function call failed"

# Test closures
def test_closures():
    vm = VM()

    # Define an outer function that creates a closure
    vm.define_function('outer', 1, [
        'SET', 10, 'STORE', 'x',
        'LOAD', 'ARG1', 'STORE', 'y',
        'LOAD', 'x', 'LOAD', 'y', 'ADD', 'RET'
    ])

    # Execute the outer function
    vm.execute(['SET', 5, 'CALL', 'outer', 1])
    assert vm.stack.pop() == 15, "Closure creation or outer function failed"

# Test stack manipulation
def test_stack_operations():
    vm = VM()

    # Test DUP operation
    vm.execute(['SET', 42, 'DUP'])
    assert vm.stack.pop() == 42, "DUP operation failed"
    assert vm.stack.pop() == 42, "DUP operation failed"

    # Test POP operation
    vm.execute(['SET', 100, 'POP'])
    assert len(vm.stack) == 0, "POP operation failed"

# Test list operations
def test_list_operations():
    vm = VM()

    # Test LIST creation
    vm.execute(['SET', 1, 'SET', 2, 'SET', 3, 'LIST'])
    assert vm.stack.pop() == [1, 2, 3], "LIST operation failed"

    # Test CONS operation
    vm.execute(['SET', [2, 3], 'SET', 1, 'CONS'])
    assert vm.stack.pop() == [1, 2, 3], "CONS operation failed"

    # Test CAR operation
    vm.execute(['SET', [10, 20, 30], 'CAR'])
    assert vm.stack.pop() == 10, "CAR operation failed"

    # Test CDR operation
    vm.execute(['SET', [10, 20, 30], 'CDR'])
    assert vm.stack.pop() == [20, 30], "CDR operation failed"

if __name__ == "__main__":
    test_arithmetic_operations()
    test_bitwise_operations()
    test_logical_operations()
    test_comparison_operations()
    test_function_calls()
    test_closures()
    test_stack_operations()
    test_list_operations()

    print("All tests passed!")
