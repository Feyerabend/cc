
## Build your own VM from a Object-Oriented or Functional model


### Object-Oriented model for a simple VM

When building an interpreter or a simple object-oriented virtual machine (VM),
there are several considerations to keep in mind for each. Here's a breakdown
of key factors to consider for both:

1.	Language syntax and semantics:
	* Define the syntax (grammar) of the language you want to interpret. This includes expressions,
      statements, and constructs.
	* Ensure you have a clear understanding of the semantics (meaning) behind each construct.

2.	Lexical analysis:
	* Implement a lexer (tokenizer) to break down source code into tokens. Tokens represent basic elements
      like keywords, identifiers, literals, and operators.

3.	Parsing:
	* Create a parser to construct an abstract syntax tree (AST) or similar structure from the tokens.
      The AST represents the hierarchical structure of the source code.

4.	Evaluation strategy:
	* Decide on an evaluation strategy: eager (immediate evaluation) vs. lazy (deferred evaluation).
	* Implement an evaluator that traverses the AST and performs computations based on the semantics of the language.

5.	Error handling:
	* Incorporate robust error handling to manage syntax errors, runtime errors, and semantic errors.
      Provide meaningful error messages to users.

6.	Environment management:
	* Implement an environment model to manage variable bindings, scopes, and functions. This often involves 
      creating a structure to represent the global and local environments.

7.	Built-in functions:
	* Define and implement built-in functions that are essential for the language’s usability, such as
      mathematical operations, string manipulation, and control flow.

8.	Support for data structures:
	* Consider how the language will handle various data types and structures (e.g., lists, dictionaries, sets)
      and implement them accordingly.

9.	Testing and debugging:
	* Create a suite of tests to validate the correctness of the interpreter. Include unit tests for individual
      components as well as integration tests for overall functionality.

#### Considerations for building a simple Object-Oriented VM

1.	Object model:
	* Define the object model, including concepts like classes, objects, inheritance, encapsulation,
      and polymorphism. Decide how objects and classes will be represented and managed.

2.	Memory management:
	* Implement a strategy for memory allocation and garbage collection. Consider how objects are
      created, referenced, and destroyed to avoid memory leaks.

3.	Method resolution:
	* Develop a method resolution mechanism to determine which method to invoke based on the object
      and the method name. This includes handling method overriding and dynamic dispatch.

4.	Bytecode or intermediate representation:
	* Decide whether to implement a bytecode compiler that translates the high-level object-oriented
      code into a lower-level representation for execution. This can improve performance.

5.	Inheritance and composition:
	* Implement support for inheritance (class-based or prototype-based) and composition, allowing
      for code reuse and modular design.

6.	Dynamic typing vs. static typing:
	* Decide on the typing system for the VM. Dynamic typing allows for greater flexibility, while
      static typing can provide safety and performance benefits.

7.	Reflection and introspection:
	* Consider implementing features that allow objects to inspect their own structure and behavior,
      enabling capabilities like serialization and dynamic method invocation.

8.	Concurrency:
	* If the VM is intended to support concurrent execution, consider how to handle threads,
      synchronization, and shared state among objects.

9.	Error handling:
	* Design a robust error-handling mechanism that accommodates runtime errors, type errors,
      and any specific exceptions related to object-oriented operations.

10.	Extensibility:
	* Consider how the VM can be extended in the future, allowing users to add new classes,
      methods, or even new language features without extensive changes to the existing codebase.

By taking these considerations into account, you can build a functional and extensible interpreter
or object-oriented VM that effectively serves its intended purpose and can be enhanced over time.


### Functional model for an interpreter

Building an interpreter for a functional language involves different design principles and considerations
compared to object-oriented and imperative languages. Functional languages emphasize immutability,
first-class functions, recursion, and higher-order functions. Below are some key considerations and
principles when building a functional language interpreter, alongside how they differ from object-oriented
approaches.


#### Considerations for building a functional language interpreter

1. First-class and higher-order functions:

* First-class functions: Functions are treated as first-class citizens, meaning they can be
  passed as arguments, returned from other functions, and assigned to variables.

* Higher-Order Functions: Your interpreter needs to support higher-order functions, which are
  functions that take other functions as arguments or return them.

Example:

```python
    def eval_lambda(self, expr):
        _, params, body = expr
        return (params, body, self.env)  # Returning a closure
```

2. Immutability:

* In functional languages, data is typically immutable. When you apply a function,
  it doesn’t modify its inputs. Instead, it returns new data.

* You must handle this immutability in your interpreter, making sure that variable
  assignments create new values rather than modify existing ones.

Note: You can avoid using mutable data structures internally, or implement functional
versions of lists, sets, and maps (such as persistent data structures).

3. Recursion over iteration:

* Functional languages use recursion as the primary form of repetition rather than loops (iteration).

* Tail recursion optimization is an important feature in many functional languages, allowing recursive
  calls to reuse stack frames and avoid stack overflow in deep recursions.

