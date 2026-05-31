## Projects

### Craftsmanship, AI Tools, and Critical Analysis

These projects sit at the intersection of technical work and reflective thinking.
Most require both building something and writing something. The written component
is not secondary — it is often where the learning actually happens.

LLM use is explicitly allowed in all of these projects. But usage must be documented:
record every significant prompt, every output you accepted, and every output you
rejected or modified. That documentation is part of the deliverable.


#### Project 1: GPT-2 Failure Analysis

*Objective:* Run the GPT-2 pipeline, generate text in three different domains,
and produce a structured critique of its output.

Use `ch06/addition/gpt2/` for the pipeline setup.

Generate at least ten outputs in each of these categories:
1. *Factual:* Ask for a summary of a historical event, a scientific fact, or a
   biographical description. Verify each claim independently.
2. *Mathematical:* Ask it to perform simple arithmetic, explain a proof step,
   or describe an algorithm. Check every claim rigorously.
3. *Code:* Ask it to write a small function, explain what a code snippet does,
   or identify a bug. Run the code. Test it.

For each category, write a short analysis:
- What proportion of outputs were factually correct?
- What kinds of errors were most common?
- What patterns make an output *look* authoritative even when it is wrong?
- What would a user have to know to detect each error?

*Final question:* What does this analysis reveal about the gap between what an LLM
*appears* to do and what it *actually* does?


#### Project 2: Deskilling Study

*Objective:* Perform the same programming task twice — once without LLM assistance,
once with full LLM assistance — and write a comparative analysis.

Choose a task of moderate difficulty: implement a small interpreter, write a network
client, build a data structure with non-trivial invariants. The task should be
unfamiliar enough that you cannot complete it from memory alone.

*Run 1 — No LLM:*
- Use only documentation, reference materials, and your own reasoning.
- Record the time taken.
- Note: where did you get stuck? What did you look up? What decisions did you make?

*Run 2 — Full LLM:*
- Use an LLM freely. Accept or reject suggestions as you see fit.
- Record the time taken.
- Note: what did the LLM get right? What did it get wrong? What did you have to correct?

*Written analysis:* Compare the two runs.
- What was different about your understanding of the result in each case?
- Could you modify Run 2's code confidently without the LLM's help?
- What cognitive work did the LLM replace? Was that work valuable to do yourself?
- Where in the `ch06/addition/deskilling/README.md` does your experience connect?


#### Project 3: Logic Audit

*Objective:* Apply the logic audit methodology to a piece of existing code and
produce a formal audit report.

Use `ch06/addition/logicaudit/GUIDE.md` and `EXAMPLES.md` as your methodology reference.

Choose a subject: the SAP VM from ch03, the Raft implementation from ch07, or any
other non-trivial program in the repository.

An audit examines:
- *Comment-to-code consistency:* Does each comment accurately describe the code beneath it?
  Does the code actually do what the comment claims?
- *Invariant maintenance:* Are invariants stated anywhere (in comments, asserts, tests)?
  Are they actually maintained?
- *Precondition checking:* Are function inputs validated? Are assumptions made explicit?
- *Error handling completeness:* Are all error paths handled? Are any silently ignored?

*Deliverable:* A written audit report with findings categorised by severity (critical,
warning, informational). For each critical finding, propose a fix.

*Reflection:* How many findings were genuine bugs versus stylistic concerns?
How much of the code's correctness depended on implicit assumptions that were not
stated anywhere?


#### Project 4: Alloy Protocol Model

*Objective:* Model a protocol in Alloy and use the model checker to find
invariant violations.

Use `ch06/addition/algebra/alloy/` for the Alloy setup.

Model the 2FA protocol from ch04: a client, a server, a token with a validity window,
and a shared secret. Specify:
- The valid sequence of messages in an authentication session.
- The invariant: "a client is authenticated only if it has presented a valid token
  within the current window."
- The property: "no two simultaneous sessions can be authenticated with the same token."

Run Alloy's model checker. If it finds a counterexample, study the execution trace.
Ask: is this a real attack, or a limitation of the model?

*Extension:* Add an attacker with the ability to replay captured messages.
Check whether the protocol prevents replay attacks. If not, modify the protocol
until it does.

*Questions:*
- What does Alloy's counterexample tell you that manual analysis might have missed?
- What aspects of the real 2FA protocol are *outside* the model you built?
  What does that mean for the model's validity?


#### Project 5: TDD Progression Study

*Objective:* Read the five-stage TDD progression in `ch06/addition/tdd/01`–`05`
and produce a design history analysis. Then add a new feature using strict TDD.

*Part A — Analysis:*
Read the diff between each consecutive stage. For each change, classify it:
- *Test-driven:* the implementation change was required by a failing test.
- *Refactor:* the change improved structure without changing behaviour.
- *Design-driven:* the change was a proactive design decision not prompted by a test.

Write a short narrative of the design's evolution: what problems emerged at each
stage? How did the test suite shape the design?

*Part B — Extension:*
Add one new feature to the final stage. The feature must be specified as a set of
failing tests before any implementation is written.

Follow the log discipline from d03/Project 6: record every test-first, every
green step, and every refactor.

*Questions:*
- Were there moments in Part A where you thought the TDD discipline produced a
  *worse* design than you would have made by planning ahead? Justify your view.
- Did writing the tests first in Part B change the interface you designed?
