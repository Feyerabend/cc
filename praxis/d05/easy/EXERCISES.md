## Exercises

### Languages and Their Implementation

#### What Is a Programming Language?

1. *What is the difference between the syntax of a language and its semantics?*
   - Give an example of a sentence that is syntactically valid but semantically meaningless,
     both in a natural language and in a programming language.

2. *What is a grammar? What does it specify?*
   - What does it mean for a string to be "in" a language defined by a grammar?

3. *What is ambiguity in a grammar? Give an example.*
   - Why is ambiguity a problem for a parser? How is it typically resolved?

4. *What is the difference between a context-free grammar and a regular grammar?*
   - What class of programs can be recognised by each? Which is more expressive?

5. *Why do programming languages need to be precisely defined?*
   - What goes wrong if two compilers interpret the same language specification differently?

6. *What is a token? Give five examples from a programming language you know.*
   - What is the difference between a token and a character?

7. *What is the difference between a statically typed language and a dynamically typed language?*
   - Give one advantage and one disadvantage of each.


#### Lexing and Parsing

1. *What does a lexer do? What is its input and what is its output?*
   - Why is lexing kept separate from parsing?

2. *What is a regular expression, and why are regular expressions used for lexing?*
   - What class of patterns can a regular expression describe? What can it not describe?

3. *What is a parser? What is its input and what is its output?*
   - Describe the difference between a top-down parser and a bottom-up parser.

4. *What is recursive descent parsing?*
   - How does the structure of the parser relate to the structure of the grammar?

5. *What is an abstract syntax tree (AST)?*
   - How does an AST differ from a parse tree (or concrete syntax tree)?

6. *What is left recursion in a grammar? Why does it cause problems for recursive descent parsers?*
   - How can a left-recursive rule be rewritten to eliminate the recursion?

7. *What is operator precedence? How is it encoded in a grammar?*
   - Write a grammar for arithmetic expressions where multiplication binds more tightly than addition.

8. *What is a parse error? How should a parser respond to one?*
   - What is error recovery? Why is it important for a usable programming environment?


#### Compilation and Interpretation

1. *What are the stages of a typical compiler?*
   - Name them in order. What is the input and output of each stage?

2. *What is an intermediate representation (IR)?*
   - Why do compilers use an IR rather than translating directly from source to machine code?

3. *What is a symbol table? What information does it contain?*
   - When is the symbol table built? What kind of errors does it detect?

4. *What is type checking? What is the difference between static and dynamic type checking?*
   - Give an example of a type error that static checking catches and one that requires
     dynamic checking.

5. *What is code generation? What does the code generator receive, and what does it produce?*
   - What simplifications does an IR allow the code generator to make?

6. *What is an interpreter? How does it differ from a compiler?*
   - Describe tree-walking interpretation. What does the interpreter do at each node of the AST?

7. *What is a just-in-time (JIT) compiler? At what point does it compile?*
   - What makes a code path "hot" in the sense that a JIT cares about?

8. *What is the lambda calculus? Why is it considered a universal model of computation?*
   - What three things can you do in the lambda calculus? What can you not do directly?


#### Type Systems

1. *What is a type? What purpose does the type system serve?*
   - Think of a type as a set of values. What does it mean for an expression to "have" a type?

2. *What is a type error? Give an example of one caught at compile time and one caught at runtime.*

3. *What is type inference? What problem does it solve for the programmer?*
   - Give an example of a language that supports type inference. What does the programmer not
     have to write?

4. *What is polymorphism? What are the two most common kinds?*
   - Describe parametric polymorphism and subtype polymorphism. Give an example of each.

5. *What is an affine type? What is a linear type?*
   - How do these type systems track resource usage? What class of errors do they prevent?

6. *What does it mean for a type system to be "sound"?*
   - What guarantee does soundness provide? What is the cost of achieving it?
