
## The Logic Auditor Manifesto

*For the age of machine-generated code*



### I. The Crisis

We stand at a peculiar juncture.

Machines can now write code. Not perfectly, but plausibly. Fast enough to seem useful. 
Good enough to be dangerous.

The old model breaks: *write code -> understand through writing -> maintain what you built*.

The new reality: *describe intent -> machine generates -> ??? -> hope it works*.

That middle step--the ???--is where everything fails or succeeds.


*We need a new discipline.*



### II. The Core Problem

#### The question is not: "Can machines write code?"

They can. They do. Daily. Millions of lines.

#### The question is: "Can we trust what they write?"

And deeper: *"Can we even tell?"*

*The problem:*
- LLMs generate plausible code, not necessarily correct code
- Syntax correct ≠ semantics correct ≠ norms satisfied
- Verification is harder than generation
- Understanding code you didn't write is harder than writing it yourself

*The traditional answer fails:*
"Just review it carefully"--but how? By what standard? With what tools?

*We need formal foundations.*



### III. The Fundamental Insight

#### Every system has an admissible space.

* Not all behaviors are acceptable.
* Not all states are valid.
* Not all futures are permitted.

*The boundary between acceptable and unacceptable is normative.*

* In mathematics: constraints define solution spaces.
* In law: norms define permissible actions.
* In software: requirements define admissible executions.

*This is not new. We've been doing this for 60 years.*

What's new: machines generating code that must satisfy these constraints.



### IV. The Semantic Foundation

#### Normativity = World Selection

* Let W be all possible system behaviors.
* Let A ⊆ W be the admissible subset.

*Everything derives from A:*

- *Obligation*: What must hold in all admissible worlds
`O φ ≡ ∀w ∈ A: φ(w)`

- *Prohibition*: What must not hold in any admissible world
`F φ ≡ ∀w ∈ A: ¬φ(w)`

- *Permission*: What may hold in some admissible world
`P φ ≡ ∃w ∈ A: φ(w)`

- *Requirement*: What constitutes admissibility itself
`R φ ≡ [O φ ∧ removing φ expands A]`

*This is not modal mysticism. This is first-order logic over explicit structures.*

```
Deontic operators -> First-order quantification -> Computational verification
```

*The bridge from philosophy to software engineering.*



### V. The Role We Need

#### The Logic Auditor

Not a programmer in the traditional sense.
Not a code reviewer in the old meaning.
Not a tester in the conventional role.

*A new discipline:*

The Logic Auditor is a *normative systems analyst* who ensures machine-generated 
code inhabits admissible worlds.

*Their craft:*
1. *Hermeneutic understanding*--interpreting what the domain *means*
2. *Formal modeling*--encoding meaning as first-order predicates
3. *Admissibility definition*--establishing the boundary of acceptable behavior
4. *Countermodel identification*--making forbidden states explicit
5. *Verification orchestration*--using all available tools to check compliance
6. *Prompt engineering*--guiding generation with normative specifications
7. *Code reading*--deep analysis of machine output against semantic models
8. *Surgical refinement*--correcting violations while preserving valid aspects

*This is craft, but intellectual rather than manual.*

The "material" is the semantic space itself.
The "tool feel" comes from sensitivity to norm violations.



### VI. The Method

#### Phase 0: Understand (Hermeneutic)

Before any formalism, understand the domain.

- What are we really building?
- What could go catastrophically wrong?
- What are the true constraints, beyond stated requirements?
- What assumptions are embedded in current practice?

*Output: Conceptual model*



#### Phase 1: Specify (Deontic)

Formalize admissibility.

1. Define worlds W (states, trajectories, executions)
2. Define predicates over worlds (Borrowed, Paid, Stock, Shipped)
3. Define norms (obligations, prohibitions, permissions, invariants)
4. Establish priorities (critical, high, medium, low)
5. Compute admissibility A from norms and priorities
6. Identify countermodels wX explicitly

*Output: Formal specification in first-order logic*



#### Phase 2: Explore (Formal Methods)

Understand the admissible space before generating code.

- Encode in Alloy or TLA+
- Generate example admissible worlds
- Find counterexamples to proposed properties
- Refine specification based on findings
- Validate consistency of norms

*Output: Validated formal model with concrete instances*



#### Phase 3: Encode (Type Systems)

Make simple violations impossible by construction.

- Design type structure reflecting domain
- Encode preconditions as type constraints
- Use phantom types for state machines
- Leverage dependent/refinement types where available
- Make illegal states unrepresentable

*Output: Type signatures that enforce basic norms*



#### Phase 4: Specify Tests (Property-Based)

Translate every norm into an executable property.

