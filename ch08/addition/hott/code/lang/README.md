
## llang - Graph Reduction VM for HoTT


### Building

```sh
make          # produces ./llang  (no readline)
make llang-rl # produces ./llang-rl  (readline via macOS libedit)
```

Run the REPL:

```
$ ./llang
llang  (graph reduction, Phase 4: β + ι + neutrals + :type + :conv + let)
  ...
>>
```

The `--dump-graph` flag prints the raw node array to stderr after each
reduction, useful for debugging:

```
$ ./llang --dump-graph
```



### REPL reference

#### Evaluate an expression

Type any expression. It is reduced to full normal form and printed.

```
>> natrec (fn _. Nat) zero (fn _ acc. succ acc) (succ (succ zero))
  normal : succ (succ zero)

>> fst (succ zero, true)
  normal : succ zero

>> S1rec Nat zero (refl zero) loop
  normal : [loop · S1rec(Nat, zero, refl zero)]
```

#### `:type expr` - reduce and show type

Reduces the expression and infers its type via the core bidirectional
checker. Bare lambdas and unannotated eliminators may fail; wrap them in
an explicit annotation `(e : T)`.

```
>> :type zero
  normal : zero
  type   : Nat

>> :type refl zero
  normal : refl zero
  type   : Id Nat zero zero

>> :type (fn x. x : Nat -> Nat)
  normal : <fn>
  type   : Π(_ : Nat). Nat
```

#### `:conv e1 ; e2` - check convertibility

Reduces both sides to NF and checks structural α-equivalence. Globals
unfold transparently.

```
>> :conv fst (zero, true) ; zero
  lhs    : zero
  rhs    : zero
  conv   : yes

>> :conv (fn A. A -> A) Nat ; Nat -> Nat
  lhs    : Π(_ : Nat). Nat
  rhs    : Π(_ : Nat). Nat
  conv   : yes

>> :conv Id Nat zero zero ; Id Nat zero (succ zero)
  lhs    : Id Nat zero zero
  rhs    : Id Nat zero (succ zero)
  conv   : no
```

#### `let name [: type] = expr` - define a global

Binds a name in the global definition table. The definition persists for
all subsequent REPL lines in the same session.

```
>> let add : Nat -> Nat -> Nat = fn m n. natrec (fn _. Nat) n (fn _ acc. succ acc) m
   defined: add
>> add (succ (succ zero)) (succ zero)
   normal : succ (succ (succ zero))

>> let two = succ (succ zero)
   defined: two
>> add two two
   normal : succ (succ (succ (succ zero)))
```

The optional `: type` annotation stores the type value; `:type name` then
returns it. Without an annotation the stored type is unknown and `:type`
will report a type error.

Bare lambdas in motive/step positions (e.g. `natrec (fn _. Nat) ...`) are
accepted because `let` evaluates without running the bidirectional type
checker. Use `:type` separately if you want to verify the type.

Shadowing is allowed: a second `let x = ...` makes the new definition
take precedence for all subsequent uses.



### Surface syntax

All ASCII aliases are preprocessed before the core parser sees the input.

| Written     | Meaning                          |
|-------------|----------------------------------|
| `fn x. e`   | lambda - `λx. e`                 |
| `\x. e`     | lambda (direct)                  |
| `fn x y. e` | multi-arg lambda (desugared)     |
| `Pi(x:A). B`| dependent Pi type - `Π(x:A). B`  |
| `Sg(x:A). B`| dependent Sigma type - `Σ(x:A).B`|
| `A -> B`    | non-dependent Pi - `Π(_:A). B`   |

#### Types and constructors

| Token           | Type/value                                     |
|-----------------|------------------------------------------------|
| `Nat`           | natural number type                            |
| `zero`          | `0 : Nat`                                      |
| `succ n`        | `n + 1 : Nat`                                  |
| `Bool`          | boolean type                                   |
| `true`, `false` | `Bool` constructors                            |
| `Unit`          | unit type                                      |
| `star`          | `star : Unit`                                  |
| `Empty`         | empty type                                     |
| `(a, b)`        | Sigma pair                                     |
| `A + B`         | sum type (written as `Sum A B` in eliminators) |
| `inl a`, `inr b`| sum constructors                               |
| `Id A a b`      | identity/path type                             |
| `refl a`        | reflexivity                                    |
| `S1`            | circle type                                    |
| `base`          | base point of S¹                               |
| `loop`          | path `base = base` in S¹ (stuck sentinel)      |
| `trunc A`       | propositional truncation `‖A‖`                 |
| `trint a`       | truncation constructor                         |
| `W(x:A). B`     | well-founded tree type                         |
| `sup a f`       | W-tree constructor                             |
| `Type`          | universe (level 0)                             |
| `Type_N`        | universe level N                               |

