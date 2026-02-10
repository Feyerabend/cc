
## On Tests, Understanding, and Craft


### What Tests Are

Tests are *documentation of behaviour*. Not intent, not aspiration, but what actually happens when
code runs. When a comment says "this validates input," a test proves "this accepts 'café' and rejects 'key-name'."
Tests are evidence.

When you write `assertEqual(result, "Invalid command")` and the test fails with
`AssertionError: 'Added key: value' != 'Invalid command'`, you've learned something true about the system.
The test becomes a record of that truth.

Tests accumulate knowledge. Each test is a small assertion: "I checked this, and here's what I found."
Over time, a test suite becomes a map of the territory--not the territory itself, but a faithful
representation of what exists.

Comments written by programmers generally aim to clarify the author’s intention and the intended
use of the code.


### What TDD Is

*Test-Driven Development* is a methodology with a specific rhythm: write a failing test, make it pass, refactor.
Red, green, refactor. Repeat. It's a discipline, a practice, a set of steps you can follow.

TDD emerged when writing code was slow and changing code was dangerous. Tests first meant thinking through
the interface before implementation. It forced clarity. It prevented waste. You wouldn't spend an hour
implementing something only to discover you'd misunderstood the requirement.

TDD treats tests as *design tools*. The test shapes the code that follows. The interface emerges from
thinking about how you want to use something before building it. This is valuable, it creates external
pressure toward simplicity and usability.

But TDD also locks down progress. You cannot write code without first writing a test. You must know what you
want before you can build it. This assumes a kind of certainty: that you understand the problem well enough
to specify the solution before exploring it.


### The Difference Between Philosophy and Methodology

A methodology tells you what to do. TDD says: write test, watch it fail, make it pass, clean up the code.
You can observe whether someone is "doing TDD" or not.

A philosophy tells you how to think. The philosophy underlying TDD includes beliefs: that tests improve design,
that small steps reduce risk, that feedback should be fast and constant. You can practice TDD without embracing
these beliefs, or embrace the beliefs without strict TDD practice.

This distinction matters because methodologies can be adopted or abandoned based on context. TDD works well here,
less well there. But the philosophical commitment to testability, to verification, to understanding, these
transcend any specific practice.



### Tests as Discovery

Writing tests can naturally occur outside of TDD. We can write tests that expected certain behaviour, run them,
and discover the actual behaviour. We can discover that the actual behaviour is different during coding, and we
update the tests to document reality.

This is exploratory testing. Tests become tools for understanding existing systems rather than shaping new ones.
Each failure reveals something: "I thought spaces in keys would be rejected - but they're actually accepted,
treating the first word as the key."

These tests accumulate into regression suites. They say: "This is how the system behaves. If this changes, we
want to know." They're not driving development forward, but they're maintaining understanding of what already exists.

This approach treats tests as scientific instruments. You form a hypothesis ("command injection should fail"),
run an experiment (the test), observe the result ("actually, the string is stored as-is"), and document your
findings (update the test).


### Literate Programming's Alternative

To make a contrast. Literate programming, as conceived by Donald Knuth, interweaves code and explanation. You
write for human readers, explaining your thinking as you develop. The code emerges from the narrative rather
than the narrative being added after.

Where TDD says "specify behaviour, then implement," literate programming says "explain what you're doing as you discover it."
It's fluid rather than rigid. You can explore, backtrack, reconsider. The act of explaining forces clarity, but
it doesn't require pre-commitment to specific behaviours.

Tests in a literate programming context become part of the explanation: "Here's what happens when we pass spaces.
Here's what happens with unicode. Here's the edge case I discovered." They document the journey of understanding.

TDD and literate programming exist in tension. TDD wants tests first, locking down behaviour. Literate programming
wants understanding first, with behaviour emerging. One is disciplined and constrained, the other is exploratory
and expressive.


### The LLM Shift

LLMs change the economics of code generation. What took hours now takes seconds. You can ask for an implementation,
evaluate it, ask for a different approach, compare them. Iteration becomes nearly free.

