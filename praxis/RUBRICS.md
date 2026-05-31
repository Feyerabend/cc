## Rubrics: Assessing Learning Across the Book

This document defines the assessment framework used throughout the companion
materials. It is intended for teachers applying grades or feedback, and for
students who want to understand what "good work" looks like before they begin.

The framework uses four dimensions. All four apply to every project. Their
relative weights shift by chapter, reflecting what each chapter is primarily
teaching. A chapter that focuses on debugging process weights process quality
most heavily; a chapter that focuses on critical analysis of tools weights
reasoning and reflection most heavily.

---

### The Four Dimensions

#### Dimension 1: Technical Correctness

Does the work do what it is supposed to do?

This includes: the program runs and produces correct output, edge cases are
handled, the implementation matches the specification, and the code does not
contain silent failures (wrong output that looks right).

Technical correctness is necessary but not sufficient. A correct program produced
by an LLM and accepted without understanding scores low on other dimensions even
if it scores high here.

#### Dimension 2: Process Quality

Was the work done with the right habits?

This includes: predictions written before running, hypotheses formed before
debugging, tests written before code (where TDD is required), LLM interactions
logged (where required), stages completed in order rather than jumped over.

The process log is the primary evidence for this dimension. In its absence,
this dimension cannot be assessed at all. Students who do not keep a log score
zero on this dimension regardless of the quality of their final result.

#### Dimension 3: Reasoning and Reflection

Does the student understand what they built?

This includes: ability to explain design decisions verbally, ability to answer
follow-up questions about the work, quality of the "one thing I got wrong"
reflection, accuracy of predictions relative to outcomes, and evidence of a
revised mental model after surprises.

This dimension is primarily assessed through the oral examination and written
reflections. It cannot be assessed from the submitted program alone.

#### Dimension 4: Critical Use of Tools

Were tools — including LLMs — used deliberately and critically?

This includes: LLM outputs verified rather than accepted, at least one LLM claim
identified as incorrect and corrected with evidence, alternative approaches
compared rather than first suggestion accepted, and documentation of what the
tool was asked and what was done with the output.

This dimension applies from chapter 3 onward. It is not assessed in chapters 1–2,
where LLM use is intentionally restricted.

---

### Levels

Each dimension is assessed at one of three levels.

#### Not Yet

The work shows significant gaps in this dimension. Intervention and re-engagement
are needed before the student is ready to move on.

| Dimension | Not Yet looks like |
|-----------|-------------------|
| Technical correctness | Program does not run, or runs but produces wrong output on straightforward cases. Core requirements not met. |
| Process quality | No prediction log or hypothesis log. Stages skipped. No evidence of systematic approach. |
| Reasoning and reflection | Student cannot explain what the program does. Reflection is absent or generic. Cannot answer a basic follow-up question. |
| Critical tool use | LLM output accepted without verification. No log. No evidence of critical evaluation. |

#### Meets Expectations

The work demonstrates solid, reliable competence in this dimension.
This is the expected level for a student who has engaged genuinely with the material.

| Dimension | Meets Expectations looks like |
|-----------|------------------------------|
| Technical correctness | Program runs correctly on intended inputs. Known edge cases handled. Specification requirements met. |
| Process quality | Predictions written. Hypotheses documented. Log exists with enough detail to reconstruct the working process. |
| Reasoning and reflection | Student can explain what was built and why the main design decisions were made. Reflection identifies a genuine specific wrong turn. Can answer one follow-up question. |
| Critical tool use | LLM interactions logged. At least one output verified independently. At least one claim corrected with evidence. |

#### Exceeds Expectations

The work shows depth, precision, and insight beyond what is required.
This level should not be common — if most students exceed expectations, the
expectations are too low.

