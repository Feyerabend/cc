## Learning Blueprint: Correctness in Complex Systems

This chapter deals with programming that is genuinely difficult to reason about:
concurrent programs that may fail non-deterministically, type systems that
prevent errors by construction, distributed protocols that must survive partial
failure. The difficulty is not superficial. It reflects fundamental properties
of these systems.

The central pedagogical challenge is that bugs in this domain are often invisible
until a specific, hard-to-trigger condition is met. A concurrent program may run
correctly ten thousand times and fail on the ten-thousand-and-first. A type error
that a linear type system would catch is silently accepted by a simpler type system
and causes a crash six months later.

The teaching strategy is therefore: *create the conditions for failure systematically,
and use the failure as the primary instructional material.*

Students in this chapter are expected to be comfortable with the material of all
previous chapters. LLMs may be used freely but should be treated as an unreliable
reviewer: capable of generating plausible explanations, not reliably correct ones.
Students are required to disagree with at least one LLM claim per project, with a
written justification for the disagreement.


### Pedagogical Principles

__1. Failure is the curriculum__

Providing a concurrent program that "works most of the time" and asking students
to reproduce, explain, and fix the failure is more educational than any correct
implementation. The failure is not a problem to avoid; it is the thing to study.

__2. Reasoning must be written down__

Concurrent and distributed reasoning is too complex to hold entirely in working
memory. Students write down their model of the system before running it.
After the run, they compare the model with what actually happened.
The discrepancy is the lesson.

__3. Type systems are verified reasoning__

Advanced type systems (linear, session, dependent) are not a convenience feature.
They encode a claim about the program. Students are asked to state the claim first,
then verify that the type system enforces it.

__4. Scale is introduced gradually__

Distributed systems concepts (Raft, session types, RTOS) are introduced first
in their simplest form — 3 nodes, 2 parties, 2 tasks — and scaled up only
when the simpler form is understood. The complexity of full-scale systems comes
from composition, not from the individual concepts.


### Structure of the Chapter

#### Sequence 1: The Race Condition

*Experience*

Students are given a concurrent counter program that uses two threads to increment
a shared variable. They run it 1000 times and record the distribution of outputs.

The expected output is always 2000. Most runs produce something close. Some do not.

*Reflection*

"How many runs were incorrect? What is the smallest incorrect value you saw?
Can you explain why that value is possible? Can you construct a specific
interleaving of operations that would produce it?"

Write out the interleaving on paper, step by step, showing the machine state
at each instruction.

LLM-assisted task: "Here is a concurrent counter program. Describe all possible
outcomes. For each incorrect outcome, give me the specific instruction interleaving
that produces it."

*Conceptualisation*

Introduce the memory model: why non-atomic operations produce non-atomic behaviour.
The happens-before relation. Mutual exclusion and its cost.

The critical point: the program looked correct because it usually worked.
This is the most dangerous kind of bug — not one that always fails,
but one that fails rarely enough to escape testing.

*Extension*

Students fix the counter using a mutex, then using an atomic operation, then
measure the performance difference between the two fixes.


#### Sequence 2: Structured Failure in Distributed Systems

*Experience*

Students run the Raft implementation from `ch07/addition/raft/` with 3 nodes.
They perform a sequence of writes, then kill the leader.

The question: *does the system continue to work? Does any data get lost?
Does any data get duplicated?*

*Reflection*

"Before you killed the leader, what did you expect to happen? What actually happened?
Write down every assumption you made that turned out to be correct, and every
assumption that turned out to be wrong."

LLM-assisted task: "I killed the Raft leader during a write operation.
The system [describe what happened]. Explain why this happened, step by step,
using Raft's protocol. Then tell me one scenario where your explanation would
not hold."

*Conceptualisation*

Introduce the Raft safety guarantee: at most one leader at a time.
The liveness caveat: during a partition, the minority partition stops making progress.
This is a deliberate design choice. Why?

