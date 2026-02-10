"""
Comprehensive Test Suite for Virtual Machine
Demonstrates TDD best practices
Run with: python test_vm.py
"""

from vm import (
    VirtualMachine, run_program,
    VMError, StackUnderflowError, InvalidRegisterError,
    DivisionByZeroError, InvalidJumpError, ReturnWithoutCallError
)


# TEST UTILITIES

class TestRunner:
    """Simple test runner to organize and run tests."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def run_test(self, test_func, test_name):
        """Run a single test and track results."""
        try:
            test_func()
            self.passed += 1
            print(f"  ✓ {test_name}")
        except AssertionError as e:
            self.failed += 1
            self.errors.append((test_name, str(e)))
            print(f"  ✗ {test_name}: {e}")
        except Exception as e:
            self.failed += 1
            self.errors.append((test_name, f"Error: {e}"))
            print(f"  ✗ {test_name}: Error: {e}")
    
    def run_test_class(self, test_class):
        """Run all test methods in a class."""
        print(f"\n{test_class.__name__}")
        instance = test_class()
        
        # Get all methods that start with 'test_'
        test_methods = [method for method in dir(instance) 
                       if method.startswith('test_') and callable(getattr(instance, method))]
        
        for method_name in test_methods:
            self.run_test(getattr(instance, method_name), method_name)
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Tests Run: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.errors:
            print(f"\n{'='*60}")
            print("FAILURES:")
            for test_name, error in self.errors:
                print(f"\n{test_name}:")
                print(f"  {error}")
        
        print(f"{'='*60}")
        return self.failed == 0


def assert_raises(exception_type, func):
    """Assert that a function raises a specific exception."""
    try:
        func()
        raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
    except exception_type:
        pass  # Expected exception was raised


# HELPER FUNCTIONS TO REPLACE FIXTURES

def get_fresh_vm():
    """Create a fresh VM instance."""
    return VirtualMachine()


def get_debug_vm():
    """Create a VM with debug logging enabled."""
    return VirtualMachine(debug=True)


def get_initialized_vm():
    """Create a VM with some pre-loaded values."""
    vm = VirtualMachine()
    vm.execute([
        ("MOV", "R0", 10),
        ("MOV", "R1", 20),
        ("MOV", "R2", 30),
    ])
    return vm


# DATA MOVEMENT TESTS

class TestDataMovement:
    """Test MOV, PUSH, POP instructions."""
    
    def test_mov_literal_to_register(self):
        """MOV should store literal value in register."""
        vm = get_fresh_vm()
        vm.execute([("MOV", "R0", 42)])
        assert vm.get_register("R0") == 42
    
    def test_mov_register_to_register(self):
        """MOV should copy value between registers."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 100),
            ("MOV", "R1", "R0")
        ])
        assert vm.get_register("R1") == 100
        assert vm.get_register("R0") == 100  # Source unchanged
    
    def test_mov_multiple_registers(self):
        """MOV can be chained."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 10),
            ("MOV", "R1", "R0"),
            ("MOV", "R2", "R1"),
        ])
        assert vm.get_register("R2") == 10
    
    def test_mov_overwrites_existing_value(self):
        """MOV should overwrite previous value."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 100),
            ("MOV", "R0", 200),
        ])
        assert vm.get_register("R0") == 200
    
    def test_mov_invalid_register_raises_error(self):
        """MOV to invalid register should raise error."""
        vm = get_fresh_vm()
        assert_raises(InvalidRegisterError, 
                     lambda: vm.execute([("MOV", "R99", 42)]))
    
    def test_push_literal(self):
        """PUSH should store literal on stack."""
        vm = get_fresh_vm()
        vm.execute([("PUSH", 42)])
        assert vm.get_stack() == [42]
    
    def test_push_register(self):
        """PUSH should store register value on stack."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 100),
            ("PUSH", "R0")
        ])
        assert vm.get_stack() == [100]
    
    def test_push_multiple_values(self):
        """PUSH should maintain LIFO order."""
        vm = get_fresh_vm()
        vm.execute([
            ("PUSH", 10),
            ("PUSH", 20),
            ("PUSH", 30)
        ])
        assert vm.get_stack() == [10, 20, 30]
    
    def test_pop_to_register(self):
        """POP should retrieve value from stack."""
        vm = get_fresh_vm()
        vm.execute([
            ("PUSH", 42),
            ("POP", "R0")
        ])
        assert vm.get_register("R0") == 42
        assert vm.get_stack() == []
    
    def test_pop_lifo_order(self):
        """POP should follow Last-In-First-Out."""
        vm = get_fresh_vm()
        vm.execute([
            ("PUSH", 10),
            ("PUSH", 20),
            ("PUSH", 30),
            ("POP", "R0"),
            ("POP", "R1"),
            ("POP", "R2")
        ])
        assert vm.get_register("R0") == 30  # Last in
        assert vm.get_register("R1") == 20
        assert vm.get_register("R2") == 10  # First in
    
    def test_pop_empty_stack_raises_error(self):
        """POP from empty stack should raise error."""
        vm = get_fresh_vm()
        assert_raises(StackUnderflowError, 
                     lambda: vm.execute([("POP", "R0")]))
    
    def test_push_pop_preserves_value(self):
        """PUSH then POP should preserve value."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 123),
            ("PUSH", "R0"),
            ("MOV", "R0", 0),     # Clear R0
            ("POP", "R0")         # Restore
        ])
        assert vm.get_register("R0") == 123


