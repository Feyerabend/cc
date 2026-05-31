
## Teaching / Learning

In a classroom setting the first chapter would do well to teach and learn,
without help from LLMs. It should be elementary, and easy to digest.

A mix of different learning styles are propsed in [PLAN.md](./PLAN.md).

In this students must understand *representation*, not *syntax*. That is why it
is required two languages (Python and C) at start, to underline the structures
beneath the syntax. This is about building a mental model of what the machine
actually does.

For each concept developed through the chapter:
1. Present a small program
2. Ask students to predict behaviour
3. Run it
4. Explain discrepancy
5. Tie it back to representation

This pattern builds correct skepticism.

Teacher focus:
- Binary, floating point, types, mutability
- Emphasise where intuition breaks
- No "just trust the language" explanations

Student tasks:
- Predict outcomes before running code
- Explain differences between representations
- Write short reasoning notes, not long programs


### Concrete exercise

Give students three short programs that differ only in:
- integer overflow
- floating-point comparison
- mutable vs immutable state

Ask:
- Which ones are correct?
- Which ones fail silently?
- Why?

If LLM will be used:
- Allowed only to explain outcomes
- Students must identify one incorrect
  or incomplete explanation from the LLM


### Eample: Teaching Floating Point

Floating point is often the first moment where students discover that computers
do not behave like mathematics. Until then, many assume that numbers in programs
are exact and comparable in the same way as numbers on paper. Floating point
breaks this assumption.

A floating-point number is not a real number. It is a finite binary approximation.
Most decimal fractions, such as 0.1, cannot be represented exactly in base 2,
so the value stored in memory is already slightly wrong before any computation
takes place. When these approximations are combined, the error propagates.
This is why an expression like 0.1 + 0.2 == 0.3 can evaluate to false. The
comparison itself is the mistake, not the arithmetic.

The correct mental model is that floating point is binary scientific notation with
limited precision. Each value has a fixed number of bits, so precision is relative
to magnitude. Small values can disappear when added to large ones, and equality
is usually not a meaningful operation.

This is exactly where teaching must resist "just trust the language" explanations.
Telling students that floating point is "inexact" without explaining why trains
avoidance, not understanding. Students need to know what guarantees the representation
provides and which it does not.

A good way to teach this is to start with a prediction. Ask students whether 0.1 + 0.2
equals 0.3? run the program, and let the surprise happen. Then show that the error
already exists in the representation, not in the addition. Introduce floating point
as binary scientific notation, not as "numbers". Finally, replace equality with
approximate comparison and make students choose and justify an error tolerance.

The goal is __not__ to memorize rules, but to change intuition. Students should stop
assuming exactness and start reasoning in terms of representation, precision, and
acceptable error. That habit is what prepares them to write correct numerical code
and to question confident but shallow explanations from tools, languages, or models.

