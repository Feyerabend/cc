## Assessment: Chapter 7 — Advanced Programming

### Overview

This chapter deals with systems that fail non-deterministically, type systems
that prevent errors by construction, and distributed protocols that must survive
partial failure. The assessment must match this difficulty: it cannot rely on
"does the program produce the right output?" because many of the most important
programs in this chapter produce *different* correct outputs on different runs.

The **failure report** is the primary deliverable. A project where nothing went
wrong is not complete. The oral examination asks the student to reason about
failure modes they have not yet triggered.

**Timing:** Assess after completing the central project (Raft fault injection or
session types verifier). The failure report should be submitted before the oral.

**Primary dimensions:** Process quality (35%), Technical correctness (25%),
Reasoning and reflection (25%), Critical tool use (15%).

---

### Oral Examination Questions

**Q1.** Show me the specific instruction interleaving that produces an incorrect
result in the race condition you studied. Write it out, step by step.
At which step does the shared state become inconsistent?
- *Follow-up:* Your fix uses [mutex / atomic]. Show me how the same interleaving
  is prevented by the fix. What is the cost of the fix in terms of performance?

**Q2.** You killed the Raft leader during a write operation. What happened?
Was any data lost? Was any data duplicated? Why?
- *Follow-up:* What is the minimum number of nodes a Raft cluster needs
  to tolerate one failure? Two simultaneous failures? Derive the answer from
  the protocol, not from memory.

**Q3.** [For session types project] Your type checker rejected a program.
Read me the session type that it violated. Explain what the session type says
in plain language. Was the rejection correct?
- *Follow-up:* I want to add a timeout to this protocol: if no message arrives
  within 5 seconds, the channel closes. Can you express that in session types?
  If not, what would you need to add?

**Q4.** [For algebraic effects project] You composed state and exception effects.
What happens when an exception is thrown while in a modified state?
Does the state get rolled back? Why or why not?
- *Follow-up:* How would you implement a transactional handler: one where
  an exception causes the state modification to be rolled back?
  Sketch the handler, not the full implementation.

**Q5.** You asked an LLM to explain [concurrency concept / Raft property /
type system rule]. What did it say? Was that correct? Where was it wrong or
incomplete? How did you discover the error?
- *Follow-up:* Why do you think the LLM got that specific thing wrong?
  What does that suggest about the limits of its training?

---

### Assessment Task: The Failure Analysis

*This task is part of the project deliverable, not a separate timed exercise.*

Every project in this chapter must be submitted with a structured failure report.
The template is:

---

**System:** [Brief description of what was built]

**Failure mode investigated:** [What kind of failure were you trying to study?
e.g. "Leader failure during write", "Race condition in shared counter",
"Protocol violation in session-typed channel"]

**Setup:** [What conditions were needed to trigger the failure?
How did you create those conditions deliberately?]

**Prediction:** [Before triggering the failure, what did you expect to happen?
Be specific: "I expected the write to be lost" or "I expected both nodes to
claim leadership for approximately 150ms until the timeout resolved it."]

**Observation:** [What actually happened? Include any output, logs, or measurements.]

**Discrepancy:** [Where did your prediction differ from the observation?
What does this tell you about your prior model of the system?]

**Explanation:** [Trace the causal chain from the failure condition to the
observed outcome, using the protocol or type system rules where applicable.]

**Unresolved question:** [Name one thing you could not fully explain.
What experiment would you run next to investigate it?]

---

A failure report where Prediction and Observation are identical (everything went
exactly as expected) indicates either that the investigation was too shallow or
that the failure conditions were not challenging enough. In either case, the report
is incomplete.

---

### Process Artifact Requirements

For the Raft fault injection project: the process log must contain records of
at least three distinct fault injection experiments, each with a prediction,
an observation, and a comparison.

For the session types project: the log must contain the session type specification
written *before* implementation, and a note on any place where the specification
had to be revised during implementation and why.

For the algebraic effects project: the log must include an example of a handler
swap — two different handlers applied to the same computation — with a comparison
of the results and an explanation of why they differ.

For the borrow checker project: the log must include the program that reveals
the gap in the original checker (the use-after-free that was not caught), with
an explanation of why the gap exists.

---

### Rubric Application Notes

**Process quality (primary):** The failure report is the primary evidence.
A report with a specific, detailed discrepancy between prediction and observation
is the clearest indicator of genuine engagement with the system's behaviour.

**Reasoning and reflection:** Oral Q1 (the interleaving) is the most
discriminating question. Writing out a specific instruction interleaving
that produces an incorrect result requires genuine understanding of the
memory model. Students who understand the race condition abstractly but
cannot write the interleaving have not fully understood the mechanism.

**Technical correctness:** In concurrent systems, "works correctly" must be
verified under load, not just in a single run. A program that passes a single
test of the race condition fix is not assessed the same as one that passes
1000 repeated runs with no incorrect results.

**Critical tool use:** Oral Q5 directly assesses this. A student who found
an LLM error, verified it was an error, and can explain why the LLM made
that particular error demonstrates the kind of critical engagement this chapter
requires. "The LLM was wrong about X" without the verification and the
explanation is not sufficient.
