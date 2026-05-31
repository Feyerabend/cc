from typing import Dict, List, Set, Callable, Any, Tuple
import random
import math

# Base Strategy Classes
class Strategy:
    """Base class for generating test data"""
    def generate(self, random_state, size):
        raise NotImplementedError

class IntegerStrategy(Strategy):
    """Strategy for generating random integers within a range"""
    def __init__(self, min_val: int, max_val: int):
        self.min_val = min_val
        self.max_val = max_val
    
    def generate(self, random_state, size):
        return random_state.randint(self.min_val, self.max_val)

class FloatStrategy(Strategy):
    """Strategy for generating random floats within a range"""
    def __init__(self, min_val: float, max_val: float):
        self.min_val = min_val
        self.max_val = max_val
    
    def generate(self, random_state, size):
        return random_state.uniform(self.min_val, self.max_val)

class ListStrategy(Strategy):
    """Strategy for generating lists using an element strategy"""
    def __init__(self, element_strategy: Strategy, min_size: int = 0, max_size: int = None):
        self.element_strategy = element_strategy
        self.min_size = min_size
        self.max_size = max_size
    
    def generate(self, random_state, size):
        if self.max_size is None:
            list_size = min(size, 20)  # Cap at reasonable size
        else:
            list_size = random_state.randint(self.min_size, min(self.max_size, size))
        
        return [self.element_strategy.generate(random_state, 1) for _ in range(list_size)]

class TupleStrategy(Strategy):
    """Strategy for generating tuples with multiple element types"""
    def __init__(self, *element_strategies: Strategy):
        self.element_strategies = element_strategies
    
    def generate(self, random_state, size):
        return tuple(strategy.generate(random_state, 1) for strategy in self.element_strategies)

# Metamorphic Testing Framework
class MetamorphicRelation:
    """Encapsulates a metamorphic relation between function inputs and outputs"""
    
    def __init__(self, name: str, input_transform: Callable, 
                 output_relation: Callable[[Any, Any], bool]):
        self.name = name
        self.input_transform = input_transform
        self.output_relation = output_relation
    
    def test(self, func: Callable, original_input: Any) -> bool:
        """Test if the metamorphic relation holds for given function and input"""
        try:
            # Execute function on original input
            original_output = func(original_input)
            
            # Transform input according to metamorphic relation
            transformed_input = self.input_transform(original_input)
            
            # Execute function on transformed input
            transformed_output = func(transformed_input)
            
            # Check if outputs satisfy the expected relation
            return self.output_relation(original_output, transformed_output)
        
        except Exception as e:
            # For debugging: print(f"Exception in metamorphic test: {e}")
            return False  # Any exception indicates relation violation

class MetamorphicTestSuite:
    """Comprehensive metamorphic testing framework"""
    
    def __init__(self):
        self.relations = []
    
    def add_relation(self, relation: MetamorphicRelation):
        """Add a metamorphic relation to the test suite"""
        self.relations.append(relation)
    
    def test_function(self, func: Callable, strategy: Strategy, 
                     num_tests: int = 100) -> Dict[str, Any]:
        """Test all metamorphic relations for a function"""
        results = {}
        random_state = random.Random(42)
        
        for relation in self.relations:
            successes = 0
            failures = []
            
            print(f"Testing metamorphic relation: {relation.name}")
            
            for i in range(num_tests):
                size = i // 10 + 1  # Gradually increase complexity
                test_input = strategy.generate(random_state, size)
                
                if relation.test(func, test_input):
                    successes += 1
                else:
                    failures.append(test_input)
                    if len(failures) <= 3:  # Keep first few failures for analysis
                        print(f"  Failure with input: {test_input}")
            
            results[relation.name] = {
                'success_rate': successes / num_tests,
                'total_tests': num_tests,
                'failures': len(failures),
                'sample_failures': failures[:3]
            }
        
        return results

# Custom relation that checks element preservation against the original input,
# rather than comparing two outputs (which would be identical with identity transform).
class SameElementsRelation(MetamorphicRelation):
    """Verifies that func's output is a permutation of its input."""
    def test(self, func: Callable, original_input: Any) -> bool:
        try:
            from collections import Counter
            output = func(original_input)
            return Counter(output) == Counter(original_input)
        except Exception:
            return False


