## Assessment: Chapter 1 — Representation

### Overview

This chapter builds foundational intuitions about how data is stored and
interpreted. The primary risk is that students learn the vocabulary without
building the correct mental model: they can say "floating-point is imprecise"
without understanding *why*, or describe two's complement without being able
to predict its behaviour at the boundary.

Assessment therefore focuses on **prediction accuracy** and **causal explanation**.
A student who predicted wrong and can explain the discrepancy has learned more
than one who predicted right by coincidence.

**Timing:** Assess after completing the floating-point and Hamming projects.
Oral examination can be conducted during or immediately after project work.

**Primary dimensions (see RUBRICS.md):** Technical correctness (40%), Process quality
(30%), Reasoning and reflection (30%). Tool use not assessed in this chapter.

---

### Oral Examination Questions

Use two or three of these per student. The prepared question is listed first;
the follow-up is asked only if the prepared question is answered well.

**Q1.** Your program prints `False` for `0.1 + 0.2 == 0.3`. Explain exactly
why this happens, starting from how `0.1` is stored in memory.
- *Follow-up:* If I change the comparison to `abs((0.1 + 0.2) - 0.3) < 1e-10`,
  does that make the computation correct? Or just less wrong?

**Q2.** Show me the two's complement representation of −1 in an 8-bit system.
Now show me −128. What is special about −128?
- *Follow-up:* What happens if I try to negate −128 in an 8-bit signed integer?
  Is the result correct? Why not?

**Q3.** I have a binary file written on a big-endian machine. I read it on a
little-endian machine without any conversion. What goes wrong? What doesn't go wrong?
- *Follow-up:* If the file contains only single bytes (like ASCII text), does
  endianness matter? Why?

**Q4.** Explain what Hamming code does to detect and correct a single-bit error.
Walk me through what happens when a single bit is flipped in transit.
- *Follow-up:* What happens if two bits are flipped? Does the decoder detect it?
  Correct it? Or silently produce the wrong message?

**Q5.** You wrote a prediction before running your floating-point program.
What did you predict? What actually happened? What does the discrepancy tell you
about your model of floating-point arithmetic?
- *Follow-up:* If you were teaching someone else the same concept, what would
  you have them predict, and why?

---

### Assessment Task: The Silent Failure

*Time allowed: 30–45 minutes. No LLM assistance.*

The following program contains a bug. It compiles and runs. It does not crash.
On most inputs it produces correct output. On some inputs it produces the wrong
output without any error or warning.

```python
def average(values):
    total = 0
    for v in values:
        total += v
    return total / len(values)

def is_close(a, b):
    return a == b

# Test
data = [0.1, 0.2, 0.3, 0.4]
result = average(data)
print(is_close(result, 0.25))   # Should print True
```

**Part A:** Run the program. Record the output.

**Part B:** Before making any changes, write down:
1. What you expected the output to be.
2. Why the output is what it is, in terms of representation.
3. Whether `is_close` is the right function to use here.

**Part C:** Fix the bug in `is_close`. Explain in one sentence why your fix is
correct and what it relies on.

**Part D:** Now try this input: `[1.0/3.0, 1.0/3.0, 1.0/3.0]`.
Expected average: `1.0/3.0`. Does your fixed version pass? Should it?
Justify your answer.

---

### Process Artifact Requirements

The prediction log for this chapter must contain:
- At least three predictions written *before* running code, including the
  prediction from the floating-point exercise in `d01/easy/EXERCISES.md`.
- The actual output for each prediction.
- A sentence explaining each discrepancy (or confirming that the prediction
  was correct and why).

A log that only records correct predictions is incomplete. Predictions that turn
out to be wrong are the most valuable entries.

---

### Rubric Application Notes

**Technical correctness:** Does the Hamming codec encode and decode correctly?
Does it handle single-bit errors? Does the floating-point visualiser show the
correct bit layout?

**Process quality:** Is the prediction log present? Does it contain genuine
predictions (not retrospective descriptions)? Is the log specific (names the
actual values predicted, not just "I thought it would work")?

**Reasoning and reflection:** In the oral examination, can the student explain
*why* the float representation is imprecise, not just *that* it is?
Can they predict the behaviour of a new floating-point expression they have
not seen before?

**A common failure mode:** Students who have read about floating-point often
describe the phenomenon correctly ("it's because of binary representation")
without being able to apply it to a specific case. The oral question Q1 and
the assessment task Part B distinguish these students from those who have
genuinely internalised the model.
