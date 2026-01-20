
## Combinator Parsers

Combinator parsers are a functional programming approach to parsing, where parsers are
treated as modular, composable functions. The term "combinator" refers to the higher-order
functions used to combine simpler parsers into more complex ones. They were popularised
in functional programming languages such as Haskell, but the concepts have been adapted
to other languages, including Python.


### History

The idea of using combinators in parsing stems from research in functional programming
and formal language theory. Combinator-based parsers gained prominence in the 1980s and
1990s with the development of languages like ML and Haskell. Papers like "Monadic Parser
Combinators" by Graham Hutton and Erik Meijer helped establish their modern usage.
These parsers contrast with traditional parser generators (like YACC or ANTLR), which
require a separate step to produce parser code.

Combinator parsers rely on small, reusable building blocks:

1. *Atomic Parsers*: These handle basic patterns, such as matching a specific string
   (literal) or a regular expression (regex).

2. *Combinators*: These are higher-order functions that combine smaller parsers into
   more complex ones. Examples include:
    - seq: Parses a sequence of expressions.
    - choice: Attempts multiple parsers, succeeding with the first match.
    - many: Parses zero or more repetitions of a pattern.
    - opt: Matches an optional expression.

Core Concepts

1. Parser as a Function: Each parser is a function that takes an input string and returns either:
	- A tuple (result, remaining_input) if successful.
	- None if the parsing fails.

2. Composability: Complex grammars can be built by combining smaller parsers. For example, a
   JSON parser might combine parsers for numbers, strings, and lists.

3. Recursion: Recursive parsers handle nested structures like lists or parentheses by invoking
   themselves within combinators.

4. Error Handling: Advanced combinators allow for error reporting and recovery, making it
   easier to debug parsing failures.


### Example: combinator.py

* Atomic Parsers: literal, regex.
* Combinators: seq (for sequences), choice (for alternatives), many (for repetitions).
* Recursive Structures: parse_list recursively parses nested lists using parse_expr.

The parser processes a Lisp-like language where expressions can be numbers, symbols, or lists.
For example: the input "(1 (2 (3 ())))" is parsed into Python lists: [1, [2, [3, []]]].

It handles:
* Parsing Atoms: Symbols and numbers are parsed with parse_symbol and parse_number.
* Whitespace Handling: parse_whitespace ensures formatting flexibility.
* Expression Parsing: parse_expr combines atom and list parsing, enabling nested expressions.

### Pros and Cons

Pro:
- Modularity: Parsers for sub-expressions can be reused across different grammars.
- Readability: The functional style closely mirrors the structure of the grammar.
- Extensibility: Adding new grammar rules requires minimal changes.
- No External Tools: Unlike parser generators, combinator parsers are embedded
  directly in the programming language.

Con:
- Performance: Recursive descent can be slower than generated parsers, especially
  for large inputs or ambiguous grammars.
- Complexity in Error Reporting: Custom logic may be needed for meaningful error
  messages.


### Usage

Combinator parsers are often used in:
- Interpreters and Compilers: For domain-specific languages (DSLs) and scripting languages.
- Data Parsing: JSON, XML, and custom file formats.
- Code Analysis Tools: Syntax checking and refactoring.

Their conceptual elegance and practical flexibility make combinator parsers a favorite
among language enthusiasts and functional programmers.