# Example: Metamorphic testing for sorting algorithms
def create_sorting_metamorphic_suite() -> MetamorphicTestSuite:
    """Create metamorphic test suite for sorting functions"""
    suite = MetamorphicTestSuite()
    
    # Relation 1: Permutation invariance
    # Sorting any permutation of a list should yield the same result
    def permutation_transform(lst):
        if len(lst) <= 1:
            return lst
        shuffled = lst.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def same_result_relation(output1, output2):
        return output1 == output2
    
    suite.add_relation(MetamorphicRelation(
        "Permutation Invariance",
        permutation_transform,
        same_result_relation
    ))
    
    # Relation 2: Element preservation
    # The sorted output must be a permutation of the input — no elements added or dropped.
    # Uses SameElementsRelation (custom subclass) because the standard MetamorphicRelation
    # only compares two *outputs*; here we need to compare the output against the *input*.
    suite.add_relation(SameElementsRelation(
        "Same Elements Property",
        lambda lst: lst,       # dummy transform — not used by the overridden test()
        lambda o1, o2: True    # dummy relation — not used by the overridden test()
    ))
    
    # Relation 3: Duplication property
    # Sorting a list with duplicated elements should produce a sorted list
    # with correspondingly duplicated elements
    def duplication_transform(lst):
        return lst + lst  # Duplicate entire list
    
    def duplication_relation(original_output, duplicated_output):
        expected = sorted(original_output + original_output)
        return duplicated_output == expected
    
    suite.add_relation(MetamorphicRelation(
        "Duplication Property",
        duplication_transform,
        duplication_relation
    ))
    
    # Relation 4: Subset property
    # If we add elements to a list, the original sorted elements should appear
    # as a subsequence in the new sorted list
    def add_elements_transform(lst):
        additional_elements = [random.randint(-100, 100) for _ in range(random.randint(1, 3))]
        return lst + additional_elements
    
    def subset_relation(original_output, extended_output):
        # Check if original_output elements appear in extended_output with correct counts
        from collections import Counter
        orig_counter = Counter(original_output)
        extended_counter = Counter(extended_output)
        
        for element, count in orig_counter.items():
            if extended_counter[element] < count:
                return False
        return True
    
    suite.add_relation(MetamorphicRelation(
        "Subset Property",
        add_elements_transform,
        subset_relation
    ))
    
    return suite

# Module-level custom relation classes for mathematical properties.
# They override test() directly so they can access the original *input*,
# not just the two outputs that the standard MetamorphicRelation exposes.

class SqrtScalingRelation(MetamorphicRelation):
    """sqrt(k²·x) = k·sqrt(x) for any k > 0 and x ≥ 0."""
    def test(self, func: Callable, original_input: Any) -> bool:
        try:
            x = abs(original_input)          # ensure non-negative
            original_output = func(x)
            k = random.uniform(1, 10)
            scaled_output = func(k * k * x)
            return abs(scaled_output - k * original_output) < 1e-9
        except Exception:
            return False


class LogAdditionRelation(MetamorphicRelation):
    """log(a) + log(b) = log(a·b) for a, b > 0."""
    def test(self, func: Callable, original_input: Any) -> bool:
        try:
            a = abs(original_input) if original_input <= 0 else original_input
            b = random.uniform(1, 100)
            return abs(func(a) + func(b) - func(a * b)) < 1e-9
        except Exception:
            return False


def create_sqrt_metamorphic_suite() -> MetamorphicTestSuite:
    """Metamorphic suite for square-root functions: sqrt(k²·x) = k·sqrt(x)."""
    suite = MetamorphicTestSuite()
    suite.add_relation(SqrtScalingRelation(
        "Square Root Scaling Property",
        lambda x: x,       # dummy — overridden by test()
        lambda x, y: True  # dummy — overridden by test()
    ))
    return suite


def create_log_metamorphic_suite() -> MetamorphicTestSuite:
    """Metamorphic suite for logarithm functions: log(a) + log(b) = log(a·b)."""
    suite = MetamorphicTestSuite()
    suite.add_relation(LogAdditionRelation(
        "Logarithm Addition Property",
        lambda x: x,       # dummy — overridden by test()
        lambda x, y: True  # dummy — overridden by test()
    ))
    return suite

# String processing metamorphic relations
def create_string_metamorphic_suite() -> MetamorphicTestSuite:
    """Create metamorphic relations for string processing functions"""
    suite = MetamorphicTestSuite()
    
    # Relation: Case insensitive operations
    # For functions that should be case insensitive
    def case_transform(s):
        if isinstance(s, str):
            return s.swapcase()
        return s
    
    def case_insensitive_relation(output1, output2):
        if isinstance(output1, str) and isinstance(output2, str):
            return output1.lower() == output2.lower()
        return output1 == output2
    
    suite.add_relation(MetamorphicRelation(
        "Case Insensitive Property",
        case_transform,
        case_insensitive_relation
    ))
    
    # Relation: Whitespace normalization
    # Functions should handle extra whitespace consistently
    def whitespace_transform(s):
        if isinstance(s, str):
            return "  " + s + "  "  # Add leading/trailing whitespace
        return s
    
    def whitespace_relation(output1, output2):
        if isinstance(output1, str) and isinstance(output2, str):
            return output1.strip() == output2.strip()
        return output1 == output2
    
    suite.add_relation(MetamorphicRelation(
        "Whitespace Normalization",
        whitespace_transform,
        whitespace_relation
    ))
    
    return suite

