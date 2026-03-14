
## Linear Logic

Linear logic is a *resource-sensitive* logical system developed
by Jean-Yves Girard in 1987. Unlike classical or intuitionistic
logic where propositions can be used arbitrarily many times,
linear logic treats propositions as *resources* that must be used
exactly once. This fundamental shift makes it particularly well-suited
for reasoning about computation, state changes, and resource management.


### The Core Insight: Resources vs. Truth

In classical logic, if you know proposition A is true, you can use
this fact as many times as you want. The formula A → (A ∧ A) is
valid--from one A, you can magically produce two copies. This
reflects the nature of *eternal truths*: knowing 2+2=4 doesn't
"consume" this fact.

Linear logic rejects this. If A represents "you have one dollar,"
then A → (A ∧ A) would mean "from one dollar, you get two dollars".
Not really realistic. In linear logic, propositions represent
*resources* that are consumed when used.

This seems like a small change, but it's revolutionary. Classical
logic is *timeless*--truths are eternal, unchanging, infinitely
reusable. Linear logic is *temporal*--it tracks what you have *now*,
what gets consumed, what gets produced. It's the difference between
mathematics (eternal truths) and physics (actual stuff that moves around).
This will be more practical in the code/computational context.


### The Exponentials: Controlled Reuse

Linear logic doesn't completely forbid reuse--instead,
it makes it explicit through *exponential modalities*:

- *!A* ("of course A" or "bang A"): A resource you can use as many
  times as you want (including zero times). This captures the
  classical notion of persistent truth.

- *?A* ("why not A"): Dual to !A, represents a resource that
  might be available multiple times.

These modalities satisfy important rules:

- *Dereliction*: !A ⊸ A (if you have unlimited A, you can get one A)
- *Contraction*: !A ⊸ (!A ⊗ !A) (unlimited A can be split into two unlimited As)
- *Weakening*: !A ⊸ 1 (unlimited A can be discarded)

The exponentials are what make linear logic a *conservative extension*
of classical logic. Classical logic is just linear logic where everything
is wrapped in !. So !A → !B is the classical implication--you can use
both sides as many times as you want.

Think of ! as a "xerox machine" for propositions. Without it, you have
exactly one copy. With it, you can make unlimited photocopies. The
brilliance is that linear logic forces you to *decide* what can be
copied and what can't. Most logics give you the xerox machine for
everything; linear logic makes you earn it.


### The Connectives: Multiplicative vs. Additive

Linear logic has *eight main connectives*, organised in dual pairs.
This richness comes from distinguishing between different ways
resources can combine.

Why so many? Because linear logic is *finer-grained* than classical logic.
In classical logic, we have one "and" (∧) and one "or" (∨). But when
resources are involved, there are different *kinds* of "and" depending
on *how* you're combining things. Are you using both resources at the
same time? Or offering a choice between them? These are different
situations that deserve different connectives.

#### Multiplicative Connectives

*⊗ (tensor, "times")*: Combines resources simultaneously. A ⊗ B means
"you have both A and B available at the same time." If A is "one apple"
and B is "one banana," then A ⊗ B is "one apple and one banana together."

Think of tensor as parallel composition. You have both resources, you
can use them independently, and they're both *there* in your hand at
the same moment.

*⅋ (par)*: Dual to tensor. Represents offering a choice of resources
to the environment. While tensor combines what you have, par combines
what you need.

Par is weird and takes some getting used to. A ⅋ B doesn't mean "you
have A or B"--that's the additive ⊕. Instead, par means "the environment
must provide either A or B (or both), but you don't get to choose which."
It's like saying "I need either a screwdriver or a hammer to proceed,
dealer's choice." You're offering multiple *interfaces* for the other
party to satisfy.

*1 (multiplicative unit)*: The neutral element for ⊗.
Represents "no resource" or completion.

Think of 1 as "done" or "finished." It's the proposition that's always
true but represents having accomplished something. A ⊗ 1 is just A--adding
"done" to a resource doesn't change what you have.

*⊥ (bottom)*: Dual to 1, the neutral element for ⅋.

⊥ (read as "bottom" or sometimes "bottom") represents the need for nothing.
It's trivially satisfiable--asking for nothing is always fulfillable.

#### Additive Connectives

*& (with)*: External choice. A & B means "you have A and B, and you can
choose which one to use (but only one)." Like a menu where you pick one dish.

The crucial difference from tensor: with &, you have *both* available,
but when you pick one, the other vanishes. You can't use both. It's
like having a gift card that works at two stores, but once you use it
at one, it's gone. With ⊗, you'd have two separate gift cards.

