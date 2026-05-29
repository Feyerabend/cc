## Foundations: Language, Meaning, and the Act of Compilation

### 1. What It Means to Define a Language

A programming language is a formal system: a precisely defined set of rules for
forming programs and interpreting their meaning. The precision is not decorative.
It is what makes programs *reproducible*: two correct compilers for the same
language will produce programs that behave identically on the same input.

This precision is harder to achieve than it appears. Natural language is full of
context-dependence, ambiguity, and convention. A programming language must be
fully explicit. Every construct must have a defined meaning under every possible
condition. What happens when you divide by zero? What happens when you access
an array out of bounds? What happens when two threads write to the same variable
simultaneously? If the language specification does not say, the answer is
"undefined behaviour" — and programs that rely on undefined behaviour are
incorrect, even if they appear to work.

The study of language design is therefore the study of what to promise and what
to leave unspecified. The specification of Java's memory model, for example, is
hundreds of pages long, most of which defines what programs can rely on about
the relationship between threads. The simplicity of a language as a user
experiences it often rests on deep complexity in its specification.


### 2. Syntax, Semantics, and Their Relationship

The distinction between syntax and semantics is one of the most important in
language theory, and one of the most commonly misunderstood in practice.

*Syntax* is the set of rules for forming valid programs. A syntactically valid
program is one that can be parsed without error. Syntax says nothing about meaning.

*Semantics* is the assignment of meaning to syntactically valid programs.
Operational semantics defines meaning in terms of execution steps.
Denotational semantics defines meaning in terms of mathematical functions.
Axiomatic semantics defines meaning in terms of logical assertions about program state.

These are not merely academic distinctions. They determine what questions you can
ask about a program and how you can answer them. Operational semantics supports
questions like "what will this program do?" Axiomatic semantics supports questions
like "is this program correct?" Ch08's formal verification tools — Hoare logic,
Z3, model checking — are all grounded in axiomatic semantics.

A type system sits between syntax and semantics: it is more powerful than syntax
(it rejects programs that are syntactically valid but semantically wrong) but
less powerful than full semantics (it over-approximates, rejecting some programs
that would actually behave correctly).


### 3. Parsing as Structure Discovery

Parsing is not just about identifying whether a program is valid. It is about
discovering its structure — the hierarchical organisation of constructs that
determines their meaning.

The same string of characters can mean different things under different structural
parsings. `2 + 3 * 4` means different things depending on whether `+` or `*`
has higher precedence. The grammar encodes precedence and associativity. The parser
recovers the structure that the grammar implies. Without this recovered structure,
there is no meaning to evaluate.

The variety of parsing strategies — recursive descent, LL, LR, PEG, Earley,
CYK — reflects the variety of grammars that programmers need to handle and the
tradeoffs between parsing power, efficiency, and error quality. Recursive descent
is simple and produces good error messages but cannot handle certain left-recursive
grammars. Earley is maximally powerful but slow. Most production parsers use
strategies between these extremes.

The `ch05/addition/parsers/` folder provides twelve working implementations.
Studying them is not just a survey of techniques. Each one encodes a different
answer to the question: *what should a parser promise about the programs it accepts?*


### 4. Abstract Machines as Compilation Targets

A compiler does not simply translate source code to machine code. It translates
source code to the *instruction set* of a target machine. That target may be a
real CPU, or it may be an abstract machine.

The SECD machine (`ch05/addition/am/secd`) was designed by Peter Landin in 1964
as a mathematical model for evaluating lambda calculus expressions. It is an
abstract machine with four components: a Stack, an Environment, a Control list,
and a Dump. These four components correspond exactly to what is needed to evaluate
an applicative language: intermediate values, variable bindings, remaining computation,
and saved computation state for function returns.

The Warren Abstract Machine (`ch05/addition/am/wam`) plays the same role for Prolog.
Prolog programs compile to WAM instructions; the WAM is implemented on real hardware.
The WAM encodes backtracking, unification, and clause selection as explicit operations
in its instruction set.

Both machines illustrate a general principle: the design of an abstract machine is
the design of a *computational model*. Choosing what operations the machine supports
is choosing what computational ideas the language can express efficiently. A stack
machine without closures cannot efficiently implement higher-order functions.
A machine without a heap cannot easily support dynamically allocated structures.

The vtable model (`ch05/addition/vtable`) is a different kind of abstract machine,
one designed for object-oriented dispatch. The vtable encodes which method implementation
to invoke for a given class and method name. Dynamic dispatch, the ability to call the
right method without knowing the class at compile time, is a machine operation.


### 5. Types as Specifications

A type is a constraint on what values an expression can produce. At the level of
simple types, `int` means "this will be an integer." At the level of dependent types,
`Vector n Int` means "this will be a vector of exactly n integers."

More powerfully, types can express program properties that go beyond value shapes.
Affine types (`ch05/addition/affine`) express "this value will be used at most once."
Linear types (`ch08/addition/linear`) express "this value will be used exactly once."
Session types (`ch07/addition/sessions`) express "this communication channel will
follow this protocol."

The progression from simple types to rich type systems is a progression from
shallow guarantees to deep guarantees. A type checker for simple types prevents
some errors. A type checker for linear types prevents resource leaks. A type checker
for session types prevents protocol violations. The cost is that more expressive
type systems are harder to check, harder to write programs in, and sometimes
impossible to infer — the programmer must provide more annotations.

The Curry-Howard correspondence, which ch08 explores, makes this connection explicit:
types are propositions, and programs are proofs. A well-typed program is a proof
that a certain property holds. The type checker verifies the proof.


### 6. Language Design as Trade-off

A language designer makes hundreds of decisions, each of which constrains what
programs can express and how they behave. These decisions interact.

Making a language dynamically typed makes it more flexible but moves errors to runtime.
Making it statically typed catches errors earlier but imposes annotation burden.
Making types inferred reduces annotation burden but can make error messages cryptic.
Making the type system more expressive allows more programs to be verified but
makes the compiler more complex.

Making evaluation strict (eager) makes performance predictable but prevents some
optimisations. Making it lazy enables optimisations and infinite data structures but
makes performance difficult to reason about.

The `ch05/addition/language/PHILOSOPHY.md` and `LINGUISTICS.md` materials explore
these tradeoffs from different angles — the philosophical traditions that shaped how
we think about formal language, and the linguistic analogies that designers have used
(sometimes misleadingly) to reason about programming language design.

There is no universally correct answer to any of these tradeoffs. Every existing
language is a particular set of answers to a particular set of historical pressures.
Understanding why a language was designed as it was — what problems its designers
were trying to solve, what tradeoffs they were willing to accept — gives a much
richer understanding than memorising its syntax.
