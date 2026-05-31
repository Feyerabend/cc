
## Teaching / Learning

*Students must understand where responsibility lies in a tool-rich world —
and what tools cannot do.*

This chapter asks the hardest question in the book: can a program be known to be
correct? Not tested thoroughly. Not reviewed carefully. *Known*, in the sense that
a mathematical proof is known.

The answer is: sometimes yes, always partially, never cheaply. Formal verification
provides a level of assurance that no amount of testing can match, for the parts
of a system it can cover. Understanding both what it offers and where it ends is
essential for anyone who will work on software where correctness matters.

This is also the chapter where all previous threads converge. The representation
concerns of ch01, the VM semantics of ch02, the testing philosophy of ch03,
the type systems of ch05 and ch07 — all of these connect to the formal reasoning
tools introduced here. A teacher who can draw those connections explicitly will
make this chapter feel like a culmination rather than a detour.

The chapter is challenging and should not be rushed. It is better to go deep on
one formal method — Z3, or CTL model checking, or the Curry-Howard correspondence —
than to survey all of them shallowly. Depth produces understanding; breadth without
depth produces anxiety.


### Teacher Focus

- **Ground every abstraction in a tool.** Do not introduce Hoare logic, CTL, or the
  Curry-Howard correspondence in the abstract. Show the tool first. Run it.
  Produce output. Then explain what the tool is doing theoretically.
- **The counterexample is a teaching moment, not a failure.** When a model checker
  or SMT solver finds a counterexample, study it carefully with the class.
  A counterexample trace is a concrete execution that violates a claimed property.
  It is more informative than a passing test.
- **Connect to earlier work at every step.** Every verification exercise should
  target something students have already built. "Does your Hamming codec always
  correct single-bit errors?" is a much better starting question than a
  hypothetical system.
- **The specification is the hard part.** Students will initially spend more effort
  running solvers than writing specifications. The lesson must redirect this:
  the specification encodes what you are trying to prove. A wrong specification
  proves nothing useful.
- **Acknowledge the limits explicitly.** Rice's theorem and the halting problem are
  not discouraging footnotes. They are central results that explain why formal
  verification is a tool, not a solution. Teach them as liberating: they tell
  you exactly what to expect and what not to expect.


### Student Tasks

- Solve one logic puzzle using Z3, then verify the answer by hand.
- Encode a property of a program from an earlier chapter as a Z3 query. Run it.
  If it returns unsat, the property holds. Explain what that means.
- Model a state machine from ch04 or ch07 in a model checker. Specify one safety
  and one liveness property. Document what the checker found.
- Write an informal proof of a simple program property. Identify every step that
  uses the word "clearly" or "obviously". Those are the steps that would require
  formal lemmas.
- Attempt one verification that the tools cannot complete. Document why and what
  that implies.


### Concrete Exercise: Z3 as a Bug Finder

Give students a function with a subtle bug — a boundary condition that fails
on a specific input. Do not point out the bug. Ask students to use Z3 to find it.

The exercise has four parts:

1. *Informal specification.* Write in plain language: "this function should always
   return a value in range [0, n-1]." What inputs might violate this?

2. *Z3 encoding.* Express the specification as a Z3 constraint. Ask Z3 to find
   a counterexample — an input that violates the specification.

3. *Counterexample analysis.* When Z3 produces a counterexample, trace through
   the function manually on that input. Confirm the bug. Explain why the function
   fails at that specific value.

4. *Fix and re-verify.* Fix the function. Re-run Z3. It should now return unsat —
   no counterexample exists.

This exercise teaches the full cycle: specify, verify, interpret, fix, re-verify.
It also introduces the most important distinction in formal methods: there is a
difference between a tool that says "I found no bug" and a tool that says
"no bug exists." Z3's unsat means the latter — but only for the encoding you provided.
If the encoding was incomplete, the guarantee is incomplete.

The class discussion after the exercise should focus on: what did you have to assume
to get unsat? Are all those assumptions valid? What would break if one of them were not?


### Example: The Gap Between Informal and Formal Proof

Most students have written informal proofs before, even if they have not called them that.
"This function is correct because it handles the base case and the recursive case" is an
informal proof. It is convincing but not verified.

The gap between informal and formal proof becomes visible in a proof assistant.
A step that takes one line in an informal argument — "and since the list is sorted,
the minimum element is at the head" — may require five lemmas in Agda or Lean:
a definition of "sorted", a proof that your sort function satisfies it, a proof
that the head of a sorted non-empty list is minimal, and so on.

This is not a criticism of formal methods. It is their point. The informal proof
hides assumptions; the formal proof makes them explicit. Every "clearly" and "obviously"
in an informal proof is a place where a formal proof does real work.

A productive classroom activity: take an informal proof (of sorting correctness,
or of the Hamming codec) and together with the class, list every hidden assumption.
Write each one on the board. For each, ask: is this obviously true? Could it be wrong
for some input? Has it been verified?

Students invariably find at least one assumption that is not as obvious as it seemed.
That moment of doubt is the beginning of formal thinking.


### LLM Use

LLMs are fully permitted in this chapter. Usage must be documented and critiqued.

Guidelines:
- LLMs can be helpful for generating initial Z3 encodings, explaining CTL syntax,
  and sketching proof structures. Use them for this.
- LLMs sometimes make incorrect claims about what formal tools can and cannot prove.
  Every significant LLM claim about a formal system must be verified against the
  actual tool output or the formal specification.
- If an LLM says "Z3 can prove this property", run Z3. If it says "this type system
  is sound", find the soundness proof or the known counterexample.
- For the proof development project, LLMs may suggest proof strategies. The student
  must attempt the strategy in the proof assistant and document whether it worked
  and why.

The critical habit this chapter aims to develop: the difference between *plausible*
and *verified*. An LLM produces plausible outputs. A proof assistant produces
verified ones. Both are useful. They are not the same thing, and knowing which
you have matters.