# ARITHMETIC TESTS

class TestArithmetic:
    """Test ADD, SUB, MUL, DIV, MOD instructions."""
    
    def test_add_literal(self):
        """ADD should add literal to register."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 10),
            ("ADD", "R0", 5)
        ])
        assert vm.get_register("R0") == 15
    
    def test_add_register(self):
        """ADD should add register to register."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 10),
            ("MOV", "R1", 20),
            ("ADD", "R0", "R1")
        ])
        assert vm.get_register("R0") == 30
        assert vm.get_register("R1") == 20  # Source unchanged
    
    def test_sub_literal(self):
        """SUB should subtract literal from register."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 20),
            ("SUB", "R0", 7)
        ])
        assert vm.get_register("R0") == 13
    
    def test_sub_register(self):
        """SUB should subtract register from register."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 50),
            ("MOV", "R1", 30),
            ("SUB", "R0", "R1")
        ])
        assert vm.get_register("R0") == 20
    
    def test_mul_literal(self):
        """MUL should multiply register by literal."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 7),
            ("MUL", "R0", 6)
        ])
        assert vm.get_register("R0") == 42
    
    def test_mul_register(self):
        """MUL should multiply register by register."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 4),
            ("MOV", "R1", 5),
            ("MUL", "R0", "R1")
        ])
        assert vm.get_register("R0") == 20
    
    def test_div_literal(self):
        """DIV should perform integer division."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 20),
            ("DIV", "R0", 3)
        ])
        assert vm.get_register("R0") == 6  # Integer division
    
    def test_div_register(self):
        """DIV should divide by register value."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 100),
            ("MOV", "R1", 4),
            ("DIV", "R0", "R1")
        ])
        assert vm.get_register("R0") == 25
    
    def test_div_by_zero_literal_raises_error(self):
        """DIV by zero should raise error."""
        vm = get_fresh_vm()
        assert_raises(DivisionByZeroError,
                     lambda: vm.execute([
                         ("MOV", "R0", 10),
                         ("DIV", "R0", 0)
                     ]))
    
    def test_div_by_zero_register_raises_error(self):
        """DIV by register containing zero should raise error."""
        vm = get_fresh_vm()
        assert_raises(DivisionByZeroError,
                     lambda: vm.execute([
                         ("MOV", "R0", 10),
                         ("MOV", "R1", 0),
                         ("DIV", "R0", "R1")
                     ]))
    
    def test_mod_literal(self):
        """MOD should compute modulo."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 17),
            ("MOD", "R0", 5)
        ])
        assert vm.get_register("R0") == 2
    
    def test_mod_register(self):
        """MOD should work with registers."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 23),
            ("MOV", "R1", 7),
            ("MOD", "R0", "R1")
        ])
        assert vm.get_register("R0") == 2
    
    def test_chained_arithmetic(self):
        """Arithmetic operations can be chained."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 10),
            ("ADD", "R0", 5),      # 15
            ("MUL", "R0", 2),      # 30
            ("SUB", "R0", 6),      # 24
            ("DIV", "R0", 4),      # 6
            ("MOD", "R0", 5),      # 1
        ])
        assert vm.get_register("R0") == 1


# BITWISE LOGIC TESTS

class TestBitwiseLogic:
    """Test AND, OR, XOR, NOT instructions."""
    
    def test_and_literal(self):
        """AND should perform bitwise AND."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 0b1100),
            ("AND", "R0", 0b1010)
        ])
        assert vm.get_register("R0") == 0b1000
    
    def test_and_register(self):
        """AND should work with registers."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 0b1111),
            ("MOV", "R1", 0b0101),
            ("AND", "R0", "R1")
        ])
        assert vm.get_register("R0") == 0b0101
    
    def test_or_literal(self):
        """OR should perform bitwise OR."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 0b1100),
            ("OR", "R0", 0b1010)
        ])
        assert vm.get_register("R0") == 0b1110
    
    def test_or_register(self):
        """OR should work with registers."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 0b1100),
            ("MOV", "R1", 0b0011),
            ("OR", "R0", "R1")
        ])
        assert vm.get_register("R0") == 0b1111
    
    def test_xor_literal(self):
        """XOR should perform bitwise XOR."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 0b1100),
            ("XOR", "R0", 0b1010)
        ])
        assert vm.get_register("R0") == 0b0110
    
    def test_xor_register(self):
        """XOR should work with registers."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 0b1111),
            ("MOV", "R1", 0b0101),
            ("XOR", "R0", "R1")
        ])
        assert vm.get_register("R0") == 0b1010
    
    def test_not_operation(self):
        """NOT should perform bitwise NOT."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 0),
            ("NOT", "R0")
        ])
        assert vm.get_register("R0") == -1  # Two's complement