```
O φ -> ∀w ∈ A: φ(w) -> property test
F φ -> ∀w ∈ A: ¬φ(w) -> negative property test
R φ -> ∀execution: always φ -> invariant test
```

Generate thousands of random test cases automatically.
Let the machine search for countermodels.

*Output: Comprehensive property-based test suite*



#### Phase 5: Generate (LLM Collaboration)

Prompt with full normative context.

Include in prompt:
- Type signatures
- Formal norms with priorities
- Example admissible worlds
- Explicit countermodels to prevent
- Preconditions and effects
- Invariants that must hold

Generate multiple candidates.
Explore the design space.

*Output: Multiple candidate implementations*



#### Phase 6: Verify (Multi-Level)

Check admissibility at every level.

1. *Type check*--catches basic violations instantly
2. *Property test*--finds empirical countermodels
3. *Formal verify*--proves absence of violations (when critical)
4. *Manual read*--deep semantic analysis, hermeneutic interpretation
5. *Priority check*--ensure high-priority norms satisfied, document trade-offs

*Output: Verified implementation or detailed violation report*



#### Phase 7: Refine (If Needed)

Fix violations surgically.

- Type errors -> reject, re-prompt
- Property failures -> analyze countermodel, understand why
- Semantic errors -> manual correction of specific issue
- Preserve what's valid, correct only what violates A

*Output: Corrected implementation*



#### Phase 8: Document (Provenance)

Make the normative structure explicit.

- Link code to norms via comments
- Document which countermodels were prevented
- Record priority conflicts and resolutions
- Trace requirements through to implementation
- Create audit trail for future maintainers

*Output: Traceable, auditable codebase*



#### Phase 9: Monitor (Runtime)

Verify in production.

- Runtime assertions for critical invariants
- Telemetry for norm violations
- Logging of forbidden states if reached
- Continuous verification that A is maintained

*Output: Production system with runtime guarantees*



### VII. The Tools We Use

#### Formal Specification
- *Alloy*--lightweight, SAT-based model finding
- *TLA+*--temporal logic, industry-proven
- *Z notation*--schema-based specification
- *First-order logic*--the foundation beneath it all

#### Type Systems
- *Rust*--affine types, ownership, no garbage collector needed
- *Haskell*--algebraic types, type classes, purity
- *OCaml/F#*--practical ML-family languages
- *Liquid Haskell*--refinement types for stronger guarantees
- *Idris/Agda/Lean*--dependent types (future, but watch this space)

#### Property-Based Testing
- *Hypothesis* (Python)--generative, shrinking, stateful machines
- *QuickCheck* (Haskell)--the original, still excellent
- *PropEr* (Erlang)--concurrent property testing
- *fast-check* (JavaScript)--bringing properties to the masses

#### Model Checkers
- *Alloy Analyzer*--bounded verification
- *TLC*--TLA+ model checker
- *SPIN*--LTL verification
- *NuSMV*--symbolic model checking

#### Static Analysis
- *Type checkers*--the first line of defense
- *Linters*--pattern-based error detection
- *Abstract interpretation*--semantic analysis
- *Symbolic execution*--path exploration

#### Category Theory
- *Functors*--structure-preserving mappings
- *Monads*--effect composition
- *Natural transformations*--comparing implementations
- *String diagrams*--visual reasoning about composition

*We use whatever works.*

The principle: verification through multiple independent methods.
Type checking catches what it can.
Properties find what types miss.
Formal methods prove what properties can't.
Human reading catches what machines don't.

*Defense in depth, all serving A.*



### VIII. What We Reject

#### We reject the myth that LLMs "understand"

They generate plausible tokens based on statistical patterns.
Sometimes brilliant. Often wrong. Always unreliable alone.

*We verify, always.*



#### We reject "just trust the AI"

Trust must be earned through verification, not assumed through hype.

*Show us A. Show us the proof.*



#### We reject untraceable code

Every line must trace back to requirements.
Every requirement must manifest in code.
No gaps. No guesses.

*Provenance is not optional.*



#### We reject informal specifications

"Make it work well" is not a specification.
"Be secure" is not a norm.
"Handle edge cases" is not admissibility criteria.

*Formalize or fail.*



#### We reject exception-driven design

There are no "special cases" and "exceptions."
There are only constraints that define A.

*All rules are declarative constraints.*



#### We reject axiom-heavy systems

Classical deontic logic with its paradoxes and proof systems.
We are engineers, not philosophers.

*Semantics first. Proofs if needed.*



#### We reject monotonicity

Real systems have conflicting norms.
Priorities are real.
Trade-offs are necessary.

