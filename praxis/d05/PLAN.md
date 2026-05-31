## Learning Blueprint: Language Understanding Through Construction

This chapter takes a deliberate methodological stance: theory follows practice.
Students build parsers before they study parsing theory. They write evaluators
before they encounter operational semantics. They implement closures before they
see the formal definition of an environment.

This reversal is intentional. Formal theory is powerful precisely because it
explains something you already understand informally. A student who has struggled
to handle left recursion in a hand-written parser reads the theory of LL(1) grammars
as an explanation of their own experience. A student who has never parsed anything
reads the same theory as a collection of symbols to memorise.

LLMs may be used throughout this chapter as "explanation partners" and as sources
of alternative implementations to compare. They should not be used to generate the
primary implementation — doing so skips the learning that comes from struggling with
the problem yourself. However, using an LLM to review your implementation, suggest
edge cases, or explain a concept you have encountered in practice is entirely appropriate.


### Pedagogical Principles

__1. Code before theory, theory to explain code__

Every formal concept is introduced after the student has encountered the problem
it solves. This means accepting that students will have imperfect implementations
before they have theoretical grounding. That imperfection is the curriculum.

__2. The parser is the primary unit of study__

A parser is small enough to hold in your head, complex enough to reveal real
difficulties, and concrete enough to run and test. It is the best single artefact
for teaching syntax, grammars, recursion, and the relationship between specification
and implementation.

__3. Multiple implementations of the same thing__

Students implement the same grammar multiple times using different strategies.
The comparison between implementations reveals what is essential (the grammar)
and what is accidental (the implementation technique).

__4. Specification as a check on implementation__

Every implementation should eventually be checked against a formal specification.
The specification is not the starting point; it is the test. When the implementation
diverges from the specification, the divergence is the lesson.


### Structure of the Chapter

#### Sequence 1: The First Parser

*Experience*

Students write a parser for arithmetic expressions with only addition and
multiplication — no variables, no parentheses. They may use any approach they find
natural: if-statements checking characters, splitting strings, recursive functions.
No guidance on method. The goal is a working program, however ugly.

*Reflection*

"How did you handle operator precedence? Did you think about it explicitly, or
did something in your code accidentally handle it? How do you know?"

LLM-assisted task: "Here is my arithmetic parser. Tell me five inputs where it
might produce wrong results. For each, explain what assumption in my code it violates."

*Conceptualisation*

Introduce the concept of a grammar. Write the grammar for the student's parser
*after* the student has written the code. Show that the grammar describes what
their code already does. Introduce ambiguity: what happens if multiplication and
addition have the same precedence in the grammar?

*Extension*

Students add parentheses to their parser. This typically forces a structural change.
They discover something: handling parentheses requires the parser to be recursive.
This is the moment to introduce recursive descent.


#### Sequence 2: Tokens and Structure

*Experience*

Students add a lexer to their parser: instead of scanning characters directly,
the parser now receives a list of tokens. They write the lexer themselves.

The first problem they encounter: how do you handle whitespace? How do you
handle multi-digit numbers? How do you handle keywords versus identifiers?

*Reflection*

"What decisions did you make in the lexer that the parser now depends on?
If you changed those decisions, what in the parser would break?"

LLM-assisted task: "I separated my lexer from my parser. What are the advantages
of this separation? What information is unavoidably lost in the tokenisation step?"

*Conceptualisation*

Introduce the formal concept of a token. Regular languages and regular expressions
as the theory of what a lexer can and cannot recognise. The reason lexing and
parsing are separate: different formalisms apply to each.

*Extension*

Students implement a small lexer for a language with at least two token types
that share a prefix (e.g. `=` and `==`). They discover the maximal munch rule
and understand why it is needed.


#### Sequence 3: The AST and Evaluation

*Experience*

Students modify their parser to produce an AST rather than immediately evaluating.
They represent the AST as nested data structures (tuples, dictionaries, or objects).

Then they write a separate evaluator that walks the AST.

The question to surface: *why separate the parsing from the evaluation?*

*Reflection*

