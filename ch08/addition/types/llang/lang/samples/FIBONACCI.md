
## What llang does with Fibonacci

A worked explanation of exactly what this system checks, how it represents things
internally, and how it evaluates — using `fibonacci.lam` as the concrete example.



### The source file

```lam
-- fibonacci.lam
import "../lib/nat.lam"   -- provides: plus, mult, pred, iszero

let rec fib : Nat → Nat = \
  λn. match n of \
    | zero   → zero \
    | succ k → match k of \
        | zero   → succ zero \
        | succ j → plus (fib k) (fib j)
```

The `\` at the end of each line is a continuation marker — the file loader joins these
into one logical line before parsing.  Once joined, `->` is rewritten to `→` and `fn`
to `λ` by the preprocessor.



### Surface syntax: similarities and differences from OCaml

If you know OCaml (or any ML-family language), the surface syntax will feel familiar —
but several details differ in ways that matter.

#### First: the fundamental difference in what these systems *are*

Before syntax, there is a deeper architectural gap.

*OCaml is a compiler.* You write source code; `ocamlopt` (or `ocamlc`) compiles it
to native machine code (or bytecode). The result is an executable that runs on a CPU.
Type checking happens once during compilation and is then *discarded* — the binary
contains no type information. Running `fib 7` executes machine instructions and returns
`13` as a machine integer.

*llang is a proof kernel.* There is no compilation step and no output binary. Loading
a file *is* the checking step. The "result" of evaluating `fib 7` is not an integer —
it is a *normal form*: the term `succ (succ ... (succ zero)...)` with 13 nested `succ`
constructors, a symbolic object that lives inside the kernel. Nothing is compiled to
machine code; everything stays as terms.

This difference cascades into everything else:

|                             | OCaml                                   | llang                             |
|-----------------------------|-----------------------------------------|-----------------------------------|
| What it produces            | native binary / bytecode                | normal forms (terms)              |
| Type info at runtime        | erased after compilation                | types ARE terms, never erased     |
| Can a program loop forever? | yes — no termination check              | no — structural check required    |
| What does "running" mean?   | executing machine instructions          | reducing terms to normal form     |
| Output of `fib 7`           | machine integer `13`                    | term `succ (succ ... zero)`       |
| Trusted core                | compiler + runtime (~millions of lines) | kernel: ~5000 lines of C          |
| Programs are also...        | only programs                           | also proofs in constructive logic |

*Type erasure vs type persistence.*
In OCaml, types exist only at compile time. After `ocamlopt` runs, `List.map` in the
binary knows nothing about `'a` — it has been erased. You cannot inspect the type of
a value at runtime.

In llang, types are terms and terms are types (Curry-Howard). The type `Vec Nat 3` is
itself a value of type `Type`. A function `Pi(A : Type). A → A` takes a type as its
*first argument* at runtime (in the sense of normalisation). Types are never erased
and can be computed, passed, returned, and stored like any other term.

*Turing-completeness vs totality.*
OCaml is Turing-complete: any computable function can be expressed, including ones
that diverge. The compiler does not attempt to verify termination.

llang enforces totality: every accepted `let rec` definition must pass the structural
termination checker. The system is deliberately *not* Turing-complete. This is a
feature, not a limitation — it is what makes the logic consistent. A Turing-complete
proof language could prove anything (including `False`) by writing a non-terminating
proof term.

*What "correct" means.*
In OCaml, correctness is an external property — you write tests, or perhaps use a
separate tool like a model checker or Coq proof. The type system catches type errors
but says nothing about whether `fib` actually computes Fibonacci numbers.  
In llang, correctness is stated as a *type*. If you write:
```lam
let fib_spec : Pi(n : Nat). Id Nat (fib n) (fib_reference n) = ...
```
then the kernel verifying that this term type-checks *is* the proof. There is no
separation between "running the program" and "checking the proof" — they are the same
kernel invocation.

*Trusted computing base.*
When you trust an OCaml program's result, you are trusting: the programmer, the type
system, the compiler (`ocamlopt` is ~200k lines of OCaml), the C runtime, the OS, and
the CPU.  

When you trust a llang proof, you are trusting: the kernel — `core/eval.c`,
`core/check.c`, `core/parse.c`, `core/defs.c`, `core/elab.c` — roughly 5000 lines of
straightforward C with no external dependencies. This small, auditable core is the
entire basis for trusting any result the system produces. This is the de Bruijn
criterion: keep the trusted core as small as possible.



#### Side by side

