## Learning Blueprint: Formal Reasoning from the Ground Up

This chapter is the most abstract in the book. It asks students to work with
mathematical objects — types, proofs, logical formulas, state machines — and to
connect those objects to programs they have already written. The abstraction is
not decorative. It enables a kind of certainty that testing cannot provide.

The pedagogical challenge is that formal methods have a steep entry cost.
Students who have not previously worked with logic or type theory may feel that
the material is impenetrable. The approach here is therefore strongly concrete-first:
every abstract concept is introduced through a working tool that produces tangible
output. The Z3 solver, the Presburger arithmetic solver, and the CTL model checker
all give answers, counterexamples, and traces that students can read, discuss, and
argue about before engaging with the theory.

LLMs are fully permitted in this chapter, including for generating proof sketches
and explaining type-theoretic concepts. However, every LLM claim about a formal
system must be verified: run the tool, check the output, consult the specification.
LLMs make confident claims about formal systems that are sometimes wrong, and this
chapter is precisely about the difference between a confident claim and a verified one.


### Pedagogical Principles

__1. Tools before theory__

Students run Z3, the Presburger solver, or a model checker before they understand
the theory behind them. The tools produce output — sat, unsat, a counterexample
trace — that is concrete and discussable. The theory is introduced to explain
what the tools are doing.

__2. Specification is the hard part__

The technical difficulty of this chapter is not running the tools. It is
specifying what you want to verify. Students spend more time writing and
revising specifications than running solvers.

__3. A counterexample is a gift__

When a model checker or solver finds a counterexample, that counterexample
is the most valuable output of the verification process. Students are trained
to read counterexamples carefully, not to dismiss them as tool failures.

__4. Connect to earlier work__

Every verification exercise is grounded in something students have already built:
the Hamming codec from ch01, the VM from ch02, the Raft implementation from ch07.
The formal tools do not introduce new problems; they ask sharper questions about
old ones.


### Structure of the Chapter

#### Sequence 1: The First Z3 Proof

*Experience*

Students solve a logic puzzle using Z3. The puzzle should be one they can
also solve by hand — three people, three rooms, three constraints — so they
can verify Z3's output independently.

Then they encode a claim about a program: "this function never returns a
negative number for positive inputs."

*Reflection*

"What did you have to specify to make Z3 answer your question?
What was implicit in your natural-language formulation that you had to make
explicit for Z3?"

LLM-assisted task: "I want to prove [X] about my program using Z3.
Help me identify every assumption my informal proof uses.
Do not write the Z3 encoding — just list the assumptions."

*Conceptualisation*

Introduce SMT solving: what "satisfiability modulo theories" means.
The difference between sat (a satisfying assignment exists) and valid (all
assignments satisfy the formula). Why the second requires negation and unsat.

*Extension*

Students encode the Hamming codec from ch01 symbolically and verify that
single-bit error correction always succeeds. They then ask whether double-bit
errors are silently mis-corrected, and examine the counterexample Z3 produces.


#### Sequence 2: Model Checking and State Space

*Experience*

Students model a traffic light controller (which they implemented in hardware in ch04)
as a finite state machine. They specify two properties:
1. The light is never both red and green simultaneously.
2. The light eventually turns green.

They run the model checker from `ch08/addition/model/ctl/`.

*Reflection*

"Did the model checker verify both properties? If not, what counterexample
did it produce? Does the counterexample reveal a real bug in your ch04
implementation, or a limitation of your model?"

LLM-assisted task: "Here is a CTL formula: `AG ¬(red ∧ green)`.
Explain this formula in plain language. Now write a CTL formula that says
'green eventually follows red'."

*Conceptualisation*

Introduce CTL: the difference between AG (always globally), EF (exists eventually),
and their combination. The state explosion problem: why model checking scales poorly
with the number of concurrent components. Symbolic model checking as a response.

*Extension*

Students model the Raft leader election from ch07 as a 3-node system and
verify: "there is never more than one leader simultaneously." If the model
checker cannot verify this within a reasonable time, they discuss why.


#### Sequence 3: Types as Propositions

*Experience*

Students are shown a function with a dependent type signature:
`sort : (xs : List Int) -> {ys : List Int | sorted ys ∧ permutation xs ys}`.

