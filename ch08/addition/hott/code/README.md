
## llang Tutorial - HoTT in the REPL

A progressive walkthrough from basic types to homotopy type theory.
Start the REPL with `./llang` and follow along.



### Part 1 - The basics

#### Natural numbers

Nat is defined inductively: `zero` is the base, `succ n` is the successor.

```
>> succ (succ (succ zero))
  normal : succ (succ (succ zero))
```

`natrec` is the recursor. It takes a motive, a base case, a step
function, and the scrutinee:

```
natrec (motive : Nat -> Type)
       (base   : motive zero)
       (step   : Pi(n:Nat). motive n -> motive (succ n))
       (n      : Nat)
     : motive n
```

Addition by recursion on the first argument:

```
>> let add : Nat -> Nat -> Nat = fn m n. natrec (fn _. Nat) n (fn _ acc. succ acc) m
   defined: add
>> add (succ (succ zero)) (succ zero)
   normal : succ (succ (succ zero))
```

Multiplication builds on addition:

```
>> let mul : Nat -> Nat -> Nat = fn m n. natrec (fn _. Nat) zero (fn _ acc. add n acc) m
   defined: mul
>> mul (succ (succ zero)) (succ (succ (succ zero)))
   normal : succ (succ (succ (succ (succ (succ zero)))))
```

Predecessor (returns zero for zero):

```
>> let pred : Nat -> Nat = fn n. natrec (fn _. Nat) zero (fn m _. m) n
   defined: pred
>> pred (succ (succ (succ zero)))
   normal : succ (succ zero)
```

The `:type` command infers a type via the core checker:

```
>> :type zero
   type   : Nat
>> :type succ zero
   type   : Nat
```


#### Booleans

```
>> let not : Bool -> Bool = fn b. boolrec (fn _. Bool) false true b
   defined: not
>> not true
   normal : false
>> not false
   normal : true

>> let and : Bool -> Bool -> Bool = fn a b. boolrec (fn _. Bool) b false a
   defined: and
>> and true false
   normal : false
>> and true true
   normal : true
```

The motive in `boolrec` gives the return type as a function of the
scrutinee. Here `fn _. Bool` means the return type is always `Bool`
regardless of which branch we take.


#### Functions and dependent products

Lambda syntax: `fn x. body` or `\x. body`. Multiple arguments: `fn x y. body`.

```
>> (fn x y. x) zero true
   normal : zero

>> (fn f x. f (f x)) (fn n. succ n) zero
   normal : succ (succ zero)
```

The identity function at any type (`Pi(A:Type). A -> A`):

```
>> let id : Pi(A : Type). Pi(_ : A). A = fn A x. x
   defined: id
>> id Nat (succ zero)
   normal : succ zero
>> id Bool true
   normal : true
```

Check its type:

```
>> :type id Nat zero
   type   : Nat
```

The `->` arrow is sugar for a non-dependent Pi. `Nat -> Nat` means
`Pi(_ : Nat). Nat`, where the return type doesn't mention the argument.


#### Sigma types (dependent pairs)

`Sg(x:A). B` is the dependent sum: a pair where the type of the second
component depends on the value of the first. `(a, b)` constructs a pair;
`fst p` and `snd p` project it.

```
>> fst (succ zero, true)
   normal : succ zero
>> snd (succ zero, true)
   normal : true
```

Swap a pair:

```
>> let swap : Pi(A : Type). Pi(B : Type). Sg(_ : A). B -> Sg(_ : B). A =
     fn A B p. (snd p, fst p)
   defined: swap
>> swap Nat Bool (succ zero, true)
   normal : (true, succ zero)
```

A dependent example - a pair of a Nat and a proof it equals itself:

```
>> :type (succ zero, refl (succ zero))
   type error: cannot infer type of pair ...
```

Pairs need an explicit annotation when the type is dependent:

```
>> :type ((succ zero, refl (succ zero)) : Sg(n : Nat). Id Nat n n)
   type   : Σ(n : Nat). Id Nat n n
```




### Part 2 - Identity types and path reasoning

The identity type `Id A a b` represents a proof that `a` and `b` are
equal (or more precisely: a *path* from `a` to `b` in type `A`).