*We handle conflict pragmatically through priority orderings.*



### IX. What We Embrace

#### We embrace semantic modeling

Worlds, admissibility, actions, transitions.
First-order predicates over explicit structures.

*This is the foundation.*



#### We embrace countermodels

wX states are not bugs found in testing.
They are design artifacts, explicitly modeled upfront.

*Make forbidden states visible before coding.*



#### We embrace multiple verification strategies

Types, tests, proofs, reading.
Each sees what others miss.

*Verification through diversity.*



#### We embrace LLMs as tools

Not replacements for understanding.
Not shortcuts around rigor.
But powerful generators in a verified workflow.

*Generate freely. Verify ruthlessly.*



#### We embrace the hermeneutic tradition

Code is text. Programs are meaning-bearing artifacts.
Understanding requires interpretation, not just execution.

*Reading is as important as writing.*



#### We embrace 60 years of formal methods

From Kanger and von Wright through Alloy and TLA+.
The theory is mature. The tools exist.

*We stand on giants' shoulders.*



#### We embrace the collapse to first-order logic

Modal operators are sugar.
Underneath: quantification over worlds.
Therefore: computable, verifiable, checkable.

*Philosophy becomes engineering.*



### X. The Knowledge Required

#### The Logic Auditor must know:

*Formal Foundations:*
- First-order logic
- Model theory basics
- Deontic semantics
- Temporal logic
- Type theory

*Verification Techniques:*
- Property-based testing methodology
- Model checking principles
- Type systems (simple -> dependent)
- Static analysis approaches
- Runtime verification

*Semantic Modeling:*
- Domain modeling
- State space analysis
- Action systems
- Invariant identification
- Countermodel construction

*Software Craft:*
- Deep code reading
- Multiple programming paradigms
- System architecture
- Performance characteristics
- Security principles

*Compositional Reasoning:*
- Basic category theory (functors, natural transformations, monads)
- Process algebras
- Temporal composition
- Modular verification

*LLM Collaboration:*
- Prompt engineering
- Understanding LLM capabilities and limitations
- Iterative refinement
- Effective specification formats

*This is demanding. Necessarily so.*

Verification is harder than generation.
Understanding is harder than production.
The Logic Auditor must know more, not less.



### XI. The Education We Need

#### The curriculum must change.

*Year 1-2: Classical Foundations*
- Programming (to build intuition through doing)
- Algorithms and data structures
- Type systems and functional programming
- Formal logic and proof
- Basic category theory

*Year 2-3: Analytical Skills*
- Deep code reading (not just writing)
- Semantic modeling
- Property-based testing
- Formal specification (Alloy, TLA+)
- Domain modeling

*Year 3-4: Verification Engineering*
- Advanced type systems (refinement, dependent)
- Model checking
- Static analysis
- Deontic action logic
- Applied category theory
- LLM collaboration and verification

*Specialized Tracks:*
- High-assurance systems (dependent types, certified compilation)
- Compositional systems (advanced category theory, process algebras)
- Temporal systems (TLA+, LTL, CTL model checking)
- Domain-specific (medical, financial, safety-critical)

*Apprenticeship:*
Working with senior Logic Auditors.
Learning judgment through guided practice.
Building intuition for norm violations.
Developing taste for good specifications.

*The goal: 70% traditional programming knowledge + 30% verification expertise*

Or perhaps: 100% traditional + 20% additional.

The Logic Auditor is more demanding, not less.

---

### XII. The Systems We Build

#### With Logic Auditors, systems become:

*Explicit in their norms*
— No hidden assumptions, all constraints documented

*Verifiable in their behavior*
— Admissibility checkable at multiple levels

*Traceable in their provenance*
— From requirements through norms to code

*Composable in their structure*
— Verified components combine into verified systems

*Maintainable over time*
— Future maintainers see the normative structure

*Trustworthy in production*
— Runtime monitoring ensures A is preserved

*Evolvable with confidence*
— Changes verified against preserved norms



### XIII. The Future We See

#### In 5 years:

Property-based testing becomes standard in all serious software.
Type systems grow stronger (refinement types in mainstream languages).
LLM-generated code is common but always verified.
"Logic Auditor" appears in job descriptions.

#### In 10 years:

Formal specification precedes all critical system development.
Dependent types are practical for important domains.
Alloy/TLA+ are taught in undergraduate CS programs.
Most code is generated, all code is audited.

#### In 20 years:

The Logic Auditor is the *normal* software engineer role.
Manual coding is for learning and exceptional cases.
Unverified code is unthinkable in production.
The distinction between "programmer" and "auditor" fades.

*Everyone verifies. Some generate. All reason about admissibility.*