"What can you do with an AST that you could not do if you evaluated immediately?
List at least three things."

LLM-assisted task: "Here is my AST evaluator. What transformation would I need
to perform before evaluation to support variable binding? Sketch the change without
implementing it."

*Conceptualisation*

Introduce the separation of concerns between syntax and semantics. The AST as
an intermediate representation. Tree-walking interpretation as the simplest
evaluation strategy. Introduce the concept of an environment (variable bindings).

*Extension*

Students add variable binding to their language: `let x = 5 in x + 3`. They must
thread the environment through the evaluator. This introduces the idea of scope.


#### Sequence 4: The Parser Comparison

*Experience*

Students take the grammar they have implemented using recursive descent and
implement it again using a different parsing strategy from `ch05/addition/parsers/`.
The recommended alternative is packrat (PEG) because it handles the same class
of grammars as recursive descent and the comparison is illuminating.

*Reflection*

"What did your second implementation handle more easily than the first?
What was harder? What does that tell you about the underlying differences?"

LLM-assisted task: "Compare recursive descent and PEG parsing.
For my specific grammar, which would you recommend, and why? Now tell me
what the best argument against your recommendation would be."

*Conceptualisation*

Introduce the taxonomy of parsing strategies: top-down vs bottom-up, LL vs LR,
deterministic vs non-deterministic. The parser comparison project from
[PROJECTS.md](./intermediate/PROJECTS.md) structures this formally.

*Extension*

Students attempt to parse a grammar that their first parser could not handle —
a left-recursive grammar — using an LR parser from `ch05/addition/parsers/LR1/`.
They compare the effort required.


#### Sequence 5: Types and What They Prevent

*Experience*

Students add a type checker to their language: expressions have types, and the
type checker rejects programs where an operation is applied to values of the
wrong type (e.g. adding a boolean to a number).

They then deliberately write a program that passes the type checker but behaves
incorrectly in a way the type checker cannot see.

*Reflection*

"What did the type checker prevent? What did it not prevent? Where is the boundary?
Is that boundary in the right place?"

LLM-assisted task: "Here is my type checker. What class of errors does it
guarantee to catch? What class of errors passes through it? Is there a theoretical
name for the property it provides?"

*Conceptualisation*

Introduce type soundness: progress and preservation. The Curry-Howard correspondence
as a brief pointer toward ch08. The tradeoff between expressive power and
decidability in type systems.

*Extension*

Students add one additional type rule: a function type, a list type, or an if-expression
that requires both branches to have the same type. They observe how a single new rule
interacts with the existing type system.


#### Sequence 6: The Central Project

Students undertake the language pipeline project from
[PROJECTS.md](./intermediate/PROJECTS.md), building a complete pipeline
from lexer through to evaluated output for a small language of their own design.

The language must differ from the in-class examples in at least one meaningful
structural way — a different control construct, a different type of value,
or a different evaluation strategy.

*Assessment suggestion:*

Each student presents their language with three demonstrations:
1. A program that runs correctly and produces the expected output.
2. A program with a deliberate syntax error — the student shows and explains the error message.
3. A program with a deliberate type error — the student shows how the type checker catches it.

The third demonstration in particular reveals whether the student understands what the
type checker is doing or has simply implemented it by pattern-matching examples.


#### Self-Study Path

A learner working alone follows this order:
1. Write a minimal arithmetic parser without reading any theory first.
2. Read `easy/EXERCISES.md` sections on lexing, parsing, and type systems.
3. Add a lexer, then an AST, then an evaluator, one step at a time.
4. Attempt the parser comparison project: implement the same grammar twice.
5. Read `advanced/FOUNDATIONS.md`.
6. Choose one extension project from PROJECTS.md.

*Outcome:*

By the end of this chapter the learner will:
- Have built a complete language pipeline from scratch.
- Understand the distinction between syntax and semantics at an operational level.
- Have compared at least two parsing strategies on the same grammar.
- Have implemented a type checker and understand what it guarantees.
- Be able to read and evaluate formal grammar notation by connecting it to working code.