| Concept             | OCaml                                | llang                                                |
|---------------------|--------------------------------------|------------------------------------------------------|
| Recursive binding   | `let rec fib n = ...`                | `let rec fib n = ...`                                |
| Type annotation     | `let fib : int -> int = ...`         | `let fib : Nat → Nat = ...`                          |
| Lambda              | `fun n -> body`                      | `fn n. body` or `λn. body`                           |
| Multi-arg lambda    | `fun n k -> body`                    | `fn n k. body` (dot at the end, not after each name) |
| Match keyword       | `match n with`                       | `match n of`                                         |
| Match arm separator | `\| pat -> body`                     | `\| pat => body` or `\| pat → body`                  |
| Constructor names   | `Zero`, `Succ n` (capitalised)       | `zero`, `succ n` (lowercase)                         |
| Function type       | `int -> int`                         | `Nat → Nat` or `Nat -> Nat`                          |
| Dependent Pi type   | —                                    | `Pi(x : A). B` or `Π(x:A). B`                        |
| Pair type           | `int * bool`                         | `Σ(x : Nat). Bool` or `Sg(x:Nat). Bool`              |
| Pair construction   | `(1, true)`                          | `(zero, true)` (needs annotation to infer)           |
| Tuple projection    | `fst`, `snd` (via `let (a,b) = ...`) | `fst p`, `snd p`                                     |
| Comments            | `(* ... *)`                          | `-- ...` to end of line                              |
| Line continuation   | not needed (uses `;` or indentation) | `\` at end of line in `.lam` files                   |
| Polymorphism        | `'a list`                            | `List (A : Type)` — explicit Type argument           |
| Integers            | machine `int`                        | Peano `Nat` (zero/succ encoding)                     |

#### Where the similarity is genuine

*`let rec f x = body`* — both OCaml and llang support this argument-shorthand form.
In both cases it desugars to a lambda: `let rec f = fun x -> body` / `let rec f = fn x. body`.

*`match ... | ctor -> ...`* — the overall structure is the same: a scrutinee, then
arms beginning with `|`. OCaml uses `match e with` and `->` in arms; llang uses
`match e of` and `=>` (or `→`) in arms. These are small syntactic choices with no
semantic difference.

*Type annotations with `:`* — both languages use `name : type` syntax, in the same
positions (after a binding name, or as a cast `(e : T)`).

*Function application by juxtaposition* — `f x y` means "apply f to x then to y"
in both. No difference.

#### Where it looks the same but means something different

*`let rec` — no type inference for the body.*  
In OCaml, `let rec fib n = ...` fully infers the type of `fib` from its body.  
In llang, the `: Nat → Nat` annotation is *declared* but the body is NOT type-checked
against it — the system trusts the annotation and runs only the structural termination
check.  The actual type checking for `let rec` bodies is deferred to the callers.

*`let rec` — termination is *enforced*, not just expected.*  
OCaml happily accepts `let rec bad n = bad n` and diverges at runtime.  
llang rejects it at definition time:
```
termination: 'bad' is not structurally recursive on any argument
error  : could not define 'bad'
```
Every `let rec` must pass the structural checker in `core/termcheck.c`.

*Constructor names are lowercase.*
OCaml requires `Zero` and `Succ` (capitalised type constructors).  
llang uses `zero` and `succ` as lowercase keywords. User-defined constructors declared
with `data` are also lowercase. There is no lexical distinction between constructors
and variables — the parser resolves names against the definition table.

*Natural numbers are symbolic, not machine integers.*
OCaml's `int` is a 63-bit machine word.  
llang's `Nat` is the inductive type `zero | succ Nat`. The number 7 is
`succ (succ (succ (succ (succ (succ (succ zero))))))`. Arithmetic is real β-reduction
over this structure. There is no built-in fixed-precision arithmetic.  
This means `fib 7` genuinely computes by unrolling the recursive definition seven
times over symbolic constructors — what you see in the normal form is the full answer.

*Parametric polymorphism requires an explicit `Type` argument.*
In OCaml, `'a list` is automatically polymorphic.  
In llang, the type parameter must be passed explicitly:

```lam
-- OCaml:  List.length : 'a list -> int
-- llang:
let length : Pi(A : Type). List A -> Nat = ...
length Nat my_nat_list
length Bool my_bool_list
```

The `_` hole syntax lets the elaborator infer the type argument when it can:
`length _ my_nat_list`.

*Dependent types — the key addition.*
OCaml's type system is parametric but not dependent: types cannot depend on values.  
llang's type system is *fully dependent*: types can contain arbitrary terms.

