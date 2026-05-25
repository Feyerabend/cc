import time
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Optional, Dict, Iterator
import random


@dataclass
class ShrinkResult:
    """Results from the shrinking process"""
    minimal_case: Any
    iterations: int
    time_spent: float
    reduction_ratio: float


@dataclass
class TestResult:
    """Comprehensive test execution results"""
    passed: bool
    examples_tried: int
    shrink_iterations: int
    execution_time: float
    minimal_failing_case: Optional[Any] = None
    exception: Optional[Exception] = None
    exception_traceback: Optional[str] = None
    complexity_reduction: float = 0.0
    coverage_info: Optional[Dict] = None


def test_property(property_func: Callable[[Any], bool], 
                 strategy: 'Strategy',
                 max_examples: int = 100,
                 random_seed: Optional[int] = None,
                 verbose: bool = False,
                 max_shrink_time: float = 30.0) -> TestResult:
    """Execute a comprehensive property-based test
    
    Args:
        property_func: Property function returning True for valid inputs
        strategy: Strategy for generating test inputs
        max_examples: Maximum test cases to generate before declaring success
        random_seed: Optional seed for reproducible test runs
        verbose: Whether to print progress information
        max_shrink_time: Maximum time to spend shrinking failures
        
    Returns:
        TestResult containing detailed execution information
    """
    start_time = time.time()
    random_state = random.Random(random_seed)
    
    if verbose:
        print(f"Testing property with up to {max_examples} examples")
        print(f"Random seed: {random_seed}")
    
    for example_count in range(max_examples):
        # Generate progressively more complex examples
        size = _calculate_size(example_count, max_examples)
        test_case = strategy.generate(random_state, size)
        
        if verbose and example_count % 20 == 0:
            print(f"  Generated example {example_count + 1}/{max_examples}")
        
        try:
            # Execute property function
            result = property_func(test_case)
            
            if not result:
                raise AssertionError("Property returned False")
                
        except Exception as e:
            # Property failed - begin comprehensive failure analysis
            if verbose:
                print(f"Property failed at example {example_count + 1}")
                print(f"Failure type: {type(e).__name__}")
                print(f"Original failing case: {test_case}")
            
            # Capture full traceback
            exception_traceback = traceback.format_exc()
            
            # Perform shrinking to find minimal failing case
            shrink_result = shrink_failure(
                lambda x: _test_property(property_func, x), 
                test_case, 
                strategy,
                max_time=max_shrink_time,
                verbose=verbose
            )
            
            execution_time = time.time() - start_time
            
            return TestResult(
                passed=False,
                examples_tried=example_count + 1,
                shrink_iterations=shrink_result.iterations,
                execution_time=execution_time,
                minimal_failing_case=shrink_result.minimal_case,
                exception=e,
                exception_traceback=exception_traceback,
                complexity_reduction=shrink_result.reduction_ratio
            )
    
    # All examples passed successfully
    execution_time = time.time() - start_time
    
    if verbose:
        print(f"Property passed on all {max_examples} examples")
        print(f"Total execution time: {execution_time:.3f}s")
    
    return TestResult(
        passed=True,
        examples_tried=max_examples,
        shrink_iterations=0,
        execution_time=execution_time
    )