Example:

```python
    def eval(self, expr, env=None):
        # base case and recursive calls
        if isinstance(expr, list) and expr[0] == 'if':
            _, cond, true_branch, false_branch = expr
            return self.eval(true_branch if self.eval(cond) else false_branch)
        # tail-recursive calls or other recursion handling can be implemented here
```

4. Closures and lexical scoping:

* In functional languages, functions remember the environment in which they were created (closure) and carry it with them.

* Your interpreter must handle lexical scoping, where the variable bindings are resolved in the environment where the
  function was *defined*, not necessarily where it is *called*.

Example:

```python
    def eval_lambda(self, expr):
        _, params, body = expr
        return (params, body, self.env)  # closure includes environment
```

5. Function composition:

* A common pattern in functional programming is *function composition*, where two or more functions are combined to form a new function.

* Consider adding support for function composition and piping.

Example:

```lisp
  (define compose
    (lambda (f g)
      (lambda (x)
        (f (g x)))))
```

6. Pure functions:

* Functional languages emphasize pure functions, which always produce the same output for the same input and have no side effects.

* Your interpreter should allow pure functions to be defined and used freely. You might also enforce functional purity by limiting
  the use of mutable state and side effects like I/O.


7. Lazy evaluation (optional):

* Some functional languages like Haskell use lazy evaluation, where expressions are not evaluated until their results are needed.

* This requires the interpreter to defer evaluation of expressions and only compute them when they are actually used
  (i.e., lazy evaluation of function arguments).

Example:

```python
    def eval(self, expr):
        if isinstance(expr, LazyExpression):
            return expr.force()  # force evaluation of lazy expressions
        # other eval cases for normal expressions
```


8. Higher-order data structures:

* Functional languages often manipulate higher-order data structures, such as lists or trees, through functional transformations (e.g. map, filter, reduce).

* Implement built-in support for these transformations or provide libraries with these features.

Example:

```python
    def _map(self, func, iterable):
        return [self.apply(func, [item]) for item in iterable]
```

#### Example: functional Language in pseudo-code:

Below is a simplified interpreter (evaluator) workflow for a functional language:

```
FUNCTION eval(expr, env):
    IF expr is a constant (number, string):
        RETURN expr
    ELSE IF expr is a variable (symbol):
        RETURN env.get(expr)  # Lookup in the environment
    ELSE IF expr is a list:
        LET op = expr[0]  # First element is the operation
        LET args = expr[1:]  # Remaining elements are arguments
        IF op is 'lambda':
            RETURN (args[0], args[1], env)  # Create a closure with params, body, and env
        ELSE IF op is 'define':
            env.set(args[0], eval(args[1], env))  # Define a new variable
            RETURN None
        ELSE:
            LET func = eval(op, env)  # Evaluate the function
            LET evaluated_args = [eval(arg, env) for arg in args]  # Evaluate each argument
            RETURN apply(func, evaluated_args)

FUNCTION apply(func, args):
    IF func is a closure:
        LET (params, body, closure_env) = func
        LET new_env = extend(closure_env, params, args)  # Bind arguments to parameters
        RETURN eval(body, new_env)  # Evaluate the body of the function
    ELSE:
        RETURN func(args)  # Apply built-in functions

ENVIRONMENT = GlobalEnvironment()
```

```
    # Sample Code
    1. eval(['define', 'add', ['lambda', ['x', 'y'], ['+', 'x', 'y']]], ENVIRONMENT)
    2. eval(['add', 2, 3], ENVIRONMENT)
```

#### Considerations for building an Object-Oriented VM

In contrast, when building an object-oriented VM, you focus on managing objects, classes
inheritance, and method resolution. Object-oriented VMs typically support dynamic dispatch,
method overriding, and encapsulation.

* *Object representation*: Objects are instances of classes, and they have fields and methods.
* *Class hierarchy*: Implement inheritance and ensure that objects can inherit fields and methods from parent classes.
* *Method dispatch*: Use dynamic dispatch to select the correct method to invoke at runtime based on the class of the object.
* *Memory management*: Allocate memory for objects and ensure proper garbage collection.

#### Summary Comparison:

|Aspect|	Functional Interpreter|	Object-Oriented VM|
|---|---|---|
|Core Constructs|	Functions, recursion, immutability|	Objects, classes, inheritance, dynamic dispatch|
|Main Evaluation|	Function application|	Method invocation|
|Memory Management|	Closures and function environments|	Objects, method tables, and fields||
|Core Paradigm	|First-class functions, higher-order functions|	Encapsulation, inheritance, polymorphism
|Key Language Features|	Pure functions, recursion, closures, tail calls|	Method resolution, memory allocation for objects|
|Control Structures|	Recursion and conditionals|	Method calls, dynamic dispatch|

Each approach requires different underlying mechanisms and features, and both offer unique strengths for different types of programming languages.
