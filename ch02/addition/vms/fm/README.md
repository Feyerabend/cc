
## Project

*Enhance this interpreter, transforming it into a "functional machine" inspired by 'Lisp',
and experiment with various samples to explore its capabilities further.*

*Prerequisites: A basic understanding of functional programming concepts.*

### Overview

The interpreter is designed to evaluate basic Lisp expressions, allowing users to define
variables, create functions, and perform arithmetic operations.

#### Key components

1. LispError: A custom exception class used to signal errors in the 'Lisp' interpreter.
2. Environment: A class representing a variable environment that supports variable bindings.
   It can have parent environments, enabling nested scopes.
3. Lisp: The main class for the interpreter, which initializes the environment and built-in
   functions, and includes methods for evaluating expressions.

#### Classes

* LispError: This class inherits from Python's built-in Exception class and is used for
  handling errors specific to the Lisp interpreter.

```python
class LispError(Exception):
    pass
```

* Environment: This class maintains a dictionary of variable bindings and can access parent
  environments for variable lookup.

```python
class Environment:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def set(self, name, value):
        self.bindings[name] = value

    def get(self, name):
        if name in self.bindings:
            return self.bindings[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise LispError(f"Undefined variable: {name}")
```

* Lisp: This class is responsible for evaluating Lisp expressions. It includes methods for
  defining variables and functions, performing arithmetic, and handling user-defined functions.

```python
class Lisp:
    def __init__(self):
        self.env = Environment()  # global environment
        self._initialize_builtins()  # init built-in functions

    def _initialize_builtins(self):
        self.env.set('+', self._add)
        self.env.set('-', self._subtract)
        self.env.set('*', self._multiply)
        self.env.set('/', self._divide)

    # other methods ..
```

#### Evaluation

The eval method processes different types of expressions:

* Numeric literals: Returns the value directly.
* Variables: Retrieves the value from the environment.
* Function definitions: Evaluates a define expression to bind a name to a function or variable.
* Lambda functions: Creates a new function and returns it as a closure.
* Function calls: Evaluates the function and its arguments, then applies the function.

#### Example

The main program demonstrates defining and calling functions in the interpreter:

```python
if __name__ == '__main__':
    lisp = Lisp()

    # define simple function
    lisp.eval(['define', 'add', ['lambda', ['x', 'y'], ['+', 'x', 'y']]])

    # call add function
    result = lisp.eval(['add', 3, 5])
    print(f"3 + 5 = {result}")  # output: 3 + 5 = 8

    # define function that adds 10 to input
    lisp.eval(['define', 'add_ten', ['lambda', ['x'], ['+', 'x', 10]]])

    # call add_ten function
    result = lisp.eval(['add_ten', 5])
    print(f"5 + 10 = {result}")  # output: 5 + 10 = 15
```

#### Pseudo code

The following pseudo code illustrates how the interpreter processes an example:

1. Define the add function:

```lisp
    (define add (lambda (x y) (+ x y)))
```

2. Call add function:

```lisp
    (add 3 5)
```

3. Execution steps:
* Evaluate add: Check if it's defined, retrieve its closure.
* Evaluate arguments 3 and 5.
* Call add function:
* Create new environment for function call.
* Bind x to 3 and y to 5.
* Evaluate the body (+ x y) in the new environment, which computes 3 + 5.

4. Output:

```
    3 + 5 = 8
```

5. Define add_ten function:

```lisp
    (define add_ten (lambda (x) (+ x 10)))
```

6. Call add_ten function:

```lisp
    (add_ten 5)
```

7. Execution steps:
* Evaluate add_ten: Retrieve its closure.
* Evaluate argument 5.
* Call add_ten function:
* Create new environment for function call.
* Bind x to 5.
* Evaluate the body (+ x 10) in the new environment, which computes 5 + 10.

8. Output:

```
    5 + 10 = 15
```


### Conclusion

This simple 'Lisp' interpreter provides a foundation for understanding some of
interpreters and functional programming concepts. You can enhance and expand this
interpreter by adding more built-in functions, control flow constructs, error
handling, and additional features like list manipulation or recursion.