# Test functions to demonstrate the framework
def correct_sort(lst):
    """Correct sorting implementation"""
    return sorted(lst)

def buggy_sort(lst):
    """Buggy sorting implementation that silently drops duplicate elements"""
    if len(lst) <= 1:
        return lst
    # Bug: converts to set() before sorting, which removes all duplicate values
    return sorted(set(lst))

def safe_sqrt(x):
    """Safe square root that handles edge cases"""
    return math.sqrt(abs(x))

def safe_log(x):
    """Safe logarithm that handles edge cases"""
    return math.log(abs(x) + 1e-10)

# Example usage and demonstrations
if __name__ == "__main__":
    print("="*60)
    print("METAMORPHIC TESTING FRAMEWORK DEMONSTRATION")
    print("="*60)
    
    # Test 1: Correct sorting function
    print("\n1. Testing CORRECT sorting function:")
    print("-" * 40)
    sorting_suite = create_sorting_metamorphic_suite()
    correct_results = sorting_suite.test_function(
        correct_sort,
        ListStrategy(IntegerStrategy(-50, 50)),
        num_tests=50
    )
    
    print("\nRESULTS - Correct Sort:")
    for relation_name, results in correct_results.items():
        print(f"{relation_name}: {results['success_rate']:.2%} success rate")
    
    # Test 2: Buggy sorting function
    print("\n\n2. Testing BUGGY sorting function:")
    print("-" * 40)
    buggy_results = sorting_suite.test_function(
        buggy_sort,
        ListStrategy(IntegerStrategy(-10, 10)),
        num_tests=30
    )
    
    print("\nRESULTS - Buggy Sort:")
    for relation_name, results in buggy_results.items():
        print(f"{relation_name}: {results['success_rate']:.2%} success rate")
        if results['failures'] > 0:
            print(f"  → Found {results['failures']} failures!")
    
    # Test 3: Mathematical functions — each function paired with its own suite
    print("\n\n3. Testing mathematical functions:")
    print("-" * 40)

    sqrt_suite = create_sqrt_metamorphic_suite()
    sqrt_results = sqrt_suite.test_function(
        safe_sqrt,
        FloatStrategy(0.1, 100.0),
        num_tests=30
    )

    log_suite = create_log_metamorphic_suite()
    log_results = log_suite.test_function(
        safe_log,
        FloatStrategy(0.1, 100.0),
        num_tests=30
    )

    print("\nRESULTS - Square Root Function:")
    for relation_name, results in sqrt_results.items():
        print(f"{relation_name}: {results['success_rate']:.2%} success rate")

    print("\nRESULTS - Logarithm Function:")
    for relation_name, results in log_results.items():
        print(f"{relation_name}: {results['success_rate']:.2%} success rate")
    
    # Test 4: String functions
    print("\n\n4. Testing string functions:")
    print("-" * 40)
    
    def simple_upper(s):
        return str(s).upper()
    
    class StringStrategy(Strategy):
        def generate(self, random_state, size):
            chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '
            length = random_state.randint(1, min(size + 5, 20))
            return ''.join(random_state.choice(chars) for _ in range(length))
    
    string_suite = create_string_metamorphic_suite()
    string_results = string_suite.test_function(
        simple_upper,
        StringStrategy(),
        num_tests=20
    )
    
    print("\nRESULTS - String Upper Function:")
    for relation_name, results in string_results.items():
        print(f"{relation_name}: {results['success_rate']:.2%} success rate")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("Metamorphic testing successfully identified:")
    print("  Correct implementations (high success rates)")
    print("x Buggy implementations (low success rates)")
    print("  Edge cases and corner cases")
    print("  Different types of functions (sort, math, string)")
    print("\nThis framework can be extended with custom relations")
    print("for testing any software component!")

# Metamorphic testing represents an advanced property-based testing technique
# that focuses on relationships between multiple executions of a function with
# related inputs, rather than checking absolute correctness. This approach is
# particularly valuable when the expected output is difficult to compute
# independently or when testing complex algorithms where oracle problems exist.
