
## Vtable and Projects

Vtables, or virtual method tables, are described in the sources as a behind-the-scenes mechanism
used in object-oriented programming (OOP) to enable *dynamic polymorphism*. This allows objects of
different types to respond uniquely to the same method call.

In essence, vtables serve as a link that enables objects to exhibit unique behaviours while adhering
to a common interface defined by their class hierarchy. They bridge the gap between the static
nature of code and the dynamic behaviour of objects at runtime.


### Easier Projects

1. Add Support for Integer Variables and Arithmetic
   - *Description*: Extend the first compiler to support integer variables and basic arithmetic operations
     (e.g. `+`, `-`, `*`, `/`) within methods. For example, allow syntax like `def calculate() { print(5 + 3); }`.
   - *Learning Goals*: Understand tokenization, parsing expressions, and generating C code for arithmetic.
   - *Challenge*: Modify the lexer (`TOKENS`) to recognise numbers and operators, update the parser to handle
     expressions, and generate appropriate `printf` calls in C.

2. Support Multiple Print Statements
   - *Description*: Enhance the first compiler to allow multiple `print` statements in a method and concatenate
     their outputs. For example, `print("Hello"); print("World");` should output `HelloWorld\n`.
   - *Learning Goals*: Learn to handle multiple statements in a method body and manage AST (Abstract Syntax Tree) nodes.
   - *Challenge*: Update `parse_method` to collect multiple print statements and adjust `generate_c_code` to
     combine them into a single `printf` or multiple sequential calls.

3. Add a Simple Main Method
   - *Description*: Allow users to define a `main` method in their class that runs automatically instead of
     hardcoding the first method call in the generated `main()` function.
   - *Learning Goals*: Explore entry-point concepts and conditional code generation.
   - *Challenge*: Modify the parser to identify a `main` method and adjust `generate_c_code` to call it
     explicitly in the C `main()` function.


### Medium Projects

4. *Add Instance Variables*
   - *Description*: Extend the first compiler to support instance variables in classes (e.g.
     `class Person { int age; def show() { print(age); } }`). Generate C structs with fields and access them in methods.
   - *Learning Goals*: Understand data storage in structs, variable scoping, and pointer manipulation in C.
   - *Challenge*: Add variable declarations to the parser, include them in the generated struct, and translate
     variable references into C pointer dereferences (e.g. `self->age`).

5. *Support Method Parameters*
   - *Description*: Modify the first compiler to allow methods with parameters (e.g.
     `def say(string msg) { print(msg); }`). Pass parameters from the caller to the method in the generated C code.
   - *Learning Goals*: Learn about function signatures, parameter passing, and type handling.
   - *Challenge*: Update the lexer and parser to handle parameter lists in method definitions and generate
     C function signatures with appropriate arguments.

6. *Implement Basic Inheritance*
   - *Description*: Upgrade the first compiler to support inheritance like the second compiler (e.g.
     `class Dog inherits Animal`). Generate C code with proper struct embedding and vtable inheritance.
   - *Learning Goals*: Explore object-oriented concepts like inheritance and polymorphism in a low-level language.
   - *Challenge*: Modify the parser to handle `inherits`, embed the parent struct in the child's struct,
     and set up the vtable hierarchy.



### Advanced Projects

7. *Add Support for Multiple Classes and Objects*
   - *Description*: Extend the first compiler to support multiple classes in a single file (like the second
     compiler) and allow creating multiple objects in `main()` with method calls (e.g. `Dog* d1 = Dog_create(); d1->speak();`).
   - *Learning Goals*: Understand multi-class parsing, object instantiation, and runtime behaviour.
   - *Challenge*: Update the parser to handle multiple `parse_class` calls, store them in the AST, and
     generate C code for multiple class definitions and object interactions.

8. *Implement Virtual Method Overriding*
   - *Description*: Enhance the second compiler to explicitly support method overriding with a `virtual`
     keyword (e.g. `virtual def speak()`) and ensure the correct method is called based on the object's actual type.
   - *Learning Goals*: Dive into polymorphism, vtable mechanics, and dynamic dispatch.
   - *Challenge*: Add a `virtual` token, track overridden methods in the AST, and ensure the vtable points
     to the most derived implementation.

9. *Add Exception Handling*
   - *Description*: Introduce a simple `try-catch` mechanism (e.g. `try { print("Risky"); } catch { print("Error"); }`)
     and generate C code with basic error checking (e.g. null pointer checks).
   - *Learning Goals*: Explore error handling, control flow, and runtime safety.
   - *Challenge*: Extend the lexer and parser for `try` and `catch`, and generate C code with `if` conditions
     and jumps to simulate exceptions.

10. *Support File Input/Output*
    - *Description*: Add syntax for reading from and writing to files (e.g.
      `def writeFile() { write("output.txt", "Hello"); }`) and generate C code using `fopen`, `fprintf`, etc.
    - *Learning Goals*: Learn about file I/O in C and integrate it into a high-level language.
    - *Challenge*: Parse file-related syntax, manage file pointers in the generated struct, and ensure
      proper resource cleanup (e.g. `fclose`).


### Open-Ended Projects

11. *Design a Domain-Specific Language (DSL)*
    - *Description*: Use the first compiler as a base to create a DSL for a specific purpose (e.g.
      a scripting language for a game or a configuration language). Define new keywords and semantics.
    - *Learning Goals*: Understand language design and customisation.
    - *Challenge*: Redefine `TOKENS` and the parser for the new DSL, then map it to C code that fits the domain.

12. *Build a Simple REPL*
    - *Description*: Create a Read-Eval-Print Loop (REPL) that uses the second compiler's parser
      and code generator to execute commands interactively (e.g. type `Dog* d = Dog_create(); d->speak();` and see the output).
    - *Learning Goals*: Explore interactive programming and runtime code execution.
    - *Challenge*: Integrate the compiler into a loop, dynamically generate and compile C code (e.g. using 'gcc'), and execute it.

13. *Optimise the Generated C Code*
    - *Description*: Analyse the C code output by either compiler and optimise it (e.g. reduce redundant
      allocations, inline small methods, or improve vtable lookups).
    - *Learning Goals*: Learn about code optimisation and performance tuning.
    - *Challenge*: Profile the generated code with tools like 'gcc -O2' or 'valgrind', then modify
      `generate_c_code` to produce more efficient output.
