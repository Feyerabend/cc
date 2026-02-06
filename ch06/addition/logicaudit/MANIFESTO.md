
### The Logic Auditor Manifesto

*For the age of machine-generated code*

*Version 2.0 - February 2026*




### Part I: The Problem

#### I. The Crisis

We stand at a peculiar juncture.

Machines can now write code. Not perfectly, but plausibly. Fast enough to seem useful. 
Good enough to be dangerous.

The old model breaks: *write code -> understand through writing -> maintain what you built*.

The new reality: *describe intent -> machine generates -> ??? -> hope it works*.

That middle step—the ???—is where everything fails or succeeds.

*We need a new discipline.*


#### II. The Core Problem

*The question is not: "Can machines write code?"*

They can. They do. Daily. Millions of lines.

*The question is: "Can we trust what they write?"*

And deeper: *"Can we even tell?"*

*The problem:*
- LLMs generate plausible code, not necessarily correct code
- Syntax correct ≠ semantics correct ≠ norms satisfied
- Verification is harder than generation (and always will be)
- Understanding code you didn't write is harder than writing it yourself
- The cost of undetected errors escalates with deployment scale

*The traditional answer fails:*
"Just review it carefully"—but how? By what standard? With what tools?
Human code review catches perhaps 60% of defects. For AI-generated code with no implementation intuition, likely less.

*We need formal foundations.*


#### III. The Fundamental Insight

*Every system has an admissible space.*

- Not all behaviors are acceptable
- Not all states are valid
- Not all futures are permitted

*The boundary between acceptable and unacceptable is normative.*

- In mathematics: constraints define solution spaces
- In law: norms define permissible actions
- In software: requirements define admissible executions

*This is not new. We've been doing this for 60 years.*

What's new: machines generating code at scale that must satisfy these constraints—and the inversion of the bottleneck from generation to verification.


#### IV. The Semantic Foundation

*Normativity = World Selection*

- Let W be all possible system behaviors
- Let A ⊆ W be the admissible subset

*Everything derives from A:*

- *Obligation*: What must hold in all admissible worlds:
`O φ ≡ ∀w ∈ A: φ(w)`

- *Prohibition*: What must not hold in any admissible world:
`F φ ≡ ∀w ∈ A: ¬φ(w)`

- *Permission*: What may hold in some admissible world:
`P φ ≡ ∃w ∈ A: φ(w)`

- *Requirement*: What constitutes admissibility itself:
`R φ ≡ [O φ ∧ removing φ expands A]`

*This is not modal mysticism. This is first-order logic over explicit structures.*

```
Deontic operators -> First-order quantification -> Computational verification
```

*The bridge from philosophy to software engineering.*


#### IV.5 The Inversion

*Why formal methods failed to achieve widespread adoption (1970-2020):*

Cost(specification) > Cost(bugs in production)

Writing formal specs was slower and more expensive than fixing problems after deployment. For most software, this was rational.

*Why LLMs change everything (2023->):*

Cost(generation) < Cost(verification) < Cost(undetected failures)

Code generation is now FASTER than verification. The bottleneck inverts. We have too much unverified code.

*Specification becomes the cheaper approach:*
- Specify once, generate many candidate implementations
- Test all candidates against specification automatically
- Select best-performing verified implementation
- Regenerate when requirements change

*Plus:* The tools matured simultaneously (Alloy 2000s, property testing 2010s, practical type systems 2020s, capable LLMs 2023).

*The pieces were waiting for this moment.*




### Part II: The Solution

#### V. The Role We Need

*The Logic Auditor*

Not a programmer in the traditional sense.
Not a code reviewer in the old meaning.
Not a tester in the conventional role.

*A new discipline:*

The Logic Auditor is a *normative systems analyst* who ensures machine-generated code inhabits admissible worlds.

*But more precisely: The Logic Auditor is a curator.*

Programming becomes *curation*—the skillful orchestration and refinement of:
- Problem decompositions
- Specification quality across multiple formalizations
- Verification strategies (types, tests, proofs, manual analysis)
- Generated solutions from multiple candidates
- Normative priorities when requirements conflict
- Risk acceptance for what remains unverified

