#!/usr/bin/env python3
"""
Comprehensive Test Suite for Parallel K Interpreter

Tests both correctness and parallel execution behavior.
"""

import time
import sys
from k_interpreter_parallel import (
    evaluate_expression,
    register_standard_operations,
    global_variables,
    ParallelConfig,
    KError
)


def run_test(description, expression, expected=None, should_fail=False):
    """Run a single test and report results."""
    try:
        result = evaluate_expression(expression)
        
        if should_fail:
            print(f"✗ {description}")
            print(f"  Expression: {expression}")
            print(f"  Expected: Error, but got: {result}")
            print()
            return False
        
        if expected is None or result == expected:
            print(f"✓ {description}")
            if expected is not None:
                print(f"  Result: {result}")
            return True
        else:
            print(f"✗ {description}")
            print(f"  Expression: {expression}")
            print(f"  Result: {result}")
            print(f"  Expected: {expected}")
            print()
            return False
            
    except KError as e:
        if should_fail:
            print(f"✓ {description}")
            print(f"  Error (expected): {e}")
            return True
        else:
            print(f"✗ {description}")
            print(f"  Expression: {expression}")
            print(f"  Error: {e}")
            print()
            return False


def section(title):
    """Print a section header."""
    print("=" * 70)
    print(f" {title}")
    print("=" * 70)
    print()


def test_basic_operations():
    """Test basic operations that should work in both serial and parallel."""
    section("Basic Operations (Serial)")
    
    tests_passed = 0
    tests_total = 0
    
    tests = [
        ("Addition", [3, "+", 4], 7),
        ("Subtraction", [10, "-", 3], 7),
        ("Multiplication", [6, "*", 7], 42),
        ("Vector addition", [[1, 2, 3], "+", 10], [11, 12, 13]),
        ("Boolean negation", ["-", [True, False, True]], [False, True, False]),
        ("Boolean OR", [[True, False], "+", [False, True]], [True, True]),
        ("Boolean AND", [[True, True, False], "*", [True, False, True]], [True, False, False]),
    ]
    
    for desc, expr, expected in tests:
        tests_total += 1
        if run_test(desc, expr, expected):
            tests_passed += 1
    
    print(f"Passed: {tests_passed}/{tests_total}\n")
    return tests_passed, tests_total


def test_parallel_operations():
    """Test parallel execution with large arrays."""
    section("Parallel Operations (Large Arrays)")
    
    tests_passed = 0
    tests_total = 0
    
    # Enable parallel with low threshold for testing
    ParallelConfig.enable()
    ParallelConfig.set_threshold(100)
    
    # Create large arrays
    size = 10000
    
    print(f"Testing with arrays of size {size}")
    print(f"Parallel threshold: {ParallelConfig.threshold}")
    print(f"Number of workers: {ParallelConfig.num_workers}")
    print()
    
    # Test 1: Large array sum
    tests_total += 1
    print("Test: Sum of large array")
    large_array = list(range(size))
    start = time.time()
    result = evaluate_expression(["+", large_array])
    elapsed = time.time() - start
    expected = sum(range(size))
    if result == expected:
        print(f"✓ Parallel sum correct: {result} (took {elapsed:.4f}s)")
        tests_passed += 1
    else:
        print(f"✗ Parallel sum incorrect: {result} != {expected}")
    print()
    
    # Test 2: Large array negation
    tests_total += 1
    print("Test: Negate large array")
    start = time.time()
    result = evaluate_expression(["-", large_array[:1000]])
    elapsed = time.time() - start
    expected = [-x for x in range(1000)]
    if result == expected:
        print(f"✓ Parallel negation correct (took {elapsed:.4f}s)")
        tests_passed += 1
    else:
        print(f"✗ Parallel negation incorrect")
    print()
    
    # Test 3: Large vector addition
    tests_total += 1
    print("Test: Large vector addition")
    vec1 = list(range(1000))
    vec2 = list(range(1000, 2000))
    start = time.time()
    result = evaluate_expression([vec1, "+", vec2])
    elapsed = time.time() - start
    expected = [a + b for a, b in zip(vec1, vec2)]
    if result == expected:
        print(f"✓ Parallel vector addition correct (took {elapsed:.4f}s)")
        tests_passed += 1
    else:
        print(f"✗ Parallel vector addition incorrect")
    print()
    
    # Test 4: Minimum of large array
    tests_total += 1
    print("Test: Minimum of large array")
    large_array_shuffled = [x * 7 % 10000 for x in range(size)]
    start = time.time()
    result = evaluate_expression(["&", large_array_shuffled])
    elapsed = time.time() - start
    expected = min(large_array_shuffled)
    if result == expected:
        print(f"✓ Parallel minimum correct: {result} (took {elapsed:.4f}s)")
        tests_passed += 1
    else:
        print(f"✗ Parallel minimum incorrect: {result} != {expected}")
    print()
    
    # Test 5: Maximum of large array
    tests_total += 1
    print("Test: Maximum of large array")
    start = time.time()
    result = evaluate_expression(["*", large_array_shuffled])
    elapsed = time.time() - start
    expected = max(large_array_shuffled)
    if result == expected:
        print(f"✓ Parallel maximum correct: {result} (took {elapsed:.4f}s)")
        tests_passed += 1
    else:
        print(f"✗ Parallel maximum incorrect: {result} != {expected}")
    print()
    
    print(f"Passed: {tests_passed}/{tests_total}\n")
    return tests_passed, tests_total


