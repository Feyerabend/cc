## Projects

### Debugging, Testing, and Optimisation

These projects are grounded in the code available in `ch03/` and `ch03/addition/`.
Each project has a defined goal and a set of constraints. Read those constraints
carefully before starting: some explicitly prohibit certain actions to force you
toward a more disciplined process.


#### Project 1: Hypothesis-Driven Debugging Challenge

*Objective:* Debug a broken program without changing any code until you have a
complete causal explanation.

Take the `ch03/sec3.8/tictactoe` program. A bug has been introduced: under
certain inputs, the game declares a winner incorrectly, or fails to declare one
at all.

*Rules:*
- You may not modify any code until you have written down two falsifiable hypotheses
  about the cause of the bug.
- One of your hypotheses must be a *null hypothesis*: "The bug is not in component X."
- For each hypothesis, design one experiment that would prove or disprove it.
- Only after you have run those experiments and reached a conclusion may you fix the code.
- After fixing, write one sentence: "The bug was caused by X, which I confirmed by Y."

*Deliverable:* A short written log of your hypotheses, experiments, and conclusions.
The fix itself is secondary.

*Reflection questions:*
- Did your first hypothesis turn out to be correct?
- Was the null hypothesis useful? Did it rule out anything you suspected?
- How long did the disciplined process take compared to how long random trial-and-error
  would have taken?


#### Project 2: Delta Debugging

*Objective:* Apply the delta debugging algorithm to minimise a failing test input.

Use `ch03/addition/fail/ddebug.py` as a reference implementation.

Steps:
- Choose a function or program that fails on certain inputs (you may introduce a bug
  into a simple parser or calculator if no suitable broken program is available).
- Create a large input that triggers the failure.
- Apply delta debugging to find the smallest input that still causes the failure.
- Verify that the minimal input actually isolates the root cause.

*Extension:* Implement the delta debugging algorithm yourself from scratch, without
looking at `ddebug.py`, then compare your version.

*Questions:*
- How does the minimised input help you understand the bug?
- Are there bugs where delta debugging would not help? What would make an input irreducible?


#### Project 3: Mutation Testing Game

*Objective:* Measure the quality of a test suite by seeing how many automatically
generated mutants it kills.

Use `ch03/addition/fuzzmut/fuzzmut.py` as a mutation engine.

Steps:
- Choose a small program to test (the SAP VM, a simple calculator, or a parser).
- Write a test suite for it. Aim for what feels like thorough coverage.
- Apply `fuzzmut.py` to the program to generate mutants (operator swaps, constant
  changes, condition inversions, etc.).
- Run your test suite against each mutant. Record which mutants survive (are not caught).
- For each surviving mutant, decide: is this an *equivalent mutant* (semantically
  identical to the original) or a genuine test gap?
- Write additional tests to kill the non-equivalent surviving mutants.

*Target:* Achieve a mutation kill rate above 90%.

*Questions:*
- Which mutation types were hardest to kill? What does this reveal about your tests?
- What is an equivalent mutant? How do you detect one?
- Does a 90% kill rate mean the program is correct?


#### Project 4: SAP VM Coverage and Testing

*Objective:* Measure and improve test coverage of the SAP VM.

The SAP VM lives in `ch03/addition/sap/`. It has a complete test harness
(`sap_vm_test.c`), a debugger (`sap_vm_debug.c`), and sample programs.

Steps:
- Build and run the existing test suite. Familiarise yourself with the structure.
- Add branch coverage tracking to the VM's main interpreter loop: record which
  branches are taken and which are never executed during the test run.
- Identify uncovered branches.
- Write new test programs (in SAP bytecode) that exercise those branches.
- Repeat until all reachable branches are covered.

*Extension:* Use `fuzzmut` to generate random valid programs and check whether
any cause a crash or assertion failure not caught by the existing tests.

*Questions:*
- Are there branches in the SAP VM that you could not cover? Why might that be?
- Did the coverage measurement reveal anything surprising about the existing tests?
- What is the difference between reachable and unreachable code in a VM interpreter?


#### Project 5: Fern Optimisation Analysis

*Objective:* Profile and explain the performance difference between a naive and
an optimised program.

`ch03/addition/fern/fern.py` renders a Barnsley fern using an iterated function
system. `ch03/addition/fern/optfern.py` is an optimised version.

Steps:
- Profile both versions using Python's `cProfile` or `timeit`.
- Identify the three most expensive operations in `fern.py`.
- For each, determine whether `optfern.py` addresses it and how.
- Name the optimisation technique used (loop-invariant hoisting, precomputation,
  data structure change, etc.).
- Measure the actual speedup for each change in isolation.

*Extension:* Apply one further optimisation that neither version uses. Measure its effect.

*Questions:*
- Which single change produced the largest speedup?
- Were any of the optimisations in `optfern.py` ones you would call "premature"?
  Justify your answer.
- How does the `ch03/addition/optimisation/GOTO.md` material connect to what you found?


#### Project 6: TDD from a Specification

*Objective:* Build a small program from scratch using strict test-first development.

Choose one: a simple expression evaluator, a small state machine, or a Roman numeral
converter. Do not use any existing code.

*Rules:*
- Write no implementation code before writing a failing test.
- Each test must be *red* before you write the code to make it *green*.
- After each green step, refactor if needed, but keep all tests passing.
- Keep a log: for each feature added, write down the test you wrote first and
  the implementation you wrote to satisfy it.

Use the `ch03/addition/ttd` and `ch06/addition/tdd` materials for context on
the TDD discipline.

*Deliverable:* The complete test suite, the implementation, and the log showing
the order in which they were written.

*Questions:*
- Did writing the test first change how you designed the interface?
- Were there moments where a failing test revealed something you had not thought about?
- Which was harder: writing the tests or writing the code?