`refl a : Id A a a` is the reflexivity proof / constant path.

```
>> :type refl zero
   type   : Id Nat zero zero
>> :type refl true
   type   : Id Bool true true
```

#### Built-in path operations

Four functions are loaded automatically from the stdlib:

*`sym`* - reverse a path (`a = b` becomes `b = a`):

```
sym : Pi(A:Type). Pi(a b : A). Id A a b -> Id A b a
```

```
>> sym Nat zero zero (refl zero)
   normal : refl zero
```

*`trans`* - concatenate paths (`a = b` and `b = c` gives `a = c`):

```
trans : Pi(A:Type). Pi(a b c : A). Id A a b -> Id A b c -> Id A a c
```

```
>> trans Nat zero zero zero (refl zero) (refl zero)
   normal : refl zero
```

*`ap`* - apply a function to a path (`a = b` gives `f a = f b`):

```
ap : Pi(A B : Type). Pi(f : A -> B). Pi(a b : A). Id A a b -> Id B (f a) (f b)
```

```
>> ap Nat Nat (fn n. succ n) zero zero (refl zero)
   normal : refl (succ zero)
```

*`transport`* - transport a value along a path (`a = b` lifts a proof
from `P a` to `P b`):

```
transport : Pi(A:Type). Pi(P : A -> Type). Pi(a b : A). Id A a b -> P a -> P b
```

```
>> transport Nat (fn _. Bool) zero zero (refl zero) true
   normal : true
```

All four are derived from the J eliminator - no axioms needed.


#### J - the path induction principle

J is the eliminator for identity types. It says: to prove something
about all paths `p : Id A a b`, it suffices to prove it for `refl a`.

```
J : Pi(A : Type). Pi(a : A).
    Pi(P : Pi(y:A). Pi(_ : Id A a y). Type).
    Pi(_ : P a (refl a)).
    Pi(b : A). Pi(p : Id A a b). P b p
```

J fires when the proof is `refl`:

```
>> J Nat zero (fn y _. Id Nat zero y) (refl zero) zero (refl zero)
   normal : refl zero
```

On a stuck path (open variable), J stays neutral:

```
>> J Nat zero (fn y _. Id Nat zero y) (refl zero) zero loop
   normal : [loop · J(Nat, zero, <fn>, refl zero, zero)]
```


#### Proving non-trivial equalities

We can prove `succ (succ zero) = succ (succ zero)` by reflexivity:

```
>> refl (succ (succ zero))
   normal : refl (succ (succ zero))
```

Check that `sym` is its own inverse - `sym (sym p) ≡ p` definitionally:

```
>> let p = refl (succ zero)
   defined: p
>> :conv sym Nat (succ zero) (succ zero) (sym Nat zero (succ zero) p) ; p
   lhs    : refl (succ zero)
   rhs    : refl (succ zero)
   conv   : yes
```

Here `:conv` checks *definitional equality* - both sides reduce to the
same normal form. This is stronger than propositional equality.


#### Heterogeneous equality and dependent paths

The identity type `Id A a b` requires `a` and `b` to lie in the *same*
type `A`. The type itself is the carrier.

This becomes important when reasoning about equalities between elements
of different types - a central concern in HoTT. For now, we can encode
many such proofs using `transport` to move between fibres.




### Part 3 - HoTT proper

#### What makes this HoTT

Classical Martin-Löf Type Theory treats all proof terms as definitionally
equal if they can be reduced to the same normal form. In MLTT, `Id A a b`
has at most one inhabitant (definitional proof-irrelevance via uniqueness
of identity proofs, UIP).

HoTT rejects UIP. The identity type `Id A a b` is interpreted as the
*space of paths* from `a` to `b`. A type is not just a set - it is a
space with a potentially non-trivial homotopy structure. Two paths between
the same endpoints can be different, and there can be paths-between-paths
(homotopies), paths-between-those, and so on.

This implementation includes:

- *Univalence* (`ua`) - equal types are identical
- *Function extensionality* (`funext`) - functions equal on all inputs are identical
- *Propositional truncation* (`‖A‖`) - squash a type to a proposition
- *The circle* (`S¹`) - a non-trivial higher type with a loop

