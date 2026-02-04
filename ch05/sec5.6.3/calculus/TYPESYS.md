
### Introduction to Type Systems

- [Luca Cardelli: Type Systems](http://lucacardelli.name/papers/typesystems.pdf)

An introduction I found valuable reading about type systems many years ago is Luca Cardelli's
paper "Type Systems" (from 1996). You might find it interesting too. It explores the formal
side of things in a very clear way. At its core, a type system is like a set of rules in a
programming language that helps classify values and expressions into categories called *types*.
These types tell the computer (or the programmer) what kind of data something is (like numbers,
text, or lists) and what operations are allowed on them. A type system prevents "disasters"
in code by catching mismatches early.

Cardelli's paper puts it nicely: The main goal of a type system is to *prevent execution errors*
during runtime. An execution error is when your program crashes or does something unexpected,
like trying to add a number to a word (e.g., 5 + "apple" = ?). In untyped languages (like raw
machine code or pure lambda calculus, a simple mathematical model of computation), there's no
such protection—anything goes, which can be flexible but risky.


#### Typed vs. Untyped Languages: A Simple Distinction

- *Untyped Languages*: These don't have built-in types. Everything is treated as raw data, like bits in memory.
  Examples include assembly language or the untyped lambda calculus (a formal system where functions are defined
  as λx.M, meaning "a function that takes x and returns M"). It's powerful for theory but error-prone in practice
  because there's no check to stop you from applying a function to the wrong kind of input.
  
- *Typed Languages*: Here, every value has a type, and the language enforces rules. For instance, in a typed
  lambda calculus (often called λ-calculus with types), you might write λx:Int. x + 1, meaning "a function
  that takes an integer x and adds 1 to it." If you try to pass a string instead, the system flags it as
  a *type error*.

Cardelli emphasises that even "untyped" languages can be seen as having a single universal type
(everything fits into one big category), but typed ones have more structure to catch problems.


#### Key Formal Aspects: Keeping It Light

1. *Type Checking*: This is the process of verifying if a program follows the type rules.
   It can happen at *compile time* (static checking, before running) or *runtime*
   (dynamic checking, while running).
   - *Static Typing*: Checks types early. Example: In Java, you declare `int x = 5;`--the
     compiler ensures you don't treat x as a string later.
   - *Dynamic Typing*: Checks at runtime. Example: Python lets you do `x = 5; x = "hello";`
     but crashes if you try `x + 1` after reassigning.
   - Formal idea: Type rules look like judgments, e.g., Γ ⊢ e : T, which reads "in environment Γ,
     expression e has type T." (Γ is like a list of variable types.)

2. *Type Inference*: Sometimes, the system figures out types automatically without you declaring them.
   In languages like ML or Haskell, you can write a function without specifying types, and the compiler
   infers them based on usage. Cardelli notes this blends flexibility with safety.

3. *Strong vs. Weak Typing*: 
   - *Strong Typing*: Strictly enforces types--no conversions. If something's not compatible,
     it errors out (e.g., no automatic "5" + 3 in strongly typed languages).
   - *Weak Typing*: Allows implicit conversions, like in C where an int might quietly become a float.
     Cardelli warns that weak typing can lead to subtle bugs, as it relaxes rules too much.

4. *Polymorphism*: This is a way of saying "types that work in multiple ways." 
   - *Parametric Polymorphism*: Like generics in Java--a list that can hold any type, as long as it's consistent (e.g., List<T>).
   - *Subtype Polymorphism*: In object-oriented languages, a subclass can stand in for its parent (e.g., a "Cat" is a subtype of "Animal").
   - Formal touch: Cardelli uses examples from typed lambda calculus, like ∀α. α → α
     (a function that takes any type α and returns the same type, like an identity function).


#### Benefits

Type systems make code safer, easier to debug, and more efficient (compilers can optimise better).
They also help with big projects--imagine a team where everyone knows what data to expect.
Cardelli's paper shows how these ideas come from formal logic and math, like lambda calculus,
which underpins modern functional programming.

If a program is well-typed under a sound type system, it won't have certain runtime errors
(this is called *type safety*). But remember, types don't catch everything--like logic bugs
(e.g., dividing by zero might be typed correctly but still crash).


#### An Example

Let's end with a simple example. Suppose we have a tiny language with numbers and addition:

- Type rule for numbers: `⊢ 5 : Int` (5 has type integer).
- Type rule for addition: __If__ `⊢ e1 : Int` __and__ `⊢ e2 : Int`, __then__ `⊢ e1 + e2 : Int`.

So, 5 + 3 is fine (Int + Int = Int), but 5 + "hello" fails because "hello" isn't Int.


### Building on the Basics

We covered the basics—types as classifiers for values, typed vs. untyped paradigms, and core
mechanisms like type checking and inference. Let's raise the level into more structured reasoning
about why type systems work. Assume you're comfortable with simple programming concepts and
basic lambda notation; we'll use that to explore type safety, polymorphism in depth, and subtyping,
with some lightweight proofs and examples. This isn't full rigour, but it'll build logical
intuition for analysing programs.


#### Type Safety: Proving Your Program Won't Go Wrong

One of Cardelli's key contributions is emphasising *type soundness* (or type safety), a property
that ensures well-typed programs don't exhibit certain bad behaviours at runtime. In formal terms:
If a program is *well-typed*, it either progresses (reduces to a value) or gets stuck only in
expected ways—not due to type mismatches.

- *Progress and Preservation*: These are the twin pillars of soundness, from Milner-style type systems.
  - *Progress*: A well-typed expression that's not a value can take a step (reduce) without error.
    No "stuck" states like applying a non-function.
  - *Preservation*: If an expression e has type `T` and reduces to `e'`, then `e'` also has type `T`.
    Types are invariant under execution.

Consider our tiny language. Extend it to include functions via simply typed lambda calculus (STLC):

- Syntax: `e ::= x | λx:T. e | e e | n | e + e`  (variables, abstractions, applications, numbers, addition).
- Typing rules (selected, in judgmental form):
  - For abstraction: If Γ, x:T1 ⊢ e : T2, then Γ ⊢ λx:T1. e : T1 → T2.
  - For application: If Γ ⊢ e1 : T1 → T2 and Γ ⊢ e2 : T1, then Γ ⊢ e1 e2 : T2.
  - (Plus the number/add rules as above.)

Example: `Let id = λx:Int. x`. Then `id` has type `Int → Int`. Applying `id 5` yields `5` (type `Int`),
but `id "hello"` fails type checking (no string type here yet). Soundness theorem (sketch): By induction on
the derivation, show progress (e.g., if it's an app, check if `e1` is lambda) and preservation
(reduction preserves typing).

Why reason this way? It lets us prove absence of errors like "function applied to wrong argument"
before running code. Cardelli notes that in untyped lambda, you can write `(λx. x x) (λx. x x)` which
loops forever, but typing prevents self-application mismatches.


#### Polymorphism: Generalising Types for Reuse

We touched on polymorphism briefly; let's reason through its variants and why it's powerful.
Polymorphism allows code to work over multiple types without duplication, but with safety.

- *Parametric Polymorphism (Generics)*: Types with variables, like `∀α. α → α` (universal quantification).
  The identity function `id = λx. x` can be instantiated for any `α` (e.g., `Int → Int` or `Bool → Bool`).
  - Formal reasoning: In System F (a polymorphic lambda calculus), typing includes introduction/elimination for ∀.
    - Intro: If Γ ⊢ e : T (with α free), then Γ ⊢ Λα. e : ∀α. T (type abstraction).
    - Elim: If Γ ⊢ e : ∀α. T, then Γ ⊢ e [U] : T[α/U] (instantiate with U).
  - Benefit: Reuse without casting. Example: A list reverse function rev: `∀α. List α → List α`.
    Proving type safety here involves showing that polymorphic code doesn't "leak" type info--α is abstract.

- *Ad-hoc Polymorphism (Overloading)*: Operators like `+` work on ints or floats differently.
  Cardelli contrasts this with parametric: Ad-hoc requires runtime dispatch, potentially less safe.

- *Inclusion Polymorphism (Subtyping)*: Central to object-oriented typing. If `S <: T` (S is subtype of T),
  then values of S can be used where T is expected.
  - Reasoning: Subtyping rules, e.g., for records: If `{l1:T1, l2:T2} <: {l1:T1}`, you can "forget"
    fields (width subtyping). For functions: If `T1 <: S1` and `S2 <: T2`, then `S1 → S2 <: T1 → T2`
    (contravariant in args, covariant in results).
  - Example: `Animal = {name:String, speak:Unit→String}; Cat = {name:String, speak:Unit→String, purr:Unit→Unit}`.
    Then `Cat <: Animal`. You can pass a Cat to a function expecting Animal.
  - Complex bit: Subtyping + references can break soundness (e.g., Java's array covariance issues).
    Cardelli discusses bounded quantification (`∀α<:T. ...`) to tame this.

To reason about a polymorphic program: Use type substitution
lemmas--replacing α with a concrete type preserves typing.


#### Untyped as Unityped: A Unifying View

Cardelli's insight: Untyped languages aren't type-less; they're *unityped*—everything has a single type,
say "Any" or "Dyn" (dynamic). This lets us embed untyped into typed systems.
- Embedding: Map untyped `λx.M` to `λx:Dyn. M`, with implicit checks.
- Reasoning: Type reconstruction algorithms (like Hindley-Milner) can infer types for untyped code if possible,
  failing otherwise. This bridges dynamic languages (Python) to static ones (via gradual typing).


#### Challenges and Extensions

Raising the bar means acknowledging limits:
- *Type-Dependent Types*: Beyond Cardelli, dependent types (e.g., in Coq) let types depend on values,
  enabling proofs like "vector of length n".
- *Effects*: Pure types ignore side effects (IO, exceptions). Cardelli hints at monads or effect systems
  for handling them.
- *Inference Complexity*: Full polymorphism is undecidable in higher kinds, so languages approximate.

Try this exercise: Prove by contradiction that in STLC, you can't type the untyped omega combinator
(self-applying loop). Assume it has type T; derive inconsistency.

For hands-on: Implement a tiny type checker in Python (use pattern matching for expressions).
If this level clicks, explore Cardelli's sections on higher-order types or bounded quantification--they
build on these ideas for real-world systems like ML or Java.



### Addition to Cardelli

While Cardelli's paper provides a strong foundation in type safety, polymorphism, and inference,
the code examples in this repository extend these ideas with practical features common in functional
languages like ML or Haskell. These additions address recursion, algebraic data types (ADTs),
pattern matching, and explicit polymorphism, enabling more expressive and real-world programming
while maintaining soundness.


#### Recursive Types and Functions

Recursive types (e.g., μ α. τ) allow defining infinite structures like lists or trees directly in
the type system, preventing type errors in self-referential data. In `recur.py`, we implement μ-types
via `RecursiveType` and support recursive functions with `LetRec` and `Fix` combinators. For instance, 
factorial or list folds infer types like `Int → Int` or `(α → β → β) → β → List α → β`, handling occurs
checks to avoid infinite types during unification. This builds on Cardelli's unityped view by safely
embedding untyped recursion (e.g., Y-combinator) into typed systems.


#### Hindley-Milner Type Inference in Detail

Cardelli touches on inference, but the Hindley-Milner (HM) algorithm (Algorithm W) provides a concrete
mechanism for polymorphic inference without annotations. In `hm.py`, we detail unification (`unify` for
equating types via substitutions), generalisation (`generalize` for ∀-quantification), and instantiation,
inferring types like `α → β → α` for constants. This adds decidable polymorphism to simply typed lambda
calculus (`lambda.py`), with fresh variables and composition ensuring efficiency and safety.


#### Algebraic Data Types and Pattern Matching

ADTs like sums (e.g., Maybe α = None | Some α) and products (e.g., Pair α β) extend polymorphism for
structured data, with constructors and destructors. `generics.py` and `recur.py` use `TypeApplication`
for generics and `Match` for exhaustive pattern matching, inferring unified types across cases
(e.g., `Maybe Int → Int` for unwrap-or-zero). This enhances Cardelli's record/subtyping focus by
incorporating ML-style variants, ensuring type safety in data decomposition.


#### System F: Explicit Polymorphism

For finer control, System F adds explicit universal types (∀α. τ) with type abstraction
(`TypeAbs` as Λα. e) and application (`TypeInstantiation` as e [τ]). In `generics.py`,
this allows instantiating generics like `∀α. α → α` to `Int → Int`, contrasting HM's
implicit style. It addresses Cardelli's higher-order types, enabling rank-n polymorphism
while preserving decidability in inference.

These features, demonstrated through the Python implementations, show how type theory
evolves for practical use. For much deeper proofs, consult Pierce's
*Types and Programming Languages* (TAPL), Chapters 11 (ADTs), 22 (HM), and 23-24
(System F and recursion).