# COMPARISON AND CONTROL FLOW TESTS

class TestComparisonAndControlFlow:
    """Test CMP, JMP, JMP_IF, CALL, RET, HALT instructions."""
    
    def test_cmp_sets_zero_flag(self):
        """CMP should set ZERO flag when values equal."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 42),
            ("CMP", "R0", 42)
        ])
        assert vm.status_flag == "ZERO"
    
    def test_cmp_sets_less_flag(self):
        """CMP should set LESS flag when first < second."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 10),
            ("CMP", "R0", 20)
        ])
        assert vm.status_flag == "LESS"
    
    def test_cmp_sets_greater_flag(self):
        """CMP should set GREATER flag when first > second."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 30),
            ("CMP", "R0", 20)
        ])
        assert vm.status_flag == "GREATER"
    
    def test_cmp_with_registers(self):
        """CMP should work with two registers."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 15),
            ("MOV", "R1", 15),
            ("CMP", "R0", "R1")
        ])
        assert vm.status_flag == "ZERO"
    
    def test_jmp_unconditional(self):
        """JMP should jump unconditionally."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 1),
            ("JMP", 3),
            ("MOV", "R0", 999),  # Skipped
            ("MOV", "R0", 2),
            ("HALT",)
        ])
        assert vm.get_register("R0") == 2
    
    def test_jmp_if_zero_when_true(self):
        """JMP_IF ZERO should jump when ZERO flag is set."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 1),
            ("CMP", "R0", 1),        # Sets ZERO
            ("JMP_IF", "ZERO", 5),
            ("MOV", "R0", 999),      # Skipped
            ("MOV", "R1", 999),      # Skipped (set R1 to detect skip)
            ("HALT",)                # Jump target
        ])
        assert vm.get_register("R0") == 1
        assert vm.get_register("R1") == 0  # R1 was never set, proving jump worked
    
    def test_jmp_if_zero_when_false(self):
        """JMP_IF ZERO should not jump when ZERO flag is clear."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 1),
            ("CMP", "R0", 2),        # Clears ZERO
            ("JMP_IF", "ZERO", 5),
            ("MOV", "R0", 3),
            ("HALT",)
        ])
        assert vm.get_register("R0") == 3
    
    def test_jmp_if_less(self):
        """JMP_IF LESS should jump when LESS flag is set."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 10),
            ("CMP", "R0", 20),       # Sets LESS
            ("JMP_IF", "LESS", 5),
            ("MOV", "R0", 999),      # Skipped
            ("MOV", "R1", 999),      # Skipped
            ("HALT",)
        ])
        assert vm.get_register("R0") == 10
        assert vm.get_register("R1") == 0  # Proves jump worked
    
    def test_jmp_if_greater(self):
        """JMP_IF GREATER should jump when GREATER flag is set."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 30),
            ("CMP", "R0", 20),       # Sets GREATER
            ("JMP_IF", "GREATER", 5),
            ("MOV", "R0", 999),      # Skipped
            ("MOV", "R1", 999),      # Skipped
            ("HALT",)
        ])
        assert vm.get_register("R0") == 30
        assert vm.get_register("R1") == 0  # Proves jump worked
    
    def test_simple_loop(self):
        """Loop using JMP should execute multiple times."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 5),
            ("CMP", "R0", 0),
            ("JMP_IF", "ZERO", 5),
            ("SUB", "R0", 1),
            ("JMP", 1),
            ("HALT",)
        ])
        assert vm.get_register("R0") == 0
    
    def test_call_and_return(self):
        """CALL should jump and RET should return."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 1),
            ("CALL", 4),         # Call function at line 4
            ("MOV", "R0", 3),    # After return
            ("HALT",),
            # Function
            ("MOV", "R0", 2),
            ("RET",)
        ])
        assert vm.get_register("R0") == 3
    
    def test_nested_calls(self):
        """Nested CALL/RET should work correctly."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 0),        # 0
            ("CALL", 3),             # 1: Call to line 3 (first function)
            ("HALT",),               # 2
            # First function starts at 3
            ("ADD", "R0", 1),        # 3: R0 = 1
            ("CALL", 7),             # 4: Nested call to line 7
            ("ADD", "R0", 1),        # 5: R0 = 3 (after nested returns)
            ("RET",),                # 6: Return to 2
            # Second function starts at 7
            ("ADD", "R0", 1),        # 7: R0 = 2
            ("RET",)                 # 8: Return to 5
        ])
        # Execution: 0 -> 1 -> 2 -> 3
        assert vm.get_register("R0") == 3
    
    def test_call_preserves_return_address(self):
        """Multiple CALLs should preserve return addresses."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R1", 1),
            ("CALL", 5),
            ("MOV", "R1", 2),
            ("HALT",),
            ("MOV", "R0", "R1"),
            ("RET",)
        ])
        assert vm.get_register("R1") == 2
    
    def test_return_without_call_raises_error(self):
        """RET without CALL should raise error."""
        vm = get_fresh_vm()
        assert_raises(ReturnWithoutCallError,
                     lambda: vm.execute([("RET",)]))
    
    def test_jump_out_of_bounds_raises_error(self):
        """Jump to invalid address should raise error."""
        vm = get_fresh_vm()
        assert_raises(InvalidJumpError,
                     lambda: vm.execute([("JMP", 999)]))
    
    def test_halt_stops_execution(self):
        """HALT should stop program execution."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 1),
            ("HALT",),
            ("MOV", "R0", 999)     # Never executed
        ])
        assert vm.get_register("R0") == 1
        assert vm.halted is True