```lam
-- A function whose return type depends on the value of its argument:
let Vec_head : Pi(n : Nat). Vec Nat (succ n) -> Nat = ...

-- The type Vec Nat (succ n) rules out empty vectors at the type level.
-- There is no runtime bounds check; the type is the proof of safety.
```

This is why llang needs `Π(x:A). B` — `B` can mention `x`, making the type of the
result depend on the actual argument passed.

*Side effects — none.*
OCaml functions can perform I/O, raise exceptions, and mutate references.  
llang functions are total, pure, and deterministic. There is no `unit -> 'a` escape
hatch, no exceptions, no mutation. A well-typed llang term always reduces to a value.

#### A direct translation

Here is the `fib` function in OCaml and llang side by side:

```ocaml
(* OCaml *)
let rec fib n =
  match n with
  | 0 -> 0
  | 1 -> 1
  | _ -> fib (n - 1) + fib (n - 2)
```

```lam
-- llang (fibonacci.lam)
let rec fib : Nat → Nat =
  λn. match n of
    | zero   → zero
    | succ k → match k of
        | zero   → succ zero
        | succ j → plus (fib k) (fib j)
```

Key differences visible here:

1. OCaml matches on integer literals `0`, `1`, and a wildcard `_`.  
   llang matches on constructors `zero` and `succ k` (binding the predecessor `k`).
   There is no integer literal syntax; the structure of the value is exposed directly.

2. OCaml's `_` arm catches all remaining cases (including all `n ≥ 2`).  
   llang's `succ k` arm then re-matches `k` to get `j = n-2`. Both recursive calls
   are visible as `fib k` and `fib j` on named, smaller subterms.

3. OCaml uses `n - 1` and `n - 2` — arithmetic on machine integers.  
   llang names `k` and `j` directly from the constructor structure — no subtraction
   needed. `k` *is* `n - 1` by construction.

4. OCaml writes `fib (n-1) + fib (n-2)` using operator `+`.  
   llang writes `plus (fib k) (fib j)` using a named function `plus` loaded from
   `lib/nat.lam`, itself defined by structural recursion over Nat.



### What the system is *actually* checking

When you load this file, the kernel does not understand Fibonacci. It verifies:
```
fib is a well-defined, total function
with the declared type Nat → Nat
```
Concretely, it runs two independent jobs in sequence.



#### Job 1 — Structural termination check

Before anything else, the system checks that every recursive call is on a
*structurally smaller* argument.

The relevant structure from `fibonacci.lam`:

```
match n of
  | zero   → ...
  | succ k → match k of          -- k is a binder from succ k: k < n
      | zero   → ...
      | succ j → plus (fib k) (fib j)  -- j is a binder from succ j: j < k < n
```

The checker (`core/termcheck.c`) verifies:

- `fib k` — `k` is a match-arm binder of the outer succ arm → `k < n` structurally
- `fib j` — `j` is a match-arm binder of the inner succ arm → `j < k < n` structurally

Both calls pass. If you tried:

```lam
let rec bad n = bad n
```

the checker rejects it immediately — `n` is not strictly smaller than `n`.

The check is purely syntactic and conservative: it looks for a single argument position
where every self-call has a strictly decreasing match-arm binder. If no such position
exists, the definition is rejected even if the function happens to terminate for other
reasons. This is intentional — the kernel trusts only what it can verify structurally.



#### Job 2 — Evaluation and registration

Once the structural check passes, the expression is evaluated by `nbe_eval` into a
semantic value (`VL_FIX` closure) and registered under the name `fib` with the
declared type `Nat → Nat`.

> *Key point:* for `let rec`, the type annotation is *declared but not verified*.
> The system stores `Nat → Nat` as `fib`'s type without running a bidirectional
> type check on the body. The structural termination check is the only safety guarantee
> for recursive definitions.  
>
> Plain `let` bindings are different: the body is passed to `infer` in `core/check.c`,
> the inferred type is checked against any annotation, and holes (`_`) are filled by
> elaboration. That full pipeline does not run for `let rec`.



### Desugaring: what the kernel actually sees

The surface form `let rec fib : Nat → Nat = body` desugars in `lang/main.c` to:
```
fix (λfib. body)
```

The core kernel represents this as `TM_FIX` — the fixpoint combinator. When applied
to an argument, `fix f` unrolls one step: `(fix f) x = f (fix f) x`.

