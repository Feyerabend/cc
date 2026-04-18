
## Categorical Compilation Pipeline

`cat_vm2.py` implements a four-stage compilation pipeline where category theory
is used as a design and verification tool at every stage above the VM level.
By the time code reaches the VM, all categorical structure has been compiled away.

This example illustrates the diagram from the main [README](./../../README.md):

```
┌─────────────────────────────────────┐
│  STAGE 1: Surface Language          │ ← category theory in TYPE SYSTEM
│  - Types as objects (Int, A×B, A+B) │   Products, sums, exponentials
│  - Terms as morphisms (f: A → B)    │   express program structure
└─────────────────────────────────────┘
            ↓ (elaboration)
┌─────────────────────────────────────┐
│  STAGE 2: Categorical IR            │ ← category theory in STRUCTURE
│  - Explicit categorical operations  │   IR preserves categorical laws
│  - De Bruijn indices for variables  │   for optimisation
└─────────────────────────────────────┘
            ↓ (optimisation)
┌─────────────────────────────────────┐
│  STAGE 3: Categorical Optimiser     │ ← category theory in OPTIMISATION
│  - Product laws: fst(⟨a,b⟩) = a    │   Laws enable sound rewrites
│  - Sum laws: case(inl(x),f,g)=f(x)  │   Guarantees correctness
│  - Fusion, eta-reduction, etc.      │
└─────────────────────────────────────┘
            ↓ (code generation)
┌─────────────────────────────────────┐
│  STAGE 4: Simple VM                 │ ← NO category theory
│  - Stack-based bytecode             │   Just efficient execution
│  - Simple instructions (PUSH, ADD)  │   Categories compiled away
└─────────────────────────────────────┘
```


### Stage 1: Surface Language

The surface language has:
- *Types*: `IntType`, `ProductType (A × B)`, `SumType (A + B)`
- *Expressions*: `Var`, `Lit`, `BinOp`, `Pair`, `Fst`, `Snd`, `InL`, `InR`, `Case`
- *Type checking*: each expression reports its type via `type_of(ctx)`

Products and sums correspond directly to categorical products and coproducts.


### Stage 2: Categorical IR

The IR uses *de Bruijn indices* (positional variable references) so that
variable binding is explicit and substitution is structurally clean.
It mirrors the surface language but with named variables removed:
`$0`, `$1`, ... for variable positions.


### Stage 3: Categorical Optimiser

The optimiser applies *equational laws* derived from category theory:

| Law | Rewrite |
|-----|---------|
| Product β | `fst(⟨a, b⟩) → a`, `snd(⟨a, b⟩) → b` |
| Sum β | `case(inl(x), f, g) → f[x]`, `case(inr(y), f, g) → g[y]` |
| Fusion | `fst(pair(a, b)) → a` etc. |

These rewrites are sound because they hold in any cartesian closed category.


### Stage 4: Stack-Based VM

The final VM uses simple stack instructions: `PUSH`, `ADD`, `SUB`, `MUL`,
`PAIR`, `FST`, `SND`, `INL`, `INR`, `CASE`. No type information is carried
at runtime — types were verified in Stage 1 and optimised away in Stage 3.


### Running

```bash
python cat_vm2.py     # run pipeline demo
python test_cat_vm2.py  # run tests
```