They are asked: "What does this type guarantee about the function's output?
Can a function with this type return an empty list when given a non-empty input?"

They work through the answer by reasoning about the type, not by running the function.

*Reflection*

"What kinds of errors would this type catch that a standard type system would miss?
What errors would still slip through?"

LLM-assisted task: "Explain the Curry-Howard correspondence to me in terms of
this function. What proposition does the type represent? What does a program
of this type prove?"

*Conceptualisation*

Introduce the Curry-Howard correspondence formally: types as propositions,
programs as proofs, type-checking as proof verification. Linear types as linear
logic. Session types as multiplicative linear logic.

Connect to the work in ch05 (type systems) and ch07 (linear types, session types).
This sequence shows that those type systems were fragments of a larger theory.

*Extension*

Students examine the code in `ch08/addition/hott/` and read the README.
They do not need to understand HoTT fully. The goal is to see that identity
types — the type of witnesses that two things are equal — can have non-trivial
structure, and to understand why this matters.


#### Sequence 4: Writing a Proof

*Experience*

Students attempt to prove, in plain mathematical prose, that insertion sort
produces a sorted permutation of its input. They write the proof before
using any tool.

They then attempt to verify the same claim in Lean or Agda using the
infrastructure in `ch08/addition/proof/`. The formal proof is harder than
the informal one.

*Reflection*

"Where did your informal proof make an argument that the proof assistant rejected?
What was the gap between 'obvious' and 'formally proved'? Was the gap a real
gap or a gap in your formalism?"

LLM-assisted task: "Here is my informal proof of sorting correctness.
List every step where I use the word 'clearly' or 'obviously'.
For each, write down the formal lemma I would need to prove to justify the step."

*Conceptualisation*

The distinction between a proof sketch and a formal proof. What proof assistants
check and what they leave to the user. Why a formal proof is harder to produce
but worth more than an informal argument.

The connection to testing: a formal proof is a claim that *all inputs* satisfy
a property; a test is a claim about *specific inputs*. Both are valuable.
Neither replaces the other.

*Extension*

Students attempt to prove one non-trivial property of a program they wrote
in an earlier chapter. Even a failed attempt — one that gets stuck on a lemma —
is valuable if the student can name what they could not prove and why.


#### Sequence 5: The Boundary of Formal Methods

*Experience*

Students attempt to verify a property using Z3 that Z3 cannot decide in
reasonable time: a nonlinear arithmetic property, a quantified property over
an unbounded domain, or a property that requires reasoning about the heap.

*Reflection*

"The tool could not verify this. Does that mean the property is false,
that the encoding was wrong, or that the problem is outside the tool's scope?
How do you determine which?"

LLM-assisted task: "Z3 returned 'unknown' for my query. Give me three
different explanations for why this might happen. For each, describe what
I could change to make the query decidable."

*Conceptualisation*

The halting problem and Rice's theorem: most interesting properties of programs
are undecidable in general. Every formal analysis tool makes a tradeoff between
expressiveness and decidability.

Presburger arithmetic as a decidable fragment: every formula is either provable
or disprovable. Z3 as an incomplete but practical tool: it handles many cases,
but not all.

The final question: *what cannot be formally verified, and what does that imply
about the limits of our confidence in software?*

*Extension*

Students compare a property they verified in Z3 with the same property
verified by the Presburger solver, and one that only Z3 can handle.
They map the boundary between the two tools' capabilities on their specific problem.


#### Self-Study Path

A learner working alone follows this order:
1. Solve the logic puzzle using Z3. Verify the answer by hand.
2. Read `easy/EXERCISES.md` on logic, type theory, and formal verification.
3. Model the traffic light from ch04 and check the two CTL properties.
4. Attempt the informal sorting proof, then read `ch08/addition/proof/README.md`.
5. Read `advanced/FOUNDATIONS.md`.
6. Choose one project from PROJECTS.md and complete it, including the boundary exercise.

*Outcome:*

By the end of this chapter the learner will:
- Be able to use Z3 to verify properties of small programs.
- Understand what CTL model checking is, what it guarantees, and where it fails.
- Understand the Curry-Howard correspondence and its connection to earlier type systems.
- Have attempted a formal proof and encountered the gap between informal and formal argument.
- Know where formal methods reach their theoretical limits and why.