The last two are Higher Inductive Types (HITs): types generated by both
point constructors *and* path constructors.


#### Univalence and function extensionality

These are present as axioms (they cannot be proved in MLTT):

```
>> :type ua
   type   : Π(A : Type_1). Π(B : Type_1). (equivalence) → Id Type_1 A B

>> :type funext
   type   : Π(A : Type). Π(B : A → Type). Π(f g : Π(x:A). B x).
            Π(_ : Π(x:A). Id (B x) (f x) (g x)). Id (Π(x:A). B x) f g
```

They are permanently stuck (no computation rule) - they produce neutral
terms that block further reduction. In Cubical Type Theory these would
compute; here they are assumed.

```
>> ua
   normal : <global:-1>
>> funext
   normal : <global:-2>
```


#### The circle S¹

S¹ is a HIT with one point constructor `base : S¹` and one path
constructor `loop : Id S¹ base base`.

```
>> :type base
   type   : S1
>> :type loop
   type   : Id S1 base base
```

`S1rec` is the recursion principle: to map out of S¹ into a type `B`,
provide an image for `base` and a path in `B` for `loop`.

```
S1rec : Pi(B : Type). Pi(b : B). Pi(l : Id B b b). S1 -> B
```

On `base` it fires; on `loop` it is stuck (loop is a neutral term):

```
>> S1rec Nat zero (refl zero) base
   normal : zero

>> S1rec Nat zero (refl zero) loop
   normal : [loop · S1rec(Nat, zero, refl zero)]
```

The second output is a *neutral term* - an irreducible expression blocked
by `loop`. It prints as a head-spine chain: the sentinel `loop` at the
head with `S1rec(...)` as a pending frame.

The constant map sends every point of S¹ to `zero`:

```
>> let const_map : S1 -> Nat = fn c. S1rec Nat zero (refl zero) c
   defined: const_map
>> const_map base
   normal : zero
>> const_map loop
   normal : [loop · S1rec(Nat, zero, refl zero)]
```

The loop case is a path `refl zero : Id Nat zero zero`, which is what the
constant map must send `loop` to - a trivial loop at `zero`.

Two maps into S¹ can be shown convertible when they have the same images:

```
>> :conv S1rec Nat zero (refl zero) base ; zero
   conv   : yes
```


#### Propositional truncation ‖A‖

`trunc A` (written `‖A‖` in HoTT) squashes a type to a *proposition*:
a type where all elements are equal. This lets us use data existentially
without exposing which element we have.

Constructors:
- `trint a` - inject `a : A` into `‖A‖` (one argument: the value)
- `squash` - the proof that all elements of `‖A‖` are equal (axiom)

Recursion principle `truncrec`:

```
truncrec : Pi(A : Type). Pi(B : Type).
           Pi(f : A -> B). trunc A -> B
```

This requires `B` to be a proposition (all elements equal) - otherwise
the result would depend on which element we chose. That constraint is
not checked computationally here; it is a typing obligation on the caller.

```
>> truncrec Nat Nat (fn n. succ n) (trint zero)
   normal : succ zero

>> truncrec Nat Bool (fn _. true) (trint (succ zero))
   normal : true
```

On a neutral truncated value, truncrec is stuck:

```
>> truncrec Nat Nat (fn n. n) loop
   normal : [loop · truncrec(Nat, Nat, <fn>)]
```


#### Why loop is a sentinel

In HoTT, `loop : Id S¹ base base` cannot be reduced - it is an
irreducible generator of the circle's fundamental group. The evaluator
treats it as a *stuck neutral*, like a free variable. Any computation
blocked on `loop` stays as a neutral term waiting for `loop` to be
supplied a concrete value - which it never will, because `loop` is not a
constructor of the identity type but a path axiom.

This is different from `refl a`, which is a constructor and fires J
immediately:

```
>> J Nat zero (fn _ _. Nat) (succ zero) zero (refl zero)
   normal : succ zero

>> J Nat zero (fn _ _. Nat) (succ zero) zero loop
   normal : [loop · J(Nat, zero, <fn>, succ zero, zero)]
```




### Part 4 - Well-founded types (W-types)