*⊕ (plus)*: Internal choice, dual to &. A ⊕ B means "you offer either
A or B, but you decide which."

Plus is about *you* making a choice and committing to it. If you have
A ⊕ B, you must pick one branch and follow through with it. The
environment doesn't get to choose--you do. It's like deciding whether
to order pizza or sushi; once you commit, that's what you're doing.

*⊤ (top)*: Neutral for &, represents "everything available."

⊤ is the weird additive unit. A & ⊤ equals A because ⊤ is the choice
you can always make but that gives you nothing. It's like a menu that
includes "or nothing"--you can always choose nothing, but why would you?

*0 (zero)*: Neutral for ⊕, represents "nothing available."

Zero is the impossible choice. You can't have A ⊕ 0 because that would
mean "offer either A or the impossible," and you can't pick the
impossible, so you're stuck with A.

The key distinction: *multiplicative connectives manage resources you're
using together*, while *additive connectives manage alternative choices*.

Multiplicatives are about parallelism and independence. Additives are
about branching and commitment. This distinction doesn't exist in classical
logic because classical logic doesn't care about the *process* of using
resources--only their eternal truth values.

#### Linear Implication

*A ⊸ B* (linear implication, "lollipop"): "Consuming A produces B."
This is fundamentally different from classical implication.
In classical logic, A → B can be used repeatedly; in linear logic,
A ⊸ B is itself a resource--a transformation that can be applied once.

The lollipop is the heart of linear logic's computational interpretation.
It's a *function*--a machine that takes one A and gives you one B,
destroying itself in the process. Unlike classical implication, which
is a static relationship between truths, linear implication is a *process*,
a *transformation*, a *reaction*.