| Dimension | Exceeds Expectations looks like |
|-----------|--------------------------------|
| Technical correctness | Program handles unexpected inputs gracefully. Implementation reveals understanding of the underlying mechanism, not just the surface requirement. Code is clean and could be extended without structural changes. |
| Process quality | Log is detailed enough to serve as a tutorial. Predictions are specific and reasoned, not just guesses. Multiple revision cycles visible. |
| Reasoning and reflection | Student can explain the design at multiple levels of abstraction. Reflection connects the specific wrong turn to a broader pattern in their understanding. Can answer multiple unexpected follow-up questions without hesitation. |
| Critical tool use | Multiple LLM claims evaluated, not just one. Errors characterised by type (hallucination, over-confidence, specification gap). Student can explain *why* the LLM was wrong in terms of its architecture. |

---

### Chapter Weightings

The four dimensions are weighted differently per chapter. These weights are
guidelines; teachers should adjust for their context.

| Chapter | Technical | Process | Reasoning | Tool use |
|---------|-----------|---------|-----------|---------|
| 01 Representation | 40% | 30% | 30% | — |
| 02 Virtual machines | 40% | 30% | 30% | — |
| 03 Debugging and testing | 25% | 40% | 35% | — |
| 04 Embedded systems | 35% | 25% | 25% | 15% |
| 05 Compilers and languages | 35% | 25% | 30% | 10% |
| 06 Craftsmanship and AI | 15% | 25% | 35% | 25% |
| 07 Advanced programming | 25% | 35% | 25% | 15% |
| 08 Formal methods | 30% | 20% | 35% | 15% |

**Reading the table:**
- Chapters 1–2: heavily weighted toward correctness and prediction discipline.
  These chapters build foundations; getting the implementation right matters.
- Chapter 3: process dominates. The hypothesis log and TDD order are the primary
  evidence. Debugging methodology is what is being taught.
- Chapter 6: reasoning and tool use dominate. The technical deliverable matters
  least here; critical thinking and documented LLM engagement matter most.
- Chapter 7: process dominates again, specifically the failure report.
  A project where nothing went wrong is incomplete.
- Chapter 8: reasoning dominates. The ability to explain what was verified,
  what was not, and why the distinction matters is the primary outcome.

---

### Applying the Rubric

#### For projects

Score each dimension separately using the three levels.
Convert levels to a numerical scale if required: Not Yet = 1, Meets = 3, Exceeds = 5
(or 0/2/3 for low-stakes formative work).

Apply the chapter weighting to produce a weighted score.

For any project where the process log was not submitted: the process dimension
scores Not Yet automatically. The overall score is capped at Meets Expectations
regardless of other dimensions — a correct program with no documented process
is evidence that the process was not followed.

#### For oral examinations

Oral examinations primarily assess reasoning and reflection. Score using the
three levels. Five to ten minutes per student is sufficient.

Suggested protocol:
1. "Walk me through what you did." (3 minutes — do not interrupt)
2. One prepared follow-up question from the chapter's `ASSESSMENT.md`.
3. One unprepared question based on something the student just said.

If the student cannot complete step 1 in a way that reveals genuine understanding,
steps 2 and 3 are not informative. Score Not Yet on reasoning and end the examination.

#### For self-study contexts

Without an oral examination, the reasoning dimension must be assessed through
written work alone. In this case, the "one thing I got wrong" reflection and
the final FOUNDATIONS engagement should be weighted more heavily.

A student doing self-study may use the rubric as a self-assessment tool.
Honest self-assessment against these criteria is itself a metacognitive skill.
See `SELFASSESS.md` for a student-facing checklist.

---

### A Note on Fairness

These rubrics are designed to be resistant to LLM-assisted shortcuts, but they
are not designed to punish the use of LLMs. A student who used an LLM extensively,
documented that use carefully, verified the outputs, corrected what was wrong,
and can explain every decision scores well on all four dimensions.

What the rubrics penalise is the absence of understanding — whether that absence
was caused by LLM over-reliance, insufficient engagement, or simple lack of time.
The instrument and the cause are separate. The rubrics measure one; the teacher
responds to the other.