*This IS craftsmanship—the craft of discernment and composition.*

The "material" is no longer code syntax. *The material is the admissible space A itself.*

- You *shape* A through specification
- You *explore* A's boundaries through countermodels
- You *test* A through property-based generation
- You *refine* A through understanding violations
- You *defend* A through multi-level verification
- You *document* A for future maintainers

*The craft isn't lost—it's elevated to the semantic level.*

But this elevation only works if you first mastered the syntactic level. You cannot audit what you cannot implement. More on this in Section XI.


#### VI. The Eight Crafts of the Logic Auditor

*Their practice requires mastery of:*

1. *Hermeneutic understanding*—interpreting what the domain *means*
 Not just stakeholder requirements, but the deep structure of the problem space. What could go catastrophically wrong? What assumptions are embedded in current practice? What are the true constraints beyond stated requirements?

2. *Formal modeling*—encoding meaning as first-order predicates
 Translating human understanding into machine-checkable logic. The gap between informal and formal is where most errors hide.

3. *Admissibility definition*—establishing the boundary of acceptable behavior
 This is the core craft. Not just "what should happen" but "what space of behaviors is permitted." The skill is knowing where the line is, not just what's clearly on each side.

4. *Countermodel identification*—making forbidden states explicit
 Don't just specify what's allowed—specify what's *prevented*. Explicit countermodels reveal assumptions and prevent regression.

5. *Verification orchestration*—using all available tools strategically
 Types, tests, proofs, manual reading—each catches different error classes. The art is knowing which tool for which property and when to combine them.

6. *Prompt engineering*—guiding generation with normative specifications
 The LLM is a tool with its own grain. Learning what it does well, what it does poorly, how to constrain its output space through careful specification.

7. *Code reading*—deep analysis of machine output against semantic models
 Reading generated code is different from reading human code. It has different failure modes. No "author's intent" to intuit—only statistical patterns. Requires heightened vigilance.

8. *Surgical refinement*—correcting violations while preserving valid aspects
 When verification fails, precise diagnosis and minimal correction. Don't regenerate everything—understand what failed and fix only that.

*This is craft, but intellectual rather than manual.*

The "tool feel" comes from sensitivity to norm violations.
The "material resistance" comes from undecidability and complexity limits.
The "mastery" comes from judgment about what to verify how.


#### VII. The Method (Nine Phases)

##### Phase 0: Understand (Hermeneutic)

Before any formalism, understand the domain.

- What are we really building?
- What could go catastrophically wrong?
- What are the true constraints, beyond stated requirements?
- What assumptions are embedded in current practice?
- What are the failure modes of similar systems?
- What do experts know that's never written down?

*Output: Conceptual model—narrative understanding of the problem space*

*Warning:* Rushing past this phase produces formally verified systems that solve the wrong problem.


##### Phase 1: Specify (Deontic)

Formalize admissibility.

1. Define worlds W (states, trajectories, executions)
2. Define predicates over worlds (Borrowed, Paid, InStock, Shipped, Authorized)
3. Define norms (obligations, prohibitions, permissions, invariants)
4. Establish priorities (critical, high, medium, low—with justification)
5. Compute admissibility A from norms and priorities
6. Identify countermodels w₁, w₂, ... explicitly—the forbidden states
7. Document conflicts and trade-offs where norms compete

*Output: Formal specification in first-order logic with explicit priorities*

*Warning:* This is where most errors enter. Invalid specifications -> useless verification.


##### Phase 2: Explore (Formal Methods)

Understand the admissible space before generating code.

- Encode in Alloy or TLA+ or Z notation
- Generate example admissible worlds (does A contain what we expect?)
- Find counterexamples to proposed properties (does A exclude what we expect?)
- Refine specification based on findings
- Validate consistency of norms (can A even exist?)
- Check that A is not empty (are requirements satisfiable?)
- Check that A is not everything (are requirements meaningful?)

*Output: Validated formal model with concrete instances and confirmed non-vacuity*

*Warning:* Models can be consistent but wrong. Generate many instances. Develop intuition for the space.


##### Phase 3: Encode (Type Systems)

Make simple violations impossible by construction.

