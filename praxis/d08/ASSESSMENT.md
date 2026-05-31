## Assessment: Chapter 8 — Formal Methods

### Overview

Formal methods sit at the boundary between programming and mathematics.
Assessment here faces a particular challenge: a student can run a tool,
get an output (sat / unsat / counterexample), and submit it without
understanding what the output means or why the tool produced it.

The assessment must therefore focus on the **specification** — which the student
writes — and on the **interpretation** — which requires understanding. Running
the tool is not the hard part. Knowing what to ask, and knowing what the answer
means, is.

**Timing:** Assess after completing the Z3 puzzle progression and at least one
of the model checking or proof development projects. The oral examination can
be brief (10–15 minutes) but should not be skipped.

**Primary dimensions:** Reasoning and reflection (35%), Technical correctness
(30%), Process quality (20%), Critical tool use (15%).

---

### Oral Examination Questions

**Q1.** You asked Z3 to verify a property of your program. Show me the query.
Explain in one sentence what you were asking Z3 to prove. What did it answer?
- *Follow-up:* Z3 returned `unsat`. What exactly does that mean? Does it mean
  the property is true for all inputs? What assumptions does the guarantee rest on?
  What would break the guarantee?

**Q2.** Your Z3 encoding has a bug: it encodes a slightly different property
than the one you intended. Z3 returns `unsat`, but the actual program has
a bug. How could this happen? Construct a specific example.
- *Follow-up:* How would you check whether your encoding correctly captures
  your informal specification? What is the relationship between this problem
  and the specification quality issue in testing?

**Q3.** Explain the Curry-Howard correspondence in one sentence without
using the words "isomorphism" or "correspondence". What does it say about
type checking?
- *Follow-up:* Your type system from ch05 — what logical proposition
  does the type `Int -> String` correspond to? Can you give an example
  of a program of that type, and say what "proof" it represents?

**Q4.** You modelled a state machine and checked a CTL property.
Read me the CTL formula you used for the safety property.
Translate it into plain English.
- *Follow-up:* Now write the CTL formula for the liveness property
  "the system eventually responds to every request." What operator do
  you need that you did not need for the safety property?

**Q5.** You hit a limit of a formal tool in this chapter — something you
could not verify, or a Z3 query that timed out, or a proof that got stuck.
Describe it. Why could the tool not handle it?
- *Follow-up:* Is this a limitation of the specific tool, or a fundamental
  theoretical limitation? How do you know which?

---

### Assessment Task: The Wrong Specification

*Time allowed: 35–45 minutes. Z3 available. LLM available but all interactions must be logged.*

The following Z3 program is intended to verify that a simple rate limiter
never allows more than 3 requests in any 10-second window. It returns `unsat`,
suggesting the property holds. But the specification has a bug: it does not
actually capture the intended property.

```python
from z3 import *

# Times of 5 requests (in seconds)
t1, t2, t3, t4, t5 = Ints('t1 t2 t3 t4 t5')

s = Solver()

# Requests arrive in order
s.add(0 <= t1, t1 < t2, t2 < t3, t3 < t4, t4 < t5)

# All within a 100-second period
s.add(t5 - t1 <= 100)

# Negation of property: find 4 requests in a 10-second window
s.add(t4 - t1 <= 10)   # Try to find 4 requests in first 10 seconds

if s.check() == sat:
    print("Property violated:", s.model())
else:
    print("Property holds (unsat)")
```

**Part A:** Run the code. It returns `unsat`. Does this mean the rate limiter
is correct? Explain specifically why or why not.

**Part B:** Construct a concrete scenario — specific request times — where
4 requests arrive in a 10-second window, but the Z3 encoding above would
not detect it. (Do not change the code yet — just describe the scenario.)

**Part C:** Identify the bug in the Z3 encoding. What property is it actually
checking? What property should it be checking?

**Part D:** Fix the encoding to correctly verify the intended property.
Show that the fixed version finds the scenario you described in Part B.

**Part E:** The fixed encoding checks whether any 4 requests among the 5
fall within a 10-second window. Is this the same as "no more than 3 requests
in any 10-second window"? If not, what is the difference? How would you
encode the full property?

---

### Process Artifact Requirements

The specification evolution log for this chapter must contain:

1. For at least one Z3 project: the initial informal specification (in English),
   the first Z3 encoding, at least one revision of the encoding, and the reason
   for each revision.

2. The answer to: "What does `unsat` mean for this specific query? What does
   it guarantee, and what does it not guarantee?"

3. For the CTL model checking project: the CTL formulas written before running
   the model checker, with an English translation of each. If the model checker
   found a counterexample, include the counterexample trace and an explanation
   of what execution it represents.

4. For the proof development project: a record of the point at which the
   informal proof and the formal proof diverged — where a step that seemed
   obvious in English required a non-trivial lemma in the proof assistant.

---

### Rubric Application Notes

**Reasoning and reflection (primary):** The oral Q1 and Q2 together are the
clearest tests. A student who can explain what `unsat` means, and who can
construct a scenario where a wrong encoding gives a false `unsat`, understands
formal verification at the level this chapter requires.

**Technical correctness:** Formal results have an unusual property: either
the tool accepts the encoding and the result is reliable (within the tool's
guarantees), or the encoding is wrong. An incorrect encoding that nonetheless
gives the "right" answer by accident is worse than an encoding that gives
the wrong answer, because the former cannot be detected without the kind of
reasoning that Q2 assesses.

**Process quality:** The specification evolution log matters most here.
A student who arrived at a correct encoding on the first attempt either had
prior formal methods experience (which should be noted) or did not engage
deeply with what the encoding means. The log of revisions is evidence of
genuine specification work.

**Critical tool use:** Oral Q5 is the most revealing question in this chapter.
The ability to distinguish a tool limitation from a theoretical limitation —
and to explain the theoretical basis for the distinction — is the highest-level
outcome of this chapter.

**Connection to earlier chapters:** The assessment tasks in this chapter
are designed to connect to earlier work. A student who can say "the gap
between this Z3 guarantee and correctness is the same gap as between 100%
test coverage and correctness" has understood something that spans the
entire book. This connection, if it appears spontaneously in the oral
examination, should be recognised and noted.
