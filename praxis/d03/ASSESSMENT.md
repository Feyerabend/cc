## Assessment: Chapter 3 — Debugging, Testing, and Optimisation

### Overview

This chapter is about epistemic discipline: forming hypotheses, testing them,
and revising understanding based on evidence. The process is the point.
A student who found the bug by randomly changing code and submitting the
result that worked has not met the chapter's learning outcomes, even if the
final program is correct.

Assessment therefore weights **process quality** most heavily. The hypothesis log
is the primary assessment artifact. Technical correctness is secondary.

**Timing:** Assess after completing Project 1 (hypothesis lab) and Project 3
(mutation testing). The oral examination may be conducted mid-chapter, after
the hypothesis lab, to reinforce the discipline before the mutation testing project.

**Primary dimensions:** Process quality (40%), Reasoning and reflection (35%),
Technical correctness (25%).

---

### Oral Examination Questions

**Q1.** Walk me through one bug you debugged in this chapter.
What was your first hypothesis? How did you test it?
What did the test reveal? What was your second hypothesis?
- *Follow-up:* Was your null hypothesis ever the right one?
  What would it have meant if the bug was not where you thought?

**Q2.** You ran mutation testing on your test suite. Some mutants survived.
Choose one surviving mutant and explain: is it a genuine test gap,
or an equivalent mutant? How do you know?
- *Follow-up:* A test suite kills 100% of mutants. Does that mean the
  program is correct? What could still go wrong?

**Q3.** Explain TDD's red-green-refactor cycle. Why does the test have to
be written *before* the implementation, not after?
- *Follow-up:* What does writing the test first force you to decide that
  writing the code first does not?

**Q4.** I have a function that produces the correct output but runs in
O(n²) time when it could run in O(n). My profiler shows it is responsible
for 2% of total runtime. Should I optimise it? Why or why not?
- *Follow-up:* What would you need to know to change your answer?

**Q5.** Explain delta debugging. What is the input to the algorithm and
what is the output? Why is the minimal failing input more useful than
the original failing input?
- *Follow-up:* Describe a bug where delta debugging would not be helpful.
  What property of the bug makes it unsuitable?

---

### Assessment Task: The Undocumented Bug

*Time allowed: 45 minutes. No LLM assistance for the debugging phase.
LLM may be used to generate hypotheses in Part C only — if used, log the interaction.*

The following function has a bug. It produces wrong output on some inputs
and correct output on others. It does not crash.

```python
def find_second_largest(numbers):
    if len(numbers) < 2:
        return None
    first = second = float('-inf')
    for n in numbers:
        if n > first:
            second = first
            first = n
        elif n > second:
            second = n
    return second
```

**Part A:** Write down three inputs you expect to produce correct output
and one input you think might produce wrong output. Write these *before*
running the function.

**Part B:** Run the function on your predicted inputs. Record the actual
outputs. For each wrong result, write: "I expected X, I got Y."

**Part C:** Form two hypotheses about the cause of the bug. One must be
a null hypothesis ("the bug is not in the comparison logic").
For each hypothesis, describe one experiment that would prove or disprove it.

**Part D:** Run the experiments. Revise your hypotheses if needed.
Write the causal explanation: "The bug occurs because [specific condition],
which I confirmed by [specific experiment]."

**Part E:** Fix the bug with the minimal change. Write one test that
distinguishes the buggy version from the correct version.

---

### Process Artifact Requirements

The hypothesis log for this chapter is the primary assessed artifact.
It must contain, for at least one debugging session:

1. The initial observation (what wrong output was produced, on what input).
2. The first hypothesis (specific and falsifiable — not "the logic is wrong"
   but "the comparison on line 7 uses < when it should use <=").
3. The null hypothesis (what was ruled out and how).
4. The experiment(s) run to test each hypothesis.
5. The result of each experiment.
6. The final causal explanation.

A log that begins with the fix and works backwards is not a hypothesis log.
The temporal structure — observation before hypothesis before experiment
before conclusion — is essential.

For the TDD project: the log must show the order in which tests and
implementation were written. A log that lists tests and implementation
without showing the order cannot be assessed.

---

### Rubric Application Notes

**Process quality (primary):** Is the hypothesis log structured correctly?
Does it show genuine hypothesis formation before code changes? The log can
reveal this even when the student did not follow the discipline: a log that
jumps from "the bug" to "I changed X" without a documented hypothesis shows
that the process was not followed.

**Reasoning and reflection:** In the oral examination, Q1 is the most important.
A student who can describe a specific bug, a specific hypothesis, a specific
experiment, and the specific result of that experiment has learned the method.
A student who says "I looked at the code and found the bug" has not.

**Technical correctness:** The fixed program should pass the test suite,
including the test written in Part E of the assessment task.

**A note on the mutation testing project:** Surviving mutants are not a failure.
They are information. A student who identifies and explains three equivalent
mutants shows more understanding than one who writes enough tests to kill all
mutants by brute force. The oral Q2 probes for this distinction.
