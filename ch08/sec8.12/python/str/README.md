
> [!WARNING]
> The scripts requires besides Hypothesis, also installation of pytest.

## PBT: Comparations

These scripts showcase the difference between traditional example-based testing and
property-based testing:

- *Traditional testing*: You manually write specific test cases with known inputs/outputs
- *Property-based testing*: You define mathematical properties that should always hold true,
  and Hypothesis automatically generates hundreds of random test cases to verify these properties


### Properties Being Tested

#### 1. *Associativity* (`test_string_concatenation_associativity`)
```python
(a + b) + c == a + (b + c)
```
This tests that string concatenation is *associative*--the grouping of operations doesn't matter.
Whether you concatenate "hello" + "world" first, then add "!", or concatenate "world" + "!"
first, then prepend "hello", you get the same result.

#### 2. *Identity Element* (`test_string_concatenation_identity`)
```python
s + "" == s  and  "" + s == s
```
This verifies that the empty string acts as an *identity* element--adding nothing to a string
leaves it unchanged, regardless of whether you add the empty string on the left or right.

#### 3. *Length Additivity* (`test_string_concatenation_length`)
```python
len(a + b) == len(a) + len(b)
```
This ensures that when you *concatenate* two strings, the resulting length equals the sum of
the individual lengths--no characters are lost or mysteriously added.

#### 4. *Involution Property* (`test_string_reverse_twice`)
```python
s[::-1][::-1] == s
```
This tests that *reversing* a string twice returns the original string--reverse is its
own *inverse* operation.

#### 5. *Substring Preservation* (`test_string_substring_property`)
```python
a in (a + b)  and  b in (a + b)
```
This verifies that when you *concatenate* two strings, both original strings *remain* as
substrings in the result.


### How Hypothesis Works

The `@given` decorator tells Hypothesis to:
1. Generate random strings using `st.text()`
2. Run the test function hundreds of times with different random inputs
3. If any generated input causes the assertion to fail, Hypothesis will
   try to find the smallest/simplest input that demonstrates the failure
4. Report both the failing case and attempt to "shrink" it to a minimal example

These scripts demonstrate several important concepts:

*Mathematical Rigour in Programming*: They show how fundamental algebraic properties
(associativity, identity, etc.) apply to everyday programming operations like string
manipulation.

*Automated Edge Case Discovery*: Instead of trying to think of all possible edge cases
manually, Hypothesis explores the input space automatically, potentially finding cases
you'd never consider (empty strings, Unicode characters, very long strings, etc.).

*Specification Through Properties*: Rather than testing specific examples, you're defining
the mathematical laws that your code should obey, creating a more complete and robust
specification.

*Confidence Through Volume*: By running hundreds of randomized tests, you gain much
higher confidence that your code works correctly across the entire domain of possible inputs.


### Comparation: Hypothesis and classic testing approaches

Below shows how property-based testing can be more thorough and require less manual
effort to achieve better coverage of the problem space.

__1. Associativity__

Hypothesis (property-based):
```python
from hypothesis import given, strategies as st

@given(st.text(), st.text(), st.text())
def test_string_concatenation_associativity(a, b, c):
    assert (a + b) + c == a + (b + c)
```
Classic (example-based):
```python
def test_string_concatenation_associativity_classic():
    cases = [
        ("a", "b", "c"),
        ("", "foo", "bar"),
        ("x", "", "y"),
        ("", "", ""),
        ("hello", " ", "world")
    ]
    for a, b, c in cases:
        assert (a + b) + c == a + (b + c)
```



__2. Identity (empty string)__

Hypothesis:
```python
@given(st.text())
def test_string_concatenation_identity(s):
    assert s + "" == s
    assert "" + s == s
```
Classic:
```python
def test_string_concatenation_identity_classic():
    cases = ["", "a", "foo", " "]
    for s in cases:
        assert s + "" == s
        assert "" + s == s
```



__3. Length additivity__

Hypothesis:
```python
@given(st.text(), st.text())
def test_string_concatenation_length(a, b):
    assert len(a + b) == len(a) + len(b)
```
Classic:
```python
def test_string_concatenation_length_classic():
    cases = [
        ("a", "b"),
        ("", "foo"),
        ("bar", ""),
        ("hello", "world")
    ]
    for a, b in cases:
        assert len(a + b) == len(a) + len(b)
```



__4. Double reversal__

Hypothesis:
```python
@given(st.text())
def test_string_reverse_twice(s):
    assert s[::-1][::-1] == s
```
Classic:
```python
def test_string_reverse_twice_classic():
    cases = ["", "a", "abc", "hello world"]
    for s in cases:
        assert s[::-1][::-1] == s
```



__5. Substring property__

Hypothesis:
```python
@given(st.text(), st.text())
def test_string_substring_property(a, b):
    concatenated = a + b
    assert a in concatenated
    assert b in concatenated
```
Classic:
```python
def test_string_substring_property_classic():
    cases = [
        ("a", "b"),
        ("", "foo"),
        ("bar", ""),
        ("hello", "world")
    ]
    for a, b in cases:
        concatenated = a + b
        assert a in concatenated
        assert b in concatenated
```



*Hypothesis*: generates many random cases automatically, potentially uncovering edge
cases you didn’t think of.

*Classic*: you pick a finite set of examples manually, so some edge cases may be missed.

Both use assert to check correctness.
