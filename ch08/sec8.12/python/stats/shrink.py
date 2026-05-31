import statistics
from collections import defaultdict, Counter
from typing import Dict, List, Set, Callable, Any, Tuple, Optional, Union
import math
import random
from abc import ABC, abstractmethod
import copy

class ShrinkResult:
    """Container for shrinking results with metadata"""
    def __init__(self, value: Any, shrink_steps: int = 0, shrink_path: List[str] = None):
        self.value = value
        self.shrink_steps = shrink_steps
        self.shrink_path = shrink_path or []
    
    def with_step(self, step_name: str) -> 'ShrinkResult':
        """Create new result with additional shrink step"""
        return ShrinkResult(
            self.value, 
            self.shrink_steps + 1, 
            self.shrink_path + [step_name]
        )

class Shrinker(ABC):
    """Abstract base class for value shrinkers"""
    
    @abstractmethod
    def shrink(self, value: Any) -> List[Any]:
        """Generate smaller variants of the value"""
        pass
    
    def shrink_towards_zero(self, n: Union[int, float]) -> List[Union[int, float]]:
        """Shrink numeric values towards zero"""
        if n == 0:
            return []
        
        candidates = []
        
        # Direct path to zero
        candidates.append(0)
        
        # Binary search approach
        if abs(n) > 1:
            candidates.append(n // 2 if isinstance(n, int) else n / 2)
        
        # Step down by 1
        if isinstance(n, int) and abs(n) > 1:
            candidates.append(n - 1 if n > 0 else n + 1)
        
        # Remove sign
        if n < 0:
            candidates.append(-n)
        
        return [c for c in candidates if c != n]

class IntegerShrinker(Shrinker):
    """Shrinker for integer values"""
    
    def shrink(self, value: int) -> List[int]:
        return self.shrink_towards_zero(value)

class FloatShrinker(Shrinker):
    """Shrinker for float values"""
    
    def shrink(self, value: float) -> List[float]:
        candidates = self.shrink_towards_zero(value)
        
        # Round to simpler values
        if value != int(value):
            candidates.append(float(int(value)))
        
        # Reduce precision
        if abs(value) >= 0.1:
            candidates.append(round(value, 1))
        
        return candidates

class ListShrinker(Shrinker):
    """Advanced shrinker for list values"""
    
    def __init__(self, element_shrinker: Optional[Shrinker] = None):
        self.element_shrinker = element_shrinker or self._get_default_shrinker
    
    def shrink(self, value: List[Any]) -> List[List[Any]]:
        if not value:
            return []
        
        candidates = []
        
        # 1. Remove elements (most important for lists)
        candidates.extend(self._shrink_by_removal(value))
        
        # 2. Shrink individual elements
        candidates.extend(self._shrink_elements(value))
        
        # 3. Sort the list (sometimes reveals ordering issues)
        try:
            sorted_list = sorted(value)
            if sorted_list != value:
                candidates.append(sorted_list)
        except TypeError:
            pass  # Elements not sortable
        
        # 4. Replace with simpler patterns
        candidates.extend(self._replace_with_patterns(value))
        
        return candidates
    
    def _shrink_by_removal(self, lst: List[Any]) -> List[List[Any]]:
        """Generate lists with elements removed"""
        candidates = []
        
        # Remove entire list
        candidates.append([])
        
        # Remove half the elements
        if len(lst) > 2:
            mid = len(lst) // 2
            candidates.append(lst[:mid])
            candidates.append(lst[mid:])
        
        # Remove from ends
        if len(lst) > 1:
            candidates.append(lst[1:])    # Remove first
            candidates.append(lst[:-1])   # Remove last
        
        # Remove individual elements
        for i in range(min(len(lst), 5)):  # Limit to avoid explosion
            candidates.append(lst[:i] + lst[i+1:])
        
        # Remove chunks
        if len(lst) > 4:
            chunk_size = len(lst) // 4
            for i in range(0, len(lst), chunk_size):
                if i + chunk_size < len(lst):
                    candidates.append(lst[:i] + lst[i+chunk_size:])
        
        return candidates
    
    def _shrink_elements(self, lst: List[Any]) -> List[List[Any]]:
        """Generate lists with individual elements shrunk"""
        candidates = []
        
        for i, element in enumerate(lst):
            shrinker = self._get_shrinker_for_element(element)
            if shrinker:
                for shrunk_element in shrinker.shrink(element):
                    new_list = lst.copy()
                    new_list[i] = shrunk_element
                    candidates.append(new_list)
        
        return candidates
    
    def _replace_with_patterns(self, lst: List[Any]) -> List[List[Any]]:
        """Replace list with simpler patterns"""
        if not lst:
            return []
        
        candidates = []
        
        # Single element repeated
        for element in set(lst[:3]):  # Limit unique elements to check
            candidates.append([element])
            if len(lst) > 1:
                candidates.append([element, element])
        
        # Simple sequences for numeric lists
        if all(isinstance(x, (int, float)) for x in lst):
            if len(lst) > 1:
                candidates.extend([
                    [0] * len(lst),
                    [1] * len(lst),
                    list(range(len(lst)))
                ])
        
        return candidates
    
    def _get_shrinker_for_element(self, element: Any) -> Optional[Shrinker]:
        """Get appropriate shrinker for an element"""
        if isinstance(element, int):
            return IntegerShrinker()
        elif isinstance(element, float):
            return FloatShrinker()
        elif isinstance(element, list):
            return ListShrinker()
        elif isinstance(element, str):
            return StringShrinker()
        return None
    
    def _get_default_shrinker(self, element: Any) -> Optional[Shrinker]:
        """Default shrinker selection"""
        return self._get_shrinker_for_element(element)

class StringShrinker(Shrinker):
    """Shrinker for string values"""
    
    def shrink(self, value: str) -> List[str]:
        if not value:
            return []
        
        candidates = []
        
        # Empty string
        candidates.append("")
        
        # Remove characters
        if len(value) > 1:
            candidates.append(value[1:])    # Remove first
            candidates.append(value[:-1])   # Remove last
            candidates.append(value[len(value)//2:])  # Remove first half
            candidates.append(value[:len(value)//2])  # Remove second half
        
        # Single characters
        for char in set(value[:5]):  # Limit to avoid explosion
            candidates.append(char)
        
        # Simple patterns
        if len(value) > 1:
            candidates.extend([
                "a" * len(value),
                "0" * len(value) if value.isdigit() else "a",
            ])
        
        # Lowercase
        if value != value.lower():
            candidates.append(value.lower())
        
        return candidates

class DictShrinker(Shrinker):
    """Shrinker for dictionary values"""
    
    def shrink(self, value: Dict[Any, Any]) -> List[Dict[Any, Any]]:
        if not value:
            return []
        
        candidates = []
        
        # Empty dict
        candidates.append({})
        
        # Remove keys
        keys = list(value.keys())
        for i, key in enumerate(keys[:5]):  # Limit to prevent explosion
            new_dict = {k: v for k, v in value.items() if k != key}
            candidates.append(new_dict)
        
        # Keep only one key-value pair
        for key in keys[:3]:
            candidates.append({key: value[key]})
        
        # Shrink values
        for key, val in list(value.items())[:3]:
            shrinker = self._get_shrinker_for_value(val)
            if shrinker:
                for shrunk_val in shrinker.shrink(val):
                    new_dict = value.copy()
                    new_dict[key] = shrunk_val
                    candidates.append(new_dict)
        
        return candidates
    
    def _get_shrinker_for_value(self, value: Any) -> Optional[Shrinker]:
        """Get appropriate shrinker for a value"""
        if isinstance(value, int):
            return IntegerShrinker()
        elif isinstance(value, float):
            return FloatShrinker()
        elif isinstance(value, str):
            return StringShrinker()
        elif isinstance(value, list):
            return ListShrinker()
        elif isinstance(value, dict):
            return DictShrinker()
        return None

class StatisticalTestRunner:
    """Enhanced test runner with statistical analysis and advanced shrinking"""
    
    def __init__(self, significance_level: float = 0.05, max_shrink_iterations: int = 100):
        self.significance_level = significance_level
        self.max_shrink_iterations = max_shrink_iterations
        self.test_statistics = defaultdict(list)
        self.distribution_data = defaultdict(list)
    
    def run_statistical_test(self, property_func: Callable[[Any], bool],
                           strategy: 'Strategy',
                           sample_size: int = 1000,
                           hypothesis: str = "Property holds uniformly") -> Dict:
        """Run property test with statistical analysis and shrinking"""
        
        print(f"Running statistical test: {hypothesis}")
        print(f"Sample size: {sample_size}")
        
        successes = 0
        failures = []
        input_characteristics = []
        shrunk_counterexamples = []
        
        random_state = random.Random(42)  # Reproducible results
        
        for i in range(sample_size):
            size = self._adaptive_sizing(i, sample_size)
            test_input = strategy.generate(random_state, size)
            
            # Collect input characteristics for analysis
            characteristics = self._analyze_input(test_input)
            input_characteristics.append(characteristics)
            
            try:
                result = property_func(test_input)
                if result:
                    successes += 1
                    self.test_statistics['success_characteristics'].append(characteristics)
                else:
                    # Failure found - shrink it!
                    print(f"\nFailure found at iteration {i}, shrinking...")
                    shrink_result = self._shrink_counterexample(test_input, property_func)
                    failures.append((test_input, characteristics))
                    shrunk_counterexamples.append(shrink_result)
                    self.test_statistics['failure_characteristics'].append(characteristics)
                    
                    print(f"Original failing input: {test_input}")
                    print(f"Shrunk to: {shrink_result.value}")
                    print(f"Shrink steps: {shrink_result.shrink_steps}")
                    print(f"Shrink path: {' → '.join(shrink_result.shrink_path)}")
            except Exception as e:
                # Exception during test - shrink the input that caused it
                print(f"\nException found at iteration {i}, shrinking...")
                shrink_result = self._shrink_counterexample(
                    test_input, 
                    lambda x: self._safe_property_test(property_func, x)
                )
                failures.append((test_input, characteristics, e))
                shrunk_counterexamples.append(shrink_result)
                self.test_statistics['failure_characteristics'].append(characteristics)
        
        # Statistical analysis
        success_rate = successes / sample_size
        confidence_interval = self._calculate_confidence_interval(
            successes, sample_size, self.significance_level
        )
        
        # Distribution analysis
        distribution_analysis = self._analyze_input_distribution(input_characteristics)
        
        # Failure pattern analysis
        failure_patterns = self._analyze_failure_patterns(failures)
        
        # Shrinking effectiveness analysis
        shrinking_analysis = self._analyze_shrinking_effectiveness(shrunk_counterexamples)
        
        return {
            'hypothesis': hypothesis,
            'sample_size': sample_size,
            'success_rate': success_rate,
            'confidence_interval': confidence_interval,
            'distribution_analysis': distribution_analysis,
            'failure_patterns': failure_patterns,
            'shrunk_counterexamples': shrunk_counterexamples,
            'shrinking_analysis': shrinking_analysis,
            'statistical_power': self._calculate_statistical_power(sample_size, success_rate)
        }
    
    def _shrink_counterexample(self, failing_input: Any, property_func: Callable[[Any], bool]) -> ShrinkResult:
        """Shrink a failing test case to minimal counterexample"""
        current = ShrinkResult(failing_input)
        visited = {str(failing_input)}  # Avoid cycles
        
        # Verify the original input actually fails
        if self._safe_property_test(property_func, failing_input):
            return current  # Not actually a counterexample
        
        iteration = 0
        progress_made = True
        
        while progress_made and iteration < self.max_shrink_iterations:
            progress_made = False
            iteration += 1
            
            # Get appropriate shrinker
            shrinker = self._get_shrinker(current.value)
            if not shrinker:
                break
            
            # Generate shrinking candidates
            candidates = shrinker.shrink(current.value)
            
            # Test candidates in order of preference
            for candidate in candidates:
                candidate_str = str(candidate)
                if candidate_str in visited:
                    continue
                
                visited.add(candidate_str)
                
                # Test if the candidate still fails the property
                if not self._safe_property_test(property_func, candidate):
                    # Found a smaller counterexample
                    step_name = self._describe_shrink_step(current.value, candidate)
                    current = ShrinkResult(candidate, current.shrink_steps + 1, 
                                         current.shrink_path + [step_name])
                    progress_made = True
                    print(f"  Shrink step {current.shrink_steps}: {step_name}")
                    break  # Take the first improvement found
        
        return current
    
    def _safe_property_test(self, property_func: Callable[[Any], bool], test_input: Any) -> bool:
        """Safely test property, treating exceptions as failures"""
        try:
            return property_func(test_input)
        except Exception:
            return False  # Exception counts as property violation
    
    def _get_shrinker(self, value: Any) -> Optional[Shrinker]:
        """Get appropriate shrinker for a value type"""
        if isinstance(value, int):
            return IntegerShrinker()
        elif isinstance(value, float):
            return FloatShrinker()
        elif isinstance(value, list):
            return ListShrinker()
        elif isinstance(value, str):
            return StringShrinker()
        elif isinstance(value, dict):
            return DictShrinker()
        return None
    
    def _describe_shrink_step(self, original: Any, shrunk: Any) -> str:
        """Generate human-readable description of shrinking step"""
        if isinstance(original, list) and isinstance(shrunk, list):
            if len(shrunk) == 0:
                return "removed all elements"
            elif len(shrunk) < len(original):
                return f"removed {len(original) - len(shrunk)} elements"
            elif shrunk != original:
                return "modified elements"
        elif isinstance(original, (int, float)) and isinstance(shrunk, (int, float)):
            if shrunk == 0:
                return "reduced to zero"
            elif abs(shrunk) < abs(original):
                return f"reduced magnitude {original} → {shrunk}"
        elif isinstance(original, str) and isinstance(shrunk, str):
            if len(shrunk) == 0:
                return "emptied string"
            elif len(shrunk) < len(original):
                return f"shortened string ({len(original)} → {len(shrunk)} chars)"
        
        return f"simplified value"
    
    def _analyze_shrinking_effectiveness(self, shrink_results: List[ShrinkResult]) -> Dict:
        """Analyze effectiveness of shrinking process"""
        if not shrink_results:
            return {"effectiveness": "No counterexamples to analyze"}
        
        total_steps = sum(result.shrink_steps for result in shrink_results)
        avg_steps = total_steps / len(shrink_results) if shrink_results else 0
        
        # Analyze reduction in complexity
        complexity_reductions = []
        for result in shrink_results:
            original_complexity = self._estimate_complexity(result.value)  # Simplified
            complexity_reductions.append(original_complexity)
        
        return {
            "total_counterexamples": len(shrink_results),
            "average_shrink_steps": avg_steps,
            "max_shrink_steps": max(result.shrink_steps for result in shrink_results) if shrink_results else 0,
            "shrinking_success_rate": len([r for r in shrink_results if r.shrink_steps > 0]) / len(shrink_results) if shrink_results else 0
        }
    
    def _estimate_complexity(self, value: Any) -> int:
        """Simple complexity estimation for shrinking analysis"""
        if isinstance(value, (int, float)):
            return int(math.log10(abs(value) + 1))
        elif isinstance(value, (list, tuple)):
            return len(value) + sum(self._estimate_complexity(item) for item in value)
        elif isinstance(value, str):
            return len(value)
        elif isinstance(value, dict):
            return len(value) + sum(self._estimate_complexity(v) for v in value.values())
        return 1
    
    # ... (keeping all the original analysis methods unchanged)
    def _analyze_input(self, test_input: Any) -> Dict[str, Any]:
        """Extract statistical characteristics from test input"""
        characteristics = {}
        
        if isinstance(test_input, (int, float)):
            characteristics.update({
                'type': 'numeric',
                'magnitude': abs(test_input),
                'sign': 1 if test_input >= 0 else -1
            })
        elif isinstance(test_input, (list, tuple)):
            characteristics.update({
                'type': 'sequence',
                'length': len(test_input),
                'complexity': self._sequence_complexity(test_input)
            })
        elif isinstance(test_input, dict):
            characteristics.update({
                'type': 'mapping',
                'size': len(test_input),
                'key_types': list(set(type(k).__name__ for k in test_input.keys())),
                'value_types': list(set(type(v).__name__ for v in test_input.values()))
            })
        elif isinstance(test_input, str):
            characteristics.update({
                'type': 'string',
                'length': len(test_input),
                'character_diversity': len(set(test_input))
            })
        
        return characteristics
    
    def _sequence_complexity(self, sequence: List[Any]) -> float:
        """Calculate complexity metric for sequences"""
        if not sequence:
            return 0.0
        
        # Measure based on uniqueness and distribution
        unique_elements = len(set(str(x) for x in sequence))
        length = len(sequence)
        
        # Shannon entropy as complexity measure
        if unique_elements <= 1:
            return 0.0
        
        element_counts = Counter(str(x) for x in sequence)
        entropy = -sum(
            (count / length) * math.log2(count / length)
            for count in element_counts.values()
        )
        
        return entropy
    
    def _calculate_confidence_interval(self, successes: int, total: int, 
                                     alpha: float) -> Tuple[float, float]:
        """Calculate confidence interval for success rate"""
        if total == 0:
            return (0.0, 0.0)
        
        p = successes / total
        z_score = 1.96  # 95% confidence interval
        
        margin = z_score * math.sqrt(p * (1 - p) / total)
        return (max(0, p - margin), min(1, p + margin))
    
    def _analyze_input_distribution(self, characteristics: List[Dict]) -> Dict:
        """Analyze distribution of input characteristics"""
        analysis = {}
        
        # Type distribution
        types = [char.get('type', 'unknown') for char in characteristics]
        analysis['type_distribution'] = dict(Counter(types))
        
        # Size/length distributions
        lengths = [char.get('length', char.get('size', 0)) for char in characteristics]
        if lengths:
            analysis['size_statistics'] = {
                'mean': statistics.mean(lengths),
                'median': statistics.median(lengths),
                'std_dev': statistics.stdev(lengths) if len(lengths) > 1 else 0,
                'range': (min(lengths), max(lengths))
            }
        
        return analysis
    
    def _analyze_failure_patterns(self, failures: List) -> Dict:
        """Identify patterns in test failures"""
        if not failures:
            return {'pattern': 'No failures detected'}
        
        patterns = {}
        
        # Extract characteristics from failures
        failure_chars = [failure[1] for failure in failures if len(failure) > 1]
        
        if failure_chars:
            # Common characteristics in failures
            common_types = Counter(char.get('type') for char in failure_chars)
            patterns['failure_types'] = dict(common_types.most_common(3))
            
            # Size analysis for failures
            failure_sizes = [char.get('length', char.get('size', 0)) for char in failure_chars]
            if failure_sizes:
                patterns['failure_size_stats'] = {
                    'mean_size': statistics.mean(failure_sizes),
                    'size_range': (min(failure_sizes), max(failure_sizes))
                }
        
        return patterns
    
    def _calculate_statistical_power(self, sample_size: int, observed_rate: float) -> float:
        """Estimate statistical power of the test"""
        # Simplified power calculation
        # In practice, this would depend on effect size and alternative hypothesis
        if sample_size < 30:
            return 0.5  # Low power for small samples
        elif sample_size < 100:
            return 0.7
        else:
            return 0.9  # High power for large samples
    
    def _adaptive_sizing(self, iteration: int, total_iterations: int) -> int:
        """Calculate adaptive size parameter for test generation"""
        # Use more complex inputs as testing progresses
        progress = iteration / total_iterations
        return int(1 + progress * 25)


# Enhanced strategy classes with better shrinking support
class Strategy:
    """Base strategy class"""
    def generate(self, random_state, size):
        raise NotImplementedError

class IntegerStrategy(Strategy):
    """Strategy for generating integers within a range"""
    def __init__(self, min_val=-100, max_val=100):
        self.min_val = min_val
        self.max_val = max_val
    
    def generate(self, random_state, size):
        return random_state.randint(self.min_val, self.max_val)

class ListStrategy(Strategy):
    """Strategy for generating lists using another strategy"""
    def __init__(self, element_strategy, max_length=50):
        self.element_strategy = element_strategy
        self.max_length = max_length
    
    def generate(self, random_state, size):
        length = random_state.randint(0, min(size, self.max_length))
        return [self.element_strategy.generate(random_state, size) for _ in range(length)]


# Example usage with enhanced statistical analysis and shrinking
if __name__ == "__main__":
    def buggy_sorting_property(lst):
        """A buggy property that fails on lists with duplicates"""
        if not isinstance(lst, list) or len(lst) <= 1:
            return True
        
        sorted_lst = sorted(lst)
        
        # Check ordering (correct)
        for i in range(len(sorted_lst) - 1):
            if sorted_lst[i] > sorted_lst[i + 1]:
                return False
        
        # Buggy check: fails when there are duplicates
        # This will cause the property to fail, demonstrating shrinking
        return len(set(lst)) == len(lst)  # Bug: requires all elements to be unique
    
    def correct_sorting_property(lst):
        """Correct property: sorted list should be ordered and preserve elements"""
        if not isinstance(lst, list):
            return False
        
        sorted_lst = sorted(lst)
        
        # Check ordering
        for i in range(len(sorted_lst) - 1):
            if sorted_lst[i] > sorted_lst[i + 1]:
                return False
        
        # Check element preservation (using Counter to handle duplicates)
        from collections import Counter
        return Counter(lst) == Counter(sorted_lst)
    
    print("Testing buggy property (will demonstrate shrinking):")
    print("=" * 60)
    
    # Test the buggy property to demonstrate shrinking
    runner = StatisticalTestRunner(max_shrink_iterations=50)
    results = runner.run_statistical_test(
        buggy_sorting_property,
        ListStrategy(IntegerStrategy(-10, 10)),
        sample_size=100,
        hypothesis="Sorting preserves unique elements and maintains ordering (BUGGY)"
    )
    
    print("\n" + "="*60)
    print("STATISTICAL TEST RESULTS")
    print("="*60)
    print(f"Hypothesis: {results['hypothesis']}")
    print(f"Success Rate: {results['success_rate']:.3f}")
    print(f"Confidence Interval: {results['confidence_interval']}")
    print(f"Statistical Power: {results['statistical_power']:.3f}")
    print("\nShrinking Analysis:")
    for key, value in results['shrinking_analysis'].items():
        print(f"  {key}: {value}")
    
    if results['shrunk_counterexamples']:
        print(f"\nMinimal Counterexamples Found:")
        for i, shrink_result in enumerate(results['shrunk_counterexamples'][:3]):
            print(f"  {i+1}. {shrink_result.value} (shrunk in {shrink_result.shrink_steps} steps)")
    
    print("\n" + "="*60)
    print("Now testing correct property:")
    print("="*60)
    
    # Test the correct property
    results2 = runner.run_statistical_test(
        correct_sorting_property,
        ListStrategy(IntegerStrategy(-10, 10)),
        sample_size=100,
        hypothesis="Sorting preserves elements and maintains ordering (CORRECT)"
    )
    
    print(f"Success Rate: {results2['success_rate']:.3f}")
    print(f"Counterexamples: {len(results2['shrunk_counterexamples'])}")
    print(f"Statistical Power: {results2['statistical_power']:.3f}")