def test_serial_vs_parallel():
    """Compare serial and parallel results for correctness."""
    section("Serial vs Parallel Correctness")
    
    tests_passed = 0
    tests_total = 0
    
    size = 5000
    test_array = list(range(size))
    
    tests = [
        ("Sum", ["+", test_array]),
        ("Min", ["&", test_array]),
        ("Max", ["*", test_array]),
        ("Average", ["%", test_array]),
        ("Negate", ["-", test_array[:500]]),
    ]
    
    for desc, expr in tests:
        tests_total += 1
        
        # Serial result
        ParallelConfig.disable()
        serial_result = evaluate_expression(expr)
        
        # Parallel result
        ParallelConfig.enable()
        ParallelConfig.set_threshold(100)
        parallel_result = evaluate_expression(expr)
        
        if serial_result == parallel_result:
            print(f"✓ {desc}: Serial and parallel match")
            tests_passed += 1
        else:
            print(f"✗ {desc}: Serial != Parallel")
            print(f"  Serial: {serial_result}")
            print(f"  Parallel: {parallel_result}")
        print()
    
    print(f"Passed: {tests_passed}/{tests_total}\n")
    return tests_passed, tests_total


def test_nested_structures():
    """Test nested lists and complex structures."""
    section("Nested Structures")
    
    tests_passed = 0
    tests_total = 0
    
    tests = [
        ("Nested list", [[1, 2], [3, 4], [5, 6]], [[1, 2], [3, 4], [5, 6]]),
        ("Flatten", [";", [[1, 2], [3, 4], [5, 6]]], [1, 2, 3, 4, 5, 6]),
        ("Transpose", [".", [[1, 2, 3], [4, 5, 6]]], [[1, 4], [2, 5], [3, 6]]),
        ("Mixed types", [1, 3.14, '"hello"', True], [1, 3.14, "hello", True]),
    ]
    
    for desc, expr, expected in tests:
        tests_total += 1
        if run_test(desc, expr, expected):
            tests_passed += 1
    
    print(f"Passed: {tests_passed}/{tests_total}\n")
    return tests_passed, tests_total


def test_string_operations():
    """Test string operations."""
    section("String Operations")
    
    tests_passed = 0
    tests_total = 0
    
    tests = [
        ("String concat", ['"hello"', "+", '"world"'], "helloworld"),
        ("String reverse", ["|", '"hello"'], "olleh"),
        ("String length", ["#", '"hello"'], 5),
        ("String index", ['"hello"', "@", 1], "e"),
        ("String multi-index", ['"hello"', "@", [0, 4, 1, 3]], "hoel"),
    ]
    
    for desc, expr, expected in tests:
        tests_total += 1
        if run_test(desc, expr, expected):
            tests_passed += 1
    
    print(f"Passed: {tests_passed}/{tests_total}\n")
    return tests_passed, tests_total