W-types `W(x:A). B(x)` are the generic well-founded trees. A node
`sup a f` consists of a label `a : A` and a function `f : B(a) -> W(x:A). B(x)`
giving the subtrees indexed by `B(a)`.

- `A` is the type of node labels
- `B(a)` is the branching arity at a node labelled `a`


#### Lists as W-types

A list over type `T` has two kinds of node:
- `false` (empty / nil) - branching arity `Empty` (no children)
- `true`  (cons) - branching arity `Unit` (one child, since `Unit` has
  one element `star`)

```
W(b : Bool). boolrec (fn _. Type) T Unit
```

Length of such a list:

```
>> let length = fn l. wrec (fn _. Nat)
                            (fn b f ih. boolrec (fn _. Nat) (succ (ih star)) zero b)
                            l
   defined: length
```

Build a two-element list `[succ zero, succ (succ zero)]`:

```
>> length (sup true (fn _. sup true (fn _. sup false (fn _. star))))
   normal : succ (succ zero)
```

The induction hypothesis `ih` in `wrec` is a function from child indices
to recursive results. `ih star` asks for the result on the unique child
(index `star : Unit`).


#### Binary trees as W-types

A binary tree uses `Bool` labels with `Bool`-indexed branching:
- `false` = leaf (no children): `B(false) = Empty`
- `true`  = branch (two children): `B(true) = Bool`

```
>> let depth = fn t. wrec (fn _. Nat)
                           (fn b f ih. boolrec (fn _. Nat)
                             (succ (natrec (fn _.Nat)
                                           (ih true)
                                           (fn _ acc. boolrec (fn _.Nat) acc (succ acc) (natrec (fn _.Nat) false (fn _ _. true) acc))
                                           (ih false)))
                             zero b)
                           t
```

Simpler: just count total nodes.

```
>> let count = fn t. wrec (fn _. Nat)
                           (fn b f ih. boolrec (fn _. Nat)
                             (succ (add (ih true) (ih false)))
                             (succ zero) b)
                           t
   defined: count
```

A three-node tree (root with two leaves):

```
>> count (sup true (fn _. sup false (fn x. abort Nat x)))
   normal : succ (succ (succ zero))
```


#### The WREC step signature

The step function in `wrec P s t` has type:

```
Pi(a : A). Pi(f : B(a) -> W(x:A). B(x)). Pi(ih : B(a) -> P). P
```

- `a` is the current node's label
- `f` is the children function (index → subtree)
- `ih` is the induction hypothesis (index → result on that subtree)
- result is `P` applied to the current node



### Part 5 - Other type formers

#### Sum types A + B

Disjoint union. Constructors `inl a : A+B` and `inr b : A+B`.
Elimination with `case`:

```
case : Pi(P : A+B -> Type). Pi(fl : Pi(a:A). P(inl a)).
       Pi(fr : Pi(b:B). P(inr b)). Pi(s : A+B). P s
```

```
>> case (fn _. Nat) (fn n. n) (fn b. boolrec (fn _. Nat) zero (succ zero) b) (inl (succ zero))
   normal : succ zero

>> case (fn _. Nat) (fn n. n) (fn b. boolrec (fn _. Nat) zero (succ zero) b) (inr true)
   normal : succ zero
```

#### The empty type ⊥

`Empty` has no constructors. `abort A s` has type `A` for any `A` when
`s : Empty`. It is always stuck because there is no inhabitant to match.

```
>> abort Nat loop
   normal : [loop · abort(Nat)]
```

#### The unit type ⊤

`Unit` has one constructor `star`. Recursion with `unitrec`:

```
>> unitrec (fn _. Nat) (succ zero) star
   normal : succ zero
```



### Part 6 - Session workflow

#### Buildng up a library in one session

Definitions accumulate across REPL lines within the same session.
A complete arithmetic session:

```
>> let zero' = zero
>> let one   = succ zero
>> let two   = succ one
>> let three = succ two
>> let add : Nat -> Nat -> Nat = fn m n. natrec (fn _. Nat) n (fn _ acc. succ acc) m
>> let mul : Nat -> Nat -> Nat = fn m n. natrec (fn _. Nat) zero (fn _ acc. add n acc) m
>> mul three two
   normal : succ (succ (succ (succ (succ (succ zero)))))
>> :conv mul two three ; mul three two
   conv   : yes
```