Connect to the CAP theorem. Which two properties does Raft guarantee?
Which does it sacrifice?

*Extension*

Students simulate a network partition by blocking messages between two nodes
and writing to both partitions. They observe the behaviour and compare it to
the theory.


#### Sequence 3: Types as Proof Obligations

*Experience*

Students take a simple program with resource handling (opening and closing files,
or allocating and freeing memory) and introduce two bugs:
1. A resource used after it has been freed.
2. A resource freed twice.

They verify that neither bug is caught by a standard type checker.

Then they run the same program through the affine type checker in
`ch05/addition/affine/` or the borrow checker in `ch07/addition/borrow/`.

*Reflection*

"The type checker rejected the program. What claim about the program did
the rejection communicate? Is the claim correct? Was the bug real?"

LLM-assisted task: "Here is a program with a use-after-free bug.
What type system feature would prevent this class of error?
Give me the formal rule as a typing judgment."

*Conceptualisation*

Introduce linear types and their relationship to resource management.
The type checker as a verifier of resource discipline.
The Curry-Howard correspondence as a pointer: the type rule is a logical axiom;
the program is a proof that the axiom is satisfied.

*Extension*

Students write a program that a linear type checker rejects but that they
believe would actually execute correctly. Can they modify the type system
(just the rules, not the implementation) to accept it without losing safety?


#### Sequence 4: Session Types and Protocol Compliance

*Experience*

Students implement a simple request-response protocol using raw sockets or
message passing. They deliberately introduce a protocol violation: one side
sends two responses to a single request. The receiving side blocks waiting
for a second response that never comes.

*Reflection*

"The protocol violation was obvious in this small program. How would you
detect the same kind of violation in a system with 20 interacting components?"

LLM-assisted task: "I have a communication protocol. Describe it as a session
type. What does the session type prevent that a regular type system does not?
What does it still not prevent?"

*Conceptualisation*

Introduce session types from `ch07/addition/sessions/THEORY.md`.
The type describes the conversation, not just the values. Duality:
what one side sends, the other must receive.

Connect to the 2FA protocol from ch04: could that protocol be expressed
as a session type? What would the session type say?

*Extension*

Students implement the same protocol using the session type VM from
`ch07/addition/sessions/session_vm.py` and verify that the earlier protocol
violation is now caught by the type checker.


#### Sequence 5: The Central Project

Students choose one of the projects from [PROJECTS.md](./intermediate/PROJECTS.md).

The recommended project for classroom use is **Raft fault injection** (Project 1),
because it produces concrete, discussable failures in a group setting.

For individual study, **algebraic effects composition** (Project 2) or
**session types protocol verifier** (Project 3) are recommended: both are
self-contained and produce type-theoretic results that connect directly to ch08.

*Assessment suggestion:*

Students present their central project by writing a **failure report**: not a
description of what worked, but a structured account of:
1. What failure mode they were trying to study.
2. What they predicted would happen.
3. What actually happened.
4. The difference between their model and reality, and what that reveals.

A project where nothing went wrong is incomplete. If nothing failed, the student
did not push the system hard enough.


#### Self-Study Path

A learner working alone follows this order:
1. Run the race condition experiment. Record results from at least 100 runs.
2. Work through `easy/EXERCISES.md` on concurrency and type systems.
3. Run the Raft implementation. Kill the leader. Observe and document.
4. Implement the linear type checker from `advanced/FOUNDATIONS.md`'s description.
5. Read `ch07/addition/sessions/THEORY.md` and run the session type demo.
6. Choose one project from PROJECTS.md and complete it with a failure report.

*Outcome:*

By the end of this chapter the learner will:
- Have reproduced, explained, and fixed a race condition.
- Understand Raft's safety and liveness guarantees and their limits.
- Have used a substructural type system and understand what it prevents.
- Have implemented or used a session type checker.
- Be able to write a structured failure report for a complex system.
