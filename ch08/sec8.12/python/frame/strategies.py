from abc import ABC, abstractmethod
import random
import string
from typing import Any, Iterator, List, Optional, Callable, Union
from itertools import islice


class Strategy(ABC):
    """Abstract base class for all test input generation strategies"""
    
    @abstractmethod
    def generate(self, random_state: random.Random, size: int) -> Any:
        """Generate a test value of appropriate complexity
        
        Args:
            random_state: Seeded random number generator for reproducibility
            size: Hint for complexity/size of generated value (0-100)
            
        Returns:
            Generated value according to this strategy's distribution
        """
        pass
    
    @abstractmethod
    def shrink(self, value: Any) -> Iterator[Any]:
        """Generate progressively simpler versions of a value
        
        Args:
            value: Complex value to be simplified
            
        Yields:
            Simpler variants that maintain the same type and structure
        """
        pass
    
    def map(self, transform_func: Callable[[Any], Any]) -> 'MappedStrategy':
        """Transform generated values through a mapping function"""
        return MappedStrategy(self, transform_func)
    
    def filter(self, predicate_func: Callable[[Any], bool]) -> 'FilteredStrategy':
        """Filter generated values that satisfy a predicate"""
        return FilteredStrategy(self, predicate_func)


class IntegerStrategy(Strategy):
    """Generate integers with configurable range and distribution"""
    
    def __init__(self, min_value: int = -1000, max_value: int = 1000):
        if min_value >= max_value:
            raise ValueError("min_value must be less than max_value")
        self.min_value = min_value
        self.max_value = max_value
    
    def generate(self, random_state: random.Random, size: int) -> int:
        """Generate integers with size-dependent distribution"""
        # Small sizes favor simple values near zero
        if size < 10:
            # Bias toward smaller absolute values for simple cases
            limited_range = min(size * 2, abs(self.max_value - self.min_value) // 4)
            center = (self.min_value + self.max_value) // 2
            actual_min = max(self.min_value, center - limited_range)
            actual_max = min(self.max_value, center + limited_range)
        else:
            # Use full range for complex cases
            actual_min, actual_max = self.min_value, self.max_value
        
        return random_state.randint(actual_min, actual_max)
    
    def shrink(self, value: int) -> Iterator[int]:
        """Shrink integers toward zero through binary reduction"""
        if not isinstance(value, int) or value == 0:
            return
        
        # Always try zero first as it's the simplest value
        if self.min_value <= 0 <= self.max_value:
            yield 0
        
        # Then try progressively smaller absolute values
        current = abs(value)
        sign = 1 if value > 0 else -1
        
        while current > 1:
            current = current // 2
            candidate = sign * current
            if (self.min_value <= candidate <= self.max_value and 
                candidate != value):
                yield candidate


class FloatStrategy(Strategy):
    """Generate floating point numbers"""
    
    def __init__(self, min_value: float = -1000.0, max_value: float = 1000.0):
        if min_value >= max_value:
            raise ValueError("min_value must be less than max_value")
        self.min_value = min_value
        self.max_value = max_value
    
    def generate(self, random_state: random.Random, size: int) -> float:
        if size < 5:
            # Simple cases: integers as floats or common fractions
            if random_state.random() < 0.5:
                return float(random_state.randint(-size, size))
            else:
                return random_state.choice([0.5, -0.5, 0.25, -0.25, 1.5, -1.5])
        
        return random_state.uniform(self.min_value, self.max_value)
    
    def shrink(self, value: float) -> Iterator[float]:
        if not isinstance(value, (int, float)) or value == 0.0:
            return
        
        # Try zero
        if self.min_value <= 0.0 <= self.max_value:
            yield 0.0
        
        # Try integer version
        int_val = int(value)
        if self.min_value <= int_val <= self.max_value and int_val != value:
            yield float(int_val)
        
        # Try halving
        half = value / 2
        if self.min_value <= half <= self.max_value:
            yield half


class StringStrategy(Strategy):
    """Generate strings with configurable alphabet and length"""
    
    def __init__(self, alphabet: str = string.ascii_letters + string.digits, 
                 min_length: int = 0, max_length: int = 50):
        if not alphabet:
            raise ValueError("Alphabet cannot be empty")
        if min_length < 0 or max_length < min_length:
            raise ValueError("Invalid length constraints")
        
        self.alphabet = alphabet
        self.min_length = min_length
        self.max_length = max_length
    
    def generate(self, random_state: random.Random, size: int) -> str:
        # Length grows with size but respects bounds
        max_len = min(self.max_length, max(self.min_length, size))
        length = random_state.randint(self.min_length, max_len)
        
        if length == 0:
            return ""
        
        # For small sizes, prefer simple characters
        if size < 10:
            simple_chars = [c for c in self.alphabet if c.isalnum()]
            if simple_chars:
                alphabet = simple_chars
            else:
                alphabet = self.alphabet
        else:
            alphabet = self.alphabet
        
        return ''.join(random_state.choices(alphabet, k=length))
    
    def shrink(self, value: str) -> Iterator[str]:
        if not isinstance(value, str):
            return
        
        # Try empty string
        if self.min_length == 0 and value:
            yield ""
        
        # Try removing characters from end
        for length in range(len(value) - 1, self.min_length - 1, -1):
            if length >= 0:
                yield value[:length]
        
        # Try removing characters from different positions
        for i in range(len(value)):
            if len(value) - 1 >= self.min_length:
                yield value[:i] + value[i+1:]


class ListStrategy(Strategy):
    """Generate lists using an element strategy"""
    
    def __init__(self, element_strategy: Strategy, 
                 min_length: int = 0, max_length: int = 50):
        if min_length < 0 or max_length < min_length:
            raise ValueError("Invalid length constraints")
        self.element_strategy = element_strategy
        self.min_length = min_length
        self.max_length = max_length
    
    def generate(self, random_state: random.Random, size: int) -> list:
        """Generate lists with size-dependent length distribution"""
        # Length grows with size but respects bounds
        max_len = min(self.max_length, max(self.min_length, size))
        length = random_state.randint(self.min_length, max_len)
        
        # Generate elements with reduced size to prevent exponential growth
        element_size = max(1, size // 2) if length > 0 else size
        
        return [
            self.element_strategy.generate(random_state, element_size)
            for _ in range(length)
        ]
    
    def shrink(self, value: list) -> Iterator[list]:
        """Shrink lists through element removal and element shrinking"""
        if not isinstance(value, list):
            return
        
        # Try empty list
        if self.min_length == 0 and value:
            yield []
        
        # Phase 1: Remove elements (try removing from different positions)
        for i in range(len(value)):
            if len(value) - 1 >= self.min_length:
                yield value[:i] + value[i+1:]
        
        # Phase 2: Try removing multiple elements (divide and conquer)
        if len(value) > 2:
            mid = len(value) // 2
            if mid >= self.min_length:
                yield value[:mid]
            if len(value) - mid >= self.min_length:
                yield value[mid:]
        
        # Phase 3: Shrink individual elements while keeping structure
        for i, element in enumerate(value):
            for shrunken_element in self.element_strategy.shrink(element):
                new_list = value.copy()
                new_list[i] = shrunken_element
                yield new_list


class TupleStrategy(Strategy):
    """Generate tuples by combining multiple strategies"""
    
    def __init__(self, *element_strategies: Strategy):
        if not element_strategies:
            raise ValueError("TupleStrategy requires at least one element strategy")
        self.element_strategies = element_strategies
    
    def generate(self, random_state: random.Random, size: int) -> tuple:
        """Generate tuple with each element from its respective strategy"""
        element_size = max(1, size // len(self.element_strategies))
        return tuple(
            strategy.generate(random_state, element_size)
            for strategy in self.element_strategies
        )
    
    def shrink(self, value: tuple) -> Iterator[tuple]:
        """Shrink tuples by shrinking individual elements"""
        if not isinstance(value, tuple) or len(value) != len(self.element_strategies):
            return
        
        # Shrink each element position independently
        for i, (element, strategy) in enumerate(zip(value, self.element_strategies)):
            for shrunken_element in strategy.shrink(element):
                yield value[:i] + (shrunken_element,) + value[i+1:]


class DictionaryStrategy(Strategy):
    """Generate dictionaries with configurable key and value strategies"""
    
    def __init__(self, key_strategy: Strategy, value_strategy: Strategy,
                 min_size: int = 0, max_size: int = 20):
        if min_size < 0:
            raise ValueError("min_size must be non-negative")
        if max_size < min_size:
            raise ValueError("max_size must be >= min_size")
            
        self.key_strategy = key_strategy
        self.value_strategy = value_strategy
        self.min_size = min_size
        self.max_size = max_size
    
    def generate(self, random_state: random.Random, size: int) -> dict:
        """Generate dictionary with size-dependent number of entries"""
        dict_size = random_state.randint(
            self.min_size, 
            min(self.max_size, max(self.min_size, size))
        )
        
        result = {}
        attempts = 0
        max_attempts = dict_size * 3 if dict_size > 0 else 1

        # Allow for key collisions by trying multiple times
        element_size = max(1, size // 2)
        
        while len(result) < dict_size and attempts < max_attempts:
            try:
                key = self.key_strategy.generate(random_state, element_size)
                # Keys must be hashable
                hash(key)  # This will raise TypeError if not hashable
                value = self.value_strategy.generate(random_state, element_size)
                result[key] = value
            except TypeError:
                # Generated key is not hashable, try again
                pass
            attempts += 1
        
        return result
    
    def shrink(self, value: dict) -> Iterator[dict]:
        """Shrink dictionaries by removing entries and shrinking keys/values"""
        if not isinstance(value, dict):
            return
            
        # Try empty dict
        if self.min_size == 0 and value:
            yield {}
        
        # Phase 1: Remove entries
        items = list(value.items())
        for i in range(len(items)):
            if len(items) - 1 >= self.min_size:
                new_dict = {k: v for j, (k, v) in enumerate(items) if j != i}
                yield new_dict
        
        # Phase 2: Remove multiple entries (divide and conquer)
        if len(items) > 2:
            mid = len(items) // 2
            if mid >= self.min_size:
                yield dict(items[:mid])
            if len(items) - mid >= self.min_size:
                yield dict(items[mid:])
        
        # Phase 3: Shrink individual keys and values
        for key, val in items:
            # Try shrinking the key
            for shrunken_key in self.key_strategy.shrink(key):
                try:
                    # Ensure the shrunken key is hashable
                    hash(shrunken_key)
                    if shrunken_key not in value:  # Avoid key conflicts
                        new_dict = value.copy()
                        del new_dict[key]
                        new_dict[shrunken_key] = val
                        yield new_dict
                except (TypeError, KeyError):
                    continue
            
            # Try shrinking the value
            for shrunken_val in self.value_strategy.shrink(val):
                new_dict = value.copy()
                new_dict[key] = shrunken_val
                yield new_dict


class OneOfStrategy(Strategy):
    """Choose randomly from multiple strategies with weighted selection"""
    
    def __init__(self, *strategies: Strategy, weights: Optional[List[float]] = None):
        if not strategies:
            raise ValueError("OneOfStrategy requires at least one strategy")
        self.strategies = strategies
        self.weights = weights or [1.0] * len(strategies)
        
        if len(self.weights) != len(strategies):
            raise ValueError("Number of weights must match number of strategies")
        
        # Normalize weights
        total_weight = sum(self.weights)
        if total_weight <= 0:
            raise ValueError("Total weight must be positive")
        self.weights = [w / total_weight for w in self.weights]
    
    def generate(self, random_state: random.Random, size: int) -> Any:
        """Select strategy based on weights and generate value"""
        chosen = random_state.choices(self.strategies, weights=self.weights)[0]
        return chosen.generate(random_state, size)
    
    def shrink(self, value: Any) -> Iterator[Any]:
        """Try shrinking with each strategy that could have produced this value"""
        for strategy in self.strategies:
            try:
                yield from strategy.shrink(value)
            except (TypeError, AttributeError, ValueError):
                continue  # Strategy cannot shrink this value type


class ConstantStrategy(Strategy):
    """Generate constant values"""
    
    def __init__(self, value: Any):
        self.value = value
    
    def generate(self, random_state: random.Random, size: int) -> Any:
        return self.value
    
    def shrink(self, value: Any) -> Iterator[Any]:
        return iter([])  # Constants cannot be shrunk


class MappedStrategy(Strategy):
    """Transform values from another strategy"""
    
    def __init__(self, base_strategy: Strategy, transform_func: Callable[[Any], Any]):
        self.base_strategy = base_strategy
        self.transform_func = transform_func
    
    def generate(self, random_state: random.Random, size: int) -> Any:
        base_value = self.base_strategy.generate(random_state, size)
        return self.transform_func(base_value)
    
    def shrink(self, value: Any) -> Iterator[Any]:
        # This is tricky - we need to reverse-map to shrink the base value
        # For now, we'll skip shrinking mapped strategies
        return iter([])


class FilteredStrategy(Strategy):
    """Filter values from another strategy based on a predicate"""
    
    def __init__(self, base_strategy: Strategy, predicate_func: Callable[[Any], bool]):
        self.base_strategy = base_strategy
        self.predicate_func = predicate_func
    
    def generate(self, random_state: random.Random, size: int) -> Any:
        max_attempts = 100
        for _ in range(max_attempts):
            candidate = self.base_strategy.generate(random_state, size)
            if self.predicate_func(candidate):
                return candidate
        
        raise RuntimeError(f"Could not generate valid value after {max_attempts} attempts")
    
    def shrink(self, value: Any) -> Iterator[Any]:
        for shrunk in self.base_strategy.shrink(value):
            if self.predicate_func(shrunk):
                yield shrunk


# Convenience functions for common strategies
def integers(min_value: int = -1000, max_value: int = 1000) -> IntegerStrategy:
    """Create an integer strategy"""
    return IntegerStrategy(min_value, max_value)

def floats(min_value: float = -1000.0, max_value: float = 1000.0) -> FloatStrategy:
    """Create a float strategy"""
    return FloatStrategy(min_value, max_value)

def text(alphabet: str = string.ascii_letters, 
         min_size: int = 0, max_size: int = 50) -> StringStrategy:
    """Create a string strategy"""
    return StringStrategy(alphabet, min_size, max_size)

def lists(element_strategy: Strategy, 
          min_size: int = 0, max_size: int = 50) -> ListStrategy:
    """Create a list strategy"""
    return ListStrategy(element_strategy, min_size, max_size)

def tuples(*element_strategies: Strategy) -> TupleStrategy:
    """Create a tuple strategy"""
    return TupleStrategy(*element_strategies)

def dictionaries(key_strategy: Strategy, value_strategy: Strategy,
                min_size: int = 0, max_size: int = 20) -> DictionaryStrategy:
    """Create a dictionary strategy"""
    return DictionaryStrategy(key_strategy, value_strategy, min_size, max_size)

def one_of(*strategies: Strategy, weights: Optional[List[float]] = None) -> OneOfStrategy:
    """Create a choice strategy"""
    return OneOfStrategy(*strategies, weights=weights)

def just(value: Any) -> ConstantStrategy:
    """Create a constant strategy"""
    return ConstantStrategy(value)
