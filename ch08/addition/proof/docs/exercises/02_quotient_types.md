
## Exercise: Quotient Types

*Difficulty:* Large (≈ 300 lines + careful design decisions)

*Prerequisite:* Read all orientation docs, and study how `TM_ID`/`TM_J` work
in `check.c` and `eval.c`.  Read §6.10 of the HoTT textbook (Homotopy Type
Theory, available at homotopytypetheory.org) or Awodey & Warren on quotient
types for the mathematical background.



### What you are building

A *quotient type* `A / R` identifies elements of `A` that are related by `R`.
For example, integers modulo 2 are `Int / (λ m n. even (m - n))`.

In homotopy type theory, quotients are a *higher inductive type*: you add not
just constructors for elements, but also path constructors that make related
elements definitionally equal.



### Mathematical specification

```
Formation:    A : Type    R : A → A → Type
              ─────────────────────────────
              A / R : Type

Introduction: a : A
              ──────
              [a] : A / R            (the equivalence class of a)

Path constructor:
              a b : A    p : R a b
              ──────────────────────
              quot_path a b p : Id (A/R) [a] [b]

Elimination:  (dependent eliminator)
              B : A/R → Type
              f : Π(a:A). B [a]
              coh : Π(a b:A). Π(p:R a b).
                    Id (B [a])                          ← transport
                       (transport (quot_path a b p) (f a))
                       (f b)
              q : A/R
              ────────────────
              quotrec B f coh q : B q

β-rule:       quotrec B f coh [a] ≡ f a
```



### Design decisions to resolve before coding

1. *Path constructor as an axiom or as a term tag?*  
   The simplest approach: add `TM_QUOTPATH` as a neutral axiom (like `ua`),
   with a fixed type stored in a static arena.  The harder approach: add it as
   a proper term with definitional computation (requires cubical structure).

2. *Transport.*  
   The coherence condition requires `transport` along the path. In this system
   `ua` is an axiom and transport stays neutral. If `quot_path` is also an
   axiom, the coherence condition cannot be *checked* computationally — you can
   only postulate it (the user provides the proof). This is the safe choice for
   a first implementation.

3. *The scrutinee in quotrec.*  
   Unlike `natrec` (which sees a VL_ZERO or VL_SUCC), `quotrec` sees either
   `VL_QUOT_CLASS(a)` or a neutral. It cannot see a "raw" `a : A` because `[a]`
   and `a` are different types.



### Files to change

| File           | What to add                                                      |
|----------------|------------------------------------------------------------------|
| `core/term.h`  | `TM_QUOT`, `TM_QUOT_CLASS`, `TM_QUOTREC`, `TM_QUOTPATH` tags     |
| `core/term.c`  | constructors                                                     |
| `core/parse.c` | `A / R` as infix operator; `[a]` for class; `quotrec`            |
| `core/eval.c`  | `nbe_vquotrec` + cases in `nbe_eval` and `nbe_quote`             |
| `core/check.c` | `TM_QUOT`, `TM_QUOT_CLASS`, `TM_QUOTREC`, `TM_QUOTPATH` in infer |



### Hints

*Parsing `A / R`* as an infix operator is the trickiest part because `/` is
also division in some notations.  One approach: require `(A / R)` with
parentheses, parsed in `parse_atom`.

*The β-rule* in `nbe_vquotrec` follows the same pattern as `nbe_vnatrec`:
```c
if (q->tag == VL_QUOT_CLASS) return nbe_vapp(a, f, q->inj);
if (q->tag == VL_NEUTRAL)    /* accumulate on spine */;
```

*The coherence proof* in `quotrec` must be well-typed. Checking it requires
computing the transport type, which in turn requires evaluating `quot_path`.
Since `quot_path` is neutral (axiomatic), `transport` will be neutral too.
You may need to accept the coherence proof on faith (check that it has the right
*type* but not that it actually computes correctly).



### Connection to the broader system

Quotient types extend this system from a *proof checker* into a tool for
reasoning about programs that have *observational equivalences* - situations
where two distinct representations should be treated as the same thing.

They unlock several important patterns:

*Abstract data types with enforced invariants.* A type `T / ∼` exposes only
the structure that respects `∼`. For example, a priority queue can be defined
as a list quotiented by permutation: two lists are the same queue if one is a
permutation of the other. Any function on the queue type must be shown to
respect this equivalence before it can be defined.

*Setoids.* A setoid is a type paired with a chosen equivalence relation that
is not necessarily propositional equality. Quotient types provide the
dependent-type account of setoids: instead of carrying the relation as extra
data, you build it into the type itself via `A / R`.

*The integers.* The standard exercise: define integers as `(Nat × Nat) / ∼`
where `(a, b) ∼ (c, d) ↔ a + d = b + c` (the pair represents the difference
`a - b`). Show that `succ`, `plus`, and `neg` are well-defined on the quotient
by providing the coherence proofs required by `quotrec`. This brings in all the
arithmetic identities already in `proofs.lam` as proof obligations.

*The connection to identity types.* In the presence of the univalence axiom
(already present as `ua` in this system), quotient types have an alternative
account via higher inductive types: `A / R` is constructed by freely adding
paths between elements that `R` relates. The `quot_path` constructor in this
exercise corresponds to exactly those added paths.
