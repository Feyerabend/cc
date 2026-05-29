## Foundations: Craftsmanship, Judgment, and the New Landscape of Programming

### 1. Craftsmanship as a Historical Idea

The metaphor of programming as a craft has a long and contested history.

In the early decades of software engineering, the dominant metaphor was engineering itself:
programs should be built like bridges, from precise specifications, using proven methods,
with predictable outcomes. This metaphor drove the structured programming movement, the
waterfall model, and the emphasis on formal specification. It was a response to genuine
problems — software projects were failing catastrophically — and it imported the discipline
of engineering as a corrective.

The craftsmanship metaphor emerged as a counterpoint, most explicitly in the Agile movement
and in the Software Craftsmanship Manifesto. It emphasised skill developed through practice,
judgment that cannot be fully codified, responsibility to the quality of the work, and
mentorship as the primary mode of knowledge transfer. These are the properties of a craft
in the pre-industrial sense: a body of tacit knowledge, held by skilled practitioners, passed
from person to person through example and correction.

Both metaphors capture something true. Software development requires both the engineer's
rigour and the craftsman's judgment. The tension between them — between what can be
specified and what must be felt — is one of the permanent tensions of the field.


### 2. What LLMs Change (and What They Do Not)

The emergence of LLMs capable of generating plausible code forces a re-examination of
both metaphors.

For the engineering metaphor, LLMs are a tool with a known error rate. You specify what
you want; the tool produces an approximation; you verify the result. This is a familiar
engineering workflow. The novelty is that the tool's errors are not random and not
systematic in the usual sense — they are contextually plausible failures that are
difficult to detect without domain knowledge.

For the craftsmanship metaphor, the challenge is deeper. Craftsmanship assumes that
expertise is developed through the labour of building. If an LLM performs the labour,
does the expertise still develop? This is the deskilling question, and it has no
simple answer. It depends on how the tool is used, what cognitive work it replaces,
and whether the programmer engages critically with its output or accepts it passively.

What LLMs do not change: the need to understand what a program does. This need
is, if anything, greater when programs are generated rather than written. A generated
program is a hypothesis about what you want. Verifying that hypothesis requires
exactly the skills that craftsmanship was meant to develop.


### 3. The Logic Audit as a Practice

The logic audit (`ch06/addition/logicaudit/`) is a systematic attempt to apply
critical reading to code. It asks a question that is surprisingly rare in software
engineering: does this code do what its authors claim?

Most code review focuses on style, performance, and obvious bugs. The logic audit
goes further. It checks invariants — properties claimed to always hold — and
whether the code actually maintains them. It checks comments — descriptions of what
code does — and whether those descriptions are accurate. It checks error handling —
what happens when things go wrong — and whether those paths have been thought through
with the same care as the happy path.

This is related to, but distinct from, formal verification. Formal verification
provides a proof that a property holds. The logic audit provides a human judgement
about whether the evidence for a property is adequate. It is closer to scientific
peer review than to formal proof — less certain, but faster, and applicable to a
wider range of code.

The logic audit matters most in exactly the cases where LLMs are most plausible:
code that looks correct but has not been reasoned about carefully. LLM-generated
code can have the surface features of good code — consistent style, reasonable
naming, appropriate comments — while embodying faulty assumptions or missing edge
cases. The logic audit is a discipline for detecting this class of failure.


### 4. Design as Decision-Making Under Constraints

The d06 README frames programming as "decision-making under constraints." This is
worth unpacking.

Every design decision is made against a background of constraints: requirements that
must be met, resources that are limited, schedules that are fixed, interfaces that
cannot change. Some constraints are real and some are assumptions. One of the most
valuable skills in software design is distinguishing between them.

Constraints interact. A decision that satisfies one constraint may violate another.
Choosing a fast algorithm may increase memory usage. Choosing a simple interface may
limit extensibility. Choosing to use a library reduces implementation effort but
introduces a dependency. These tradeoffs cannot be resolved by a rule; they require
judgment about which constraints matter most in the current context.

This is why design cannot be fully automated — not even by an LLM. An LLM can
generate code that satisfies stated constraints. It cannot identify which unstated
constraints matter, or judge how constraints will change as the system evolves.
These require an understanding of *why* the constraints exist, which requires
knowledge of the context that the programmer has and the model does not.


### 5. Documentation as Thought

Good documentation is not a description of what code does. That information is
already in the code. Good documentation explains *why*: why this design was chosen
over the alternatives, what problem this code is solving and why it is a problem,
what invariants this module depends on, what assumptions it makes about its environment.

The JHotDraw codebase in `ch06/addition/documentation/` provides a large-scale example.
JHotDraw is one of the most carefully documented Java codebases from the era of
design-pattern-based programming. Its documentation was written by programmers who
believed that patterns were a vocabulary for design decisions. Looking at it now
reveals both the value of that vocabulary and its limits: it describes structure
well, but the reasons behind the structure are often left to be inferred.

This connects to the logic audit: documentation that describes what the code does
is easy to write and of limited value. Documentation that explains the reasoning
behind design decisions is rare and valuable. The discipline of writing good
documentation is partly the discipline of understanding your own design well enough
to explain it.


### 6. The Future of Programming Practice

The materials in `ch06/addition/future/` and `ch06/addition/deskilling/` ask a
question that this chapter cannot fully answer: what will the practice of programming
look like in ten or twenty years, given the trajectory of AI tools?

Several scenarios are possible:

In one, LLMs become reliable enough to handle routine coding tasks almost completely.
Programmers become primarily specifiers, reviewers, and architects. The skills of
careful reading, system-level reasoning, and verification become central, while the
skills of syntax and API memorisation become less so. This shifts the craft but does
not eliminate it.

In another, LLMs remain useful assistants that handle some tasks well and fail
unpredictably on others. The programmer's judgment about when to trust the tool
becomes a critical skill. The ability to detect subtle errors in plausible-looking
code — the logic audit in practice — becomes essential.

In a third, the proliferation of AI-assisted development produces a large body of
code that no individual fully understands. Maintenance of such systems requires
new tools and new practices. The relationship between programmer and code changes
from author to archaeologist.

What seems clear is that the skills that matter most in all three scenarios are not
the skills that are easiest to develop: careful reading, systematic thinking, the
ability to reason about what a system does and why. These are the skills that the
craftsmanship tradition valued. Whether they are called craftsmanship or something
else, they remain the core of what it means to program well.
