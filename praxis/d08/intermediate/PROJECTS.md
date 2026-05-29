## Projects

### Formal Methods, Types, and Verification

These projects sit at the boundary between programming and mathematics. They require
precise thinking and tolerance for working in unfamiliar notations. The reward is a
different kind of confidence in programs: not "the tests pass" but "this is proven."

Expect to spend significant time reading before writing. The foundations materials
for this chapter, and the theoretical documents in `ch08/addition/`, are as important
as the code.


#### Project 1: Z3 Puzzle Progression

*Objective:* Use Z3 to solve problems of increasing complexity, concluding with
the formal verification of a property from an earlier chapter.

Use `ch08/addition/z3/simple.py` as a starting point.

*Level 1 — Logic puzzles:*
Solve three logic puzzles using Z3's boolean and integer arithmetic theories:
- A classic scheduling puzzle ("Alice, Bob, and Carol are in different rooms...")
- The N-queens problem for N = 8.
- A Sudoku puzzle.

For each, encode the constraints, call the solver, and extract the solution.

*Level 2 — Program property:*
Use `ch08/addition/z3/sym_regvm.py` as a template.
Pick a small function (factorial, GCD, binary search) and encode it symbolically.
Ask Z3 to prove: "for all inputs in range [0, 100], this function returns the correct result."

*Level 3 — Rate limiter verification:*
Study `ch08/addition/z3/verify_rate_limiter.py`.
Find an input sequence that the rate limiter *should* reject but does not (a gap in the
specification). Model a fix. Verify that the fixed version rejects all sequences it should.

*Level 4 — Hamming code correctness:*
Encode the Hamming codec from ch01 symbolically. Ask Z3 to verify:
"If exactly one bit is flipped, the decoder always produces the original message."
Then ask: "If two bits are flipped, is there any case where the decoder silently
produces the wrong message?" Show the counterexample.

*Questions:*
- What is the difference between Z3 saying "sat" and "unsat"? What does each mean
  for your verification goal?
- What happens if the encoding of your program is incorrect? Can Z3 detect that?
- At Level 4, what does the counterexample for two-bit errors look like?


#### Project 2: CTL Model Checker for a Protocol

*Objective:* Model a concurrent protocol as a finite state machine and verify
safety and liveness properties using CTL.

Use `ch08/addition/model/ctl/` and `vmmodel.c` as reference implementations.

*Stage 1 — State machine model:*
Choose a protocol to model:
- The Raft leader election from ch07 (simplified to 3 nodes, no log replication).
- The 2FA authentication protocol from ch04.
- The producer-consumer problem with a bounded buffer.

Model the protocol as a set of states and a labelled transition relation.

*Stage 2 — Property specification:*
Write CTL formulas for:
- A safety property: "something bad never happens" (e.g. "there is never more than
  one leader simultaneously").
- A liveness property: "something good eventually happens" (e.g. "a leader is
  eventually elected after any failure").

*Stage 3 — Model checking:*
Run the model checker on your model with your properties.
If a property fails, study the counterexample trace. Is it a real violation or an
artifact of the model's simplifications?

*Stage 4 — Fix and recheck:*
If the initial model had a bug (a property violation), fix the model and recheck.

*Questions:*
- What is the difference between `AG p` and `EG p` in CTL?
- What aspects of the Raft protocol cannot be expressed in CTL? What more expressive
  logic would you need?
- What is the state explosion problem? Did you encounter it with your model?


#### Project 3: Linear Type Checker

*Objective:* Implement a linear type checker for a small language. Prove that it
prevents use-after-free by construction.

See `ch08/addition/linear/README.md`, `ch07/addition/borrow/`, and
`ch05/addition/affine/` for related implementations.

Design a minimal language with:
- Variables that can be *consumed* (ownership transferred to a callee).
- Functions that declare whether they consume their arguments.
- An explicit `free` operation that consumes a resource.

*Implement the type checker:*
- Track which variables are "live" (available for use) at each program point.
- When a variable is consumed (passed to a consuming function or freed), remove it
  from the live set.
- Report a type error if a variable is used after it has been consumed.
- Report a type error if a variable is consumed twice.

*Test suite:*
Write programs that the checker should accept and programs it should reject.
For each rejection, write a comment explaining what would go wrong at runtime
if the program were executed anyway.

*Extension:* Add a simple region-based memory system. Resources allocated in a
region must be freed before the region closes. The type checker enforces this.

*Questions:*
- What is the relationship between your type checker and Rust's borrow checker?
- What programs does your checker incorrectly reject (false positives)?
  Can you reduce false positives without losing soundness?
- What is the Curry-Howard reading of the linear type rules you implemented?


#### Project 4: Proof Development in a Proof Assistant

*Objective:* Write and verify a formal proof of a property of a program from an
earlier chapter.

See `ch08/addition/proof/` for the infrastructure and `hott/` for context.
Use a proof assistant of your choice: Lean, Agda, or Coq. The proof assistant
is available as a tool; the thinking is yours.

Choose one:

*Option A — Sorting correctness:*
Formally specify insertion sort. Prove:
1. The output is a permutation of the input.
2. The output is sorted.

*Option B — Hamming code:*
Formally specify the Hamming (7,4) encoding function. Prove that:
1. The encoding always produces a valid codeword.
2. Single-bit error correction always recovers the original data.

*Option C — Type system soundness:*
Take the simple type checker from ch05 and prove it sound:
1. Define what it means for an expression to be well-typed.
2. Prove the progress theorem: a well-typed expression is either a value or
   can take a step.
3. Prove the preservation theorem: if a well-typed expression takes a step,
   the result is well-typed.

*Questions:*
- What was the hardest lemma to prove? What made it hard?
- Did the proof reveal any bugs in the specification? What did you have to fix?
- What is the relationship between this proof and the tests you would have written
  instead? What does each one give you?


#### Project 5: Presburger vs. Z3 Boundary

*Objective:* Identify the boundary between what Presburger arithmetic can decide
and what requires a more powerful solver.

Use `ch08/addition/presburger/cooper.py`, `presburger.py`, and
`ch08/addition/z3/simple.py`.

*Stage 1 — Shared problems:*
Encode five problems in Presburger arithmetic and solve them with both `cooper.py`
and Z3. Compare: which is faster? Which produces more readable output?

*Stage 2 — Presburger limitations:*
Find two problems that Presburger arithmetic cannot express:
- One involving multiplication of two variables (nonlinear arithmetic).
- One involving quantification over functions or arrays.

Show that Z3 can handle these (with appropriate theories) but `cooper.py` cannot.

*Stage 3 — Completeness demonstration:*
Presburger arithmetic is complete: for every formula, the solver either proves it
or finds a counterexample. Z3 is not complete for all theories.

Find a Z3 query (involving nonlinear arithmetic or quantifiers) that Z3 times out on.
Show that the corresponding Presburger version (if encodable) terminates quickly.

*Questions:*
- What is decidability? Why does it matter for a verification tool?
- What is the complexity of Presburger arithmetic decision procedures?
  Is it practical for large programs?
- For verifying array bounds in a typical program, which tool would you use?
  Why?
