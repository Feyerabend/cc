
## core

A minimal Homotopy Type Theory kernel in C.

The kernel answers one question: given a term and a type, does the term
have that type? It does not search for proofs, suggest completions, or
infer missing arguments. It checks.



### What is implemented

#### Identity types and path structure

Identity types `Id A a b` with reflexivity and the J eliminator. J is
the sole primitive for path reasoning — `sym`, `trans`, `transport`, and
`ap` are derived from it in the global definition table, not built in.

#### Univalence and function extensionality

Both are present as axiom constants that stay neutral: they reduce to
nothing, but they typecheck, and terms that apply them typecheck against
the correct types. Univalence gives `Id Type_1 A B` from an equivalence;
funext gives `Id (Π(x:A). B x) f g` from a pointwise homotopy.

#### Propositional truncation ‖A‖

The type former `trunc A`, constructor `trint A a`, and path constructor
`squash` are implemented via sentinel neutrals. The eliminator `truncrec`
has a β-rule that fires when the scrutinee is `trint A a`. The squash
constructor stays permanently stuck, as required. The eliminator does
not check that the target type is a proposition — that obligation rests
with the user.

#### The circle S¹

`S1` and `base` are canonical values. `loop : Id S1 base base` is a
sentinel neutral — it is not definitionally equal to `refl base`, which
is the key HoTT fact about the circle. The recursor `S1rec B b l s`
fires when `s = base`, returning `b`. On any other neutral scrutinee it
stays stuck.

What is absent: the path coherence axiom `ap (S1rec B b l) loop ≡ l`.
See below.

#### Standard MLTT type formers

Π, Σ, Nat, Bool, Empty (⊥), Unit (⊤), Sum (A+B), W-types, universe
hierarchy. These are present primarily as scaffolding and for testing
path algebra. The HoTT interest lies in the items above.



### Architecture

**Normalization by Evaluation (NbE).** Terms are evaluated into semantic
values (`eval`), then reified back into normal-form terms (`quote`).
Conversion checking works on values, not on syntax.

**Bidirectional type checking.** `infer` synthesizes a type for a term;
`check` verifies a term against a given type. Lambdas, pairs, `inl`,
`inr`, and `sup` require a known type and go through `check`. Everything
else goes through `infer`.

**Spine-based neutrals.** A stuck term is represented as a head (a de
Bruijn level or a sentinel constant) plus a spine of pending eliminators.
Axiom constants like `ua`, `funext`, `loop` are sentinels: fixed negative
integers that cannot collide with any real de Bruijn level.

**Arena allocation.** All values live in a single bump-pointer arena.
There is no incremental garbage collection; the arena is freed in bulk.



### Deliberate omissions

**S¹-path coherence.** The axiom `ap (S1rec B b l) loop ≡ l` is absent.
Its type contains `ap (S1rec B b l) loop`, and since `ap` is currently a
derived global rather than a built-in, that type cannot be parsed at
startup. Adding S¹-path cleanly requires promoting `ap` to a built-in
sentinel with its own β-rule (`ap f (refl a) → refl (f a)`). The omission
means you can define functions out of S¹ and evaluate them at `base`, but
you cannot state or prove anything about their behaviour on `loop`.

**Unit eta.** Definitional equality `t ≡ star` for any `t : Unit` is not
checked. Implementing it requires type-directed conversion (`conv_at_type`),
which the current type-blind `conv` does not support.

**`truncrec` propositional check.** The eliminator for ‖A‖ should require
that its target type `B` is a proposition (`Π(x y : B). Id B x y`). This
check is omitted; the kernel trusts the user to supply a propositional
target. Without it, `truncrec` can be misused to "extract" from a
truncation into a non-propositional type, which is unsound.

**Universe cumulativity.** `Type : Type_1` holds, but there is no
subtyping: a term of type `Type` cannot be passed where `Type_1` is
expected without an explicit annotation. Each universe level is a
distinct type.

**No surface syntax.** There are no let-bindings, no multi-argument
lambda shorthand, no implicit arguments, and no infix operators. Every
term must be written in fully annotated, fully explicit form. This is
addressed in `lambda/lang/`.



### Building and testing

```
make             # builds ./lcore
./lcore --test   # runs the 185-test suite (0 failures expected)
./lcore <expr>   # infers the type of a single expression
./lcore          # interactive REPL
```