### XIV. The Call

#### To students:

Learn to verify, not just to code.
Master formal methods, not just frameworks.
Understand norms, not just syntax.

*The future needs Logic Auditors.*



#### To educators:

Teach specification before implementation.
Teach verification alongside programming.
Make property-based testing mandatory.
Introduce formal methods early.

*The curriculum must evolve.*



#### To practitioners:

Don't trust LLM output blindly.
Specify before generating.
Verify after receiving.
Document normative structure.

*Professionalism requires rigor.*



#### To researchers:

Make dependent types practical.
Make model checking scale.
Make verification tools accessible.
Bridge the gap between theory and practice.

*The tools exist but need refinement.*



#### To industry:

Invest in verification infrastructure.
Hire Logic Auditors.
Require formal specifications for critical systems.
Make admissibility explicit.

*Quality and safety require investment.*



### XV. The Provocation

#### We claim:

*Programming is entering a new phase.*

Not because machines can write code.
But because *human understanding must become more rigorous* to verify what machines write.

The Logic Auditor doesn't make programming easier.
*It makes programming trustworthy.*



#### We assert:

*The age of casual coding is ending.*

For critical systems, unverified code is unprofessional.
For safety-critical systems, it's unethical.
For security-critical systems, it's negligent.

*Verification is not optional.*



#### We insist:

*The foundations exist. The tools exist. The theory is mature.*

What's missing is recognition that the problem demands them.

LLMs created the crisis.
Formal methods provide the solution.

*We must connect them.*



#### We demand:

*Make admissibility explicit.*

Every system has norms.
Every codebase makes assumptions.
Every program excludes possibilities.

Stop pretending this is informal.
Stop treating it as commentary.
Stop leaving it implicit.

*Define A. Verify membership. Prove compliance.*



### XVI. The Synthesis

From Stig Kanger/Georg Henrik von Wright in the late 1950s to Alloy in 2000 to LLMs in 2025 and beyond.

The arc is clear:
- Norms as world selection (Kanger, von Wright)
- First-order reduction (model theory)
- Computational verification (Alloy, TLA+)
- Property-based testing (QuickCheck -> Hypothesis)
- Type-level encoding (Rust, Haskell, dependent types)
- Machine generation (LLMs)
- *Human verification (Logic Auditors)*

*This is not speculation. This is synthesis.*

60 years of formal methods.
30 years of property-based testing.
20 years of practical model checking.
10 years of strong type systems in mainstream languages.
3 years of capable LLMs.

*The pieces were waiting for assembly.*



### XVII. The Conclusion

#### The question was never:

"Will LLMs replace programmers?"

#### The question is:

"What must programmers become to work effectively with LLMs?"

#### The answer:

*Logic Auditors.*

Normative systems analysts who ensure machine-generated code inhabits admissible worlds.

*This is not a job title. This is a discipline.*

Grounded in 60 years of formal methods.
Enabled by modern verification tools.
Necessary for the age of machine-generated code.

*The theory is complete.*
*The tools are ready.*
*The need is urgent.*



### XVIII. The Commitment

#### We, the undersigned, commit to:

*Specify before generating*
— No code without norms

*Verify after receiving*
— No deployment without proof

*Document all decisions*
— No gaps in provenance

*Make countermodels explicit*
— No hidden failure modes

*Use all available tools*
— Types, tests, proofs, reading

*Maintain rigor under pressure*
— No shortcuts when stressed

*Teach the next generation*
— Pass on the discipline

*Evolve the practice*
— Improve the tools and methods

*Stay honest about limitations*
— Acknowledge what we don't verify

*Remember the purpose*
— Software serves humans; verification serves trust



### XIX. The Invitation

This is not dogma.
This is not prescription.
This is not the final word.

*This is a call to practice.*

If you build systems where correctness matters:
*Try formal specification.*

If you use LLMs to generate code:
*Verify the output.*

If you teach programming:
*Teach verification.*

If you research verification:
*Make it practical.*

*Join us in building the discipline.*



### XX. The Beginning

We stand at the threshold.

Machines can generate code.
Humans must ensure it's trustworthy.

The discipline: Logic Auditing.
The method: Normative verification.
The foundation: Admissibility.

*From possible worlds to actual code.*
*From norms to verification.*
*From philosophy to practice.*

This is not the end of programming.
*This is its maturation.*

Welcome to the age of the Logic Auditor.


*Admissibility is not optional.*


### XXI. Spread

*License:* This manifesto is released into the public domain.

*Version:* 1.0

*Date:* February 2026

*Foundation:* 60 years of formal methods

*The code we trust is the code we verify.*


