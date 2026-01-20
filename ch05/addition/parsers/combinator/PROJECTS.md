
## Projects

1. Enhancing Error Reporting
	- Task: Extend the parser to provide detailed error messages, including the
      location of errors (e.g. line and column numbers).
	- Goal: Teach you how to track parsing context and improve debugging for language users.
	- Extension: Allow error recovery, where parsing continues past an error, if possible.

2. Parsing a Larger Grammar
	- Task: Expand the parser to handle a more complex grammar, such as a small programming language
      with conditionals, loops, and function definitions.
	- Goal: Introduce the challenges of recursive parsing, operator precedence, and scope management.
	- Example: Parse Python-like syntax: if x > 0: print(x).

3. Transforming Parse Trees into Abstract Syntax Trees (ASTs)
	- Task: Convert the parse tree produced by the parser into a stricter AST, which could simplify
      interpretation or code generation.
	- Goal: Teach you the distinction between parse trees and ASTs, and how to simplify tree
      structures while preserving semantic meaning.

4. Evaluating Parsed Expressions
	- Task: Implement an interpreter that evaluates the parsed expressions, like a
      Lisp interpreter.
	- Goal: Demonstrate how to traverse parse trees or ASTs and map them to computations.
	- Example: Evaluate (+ 1 2) into 3 or (* (+ 1 2) 4) into 12.

5. Handling Operator Precedence
	- Task: Modify the parser to respect operator precedence and associativity rules
      (e.g. 1 + 2 * 3 evaluates as 1 + (2 * 3)).
	- Goal: Explore how to use combinators to structure rules for precedence parsing.
	- Challenge: Implement precedence climbing or similar techniques in the combinator
      framework.

6. Adding Support for String Literals
	- Task: Extend the parser to handle quoted strings with escape sequences
      (e.g. "Hello, world!\n").
	- Goal: Introduce you to lexical challenges and stateful parsing.
	- Bonus: Implement error handling for unmatched or malformed string literals.

7. Parsing Custom Data Formats
	- Task: Adapt the parser to handle a structured data format like JSON or CSV.
	- Goal: Teach you how to represent real-world formats using combinators.
	- Example: Parse {"key": [1, 2, 3]} into a Python dictionary.

8. Visualisation of Parse Trees
	- Task: Create a graphical tool (e.g. JavaScript) that visualises the parse
      tree produced by the parser.
	- Goal: Help you to understand the hierarchical structure of parsed data.
	- Tools: Use libraries like graphviz or matplotlib to render trees.

9. Adding State to the Parser
	- Task: Introduce a stateful parser that can track variable definitions or
      other contextual information during parsing.
	- Goal: Show how to integrate state management into combinator parsers.
	- Example: Parse and track variable assignments: (define x 10) and then
      use x in subsequent expressions.

10. Tokenisation Layer
	- Task: Implement a clearer tokeniser (lexer) as a separate stage before parsing.
	- Goal: Demonstrate the separation of lexical analysis from syntactic analysis.
	- Extension: Optimise parsing by working with tokens instead of raw input.

11. Building a REPL (Read-Eval-Print Loop)
	- Task: Use the parser as the foundation for a command-line REPL for the Lisp-like language.
	- Goal: Introduce you to interactive environments and real-time feedback loops.
	- Example: Support inputs like (define x 10) and (print (* x 2)).

12. Performance Optimisation
	- Task: Profile the parser's performance on large inputs and identify bottlenecks.
	- Goal: Teach you techniques for improving recursive parsers, such as memoization or tail recursion.
	- Tools: Use Python’s timeit or profiling libraries like cProfile.

13. Grammar Testing Framework
	- Task: Develop a test suite that automatically verifies the correctness
      of the parser for various inputs.
	- Goal: Reinforce the importance of robust testing for complex systems.
	- Bonus: Include property-based testing with tools like hypothesis.

14. Creating a Compiler Frontend
	- Task: Extend the parser to output intermediate representations
      (e.g. three-address code) for a compiler.
	- Goal: Explore how parsing fits into the broader pipeline of compilation.
	- Example: Parse and translate (define x 2) into LOAD_CONST 2, STORE x.

15. Dynamic Grammar Generation
	- Task: Build a system where users can define their own grammars at runtime,
      and the parser adapts to them.
	- Goal: Introduce the meta-level capabilities of combinator parsers.
	- Challenge: Handle ambiguous grammars or poorly defined rules gracefully.