# INTEGRATION TESTS - COMPLETE PROGRAMS

class TestCompletePrograms:
    """Test complete, realistic programs."""
    
    def test_factorial(self):
        """Calculate 5! = 120."""
        vm = get_fresh_vm()
        program = [
            ("MOV", "R0", 1),          # result = 1
            ("MOV", "R1", 5),          # n = 5
            # Loop
            ("CMP", "R1", 0),
            ("JMP_IF", "ZERO", 7),
            ("MUL", "R0", "R1"),
            ("SUB", "R1", 1),
            ("JMP", 2),
            # End
            ("HALT",)
        ]
        vm.execute(program)
        assert vm.get_register("R0") == 120
    
    def test_fibonacci(self):
        """Calculate 10th Fibonacci number."""
        vm = get_fresh_vm()
        program = [
            ("MOV", "R0", 0),          # 0: fib(n-2)
            ("MOV", "R1", 1),          # 1: fib(n-1)
            ("MOV", "R2", 9),          # 2: counter (9 iterations for fib(10))
            # Loop
            ("CMP", "R2", 0),          # 3
            ("JMP_IF", "ZERO", 10),    # 4: Jump to HALT at line 10
            ("MOV", "R3", "R1"),       # 5: temp = fib(n-1)
            ("ADD", "R1", "R0"),       # 6: fib(n-1) += fib(n-2)
            ("MOV", "R0", "R3"),       # 7: fib(n-2) = temp
            ("SUB", "R2", 1),          # 8
            ("JMP", 3),                # 9: Loop back
            # Result in R1
            ("HALT",)                  # 10
        ]
        vm.execute(program)
        assert vm.get_register("R1") == 55  # 10th Fibonacci
    
    def test_sum_of_squares(self):
        """Calculate sum of squares: 1² + 2² + 3² + 4² + 5² = 55."""
        vm = get_fresh_vm()
        program = [
            ("MOV", "R0", 5),          # n
            ("MOV", "R1", 0),          # sum
            # Loop
            ("CMP", "R0", 0),
            ("JMP_IF", "ZERO", 9),
            ("MOV", "R2", "R0"),       # temp = n
            ("MUL", "R2", "R0"),       # temp = n²
            ("ADD", "R1", "R2"),       # sum += n²
            ("SUB", "R0", 1),
            ("JMP", 2),
            # End
            ("HALT",)
        ]
        vm.execute(program)
        assert vm.get_register("R1") == 55
    
    def test_gcd_euclidean(self):
        """Calculate GCD(48, 18) = 6 using Euclidean algorithm."""
        vm = get_fresh_vm()
        program = [
            ("MOV", "R0", 48),         # a
            ("MOV", "R1", 18),         # b
            # Loop
            ("CMP", "R1", 0),
            ("JMP_IF", "ZERO", 9),
            ("MOV", "R2", "R0"),       # temp = a
            ("MOD", "R2", "R1"),       # temp = a % b
            ("MOV", "R0", "R1"),       # a = b
            ("MOV", "R1", "R2"),       # b = temp
            ("JMP", 2),
            # GCD in R0
            ("HALT",)
        ]
        vm.execute(program)
        assert vm.get_register("R0") == 6
    
    def test_recursive_power(self):
        """Calculate 2^8 = 256 using repeated multiplication."""
        vm = get_fresh_vm()
        program = [
            ("MOV", "R0", 1),          # result
            ("MOV", "R1", 2),          # base
            ("MOV", "R2", 8),          # exponent
            # Loop
            ("CMP", "R2", 0),
            ("JMP_IF", "ZERO", 8),
            ("MUL", "R0", "R1"),
            ("SUB", "R2", 1),
            ("JMP", 3),
            # End
            ("HALT",)
        ]
        vm.execute(program)
        assert vm.get_register("R0") == 256
    
    def test_nested_loops(self):
        """Test nested loops: 3 * 4 = 12."""
        vm = get_fresh_vm()
        program = [
            ("MOV", "R0", 3),          # Outer counter
            ("MOV", "R3", 0),          # Result
            # Outer loop
            ("CMP", "R0", 0),
            ("JMP_IF", "ZERO", 12),
            ("MOV", "R1", 4),          # Inner counter
            # Inner loop
            ("CMP", "R1", 0),
            ("JMP_IF", "ZERO", 10),
            ("ADD", "R3", 1),
            ("SUB", "R1", 1),
            ("JMP", 5),
            # End inner
            ("SUB", "R0", 1),
            ("JMP", 2),
            # End outer
            ("HALT",)
        ]
        vm.execute(program)
        assert vm.get_register("R3") == 12


