
## What is Packrat Parsing?

Packrat parsing is a parsing technique based on parsing expression grammars (PEGs).
It is a top-down, recursive descent parsing method that guarantees linear-time performance
by *memoizing* (see below) intermediate parsing results. Packrat parsers are particularly suitable
for implementing PEGs, which are formal grammars used to describe the syntax of programming
languages and other structured data formats.

1. Memoization

- Packrat parsing stores intermediate results of sub parsing operations in a table (memoization table).

- This avoids re-evaluating the same input multiple times, ensuring that the parsing is efficient
  even for complex, ambiguous grammars.


2. Deterministic

- Unlike traditional context-free grammars (CFGs), PEGs and their associated Packrat parsers are
  deterministic.

- There is no ambiguity because PEGs resolve conflicts by always choosing the first matching rule.


3. Linear Time Complexity

- Memoization ensures that each portion of the input is processed only once for every grammar rule,
  leading to O(n) complexity for an input of size n.


4. Infinite Lookahead

- Packrat parsers support arbitrary lookahead since they can memoize results of partial parses.
  This makes it possible to handle constructs that would be difficult for other parsing techniques.

#### History and Development

- Origins in Parsing Expression Grammars

  Packrat parsing was introduced by Bryan Ford in his 2002 paper Parsing Expression Grammars:
  A Recognition-Based Syntactic Foundation. It built on the idea of PEGs as a formalism for
  defining syntax and provided a practical parsing strategy.

- Advantages Over Traditional Parsers

  Packrat parsing emerged as an alternative to parsers based on CFGs, such as LL(k) and LR(k)
  parsers. It avoids the complexity of constructing parse tables (as in LR parsers) and the
  limitations of fixed lookahead (as in LL parsers).


### How Packrat Parsing Works

__1. Parsing Expression Grammar (PEG)__

A PEG defines syntax using rules like:

```peg
Expression <- Term (('+' / '-') Term)*
Term       <- Factor (('*' / '/') Factor)*
Factor     <- Number / '(' Expression ')'
Number     <- [0-9]+
```

These rules are deterministic, meaning no ambiguity exists in parsing.


__2. Recursive Descent__

The Packrat parser uses a recursive descent strategy where it tries to match the input against the PEG rules.


__3. Memoization Table__

During parsing, results of each rule applied at a specific position in the input are stored in a table.
Subsequent attempts to parse the same rule at the same position reuse the stored result instead of re-computing it.


#### Example: Simple Expression Parsing

Grammar
```peg
Expr  <- Term ('+' Term)*
Term  <- Factor ('*' Factor)*
Factor <- Number / '(' Expr ')'
Number <- [0-9]+
```

Input: "3 + 4 * 5"
1. Start at position 0 with the Expr rule.
2. Match the first 'Term (3)' and store its result in the memo table.
3. Match the '+' operator and proceed to the next 'Term'.
4. Reuse the memoized result for parsing Factor at position '4' for the '*' operator.

Advantages of Packrat Parsing
- Simplicity: It uses a straightforward *recursive descent* strategy.
- Flexibility: PEGs allow defining complex grammars, including those with left recursion and infinite lookahead.
- Guaranteed Performance: Linear-time parsing for any PEG grammar.


#### Limitations

1. Memory Usage:
- Memoization requires substantial memory, as it stores results for every rule at
  every input position. The size of the memoization table is proportional to
   ￼, where ￼ is the number of grammar rules and ￼ is the input size.

2. Left Recursion:
- Packrat parsers cannot handle direct left recursion natively, though extensions exist to address this.

3. Error Reporting:
- Error messages from Packrat parsers can be less informative than those from other parsers because PEGs are deterministic, making it harder to track alternatives.


#### Uses

Packrat parsing is used in parsers for programming languages and domain-specific languages (DSLs).
Many language processing tools and interpreters use PEGs and Packrat parsers for their deterministic
nature and ease of implementation. More over, Parboiled (Java/Scala) and Rats! are examples of frameworks
that use Packrat parsing.

Packrat parsing offers an efficient alternative for parsing complex grammars, combining the power
of PEGs with deterministic and efficient execution.


### Memoizing

Memoizing (or memoization) is a programming optimisation technique where you store the results of
expensive function calls in a cache so that future calls with the same inputs can return the cached
result instead of recomputing it.

How It Works
1. Function Input as Key: Each function call’s arguments act as a key for the cache.
2. Store the Result: The result of the computation is stored in a data structure (often a dictionary
   or hash map).
3. Reuse the Result: If the function is called again with the same arguments, the cached result is
   returned immediately, avoiding redundant computation.

#### Why Use Memoization?

Memoization is especially useful in:
- Recursive Functions: Avoids repeated calculations for overlapping subproblems (e.g. Fibonacci numbers,
  dynamic programming).
- Parsing: Caches intermediate results to avoid recalculating grammar rules at the same input position
  (as in packrat parsing).


#### Example: Fibonacci with and without Memoization

Without Memoization:

```python
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(10))  # exponential time complexity: O(2^n)
```

With Memoization:

```python
def fib(n, cache={}):
    if n in cache:
        return cache[n]
    if n <= 1:
        return n
    cache[n] = fib(n - 1, cache) + fib(n - 2, cache)
    return cache[n]

print(fib(10))  # linear time complexity: O(n)
```

#### Memoization in Packrat Parsing

In packrat parsing, memoization is used to store the results of parsing rules (functions)
at specific positions in the input. This avoids redundant work by:
- Preventing the parser from re-evaluating the same rule at the same position.
- Storing intermediate results in a memo table.

How It Works in Parsing
1. Each rule (like expr, term, or factor) checks if the result is already cached for the current input position.
2. If found, it uses the cached result.
3. If not, it computes the result, stores it in the cache, and then returns it.

Benefits of Memoization
- Improved Performance: Reduces the time complexity of recursive algorithms by avoiding redundant work.
- Deterministic Behaviour: Ensures that parsing results are consistent and prevents infinite loops in left-recursive grammars.

Trade-Offs
- Space Overhead: Memoization uses extra memory for storing results.
- Implementation Complexity: Requires careful handling of the cache to avoid logical bugs.