- Design type structure reflecting domain ontology
- Encode preconditions as type constraints
- Use phantom types for state machines
- Leverage refinement types where available (Liquid Haskell, F*)
- Make illegal states unrepresentable
- Use affine/linear types for resource management (Rust, ATS)

*Output: Type signatures that enforce basic norms*

*Coverage:* Types typically enforce 20-40% of total norms. They catch errors instantly but can't express all properties.


##### Phase 4: Specify Tests (Property-Based)

Translate every norm into executable properties.

```
O φ->∀w ∈ A: φ(w) ->property test "φ always holds"
F φ->∀w ∈ A: ¬φ(w)->negative property "φ never holds"
R φ->∀execution: φ->invariant test "φ throughout"
```

Generate thousands of random test cases automatically.
Use shrinking to find minimal counterexamples.
Build stateful property tests for complex protocols.

*Output: Comprehensive property-based test suite*

*Coverage:* Properties typically find 60-80% of semantic errors types miss. Empirical, not exhaustive.


##### Phase 5: Generate (LLM Collaboration)

Prompt with full normative context.

Include in prompt:
- Type signatures (constrain output space)
- Formal norms with priorities (specify requirements)
- Example admissible worlds (show correct instances)
- Explicit countermodels to prevent (show incorrect instances)
- Preconditions and effects (specify contracts)
- Invariants that must hold (specify constraints)
- Performance requirements (guide algorithm choice)

Generate 3-5 candidate implementations.
Explore different approaches (recursive vs iterative, pure vs stateful, etc.).

*Output: Multiple candidate implementations with full context*

*Strategy:* Diversity in generation creates options for verification. One may verify where others fail.


##### Phase 6: Verify (Multi-Level)

Check admissibility at every level.

1. *Type check*—catches basic violations instantly (automated)
2. *Property test*—finds empirical countermodels through random generation (automated)
3. *Formal verify*—proves absence of violations for critical properties (semi-automated)
4. *Manual read*—deep semantic analysis, hermeneutic interpretation (human judgment)
5. *Priority check*—ensure high-priority norms satisfied, document trade-offs (human judgment)

*Verification is stratified by criticality:*

- *Critical norms* (safety, security): Require formal proof or extensive property testing + manual analysis
- *High norms* (correctness, performance): Property testing + code review
- *Medium norms* (maintainability, style): Type checking + spot review
- *Low norms* (convenience, elegance): Accept best-effort

*Output: Verified implementation with documented verification levels OR detailed violation report*

*Reality check:* Perfect verification is asymptotic. We verify what matters most and acknowledge what remains uncertain.


##### Phase 7: Refine (When Needed)

Fix violations surgically.

- Type errors -> reject, re-prompt with error details
- Property failures -> analyze countermodel, understand root cause, decide:
- Is specification wrong? (Fix spec, regenerate)
- Is implementation wrong? (Fix code or re-prompt)
- Is priority wrong? (Document trade-off, accept or reject)
- Semantic errors -> manual correction of specific issue
- Performance errors -> profile, identify bottleneck, re-prompt with constraints

*Principle:* Preserve what's valid, correct only what violates A.

*Output: Corrected implementation with traceability to verification failures*


##### Phase 8: Document (Provenance)

Make the normative structure explicit.

- Link code to norms via structured comments or annotations
- Document which countermodels were prevented and how
- Record priority conflicts and resolutions with justification
- Trace requirements through specification to implementation
- Create audit trail for future maintainers
- Note what was verified at what level
- *Acknowledge what was NOT verified and why*

*Output: Traceable, auditable codebase with explicit verification boundaries*

*Honesty:* Documentation of unverified properties is as important as documentation of verified ones.


##### Phase 9: Monitor (Runtime)

Verify in production.

- Runtime assertions for critical invariants (fail fast if violated)
- Telemetry for norm violations (detect degradation)
- Logging of forbidden states if reached (incident response)
- Continuous verification that A is maintained
- Canary deployments with verification gates
- Rollback triggers on invariant violations

*Output: Production system with runtime guarantees and observable verification*

*Limitation:* Runtime monitoring catches violations but cannot prevent first occurrence. Use for detection + response, not prevention alone.




