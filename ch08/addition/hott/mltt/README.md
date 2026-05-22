
## Martin-Löf Type Theory - This Implementation

Martin-Löf Type Theory is a formal system where *types and propositions are
the same thing*, and *terms and proofs are the same thing*. To prove a
statement `P` is to construct a term of type `P`. This is the
Curry-Howard correspondence taken as a foundation.

Three properties distinguish MLTT from simpler type theories:

1. *Types can depend on terms.* `Π(n : Nat). Vec A n` is a type indexed by
   a concrete natural number. This is what makes it *dependent*.

2. *Proof relevance is left open.* The identity type `Id A a b` (a proof
   that `a` equals `b`) is itself a type, and its elements are proofs.
   In pure MLTT, those proofs are indistinguishable - there is at most one
   proof of `a = b` up to definitional equality. HoTT abandons this.

3. *Computation is part of typing.* Two terms that reduce to the same
   normal form are *definitionally equal* and interchangeable without
   explicit proof. This is stronger than propositional equality.



### The Four Judgments

Everything in MLTT is stated relative to a *context* Γ (a list of typed
variables):

| Judgment        | Meaning                                    |
|-----------------|--------------------------------------------|
| `Γ ⊢ A type`    | `A` is a well-formed type                  |
| `Γ ⊢ a : A`     | `a` is a term of type `A`                  |
| `Γ ⊢ A ≡ B`     | `A` and `B` are definitionally equal types |
| `Γ ⊢ a ≡ b : A` | `a` and `b` are definitionally equal terms |

*Definitional equality* (`≡`) is decidable and is the kernel's `conv`
function. It includes β-reduction and η-expansion and is checked by
normalization-by-evaluation (NbE). It is *not* the same as propositional
equality (`Id A a b`), which requires constructing a proof term.



### Type Formers

Each type former has four aspects:

- *Formation* - what universe it lives in
- *Introduction* - how to build values of the type
- *Elimination* - how to use values of the type
- *β-rule* - computation: intro followed by elim reduces
- *η-rule* - uniqueness: any term of this type is definitionally equal to
  its introduction form (not all type formers have η)



#### Π - Dependent Function Types

`Π(x : A). B(x)` - the type of functions that take `x : A` and return
something of type `B(x)`, where the return type can mention the argument.

```
Formation:   A : Type_i,  x:A ⊢ B x : Type_j
            ---------------------------------
              Π(x:A). B x : Type_{max(i,j)}

Introduction:     x:A ⊢ t : B x
              ---------------------
              λx. t : Π(x:A). B x

Elimination:  f : Π(x:A). B x,  a : A
              -------------------------
                    f a : B(a)

β:  (λx. t) a  ≡  t[a/x]
η:  f  ≡  λx. f x
```

`A → B` is notation for `Π(_ : A). B` (non-dependent).

*Kernel*: `TM_PI`, `TM_LAM`, `TM_APP`. η is tested in `conv` by applying
both sides to a fresh neutral variable.



#### Σ - Dependent Pair Types

`Σ(x : A). B(x)` - pairs `(a, b)` where `a : A` and `b : B(a)`. The type
of the second component depends on the value of the first.

```
Formation:   A : Type_i,  x:A ⊢ B x : Type_j
             ---------------------------------
               Σ(x:A). B x : Type_{max(i,j)}

Introduction:     a : A,  b : B(a)
              -------------------------
                (a, b) : Σ(x:A). B x

Elimination:  fst (a, b) ≡ a
              snd (a, b) ≡ b(a)        [b(a) : B(a)]

β:  fst(a, b) ≡ a
    snd(a, b) ≡ b
η:  p ≡ (fst p, snd p)
```

`A × B` is notation for `Σ(_ : A). B` (non-dependent, a plain product).

*Kernel*: `TM_SIG`, `TM_PAIR`, `TM_FST`, `TM_SND`. η in `conv` via
projections on both sides.



#### Id - Identity Type (Propositional Equality)

`Id A a b` - the type whose elements are *proofs* that `a` and `b` are
equal. This is distinct from definitional equality: an element of `Id A a b`
is a term you construct and pass around, not a judgment the kernel checks.