#### Eliminators

| Eliminator                          | Computes               |
|-------------------------------------|------------------------|
| `fst p`, `snd p`                    | Sigma projections      |
| `natrec P z s n`                    | Nat recursion          |
| `boolrec P t f b`                   | Bool case split        |
| `case P fl fr s`                    | Sum case split         |
| `unitrec P ps u`                    | Unit recursion         |
| `abort A s`                         | Ex falso (Empty elim)  |
| `J A a P d b p`                     | Path induction         |
| `S1rec B b l c`                     | Circle recursion       |
| `truncrec A B f t`                  | Truncation recursion   |
| `wrec P s t`                        | W-type recursion       |

#### Stdlib globals (loaded at startup)

`sym`, `trans`, `transport`, `ap` - derived from J; available in every
session without a `let` binding.



### Architecture

#### The node heap

All terms live in a flat `Node` array. References are 32-bit indices:

```c
typedef uint32_t NodeRef;
#define NULL_REF 0xFFFFFFFFu
```

Each node:

```c
typedef struct {
    uint8_t  tag;       /* NodeTag                            */
    uint8_t  flags;     /* NF_WHNF | NF_NF | NF_BLACKHOLE     */
    uint16_t _pad;
    NodeRef  ch[6];     /* up to six child references         */
    char    *name;      /* binder name: LAM, PI, SIGMA, W     */
    union {
        int   lvl;      /* VAR: open level; GLOBAL: def index */
        int   ulvl;     /* UNI: universe level                */
        void *aux;      /* LAM/THUNK: Term* body; CORE: Val*  */
    };
} Node;
```

The heap grows by doubling. After realloc, all `h->nodes` pointers are
invalidated; only `NodeRef` integer indices remain stable across
allocations. Code that calls multiple `mk_*` constructors always captures
needed `NodeRef`s before allocating new nodes.

#### Node taxonomy

*Structural nodes:*

| Tag            | Children / data                                |
|----------------|------------------------------------------------|
| `ND_APP`       | ch[0]=fun, ch[1]=arg                           |
| `ND_LAM`       | ch[0]=env chain; name=binder; aux=Term* body   |
| `ND_ENV`       | ch[0]=value, ch[1]=next - environment link     |
| `ND_VAR`       | lvl=open level (sentinel or unbound)           |
| `ND_REF`       | ch[0]=target - indirection node for sharing    |
| `ND_THUNK`     | ch[0]=env; aux=Term* - unevaluated expression  |
| `ND_BLACKHOLE` | cycle guard; fatal if forced a second time     |

*Type-former nodes:*

| Tag       | Children                                        |
|-----------|-------------------------------------------------|
| `ND_PI`   | ch[0]=dom, ch[1]=cod thunk; name=binder         |
| `ND_SIGMA`| ch[0]=dom, ch[1]=cod thunk; name=binder         |
| `ND_W`    | ch[0]=dom, ch[1]=cod thunk; name=binder         |
| `ND_ID`   | ch[0]=type, ch[1]=lhs, ch[2]=rhs                | 
| `ND_SUM`  | ch[0]=left type, ch[1]=right type               |
| `ND_UNI`  | ulvl=universe level                             |

The PI/SIGMA/W cod is always stored as an `ND_THUNK` holding the
unevaluated `Term*` body plus the environment at the point of creation.
It is never forced during ordinary `nf()` - doing so would require the
binder variable to be in scope. The bridge forces it separately using a
fresh sentinel when serialization is needed.

*Canonical constructors:* `ND_ZERO`, `ND_SUCC`, `ND_NAT`, `ND_TRUE`,
`ND_FALSE`, `ND_BOOL`, `ND_STAR`, `ND_UNIT`, `ND_EMPTY`, `ND_PAIR`,
`ND_REFL`, `ND_INL`, `ND_INR`, `ND_SUP`, `ND_S1`, `ND_BASE`, `ND_TRUNC`,
`ND_TRINT`.

