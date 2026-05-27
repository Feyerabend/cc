
## Exercise: Add `lmax` - Maximum of Two Universe Levels

**Difficulty:** Medium (≈ 80 lines across 5 files)

**Prerequisite:** Read chapters 01-04, and study the `core/term.h` sections on
TM_LEVEL/TM_LZERO/TM_LSUC/TM_UNI_V (universe polymorphism).



### What you are building

Currently, `lsuc lzero` gives level 1, `lsuc (lsuc lzero)` gives level 2, and
so on.  But there is no way to compute the *maximum* of two variable levels.

```
-- You want to write:
let pair_type : Π(l1 : Level). Π(l2 : Level).
                Type_(lmax l1 l2) → Type_(lmax l1 l2) → Type_(lmax l1 l2)
  = \l1 l2 A B. Σ(_ : A). B
```

Without `lmax`, `l1` and `l2` would have to be the same level.  With it, you
can write combinators that work at the maximum of two input levels.



### Mathematical specification

`lmax` is a binary operation on levels with the following reduction rules:

```
lmax lzero      n           = n
lmax n          lzero       = n
lmax (lsuc m)   (lsuc n)    = lsuc (lmax m n)
lmax n          n           = n          -- by the above rules
```

On concrete (numeric) levels: `lmax i j = max(i, j)`.

In the type checker:
```
lmax l1 l2 : Level   (whenever l1 : Level and l2 : Level)
Type_(lmax l1 l2) : Type_{max(i,j)+1}
```



### Files to change

| File           | What to add                                                                 |
|----------------|-----------------------------------------------------------------------------|
| `core/term.h`  | `TM_LMAX` tag, `tm_lmax` constructor; `VL_LMAX` tag (or fold into existing) |
| `core/term.c`  | `tm_lmax` constructor body                                                  |
| `core/parse.c` | parse `lmax e1 e2` in `parse_atom`                                          |
| `core/eval.c`  | `nbe_vlmax` function + `TM_LMAX` case in `nbe_eval`; quote case             |
| `core/check.c` | `TM_LMAX` case in `infer`; update `as_universe`/`imax` if needed            |

Also update `core/elab.c` (`elab_subst`, `term_has_holes`) if you want holes to
work inside `lmax` expressions.



### Hints

**Evaluation:** Concrete levels should be collapsed eagerly (as `lsuc` is):

```c
Val *nbe_vlmax(Arena *a, Val *l1, Val *l2) {
    /* both concrete: VL_ZERO, VL_LSUC(VL_ZERO), etc. */
    if (is_concrete_level(l1) && is_concrete_level(l2)) {
        return vl_lzero_plus_n(a, max(concrete_lvl(l1), concrete_lvl(l2)));
    }
    /* zero on either side: identity */
    if (l1->tag == VL_LZERO) return l2;
    if (l2->tag == VL_LZERO) return l1;
    /* both succ: lmax (lsuc m) (lsuc n) = lsuc (lmax m n) */
    if (l1->tag == VL_LSUC && l2->tag == VL_LSUC)
        return vl_lsuc(a, nbe_vlmax(a, l1->succ, l2->succ));
    /* variable: build a neutral or a new VL_LMAX */
    return vl_lmax(a, l1, l2);
}
```

You may need a new `VL_LMAX` tag, or you can represent a stuck `lmax` as a
`VL_NEUTRAL` with a two-argument spine (but the former is simpler).

**Type checking:** `lmax l1 l2 : Level` - mirror `TM_LSUC`'s infer case.

**Conversion:** Two `lmax` expressions are equal iff their arguments are equal
(after reduction).  Add a `VL_LMAX` case to `conv`.

**Quoting:** Add `VL_LMAX` to `nbe_quote` - quote both sub-levels and build
`TM_LMAX`.



### Test cases to add to `main.c`

```c
/* lmax of two zero levels */
expect_conv(a, "lmax lzero lzero", "lzero", 1);

/* lmax with concrete succ */
expect_conv(a, "lmax (lsuc lzero) (lsuc (lsuc lzero))", "lsuc (lsuc lzero)", 1);

/* lmax commutes with succ on both sides */
expect_conv(a, "lmax (lsuc lzero) lzero", "lsuc lzero", 1);

/* lmax at a type level */
expect_type(a,
    "\\l1 l2. \\(A : Type_(lmax l1 l2)). A",
    "Π(l1 : Level). Π(l2 : Level). Π(A : Type_(lmax l1 l2)). Type_(lmax l1 l2)");
```



### Stretch goal

Add `lmax` to the lang layer as well: `ND_LMAX` node, cases in
`lang/bridge.c` and `lang/reduce.c`.  Follow the pattern of `ND_LSUC`.
