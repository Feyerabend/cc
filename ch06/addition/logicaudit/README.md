
## The Logic Auditor

> *A framework for trustworthy software in the age of machine-generated code*

### What This Is

This repository presents *Logic Auditing*--a discipline for ensuring that AI-generated
code satisfies formal normative requirements. It synthesises 60 years of formal methods
(purely personal choice of philosophers Stig Kanger and Georg Henrik von Wright through
Alloy and TLA+) with modern verification techniques to address a new challenge:
*how do we trust code we didn't write?*

*Core concept:* Every system has an *admissible space*--the subset of all possible
behaviours that satisfy requirements, regulations, and constraints. The Logic Auditor's
role is to ensure generated code stays within this space.

* *Foundation:* Deontic action logic with first-order semantics
* *Method:* Multi-level verification (types, properties, formal proofs, human reading)
* *Tools:* Alloy, TLA+, property-based testing, type systems, category theory
* *Practice:* Specify norms → generate code → verify admissibility → refine iteratively

Read the full manifesto: [MANIFESTO.md](./MANIFESTO.md)

We will through the book/repository return to use of many of the indicated solutions, such as
property-based testing and dependent types.


### Why This Matters Now

Large Language Models can generate plausible code at scale. But:
- Plausible ≠ correct
- Syntax ≠ semantics
- Compiles ≠ satisfies requirements
- Passes simple tests ≠ handles all edge cases

*Verification is harder than generation.*

The Logic Auditor provides a rigorous framework for verification grounded in formal semantics,
not wishful thinking.



### The Short Version

#### The Problem
LLMs generate code. We need to verify it satisfies normative requirements (security,
correctness, regulations, domain constraints).

#### The Foundation
Define *admissibility predicate* `A(w)`--which system states/behaviors are acceptable.

All norms derive from A:
- *Obligation*: must hold in all admissible worlds
- *Prohibition*: must not hold in any admissible world
- *Permission*: may hold in some admissible world
- *Requirement*: constitutes admissibility itself

This collapses to first-order logic → computationally verifiable.

#### The Practice
1. *Specify* norms formally (obligations, prohibitions, invariants)
2. *Model* admissible space (Alloy/TLA+)
3. *Encode* simple norms as types
4. *Generate* properties from norms (property-based testing)
5. *Prompt* LLM with full specification
6. *Verify* output at multiple levels (types, tests, proofs, reading)
7. *Refine* violations surgically
8. *Document* provenance and decisions
9. *Monitor* in production

#### The Tools
- *Formal methods:* Alloy, TLA+, Z notation
- *Type systems:* Rust, Haskell, OCaml, dependent types
- *Property testing:* Hypothesis, QuickCheck, PropEr
- *Model checking:* Alloy Analyzer, TLC, SPIN
- *Category theory:* For compositional reasoning

#### The Knowledge
Logic Auditors need formal foundations (first-order logic, model theory, type theory),
verification techniques (property-based testing, model checking), semantic modeling
(domain analysis, state spaces, invariants), software craft (deep code reading, architecture),
and LLM collaboration skills.

*This is demanding. Necessarily so.*
Verification is harder than generation.



### Make This Your Own

#### This is *a* manifesto, not *the* manifesto.

We present one approach grounded in deontic logic and formal semantics.
But the field is young and evolving. *You should develop your own.*

#### Questions to explore

*On foundations:*
- Are there better formal systems than deontic logic for normative constraints?
- Can probabilistic logics handle uncertainty in requirements better?
- How do temporal logics integrate with admissibility?
- What role should epistemic logic (knowledge, belief) play?

*On tools:*
- Which verification tools scale to real industrial systems?
- Can we make dependent types practical for everyday use?
- How do we make formal methods accessible to working programmers?
- What's the right balance between automation and human judgment?

*On methodology:*
- Should specification always precede generation?
- How do we handle evolving requirements?
- What's the role of sketching and exploration vs. formal rigour?
- How do different domains (medical, financial, games) change the approach?

*On philosophy:*
- Is curation a legitimate form of craftsmanship?
- What knowledge can only come from direct creation vs. evaluation?
- How does interpretation (hermeneutics) fit with formal verification?
- What's the ethical responsibility of the Logic Auditor?

#### Build your own toolkit!

*Start with curiosity, not dogma.*

