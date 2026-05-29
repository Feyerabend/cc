## Self-Assessment: Learning Outcomes by Chapter

This document is for students. It gives you a way to locate yourself in the
material: to know what you should be able to do after each chapter, and to
identify honestly where you need more work.

Use it in two ways:
- **Before starting a chapter:** read the checklist to know what you are working toward.
- **After completing a chapter:** go through the checklist item by item.
  Mark each one honestly. The items you cannot mark are where you should focus.

The three levels are:
- **Not yet** — I have not encountered this, or I encountered it but cannot do it.
- **Working on it** — I understand the idea but make errors or need to look things up.
- **Yes** — I can do this reliably and explain why it works.

Do not mark "Yes" because the project ran correctly. Mark "Yes" when you can
explain what you did and why, answer a follow-up question about it, and apply
the same idea to a problem you have not seen before.

---

### Chapter 1 — Representation

#### I can...

| | Not yet | Working | Yes |
|-|---------|---------|-----|
| Convert a number between binary, decimal, and hexadecimal without a calculator | | | |
| Explain why `0.1 + 0.2 != 0.3` in terms of IEEE 754 representation | | | |
| Show, in bits, how two's complement encodes a negative number | | | |
| Explain what happens at the bit level when a signed integer overflows | | | |
| Encode a short string in ASCII and identify its binary representation | | | |
| Explain the difference between big-endian and little-endian and give one context where it matters | | | |
| Describe what Gray code is and why it is used instead of binary in some sensors | | | |
| Explain how Hamming code detects and corrects a single-bit error | | | |
| Predict the output of a program involving floating-point comparison *before* running it | | | |

#### Reflection prompts

- What surprised you most about how computers store numbers?
- Describe a real situation (not from the book) where a representation choice could cause a bug.
- What is the difference between a representation and the value it represents?
  Why does this distinction matter?

---

### Chapter 2 — Virtual Machines

#### I can...

| | Not yet | Working | Yes |
|-|---------|---------|-----|
| Trace the execution of a short bytecode program by hand, showing the stack at each step | | | |
| Explain the fetch-decode-execute cycle in terms of my own VM implementation | | | |
| Describe the difference between a stack VM and a register VM, with a concrete tradeoff | | | |
| Explain what a call stack is and what happens to it when a function calls another function | | | |
| Describe the difference between the heap and the stack, and give one example of each | | | |
| Explain what the Harvard architecture is and what security property it provides | | | |
| Describe the difference between interpretation and compilation | | | |
| Explain why a pool allocator is faster than `malloc` for fixed-size allocations | | | |

#### Reflection prompts

- In what sense is a virtual machine a "contract"? Who makes the contract, and with whom?
- What did building a VM reveal about how programming languages work that you did not see before?
- What would it mean for a VM to be "incorrect"? Incorrect with respect to what?

---

### Chapter 3 — Debugging, Testing, and Optimisation

#### I can...

| | Not yet | Working | Yes |
|-|---------|---------|-----|
| Write a falsifiable hypothesis about a bug before touching the code | | | |
| Describe the delta debugging algorithm and explain what "minimising the failing input" means | | | |
| Explain what a mutant is in mutation testing and what it means to "kill" one | | | |
| Write a test that fails before the code is written (TDD red step) | | | |
| Distinguish between a test that achieves 100% line coverage and a test that proves correctness | | | |
| Explain what profiling is and why it is necessary before optimising | | | |
| Describe tail-call optimisation and the kind of recursion it applies to | | | |
| Apply the null hypothesis discipline: name one thing I ruled out during debugging and how | | | |

#### Reflection prompts

- Describe a bug you found using hypotheses. What was the null hypothesis you tested?
- What is the difference between a test suite that passes and a test suite you trust?
- When is a surviving mutant useful information rather than a gap to fill?

---

### Chapter 4 — Embedded Systems

#### I can...

| | Not yet | Working | Yes |
|-|---------|---------|-----|
| Explain why physical buttons require debouncing, in terms of the electrical behaviour | | | |
| Draw a state machine for a system I built, with states, transitions, and events labelled | | | |
| Explain the difference between polling and interrupts, and describe a situation where each is preferable | | | |
| Describe what an ISR is and name two things that must not happen inside one | | | |
| Explain why the Pico's two cores introduce real concurrency and what synchronisation is needed | | | |
| Describe what a threat model is and apply it to the 2FA protocol | | | |
| Explain why flash memory has write constraints that RAM does not | | | |
| Connect the embedded state machine concept to the finite automata in ch05 parsers | | | |

#### Reflection prompts

- What did working with real hardware teach you that a simulation could not?
- Describe one assumption in your embedded program that the hardware proved wrong.
- What is the connection between the memory constraints of an embedded device and the
  memory model concepts from ch02?

---

