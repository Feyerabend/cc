
## Programming Language Semantics: A Comprehensive Guide

Programming language semantics is the study of what programs mean--how to rigorously
define what a program does when executed. While syntax tells us whether a program is
well-formed, semantics tells us what that well-formed program actually computes. There
are three primary approaches to defining semantics: *operational*, *denotational*, and
*axiomatic*. Each approach serves different purposes and provides unique insights
into program behaviour.

A serious compiler typically relies on all three:
- Operational:
  To ensure generated machine code behaves like the source program.
- Denotational:
  To justify that transformations preserve meaning.
- Axiomatic:
  To reason about correctness, safety, and invariants.

In a deep sense:
```
Operational semantics  ->  How it runs
Denotational semantics ->  What it means
Axiomatic semantics    ->  What is guaranteed
```

Semantics is primarily about specifying a language. A compiler is only one
consumer of that specification. The real goal is to define what programs
mean in a precise and unambiguous way.


### Operational Semantics

#### What It Is

Operational semantics defines the meaning of a program by specifying how it executes
step-by-step on an abstract machine. It describes computation as a sequence of state
transitions, essentially creating a mathematical model of program execution. Think
of it as a formal, precise specification of an interpreter.

#### How It Works

Operational semantics typically comes in two flavours:

*Small-step (structural) operational semantics* defines individual computation steps.
Each rule shows how a single atomic operation transforms the program state. For example:

- `(x := 5, σ) → σ[x ↦ 5]` (assignment updates the state)
- `(3 + 4, σ) → (7, σ)` (arithmetic evaluation)
- `(if true then S1 else S2, σ) → (S1, σ)` (conditional branch)

*Big-step (natural) semantics* describes the overall result of executing a program or
expression, jumping directly from initial state to final state without showing intermediate steps.
For example:

- `⟨x := 5, σ⟩ ⇓ σ[x ↦ 5]` (assignment produces updated state)
- `⟨while B do S, σ⟩ ⇓ σ'` (while loop produces final state after all iterations)

Both styles use inference rules with premises above a line and conclusions below.
For instance, a rule for sequence composition might be:

```
⟨S1, σ⟩ → ⟨S1', σ'⟩
─────────────────────
⟨S1; S2, σ⟩ → ⟨S1'; S2, σ'⟩
```

This reads: "If statement S1 in state σ steps to S1' in state σ', then the sequence
S1; S2 in state σ steps to S1'; S2 in state σ'."


#### Why It Is Used

Operational semantics is widely used because it:

- *Closely mirrors implementation*: It models how real interpreters and compilers work,
  making it intuitive for implementers
- *Enables reasoning about execution*: You can trace program behavior step-by-step,
  which is invaluable for debugging and understanding
