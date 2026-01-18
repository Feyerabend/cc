
## Project Ideas

These projects are designed to help you explore and verify the functionality of the SECD machine
implementation. Each project tests specific instructions, builds on existing tests (1–9),
and provides a sample SECD program to implement in your `secd_machine.py`. The projects focus on
functional programming concepts like list manipulation, recursion, and higher-order functions,
ensuring comprehensive coverage of all instructions
(`ADD`, `SUB`, `DIV`, `EQ`, `LT`, `GT`, `MUL`, `POP`, `DUP`, `SWAP`, `CONS`, `CAR`, `CDR`, `NIL`,
`ATOM`, `SEL`, `JOIN`, `RTN`, `LD`, `LDC`, `LDF`, `AP`, `RAP`, `DUM`).
Instructions for integrating and debugging each project are included.


### Project 1: List Equality Check

*Description*: Create a function to compare two lists for equality (e.g., `[1, [2, []]]` vs. `[1, [2, []]]`
returns `True`). This project tests your ability to compare elements and traverse lists recursively.

*Why?*:
- Tests `EQ` for element comparison, which is underutilized in your current tests.
- Exercises `LT` and `GT` for potential ordering extensions.
- Reinforces list manipulation with `CAR`, `CDR`, and `ATOM`.

*Task*:
- Implement a recursive function that checks if two lists are equal by comparing their heads (`CAR`) and tails (`CDR`).
- If both lists are empty (`ATOM`), return `True`.
- If heads are equal (`EQ`), recurse on tails; otherwise, return `False`.
- Add a test case to compare `[1, [2, []]]` with itself.

*Sample SECD Program*:
- Define a function that takes a pair of lists `[[list1], [list2]]`.
- Use `EQ` to compare heads and `SEL` for branching.
- Add as Test 10 in your `secd_machine.py` under `if __name__ == "__main__":`.

```python
# Test 10: List equality
code10 = [
    'DUM',
    'LDF', [            # Equality function
        'LD', 0, 0,     # Load first list
        'ATOM',         # Check if empty
        'LD', 0, 1,     # Load second list
        'ATOM',         # Check if empty
        'EQ',           # Both empty?
        'SEL',
        ['LDC', True, 'RTN'],  # Both empty -> True
        [               # Else
            'LD', 0, 0, 'CAR',  # Head of first
            'LD', 0, 1, 'CAR',  # Head of second
            'EQ',           # Heads equal?
            'SEL',
            [               # Heads equal
                'LD', 0, 0, 'CDR',  # Tail of first
                'LD', 0, 1, 'CDR',  # Tail of second
                'LD', 1, 0,     # Load eq function
                'AP',           # Recurse
                'RTN'
            ],
            ['LDC', False, 'RTN'],  # Heads unequal
            'JOIN'
        ],
        'JOIN'
    ],
    'NIL',
    'CONS',
    'NIL', 'LDC', 2, 'CONS', 'LDC', 1, 'CONS',  # [1, [2, []]]
    'NIL', 'LDC', 2, 'CONS', 'LDC', 1, 'CONS',  # [1, [2, []]]
    'CONS',             # [[1, [2, []]], [1, [2, []]]]
    'RAP'
]
print("\nTest 10 (List equality):", secd_eval(code10))  # Output: True
```

*Instructions Tested*:
- `EQ`: Compares heads and checks if both lists are empty.
- `CAR`, `CDR`, `ATOM`: Traverses lists.
- `DUM`, `RAP`: Supports recursive calls.
- `SEL`, `JOIN`, `LDF`, `AP`, `LD`, `LDC`, `RTN`: Manages control flow and function application.

*Debugging Tips*:
- Run with `debug=True` to trace execution:
  ```python
  print("\nTest 10 (List equality):", secd_eval(code10, debug=True))
  ```
- Verify `EQ` pushes `True` for equal heads (e.g., `1 == 1`) and `False` otherwise.
- Check that `CAR` and `CDR` correctly extract heads and tails.
- Ensure `RAP` maintains the environment for recursion.
- If the output is incorrect, add debug prints in `EQ_command`:
  ```python
  print(f"EQ: comparing {a} == {b} -> {a == b}")
  ```

