## Assessment: Chapter 5 — Compilers and Languages

### Overview

This chapter builds a skill that is easy to fake and hard to genuinely acquire:
the ability to think about programs at the level of their structure rather than
their surface appearance. A student who has built a working parser and evaluator
should be able to look at a new grammar and reason about what it accepts, where
it is ambiguous, and what type errors a type checker would catch.

Assessment focuses on **structural reasoning** — can the student think in terms
of grammars, ASTs, and type rules? — rather than on whether the pipeline runs.

**Timing:** Assess after completing the language pipeline project. The oral
examination involves the student's own language, so they should bring it.

**Primary dimensions:** Technical correctness (35%), Reasoning and reflection
(30%), Process quality (25%), Critical tool use (10%).

---

### Oral Examination Questions

**Q1.** Your parser accepts this input: `3 + 4 * 2`. Show me the AST it produces.
Now write the grammar rule that produces that AST. Is multiplication handled
correctly with respect to precedence?
- *Follow-up:* How would your grammar need to change to make `3 + 4 * 2`
  parse left-associatively? Would that change be correct?

**Q2.** Your parser rejects `3 + * 4`. Walk me through what happens in the
parser when it encounters the `*` after `+`. What error does it produce?
Is that a good error message?
- *Follow-up:* What would a better error message say? What information
  would it need to produce it?

**Q3.** Your type checker rejects this expression: [show an expression that
the student's type checker should reject]. Why is that rejection correct?
Now write a program that your type checker accepts but that produces a
runtime error anyway.
- *Follow-up:* What is the gap between what your type checker guarantees
  and what a fully sound type system would guarantee?

**Q4.** Explain what a closure is. Does your evaluator support closures?
If yes: how does the environment capture work? If no: what would need to
change in your implementation to add closures?
- *Follow-up:* What is the difference between lexical scope and dynamic
  scope? Which does your implementation use?

**Q5.** You implemented two parsers for the same grammar.
Which was easier to write? Which produced better error messages?
Which would be easier to maintain if the grammar changed?
- *Follow-up:* Pick one grammar rule. Show me how it is represented
  in each of your two parsers. What does the comparison reveal about
  the relationship between the grammar and the implementation?

---

### Assessment Task: Grammar Debugging

*Time allowed: 40 minutes. LLM may be used to suggest test inputs only —
not to fix the grammar. Log any LLM use.*

The following grammar is intended to parse simple arithmetic with operator
precedence (multiplication before addition), parentheses, and negative numbers.
It has at least two bugs.

```
expr   → expr '+' term | expr '-' term | term
term   → term '*' factor | term '/' factor | factor
factor → NUMBER | '(' expr ')' | '+' factor | '-' factor
```

**Part A:** Identify the structural problem with this grammar for a
recursive descent parser. Which rule is the problem, and why?
(Do not fix it yet — just name and explain the problem.)

**Part B:** Write three inputs where this grammar would cause a problem
for a recursive descent parser. For each, explain what the parser would
do (loop, reject valid input, or accept invalid input).

**Part C:** Rewrite the grammar to fix the structural problem while
preserving the intended precedence and associativity.

**Part D:** Does your rewritten grammar correctly handle all three of
your problematic inputs? Verify by tracing the parse for each one.

**Part E:** What does this grammar not support that a real language would need?
Name two things. For each, describe the grammar change required.

---

### Process Artifact Requirements

The grammar annotation for this chapter must include:

1. The student's original parser attempt — the one written before reading theory.
   (This is the first parser from PLAN.md Sequence 1, kept as-is.)
2. A post-theory annotation of that parser: for each significant code structure,
   which grammar rule does it implement? Where does it deviate from the correct
   rule?
3. The revised parser, with a note describing what changed and why.

The purpose is to make the learning arc visible: from ad-hoc parsing logic to
grammar-grounded implementation. A student who only submits the final parser
cannot demonstrate this arc.

For the type checker: the process log must include an example program that
the type checker incorrectly accepted or rejected (a false positive or false
negative). The student must explain the gap and whether it is fixable within
the current type system design.

---

### Rubric Application Notes

**Technical correctness:** Does the parser correctly handle the intended grammar,
including precedence, associativity, and parentheses? Does the evaluator produce
correct results for all syntactically valid inputs? Does the type checker reject
type-incorrect programs and accept type-correct ones?

**Reasoning and reflection:** The grammar debugging task is the clearest test.
A student who understands grammars can identify left recursion on sight and
explain why it causes problems for recursive descent. This requires understanding,
not just implementation experience.

**Process quality:** The grammar annotation (original → annotated → revised) is
the key artifact. It demonstrates the code-before-theory approach that this
chapter is built around.

**Critical tool use:** Was the LLM used to help write the initial parser?
If so, was its output understood and annotated? A parser written by an LLM and
submitted unchanged without annotation shows the opposite of what this chapter intends.
A parser written by an LLM, annotated with grammar rules, and extended by the student
shows appropriate critical use.