- *Supports formal proofs*: Properties like type safety ("well-typed programs don't
  get stuck") are often proven using operational semantics
- *Facilitates tool development*: Many program analysis tools, debuggers, and
  theorem provers are built on operational semantic foundations
- *Handles non-termination naturally*: Small-step semantics can represent infinite
  computation sequences explicitly

It's particularly useful in language design, compiler verification, and when you
need to reason about computational complexity or resource usage.



### Denotational Semantics

#### What It Is

Denotational semantics assigns mathematical objects (denotations) to programs.
Instead of describing how programs execute, it defines what they compute by mapping
program constructs to elements in well-understood mathematical domains. A program
becomes a mathematical function from inputs to outputs.

#### How It Works

The key idea is to define a semantic function (often written as ⟦·⟧) that maps
syntactic constructs to mathematical meanings. For example:

*For arithmetic expressions:*
- ⟦n⟧ = n (a numeral denotes its numeric value)
- ⟦x⟧σ = σ(x) (a variable denotes its value in state σ)
- ⟦E1 + E2⟧σ = ⟦E1⟧σ + ⟦E2⟧σ (addition denotes mathematical addition)

*For commands (statements):*
- ⟦skip⟧ = id (the identity function on states)
- ⟦x := E⟧σ = σ[x ↦ ⟦E⟧σ] (assignment denotes state update)
- ⟦S1; S2⟧ = ⟦S2⟧ ∘ ⟦S1⟧ (sequence denotes function composition)

*For loops and recursion:*
Denotational semantics uses fixed-point theory from domain theory. A while loop
denotes the least fixed point of a functional:
```
⟦while B do S⟧ = fix(λf. λσ. if ⟦B⟧σ then f(⟦S⟧σ) else σ)
```
This requires sophisticated mathematical machinery like complete partial orders (CPOs),
continuous functions, and least upper bounds to handle non-termination and recursion properly.

#### Why It Is Used

Denotational semantics is valuable because it:

- *Provides compositional meaning*: The meaning of a compound expression is built from
  the meanings of its parts, enabling modular reasoning
- *Abstracts from execution details*: It focuses on what is computed, not how, making
  it easier to prove programs equivalent
- *Enables algebraic reasoning*: You can manipulate programs algebraically using mathematical laws
- *Supports program transformation*: Compiler optimizations can be proven correct by showing they preserve denotations
- *Connects to mathematical logic*: It provides a bridge to other mathematical theories and proof techniques
- *Handles higher-order features elegantly*: Functions as first-class values map naturally to mathematical function spaces

It's particularly useful in compiler correctness proofs, program equivalence, and when designing language features that interact in subtle ways (like scoping, closures, and continuations).



### Axiomatic Semantics

#### What It Is

Axiomatic semantics defines program meaning through logical assertions about program behavior.
Rather than describing execution or mathematical denotations, it specifies what is true before
and after program execution using preconditions and postconditions. It's the foundation of
program verification and formal correctness proofs.


#### How It Works

The primary framework is *Hoare logic*, which uses Hoare triples:
```
{P} S {Q}
```
This means: "If precondition P holds before executing statement S, then postcondition Q will
hold after S terminates (if it terminates)."

*Key axioms and inference rules:*

*Assignment axiom:*
```
{P[E/x]} x := E {P}
```
To find what must be true before assignment, substitute E for x in the postcondition.

*Composition rule:*
```
{P} S1 {Q}    {Q} S2 {R}
─────────────────────────
{P} S1; S2 {R}
```

*Conditional rule:*
```
{P ∧ B} S1 {Q}    {P ∧ ¬B} S2 {Q}
──────────────────────────────────
{P} if B then S1 else S2 {Q}
```

*While loop rule:*
```
{I ∧ B} S {I}
─────────────────────────
{I} while B do S {I ∧ ¬B}
```
Here, I is a loop invariant—a property that remains true throughout all loop iterations.

*Example proof:*
Prove `{x = 5} y := x + 1 {y = 6}`:

Using the assignment axiom with P = (y = 6) and E = x + 1:
- Substitute: P[E/y] = (x + 1 = 6) = (x = 5)
- So we have: `{x = 5} y := x + 1 {y = 6}` ✓


#### Why It Is Used

Axiomatic semantics is essential for:

- *Program verification*: Proving programs correct with respect to specifications
- *Automated verification tools*: Static analyzers, model checkers, and theorem provers
  (like Dafny, Frama-C, Coq) implement axiomatic semantics
- *Correctness by construction*: Writing programs with specifications that are verified during development
- *Finding loop invariants*: The need to specify invariants helps identify the essential properties programs maintain
- *Reasoning about partial correctness*: Proving that if a program terminates, it produces correct results
- *Security analysis*: Proving information flow properties and security policies
- *Contract-based design*: Pre/postconditions form the basis of design-by-contract methodologies

It's the semantic approach of choice when the goal is proving properties about programs
rather than understanding their computational behavior.



### Comparing the Three Approaches

| Aspect | Operational | Denotational | Axiomatic |
|--------|-------------|--------------|-----------|
| *Focus* | How programs run | What programs compute | What programs guarantee |
| *Representation* | State transitions | Mathematical functions | Logical assertions |
| *Strength* | Implementation-oriented | Compositional, abstract | Verification-oriented |
| *Typical use* | Language implementation | Compiler correctness | Program verification |
| *Handles non-termination* | Naturally | Via fixed points | Partial correctness |
| *Learning curve* | Moderate | Steep (domain theory) | Moderate (logic) |


#### When to Use Each

- *Use operational semantics* when implementing languages, proving type safety, or
  reasoning about resource usage and execution traces
- *Use denotational semantics* when proving program equivalences, verifying compiler
  transformations, or working with higher-order features
- *Use axiomatic semantics* when verifying program correctness, developing verified
  software, or reasoning about specific program properties



### Connections and Complementarity

These three approaches are not mutually exclusive—they complement each other:

- *Soundness theorems* connect axiomatic to operational semantics, proving that Hoare
  logic rules correctly describe program behavior
- *Adequacy theorems* link denotational to operational semantics, showing the
  mathematical model accurately represents execution
- *Full abstraction* relates denotational semantics to observational equivalence,
  ensuring the mathematical model captures all observable program behaviors

Together, these three approaches form a complete framework for understanding programming
languages at a deep, formal level. Each provides unique insights, and modern programming
language research often employs all three to fully understand and verify language designs
and implementations.


### Reference

This book/repository is not intended to be too deep into the formal, abstract aspect of compilation
theory (and other close subjects), but here are some tips:

![Denotational](./../../assets/image/denotational.png) ![Semantics](./../../assets/image/semantics.png)

#### Denotational
Stoy, J.E. (1981). *Denotational semantics: the Scott-Strachey approach to programming language theory*. (1., MIT Press paperback ed.) Cambridge, Mass.: MIT Press.

#### Axiomatic
Hoare, C. A. R. (1969). *An axiomatic basis for computer programming*. Communications of the ACM, 12(10), 576-580. https://doi.org/10.1145/363235.363259

#### *All*
Nielson, H. R., & Nielson, F. (2007). *Semantics with applications: An appetizer*. Springer.