### Chapter 5 — Compilers and Languages

#### I can...

| | Not yet | Working | Yes |
|-|---------|---------|-----|
| Explain the difference between a token and a character, and why the distinction matters | | | |
| Write a grammar rule for arithmetic expressions that correctly encodes operator precedence | | | |
| Describe what an AST is and explain why it is different from a parse tree | | | |
| Explain what left recursion is and why it causes problems for recursive descent parsers | | | |
| Describe the stages of compilation and what the input and output of each stage are | | | |
| Explain what a type checker is verifying and give an example of a type error it catches | | | |
| Describe the difference between static and dynamic type checking with an example of each | | | |
| Explain what the Curry-Howard correspondence says, in one sentence | | | |

#### Reflection prompts

- What changed in your understanding of parsing between your first attempt and
  after reading the theory?
- Your parser accepted or rejected something it should not have. What grammar rule
  did it implicitly implement? How did you find it?
- What is the difference between a language and its implementation?

---

### Chapter 6 — Craftsmanship and AI Tools

#### I can...

| | Not yet | Working | Yes |
|-|---------|---------|-----|
| Identify and name three different quality dimensions of code (not just "correctness") | | | |
| Conduct a logic audit: check a comment against the code it describes and report the discrepancy | | | |
| Describe what the deskilling effect is and give one observation from my own experience | | | |
| Explain what technical debt is and distinguish between deliberate and accidental debt | | | |
| Log an LLM interaction in a way that records what was asked, what was produced, and what was done with it | | | |
| Identify at least one factual error in a GPT-2 or LLM output and explain why it occurred | | | |
| Defend a design decision orally, including naming the alternatives I considered | | | |
| Explain the difference between an LLM output that is *plausible* and one that is *correct* | | | |

#### Reflection prompts

- What did the deskilling study reveal about your own use of LLMs?
- Describe a design decision you made that you would make differently now.
  What changed in your understanding?
- What does "responsibility" mean for a programmer using LLM-generated code?

---

### Chapter 7 — Advanced Programming

#### I can...

| | Not yet | Working | Yes |
|-|---------|---------|-----|
| Construct a specific instruction interleaving that produces an incorrect result in a race condition | | | |
| Explain why a mutex prevents the race condition I described above | | | |
| Describe Raft's leader election protocol and explain what prevents two nodes from both believing they are leader | | | |
| Explain what the CAP theorem says and identify which property Raft sacrifices during a network partition | | | |
| Describe what a linear type is and give one example of a resource it would prevent being used twice | | | |
| Explain what a session type specifies and give a simple example | | | |
| Describe what an algebraic effect is and explain the difference between an effect and its handler | | | |
| Write a failure report: what I predicted, what happened, and what the difference reveals | | | |

#### Reflection prompts

- Describe the race condition you found or studied. Write out the specific interleaving
  that produces the incorrect result.
- What did the Raft fault injection experiment reveal that the protocol description alone
  would not have?
- Where in this chapter did you most feel the gap between "understanding the concept"
  and "being able to reason about the system"?

---

### Chapter 8 — Formal Methods

#### I can...

| | Not yet | Working | Yes |
|-|---------|---------|-----|
| Use Z3 to verify that a small function satisfies a stated property, and explain what "unsat" means | | | |
| Explain the difference between a counterexample and a proof, in terms of what Z3 produces | | | |
| Write a CTL formula for a simple safety property and explain what `AG` means | | | |
| Describe the Curry-Howard correspondence: types as propositions, programs as proofs | | | |
| Explain what a dependent type is and give a simple example of a type error it would catch | | | |
| Explain why the halting problem implies that no tool can verify all properties of all programs | | | |
| Describe the difference between Presburger arithmetic and Z3's nonlinear arithmetic in terms of decidability | | | |
| Identify the gap between an informal proof step that says "clearly" and the formal lemma it requires | | | |

#### Reflection prompts

- What property did you verify formally in this chapter? What did the verification guarantee?
  What did it not guarantee?
- Where did you hit the boundary of what the tools could handle? What does that boundary tell you?
- How has this chapter changed the way you think about testing in the earlier chapters?

---

### Across All Chapters

#### Habits

| Habit | Not yet | Working | Yes |
|-------|---------|---------|-----|
| I write predictions before running code | | | |
| I keep a log of what I tried and what happened | | | |
| I form a hypothesis before changing code when debugging | | | |
| I write a reflection after each project | | | |
| I verify LLM claims before acting on them | | | |
| I can explain my work out loud without looking at it | | | |
| I document what went wrong, not just what worked | | | |

#### A Final Question

After completing the book, answer this in writing:

*What is the most important thing you now understand about computation that you
did not understand before? Why does it matter?*

There is no correct answer. But there should be a specific one.
A vague answer ("I understand programming better") means the question is still open.
