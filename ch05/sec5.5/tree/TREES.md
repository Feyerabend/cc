
## Grammars and Production Rules

Understanding grammars, production rules, and parsing techniques bridges the gap between syntax and meaning,
enabling robust language processing in both natural and programming contexts. We start with some simple
examples and concepts.


### Grammars

A grammar is a set of rules that define the structure of a language. It describes how sequences of
symbols (e.g. numbers, operators, and parentheses in arithmetic) are organised into valid expressions.
Grammars are used in parsers to check whether an input string belongs to a given language.

The most common type of grammar for programming languages and parsers is a context-free grammar (CFG).
A CFG is defined by:
1. *Terminals*: The actual symbols in the language, like 3, +, *, or ( in arithmetic.
2. *Non-terminals*: Abstract symbols representing groups of terminals or other non-terminals.
   Examples are Expr, Term, and Factor in arithmetic grammar.
3. *Production rules*: Rules that specify how non-terminals can be expanded into terminals or other non-terminals.
4. *Start symbol*: The non-terminal that represents a complete sentence or program. In our case, it could be Expr.

Example Grammar for Arithmetic Expressions:

```enbf
Expr → Term ( ("+" | "-") Term )*
Term → Factor ( ("*" | "/") Factor )*
Factor → Num | "(" Expr ")"
Num → [0-9]+
```

This grammar describes:
- An expression (Expr) as a term followed by optional additions or subtractions.
- A term (Term) as a factor followed by optional multiplications or divisions.
- A factor (Factor) as either a number or a parenthesized expression.


### Production Rules

Production rules define the transformations in a grammar. Each rule specifies how a non-terminal
can be replaced by a sequence of other non-terminals or terminals.

For example:
- `Expr → Term ("+" Term | "-" Term)*` means an expression can be:
- A term.
- A term followed by one or more additions or subtractions of other terms.

Production rules are used to:
1.	*Parse input*: Starting from the start symbol, recursively expand non-terminals until the input matches the terminals.
2.	*Generate strings*: Starting with the start symbol, apply rules to create valid expressions.


### Parse Tree vs. AST

Both parse trees and ASTs are derived from the grammar and production rules, but they serve different purposes.

1. *Parse Tree*:
	- A parse tree is a full derivation of the input string based on the grammar.
	- Every application of a production rule corresponds to a node in the parse tree.
	- It includes all details of the grammar, even those that might be redundant for evaluation or transformation.
	- Example:
        - For 3 + 2 * (4 - 1), a parse tree based on the grammar would explicitly show:
    	    - Expr expanded to Term + Term.
	        - Term expanded to Factor * Factor, and so on.
            - E.g. (Expr (Term Num(3)) + (Term (Factor ...)))

2. *AST*:
	- An abstract syntax tree is a *simplified* representation of the structure of the input.
	- It eliminates *unnecessary nodes* (like non-terminals for Expr, Term, etc.) and focuses on the core logical structure.
	- Example:
        - For 3 + 2 * (4 - 1), the AST might look like:

```text
  +
 / \
3   *
   / \
  2   -
     / \
    4   1
```

#### Parsing in Context

Parsing is the process of taking an input string and constructing either a parse tree or an AST, depending on the needs:
- A *top-down parser* starts from the start symbol and tries to derive the input using production rules (e.g. recursive descent parsers).
- A *bottom-up parser* starts from the input and applies production rules in reverse to reconstruct the start symbol (e.g. shift-reduce parsers).

Relevance of Grammars and Parsing
- *Compiler design*: Compilers use grammars to parse code into ASTs for semantic analysis, optimization, and code generation.
- *Interpreters*: Interpreters evaluate input directly after parsing into an AST.
- *Validation*: Grammars are used to validate input, ensuring it follows language syntax rules.

