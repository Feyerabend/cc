
## Types

In programming, "types" define the kind of data a variable can hold and determine the operations that
can be performed on it. Types can range from simple data types like integers and floats to more complex
structures like lists or custom objects. For example:
- Integers (int) are used for whole numbers.
- Floats (float) are used for decimal numbers.
- Strings (str) are used for text.
- Booleans (bool) are used for true/false values.
- Lists (list) are used to store collections of items.


### What Are Types?

Types ensure that operations performed on data are meaningful. For instance, adding two integers or two
floats makes sense and produces a numerical result. However, adding an integer to a string would lead
to an error because it doesn’t make logical sense.

In the context of the VM, operations like ADD, SUB, MUL, and DIV expect numeric types (either int or float).
Operations like CAT expect lists or strings, and CAR and CDR expect lists. By enforcing type checks, we
ensure that operations don't produce unexpected errors.

### Static vs. Dynamic Typing

- Static Typing: In languages like C++ or Java, types are checked during compile-time. This means that
type errors are caught before running the program.

- Dynamic Typing: In dynamically typed languages like Python or this VM, types are checked at runtime.
The types are not fixed, and the program can work with different types at different points in execution.

Here in this VM we are dealing with dynamic typing because we don’t enforce type constraints during
*compilation* but only during *execution*.


### Type Safety

Type safety ensures that operations are only performed on valid types. For instance:
- The ADD instruction checks if both operands are numbers (either int or float).
- If you try to add a string to a number, the VM will raise an error because this operation is not type-safe.

Currently, the VM is *not strictly* type-safe. It checks types dynamically and throws exceptions if
operations are attempted with invalid types (e.g. adding a string to a number), but it does not
automatically enforce type constraints across the entire execution.


### Type Coercion

Some languages automatically convert types when necessary, a concept known as type coercion. For example,
in Python, dividing an integer by a float would automatically convert the integer to a float.

Here, type coercion is partially implemented. The _type_coerce function is designed to convert an integer
to a float if needed for operations like division, but it does not handle all possible coercions.
The _type_coerce_bool function is used for coercing integer values to booleans, where 0 becomes False
and any non-zero value becomes True.


### Type Hierarchy

Types can be organized into a hierarchy, which helps with polymorphism and inheritance. For example:
- Numbers might be a superclass for int and float types. This hierarchy allows operations that can work
on any number, whether it’s an integer or a floating-point number.

In this VM, you can see a simplified type hierarchy for numeric operations:
- The ADD, SUB, MUL, and DIV operations expect either int or float, so the VM can treat them similarly
due to their shared numeric nature.


### Type Annotations

In modern languages like Python, type annotations are used to specify the expected types of variables,
parameters, and return values. These annotations help developers understand how a function or variable
is supposed to be used and can also be used for static analysis tools to catch errors before runtime.

This VM doesn’t use type annotations, but it does include type checks via the _check_type and _type_coerce
functions, which ensure that only valid types are used in operations like addition, subtraction, etc.
These checks could be seen as a form of "runtime type annotation" because they define what types are
allowed for certain operations.


### Type Errors

The VM raises errors in various cases where types don’t align with the expected operations. Some examples
include:
- Adding a string and a number: If this happens in the ADD instruction, a TypeError will be raised because
  the operation doesn’t make sense for mismatched types.
- Division by zero: The VM explicitly checks for division by zero in the DIV instruction and raises an
  error if it occurs.
- Accessing a non-existent index in a list: If you try to access an index in a list that doesn’t exist,
  the NTH or IDX instructions will raise an exception.


### Type-Specific Instructions

Several instructions in the VM are type-specific. Here’s how they break down:
- ADD, SUB, MUL, DIV: These operations work on numeric types (int and float). The _check_type function
  ensures that both operands are valid for the operation before performing it.
- CAT: This instruction works with lists and strings. It concatenates two lists or strings.
- CAR, CDR: These instructions work with lists. They return the first element (CAR) or the rest of the
list (CDR).


### The Code

1. Type Checking in Operations:
The VM has a _check_type method that checks if a value matches the expected type for each operation.
This is important to avoid invalid operations, such as adding incompatible types.

```python
def _check_type(self, value, expected_type, operation):
    if isinstance(value, expected_type):
        return value
    self._type_coerce(value, expected_type, operation)
```

For instance, in the ADD instruction, it checks if both operands are either int or float before adding them:

```python
if instr == 'ADD':
    if self.stack:
        b = self.stack.pop()
        a = self.stack.pop()
        self._check_type(a, (int, float), 'ADD')
        self._check_type(b, (int, float), 'ADD')
```

2. Coercing Types:
If the operand types don’t match, the VM can coerce types. For example, when adding two numbers,
it will ensure they are both numbers (either int or float). This is done through the _type_coerce
function, which coerces integers to floats where necessary.

```python
def _type_coerce(self, value, expected_type, operation):
    if expected_type == (int, float):
        if isinstance(value, int):
            return float(value)  # Coerce int to float if expected type is float
        elif isinstance(value, float):
            return value
        else:
            raise TypeError(f"Invalid type for {operation}: expected {expected_type}, got {type(value)}")
```


3. Specific Instructions like CAR and CDR:
The VM also has type-specific instructions for lists. For example, CAR and CDR are designed to work with lists.
These instructions will check if the stack contains a list and whether it’s non-empty.

```python
elif instr == 'CAR':
    lst = self.stack.pop() if self.stack else None
    if isinstance(lst, list) and len(lst) > 0:
        self.stack.append(lst[0])
    else:
        raise Exception("Expected a non-empty list")
```


### Examples

1. Defining a Function:
   - How a function is defined with a specific number of arguments and bytecode.
   - Example:
     ```python
     vm.define_function('add_two', 2, ['LOAD', 'ARG1', 'LOAD', 'ARG2', 'ADD', 'RET'])
     ```

2. Type Checking in Operations:
   - How `ADD` works with numbers but fails with strings.
   - Example:
     ```python
     vm.execute(['SET', 5, 'SET', 3, 'ADD', 'PRINT'])  # Works
     vm.execute(['SET', 'hello', 'SET', 3, 'ADD', 'PRINT'])  # Fails
     ```

3. Environment and Closures:
   - How closures capture the environment at the time of creation and how types are preserved in the environment.
   - Example:
     ```python
     vm.execute(['SET', 10, 'STORE', 'x', 'CREATE_CLOSURE', 'add_two', 'CALL', 'add_two', 2, 3])
     ```

4. Type-Specific Instructions:
   - How `CAR` and `CDR` work with lists but fail with other types.
   - Example:
     ```python
     vm.execute(['SET', [1, 2, 3], 'CAR', 'PRINT'])  # Works
     vm.execute(['SET', 5, 'CAR', 'PRINT'])  # Fails
     ```


### Summary

Types in this VM play a role in ensuring that operations are meaningful and errors are avoided. While the
VM is dynamically typed and doesn’t have the strict static typing of other languages, it implements type
checking at runtime to ensure that operations like adding numbers or manipulating lists are valid. It also
uses type coercion and type-specific instructions to handle cases where types might be compatible, like
converting integers to floats or concatenating lists.