### Part III: The Practice

#### VIII. The Tools We Use

*Formal Specification:*
- *Alloy*—lightweight, SAT-based model finding, excellent for exploration
- *TLA+*—temporal logic, industry-proven for distributed systems
- *Z notation*—schema-based specification, good for data-heavy systems
- *First-order logic*—the foundation beneath it all

*Type Systems:*
- *Rust*—affine types, ownership, practical systems programming
- *Haskell*—algebraic types, type classes, purity, strong inference
- *OCaml/F#*—practical ML-family languages, good mainstream adoption
- *Liquid Haskell*—refinement types, SMT-backed verification
- *Idris/Agda/Lean*—dependent types (research-grade, watch this space)

*Property-Based Testing:*
- *Hypothesis* (Python)—generative, shrinking, stateful machines, accessible
- *QuickCheck* (Haskell)—the original, still excellent
- *PropEr* (Erlang)—concurrent property testing for distributed systems
- *fast-check* (JavaScript)—bringing properties to the masses

*Model Checkers:*
- *Alloy Analyzer*—bounded verification, countermodel generation
- *TLC*—TLA+ model checker, explicit state
- *SPIN*—LTL verification, mature tooling
- *CBMC*—bounded model checking for C

*Static Analysis:*
- *Type checkers*—the first line of defense, zero runtime cost
- *Linters*—pattern-based error detection
- *Abstract interpretation*—semantic analysis, sound over-approximation
- *Symbolic execution*—path exploration, good for security properties

*Category Theory* (when appropriate):
- *Functors*—structure-preserving mappings
- *Monads*—effect composition, separation of concerns
- *Natural transformations*—comparing implementations
- *String diagrams*—visual reasoning about composition

*We use whatever works.*

The principle: *verification through multiple independent methods*.

- Type checking catches what it can (20-40% of errors, instantly)
- Properties find what types miss (60-80% of remaining, empirically)
- Formal methods prove what properties can't (critical properties, exhaustively)
- Human reading catches what machines don't (semantic errors, domain violations)

*Defense in depth, all serving A.*

No single method is sufficient. Each has blind spots. Combined, they create trustworthy systems.


#### IX. What We Reject

*We reject the myth that LLMs "understand"*

They generate plausible tokens based on statistical patterns learned from training data.
Sometimes brilliant. Often wrong. Always unreliable alone.
They have no semantic model, no world understanding, no intentionality.

*We use them as tools, not as authorities.*


*We reject "vibes-based" code review*

"Looks good to me" is not verification.
Intuition without formal grounding misses subtle violations.
Human pattern-matching fails on unfamiliar AI-generated structures.

*We verify against explicit specifications, not feelings.*


*We reject the notion that verification is ever "solved"*

