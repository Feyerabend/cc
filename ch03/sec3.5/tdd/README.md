
## TDD Journey: From Failures to Success

This is a demonstration of Test-Driven Development (TDD) in action. We start with an
test suite that defines ambitious requirements, then systematically fix implementation
issues revealed by failing tests.

The samples are from [basic](./../basic/) testing.

Our point of departure is [tdd](./01/tdd.py), tests before code.
Now testing begins .. the sequence of events in this journey are:
- [First attempt](./01/) and failure
- [Second attempt](./02/), and failure, but
- [Third attempt](./03/) which is successful


### *Failure #1: Negative Number Conversion*
```
FAIL: test_add_edge_cases - AssertionError: '-123' != -123
```

*The Problem:*
- Original code: `value.isdigit()` only detects positive numbers
- `"-123".isdigit()` returns `False`, so negative numbers stayed as strings
- Test expected: `"-123"` → `-123` (integer)
- Reality: `"-123"` → `"-123"` (string)

*The Fix:*
Replaced simple `isdigit()` check with `try/except int()` conversion:
```python
# Before: Only positive numbers converted
if isinstance(value, str) and value.isdigit():
    value = int(value)

# After: Handles positive, negative, and zero
try:
    if value.strip() and not ('.' in value or 'e' in value.lower() or '+' in value):
        value = int(value)
except ValueError:
    pass
```

*The Learning:* Simple string methods like `isdigit()` have limitations. The test revealed this gap.


### *Failure #2: Whitespace Edge Cases*
```
FAIL: test_type_coercion_edge_cases - AssertionError: 123 != '  123  '
```

*The Problem:*
- Our "fixed" code converted `"  123  "` to `123` 
- Test expected it to remain as `"  123  "` (string with spaces)
- The test defined a business rule: *strings with whitespace should NOT be converted*

*The Fix:*
Added whitespace validation to the conversion logic:
```python
# Added this condition
if (value == value.strip() and  # No leading/trailing whitespace
    value.strip() and           # Not empty
    not ('.' in value or 'e' in value.lower() or '+' in value)):
```

*The Learning:* Tests don't just catch bugs—they define precise business logic.
The test specified exactly when conversion should happen.


### *The TDD Cycle in Action*

#### *RED Phase* (Write Failing Tests)
- Created comprehensive test suite with edge cases
- Tests failed initially because features weren't implemented
- Failures revealed gaps in existing implementation

#### *GREEN Phase* (Make Tests Pass)
- Fixed negative number handling
- Fixed whitespace edge cases  
- Implemented just enough code to pass the tests

#### *REFACTOR Phase* (Improve Code Quality)
- Moved from brittle `isdigit()` to robust `try/except`
- Created clear, readable conversion logic
- Maintained all test passes while improving code


### *Key TDD Insights from This Journey*

#### 1. *Tests as Specifications*
The tests weren't just checking code—they were *defining requirements*:
- "Negative numbers should convert to integers"
- "Strings with whitespace should remain strings"
- "Decimal numbers should remain strings"

#### 2. *Failures Are Valuable*
Each failure taught us something:
- *Failure #1:* Revealed incomplete numeric handling
- *Failure #2:* Clarified exact business rules for conversion

#### 3. *Incremental Improvement*
We didn't rewrite everything at once:
- Fixed one failing test at a time
- Each fix was minimal and targeted
- Built confidence with each green test

#### 4. *Tests Drive Design*
The tests shaped our implementation:
- Forced us to think about edge cases upfront
- Defined clear boundaries for behaviour
- Prevented over-engineering


### *The Final Result*

#### *Before TDD:*
```python
# Simple, but limited
if isinstance(value, str) and value.isdigit():
    value = int(value)
```

#### *After TDD:*
```python
# Robust, handles all edge cases
if isinstance(value, str):
    try:
        if (value == value.strip() and 
            value.strip() and 
            not ('.' in value or 'e' in value.lower() or '+' in value)):
            value = int(value)
    except ValueError:
        pass
```


### *Why This Journey Exemplifies Good TDD*

1. *Tests First:* We wrote comprehensive tests before implementation
2. *Red-Green-Refactor:* Classic TDD cycle followed naturally  
3. *Edge Cases:* Tests covered scenarios we might miss coding-first
4. *Clear Requirements:* Tests defined exact expected behaviour
5. *Confidence:* Each fix was validated immediately
6. *Documentation:* Tests serve as living examples of how code should work


### Summary

In this TDD reasoning, those "failures" weren't bugs--they were *discovery*.
Each failing test revealed something we didn't know we needed to handle.
This is TDD at its best: letting tests guide you to better,
more robust solutions than you would have built without them.

The journey from red to green wasn't just about fixing code, it was about
understanding requirements deeply and building exactly what was needed,
no more, no less. Nonetheless.