def shrink_failure(property_func: Callable[[Any], bool], 
                  failing_input: Any, 
                  strategy: 'Strategy', 
                  max_iterations: int = 1000,
                  max_time: float = 30.0,
                  verbose: bool = False) -> ShrinkResult:
    """Find minimal failing case through systematic reduction
    
    Args:
        property_func: Property that should return True for valid inputs
        failing_input: Known failing input to be minimized
        strategy: Strategy with shrink method for the input type
        max_iterations: Maximum number of shrinking attempts
        max_time: Maximum time to spend shrinking (seconds)
        verbose: Whether to print shrinking progress
        
    Returns:
        ShrinkResult with minimal case and process statistics
    """
    start_time = time.time()
    current = failing_input
    iterations = 0
    original_complexity = _estimate_complexity(failing_input)
    
    # Verify the input actually fails
    if _test_property(property_func, current):
        raise ValueError("Input doesn't actually fail the property")
    
    if verbose:
        print(f"Starting shrinking from complexity {original_complexity}")
    
    while (iterations < max_iterations and 
           time.time() - start_time < max_time):
        
        found_simpler = False
        
        # Try all shrinking candidates from current state
        for candidate in strategy.shrink(current):
            iterations += 1
            
            # Check termination conditions
            if (iterations >= max_iterations or 
                time.time() - start_time >= max_time):
                break
            
            # Test if this simplified version still fails
            if not _test_property(property_func, candidate):
                current = candidate
                found_simpler = True
                complexity = _estimate_complexity(current)
                if verbose:
                    print(f"  Shrunk to complexity {complexity} after {iterations} iterations")
                break  # Greedy: take first improvement found
        
        if not found_simpler:
            break  # No further simplification possible
    
    final_complexity = _estimate_complexity(current)
    reduction_ratio = (original_complexity - final_complexity) / max(original_complexity, 1)
    time_spent = time.time() - start_time
    
    if verbose:
        print(f"Shrinking complete: {original_complexity} → {final_complexity} "
              f"({reduction_ratio:.2%} reduction) in {iterations} iterations")
    
    return ShrinkResult(current, iterations, time_spent, reduction_ratio)


def _test_property(property_func: Callable, test_input: Any) -> bool:
    """Test property function, handling exceptions as failures"""
    try:
        result = property_func(test_input)
        return bool(result)  # Ensure boolean return
    except (AssertionError, Exception):
        return False  # Any exception counts as property failure


def _estimate_complexity(value: Any) -> int:
    """Estimate the structural complexity of a test value"""
    if value is None:
        return 0
    elif isinstance(value, bool):
        return 1
    elif isinstance(value, int):
        return abs(value) + 1
    elif isinstance(value, float):
        return int(abs(value)) + 1
    elif isinstance(value, str):
        return len(value)
    elif isinstance(value, (list, tuple)):
        return len(value) + sum(_estimate_complexity(item) for item in value)
    elif isinstance(value, dict):
        return (len(value) + 
                sum(_estimate_complexity(k) + _estimate_complexity(v) 
                    for k, v in value.items()))
    elif isinstance(value, set):
        return len(value) + sum(_estimate_complexity(item) for item in value)
    else:
        return 1  # Unknown types get minimal complexity


def _calculate_size(example_num: int, max_examples: int) -> int:
    """Calculate appropriate size parameter for test generation"""
    # Start small and gradually increase complexity
    if max_examples <= 1:
        return 10
    
    # Linear growth from 1 to 50, with some examples at size 0
    progress = example_num / (max_examples - 1)
    if example_num < 3:
        return example_num  # Very simple cases first
    else:
        return int(1 + progress * 49)  # Scale from 1 to 50


# Decorators for easier testing
def given(*strategy_args, **strategy_kwargs):
    """Decorator for property-based testing
    
    Usage:
        @given(integers(0, 100))
        def test_positive_sqrt(x):
            assert math.sqrt(x) >= 0
    """
    def decorator(test_func):
        def wrapper(**test_kwargs):
            # Extract strategy from args
            if len(strategy_args) == 1:
                strategy = strategy_args[0]
            else:
                try:
                    from .strategies import tuples
                except ImportError:
                    from strategies import tuples
                strategy = tuples(*strategy_args)
            
            # Merge test settings
            settings = {
                'max_examples': 100,
                'random_seed': None,
                'verbose': False,
                'max_shrink_time': 30.0
            }
            settings.update(strategy_kwargs)
            settings.update(test_kwargs)
            
            # Create property function
            def property_func(args):
                if len(strategy_args) == 1:
                    return test_func(args)
                else:
                    return test_func(*args)
            
            # Run test
            result = test_property(property_func, strategy, **settings)
            
            if not result.passed:
                error_msg = f"Property failed after {result.examples_tried} examples"
                if result.minimal_failing_case is not None:
                    error_msg += f"\nMinimal failing case: {result.minimal_failing_case}"
                if result.exception:
                    error_msg += f"\nOriginal exception: {result.exception}"
                raise AssertionError(error_msg)
            
            return result
        
        return wrapper
    return decorator


