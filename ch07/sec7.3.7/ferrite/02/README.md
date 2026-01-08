
## Extending the Ferrite Programming Language

You are tasked with extending Ferrite, a small, Rust-inspired programming language focused on
memory safety through ownership and borrowing semantics. The current implementation (in the
provided `ferrite.py` with traits) serves as your starting point. This version includes basic
features like structs, functions, ownership tracking, borrowing (immutable and mutable), pattern
matching, and a trait system supporting derivation for traits like `Copy`, `Clone`, and `Debug`.
It compiles Ferrite code to C for execution.

Ferrite's design emphasises compile-time safety without garbage collection, using an affine type
system where values are used at most once unless they implement `Copy`. The language is formally
specified in [ferrite-spec.pdf](./../../../assets/pdf/ferrite-spec.pdf), which defines its
syntax, static semantics (typing rules), dynamic semantics (evaluation steps), and soundness
properties (progress and preservation theorems). Also, if you havn't, do have a look at the
mentioned "affine" property in chapter 5 ([ch05](./../../../../ch05/addition/affine/)) addition.
The [DESIGN.md](./DESIGN.md) document provides a small but broader guidance on programming
language design principles.

Your project will involve adding new features while maintaining Ferrite's safety guarantees.
This is not just about coding--it's an exercise in principled language design. You'll balance
theoretical rigour (formal semantics and proofs) with practical implementation, ensuring every
extension preserves type soundness.


### Project Goals

The primary goal is to evolve Ferrite into a more capable language while deepening your
understanding of language design. By the end, you should have:
- One or more new features implemented in the compiler.
- Updated formal specifications (extending [ferrite-spec.pdf](./../../../assets/pdf/ferrite-spec.pdf)).
- Proof sketches or updates to demonstrate that your extensions maintain type soundness.
- A set of example programs demonstrating the new features.
- A report discussing your design choices, challenges, and lessons learned.

Why this project? Extending a language like Ferrite teaches you why languages like Rust work:
safety isn't accidental--it's enforced through careful static and dynamic semantics. You'll
learn to avoid common pitfalls (e.g., undefined behavior) by prioritizing theory alongside code.


### Suggested Extensions

Choose 1-3 extensions based on your interests and time. Start small and build iteratively.
Here are ideas, ordered from simpler to more advanced:

1. *Generics (Parametric Polymorphism)*: Add type parameters to structs and functions
   (e.g., `struct List<T> { ... }`). This allows reusable data structures like generic lists or options.
   - *Why?* Ferrite's current types are monomorphic; generics promote code reuse without sacrificing safety.
   - *What to Add:* Syntax for type parameters, type inference (basic), and polymorphic typing rules.

2. *More Traits and Bounds*: Extend the trait system with user-defined traits beyond `Copy/Clone/Debug`
   (e.g., `Eq` for equality or `Ord` for ordering). Add trait bounds in function signatures
   (e.g., `fn sort<T: Ord>(list: &mut List<T>)`).
   - *Why?* Traits enable polymorphism and constraints, key to safe abstraction in Rust-like languages.
   - *What to Add:* Trait inheritance, default implementations, and dispatch (static or dynamic).

3. *Lifetimes and Explicit Lifetime Annotations*: Introduce named lifetimes (e.g., `&'a T`)
   to handle more complex borrowing scenarios, like returning borrows from functions.
   - *Why?* Current borrowing is simple; lifetimes prevent dangling references, strengthening memory safety.
   - *What to Add:* Lifetime parameters, subtyping rules for lifetimes, and borrow checker enhancements.

4. *Enums and Algebraic Data Types (ADTs)*: Add sum types (e.g., `enum Option { None, Some(i32) }`)
   with pattern matching.
   - *Why?* Ferrite has structs (product types); enums complete the foundation for expressive data modeling.
   - *What to Add:* New type constructors, matching rules, and exhaustion checks.

5. *Concurrency Primitives*: Introduce basic threads or channels with ownership transfer across threads.
   - *Why?* To explore how ownership prevents data races, a core Rust feature.
   - *What to Add:* Thread spawning, send/receive, and sync traits (advanced--tackle only if time allows).