*Sentinel:* `ND_LOOP` - the circle path; permanently stuck (no
constructor to match against). `ND_VAR` with an unbound level is also
treated as a sentinel during reduction.

*Eliminators:* `ND_FST`, `ND_SND`, `ND_NATREC`, `ND_BOOLREC`,
`ND_S1REC`, `ND_TRUNCREC`, `ND_CASESPLIT`, `ND_ABORT`, `ND_UNITREC`,
`ND_J`, `ND_WREC`.

*Other:* `ND_GLOBAL` (lvl=def index; negative = axiom constant),
`ND_CORE` (aux=`Val*` from the core NbE evaluator).



#### Reduction (`reduce.c`)

The main entry point is `nf(h, a, root)` which drives:

1. `force()` - bring to WHNF  
2. Recurse into children

`force()` implements four laws:

*θ - thunk instantiation*

```
THUNK(expr, env) → translate expr with env, then force
```

`term_to_node` translates a `Term*` into heap nodes, substituting de
Bruijn variable references by walking the `ND_ENV` chain.

*β - lambda application*

```
APP(LAM(env, body), arg) → translate body with (arg : env), then force
```

The result overwrites the `ND_APP` node as `ND_REF` to the outcome,
giving call-by-need sharing. All live values that hold a reference to the
original `ND_APP` node automatically see the result.

*δ - global unfolding*

```
APP(GLOBAL(idx), arg) → quote(def[idx].val) as Term*, re-apply to arg
```

A global in function position unfolds to its definition via
`nbe_quote` + `term_to_node`. A global in non-function position stays as
`ND_GLOBAL` until applied. Axiom constants (`ua`, `funext`, `squash`)
have negative indices and never unfold.

*ι - eliminator rules*

Each rule forces the scrutinee to WHNF, checks its constructor tag, and
fires if it matches:

| Rule                            | Scrutinee         | Result                           |
|---------------------------------|-------------------|----------------------------------|
| `FST(PAIR(a,b))`                | `ND_PAIR`         | `a`                              |
| `SND(PAIR(a,b))`                | `ND_PAIR`         | `b`                              |
| `NATREC(P,z,s, ZERO)`           | `ND_ZERO`         | `z`                              |
| `NATREC(P,z,s, SUCC(n))`        | `ND_SUCC`         | `APP(APP(s,n), NATREC(P,z,s,n))` |
| `BOOLREC(P,t,f, TRUE)`          | `ND_TRUE`         | `t`                              |
| `BOOLREC(P,t,f, FALSE)`         | `ND_FALSE`        | `f`                              |
| `CASE(P,fl,fr, INL(a))`         | `ND_INL`          | `APP(fl,a)`                      |
| `CASE(P,fl,fr, INR(b))`         | `ND_INR`          | `APP(fr,b)`                      |
| `UNITREC(P,ps, STAR)`           | `ND_STAR`         | `ps`                             |
| `J(A,a,P,d,_,REFL(_))`          | `ND_REFL`         | `d`                              |
| `S1REC(B,b,l, BASE)`            | `ND_BASE`         | `b`                              |
| `TRUNCREC(A,B,f, APP(TRINT,a))` | `ND_APP(TRINT,_)` | `APP(f,a)`                       |
| `WREC(P,s, SUP(a,f))`           | `ND_SUP`          | `APP(APP(APP(s,a),f), IH)`       |

`ABORT` is always stuck - `Empty` has no constructors.

*WREC induction hypothesis:*
The IH lambda `λx. WREC(P, s, APP(f, x))` is built by capturing P, s, f
as `NodeRef`s in an env chain `[P, s, f]`. The body is the pre-allocated
`Term*` `wrec(var(1), var(2), app(var(3), var(0)))`. When applied to `x`,
the env becomes `[x, P, s, f]` and de Bruijn indices resolve correctly.
No serialization is required.

*Stuck (neutral) nodes:*
When a scrutinee forces to `ND_LOOP` or an open `ND_VAR`, the eliminator
cannot fire. The eliminator node is marked `NF_WHNF` in-place without
becoming an `ND_REF` (a self-referential indirection would be meaningless).



#### Neutral printing (`node.c`)

A neutral term has a sentinel at its head with a chain of stuck
eliminators wrapping it. The printer walks inward to the sentinel, then
unwinds printing each frame with a `·` separator:

