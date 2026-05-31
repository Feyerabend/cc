## Foundations: Correctness, Evidence, and the Limits of Testing

### 1. Debugging as Hypothesis Testing

Programming is often described as a craft of construction, but debugging is a craft
of investigation. The investigator begins with an observation — an unexpected output,
a crash, a silent wrong answer — and must reason backward to a cause. This is not
primarily a technical skill. It is an epistemic one.

The scientific method applies directly. A hypothesis about a bug's cause is a
falsifiable claim about the program's state or behavior. A good debugging hypothesis
names a specific component, condition, or assumption that, if wrong, would produce
the observed failure. A bad one is too vague to be tested.

The *null hypothesis* in debugging states that the suspected cause is not responsible.
This is worth maintaining explicitly because it counteracts a natural cognitive bias:
confirmation bias leads investigators to seek evidence that confirms what they already
believe, rather than evidence that could change their mind. A null hypothesis forces
the question: what would I need to observe to rule this out?

Edsger Dijkstra, one of the founders of formal software engineering, distinguished
sharply between *testing* (demonstrating the presence of bugs) and *verification*
(demonstrating the absence of bugs). Testing can never guarantee correctness, but it
can establish evidence. The quality of that evidence depends on how carefully the
tests were designed to challenge, not merely confirm.


### 2. Testing as an Epistemic Practice

A test suite is not just a safety net. It is a body of claims about a program's behavior.

Each test encodes a belief: "When given this input, the program should produce this output."
Running the test checks whether that belief is currently accurate. A failing test means
the belief is false — either the program is wrong, or the belief itself was wrong.
Both are valuable discoveries.

This perspective reveals several things that are easy to miss.

First, tests are only as good as the beliefs they encode. A test suite that only checks
easy cases gives strong evidence for easy cases. A program that fails on surprising or
adversarial inputs is not revealed by tests that do not include them. This is why
mutation testing is informative: it asks not "do the tests pass?" but "are the tests
capable of distinguishing between this program and a slightly wrong version?"

Second, tests are always incomplete. No finite test suite can cover all possible inputs
for a non-trivial program. Property-based testing acknowledges this by testing
*classes* of inputs, generated randomly. Fuzzing acknowledges this by treating the
input space as an adversary.

Third, coverage metrics measure what was executed, not what was understood. One hundred
percent line coverage can coexist with serious specification gaps. A program can execute
every line with correct outputs on every tested input and still behave wrongly on inputs
that were never tried.


### 3. The Empirical Programmer

There is a tradition in software engineering that treats the programmer as an empiricist.
The program is a model; running it produces observations; those observations either
confirm or challenge the model. Bugs are not failures of moral character or attention;
they are predictions that turned out to be wrong.

This empirical stance has practical implications. It means that the goal of debugging
is not to fix the symptom but to identify the mismatch between the programmer's mental
model and the program's actual behavior. Without correcting the mental model, the same
kind of bug will recur.

It also implies something about programming culture: an environment in which bugs are
punished makes programmers hide evidence and avoid investigation. An environment in
which bugs are treated as data makes programmers better at finding and understanding them.


### 4. Optimisation as Tradeoff

Optimisation is not the same as making a program faster. It is the process of moving
a program closer to some goal, with the constraint that other properties must be
preserved.

The goals of optimisation vary:
- Execution time (latency, throughput, worst case)
- Memory usage (peak, average, fragmentation)
- Power consumption (especially important in embedded systems, ch04)
- Code size (for constrained environments)
- Readability, maintainability (sometimes in deliberate tension with the above)

These goals frequently conflict. Code that runs faster often uses more memory.
Code that uses less memory often runs slower. Code that has been heavily optimised
for performance is often harder to maintain. Optimisation is always a tradeoff.

Knuth's warning — "premature optimisation is the root of all evil" — is widely quoted
but frequently misunderstood. He was not saying that performance does not matter.
He was saying that optimising before you have measured is a form of speculation,
and that speculation about performance is usually wrong. Profile first. Optimise second.

This connects to testing: before optimising, you need a test suite that will detect
regressions. An optimisation that breaks correctness is not an optimisation.


### 5. The Relationship Between Testing and Formal Verification

Testing and formal verification sit at opposite ends of a spectrum of confidence.

Testing gives empirical evidence: "this program behaved correctly on these inputs."
The confidence it provides scales with the size and quality of the test suite,
but it is never absolute.

Formal verification gives deductive evidence: "this program satisfies this property
for all possible inputs." The confidence it provides is absolute within the scope
of the formal model, but that model is itself a simplification, and errors in the
specification are not caught by the verification.

In practice, the two approaches are complementary. Testing is fast and finds bugs
quickly during development. Formal verification is slow and expensive but provides
a level of assurance that testing cannot. For safety-critical software, both are used.

The tools in `ch08/addition/z3` and `ch08/addition/model` give concrete examples of
what formal verification looks like in practice. Chapter 3's tools — mutation testing,
property-based testing, coverage measurement — can be seen as the testing end of
the same continuum.


### 6. Build Tools and Reproducibility

Debugging is only possible if the program under investigation is the program that
was actually deployed. This obvious requirement is surprisingly hard to satisfy.

A build system is a specification of how source code is transformed into executables.
If the build is not reproducible — if running the build twice does not produce the
same output — then a bug found in a deployed binary may not be present in the locally
built binary, and vice versa. This is a form of environmental non-determinism, and it
is one of the most common sources of "it works on my machine" failures.

The `ch03/sec3.5.1` material covers CI (Continuous Integration) and Make. These are
not merely convenience tools. They are instruments of reproducibility. A Makefile
encodes the dependency structure of a build. A CI pipeline ensures that the build
is always executed in a controlled, documented environment. Together they close the
gap between "the code" and "the running program."

The connection to testing is direct: a test suite is only meaningful if it is run
consistently. A test that passes locally but fails in CI is a symptom of an
irreproducible environment.