```
Formation:    A : Type_i,  a b : A
             -----------------------
               Id A a b : Type_i

Introduction:        a : A
              ----------------------
                refl a : Id A a a

Elimination (J):
  A : Type_i,  a : A,
  P : Π(b:A). Id A a b → Type_k,
  d : P a (refl a),  b : A,  p : Id A a b
  ------------------------------------------
  J A a P d b p : P b p

β:  J A a P d a (refl a)  ≡  d
```

*J is path induction*: to prove `P b p` for all `b` and all paths
`p : a = b`, it suffices to prove `P a (refl a)`. The proof of `P` is then
transported along `p`.

There is *no η-rule* for Id in MLTT. Two distinct elements `p q : Id A a b`
need not be definitionally equal. This is the point where HoTT diverges.

*Kernel*: `TM_ID`, `TM_REFL`, `TM_J`. β fires when proof is `VL_REFL`.

Derived from J (defined as globals in the test suite):
- `sym : Id A a b → Id A b a`
- `trans : Id A a b → Id A b c → Id A a c`
- `transport : Id A a b → P a → P b`
- `ap : (A → B) → Id A a b → Id B (f a) (f b)`



#### Nat - Natural Numbers

```
Formation:   Nat : Type_0

Introduction: zero : Nat
              n : Nat ⊢ succ n : Nat

Elimination (natrec):
    P : Nat → Type_i,  z : P zero,  s : Π(m:Nat). P m → P(succ m),  n : Nat
  --------------------------------------------------------------------------
    natrec P z s n : P n

β:  natrec P z s zero      ≡  z
    natrec P z s (succ m)  ≡  s m (natrec P z s m)
```

*Kernel*: `TM_NAT`, `TM_ZERO`, `TM_SUCC`, `TM_NATREC`.



#### Bool - Booleans

```
Formation:   Bool : Type_0

Introduction: true false : Bool

Elimination (boolrec):
   P : Bool → Type_i,  pt : P true,  pf : P false,  b : Bool
  -----------------------------------------------------------
   boolrec P pt pf b : P b

β:  boolrec P pt pf true   ≡  pt
    boolrec P pt pf false  ≡  pf
```

*Kernel*: `TM_BOOL`, `TM_TRUE`, `TM_FALSE`, `TM_BOOLREC`.



#### Empty - The Empty Type (⊥, Falsehood)

The type with no inhabitants. Eliminating an element of Empty proves
anything - *ex falso quodlibet*.

```
Formation:   Empty : Type_0

Introduction: (none)

Elimination (abort):
   A : Type_i,  e : Empty
  ------------------------
      abort A e : A
```

Negation is defined as: `¬A  ≡  A → Empty`

There is no β-rule because Empty has no constructors. `abort A e` is always
stuck when `e` is a neutral variable (a free variable of type Empty).

*Kernel*: `TM_EMPTY`, `TM_ABORT`. `nbe_vabort` is always stuck.



#### Unit - The Unit Type (⊤, Truth)

The type with exactly one inhabitant.

```
Formation:   Unit : Type_0

Introduction: star : Unit

Elimination (unitrec):
    P : Unit → Type_i,  ps : P star,  s : Unit
  ---------------------------------------------
             unitrec P ps s : P s

β:  unitrec P ps star  ≡  ps
```

Unit η (any `t : Unit` is definitionally equal to `star`) is *not*
implemented here - it requires type-directed conversion and is left for
a later phase.

*Kernel*: `TM_UNIT`, `TM_STAR`, `TM_UNITREC`.



#### Sum - Disjoint Union (A + B, Constructive Disjunction)

```
Formation:        A : Type_i,  B : Type_j
             ---------------------------------
                 Sum A B : Type_{max(i,j)}

Introduction:     a : A                     b : B
              -----------------         -----------------
              inl a : Sum A B           inr b : Sum A B

Elimination (case):
  P : Sum A B → Type_k,
  fl : Π(a:A). P(inl a),  fr : Π(b:B). P(inr b),  s : Sum A B
 -------------------------------------------------------------
  case P fl fr s : P s

β:  case P fl fr (inl a)  ≡  fl a
    case P fl fr (inr b)  ≡  fr b
```

`inl` and `inr` must be checked against a known Sum type - they cannot be
inferred without annotation: `(inl a : Sum A B)`.

Used for: constructive `∨`, decidability `Sum (a = b) (¬(a = b))`,
disjoint options.

