
## Reflections: What do You Need to Know?

The question of how much knowledge a programmer will need for
architecting systems with large language models (LLMs) in the
future is not straightforward. The answer will likely vary
depending on the role, the domain, and the level of abstraction
at which one chooses to work.

Looking back at earlier technological waves offers useful perspective.
In the 1990s, I was partly interested in web-based 3D technologies,
particularly VRML (Virtual Reality Modeling Language). VRML was designed
to extend ideas from HTML into interactive 3D environments. It
supported animation and promised rich, immersive experiences
directly in the browser. Conceptually, it was exciting. Practically,
however, it faced serious limitations: client-side performance was
often poor, hardware acceleration was immature, and browser support
was inconsistent. As a result, many of its possibilities remained
more theoretical than actually usable.

My interests gradually shifted toward SVG and 2D rendering. These
technologies were simpler, more stable, and better supported.
I eventually built a custom 2D renderer in Java. It performed
significantly better than the default rendering provided by standard
libraries at the time. This hands-on experience proved valuable.
Implementing even a modest rendering engine forced me to confront
issues such as coordinate systems, transformation matrices,
rasterisation trade-offs, buffering strategies, and performance
bottlenecks.

Later, when source code from a Java implementation of Flash
circulated--whether officially authorised or not--certain ideas
that had previously been difficult to reason about became easier
to understand. Seeing concrete implementations demystified abstractions.
Techniques that once seemed opaque became accessible because they
were expressed in working code rather than documentation or theory.

The result of these experiences was not merely a better renderer.
More importantly, it cultivated a deeper intuition about graphical
systems. By building something myself, I developed the ability to
recognise patterns and problems in other rendering technologies.
I could better understand performance limitations, architectural
choices, and design trade-offs. In contrast, with VRML--which I
never attempted to implement--my understanding remained largely
conceptual. Without the friction of implementation, my knowledge
was broader but shallower.

If this always is the case is not that certain. The question about
when to use LLMs, how to work with them, what you should know,
when your knowledge is enough, can be tricky ..

If this pattern were universal, the conclusion would be simple:
deeper technical knowledge always yields deeper understanding.
Yet the reality is more nuanced. The relationship between knowledge
and effectiveness is changing, particularly in the context of LLMs.

With traditional software systems, the boundary between user and
implementer was relatively clear. To build a renderer, a compiler,
or a database, one had to understand algorithms, data structures,
memory behaviour, and performance characteristics. The abstractions
were thin enough that ignorance quickly surfaced as bugs or inefficiencies.

LLM-based systems shift this balance.

A developer can now produce something compelling while understanding
very little about model internals. Prompting, chaining API calls, or
connecting retrieval systems can generate results that appear sophisticated.
In some cases, this is entirely appropriate. High-level abstractions
exist precisely to reduce cognitive load and accelerate development.

However, this ease introduces a subtle risk: the illusion of understanding.

Because LLMs generate fluent language, their outputs often feel like
evidence of reasoning rather than statistical synthesis. A system that
"sounds correct" may mask brittle assumptions, silent failures, or
probabilistic inconsistencies. The friction that once exposed gaps in
understanding is reduced. Errors become less obvious, more semantic
than syntactic.

This leads to a different kind of architectural challenge.

The question is no longer only "How do I build this?" but also:
* What are the model's failure modes in this domain?
* How stable is its behavior across prompts and contexts?
* Where must deterministic logic replace probabilistic output?
* What guarantees can realistically be offered to users?
* How should uncertainty be communicated or constrained?

In other words, judgment becomes central.

Deep knowledge of transformer mathematics may not be required for most
practitioners, just as most graphics programmers no longer implement 
asterisers from scratch. Yet architectural competence increasingly
depends on understanding model behavior, limitations, and emergent properties.

For example:
- A programmer who understands latency and token economics
  will design differently from one who does not.
- A programmer who understands hallucination dynamics will
  validate differently from one who trusts outputs implicitly.
- A programmer who understands embedding drift will monitor
  differently from one who assumes static semantics.

These are not purely theoretical concerns.
They shape reliability, cost, safety, and user trust.

Another important shift concerns determinism.

Classical software engineering is built around predictability. Given the
same inputs, a function returns the same outputs. LLMs operate probabilistically.
Even with temperature set to zero, small variations in context or phrasing
can produce different results. Architectures must therefore absorb
variability rather than eliminate it.

This requires new design instincts:
* Designing guardrails instead of strict rules
* Validating distributions instead of single outputs
* Monitoring behaviors instead of states
* Treating prompts as part of the codebase
* Accepting that some components are inherently stochastic

There is also an epistemic dimension.

When building conventional systems, one could often trace causality: a bug
emerges from identifiable logic. With LLMs, undesired behavior may arise from
training data biases, token interactions, context truncation, or emergent
reasoning artifacts. The "why" behind an output is frequently opaque.

Thus, knowledge itself becomes layered:
1. *Operational knowledge*: how to call APIs, structure prompts, and integrate tools
2. *Behavioral knowledge*: how models respond, fail, drift, and generalise
3. *Conceptual knowledge*. how transformers, embeddings, and training dynamics work
4. *Meta-knowledge*: knowing what cannot be reliably known or controlled

Not every programmer needs to reach every layer. But misunderstanding which
layer one is operating within can lead to fragile systems.

There is a recurring historical pattern here as well.

Early adopters of new technologies often oscillate between overengineering
and overtrust. Some dive deeply into internals prematurely; others treat the
technology as magic. Over time, disciplines stabilise. Best practices emerge.
Tooling matures. Abstractions thicken.

We are still in that formative phase with LLM architectures.

The practical question, then, is not whether deep knowledge is "necessary,"
but when it becomes valuable:
* Valuable when systems must be reliable
* Valuable when stakes are high
* Valuable when costs scale
* Valuable when behavior must be explainable
* Valuable when failure is expensive

Conversely, shallow knowledge may be sufficient:
* For experimentation
* For prototypes
* For creative exploration
* For low-risk applications

The tension between these modes is not a flaw but a characteristic of technological evolution.

Returning to the earlier analogy: implementing a renderer was not required to use graphics,
but it transformed how one thought about graphics. Likewise, studying LLM behavior is not
required to build with LLMs, yet it transforms how one reasons about AI systems.

Perhaps the deeper insight is this:
* In earlier eras, technical complexity limited who could build.
* In the LLM era, cognitive complexity may limit who can build well.

Because building is easier.
But understanding remains hard.

And architecture--as always--lives in the space between
what a system can do and what it can be trusted to do.

