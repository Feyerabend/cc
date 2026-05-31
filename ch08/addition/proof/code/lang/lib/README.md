
## `lang/lib/` - Standard Library

Load the whole library with `:load "lib/prelude.lam"` from the `lang/` directory.
Individual files can be loaded independently; imports are deduplicated automatically.



### The big picture

This library has two purposes that look different on the surface but are the same
thing underneath:

1. *Programs* - `plus`, `vconcat`, `toNat` - functions that compute.
2. *Proofs* - `plus_comm`, `plus_zero_r` - mathematical theorems.

They are written in the same language, with the same syntax, and run through the
same evaluator. This is not a coincidence. It is the Curry-Howard correspondence:
*a type is a proposition, and a term of that type is a proof of that proposition.*
The type checker is a proof checker. The graph reducer is a proof evaluator.

A proof is not just a certificate that the statement is true. It is a *program*
that computes evidence. Run `plus_comm 2 3` and the evaluator returns
`refl 5` - a concrete witness that `2+3 = 3+2`.



### `nat.lam` - arithmetic on `Nat`

`Nat` is a built-in inductive type with two constructors:

```
zero : Nat
succ : Nat -> Nat
```

The number 3 is `succ (succ (succ zero))`. This is not an encoding trick; it is
the definition. The evaluator works with these constructor trees directly.

#### `natrec` - the eliminator for Nat

Every function on `Nat` is built from `natrec`, which encodes proof by induction
(equivalently: primitive recursion). Its signature is:

```
natrec (P : Nat -> Type) (z : P zero) (s : Pi(k:Nat). P k -> P (succ k)) (n : Nat)
     : P n
```

Reading this as induction: `P` is what you want to prove, `z` is the base case,
and `s` is the inductive step - given that `P k` holds (the induction hypothesis
`ih`), produce `P (succ k)`. The result is a proof of `P n` for any `n`.

Reading this as programming: `natrec P z s n` recurses on `n`, returning `z` at
`zero` and calling `s k ih` at each `succ k`, where `ih` is the result of the
recursive call on `k`.

#### `plus`

```
plus m n = natrec (\k. Nat) n (\k. \ih. succ ih) m
```

- Motive `\k. Nat`: the result type is always `Nat`, independent of `k`.
- Base case `n`: `plus zero n = n`.
- Step `\k. \ih. succ ih`: `plus (succ k) n = succ (plus k n)`.

The recursion is on the *first* argument `m`. This choice matters: `plus zero n`
reduces to `n` *immediately* (definitionally), but `plus n zero` requires `n`
steps to reduce. This asymmetry will come up again in the proofs.

#### `mult`

```
mult m n = natrec (\k. Nat) zero (\k. \ih. plus n ih) m
```

Base: `mult zero n = zero`. Step: `mult (succ k) n = plus n (mult k n)`.
So `mult 2 3 = plus 3 (plus 3 zero) = 6`. The accumulator `ih` is the
partial product; each step adds one more copy of `n`.

#### `pred` and `iszero`

```
pred n = natrec (\k. Nat) zero (\k. \ih. k) n
```

At `succ k`, the step function receives `k` (the predecessor) and `ih` (the
recursive result on `k`, which is `pred k`). We want `k`, not `ih`, so we
return `k` directly. This is how you access the predecessor: the step's first
argument is always the predecessor.



### `vec.lam` - length-indexed vectors

#### The type declaration

```
data Vec (A : Type) : Nat -> Type where
  vnil  : Vec A zero
  vcons : Pi(n : Nat). A -> Vec A n -> Vec A (succ n)
```

`Vec A n` is a family of types *indexed by* `n`. `Vec Bool 3` and `Vec Bool 5`
are different types - not different values of the same type. The length is baked
into the type, not stored as a runtime field.

`vnil` has type `Vec A zero`: an empty vector has length zero.
`vcons n a v` has type `Vec A (succ n)`: prepending an element to a length-`n`
vector yields a length-`succ n` vector.

A value like `vcons Bool 1 true (vcons Bool 0 false (vnil Bool))` has type
`Vec Bool 2`. You cannot pass it where a `Vec Bool 3` is expected; the type
system rejects it at compile time without any runtime check.

#### `indrec` - the eliminator for inductive families

Functions on `Vec` are written with `indrec Vec`, analogous to how `natrec`
handles `Nat`. The motive `\n. \v. T(n, v)` is a type that can depend on both
the index `n` and the vector `v` itself.

```
indrec Vec (\n. \v. T)
  nil_case              -- value for vnil
  (\n. \a. \v. \ih. ..) -- value for vcons n a v, given ih = result on v
  scrutinee
```

The `ih` in the cons case is the result of the recursive call on the tail `v`.

#### `vlength`

```
vlength A n v = indrec Vec (\n. \v. Nat) zero (\n. \a. \v. \ih. succ ih) v
```