#### Annotated vs unannotated let

```
let f = expr                  -- no type stored; :type f gives type error
let f : T = expr              -- T stored; :type f returns T
```

Use the annotated form when you want `:type` to work:

```
>> let six : Nat = mul two three
   defined: six
>> :type six
   type   : Nat
```

#### Using :conv as an equality oracle

`:conv` reduces both sides to NF and checks structural α-equivalence.
It is definitional equality - stronger than propositional equality.

```
>> :conv add two three ; add three two
   lhs    : succ (succ (succ (succ (succ zero))))
   rhs    : succ (succ (succ (succ (succ zero))))
   conv   : yes
```

This confirms that addition is commutative on these specific values
(and all concrete ones, by computation). A general proof for all `m n`
would require induction and is a *propositional* statement, not
*definitional*.

#### Debugging with :type

`:type e` calls the core bidirectional checker on the *original* term
(before graph reduction). If the term is not type-inferable (bare lambda,
unannotated pair), wrap it:

```
>> :type (fn x. succ x : Nat -> Nat)
   type   : Π(_ : Nat). Nat

>> :type (sym Nat zero zero (refl zero) : Id Nat zero zero)
   type   : Id Nat zero zero
```



### Part 7 - Where this sits

#### What this system is

This is a *research and learning kernel* for Homotopy Type Theory. It
consists of two layers:

*`core/`* - a bidirectional NbE (normalisation-by-evaluation)
type checker for full MLTT + HoTT. Correct, complete, and frozen at 185
passing tests. This is what validates that your terms are well-typed.

*`lang/`* - a call-by-need graph reduction VM sitting above the
core. Terms live on a heap of sharing nodes and reduce lazily. The core
is invoked on demand for type-checking (`:type`) and serialization
(`:conv` on binder types). The `let` command defines persistent globals.

The two layers are independent. You can use `core` alone as a proof
checker; `lang` adds interactive evaluation with lazy sharing.

#### Comparison to other systems

| System         | Type theory                                        | Computation                 | HITs                          | Proof style                |
|----------------|----------------------------------------------------|-----------------------------|-------------------------------|----------------------------|
| *This*         | MLTT + ua + funext + S¹ + ‖·‖                      | Graph reduction (lazy)      | S¹, ‖·‖ as axioms             | Interactive REPL           |
| *Agda*         | MLTT, with records, modules, universe polymorphism | Definitional NbE            | Via `--cubical` or postulates | Dependent pattern matching |
| *Cubical Agda* | Cubical TT (CCHM)                                  | Interval, composition, Glue | Computational (genuine paths) | Cubical paths, `hcomp`     |
| *Coq/Rocq*     | CIC (Calculus of Inductive Constructions)          | Strong normalization        | Via HoTT library + axioms     | Tactic-based proofs        |
| *Lean 4*       | CIC + quotient types                               | Reduction + elaboration     | Via Mathlib + axioms          | Tactic + term mode         |
| *Idris 2*      | Quantitative Type Theory                           | NbE                         | Via postulates                | Dependent types + effects  |
| *miniTT*       | MLTT core                                          | NbE                         | None                          | Reference implementation   |
| *HoTT-Agda*    | MLTT + ua axiom                                    | Definitional                | HITs as postulates            | Agda library               |

*Key distinctions:*

*vs Agda/Lean/Coq:* This is a kernel, not a proof assistant. There is
no termination checker - a non-terminating definition silently diverges
or hits a blackhole. There are no tactics, no modules, no universe
polymorphism, no type classes. The bidirectional checker requires more
manual annotations.

*vs Cubical Agda:* The most important difference. Here `ua` and `funext`
are axioms that block computation - `ua (id-equiv A)` stays as a neutral
term. In Cubical Agda they compute; `ua e` applied to a term in `A`
reduces to applying `e`. This means Cubical Agda has *no proof-relevant*
axioms and transporting across `ua` is computable. Here it is not.