- Some properties are undecidable (Rice's theorem, halting problem)
- Some systems are too complex to model completely (state explosion)
- Some norms conflict (priority decisions are judgment calls)
- Some behaviors emerge only at scale (production ≠ test)

Perfect verification is asymptotic. We verify what matters most and acknowledge the rest.

*We pursue rigor, not perfection.*


*We reject verification theater*

Writing specs that don't capture real requirements accomplishes nothing.
Property tests that pass but test the wrong thing provide false confidence.
Type systems that enforce trivial constraints waste effort.

*We verify properties that matter, not properties that are easy.*


*We reject the false choice between speed and safety*

Specification-first development is often FASTER than debug-later development.
Finding bugs in testing costs 10x finding them in specification.
Finding bugs in production costs 100x finding them in testing.

*Rigor is efficiency at scale.*


*We reject the "move fast and break things" mentality for critical systems*

When your code handles medical decisions, financial transactions, infrastructure control, or personal data:
Moving fast and breaking things is not innovation—it's negligence.

*For critical systems: specify, verify, then deploy.*


#### X. What We Embrace

*We embrace intellectual honesty about uncertainty*

Not all properties can be verified.
Not all norms can be formalized.
Not all systems justify formal methods.

We document what we verified, at what level, with what confidence.
*We document what we did NOT verify and why.*

*Acknowledged uncertainty is better than false confidence.*


*We embrace appropriate rigor*

Not every system needs Alloy models and formal proofs.

*Critical systems* (medical, aerospace, financial infrastructure):
Full formal verification. Proofs for safety properties. Extensive property testing.

*High-value systems* (enterprise, payment processing):
Strong type systems. Comprehensive property testing. Strategic formal modeling.

*Standard applications* (most web apps, internal tools):
Good types. Solid unit/integration tests. Property tests for complex logic.

*Throwaway scripts* (one-off analysis, personal automation):
Whatever ensures it works. Verification would be overkill.

*Match rigor to stakes.*


*We embrace the tool-assisted human*

LLMs are powerful tools for code generation.
Formal methods are powerful tools for verification.
Types are powerful tools for constraint encoding.

But *judgment remains human:*
- What properties matter most?
- Where to invest verification effort?
- When to accept risk vs. when to prove correctness?
- How to trade off conflicting norms?

*Tools amplify judgment; they don't replace it.*


*We embrace continuous learning*

The tools evolve (dependent types becoming practical, better SMT solvers, more capable LLMs).
The practice evolves (new patterns for verification, better specification techniques).
Our understanding evolves (learning what works, what fails, where to focus effort).

*This is not dogma. This is living practice.*


#### XI. The Education Problem

*The Pedagogical Paradox:*

You cannot audit what you cannot implement.

The Logic Auditor requires:
- Deep understanding of algorithms and data structures
- Fluency in reading and reasoning about code
- Intuition for performance characteristics and failure modes
- Experience with debugging, refactoring, system design

*All of this comes from implementation experience.*

Yet if juniors use LLMs from day one, they never develop this foundation.
They can prompt. They can run tests. But they cannot *judge*.


*The Educational Path:*

*Phase 1: Foundation (2-3 years)*
- Traditional programming WITHOUT LLMs
- Implement core algorithms by hand (sorting, searching, graph algorithms)
- Build systems from scratch (web server, database, compiler)
- Experience the pain of choosing wrong (bubble sort on 1M items, O(n²) joins)
- Debug obscure errors, refactor messy code, optimize slow systems
- *Build intuition through struggle*

*Phase 2: Formalization (1-2 years)*
- Formal logic and proof techniques
- Type theory and type systems
- Formal methods (Alloy, TLA+, model checking)
- Property-based testing frameworks
- Specification techniques and patterns
- *Learn to verify what you can already implement*

*Phase 3: Integration (1-2 years)*
- Auditing LLM-generated code with formal tools
- Specification-first development workflows
- Multi-level verification strategies
- Prompt engineering for constrained generation
- Working with senior Logic Auditors on real systems
- *Learn to curate what machines generate*

*Total: 4-7 years to develop a competent Logic Auditor.*

This is not faster than traditional programming education.
*This is more demanding.*

The Logic Auditor needs:
- 100% of traditional programming knowledge (to read and understand generated code)
- 100% of formal methods knowledge (to specify and verify)
- 100% of domain knowledge (to interpret and model)
- 100% of judgment (to allocate effort appropriately)

*This is a multiplicative burden, not an additive one.*


*For Universities:*

- Keep algorithms, data structures, systems programming courses
- Add formal methods as required, not elective
- Integrate property-based testing from intro courses onward
- Teach specification BEFORE implementation in upper-level courses
- Create capstone projects: specify -> verify -> audit AI-generated implementation

*For Bootcamps:*

- Teach traditional programming first
- Add verification modules AFTER implementation competence
- Focus on property-based testing (accessible, high ROI)
- Don't claim to produce Logic Auditors in 12 weeks—it takes years


*The Dangerous Middle Ground:*

Developers who know *just enough* to use LLMs but not enough to catch their mistakes.

They can generate code. They can run tests. They cannot judge.
They accept plausible-looking output without deep understanding.
They miss subtle semantic errors that surface in production.

*This is where disasters come from.*


#### XII. The Failure Modes

*Cargo Cult Verification:*

- Writing formal specs that don't capture real requirements
- Specifications too weak (allow prohibited behaviors)
- Specifications too strong (prohibit valid behaviors)
- Property tests that pass but test the wrong thing
- Type systems that enforce trivial constraints while missing critical ones
- Formal verification of irrelevant properties

*Verification theater provides false confidence.*


*Analysis Paralysis:*

- Over-specifying low-risk components
- Attempting formal proofs where statistical testing suffices
- Perfect becoming the enemy of good
- Verification effort exceeding implementation effort without justification
- Missing deadlines because of excessive rigor in non-critical paths

*Match effort to stakes.*


*False Confidence:*

- Believing verification proves correctness when it only proves consistency with specs
- Missing the gap between specified norms and true requirements
- Confusing "no countermodel found" with "proof of correctness"
- Over-trusting automated tools without understanding their limits
- Assuming verified components compose into verified systems (they often don't)

*Verification shows consistency, not truth.*


*Knowledge Gaps:*

- Auditors who can use tools but don't understand foundations
- Specification errors that propagate through entire verification process
- Missing the semantic violations that slip through syntactic checks
- Not recognizing when LLM output is plausible but wrong
- Inability to debug verification failures

*Tools without understanding are dangerous.*


*Tool Brittleness:*

- SMT solvers that time out on complex formulas
- Model checkers that hit state explosion
- Type systems that can't express needed constraints
- Property tests that miss edge cases
- Overreliance on one verification method

*No single tool is sufficient.*


*Organizational Resistance:*

- "We don't have time for formal methods"
- "Our developers don't know this stuff"
- "It works in production, why verify?"
- Pressure to ship unverified code to meet deadlines
- Cutting corners when stressed

*Quality requires sustained organizational commitment.*


#### XIII. The Systems We Build

*With Logic Auditors, systems become:*

*Explicit in their norms*
No hidden assumptions. All constraints documented. Admissibility defined.

*Verifiable in their behavior*
Admissibility checkable at multiple levels. Evidence of correctness, not just absence of detected errors.

*Traceable in their provenance*
From domain requirements through formal specification through verified implementation. Clear audit trail.

*Composable in their structure*
Verified components with explicit contracts. Composition preserves properties (when done right).

*Maintainable over time*
Future maintainers see the normative structure. Changes verified against preserved invariants.

*Trustworthy in production*
Runtime monitoring ensures A is preserved. Observable verification.

*Evolvable with confidence*
Changes verified against formal specifications. Regression caught automatically.

*Honest about limitations*
Explicit documentation of unverified properties. Acknowledged risks.




### Part IV: The Call

#### XIV. The Future We See

*In 5 years:*

- Property-based testing becomes standard in serious software development
- Type systems grow stronger (refinement types in mainstream languages)
- LLM-generated code is common but always verified against specifications
- "Logic Auditor" appears in job descriptions for critical systems
- University CS programs add formal methods to required curriculum

*In 10 years:*

- Formal specification precedes all critical system development
- Dependent types are practical for high-value domains
- Alloy/TLA+ are taught in undergraduate CS programs
- Most code is generated, all critical code is audited
- Unverified code in production systems is considered unprofessional

*In 20 years:*

- The Logic Auditor is a standard role in software engineering
- Manual coding persists for learning and exceptional cases
- Unverified code is unthinkable for critical systems
- Standard applications use strong types + property tests as baseline
- The distinction between "programmer" and "auditor" becomes fluid

*Stratification persists:*

- Critical systems: Full formal verification
- High-value systems: Property-based testing + strategic formal methods
- Standard systems: Strong types + good tests
- Throwaway scripts: Still exist, verification overkill

*Everyone verifies what matters. Some verify everything. All reason about admissibility when stakes are high.*


#### XV. The Historical Arc

*From Kanger (1957) to LLMs (2025):*

The arc is clear:

- *1957-1970:* Norms as world selection (Kanger, von Wright) - philosophical foundation
- *1970-1990:* First-order reduction, model theory - mathematical foundation
- *1990-2010:* Computational verification (Alloy, TLA+, SPIN) - practical tools emerge
- *2000-2020:* Property-based testing (QuickCheck -> Hypothesis) - empirical verification
- *2010-2020:* Type-level encoding (Rust, Haskell, dependent types) - construction by constraint
- *2020-2025:* Machine generation (LLMs) - the inversion of the bottleneck
- *2025->:* Human verification (Logic Auditors) - the synthesis

*This is not speculation. This is synthesis.*

60 years of formal methods development.
30 years of property-based testing refinement.
20 years of practical model checking deployment.
15 years of strong type systems in mainstream languages.
3 years of capable LLMs.

*The pieces were waiting for assembly.*

*Why formal methods didn't dominate before:*
Specification was more expensive than fixing bugs in production.

*Why LLMs change everything:*
Generation is now cheaper than verification, creating a flood of unverified code.

*The crisis creates the opportunity.*


#### XVI. The Ethical Dimension

*When your code handles:*

*Medical treatment decisions:*
Unverified code = potential deaths. Every line matters. Formal verification required.

*Financial transactions:*
Unverified code = potential theft, market manipulation, economic harm. Strong verification required.

*Infrastructure control:*
Unverified code = potential catastrophe (power grids, water systems, transportation). Formal verification required.

*Personal data:*
Unverified code = potential privacy violations, surveillance, discrimination. Strong verification required.

*Safety-critical systems:*
Unverified code = potential injury or death. Formal verification required.


*The Logic Auditor's ethical commitment:*

*I will not deploy code whose failure modes I have not characterized.*

*I will not accept plausible but unverified output from machines.*

*I will document what I verified and what I did not.*

*I will advocate for appropriate rigor based on stakes.*

*I will refuse pressure to ship unverified critical systems.*


*Professional standards:*

For critical systems:
- Unverified code is unprofessional
- Unverified code is unethical
- Unverified code is negligent

For standard systems:
- Best-effort verification is acceptable
- Match rigor to consequences
- Document verification levels

*Verification is not optional when lives or livelihoods are at stake.*


#### XVII. The Call to Action

*To students:*

*This week:*
- Implement one algorithm from scratch without AI assistance
- Read the Alloy tutorial (2 hours)
- Write your first property-based test

*This semester:*
- Take formal methods or programming languages theory
- Implement a non-trivial system entirely manually
- Learn a strongly-typed functional language

*Before graduation:*
- Audit an LLM-generated system with formal specifications
- Contribute to an open-source project using verification
- Build deep understanding before becoming an auditor

*The future needs Logic Auditors, but they need foundations first.*


*To educators:*

*This semester:*
- Add one property-based testing module to intro programming
- Require students to write specifications before implementations
- Show students the failure modes of unverified code

*This year:*
- Make formal methods required, not elective
- Integrate verification across all courses, not siloed
- Create capstone projects involving LLM auditing

*Next curriculum review:*
- Rebalance toward verification without losing implementation
- Teach specification-first development as standard workflow
- Prepare students for the age of machine-generated code

*The curriculum must evolve to meet the future.*


*To practitioners:*

*This week:*
- Add one property test to your codebase
- Document one critical invariant formally
- Review one LLM-generated PR with explicit verification criteria

*This quarter:*
- Model one critical component in Alloy or TLA+
- Require countermodel documentation for new features
- Learn a verification tool relevant to your domain

*This year:*
- Establish verification standards for critical vs. standard code
- Invest in team training on formal methods
- Build verification into your development workflow

*Professionalism requires rigor.*


*To researchers:*

*Urgent needs:*
- Make dependent types practical for mainstream use
- Make model checking scale to real systems
- Make verification tools more accessible
- Bridge the gap between theory and practice
- Develop better SMT solvers for complex domains

*The tools exist but need refinement.*

We have the theory. We need better engineering.


*To industry:*

*Immediate actions:*
- Invest in verification infrastructure and tooling
- Hire and train Logic Auditors for critical systems
- Require formal specifications before implementation
- Make admissibility explicit in all system designs
- Support research into practical verification

*Cultural shifts:*
- Treat verification as engineering, not research
- Allocate time and budget for specification work
- Resist pressure to ship unverified critical code
- Reward thoroughness, not just speed

*Quality and safety require sustained investment.*


#### XVIII. The Provocation

*We claim:*

*Programming is entering a new phase.*

Not because machines can write code.
But because *human understanding must become more rigorous* to verify what machines write.

The Logic Auditor doesn't make programming easier.
*It makes programming trustworthy.*


*We assert:*

*For critical systems, the age of casual coding has ended.*

When lives, livelihoods, or security are at stake:
- Unverified code is unprofessional
- Unverified code is unethical
- Unverified code is negligent

*Verification is not optional.*


*We insist:*

*The foundations are mature. The tools exist. The theory is validated.*

What was missing was the crisis that demands them.

LLMs created the crisis:
Code generation faster than verification -> flood of unverified code.

Formal methods provide the solution:
Specification once -> verification of many candidates -> deployment with confidence.

*We must connect them.*


*We demand:*

*Make admissibility explicit.*

Every system has norms.
Every codebase makes assumptions.
Every program excludes possibilities.

Stop pretending this is informal.
Stop treating it as commentary.
Stop leaving it implicit.

*Define A. Verify membership. Document coverage. Acknowledge gaps.*


#### XIX. The Commitment

*We, the practicing Logic Auditors, commit to:*

*Specify before generating*
No code without norms. No generation without admissibility defined.

*Verify after receiving*
No deployment without evidence. Match verification depth to stakes.

*Document all decisions*
No gaps in provenance. Trace requirements to implementation.

*Make countermodels explicit*
No hidden failure modes. Document what's prevented and how.

*Use all appropriate tools*
Types, tests, proofs, manual analysis. Defense in depth.

*Maintain rigor under pressure*
No shortcuts when stressed. Advocate for appropriate verification.

*Be honest about limitations*
Document what's unverified. Acknowledge uncertainty.

*Teach the next generation*
Pass on foundations first, then tools. Build judgment through practice.

*Evolve the practice*
Improve tools and methods. Share what works and what fails.

*Remember the purpose*
Software serves humans. Verification serves trust. Trust enables everything else.


#### XX. The Invitation

This is not dogma.
This is not prescription.
This is not the final word.

*This is a call to practice.*

If you build systems where correctness matters:
*Try formal specification. Model one component in Alloy.*

If you use LLMs to generate code:
*Verify the output. Write properties, not just unit tests.*

If you teach programming:
*Teach verification. Make it essential, not optional.*

If you research verification:
*Make it practical. Bridge theory and engineering.*

If you lead engineering teams:
*Invest in rigor. Match verification to stakes.*

*Join us in building the discipline.*

Not because it's easy.
Because it's necessary.


#### XXI. The Beginning

We stand at the threshold.

Machines can generate code faster than humans can verify it.
Humans must ensure generated code is trustworthy.

*The discipline:* Logic Auditing
*The method:* Normative verification
*The foundation:* Admissibility
*The practice:* Curation and composition

*From possible worlds to actual code.*
*From norms to verification.*
*From philosophy to practice.*

This is not the end of programming.
*This is its maturation.*

Welcome to the age of the Logic Auditor.


*Admissibility is not optional.*




#### XXII. Spread

*License:* CC0 1.0 Universal - Public Domain Dedication

*Version:* 2.0

*Date:* February 2026

*Foundation:* 60 years of formal methods + 3 years of capable LLMs = the synthesis moment

*Contact:* Share, fork, remix, improve. This is a living document.

*The code we trust is the code we verify.*

*The systems we deploy are the systems we can defend.*

*The future we build is the future we can reason about.*




### Appendix: Suggested Reading

*Foundations:*
- Kanger, S. (1957). *New Foundations for Ethical Theory*
- von Wright, G.H. (1963). *Norm and Action*
- Jackson, D. (2006). *Software Abstractions: Logic, Language, and Analysis*
- Lamport, L. (2002). *Specifying Systems: The TLA+ Language*

*Practice:*
- Kudrjavets et al. (2021). *Property-Based Testing in Practice*
- Hillel, H. (2023). *Practical TLA+*
- Claessen & Hughes (2000). *QuickCheck: A Lightweight Tool for Random Testing*

*Type Systems:*
- Pierce, B. (2002). *Types and Programming Languages*
- Wadler, P. (2015). *Propositions as Types*

*Verification:*
- Huth & Ryan (2004). *Logic in Computer Science*
- Clarke et al. (2018). *Model Checking*

*Read, practice, verify.*