Essential: Whatever you choose, ensure the extension integrates with ownership/borrowing.
Non-essential: Advanced optimizations, fancy syntax (stick to S-expressions),
or runtime features like garbage collection--these contradict Ferrite's design.


### Approach: Theory and Implementation

Follow a theory-first, iterative approach to ensure soundness from the start.
Don't implement first and "fix" bugs later--this often leads to accidental
redefinitions of the language (as warned in [DESIGN.md](./DESIGN.md)).
Instead:

#### Step 1: Theory First (Design and Specify)
- *How:* Before coding, update the formal specification.
  - Extend the types, judgements, and rules in
    [ferrite-spec.pdf](./../../../assets/pdf/ferrite-spec.tex)
    (e.g., add new typing rules for your feature).
  - Sketch proofs for progress and preservation. Use paper or a
    tool like Coq/Lean if you're ambitious, but pen-and-paper derivations are sufficient.
  - Reference [DESIGN.md](./DESIGN.md) for guidance:
    Focus on static semantics to prevent dynamic errors.
- *Why:* This prevents implementation bugs from becoming "features." Soundness theorems
  guarantee "well-typed programs don't go wrong."
- *What:* Aim for 2-5 new rules per extension. For example, for generics,
  define polymorphic environments (Γ[x: ∀α.τ]).

#### Step 2: Implementation (Extend the Compiler)
- *How:* Modify `ferrite.py` (the traits version).
  - Update the parser for new syntax (e.g., add generics to `parse_type`).
  - Extend the type checker (`compile_expr`, `check_can_use`, etc.) to enforce new rules.
  - Update code generation (`CCodeGen`) to produce correct C code.
  - Add tests: Write Ferrite programs that use your feature, compile to C, and run them.
  - Handle errors gracefully--e.g., report borrowing violations clearly.
- *Why:* Implementation realizes the theory, but without theory, it's just hacking.
  Iterate: If implementation reveals spec flaws, revise the theory.
- *What:* Keep changes modular. For traits, build on existing `TraitDef` and `TraitImpl` classes.

#### Step 3: Validation and Iteration
- *How:* 
  - Test for soundness: Create programs that should fail (e.g., use-after-move)
    and ensure the compiler rejects them.
  - Prove key lemmas (e.g., "borrowing preserves ownership state").
  - If working in a group, divide: One person on theory, another on implementation,
    then swap for review.
- *Why:* Iteration catches inconsistencies early. Essential: Maintain the progress
  and preservation theorems. Non-essential: Performance tuning--focus on correctness.
- *What:* Document edge cases (e.g., how generics interact with borrowing).

#### Timeline and Milestones (Suggested for a Semester Project)
- Week 1-2: Study provided files. Choose extensions. Sketch initial spec updates.
- Week 3-5: Formalize theory and proofs.
- Week 6-8: Implement and test core features.
- Week 9-10: Add examples, fix bugs, refine proofs.
- Week 11-12: Write report and demo.


### Tools and Resources
- *Implementation:* Python (extend `ferrite.py`). Use the code execution
  environment if needed for testing.
- *Theory:* LaTeX for updating [ferrite-spec.tex](./../../../assets/pdf/ferrite-spec.tex).
  Read [DESIGN.md](./DESIGN.md) thoroughly.
- *Testing:* Compile to C and run with GCC. Add unit tests in Python.
- *Collaboration:* If multiple people, use Git for version control.


### Evaluation Criteria
- *Correctness (Essential):* Does your extension preserve soundness? Are proofs updated?
- *Design Quality:* Are choices justified (why this syntax/rule over alternatives)?
- *Completeness:* Working implementation with examples.
- *Documentation:* Updated spec, report explaining how/what/why.
- *Creativity (Non-essential but Bonus):* Innovative extensions that fit Ferrite's philosophy.

This project will challenge you to think like a language designer.
Remember: The goal isn't a "big" language--it's a safe, well-reasoned one.
If you get stuck, revisit the spec: Ferrite's simplicity is its strength!