# Context manager for test settings
class PropertyTestSettings:
    """Context manager for configuring property tests"""
    
    def __init__(self, max_examples: int = 100, 
                 random_seed: Optional[int] = None,
                 verbose: bool = False,
                 max_shrink_time: float = 30.0):
        self.settings = {
            'max_examples': max_examples,
            'random_seed': random_seed,
            'verbose': verbose,
            'max_shrink_time': max_shrink_time
        }
        self._old_settings = None
    
    def __enter__(self):
        # In a real implementation, you might store global settings
        return self.settings
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Example usage
if __name__ == "__main__":
    from strategies import integers, lists
    
    # Test the framework with a simple property
    def test_list_reverse_property(lst):
        """Property: reversing a list twice should yield original"""
        return list(reversed(list(reversed(lst)))) == lst
    
    # Run property test
    result = test_property(
        test_list_reverse_property,
        lists(integers(-10, 10)),
        max_examples=50,
        random_seed=42,
        verbose=True
    )
    
    print(f"\nTest Result: {'PASSED' if result.passed else 'FAILED'}")
    print(f"Examples tried: {result.examples_tried}")
    print(f"Execution time: {result.execution_time:.3f}s")
    
    if not result.passed:
        print(f"Minimal failing case: {result.minimal_failing_case}")
        print(f"Shrink iterations: {result.shrink_iterations}")
        print(f"Complexity reduction: {result.complexity_reduction:.2%}")
        print(f"Exception: {result.exception}")
    
    # Example with decorator usage
    print("\n" + "="*50)
    print("Testing with decorator:")
    
    @given(integers(0, 100))
    def test_square_root_positive(x):
        """Test that square root of non-negative numbers is non-negative"""
        import math
        return math.sqrt(x) >= 0
    
    try:
        test_result = test_square_root_positive(verbose=True, max_examples=25)
        print("Square root property test passed!")
    except AssertionError as e:
        print(f"Square root property test failed: {e}")
    
    # Example of a failing property for demonstration
    print("\n" + "="*50)
    print("Testing a property that should fail:")
    
    def test_division_property(x):
        """Intentionally flawed property: x/x should always equal 1"""
        return x / x == 1.0  # This will fail when x=0
    
    fail_result = test_property(
        test_division_property,
        integers(-5, 5),
        max_examples=100,
        random_seed=42,
        verbose=True
    )
    
    print(f"\nFailing Test Result: {'PASSED' if fail_result.passed else 'FAILED'}")
    if not fail_result.passed:
        print(f"Found failure after {fail_result.examples_tried} examples")
        print(f"Minimal failing case: {fail_result.minimal_failing_case}")
        print(f"Shrinking took {fail_result.shrink_iterations} iterations")
        print(f"Exception type: {type(fail_result.exception).__name__}")
    
    # Demonstrate context manager usage
    print("\n" + "="*50)
    print("Using context manager for settings:")
    
    with PropertyTestSettings(max_examples=30, verbose=True, random_seed=123) as settings:
        def test_list_length_property(lst):
            """Property: length of list should be non-negative"""
            return len(lst) >= 0
        
        ctx_result = test_property(
            test_list_length_property,
            lists(integers()),
            **settings
        )
        
        print(f"Context manager test: {'PASSED' if ctx_result.passed else 'FAILED'}")
        print(f"Used settings: {settings}")