*vs miniTT:* miniTT is a reference implementation of pure MLTT without
HITs. This adds HITs (S¹, ‖·‖), a graph reduction surface layer, and
the core is more complete (W-types, sum, empty, unit, J).

*What this does well:*
- Lazy graph reduction gives genuine call-by-need sharing; a term computed
  once is never recomputed
- Neutral terms print as readable head-spine chains
- The bridge layer lets graph-reduced NF nodes round-trip through the core
  type checker for exact type information
- Small, self-contained C codebase (~2500 lines) - easy to read and extend

#### What is missing

The following features are present in mature proof assistants but absent here:

| Feature                       | Notes                                                     |
|-------------------------------|-----------------------------------------------------------|
| *Termination checking*        | Recursive definitions can diverge                         |
| *Universe polymorphism*       | Only `Type` and `Type_1`                                  |
| *Pattern matching*            | Must use eliminators explicitly                           |
| *Numeric literals*            | `2` is `succ (succ zero)`                                 |
| *Tactics*                     | All proofs are term-mode only                             |
| *Modules / namespaces*        | One flat global namespace                                 |
| *Where-clauses*               | Local definitions inside expressions                      |
| *Infix operators*             | No user-definable syntax                                  |
| *Cubical structure*           | Interval, `hcomp`, `transp`, `Glue`                       |
| *Eta for Pi*                  | Lambda convertibility is conservative (same body pointer) |
| *Normalization of open terms* | Only closed terms fully reduce                            |



### Part 8 - What can be added

The codebase is designed to be extended. Here is a map of natural next steps.

#### Numeric literals

The easiest quality-of-life improvement. In `main.c`'s `preprocess()`
function, detect digit sequences and expand them:
`3` → `succ (succ (succ zero))`. Reverse in the printer.

#### Where-clauses and local let

`let f x = let y = expr in body` - parse `in` as a scope delimiter and
desugar to immediate beta reduction. No new node types needed.

#### Quotient types

`A / R` where `R : A → A → Type` is a propositional equivalence relation.
Constructors: `class a : A/R` and `quot : R a b → Id (A/R) (class a) (class b)`.
Recursor: function out of `A/R` into a set, compatible with `R`.

Quotients + propositional truncation give *set-quotients*, enough to
define rational numbers, integers (as ℤ = ℕ + ℕ / equivalence), etc.

#### More Higher Inductive Types

*The 2-sphere S²:* Base point and a 2-cell (a loop-between-loops).
Adds a new sentinel and a recursion principle that includes a surface case.

*Suspension ΣA:* Two poles `N, S` and a meridian path for each `a : A`.
The circle is `Σ Bool`; S² is `Σ S¹`.

*Pushouts:* Given `A ←f- C -g→ B`, the pushout `A ⊔_C B` has
constructors `inl a`, `inr b`, and a path `glue c : inl (f c) = inr (g c)`.
Pushouts encode many HITs: suspension, joins, coequalisers, mapping cones.

*Truncations at higher levels:* The `-1`-truncation `‖A‖` is already
present. The `0`-truncation (set-truncation) `‖A‖₀` adds a 2-cell
squashing all paths. Requires universe lifting.

#### Cubical structure

The big extension: add an interval type `𝕀` with two endpoints `i0, i1 : 𝕀`.
Paths become functions out of `𝕀`. Univalence becomes a theorem rather
than an axiom (`Glue` types). Transport computes.

This is Cubical Agda's approach and requires substantial new primitives:
`hcomp` (homogeneous composition), `transp`, `Glue`/`unglue`. The node
heap would gain interval-typed children and composition operations.

#### Termination checking

A structural recursion checker would refuse non-terminating definitions.
Simplest approach: check that each recursive call uses a structurally
smaller argument (a subterm of the original scrutinee). This handles
the `natrec`/`boolrec`/`wrec` patterns already in the language.

#### Eta-expansion for Pi

The current `node_conv` treats lambdas conservatively: two lambdas are
equal only if their `Term*` bodies match. Eta-expansion would allow
`fn x. f x ≡ f` by reducing to a single normal form. Needed to prove
`funext` computable from univalence.

#### Integer and string types

Primitives backed by C `int` / `char*` with built-in arithmetic nodes
would give practical performance for concrete computation without encoding
everything through Nat.