# EDGE CASES AND ERROR HANDLING

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_all_registers_independent(self):
        """Each register should store independently."""
        vm = get_fresh_vm()
        for i in range(10):
            vm.execute([("MOV", f"R{i}", i * 10)])
        
        for i in range(10):
            assert vm.get_register(f"R{i}") == i * 10
    
    def test_large_numbers(self):
        """VM should handle large numbers."""
        vm = get_fresh_vm()
        large = 2**30
        vm.execute([
            ("MOV", "R0", large),
            ("ADD", "R0", 1)
        ])
        assert vm.get_register("R0") == large + 1
    
    def test_negative_numbers(self):
        """VM should handle negative numbers."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", -100),
            ("ADD", "R0", 50)
        ])
        assert vm.get_register("R0") == -50
    
    def test_deep_call_stack(self):
        """VM should handle deep function calls."""
        vm = get_fresh_vm()
        # Create a simpler chain: each function sets a register and calls the next
        program = [
            ("CALL", 2),             # 0: Call first function
            ("HALT",),               # 1
            # Function 0
            ("MOV", "R0", 0),        # 2
            ("CALL", 5),             # 3
            ("RET",),                # 4
            # Function 1
            ("MOV", "R1", 1),        # 5
            ("CALL", 8),             # 6
            ("RET",),                # 7
            # Function 2
            ("MOV", "R2", 2),        # 8
            ("CALL", 11),            # 9
            ("RET",),                # 10
            # Function 3
            ("MOV", "R3", 3),        # 11
            ("RET",)                 # 12
        ]
        
        vm.execute(program)
        # All functions should have executed
        assert vm.get_register("R0") == 0
        assert vm.get_register("R1") == 1
        assert vm.get_register("R2") == 2
        assert vm.get_register("R3") == 3
    
    def test_empty_program(self):
        """Executing empty program should work."""
        vm = get_fresh_vm()
        vm.execute([])
        assert not vm.halted


# DEBUGGING AND LOGGING TESTS

class TestDebugging:
    """Test debug features and logging."""
    
    def test_debug_mode_creates_log(self):
        """Debug mode should create execution log."""
        debug_vm = get_debug_vm()
        debug_vm.execute([
            ("MOV", "R0", 10),
            ("ADD", "R0", 5)
        ])
        log = debug_vm.get_execution_log()
        assert len(log) == 2
        assert log[0]["instruction"] == ("MOV", "R0", 10)
        assert log[1]["instruction"] == ("ADD", "R0", 5)
    
    def test_execution_stats(self):
        """VM should track execution statistics."""
        vm = get_fresh_vm()
        vm.execute([
            ("MOV", "R0", 1),
            ("ADD", "R0", 1),
            ("PUSH", "R0"),
            ("HALT",)
        ])
        stats = vm.get_stats()
        assert stats["instruction_count"] == 4
        assert stats["stack_size"] == 1
        assert stats["halted"] is True


# PERFORMANCE TESTS

class TestPerformance:
    """Test VM performance with larger programs."""
    
    def test_large_loop_performance(self):
        """VM should handle large iteration counts."""
        vm = get_fresh_vm()
        program = [
            ("MOV", "R0", 10000),
            ("CMP", "R0", 0),
            ("JMP_IF", "ZERO", 5),
            ("SUB", "R0", 1),
            ("JMP", 1),
            ("HALT",)
        ]
        vm.execute(program)
        assert vm.get_register("R0") == 0
        # Should complete without timeout
    
    def test_very_large_computation(self):
        """Test with computationally intensive program."""
        vm = get_fresh_vm()
        # Calculate sum of 1 to 1000
        program = [
            ("MOV", "R0", 1000),       # counter
            ("MOV", "R1", 0),          # sum
            ("CMP", "R0", 0),
            ("JMP_IF", "ZERO", 7),
            ("ADD", "R1", "R0"),
            ("SUB", "R0", 1),
            ("JMP", 2),
            ("HALT",)
        ]
        vm.execute(program)
        assert vm.get_register("R1") == 500500  # Sum of 1 to 1000


# MAIN TEST RUNNER

def main():
    """Run all tests."""
    runner = TestRunner()
    
    # Run all test classes
    test_classes = [
        TestDataMovement,
        TestArithmetic,
        TestBitwiseLogic,
        TestComparisonAndControlFlow,
        TestCompletePrograms,
        TestEdgeCases,
        TestDebugging,
        TestPerformance,
    ]
    
    for test_class in test_classes:
        runner.run_test_class(test_class)
    
    # Print summary and return exit code
    success = runner.print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