```
[loop · S1rec(Nat, zero, refl zero)]
[loop · wrec(<fn>, <fn>)]
```

PI/SIGMA/W nodes with unforced cod thunks are routed through the bridge
(`node_to_term` → `term_fprint`) so that the codomain prints correctly:

```
Π(_ : Nat). Nat
```



#### Convertibility (`node.c - node_conv`)

`node_conv(h, a, r1, r2)` checks structural α-equivalence of two NF nodes:

- *Sentinels*: `ND_LOOP` always equal; `ND_VAR` by level.
- *Atomics*: trivially equal if same tag.
- *Compounds*: recurse on children pairwise.
- *PI/SIGMA/W cod*: `conv_cod` forces both thunks with the *same*
  fresh `ND_VAR(BINDER_LVL)` sentinel. Using one sentinel for both sides
  means binder-variable occurrences in each cod resolve to the identical
  heap node, and the `r1 == r2` shortcut catches them as equal.
- *Lambdas*: conservative - `Term*` body pointer must match; no
  eta-expansion.
- *Bare thunks* (outside a cod position): compared by structural
  `term_eq` of their `Term*` bodies plus env-chain conv.
- *ND_CORE*: pointer equality of the wrapped `Val*`.



#### Bridge to core (`bridge.c`)

The bridge is the only file in `lang/` that includes core headers directly.
It provides two public functions:

```c
Term   *node_to_term(Heap *h, NodeRef r, Arena *a);
NodeRef val_to_node (Heap *h, Val *v);
```

`val_to_node` wraps a core `Val*` in an `ND_CORE` node marked WHNF+NF,
for embedding type-checker results back into the heap.

`node_to_term` serializes an NF heap node back to a core `Term*`:

- Most node tags translate directly (constructors, types, eliminators).
- `ND_LAM` with a captured env returns `NULL` - lambdas with closed-over
  environments cannot be serialized back to de Bruijn terms.
- *PI/SIGMA/W cod* is handled by `force_cod`: a copy of the thunk is
  made with a fresh `ND_VAR(BINDER_LVL)` sentinel prepended to its env.
  After forcing, a `SentCtx` stack maps each sentinel's `NodeRef` to its
  de Bruijn index (0 = innermost). When the resulting tree contains an
  `ND_VAR(BINDER_LVL)`, `sent_lookup` converts it back to `TM_VAR(idx)`.

This mechanism handles nested binders correctly: each nested `force_cod`
call pushes a new entry onto the `SentCtx` stack with a distinct
`NodeRef`, so inner and outer binders are never confused.



#### Global definitions (`core/defs.c`)

Two registration functions:

*`def_define(name, src)`* - parses `src`, runs bidirectional type
inference (`infer`), evaluates, and registers. Used for stdlib functions
(`sym`, `trans`, `transport`, `ap`). Requires all lambda motives to be
annotated.

*`def_define_nocheck(name, type_src, expr_src)`* - parses and evaluates
without type-checking. Used by `let` bindings. Accepts bare lambdas in
motive/step positions that `infer` cannot handle. If `type_src` is
non-NULL, the type is stored as an evaluated `Val*` (returned by `:type`
lookups); otherwise the stored type is `NULL`.

All definitions live in a permanent arena that survives `arena_free_all()`
calls between REPL iterations.



### File layout

```
lang/
  node.h      NodeRef, Node struct, NodeTag enum, heap API, constructors
  node.c      heap allocation, environment lookup, constructors,
              neutral printer, node_conv, conv_cod
  reduce.h    term_to_node, nf declarations
  reduce.c    term_to_node, force (β/δ/θ/ι), nf
  bridge.h    node_to_term, val_to_node declarations
  bridge.c    SentCtx, force_cod, node_to_term_ctx, val_to_node
  main.c      REPL: preprocessing, let/type/conv dispatch, stdlib load
  Makefile    plain and readline builds
```

`bridge.c` is the single file that imports `../core/`. All other `lang/`
files depend only on each other and the standard library.



### Relationship to `core/`

```
core/     NbE evaluator + bidirectional type checker (frozen)
lang/     graph reduction VM + surface elaboration (this)
```

The core's 185-test suite (`./lcore --test`) is the correctness baseline.
After any change to `bridge.c`, run it to confirm nothing is broken.