- Try different specification languages (Alloy, TLA+, Z, VDM, B)
- Explore type system capabilities (Haskell, Rust, Idris, F*, Lean)
- Experiment with property-based testing frameworks
- Read formal methods literature critically
- Build real systems and see what breaks

*Document your journey:*

- What worked? What failed?
- Where do tools fall short?
- What assumptions proved wrong?
- What new patterns emerged?

#### Create your own manifesto

*We encourage you to:*

1. *Question our assumptions*--We privilege semantic approaches over syntactic. Why? Is this always right?

2. *Extend the framework*--What's missing? Probabilistic norms? Multi-agent systems? Evolutionary requirements?

3. *Simplify where possible*--Is this too heavyweight for some domains? What's the minimal viable verification?

4. *Critique the foundations*--Does first-order reduction lose important structure? Are there better formalisms?

5. *Test in practice*--Apply to real projects. Where does theory meet reality? Where do they diverge?

6. *Build better tools*--The tools we have are good but not great. Make them better. Make new ones.

7. *Write your own synthesis*--Combine ideas from formal methods, type theory, testing, whatever works. Make it yours.

*The field needs diverse approaches.*

Some systems need heavy formal verification. Others need lighter-weight pragmatic checks.
Some domains have stable requirements. Others evolve constantly. *One size does not fit all.*



### Standing on Shoulders: Other Developer Manifestos

This work joins a long tradition of developers articulating principles and practices.
We recommend reading these diverse perspectives:

#### Classic Manifestos