The `match` expressions stay as `TM_MATCH` — they are *not* compiled to `natrec`.
The kernel has `TM_MATCH` as a first-class term constructor, handled directly by the
type checker and evaluator. `natrec` is a separate, lower-level primitive that is
still available but not what `match` compiles to.

So the kernel's actual internal representation of `fib`, after desugaring and parsing:
```
TM_FIX("fib",
  TM_LAM("n",
    TM_MATCH(VAR n, Nat,
      arm_zero → TM_ZERO,
      arm_succ("k") →
        TM_MATCH(VAR k, Nat,
          arm_zero → TM_SUCC(TM_ZERO),
          arm_succ("j") →
            APP(APP(plus, APP(VAR fib, VAR k)),
                           APP(VAR fib, VAR j))))))
```

(Shown symbolically. The real representation uses de Bruijn indices for bound variables
and a global definition table lookup for `fib` and `plus`.)



### Pattern matching: TM_MATCH in detail

`match` has two separate roles: type checking and evaluation.

#### During type checking (core/check.c)

The type checker handles `TM_MATCH` bidirectionally:

- *Family inference* — it infers the scrutinee's type to determine which inductive
  family is being matched (here: `Nat`).
- *Exhaustiveness* — it requires exactly one arm per constructor. For `Nat` that
  means exactly two arms: `zero` and `succ`. Missing or extra arms produce a type
  error. This is the system's form of coverage checking.
- *Arm body checking* — each arm body is type-checked in a context extended with the
  arm's binders. The `succ k` arm adds `k : Nat` to the context; an IH binder
  `succ k ih` additionally adds `ih : T(k)`.

#### During evaluation (core/eval.c)

The evaluator handles `TM_MATCH` by normalising the scrutinee and case-splitting:

- If the value is `VL_ZERO`, the zero arm fires immediately.
- If the value is `VL_SUCC(v)`, the succ arm fires with `k` bound to `v`.
- If the value is neutral (a stuck expression under an unknown variable), the whole
  match stays stuck, recorded as a `VL_NEUTRAL` with an `SP_MATCH` spine.



### The two evaluation layers

The system has two distinct evaluation paths that coexist.

#### Layer 1 — lang graph reducer (lang/reduce.c)

When you type `fib (succ (succ (succ (succ (succ zero)))))` in the REPL, evaluation
goes through the graph reducer:

- Terms are nodes on a mutable heap; edges are shared pointers.
- `nf(h, a, root)` normalises a node in-place by repeatedly firing reduction rules.
- Sharing means `fib k` and `fib j` that appear in multiple branches are only
  evaluated once — their node is updated in place.
- `fix` nodes unroll lazily: `(fix f) arg` becomes `f (fix f) arg`, then `f` is
  applied, then the resulting body is normalised.

This is what produces the REPL output:
```
>> fib (succ (succ (succ (succ (succ (succ (succ zero)))))))
  normal : succ (succ (succ (succ (succ (succ (succ (succ (succ (succ (succ (succ (succ zero))))))))))))
```

That is fib 7 = 13, written as 13 nested `succ` constructors. The REPL displays normal
forms — fully reduced terms with only constructors and binders remaining.

#### Layer 2 — NbE kernel (core/eval.c)

The type checker uses a separate, purely functional evaluator based on
*Normalisation by Evaluation (NbE)*. It is used whenever the checker needs to
decide definitional equality — for example, checking that the return type of an
application matches the expected type.

NbE works in two phases:

*Phase 1: eval — Term → Val*

`nbe_eval` interprets a `Term` into a `Val`. The key idea is that functions become
host-language closures:
```c
// Simplified view of nbe_eval in core/eval.c:
case TM_LAM:
    return vl_lam(a, t->lam.name, env, t->lam.body);
    // stores env + body; no beta-reduction yet

case TM_APP:
    return nbe_vapp(a,
        nbe_eval(a, env, t->app.fun),
        nbe_eval(a, env, t->app.arg));
    // nbe_vapp fires beta immediately if fun is VL_LAM,
    // otherwise records a neutral spine
```

The `Val` type has constructors for:
- `VL_ZERO`, `VL_SUCC` — concrete Nat values
- `VL_LAM` — a closure: a C pointer to the body `Term` plus a captured `Env*`
- `VL_FIX` — a fixpoint closure (for `let rec` definitions)
- `VL_NEUTRAL` — a stuck term: a level (de Bruijn variable) with an accumulated spine
  of applications, eliminations, and path applications

Beta-reduction happens inside `nbe_vapp` when the function is `VL_LAM`: it extends
the closure's environment with the argument and calls `nbe_eval` on the body.
This is reduction in the *semantic domain*, not syntactic substitution.