#### Module / namespace system

A two-level `let open Module` and `Module.name` dot syntax, with a simple
symbol table per module. Re-using `def_define_nocheck` per module.



### Part 9 - What it can be used for

#### Learning MLTT and HoTT

This is the most natural use. The REPL gives immediate feedback on how
terms reduce, what type they have, and whether two expressions are equal.

Working through the HoTT Book chapter by chapter and checking each
construction in the REPL is instructive in a way that reading alone is not.
The system is small enough that you can read every line of the evaluator
and understand why each reduction fires.

#### Understanding the gap between constructive and classical mathematics

Classical mathematics assumes the law of excluded middle: for any P,
either P or ¬P. In this type theory, that is not provable for arbitrary P.
You can see this concretely: `boolrec (fn _. Type) (Nat -> Empty) Nat loop`
is a stuck term - there is no way to decide whether `loop` is `true` or
`false` in the surface language.

#### Experimenting with proof-relevant mathematics

HoTT takes seriously the idea that proofs are mathematical objects with
their own structure. In this system you can see directly that:

- `refl zero ≢ sym Nat zero zero (refl zero)` - check with `:conv`
  (they both reduce to `refl zero`, so they *are* definitionally equal)
- Functions that are pointwise equal are equal: `funext` asserts this
- Two types with an equivalence between them are identical: `ua` asserts
  this, enabling coercion without manual reformulation

#### Prototyping type theory extensions

The codebase is small (~2500 lines of C). Adding a new type former means:
1. A new `NodeTag` in `node.h`
2. A constructor in `node.c`
3. A reduction rule in `reduce.c`'s `force()`
4. A case in `bridge.c`'s `node_to_term_ctx`
5. A new `Term` tag in `core/term.h` and corresponding cases in
   `core/eval.c`, `core/check.c`, `core/parse.c`

The layered architecture means you can prototype the evaluator rule in
`reduce.c` first, run it through the REPL, and add the core checker case
later.

#### A reference for implementing your own type checker

The core (`core/`) is a clean bidirectional NbE implementation.
The evaluator (`eval.c`) is roughly 400 lines; the checker (`check.c`)
is roughly 900 lines including all MLTT and HoTT rules. Reading them
alongside the HoTT Book is a practical route to understanding how type
theory is implemented.

The graph reduction VM (`lang/`) shows how to build a lazy surface
evaluator that shares computation and handles neutrals, sitting above a
separate type-checking kernel.



### Quick reference card

```
Syntax          Meaning
----------------------------------------------------------------
fn x. e         lambda abstraction
fn x y z. e     multi-arg lambda (desugared to nested)
e1 e2           application (left-associative)
Pi(x:A). B      dependent function type
Sg(x:A). B      dependent pair type
A -> B          non-dependent function type
(a, b)          pair constructor
fst p, snd p    pair projections
Id A a b        identity/path type
refl a          reflexivity / constant path
W(x:A). B       well-founded tree type
sup a f         tree constructor
A + B           disjoint sum (written as Sum A B in eliminators)
inl a, inr b    sum constructors
Type            universe (also Type_1 for the next level)

Commands
----------------------------------------------------------------
expr            reduce to normal form
:type expr      reduce and show inferred type
:conv e1 ; e2   check definitional equality
let x = e       bind global (no type stored)
let x : T = e   bind global with type T
Ctrl-D          quit

Eliminators
----------------------------------------------------------------
natrec P z s n              Nat recursion
boolrec P t f b             Bool case split
case P fl fr s              Sum case split
unitrec P ps u              Unit recursion (u = star fires)
abort A s                   Ex falso (always stuck)
J A a P d b p               Path induction (p = refl fires)
S1rec B b l c               Circle recursion (c = base fires)
truncrec A B f t            Truncation recursion (t = trint a fires)
wrec P s t                  W-type recursion (t = sup fires)

Stdlib (auto-loaded)
----------------------------------------------------------------
sym A a b p                 reverse path: Id A b a
trans A a b c p q           concatenate paths: Id A a c
ap A B f a b p              apply function: Id B (f a) (f b)
transport A P a b p x       coerce along path: P b
```
