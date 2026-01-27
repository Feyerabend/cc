
## PEG: Parsing Expression Grammar

Here your project becomes making a PEG parser. A PEG is best understood as a
formal *description* of a deterministic parser. It is not a language specification
first and a parser second; the grammar *is* the parser.

Formally a PEG consists of:
```
N  = set of non-terminals
Σ  = alphabet (terminals)
R  = rules A <- e
S  = start symbol
```
Each rule defines how to match input, from left to right, at a given position.

The right-hand side e is not a string of symbols but a parsing expression.
Parsing expressions are executable objects.

Basic building blocks:
```
e1 e2      sequence
e1 / e2    ordered choice
e*         zero or more
e+         one or more
e?         optional
& e        positive lookahead
! e        negative lookahead
"A"        literal
[a-z]      character class
.          any character
A          non-terminal reference
```
Example:
```
Expr   <- Term (("+" / "-") Term)*
Term   <- Factor (("*" / "/") Factor)*
Factor <- Number / "(" Expr ")"
Number <- [0-9]+
```
This grammar is directly executable as a parser.



### Core semantic idea

Every expression is a function:
```
parse(e, pos) → success(new_pos) | failure
```
Meaning:
1. Try to match e starting at position pos.
2. If it matches, return the new input position.
3. If not, fail and consume nothing.

Everything in PEG follows from this.



#### Sequence:
```
e1 e2
```
Means:
```
Match e1, then immediately match e2 at the new position.
```
Formally:
```
parse(e1 e2, pos):
    r1 = parse(e1, pos)
    if fail → fail
    return parse(e2, r1.pos)
```



#### Ordered choice:
```
e1 / e2
```
Means:
```
Try e1 first.
If it succeeds, stop.
Only if it fails, try e2.
```
Not “either/or” but “try-first-then”.
```
parse(e1 / e2, pos):
    r1 = parse(e1, pos)
    if success → return r1
    else → return parse(e2, pos)
```
This single rule removes ambiguity completely.



#### Repetition:
```
e*
```
Means:
```
Repeat e as many times as possible until it fails.
Never fails.
```
```
parse(e*, pos):
    p = pos
    while parse(e, p) succeeds:
        p = new_pos
    return success(p)
```



#### Predicates (lookahead):
```
& e   succeeds if e succeeds, but consumes nothing
! e   succeeds if e fails, but consumes nothing
```
They let you inspect the future input without touching it.
This is extremely powerful and replaces many context-sensitive hacks.



#### Non-terminals:

For a rule:
```
A <- e
```
Parsing A means parsing e:
```
parse(A, pos) = parse(e, pos)
```



#### Acceptance:

Parsing succeeds if:
```
parse(S, 0) succeeds
and new_pos == length(input)
```
Otherwise the input is rejected.



### Determinism and unambiguity

In PEG there is never more than one parse tree.

Because:
- Ordered choice commits to the first success
- There is no backtracking between alternatives once one matches
- The grammar defines control flow, not just structure

So PEG defines a *recogniser algorithm*, not a set of possible derivations.



### Execution model

A PEG parser is usually implemented as:

* Recursive descent + memoization (Packrat parsing)

Each non-terminal is a function:
```
parse_A(pos)
```
With memoization:
```
memo[A][pos] = success(new_pos) | fail
```
So:
- Each rule is evaluated at most once per input position
- Total time becomes linear in input size
- Memory is linear in (number of rules × input length)

This makes PEGs practical for real parsers.



#### Left recursion

This grammar is illegal in PEG:
```
Expr <- Expr "+" Term
```
Because it causes infinite recursion.

It must be rewritten:
```
Expr <- Term ("+" Term)*
```
This is not a limitation in expressive power,
but it forces grammars to be written in a parsing-friendly shape.



### AST construction

The basic PEG only returns success or failure.
In practice you attach semantic actions or tree builders:

Conceptually:
```
parse(e, pos) → success(new_pos, node)
```
For example:
```
Number <- [0-9]+
```
produces:
```
NumberNode(value)
```
You usually build nodes only for important rules and
ignore syntactic noise like parentheses and commas.



What you need to build a PEG parser
1. Grammar representation

Each rule:
```
A <- expression tree
```
Where expression tree nodes are:
```
Sequence
Choice
ZeroOrMore
OneOrMore
Optional
AndPredicate
NotPredicate
Literal
Class
Any
NonTerminalRef
```
2. Core parsing function
```
parse(expr, pos)
```
Returning:
```
(success, new_pos, optional AST node)
```
3. Rule dispatcher
```
parseNonTerminal(A, pos)
```
With memoization:
```
if memo[A][pos] exists:
    return it
else:
    compute, store, return
```
4. Input abstraction

Random-access string or byte buffer:
```
input[i]
```
5. Optional AST builder

Mapping rules to node constructors.



### Minimal mental model

A PEG is not describing what strings exist.
It describes how to read a string.

It is closer to writing:
```
if (try this)
else if (try that)
else fail
```
than to writing algebraic grammar rules.

This is why PEG grammars:
- Feel procedural
- Are deterministic
- Are directly executable
- Are very attractive for language implementation and DSLs

They sit exactly between *formal grammar* and *handwritten recursive-descent parser*
and unify both into a single object.