*[The Agile Manifesto](https://agilemanifesto.org/)* (2001)
"Individuals and interactions over processes and tools"

*How we relate: Values flexibility, iteration, collaboration*

*How we differ: We add formal rigor to agile's flexibility*


*[The Reactive Manifesto](https://www.reactivemanifesto.org/)* (2013)
"Responsive, Resilient, Elastic, Message-Driven"

*How we relate: Shared concern for system properties*

*How we differ: We focus on normative correctness, they focus on runtime behaviour*


*[Software Craftsmanship Manifesto](http://manifesto.softwarecraftsmanship.org/)* (2009)
"Not only working software, but also well-crafted software"

*How we relate: Deep respect for quality and mastery*

*How we differ: We argue curation can be craft, they emphasize direct creation*


#### Specific Practice Manifestos

*[The Twelve-Factor App](https://12factor.net/)* (2011)
Principles for building software-as-a-service

*Complements our approach: Good architecture + formal verification = trustworthy systems*

*[Test-Driven Development](http://www.extremeprogramming.org/rules/testfirst.html)*
Write tests before code

*We extend: Tests specify norms → LLM generates → tests verify*

*[Design by Contract](https://www.eiffel.com/values/design-by-contract/)* (Bertrand Meyer)
Preconditions, postconditions, invariants

*Direct ancestor: We formalize contracts as norms over admissible worlds*

#### Philosophical/Cultural

*[The Cathedral and the Bazaar](http://www.catb.org/~esr/writings/cathedral-bazaar/)* (Eric S. Raymond, 1999)
On open source development

*Orthogonal: We care about verification method, not development model*

*[Unix Philosophy](https://en.wikipedia.org/wiki/Unix_philosophy)*
"Do one thing well", "Composition over monoliths"

*We embrace: Compositional verification, modular reasoning*

*[Hammock-Driven Development](https://www.youtube.com/watch?v=f84n5oFoZBc)* (Rich Hickey)
Think before you code

*We amplify: Specify before you generate*

#### Contemporary/Recent

*[Indie Web Manifesto](https://indieweb.org/principles)*
Own your data, scratch your own itch

*Different domain: We focus on verification, they focus on independence*

*[Ethical Source](https://ethicalsource.dev/)*
Software freedom with social responsibility

*Shared concern: Responsibility for what we build*

#### Academic/Formal

*[The Curry-Howard Correspondence](https://en.wikipedia.org/wiki/Curry%E2%80%93Howard_correspondence)*
Programs are proofs, types are propositions

*Foundation: We use types to encode norms*

#### What We Learn From These

*Common threads:*
- Articulating principles makes them discussable
- Practices need philosophical grounding
- Tools alone don't solve problems
- Communities form around shared values

*Our contribution:*
- Formal semantics for normative verification
- Multi-level verification strategies
- Framework for LLM collaboration
- Bridge from philosophy (Kanger) to practice (Alloy)

*Where we fit:*
- More formal than Agile, less dogmatic than Waterfall
- More rigorous than TDD, more practical than pure formal methods
- Embraces craftsmanship through curation, not just creation
- Adds verification layer to any development methodology



### Your Turn: A Template

If you want to develop your own manifesto or framework, consider:

#### 1. Identify the Problem
What challenge are you addressing? Be specific.
- What fails in current practice?
- Why do existing solutions fall short?
- What's the concrete pain point?

#### 2. Articulate Core Principles
What fundamental truths ground your approach?
- What do you believe about software, verification, quality?
- What trade-offs do you make?
- What hills will you die on?

#### 3. Define the Practice
How do you actually work?
- What's your workflow?
- What tools do you use?
- What skills are required?

#### 4. Show Concrete Examples
Theory needs grounding.
- Real code samples
- Actual specifications
- Specific tools and commands
- Before/after comparisons

#### 5. Acknowledge Limitations
Where doesn't your approach apply?
- What domains are out of scope?
- What problems don't you solve?
- What are honest drawbacks?

#### 6. Provide Entry Points
How can others start?
- Simple first steps
- Learning resources
- Starter projects
- Community/mentorship

#### 7. Invite Evolution
Your framework will change.
- What are open questions?
- Where do you need help?
- What might you be wrong about?



### Resources to Get Started

#### Learn the Foundations

*Formal Methods:*
- *Software Abstractions* by Daniel Jackson (Alloy)
- *Specifying Systems* by Leslie Lamport (TLA+)
- *Logic in Computer Science* by Huth & Ryan
- [Hillel Wayne's Practical TLA+](https://learntla.com/)

*Property-Based Testing:*
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- *Property-Based Testing with PropEr, Erlang, and Elixir* by Hebert
- [QuickCheck Tutorial](https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quick.pdf)

*Type Theory:*
- *Types and Programming Languages* by Pierce
- *Programming in Haskell* by Hutton
- *The Little Typer* by Friedman & Christiansen

*Deontic Logic:*
- Hilpinen (Ed.), *Deontic Logic: Introductory and Systematic Readings* (1971)
- von Wright, "Deontic Logic" (Mind, 1951)
- Kanger, "New Foundations for Ethical Theory" (1957)

*Category Theory (Applied):*
- *Category Theory for Programmers* by Milewski
- [Seven Sketches in Compositionality](https://arxiv.org/abs/1803.05316)
- *Categories for the Working Mathematician* by Mac Lane (advanced)

#### Practice the Skills

*Start Simple:*
1. Pick a small program (to-do list, shopping cart)
2. Write norms in plain English
3. Formalize one norm in Alloy
4. Generate test cases from that norm
5. Get one property test passing

*Build Up:*
1. Model a full system in Alloy
2. Generate code (manually or via LLM)
3. Verify against specification
4. Find where they diverge
5. Iterate

*Go Deep:*
1. Pick a critical domain (medical, financial)
2. Study real regulations
3. Formalize as norms
4. Build a verified implementation
5. Write about what you learned



### Take This Project Further ..

We welcome:

- *Critiques:* Where are we wrong?
- *Extensions:* What's missing?
- *Examples:* Show the practice in action
- *Tools:* Build better verification workflows
- *Educational material:* Help others learn
- *Alternative manifestos:* Your own synthesis

This is a living document. The field is young. *Make it better.*



### Acknowledgments

This work stands on 60 years of formal methods:

- *Stig Kanger* (1957)--semantic foundations for deontic logic
- *G.H. von Wright* (1951)--deontic operators and action logic
- *Daniel Jackson* (2000s)--Alloy and lightweight formal methods
- *Leslie Lamport* (1990s-2000s)--TLA+ and temporal logic
- *Koen Claessen & John Hughes* (1999)--QuickCheck and property-based testing

And the ongoing work of countless researchers, practitioners, and tool builders.



### Final Words

*To students:*
Don't accept this framework uncritically.
Build your own.
Question everything.
Make it better.

*To practitioners:*
Try these ideas in practice.
See what works.
Report what doesn't.
Iterate.

*To researchers:*
The tools need improvement.
The theory needs extension.
The bridge to practice needs strengthening.

*To everyone:*
LLMs are here.
The code they generate needs verification.
