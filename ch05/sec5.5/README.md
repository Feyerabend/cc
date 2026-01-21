
## Parsers Overview

Parsers represent a broad and foundational area within computer science and related disciplines, having
evolved significantly over time. In this discussion, we focus on a select aspect of their [history](HISTORY.md),
highlighting their application and relevance, particularly in the context of computer languages.

Production rules are the formal constructs in a grammar that define the syntactic structure of a language.
They specify how symbols in the language can be generated or replaced during parsing. Each production rule
maps a non-terminal symbol to a sequence of terminal and/or non-terminal symbols, describing a valid
transformation within the grammar.

The general form of a production rule is:

```text
    A → α
```

Here, `A` is a non-terminal symbol (representing a syntactic category), and `α` is a sequence of terminals
(actual symbols of the language) and/or non-terminals (further rules). The left-hand side (`A`) indicates
what is being defined, and the right-hand side (`α`) specifies how it can be expanded.

For example, in a grammar for simple arithmetic expressions:

```text
    Expr → Expr + Term
    Expr → Term
    Term → Number
    Number → 0 | 1 | 2 | ... | 9
```

These rules define how complex expressions like `3 + 5` can be decomposed into their basic components
(numbers, operators) and parsed accordingly.

See some [simple](./simple) explanation of these basic steps: from a textual input to a representation of
the input in data structures that can be processed by the computer (a parse tree or AST).


### Top-Down Parsers

These parsers start from the start symbol of the grammar and attempt to derive the input string by applying production rules.
1. LL Parsers:
 - The abbreviation stands for `Left-to-right parsing, Leftmost derivation`.
 - They process the input from left to right and produce a leftmost derivation of the input string.
 - LL(k): This means the parser looks ahead k tokens to make decisions.
 - LL(1): The most common variant where only one token of lookahead is used.
 - Works well for grammars without ambiguity, left recursion, or significant ambiguity in production choices.
 - Recursive Descent Parsers (discussed further below) are typically implemented as LL(1) parsers.

2. Recursive Descent Parsing:
 - A simple top-down parsing method where each non-terminal in the grammar is implemented as a recursive function.
 - Relies on LL(1) grammar for correctness.
 - It's intuitive and easy to implement but requires that the grammar avoids left recursion and excessive ambiguity.

3. Predictive Parsing:
 - A non-recursive approach to LL parsing that uses a predictive table to guide parsing decisions.
 - Efficient for LL(1) grammars and avoids the need for recursive calls.


### Bottom-Up Parsers

These parsers start with the input tokens and attempt to reconstruct the start symbol of the grammar by reversing derivations.
1. LR Parsers:
 - The abbreviation stands for `Left-to-right parsing, Rightmost derivation in reverse`.
 - They process the input from left to right and construct a parse tree for a rightmost derivation in reverse.
 - Suitable for a broader class of grammars compared to LL parsers.

2. LR Variants:
 - SLR (Simple LR): Simplifies parsing by using a basic lookahead to resolve conflicts but works for a restricted set of grammars.
 - LALR (Lookahead LR): Combines states with identical cores to create a smaller parsing table, making it more memory-efficient
      than LR(1) while still supporting most programming language grammars.
 - LR(1): Uses a single lookahead token, supports a wide range of grammars, but parsing tables can become large.
 - GLR (Generalised LR): Handles non-deterministic or ambiguous grammars using parallel parsing paths.

3. Operator-Precedence Parsers:
 - A specific kind of bottom-up parser used for grammars where the structure is defined by operator precedence rules.
 - Simpler than full LR parsers but limited to certain grammars.


### Selected Parsing Techniques

4. [LL(1)](./LL1) Parsing:
 - Strengths: Easy to implement, efficient for simple grammars, and guarantees linear parsing time for LL(1) grammars.
 - Limitations: Cannot handle left-recursive or ambiguous grammars. Requires careful grammar design to fit LL(1) constraints.
 - Uses a parsing table for predictive parsing, where each cell indicates which production to apply based on the current input token and non-terminal.

5. [Recursive Descent](./simple) Parsing:
 - Implements each grammar rule as a function, where non-terminals are recursive calls.
 - Parsing decisions are guided by lookahead (one token ahead in LL(1)).
 - Direct and clear for grammar constructs, making it excellent for prototyping parsers.

### Additional

Additional parser can be found at [parsers](./../addition/parsers/).

Perhaps, as for me, you find it much more interesting to build parsers in practice and
explore them, rather than just reading about them. This is where your project can begin.
First, decide what you want to accomplish, and then try to achieve it, with or without
the help of LLMs. Parsing is a rewarding experience in its own right.