*Phase 2: quote — Val → Term*

`nbe_quote` converts a `Val` back to a `Term` in normal form. Free variables that
appeared as neutrals are quoted back into their corresponding binder names. The result
is a canonical term — unique up to α-equivalence — enabling direct syntactic
comparison for conversion checking.

*Why NbE instead of rewriting*

Term-rewriting works by substituting sub-terms at each step. For a function like
`(λx. body) arg`, it copies `body` with `arg` substituted for `x`. Nested applications
with large arguments produce large intermediate trees, and sharing is lost.

NbE avoids this: the `VL_LAM` closure captures the environment by pointer — no copy.
`nbe_vapp` fires β-reduction by extending a single environment cell. Duplicated
sub-expressions share the same `Val*` pointer. The intermediate "reduction tree" is
never built; only the final normal form is reconstructed during readback.

For the type checker, which calls `nbe_eval` on types many thousands of times,
this efficiency is essential.



### Concrete evaluation trace: fib 3

Let's trace `fib (succ (succ (succ zero)))` through the graph reducer.

Write `n` for the successor-encoded natural number `n`.

```
fib 3
  scrutinee 3 = succ 2 → succ arm, k = 2
  inner scrutinee k = 2 = succ 1 → succ arm, j = 1
  → plus (fib 2) (fib 1)

fib 2
  scrutinee 2 = succ 1 → succ arm, k = 1
  inner scrutinee k = 1 = succ 0 → succ arm, j = 0
  → plus (fib 1) (fib 0)

fib 1
  scrutinee 1 = succ 0 → succ arm, k = 0
  inner scrutinee k = 0 = zero → zero arm
  → succ zero = 1

fib 0
  scrutinee 0 = zero → zero arm
  → zero = 0
```

Substituting back:
```
fib 2 = plus 1 0 = 1
fib 3 = plus 1 1 = 2  ✓
```

The graph reducer shares the `fib 1` value between the two places it is needed
in the `fib 3` computation, so it is only evaluated once.



### What is NOT being checked

Despite accepting the definition, the system does not verify:

*Correctness of the algorithm.* It does not prove that `fib` computes Fibonacci
numbers in the standard sense. To state and verify that property, you would need
an explicit inductive specification and a proof:

```lam
-- e.g., a relation linking n, fib(n-1), fib(n-2), and fib(n)
-- and an inductive proof that fib satisfies it
```

The type `Nat → Nat` says only that the function maps naturals to naturals.

*The type annotation.* As noted above, `fib : Nat → Nat` is stored but not verified
against the body for `let rec`. A subsequent plain `let` definition that uses `fib`
will be type-checked bidirectionally, so unsound annotations would surface then.

*Computational complexity.* The structural checker ensures termination only. The
naive doubly-recursive implementation accepted here is exponential. The kernel does
not reason about time or space.



### What the system *does* guarantee, once accepted

1. *Totality* — `fib n` terminates for every `n : Nat`, because the structural
   checker verified that every call descends in the Nat order.

2. *Nat-in, Nat-out* — the registered type is `Nat → Nat`. Any subsequent
   definition that uses `fib` and is type-checked by `infer`/`check` must pass it a
   `Nat` and treat the result as a `Nat`.

3. *Definitional reduction* — the computation rules for `match` and `fix` are part
   of the system's definitional equality. The kernel's conversion checker will reduce
   `fib (succ zero)` to `succ zero` automatically when comparing types, not just when
   evaluating in the REPL.



### Architecture: what runs, in order

```
fibonacci.lam (text file)
     │
     ▼  lang/main.c: load_file
        — join continuation lines
        — strip comments
        — per-line: process_line

     ▼  lang/main.c: process_line (for each let rec)
        — preprocess:  ->  →    fn  λ
        — desugar:  let rec fib : T = body
                    →  def_define_nocheck("fib", "Nat → Nat",
                                          "fix (λfib. body)")

     ▼  core/defs.c: def_define_nocheck
        — parse "fix (λfib. body)" → Term (TM_FIX)
        — core/termcheck.c: term_check_structural
            checks every recursive call is on a smaller binder  ← STRUCTURAL CHECK
        — parse "Nat → Nat" → Term → Val (the declared type)
        — core/eval.c: nbe_eval on the TM_FIX
            → VL_FIX closure stored in the definition table

     ▼  REPL: fib (succ ... (succ zero) ...)
        — lang/reduce.c: graph reduction + fix unrolling
        — prints normal form (successor-encoded result)
```