Motive `\n. \v. Nat`: ignoring both the index and the vector, the result is
always a `Nat`. The nil case returns `zero`. The cons case ignores `a` and `v`
and returns `succ ih` - one more than the length of the tail.

This computes the length by structural recursion, re-deriving what the type
already knows. It is not circular: `vlength` *uses* the structure to count;
the type *carries* the count statically.

#### `vmap`

```
vmap A B n f v = indrec Vec (\n. \v. Vec B n) (vnil B) (\n. \a. \v. \ih. vcons B n (f a) ih) v
```

Motive `\n. \v. Vec B n`: given a vector of length `n`, produce a vector of the
same length `n` but over type `B`. The cons case builds `vcons B n (f a) ih`,
where `ih` is the already-mapped tail. The type checker confirms the lengths
match - not as a runtime assertion but as a fact about the types.

#### `vconcat`

```
vconcat A m n u v : Vec A (plus m n)
```

This is the key example. The result type is `Vec A (plus m n)` - a vector whose
length is *computed* by the `plus` function. The type checker must verify that
the cons and nil cases produce values whose index matches `plus m n` for their
respective `m`.

The recursion is on `u : Vec A m`:

- Nil case (`m = zero`): return `v`. The expected type is `Vec A (plus zero n)`.
  `plus zero n` reduces definitionally to `n` (because `plus` recurses on its
  first argument, and `plus zero n = n` is the base case). So `Vec A (plus zero n)
  = Vec A n` definitionally, and `v : Vec A n` typechecks without any cast.

- Cons case (`m = succ k`): build `vcons A (plus k n) a ih`. Here `ih` has type
  `Vec A (plus k n)` (the recursive result on the tail). The expected type is
  `Vec A (plus (succ k) n)`. By the step rule of `plus`, `plus (succ k) n =
  succ (plus k n)` definitionally. So the types align without any proof term.

This is what dependent types buy you: the length arithmetic in the type reduces
alongside the structural recursion on the vector, and the two computations stay
in sync definitionally.



### `fin.lam` - bounded natural numbers

#### The type declaration

```
data Fin : Nat -> Type where
  fzero : Pi(n : Nat). Fin (succ n)
  fsucc : Pi(n : Nat). Fin n -> Fin (succ n)
```

`Fin n` is a type with exactly `n` inhabitants. Think of it as the set
{0, 1, ..., n−1}. The constructors mirror `Nat`'s, but the index tracks
the upper bound:

- `fzero n : Fin (succ n)` - the element 0 in a set of size `succ n`.
- `fsucc n i : Fin (succ n)` - the element `i+1`, given `i : Fin n`.

So `fzero 2 : Fin 3` represents 0 ∈ {0,1,2}, and
`fsucc 2 (fsucc 1 (fzero 0)) : Fin 3` represents 2 ∈ {0,1,2}.

The bound `n` is a proof carried by the type. `Fin 0` is uninhabited - there is
no constructor that produces `Fin 0` - so any function receiving a `Fin 0`
argument can never be called. This is how dependent types enforce array bounds:
pass a `Fin n` index to a `Vec A n` and the types guarantee the access is valid
without any runtime check.

#### `toNat`

```
toNat n i = indrec Fin (\n. \i. Nat) (\n. zero) (\n. \i. \ih. succ ih) i
```

Forgets the bound and returns the underlying number. `fzero n` maps to `zero`;
`fsucc n i` maps to `succ (toNat n i)`. This is the embedding Fin n ↪ Nat.

#### `finWeaken`

```
finWeaken n i : Fin (succ n)
```

Raises the bound by one without changing the value. `fzero n` (element 0 in a
set of size `succ n`) becomes `fzero (succ n)` (element 0 in a set of size
`succ (succ n)`). The value is unchanged; only the type's upper bound grows.
This is the canonical weakening map in the Fin family.



### `proofs.lam` - arithmetic identities

This is where the system shows its character. The functions here are not
programs in the conventional sense - they are *proofs*, and their types are
*propositions*. But they are written and run exactly like any other function.

#### `Id` - the identity type

`Id A a b` is the type of proofs that `a` and `b` are equal (as elements of
`A`). It has one constructor:

```
refl a : Id A a a
```

A term of type `Id A a b` is evidence that `a = b`. The only way to construct
such evidence directly is `refl`, which requires `a` and `b` to be
*definitionally equal* - reducible to the same normal form by the evaluator.

The built-in combinators `sym`, `trans`, `ap`, `transport`, and `J` (the full
eliminator) let you combine and manipulate this evidence.

#### Definitional vs propositional equality

Two key flavors of equality appear in this library:

*Definitional equality* is checked by the evaluator: `plus zero n` and `n`
are definitionally equal because `plus zero n` reduces to `n` in one step.
You can write `refl n : Id Nat (plus zero n) n` and the type checker accepts it
immediately, because both sides normalize to `n`.

