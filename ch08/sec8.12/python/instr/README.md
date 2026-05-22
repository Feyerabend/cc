
## Example of Property-Based Test

> *Sometime in the mid 1980s, I taught a BASIC programming class for beginners. Unfortunately, I got
> sidetracked early on into logic and discussions about how logic could aid in specifying functions.
> If I remember correctly, we used the Commodore VIC-20 or it might have been ABC80, and an
> implementation of the INSTR function that I thought could help with understanding programming.
> The students weren’t very happy, so we eventually switched to simple games and easy examples
> to keep things engaging. My specification was also very provisional, not close to what came
> in later discovery.*

Well, what I more specifically tried was a first-order specification of a function INSTR.

In BASIC, `INSTR(start, string1, string2)` returns the position (1-based) of the first occurrence
of `string2` within `string1` starting from position `start`. If `string2` is not found, it returns `0`.


#### Function: INSTR

*INSTR is used to find the position of a specific sequence of characters (the substring) within a larger string.*

*Return Value:*
- Positive Integer: If the substring is found, INSTR returns the index (starting from 1)
  of the first character of the substring's first occurrence within the larger string. 
- Zero (0): If the substring is not found in the string. 
- Null: In some implementations, if either the string or the substring is null, the function might return null. 

*Parameters:*
- The INSTR function typically takes two or more string arguments: the string to search
  within (the "main" string) and the substring to search for. 
- Optionally, it may take a starting position to begin the search and a comparison type
  (e.g., binary or text). 


#### Specification

Let:

- $s$ and $t$ be strings
- $|s|$ and $|t|$ their lengths
- $\text{start} \in \mathbb{N}$, $1 \leq \text{start} \leq |s| + 1$
- $\text{instr}(\text{start}, s, t) = r \in \mathbb{N}$

The definition of $r$ is:

```
r = 0 ⇔ ¬∃ i ∈ ℕ, start ≤ i ≤ |s| - |t| + 1 such that
          ∀ j ∈ [0, |t|-1], s[i + j] = t[j + 1]

r ≠ 0 ⇔ ∃ i ∈ ℕ, start ≤ i ≤ |s| - |t| + 1 such that
          ∀ j ∈ [0, |t|-1], s[i + j] = t[j + 1]
          ∧
          ∀ k ∈ ℕ, (start ≤ k < i) ⇒ ∃ j ∈ [0, |t|-1], s[k + j] ≠ t[j + 1]
```

*Explanation:*

- If $r = 0$, no substring of $s$ starting at or after $\text{start}$ matches $t$.
- If $r \neq 0$, then $r$ is the smallest index $i$ such that the substring of $s$
  starting at $i$ equals $t$.
- The indices are 1-based.
- The notation $s[x]$ means the character at position $x$ in $s$.


#### Property-Based Test of INSTR function

```python
def instr(start, string1, string2):
    """
    Find the position of string2 within string1, starting from position start.
    
    Args:
        start: 1-based starting position to begin search
        string1: string to search in
        string2: substring to search for
    
    Returns:
        1-based position of first occurrence of string2 in string1 at or after start,
        or 0 if not found
    """
    # Handle edge cases
    if start < 1:
        start = 1
    
    # Check bounds first, before handling empty string2
    if start > len(string1) + 1:
        return 0
    
    # Handle empty string2 - but only if start is within bounds
    if string2 == "":
        return start
    
    # Convert to 0-based indexing for Python string operations
    start_idx = start - 1
    
    # Search for substring starting from start position
    pos = string1.find(string2, start_idx)
    
    # Convert back to 1-based indexing, or return 0 if not found
    return pos + 1 if pos != -1 else 0


# Property-based tests using Hypothesis
from hypothesis import given, strategies as st

@given(st.integers(min_value=1), st.text(), st.text())
def test_instr_properties(start, string1, string2):
    # Ensure start is valid (or handle in function)
    start = max(1, start)
    pos = instr(start, string1, string2)

    # Property 1: empty string2 (only when start is in bounds)
    if string2 == "" and start <= len(string1) + 1:
        assert pos == start

    # Property 2: start out of bounds
    if start > len(string1) + 1:
        assert pos == 0

    # Property 3: substring match at pos
    if pos != 0:
        # pos is 1-based, adjust for Python 0-based indexing
        assert string1[pos-1 : pos-1 + len(string2)] == string2

    # Property 4: pos >= start or zero
    assert pos == 0 or pos >= start


# Additional unit tests for specific cases
def test_instr_examples():
    """Test specific examples to verify behavior"""
    # Basic substring search
    assert instr(1, "hello world", "world") == 7
    assert instr(1, "hello world", "hello") == 1
    assert instr(1, "hello world", "xyz") == 0
    
    # Starting position tests
    assert instr(3, "hello hello", "hello") == 7
    assert instr(8, "hello world", "world") == 0
    
    # Edge cases
    assert instr(1, "", "test") == 0
    assert instr(1, "test", "") == 1
    assert instr(5, "test", "") == 5  # Position 5 is valid (at end of 4-char string)
    assert instr(6, "test", "") == 0  # Position 6 is out of bounds
    assert instr(10, "short", "test") == 0
    
    # Empty string edge cases
    assert instr(1, "", "") == 1
    assert instr(2, "", "") == 0  # This was the failing case
    
    # Case sensitivity
    assert instr(1, "Hello", "hello") == 0
    
    print("All unit tests passed!")


if __name__ == "__main__":
    # Run unit tests
    test_instr_examples()
    
    # Run property-based tests
    print("Running property-based tests...")
    test_instr_properties()
    print("Property-based tests completed!")
    
    # Interactive examples
    print("\nExample usage:")
    print(f'instr(1, "hello world", "world") = {instr(1, "hello world", "world")}')
    print(f'instr(1, "hello world", "hello") = {instr(1, "hello world", "hello")}')
    print(f'instr(7, "hello world", "world") = {instr(7, "hello world", "world")}')
    print(f'instr(8, "hello world", "world") = {instr(8, "hello world", "world")}')
    print(f'instr(5, "test", "") = {instr(5, "test", "")}')  # Should be 5
    print(f'instr(2, "", "") = {instr(2, "", "")}')  # The failing case
```