This shifts what's valuable. When writing code was slow, TDD's discipline prevented wasted effort. When humans made
typos constantly, tests caught simple errors. When thinking through design was hard, tests forced that thinking.

But now:
- Generating code is fast: the bottleneck isn't typing
- LLMs rarely make syntax errors: tests catch semantic mismatches
- You can generate multiple designs rapidly: exploration has less cost

The question becomes: where should you spend your limited time? Writing tests before implementation, or generating
implementations and testing them after?

TDD assumed code generation was the expensive part. If testing becomes the expensive part, the calculus changes.


### The Craftsperson's Question

A craftsperson develops deep understanding through direct engagement with materials. A woodworker knows how grain
behaves, how different woods respond to tools, how joints bear weight. This knowledge comes from doing.

In software, the traditional craft was writing code. You understood it because you wrote it, line by line. TDD was
a craft practice: the ritual of red-green-refactor, the discipline of small steps, the accumulation of mastery through
repetition.

When an LLM writes code, something changes. You specified what you wanted, reviewed what appeared, perhaps tested it.
But did you understand it the same way? Is it your craft, or are you now more of a director, a curator, a verifier?

This isn't inherently bad or good. It's different. The craft might be shifting. Perhaps the craftsperson's role becomes:
- Understanding systems deeply enough to verify them
- Asking the right questions to reveal behaviour
- Maintaining institutional knowledge through documentation
- Ensuring quality through comprehensive testing

Your regression tests are craft work in this new mode. You're exploring the system, discovering its edges, documenting
what you find. The tests are yours in a way the generated code might not be. They represent your understanding, your
curiosity, your standards.


### What Tests Can Be

- Tests can be *specifications*: "the system must do this." This is TDD's view. Tests define correctness before implementation exists.

- Tests can be *documentation*: "the system actually does this." This is the regression view. Tests record observed behaviour, creating a reference for future changes.

- Tests can be *exploration*: "what happens if we try this?" This is the scientific view. Tests are experiments that reveal system properties.

- Tests can be *communication*: "this is what we care about." This is the team view. Tests make implicit requirements explicit, creating shared understanding.

- Tests can be *safety nets*: "don't break this." This is the refactoring view. Tests enable change by catching unintended consequences.

- Tests can be *design pressure*: "if this is hard to test, maybe the design is wrong." This is the architectural view. Tests reveal coupling, complexity, hidden dependencies.

None of these are mutually exclusive. A single test can serve multiple purposes. But the emphasis shifts based on context and goals.


### The Way Forward

Perhaps the question isn't "should we do TDD?" but rather "what role should tests play in our process?"

If you're exploring unfamiliar territory, tests as discovery tools make sense. Write code, probe its behaviour,
document what you find. Let understanding emerge.

If you're building on stable foundations with clear requirements, tests as specifications make sense.
Define behaviour upfront, then implement to match.

If you're maintaining complex systems, tests as documentation and safety nets make sense.
Capture current behaviour, prevent regression, enable confident change.

If you're working with LLMs, tests as verification make sense. Generate quickly, test thoroughly, iterate based on findings.

The craft might be in choosing the right approach for the context, rather than committing dogmatically to one methodology.
TDD is a tool. So is exploratory testing. So is literate programming. The craftsperson knows which tool fits the work at hand.


### On Understanding

This is perhaps the deepest value of tests: they force confrontation with reality. Code can be elegant in theory and broken in practice.
Tests show you which. They're uncomfortable when they fail, failure means your mental model was wrong, but that discomfort is where
learning lives.

Whether you write tests first (TDD) or after (regression), whether you generate code with LLMs or craft it by hand, whether
you follow rigid methodologies or fluid exploration: tests remain valuable because they anchor understanding in observable behaviour.

TDD, literate programming, LLM-assisted development, craft .. are approaches to the work. They have different strengths, different
costs, different contexts where they shine. But they all ultimately serve the same goal: creating software that works, that you
understand, that you can maintain and evolve.

Tests are the through-line. They're how you know what you've built. They're how you remember what you learned. They're how you
preserve understanding over time, across people, through change.
