
## Teaching / Learning

*Correctness lives in details that do not show up in ordinary testing.*

This chapter addresses the part of programming that most courses leave implicit:
what happens when programs interact with each other, with time, and with physical
resources. Concurrency, ownership, distributed coordination, and advanced type
systems are not exotic specialisations — they are the conditions under which
most real software runs, and where most subtle failures occur.

The central teaching insight is that bugs in this domain reveal themselves slowly.
A race condition may surface after ten thousand correct runs. A protocol violation
may be masked for months by a reliable network. A use-after-free may be invisible
until a specific allocation pattern triggers it. The classroom must therefore
actively *create* the conditions for failure, not wait for them to arise incidentally.

The chapter builds on ch03 (testing), ch04 (embedded concurrency), and ch05
(type systems). Students who have not yet worked through those chapters will find
this material harder to anchor.


### Teacher Focus

- **Failure as instruction.** Provide broken, unreliable, or violating programs and ask
  students to reproduce the failure before attempting a fix. The ability to reproduce a
  non-deterministic failure is itself a skill.
- **The written model.** Before running any concurrent program, require students to
  write down their model of the possible execution orderings. After running, compare
  the model with what happened. The discrepancy is the lesson.
- **Type systems as verified claims.** When introducing linear types or session types,
  first state the property the type system enforces, then show the program that violates it,
  then show that the type checker catches it. The type checker is evidence for a claim, not magic.
- **Scale last.** Begin with three nodes, two parties, two tasks. Do not introduce
  full-scale distributed systems until the student understands the behaviour of
  the simplest non-trivial case.


### Student Tasks

- Run the race condition experiment. Record the distribution of incorrect outputs.
  Write out a concrete instruction interleaving that produces one of them.
- Trace a Raft leader election by hand, using the protocol rules, before running the code.
- Write a program that a linear type system rejects. Explain why it was rejected
  and whether the rejection was warranted.
- Find at least one LLM explanation of a concurrency concept that is incorrect.
  Write a one-paragraph correction with evidence.
- Complete one project with a **failure report**: what you expected, what happened,
  and what the difference reveals about the system.


### Concrete Exercise: The Unreliable Reviewer

Provide students with a concurrent program that has a subtle bug — a counter
incremented without synchronisation, or a Raft node that accepts two write
operations simultaneously.

Ask students:
1. Read the program. Does it look correct?
2. Run it 1000 times. Record the distribution of outputs.
3. Ask an LLM whether the program is correct. Record its answer.
4. Ask the LLM to explain the bug. Record whether its explanation is accurate.
5. Fix the program minimally.
6. Explain in writing what the LLM got right, what it got wrong, and why.

The goal is not to embarrass the LLM. It is to establish the habit of treating
LLM output as a hypothesis to be tested, not a conclusion to be accepted.
In this chapter especially — where correctness is subtle and failures are
non-deterministic — the LLM's confident tone is itself a risk.


### Example: Teaching the Race Condition

The most common mistake in teaching concurrency is to explain race conditions
before students have seen one. Abstract descriptions of interleaving are difficult
to connect to experience. The lesson starts with experience.

A teacher runs a program that increments a shared counter using two threads.
The program is shown on screen. The expected output is 2000. Run it once: 2000.
Run it again: 2000. Run it ten times: 2000 every time.

Then: run it 10,000 times in a loop. At some point the count is 1997, or 1999,
or 1983. The class sees it.

Now the question is not "could this happen?" but "why did it happen when it did?"

Students write down, step by step, an instruction sequence for two threads that
produces an incorrect result. This is hard the first time. It requires thinking
at the level of individual register operations, not lines of Python. That difficulty
is the point: the mental model that says "this loop runs once, then this loop runs"
is wrong, and the only way to see that it is wrong is to construct the counterexample.

Once the counterexample is on paper, the fix is obvious. The mutex prevents that
interleaving. The atomic operation prevents it more efficiently. The question then
becomes: what did we give up to get that guarantee?

This teaching pattern — see the failure, explain the failure, fix minimally, measure
the cost of the fix — scales from the race condition all the way to Raft consensus.


### LLM Use

LLMs are treated as unreliable reviewers in this chapter.

This is not a claim about LLMs in general. It is a claim about this specific domain:
concurrency and formal correctness are areas where LLMs are known to produce confident
but incorrect explanations. The lesson in using an LLM to explain a race condition
or a type system rule is partly a lesson about when to trust a tool.

Guidelines for this chapter:
- Use LLMs freely for exploring concepts, generating alternative implementations,
  and explaining unfamiliar APIs.
- For every significant LLM claim about a correctness property, run the tool or
  check the specification to confirm.
- In each project, identify at least one LLM explanation that was wrong or incomplete.
  Document it and write the correction.

The habit of disagreeing with a tool on the basis of evidence — rather than
accepting or rejecting on instinct — is what this chapter is designed to develop.