def test_dictionary_operations():
    """Test dictionary operations."""
    section("Dictionary Operations")
    
    tests_passed = 0
    tests_total = 0
    
    tests = [
        ("Create dict", '["a":1;"b":2;"c":3]', {"a": 1, "b": 2, "c": 3}),
        ("Dict lookup", ['["x":10;"y":20]', "$", '"x"'], 10),
        ("Dict multi-lookup", ['["x":10;"y":20;"z":30]', "$", ['"x"', '"z"']], [10, 30]),
    ]
    
    for desc, expr, expected in tests:
        tests_total += 1
        if run_test(desc, expr, expected):
            tests_passed += 1
    
    print(f"Passed: {tests_passed}/{tests_total}\n")
    return tests_passed, tests_total


def test_edge_cases():
    """Test edge cases and error conditions."""
    section("Edge Cases and Error Handling")
    
    tests_passed = 0
    tests_total = 0
    
    # Empty arrays
    tests_total += 1
    if run_test("Empty list sum", ["+", []], 0):
        tests_passed += 1
    
    tests_total += 1
    if run_test("Empty list min", ["&", []], None, should_fail=True):
        tests_passed += 1
    
    # Division by zero
    tests_total += 1
    if run_test("Division by zero", [5, "%", 0], None, should_fail=True):
        tests_passed += 1
    
    # Type errors
    tests_total += 1
    if run_test("Add string to number", ['"hello"', "+", 5], None, should_fail=True):
        tests_passed += 1
    
    print(f"Passed: {tests_passed}/{tests_total}\n")
    return tests_passed, tests_total


def test_performance():
    """Test performance characteristics of parallel execution."""
    section("Performance Testing")
    
    print("Testing performance with different array sizes...\n")
    
    sizes = [100, 1000, 10000, 100000]
    
    for size in sizes:
        print(f"Array size: {size:,}")
        test_array = list(range(size))
        
        # Serial
        ParallelConfig.disable()
        start = time.time()
        result_serial = evaluate_expression(["+", test_array])
        time_serial = time.time() - start
        
        # Parallel
        ParallelConfig.enable()
        ParallelConfig.set_threshold(1000)
        start = time.time()
        result_parallel = evaluate_expression(["+", test_array])
        time_parallel = time.time() - start
        
        speedup = time_serial / time_parallel if time_parallel > 0 else 0
        
        print(f"  Serial:   {time_serial:.6f}s")
        print(f"  Parallel: {time_parallel:.6f}s")
        print(f"  Speedup:  {speedup:.2f}x")
        print(f"  Correct:  {result_serial == result_parallel}")
        print()


def main():
    """Run all tests."""
    print("K Interpreter (Parallel Edition) Test Suite")
    print("=" * 70)
    print()
    
    # Initialize
    register_standard_operations()
    global_variables.clear()
    
    total_passed = 0
    total_tests = 0
    
    # Run test suites
    passed, total = test_basic_operations()
    total_passed += passed
    total_tests += total
    
    passed, total = test_nested_structures()
    total_passed += passed
    total_tests += total
    
    passed, total = test_string_operations()
    total_passed += passed
    total_tests += total
    
    passed, total = test_dictionary_operations()
    total_passed += passed
    total_tests += total
    
    passed, total = test_edge_cases()
    total_passed += passed
    total_tests += total
    
    passed, total = test_parallel_operations()
    total_passed += passed
    total_tests += total
    
    passed, total = test_serial_vs_parallel()
    total_passed += passed
    total_tests += total
    
    # Performance tests (informational)
    test_performance()
    
    # Summary
    section("Test Summary")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print(f"Success Rate: {100 * total_passed / total_tests:.1f}%")
    print()
    
    if total_passed == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