*Kernel*: `TM_SUM`, `TM_INL`, `TM_INR`, `TM_CASESPLIT`. `inl`/`inr` are
check-mode only.



#### W - Well-Founded Trees

`W(x : A). B(x)` is the general inductive type: a tree where each node has
label `a : A` and children indexed by `B(a)`.

```
Formation:    A : Type_i,  x:A ⊢ B x : Type_j
             ---------------------------------
               W(x:A). B x : Type_{max(i,j)}

Introduction:     a : A,  f : B(a) → W(x:A). B x
              --------------------------------------
                     sup a f : W(x:A). B x

Elimination (wrec):
  P : W → Type_k,
  s : Π(a:A). Π(f: B(a)→W). Π(ih: Π(b:B(a)). P(f b)). P(sup a f),
  w : W(x:A). B x
  -----------------------------------------------------------------
  wrec P s w : P w

β:  wrec P s (sup a f)  ≡  s a f (λb. wrec P s (f b))
```

The IH (`ih`) is a function giving the recursive result for each child.
W-types can encode Nat, List, and other inductive types.

*Kernel*: `TM_W`, `TM_SUP`, `TM_WREC`. The IH closure is built synthetically
in `nbe_vwrec` (see `eval.c`).



#### Type - Universe Hierarchy

Types live in universes. This kernel uses a *cumulative Russell-style
hierarchy*:

```
Type_0 : Type_1 : Type_2 : ...
```

- `Type` is shorthand for `Type_0`
- `Nat, Bool, Empty, Unit : Type_0`
- `Sum A B : Type_{max(i,j)}` when `A : Type_i`, `B : Type_j`
- `Π(x : Type). x : Type_1` (the domain is `Type_0` but that lives in `Type_1`)

*Kernel*: `TM_UNI` with integer level; `imax(i, j)` for universe arithmetic;
printed as `Type` (level 0), `Type_1`, `Type_2`, …



### NbE - Normalization by Evaluation

This kernel decides definitional equality by normalization. The pipeline:

```
Term --eval--> Val --quote--> Term (normal form)
```

*`eval`* maps syntactic terms to semantic values. β-reduction fires here
eagerly: `(λx. t)` applied to `v` immediately yields `t[v/x]`.

*`quote`* maps values back to terms in β-normal, η-long form.

*`conv`* compares two values structurally, applying η-expansion on the fly:
- For functions: apply both to a fresh neutral, compare bodies
- For pairs: compare projections
- For neutrals: compare head levels and spine frames

*Neutral values* are the key to handling open terms. A *neutral* is a free
variable (represented by its de Bruijn level) with a stack of eliminators
applied to it. For example, if `n` is a variable of type `Nat`:

```
natrec P z s n     →  VL_NEUTRAL { lvl=n, spine=[SP_NATREC(P,z,s)] }
```

This stays stuck until `n` is substituted. Two stuck neutrals are
definitionally equal only if they have the same head and the same spine.

*Bidirectional type checking:*
- `infer` synthesizes a type from a term (works for most eliminators and
  annotated terms)
- `check` verifies a term has a given type (handles lambdas, pairs, `inl`,
  `inr`, `sup` - forms that need a known type to typecheck)



### Global Definitions

The `:let` REPL command (and `def_define` in tests) stores a name with its
type and normal value. References are `TM_GLOBAL` nodes resolved at eval
time. All derived combinators (`sym`, `trans`, `transport`, `ap`) are
globals defined in `main.c`'s test setup.



### The MLTT / HoTT Boundary

Everything above is *standard MLTT*. It is:

- *Consistent* - no term of type `Empty` is derivable
- *Proof-irrelevant for identity* - in a set-theoretic model, `Id A a b`
  has at most one element; UIP holds
- *Decidable definitional equality* - NbE always terminates

The following are the seeds of HoTT, *already present as stuck axioms*:

| Name     | Sentinel level            | What it does                           |
|----------|---------------------------|----------------------------------------|
| `ua`     | `UA_CONST_LVL = -999`     | Univalence: equivalent types are equal |
| `funext` | `FUNEXT_CONST_LVL = -998` | Functions equal pointwise are equal    |

These are consistent with MLTT (they have set-theoretic models), but
they change the nature of the identity type. With `ua`, the path space
`Id Type_1 A B` is inhabited whenever `A ≃ B`, meaning *types themselves
have non-trivial identity proofs*.
