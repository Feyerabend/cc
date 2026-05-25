import statistics
from collections import defaultdict, Counter
from typing import Dict, List, Set, Callable, Any, Tuple
import math
import random

class StatisticalTestRunner:
    """Advanced test runner with statistical analysis capabilities"""
    
    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.test_statistics = defaultdict(list)
        self.distribution_data = defaultdict(list)
    
    def run_statistical_test(self, property_func: Callable[[Any], bool],
                           strategy: 'Strategy',
                           sample_size: int = 1000,
                           hypothesis: str = "Property holds uniformly") -> Dict:
        """Run property test with statistical analysis"""
        
        print(f"Running statistical test: {hypothesis}")
        print(f"Sample size: {sample_size}")
        
        successes = 0
        failures = []
        input_characteristics = []
        
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
                    failures.append((test_input, characteristics))
                    self.test_statistics['failure_characteristics'].append(characteristics)
            except Exception as e:
                failures.append((test_input, characteristics, e))
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
        
        return {
            'hypothesis': hypothesis,
            'sample_size': sample_size,
            'success_rate': success_rate,
            'confidence_interval': confidence_interval,
            'distribution_analysis': distribution_analysis,
            'failure_patterns': failure_patterns,
            'statistical_power': self._calculate_statistical_power(sample_size, success_rate)
        }
    
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


# Basic strategy classes for the example to work
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


# Example usage with statistical analysis
if __name__ == "__main__":
    def sorting_property(lst):
        """Property: sorted list should be ordered and preserve elements"""
        if not isinstance(lst, list):
            return False

        sorted_lst = sorted(lst)

        # Check ordering
        for i in range(len(sorted_lst) - 1):
            if sorted_lst[i] > sorted_lst[i + 1]:
                return False

        # Check element preservation (multiset equality handles duplicates)
        from collections import Counter
        return Counter(lst) == Counter(sorted_lst)
    
    # Run statistical analysis
    runner = StatisticalTestRunner()
    results = runner.run_statistical_test(
        sorting_property,
        ListStrategy(IntegerStrategy(-100, 100)),
        sample_size=500,
        hypothesis="Sorting preserves elements and maintains ordering"
    )
    
    print("\n" + "="*60)
    print("STATISTICAL TEST RESULTS")
    print("="*60)
    print(f"Hypothesis: {results['hypothesis']}")
    print(f"Success Rate: {results['success_rate']:.3f}")
    print(f"Confidence Interval: {results['confidence_interval']}")
    print(f"Statistical Power: {results['statistical_power']:.3f}")
    print("\nDistribution Analysis:")
    for key, value in results['distribution_analysis'].items():
        print(f"  {key}: {value}")
    print("\nFailure Patterns:")
    for key, value in results['failure_patterns'].items():
        print(f"  {key}: {value}")

# Advanced property-based testing goes beyond simple random generation to
# incorporate statistical analysis and hypothesis-driven testing. This
# approach treats software testing as an experimental science where hypotheses
# about program behavior are systematically validated through controlled experiments.