*Extension*:
- Modify to compare lists with `LT` or `GT` for lexicographic ordering.
- Test unequal lists (e.g., `[1, [2, []]]` vs. `[1, [3, []]]` → `False`).


### Project 2: Multiply List Elements

*Description*: Compute the product of all numbers in a list (e.g., `[2, [3, []]]` returns `6`).
This project tests multiplication and stack manipulation.

*Why?*:
- Tests `MUL`, which is untested in your current suite.
- Uses `POP` to demonstrate stack cleanup, ensuring stack discipline.
- Reinforces list traversal and recursion.

*Task*:
- Implement a recursive function that multiplies all elements in a list.
- If the list is empty (`ATOM`), return `1`; else, return `head * product(tail)`.
- Use `POP` to discard a duplicated value for testing.
- Add a test case for `[2, [3, []]]`.

*Sample SECD Program*:
- Define a function that processes a list.
- Use `MUL` for multiplication and `POP` after duplicating the result.
- Add as Test 11 in your `secd_machine.py`.

```python
# Test 11: List product
code11 = [
    'DUM',
    'LDF', [            # Product function
        'LD', 0, 0,     # Load list
        'ATOM',         # Check if empty
        'SEL',
        ['LDC', 1, 'RTN'],  # Empty -> 1
        [               # Else
            'LD', 0, 0, 'CAR',  # Head
            'LD', 0, 0, 'CDR',  # Tail
            'LD', 1, 0,     # Load product function
            'AP',           # Recurse
            'MUL',          # Multiply head * result
            'DUP',          # Duplicate result
            'POP',          # Discard duplicate
            'RTN'
        ],
        'JOIN'
    ],
    'NIL',
    'CONS',
    'NIL', 'LDC', 3, 'CONS', 'LDC', 2, 'CONS',  # [2, [3, []]]
    'RAP'
]
print("\nTest 11 (List product):", secd_eval(code11))  # Output: 6
```

*Instructions Tested*:
- `MUL`: Computes the product of elements.
- `POP`, `DUP`: Manipulates the stack (duplicate and discard).
- `CAR`, `CDR`, `ATOM`: Traverses the list.
- `DUM`, `RAP`, `SEL`, `JOIN`, `LDF`, `AP`, `LD`, `LDC`, `RTN`: Handles recursion and control flow.

*Debugging Tips*:
- Run with `debug=True` to verify stack operations:
  ```python
  print("\nTest 11 (List product):", secd_eval(code11, debug=True))
  ```
- Check that `MUL` correctly computes `2 * 3 = 6`.
- Verify `POP` removes the duplicated result, leaving the correct value.
- Ensure `CAR` extracts heads (e.g., `2`, then `3`).
- If the output is incorrect, add debug prints in `MUL_command`:
  ```python
  print(f"MUL: {a} * {b} = {a * b}")
  ```

*Extension*:
- Handle empty lists explicitly (`[]` → `1`).
- Add error handling for non-numeric elements using `SEL` and `EQ`.

### Project 3: Duplicate List Elements

*Description*: Create a new list with each element duplicated (e.g., `[1, [2, []]]` returns `[1, [1, [2, [2, []]]]]`).
This project tests stack manipulation and list construction.

*Why?*:
- Tests `DUP` extensively, which is untested in your current suite.
- Exercises complex list construction with `CONS` and `NIL`.
- Reinforces recursive list processing.

*Task*:
- Implement a recursive function that duplicates each element in a list.
- If the list is empty, return `[]`; else, prepend `[head, [head, ...]]` to the duplicated tail.
- Use `DUP` to duplicate the head element.
- Add a test case for `[1, [2, []]]`.

*Sample SECD Program*:
- Define a function that processes a list.
- Use `DUP` to duplicate heads and `CONS` to build the new list.
- Add as Test 12 in your `secd_machine.py`.

