from typing import TypeVar, Callable, Any
from functools import wraps

T = TypeVar('T')

class RefinementError(TypeError):
    """Raised when a refinement type constraint is violated"""
    pass

class Refined:
    """A refinement type wrapper"""
    def __init__(self, base_type: type, predicate: Callable[[Any], bool], 
                 description: str = ""):
        self.base_type = base_type
        self.predicate = predicate
        self.description = description
    
    def check(self, value: Any) -> Any:
        """Validate that value satisfies the refinement"""
        if not isinstance(value, self.base_type):
            raise RefinementError(
                f"Expected {self.base_type.__name__}, got {type(value).__name__}"
            )
        if not self.predicate(value):
            desc = self.description or "predicate"
            raise RefinementError(
                f"Value {value} does not satisfy {desc}"
            )
        return value
    
    def __repr__(self):
        desc = self.description or "custom predicate"
        return f"{{x: {self.base_type.__name__} | {desc}}}"

## Common refinement types
Positive = Refined(int, lambda x: x > 0, "x > 0")
NonZero = Refined(int, lambda x: x != 0, "x != 0")
NonEmpty = Refined(str, lambda x: len(x) > 0, "len(x) > 0")
Percentage = Refined(float, lambda x: 0 <= x <= 100, "0 <= x <= 100")

def refined(*param_refinements, return_refinement=None):
    """Decorator to add refinement type checking to functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ## Check parameters
            for i, (arg, refinement) in enumerate(zip(args, param_refinements)):
                if refinement is not None:
                    try:
                        refinement.check(arg)
                    except RefinementError as e:
                        raise RefinementError(
                            f"Parameter {i} of {func.__name__}: {e}"
                        )
            
            ## Call function
            result = func(*args, *kwargs)
            
            ## Check return value
            if return_refinement is not None:
                try:
                    return_refinement.check(result)
                except RefinementError as e:
                    raise RefinementError(
                        f"Return value of {func.__name__}: {e}"
                    )
            
            return result
        return wrapper
    return decorator

## Example usage
@refined(Positive, NonZero, return_refinement=Positive)
def safe_divide(numerator: int, denominator: int) -> int:
    """Divide two positive integers, denominator must be non-zero"""
    return numerator // denominator

@refined(NonEmpty, return_refinement=Positive)
def string_length(s: str) -> int:
    """Get length of non-empty string"""
    return len(s)

## Demonstration
if __name__ == "__main__":
    print("Testing refinement types...")
    
    ## Valid calls
    print(f"safe_divide(10, 2) = {safe_divide(10, 2)}")
    print(f"string_length('hello') = {string_length('hello')}")
    
    ## Invalid calls - these will raise RefinementError
    try:
        safe_divide(10, 0)  ## Violates NonZero
    except RefinementError as e:
        print(f"Error: {e}")
    
    try:
        safe_divide(-5, 2)  ## Violates Positive
    except RefinementError as e:
        print(f"Error: {e}")
    
    try:
        string_length("")  ## Violates NonEmpty
    except RefinementError as e:
        print(f"Error: {e}")