In chemistry, you might write: 2H₂ + O₂ → 2H₂O. This isn't a classical
implication (it's not saying "if hydrogen and oxygen exist, then water
exists"). It's a linear implication: if you *consume* 2H₂ and O₂, you
*produce* 2H₂O. The reactants are *used up*. That's ⊸.


### Linear Negation

Linear logic has a beautiful involutive negation: A⊥ (read "A perp" or
"A dual"). Unlike classical negation, linear negation is about *duality*,
not *falsity*.

The idea: A⊥ represents "the demand for A" or "A's dual role." If A is
"I give you a dollar," then A⊥ is "I receive a dollar." They're perfect
complements--if one happens, the other happens in the opposite direction.

Key property: (A⊥)⊥ = A. Negation is involutive--the dual of the dual
is back where you started.

De Morgan dualities fall out beautifully:
- (A ⊗ B)⊥ = A⊥ ⅋ B⊥
- (A ⅋ B)⊥ = A⊥ ⊗ B⊥
- (A & B)⊥ = A⊥ ⊕ B⊥
- (A ⊕ B)⊥ = A⊥ & B⊥

These aren't arbitrary rules--they're forced by the interpretation of
negation as duality. The dual of "having both A and B" is "needing
either A⊥ or B⊥."


### Structural Rules and Their Rejection

Classical logic has three structural rules that linear logic restricts:

1. *Weakening* (A ⊢ B → A): You can add unused hypotheses.
   Linear logic rejects this—every resource must be accounted for.

2. *Contraction* (A, A ⊢ B → A ⊢ B): You can treat multiple copies
   of a hypothesis as one. Linear logic rejects this—each resource is distinct.

3. *Exchange* (A, B ⊢ C → B, A ⊢ C): Order doesn't matter.
   Linear logic generally keeps this, though some variants restrict it.

These restrictions are what make linear logic *substructural*. By removing
structural rules, we make the logic sensitive to *how many* times something
is used (contraction) and *whether* it's used at all (weakening).

Why does this matter? Because computation isn't just about truth--it's
about *resources*. Memory can't be used twice without copying it. A file
handle can't be ignored without leaking resources. Linear logic's restrictions
match the restrictions of physical reality.


### Sequent Calculus Presentation

Linear logic is elegantly presented as a sequent calculus.
A sequent Γ ⊢ Δ means "consuming all resources in Γ produces all resources in Δ."

In classical logic, sequents have a single conclusion (intuitionistic) or
the conclusion is a disjunction (classical). In linear logic, the conclusion
can be a genuine *multiset* of resources--you can produce many independent
things.

Here are the key inference rules in standard sequent calculus notation:

#### Structural Rules

*Identity (Axiom)*:
```
─────────
  A ⊢ A
```
A resource can be passed through unchanged.

*Cut*:
```
Γ ⊢ A, Δ    A, Σ ⊢ Π
─────────────────────
   Γ, Σ ⊢ Δ, Π
```
Compose transformations. If you can produce A from Γ, and consume A to get Π,
then you can go directly from Γ to Π by "cutting out the middleman" A.

Cut elimination--the theorem that all cuts can be removed from proofs--is
fundamental. It says that any indirect proof can be made direct, any
detour can be removed. In computational terms, it's normalization:
programs can be reduced to simpler forms.

*Exchange* (often implicit):
```
Γ, A, B, Δ ⊢ Σ
───────────────
Γ, B, A, Δ ⊢ Σ
```
Order of resources doesn't matter (in most variants of linear logic).

Note: Linear logic does NOT have weakening or contraction as structural rules.
These are only available through the exponentials (!, ?).

#### Multiplicative Connectives

*Tensor Right (⊗R)*:
```
Γ ⊢ A, Δ      Σ ⊢ B, Π
──────────────────────
  Γ, Σ ⊢ A ⊗ B, Δ, Π
```
If you can independently produce A from Γ and B from Σ, then you can
produce both simultaneously. The contexts Γ and Σ are *split* and used
separately--this is linear logic's way of tracking resource usage.

*Tensor Left (⊗L)*:
```
Γ, A, B ⊢ Δ
─────────────
Γ, A ⊗ B ⊢ Δ
```
To use a tensor, decompose it into its components.

*Par Right (⅋R)*:
```
Γ ⊢ A, B, Δ
─────────────
Γ ⊢ A ⅋ B, Δ
```
Par combines resources in the conclusion.

*Par Left (⅋L)*:
```
Γ, A ⊢ Δ    Σ, B ⊢ Π
──────────────────────
  Γ, Σ, A ⅋ B ⊢ Δ, Π
```
To use a par, split the context.

*Multiplicative Units*:
```
────────     (1R)
 Γ ⊢ 1, Δ
```
When Γ is empty, this produces 1 from nothing.

```
  Γ ⊢ Δ
─────────     (1L)
 Γ, 1 ⊢ Δ
```
The unit 1 can be discarded (when used).

```
────────     (⊥R)
 Γ ⊢ ⊥, Δ
```

```
  Γ ⊢ Δ
─────────     (⊥L)
 Γ, ⊥ ⊢ Δ
```

#### Additive Connectives

*With Right (&R)*:
```
Γ ⊢ A, Δ     Γ ⊢ B, Δ
──────────────────────
    Γ ⊢ A & B, Δ
```
With the additive &, you use the *same* resources Γ for both branches.
You're not splitting resources--you're offering alternative *uses* of
the same pile of stuff.

*With Left (&L₁)* and *(&L₂)*:
```
Γ, A ⊢ Δ              Γ, B ⊢ Δ
─────────             ─────────
Γ, A & B ⊢ Δ         Γ, A & B ⊢ Δ
```
To use a with, choose one side (external choice).

*Plus Right (⊕R₁)* and *(⊕R₂)*:
```
Γ ⊢ A, Δ              Γ ⊢ B, Δ
─────────             ─────────
Γ ⊢ A ⊕ B, Δ          Γ ⊢ A ⊕ B, Δ
```
To prove a plus, choose one side (internal choice).

*Plus Left (⊕L)*:
```
Γ, A ⊢ Δ      Γ, B ⊢ Δ
──────────────────────
   Γ, A ⊕ B ⊢ Δ
```
To use a plus, be ready for either case.

*Additive Units*:
```
────────     (⊤R)
Γ ⊢ ⊤, Δ
```
Top can always be proven (no left rule--you can't use ⊤).

```
           (0L)
─────────
Γ, 0 ⊢ Δ
```
Zero proves anything (no right rule--you can't prove 0).

#### Linear Implication

*Implication Right (⊸R)*:
```
Γ, A ⊢ B, Δ
────────────
Γ ⊢ A ⊸ B, Δ
```
To prove A ⊸ B, assume A and prove B.

*Implication Left (⊸L)*:
```
Γ ⊢ A, Δ      Σ, B ⊢ Π
──────────────────────
  Γ, Σ, A ⊸ B ⊢ Δ, Π
```
To use A ⊸ B, provide an A to get a B.

#### Exponentials

*Bang Right (!R)*:
```
  Γ ⊢ A
─────────
!Γ ⊢ !A
```
Where !Γ means every formula in Γ is wrapped in !.
To prove !A, prove A using only unlimited resources.

*Bang Left (!L)*:
```
Γ, A ⊢ Δ
─────────
Γ, !A ⊢ Δ
```
You can extract one copy from unlimited copies (dereliction).

*Weakening (!W)*:
```
  Γ ⊢ Δ
─────────
Γ, !A ⊢ Δ
```
Unlimited resources can be discarded.

*Contraction (!C)*:
```
 Γ, !A, !A ⊢ Δ
───────────────
   Γ, !A ⊢ Δ
```
Unlimited resources can be duplicated.

*Question Mark (Dual to !)*:
The rules for ?A are dual to those for !A (swap left/right, premises/conclusions).

#### Negation

*Negation Right (¬R)*:
```
A, Γ ⊢ Δ
─────────
Γ ⊢ A⊥, Δ
```

*Negation Left (¬L)*:
```
Γ ⊢ A, Δ
─────────
Γ, A⊥ ⊢ Δ
```

Linear negation satisfies (A⊥)⊥ = A (involution).

#### Example Derivation

Let's prove (A ⊗ B) ⊸ (B ⊗ A) (tensor is commutative):

```
─────────      ─────────
  B ⊢ B         A ⊢ A         (Identity)
─────────────────────────     (⊗R)
      A, B ⊢ B ⊗ A
      ─────────────           (⊗L)
      A ⊗ B ⊢ B ⊗ A
      ─────────────           (⊸R)
      ⊢ (A ⊗ B) ⊸ (B ⊗ A)
```

Reading bottom-to-top:
1. Start with the goal: ⊢ (A ⊗ B) ⊸ (B ⊗ A)
2. Apply ⊸R: assume A ⊗ B, prove B ⊗ A
3. Apply ⊗L on the left: decompose A ⊗ B into A, B
4. Apply ⊗R: split the context to prove B and A independently
5. Apply Identity twice: B ⊢ B and A ⊢ A

The beauty is that each connective's meaning emerges from its inference rules.
The rules aren't arbitrary--they encode the exact resource behavior we want.



### Phase Semantics and Models

Linear logic can be interpreted through *phase semantics*, where:
- A phase space is a commutative monoid M with a closure operator
- Propositions are interpreted as subsets (phases) of M
- ⊗ corresponds to the monoid operation
- Linear negation (−)⊥ corresponds to orthogonal complement

This provides an algebraic/geometric understanding of
linear propositions as "zones" in a resource space.

Phase semantics is deeply satisfying because it gives linear logic a
*geometric* interpretation. Propositions aren't just syntactic formulas--
they're actual regions of a mathematical space. Implication becomes
"if you're in region A, you can reach region B." Tensor becomes "the
Minkowski sum of regions." It's logic as geometry.

The orthogonality relation is key: A⊥ is the set of all elements that
"annihilate" with elements of A under the monoid operation. This makes
negation a spatial notion--the dual of a region is its orthogonal complement.


### Proof Nets

Girard also developed *proof nets*, a graph-theoretic representation
of linear logic proofs that eliminates syntactic bureaucracy.
Unlike sequent proofs, proof nets represent the essential structure
of deduction without spurious ordering choices. They're the "true proofs"
beneath different sequential presentations.

Sequent proofs have artificial choices: do you apply the ⊗-right rule
before or after the ⊸-right rule? Different orders give different
proof trees, but they're really the same proof--just written differently.

Proof nets solve this by representing proofs as *graphs*, where:
- Formulas are vertices
- Inference rules are edges with specific patterns
- The order of rule applications doesn't matter

The correctness criterion (Danos-Regnier criterion for multiplicatives)
ensures that a graph is a valid proof net. It's a beautiful mix of
logic and graph theory--proof theory becomes combinatorics.

Proof nets also reveal the deep connection to Petri nets, flowcharts,
and other models of concurrent computation. A proof net *is* a dataflow
graph--it shows how resources flow through a computation.


### The Curry-Howard-Lambek Correspondence

Linear logic has a beautiful computational interpretation
through the Curry-Howard correspondence:
- *Propositions* <-> *Types*
- *Proofs* <-> *Programs*  
- *Proof normalization* <-> *Computation*

In this correspondence:
- A ⊸ B corresponds to linear functions (consuming their argument exactly once)
- A ⊗ B corresponds to pairs that must be deconstructed exactly once
- !A corresponds to values that can be freely duplicated
- Proof reduction corresponds to beta-reduction (function application)

This isn't just an analogy--it's a precise mathematical correspondence.
Every proof in linear logic is a program. Normalizing the proof (simplifying
it) corresponds to running the program. The final normal form is the
program's result.

What makes linear logic special is that this correspondence is *resource-aware*.
Classical Curry-Howard gives you lambda calculus, but it's wasteful--variables
can be duplicated or ignored freely. Linear Curry-Howard gives you *linear
lambda calculus*, where every variable is used exactly once. This matches
reality: memory isn't free, functions can't magically duplicate their inputs.


### Variants and Extensions

*Intuitionistic Linear Logic (ILL)*: Restricts to single conclusions (Γ ⊢ A),
making it more directly applicable to programming.

ILL removes the classical "multiple conclusion" feature. In classical
linear logic, Γ ⊢ A, B means "from Γ, produce either A or B (environment's
choice)." In ILL, you can only produce one thing. This matches functional
programming better--functions return one value, not "one of several values,
caller's choice."

*Light Linear Logic*: Restricts exponentials to ensure polynomial-time complexity,
capturing "feasible" computation.

Light linear logic is genius: it puts syntactic restrictions on the !
modality that *guarantee* all provable functions are polynomial-time
computable. It's a logic that captures exactly the "efficiently computable"
functions. This connects proof theory to complexity theory in a deep way.

*Differential Linear Logic*: Adds operators for analyzing program sensitivity,
connecting to differentiation in calculus.

Differential linear logic adds a "derivative" operator that measures how
much a proof "depends on" a particular assumption. This isn't metaphorical--
it literally connects to calculus. The derivative of a function (in the
analytic sense) corresponds to the logical derivative in the proof.


### Why Linear Logic Matters

Linear logic isn't just academic abstraction. It's a fundamental rethinking
of what logic *is*. Classical logic is about eternal truths. Linear logic
is about processes, transformations, and resources.

This has profound implications:

*Concurrency*: Linear logic naturally models concurrent processes. Tensor
is parallel composition, par is synchronization. Proof nets are dataflow
graphs. Linear logic gives a logical foundation for concurrency.

*Quantum Computing*: Quantum states can't be copied (no-cloning theorem)
and must be used exactly once. Linear logic is a natural fit for reasoning
about quantum computation.

*Game Semantics*: Linear logic can be interpreted as a game between two
players (you and the environment). Connectives become game operations.
Proofs become winning strategies. This connects logic to game theory.

*Programming Language Theory*: Linear types solve real problems. They
prevent resource leaks, enable safe manual memory management, and make
concurrency safer. Rust's ownership system is linear logic in disguise.

The philosophical shift is profound. Classical logic assumes a platonic
realm of eternal truths. Linear logic assumes a physical world of limited
resources that change over time. It's logic for engineers, not just
mathematicians.


### Connection to Programming Languages

#### The Resource Problem in Traditional Type Systems

Standard type systems face a fundamental mismatch: types are treated as
infinitely reusable, but many computational resources aren't. Consider:

```c
FILE* f = fopen("data.txt", "r");

fclose(f);

fclose(f);
```

The type system knows `f` is a file pointer, but not that `fclose` *consumes* it.
This mismatch causes:
- Memory leaks (forgetting to deallocate)
- Use-after-free bugs (using consumed resources)
- Double-free errors (deallocating twice)
- Data races (sharing mutable state unsafely)

Every C programmer has written these bugs. They're not stupidity--they're
the inevitable result of a type system that *can't express* resource
ownership. The type FILE* means "pointer to a file structure," not
"exclusive ownership of an open file handle."


#### Linear Types: Exact Usage

A *linear type system* ensures every variable is used *exactly once*.
If `x` has linear type `T`, then:
- `x` must appear exactly once in the rest of the program
- `x` cannot be duplicated or ignored
- Passing `x` to a function *moves* it (the caller loses access)

```rust
// Conceptual linear type system
fn linear_example() {
    let x: LinearInt = LinearInt::new(5);
    
    consume(x);  // x is moved here
    
    // consume(x);  // ERROR: x already used
    // let y = x;   // ERROR: x already used
}
```

This solves resource management: closing a file consumes it,
so the type system prevents double-close.

But pure linearity is harsh. What if you just want to ignore a return
value? What if you want to read a value without consuming it? Pure
linear types say "too bad, use it exactly once or the code doesn't compile."


#### Affine Types: At Most Once

*Affine types* relax linear types: variables must be used
*at most once* (they can be discarded). This is more
practical--sometimes you want to ignore a return value or abandon a resource.

Rust uses affine types (disguised as "ownership"):

```rust
fn affine_example() {
    let s = String::from("hello");
    
    // OK: s moved to consume
    consume(s);
    
    // ERROR: s already moved
    // println!("{}", s);
}

fn affine_with_drop() {
    let s = String::from("hello");
    
    // OK: s dropped at scope end (used zero times)
    
    // The Drop trait is called automatically
}
```

Rust's *ownership* is essentially affine types:
- Each value has one owner
- Ownership can be transferred (move)
- Owner can be dropped (zero uses)

But Rust adds *borrowing* to allow temporary, controlled sharing.

The genius of Rust is that it combines affine types (ownership) with
*borrowing* (temporary aliasing). You can't have two owners, but you
can have many *borrowers*--readers who temporarily access the data
without taking ownership.

This solves the usability problem of pure linear types. You can pass
a reference (&T) to a function without moving the value. The function
can read it, but the caller still owns it. It's like lending someone
a book--they can read it, but it's still your book.


#### Relevant Types: At Least Once

*Relevant types* ensure variables are used *at least once*
(can be duplicated). This prevents resource leaks—you can't forget to close a file:

```rust
// Conceptual relevant type system
fn relevant_example() {
    let f: RelevantFile = open_file("data.txt");
    
    // ERROR: f not used before scope end
    
}  // Compile error: f must be explicitly closed

fn relevant_correct() {
    let f: RelevantFile = open_file("data.txt");
    close(f);  // OK: f used
}
```

Relevant types are less common in practice than affine types, but they're
useful for certain scenarios. The idea is: you can copy this value as
much as you want, but you *must* use it at least once. No ignoring it.

This is useful for ensuring actions are taken. If a function returns
"you must call this cleanup function," relevant types ensure you can't
just ignore that obligation.


#### Affine Types in Practice: Rust

Rust's type system is fundamentally affine:

```rust
struct FileHandle { /* ... */ }

impl FileHandle {
    // Constructor: produces owned value
    fn open(path: &str) -> FileHandle { /* ... */ }
    
    // Consuming method: takes self by value (moves ownership)
    fn close(self) { /* ... */ }
    
    // Borrowing method: takes &mut self (temporary exclusive access)
    fn write(&mut self, data: &[u8]) { /* ... */ }
}

fn usage() {
    let mut f = FileHandle::open("data.txt");
    
    f.write(b"hello");  // Borrows f mutably
    f.write(b"world");  // Can borrow again after first borrow ends
    
    f.close();  // Moves f, consuming it
    
    // f.write(b"!");  // ERROR: f moved
}
```

Key features:

1. *Move semantics*: By default, assignment/passing moves ownership
2. *Borrowing*: `&T` (shared) and `&mut T` (exclusive)
   allow temporary access without consuming
3. *Copy trait*: Types that implement `Copy` are duplicated
   instead of moved (for cheap-to-copy types like integers)
4. *Drop trait*: Automatic cleanup when values go out of scope

The Drop trait is crucial. When a value goes out of scope, Rust
automatically calls its destructor. This is affine logic at work:
the value can be used zero times (dropped without explicit use) or
one time (explicitly consumed), but not more.

Borrowing is the escape hatch that makes affine types practical. Without
it, you'd constantly be moving values around, unable to pass the same
value to multiple functions. With borrowing, you get the safety of
affine types with the usability of normal programming.


#### Linear Logic Connectives in Types

The correspondence between linear logic and types:

*A ⊸ B* (linear function): Function that consumes its argument exactly once

```rust
fn consume_string(s: String) -> usize {
    s.len()
}
```

In Rust, any function that takes a non-Copy type by value is a linear
function. The argument is moved in and consumed.

*A ⊗ B* (linear pair): Pair that must be deconstructed exactly once

```rust
struct LinearPair<A, B>(A, B);

fn use_pair(p: LinearPair<String, i32>) {
    let LinearPair(s, n) = p;  // Must destructure to use
    // Both s and n must now be used
}
```

A tuple of non-Copy types is a tensor. You must destructure it to use
the components, and once you do, both components must be used.

*A & B* (choice): A value offering both capabilities (you pick one)

```rust
enum Choice<A, B> {
    Left(A),
    Right(B),
}
// Receiver chooses which branch when pattern matching
```

An enum is an additive choice. The value contains either A or B, and
pattern matching lets you pick which one you got.

*!A* (unlimited): Can be duplicated freely

```rust
// In Rust: types implementing Copy
let x: i32 = 5;  // i32 implements Copy
let y = x;       // x duplicated, not moved
let z = x;       // Can use x again
```

Types implementing Copy are "unrestricted" in linear logic terms.
They can be duplicated freely, like values wrapped in !.


#### Beyond Rust: Linear Type Systems

*ATS (Applied Type System)*: Supports both linear and proof-carrying types,
allowing you to prove resource safety properties.

ATS is hardcore. It has linear types for resource management *and*
dependent types for proving correctness properties. You can write
a sort function and prove it actually sorts, all in the type system.
The learning curve is steep, but it's the most powerful type system
in practical use.

*Clean*: Uses uniqueness types (similar to linear types) to
ensure safe in-place updates and I/O.

Clean's uniqueness types are interesting because they're designed for
*performance*, not just safety. By marking types as unique, the compiler
knows it can do destructive updates in place--no copying needed. It's
linear types for efficiency.

*Haskell with Linear Types*: GHC 9.0+ added linear types as an extension:

```haskell
-- %1 means linear (must use exactly once)
-- %m means multiplicity-polymorphic

consume :: a %1 -> ()
consume x = ()

duplicate :: a %1 -> (a, a)  -- Type error! Can't duplicate linear value

withFile :: FilePath -> (Handle %1 -> IO a) %1 -> IO a
withFile path action = do
    h <- openFile path
    result <- action h
    closeFile h  -- h used exactly once in action
    return result
```

Haskell's approach is interesting: linear types are *opt-in*. Most of
Haskell is still the usual unrestricted types, but you can mark specific
functions as linear when you need resource safety. The %1 annotation
means "linear multiplicity"--this argument must be used exactly once.


#### Session Types: Linear Logic for Communication

Session types are a beautiful application of linear logic to concurrent
programming. The idea: a communication protocol is a linear logic proposition.

Imagine a protocol: "send a number, receive a string, then close the channel."
In session types, this is:
```
    !Int ⊸ ?String ⊸ End
```
The ! means "send," ? means "receive," ⊸ means "then." It's a linear
type because the channel must be used in exactly this order. You can't
receive before sending. You can't forget to close the channel. The type
system enforces the protocol.

This is linear logic in action: a channel is a resource that must be
used exactly according to its protocol. Tensor (⊗) becomes parallel
composition of channels. Par (⅋) becomes synchronized communication.
The correspondence is perfect.


#### Practical Benefits

Linear/affine types catch bugs at compile time:

1. *Memory safety without GC*: Rust prevents use-after-free, double-free,
   and leaks through affine types
2. *Resource management*: Files, sockets, locks automatically handled correctly
3. *Protocol enforcement*: Can encode state machines in types (e.g., socket
   must be connected before sending)
4. *Fearless concurrency*: Affine types + borrowing prevent data races by
   ensuring exclusive access to mutable data

The cost is a steeper learning curve—programmers must think explicitly
about ownership and lifetimes. But the payoff is entire classes of bugs
eliminated at compile time, without runtime overhead.

Consider data races. In most languages, if two threads access the same
memory location and at least one writes, you have undefined behavior.
Race conditions are notoriously hard to debug. Rust makes them *impossible*
through the type system:
- To mutate, you need &mut T (exclusive borrow)
- You can have many &T (shared borrows) or one &mut T, never both
- The type system enforces this at compile time

This is linear logic: a mutable reference is a linear resource. You
can't copy it. When you pass it to a function, you give up access.
The resource discipline of linear logic becomes the memory discipline
of safe concurrency.


### Linear Logic and the Future

Linear logic isn't just a theoretical curiosity. It's increasingly
relevant as programming moves toward:

*Manual memory management without garbage collection*: Rust shows that
linear types can give C-like performance with high-level safety. As
systems move to embedded devices, IoT, and performance-critical
applications, GC-free memory management becomes crucial.

*Correctness-critical systems*: In aerospace, medical devices, and
autonomous vehicles, bugs aren't just annoying--they're deadly. Linear
types catch whole categories of bugs at compile time. They're not
just optimization; they're verification.

*Concurrent and parallel programming*: As CPUs plateau in single-thread
performance and shift to more cores, concurrency becomes unavoidable.
Linear types make concurrency *safe* by preventing data races at the
type level.

*Quantum computing*: Quantum bits can't be copied (no-cloning theorem)
and must be used carefully. Linear logic is the natural framework for
quantum programming languages.

The insight of linear logic--that resources have to be managed carefully,
that copying isn't free, that actions have consequences--is exactly what
computation needs. Classical logic is beautiful but unrealistic. Linear
logic is realistic. It's logic for a world where memory is finite, time
is real, and actions matter.


### Conclusion: Logic Meets Reality

Linear logic represents a fundamental shift in how we think about logic.
Classical logic is the logic of eternal truths--mathematical facts that
exist outside time. Linear logic is the logic of *processes*--things
that happen, resources that flow, states that change.

For programmers, this shift is profound. We don't write programs that
compute eternal truths. We write programs that manipulate memory, open
files, send network packets, and manage state. These are *resources*,
not truths. They must be tracked, accounted for, and managed carefully.

Linear logic gives us the tools to do this *in the type system*. Instead
of hoping programmers remember to close files and free memory, we make
it a logical necessity. Instead of finding race conditions with testing,
we prevent them with types. Instead of debugging use-after-free at 3 AM,
we catch it at compile time.

The cost is complexity. Linear types are harder to learn than classical
types. Rust's ownership system has a reputation for a steep learning
curve. But the payoff is real: entire categories of bugs--use-after-free,
double-free, memory leaks, data races--simply can't happen in a well-typed
linear program.

As we build increasingly complex systems--distributed databases, autonomous
vehicles, spacecraft--we need stronger guarantees. Testing finds bugs,
but it can't prove their absence. Linear types *prove* resource safety.
They're not just a tool for writing correct programs--they're a tool
for *knowing* your program is correct.

Linear logic's insight--that resources matter, that they must be tracked,
that copying and discarding aren't free--turns out to be exactly what
programming needs. By embedding linear logic into type systems, we get
languages that align with how computers actually work. We catch resource
errors before the program ever runs. We turn debugging into proof.

That's the promise of linear logic: logic that matches reality, types
that track resources, and programs that are correct by construction.


### Reference

- Girard, J.-Y. (1987). Linear logic. *Theoretical Computer Science*, *50*(1), 1-102.

- Girard, J.-Y. (1995). Linear logic: Its syntax and semantics. In J.-Y. Girard, Y. Lafont, & L. Regnier (Eds.), *Advances in linear logic* (pp. 1-42). Cambridge University Press.

- Lincoln, P., & Mitchell, J. (1992). Computational aspects of linear logic. *Theoretical Computer Science*, *111*(1-2), 3-43.

- Wadler, P. (1993). A taste of linear logic. In A. M. Borzyszkowski & S. Sokołowski (Eds.), *Mathematical foundations of computer science 1993* (pp. 185-210). Springer.

- Abramsky, S. (1993). Computational interpretations of linear logic. *Theoretical Computer Science*, *111*(1-2), 3-57.

- Girard, J.-Y., Lafont, Y., & Taylor, P. (1989). *Proofs and types*. Cambridge University Press.

- Troelstra, A. S. (1992). *Lectures on linear logic*. CSLI Publications.

- Girard, J.-Y. (1987). Proof-nets: The parallel syntax for proof theory. In A. Ursini & P. Aglianò (Eds.), *Logic and algebra* (pp. 97-124). Marcel Dekker.

- Danos, V., & Regnier, L. (1989). The structure of multiplicatives. *Archive for Mathematical Logic*, *28*, 181-203.


#### Programming

- Wadler, P. (1990). Linear types can change the world! In M. Broy & C. Jones (Eds.), *Programming concepts and methods* (pp. 347-359). North Holland.

- Walker, D. (2005). Substructural type systems. In B. C. Pierce (Ed.), *Advanced topics in types and programming languages* (pp. 3-43). MIT Press.

- Baker, H. G. (1992). Lively linear Lisp—'Look Ma, no garbage!' *ACM SIGPLAN Notices*, *27*(8), 89-98.

- Jung, R., Jourdan, J.-H., Krebbers, R., & Dreyer, D. (2017). RustBelt: Securing the foundations of the Rust programming language. *Proceedings of the ACM on Programming Languages*, *2*(POPL), Article 66.

- Bernardy, J.-P., Boespflug, M., Newton, R. R., Peyton Jones, S., & Spiwack, A. (2018). Linear Haskell: Practical linearity in a higher-order polymorphic language. *Proceedings of the ACM on Programming Languages*, *2*(POPL), Article 5.


#### Applications and Extensions

- Lincoln, P., Mitchell, J., Scedrov, A., & Shankar, N. (1992). Decision problems for propositional linear logic. *Annals of Pure and Applied Logic*, *56*(1-3), 239-311.

- Danos, V., Joinet, J.-B., & Schellinx, H. (1997). A new deconstructive logic: Linear logic. *Journal of Symbolic Logic*, *62*(3), 755-807.

- Dal Lago, U., & Hofmann, M. (2011). Bounded linear logic, revisited. *Logical Methods in Computer Science*, *7*(4), 1-31.

- Caires, L., & Pfenning, F. (2010). Session types as intuitionistic linear propositions. In P. Gastin & F. Laroussinie (Eds.), *CONCUR 2010—Concurrency theory* (pp. 222-236). Springer.

- Pfenning, F. (n.d.). *Linear logic* [Lecture notes]. CMU 15-816, Carnegie Mellon University.

- Lafont, Y. (1993). *Introduction to linear logic* [Course notes]. University of Marseille.

- Abrusci, V. M., & Ruet, P. (1999). Non-commutative logic I: The multiplicative fragment. *Annals of Pure and Applied Logic*, *101*(1), 29-64.