```python
# Test 12: Duplicate list elements
code12 = [
    'DUM',
    'LDF', [            # Duplicate function
        'LD', 0, 0,     # Load list
        'ATOM',         # Check if empty
        'SEL',
        ['NIL', 'RTN'], # Empty -> []
        [               # Else
            'LD', 0, 0, 'CAR',  # Head
            'DUP',          # Duplicate head
            'NIL',          # []
            'CONS',         # [head, []]
            'SWAP',         # [[head, []], head]
            'CONS',         # [head, [head, []]]
            'LD', 0, 0, 'CDR',  # Tail
            'LD', 1, 0,     # Load duplicate function
            'AP',           # Recurse
            'CONS',         # Prepend [head, [head, ...]]
            'RTN'
        ],
        'JOIN'
    ],
    'NIL',
    'CONS',
    'NIL', 'LDC', 2, 'CONS', 'LDC', 1, 'CONS',  # [1, [2, []]]
    'RAP'
]
print("\nTest 12 (List duplicate):", secd_eval(code12))  # Output: [1, [1, [2, [2, []]]]]
```

*Instructions Tested*:
- `DUP`: Duplicates each element.
- `CONS`, `NIL`, `CAR`, `CDR`, `ATOM`: Builds and traverses lists.
- `SWAP`, `DUM`, `RAP`, `SEL`, `JOIN`, `LDF`, `AP`, `LD`, `RTN`: Manages stack and control flow.

*Debugging Tips*:
- Run with `debug=True` to trace list construction:
  ```python
  print("\nTest 12 (List duplicate):", secd_eval(code12, debug=True))
  ```
- Verify `DUP` creates two copies of each head (e.g., `1`, `1`).
- Check that `CONS` builds `[head, [head, []]]` correctly.
- Ensure `RAP` applies the function to the tail.
- If the output is incorrect, add debug prints in `DUP_command`:
  ```python
  print(f"DUP: duplicating {stack[-1]}")
  ```

*Extension*:
- Modify to triplicate elements (e.g., `[1, [1, [1, ...]]]`).
- Test with an empty list (`[]` → `[]`).

### Integration and Verification

*How to Use These Projects*:
1. *Add to Your Script*:
   - Copy each test (`code10`, `code11`, `code12`) into the `if __name__ == "__main__":` block of your `secd_machine.py`.
   - Ensure your script includes all commands, including `LEQ` from previous tests.

2. *Run and Verify*:
   - Run the script to confirm outputs:
     - Test 10: `True`
     - Test 11: `6`
     - Test 12: `[1, [1, [2, [2, []]]]]`
   - Use debug mode to trace execution:
     ```python
     print("\nTest 10 (List equality):", secd_eval(code10, debug=True))
     ```

3. *Instruction Coverage*:
   - Combined with your Tests 1–9, these projects cover all instructions:
     - Tests 1–9: `ADD`, `SUB`, `DIV`, `SEL`, `JOIN`, `LDF`, `AP`, `SWAP`, `CONS`, `NIL`, `ATOM`, `CAR`, `CDR`, `DUM`, `RAP`, `LD`, `LDC`, `RTN`.
     - Tests 10–12: `EQ`, `LT`, `GT`, `MUL`, `POP`, `DUP`.
   - If you want to test `LT` or `GT` more explicitly, modify Project 1 to compare lists lexicographically.

4. *Handle Issues*:
   - If a test fails, check the debug output for stack, environment, and control states.
   - Add debug prints in commands (e.g., `EQ_command`, `MUL_command`) to trace values.
   - Verify environment setup in `RAP` and `LDF` for recursive calls.

*Additional Ideas*:
- *Map Function*: Implement a `map` function to apply a function (e.g., add 1) to each list element. Tests higher-order functions and `AP`.
- *Simple Lisp Interpreter*: Write a parser to translate Lisp-like expressions (e.g., `(add 2 3)`) into SECD code. Tests all instructions in a real-world context.
- *Tail Recursion Optimization*: Modify `RAP` to optimize tail-recursive calls, reducing stack usage. Tests `RTN` and `DUM`.

If you want to dive deeper, consider:
- Writing a front-end to translate Lisp-like code into SECD instructions.
- Optimising the machine for tail recursion or lazy evaluation.
- Comparing it with other abstract machines like the Krivine machine.