*Propositional equality* requires a proof term: `plus n zero` and `n` are
*not* definitionally equal (because `plus` recurses on its first argument, and
`n` is a variable - the evaluator cannot reduce further). You must construct an
element of `Id Nat (plus n zero) n` by induction.

#### `plus_zero_l`

```
plus_zero_l n = refl n : Id Nat (plus zero n) n
```

No induction. `plus zero n` reduces immediately to `n`, so `refl n` suffices.
The type checker confirms both sides are `n`.

#### `plus_zero_r`

```
plus_zero_r n : Id Nat (plus n zero) n
```

Induction on `n`. The motive is `P k = Id Nat (plus k zero) k` - the statement
"plus k zero = k" for each `k`.

- *Base case* (`k = zero`): `plus zero zero = zero` definitionally, so
  `refl zero : Id Nat (plus zero zero) zero`.

- *Inductive step*: assume `ih : Id Nat (plus k zero) k`. We need
  `Id Nat (plus (succ k) zero) (succ k)`. By definition of `plus`,
  `plus (succ k) zero = succ (plus k zero)`. So we need
  `Id Nat (succ (plus k zero)) (succ k)`. Applying `succ` to both sides of `ih`
  gives exactly this - that is `ap Nat Nat (\x. succ x) (plus k zero) k ih`.

When you evaluate `plus_zero_r (succ (succ zero))`, the induction unwinds:
the step fires twice, wrapping `refl zero` in two `ap` calls, and the whole
expression reduces to `refl (succ (succ zero))`. The proof computes.

#### `plus_succ_r`

```
plus_succ_r m n : Id Nat (plus m (succ n)) (succ (plus m n))
```

This lemma is needed for commutativity. Induction on `m`:

- *Base*: `plus zero (succ n) = succ n = succ (plus zero n)` definitionally.
  `refl (succ n)` suffices.
- *Step*: assume `ih : plus k (succ n) = succ (plus k n)`. Apply `succ` to
  both sides.

#### `plus_comm`

```
plus_comm m n : Id Nat (plus m n) (plus n m)
```

Induction on `m`. The motive is `P k = Id Nat (plus k n) (plus n k)`.

- *Base* (`m = zero`): we need `Id Nat n (plus n zero)`. That is
  `sym Nat n (plus n zero) (plus_zero_r n)` - symmetry of `plus_zero_r n`.

- *Step*: assume `ih : plus k n = plus n k`. We need
  `plus (succ k) n = plus n (succ k)`.
  
  The left side: `plus (succ k) n = succ (plus k n)` definitionally.  
  The right side: `plus n (succ k) = succ (plus n k)` by `plus_succ_r n k`.
  
  Chain: `succ (plus k n) = succ (plus n k)` by `ap succ ih`, then
  `succ (plus n k) = plus n (succ k)` by `sym plus_succ_r n k`. Then
  `trans` glues them together.

Running `plus_comm 2 3` evaluates the whole induction, unwinds the `trans` and
`sym` calls, and reduces to `refl 5`. Both `plus 2 3` and `plus 3 2` compute to
`5`, the `Id` type's two sides become definitionally equal, and `refl` is the
result. The proof is a program; programs run; running this one terminates with
evidence.



### `prelude.lam` - entry point

```
import "nat.lam"
import "vec.lam"
import "fin.lam"
import "proofs.lam"
```

Loading `prelude.lam` transitively loads all four files. The import system
deduplicates: `vec.lam` imports `nat.lam`, but loading `prelude.lam` loads
`nat.lam` only once.

#### Quick-start session

```
:load "lib/prelude.lam"

-- Arithmetic
plus (succ (succ zero)) (succ zero)             -- 3
mult (succ (succ zero)) (succ (succ (succ zero))) -- 6
pred (succ (succ (succ zero)))                  -- 2
iszero zero                                     -- true

-- Vectors (length in the type)
vconcat Bool (succ zero) (succ zero)
  (vcons Bool zero true (vnil Bool))
  (vcons Bool zero false (vnil Bool))
-- → vcons (succ zero) true (vcons zero false vnil)
-- result has type Vec Bool (plus 1 1) = Vec Bool 2

-- Finite sets
toNat (succ (succ zero)) (fsucc (succ zero) (fzero zero))  -- 1
finWeaken (succ zero) (fzero zero)                          -- fzero (succ zero)

-- Proofs that compute
plus_zero_l (succ (succ zero))                  -- refl (succ (succ zero))
plus_zero_r (succ (succ zero))                  -- refl (succ (succ zero))
plus_comm (succ (succ zero)) (succ (succ (succ zero)))  -- refl (succ^5 zero)
```

The last line is the headline: commutativity of addition is not just *stated* -
it is *run*, and the evaluator confirms it by reducing both sides to the same
number.
