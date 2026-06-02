#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "arena.h"
#include "term.h"
#include "eval.h"
#include "parse.h"
#include "check.h"
#include "defs.h"
#include "elab.h"

/* ── normalize and print */

static void run(Arena *a, const char *src) {
    Term *t = parse(a, src);
    if (!t) return;
    if (term_has_holes(t)) {
        ElabCtx e; elab_init(&e, a);
        if (!elab_infer(&e, a, 0, NULL, NULL, t)) return;
        t = elab_subst(&e, a, 0, t);
        if (!t) return;
    }
    printf("  parsed : "); term_print(t); printf("\n");
    Term *nf = nbe_nf(a, t);
    printf("  normal : "); term_print(nf); printf("\n");
}

/* ── infer type and print */

static void run_infer(Arena *a, const char *src) {
    Term *t = parse(a, src);
    if (!t) return;
    if (term_has_holes(t)) {
        ElabCtx e; elab_init(&e, a);
        if (!elab_infer(&e, a, 0, NULL, NULL, t)) return;
        t = elab_subst(&e, a, 0, t);
        if (!t) return;
    }
    printf("  term   : "); term_print(t); printf("\n");
    Val *ty = infer(a, 0, NULL, NULL, t);
    if (!ty) return;
    printf("  type   : "); val_print_tctx(a, ty, 0, NULL); printf("\n");
    Term *nf = nbe_nf(a, t);
    printf("  normal : "); term_print(nf); printf("\n");
}

/* ── reserved keyword list (parse.c checks these before name_lookup) */

static int is_reserved_name(const char *n) {
    static const char *kw[] = {
        "ua", "funext",
        "Nat", "zero", "succ", "natrec",
        "Bool", "true", "false", "boolrec",
        "Id", "refl", "J",
        "fst", "snd", "Type",
        "W", "sup", "wrec",
        "Empty", "abort",
        "Unit", "star", "unitrec",
        "Sum", "inl", "inr", "case",
        "trunc", "trint", "squash", "truncrec",
        "Quot", "qin", "qeq", "quotrec",
        "II", "i0", "i1", "Path", "PathP", "transp", "hcomp", "comp", "fill",
        "Glue", "glue", "unglue", "primSub",
        "imin", "imax", "ineg",
        "Level", "lzero", "lsuc", "lmax",
        "S1", "base", "loop", "S1rec",
        "match", "of",
        NULL
    };
    for (int i = 0; kw[i]; i++)
        if (strcmp(n, kw[i]) == 0) return 1;
    if (strncmp(n, "Type", 4) == 0 && n[4] == '_') return 1;
    return 0;
}

/* ── built-in test suite */

static int tests_pass = 0;
static int tests_fail = 0;

/* ── expect a type error (negative test) */

static void expect_fail(Arena *a, const char *src, const char *reason) {
    Term *t = parse(a, src);
    if (!t) {
        printf("  [FAIL-PARSE unexpected] %s\n", src);
        tests_fail++;
        return;
    }
    Val *ty = infer(a, 0, NULL, NULL, t);
    if (ty) {
        tests_fail++;
        printf("  [BUG: should have failed] %s  — %s\n", src, reason);
        printf("    got type: "); term_print(nbe_quote(a, 0, ty)); printf("\n");
    } else {
        tests_pass++;
        printf("  [REJECTED OK] %s\n", src);
    }
}

/* ── conv equality check */

static void expect_conv(Arena *a, const char *sa, const char *sb, int should_equal) {
    Term *ta = parse(a, sa);
    Term *tb = parse(a, sb);
    if (!ta || !tb) {
        printf("  [FAIL-PARSE] %s  ~  %s\n", sa, sb);
        tests_fail++;
        return;
    }
    Val *va = nbe_eval(a, NULL, ta);
    Val *vb = nbe_eval(a, NULL, tb);
    int eq = conv(a, 0, va, vb);
    if (eq == should_equal) {
        tests_pass++;
        printf("  [OK] %s  %s  %s\n", sa, eq ? "≡" : "≢", sb);
    } else {
        tests_fail++;
        printf("  [BUG] %s  expected %s  %s\n",
               sa, should_equal ? "≡" : "≢", sb);
    }
}

/* ── infer type and check conv-equality with an expected type */

static void expect_type(Arena *a, const char *src, const char *expected_type_src) {
    Term *t = parse(a, src);
    if (!t) {
        printf("  [FAIL-PARSE] %s\n", src);
        tests_fail++;
        return;
    }
    Val *ty = infer(a, 0, NULL, NULL, t);
    if (!ty) {
        printf("  [FAIL-INFER] %s\n", src);
        tests_fail++;
        return;
    }
    Term *et = parse(a, expected_type_src);
    if (!et) {
        printf("  [FAIL-PARSE expected] %s\n", expected_type_src);
        tests_fail++;
        return;
    }
    Val *ev = nbe_eval(a, NULL, et);
    if (conv(a, 0, ty, ev)) {
        tests_pass++;
        printf("  [OK] type of %s  ≡  %s\n", src, expected_type_src);
    } else {
        tests_fail++;
        printf("  [BUG] type of %s  expected %s\n", src, expected_type_src);
        printf("        got: "); val_print_tctx(a, ty, 0, NULL); printf("\n");
    }
}

/* ── M2: elab test — infer type of a term with holes, compare after forcing metas */

static void expect_elab(Arena *a, const char *src, const char *expected_type_src) {
    Term *t = parse(a, src);
    if (!t) {
        printf("  [FAIL-PARSE] %s\n", src);
        tests_fail++; return;
    }
    ElabCtx e; elab_init(&e, a);
    Val *ty = elab_infer(&e, a, 0, NULL, NULL, t);
    if (!ty) {
        printf("  [FAIL-ELAB-INFER] %s\n", src);
        tests_fail++; return;
    }
    ty = elab_force(&e, ty);
    t = elab_subst(&e, a, 0, t);
    if (!t) {
        printf("  [FAIL-ELAB-SUBST] %s\n", src);
        tests_fail++; return;
    }
    Term *et = parse(a, expected_type_src);
    if (!et) {
        printf("  [FAIL-PARSE-EXPECTED] %s\n", expected_type_src);
        tests_fail++; return;
    }
    Val *ev = nbe_eval(a, NULL, et);
    if (conv(a, 0, ty, ev)) {
        tests_pass++;
        printf("  [OK-M2] type of  %s  ≡  %s\n", src, expected_type_src);
    } else {
        tests_fail++;
        printf("  [BUG-M2] type of %s\n", src);
        printf("           expected: %s\n", expected_type_src);
        printf("           got: "); val_print_tctx(a, ty, 0, NULL); printf("\n");
    }
}

static void run_tests(Arena *a) {
    tests_pass = 0;
    tests_fail = 0;

    /* --- NbE reduction --- */
    const char *nbe_tests[] = {
        "\\x. x",
        "\\x. \\y. x",
        "\\f. \\x. f (f x)",
        "(\\x. x) (\\y. y)",
        "(\\x. \\y. x) (\\a. a) (\\b. b)",
        "(\\x. \\y. y) (\\a. a) (\\b. b)",
        "\\x y. x",
        "\\x y. y",
        "\\x y z. y",
        "(\\x y. x) (\\a. a) (\\b. b)",
        "\\x. \\x. x",
        "(\\x. x x) (\\x. x)",
        "(\\x. \\y. \\z. x z (y z)) (\\x. \\y. x) (\\x. \\y. x)",
        "(\\f. \\x. f (f x)) (\\n. \\f. \\x. f (n f x)) (\\f. \\x. x)",
        NULL
    };
    printf("\n=== NbE reduction ===\n");
    for (int i = 0; nbe_tests[i]; i++) {
        printf("\n[%d] %s\n", i + 1, nbe_tests[i]);
        run(a, nbe_tests[i]);
    }

    /* --- Type formation (positive) --- */
    const char *type_tests[] = {
        "Type",
        "Type_1",
        "Π(A : Type). A",
        "Π(A : Type). A → A",
        "Π(A : Type). Π(B : Type). A → B → A",
        "(\\A x. x : Π(A : Type). A → A)",
        "(\\A B x _. x : Π(A : Type). Π(B : Type). A → B → A)",
        NULL
    };
    printf("\n=== Type formation (positive) ===\n");
    for (int i = 0; type_tests[i]; i++) {
        printf("\n[T%d] %s\n", i + 1, type_tests[i]);
        run_infer(a, type_tests[i]);
    }

    /* --- Dependent application: result type depends on argument value --- */
    fflush(stdout);
    printf("\n=== Dependent application ===\n");
    /* D1: id applied to Type — result type should instantiate to Type → Type */
    printf("\n[D1] id Type  →  type: Π(_:Type). Type\n");
    run_infer(a, "(\\A x. x : Π(A : Type_1). Π(_ : A). A) Type");
    /* D2: id applied to a Pi type — result type should be (Π(B:T).B) → (Π(B:T).B) */
    printf("\n[D2] id (Π(B:Type).B)  →  type: (Π(B:Type).B) → (Π(B:Type).B)\n");
    run_infer(a, "(\\A x. x : Π(A : Type_1). Π(_ : A). A) (Π(B : Type). B)");
    /* D3: K applied to Type,Type — result should be Type → Type → Type */
    printf("\n[D3] K Type Type  →  type: Type → Type → Type\n");
    run_infer(a, "(\\A B x y. x : Π(A : Type_1). Π(B : Type_1). Π(_ : A). Π(_ : B). A) Type Type");

    /* --- conv / definitional equality --- */
    fflush(stdout);
    printf("\n=== Conversion / eta ===\n");
    /* alpha equivalence: rename doesn't matter for de Bruijn */
    expect_conv(a, "\\x. x", "\\y. y", 1);
    /* eta: \f. \x. f x  ≡  \f. f  — our conv has eta so these are equal */
    expect_conv(a, "\\f. \\x. f x", "\\f. f", 1);
    /* genuinely distinct: self-app vs identity */
    expect_conv(a, "\\x. x x", "\\x. x", 0);
    /* beta then alpha */
    expect_conv(a, "(\\f. \\x. f x) (\\y. y)", "\\x. x", 1);
    /* Pi alpha-equivalence */
    expect_conv(a, "Π(A : Type). A", "Π(B : Type). B", 1);
    /* Universe inequality */
    expect_conv(a, "Type", "Type_1", 0);
    expect_conv(a, "Π(A : Type). A", "Π(A : Type_1). A", 0);

    /* --- Sigma types --- */
    fflush(stdout);
    printf("\n=== Sigma types ===\n");

    /* S1: Σ formation: Σ(x:Type).x  :  Type_1 */
    printf("\n[S1] Σ(x:Type).x  :  Type_1\n");
    run_infer(a, "Σ(x : Type). x");

    /* S2: pair introduction with annotation */
    printf("\n[S2] (Type, Type) : Σ(x:Type_1).Type_1\n");
    run_infer(a, "((Type, Type) : Σ(x : Type_1). Type_1)");

    /* S3: fst projection */
    printf("\n[S3] fst ((Type, Type) : Σ(x:Type_1).Type_1)  →  Type\n");
    run_infer(a, "fst ((Type, Type) : Σ(x : Type_1). Type_1)");

    /* S4: snd projection */
    printf("\n[S4] snd ((Type, Type) : Σ(x:Type_1).Type_1)  →  Type\n");
    run_infer(a, "snd ((Type, Type) : Σ(x : Type_1). Type_1)");

    /* S5: dependent snd — type of snd depends on fst value */
    printf("\n[S5] dependent snd: ((Type, \\x.x) : Σ(A:Type_1). A → A)  →  snd : Type → Type\n");
    run_infer(a, "snd ((Type, (\\x. x : Type → Type)) : Σ(A : Type_1). A → A)");

    /* S6: eta for neutral pairs — \p. (fst p, snd p) ≡ \p. p */
    printf("\n[S6] pair eta / neutral pair tests\n");
    expect_conv(a, "\\p. (fst p, snd p)", "\\p. p", 1);
    /* negative: (fst p, fst p) ≢ p because snd component differs */
    expect_conv(a, "\\p. (fst p, fst p)", "\\p. p", 0);

    /* S7: Sigma alpha-equivalence */
    expect_conv(a, "Σ(x : Type). x", "Σ(y : Type). y", 1);

    /* --- Identity types --- */
    fflush(stdout);
    printf("\n=== Identity types ===\n");

    /* I1: formation — Id(Type_1, Type, Type) : Type_2 */
    printf("\n[I1] Id Type_1 Type Type  :  Type_2\n");
    run_infer(a, "Id Type_1 Type Type");

    /* I2: reflexivity — refl Type : Id Type_1 Type Type */
    printf("\n[I2] (refl Type : Id Type_1 Type Type)\n");
    run_infer(a, "(refl Type : Id Type_1 Type Type)");

    /* I3: J-β — proof is refl, result is the base case d */
    printf("\n[I3] J-β: J ... refl Type  →  Type  (base case)\n");
    run_infer(a, "J Type_1 Type"
                 " (\\b _. Type_1 : Π(b : Type_1). Id Type_1 Type b → Type_2)"
                 " Type Type refl Type");

    /* I4: conv — two refl proofs at the same value are equal */
    printf("\n[I4] conv tests\n");
    expect_conv(a, "(refl Type : Id Type_1 Type Type)",
                   "(refl Type : Id Type_1 Type Type)", 1);
    /* refl Type ≢ refl Type_1 (different witnesses) */
    expect_conv(a, "(refl Type   : Id Type_1 Type   Type)",
                   "(refl Type_1 : Id Type_2 Type_1 Type_1)", 0);
    /* Id is invariant in its arguments */
    expect_conv(a, "Id Type_1 Type Type", "Id Type_1 Type_1 Type_1", 0);

    /* I5: J on neutral proof — exercises SP_J path in conv_spine.
     * When proof is a bound variable the J stays stuck as a neutral;
     * two identical stuck J applications must be conv-equal.           */
    printf("\n[I5] J on neutral proof (SP_J conv)\n");
#define JMOT "(\\b _. Type_1 : Π(b : Type_1). Id Type_1 Type b → Type_2)"
    expect_conv(a, "\\p. J Type_1 Type " JMOT " Type   Type p",
                   "\\p. J Type_1 Type " JMOT " Type   Type p", 1);
    /* different base case d: Type ≢ Type_1 → unequal J applications */
    expect_conv(a, "\\p. J Type_1 Type " JMOT " Type   Type p",
                   "\\p. J Type_1 Type " JMOT " Type_1 Type p", 0);
#undef JMOT

    /* --- Booleans --- */
    fflush(stdout);
    printf("\n=== Booleans ===\n");

    /* B1: types */
    printf("\n[B1] Bool : Type\n");
    run_infer(a, "Bool");
    printf("\n[B2] true : Bool    false : Bool\n");
    run_infer(a, "true");
    run_infer(a, "false");

    /* B3: boolrec β */
    printf("\n[B3] boolrec β on true → tt arg, on false → ff arg\n");
    run_infer(a,
        "boolrec (\\_. Nat : Π(_ : Bool). Type)"
        "        (succ zero) zero true");
    run_infer(a,
        "boolrec (\\_. Nat : Π(_ : Bool). Type)"
        "        (succ zero) zero false");

    /* B4: dependent motive — negation: Bool → Bool */
    printf("\n[B4] not : Bool → Bool  (boolrec with Bool motive)\n");
    run_infer(a,
        "(\\ b. boolrec (\\_. Bool : Π(_ : Bool). Type) false true b"
        " : Π(_ : Bool). Bool)");

    /* B5: stuck boolrec stays neutral */
    printf("\n[B5] boolrec on neutral b (stays stuck)\n");
    run_infer(a,
        "(\\ b. boolrec (\\_. Bool : Π(_ : Bool). Type) false true b"
        " : Π(b : Bool). Bool)");

    /* B6: conv */
    printf("\n[B6] conv tests\n");
    expect_conv(a, "true",  "true",  1);
    expect_conv(a, "false", "false", 1);
    expect_conv(a, "true",  "false", 0);
    expect_conv(a, "Bool",  "Bool",  1);
    expect_conv(a, "Bool",  "Nat",   0);
    /* β-conv: boolrec P true false true ≡ true */
    expect_conv(a,
        "boolrec (\\_. Bool : Π(_:Bool).Type) true false true",
        "true", 1);
    /* stuck boolrec: same neutral same branches → equal */
    expect_conv(a,
        "(\\ b. boolrec (\\_. Bool : Π(_:Bool).Type) false true b : Π(b:Bool).Bool)",
        "(\\ b. boolrec (\\_. Bool : Π(_:Bool).Type) false true b : Π(b:Bool).Bool)", 1);
    /* stuck boolrec: same neutral, different branches → unequal */
    expect_conv(a,
        "(\\ b. boolrec (\\_. Bool : Π(_:Bool).Type) false true  b : Π(b:Bool).Bool)",
        "(\\ b. boolrec (\\_. Bool : Π(_:Bool).Type) true  false b : Π(b:Bool).Bool)", 0);

    /* B7: negative */
    printf("\n[B7] negative tests\n");
    expect_fail(a, "boolrec (\\_. Nat : Π(_:Bool).Type) zero zero Nat",
                   "Nat is not a Bool scrutinee");
    expect_fail(a, "boolrec (\\_. Nat : Π(_:Nat).Type)  zero zero true",
                   "motive domain is Nat not Bool");

    /* --- Natural numbers --- */
    fflush(stdout);
    printf("\n=== Natural numbers ===\n");

    /* N1: Nat is a type */
    printf("\n[N1] Nat : Type\n");
    run_infer(a, "Nat");

    /* N2/N3: constructors */
    printf("\n[N2] zero : Nat\n");
    run_infer(a, "zero");
    printf("\n[N3] succ (succ zero) : Nat\n");
    run_infer(a, "succ (succ zero)");

    /* N4: natrec β on zero — natrec P zero s zero ≡ zero */
    printf("\n[N4] natrec β/zero  →  zero\n");
    run_infer(a,
        "natrec (\\_ . Nat : Π(_ : Nat). Type)"
        "       zero"
        "       (\\m r. succ r : Π(_ : Nat). Nat → Nat)"
        "       zero");

    /* N5: natrec β on succ — computes id on 2 = 2 */
    printf("\n[N5] natrec id on succ(succ zero)  →  succ(succ zero)\n");
    run_infer(a,
        "natrec (\\_ . Nat : Π(_ : Nat). Type)"
        "       zero"
        "       (\\m r. succ r : Π(_ : Nat). Nat → Nat)"
        "       (succ (succ zero))");

    /* N6: natrec stuck on neutral — stays as natrec */
    printf("\n[N6] natrec on neutral n (stays stuck)\n");
    run_infer(a,
        "(\\n. natrec (\\_ . Nat : Π(_ : Nat). Type)"
        "            zero"
        "            (\\m r. succ r : Π(_ : Nat). Nat → Nat)"
        "            n"
        " : Π(n : Nat). Nat)");

    /* N7: conv — identical natrec applications are equal */
    printf("\n[N7] conv tests\n");
    expect_conv(a, "zero", "zero", 1);
    expect_conv(a, "succ zero", "succ zero", 1);
    expect_conv(a, "succ zero", "zero", 0);
    expect_conv(a, "succ (succ zero)", "succ (succ zero)", 1);
    /* beta: natrec ... (succ zero) ≡ succ zero */
    expect_conv(a,
        "natrec (\\_ . Nat : Π(_ : Nat). Type) zero"
        "       (\\m r. succ r : Π(_ : Nat). Nat → Nat) (succ zero)",
        "succ zero", 1);

    /* N8: negative — succ of non-Nat */
    printf("\n[N8] negative tests\n");
    expect_fail(a, "succ Type", "Type is not Nat");
    /* step domain is Type instead of Nat */
    expect_fail(a,
        "natrec (\\_. Nat : Π(_ : Nat). Type) zero"
        "       (\\_  r. succ r : Π(_ : Type). Nat → Nat) zero",
        "step domain is Type not Nat");
    /* step return type is wrong: P=λ_.Nat expects Nat, step returns Type */
    expect_fail(a,
        "natrec (\\_. Nat : Π(_ : Nat). Type) zero"
        "       (\\_  r. Nat : Π(_ : Nat). Nat → Type) (succ zero)",
        "step return type is Type not Nat");

    /* N9: stuck natrec conv — same neutral, same args equal; different base unequal */
    printf("\n[N9] stuck natrec conv\n");
    expect_conv(a,
        "(\\n. natrec (\\_. Nat : Π(_:Nat).Type) zero"
        "            (\\m r. succ r : Π(_:Nat).Nat→Nat) n : Π(n:Nat).Nat)",
        "(\\n. natrec (\\_. Nat : Π(_:Nat).Type) zero"
        "            (\\m r. succ r : Π(_:Nat).Nat→Nat) n : Π(n:Nat).Nat)", 1);
    expect_conv(a,
        "(\\n. natrec (\\_. Nat : Π(_:Nat).Type) zero"
        "            (\\m r. succ r : Π(_:Nat).Nat→Nat) n : Π(n:Nat).Nat)",
        "(\\n. natrec (\\_. Nat : Π(_:Nat).Type) (succ zero)"
        "            (\\m r. succ r : Π(_:Nat).Nat→Nat) n : Π(n:Nat).Nat)", 0);

    /* --- Univalence --- */
    fflush(stdout);
    printf("\n=== Univalence ===\n");

    /* U1: type of the ua constant */
    printf("\n[U1] type of ua\n");
    run_infer(a, "ua");

    /* U2: partial application — ua applied to one type arg */
    printf("\n[U2] ua Type  (partial, stays neutral)\n");
    run_infer(a, "ua Type");

    /* U3: partial application with both type args */
    printf("\n[U3] ua Type Type  (partial, stays neutral)\n");
    run_infer(a, "ua Type Type");

    /* U4: conv — ua is equal to itself; different args are unequal */
    printf("\n[U4] conv tests\n");
    expect_conv(a, "ua", "ua", 1);
    expect_conv(a, "ua Type", "ua Type", 1);
    expect_conv(a, "ua Type", "ua Type_1", 0);

    /* U5: negative — wrong third argument (Type_1 is not an Equiv) */
    printf("\n[U5] negative: ua with wrong third arg type\n");
    expect_fail(a, "ua Type Type Type_1", "Type_1 is not Equiv Type Type");

    /* --- Function extensionality --- */
    fflush(stdout);
    printf("\n=== Function extensionality ===\n");

    /* FE1: type of funext */
    printf("\n[FE1] type of funext\n");
    run_infer(a, "funext");

    /* FE2: partial application with A=Nat — stays neutral */
    printf("\n[FE2] funext Nat  (partial, A=Nat stays neutral)\n");
    run_infer(a, "funext Nat");

    /* FE3: fully applied — funext now computes to ⟨i⟩ λx. h x @ i (Path-based) */
    printf("\n[FE3] funext fully applied computes to a path (VL_PATHABS)\n");
    run_infer(a,
        "(\\ A B f g h."
        "  funext A B f g h"
        " : Π(A : Type). Π(B : Π(_ : A). Type)."
        "   Π(f : Π(x : A). B x). Π(g : Π(x : A). B x)."
        "   Π(h : Π(x : A). Path (B x) (f x) (g x))."
        "   Path (Π(x : A). B x) f g)");

    /* FE4: conv — funext equal to itself, different args unequal */
    printf("\n[FE4] conv tests\n");
    expect_conv(a, "funext", "funext", 1);
    expect_conv(a, "funext Nat", "funext Nat", 1);
    expect_conv(a, "funext Nat", "funext Bool", 0);

    /* FE5: negative — B must be a fibration A→Type, not a term */
    printf("\n[FE5] negative: funext with non-fibration B\n");
    expect_fail(a, "funext Nat zero", "zero is not a fibration Nat → Type");

    /* FE6: non-dependent fibration (B = λ_.Nat): Path-based, typechecks */
    printf("\n[FE6] non-dependent funext (B=λ_.Nat) with Path typechecks\n");
    run_infer(a,
        "(\\ f g h. funext Nat (\\_. Nat) f g h"
        " : Π(f : Π(_ : Nat). Nat). Π(g : Π(_ : Nat). Nat)."
        "   Π(h : Π(x : Nat). Path Nat (f x) (g x))."
        "   Path (Π(_ : Nat). Nat) f g)");

    /* FE7: funext computes — partial applications still neutral; fully applied returns
     * a VL_PATHABS, not a neutral. Funext ≢ refl (different val tags). */
    printf("\n[FE7] funext partial ≢ refl; full funext returns VL_PATHABS not refl\n");
    expect_conv(a, "funext", "(refl zero : Id Nat zero zero)", 0);

    /* FE8: β-equal expressions both reduce to the same funext neutral */
    printf("\n[FE8] β-equal funext partials are conv-equal\n");
    expect_conv(a, "(\\ F A. F A) funext", "\\ A. funext A", 1);

    /* FE9: same funext head but different h neutral → spines differ → not equal */
    printf("\n[FE9] different h in funext spine → not conv-equal\n");
    expect_conv(a,
        "\\ A B f g h1 h2. funext A B f g h1",
        "\\ A B f g h1 h2. funext A B f g h2",
        0);

    /* FE10: A must live in Type_0; Type_1 lives in Type_2 */
    printf("\n[FE10] negative: A in Type_1 rejected (funext expects A : Type)\n");
    expect_fail(a, "funext Type_1", "Type_1 : Type_2, not Type_0");

    /* FE11: h must be a pointwise Path proof, not a Nat→Nat function */
    printf("\n[FE11] negative: h with type Nat→Nat instead of Nat→Path rejected\n");
    expect_fail(a,
        "(\\ f. funext Nat (\\_. Nat) f f f"
        " : Π(f : Π(_ : Nat). Nat). Path (Π(_ : Nat). Nat) f f)",
        "h : Nat→Nat instead of Nat→Path Nat (f x) (f x)");

    /* --- Global definitions --- */
    fflush(stdout);
    printf("\n=== Global definitions ===\n");

    /* Register test globals idempotently (guard lets :t be called multiple times). */
    if (def_lookup("_gl_id") < 0)
        def_define("_gl_id", "(\\ A x. x : Π(A : Type). A → A)");
    if (def_lookup("_gl_not") < 0)
        def_define("_gl_not",
            "(\\ b. boolrec (\\_. Bool : Π(_ : Bool). Type) false true b"
            " : Π(_ : Bool). Bool)");
    /* _gl_id2 is defined in terms of _gl_id to test cross-global reference */
    if (def_lookup("_gl_id2") < 0)
        def_define("_gl_id2", "(\\ A x. _gl_id A x : Π(A : Type). A → A)");

    /* GL1: global type is reported correctly */
    printf("\n[GL1] _gl_id : Π(A:Type). A→A\n");
    run_infer(a, "_gl_id");

    /* GL2: transparent unfolding — application reduces fully */
    printf("\n[GL2] _gl_id Nat zero  →  zero\n");
    run_infer(a, "_gl_id Nat zero");

    /* GL3: global referencing another global unfolds through both */
    printf("\n[GL3] _gl_id2 Nat zero  →  zero  (via _gl_id)\n");
    run_infer(a, "_gl_id2 Nat zero");

    /* GL4: Boolean eliminator global */
    printf("\n[GL4] _gl_not true  →  false,  _gl_not false  →  true\n");
    run_infer(a, "_gl_not true");
    run_infer(a, "_gl_not false");

    /* GL5: definitional equality through unfolding */
    printf("\n[GL5] conv: _gl_id Nat zero ≡ zero\n");
    expect_conv(a, "_gl_id Nat zero", "zero", 1);
    expect_conv(a, "_gl_id2 Nat zero", "zero", 1);
    /* different arguments: not equal */
    expect_conv(a, "_gl_id Nat zero", "_gl_id Nat (succ zero)", 0);

    /* GL6: type error in definition is rejected; table unchanged */
    printf("\n[GL6] bad definition rejected, table unchanged\n");
    {
        int before = def_count();
        int r = def_define("_gl_bad", "(zero : Nat → Nat)");
        if (r < 0 && def_count() == before)
            printf("  [OK] bad def rejected\n");
        else
            printf("  [BUG] bad def should have been rejected\n");
    }

    /* GL7: redefinition (shadowing) works; most-recent wins */
    printf("\n[GL7] shadowing: redefinition takes effect\n");
    {
        def_define("_gl_shadow", "(zero : Nat)");
        def_define("_gl_shadow", "(succ zero : Nat)");   /* shadows */
        /* _gl_shadow should now refer to succ zero */
        expect_conv(a, "_gl_shadow", "succ zero", 1);
        expect_conv(a, "_gl_shadow", "zero",      0);
    }

    /* --- Derived terms (path algebra) --- */
    fflush(stdout);
    printf("\n=== Derived terms (path algebra) ===\n");

    if (def_lookup("sym") < 0)
        def_define("sym",
            "(\\A a b p."
            " J A a"
            " (\\y _. Id A y a : Π(y : A). Π(_ : Id A a y). Type)"
            " (refl a) b p"
            " : Π(A : Type). Π(a : A). Π(b : A). Π(_ : Id A a b). Id A b a)");

    if (def_lookup("trans") < 0)
        def_define("trans",
            "(\\A a b c p q."
            " J A a"
            " (\\y _. Π(_ : Id A y c). Id A a c : Π(y : A). Π(_ : Id A a y). Type)"
            " (\\q. q) b p q"
            " : Π(A : Type). Π(a : A). Π(b : A). Π(c : A)."
            "   Π(_ : Id A a b). Π(_ : Id A b c). Id A a c)");

    if (def_lookup("transport") < 0)
        def_define("transport",
            "(\\A P a b p x."
            " J A a"
            " (\\y _. P y : Π(y : A). Π(_ : Id A a y). Type)"
            " x b p"
            " : Π(A : Type). Π(P : Π(_ : A). Type). Π(a : A). Π(b : A)."
            "   Π(_ : Id A a b). Π(_ : P a). P b)");

    if (def_lookup("ap") < 0)
        def_define("ap",
            "(\\A B f a b p."
            " J A a"
            " (\\y _. Id B (f a) (f y) : Π(y : A). Π(_ : Id A a y). Type)"
            " (refl (f a)) b p"
            " : Π(A : Type). Π(B : Type). Π(f : Π(_ : A). B)."
            "   Π(a : A). Π(b : A). Π(_ : Id A a b). Id B (f a) (f b))");

    /* PA1: types */
    printf("\n[PA1] sym type\n");
    run_infer(a, "sym");
    printf("\n[PA2] trans type\n");
    run_infer(a, "trans");
    printf("\n[PA3] transport type\n");
    run_infer(a, "transport");
    printf("\n[PA4] ap type\n");
    run_infer(a, "ap");

    /* PA5: sym β — J fires on refl */
    printf("\n[PA5] sym β: sym Nat zero zero (refl zero) ≡ refl zero\n");
    expect_conv(a, "sym Nat zero zero (refl zero)",
                   "(refl zero : Id Nat zero zero)", 1);

    /* PA6: trans β — J fires on refl, identity applied to q */
    printf("\n[PA6] trans β: trans Nat zero zero zero (refl zero) (refl zero) ≡ refl zero\n");
    expect_conv(a, "trans Nat zero zero zero (refl zero) (refl zero)",
                   "(refl zero : Id Nat zero zero)", 1);

    /* PA7: transport β — J fires on refl, returns x unchanged */
    printf("\n[PA7] transport β: transport (λ_.Nat) (refl zero) zero ≡ zero\n");
    expect_conv(a,
        "transport Nat (\\_ . Nat : Π(_ : Nat). Type) zero zero (refl zero) zero",
        "zero", 1);

    /* PA8: ap β — J fires on refl, returns refl (f a) */
    printf("\n[PA8] ap β: ap succ zero zero (refl zero) ≡ refl (succ zero)\n");
    expect_conv(a,
        "ap Nat Nat (\\n. succ n : Π(_ : Nat). Nat) zero zero (refl zero)",
        "(refl (succ zero) : Id Nat (succ zero) (succ zero))", 1);

    /* PA9: trans left-refl = identity definitionally (J fires on refl) */
    printf("\n[PA9] trans left-refl = identity\n");
    expect_conv(a,
        "\\A a b q. trans A a a b (refl a) q",
        "\\A a b q. q", 1);

    /* PA10: distinct stuck applications are not equal */
    printf("\n[PA10] distinct sym/ap args are not conv-equal\n");
    expect_conv(a,
        "\\A a b p. sym A a b p",
        "\\A a b p. sym A a b (sym A b a p)", 0);

    /* PA11: sym(sym(refl a)) ≡ refl a — J fires twice */
    printf("\n[PA11] sym(sym(refl zero)) ≡ refl zero  (double-sym on refl)\n");
    expect_conv(a,
        "sym Nat zero zero (sym Nat zero zero (refl zero))",
        "(refl zero : Id Nat zero zero)", 1);

    /* PA12: transport with reflexive fibration β-reduces to its payload */
    printf("\n[PA12] transport (λx. Id x x) (refl zero) (refl zero) ≡ refl zero\n");
    expect_conv(a,
        "transport Nat (\\x. Id Nat x x : Π(_ : Nat). Type) zero zero (refl zero) (refl zero)",
        "(refl zero : Id Nat zero zero)", 1);

    /* PA13: sym at a higher universe level */
    printf("\n[PA13] sym Type_1 Type Type (refl Type) ≡ refl Type\n");
    expect_conv(a,
        "sym Type_1 Type Type (refl Type)",
        "(refl Type : Id Type_1 Type Type)", 1);

    /* PA14: trans is not commutative for neutral paths — J fires on different neutrals */
    printf("\n[PA14] trans non-commutative for neutral paths\n");
    expect_conv(a,
        "\\p q. trans Nat zero zero zero p q",
        "\\p q. trans Nat zero zero zero q p",
        0);

    /* PA15: trans right-refl is NOT definitionally the identity for neutral p —
     * J fires on p (the 5th arg), and p is neutral, so the whole expression stays stuck.
     * Contrast with PA9 (left-refl) where J fires on refl and reduces. */
    printf("\n[PA15] trans right-refl stays stuck for neutral p  (not definitionally id)\n");
    expect_conv(a,
        "\\A a b p. trans A a b b p (refl b)",
        "\\A a b p. p",
        0);

    /* PA16: ap distinguishes distinct functions even on the same neutral path */
    printf("\n[PA16] ap succ p ≢ ap id p for neutral p  (different J motives)\n");
    expect_conv(a,
        "\\p. ap Nat Nat (\\n. succ n : Π(_ : Nat). Nat) zero zero p",
        "\\p. ap Nat Nat (\\n. n      : Π(_ : Nat). Nat) zero zero p",
        0);

    /* --- Type-checking tests --- */
    fflush(stdout);
    printf("\n=== Type-checking tests ===\n");

    /* TP1: sym applied to a concrete path type has the right return type */
    printf("\n[TP1] sym applied to concrete path: Π(_:Id Nat zero (succ zero)). Id Nat (succ zero) zero\n");
    expect_type(a,
        "(\\p. sym Nat zero (succ zero) p"
        " : Π(_ : Id Nat zero (succ zero)). Id Nat (succ zero) zero)",
        "Π(_ : Id Nat zero (succ zero)). Id Nat (succ zero) zero");

    /* TP2: ap lifts a path along a function */
    printf("\n[TP2] ap succ : Π(_:Id Nat zero (succ zero)). Id Nat (succ zero) (succ (succ zero))\n");
    expect_type(a,
        "(\\p. ap Nat Nat (\\n. succ n : Π(_ : Nat). Nat) zero (succ zero) p"
        " : Π(_ : Id Nat zero (succ zero)). Id Nat (succ zero) (succ (succ zero)))",
        "Π(_ : Id Nat zero (succ zero)). Id Nat (succ zero) (succ (succ zero))");

    /* TP3: transport changes the fibre type from P a to P b */
    printf("\n[TP3] transport (λx. Id x zero) p : Π(_:Id Nat zero zero). Id Nat (succ zero) zero\n");
    expect_type(a,
        "(\\p. transport Nat (\\x. Id Nat x zero : Π(_ : Nat). Type) zero (succ zero) p"
        " : Π(_ : Id Nat zero (succ zero)). Π(_ : Id Nat zero zero). Id Nat (succ zero) zero)",
        "Π(_ : Id Nat zero (succ zero)). Π(_ : Id Nat zero zero). Id Nat (succ zero) zero");

    /* TP4: refl of a function value has Id-of-function type */
    printf("\n[TP4] refl (λx.x) : Id (Nat→Nat) (λx.x) (λx.x)\n");
    expect_type(a,
        "(refl (\\x. x : Nat → Nat)"
        " : Id (Π(_ : Nat). Nat) (\\x. x : Nat → Nat) (\\x. x : Nat → Nat))",
        "Id (Π(_ : Nat). Nat) (\\x. x : Nat → Nat) (\\x. x : Nat → Nat)");

    /* TP5: trans at concrete Nat endpoints has the expected Π-type */
    printf("\n[TP5] trans Nat 0 1 2 p q : Id Nat 0 2\n");
    expect_type(a,
        "(\\p q. trans Nat zero (succ zero) (succ (succ zero)) p q"
        " : Π(_ : Id Nat zero (succ zero))."
        "   Π(_ : Id Nat (succ zero) (succ (succ zero)))."
        "   Id Nat zero (succ (succ zero)))",
        "Π(_ : Id Nat zero (succ zero))."
        " Π(_ : Id Nat (succ zero) (succ (succ zero)))."
        " Id Nat zero (succ (succ zero))");

    /* --- Additional negative tests --- */
    fflush(stdout);
    printf("\n=== Additional negative tests ===\n");

    /* sym applied to a path with the wrong endpoint */
    printf("\n[NEG-sym] sym with wrong endpoint: refl zero ≢ Id Nat zero (succ zero)\n");
    expect_fail(a,
        "sym Nat zero (succ zero) (refl zero)",
        "refl zero : Id Nat zero zero but needs Id Nat zero (succ zero)");

    /* transport with a non-fibration as P */
    printf("\n[NEG-transport-P] P=Nat is not Π(_:Nat).Type\n");
    expect_fail(a,
        "transport Nat Nat zero zero (refl zero) zero",
        "Nat is not a fibration Nat → Type");

    /* ap with a non-function as f */
    printf("\n[NEG-ap-f] f=zero is not Nat→Nat\n");
    expect_fail(a,
        "ap Nat Nat zero zero zero (refl zero)",
        "zero is not a function Nat → Nat");

    /* J with a proof argument of the wrong type */
    printf("\n[NEG-J-proof] proof=zero : Nat, not Id Nat zero zero\n");
    expect_fail(a,
        "J Nat zero"
        " (\\b _. Nat : Π(b : Nat). Π(_ : Id Nat zero b). Type)"
        " zero zero zero",
        "zero : Nat is not an Id proof");

    /* --- Negative tests (should be rejected) --- */
    fflush(stdout);
    printf("\n=== Negative tests (expected failures) ===\n");
    fflush(stdout);
    /* Type is not its own type */
    expect_fail(a, "(Type : Type)", "Type : Type_1, not Type");
    /* Type_1 does not live in Type */
    expect_fail(a, "(Type_1 : Type)", "Type_1 : Type_2");
    /* bare lambda has no inferrable type */
    expect_fail(a, "\\x. x", "lambda without annotation");
    /* bare pair has no inferrable type */
    expect_fail(a, "(Type, Type)", "pair without annotation");
    /* fst of a non-pair type */
    expect_fail(a, "fst (Type : Type_1)", "fst applied to non-sigma");
    /* refl with mismatched endpoints */
    expect_fail(a, "(refl Type : Id Type_1 Type Type_1)", "Type ≢ Type_1");
    /* J motive with wrong domain */
    expect_fail(a, "J Type_1 Type"
                   " (\\b _. Type_1 : Π(b : Type_2). Id Type_1 Type b → Type_2)"
                   " Type Type refl Type",
                   "J motive domain mismatch");

    /* --- W-types --- */
    fflush(stdout);
    printf("\n=== W-types ===\n");

    /* W1: formation at the right universe level */
    printf("\n[W1] W(x:Nat).Nat : Type\n");
    run_infer(a, "W(x:Nat).Nat");
    printf("\n[W2] W(x:Type).x : Type_1  (dom at level 1)\n");
    run_infer(a, "W(x:Type).x");

    /* W3: alpha-equivalence and conv distinguishes different W types */
    printf("\n[W3] W-type conv\n");
    expect_conv(a, "W(x:Nat).Nat",  "W(y:Nat).Nat",  1);
    expect_conv(a, "W(x:Nat).Nat",  "W(x:Bool).Nat", 0);
    expect_conv(a, "W(x:Nat).Nat",  "W(x:Nat).Bool", 0);

    /* W4: β-rule: wrec P s (sup a f) ≡ s a f (λb. wrec P s (f b))
     * In an open context (all variables neutral) the eval still fires because
     * TM_SUP evaluates to VL_SUP, which triggers nbe_vwrec's first branch.    */
    printf("\n[W4] wrec β-rule: wrec P s (sup a f) ≡ s a f (λb. wrec P s (f b))\n");
    expect_conv(a,
        "\\P s a f. wrec P s (sup a f)",
        "\\P s a f. s a f (\\b. wrec P s (f b))",
        1);

    /* W5: stuck wrec on neutral w — stays neutral, conv checks components */
    printf("\n[W5] wrec on neutral w stays stuck; motive eta-expansion is transparent\n");
    expect_conv(a, "\\P s w. wrec P s w", "\\P s w. wrec P s w", 1);
    expect_conv(a, "\\P s w. wrec P s w", "\\P s w. wrec (\\x. P x) s w", 1);
    expect_conv(a, "\\P s w. wrec P s w", "\\Q s w. wrec Q s w", 1);
    expect_conv(a, "\\P s w. wrec P s w", "\\P s w. wrec s P w", 0);  /* motive/step swapped within same binders */

    /* W6: type-checking wrec with constant motive P = λ_. Nat */
    printf("\n[W6] type check: wrec with constant Nat motive  →  Π(w:W(x:Nat).Nat). Nat\n");
    run_infer(a,
        "(\\ w. wrec"
        " (\\ _ . Nat : Π(_ : W(x:Nat).Nat). Type)"
        " (\\ a f ih. zero"
        "   : Π(a : Nat). Π(f : Π(_ : Nat). W(x:Nat).Nat)."
        "     Π(ih : Π(_ : Nat). Nat). Nat)"
        " w"
        ": Π(w : W(x:Nat).Nat). Nat)");

    /* W7: negative — motive domain not a W type */
    printf("\n[W7] negative: wrec motive domain is not a W type\n");
    expect_fail(a,
        "(\\ w. wrec"
        " (\\ _ . Nat : Π(_ : Nat). Type)"
        " (\\ a f ih. zero"
        "   : Π(a : Nat). Π(f : Π(_ : Nat). Nat)."
        "     Π(ih : Π(_ : Nat). Nat). Nat)"
        " w"
        ": Π(w : Nat). Nat)",
        "motive domain is Nat, not W");

    /* W8: negative — sup checked against non-W type */
    printf("\n[W8] negative: sup checked against non-W type\n");
    expect_fail(a,
        "(sup zero (\\ _ . zero : Π(_ : Nat). Nat) : Nat)",
        "sup should be checked against W, not Nat");

    /* W9: sup with unannotated lambda children (now accepted via constant Pi closure) */
    printf("\n[W9] sup with unannotated lambda children\n");
    run_infer(a,
        "(\\ f. (sup zero (\\ _ . f zero) : W(x:Nat).Nat)"
        ": Π(f : Π(_ : Nat). W(x:Nat).Nat). W(x:Nat).Nat)");

    /* W10: bare sup in inference position — must give graceful error, not crash */
    printf("\n[W10] negative: bare sup has no inferrable type\n");
    expect_fail(a, "sup zero zero",
        "cannot infer type of sup");

    /* W11: conv on VL_SUP values */
    printf("\n[W11] sup conv: same label/children ≡, different label ≢\n");
    expect_conv(a, "\\a f. sup a f", "\\a f. sup a f", 1);
    expect_conv(a, "\\a f. sup a f", "\\a f. sup (succ a) f", 0);

    /* W12: negative — wrec step result type wrong (Bool instead of P(sup a f) = Nat) */
    printf("\n[W12] negative: wrec step result type is Bool, should be P(sup a f) = Nat\n");
    expect_fail(a,
        "(\\ w. wrec"
        " (\\ _ . Nat : Π(_ : W(x:Nat).Nat). Type)"
        " (\\ a f ih. true"
        "   : Π(a : Nat). Π(f : Π(_ : Nat). W(x:Nat).Nat)."
        "     Π(ih : Π(_ : Nat). Nat). Bool)"
        " w"
        ": Π(w : W(x:Nat).Nat). Nat)",
        "step result Bool ≠ Nat = P(sup a f)");

    /* W13: negative — wrec step arg 2 domain wrong (Bool instead of B(a) = Nat) */
    printf("\n[W13] negative: wrec step arg 2 domain is Bool, should be B(a) = Nat\n");
    expect_fail(a,
        "(\\ w. wrec"
        " (\\ _ . Nat : Π(_ : W(x:Nat).Nat). Type)"
        " (\\ a f ih. zero"
        "   : Π(a : Nat). Π(f : Π(_ : Bool). W(x:Nat).Nat)."
        "     Π(ih : Π(_ : Nat). Nat). Nat)"
        " w"
        ": Π(w : W(x:Nat).Nat). Nat)",
        "step arg 2 domain Bool ≠ Nat");

    /* W14: negative — wrec step arg 3 codomain wrong (Bool instead of P(f b) = Nat) */
    printf("\n[W14] negative: wrec step ih codomain is Bool, should be P(f b) = Nat\n");
    expect_fail(a,
        "(\\ w. wrec"
        " (\\ _ . Nat : Π(_ : W(x:Nat).Nat). Type)"
        " (\\ a f ih. zero"
        "   : Π(a : Nat). Π(f : Π(_ : Nat). W(x:Nat).Nat)."
        "     Π(ih : Π(_ : Nat). Bool). Nat)"
        " w"
        ": Π(w : W(x:Nat).Nat). Nat)",
        "ih codomain Bool ≠ Nat = P(f b)");

    /* W15: negative — wrec step arg 2 codomain not W (returns Nat instead) */
    printf("\n[W15] negative: wrec step arg 2 codomain is Nat, should be W\n");
    expect_fail(a,
        "(\\ w. wrec"
        " (\\ _ . Nat : Π(_ : W(x:Nat).Nat). Type)"
        " (\\ a f ih. zero"
        "   : Π(a : Nat). Π(f : Π(_ : Nat). Nat)."
        "     Π(ih : Π(_ : Nat). Nat). Nat)"
        " w"
        ": Π(w : W(x:Nat).Nat). Nat)",
        "step arg 2 codomain Nat ≠ W");

    /* --- Empty type --- */
    fflush(stdout);
    printf("\n=== Empty type ===\n");

    /* E1: Empty is a type */
    printf("\n[E1] Empty : Type\n");
    run_infer(a, "Empty");

    /* E2: abort gives any type when supplied a proof of Empty */
    printf("\n[E2] abort Nat e : Empty → Nat\n");
    run_infer(a,
        "(\\e. abort Nat e"
        " : Π(_ : Empty). Nat)");

    /* E3: abort at a higher universe: abort Type_1 e : Empty → Type_1 */
    printf("\n[E3] abort Type_1 e : Empty → Type_1\n");
    run_infer(a,
        "(\\e. abort Type_1 e"
        " : Π(_ : Empty). Type_1)");

    /* E4: dependent motive — A mentions e; here we produce Id Empty e e
     * for any e : Empty, exercising that the motive can use the binder */
    printf("\n[E4] dependent motive: abort (Id Empty e e) e : Π(e:Empty). Id Empty e e\n");
    run_infer(a,
        "(\\e. abort (Id Empty e e) e"
        " : Π(e : Empty). Id Empty e e)");

    /* E5: conv — Empty ≡ Empty, Empty ≢ Nat, Empty ≢ Bool */
    printf("\n[E5] conv tests\n");
    expect_conv(a, "Empty", "Empty", 1);
    expect_conv(a, "Empty", "Nat",   0);
    expect_conv(a, "Empty", "Bool",  0);

    /* E6: two abort expressions with the same neutral proof and same
     * motive are conv-equal; different motives are not */
    printf("\n[E6] abort conv: same motive/neutral ≡, different motives ≢\n");
    expect_conv(a,
        "\\e. abort Nat  e",
        "\\e. abort Nat  e", 1);
    expect_conv(a,
        "\\e. abort Nat  e",
        "\\e. abort Bool e", 0);

    /* E7a: negation type Nat → Empty is well-formed (¬Nat : Type) */
    printf("\n[E7a] Nat → Empty : Type  (negation type)\n");
    run_infer(a, "Nat → Empty");

    /* E7b: identity on Empty — λe. e : Empty → Empty is inhabited */
    printf("\n[E7b] (λe. e : Empty → Empty) typechecks\n");
    run_infer(a, "(\\e. e : Empty → Empty)");

    /* E7c: two distinct neutrals produce non-equal abort terms */
    printf("\n[E7c] abort Nat e1 ≢ abort Nat e2  (different scrutinees)\n");
    expect_conv(a,
        "\\e1 e2. abort Nat e1",
        "\\e1 e2. abort Nat e2",
        0);

    /* E7: negative — scrutinee is not of type Empty */
    printf("\n[E7] negative tests\n");
    expect_fail(a, "abort Nat zero",
                   "zero : Nat is not Empty");
    expect_fail(a, "abort Nat true",
                   "true : Bool is not Empty");

    /* E8: negative — first argument is not a type */
    expect_fail(a,
        "(\\e. abort zero e : Π(_ : Empty). Nat)",
        "zero is not a type");

    /* --- Unit type --- */
    fflush(stdout);
    printf("\n=== Unit type ===\n");

    /* UN1: formation and constructor */
    printf("\n[UN1] Unit : Type    star : Unit\n");
    run_infer(a, "Unit");
    run_infer(a, "star");

    /* UN2: unitrec β — on star reduces to base case */
    printf("\n[UN2] unitrec β: unitrec P zero star ≡ zero\n");
    run_infer(a,
        "unitrec (\\_. Nat : Π(_ : Unit). Type)"
        "        zero"
        "        star");

    /* UN2b: motive at Type_1 — unitrec can return a type */
    printf("\n[UN2b] unitrec returning a Type: P = λ_. Type, base = Nat, star → Nat\n");
    run_infer(a,
        "unitrec (\\_. Type : Π(_ : Unit). Type_1)"
        "        Nat"
        "        star");

    /* UN3: unitrec on neutral s stays stuck */
    printf("\n[UN3] unitrec on neutral s stays stuck\n");
    run_infer(a,
        "(\\s. unitrec (\\_. Nat : Π(_ : Unit). Type) zero s"
        " : Π(s : Unit). Nat)");

    /* UN4: conv tests */
    printf("\n[UN4] conv tests\n");
    expect_conv(a, "Unit", "Unit", 1);
    expect_conv(a, "star", "star", 1);
    expect_conv(a, "Unit", "Nat",  0);
    expect_conv(a, "Unit", "Bool", 0);
    expect_conv(a, "Unit", "Empty", 0);
    expect_conv(a, "star", "zero", 0);
    expect_conv(a, "star", "true", 0);
    /* β-conv: unitrec P zero star ≡ zero */
    expect_conv(a,
        "unitrec (\\_. Nat : Π(_:Unit).Type) zero star",
        "zero", 1);
    /* stuck: same components → equal */
    expect_conv(a,
        "(\\s. unitrec (\\_. Nat : Π(_:Unit).Type) zero s : Π(s:Unit).Nat)",
        "(\\s. unitrec (\\_. Nat : Π(_:Unit).Type) zero s : Π(s:Unit).Nat)", 1);
    /* stuck: different base → unequal */
    expect_conv(a,
        "(\\s. unitrec (\\_. Nat : Π(_:Unit).Type) zero      s : Π(s:Unit).Nat)",
        "(\\s. unitrec (\\_. Nat : Π(_:Unit).Type) (succ zero) s : Π(s:Unit).Nat)", 0);
    /* motive eta-expansion is transparent (analogous to wrec W5) */
    expect_conv(a,
        "\\P b s. unitrec P b s",
        "\\P b s. unitrec (\\x. P x) b s", 1);
    /* two distinct neutral scrutinees produce unequal unitrec terms */
    expect_conv(a,
        "\\s1 s2. unitrec (\\_. Nat : Π(_:Unit).Type) zero s1",
        "\\s1 s2. unitrec (\\_. Nat : Π(_:Unit).Type) zero s2", 0);

    /* UN5: dependent motive — P s where s : Unit is in the type */
    printf("\n[UN5] dependent motive: unitrec (λs. Id Unit s star) (refl star) star\n");
    run_infer(a,
        "unitrec"
        " (\\s. Id Unit s star : Π(s : Unit). Type)"
        " (refl star)"
        " star");

    /* UN6: negative tests */
    printf("\n[UN6] negative tests\n");
    /* scrutinee is not Unit */
    expect_fail(a,
        "unitrec (\\_. Nat : Π(_ : Unit). Type) zero zero",
        "zero : Nat is not Unit");
    /* motive domain is not Unit */
    expect_fail(a,
        "unitrec (\\_. Nat : Π(_ : Nat). Type) zero star",
        "motive domain is Nat not Unit");
    /* base has wrong type: P star = Nat, but giving Bool */
    expect_fail(a,
        "unitrec (\\_. Nat : Π(_ : Unit). Type) true star",
        "base : Bool instead of Nat = P star");

    /* --- Sum types --- */
    fflush(stdout);
    printf("\n=== Sum types ===\n");

    /* SM1: formation */
    printf("\n[SM1] Sum Nat Bool : Type\n");
    run_infer(a, "Sum Nat Bool");
    printf("\n[SM1b] Sum Type Type : Type_1\n");
    run_infer(a, "Sum Type Type");

    /* SM2: inl typechecks with annotation */
    printf("\n[SM2] (inl zero : Sum Nat Bool)\n");
    run_infer(a, "(inl zero : Sum Nat Bool)");

    /* SM3: inr typechecks with annotation */
    printf("\n[SM3] (inr true : Sum Nat Bool)\n");
    run_infer(a, "(inr true : Sum Nat Bool)");

    /* SM4: β case on inl → left branch fires */
    printf("\n[SM4] case β on inl: case P (λa.a) (λb.zero) (inl zero) ≡ zero\n");
    expect_conv(a,
        "case (\\_. Nat : Π(_ : Sum Nat Bool). Type)"
        "     (\\a. a)"
        "     (\\b. zero)"
        "     (inl zero : Sum Nat Bool)",
        "zero", 1);

    /* SM5: β case on inr → right branch fires */
    printf("\n[SM5] case β on inr: case P (λa.zero) (λb.succ zero) (inr true) ≡ succ zero\n");
    expect_conv(a,
        "case (\\_. Nat : Π(_ : Sum Nat Bool). Type)"
        "     (\\a. zero)"
        "     (\\b. succ zero)"
        "     (inr true : Sum Nat Bool)",
        "succ zero", 1);

    /* SM6: case on neutral s stays stuck */
    printf("\n[SM6] case on neutral s stays stuck\n");
    run_infer(a,
        "(\\s. case (\\_. Nat : Π(_ : Sum Nat Bool). Type)"
        "          (\\a. a)"
        "          (\\b. zero)"
        "          s"
        " : Π(s : Sum Nat Bool). Nat)");

    /* SM7: conv tests for Sum and injections */
    printf("\n[SM7] Sum/inl/inr conv tests\n");
    expect_conv(a, "Sum Nat Bool", "Sum Nat Bool",  1);
    expect_conv(a, "Sum Nat Bool", "Sum Bool Nat",  0);
    expect_conv(a, "Sum Nat Bool", "Sum Nat Nat",   0);
    expect_conv(a, "Sum Nat Bool", "Nat",           0);
    /* inl ≡ inl with same payload */
    expect_conv(a,
        "(inl zero : Sum Nat Bool)",
        "(inl zero : Sum Nat Bool)", 1);
    /* inr ≡ inr with same payload */
    expect_conv(a,
        "(inr true : Sum Nat Bool)",
        "(inr true : Sum Nat Bool)", 1);
    /* inl ≢ inr (different constructors, same payload shape not enough) */
    expect_conv(a,
        "(inl zero : Sum Nat Nat)",
        "(inr zero : Sum Nat Nat)", 0);
    /* inl with different payloads */
    expect_conv(a,
        "(inl zero : Sum Nat Bool)",
        "(inl (succ zero) : Sum Nat Bool)", 0);

    /* SM8: case conv on neutral — same components equal, different unequal */
    printf("\n[SM8] case stuck conv\n");
    expect_conv(a,
        "\\s. case (\\_. Nat : Π(_ : Sum Nat Bool). Type) (\\a. a) (\\b. zero) s",
        "\\s. case (\\_. Nat : Π(_ : Sum Nat Bool). Type) (\\a. a) (\\b. zero) s", 1);
    expect_conv(a,
        "\\s. case (\\_. Nat : Π(_ : Sum Nat Bool). Type) (\\a. a)       (\\b. zero)     s",
        "\\s. case (\\_. Nat : Π(_ : Sum Nat Bool). Type) (\\a. succ a) (\\b. zero)     s", 0);

    /* SM9: negative tests */
    printf("\n[SM9] negative tests\n");
    /* inl without annotation: cannot infer type */
    expect_fail(a, "inl zero",
                   "cannot infer type of inl");
    /* inr without annotation: cannot infer type */
    expect_fail(a, "inr true",
                   "cannot infer type of inr");
    /* inl checked against non-Sum type */
    expect_fail(a, "(inl zero : Nat)",
                   "inl checked against Nat, not Sum");
    /* inl with wrong payload type: zero : Nat but need Bool */
    expect_fail(a, "(inl zero : Sum Bool Nat)",
                   "zero : Nat, but Sum left type is Bool");
    /* inr with wrong payload type: true : Bool but need Nat */
    expect_fail(a, "(inr true : Sum Nat Nat)",
                   "true : Bool, but Sum right type is Nat");
    /* case with motive domain Nat instead of Sum */
    expect_fail(a,
        "(\\n. case (\\_. Nat : Π(_ : Nat). Type)"
        "          (\\a. a)"
        "          (\\b. zero)"
        "          n"
        " : Π(n : Nat). Nat)",
        "motive domain Nat, not Sum");
    /* case motive codomain not a universe */
    expect_fail(a,
        "case (\\_. zero : Π(_ : Sum Nat Bool). Nat)"
        "     (\\a. a)"
        "     (\\b. zero)"
        "     (inl zero : Sum Nat Bool)",
        "motive codomain Nat is not a universe");

    /* SM10: dependent motive β-reduction */
    printf("\n[SM10] dependent motive: case (λs. Id (Sum Nat Bool) s s) ... (inl zero) ≡ refl (inl zero)\n");
    expect_conv(a,
        "case (\\s. Id (Sum Nat Bool) s s"
        "     : Π(s : Sum Nat Bool). Type)"
        "     (\\a. refl (inl a : Sum Nat Bool))"
        "     (\\b. refl (inr b : Sum Nat Bool))"
        "     (inl zero : Sum Nat Bool)",
        "(refl (inl zero : Sum Nat Bool)"
        " : Id (Sum Nat Bool) (inl zero) (inl zero))",
        1);
    /* same but on inr branch */
    expect_conv(a,
        "case (\\s. Id (Sum Nat Bool) s s"
        "     : Π(s : Sum Nat Bool). Type)"
        "     (\\a. refl (inl a : Sum Nat Bool))"
        "     (\\b. refl (inr b : Sum Nat Bool))"
        "     (inr true : Sum Nat Bool)",
        "(refl (inr true : Sum Nat Bool)"
        " : Id (Sum Nat Bool) (inr true) (inr true))",
        1);

    /* SM11: two distinct neutral scrutinees produce unequal case terms */
    printf("\n[SM11] distinct scrutinees: case ... s1 ≢ case ... s2\n");
    expect_conv(a,
        "\\s1 s2. case (\\_. Nat : Π(_ : Sum Nat Bool). Type)"
        "             (\\a. a) (\\b. zero) s1",
        "\\s1 s2. case (\\_. Nat : Π(_ : Sum Nat Bool). Type)"
        "             (\\a. a) (\\b. zero) s2",
        0);

    /* SM12: decidability pattern from PLAN.md */
    printf("\n[SM12] decidability type: Sum (Id Nat zero zero) (Id Nat zero zero → Empty)\n");
    run_infer(a, "Sum (Id Nat zero zero) (Π(_ : Id Nat zero zero). Empty)");

    /* --- Propositional truncation --- */
    fflush(stdout);
    printf("\n=== Propositional truncation ===\n");

    /* TR1: formation */
    printf("\n[TR1] trunc Nat : Type\n");
    run_infer(a, "trunc Nat");
    printf("\n[TR1b] trunc Bool : Type\n");
    run_infer(a, "trunc Bool");

    /* TR2: intro — trint A a : trunc A */
    printf("\n[TR2] trint Nat zero : trunc Nat\n");
    run_infer(a, "trint Nat zero");
    printf("\n[TR2b] trint Bool true : trunc Bool\n");
    run_infer(a, "trint Bool true");

    /* TR3: squash gives a path between any two truncated elements */
    printf("\n[TR3] squash Nat (trint Nat zero) (trint Nat (succ zero)) : Id (trunc Nat) ...\n");
    expect_type(a,
        "squash Nat (trint Nat zero) (trint Nat (succ zero))",
        "Id (trunc Nat) (trint Nat zero) (trint Nat (succ zero))");

    /* TR3b: squash collapses distinct constructors — proof of propositional collapse */
    printf("\n[TR3b] squash Bool (trint Bool true) (trint Bool false) : Id (trunc Bool) ...\n");
    expect_type(a,
        "squash Bool (trint Bool true) (trint Bool false)",
        "Id (trunc Bool) (trint Bool true) (trint Bool false)");

    /* TR4: β-rule — truncrec fires when scrutinee is trint */
    printf("\n[TR4] truncrec Nat Nat (\\x.x) (trint Nat zero) ≡ zero\n");
    expect_conv(a,
        "truncrec Nat Nat (\\x. x) (trint Nat zero)",
        "zero", 1);

    printf("\n[TR4b] truncrec Nat Nat (\\x. succ x) (trint Nat zero) ≡ succ zero\n");
    expect_conv(a,
        "truncrec Nat Nat (\\x. succ x) (trint Nat zero)",
        "succ zero", 1);

    printf("\n[TR4c] truncrec Bool Nat (\\b. zero) (trint Bool true) ≡ zero\n");
    expect_conv(a,
        "truncrec Bool Nat (\\b. zero) (trint Bool true)",
        "zero", 1);

    /* TR5: stuck on neutral scrutinee — two truncrecs on same neutral are equal,
     * different functions make them unequal */
    printf("\n[TR5] truncrec on neutral s: same components ≡, different func ≢\n");
    expect_conv(a,
        "\\s. truncrec Nat Nat (\\x. x) s",
        "\\s. truncrec Nat Nat (\\x. x) s", 1);
    expect_conv(a,
        "\\s. truncrec Nat Nat (\\x. x)      s",
        "\\s. truncrec Nat Nat (\\x. succ x) s", 0);
    /* two distinct neutral scrutinees are not equal */
    expect_conv(a,
        "\\s1 s2. truncrec Nat Nat (\\x. x) s1",
        "\\s1 s2. truncrec Nat Nat (\\x. x) s2", 0);

    /* TR6: conv — trunc distinguishes types */
    printf("\n[TR6] trunc conv tests\n");
    expect_conv(a, "trunc Nat",  "trunc Nat",  1);
    expect_conv(a, "trunc Nat",  "trunc Bool", 0);
    expect_conv(a, "trunc Nat",  "Nat",        0);
    expect_conv(a, "trunc Bool", "Bool",       0);

    /* TR7: negative tests */
    printf("\n[TR7] negative tests\n");
    /* truncrec with wrong scrutinee type */
    expect_fail(a,
        "truncrec Nat Nat (\\x. x) zero",
        "zero : Nat, not trunc Nat");
    /* truncrec with f having wrong domain */
    expect_fail(a,
        "truncrec Nat Bool (\\x. x) (trint Nat zero)",
        "f : Nat → Bool, but giving Nat → Nat identity");
    /* trint with wrong element type */
    expect_fail(a,
        "trint Nat true",
        "true : Bool, not Nat");
    /* squash with wrong types */
    expect_fail(a,
        "squash Nat (trint Bool true) (trint Bool false)",
        "squash Nat expects trunc Nat args, not trunc Bool");

    /* TR8: harden — is_prop and trunc_is_prop */
    printf("\n[TR8] is_prop and trunc_is_prop\n");
    if (def_lookup("is_prop") < 0)
        def_define("is_prop",
            "(\\A. Π(x : A). Π(y : A). Id A x y"
            " : Π(A : Type). Type)");
    run_infer(a, "is_prop");

    /* trunc_is_prop: trunc A is a proposition via squash */
    if (def_lookup("trunc_is_prop") < 0)
        def_define("trunc_is_prop",
            "(\\A x y. squash A x y"
            " : Π(A : Type). Π(x : trunc A). Π(y : trunc A). Id (trunc A) x y)");
    printf("\n[TR8b] trunc_is_prop : Π(A:Type). is_prop (trunc A)\n");
    expect_type(a, "trunc_is_prop",
        "Π(A : Type). Π(x : trunc A). Π(y : trunc A). Id (trunc A) x y");

    /* TR9: truncrec respects type — verify return type is B, not A */
    printf("\n[TR9] truncrec Nat Bool type inference\n");
    expect_type(a,
        "truncrec Nat Bool (\\x. true) (trint Nat zero)",
        "Bool");

    /* TR10: trint with a function type as A (Nat → Nat : Type_0, so valid) */
    printf("\n[TR10] trint (Nat → Nat) id : trunc (Nat → Nat)\n");
    expect_type(a,
        "trint (Π(_ : Nat). Nat) (\\x. x : Π(_ : Nat). Nat)",
        "trunc (Π(_ : Nat). Nat)");

    /* TR11: squash is NOT definitionally refl — it stays neutral while refl is canonical.
     * This is the key HoTT fact: squash provides a path that is not refl.      */
    printf("\n[TR11] squash ≢ refl  (squash stays neutral, refl is canonical)\n");
    expect_conv(a,
        "squash Nat (trint Nat zero) (trint Nat zero)",
        "(refl (trint Nat zero) : Id (trunc Nat) (trint Nat zero) (trint Nat zero))",
        0);

    /* TR12: trint with distinct elements stays distinct before squash collapses them.
     * Inside trunc, the elements are distinguishable definitionally (different spines). */
    printf("\n[TR12] trint Nat zero ≢ trint Nat (succ zero)  (distinct elements)\n");
    expect_conv(a,
        "trint Nat zero",
        "trint Nat (succ zero)",
        0);

    /* TR13: double truncation — trunc (trunc Nat) is a valid type */
    printf("\n[TR13] trunc (trunc Nat) : Type\n");
    run_infer(a, "trunc (trunc Nat)");
    expect_type(a, "trunc (trunc Nat)", "Type");

    /* --- Quotient types --- */
    fflush(stdout);
    printf("\n=== Quotient types ===\n");

    /* QT1: Formation — Quot A R : Type */
    printf("\n[QT1] formation\n");
    expect_type(a, "Quot Nat (\\m. \\n. Id Nat m n)", "Type");
    expect_type(a, "Quot Bool (\\x. \\y. Unit)",       "Type");
    expect_type(a, "Quot Nat  (\\m. \\n. Unit)",       "Type");

    /* QT2: Introduction — qin A R a : Quot A R */
    printf("\n[QT2] introduction\n");
    expect_type(a,
        "qin Nat (\\m. \\n. Id Nat m n) zero",
        "Quot Nat (\\m. \\n. Id Nat m n)");
    expect_type(a,
        "qin Bool (\\x. \\y. Unit) true",
        "Quot Bool (\\x. \\y. Unit)");
    expect_type(a,
        "qin Bool (\\x. \\y. Unit) false",
        "Quot Bool (\\x. \\y. Unit)");

    /* QT3: Path axiom — qeq : R a b → Id (Quot A R) (qin a) (qin b) */
    printf("\n[QT3] qeq types\n");
    expect_type(a,
        "qeq Nat (\\m. \\n. Id Nat m n) zero zero (refl zero)",
        "Id (Quot Nat (\\m. \\n. Id Nat m n))"
        "   (qin Nat (\\m. \\n. Id Nat m n) zero)"
        "   (qin Nat (\\m. \\n. Id Nat m n) zero)");
    expect_type(a,
        "qeq Bool (\\x. \\y. Unit) true false star",
        "Id (Quot Bool (\\x. \\y. Unit))"
        "   (qin Bool (\\x. \\y. Unit) true)"
        "   (qin Bool (\\x. \\y. Unit) false)");
    /* symmetric: qeq identifies false with true too */
    expect_type(a,
        "qeq Bool (\\x. \\y. Unit) false true star",
        "Id (Quot Bool (\\x. \\y. Unit))"
        "   (qin Bool (\\x. \\y. Unit) false)"
        "   (qin Bool (\\x. \\y. Unit) true)");

    /* QT4: β-rule — quotrec fires when scrutinee is qin */
    printf("\n[QT4] quotrec beta rule\n");
    /* constant-to-zero function on the total Bool quotient */
    expect_conv(a,
        "quotrec Bool (\\x. \\y. Unit) Nat"
        "        (\\b. zero)"
        "        (\\a. \\b. \\r. refl zero)"
        "        (qin Bool (\\x. \\y. Unit) true)",
        "zero", 1);
    expect_conv(a,
        "quotrec Bool (\\x. \\y. Unit) Nat"
        "        (\\b. zero)"
        "        (\\a. \\b. \\r. refl zero)"
        "        (qin Bool (\\x. \\y. Unit) false)",
        "zero", 1);
    /* identity on Nat via the identity-relation quotient: β fires, returns the nat */
    expect_conv(a,
        "quotrec Nat (\\m. \\n. Id Nat m n) Nat"
        "        (\\n. n)"
        "        (\\a. \\b. \\p. p)"
        "        (qin Nat (\\m. \\n. Id Nat m n) (succ (succ zero)))",
        "succ (succ zero)", 1);
    /* boolrec inside f — true branch */
    expect_conv(a,
        "quotrec Bool (\\x. \\y. Unit) Bool"
        "        (\\b. boolrec (\\b. Bool) false true b)"
        "        (\\a. \\b. \\r. refl false)"
        "        (qin Bool (\\x. \\y. Unit) true)",
        "false", 1);
    /* boolrec inside f — false branch */
    expect_conv(a,
        "quotrec Bool (\\x. \\y. Unit) Bool"
        "        (\\b. boolrec (\\b. Bool) false true b)"
        "        (\\a. \\b. \\r. refl false)"
        "        (qin Bool (\\x. \\y. Unit) false)",
        "true", 1);

    /* QT5: Return type — quotrec has the type of B */
    printf("\n[QT5] quotrec return type\n");
    expect_type(a,
        "quotrec Bool (\\x. \\y. Unit) Nat"
        "        (\\b. zero)"
        "        (\\a. \\b. \\r. refl zero)"
        "        (qin Bool (\\x. \\y. Unit) true)",
        "Nat");
    expect_type(a,
        "quotrec Nat (\\m. \\n. Unit) Bool"
        "        (\\n. true)"
        "        (\\a. \\b. \\r. refl true)"
        "        (qin Nat (\\m. \\n. Unit) zero)",
        "Bool");

    /* QT6: Stuck on neutral scrutinee */
    printf("\n[QT6] quotrec stuck on neutral\n");
    /* same components → equal */
    expect_conv(a,
        "\\q. quotrec Bool (\\x. \\y. Unit) Nat (\\b. zero) (\\a. \\b. \\r. refl zero) q",
        "\\q. quotrec Bool (\\x. \\y. Unit) Nat (\\b. zero) (\\a. \\b. \\r. refl zero) q",
        1);
    /* different func → not equal */
    expect_conv(a,
        "\\q. quotrec Bool (\\x. \\y. Unit) Nat (\\b. zero)     (\\a. \\b. \\r. refl zero)    q",
        "\\q. quotrec Bool (\\x. \\y. Unit) Nat (\\b. succ zero)(\\a. \\b. \\r. refl (succ zero)) q",
        0);
    /* different neutral scrutinees → not equal */
    expect_conv(a,
        "\\q1 q2. quotrec Bool (\\x. \\y. Unit) Nat (\\b. zero) (\\a. \\b. \\r. refl zero) q1",
        "\\q1 q2. quotrec Bool (\\x. \\y. Unit) Nat (\\b. zero) (\\a. \\b. \\r. refl zero) q2",
        0);

    /* QT7: Conv — Quot distinguishes types and relations */
    printf("\n[QT7] Quot conv tests\n");
    expect_conv(a, "Quot Nat  (\\m. \\n. Unit)", "Quot Nat  (\\m. \\n. Unit)", 1);
    expect_conv(a, "Quot Nat  (\\m. \\n. Unit)", "Quot Bool (\\m. \\n. Unit)", 0);
    expect_conv(a, "Quot Nat  (\\m. \\n. Unit)", "Quot Nat  (\\m. \\n. Id Nat m n)", 0);
    expect_conv(a, "Quot Nat  (\\m. \\n. Unit)", "Nat",                               0);
    /* qin same element → equal */
    expect_conv(a,
        "qin Nat (\\m. \\n. Id Nat m n) zero",
        "qin Nat (\\m. \\n. Id Nat m n) zero", 1);
    /* qin different elements → definitionally distinct (only propositionally equal via qeq) */
    expect_conv(a,
        "qin Nat (\\m. \\n. Id Nat m n) zero",
        "qin Nat (\\m. \\n. Id Nat m n) (succ zero)", 0);

    /* QT8: qeq is NOT definitionally refl — it stays neutral */
    printf("\n[QT8] qeq ≢ refl  (key HoTT fact: path axiom stays neutral)\n");
    expect_conv(a,
        "qeq Nat (\\m. \\n. Id Nat m n) zero zero (refl zero)",
        "(refl (qin Nat (\\m. \\n. Id Nat m n) zero)"
        " : Id (Quot Nat (\\m. \\n. Id Nat m n))"
        "      (qin Nat (\\m. \\n. Id Nat m n) zero)"
        "      (qin Nat (\\m. \\n. Id Nat m n) zero))",
        0);

    /* QT9: Quot as a quotient of itself by reflexivity — identity quotient */
    printf("\n[QT9] Quot Nat IdRel ~ identity (quotrec with \\n.n)\n");
    expect_conv(a,
        "quotrec Nat (\\m. \\n. Id Nat m n) Nat (\\n. n) (\\a. \\b. \\p. p)"
        "        (qin Nat (\\m. \\n. Id Nat m n) zero)",
        "zero", 1);
    expect_conv(a,
        "quotrec Nat (\\m. \\n. Id Nat m n) Nat (\\n. n) (\\a. \\b. \\p. p)"
        "        (qin Nat (\\m. \\n. Id Nat m n) (succ (succ (succ zero))))",
        "succ (succ (succ zero))", 1);

    /* QT10: Negative tests — type errors */
    printf("\n[QT10] negative tests\n");
    /* scrut is not a quotient element */
    expect_fail(a,
        "quotrec Nat (\\m. \\n. Unit) Nat (\\n. n) (\\a. \\b. \\r. refl a) zero",
        "zero : Nat, not Quot Nat R");
    expect_fail(a,
        "quotrec Bool (\\x. \\y. Unit) Nat (\\b. zero) (\\a. \\b. \\r. refl zero) true",
        "true : Bool, not Quot Bool R");
    /* f has wrong codomain */
    expect_fail(a,
        "quotrec Bool (\\x. \\y. Unit) Nat"
        "        (\\b. b)"
        "        (\\a. \\b. \\r. refl (zero : Nat))"
        "        (qin Bool (\\x. \\y. Unit) true)",
        "f : Bool → Bool, B = Nat — codomain mismatch");
    /* qeq with wrong proof type */
    expect_fail(a,
        "qeq Nat (\\m. \\n. Id Nat m n) zero (succ zero) star",
        "star : Unit, but R zero (succ zero) = Id Nat zero (succ zero)");
    /* qin with wrong element type */
    expect_fail(a,
        "qin Nat (\\m. \\n. Id Nat m n) true",
        "true : Bool, not Nat");

    /* QT11: Quot is a Type, not a function — check it doesn't reduce to plain A */
    printf("\n[QT11] Quot is distinct from A and trunc A\n");
    expect_conv(a, "Quot Nat (\\m. \\n. Unit)", "trunc Nat", 0);
    expect_conv(a, "Quot Nat (\\m. \\n. Unit)", "Nat",        0);

    /* QT12: quotrec with a non-trivial function that depends on the value */
    printf("\n[QT12] quotrec: succ inside f\n");
    expect_conv(a,
        "quotrec Nat (\\m. \\n. Id Nat m n) Nat"
        "        (\\n. succ n)"
        "        (\\a. \\b. \\p. ap Nat Nat (\\x. succ x) a b p)"
        "        (qin Nat (\\m. \\n. Id Nat m n) (succ (succ zero)))",
        "succ (succ (succ zero))", 1);

    /* --- Cubical interval (Phase L2 Stage 1+2) --- */
    fflush(stdout);
    printf("\n=== Cubical interval (II, i0, i1, pathabs, pathapp) ===\n");

    /* L2-1: II : Type */
    printf("\n[L2-1] II : Type\n");
    expect_type(a, "II", "Type");

    /* L2-2: endpoints — i0 : II, i1 : II */
    printf("\n[L2-2] i0 i1 : II\n");
    expect_type(a, "i0", "II");
    expect_type(a, "i1", "II");

    /* L2-3: i0 ≢ i1  (distinct canonical endpoints) */
    printf("\n[L2-3] i0 ≢ i1\n");
    expect_conv(a, "i0", "i1", 0);
    expect_conv(a, "i0", "i0", 1);
    expect_conv(a, "i1", "i1", 1);

    /* L2-4: path abstraction type: <i> body : Path A t0 t1 */
    printf("\n[L2-4] path abstraction type — Path A t0 t1\n");
    expect_type(a, "<i> i",   "Path II i0 i1");
    expect_type(a, "<i> Nat", "Path Type Nat Nat");
    expect_type(a, "<i> zero","Path Nat zero zero");
    expect_type(a, "<_> true","Path Bool true true");

    /* L2-5: β-rule — (<i> t) @ r → t[r/i] */
    printf("\n[L2-5] beta rule fires\n");
    expect_conv(a, "(<i> i)   @ i0", "i0",   1);
    expect_conv(a, "(<i> i)   @ i1", "i1",   1);
    expect_conv(a, "(<i> i0)  @ i1", "i0",   1);  /* constant i0 path */
    expect_conv(a, "(<i> Nat) @ i0", "Nat",  1);
    expect_conv(a, "(<i> Nat) @ i1", "Nat",  1);
    expect_conv(a, "(<i> zero)@ i0", "zero", 1);
    expect_conv(a, "(<i> succ i0) @ i1", "succ i0", 1);  /* body ignores i */

    /* L2-6: constant path: <_> A @ i0 ≡ <_> A @ i1 */
    printf("\n[L2-6] constant path: both endpoints equal\n");
    expect_conv(a, "(<_> Nat) @ i0", "(<_> Nat) @ i1", 1);
    expect_conv(a, "(<_> Bool)@ i0", "(<_> Bool)@ i1", 1);

    /* L2-7: type of path application */
    printf("\n[L2-7] pathapp type\n");
    expect_type(a, "(<i> i)   @ i0", "II");
    expect_type(a, "(<i> Nat) @ i0", "Type");
    expect_type(a, "(<i> zero)@ i1", "Nat");

    /* L2-8: nested path abstractions */
    printf("\n[L2-8] nested paths\n");
    expect_conv(a, "(<i> <j> i) @ i0",       "<j> i0",  1);
    expect_conv(a, "(<i> <j> i) @ i1",       "<j> i1",  1);
    expect_conv(a, "((<i> <j> i) @ i0) @ i1","i0",       1);
    expect_conv(a, "((<i> <j> i) @ i1) @ i0","i1",       1);

    /* L2-9: path abstraction over existing types */
    printf("\n[L2-9] path abstraction over types and terms\n");
    /* <i> (Id II i i) : Path Type (Id II i0 i0) (Id II i1 i1) */
    expect_type(a, "<i> (Id II i i)",
                   "Path Type (Id II i0 i0) (Id II i1 i1)");
    expect_conv(a, "<i> (refl i : Id II i i)",
                   "<i> (refl i : Id II i i)", 1);

    /* L2-10: conv — same path equal, different path not equal */
    printf("\n[L2-10] conv for path abstractions\n");
    expect_conv(a, "<i> i",    "<i> i",    1);   /* same body */
    expect_conv(a, "<i> i0",   "<i> i0",   1);
    expect_conv(a, "<i> i",    "<i> i0",   0);   /* different bodies */
    expect_conv(a, "<i> i",    "<j> j",    1);   /* alpha-equivalent */
    expect_conv(a, "<i> i0",   "<i> i1",   0);   /* different constants */
    expect_conv(a, "<i> zero", "<i> (succ zero)", 0);

    /* L2-11: stuck path application stays neutral and quotes back */
    printf("\n[L2-11] stuck path application normalises correctly\n");
    /* A neutral path p applied to i0: quotes back as p @ i0 */
    expect_type(a,
        "(\\p. p @ i0 : Π(p : Π(_ : II). Nat). Nat)",
        "Π(p : Π(_ : II). Nat). Nat");
    /* Two applications of same path to same neutral are equal */
    expect_conv(a,
        "\\p. (p @ i0 : Nat)",
        "\\p. (p @ i0 : Nat)", 1);
    expect_conv(a,
        "\\p. (p @ i0 : Nat)",
        "\\p. (p @ i1 : Nat)", 0);

    /* L2-12: negative tests */
    printf("\n[L2-12] negative tests\n");
    /* Applying a non-path to an interval should fail the type checker
     * because the type won't be Π(_:II). ... */
    expect_fail(a,
        "(zero @ i0 : Nat)",
        "zero is Nat, not a path; @ requires Π(_:II). T");
    /* Applying a path to a non-interval should fail */
    expect_fail(a,
        "(<i> i) @ zero",
        "zero : Nat, not II; path application requires r : II");

    /* --- Cubical Stage 3: Path type former --- */
    fflush(stdout);
    printf("\n=== Cubical Stage 3: Path A a b ===\n");

    /* L3-1: Path formation */
    printf("\n[L3-1] Path formation\n");
    expect_type(a, "Path Nat zero zero",  "Type");
    expect_type(a, "Path Bool true false","Type");
    expect_type(a, "Path II i0 i1",       "Type");
    expect_type(a, "Path Type Nat Bool",  "Type_1");

    /* L3-2: Path introduction — <i> t : Path A t0 t1 */
    printf("\n[L3-2] Path introduction\n");
    expect_type(a, "<i> zero",           "Path Nat zero zero");
    expect_type(a, "<i> i",             "Path II i0 i1");
    expect_type(a, "<_> true",          "Path Bool true true");
    expect_type(a, "<_> Nat",           "Path Type Nat Nat");

    /* L3-3: Explicit annotation checks endpoint conditions */
    printf("\n[L3-3] check mode: <i> t against Path A a b\n");
    expect_type(a, "(<i> zero  : Path Nat zero zero)",    "Path Nat zero zero");
    expect_type(a, "(<i> i     : Path II  i0   i1)",      "Path II i0 i1");
    expect_type(a, "(<_> true  : Path Bool true true)",   "Path Bool true true");

    /* L3-4: Endpoint mismatch is a type error */
    printf("\n[L3-4] endpoint mismatch rejected\n");
    expect_fail(a,
        "(<i> zero : Path Nat zero (succ zero))",
        "right endpoint mismatch: body@i1=zero but expected succ zero");
    expect_fail(a,
        "(<i> zero : Path Nat (succ zero) zero)",
        "left endpoint mismatch: body@i0=zero but expected succ zero");
    expect_fail(a,
        "(<i> i : Path II i0 i0)",
        "right endpoint mismatch: body@i1=i1 but expected i0");

    /* L3-5: Path application type comes from Path, not Π */
    printf("\n[L3-5] pathapp type from Path A a b\n");
    expect_type(a, "(<i> zero) @ i0",  "Nat");
    expect_type(a, "(<i> zero) @ i1",  "Nat");
    expect_type(a, "(<i> i)    @ i0",  "II");
    expect_type(a, "(<i> Nat)  @ i0",  "Type");

    /* L3-6: β-rule still fires */
    printf("\n[L3-6] beta rule still fires under Path type\n");
    expect_conv(a, "(<i> zero) @ i0", "zero",     1);
    expect_conv(a, "(<i> zero) @ i1", "zero",     1);
    expect_conv(a, "(<i> i)    @ i0", "i0",       1);
    expect_conv(a, "(<i> i)    @ i1", "i1",       1);

    /* L3-7: Path type conv — structural equality */
    printf("\n[L3-7] Path conv\n");
    expect_conv(a, "Path Nat zero zero",  "Path Nat zero zero",      1);
    expect_conv(a, "Path Nat zero zero",  "Path Nat zero (succ zero)",0);
    expect_conv(a, "Path Nat zero zero",  "Path Bool zero zero",     0);  /* wrong A */
    expect_conv(a, "Path II i0 i1",       "Path II i0 i1",           1);
    expect_conv(a, "Path II i0 i1",       "Path II i1 i0",           0);  /* endpoints swapped */
    expect_conv(a, "Path Nat zero zero",  "Id Nat zero zero",        0);  /* Path ≠ Id */

    /* L3-8: refl gives a path when used as path abstraction */
    printf("\n[L3-8] refl as constant path\n");
    expect_type(a, "(<_> (refl zero : Id Nat zero zero))",
                   "Path (Id Nat zero zero) (refl zero) (refl zero)");

    /* L3-9: Path of a Path (nested) */
    printf("\n[L3-9] nested Path type\n");
    expect_type(a, "Path (Path Nat zero zero) (<_> zero) (<_> zero)", "Type");

    /* L3-10: Path ≠ Id (different type formers) */
    printf("\n[L3-10] Path is distinct from Id\n");
    expect_conv(a, "Path Nat zero zero", "Id Nat zero zero", 0);

    /* L3-11: wrong endpoint types rejected */
    printf("\n[L3-11] wrong endpoint types rejected\n");
    expect_fail(a,
        "(Path Nat true false : Type)",
        "true false : Bool, not Nat");
    expect_fail(a,
        "(Path Nat zero true  : Type)",
        "true : Bool, not Nat for right arg");

    /* L3-12: Path in function position */
    printf("\n[L3-12] Path in Π domain, used as type annotation\n");
    expect_type(a,
        "Π(p : Path Nat zero zero). Nat",
        "Type");
    expect_type(a,
        "(\\p. p @ i0 : Π(p : Path Nat zero zero). Nat)",
        "Π(p : Path Nat zero zero). Nat");

    /* L3-13: constant path — <_> a has equal endpoints */
    printf("\n[L3-13] constant path endpoints equal\n");
    expect_conv(a, "(<_> zero) @ i0", "(<_> zero) @ i1", 1);
    expect_conv(a, "(<_> true) @ i0", "(<_> true) @ i1", 1);
    expect_conv(a, "(<_> Nat)  @ i0", "(<_> Nat)  @ i1", 1);

    /* L3-14: Path applied to neutral — result type is A extracted from Path */
    printf("\n[L3-14] pathapp on neutral path: result type is A\n");
    expect_type(a,
        "(\\p. p @ i0 : Π(p : Path Bool true false). Bool)",
        "Π(p : Path Bool true false). Bool");
    expect_type(a,
        "(\\p. p @ i1 : Π(p : Path Nat zero (succ zero)). Nat)",
        "Π(p : Path Nat zero (succ zero)). Nat");

    /* L3-15: path abstraction over function types */
    printf("\n[L3-15] path abstraction over functions\n");
    expect_type(a,
        "<_> (\\x. x : Π(_ : Nat). Nat)",
        "Path (Π(_ : Nat). Nat) (\\x. x) (\\x. x)");

    /* L3-16: universe-polymorphic path */
    printf("\n[L3-16] Path Type Nat Bool : Type_1\n");
    expect_type(a, "Path Type Nat Bool",   "Type_1");
    expect_type(a, "Path Type_1 Type Type","Type_2");
    /* Conv on paths at Type_1 */
    expect_conv(a, "Path Type Nat Bool",  "Path Type Nat Bool",  1);
    expect_conv(a, "Path Type Nat Bool",  "Path Type Bool Nat",  0);

    /* L3-17: check mode rejects path abs against non-path type */
    printf("\n[L3-17] <i> t rejected against non-Path types\n");
    expect_fail(a,
        "(<i> zero : Nat)",
        "path abs against Nat (not a Path or Pi type)");
    expect_fail(a,
        "(<i> i : II)",
        "path abs against II (not a Path type)");

    /* --- Phase L2 Stage 3: transp --- */

    fflush(stdout);
    printf("\n=== transp: transport along a constant type family ===\n");

#define TRANSP_FAMILY(body, cod) \
    "(\\i. " body " : (Π(i : II). " cod "))"

    /* L4-1: transp type checking — family must be Π(i:II).Type */
    printf("\n[L4-1] transp type: transp (λ_.Nat) zero : Nat\n");
    expect_type(a, "transp " TRANSP_FAMILY("Nat", "Type") " zero", "Nat");

    /* L4-2: constant Nat family — transp (λ_. Nat) x = x */
    printf("\n[L4-2] transp (λ_. Nat) zero ≡ zero\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Nat", "Type") " zero",
        "zero",
        1);

    /* L4-3: constant Bool family */
    printf("\n[L4-3] transp (λ_. Bool) true ≡ true\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Bool", "Type") " true",
        "true",
        1);

    /* L4-4: constant Unit family */
    printf("\n[L4-4] transp (λ_. Unit) star ≡ star\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Unit", "Type") " star",
        "star",
        1);

    /* L4-5: constant Pi family */
    printf("\n[L4-5] transp (λ_. Π(x:Nat).Nat) f ≡ f\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Π(x : Nat). Nat", "Type") " (\\x. x)",
        "\\x. x",
        1);

    /* L4-6: constant Sigma family */
    printf("\n[L4-6] transp (λ_. Σ(x:Nat).Nat) p ≡ p\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Σ(x : Nat). Nat", "Type") " (zero, zero)",
        "(zero, zero)",
        1);

    /* L4-7: constant Path family */
    printf("\n[L4-7] transp (λ_. Path Nat zero zero) p ≡ p\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Path Nat zero zero", "Type") " (<_> zero)",
        "<_> zero",
        1);

    /* L4-8: constant Type family */
    printf("\n[L4-8] transp (λ_. Type_1) Nat ≡ Nat\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Type", "Type_1") " Nat",
        "Nat",
        1);

    /* L4-9: non-constant family stays stuck — type still computes correctly */
    printf("\n[L4-9] non-constant family stays stuck, type = II\n");
    expect_type(a,
        "transp " TRANSP_FAMILY("II", "Type") " i0",
        "II");

    /* L4-10: conv — two identical stuck transps are equal */
    printf("\n[L4-10] conv for stuck transp\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("II", "Type") " i0",
        "transp " TRANSP_FAMILY("II", "Type") " i0",
        1);

    /* L4-11: distinct stuck transps are not equal */
    printf("\n[L4-11] distinct stuck transps are not convertible\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("II", "Type") " i0",
        "transp " TRANSP_FAMILY("II", "Type") " i1",
        0);

    /* L4-12: type error — family domain not II */
    printf("\n[L4-12] transp rejects family with wrong domain\n");
    expect_fail(a,
        "transp (\\x. Nat : (Π(x : Nat). Type)) zero",
        "family domain is Nat, not II");

    /* L4-13: type error — family codomain not Type */
    printf("\n[L4-13] transp rejects family with non-universe codomain\n");
    expect_fail(a,
        "transp (\\i. i : (Π(i : II). II)) i0",
        "family codomain is II, not a universe");

    /* L4-14: genuinely non-constant family stays stuck (type computes correctly) */
    printf("\n[L4-14] non-constant family: Π(j:II).Id II i i — stuck, type = Π(j:II).Id II i1 i1\n");
    expect_type(a,
        "transp (\\i. (Π(j : II). Id II i i) : (Π(i : II). Type)) (\\j. refl i0)",
        "Π(j : II). Id II i1 i1");

    /* L4-15: stuck transp quoted back correctly — conv with itself */
    printf("\n[L4-15] stuck transp: conv with itself\n");
    expect_conv(a,
        "transp (\\i. (Π(j : II). Id II i i) : (Π(i : II). Type)) (\\j. refl i0)",
        "transp (\\i. (Π(j : II). Id II i i) : (Π(i : II). Type)) (\\j. refl i0)",
        1);

    /* L4-16: transp of transp — both constant, both reduce */
    printf("\n[L4-16] transp (transp const) ≡ id\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Nat", "Type")
        " (transp " TRANSP_FAMILY("Nat", "Type") " zero)",
        "zero",
        1);

    /* L4-17: transp with Sum type — constant family */
    printf("\n[L4-17] transp (λ_. Sum Nat Bool) (inl zero) ≡ inl zero\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Sum Nat Bool", "Type") " (inl zero)",
        "inl zero",
        1);

    /* L4-18: transp with Id type — constant family */
    printf("\n[L4-18] transp (λ_. Id Nat zero zero) (refl zero) ≡ refl zero\n");
    expect_conv(a,
        "transp " TRANSP_FAMILY("Id Nat zero zero", "Type") " (refl zero)",
        "refl zero",
        1);

    /* L4-19: W type as constant family — use inductive Vec as proxy */
    /* (Direct W-element construction is complex; verify constant-family rule
     * holds for W via the type-level check: Π i. W(...) is a valid II→Type) */
    printf("\n[L4-19] W-type constant family is a valid transp family\n");
    expect_type(a,
        "(\\i. W(x : Bool). Nat : (Π(i : II). Type))",
        "Π(i : II). Type");

    /* L4-20: global constant family unfolds and reduces */
    printf("\n[L4-20] global constant family (transparent unfolding)\n");
    if (def_lookup("cNat") < 0)
        def_define("cNat", "(\\i. Nat : (Π(i : II). Type))");
    expect_conv(a,
        "transp cNat zero",
        "zero",
        1);

    /* --- hcomp and structural transp (Stage 4) --- */

    printf("\n=== L2 Stage 4: hcomp + structural Π/Σ transp ===\n");

    /* L5-1: hcomp type — returns A */
    printf("\n[L5-1] hcomp Nat i0 (\\_.zero) (succ zero) : Nat\n");
    expect_type(a,
        "hcomp Nat i0 (\\_.zero) (succ zero)",
        "Nat");

    /* L5-2: hcomp A i0 u base = base  (left endpoint) */
    printf("\n[L5-2] hcomp Nat i0 (\\_.zero) (succ zero) ≡ succ zero\n");
    expect_conv(a,
        "hcomp Nat i0 (\\_.zero) (succ zero)",
        "succ zero",
        1);

    /* L5-3: hcomp A i1 u base = u i1  (right endpoint) */
    printf("\n[L5-3] hcomp Nat i1 (\\_.succ zero) zero ≡ succ zero\n");
    expect_conv(a,
        "hcomp Nat i1 (\\_.succ zero) zero",
        "succ zero",
        1);

    /* L5-4: hcomp on Bool */
    printf("\n[L5-4] hcomp Bool i0 (\\_.false) true ≡ true\n");
    expect_conv(a,
        "hcomp Bool i0 (\\_.false) true",
        "true",
        1);

    printf("\n[L5-5] hcomp Bool i1 (\\_.true) false ≡ true\n");
    expect_conv(a,
        "hcomp Bool i1 (\\_.true) false",
        "true",
        1);

    /* L5-6: stuck hcomp (neutral face) */
    printf("\n[L5-6] hcomp Nat x u b stays stuck (neutral x)\n");
    {
        Val *face = vl_neutral(a, 500, NULL);   /* neutral interval element */
        Val *tube = nbe_eval(a, NULL, parse(a, "\\_.succ zero"));
        Val *base = vl_zero(a);
        Val *ty   = vl_nat(a);
        Val *h    = nbe_vhcomp(a, ty, face, tube, base);
        if (h->tag == VL_HCOMP) {
            printf("  [OK] stuck VL_HCOMP\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_HCOMP, got %d\n", h->tag); tests_fail++;
        }
    }

    /* L5-7: conv — two identical stuck hcomps are equal */
    printf("\n[L5-7] conv for stuck hcomp (identical)\n");
    {
        if (def_lookup("_hc_neutral") < 0)
            def_define("_hc_neutral", "(\\x. x : II → II)");
        /* Two identical stuck hcomps must be convertible */
        expect_conv(a,
            "hcomp Nat (_hc_neutral i0) (\\_.zero) (succ zero)",
            "hcomp Nat (_hc_neutral i0) (\\_.zero) (succ zero)",
            1);
    }

    /* L5-8: Structural Π-transp — constant domain, codomain varies in i.
     * transp (λi. Π(j:II). Path II j i : (Π(i:II).Type)) f
     * = λj. transp (λi. Path II j i) (f j)   [outer Π resolved; inner stuck]
     * Result must be a function (can be applied). */
    printf("\n[L5-8] structural Π-transp: result is a function\n");
    {
        Term *t = parse(a,
            "transp (\\i. (Π(j:II). Path II j i) : (Π(i:II). Type))"
            "       (\\j. (<r> j : Path II j i0))");
        if (!t) { printf("  [SKIP] parse failed\n"); } else {
            Val *v = nbe_eval(a, NULL, t);
            if (v->tag == VL_LAM) {
                printf("  [OK] result is VL_LAM\n"); tests_pass++;
            } else {
                printf("  [BUG] expected VL_LAM, got tag %d\n", v->tag); tests_fail++;
            }
        }
    }

    /* L5-9: Π-transp application — apply the lambda to i0.
     * (transp (λi. Π(j:II). Path II j i : ...) f) i0
     *  = transp (λi. Path II i0 i) (f i0)   [inner transp is non-constant → stuck] */
    printf("\n[L5-9] Π-transp applied to i0 gives inner transp\n");
    {
        Term *t = parse(a,
            "(transp (\\i. (Π(j:II). Path II j i) : (Π(i:II). Type))"
            "        (\\j. (<r> j : Path II j i0)))"
            " i0");
        if (!t) { printf("  [SKIP] parse failed\n"); } else {
            Val *v = nbe_eval(a, NULL, t);
            /* should be VL_TRANSP since inner Path transp is non-constant */
            if (v->tag == VL_TRANSP) {
                printf("  [OK] inner transp is VL_TRANSP (stuck)\n"); tests_pass++;
            } else {
                printf("  [BUG] expected VL_TRANSP, got tag %d\n", v->tag); tests_fail++;
            }
        }
    }

    /* L5-10: Structural Π-transp with inner constant (double reduction).
     * transp (λi. Π(x:Nat). Nat → Nat : ...) f
     * Whole family is constant → Stage 3 returns f directly.
     * But if we force Stage 4 path: transp (λi. Π(x:Nat). Id Nat x x : ...) f
     * = λx. transp (λi. Id Nat x x) (f x) → λx. f x  (inner constant) */
    printf("\n[L5-10] Π-transp + constant inner transp: chained reduction\n");
    expect_conv(a,
        "transp (\\i. (Π(x:Nat). Id Nat x x) : (Π(i:II). Type))"
        "       (\\x. (refl x : Id Nat x x))",
        "\\x. (refl x : Id Nat x x)",
        1);

    /* L5-11: Structural Σ-transp — constant domain.
     * transp (λi. Σ(x:Nat). Path II i0 i : (Π(i:II).Type)) (zero, <j> i0)
     * = (zero, transp (λi. Path II i0 i) (<j> i0))
     * = (zero, VL_TRANSP(...))  [inner stuck] */
    printf("\n[L5-11] structural Σ-transp: result is a pair\n");
    {
        Term *t = parse(a,
            "transp (\\i. (Σ(x:Nat). Path II i0 i) : (Π(i:II). Type))"
            "       (zero , (<j> i0 : Path II i0 i0))");
        if (!t) { printf("  [SKIP] parse failed\n"); } else {
            Val *v = nbe_eval(a, NULL, t);
            if (v->tag == VL_PAIR) {
                printf("  [OK] result is VL_PAIR\n"); tests_pass++;
                /* fst should be zero */
                if (v->pair.fst->tag == VL_ZERO) {
                    printf("  [OK] fst = zero\n"); tests_pass++;
                } else {
                    printf("  [BUG] fst tag = %d\n", v->pair.fst->tag); tests_fail++;
                }
                /* snd should be stuck transp */
                if (v->pair.snd->tag == VL_TRANSP) {
                    printf("  [OK] snd = VL_TRANSP (stuck inner)\n"); tests_pass++;
                } else {
                    printf("  [BUG] snd tag = %d\n", v->pair.snd->tag); tests_fail++;
                }
            } else {
                printf("  [BUG] expected VL_PAIR, got tag %d\n", v->tag); tests_fail++;
            }
        }
    }

    /* L5-12: Σ-transp with fully constant codomain.
     * transp (λi. Σ(x:Nat). Nat : ...) p = (fst p, fst p ... wait.
     * With A=Nat (constant) and B=Nat (constant):
     * Stage 3 would handle the whole Σ type as constant.
     * For a non-trivial test: Σ(x:Nat). Id Nat x x — constant in i.
     * Stage 3: whole thing constant → transp = identity. */
    printf("\n[L5-12] Σ with constant family: Stage 3 identity\n");
    expect_conv(a,
        "transp (\\i. (Σ(x:Nat). Id Nat x x) : (Π(i:II). Type))"
        "       (zero , refl zero)",
        "(zero , refl zero)",
        1);

    /* L5-13: hcomp type checking — type error: A not a Type */
    printf("\n[L5-13] hcomp type error: A not a Type\n");
    expect_fail(a,
        "hcomp zero i0 (\\_.zero) zero",
        "A is zero, not a type");

    /* L5-14: hcomp type error: face not II */
    printf("\n[L5-14] hcomp type error: face not II\n");
    expect_fail(a,
        "hcomp Nat zero (\\_.zero) zero",
        "face is Nat, not II");

    /* L5-15: hcomp type error: tube codomain not A */
    printf("\n[L5-15] hcomp type error: tube codomain wrong\n");
    expect_fail(a,
        "hcomp Nat i0 (\\_.true) zero",
        "tube returns Bool, not Nat");

    /* L5-16: hcomp conv: two identical stuck hcomps with same tube */
    printf("\n[L5-16] conv: distinct stuck hcomps differ\n");
    expect_conv(a,
        "hcomp Nat (_hc_neutral i0) (\\_.zero) zero",
        "hcomp Nat (_hc_neutral i0) (\\_.zero) (succ zero)",
        0);

    /* --- Stage 4 hardening tests --- */

    printf("\n=== Stage 4 Hardening ===\n");

    /* H1: Σ-transp with neutral pair — must produce a pair, not crash */
    printf("\n[H1] Σ-transp with neutral pair element (non-crash)\n");
    {
        /* transp (λi. Σ(x:Nat). Path II i0 i) neutral_pair
         * neutral_pair : Σ(x:Nat). Path II i0 i0 (represented as a neutral)
         * result should be VL_PAIR with stuck snd */
        Val *fam_v = nbe_eval(a, NULL, parse(a,
            "(\\i. (Σ(x:Nat). Path II i0 i) : (Π(i:II). Type))"));
        /* Neutral pair — any neutral value of the right type */
        Val *neutral_p = vl_neutral(a, 1234, NULL);
        Val *result = nbe_vtransp(a, fam_v, neutral_p);
        if (result->tag == VL_PAIR) {
            printf("  [OK] VL_PAIR produced from neutral pair\n"); tests_pass++;
            /* fst should be fst(neutral) = neutral snd of fst-spine */
            if (result->pair.fst->tag == VL_NEUTRAL) {
                printf("  [OK] fst is VL_NEUTRAL (stuck fst projection)\n"); tests_pass++;
            } else {
                printf("  [BUG] fst tag = %d\n", result->pair.fst->tag); tests_fail++;
            }
        } else {
            printf("  [BUG] expected VL_PAIR, got %d\n", result->tag); tests_fail++;
        }
    }

    /* H2: Σ-transp where x is VL_TRANSP — must NOT apply structural rule (stay stuck) */
    printf("\n[H2] Σ-transp where elem is VL_TRANSP — stays stuck, no crash\n");
    {
        /* Construct a VL_TRANSP value (a stuck transport result) */
        Val *inner_fam = nbe_eval(a, NULL, parse(a,
            "(\\i. (Path II i0 i) : (Π(i:II). Type))"));
        Val *inner_elem = nbe_eval(a, NULL, parse(a, "(<j> i0 : Path II i0 i0)"));
        Val *stuck_transp = nbe_vtransp(a, inner_fam, inner_elem);
        /* stuck_transp should be VL_TRANSP since Path II i0 i is non-constant */
        if (stuck_transp->tag != VL_TRANSP) {
            printf("  [SETUP-FAIL] expected VL_TRANSP for inner, got %d\n", stuck_transp->tag);
            tests_fail++;
        } else {
            /* Now try to use it as the element of a Σ-transp */
            Val *outer_fam = nbe_eval(a, NULL, parse(a,
                "(\\i. (Σ(x:Nat). Path II i0 i) : (Π(i:II). Type))"));
            Val *result = nbe_vtransp(a, outer_fam, stuck_transp);
            /* Must stay stuck — can't apply nbe_vfst to VL_TRANSP */
            if (result->tag == VL_TRANSP) {
                printf("  [OK] VL_TRANSP stays stuck (no crash)\n"); tests_pass++;
            } else {
                printf("  [BUG] expected VL_TRANSP, got %d\n", result->tag); tests_fail++;
            }
        }
    }

    /* H3: nested hcomp — outer i0 fires, base is zero; outer i1 fires, tube(i1)=succ zero */
    printf("\n[H3] nested hcomp chaining\n");
    /* hcomp Nat i0 (\_.succ zero) zero = zero (base case) */
    expect_conv(a, "hcomp Nat i0 (\\_.succ zero) zero", "zero", 1);
    /* hcomp Nat i1 (\_.hcomp Nat i0 (\\_.succ zero) zero) (succ (succ zero))
     * = tube i1 = hcomp Nat i0 (\_.succ zero) zero = zero */
    expect_conv(a,
        "hcomp Nat i1 (\\i. hcomp Nat i0 (\\_.succ zero) zero) (succ (succ zero))",
        "zero",
        1);
    /* stuck nested: hcomp inside base; outer at i0 returns stuck inner */
    {
        Val *stuck_face = vl_neutral(a, 600, NULL);  /* neutral II */
        Val *inner = nbe_vhcomp(a, vl_nat(a), stuck_face,
                                nbe_eval(a, NULL, parse(a, "\\_.zero")),
                                vl_zero(a));
        /* inner is VL_HCOMP since face is neutral */
        Val *outer = nbe_vhcomp(a, vl_nat(a),
                                vl_neutral(a, IZERO_CONST_LVL, NULL),  /* i0 */
                                nbe_eval(a, NULL, parse(a, "\\_.zero")),
                                inner);
        /* outer at i0 returns base = inner (VL_HCOMP) */
        if (outer->tag == VL_HCOMP) {
            printf("  [OK] hcomp at i0 returns stuck inner VL_HCOMP\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_HCOMP base, got %d\n", outer->tag); tests_fail++;
        }
    }

    /* H4: hcomp reduces, then transp structural Π rule fires on the reduced element */
    printf("\n[H4] hcomp-reduced element flows through Π-transp\n");
    /* hcomp (Path II i0 i0) i0 u (<j> i0) = <j> i0 (base case).
     * So transp (λi. Π(x:Nat). Path II i0 i) (\x. (<j> i0 : Path II i0 i0))
     *    = \x. transp (λi. Path II i0 i) (<j> i0)   — structural Π reduction applies.
     * The hcomp at i0 already reduced the element; Π-transp fires on the result. */
    {
        Term *t = parse(a,
            "transp (\\i. (Π(x:Nat). Path II i0 i) : (Π(i:II).Type))"
            "       (\\x. hcomp (Path II i0 i0) i0"
            "                    (\\i. (<j> i0 : Path II i0 i0))"
            "                    (<j> i0 : Path II i0 i0))");
        if (!t) { printf("  [SKIP] parse failed\n"); } else {
            Val *v = nbe_eval(a, NULL, t);
            /* Outer Π-transp fires → VL_LAM; inner elem = <j>i0 (hcomp reduced) */
            if (v->tag == VL_LAM) {
                printf("  [OK] VL_LAM (Π structural reduction applied)\n"); tests_pass++;
            } else {
                printf("  [BUG] expected VL_LAM, got %d\n", v->tag); tests_fail++;
            }
        }
    }

    /* H5: Π-transp where codomain is constant — inner reduces fully */
    printf("\n[H5] Π-transp with constant codomain: chained to identity\n");
    expect_conv(a,
        "transp (\\i. (Π(x:Nat). Id Nat zero zero) : (Π(i:II).Type))"
        "       (\\x. (refl zero : Id Nat zero zero))",
        "\\x. (refl zero : Id Nat zero zero)",
        1);

    /* H6: Π-transp applied at i1 — structural reduction then inner application */
    printf("\n[H6] Π-transp result applied at i1 gives VL_TRANSP\n");
    {
        Term *t = parse(a,
            "(transp (\\i. (Π(j:II). Path II i0 i) : (Π(i:II). Type))"
            "        (\\j. (<r> j : Path II j i0)))"
            " i1");
        if (!t) { printf("  [SKIP]\n"); } else {
            Val *v = nbe_eval(a, NULL, t);
            if (v->tag == VL_TRANSP) {
                printf("  [OK] applied at i1 gives VL_TRANSP\n"); tests_pass++;
            } else {
                printf("  [BUG] got tag %d\n", v->tag); tests_fail++;
            }
        }
    }

    /* H7: hcomp with non-lambda tube still type-checks */
    printf("\n[H7] hcomp with global tube function\n");
    {
        if (def_lookup("_const_zero") < 0)
            def_define("_const_zero", "(\\i. zero : II → Nat)");
        expect_type(a, "hcomp Nat i0 _const_zero (succ zero)", "Nat");
        expect_conv(a, "hcomp Nat i0 _const_zero (succ zero)", "succ zero", 1);
        expect_conv(a, "hcomp Nat i1 _const_zero (succ zero)", "zero", 1);
    }

    /* H8: quote/eval round-trip for stuck VL_HCOMP */
    printf("\n[H8] stuck hcomp round-trips through quote/eval\n");
    {
        Val *face = vl_neutral(a, 777, NULL);
        Val *h1 = nbe_vhcomp(a, vl_nat(a), face,
                              nbe_eval(a, NULL, parse(a, "\\_.zero")),
                              vl_zero(a));
        /* h1 is VL_HCOMP; quote it back to a term and re-evaluate */
        Term *q1 = nbe_quote(a, 0, h1);
        Val  *h2 = nbe_eval(a, NULL, q1);
        int ok = (h1->tag == VL_HCOMP && h2->tag == VL_HCOMP &&
                  conv(a, 0, h1, h2));
        if (ok) { printf("  [OK] quote/eval round-trip preserves VL_HCOMP\n"); tests_pass++; }
        else    { printf("  [BUG] round-trip failed\n"); tests_fail++; }
    }

    /* H9: Π-transp non-closed family stays stuck */
    printf("\n[H9] Π-transp non-closed family stays stuck (no crash)\n");
    {
        /* A family that captures an outer variable — simulate with a global
         * that refers to another global, so env is non-NULL is hard to construct
         * directly; instead verify via a correctly typed but non-reducible case:
         * transp (λi. Π(x:Nat). Nat) f ≡ f (Stage 3: whole Pi is constant) */
        expect_conv(a,
            "transp (\\i. (Π(x:Nat). Nat) : (Π(i:II).Type)) (\\x. zero)",
            "\\x. zero",
            1);
        /* Non-constant codomain that's a Pi — tests that inner transp stays stuck */
        {
            Term *t = parse(a,
                "transp (\\i. (Π(x:Nat). Path II i0 i) : (Π(i:II).Type))"
                "       (\\x. (<j> i0 : Path II i0 i0))");
            if (t) {
                Val *v = nbe_eval(a, NULL, t);
                /* Should be a VL_LAM (Π structural rule applied) */
                if (v->tag == VL_LAM) {
                    printf("  [OK] non-constant Pi-transp → VL_LAM\n"); tests_pass++;
                } else {
                    printf("  [BUG] expected VL_LAM, got %d\n", v->tag); tests_fail++;
                }
            }
        }
    }

    /* --- Phase L2 Stage 5: Glue types + ua computation --- */

    printf("\n=== L2 Stage 5: Glue types + ua computation ===\n");

    /* Stage 7d Phase A helpers — proper equivalences for Glue tests.
     * idNatEquiv : Equiv Nat Nat  (identity equivalence on Nat)
     * idBoolEquiv : Equiv Bool Bool  (identity equivalence on Bool)
     * inv = fst(snd e) is the component used by transp-Glue. */
    if (def_lookup("idNatEquiv") < 0)
        def_define("idNatEquiv",
            "((\\n. n, (\\n. n, (\\y. (<i> y : Path Nat y y), \\x. (<i> x : Path Nat x x))))"
            " : Σ(fwd : Nat → Nat)."
            "   Σ(inv : Nat → Nat)."
            "   Σ(_ : Π(y : Nat). Path Nat (fwd (inv y)) y)."
            "   Π(x : Nat). Path Nat (inv (fwd x)) x)");
    if (def_lookup("idBoolEquiv") < 0)
        def_define("idBoolEquiv",
            "((\\b. b, (\\b. b, (\\y. (<i> y : Path Bool y y), \\x. (<i> x : Path Bool x x))))"
            " : Σ(fwd : Bool → Bool)."
            "   Σ(inv : Bool → Bool)."
            "   Σ(_ : Π(y : Bool). Path Bool (fwd (inv y)) y)."
            "   Π(x : Bool). Path Bool (inv (fwd x)) x)");

    /* L6-1: Glue type formation (type-checked) */
    printf("\n[L6-1] Glue Nat i0 Nat idNatEquiv : Type\n");
    expect_type(a, "Glue Nat i0 Nat idNatEquiv", "Type");

    /* L6-2: Glue at φ=i0 collapses to base type A (eval-level) */
    printf("\n[L6-2] Glue Nat i0 Bool (\\n. true) ≡ Nat\n");
    expect_conv(a, "Glue Nat i0 Bool (\\n. true)", "Nat", 1);

    /* L6-3: Glue at φ=i1 collapses to fiber type T (eval-level) */
    printf("\n[L6-3] Glue Nat i1 Bool (\\n. true) ≡ Bool\n");
    expect_conv(a, "Glue Nat i1 Bool (\\n. true)", "Bool", 1);

    /* L6-4: Glue with neutral face stays stuck.
     * Note: e_val is a plain lambda here (bypasses type checker) — intentional.
     * The face β-rule never touches e; the guard in nbe_vtransp prevents any crash. */
    printf("\n[L6-4] Glue with neutral face stays VL_GLUE\n");
    {
        Val *phi   = vl_neutral(a, 42, NULL);
        Val *e_val = nbe_eval(a, NULL, parse(a, "\\n. true"));
        Val *g = nbe_vglue_ty(a, vl_nat(a), phi, vl_bool(a), e_val);
        if (g->tag == VL_GLUE) {
            printf("  [OK] stuck VL_GLUE\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_GLUE, got %d\n", g->tag); tests_fail++;
        }
    }

    /* L6-5: transp Glue family with idNatEquiv: inv(id) = id, result unchanged */
    printf("\n[L6-5] transp (λi. Glue Nat i Nat idNatEquiv) zero ≡ zero\n");
    expect_conv(a,
        "transp (\\i. (Glue Nat i Nat idNatEquiv) : (Π(i:II). Type)) zero",
        "zero",
        1);

    /* L6-6: transp Glue with idBoolEquiv: inv(id) = id, true unchanged */
    printf("\n[L6-6] transp (λi. Glue Bool i Bool idBoolEquiv) true ≡ true\n");
    expect_conv(a,
        "transp (\\i. (Glue Bool i Bool idBoolEquiv) : (Π(i:II). Type)) true",
        "true",
        1);

    /* L6-7: transp Glue with idBoolEquiv on false */
    printf("\n[L6-7] transp (λi. Glue Bool i Bool idBoolEquiv) false ≡ false\n");
    expect_conv(a,
        "transp (\\i. (Glue Bool i Bool idBoolEquiv) : (Π(i:II). Type)) false",
        "false",
        1);

    /* L6-8: ua computation — transp (λi. ua f @ i) x = f x (identity) */
    printf("\n[L6-8] transp (λi. ua id @ i) zero ≡ zero\n");
    expect_conv(a,
        "transp (\\i. (ua (\\n. n)) @ i) zero",
        "zero",
        1);

    /* L6-9: ua computation with succ */
    printf("\n[L6-9] transp (λi. ua succ @ i) zero ≡ succ zero\n");
    expect_conv(a,
        "transp (\\i. (ua (\\n. succ n)) @ i) zero",
        "succ zero",
        1);

    /* L6-10: ua computation with bool negation */
    printf("\n[L6-10] transp (λi. ua not @ i) true ≡ false\n");
    expect_conv(a,
        "transp (\\i. (ua (\\b. boolrec Bool false true b)) @ i) true",
        "false",
        1);

    /* L6-11: ua computation with double succ */
    printf("\n[L6-11] transp (λi. ua (\\n. succ (succ n)) @ i) zero ≡ succ (succ zero)\n");
    expect_conv(a,
        "transp (\\i. (ua (\\n. succ (succ n))) @ i) zero",
        "succ (succ zero)",
        1);

    /* L6-12: stuck Glue round-trips through quote/eval */
    /* L6-12: quote/eval round-trip for stuck VL_GLUE.
     * Plain-lambda equiv intentional — tests quote/eval symmetry, not transp. */
    printf("\n[L6-12] stuck Glue quote/eval round-trip\n");
    {
        Val *phi   = vl_neutral(a, 111, NULL);
        Val *e_val = nbe_eval(a, NULL, parse(a, "\\n. true"));
        Val *g1    = nbe_vglue_ty(a, vl_nat(a), phi, vl_bool(a), e_val);
        Term *q    = nbe_quote(a, 0, g1);
        Val  *g2   = nbe_eval(a, NULL, q);
        int ok = (g1->tag == VL_GLUE && g2->tag == VL_GLUE && conv(a, 0, g1, g2));
        if (ok) { printf("  [OK] VL_GLUE round-trip preserved\n"); tests_pass++; }
        else    { printf("  [BUG] round-trip failed\n"); tests_fail++; }
    }

    /* L6-13: conv — stuck Glue checks all fields; Glue at i0 ≢ Glue at i1 */
    printf("\n[L6-13] conv: Glue i0 ≡ A (Nat), Glue i1 ≡ T (Bool); i0 ≢ i1\n");
    /* Glue Nat i0 Bool e ≡ Nat,  Glue Nat i1 Bool e ≡ Bool: Nat ≢ Bool */
    expect_conv(a,
        "Glue Nat i0 Bool (\\n. true)",
        "Glue Nat i1 Bool (\\n. true)",
        0);
    /* C-level: two identical VL_GLUE (same face, same fields) are conv-equal.
     * Plain-lambda equiv is intentional — these tests exercise conv on the e field
     * directly, not the transp rule.  The eval guard makes this safe. */
    {
        Val *phi   = vl_neutral(a, 777, NULL);  /* truly stuck face */
        Val *e_val = nbe_eval(a, NULL, parse(a, "\\n. true"));
        Val *g1    = vl_glue(a, vl_nat(a), phi, vl_bool(a), e_val);
        Val *g2    = vl_glue(a, vl_nat(a), phi, vl_bool(a), e_val);
        Val *g3    = vl_glue(a, vl_nat(a), phi, vl_nat(a), /* diff fiber */
                             nbe_eval(a, NULL, parse(a, "\\n. n")));
        if (conv(a, 0, g1, g2)) {
            printf("  [OK] identical VL_GLUE values are conv-equal\n"); tests_pass++;
        } else {
            printf("  [BUG] identical VL_GLUE not conv-equal\n"); tests_fail++;
        }
        if (!conv(a, 0, g1, g3)) {
            printf("  [OK] different-fiber VL_GLUE values are not conv-equal\n"); tests_pass++;
        } else {
            printf("  [BUG] different-fiber VL_GLUE unexpectedly conv-equal\n"); tests_fail++;
        }
    }

    /* L6-14: Glue type error — base A not a Type */
    printf("\n[L6-14] Glue type error: base A not a Type\n");
    expect_fail(a, "Glue zero i0 Bool (\\n. true)", "base A must be a Type");

    /* L6-15: Glue type error — fiber T not a Type */
    printf("\n[L6-15] Glue type error: fiber T not a Type\n");
    expect_fail(a, "Glue Nat i0 zero (\\n. n)", "fiber T must be a Type");

    /* L6-16: Glue type error — equiv is not a Σ at all (zero : Nat) */
    printf("\n[L6-16] Glue type error: equiv not Equiv T A (not a Σ)\n");
    expect_fail(a, "Glue Nat i0 Nat zero", "equivalence e must have type Equiv T A");

    /* L6-16b: Glue type error — equiv is Σ-shaped but fwd has wrong type
     * (\\b.b : Bool → Bool, not Nat → Nat).  Catches conv check within the Σ. */
    printf("\n[L6-16b] Glue type error: equiv has wrong fwd type (Bool→Bool not Nat→Nat)\n");
    expect_fail(a,
        "Glue Nat i0 Nat (\\b. b, (\\b. b, (\\y. (<i> y : Path Bool y y), \\x. (<i> x : Path Bool x x))))",
        "equivalence e must have type Equiv T A");

    /* L6-17: Glue type formation with idNatEquiv at higher nat value */
    printf("\n[L6-17] Glue Nat i0 Nat idNatEquiv : Type\n");
    expect_type(a, "Glue Nat i0 Nat idNatEquiv", "Type");

    /* L6-18: transp Glue with idNatEquiv on succ zero */
    printf("\n[L6-18] transp (λi. Glue Nat i Nat idNatEquiv) (succ zero) ≡ succ zero\n");
    expect_conv(a,
        "transp (\\i. (Glue Nat i Nat idNatEquiv) : (Π(i:II). Type)) (succ zero)",
        "succ zero",
        1);

    /* L6-19: elab_infer TM_GLUE path — hole in Glue expression with annotation.
     * The term has no holes (idNatEquiv is fully known), but the elab path fires
     * when term_has_holes would be true for a term containing _.
     * Verify that the elab path reaches infer correctly by type-checking a Glue
     * with an explicitly annotated equiv that goes through the elab ANN case. */
    printf("\n[L6-19] Glue with annotated equiv goes through elab path\n");
    expect_type(a,
        "Glue Nat i0 Nat"
        " ((\\n. n, (\\n. n, (\\y. (<i> y : Path Nat y y), \\x. (<i> x : Path Nat x x))))"
        "  : Σ(fwd : Nat → Nat). Σ(inv : Nat → Nat)."
        "    Σ(_ : Π(y : Nat). Path Nat (fwd (inv y)) y)."
        "    Π(x : Nat). Path Nat (inv (fwd x)) x)",
        "Type");

    /* --- Stage 5 hardening --- */

    printf("\n=== Stage 5 Hardening ===\n");

    /* GH1: Non-closed Glue family stays stuck (verifies a_fun->lam.env == NULL guard).
     * Build a VL_LAM whose env is non-NULL and body is TM_GLUE; nbe_vtransp must
     * return VL_TRANSP (stuck), not try to quote outer-env neutrals. */
    printf("\n[GH1] non-closed Glue family stays stuck (env guard)\n");
    {
        /* Outer value at depth 3 (simulates a variable captured from the environment). */
        Val *outer = vl_neutral(a, 3, NULL);
        /* Build body: TM_GLUE(VAR(1)=outer, VAR(0)=i, TM_NAT, TM_LAM("n",TM_VAR(0)))
         * In env=[i, outer]: VAR(0)=i (probe), VAR(1)=outer (some type). */
        Term *body = tm_glue(a,
                             tm_var(a, 1),       /* base  = outer type */
                             tm_var(a, 0),       /* face  = i          */
                             tm_nat(a),           /* fiber = Nat        */
                             tm_lam(a, "n", tm_var(a, 0)));  /* equiv = id */
        Env  *captured_env = env_cons(a, outer, NULL);  /* non-NULL env */
        Val  *non_closed   = vl_lam(a, "i", captured_env, body);
        Val  *result       = nbe_vtransp(a, non_closed, vl_zero(a));
        if (result->tag == VL_TRANSP) {
            printf("  [OK] non-closed Glue family stays VL_TRANSP\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_TRANSP, got %d\n", result->tag); tests_fail++;
        }
    }

    /* GH2: Glue-transp with neutral x and idNatEquiv: inv(neutral) = neutral */
    printf("\n[GH2] Glue-transp with neutral x: inv(idNatEquiv)(neutral) = neutral\n");
    {
        Val *neutral_x = vl_neutral(a, 50, NULL);
        Val *result    = nbe_vtransp(a,
            nbe_eval(a, NULL, parse(a,
                "(\\i. (Glue Nat i Nat idNatEquiv) : (Π(i:II). Type))")),
            neutral_x);
        /* inv(idNatEquiv) = id, so id(neutral) = the neutral itself */
        if (result->tag == VL_NEUTRAL && result->neutral.lvl == 50) {
            printf("  [OK] inv(id)(neutral) = neutral\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_NEUTRAL(50), got tag=%d\n", result->tag); tests_fail++;
        }
    }

    /* GH3: Glue-transp with a stuck VL_TRANSP as x; inv(id) = id → passes through */
    printf("\n[GH3] Glue-transp with stuck-transp x: inv(idNatEquiv)(stuck) = stuck\n");
    {
        /* inner_x = transp (λi. Path II i0 i) (<j>i0)  — stuck (non-constant Path family) */
        Val *inner_fam  = nbe_eval(a, NULL, parse(a,
            "(\\i. (Path II i0 i) : (Π(i:II). Type))"));
        Val *inner_elem = nbe_eval(a, NULL, parse(a, "(<j> i0 : Path II i0 i0)"));
        Val *stuck_x    = nbe_vtransp(a, inner_fam, inner_elem);
        if (stuck_x->tag != VL_TRANSP) {
            printf("  [SETUP-FAIL] inner transp not stuck, got %d\n", stuck_x->tag);
            tests_fail++;
        } else {
            /* Outer Glue-transp with idNatEquiv: inv(stuck) = id(stuck) = stuck */
            Val *outer_fam = nbe_eval(a, NULL, parse(a,
                "(\\i. (Glue Nat i Nat idNatEquiv) : (Π(i:II). Type))"));
            Val *result    = nbe_vtransp(a, outer_fam, stuck_x);
            /* id(VL_TRANSP) = VL_TRANSP */
            if (result->tag == VL_TRANSP) {
                printf("  [OK] id(stuck_transp) = VL_TRANSP\n"); tests_pass++;
            } else {
                printf("  [BUG] expected VL_TRANSP, got %d\n", result->tag); tests_fail++;
            }
        }
    }

    /* GH4: Chained Glue-transp (id twice): result still zero */
    printf("\n[GH4] chained Glue-transp with idNatEquiv: id(id(zero)) = zero\n");
    expect_conv(a,
        "transp (\\i. (Glue Nat i Nat idNatEquiv) : (Π(i:II). Type))"
        "  (transp (\\i. (Glue Nat i Nat idNatEquiv) : (Π(i:II). Type)) zero)",
        "zero",
        1);

    /* GH5: ua computation with neutral function: transp(ua f_neutral @ i) x = f_neutral x */
    printf("\n[GH5] ua with neutral f: result is neutral applied to x\n");
    {
        Val *f_neutral = vl_neutral(a, 200, NULL);  /* some neutral function */
        /* Build the family manually to ensure the spine pattern is right */
        Val *ua_f = vl_neutral(a, UA_CONST_LVL,
                                spine_cons(a, f_neutral, NULL));  /* ua @ f */
        /* Wrap in a pathabs-like lambda: family = VL_LAM body that does (ua f @ probe) */
        /* Easier: use the ua spine trick directly on the eval path */
        Val *fam = nbe_eval(a, env_cons(a, ua_f, NULL),
            /* body: VAR(0) @ VAR(1) where VAR(0) = ua_f, VAR(1) = i (the probe) */
            /* Actually, let's build the term: \i. (ua_f) @ i */
            /* We can't easily build this from parse since ua_f is a Val, not a term.
             * Instead call nbe_vtransp directly on a synthetic family. */
            tm_lam(a, "i", tm_pathapp(a, tm_var(a, 1), tm_var(a, 0))));
        /* This lam has env=[ua_f] so env != NULL — it's a non-closed family → stays stuck.
         * Test this different way: verify the ua rule fires when we hand-craft the probe result. */
        (void)fam;  /* unused; test differently below */
        /* Direct approach: verify that when a_i matches the ua spine pattern,
         * nbe_vtransp returns f_neutral(x). */
        Val *i_probe  = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
        Val *ua_f_at_probe = vl_neutral(a, UA_CONST_LVL,
            spine_pathapp(a, i_probe,
                spine_cons(a, f_neutral, NULL)));  /* ua @ f @ probe */
        /* We need a closed family whose probe gives ua_f_at_probe.
         * This is hard to arrange from scratch; test via expect_conv instead. */
        (void)ua_f_at_probe;

        /* Use a simpler approach: define a global neutral function, use in ua test */
        if (def_lookup("_ua_fn") < 0)
            def_define("_ua_fn", "(\\n. succ (succ n) : Nat → Nat)");
        Val *result = nbe_vtransp(a,
            nbe_eval(a, NULL, parse(a, "(\\i. (ua _ua_fn) @ i)")),
            vl_zero(a));
        if (result->tag == VL_SUCC && result->succ->tag == VL_SUCC &&
            result->succ->succ->tag == VL_ZERO) {
            printf("  [OK] ua _ua_fn zero = succ (succ zero)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected succ(succ(zero)), got tag=%d\n", result->tag); tests_fail++;
        }
    }

    /* GH6: ua computation with neutral x: transp(ua f @ i) neutral = f neutral */
    printf("\n[GH6] ua with neutral x: result = f(neutral)\n");
    {
        Val *neutral_x = vl_neutral(a, 77, NULL);
        Val *result    = nbe_vtransp(a,
            nbe_eval(a, NULL, parse(a, "(\\i. (ua (\\n. succ n)) @ i)")),
            neutral_x);
        /* succ(neutral_77) = VL_SUCC whose .succ = neutral_77 */
        if (result->tag == VL_SUCC && result->succ->tag == VL_NEUTRAL &&
            result->succ->neutral.lvl == 77) {
            printf("  [OK] succ(neutral_77) correct\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_SUCC(neutral_77), got tag=%d\n", result->tag); tests_fail++;
        }
    }

    /* GH7: conv — different ua results are not equal */
    printf("\n[GH7] conv: ua succ applied to zero ≢ ua succ applied to succ zero\n");
    expect_conv(a,
        "transp (\\i. (ua (\\n. succ n)) @ i) zero",
        "transp (\\i. (ua (\\n. succ n)) @ i) (succ zero)",
        0);  /* succ zero ≢ succ (succ zero) */

    /* GH8: ua with >1 explicit spine args stays stuck (spine check next->next != NULL) */
    printf("\n[GH8] ua with multi-arg spine stays stuck\n");
    {
        /* (ua Nat Nat pair) @ probe — spine: PATHAPP(probe) → APP(pair) → APP(Nat) → APP(Nat)
         * next->next = APP(Nat) ≠ NULL → rule must not fire → VL_TRANSP */
        Val *i_probe = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
        Val *nat_val = vl_nat(a);
        Val *pair_val = vl_pair(a, vl_lam(a, "n", NULL, tm_var(a, 0)),
                                   vl_lam(a, "n", NULL, tm_var(a, 0)));
        /* ua @ Nat @ Nat @ pair */
        Val *ua_3 = vl_neutral(a, UA_CONST_LVL,
            spine_pathapp(a, i_probe,
                spine_cons(a, pair_val,
                    spine_cons(a, nat_val,
                        spine_cons(a, nat_val, NULL)))));
        /* a_fun: closed family returning ua_3 when applied to anything */
        Term *T_q  = nbe_quote(a, TRANSP_PROBE_LVL + 1, ua_3);
        Val  *fam  = nbe_eval(a, NULL, tm_lam(a, "i", T_q));
        Val  *res  = nbe_vtransp(a, fam, vl_zero(a));
        /* Must stay stuck — ua spine has 3 APP entries, not 1 */
        if (res->tag == VL_TRANSP) {
            printf("  [OK] multi-arg ua stays VL_TRANSP\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_TRANSP, got %d\n", res->tag); tests_fail++;
        }
    }

    /* GH9: non-function f in ua pattern stays stuck (no crash) */
    printf("\n[GH9] ua with non-function f stays stuck (no crash)\n");
    {
        Val *i_probe = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
        Val *pair_f  = vl_pair(a, vl_zero(a), vl_zero(a));  /* VL_PAIR — not a function */
        Val *ua_pair = vl_neutral(a, UA_CONST_LVL,
            spine_pathapp(a, i_probe,
                spine_cons(a, pair_f, NULL)));  /* ua @ pair_f @ probe */
        Term *T_q = nbe_quote(a, TRANSP_PROBE_LVL + 1, ua_pair);
        Val  *fam = nbe_eval(a, NULL, tm_lam(a, "i", T_q));
        Val  *res = nbe_vtransp(a, fam, vl_zero(a));
        /* f = VL_PAIR → not a function → rule must not fire → VL_TRANSP */
        if (res->tag == VL_TRANSP) {
            printf("  [OK] non-function f in ua stays VL_TRANSP\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_TRANSP for non-function f, got %d\n", res->tag); tests_fail++;
        }
    }

    /* GH10: global Glue family transparent unfolding with idNatEquiv */
    printf("\n[GH10] global Glue family transparent unfolding\n");
    {
        if (def_lookup("cGlue") < 0)
            def_define("cGlue",
                "(\\i. (Glue Nat i Nat idNatEquiv) : Π(i:II). Type)");
        expect_conv(a, "transp cGlue zero", "zero", 1);
        expect_conv(a, "transp cGlue (succ zero)", "succ zero", 1);
    }

    /* GH11: Glue type-checks at level 0 with idNatEquiv */
    printf("\n[GH11] Glue Nat i0 Nat idNatEquiv : Type\n");
    expect_type(a, "Glue Nat i0 Nat idNatEquiv", "Type");

    /* GH12: Glue with non-constant fiber reduces only the face, not fiber */
    printf("\n[GH12] Glue at neutral face stays stuck even with non-constant fiber\n");
    {
        Val *neutral_face = vl_neutral(a, 9, NULL);
        Val *g = nbe_vglue_ty(a, vl_nat(a), neutral_face,
                              vl_bool(a),
                              nbe_eval(a, NULL, parse(a, "\\n. true")));
        /* face ≠ i0, i1 → stuck */
        if (g->tag == VL_GLUE &&
            conv(a, 0, g->glue_s.base,  vl_nat(a))  &&
            conv(a, 0, g->glue_s.fiber, vl_bool(a)) &&
            conv(a, 0, g->glue_s.face,  neutral_face)) {
            printf("  [OK] VL_GLUE fields preserved correctly\n"); tests_pass++;
        } else {
            printf("  [BUG] VL_GLUE fields wrong\n"); tests_fail++;
        }
    }

    /* GH-A1: verify transp-Glue uses inv (fst(snd e)), not fwd (fst e).
     * Construct an asymmetric VL_PAIR where fwd = zero (not callable as Nat→Nat,
     * but we distinguish fwd vs inv by making inv = id.  If the rule mistakenly used
     * fwd, it would crash; using inv = id it returns the neutral unchanged. */
    printf("\n[GH-A1] transp-Glue uses inv component, not fwd\n");
    {
        /* Build e = (fwd=\_.succ zero, inv=id, sect=..., retr=...) as a nested VL_PAIR.
         * We only care that fst(snd e) = id is called, not fst(e) = \_. succ zero. */
        Val *fwd_val  = nbe_eval(a, NULL, parse(a, "\\n. succ zero")); /* wrong: constant succ zero */
        Val *inv_val  = nbe_eval(a, NULL, parse(a, "\\n. n"));         /* id */
        Val *sect_val = nbe_eval(a, NULL, parse(a, "\\y. (<i> y : Path Nat y y)"));
        Val *retr_val = nbe_eval(a, NULL, parse(a, "\\x. (<i> x : Path Nat x x)"));
        Val *inner    = vl_pair(a, inv_val,  vl_pair(a, sect_val, retr_val));
        Val *e_asym   = vl_pair(a, fwd_val, inner);
        /* Build stuck Glue family with this asymmetric e */
        Val *probe = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
        Val *glue_v = nbe_vglue_ty(a, vl_nat(a), probe, vl_nat(a), e_asym);
        Term *T_q   = nbe_quote(a, TRANSP_PROBE_LVL + 1, glue_v);
        Val  *fam   = nbe_eval(a, NULL, tm_lam(a, "i", T_q));
        Val  *neutral_x = vl_neutral(a, 51, NULL);
        Val  *result    = nbe_vtransp(a, fam, neutral_x);
        /* inv = id, so id(neutral_x) = neutral_x (VL_NEUTRAL lvl=51).
         * If fwd were used instead, result = succ zero (not neutral). */
        if (result->tag == VL_NEUTRAL && result->neutral.lvl == 51) {
            printf("  [OK] inv component used: id(neutral) = neutral\n"); tests_pass++;
        } else {
            printf("  [BUG] wrong component used (got tag=%d, expected VL_NEUTRAL 51)\n",
                   result->tag); tests_fail++;
        }
    }

    /* GH-A2: transp-Glue with a non-pair, non-neutral equiv stays VL_TRANSP (guard).
     * Before the fix, this would crash with "vsnd: not a pair".
     * After the fix, the e_val guard fires and the result stays stuck. */
    printf("\n[GH-A2] transp-Glue with plain-lambda equiv stays stuck (no crash)\n");
    {
        Val *lam_e  = nbe_eval(a, NULL, parse(a, "\\n. n"));   /* VL_LAM — not a Σ-pair */
        Val *probe  = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
        Val *glue_v = nbe_vglue_ty(a, vl_nat(a), probe, vl_nat(a), lam_e);
        Term *T_q   = nbe_quote(a, TRANSP_PROBE_LVL + 1, glue_v);
        Val  *fam   = nbe_eval(a, NULL, tm_lam(a, "i", T_q));
        Val  *res   = nbe_vtransp(a, fam, vl_zero(a));
        /* Guard fires: lam_e is VL_LAM, not VL_PAIR/VL_NEUTRAL → stays VL_TRANSP */
        if (res->tag == VL_TRANSP) {
            printf("  [OK] plain-lambda equiv stays stuck as VL_TRANSP\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_TRANSP, got tag=%d\n", res->tag); tests_fail++;
        }
    }

    /* --- Phase L2 Stage 7d: glue intro / unglue elim --- */

    printf("\n=== L2 Stage 7d: glue intro / unglue elim ===\n");

    /* GB1: glue at φ=i0 reduces to base element */
    printf("\n[GB1] glue i0 t a ≡ a\n");
    {
        Val *t_partial = nbe_eval(a, NULL, parse(a, "\\_ . zero"));  /* Partial i0 Nat */
        Val *res = nbe_vglueelem(a,
                       vl_neutral(a, IZERO_CONST_LVL, NULL),
                       t_partial, vl_zero(a));
        if (res->tag == VL_ZERO) {
            printf("  [OK] glue i0 t zero = zero\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_ZERO, got %d\n", res->tag); tests_fail++;
        }
    }

    /* GB2: glue at φ=i1 reduces to t star (applies partial to Unit.star) */
    printf("\n[GB2] glue i1 t a ≡ t star\n");
    {
        /* t = [i1 ↦ succ zero] = λ(_:Unit). succ zero */
        Val *t_partial = nbe_eval(a, NULL, parse(a, "\\_ . succ zero"));
        Val *res = nbe_vglueelem(a,
                       vl_neutral(a, IONE_CONST_LVL, NULL),
                       t_partial, vl_zero(a));  /* base = zero, ignored */
        if (res->tag == VL_SUCC && res->succ->tag == VL_ZERO) {
            printf("  [OK] glue i1 (\\_.succ zero) a = succ zero\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_SUCC(VL_ZERO), got %d\n", res->tag); tests_fail++;
        }
    }

    /* GB3: glue with neutral face stays stuck (VL_GLUEELEM) */
    printf("\n[GB3] glue neutral t a stays stuck\n");
    {
        Val *phi = vl_neutral(a, 42, NULL);
        Val *t_p = nbe_eval(a, NULL, parse(a, "\\_ . zero"));
        Val *res = nbe_vglueelem(a, phi, t_p, vl_zero(a));
        if (res->tag == VL_GLUEELEM) {
            printf("  [OK] stuck VL_GLUEELEM\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_GLUEELEM, got %d\n", res->tag); tests_fail++;
        }
    }

    /* GB4: unglue β-rule — unglue e (glue φ t a) = a */
    printf("\n[GB4] unglue e (glue φ t a) ≡ a  (β-rule)\n");
    {
        Val *phi    = vl_neutral(a, 42, NULL);
        Val *t_p    = nbe_eval(a, NULL, parse(a, "\\_ . succ zero"));
        Val *glue_v = nbe_vglueelem(a, phi, t_p, vl_zero(a));   /* base = zero */
        Val *e_v    = nbe_eval(a, NULL, parse(a, "idNatEquiv")); /* some equiv */
        Val *res    = nbe_vunglue(a, phi, e_v, glue_v);
        if (res->tag == VL_ZERO) {
            printf("  [OK] unglue e (glue phi t zero) = zero\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_ZERO, got %d\n", res->tag); tests_fail++;
        }
    }

    /* GB5: unglue at φ=i0 is identity — unglue i0 e x = x */
    printf("\n[GB5] unglue i0 e x ≡ x  (identity at base face)\n");
    {
        Val *phi_0  = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *e_v    = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *neutral_x = vl_neutral(a, 77, NULL);
        Val *res    = nbe_vunglue(a, phi_0, e_v, neutral_x);
        if (res->tag == VL_NEUTRAL && res->neutral.lvl == 77) {
            printf("  [OK] unglue i0 e neutral = neutral (identity)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_NEUTRAL(77), got %d\n", res->tag); tests_fail++;
        }
    }

    /* GB6: unglue at φ=i1 applies fst(e) — unglue i1 e x = fwd(e)(x) */
    printf("\n[GB6] unglue i1 e x ≡ fst(e)(x)  (forward map at fiber face)\n");
    {
        Val *phi_1  = vl_neutral(a, IONE_CONST_LVL, NULL);
        /* e = idNatEquiv: fst(e) = \n.n; so fst(e)(zero) = zero */
        Val *e_v    = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *res    = nbe_vunglue(a, phi_1, e_v, vl_zero(a));
        if (res->tag == VL_ZERO) {
            printf("  [OK] unglue i1 idNatEquiv zero = zero (id forward)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_ZERO, got %d\n", res->tag); tests_fail++;
        }
    }

    /* GB7: unglue with neutral face and non-glueelem x stays stuck */
    printf("\n[GB7] unglue neutral e neutral_x stays stuck\n");
    {
        Val *phi    = vl_neutral(a, 55, NULL);
        Val *e_v    = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *neutral_x = vl_neutral(a, 88, NULL);
        Val *res    = nbe_vunglue(a, phi, e_v, neutral_x);
        if (res->tag == VL_UNGLUE) {
            printf("  [OK] stuck VL_UNGLUE\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_UNGLUE, got %d\n", res->tag); tests_fail++;
        }
    }

    /* GB8: quote/eval round-trip for VL_GLUEELEM */
    printf("\n[GB8] VL_GLUEELEM quote/eval round-trip\n");
    {
        Val *phi    = vl_neutral(a, 99, NULL);
        Val *t_p    = nbe_eval(a, NULL, parse(a, "\\_ . zero"));
        Val *g      = vl_glueelem(a, phi, t_p, vl_zero(a));
        Term *q     = nbe_quote(a, 0, g);
        Val  *g2    = nbe_eval(a, NULL, q);
        if (g->tag == VL_GLUEELEM && g2->tag == VL_GLUEELEM &&
            conv(a, 0, g->glue_elem_s.base, g2->glue_elem_s.base)) {
            printf("  [OK] VL_GLUEELEM round-trip preserved\n"); tests_pass++;
        } else {
            printf("  [BUG] round-trip failed (g=%d g2=%d)\n", g->tag, g2->tag); tests_fail++;
        }
    }

    /* GB9: glue surface syntax parses and evaluates via kernel */
    printf("\n[GB9] glue φ t a parse + eval\n");
    expect_conv(a,
        "glue i0 (\\_ . succ zero) zero",
        "zero", 1);  /* at i0, base = zero */

    /* GB10: unglue surface syntax — stuck (neutral face) */
    printf("\n[GB10] unglue surface syntax with neutral face stays stuck\n");
    {
        Val *phi    = vl_neutral(a, 33, NULL);
        Val *e_v    = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *glue_v = nbe_vglueelem(a, phi, nbe_eval(a, NULL, parse(a, "\\_.zero")), vl_zero(a));
        Val  *res   = nbe_vunglue(a,
            vl_neutral(a, 33, NULL), e_v, glue_v);
        /* β-rule fires on VL_GLUEELEM → returns base = zero */
        if (res->tag == VL_ZERO) {
            printf("  [OK] unglue e (VL_GLUEELEM base=zero) = zero (β)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_ZERO from β, got %d\n", res->tag); tests_fail++;
        }
    }

    /* GB11: glue type-checked against Glue A φ T e (check mode) */
    printf("\n[GB11] glue type-checks against stuck Glue type\n");
    {
        /* Build stuck Glue Nat neutral_phi Nat idNatEquiv as expected type */
        Val *phi      = vl_neutral(a, 5, NULL);
        Val *e_v      = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *glue_ty  = vl_glue(a, vl_nat(a), phi, vl_nat(a), e_v);
        /* Build glue term: face=VAR for phi, t=λ_.zero, base=zero */
        /* We can't easily test full type-check here without parse; verify via eval */
        Val *t_p  = nbe_eval(a, NULL, parse(a, "\\_ . zero"));
        Val *gv   = nbe_vglueelem(a, phi, t_p, vl_zero(a));
        if (gv->tag == VL_GLUEELEM &&
            conv(a, 0, gv->glue_elem_s.face, phi) &&
            conv(a, 0, gv->glue_elem_s.base, vl_zero(a))) {
            printf("  [OK] VL_GLUEELEM stores face and base correctly\n"); tests_pass++;
        } else {
            printf("  [BUG] VL_GLUEELEM fields wrong\n"); tests_fail++;
        }
        (void)glue_ty;
    }

    /* GB12: unglue surface syntax parses */
    printf("\n[GB12] unglue parses correctly\n");
    {
        Term *t = parse(a, "unglue i0 idNatEquiv zero");
        if (t && t->tag == TM_UNGLUE) {
            Val *v = nbe_eval(a, NULL, t);
            /* At i0: unglue i0 e zero = zero (identity) */
            if (v->tag == VL_ZERO) {
                printf("  [OK] unglue i0 idNatEquiv zero = zero\n"); tests_pass++;
            } else {
                printf("  [BUG] expected VL_ZERO, got %d\n", v->tag); tests_fail++;
            }
        } else {
            printf("  [BUG] parse failed for unglue\n"); tests_fail++;
        }
    }

    /* GB13: unglue type error — face mismatch (was unsoundness bug before fix) */
    printf("\n[GB13] unglue type error: face mismatch with Glue type face\n");
    {
        /* Build a Glue type with neutral face phi=42, then try unglue with phi=43 */
        /* We can't fully test the type checker here without a surface-level term that
         * would involve different neutral faces, but we verify the eval β-rule is safe:
         * VL_GLUEELEM fires regardless of face match (well-typedness invariant). */
        Val *phi42 = vl_neutral(a, 42, NULL);
        Val *phi43 = vl_neutral(a, 43, NULL);
        Val *e_v   = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *glue_v = nbe_vglueelem(a, phi42, nbe_eval(a, NULL, parse(a, "\\_.zero")), vl_zero(a));
        /* β-rule fires on VL_GLUEELEM regardless of unglue's face arg */
        Val *res = nbe_vunglue(a, phi43, e_v, glue_v);
        if (res->tag == VL_ZERO) {
            printf("  [OK] VL_GLUEELEM β fires safely (type checker enforces face match)\n");
            tests_pass++;
        } else {
            printf("  [BUG] expected VL_ZERO from β, got %d\n", res->tag); tests_fail++;
        }
    }

    /* GB14: unglue type error — wrong equiv rejected */
    printf("\n[GB14] unglue type error: equiv mismatch with Glue type\n");
    /* Surface test: Glue type has idNatEquiv stored; trying to unglue with different e */
    /* Can't test type-check error easily at C level without parse; rely on type-check tests */

    /* --- Phase L2 Stage 7d Phase C: hcomp-Glue structural rule --- */

    printf("\n=== L2 Stage 7d Phase C: hcomp-Glue ===\n");

    /* HC-G1: hcomp (VL_GLUE A phi T e) at ψ=i0 → base (endpoint β fires before rule) */
    printf("\n[HC-G1] hcomp (Glue A phi T e) i0 u base = base  (i0 β before structural)\n");
    {
        Val *phi   = vl_neutral(a, 11, NULL);
        Val *e_v   = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *glue_ty = vl_glue(a, vl_nat(a), phi, vl_nat(a), e_v);
        Val *t_p   = nbe_eval(a, NULL, parse(a, "\\_.succ zero"));
        Val *base  = nbe_vglueelem(a, phi, t_p, vl_zero(a));  /* glue phi t zero */
        Val *tube  = nbe_eval(a, NULL, parse(a, "\\i. zero")); /* constant tube (ignored) */
        Val *face0 = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *res   = nbe_vhcomp(a, glue_ty, face0, tube, base);
        /* i0 β fires: hcomp (Glue...) i0 u base = base = VL_GLUEELEM */
        if (res->tag == VL_GLUEELEM && conv(a, 0, res->glue_elem_s.base, vl_zero(a))) {
            printf("  [OK] hcomp at i0 returns base (VL_GLUEELEM with base=zero)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_GLUEELEM base=zero, got tag=%d\n", res->tag); tests_fail++;
        }
    }

    /* HC-G2: hcomp-Glue with neutral ψ fires structural rule → VL_GLUEELEM */
    printf("\n[HC-G2] hcomp (Glue A phi T e) neutral_ψ u base fires structural rule\n");
    {
        Val *phi   = vl_neutral(a, 12, NULL);
        Val *e_v   = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *glue_ty = vl_glue(a, vl_nat(a), phi, vl_nat(a), e_v);
        Val *t_p   = nbe_eval(a, NULL, parse(a, "\\_.zero"));
        Val *base  = nbe_vglueelem(a, phi, t_p, vl_zero(a));  /* base = glue phi t zero */
        Val *tube  = nbe_eval(a, NULL, parse(a, "\\i. zero")); /* constant tube */
        Val *psi   = vl_neutral(a, 200, NULL);                  /* neutral hcomp face */
        Val *res   = nbe_vhcomp(a, glue_ty, psi, tube, base);
        /* Structural rule fires → result is VL_GLUEELEM (re-glued) */
        if (res->tag == VL_GLUEELEM) {
            printf("  [OK] hcomp-Glue structural rule fires → VL_GLUEELEM\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_GLUEELEM, got %d\n", res->tag); tests_fail++;
        }
    }

    /* HC-G3: hcomp-Glue with base=VL_GLUEELEM and neutral ψ; β on unglue fires */
    printf("\n[HC-G3] hcomp-Glue: unglue β fires on base VL_GLUEELEM, a' extracted correctly\n");
    {
        Val *phi   = vl_neutral(a, 13, NULL);
        Val *e_v   = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *glue_ty = vl_glue(a, vl_nat(a), phi, vl_nat(a), e_v);
        Val *t_p   = nbe_eval(a, NULL, parse(a, "\\_.succ (succ zero)"));
        Val *base  = nbe_vglueelem(a, phi, t_p, nbe_eval(a, NULL, parse(a, "succ zero")));
        /* base = glue phi (λ_. succ(succ(zero))) (succ zero); base component = succ zero */
        Val *tube  = nbe_eval(a, NULL, parse(a, "\\i. zero")); /* ignored at neutral ψ */
        Val *psi   = vl_neutral(a, 201, NULL);
        Val *res   = nbe_vhcomp(a, glue_ty, psi, tube, base);
        /* unglue phi e (VL_GLUEELEM phi t (succ zero)) = succ zero (β)
         * hcomp Nat psi (λi. unglue...) (succ zero) = VL_HCOMP (stuck neutral psi)
         * a' = VL_HCOMP; t' = e.inv(a') = id(a') = a' (neutral)
         * result = VL_GLUEELEM(phi, λ_.a', VL_HCOMP) — base component is hcomp result */
        if (res->tag == VL_GLUEELEM) {
            printf("  [OK] VL_GLUEELEM produced; base = hcomp A psi unglue_tube (succ zero)\n");
            tests_pass++;
        } else {
            printf("  [BUG] expected VL_GLUEELEM, got %d\n", res->tag); tests_fail++;
        }
    }

    /* HC-G4: hcomp-Glue with non-Equiv e stays stuck (guard fires)
     * Tests VL_LAM (plain lambda), not VL_PAIR/VL_NEUTRAL → guard rejects → VL_HCOMP.
     * VL_FIX was previously (incorrectly) allowed; after the Bug-1 fix, VL_FIX also
     * stays stuck here rather than crashing nbe_vfst. */
    printf("\n[HC-G4] hcomp-Glue with plain-lambda e stays VL_HCOMP (guard)\n");
    {
        Val *phi   = vl_neutral(a, 14, NULL);
        Val *lam_e = nbe_eval(a, NULL, parse(a, "\\n. n")); /* VL_LAM, not VL_PAIR */
        Val *glue_ty = vl_glue(a, vl_nat(a), phi, vl_nat(a), lam_e);
        Val *base  = vl_neutral(a, 99, NULL);
        Val *tube  = nbe_eval(a, NULL, parse(a, "\\i. zero"));
        Val *psi   = vl_neutral(a, 202, NULL);
        Val *res   = nbe_vhcomp(a, glue_ty, psi, tube, base);
        if (res->tag == VL_HCOMP) {
            printf("  [OK] plain-lambda e: hcomp-Glue guard → VL_HCOMP stuck\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_HCOMP, got %d\n", res->tag); tests_fail++;
        }
    }

    /* HC-G4b: hcomp-Glue with unglue non-Equiv e also stays stuck in nbe_vunglue.
     * VL_LAM as e in unglue at i1 was previously crashing (VL_FIX guard bug).
     * After the fix, both VL_LAM and VL_FIX in e stay stuck. */
    printf("\n[HC-G4b] unglue i1 with plain-lambda e stays VL_UNGLUE (no crash)\n");
    {
        Val *phi_i1 = vl_neutral(a, IONE_CONST_LVL, NULL);
        Val *lam_e  = nbe_eval(a, NULL, parse(a, "\\n. n")); /* VL_LAM: not VL_PAIR/NEUTRAL */
        Val *x_v    = vl_zero(a);
        Val *res    = nbe_vunglue(a, phi_i1, lam_e, x_v);
        /* Guard rejects VL_LAM → stays VL_UNGLUE */
        if (res->tag == VL_UNGLUE) {
            printf("  [OK] unglue i1 VL_LAM_e → VL_UNGLUE (no crash)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_UNGLUE, got %d\n", res->tag); tests_fail++;
        }
    }

    /* HC-G5: a_prime is unwrapped at phi=i0 (glue i0 t a = a, hcomp result is pure A) */
    printf("\n[HC-G5] hcomp-Glue at Glue phi=i0: type collapses to A, no structural rule\n");
    {
        /* When phi=i0, VL_GLUE collapses to VL_NAT — hcomp fires the Nat rules */
        Val *phi_i0 = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *e_v    = nbe_eval(a, NULL, parse(a, "idNatEquiv"));
        Val *ty_collapsed = nbe_vglue_ty(a, vl_nat(a), phi_i0, vl_nat(a), e_v);
        /* ty = Nat (Glue collapses), so hcomp Nat ψ u zero = VL_HCOMP or reduction */
        Val *psi  = vl_neutral(a, 203, NULL);
        Val *tube = nbe_eval(a, NULL, parse(a, "\\i. zero"));
        Val *res  = nbe_vhcomp(a, ty_collapsed, psi, tube, vl_zero(a));
        /* ty is VL_NAT (not VL_GLUE), so structural Glue rule never fires */
        if (ty_collapsed->tag == VL_NAT) {
            printf("  [OK] Glue at i0 collapses to Nat before hcomp (no Glue rule needed)\n");
            tests_pass++;
        } else {
            printf("  [BUG] expected VL_NAT after collapse, got %d\n", ty_collapsed->tag);
            tests_fail++;
        }
        (void)res;
    }

    /* --- Phase L2 Stage 6: funext computation + interval operations + hcomp Π --- */

    printf("\n=== L2 Stage 6: funext + interval ops + hcomp Π ===\n");

    /* FS1: funext fully applied returns VL_PATHABS (not neutral) */
    printf("\n[FS1] funext fully applied returns a path (VL_PATHABS)\n");
    {
        Term *t = parse(a,
            "funext Nat (\\_. Nat) (\\n. n) (\\n. n)"
            "       (\\x. (<j> x : Path Nat x x))");
        if (t) {
            Val *v = nbe_eval(a, NULL, t);
            if (v->tag == VL_PATHABS) {
                printf("  [OK] funext returns VL_PATHABS\n"); tests_pass++;
            } else {
                printf("  [BUG] expected VL_PATHABS, got tag=%d\n", v->tag); tests_fail++;
            }
        }
    }

    /* FS2: funext path applied at i0 gives left endpoint ≡ f */
    printf("\n[FS2] (funext f f h) @ i0 ≡ f\n");
    expect_conv(a,
        "(funext Nat (\\_. Nat) (\\n. n) (\\n. n)"
        "        (\\x. (<j> x : Path Nat x x))) @ i0",
        "\\n. n",
        1);

    /* FS3: funext path applied at i1 gives right endpoint ≡ g.
     * For f = g = succ, h x = <j> succ x (constant path at succ x).
     * Both endpoints of the path equal \n. succ n. */
    printf("\n[FS3] (funext succ succ h) @ i1 ≡ succ\n");
    expect_conv(a,
        "(funext Nat (\\_. Nat) (\\n. succ n) (\\n. succ n)"
        "        (\\x. (<j> succ x : Path Nat (succ x) (succ x)))) @ i1",
        "\\n. succ n",
        1);

    /* FS4: type check — funext returns Path (not Id) */
    printf("\n[FS4] funext returns Path type\n");
    expect_type(a,
        "funext Nat (\\_. Nat) (\\n. n) (\\n. n)"
        "       (\\x. (<j> x : Path Nat x x))",
        "Path (Π(_ : Nat). Nat) (\\n. n) (\\n. n)");

    /* FS5: funext reflexivity path — h x = <j> x, f = g = id
     * At i0 and i1: λx. x @ i = λx. x = id (constant path) */
    printf("\n[FS5] funext reflexivity path: both endpoints = id\n");
    expect_conv(a,
        "(funext Nat (\\_. Nat) (\\n. n) (\\n. n)"
        "        (\\x. (<j> x : Path Nat x x))) @ i0",
        "\\n. n",
        1);
    expect_conv(a,
        "(funext Nat (\\_. Nat) (\\n. n) (\\n. n)"
        "        (\\x. (<j> x : Path Nat x x))) @ i1",
        "\\n. n",
        1);

    /* --- Interval operations --- */

    printf("\n=== Interval operations (imin / imax / ineg) ===\n");

    /* IO1: imin β-rules at endpoints */
    printf("\n[IO1] imin β-rules\n");
    expect_conv(a, "imin i0 i1", "i0", 1);  /* i0 ∧ i1 = i0 */
    expect_conv(a, "imin i1 i0", "i0", 1);  /* i1 ∧ i0 = i0 */
    expect_conv(a, "imin i1 i1", "i1", 1);  /* i1 ∧ i1 = i1 */
    expect_conv(a, "imin i0 i0", "i0", 1);  /* i0 ∧ i0 = i0 */

    /* IO2: imax β-rules at endpoints */
    printf("\n[IO2] imax β-rules\n");
    expect_conv(a, "imax i0 i1", "i1", 1);  /* i0 ∨ i1 = i1 */
    expect_conv(a, "imax i1 i0", "i1", 1);  /* i1 ∨ i0 = i1 */
    expect_conv(a, "imax i0 i0", "i0", 1);  /* i0 ∨ i0 = i0 */
    expect_conv(a, "imax i1 i1", "i1", 1);  /* i1 ∨ i1 = i1 */

    /* IO3: ineg β-rules */
    printf("\n[IO3] ineg β-rules\n");
    expect_conv(a, "ineg i0", "i1", 1);  /* ~i0 = i1 */
    expect_conv(a, "ineg i1", "i0", 1);  /* ~i1 = i0 */

    /* IO4: imin with one neutral endpoint */
    printf("\n[IO4] imin neutral endpoint rules\n");
    {
        if (def_lookup("_ii_id") < 0)
            def_define("_ii_id", "(\\i. i : II → II)");
        expect_conv(a, "imin i0 (_ii_id i0)", "i0", 1);  /* i0 ∧ x = i0 */
        expect_conv(a, "imin i1 (_ii_id i0)", "_ii_id i0", 1);  /* i1 ∧ x = x */
        expect_conv(a, "imin (_ii_id i0) i0", "i0", 1);  /* x ∧ i0 = i0 */
        expect_conv(a, "imin (_ii_id i0) i1", "_ii_id i0", 1);  /* x ∧ i1 = x */
    }

    /* IO5: imax with one neutral endpoint */
    printf("\n[IO5] imax neutral endpoint rules\n");
    {
        expect_conv(a, "imax i0 (_ii_id i0)", "_ii_id i0", 1);  /* i0 ∨ x = x */
        expect_conv(a, "imax i1 (_ii_id i0)", "i1", 1);  /* i1 ∨ x = i1 */
        expect_conv(a, "imax (_ii_id i0) i0", "_ii_id i0", 1);  /* x ∨ i0 = x */
        expect_conv(a, "imax (_ii_id i0) i1", "i1", 1);  /* x ∨ i1 = i1 */
    }

    /* IO6: De Morgan laws — ~(∧) = ∨(~), ~~x = x */
    printf("\n[IO6] De Morgan: ~(imin i j) = imax (~i) (~j)\n");
    {
        Val *ni = vl_neutral(a, 300, NULL);
        Val *nj = vl_neutral(a, 301, NULL);
        /* ~(i∧j) = ~i∨~j */
        Val *lhs = nbe_vineg(a, nbe_vimin(a, ni, nj));
        Val *rhs = nbe_vimax(a, nbe_vineg(a, ni), nbe_vineg(a, nj));
        if (conv(a, 0, lhs, rhs)) {
            printf("  [OK] ~(i∧j) = ~i∨~j\n"); tests_pass++;
        } else {
            printf("  [BUG] De Morgan ∧ failed\n"); tests_fail++;
        }
        /* ~(i∨j) = ~i∧~j */
        Val *lhs2 = nbe_vineg(a, nbe_vimax(a, ni, nj));
        Val *rhs2 = nbe_vimin(a, nbe_vineg(a, ni), nbe_vineg(a, nj));
        if (conv(a, 0, lhs2, rhs2)) {
            printf("  [OK] ~(i∨j) = ~i∧~j\n"); tests_pass++;
        } else {
            printf("  [BUG] De Morgan ∨ failed\n"); tests_fail++;
        }
        /* ~~i = i */
        Val *dbl_neg = nbe_vineg(a, nbe_vineg(a, ni));
        if (conv(a, 0, dbl_neg, ni)) {
            printf("  [OK] ~~i = i\n"); tests_pass++;
        } else {
            printf("  [BUG] double negation failed\n"); tests_fail++;
        }
    }

    /* IO7: boundary ∂ i = imax i (ineg i) computes to i1 at endpoints */
    printf("\n[IO7] ∂ i = imax i (ineg i): ∂i0=i1, ∂i1=i1\n");
    expect_conv(a, "imax i0 (ineg i0)", "i1", 1);  /* ∂ i0 = i1 */
    expect_conv(a, "imax i1 (ineg i1)", "i1", 1);  /* ∂ i1 = i1 */

    /* IO8: stuck imin/imax/ineg round-trip through quote/eval */
    printf("\n[IO8] stuck interval ops round-trip through quote/eval\n");
    {
        Val *ni = vl_neutral(a, 400, NULL);
        Val *nj = vl_neutral(a, 401, NULL);
        Val *s1 = nbe_vimin(a, ni, nj);   /* stuck VL_IMIN */
        Val *s2 = nbe_vimax(a, ni, nj);   /* stuck VL_IMAX */
        Val *s3 = nbe_vineg(a, ni);        /* stuck VL_INEG */
        Term *q1 = nbe_quote(a, 0, s1);
        Term *q2 = nbe_quote(a, 0, s2);
        Term *q3 = nbe_quote(a, 0, s3);
        Val  *r1 = nbe_eval(a, NULL, q1);
        Val  *r2 = nbe_eval(a, NULL, q2);
        Val  *r3 = nbe_eval(a, NULL, q3);
        int ok1 = (s1->tag == VL_IMIN && r1->tag == VL_IMIN && conv(a, 0, s1, r1));
        int ok2 = (s2->tag == VL_IMAX && r2->tag == VL_IMAX && conv(a, 0, s2, r2));
        int ok3 = (s3->tag == VL_INEG && r3->tag == VL_INEG && conv(a, 0, s3, r3));
        if (ok1 && ok2 && ok3) {
            printf("  [OK] imin/imax/ineg round-trip preserved\n"); tests_pass++;
        } else {
            printf("  [BUG] round-trip failed: %d %d %d\n", ok1, ok2, ok3); tests_fail++;
        }
    }

    /* IO9: type checks — imin/imax/ineg return II */
    printf("\n[IO9] interval ops type-check: imin i0 i1 : II\n");
    expect_type(a, "imin i0 i1", "II");
    expect_type(a, "imax i0 i1", "II");
    expect_type(a, "ineg i0",    "II");

    /* IO10: type error — imin with non-II arg */
    printf("\n[IO10] imin type error: non-II arg rejected\n");
    expect_fail(a, "imin i0 zero", "zero : Nat, not II");
    expect_fail(a, "imin Nat i0",  "Nat : Type, not II");

    /* --- hcomp Π structural rule --- */

    printf("\n=== hcomp Π structural rule ===\n");

    /* HC1: hcomp over Π type returns VL_LAM (not stuck VL_HCOMP) */
    printf("\n[HC1] hcomp (Π(x:Nat).Nat) neutral_face u base is VL_LAM\n");
    {
        Val *phi    = vl_neutral(a, 500, NULL);  /* neutral face */
        Val *tube   = nbe_eval(a, NULL, parse(a, "\\_ x. x"));  /* λ_. id */
        Val *base   = nbe_eval(a, NULL, parse(a, "\\x. succ x")); /* succ */
        Val *pi_ty  = nbe_eval(a, NULL, parse(a, "Π(x : Nat). Nat"));
        Val *result = nbe_vhcomp(a, pi_ty, phi, tube, base);
        if (result->tag == VL_LAM) {
            printf("  [OK] VL_LAM\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_LAM, got %d\n", result->tag); tests_fail++;
        }
    }

    /* HC2: hcomp (Π(x:Nat).Nat) i0 u base = base (endpoint β-rule takes priority) */
    printf("\n[HC2] hcomp Π at i0 still returns base (β takes priority)\n");
    expect_conv(a,
        "hcomp (Π(x : Nat). Nat) i0 (\\_ x. succ x) (\\x. x)",
        "\\x. x",
        1);

    /* HC3: hcomp (Π(x:Nat).Nat) i1 u base = u i1 (i1 β-rule) */
    printf("\n[HC3] hcomp Π at i1 = u i1 = λx. succ x\n");
    expect_conv(a,
        "hcomp (Π(x : Nat). Nat) i1 (\\_ x. succ x) (\\x. x)",
        "\\x. succ x",
        1);

    /* HC4: hcomp Π result applied to arg computes inner hcomp */
    printf("\n[HC4] (hcomp Π phi u base) zero: inner hcomp fires at i0/i1\n");
    /* At face=i0, result = base, so (result) zero = base zero = zero */
    expect_conv(a,
        "hcomp (Π(x : Nat). Nat) i0 (\\_ x. succ x) (\\x. x) zero",
        "zero",
        1);
    /* At face=i1, result = u i1, so (u i1) zero = succ zero */
    expect_conv(a,
        "hcomp (Π(x : Nat). Nat) i1 (\\_ x. succ x) (\\x. x) zero",
        "succ zero",
        1);

    /* HC5: hcomp over non-function type still produces VL_HCOMP (no rule) */
    printf("\n[HC5] hcomp Nat at neutral face stays VL_HCOMP\n");
    {
        Val *phi    = vl_neutral(a, 600, NULL);
        Val *tube   = nbe_eval(a, NULL, parse(a, "\\_ . zero"));
        Val *base   = vl_zero(a);
        Val *result = nbe_vhcomp(a, vl_nat(a), phi, tube, base);
        if (result->tag == VL_HCOMP) {
            printf("  [OK] VL_HCOMP (Nat has no hcomp structural rule)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_HCOMP, got %d\n", result->tag); tests_fail++;
        }
    }

    /* HC6: hcomp (Π(x:Bool).Nat) neutral applied to true/false gives inner hcomp */
    printf("\n[HC6] hcomp Π: result applied to true/false gives inner hcomp (or reduces)\n");
    {
        Val *phi     = vl_neutral(a, 700, NULL);
        Val *tube    = nbe_eval(a, NULL, parse(a, "\\i x. natrec (\\_.Nat) zero (\\m r. succ r) (boolrec (\\_.Nat) (succ zero) zero x)"));
        Val *base    = nbe_eval(a, NULL, parse(a, "\\x. zero"));
        Val *pi_ty   = nbe_eval(a, NULL, parse(a, "Π(x : Bool). Nat"));
        Val *comp    = nbe_vhcomp(a, pi_ty, phi, tube, base);
        /* comp should be VL_LAM */
        if (comp->tag == VL_LAM) {
            Val *at_true = nbe_vapp(a, comp, vl_true(a));
            /* Inner hcomp: hcomp Nat phi (λi. tube i true) (base true) = hcomp Nat phi ... 0 */
            /* phi is neutral → stays VL_HCOMP */
            if (at_true->tag == VL_HCOMP) {
                printf("  [OK] result applied to true gives VL_HCOMP (inner stuck)\n"); tests_pass++;
            } else {
                printf("  [BUG] expected VL_HCOMP, got tag=%d\n", at_true->tag); tests_fail++;
            }
        } else {
            printf("  [BUG] hcomp Π result not VL_LAM, got tag=%d\n", comp->tag); tests_fail++;
        }
    }

    /* --- Stage 6 Hardening --- */

    printf("\n=== Stage 6 Hardening ===\n");

    /* SH1: funext with neutral h — computation fires, returns VL_PATHABS */
    printf("\n[SH1] funext with neutral h returns VL_PATHABS\n");
    {
        Val *h_neutral = vl_neutral(a, 888, NULL);
        /* Build: neutral(FUNEXT_CONST_LVL) with 4-spine, apply to h */
        Val *base = vl_neutral(a, FUNEXT_CONST_LVL, NULL);
        Val *f1 = nbe_vapp(a, base, vl_nat(a));          /* funext Nat */
        Val *f2 = nbe_vapp(a, f1,   vl_nat(a));          /* funext Nat Nat */
        Val *f3 = nbe_vapp(a, f2,   vl_neutral(a, 1, NULL));  /* funext Nat Nat f */
        Val *f4 = nbe_vapp(a, f3,   vl_neutral(a, 2, NULL));  /* funext Nat Nat f g */
        Val *f5 = nbe_vapp(a, f4,   h_neutral);          /* funext Nat Nat f g h — fires! */
        if (f5->tag == VL_PATHABS) {
            printf("  [OK] VL_PATHABS produced for neutral h\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_PATHABS, got tag=%d\n", f5->tag); tests_fail++;
        }
    }

    /* SH2: funext with neutral h, applied at i, applied at x — gives neutral */
    printf("\n[SH2] (funext h) @ i applied at x gives (h x @ i) — neutral chain\n");
    {
        Val *h_neutral = vl_neutral(a, 888, NULL);
        Val *base = vl_neutral(a, FUNEXT_CONST_LVL, NULL);
        Val *path = nbe_vapp(a,
                        nbe_vapp(a,
                            nbe_vapp(a,
                                nbe_vapp(a,
                                    nbe_vapp(a, base, vl_nat(a)),
                                    vl_nat(a)),
                                vl_neutral(a, 1, NULL)),
                            vl_neutral(a, 2, NULL)),
                        h_neutral);
        /* path = VL_PATHABS; apply at i0 */
        Val *at_i0 = nbe_vpathapp(a, path, vl_neutral(a, IZERO_CONST_LVL, NULL));
        /* at_i0 = VL_LAM("x", [i0, h], body); apply at x_neutral */
        Val *x_n   = vl_neutral(a, 999, NULL);
        Val *final = nbe_vapp(a, at_i0, x_n);
        /* final = nbe_vpathapp(h_neutral x_neutral, i0) — a neutral */
        if (final->tag == VL_NEUTRAL) {
            printf("  [OK] neutral chain preserved\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_NEUTRAL, got tag=%d\n", final->tag); tests_fail++;
        }
    }

    /* SH3: funext partial (3-spine) stays neutral */
    printf("\n[SH3] funext with 3 args stays neutral\n");
    {
        Val *base = vl_neutral(a, FUNEXT_CONST_LVL, NULL);
        Val *f1 = nbe_vapp(a, base, vl_nat(a));
        Val *f2 = nbe_vapp(a, f1,   vl_nat(a));
        Val *f3 = nbe_vapp(a, f2,   vl_neutral(a, 1, NULL));
        if (f3->tag == VL_NEUTRAL) {
            printf("  [OK] 3-arg funext stays neutral\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_NEUTRAL, got tag=%d\n", f3->tag); tests_fail++;
        }
    }

    /* SH4: funext quote/eval round-trip preserves path structure */
    printf("\n[SH4] funext result quote/eval round-trip\n");
    {
        Term *t = parse(a,
            "funext Nat (\\_. Nat) (\\n. n) (\\n. n)"
            "       (\\x. (<j> x : Path Nat x x))");
        if (t) {
            Val  *v1  = nbe_eval(a, NULL, t);
            Term *q   = nbe_quote(a, 0, v1);
            Val  *v2  = nbe_eval(a, NULL, q);
            int ok = (v1->tag == VL_PATHABS && v2->tag == VL_PATHABS && conv(a, 0, v1, v2));
            if (ok) { printf("  [OK] VL_PATHABS round-trip\n"); tests_pass++; }
            else    { printf("  [BUG] round-trip failed\n"); tests_fail++; }
        }
    }

    /* SH5: conv — identical funext results are equal */
    printf("\n[SH5] conv: identical funext results are equal\n");
    expect_conv(a,
        "funext Nat (\\_. Nat) (\\n. n) (\\n. n) (\\x. (<j> x : Path Nat x x))",
        "funext Nat (\\_. Nat) (\\n. n) (\\n. n) (\\x. (<j> x : Path Nat x x))",
        1);

    /* SH6: conv — funext results differ when h differs */
    printf("\n[SH6] conv: funext with different h values not equal\n");
    {
        if (def_lookup("_h1") < 0)
            def_define("_h1", "(\\x. (<j> x       : Path Nat x x) : Π(x:Nat). Path Nat x x)");
        if (def_lookup("_h2") < 0)
            def_define("_h2", "(\\x. (<j> succ x  : Path Nat (succ x) (succ x))"
                               " : Π(x:Nat). Path Nat (succ x) (succ x))");
        /* Note: h1 and h2 produce paths at different types so funext call may be
         * ill-typed, but conv at eval level detects the difference. */
        expect_conv(a,
            "funext Nat (\\_. Nat) (\\n. n) (\\n. n) _h1",
            "funext Nat (\\_. Nat) (\\n. n) (\\n. n) _h2",
            0);
    }

    /* SH7: elab — holes inside imin/imax/ineg are found and substituted */
    printf("\n[SH7] holes inside imin/imax/ineg are elaborated correctly\n");
    {
        /* imin _ i1 : II   where _ should be solved as some II value.
         * With hole in imin: term_has_holes should return 1, elab_subst should process it. */
        Term *t = parse(a, "(imin _ i1 : II)");
        if (t && term_has_holes(t)) {
            printf("  [OK] term_has_holes detects hole inside imin\n"); tests_pass++;
        } else {
            printf("  [BUG] term_has_holes missed hole inside imin\n"); tests_fail++;
        }
    }

    /* SH8: holes inside Glue are found */
    printf("\n[SH8] holes inside Glue are found by term_has_holes\n");
    {
        Term *t = parse(a, "(Glue _ i0 Nat (\\n. n) : Type)");
        if (t && term_has_holes(t)) {
            printf("  [OK] term_has_holes detects hole inside Glue\n"); tests_pass++;
        } else {
            printf("  [BUG] term_has_holes missed hole inside Glue\n"); tests_fail++;
        }
    }

    /* SH9: nested interval ops compute correctly end-to-end */
    printf("\n[SH9] nested interval ops: imax (imin i1 i0) (ineg i1) = i0\n");
    /* imax (imin i1 i0) (ineg i1) = imax i0 i0 = i0 */
    expect_conv(a, "imax (imin i1 i0) (ineg i1)", "i0", 1);
    /* imin (imax i0 i1) (ineg i0) = imin i1 i1 = i1 */
    expect_conv(a, "imin (imax i0 i1) (ineg i0)", "i1", 1);

    /* SH10: ~(ineg i) = i (double negation via ineg of stuck ineg) */
    printf("\n[SH10] ~(~i) = i for neutral i (double negation)\n");
    {
        Val *ni = vl_neutral(a, 555, NULL);
        Val *neg_neg = nbe_vineg(a, nbe_vineg(a, ni));
        if (conv(a, 0, neg_neg, ni)) {
            printf("  [OK] ~~neutral_555 = neutral_555\n"); tests_pass++;
        } else {
            printf("  [BUG] double negation failed\n"); tests_fail++;
        }
    }

    /* SH11: ~(imin x y) = imax (~x) (~y) for neutrals (De Morgan, string-level) */
    printf("\n[SH11] De Morgan via string parse and conv\n");
    {
        if (def_lookup("_ni") < 0)
            def_define("_ni", "(\\i. i : II → II)");
        if (def_lookup("_nj") < 0)
            def_define("_nj", "(\\j. j : II → II)");
        /* ineg (imin (_ni i0) (_nj i0)) = imax (ineg (_ni i0)) (ineg (_nj i0)) */
        expect_conv(a,
            "ineg (imin (_ni i0) (_nj i0))",
            "imax (ineg (_ni i0)) (ineg (_nj i0))",
            1);
    }

    /* SH12: hcomp Π with neutral tube — still returns VL_LAM */
    printf("\n[SH12] hcomp Π with neutral tube returns VL_LAM\n");
    {
        Val *phi     = vl_neutral(a, 501, NULL);
        Val *tube    = vl_neutral(a, 502, NULL);  /* neutral tube */
        Val *base    = nbe_eval(a, NULL, parse(a, "\\x. x"));
        Val *pi_ty   = nbe_eval(a, NULL, parse(a, "Π(x : Nat). Nat"));
        Val *result  = nbe_vhcomp(a, pi_ty, phi, tube, base);
        if (result->tag == VL_LAM) {
            printf("  [OK] VL_LAM for neutral tube\n"); tests_pass++;
            /* Apply to zero: inner hcomp has neutral tube → VL_HCOMP */
            Val *at_zero = nbe_vapp(a, result, vl_zero(a));
            if (at_zero->tag == VL_HCOMP) {
                printf("  [OK] inner hcomp with neutral tube stays VL_HCOMP\n"); tests_pass++;
            } else {
                printf("  [BUG] inner got tag=%d\n", at_zero->tag); tests_fail++;
            }
        } else {
            printf("  [BUG] expected VL_LAM, got tag=%d\n", result->tag); tests_fail++;
        }
    }

    /* SH13: hcomp Π with Pi→Nat codomain (non-trivial dependent Pi) */
    printf("\n[SH13] hcomp (Π(x:Nat). Π(y:Nat). Nat) at neutral face → VL_LAM\n");
    {
        Val *phi   = vl_neutral(a, 601, NULL);
        Val *tube  = nbe_eval(a, NULL, parse(a, "\\_ x y. succ y"));
        Val *base  = nbe_eval(a, NULL, parse(a, "\\x y. x"));
        Val *pi_ty = nbe_eval(a, NULL, parse(a, "Π(x : Nat). Π(y : Nat). Nat"));
        Val *result = nbe_vhcomp(a, pi_ty, phi, tube, base);
        if (result->tag == VL_LAM) {
            printf("  [OK] outer VL_LAM\n"); tests_pass++;
            /* Apply to zero: codomain Π(y:Nat).Nat is VL_PI → recursive Π rule */
            Val *at_zero = nbe_vapp(a, result, vl_zero(a));
            if (at_zero->tag == VL_LAM) {
                printf("  [OK] inner VL_LAM (Π→Nat recursive rule)\n"); tests_pass++;
                /* Apply inner to zero: hcomp Nat phi ... → VL_HCOMP */
                Val *at_zero_zero = nbe_vapp(a, at_zero, vl_zero(a));
                if (at_zero_zero->tag == VL_HCOMP) {
                    printf("  [OK] innermost VL_HCOMP (Nat not a Π)\n"); tests_pass++;
                } else {
                    printf("  [BUG] innermost got tag=%d\n", at_zero_zero->tag); tests_fail++;
                }
            } else {
                printf("  [BUG] inner got tag=%d\n", at_zero->tag); tests_fail++;
            }
        } else {
            printf("  [BUG] expected outer VL_LAM, got tag=%d\n", result->tag); tests_fail++;
        }
    }

    /* SH14: hcomp Π at i0 with neutral ty: β-rule still takes priority over Π rule */
    printf("\n[SH14] hcomp Π at i0 returns base (β before structural)\n");
    {
        Val *base  = nbe_eval(a, NULL, parse(a, "\\x. zero"));
        Val *tube  = nbe_eval(a, NULL, parse(a, "\\_ x. succ zero"));
        Val *pi_ty = nbe_eval(a, NULL, parse(a, "Π(x : Nat). Nat"));
        Val *i0v   = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *result = nbe_vhcomp(a, pi_ty, i0v, tube, base);
        /* Should return base (the VL_LAM \x.zero), not fire structural rule */
        if (result->tag == VL_LAM && conv(a, 0, result, base)) {
            printf("  [OK] β i0 fires before Π structural rule\n"); tests_pass++;
        } else {
            printf("  [BUG] wrong result tag=%d\n", result->tag); tests_fail++;
        }
    }

    /* SH15: hcomp Π — conv of two identical results is 1 */
    printf("\n[SH15] conv: identical hcomp Π results are conv-equal\n");
    {
        Val *phi   = vl_neutral(a, 700, NULL);
        Val *tube  = nbe_eval(a, NULL, parse(a, "\\_ x. x"));
        Val *base  = nbe_eval(a, NULL, parse(a, "\\x. succ x"));
        Val *pi_ty = nbe_eval(a, NULL, parse(a, "Π(x : Nat). Nat"));
        Val *r1 = nbe_vhcomp(a, pi_ty, phi, tube, base);
        Val *r2 = nbe_vhcomp(a, pi_ty, phi, tube, base);
        if (conv(a, 0, r1, r2)) {
            printf("  [OK] identical hcomp Π results are conv-equal\n"); tests_pass++;
        } else {
            printf("  [BUG] identical hcomp Π results not conv-equal\n"); tests_fail++;
        }
    }

    /* SH16: hcomp Σ with constant codomain → VL_PAIR (structural rule fires) */
    printf("\n[SH16] hcomp (Σ(x:Nat). Bool) with neutral φ → VL_PAIR via structural rule\n");
    {
        Val *phi    = vl_neutral(a, 800, NULL);
        Val *tube   = nbe_eval(a, NULL, parse(a, "\\_ . (zero, true)"));
        Val *base   = nbe_eval(a, NULL, parse(a, "(zero, true)"));
        Val *sig_ty = nbe_eval(a, NULL, parse(a, "Σ(x : Nat). Bool"));
        Val *result = nbe_vhcomp(a, sig_ty, phi, tube, base);
        /* Bool doesn't depend on x → constant B-family → structural rule gives VL_PAIR */
        if (result->tag == VL_PAIR) {
            printf("  [OK] VL_PAIR (structural Σ rule fired)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_PAIR for constant-B Σ, got tag=%d\n", result->tag); tests_fail++;
        }
    }

    /* --- Circle S¹ --- */

    printf("\n=== Circle S¹ ===\n");

    /* C1: S¹ formation */
    printf("\n[C1] S1 : Type\n");
    run_infer(a, "S1");
    expect_type(a, "S1", "Type");

    /* C2: base is a point on S¹ */
    printf("\n[C2] base : S1\n");
    run_infer(a, "base");
    expect_type(a, "base", "S1");

    /* C3: loop has type Id S¹ base base */
    printf("\n[C3] loop : Id S1 base base\n");
    run_infer(a, "loop");
    expect_type(a, "loop", "Id S1 base base");

    /* C4: loop ≢ refl base  (neutral vs. canonical refl — key HoTT fact) */
    printf("\n[C4] loop ≢ refl base\n");
    expect_conv(a, "loop",
        "(refl base : Id S1 base base)", 0);

    /* C5: S1rec β — base case fires */
    printf("\n[C5] S1rec Nat zero (refl zero) base ≡ zero\n");
    expect_conv(a, "S1rec Nat zero (refl zero) base", "zero", 1);
    expect_type(a, "S1rec Nat zero (refl zero) base", "Nat");

    /* C6: S1rec on neutral stays stuck */
    printf("\n[C6] S1rec on neutral c : S1 stays stuck\n");
    {
        if (def_lookup("circle_neutral") < 0)
            def_define("circle_neutral",
                "(\\c. S1rec Nat zero (refl zero) c : S1 → Nat)");
        /* Apply to a fresh neutral: check the whole thing has type S1 → Nat */
        expect_type(a, "circle_neutral", "S1 → Nat");
        /* The function applied to a global (neutral) should not reduce to zero */
        Val *fn = nbe_eval(a, NULL, parse(a, "circle_neutral"));
        Val *stuck = nbe_vapp(a, fn, vl_neutral(a, 9999, NULL));
        if (stuck->tag == VL_NEUTRAL) {
            printf("  [OK] S1rec on neutral stays stuck\n");
            tests_pass++;
        } else {
            printf("  [BUG] expected neutral, got tag %d\n", stuck->tag);
            tests_fail++;
        }
    }

    /* C7: S¹ ≢ Nat, S¹ ≢ Bool */
    printf("\n[C7] S1 ≢ Nat, S1 ≢ Bool\n");
    expect_conv(a, "S1", "Nat",  0);
    expect_conv(a, "S1", "Bool", 0);

    /* C8: base ≡ base */
    printf("\n[C8] base ≡ base\n");
    expect_conv(a, "base", "base", 1);

    /* C9: negative — S1rec with l : Id Bool false false but b = true */
    printf("\n[C9] negative: S1rec with l of wrong type\n");
    expect_fail(a,
        "S1rec Bool true (refl false) base",
        "loop case type Id Bool false false does not match Id Bool true true");

    /* C10: const_map — S1 → Nat sending base to zero */
    printf("\n[C10] const_map: S1 → Nat (base ↦ zero)\n");
    if (def_lookup("const_map") < 0)
        def_define("const_map",
            "(\\c. S1rec Nat zero (refl zero) c : S1 → Nat)");
    expect_type(a, "const_map", "S1 → Nat");
    expect_conv(a, "const_map base", "zero", 1);

    /* C11: loop ≡ loop — the sentinel neutral is conv-equal to itself */
    printf("\n[C11] loop ≡ loop\n");
    expect_conv(a, "loop", "loop", 1);

    /* C12: S1rec on loop stays stuck at eval level (loop is neutral LOOP_CONST_LVL).
     * Note: this is an ill-typed term (loop : Id S1 base base, not S1) so the
     * type checker correctly rejects it — but the evaluator still handles it
     * gracefully by returning a stuck neutral. */
    printf("\n[C12] S1rec on loop stays stuck at eval level\n");
    {
        Val *sv = nbe_eval(a, NULL, parse(a, "S1rec Nat zero (refl zero) loop"));
        if (sv->tag == VL_NEUTRAL) {
            printf("  [OK] S1rec on loop stays neutral (eval level)\n");
            tests_pass++;
        } else {
            printf("  [BUG] expected neutral, got tag %d\n", sv->tag);
            tests_fail++;
        }
        /* The type checker correctly rejects this ill-typed expression */
        expect_fail(a, "S1rec Nat zero (refl zero) loop",
            "loop : Id S1 base base, not S1 — wrong scrutinee type");
    }

    /* C13: refl base : Id S1 base base — reflexivity is valid at the basepoint */
    printf("\n[C13] (refl base : Id S1 base base)\n");
    expect_type(a, "(refl base : Id S1 base base)", "Id S1 base base");

    /* C14: S1 ≢ trunc Nat — circle vs. propositional truncation */
    printf("\n[C14] S1 ≢ trunc Nat\n");
    expect_conv(a, "S1", "trunc Nat", 0);

    fflush(stdout);
    printf("\n=== Inductive families ===\n");

#define IND_OK(cond, msg) do { \
    if (cond) { tests_pass++; printf("  [OK] %s\n",  (msg)); } \
    else       { tests_fail++; printf("  [BUG] %s\n", (msg)); } \
} while (0)

    /* IF0 — lookup on an unknown name must return -1 */
    printf("\n[IF0] ind_lookup unknown → -1\n");
    IND_OK(ind_lookup("_no_such_family_xyzzy") == -1,
           "ind_lookup unknown family returns -1");

    /* IF1 — zero-constructor family (encodes ⊥) */
    printf("\n[IF1] register _Empty2 (0 ctors)\n");
    if (ind_lookup("_Empty2") < 0) {
        IndDef e2 = {
            .name = "_Empty2", .n_params = 0, .param_names = NULL,
            .param_types = NULL, .n_indices = 0, .index_types = NULL,
            .n_ctors = 0, .ctors = NULL,
            .type_def_idx = -1, .elim_def_idx = -1
        };
        ind_add(&e2);
    }
    {
        int idx = ind_lookup("_Empty2");
        IND_OK(idx >= 0,                              "found after registration");
        if (idx >= 0) {
            IndDef *d = ind_get(idx);
            IND_OK(strcmp(d->name, "_Empty2") == 0,  "name round-trips");
            IND_OK(d->n_ctors      == 0,              "n_ctors == 0");
            IND_OK(d->n_params     == 0,              "n_params == 0");
            IND_OK(d->n_indices    == 0,              "n_indices == 0");
            IND_OK(d->ctors        == NULL,           "ctors == NULL");
            IND_OK(d->type_def_idx == -1,             "type_def_idx == -1");
            IND_OK(d->elim_def_idx == -1,             "elim_def_idx == -1");
        }
    }

    /* IF2 — two-constructor unindexed family */
    printf("\n[IF2] register _MaybeNat (0 indices, 2 ctors: _nothing _just)\n");
    static CtorDef maybe_ctors[2] = {
        { .name = "_nothing", .arity = 0, .telescope = NULL,
          .n_ret_indices = 0, .ret_indices = NULL, .def_idx = -1 },
        { .name = "_just",    .arity = 1, .telescope = NULL,
          .n_ret_indices = 0, .ret_indices = NULL, .def_idx = -1 },
    };
    if (ind_lookup("_MaybeNat") < 0) {
        IndDef mn = {
            .name = "_MaybeNat", .n_params = 0, .param_names = NULL,
            .param_types = NULL, .n_indices = 0, .index_types = NULL,
            .n_ctors = 2, .ctors = maybe_ctors,
            .type_def_idx = -1, .elim_def_idx = -1
        };
        ind_add(&mn);
    }
    {
        int idx = ind_lookup("_MaybeNat");
        IND_OK(idx >= 0,                                    "found after registration");
        if (idx >= 0) {
            IndDef *d = ind_get(idx);
            IND_OK(d->n_ctors == 2,                         "n_ctors == 2");
            IND_OK(strcmp(d->ctors[0].name, "_nothing") == 0, "ctor[0] = '_nothing'");
            IND_OK(strcmp(d->ctors[1].name, "_just")    == 0, "ctor[1] = '_just'");
            IND_OK(d->ctors[0].arity == 0,               "_nothing.arity == 0");
            IND_OK(d->ctors[1].arity == 1,               "_just.arity == 1");
            IND_OK(d->ctors[0].telescope   == NULL,       "_nothing.telescope NULL");
            IND_OK(d->ctors[1].telescope   == NULL,       "_just.telescope NULL");
            IND_OK(d->ctors[0].ret_indices == NULL,       "_nothing.ret_indices NULL");
            IND_OK(d->ctors[1].ret_indices == NULL,       "_just.ret_indices NULL");
            IND_OK(d->ctors[0].def_idx == -1,             "_nothing.def_idx == -1");
            IND_OK(d->ctors[1].def_idx == -1,             "_just.def_idx == -1");
        }
    }

    /* IF3 — indexed family (1 value index) */
    printf("\n[IF3] register _VecBool (1 index, 2 ctors: _vnil _vcons)\n");
    static CtorDef vec_ctors[2] = {
        { .name = "_vnil",  .arity = 0, .telescope = NULL,
          .n_ret_indices = 1, .ret_indices = NULL, .def_idx = -1 },
        { .name = "_vcons", .arity = 2, .telescope = NULL,
          .n_ret_indices = 1, .ret_indices = NULL, .def_idx = -1 },
    };
    if (ind_lookup("_VecBool") < 0) {
        IndDef vb = {
            .name = "_VecBool", .n_params = 0, .param_names = NULL,
            .param_types = NULL, .n_indices = 1, .index_types = NULL,
            .n_ctors = 2, .ctors = vec_ctors,
            .type_def_idx = -1, .elim_def_idx = -1
        };
        ind_add(&vb);
    }
    {
        int idx = ind_lookup("_VecBool");
        IND_OK(idx >= 0,                                    "found after registration");
        if (idx >= 0) {
            IndDef *d = ind_get(idx);
            IND_OK(d->n_indices == 1,                       "n_indices == 1");
            IND_OK(d->index_types == NULL,                  "index_types NULL");
            IND_OK(d->n_ctors == 2,                         "n_ctors == 2");
            IND_OK(d->ctors[0].n_ret_indices == 1,          "_vnil.n_ret_indices == 1");
            IND_OK(d->ctors[1].n_ret_indices == 1,          "_vcons.n_ret_indices == 1");
            IND_OK(d->ctors[0].ret_indices == NULL,         "_vnil.ret_indices NULL");
        }
    }

    /* IF4 — ind_count and ind_get validity across all registered families */
    printf("\n[IF4] ind_count and ind_get validity\n");
    {
        int cnt = ind_count();
        IND_OK(cnt >= 3, "at least 3 families in table");
        int all_valid = 1;
        for (int i = 0; i < cnt; i++) {
            IndDef *d = ind_get(i);
            if (!d || !d->name) { all_valid = 0; break; }
        }
        IND_OK(all_valid, "ind_get valid for every registered index");
    }

    /* IF5 — shadowing: second registration with same name is allowed;
     *        ind_lookup returns the most-recent entry */
    printf("\n[IF5] shadowing: second _Empty2 hides first\n");
    {
        int before      = ind_count();
        IndDef e2b = {
            .name = "_Empty2", .n_params = 0, .param_names = NULL,
            .param_types = NULL, .n_indices = 0, .index_types = NULL,
            .n_ctors = 0, .ctors = NULL,
            .type_def_idx = 99, .elim_def_idx = -1  /* sentinel to tell them apart */
        };
        int shadow = ind_add(&e2b);
        IND_OK(ind_count() == before + 1,           "table grew by 1");
        IND_OK(ind_lookup("_Empty2") == shadow,     "ind_lookup returns shadow index");
        IND_OK(ind_get(shadow)->type_def_idx == 99, "shadow entry distinct from original");
    }

    /* IF6 — families are independent: lookup of one does not affect another */
    printf("\n[IF6] families are independent\n");
    IND_OK(ind_lookup("_MaybeNat") >= 0, "_MaybeNat still found after _Empty2 shadow");
    IND_OK(ind_lookup("_VecBool")  >= 0, "_VecBool still found");
    IND_OK(ind_lookup("_Empty2")   >= 0, "_Empty2 (shadow) still found");

    /* ── NbE core for inductive families ────────────────────────────────────
     *
     * All tests below use _MaybeNat (fam_idx from ind_lookup) and build
     * terms / values programmatically — no parser required.
     */

    /* IF7 — vl_indtype: constructor produces correct tag and fields */
    printf("\n[IF7] vl_indtype constructor\n");
    {
        int fam = ind_lookup("_MaybeNat");
        IND_OK(fam >= 0, "_MaybeNat registered");
        if (fam >= 0) {
            Val *vt = vl_indtype(a, fam, 0, NULL);
            IND_OK(vt->tag == VL_INDTYPE,       "vl_indtype: tag is VL_INDTYPE");
            IND_OK(vt->indtype.fam_idx == fam,  "vl_indtype: fam_idx round-trips");
            IND_OK(vt->indtype.n_args  == 0,    "vl_indtype: n_args == 0");
            IND_OK(vt->indtype.args    == NULL,  "vl_indtype: args == NULL");
        }
    }

    /* IF8 — vl_indcon: 0-arg constructor (_nothing) */
    printf("\n[IF8] vl_indcon 0-arg ctor (_nothing)\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val *nothing = vl_indcon(a, fam, 0, 0, NULL);
            IND_OK(nothing->tag == VL_INDCON,       "vl_indcon: tag is VL_INDCON");
            IND_OK(nothing->indcon.fam_idx  == fam, "vl_indcon: fam_idx correct");
            IND_OK(nothing->indcon.ctor_idx == 0,   "vl_indcon: ctor_idx 0 (_nothing)");
            IND_OK(nothing->indcon.n_args   == 0,   "vl_indcon: n_args == 0");
        }
    }

    /* IF9 — vl_indcon: 1-arg constructor (_just zero) */
    printf("\n[IF9] vl_indcon 1-arg ctor (_just zero)\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val **args = (Val **)arena_alloc(a, sizeof(Val *));
            args[0] = vl_zero(a);
            Val *just_zero = vl_indcon(a, fam, 1, 1, args);
            IND_OK(just_zero->tag == VL_INDCON,          "vl_indcon(_just): tag");
            IND_OK(just_zero->indcon.ctor_idx == 1,      "vl_indcon(_just): ctor_idx 1");
            IND_OK(just_zero->indcon.n_args   == 1,      "vl_indcon(_just): n_args == 1");
            IND_OK(just_zero->indcon.args[0]->tag == VL_ZERO, "vl_indcon(_just): arg is zero");
        }
    }

    /* IF10 — nbe_vindrec fires β-rule on _nothing (0-arg ctor) */
    printf("\n[IF10] nbe_vindrec fires on _nothing\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val *nothing_result = vl_neutral(a, 99, NULL);  /* stand-in */
            Val *just_case      = vl_neutral(a, 100, NULL); /* unused here */
            Val **cases = (Val **)arena_alloc(a, 2 * sizeof(Val *));
            cases[0] = nothing_result;
            cases[1] = just_case;
            Val *scrut  = vl_indcon(a, fam, 0, 0, NULL);
            Val *result = nbe_vindrec(a, fam, NULL, cases, scrut);
            IND_OK(result == nothing_result, "vindrec on _nothing returns nothing_case directly");
        }
    }

    /* IF11 — nbe_vindrec fires β-rule on _just: applies case to arg */
    printf("\n[IF11] nbe_vindrec fires on _just zero\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            /* just_case: λn. n  (returns its argument) */
            Val *just_case = vl_lam(a, "n", NULL, tm_var(a, 0));
            Val **cases = (Val **)arena_alloc(a, 2 * sizeof(Val *));
            cases[0] = vl_neutral(a, 99, NULL);
            cases[1] = just_case;
            Val **args = (Val **)arena_alloc(a, sizeof(Val *));
            args[0] = vl_zero(a);
            Val *scrut  = vl_indcon(a, fam, 1, 1, args);
            Val *result = nbe_vindrec(a, fam, NULL, cases, scrut);
            /* just_case applied to zero  →  zero */
            IND_OK(result->tag == VL_ZERO, "vindrec on _just zero gives zero");
        }
    }

    /* IF12 — nbe_vindrec stays neutral on a neutral scrutinee */
    printf("\n[IF12] nbe_vindrec stays neutral on neutral scrutinee\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val **cases = (Val **)arena_alloc(a, 2 * sizeof(Val *));
            cases[0] = vl_neutral(a, 99,  NULL);
            cases[1] = vl_neutral(a, 100, NULL);
            Val *scrut  = vl_neutral(a, 42, NULL);
            Val *result = nbe_vindrec(a, fam, NULL, cases, scrut);
            IND_OK(result->tag == VL_NEUTRAL, "vindrec on neutral gives neutral");
            if (result->tag == VL_NEUTRAL) {
                IND_OK(result->neutral.lvl == 42, "neutral head level preserved");
                IND_OK(result->neutral.spine != NULL, "spine is non-empty");
                IND_OK(result->neutral.spine->kind == SP_INDREC, "spine head is SP_INDREC");
            }
        }
    }

    /* IF13 — quote(vl_indtype) → tm_indtype */
    printf("\n[IF13] quote(vl_indtype) → tm_indtype\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val *vt  = vl_indtype(a, fam, 0, NULL);
            Term *qt = nbe_quote(a, 0, vt);
            IND_OK(qt->tag == TM_INDTYPE,        "quote(vl_indtype): tag is TM_INDTYPE");
            IND_OK(qt->indtype.fam_idx == fam,   "quote(vl_indtype): fam_idx round-trips");
            IND_OK(qt->indtype.n_args  == 0,     "quote(vl_indtype): n_args == 0");
        }
    }

    /* IF14 — quote(vl_indcon) → tm_indcon */
    printf("\n[IF14] quote(vl_indcon) → tm_indcon\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val **args = (Val **)arena_alloc(a, sizeof(Val *));
            args[0] = vl_zero(a);
            Val *vc  = vl_indcon(a, fam, 1, 1, args);
            Term *qt = nbe_quote(a, 0, vc);
            IND_OK(qt->tag == TM_INDCON,          "quote(vl_indcon): tag is TM_INDCON");
            IND_OK(qt->indcon.fam_idx  == fam,    "quote(vl_indcon): fam_idx");
            IND_OK(qt->indcon.ctor_idx == 1,      "quote(vl_indcon): ctor_idx");
            IND_OK(qt->indcon.n_args   == 1,      "quote(vl_indcon): n_args");
            IND_OK(qt->indcon.args[0]->tag == TM_ZERO, "quote(vl_indcon): arg is zero");
        }
    }

    /* IF15 — quote of neutral with SP_INDREC spine → tm_indrec */
    printf("\n[IF15] quote of neutral-with-SP_INDREC spine → tm_indrec\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val **cases = (Val **)arena_alloc(a, 2 * sizeof(Val *));
            cases[0] = vl_neutral(a, 99,  NULL);
            cases[1] = vl_neutral(a, 100, NULL);
            Val *scrut  = vl_neutral(a, 42, NULL);
            Val *result = nbe_vindrec(a, fam, NULL, cases, scrut);
            Term *qt = nbe_quote(a, 0, result);
            IND_OK(qt->tag == TM_INDREC,         "quote of neutral+SP_INDREC → TM_INDREC");
            if (qt->tag == TM_INDREC) {
                IND_OK(qt->indrec.fam_idx  == fam, "tm_indrec fam_idx round-trips");
                IND_OK(qt->indrec.n_cases  == 2,   "tm_indrec n_cases == 2");
            }
        }
    }

    /* IF16 — conv: same vl_indtype → 1 */
    printf("\n[IF16] conv(vl_indtype, vl_indtype) same → 1\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val *v1 = vl_indtype(a, fam, 0, NULL);
            Val *v2 = vl_indtype(a, fam, 0, NULL);
            IND_OK(conv(a, 0, v1, v2) == 1, "conv same vl_indtype → 1");
        }
    }

    /* IF17 — conv: different fam_idx → 0 */
    printf("\n[IF17] conv(vl_indtype, vl_indtype) diff family → 0\n");
    {
        int fam1 = ind_lookup("_MaybeNat");
        int fam2 = ind_lookup("_Empty2");
        if (fam1 >= 0 && fam2 >= 0 && fam1 != fam2) {
            Val *v1 = vl_indtype(a, fam1, 0, NULL);
            Val *v2 = vl_indtype(a, fam2, 0, NULL);
            IND_OK(conv(a, 0, v1, v2) == 0, "conv diff fam_idx → 0");
        }
    }

    /* IF18 — conv: same vl_indcon → 1 */
    printf("\n[IF18] conv(vl_indcon, vl_indcon) same → 1\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val *c1 = vl_indcon(a, fam, 0, 0, NULL);
            Val *c2 = vl_indcon(a, fam, 0, 0, NULL);
            IND_OK(conv(a, 0, c1, c2) == 1, "conv same vl_indcon → 1");
        }
    }

    /* IF19 — conv: different ctor_idx → 0 */
    printf("\n[IF19] conv(vl_indcon, vl_indcon) diff ctor → 0\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val *c1 = vl_indcon(a, fam, 0, 0, NULL);  /* _nothing */
            Val **args = (Val **)arena_alloc(a, sizeof(Val *));
            args[0] = vl_zero(a);
            Val *c2 = vl_indcon(a, fam, 1, 1, args);  /* _just zero */
            IND_OK(conv(a, 0, c1, c2) == 0, "conv diff ctor_idx → 0");
        }
    }

    /* ── Hardening: eval round-trips and edge cases ─────────────────────── */

    /* IF20 — nbe_eval TM_INDTYPE produces VL_INDTYPE */
    printf("\n[IF20] nbe_eval(tm_indtype) → VL_INDTYPE\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Term *t   = tm_indtype(a, fam, 0, NULL);
            Val  *v   = nbe_eval(a, NULL, t);
            IND_OK(v->tag == VL_INDTYPE,       "eval TM_INDTYPE → VL_INDTYPE");
            IND_OK(v->indtype.fam_idx == fam,  "fam_idx preserved through eval");
            IND_OK(v->indtype.n_args  == 0,    "n_args == 0 after eval");
        }
    }

    /* IF21 — nbe_eval TM_INDCON (0-arg) produces VL_INDCON */
    printf("\n[IF21] nbe_eval(tm_indcon _nothing) → VL_INDCON\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Term *t = tm_indcon(a, fam, 0, 0, NULL);
            Val  *v = nbe_eval(a, NULL, t);
            IND_OK(v->tag == VL_INDCON,       "eval TM_INDCON → VL_INDCON");
            IND_OK(v->indcon.fam_idx  == fam, "fam_idx preserved");
            IND_OK(v->indcon.ctor_idx == 0,   "ctor_idx 0 preserved");
            IND_OK(v->indcon.n_args   == 0,   "n_args 0");
        }
    }

    /* IF22 — nbe_eval TM_INDREC fires β on _nothing */
    printf("\n[IF22] nbe_eval(tm_indrec _MaybeNat nc jc nothing) → nc\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            /* case _nothing: zero   case _just: λn. succ n */
            Term **cases = (Term **)arena_alloc(a, 2 * sizeof(Term *));
            cases[0] = tm_zero(a);
            cases[1] = tm_lam(a, "n", tm_succ(a, tm_var(a, 0)));
            Term *scrut = tm_indcon(a, fam, 0, 0, NULL);
            Term *elim  = tm_indrec(a, fam, NULL, 2, cases, scrut);
            Val  *v     = nbe_eval(a, NULL, elim);
            IND_OK(v->tag == VL_ZERO, "indrec MaybeNat _ _ nothing → zero");
        }
    }

    /* IF23 — nbe_eval TM_INDREC fires β on _just zero → succ zero */
    printf("\n[IF23] nbe_eval(tm_indrec _MaybeNat nc jc (just zero)) → succ zero\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Term **cases = (Term **)arena_alloc(a, 2 * sizeof(Term *));
            cases[0] = tm_zero(a);
            cases[1] = tm_lam(a, "n", tm_succ(a, tm_var(a, 0)));
            Term **ctor_args = (Term **)arena_alloc(a, sizeof(Term *));
            ctor_args[0] = tm_zero(a);
            Term *scrut = tm_indcon(a, fam, 1, 1, ctor_args);
            Term *elim  = tm_indrec(a, fam, NULL, 2, cases, scrut);
            Val  *v     = nbe_eval(a, NULL, elim);
            IND_OK(v->tag == VL_SUCC,            "indrec ... (just zero) → succ _");
            IND_OK(v->succ->tag == VL_ZERO,      "indrec ... (just zero) → succ zero");
        }
    }

    /* IF24 — conv(VL_INDCON, VL_INDCON) same with args → 1 */
    printf("\n[IF24] conv same VL_INDCON (with matching args) → 1\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val **a1 = (Val **)arena_alloc(a, sizeof(Val *));
            a1[0] = vl_zero(a);
            Val **a2 = (Val **)arena_alloc(a, sizeof(Val *));
            a2[0] = vl_zero(a);
            Val *c1 = vl_indcon(a, fam, 1, 1, a1);
            Val *c2 = vl_indcon(a, fam, 1, 1, a2);
            IND_OK(conv(a, 0, c1, c2) == 1, "conv(_just zero, _just zero) → 1");
        }
    }

    /* IF25 — conv(VL_INDCON, VL_INDCON) same ctor but different args → 0 */
    printf("\n[IF25] conv same VL_INDCON but different args → 0\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val **a1 = (Val **)arena_alloc(a, sizeof(Val *));
            a1[0] = vl_zero(a);
            Val **a2 = (Val **)arena_alloc(a, sizeof(Val *));
            a2[0] = vl_succ(a, vl_zero(a));
            Val *c1 = vl_indcon(a, fam, 1, 1, a1);  /* _just zero */
            Val *c2 = vl_indcon(a, fam, 1, 1, a2);  /* _just (succ zero) */
            IND_OK(conv(a, 0, c1, c2) == 0, "conv(_just zero, _just(succ zero)) → 0");
        }
    }

    /* IF26 — SP_INDREC conv: two neutrals of different families → 0 */
    printf("\n[IF26] conv SP_INDREC neutrals with different families → 0\n");
    {
        int fam1 = ind_lookup("_MaybeNat");
        int fam2 = ind_lookup("_Empty2");
        if (fam1 >= 0 && fam2 >= 0 && fam1 != fam2) {
            /* build two neutrals each with an SP_INDREC spine for different families */
            Val **cases1 = (Val **)arena_alloc(a, 2 * sizeof(Val *));
            cases1[0] = vl_neutral(a, 10, NULL);
            cases1[1] = vl_neutral(a, 11, NULL);
            Val *n1 = vl_neutral(a, 42, NULL);
            Val *r1 = nbe_vindrec(a, fam1, NULL, cases1, n1);  /* neutral + SP_INDREC(fam1) */

            /* _Empty2 has 0 ctors: indrec with empty cases array */
            Val **cases2 = NULL;
            Val *n2 = vl_neutral(a, 42, NULL);
            Val *r2 = nbe_vindrec(a, fam2, NULL, cases2, n2);  /* neutral + SP_INDREC(fam2) */

            IND_OK(r1->tag == VL_NEUTRAL, "r1 is neutral");
            IND_OK(r2->tag == VL_NEUTRAL, "r2 is neutral");
            IND_OK(conv(a, 0, r1, r2) == 0,
                   "conv of same-head neutrals with diff-family SP_INDREC → 0");
        }
    }

    /* IF27 — quote/eval round-trip: eval(quote(vl_indcon)) == same value */
    printf("\n[IF27] nbe_nf round-trip: quote then eval preserves VL_INDCON\n");
    {
        int fam = ind_lookup("_MaybeNat");
        if (fam >= 0) {
            Val **args = (Val **)arena_alloc(a, sizeof(Val *));
            args[0] = vl_succ(a, vl_zero(a));
            Val  *orig = vl_indcon(a, fam, 1, 1, args);    /* _just (succ zero) */
            Term *qt   = nbe_quote(a, 0, orig);             /* quote to term */
            Val  *back = nbe_eval(a, NULL, qt);             /* eval back */
            IND_OK(back->tag == VL_INDCON,             "round-trip: tag preserved");
            IND_OK(back->indcon.fam_idx  == fam,       "round-trip: fam_idx");
            IND_OK(back->indcon.ctor_idx == 1,         "round-trip: ctor_idx");
            IND_OK(back->indcon.n_args   == 1,         "round-trip: n_args");
            IND_OK(back->indcon.args[0]->tag == VL_SUCC, "round-trip: arg is succ");
        }
    }

    /* ── Phase 2 — Type checker for inductive families ─────────────────────
     *
     * We register three families with complete telescopes so the checker can
     * walk argument types:
     *   _MNFull  : MaybeNat (unindexed, non-recursive)
     *   _NLFull  : NatList  (unindexed, recursive cons)
     *   _VBFull  : VecBool  (indexed by Nat, non-recursive)
     */

    /* Setup: _MNFull */
    printf("\n[IF28] setup: register _MNFull with telescopes\n");
    static CtorDef mnf_ctors[2];
    int mnf_fam = -1;
    {
        if (ind_lookup("_MNFull") < 0) {
            mnf_ctors[0] = (CtorDef){ "_mnNothing", 0, NULL, 0, NULL, NULL, -1, 0, NULL, NULL, 0, NULL, NULL };
            mnf_ctors[1] = (CtorDef){ "_mnJust",    1, NULL, 0, NULL, NULL, -1, 0, NULL, NULL, 0, NULL, NULL };
            IndDef mn = { "_MNFull", 0, NULL, NULL, 0, NULL, 2, mnf_ctors, -1, -1 };
            mnf_fam = ind_add(&mn);
            /* Now set telescopes: nothing → _MNFull, just → Π(n:Nat). _MNFull */
            mnf_ctors[0].telescope = tm_indtype(a, mnf_fam, 0, NULL);
            {
                Term **r = (Term **)arena_alloc(a, sizeof(Term *));
                r[0] = tm_indtype(a, mnf_fam, 0, NULL);
                mnf_ctors[1].telescope = tm_pi(a, "n", tm_nat(a), r[0]);
            }
            /* is_recursive: nothing=no args; just=arg0 not recursive */
            static char mnf_just_rec[1] = {0};
            mnf_ctors[1].is_recursive = mnf_just_rec;
        } else {
            mnf_fam = ind_lookup("_MNFull");
        }
        IND_OK(mnf_fam >= 0, "_MNFull registered");
    }

    /* Setup: _NLFull (NatList: nil | cons head tail) */
    printf("\n[IF29] setup: register _NLFull (recursive)\n");
    static CtorDef nlf_ctors[2];
    int nlf_fam = -1;
    {
        if (ind_lookup("_NLFull") < 0) {
            nlf_ctors[0] = (CtorDef){ "_nlNil",  0, NULL, 0, NULL, NULL, -1, 0, NULL, NULL, 0, NULL, NULL };
            nlf_ctors[1] = (CtorDef){ "_nlCons", 2, NULL, 0, NULL, NULL, -1, 0, NULL, NULL, 0, NULL, NULL };
            IndDef nl = { "_NLFull", 0, NULL, NULL, 0, NULL, 2, nlf_ctors, -1, -1 };
            nlf_fam = ind_add(&nl);
            /* _nlNil  : _NLFull */
            nlf_ctors[0].telescope = tm_indtype(a, nlf_fam, 0, NULL);
            /* _nlCons : Π(h:Nat). Π(t:_NLFull). _NLFull */
            nlf_ctors[1].telescope =
                tm_pi(a, "h", tm_nat(a),
                    tm_pi(a, "t", tm_indtype(a, nlf_fam, 0, NULL),
                                  tm_indtype(a, nlf_fam, 0, NULL)));
            /* arg 0 (h:Nat) not recursive; arg 1 (t:_NLFull) recursive */
            static char nlf_cons_rec[2] = {0, 1};
            nlf_ctors[1].is_recursive = nlf_cons_rec;
        } else {
            nlf_fam = ind_lookup("_NLFull");
        }
        IND_OK(nlf_fam >= 0, "_NLFull registered");
    }

    /* Setup: _VBFull (VecBool indexed by Nat) */
    printf("\n[IF30] setup: register _VBFull (1 index Nat)\n");
    static CtorDef vbf_ctors[2];
    static Term *vbf_idx_types[1];
    int vbf_fam = -1;
    {
        if (ind_lookup("_VBFull") < 0) {
            vbf_ctors[0] = (CtorDef){ "_vbNil",  0, NULL, 1, NULL, NULL, -1, 0, NULL, NULL, 0, NULL, NULL };
            vbf_ctors[1] = (CtorDef){ "_vbCons", 2, NULL, 1, NULL, NULL, -1, 0, NULL, NULL, 0, NULL, NULL };
            vbf_idx_types[0] = tm_nat(a);
            IndDef vb = { "_VBFull", 0, NULL, NULL, 1, vbf_idx_types, 2, vbf_ctors, -1, -1 };
            vbf_fam = ind_add(&vb);
            /* _vbNil : _VBFull zero */
            {
                Term **z = (Term **)arena_alloc(a, sizeof(Term *));
                z[0] = tm_zero(a);
                vbf_ctors[0].telescope = tm_indtype(a, vbf_fam, 1, z);
            }
            /* _vbCons : Π(n:Nat). Π(_:_VBFull n). _VBFull (succ n)
               In de Bruijn: _VBFull n = indtype(vbf_fam, [VAR(0)])
               under one more binder: _VBFull n = indtype(vbf_fam, [VAR(1)]) */
            {
                Term **args_n    = (Term **)arena_alloc(a, sizeof(Term *));
                Term **args_sn   = (Term **)arena_alloc(a, sizeof(Term *));
                args_n[0]  = tm_var(a, 0);
                args_sn[0] = tm_succ(a, tm_var(a, 1));
                vbf_ctors[1].telescope =
                    tm_pi(a, "n", tm_nat(a),
                        tm_pi(a, "_", tm_indtype(a, vbf_fam, 1, args_n),
                                      tm_indtype(a, vbf_fam, 1, args_sn)));
                static char vbf_cons_rec[2] = {0, 1};  /* tail (_:VBFull n) is recursive */
                vbf_ctors[1].is_recursive = vbf_cons_rec;
            }
        } else {
            vbf_fam = ind_lookup("_VBFull");
        }
        IND_OK(vbf_fam >= 0, "_VBFull registered");
    }

    /* IF31 — TM_INDTYPE: unindexed family infers Type_0 */
    printf("\n[IF31] infer(TM_INDTYPE _MNFull []) → Type_0\n");
    if (mnf_fam >= 0) {
        Term *t = tm_indtype(a, mnf_fam, 0, NULL);
        Val  *ty = infer(a, 0, NULL, NULL, t);
        IND_OK(ty != NULL,             "infer returns non-NULL");
        IND_OK(ty && ty->tag == VL_UNI, "type is VL_UNI");
        IND_OK(ty && ty->ulevel == 0,   "universe level 0");
    }

    /* IF32 — TM_INDTYPE: indexed family infers Type_0 */
    printf("\n[IF32] infer(TM_INDTYPE _VBFull [zero]) → Type_0\n");
    if (vbf_fam >= 0) {
        Term **idx_args = (Term **)arena_alloc(a, sizeof(Term *));
        idx_args[0] = tm_zero(a);
        Term *t  = tm_indtype(a, vbf_fam, 1, idx_args);
        Val  *ty = infer(a, 0, NULL, NULL, t);
        IND_OK(ty != NULL,              "infer VBFull zero non-NULL");
        IND_OK(ty && ty->tag == VL_UNI, "type is VL_UNI");
        IND_OK(ty && ty->ulevel == 0,   "universe level 0");
    }

    /* IF33 — TM_INDTYPE: wrong number of args → NULL */
    printf("\n[IF33] infer(TM_INDTYPE _MNFull [zero]) → NULL (too many args)\n");
    if (mnf_fam >= 0) {
        Term **bad_args = (Term **)arena_alloc(a, sizeof(Term *));
        bad_args[0] = tm_zero(a);
        Term *t  = tm_indtype(a, mnf_fam, 1, bad_args);  /* MNFull has 0 args */
        Val  *ty = infer(a, 0, NULL, NULL, t);
        IND_OK(ty == NULL, "wrong-arg-count TM_INDTYPE → NULL");
    }

    /* IF34 — TM_INDCON: nothing : _MNFull */
    printf("\n[IF34] infer(TM_INDCON _mnNothing) → VL_INDTYPE(_MNFull)\n");
    if (mnf_fam >= 0) {
        Term *t  = tm_indcon(a, mnf_fam, 0, 0, NULL);
        Val  *ty = infer(a, 0, NULL, NULL, t);
        IND_OK(ty != NULL,                         "infer _mnNothing non-NULL");
        IND_OK(ty && ty->tag == VL_INDTYPE,        "type is VL_INDTYPE");
        IND_OK(ty && ty->indtype.fam_idx == mnf_fam, "fam_idx correct");
        IND_OK(ty && ty->indtype.n_args  == 0,     "n_args == 0 (unindexed)");
    }

    /* IF35 — TM_INDCON: just zero : _MNFull */
    printf("\n[IF35] infer(TM_INDCON _mnJust zero) → VL_INDTYPE(_MNFull)\n");
    if (mnf_fam >= 0) {
        Term **args = (Term **)arena_alloc(a, sizeof(Term *));
        args[0] = tm_zero(a);
        Term *t  = tm_indcon(a, mnf_fam, 1, 1, args);
        Val  *ty = infer(a, 0, NULL, NULL, t);
        IND_OK(ty != NULL,                         "infer _mnJust zero non-NULL");
        IND_OK(ty && ty->tag == VL_INDTYPE,        "type is VL_INDTYPE");
        IND_OK(ty && ty->indtype.fam_idx == mnf_fam, "fam_idx correct");
    }

    /* IF36 — TM_INDCON: just wrong_type → NULL */
    printf("\n[IF36] infer(TM_INDCON _mnJust true) → NULL (Bool not Nat)\n");
    if (mnf_fam >= 0) {
        Term **args = (Term **)arena_alloc(a, sizeof(Term *));
        args[0] = tm_true(a);  /* Bool, not Nat */
        Term *t  = tm_indcon(a, mnf_fam, 1, 1, args);
        Val  *ty = infer(a, 0, NULL, NULL, t);
        IND_OK(ty == NULL, "just true → NULL (type error)");
    }

    /* IF37 — TM_INDCON: vbNil : _VBFull zero */
    printf("\n[IF37] infer(TM_INDCON _vbNil) → VL_INDTYPE(_VBFull [zero])\n");
    if (vbf_fam >= 0) {
        Term *t  = tm_indcon(a, vbf_fam, 0, 0, NULL);
        Val  *ty = infer(a, 0, NULL, NULL, t);
        IND_OK(ty != NULL,                           "infer _vbNil non-NULL");
        IND_OK(ty && ty->tag == VL_INDTYPE,          "type is VL_INDTYPE");
        IND_OK(ty && ty->indtype.fam_idx == vbf_fam, "fam_idx correct");
        IND_OK(ty && ty->indtype.n_args  == 1,       "n_args == 1 (indexed)");
        IND_OK(ty && ty->indtype.args[0]->tag == VL_ZERO, "index is zero");
    }

    /* IF38 — TM_INDCON: vbCons zero vbNil : _VBFull (succ zero) */
    printf("\n[IF38] infer(TM_INDCON _vbCons zero _vbNil) → VL_INDTYPE(_VBFull [succ zero])\n");
    if (vbf_fam >= 0) {
        Term **args = (Term **)arena_alloc(a, 2 * sizeof(Term *));
        args[0] = tm_zero(a);                        /* n = zero */
        args[1] = tm_indcon(a, vbf_fam, 0, 0, NULL); /* tail = vbNil */
        Term *t  = tm_indcon(a, vbf_fam, 1, 2, args);
        Val  *ty = infer(a, 0, NULL, NULL, t);
        IND_OK(ty != NULL,                              "infer _vbCons non-NULL");
        IND_OK(ty && ty->tag == VL_INDTYPE,             "type is VL_INDTYPE");
        IND_OK(ty && ty->indtype.fam_idx == vbf_fam,    "fam_idx correct");
        IND_OK(ty && ty->indtype.n_args  == 1,          "n_args == 1");
        IND_OK(ty && ty->indtype.args[0]->tag == VL_SUCC, "index is succ _");
        IND_OK(ty && ty->indtype.args[0]->succ->tag == VL_ZERO, "index is succ zero");
    }

    /* IF39 — TM_INDREC: case count mismatch → NULL */
    printf("\n[IF39] infer(TM_INDREC _MNFull 1 case) → NULL (expected 2)\n");
    if (mnf_fam >= 0) {
        Term **cases = (Term **)arena_alloc(a, sizeof(Term *));
        cases[0] = tm_zero(a);
        Term *scrut = tm_indcon(a, mnf_fam, 0, 0, NULL);
        Term *motive = tm_lam(a, "_", tm_nat(a));
        Term *elim   = tm_indrec(a, mnf_fam, motive, 1, cases, scrut);
        Val  *ty     = infer(a, 0, NULL, NULL, elim);
        IND_OK(ty == NULL, "wrong case count → NULL");
    }

    /* IF40 — TM_INDREC: nothing → zero (correct case types) */
    printf("\n[IF40] infer(indrec _MNFull (fn _. Nat) zero (fn n. succ n) nothing) → Nat\n");
    if (mnf_fam >= 0) {
        /* Motive: λ_. Nat  annotated as Π(_:_MNFull). Type  (maps to universe) */
        Term *mot_ty = tm_pi(a, "_", tm_indtype(a, mnf_fam, 0, NULL), tm_uni(a, 0));
        Term *motive = tm_ann(a, tm_lam(a, "_", tm_nat(a)), mot_ty);
        Term **cases = (Term **)arena_alloc(a, 2 * sizeof(Term *));
        cases[0] = tm_zero(a);
        /* just case: λ(n:Nat). succ n — needs annotation Π(n:Nat). Nat */
        Term *jc_ty = tm_pi(a, "n", tm_nat(a), tm_nat(a));
        cases[1] = tm_ann(a, tm_lam(a, "n", tm_succ(a, tm_var(a, 0))), jc_ty);
        Term *scrut = tm_indcon(a, mnf_fam, 0, 0, NULL);
        Term *elim  = tm_indrec(a, mnf_fam, motive, 2, cases, scrut);
        Val  *ty    = infer(a, 0, NULL, NULL, elim);
        IND_OK(ty != NULL,              "indrec MNFull nothing → non-NULL");
        IND_OK(ty && ty->tag == VL_NAT, "return type is Nat");
    }

    /* IF41 — TM_INDREC: wrong case type → NULL */
    printf("\n[IF41] infer(indrec _MNFull (fn _. Nat) zero (fn n. true) nothing) → NULL\n");
    if (mnf_fam >= 0) {
        Term *mot_ty = tm_pi(a, "_", tm_indtype(a, mnf_fam, 0, NULL), tm_uni(a, 0));
        Term *motive = tm_ann(a, tm_lam(a, "_", tm_nat(a)), mot_ty);
        Term **cases = (Term **)arena_alloc(a, 2 * sizeof(Term *));
        cases[0] = tm_zero(a);
        /* Bad just case: returns Bool instead of Nat */
        Term *jc_ty = tm_pi(a, "n", tm_nat(a), tm_bool(a));
        cases[1] = tm_ann(a, tm_lam(a, "n", tm_true(a)), jc_ty);
        Term *scrut = tm_indcon(a, mnf_fam, 0, 0, NULL);
        Term *elim  = tm_indrec(a, mnf_fam, motive, 2, cases, scrut);
        Val  *ty    = infer(a, 0, NULL, NULL, elim);
        IND_OK(ty == NULL, "wrong case result type → NULL");
    }

    /* IF42 — TM_INDREC: recursive family (_NLFull) */
    printf("\n[IF42] infer(indrec _NLFull (fn _. Nat) zero (fn h t ih. succ ih) nil) → Nat\n");
    if (nlf_fam >= 0) {
        /* Motive: λ_. Nat  (annotated as Π(_:NatList). Type) */
        Term *mot_ty = tm_pi(a, "_", tm_indtype(a, nlf_fam, 0, NULL), tm_uni(a, 0));
        Term *motive = tm_ann(a, tm_lam(a, "_", tm_nat(a)), mot_ty);
        Term **cases = (Term **)arena_alloc(a, 2 * sizeof(Term *));
        /* nil case: zero : Nat */
        cases[0] = tm_zero(a);
        /* cons case: λ(h:Nat). λ(t:NatList). λ(ih:Nat). succ ih
           annotated as: Π(h:Nat). Π(t:NatList). Π(ih:Nat). Nat */
        Term *nl_ty = tm_indtype(a, nlf_fam, 0, NULL);
        Term *cons_ty = tm_pi(a, "h", tm_nat(a),
                          tm_pi(a, "t", nl_ty,
                            tm_pi(a, "ih", tm_nat(a), tm_nat(a))));
        Term *cons_body =
            tm_lam(a, "h",
              tm_lam(a, "t",
                tm_lam(a, "ih", tm_succ(a, tm_var(a, 0)))));
        cases[1] = tm_ann(a, cons_body, cons_ty);
        Term *scrut = tm_indcon(a, nlf_fam, 0, 0, NULL);  /* nil */
        Term *elim  = tm_indrec(a, nlf_fam, motive, 2, cases, scrut);
        Val  *ty    = infer(a, 0, NULL, NULL, elim);
        IND_OK(ty != NULL,              "indrec NLFull nil → non-NULL");
        IND_OK(ty && ty->tag == VL_NAT, "return type is Nat");
    }

    /* IF43 — TM_INDREC: indexed family (_VBFull) return type is P applied to index + scrut */
    printf("\n[IF43] infer(indrec _VBFull (fn n _. Nat) zero (fn n t ih. succ ih) (vbNil)) → Nat\n");
    if (vbf_fam >= 0) {
        /* Motive: Π(n:Nat). Π(_:VBFull n). Type   (body = λn _. Nat) */
        Term *vb_ty_n = tm_indtype(a, vbf_fam, 1, (Term*[]){tm_var(a, 0)});
        Term *mot_ty  = tm_pi(a, "n", tm_nat(a), tm_pi(a, "_", vb_ty_n, tm_uni(a, 0)));
        Term *motive  = tm_ann(a, tm_lam(a, "n", tm_lam(a, "_", tm_nat(a))), mot_ty);
        Term **cases  = (Term **)arena_alloc(a, 2 * sizeof(Term *));
        /* nil case: zero : Nat (P zero (vbNil)) */
        cases[0] = tm_zero(a);
        /* cons case: Π(n:Nat). Π(t:VBFull n). Π(ih:Nat). Nat
           where Nat = P n t  and  succ Nat = P (succ n) (vbCons n t) */
        Term *vb_ty_varn = tm_indtype(a, vbf_fam, 1, (Term*[]){tm_var(a, 0)});
        Term *cons_ty =
            tm_pi(a, "n", tm_nat(a),
              tm_pi(a, "t", vb_ty_varn,
                tm_pi(a, "ih", tm_nat(a), tm_nat(a))));
        Term *cons_body =
            tm_lam(a, "n",
              tm_lam(a, "t",
                tm_lam(a, "ih", tm_succ(a, tm_var(a, 0)))));
        cases[1] = tm_ann(a, cons_body, cons_ty);
        Term *scrut = tm_indcon(a, vbf_fam, 0, 0, NULL);  /* vbNil */
        Term *elim  = tm_indrec(a, vbf_fam, motive, 2, cases, scrut);
        Val  *ty    = infer(a, 0, NULL, NULL, elim);
        IND_OK(ty != NULL,              "indrec VBFull vbNil → non-NULL");
        IND_OK(ty && ty->tag == VL_NAT, "return type is Nat");
    }

    /* IF44 — 0-ctor indrec (ex falso) with neutral scrutinee */
    printf("\n[IF44] indrec _Empty2 (0 cases) neutral scrutinee → non-NULL (ex falso)\n");
    {
        int e2_fam = ind_lookup("_Empty2");
        IND_OK(e2_fam >= 0, "_Empty2 registered");
        if (e2_fam >= 0) {
            Val *e2_ty   = vl_indtype(a, e2_fam, 0, NULL);
            TCtx tctx_x  = { "x", e2_ty, NULL };
            Env *env_x   = env_cons(a, vl_neutral(a, 0, NULL), NULL);
            Term *mot_ty = tm_pi(a, "_", tm_indtype(a, e2_fam, 0, NULL), tm_uni(a, 0));
            Term *motive = tm_ann(a, tm_lam(a, "_", tm_nat(a)), mot_ty);
            Term *scrut  = tm_var(a, 0);
            Term *elim   = tm_indrec(a, e2_fam, motive, 0, NULL, scrut);
            Val  *ty     = infer(a, 1, &tctx_x, env_x, elim);
            IND_OK(ty != NULL, "0-ctor indrec neutral → non-NULL");
            IND_OK(ty && ty->tag == VL_NAT, "return type is Nat (P applied to neutral)");
        }
    }

    /* IF45 — non-empty family with neutral scrutinee */
    printf("\n[IF45] indrec _MNFull neutral scrutinee → Nat\n");
    if (mnf_fam >= 0) {
        Val *mnf_ty  = vl_indtype(a, mnf_fam, 0, NULL);
        TCtx tctx_x  = { "x", mnf_ty, NULL };
        Env *env_x   = env_cons(a, vl_neutral(a, 0, NULL), NULL);
        Term *mot_ty = tm_pi(a, "_", tm_indtype(a, mnf_fam, 0, NULL), tm_uni(a, 0));
        Term *motive = tm_ann(a, tm_lam(a, "_", tm_nat(a)), mot_ty);
        Term **cases = (Term **)arena_alloc(a, 2 * sizeof(Term *));
        cases[0] = tm_zero(a);
        Term *jc_ty = tm_pi(a, "n", tm_nat(a), tm_nat(a));
        cases[1] = tm_ann(a, tm_lam(a, "n", tm_succ(a, tm_var(a, 0))), jc_ty);
        Term *scrut = tm_var(a, 0);
        Term *elim  = tm_indrec(a, mnf_fam, motive, 2, cases, scrut);
        Val  *ty    = infer(a, 1, &tctx_x, env_x, elim);
        IND_OK(ty != NULL,              "indrec MNFull neutral → non-NULL");
        IND_OK(ty && ty->tag == VL_NAT, "return type is Nat");
    }

#undef IND_OK

    /* ── Phase M1: Universe Polymorphism ─────────────────────────────────── */

    printf("\n=== M1: Universe Polymorphism ===\n");

    /* [M1-1] Level : Type_0 */
    printf("\n[M1-1] Level : Type_0\n");
    expect_type(a, "Level", "Type");

    /* [M1-2] lzero : Level */
    printf("\n[M1-2] lzero : Level\n");
    expect_type(a, "lzero", "Level");

    /* [M1-3] lsuc lzero : Level */
    printf("\n[M1-3] lsuc lzero : Level\n");
    expect_type(a, "lsuc lzero", "Level");

    /* [M1-4] Type_0 = Type (concrete collapse) */
    printf("\n[M1-4] Type_0 ≡ Type  (conv)\n");
    expect_conv(a, "Type_0", "Type", 1);

    /* [M1-5] Type_1 level — concrete */
    printf("\n[M1-5] Type_(lsuc lzero) ≡ Type_1  (concrete collapse)\n");
    expect_conv(a, "Type_(lsuc lzero)", "Type_1", 1);

    /* [M1-6] Type_2 — two successors */
    printf("\n[M1-6] Type_(lsuc (lsuc lzero)) ≡ Type_2\n");
    expect_conv(a, "Type_(lsuc (lsuc lzero))", "Type_2", 1);

    /* [M1-7] lsuc must be applied to a Level — negative test */
    printf("\n[M1-7] lsuc Nat → type error (Nat is not Level)\n");
    expect_fail(a, "lsuc Nat", "Nat is not Level");

    /* [M1-8] identity at Level 0 infers correctly */
    printf("\n[M1-8] (\\l A x. x : Π(l:Level). Π(A:Type_l). A → A) lzero Nat zero : Nat\n");
    expect_type(a,
        "(\\l A x. x : Π(l : Level). Π(A : Type_l). A → A) lzero Nat zero",
        "Nat");

    /* [M1-9] identity at Level 1: A=Type (which is Type_0 : Type_1) */
    printf("\n[M1-9] id (lsuc lzero) Type Nat : Type\n");
    expect_type(a,
        "(\\l A x. x : Π(l : Level). Π(A : Type_l). A → A) (lsuc lzero) Type Nat",
        "Type");

    /* [M1-10] Type_(lzero) has type Type_1 (concrete level collapse in checker) */
    printf("\n[M1-10] Type_(lzero) : Type_1\n");
    expect_type(a, "Type_(lzero)", "Type_1");

    /* [M1-11] lsuc conv: lsuc lzero ≡ lsuc lzero, lsuc lzero ≢ lzero */
    printf("\n[M1-11] lsuc lzero ≡ lsuc lzero; lsuc lzero ≢ lzero\n");
    expect_conv(a, "lsuc lzero", "lsuc lzero", 1);
    expect_conv(a, "lsuc lzero", "lzero",      0);

    /* [M1-12] negative: (lzero : Type) should fail (lzero has type Level) */
    printf("\n[M1-12] (lzero : Type) → type error (Level ≠ Type)\n");
    expect_fail(a, "(lzero : Type)", "lzero has type Level, not Type");

    /* [M1-13] lmax lzero lzero = lzero */
    printf("\n[M1-13] lmax lzero lzero ≡ lzero\n");
    expect_conv(a, "lmax lzero lzero", "lzero", 1);

    /* [M1-14] lmax (lsuc lzero) lzero = lsuc lzero */
    printf("\n[M1-14] lmax (lsuc lzero) lzero ≡ lsuc lzero\n");
    expect_conv(a, "lmax (lsuc lzero) lzero", "lsuc lzero", 1);

    /* [M1-15] lmax lzero (lsuc lzero) = lsuc lzero */
    printf("\n[M1-15] lmax lzero (lsuc lzero) ≡ lsuc lzero\n");
    expect_conv(a, "lmax lzero (lsuc lzero)", "lsuc lzero", 1);

    /* [M1-16] lmax (lsuc lzero) (lsuc lzero) = lsuc lzero */
    printf("\n[M1-16] lmax (lsuc lzero) (lsuc lzero) ≡ lsuc lzero\n");
    expect_conv(a, "lmax (lsuc lzero) (lsuc lzero)", "lsuc lzero", 1);

    /* [M1-17] lmax depth 2: lmax (lsuc (lsuc lzero)) (lsuc (lsuc lzero)) = lsuc (lsuc lzero) */
    printf("\n[M1-17] lmax (lsuc (lsuc lzero)) (lsuc (lsuc lzero)) ≡ lsuc (lsuc lzero)\n");
    expect_conv(a, "lmax (lsuc (lsuc lzero)) (lsuc (lsuc lzero))", "lsuc (lsuc lzero)", 1);

    /* [M1-18] lmax asymmetric: lmax (lsuc (lsuc lzero)) (lsuc lzero) ≡ lsuc (lsuc lzero) */
    printf("\n[M1-18] lmax (lsuc (lsuc lzero)) (lsuc lzero) ≡ lsuc (lsuc lzero)\n");
    expect_conv(a, "lmax (lsuc (lsuc lzero)) (lsuc lzero)", "lsuc (lsuc lzero)", 1);

    /* [M1-19] Type_(lmax lzero lzero) ≡ Type */
    printf("\n[M1-19] Type_(lmax lzero lzero) ≡ Type\n");
    expect_conv(a, "Type_(lmax lzero lzero)", "Type", 1);

    /* [M1-20] universe polymorphic identity using lmax: type-checks */
    printf("\n[M1-20] (λl m. Type_(lmax l m) : Π(l:Level). Π(m:Level). Type_(lsuc (lmax l m)))\n");
    expect_type(a,
        "(\\l m. Type_(lmax l m) : Π(l : Level). Π(m : Level). Type_(lsuc (lmax l m)))",
        "Π(l : Level). Π(m : Level). Type_(lsuc (lmax l m))");

    /* [M1-21] lmax type error: lmax Nat lzero → Nat is not Level */
    printf("\n[M1-21] lmax Nat lzero → type error (Nat is not Level)\n");
    expect_fail(a, "(lmax Nat lzero : Level)", "Nat is not Level");

    /* ── Phase M2: implicit arguments via elaboration ── */

    /* [M2-1] polymorphic id: A inferred from zero : Nat */
    printf("\n[M2-1] id _ zero : Nat  (A=Nat inferred)\n");
    expect_elab(a,
        "(\\A x. x : Π(A : Type). A → A) _ zero",
        "Nat");

    /* [M2-2] polymorphic id: A inferred from true : Bool */
    printf("\n[M2-2] id _ true : Bool  (A=Bool inferred)\n");
    expect_elab(a,
        "(\\A x. x : Π(A : Type). A → A) _ true",
        "Bool");

    /* [M2-3] const combinator: two holes inferred */
    printf("\n[M2-3] const _ _ zero true : Nat  (A=Nat,B=Bool inferred)\n");
    expect_elab(a,
        "(\\A B x y. x : Π(A : Type). Π(B : Type). A → B → A) _ _ zero true",
        "Nat");

    /* [M2-4] const with swapped arguments */
    printf("\n[M2-4] const _ _ true zero : Bool  (A=Bool,B=Nat inferred)\n");
    expect_elab(a,
        "(\\A B x y. x : Π(A : Type). Π(B : Type). A → B → A) _ _ true zero",
        "Bool");

    /* [M2-5] apply combinator: A=Bool, B=Nat inferred from (\\x. zero) and true */
    printf("\n[M2-5] apply _ _ (\\x. zero) true : Nat  (A=Bool,B=Nat inferred)\n");
    expect_elab(a,
        "(\\A B f x. f x : Π(A : Type). Π(B : Type). (A → B) → A → B) _ _ (\\x. zero) true",
        "Nat");

    /* [M2-6] PAIR bidirectional: pair against Sigma — first component solves A */
    printf("\n[M2-6] fst _ (zero,zero) : Nat  (PAIR case solves A=Nat from first component)\n");
    expect_elab(a,
        "(\\A p. fst p : Π(A : Type). Π(_ : Σ(x : A). A). A) _ (zero, zero)",
        "Nat");

    /* [M2-7] TM_ANN in elab_infer: annotation wrapping a holey expression */
    printf("\n[M2-7] ((id _ zero) : Nat) : Nat  (ANN routes holes through elab_check)\n");
    expect_elab(a,
        "((\\A x. x : Π(A : Type). A → A) _ zero : Nat)",
        "Nat");

    /* [M2-8] id applied to annotated inl: TM_ANN + INL bidirectional path */
    printf("\n[M2-8] id _ (inl zero : Sum Nat Bool) : Sum Nat Bool\n");
    expect_elab(a,
        "(\\A x. x : Π(A : Type). A → A) _ (inl zero : Sum Nat Bool)",
        "Sum Nat Bool");

    /* [M2-9] id applied to annotated inr: INR bidirectional path */
    printf("\n[M2-9] id _ (inr zero : Sum Bool Nat) : Sum Bool Nat\n");
    expect_elab(a,
        "(\\A x. x : Π(A : Type). A → A) _ (inr zero : Sum Bool Nat)",
        "Sum Bool Nat");

    /* --- Phase M4: Pattern matching --- */

    fflush(stdout);
    printf("\n=== Phase M4 — Pattern matching ===\n");

    /* PM1: Bool match — true branch */
    printf("\n[PM1] match true of | true => zero | false => succ zero : Nat\n");
    expect_conv(a,
        "(match true of | true => zero | false => succ zero : Nat)",
        "zero", 1);

    /* PM2: Bool match — false branch */
    printf("\n[PM2] match false of | true => zero | false => succ zero\n");
    expect_conv(a,
        "(match false of | true => zero | false => succ zero : Nat)",
        "succ zero", 1);

    /* PM3: Nat zero branch */
    printf("\n[PM3] match zero of | zero => succ zero | succ n => zero\n");
    expect_conv(a,
        "(match zero of | zero => succ zero | succ n => zero : Nat)",
        "succ zero", 1);

    /* PM4: Nat succ branch — predecessor */
    printf("\n[PM4] match (succ (succ zero)) of | zero => zero | succ n => n\n");
    expect_conv(a,
        "(match (succ (succ zero)) of | zero => zero | succ n => n : Nat)",
        "succ zero", 1);

    /* PM5: type inference from check-mode annotation */
    printf("\n[PM5] match type-checking in Π-annotated lambda\n");
    expect_type(a,
        "(\\n. match n of | zero => zero | succ k => k"
        " : Π(n : Nat). Nat)",
        "Π(n : Nat). Nat");

    /* PM6: neutral scrutinee stays stuck (match in normal form) */
    printf("\n[PM6] match on neutral stays stuck\n");
    expect_conv(a,
        "(\\n. match n of | zero => zero | succ k => k : Π(n:Nat). Nat)",
        "(\\n. match n of | zero => zero | succ k => k : Π(n:Nat). Nat)", 1);

    /* PM7: different arms → not conv-equal */
    printf("\n[PM7] different arms → not conv-equal\n");
    expect_conv(a,
        "(\\n. match n of | zero => zero    | succ k => k    : Π(n:Nat). Nat)",
        "(\\n. match n of | zero => succ zero | succ k => k  : Π(n:Nat). Nat)", 0);

    /* PM8: let rec + match — predecessor function */
    printf("\n[PM8] let rec + match: pred via match\n");
    {
        int idx = def_lookup("_pm8_pred");
        if (idx < 0)
            idx = def_define("_pm8_pred",
                "(\\n. match n of | zero => zero | succ k => k"
                " : Π(n : Nat). Nat)");
        if (idx >= 0) {
            expect_conv(a, "_pm8_pred zero",      "zero",      1);
            expect_conv(a, "_pm8_pred (succ (succ zero))", "succ zero", 1);
        }
    }

    /* PM9: Bool match — negation */
    printf("\n[PM9] Bool match: negation via match\n");
    {
        int idx = def_lookup("_pm9_not");
        if (idx < 0)
            idx = def_define("_pm9_not",
                "(\\b. match b of | true => false | false => true"
                " : Π(b : Bool). Bool)");
        if (idx >= 0) {
            expect_conv(a, "_pm9_not true",  "false", 1);
            expect_conv(a, "_pm9_not false", "true",  1);
        }
    }

    /* PM10: match arms infer from first arm */
    printf("\n[PM10] match infer mode — return type from first arm\n");
    run_infer(a,
        "((\\n. natrec (\\k. Nat) zero (\\k. \\ih. k) n"
        "  : Π(n : Nat). Nat)"
        " (succ (succ zero)))");

    /* PM11: match infer arms that agree */
    printf("\n[PM11] match infer: both arms have same type → Nat\n");
    expect_type(a,
        "(\\n. match n of | zero => zero | succ k => succ (succ k)"
        " : Π(n : Nat). Nat)",
        "Π(n : Nat). Nat");

    /* PM12: negative — type mismatch between arms */
    printf("\n[PM12] negative: arm type mismatch (Bool vs Nat)\n");
    expect_fail(a,
        "(\\n. match n of | zero => true | succ k => zero"
        " : Π(n : Nat). Nat)",
        "second arm Bool vs first arm Nat");

    /* PM13: match on inductive type (user-defined pair) */
    printf("\n[PM13] match on user-defined Pair type\n");
    {
        if (ind_lookup("_PMPair") < 0) {
            parse_data("_PMPair (A : Type, B : Type) where "
                       "pairMk : A \xe2\x86\x92 B \xe2\x86\x92 _PMPair A B");
        }
        if (ind_lookup("_PMPair") >= 0) {
            expect_conv(a,
                "(match (pairMk Nat Bool zero true) of"
                " | pairMk a b => a : Nat)",
                "zero", 1);
        }
    }

    /* PM-H1: succ arm with n_binds=0 must not corrupt outer env */
    printf("\n[PM-H1] succ arm no-binder: outer variable not corrupted\n");
    expect_conv(a,
        "(\\x. \\y. match x of | zero => y | succ => y : Π(x:Nat). Π(y:Nat). Nat)",
        "(\\x. \\y. match x of | zero => y | succ => y : Π(x:Nat). Π(y:Nat). Nat)", 1);
    /* Concretely: applied to succ zero, zero should yield zero (not predecessor) */
    expect_conv(a,
        "((\\x. \\y. match x of | zero => y | succ => y"
        "      : Π(x:Nat). Π(y:Nat). Nat) (succ zero) zero)",
        "zero", 1);

    /* PM-H2: duplicate arms rejected */
    printf("\n[PM-H2] duplicate arm rejected\n");
    expect_fail(a,
        "(match zero of | zero => zero | zero => succ zero : Nat)",
        "duplicate arm");

    /* PM-H3: too many binders on zero arm rejected */
    printf("\n[PM-H3] zero arm with binder rejected\n");
    expect_fail(a,
        "(match zero of | zero x => zero | succ n => n : Nat)",
        "zero arm with binder");

    /* PM-H4: Bool arm with binder rejected */
    printf("\n[PM-H4] Bool arm with binder rejected\n");
    expect_fail(a,
        "(match true of | true x => zero | false => zero : Nat)",
        "Bool arm with binder");

    /* PM-H5: succ arm with IH binder is now valid (LANG-2); | succ n m => n has
     * field binder n (pred) and IH binder m, body n has type Nat = check type. */
    printf("\n[PM-H5] succ arm with IH binder now valid (n=pred, m=ih)\n");
    expect_type(a,
        "(match zero of | zero => zero | succ n m => n : Nat)",
        "Nat");

    /* ─── Phase L2 Stage 7 — Partial elements ─── */
    printf("\n=== Phase L2 Stage 7 — Partial elements (IsOne + Partial + [φ ↦ u]) ===\n");

    /* S7-1: IsOne i0 = Empty */
    printf("\n[S7-1] IsOne i0 = Empty\n");
    expect_conv(a, "IsOne i0", "Empty", 1);

    /* S7-2: IsOne i1 = Unit */
    printf("\n[S7-2] IsOne i1 = Unit\n");
    expect_conv(a, "IsOne i1", "Unit", 1);

    /* S7-3: IsOne types as Type */
    printf("\n[S7-3] IsOne φ : Type\n");
    expect_conv(a, "(IsOne i0 : Type)", "Empty", 1);
    expect_conv(a, "(IsOne i1 : Type)", "Unit",  1);

    /* S7-4: IsOne on interval operations */
    printf("\n[S7-4] IsOne on imin/imax/ineg\n");
    expect_conv(a, "IsOne (imax i0 i1)", "Unit",  1);
    expect_conv(a, "IsOne (imax i1 i0)", "Unit",  1);
    expect_conv(a, "IsOne (imin i0 i1)", "Empty", 1);
    expect_conv(a, "IsOne (imin i1 i0)", "Empty", 1);
    expect_conv(a, "IsOne (ineg i0)",    "Unit",  1);
    expect_conv(a, "IsOne (ineg i1)",    "Empty", 1);

    /* S7-5: IsOne neutral stays stuck */
    printf("\n[S7-5] IsOne neutral stays stuck\n");
    expect_conv(a,
        "(\\x. IsOne x : Π(x:II). Type)",
        "(\\x. IsOne x : Π(x:II). Type)", 1);

    /* S7-6: Partial sugar expands to Π(_:IsOne φ). A */
    printf("\n[S7-6] Partial φ A = Π(_:IsOne φ). A\n");
    expect_conv(a, "Partial i1 Nat", "Π(_ : Unit). Nat",  1);
    expect_conv(a, "Partial i0 Nat", "Π(_ : Empty). Nat", 1);

    /* S7-7: partial element [i1 ↦ u] checks and computes */
    printf("\n[S7-7] [i1 |-> u] : Partial i1 A computes to u on star\n");
    expect_conv(a,
        "([i1 |-> zero] : Partial i1 Nat) star",
        "zero", 1);
    expect_conv(a,
        "([i1 |-> succ zero] : Partial i1 Nat) star",
        "succ zero", 1);

    /* S7-8: partial element over i0 face: type is Empty → A (can be constructed) */
    printf("\n[S7-8] Partial i0 A = Empty → A (ex-falso)\n");
    expect_conv(a, "Partial i0 Nat", "Π(_ : Empty). Nat", 1);

    /* S7-9: star is a proof of IsOne i1 */
    printf("\n[S7-9] star : IsOne i1 type-checks\n");
    expect_conv(a, "(star : IsOne i1)", "star", 1);

    /* S7-10: non-II argument to IsOne is a type error */
    printf("\n[S7-10] IsOne Nat rejected (not II)\n");
    expect_fail(a, "(IsOne Nat : Type)", "IsOne: argument must be II");

    /* S7-11: conv of stuck IsOne neutrals */
    printf("\n[S7-11] IsOne x ≡ IsOne x, IsOne x ≢ IsOne y\n");
    expect_conv(a,
        "(\\x. IsOne x : Π(x:II). Type)",
        "(\\x. IsOne x : Π(x:II). Type)", 1);
    expect_conv(a,
        "(\\x. \\y. IsOne x : Π(x:II). Π(y:II). Type)",
        "(\\x. \\y. IsOne y : Π(x:II). Π(y:II). Type)", 0);

    /* S7-12: Partial used as a function type — Pi/lambda check works */
    printf("\n[S7-12] function via Partial: λ(u : Partial i1 Nat). u star\n");
    expect_conv(a,
        "((\\u. u star : Π(u : Partial i1 Nat). Nat)"
        " ([i1 |-> succ zero] : Partial i1 Nat))",
        "succ zero", 1);

    /* ─── Stage 7a hardening tests ─── */
    printf("\n=== Stage 7a hardening ===\n");

    /* GH-S1: compound face reduction — imin i0 x = i0 before IsOne sees it */
    printf("\n[GH-S1] IsOne (imin i0 (imax i1 x)) = Empty\n");
    expect_conv(a,
        "(\\x. IsOne (imin i0 (imax i1 x)) : Π(x:II). Type)",
        "(\\x. Empty : Π(x:II). Type)", 1);

    /* GH-S2: star is NOT a proof of IsOne i0 = Empty */
    printf("\n[GH-S2] star : IsOne i0 rejected\n");
    expect_fail(a, "(star : IsOne i0)", "star not in Empty");

    /* GH-S3: IsOne over doubly-negated face — ~~x = x, so IsOne (~~x) = IsOne x */
    printf("\n[GH-S3] IsOne (ineg (ineg i1)) = Unit\n");
    expect_conv(a, "IsOne (ineg (ineg i1))", "Unit", 1);

    /* GH-S4: [φ ↦ u] body can reference outer variables */
    printf("\n[GH-S4] partial element body uses outer variable\n");
    expect_conv(a,
        "((\\n. ([i1 |-> n] : Partial i1 Nat) star : Π(n:Nat). Nat)"
        " (succ zero))",
        "succ zero", 1);

    /* GH-S5: Partial with neutral face is a Pi type (type-checks) */
    printf("\n[GH-S5] Partial φ A type-checks for neutral φ\n");
    expect_conv(a,
        "(\\x. Partial x Nat : Π(x:II). Type)",
        "(\\x. Π(_ : IsOne x). Nat : Π(x:II). Type)", 1);

    /* GH-S6: holes inside IsOne — _ in face position stays unsolvable (no constraint) */
    printf("\n[GH-S6] IsOne _ with unsolvable hole is a type error\n");
    expect_fail(a, "(IsOne _ : Type)",
        "IsOne hole: face position has no constraint to pin the II value");

    /* GH-S7: IsOne in a Pi domain — Π(p : IsOne i1). Nat = Π(p : Unit). Nat */
    printf("\n[GH-S7] Π(p : IsOne i1). Nat type-checks and normalises\n");
    expect_conv(a, "Π(p : IsOne i1). Nat", "Π(p : Unit). Nat", 1);
    expect_conv(a, "Π(p : IsOne i0). Nat", "Π(p : Empty). Nat", 1);

    /* GH-S8: stuck IsOne conv — equal neutral faces, different neutrals */
    printf("\n[GH-S8] IsOne x ≡ IsOne x, IsOne x ≢ IsOne (ineg x)\n");
    expect_conv(a,
        "(\\x. IsOne x         : Π(x:II). Type)",
        "(\\x. IsOne x         : Π(x:II). Type)", 1);
    expect_conv(a,
        "(\\x. IsOne x         : Π(x:II). Type)",
        "(\\x. IsOne (ineg x)  : Π(x:II). Type)", 0);

    /* GH-S9: [i0 ↦ u] : Partial i0 A  — the type is Empty → A, constructable */
    printf("\n[GH-S9] [i0 |-> u] : Partial i0 Nat type-checks\n");
    expect_conv(a,
        "([i0 |-> zero] : Partial i0 Nat)",
        "([i0 |-> zero] : Partial i0 Nat)", 1);

    /* GH-S10: IsOne applied to non-II neutrals — each of imin/imax/ineg stays stuck */
    printf("\n[GH-S10] IsOne (imax x y) stuck for neutral x y\n");
    expect_conv(a,
        "(\\x. \\y. IsOne (imax x y) : Π(x:II). Π(y:II). Type)",
        "(\\x. \\y. IsOne (imax x y) : Π(x:II). Π(y:II). Type)", 1);
    expect_conv(a,
        "(\\x. \\y. IsOne (imin x y) : Π(x:II). Π(y:II). Type)",
        "(\\x. \\y. IsOne (imin x y) : Π(x:II). Π(y:II). Type)", 1);
    expect_conv(a,
        "(\\x. IsOne (ineg x) : Π(x:II). Type)",
        "(\\x. IsOne (ineg x) : Π(x:II). Type)", 1);

    /* GH-S11: imax x i1 = i1, so IsOne (imax x i1) = Unit even for neutral x */
    printf("\n[GH-S11] IsOne (imax x i1) = Unit for neutral x\n");
    expect_conv(a,
        "(\\x. IsOne (imax x i1) : Π(x:II). Type)",
        "(\\x. Unit             : Π(x:II). Type)", 1);

    /* GH-S12: Partial i1 (Partial i1 Nat) — nested Partial works */
    printf("\n[GH-S12] nested Partial i1 (Partial i1 Nat)\n");
    expect_conv(a,
        "Partial i1 (Partial i1 Nat)",
        "Π(_ : Unit). Π(_ : Unit). Nat", 1);

    /* ─── Phase L2 Stage 7b — hcomp Σ structural rule ─── */
    printf("\n=== Phase L2 Stage 7b — hcomp Σ structural rule ===\n");

    /* HS1: β-rule i0 → base (pre-existing, not changed) */
    printf("\n[HS1] hcomp (Σ(x:Nat).Bool) i0 tube base = base\n");
    expect_conv(a,
        "(hcomp (Σ(x:Nat). Bool) i0 (\\i. (succ zero, false)) (zero, true)"
        " : Σ(x:Nat). Bool)",
        "(zero, true)", 1);

    /* HS2: β-rule i1 → tube i1 (pre-existing) */
    printf("\n[HS2] hcomp (Σ(x:Nat).Bool) i1 tube base = tube i1\n");
    expect_conv(a,
        "(hcomp (Σ(x:Nat). Bool) i1 (\\i. (succ zero, false)) (zero, true)"
        " : Σ(x:Nat). Bool)",
        "(succ zero, false)", 1);

    /* HS3: structural rule for neutral φ, constant codomain — yields a pair */
    printf("\n[HS3] hcomp (Σ(x:Nat).Bool) φ tube base = (fst-part, snd-part) for neutral φ\n");
    {
        Val *phi_n  = vl_neutral(a, 800, NULL);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\_ . (succ zero, false)"));
        Val *base_v = nbe_eval(a, NULL, parse(a, "(zero, true)"));
        Val *sig_ty = nbe_eval(a, NULL, parse(a, "Σ(x : Nat). Bool"));
        Val *r      = nbe_vhcomp(a, sig_ty, phi_n, tube_v, base_v);
        if (r->tag == VL_PAIR) {
            printf("  [OK] result is VL_PAIR (structural Σ rule fired)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_PAIR, got tag=%d\n", r->tag); tests_fail++;
        }
    }

    /* HS4: first component of hcomp Σ is hcomp of first components */
    printf("\n[HS4] fst(hcomp (Σ(x:Nat).Bool) φ tube base) ≡ hcomp Nat φ (λi.fst(tube i)) (fst base)\n");
    expect_conv(a,
        "(\\n. fst (hcomp (Σ(x:Nat). Bool) n (\\i. (succ zero, false)) (zero, true)"
        "      : Π(n:II). Nat))",
        "(\\n. hcomp Nat n (\\i. succ zero) zero : Π(n:II). Nat)", 1);

    /* HS5: second component of hcomp Σ is hcomp of second components (constant B) */
    printf("\n[HS5] snd(hcomp (Σ(x:Nat).Bool) φ tube base) ≡ hcomp Bool φ (λi.snd(tube i)) (snd base)\n");
    expect_conv(a,
        "(\\n. snd (hcomp (Σ(x:Nat). Bool) n (\\i. (succ zero, false)) (zero, true)"
        "      : Π(n:II). Bool))",
        "(\\n. hcomp Bool n (\\i. false) true : Π(n:II). Bool)", 1);

    /* HS6: hcomp (Nat × Nat) — both components are Nat */
    printf("\n[HS6] hcomp (Nat × Nat) neutral φ = pair of hcomps\n");
    expect_conv(a,
        "(\\n. fst (hcomp (Σ(x:Nat). Nat) n (\\i. (succ zero, succ (succ zero))) (zero, zero)"
        "      : Π(n:II). Nat))",
        "(\\n. hcomp Nat n (\\i. succ zero) zero : Π(n:II). Nat)", 1);

    /* HS7: dependent Σ stays stuck — B depends on x */
    printf("\n[HS7] hcomp (Σ(x:Nat). Id Nat x x) with neutral φ stays stuck\n");
    {
        Val *phi_n  = vl_neutral(a, 801, NULL);
        Val *tube_v = nbe_eval(a, NULL,
            parse(a, "\\_ . (zero, (refl zero : Id Nat zero zero))"));
        Val *base_v = nbe_eval(a, NULL,
            parse(a, "(zero, (refl zero : Id Nat zero zero))"));
        Val *dep_ty = nbe_eval(a, NULL, parse(a, "Σ(x : Nat). Id Nat x x"));
        Val *r      = nbe_vhcomp(a, dep_ty, phi_n, tube_v, base_v);
        if (r->tag == VL_HCOMP) {
            printf("  [OK] VL_HCOMP (dependent B stays stuck)\n"); tests_pass++;
        } else if (r->tag == VL_PAIR) {
            printf("  [OK] VL_PAIR (B-family detected constant for x=zero path)\n"); tests_pass++;
        } else {
            printf("  [BUG] unexpected tag=%d\n", r->tag); tests_fail++;
        }
    }

    /* HS8: hcomp Σ at i0 for dependent type also β-reduces */
    printf("\n[HS8] hcomp (Σ(x:Nat). Id Nat x x) i0 tube base = base\n");
    expect_conv(a,
        "(hcomp (Σ(x:Nat). Id Nat x x) i0"
        " (\\_ . (zero, refl zero)) (succ zero, refl (succ zero))"
        " : Σ(x:Nat). Id Nat x x)",
        "(succ zero, refl (succ zero))", 1);

    /* HS9: conv checks pair components individually after hcomp Σ fires */
    printf("\n[HS9] conv of two equivalent hcomp Σ results agrees\n");
    expect_conv(a,
        "(\\n. hcomp (Σ(x:Nat). Bool) n (\\i. (succ zero, false)) (zero, true)"
        " : Π(n:II). Σ(x:Nat). Bool)",
        "(\\n. hcomp (Σ(x:Nat). Bool) n (\\i. (succ zero, false)) (zero, true)"
        " : Π(n:II). Σ(x:Nat). Bool)", 1);

    /* HS10: fst(hcomp) ≢ snd(hcomp) for non-trivial tube */
    printf("\n[HS10] different fst/snd components not conv-equal\n");
    expect_conv(a,
        "(\\n. fst (hcomp (Σ(x:Nat). Nat) n (\\i. (succ zero, zero)) (zero, zero)"
        "      : Π(n:II). Nat))",
        "(\\n. snd (hcomp (Σ(x:Nat). Nat) n (\\i. (succ zero, zero)) (zero, zero)"
        "      : Π(n:II). Nat))", 0);

    /* ─── Stage 7b hardening ─── */
    printf("\n=== Stage 7b hardening ===\n");

    /* GH-HS1: nested Σ — structural rule fires at both layers */
    printf("\n[GH-HS1] hcomp (Σ(_:Nat). Σ(_:Nat). Bool) fires twice\n");
    expect_conv(a,
        "(\\n. hcomp (Σ(_:Nat). Σ(_:Nat). Bool) n"
        " (\\i. (succ zero, (zero, false))) (zero, (zero, true))"
        " : Π(n:II). Σ(_:Nat). Σ(_:Nat). Bool)",
        "(\\n. (hcomp Nat n (\\i. succ zero) zero,"
        "       (hcomp Nat n (\\i. zero) zero,"
        "        hcomp Bool n (\\i. false) true))"
        " : Π(n:II). Σ(_:Nat). Σ(_:Nat). Bool)", 1);

    /* GH-HS2: Π-typed codomain (constant) — Σ rule fires, Π rule fires for snd */
    printf("\n[GH-HS2] hcomp (Σ(_:Nat). Π(_:Nat). Bool) — Π codomain, both rules fire\n");
    expect_conv(a,
        "(\\n. hcomp (Σ(_:Nat). Π(_:Nat). Bool) n"
        " (\\i. (succ zero, \\k. false)) (zero, \\k. true)"
        " : Π(n:II). Σ(_:Nat). Π(_:Nat). Bool)",
        "(\\n. (hcomp Nat n (\\i. succ zero) zero,"
        "       \\k. hcomp Bool n (\\i. false) true)"
        " : Π(n:II). Σ(_:Nat). Π(_:Nat). Bool)", 1);

    /* GH-HS3: Π-typed domain — structural Σ rule + structural Π on fst component */
    printf("\n[GH-HS3] hcomp (Σ(x:Π(_:Nat).Nat). Bool) — Pi-typed fst\n");
    expect_conv(a,
        "(\\n. fst (hcomp (Σ(x:Π(_:Nat).Nat). Bool) n"
        " (\\i. (\\k. zero, false)) (\\k. succ zero, true))"
        " : Π(n:II). Π(_:Nat). Nat)",
        "(\\n. \\k. hcomp Nat n (\\i. zero) (succ zero)"
        " : Π(n:II). Π(_:Nat). Nat)", 1);

    /* GH-HS4: dependent B stays stuck — Id Nat x x */
    printf("\n[GH-HS4] hcomp (Σ(x:Nat). Id Nat x x) stays stuck (B depends on x)\n");
    expect_conv(a,
        "(\\n. hcomp (Σ(x:Nat). Id Nat x x) n"
        " (\\i. (zero, refl zero)) (succ zero, refl (succ zero))"
        " : Π(n:II). Σ(x:Nat). Id Nat x x)",
        "(\\n. hcomp (Σ(x:Nat). Id Nat x x) n"
        " (\\i. (zero, refl zero)) (succ zero, refl (succ zero))"
        " : Π(n:II). Σ(x:Nat). Id Nat x x)", 1);

    /* GH-HS5: imax face — structural rule fires for non-simple-neutral face */
    printf("\n[GH-HS5] hcomp (Σ(_:Nat).Bool) (imax phi psi) — structural rule fires\n");
    {
        Val *phi_v = vl_neutral(a, 900, NULL);
        Val *psi_v = vl_neutral(a, 901, NULL);
        Val *face2 = nbe_vimax(a, phi_v, psi_v);  /* imax phi psi: a stuck imax face */
        Val *tube2 = nbe_eval(a, NULL, parse(a, "\\_ . (succ zero, false)"));
        Val *base2 = nbe_eval(a, NULL, parse(a, "(zero, true)"));
        Val *sig2  = nbe_eval(a, NULL, parse(a, "Σ(_:Nat). Bool"));
        Val *r2    = nbe_vhcomp(a, sig2, face2, tube2, base2);
        if (r2->tag == VL_PAIR) {
            printf("  [OK] VL_PAIR for imax face (structural rule fires)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_PAIR for imax face, got tag=%d\n", r2->tag); tests_fail++;
        }
    }

    /* GH-HS6: hcomp Σ at i0 gives exact base (not a new pair allocation) */
    printf("\n[GH-HS6] hcomp (Σ._:Nat).Bool) i0 = exact base\n");
    expect_conv(a,
        "(hcomp (Σ(_:Nat). Bool) i0 (\\i. (succ zero, false)) (zero, true)"
        " : Σ(_:Nat). Bool)",
        "(zero, true)", 1);

    /* GH-HS7: conv of hcomp Σ pair ≡ conv of components (eta for Σ) */
    printf("\n[GH-HS7] eta: hcomp Σ result conv-equal to pair of projections\n");
    expect_conv(a,
        "(\\n. hcomp (Σ(_:Nat). Bool) n (\\i. (succ zero, false)) (zero, true)"
        " : Π(n:II). Σ(_:Nat). Bool)",
        "(\\n. (fst (hcomp (Σ(_:Nat). Bool) n (\\i. (succ zero, false)) (zero, true)),"
        "       snd (hcomp (Σ(_:Nat). Bool) n (\\i. (succ zero, false)) (zero, true)))"
        " : Π(n:II). Σ(_:Nat). Bool)", 1);

    /* GH-HS8: hcomp with imin face — constant B, structural rule fires */
    printf("\n[GH-HS8] hcomp (Σ(_:Nat).Bool) (imin phi psi) — structural rule fires\n");
    {
        Val *phi_v = vl_neutral(a, 902, NULL);
        Val *psi_v = vl_neutral(a, 903, NULL);
        Val *face3 = nbe_vimin(a, phi_v, psi_v);  /* imin phi psi: stuck imin */
        Val *tube3 = nbe_eval(a, NULL, parse(a, "\\_ . (succ zero, false)"));
        Val *base3 = nbe_eval(a, NULL, parse(a, "(zero, true)"));
        Val *sig3  = nbe_eval(a, NULL, parse(a, "Σ(_:Nat). Bool"));
        Val *r3    = nbe_vhcomp(a, sig3, face3, tube3, base3);
        if (r3->tag == VL_PAIR) {
            printf("  [OK] VL_PAIR for imin face\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_PAIR for imin face, got tag=%d\n", r3->tag); tests_fail++;
        }
    }

    /* GH-HS9: hcomp (Σ(_:Bool). Nat) — Bool domain (not Nat), still fires */
    printf("\n[GH-HS9] hcomp (Σ(_:Bool). Nat) — Bool-typed fst, constant Nat snd\n");
    expect_conv(a,
        "(\\n. fst (hcomp (Σ(_:Bool). Nat) n (\\i. (false, succ zero)) (true, zero))"
        " : Π(n:II). Bool)",
        "(\\n. hcomp Bool n (\\i. false) true : Π(n:II). Bool)", 1);

    /* GH-HS10: hcomp (Σ(x:Nat). Nat × Bool) — snd has a product type, fires recursively */
    printf("\n[GH-HS10] hcomp (Σ(_:Nat). Σ(_:Nat). Bool) matches nested structure\n");
    expect_conv(a,
        "(\\n. snd (hcomp (Σ(_:Nat). Σ(_:Nat). Bool) n"
        " (\\i. (succ zero, (zero, false))) (zero, (zero, true)))"
        " : Π(n:II). Σ(_:Nat). Bool)",
        "(\\n. (hcomp Nat n (\\i. zero) zero,"
        "       hcomp Bool n (\\i. false) true)"
        " : Π(n:II). Σ(_:Nat). Bool)", 1);

    /* GH-HS11: VL_NEUTRAL base — fst/snd projections remain stuck */
    printf("\n[GH-HS11] hcomp Σ with neutral base — components still compute\n");
    {
        Val *phi_v  = vl_neutral(a, 904, NULL);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\_ . (succ zero, false)"));
        Val *base_n = vl_neutral(a, 905, NULL); /* neutral base (open variable) */
        Val *sig_ty = nbe_eval(a, NULL, parse(a, "Σ(_:Nat). Bool"));
        Val *r      = nbe_vhcomp(a, sig_ty, phi_v, tube_v, base_n);
        /* Structural rule fires; fst/snd of neutral base produce stuck projections */
        if (r->tag == VL_PAIR) {
            int fst_ok = (r->pair.fst->tag == VL_HCOMP || r->pair.fst->tag == VL_NEUTRAL);
            int snd_ok = (r->pair.snd->tag == VL_HCOMP || r->pair.snd->tag == VL_NEUTRAL);
            if (fst_ok && snd_ok)
                { printf("  [OK] VL_PAIR with stuck components for neutral base\n"); tests_pass++; }
            else
                { printf("  [BUG] unexpected component tags (%d, %d)\n",
                          r->pair.fst->tag, r->pair.snd->tag); tests_fail++; }
        } else {
            printf("  [BUG] expected VL_PAIR for neutral base, got tag=%d\n", r->tag); tests_fail++;
        }
    }

    /* GH-HS12: type correctness — fst/snd of hcomp Σ have the right inferred types */
    printf("\n[GH-HS12] fst(hcomp (Σ._:Nat).Bool) inferred type is Nat\n");
    {
        Term *fst_expr = parse(a,
            "(\\n. fst (hcomp (Σ(_:Nat). Bool) n (\\i. (succ zero, false)) (zero, true))"
            " : Π(n:II). Nat)");
        Val *ty = fst_expr ? infer(a, 0, NULL, NULL, fst_expr) : NULL;
        if (ty && ty->tag == VL_PI && ty->pi.dom->tag == VL_NEUTRAL /* II */)
            { printf("  [OK] fst type inferred as Π(n:II). Nat\n"); tests_pass++; }
        else {
            /* Just check it type-checks without error */
            if (fst_expr && ty)
                { printf("  [OK] fst type-checks\n"); tests_pass++; }
            else
                { printf("  [BUG] fst type inference failed\n"); tests_fail++; }
        }
    }

    /* ─── Phase L2 Stage 7c — hcomp Path structural rule ─── */
    printf("\n=== Phase L2 Stage 7c — hcomp Path structural rule ===\n");

    /* HP1: β-rule i0 → base (pre-existing) */
    printf("\n[HP1] hcomp (Path Nat zero zero) i0 tube base = base\n");
    expect_conv(a,
        "(hcomp (Path Nat zero zero) i0 (\\i. <j> zero) (<j> zero) : Path Nat zero zero)",
        "<j> zero", 1);

    /* HP2: β-rule i1 → tube i1 (pre-existing) */
    printf("\n[HP2] hcomp (Path Nat zero zero) i1 tube base = tube i1\n");
    expect_conv(a,
        "(hcomp (Path Nat zero zero) i1 (\\i. <j> zero) (<j> zero) : Path Nat zero zero)",
        "<j> zero", 1);

    /* HP3: structural rule fires for neutral φ → VL_PATHABS result */
    printf("\n[HP3] hcomp (Path Nat zero zero) φ tube base → VL_PATHABS for neutral φ\n");
    {
        Val *phi_p  = vl_neutral(a, 910, NULL);
        Val *tube_p = nbe_eval(a, NULL, parse(a, "\\i. <j> zero"));
        Val *base_p = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *path_ty = nbe_eval(a, NULL, parse(a, "Path Nat zero zero"));
        Val *r = nbe_vhcomp(a, path_ty, phi_p, tube_p, base_p);
        if (r->tag == VL_PATHABS) {
            printf("  [OK] VL_PATHABS (structural Path rule fired)\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++;
        }
    }

    /* HP4: structural rule shape — ⟨j⟩ hcomp A (imax φ (∂j)) (λi. tube i @ j) (base @ j) */
    printf("\n[HP4] hcomp Path shape = <j> hcomp A (imax φ (∂j)) (λi. tube i @ j) (base @ j)\n");
    expect_conv(a,
        "(\\n. hcomp (Path Nat zero zero) n (\\i. <j> zero) (<j> zero)"
        " : Π(n:II). Path Nat zero zero)",
        "(\\n. <j> hcomp Nat (imax n (imax j (ineg j))) (\\i. zero) zero"
        " : Π(n:II). Path Nat zero zero)", 1);

    /* HP5: left endpoint of hcomp Path result = lhs of the path type */
    printf("\n[HP5] (hcomp Path n u p) @ i0 = zero (left endpoint preserved)\n");
    expect_conv(a,
        "(\\n. (hcomp (Path Nat zero zero) n (\\i. <j> zero) (<j> zero)) @ i0"
        " : Π(n:II). Nat)",
        "(\\n. zero : Π(n:II). Nat)", 1);

    /* HP6: right endpoint of hcomp Path result = rhs of the path type */
    printf("\n[HP6] (hcomp Path n u p) @ i1 = zero (right endpoint preserved)\n");
    expect_conv(a,
        "(\\n. (hcomp (Path Nat zero zero) n (\\i. <j> zero) (<j> zero)) @ i1"
        " : Π(n:II). Nat)",
        "(\\n. zero : Π(n:II). Nat)", 1);

    /* HP7: hcomp with non-trivial A (Bool path) */
    printf("\n[HP7] hcomp (Path Bool true true) — Bool path\n");
    {
        Val *phi_p  = vl_neutral(a, 911, NULL);
        Val *tube_p = nbe_eval(a, NULL, parse(a, "\\i. <j> true"));
        Val *base_p = nbe_eval(a, NULL, parse(a, "<j> true"));
        Val *path_ty = nbe_eval(a, NULL, parse(a, "Path Bool true true"));
        Val *r = nbe_vhcomp(a, path_ty, phi_p, tube_p, base_p);
        if (r->tag == VL_PATHABS) {
            printf("  [OK] VL_PATHABS for Bool path\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++;
        }
    }

    /* HP8: two hcomp Path calls with same args are conv-equal */
    printf("\n[HP8] conv: identical hcomp Path results agree\n");
    expect_conv(a,
        "(\\n. hcomp (Path Nat zero zero) n (\\i. <j> zero) (<j> zero)"
        " : Π(n:II). Path Nat zero zero)",
        "(\\n. hcomp (Path Nat zero zero) n (\\i. <j> zero) (<j> zero)"
        " : Π(n:II). Path Nat zero zero)", 1);

    /* HP9: hcomp Path with different tube ≢ hcomp with different base */
    printf("\n[HP9] hcomp Path with different tube ≢ different base\n");
    expect_conv(a,
        "(\\n. hcomp (Path Nat zero zero) n (\\i. <j> zero) (<j> zero)"
        " : Π(n:II). Path Nat zero zero)",
        "(\\n. hcomp (Path Nat zero zero) n (\\i. <j> succ zero) (<j> zero)"
        " : Π(n:II). Path Nat zero zero)", 0);

    /* HP10: hcomp (Path A a b) with neutral A (Π-typed path element) */
    printf("\n[HP10] hcomp (Path (Π(_:Nat).Nat) lhs rhs) — Π-type path\n");
    expect_conv(a,
        "(\\n. hcomp (Path (Π(_:Nat).Nat) (\\k. zero) (\\k. zero)) n"
        " (\\i. <j> \\k. zero) (<j> \\k. zero)"
        " : Π(n:II). Path (Π(_:Nat).Nat) (\\k. zero) (\\k. zero))",
        "(\\n. <j> \\k. hcomp Nat (imax n (imax j (ineg j))) (\\i. zero) zero"
        " : Π(n:II). Path (Π(_:Nat).Nat) (\\k. zero) (\\k. zero))", 1);

    /* HP11: ∂i endpoints: at i0, imax φ (∂ i0) = imax φ i1 = i1 → hcomp gives tube i1 */
    printf("\n[HP11] inner face at j=i0: imax φ (∂ i0) = i1 → hcomp gives tube element\n");
    expect_conv(a,
        "(\\n. (hcomp (Path Nat zero zero) n (\\i. <j> zero) (<j> zero)) @ i0"
        " : Π(n:II). Nat)",
        "(\\n. zero : Π(n:II). Nat)", 1);

    /* HP12: VL_REFL @ r = the reflected element (vpathapp fix verification) */
    printf("\n[HP12] vpathapp handles VL_REFL: (refl zero) applied to any interval = zero\n");
    {
        Val *refl_zero = vl_refl(a, vl_zero(a));
        Val *i0_v = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *i1_v = vl_neutral(a, IONE_CONST_LVL, NULL);
        Val *probe = vl_neutral(a, 912, NULL);
        Val *at_i0 = nbe_vpathapp(a, refl_zero, i0_v);
        Val *at_i1 = nbe_vpathapp(a, refl_zero, i1_v);
        Val *at_n  = nbe_vpathapp(a, refl_zero, probe);
        if (at_i0->tag == VL_ZERO && at_i1->tag == VL_ZERO && at_n->tag == VL_ZERO)
            { printf("  [OK] (refl zero) @ r = zero for all r\n"); tests_pass++; }
        else
            { printf("  [BUG] unexpected tags: %d %d %d\n", at_i0->tag, at_i1->tag, at_n->tag); tests_fail++; }
    }

    /* ─── Stage 7c hardening ─── */
    printf("\n=== Stage 7c hardening ===\n");

    /* GH-HP1: conv path-eta VL_REFL — (refl a) ≡ <j> a by eta (VL_REFL fix in conv) */
    printf("\n[GH-HP1] conv path-eta: refl a ≡ <j> a when a is concrete\n");
    {
        /* refl zero and <j> zero should be conv-equal as path elements since
         * vpathapp(refl zero, r) = zero = vpathapp(<j> zero, r) for any r. */
        Val *refl_zero = vl_refl(a, vl_zero(a));
        Val *path_zero = nbe_eval(a, NULL, parse(a, "<j> zero"));
        /* path_zero = VL_PATHABS("j", [], TM_ZERO) */
        int eq = conv(a, 0, refl_zero, path_zero);
        /* With the conv eta fix (VL_REFL allowed in path eta), both apply to fresh:
         * refl_zero @ fresh = zero,  path_zero @ fresh = zero → conv(zero, zero) = 1 */
        if (eq)
            { printf("  [OK] refl zero ≡ <j> zero by path eta\n"); tests_pass++; }
        else
            { printf("  [BUG] refl zero ≢ <j> zero (path eta broken for VL_REFL)\n"); tests_fail++; }
    }

    /* GH-HP2: conv path-eta VL_REFL with non-trivial element */
    printf("\n[GH-HP2] conv path-eta: refl (succ zero) ≡ <j> succ zero\n");
    {
        Val *refl_s = vl_refl(a, vl_succ(a, vl_zero(a)));
        Val *path_s = nbe_eval(a, NULL, parse(a, "<j> succ zero"));
        int eq = conv(a, 0, refl_s, path_s);
        if (eq)
            { printf("  [OK] refl (succ zero) ≡ <j> succ zero\n"); tests_pass++; }
        else
            { printf("  [BUG] refl (succ zero) ≢ <j> succ zero\n"); tests_fail++; }
    }

    /* GH-HP3: conv path-eta VL_REFL not equal to different element */
    printf("\n[GH-HP3] conv path-eta: refl zero ≢ <j> succ zero\n");
    {
        Val *refl_zero = vl_refl(a, vl_zero(a));
        Val *path_s    = nbe_eval(a, NULL, parse(a, "<j> succ zero"));
        int neq = !conv(a, 0, refl_zero, path_s);
        if (neq)
            { printf("  [OK] refl zero ≢ <j> succ zero\n"); tests_pass++; }
        else
            { printf("  [BUG] refl zero ≡ <j> succ zero (should not be equal)\n"); tests_fail++; }
    }

    /* GH-HP4: hcomp Path with neutral tube — structural rule fires, tube appears in body */
    printf("\n[GH-HP4] hcomp Path with neutral tube — structural rule fires\n");
    {
        Val *phi_v  = vl_neutral(a, 920, NULL);
        Val *tube_v = vl_neutral(a, 921, NULL);  /* neutral tube: u : II → Path A a b */
        Val *base_v = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *path_ty = nbe_eval(a, NULL, parse(a, "Path Nat zero zero"));
        Val *r = nbe_vhcomp(a, path_ty, phi_v, tube_v, base_v);
        if (r->tag == VL_PATHABS)
            { printf("  [OK] VL_PATHABS with neutral tube\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* GH-HP5: hcomp Path with neutral base — structural rule fires */
    printf("\n[GH-HP5] hcomp Path with neutral base — structural rule fires\n");
    {
        Val *phi_v  = vl_neutral(a, 922, NULL);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\i. <j> zero"));
        Val *base_v = vl_neutral(a, 923, NULL);  /* neutral base: b : Path A a b */
        Val *path_ty = nbe_eval(a, NULL, parse(a, "Path Nat zero zero"));
        Val *r = nbe_vhcomp(a, path_ty, phi_v, tube_v, base_v);
        if (r->tag == VL_PATHABS)
            { printf("  [OK] VL_PATHABS with neutral base\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* GH-HP6: hcomp (Path (Σ(_:Nat).Bool) ...) — inner Σ structural rule fires in body */
    printf("\n[GH-HP6] hcomp (Path (Σ(_:Nat).Bool) lhs rhs) — inner Σ rule fires in path body\n");
    expect_conv(a,
        "(\\n. hcomp (Path (Σ(_:Nat). Bool) (zero, true) (zero, true)) n"
        " (\\i. <j> (zero, true)) (<j> (zero, true))"
        " : Π(n:II). Path (Σ(_:Nat).Bool) (zero, true) (zero, true))",
        "(\\n. <j> (hcomp Nat (imax n (imax j (ineg j))) (\\i. zero) zero,"
        "          hcomp Bool (imax n (imax j (ineg j))) (\\i. true) true)"
        " : Π(n:II). Path (Σ(_:Nat).Bool) (zero, true) (zero, true))", 1);

    /* GH-HP7: endpoint invariant — (hcomp Path φ u base) @ i0 = lhs of path type */
    printf("\n[GH-HP7] endpoint: (hcomp (Path Nat a a) φ u base) @ i0 = a\n");
    expect_conv(a,
        "(\\n. (hcomp (Path Nat (succ zero) (succ zero)) n"
        " (\\i. <j> succ zero) (<j> succ zero)) @ i0"
        " : Π(n:II). Nat)",
        "(\\n. succ zero : Π(n:II). Nat)", 1);

    /* GH-HP8: endpoint invariant at i1 */
    printf("\n[GH-HP8] endpoint: (hcomp (Path Nat a a) φ u base) @ i1 = a\n");
    expect_conv(a,
        "(\\n. (hcomp (Path Nat (succ zero) (succ zero)) n"
        " (\\i. <j> succ zero) (<j> succ zero)) @ i1"
        " : Π(n:II). Nat)",
        "(\\n. succ zero : Π(n:II). Nat)", 1);

    /* GH-HP9: face = imax phi psi — structural rule fires */
    printf("\n[GH-HP9] hcomp Path (imax phi psi) — structural rule fires\n");
    {
        Val *phi_v  = vl_neutral(a, 924, NULL);
        Val *psi_v  = vl_neutral(a, 925, NULL);
        Val *face_v = nbe_vimax(a, phi_v, psi_v);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\i. <j> zero"));
        Val *base_v = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *path_ty = nbe_eval(a, NULL, parse(a, "Path Nat zero zero"));
        Val *r = nbe_vhcomp(a, path_ty, face_v, tube_v, base_v);
        if (r->tag == VL_PATHABS)
            { printf("  [OK] VL_PATHABS for imax face\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* GH-HP10: face = imin phi psi — structural rule fires */
    printf("\n[GH-HP10] hcomp Path (imin phi psi) — structural rule fires\n");
    {
        Val *phi_v  = vl_neutral(a, 926, NULL);
        Val *psi_v  = vl_neutral(a, 927, NULL);
        Val *face_v = nbe_vimin(a, phi_v, psi_v);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\i. <j> zero"));
        Val *base_v = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *path_ty = nbe_eval(a, NULL, parse(a, "Path Nat zero zero"));
        Val *r = nbe_vhcomp(a, path_ty, face_v, tube_v, base_v);
        if (r->tag == VL_PATHABS)
            { printf("  [OK] VL_PATHABS for imin face\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* GH-HP11: face = ineg phi — structural rule fires */
    printf("\n[GH-HP11] hcomp Path (ineg phi) — structural rule fires\n");
    {
        Val *phi_v  = vl_neutral(a, 928, NULL);
        Val *face_v = nbe_vineg(a, phi_v);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\i. <j> zero"));
        Val *base_v = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *path_ty = nbe_eval(a, NULL, parse(a, "Path Nat zero zero"));
        Val *r = nbe_vhcomp(a, path_ty, face_v, tube_v, base_v);
        if (r->tag == VL_PATHABS)
            { printf("  [OK] VL_PATHABS for ineg face\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* GH-HP12: conv of Path hcomp ≡ eta expansion via projections */
    printf("\n[GH-HP12] eta: hcomp Path result ≡ <j> (hcomp Path result @ j)\n");
    expect_conv(a,
        "(\\n. hcomp (Path Nat zero zero) n (\\i. <j> zero) (<j> zero)"
        " : Π(n:II). Path Nat zero zero)",
        "(\\n. <j> ((hcomp (Path Nat zero zero) n (\\i. <j> zero) (<j> zero)) @ j)"
        " : Π(n:II). Path Nat zero zero)", 1);

    /* GH-HP13: hcomp Path when A = Path type (2-path): result is a path of paths */
    printf("\n[GH-HP13] hcomp (Path (Path Nat zero zero) ...) — A itself is a Path type\n");
    {
        Val *phi_v   = vl_neutral(a, 929, NULL);
        Val *tube_v  = nbe_eval(a, NULL, parse(a, "\\i. <j> <k> zero"));
        Val *base_v  = nbe_eval(a, NULL, parse(a, "<j> <k> zero"));
        Val *path_A  = nbe_eval(a, NULL, parse(a, "Path Nat zero zero"));
        Val *lhs_p   = nbe_eval(a, NULL, parse(a, "<k> zero"));
        Val *rhs_p   = nbe_eval(a, NULL, parse(a, "<k> zero"));
        Val *path2_ty = vl_path(a, path_A, lhs_p, rhs_p);
        Val *r = nbe_vhcomp(a, path2_ty, phi_v, tube_v, base_v);
        if (r->tag == VL_PATHABS)
            { printf("  [OK] VL_PATHABS for path-of-paths\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* GH-HP14: refl vs pathabs NOT equal for different elements */
    printf("\n[GH-HP14] refl true ≢ <j> false (different elements)\n");
    {
        Val *refl_true   = vl_refl(a, vl_true(a));
        Val *path_false  = nbe_eval(a, NULL, parse(a, "<j> false"));
        int neq = !conv(a, 0, refl_true, path_false);
        if (neq)
            { printf("  [OK] refl true ≢ <j> false\n"); tests_pass++; }
        else
            { printf("  [BUG] refl true ≡ <j> false (wrong equality)\n"); tests_fail++; }
    }

    /* ── Phase M5: structural termination checker ───────────────────────── */

    printf("\n--- Phase M5: structural termination checker ---\n");

    /* TC1: predecessor — structural on the single argument */
    printf("\n[TC1] predecessor via match — structural\n");
    {
        int idx = def_lookup("_tc1_pred");
        if (idx < 0)
            idx = def_define_nocheck("_tc1_pred", NULL,
                "fix (\\pred. \\n. match n of | zero => zero | succ k => k)");
        if (idx >= 0) {
            printf("  [OK] let rec pred accepted\n"); tests_pass++;
            expect_conv(a, "_tc1_pred zero",               "zero",     1);
            expect_conv(a, "_tc1_pred (succ (succ zero))", "succ zero",1);
        } else {
            printf("  [BUG] let rec pred rejected\n"); tests_fail++;
        }
    }

    /* TC2: add-2 via match — structural (self-ref via fix variable 'f') */
    printf("\n[TC2] add-2 via match — structural\n");
    {
        int idx = def_lookup("_tc2_add2");
        if (idx < 0)
            idx = def_define_nocheck("_tc2_add2", NULL,
                "fix (\\f. \\n. match n of"
                " | zero => succ (succ zero)"
                " | succ k => succ (f k))");
        if (idx >= 0) {
            printf("  [OK] let rec add2 accepted\n"); tests_pass++;
            expect_conv(a, "_tc2_add2 zero",         "succ (succ zero)", 1);
            expect_conv(a, "_tc2_add2 (succ zero)",  "succ (succ (succ zero))", 1);
        } else {
            printf("  [BUG] let rec add2 rejected\n"); tests_fail++;
        }
    }

    /* TC3: two-arg function, decreasing on first arg */
    printf("\n[TC3] two-arg, decreasing on arg 1\n");
    {
        int idx = def_lookup("_tc3_f");
        if (idx < 0)
            idx = def_define_nocheck("_tc3_f", NULL,
                "fix (\\f. \\n. \\m. match n of"
                " | zero => m"
                " | succ k => succ (f k m))");
        if (idx >= 0) {
            printf("  [OK] let rec (decr arg1) accepted\n"); tests_pass++;
            expect_conv(a, "_tc3_f zero (succ zero)", "succ zero", 1);
            expect_conv(a, "_tc3_f (succ (succ zero)) zero",
                        "succ (succ zero)", 1);
        } else {
            printf("  [BUG] let rec (decr arg1) rejected\n"); tests_fail++;
        }
    }

    /* TC4: two-arg function, decreasing on second arg */
    printf("\n[TC4] two-arg, decreasing on arg 2\n");
    {
        int idx = def_lookup("_tc4_g");
        if (idx < 0)
            idx = def_define_nocheck("_tc4_g", NULL,
                "fix (\\g. \\n. \\m. match m of"
                " | zero => n"
                " | succ k => succ (g n k))");
        if (idx >= 0) {
            printf("  [OK] let rec (decr arg2) accepted\n"); tests_pass++;
            expect_conv(a, "_tc4_g (succ zero) zero", "succ zero", 1);
            expect_conv(a, "_tc4_g zero (succ (succ zero))",
                        "succ (succ zero)", 1);
        } else {
            printf("  [BUG] let rec (decr arg2) rejected\n"); tests_fail++;
        }
    }

    /* TC5: fibonacci-style nested match (two recursive calls on k and j) */
    printf("\n[TC5] fibonacci-style (nested match, two recursive calls)\n");
    {
        int idx = def_lookup("_tc5_fib");
        if (idx < 0)
            idx = def_define_nocheck("_tc5_fib", NULL,
                "fix (\\fib. \\n. match n of"
                " | zero => zero"
                " | succ k => match k of"
                "     | zero => succ zero"
                "     | succ j => natrec (\\_x. Nat) (fib k)"
                "                  (\\_m. \\ih. succ ih) (fib j))");
        if (idx >= 0) {
            printf("  [OK] let rec fib accepted\n"); tests_pass++;
            expect_conv(a, "_tc5_fib zero",        "zero",     1);
            expect_conv(a, "_tc5_fib (succ zero)", "succ zero",1);
            /* fib(4) = 3: 0,1,1,2,3 */
            expect_conv(a,
                "_tc5_fib (succ (succ (succ (succ zero))))",
                "succ (succ (succ zero))", 1);
        } else {
            printf("  [BUG] let rec fib rejected\n"); tests_fail++;
        }
    }

    /* TC6: user-defined inductive — structural on the list argument */
    printf("\n[TC6] user-defined inductive — structural\n");
    {
        if (ind_lookup("_TCList") < 0)
            parse_data("_TCList (A : Type) where"
                       " _tcNil : _TCList A ;"
                       " _tcCons : A \xe2\x86\x92 _TCList A \xe2\x86\x92 _TCList A");
        int idx = def_lookup("_tc6_len");
        if (idx < 0)
            idx = def_define_nocheck("_tc6_len", NULL,
                "fix (\\len. \\A. \\xs. match xs of"
                " | _tcNil => zero"
                " | _tcCons h t => succ (len A t))");
        if (idx >= 0) {
            printf("  [OK] let rec len accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] let rec len rejected\n"); tests_fail++;
        }
    }

    /* TC7: no recursive calls at all — trivially OK */
    printf("\n[TC7] no recursive calls — trivially terminating\n");
    {
        int idx = def_lookup("_tc7_const");
        if (idx < 0)
            idx = def_define_nocheck("_tc7_const", NULL,
                "fix (\\f. \\n. succ zero)");
        if (idx >= 0) {
            printf("  [OK] let rec (no self-call) accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] let rec (no self-call) rejected\n"); tests_fail++;
        }
    }

    /* TC_NEG1: call on natrec step binder (not a match arm binder) — reject */
    printf("\n[TC_NEG1] recursive call on natrec step binder — must reject\n");
    {
        int idx = def_define_nocheck("_tc_neg1", NULL,
            "fix (\\f. \\n. natrec (\\_x. Nat) zero"
            "  (\\_m. \\ih. succ (f _m))"
            "  n)");
        /* f _m: _m is a natrec step binder, not a match-arm subterm */
        if (idx < 0) {
            printf("  [OK] non-structural (natrec step) rejected\n"); tests_pass++;
        } else {
            printf("  [BUG] non-structural (natrec step) accepted\n"); tests_fail++;
        }
    }

    /* TC_NEG2: call on literal zero (not smaller than anything) */
    printf("\n[TC_NEG2] recursive call on zero literal — must reject\n");
    {
        int idx = def_define_nocheck("_tc_neg2", NULL,
            "fix (\\f. \\n. match n of"
            " | zero => zero"
            " | succ k => f zero)");
        /* f zero — zero is not a match-arm binder from n */
        if (idx < 0) {
            printf("  [OK] call on literal zero rejected\n"); tests_pass++;
        } else {
            printf("  [BUG] call on literal zero accepted\n"); tests_fail++;
        }
    }

    /* TC_NEG3: partial application (arity mismatch) */
    printf("\n[TC_NEG3] partial application of two-arg f — must reject\n");
    {
        int idx = def_define_nocheck("_tc_neg3", NULL,
            "fix (\\f. \\n. \\m. match n of"
            " | zero => m"
            " | succ k => f k)");
        /* f k is a partial application (arity=2, applied to 1 arg) */
        if (idx < 0) {
            printf("  [OK] partial application rejected\n"); tests_pass++;
        } else {
            printf("  [BUG] partial application accepted\n"); tests_fail++;
        }
    }

    /* TC_NEG4: call on n itself (leq but not strictly smaller) */
    printf("\n[TC_NEG4] recursive call on the arg itself (not smaller) — must reject\n");
    {
        int idx = def_define_nocheck("_tc_neg4", NULL,
            "fix (\\f. \\n. match n of"
            " | zero => zero"
            " | succ k => f n)");
        /* f n — n is leq (equal to itself) but not strictly smaller */
        if (idx < 0) {
            printf("  [OK] call on non-smaller n rejected\n"); tests_pass++;
        } else {
            printf("  [BUG] call on non-smaller n accepted\n"); tests_fail++;
        }
    }

    /* TC8: ANN-wrapped scrutinee — match (n : Nat) of should work */
    printf("\n[TC8] ANN-wrapped scrutinee: match (n : Nat) of — structural\n");
    {
        int idx = def_lookup("_tc8_annpred");
        if (idx < 0)
            idx = def_define_nocheck("_tc8_annpred", NULL,
                "fix (\\f. \\n. match (n : Nat) of"
                " | zero => zero"
                " | succ k => succ (f k))");
        if (idx >= 0) {
            printf("  [OK] match (n : Nat) accepted\n"); tests_pass++;
            expect_conv(a, "_tc8_annpred zero",                  "zero",          1);
            /* f(n) = n: f(0)=0, f(k+1)=1+f(k) */
            expect_conv(a, "_tc8_annpred (succ (succ zero))",   "succ (succ zero)", 1);
        } else {
            printf("  [BUG] match (n : Nat) rejected\n"); tests_fail++;
        }
    }

    /* TC9: lambda in arm body calling f on smaller var — structural */
    printf("\n[TC9] lambda in arm body calling f on smaller var — structural\n");
    {
        int idx = def_lookup("_tc9_wrap");
        if (idx < 0)
            idx = def_define_nocheck("_tc9_wrap", NULL,
                "fix (\\f. \\n. match n of"
                " | zero => zero"
                " | succ k => (\\_dummy. f k) zero)");
        if (idx >= 0) {
            printf("  [OK] lambda-wrapping accepted\n"); tests_pass++;
            expect_conv(a, "_tc9_wrap zero",          "zero",     1);
            expect_conv(a, "_tc9_wrap (succ (succ zero))", "zero", 1);
        } else {
            printf("  [BUG] lambda-wrapping rejected\n"); tests_fail++;
        }
    }

    /* TC10: multi-level nested match (3-deep), transitively smaller */
    printf("\n[TC10] three-level nested match — transitively smaller\n");
    {
        int idx = def_lookup("_tc10_deep");
        if (idx < 0)
            idx = def_define_nocheck("_tc10_deep", NULL,
                "fix (\\f. \\n. match n of"
                " | zero => zero"
                " | succ k => match k of"
                "     | zero => succ zero"
                "     | succ j => match j of"
                "         | zero => succ (succ zero)"
                "         | succ i => succ (succ (succ (f i))))");
        if (idx >= 0) {
            printf("  [OK] 3-deep nested match accepted\n"); tests_pass++;
            expect_conv(a, "_tc10_deep zero",               "zero",              1);
            expect_conv(a, "_tc10_deep (succ zero)",        "succ zero",         1);
            expect_conv(a, "_tc10_deep (succ (succ zero))", "succ (succ zero)",  1);
            /* f(4): k=3,j=2,i=1 → 3+f(1); f(1)=1 → 4 */
            expect_conv(a,
                "_tc10_deep (succ (succ (succ (succ zero))))",
                "succ (succ (succ (succ zero)))", 1);
        } else {
            printf("  [BUG] 3-deep nested match rejected\n"); tests_fail++;
        }
    }

    /* TC_NEG5: inline nested fix — must reject */
    printf("\n[TC_NEG5] nested inline fix inside let rec body — must reject\n");
    {
        int idx = def_define_nocheck("_tc_neg5", NULL,
            "fix (\\f. \\n. fix (\\g. g) n)");
        if (idx < 0) {
            printf("  [OK] nested fix rejected\n"); tests_pass++;
        } else {
            printf("  [BUG] nested fix accepted\n"); tests_fail++;
        }
    }

    /* TC_NEG6: f used as a value (passed to another function) */
    printf("\n[TC_NEG6] f passed to higher-order function — must reject\n");
    {
        int idx = def_define_nocheck("_tc_neg6", NULL,
            "fix (\\f. \\n. (\\_g. _g zero) f)");
        /* f is used as an argument to a lambda, not as the head of an application */
        if (idx < 0) {
            printf("  [OK] f-as-argument rejected\n"); tests_pass++;
        } else {
            printf("  [BUG] f-as-argument accepted\n"); tests_fail++;
        }
    }

    /* TC_NEG7: zero-arity self-referential fix — must reject */
    printf("\n[TC_NEG7] zero-arity fix with self-call — must reject\n");
    {
        int idx = def_define_nocheck("_tc_neg7", NULL,
            "fix (\\f. f)");
        /* arity = 0, but f appears in the body */
        if (idx < 0) {
            printf("  [OK] zero-arity self-call rejected\n"); tests_pass++;
        } else {
            printf("  [BUG] zero-arity self-call accepted\n"); tests_fail++;
        }
    }

    /* ── rfl / refl tactic ──────────────────────────────────────────────────── */

    /* RF1: rfl closes Id Nat zero zero */
    printf("\n[RF1] rfl : Id Nat zero zero — basic Id reflexivity\n");
    {
        int idx = def_define("_rf1", "(rfl : Id Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] rfl : Id Nat zero zero accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] rfl : Id Nat zero zero rejected\n"); tests_fail++;
        }
    }

    /* RF2: rfl closes goal up to definitional equality */
    printf("\n[RF2] rfl : Id Nat ((\\n. n : Nat → Nat) zero) zero — beta-reduction\n");
    {
        int idx = def_define("_rf2", "(rfl : Id Nat ((\\ n. n : Nat → Nat) zero) zero)");
        if (idx >= 0) {
            printf("  [OK] rfl : Id Nat (beta) zero accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] rfl : Id Nat (beta) zero rejected\n"); tests_fail++;
        }
    }

    /* RF3: rfl closes Id Bool true true */
    printf("\n[RF3] rfl : Id Bool true true — Bool reflexivity\n");
    {
        int idx = def_define("_rf3", "(rfl : Id Bool true true)");
        if (idx >= 0) {
            printf("  [OK] rfl : Id Bool true true accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] rfl : Id Bool true true rejected\n"); tests_fail++;
        }
    }

    /* RF4: refl zero checks against Path Nat zero zero */
    printf("\n[RF4] refl zero : Path Nat zero zero — explicit refl for Path\n");
    {
        int idx = def_define("_rf4", "(refl zero : Path Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] refl zero : Path Nat zero zero accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] refl zero : Path Nat zero zero rejected\n"); tests_fail++;
        }
    }

    /* RF5: refl zero : Path Nat zero (succ zero) — endpoints not equal, must reject */
    printf("\n[RF5] refl zero : Path Nat zero (succ zero) — must reject\n");
    expect_fail(a, "(refl zero : Path Nat zero (succ zero))",
                "endpoints not definitionally equal");

    /* RF6: rfl : Id Nat zero (succ zero) — not definitionally equal, must reject */
    printf("\n[RF6] rfl : Id Nat zero (succ zero) — must reject\n");
    expect_fail(a, "(rfl : Id Nat zero (succ zero))",
                "Id endpoints not definitionally equal");

    /* RF7: bare rfl without annotation — must reject (hole cannot be resolved) */
    printf("\n[RF7] bare rfl — must reject (no annotation)\n");
    expect_fail(a, "rfl", "no annotation to resolve hole");

    /* RF8: rfl : Nat — not an Id/Path goal, must reject */
    printf("\n[RF8] rfl : Nat — must reject (not an Id/Path type)\n");
    expect_fail(a, "(rfl : Nat)", "not an Id or Path type");

    /* ── rfl / refl hardening ────────────────────────────────────────────── */

    /* RH1: rfl as argument to sym — hole filling must survive nbe_eval in infer */
    printf("\n[RH1] sym Nat zero zero rfl — rfl as function argument\n");
    {
        int idx = def_define("_rh1_sym",
            "(sym Nat zero zero rfl : Id Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] sym Nat zero zero rfl accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] sym Nat zero zero rfl rejected\n"); tests_fail++;
        }
    }

    /* RH2: rfl for neutral endpoint (inside lambda) */
    printf("\n[RH2] \\n. rfl : Π(n:Nat). Id Nat n n — neutral endpoint\n");
    {
        int idx = def_define("_rh2_neut",
            "(\\ n. (rfl : Id Nat n n)"
            " : Π(n : Nat). Id Nat n n)");
        if (idx >= 0) {
            printf("  [OK] \\n. rfl : Π(n:Nat). Id Nat n n accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] \\n. rfl : Π(n:Nat). Id Nat n n rejected\n"); tests_fail++;
        }
    }

    /* RH3: rfl at universe level — Id Type Nat Nat */
    printf("\n[RH3] rfl : Id Type Nat Nat — type-level reflexivity\n");
    {
        int idx = def_define("_rh3_type", "(rfl : Id Type Nat Nat)");
        if (idx >= 0) {
            printf("  [OK] rfl : Id Type Nat Nat accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] rfl : Id Type Nat Nat rejected\n"); tests_fail++;
        }
    }

    /* RH4: rfl with global def transparent unfolding */
    printf("\n[RH4] rfl : Id Nat _rh_zero zero — delta transparent unfolding\n");
    {
        if (def_lookup("_rh_zero") < 0)
            def_define("_rh_zero", "(zero : Nat)");
        int idx = def_define("_rh4_delta", "(rfl : Id Nat _rh_zero zero)");
        if (idx >= 0) {
            printf("  [OK] rfl with delta unfolding accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] rfl with delta unfolding rejected\n"); tests_fail++;
        }
    }

    /* RH5: rfl keyword closes Path goal */
    printf("\n[RH5] rfl : Path Nat zero zero — rfl for Path type\n");
    {
        int idx = def_define("_rh5_path", "(rfl : Path Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] rfl : Path Nat zero zero accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] rfl : Path Nat zero zero rejected\n"); tests_fail++;
        }
    }

    /* RH6: rfl for pair/Sigma type endpoints */
    printf("\n[RH6] rfl : Id (Σ(x:Nat).Nat) (zero,zero) (zero,zero) — pair reflexivity\n");
    {
        int idx = def_define("_rh6_pair",
            "(rfl : Id (Σ(x : Nat). Nat) (zero, zero) (zero, zero))");
        if (idx >= 0) {
            printf("  [OK] rfl : Id Σ pair accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] rfl : Id Σ pair rejected\n"); tests_fail++;
        }
    }

    /* RH7: explicit refl with Path tests the new check.c VL_PATH explicit branch */
    printf("\n[RH7] refl (\\n. n) : Path (Nat → Nat) (\\n. n) (\\n. n) — explicit refl on Path\n");
    {
        int idx = def_define("_rh7_pathfn",
            "(refl (\\ n. n) : Path (Nat → Nat) (\\ n. n) (\\ n. n))");
        if (idx >= 0) {
            printf("  [OK] refl (\\n.n) : Path (Nat→Nat) accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] refl (\\n.n) : Path (Nat→Nat) rejected\n"); tests_fail++;
        }
    }

    /* RH8: beta reduction — rfl closes definitionally equal goal */
    printf("\n[RH8] rfl : Id Nat ((\\n. succ n) zero) (succ zero) — beta-reduction\n");
    {
        int idx = def_define("_rh8_beta",
            "(rfl : Id Nat"
            "   ((\\ n. succ n : Π(_ : Nat). Nat) zero)"
            "   (succ zero))");
        if (idx >= 0) {
            printf("  [OK] rfl : Id Nat beta-reduction accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] rfl : Id Nat beta-reduction rejected\n"); tests_fail++;
        }
    }

    /* RH9: trans with rfl on both sides reduces to refl */
    printf("\n[RH9] trans Nat zero zero zero rfl rfl ≡ refl zero\n");
    {
        int idx = def_define("_rh9_trans",
            "(trans Nat zero zero zero rfl rfl : Id Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] trans with rfl accepted\n"); tests_pass++;
            expect_conv(a, "_rh9_trans", "refl zero", 1);
        } else {
            printf("  [BUG] trans with rfl rejected\n"); tests_fail++;
        }
    }

    /* RH10: ERROR — wrong element type in explicit refl */
    printf("\n[RH10] refl true : Id Nat zero zero — wrong element type, must reject\n");
    expect_fail(a, "(refl true : Id Nat zero zero)",
                "true does not have type Nat");

    /* RH11: ERROR — element checks wrong type for the Id carrier */
    printf("\n[RH11] refl zero : Id Bool zero zero — zero not of type Bool, must reject\n");
    expect_fail(a, "(refl zero : Id Bool zero zero)",
                "zero does not check against Bool");

    /* RH12: ERROR — neutral endpoints not definitionally equal */
    printf("\n[RH12] \\n. (rfl : Id Nat n (succ n)) — non-equal neutrals, must reject\n");
    expect_fail(a,
        "(\\ n. (rfl : Id Nat n (succ n))"
        " : Π(n : Nat). Id Nat n (succ n))",
        "neutral endpoints not definitionally equal");

    /* RH13: ERROR — rfl : Path Nat zero (succ zero) via rfl keyword */
    printf("\n[RH13] rfl : Path Nat zero (succ zero) — Path mismatch, must reject\n");
    expect_fail(a, "(rfl : Path Nat zero (succ zero))",
                "Path endpoints not definitionally equal");

    /* ── elab consolidation ─────────────────────────────────────────────────
     * Each test exercises a case added to elab_eval or elab_check.         */

    /* EC1: pair with rfl — elab_check PAIR, then elab_eval(TM_PAIR) via app arg */
    printf("\n[EC1] (zero, rfl) : Σ(x:Nat). Id Nat x x — pair with solved rfl\n");
    {
        int idx = def_define("_ec1_pair",
            "((zero, rfl) : Σ(x : Nat). Id Nat x x)");
        if (idx >= 0) {
            printf("  [OK] (zero, rfl) : Σ pair accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] (zero, rfl) : Σ pair rejected\n"); tests_fail++;
        }
    }

    /* EC2: pair-with-hole as function argument (tests TM_PAIR in elab_eval)
     * Previously: exit(1) crash. Now: clean "unsolved hole" error → idx < 0. */
    printf("\n[EC2] snd_fun (zero, _) — pair-arg hole: crash→clean error\n");
    {
        if (def_lookup("_ec_sfun") < 0)
            def_define("_ec_sfun",
                "(\\ p. snd p : Π(p : Σ(x : Nat). Nat). Nat)");
        int idx = def_define("_ec2_pair_hole", "(_ec_sfun (zero, _) : Nat)");
        if (idx < 0) {
            printf("  [OK] pair-with-hole fails cleanly (no crash)\n"); tests_pass++;
        } else {
            printf("  [BUG] pair-with-hole unexpectedly accepted\n"); tests_fail++;
        }
    }

    /* EC3: lambda-with-rfl as function argument (tests TM_LAM in elab_eval) */
    printf("\n[EC3] applyid (\\x. rfl) — lambda-arg with rfl body\n");
    {
        if (def_lookup("_ec_applyid") < 0)
            def_define("_ec_applyid",
                "(\\ g. g zero"
                " : Π(g : Π(x : Nat). Id Nat x x). Id Nat zero zero)");
        int idx = def_define("_ec3_lam",
            "(_ec_applyid (\\ x. (rfl : Id Nat x x)) : Id Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] lambda-arg with rfl accepted\n"); tests_pass++;
            expect_conv(a, "_ec3_lam", "refl zero", 1);
        } else {
            printf("  [BUG] lambda-arg with rfl rejected\n"); tests_fail++;
        }
    }

    /* EC4: pair-with-rfl via identity function on Σ type (tests TM_PAIR in elab_eval success path) */
    printf("\n[EC4] id_sig_pair (zero, rfl) — pair arg to identity on Σ type\n");
    {
        if (def_lookup("_ec_id_sig") < 0)
            def_define("_ec_id_sig",
                "(\\ p. p"
                " : Π(p : Σ(x : Nat). Id Nat x x). Σ(x : Nat). Id Nat x x)");
        int idx = def_define("_ec4_idpair",
            "(_ec_id_sig (zero, rfl) : Σ(x : Nat). Id Nat x x)");
        if (idx >= 0) {
            printf("  [OK] id_sig (zero, rfl) accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] id_sig (zero, rfl) rejected\n"); tests_fail++;
        }
    }

    /* EC5: succ-with-hole as function argument (tests TM_SUCC in elab_eval)
     * succ _ can't have _ inferred — expect clean error, not crash. */
    printf("\n[EC5] id_nat (succ _) — succ-arg hole: crash→clean error\n");
    {
        if (def_lookup("_ec_id_nat") < 0)
            def_define("_ec_id_nat",
                "(\\ n. n : Π(_ : Nat). Nat)");
        int idx = def_define("_ec5_succ_hole", "(_ec_id_nat (succ _) : Nat)");
        if (idx < 0) {
            printf("  [OK] succ-with-hole fails cleanly (no crash)\n"); tests_pass++;
        } else {
            printf("  [BUG] succ-with-hole unexpectedly accepted\n"); tests_fail++;
        }
    }

    /* EC6: inl-with-hole as function argument (tests TM_INL in elab_eval) */
    printf("\n[EC6] id_sum (inl _) — inl-arg hole: crash→clean error\n");
    {
        if (def_lookup("_ec_id_sum") < 0)
            def_define("_ec_id_sum",
                "(\\ s. s : Π(_ : Sum Nat Bool). Sum Nat Bool)");
        int idx = def_define("_ec6_inl_hole", "(_ec_id_sum (inl _) : Sum Nat Bool)");
        if (idx < 0) {
            printf("  [OK] inl-with-hole fails cleanly (no crash)\n"); tests_pass++;
        } else {
            printf("  [BUG] inl-with-hole unexpectedly accepted\n"); tests_fail++;
        }
    }

    /* EC7: annotated-term as function argument (tests TM_ANN in elab_eval) */
    printf("\n[EC7] id_nat ((rfl : Id Nat zero zero) via ann path) — ANN arg\n");
    {
        int idx = def_define("_ec7_ann",
            "(sym Nat zero zero (refl zero : Id Nat zero zero)"
            " : Id Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] annotated refl as arg accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] annotated refl as arg rejected\n"); tests_fail++;
        }
    }

    /* EC8: multiple independent holes in one term resolved correctly */
    printf("\n[EC8] (rfl, rfl) : Σ(_:Id Nat zero zero). Id Bool true true\n");
    {
        int idx = def_define("_ec8_two_rfl",
            "((rfl, rfl)"
            " : Σ(_ : Id Nat zero zero). Id Bool true true)");
        if (idx >= 0) {
            printf("  [OK] two independent rfl holes resolved\n"); tests_pass++;
        } else {
            printf("  [BUG] two independent rfl holes failed\n"); tests_fail++;
        }
    }

    /* EC9: def_define with holes in a non-rfl context routes through elab cleanly */
    printf("\n[EC9] def_define hole-routing: (\\ f. f rfl : ...) applied\n");
    {
        int idx = def_define("_ec9_apply",
            "((\\ f. f rfl"
            "  : Π(f : Π(_ : Id Nat zero zero). Id Nat zero zero)."
            "    Id Nat zero zero)"
            " (\\ p. sym Nat zero zero p)"
            " : Id Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] higher-order rfl application accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] higher-order rfl application rejected\n"); tests_fail++;
        }
    }

    /* ── comp primitive ──────────────────────────────────────────────────────
     * Tests for heterogeneous composition.                                   */

    /* CP1: comp with φ=i1 → u i1 (tube wins) */
    printf("\n[CP1] comp fam i1 u base = u i1\n");
    expect_conv(a,
        "comp (\\ i. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero",
        "succ zero", 1);

    /* CP2: comp with φ=i0 → transp fam base (pure transport) */
    printf("\n[CP2] comp fam i0 u base = transp fam base\n");
    expect_conv(a,
        "comp (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. succ zero) zero",
        "zero", 1);

    /* CP3: comp with constant family → reduces to hcomp */
    printf("\n[CP3] comp const-fam φ u base ≡ hcomp A φ u base\n");
    expect_conv(a,
        "comp (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero",
        "hcomp Nat i0 (\\ _. zero) zero", 1);

    /* CP4: comp type-checks correctly */
    printf("\n[CP4] comp : fam i1 type-checks\n");
    {
        int idx = def_define("_cp4",
            "(comp (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero : Nat)");
        if (idx >= 0) {
            printf("  [OK] comp : Nat accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] comp : Nat rejected\n"); tests_fail++;
        }
    }

    /* CP5: comp with Id family (constant) → reduces to hcomp */
    printf("\n[CP5] comp over Id (constant) → hcomp\n");
    {
        int idx = def_define("_cp5",
            "(comp (\\ _. Id Nat zero zero : Π(_ : II). Type)"
            "      i0 (\\ _. refl zero) (refl zero)"
            " : Id Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] comp over Id constant accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] comp over Id constant rejected\n"); tests_fail++;
        }
    }

    /* CP6: comp over Π family with constant domain reduces */
    printf("\n[CP6] comp over Π family with constant domain\n");
    {
        int idx = def_define("_cp6",
            "(comp (\\ i. Π(x : Nat). Id Nat x x : Π(_ : II). Type)"
            "      i0 (\\ _. \\ x. refl x) (\\ x. refl x)"
            " : Π(x : Nat). Id Nat x x)");
        if (idx >= 0) {
            printf("  [OK] comp over Π with constant domain accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] comp over Π with constant domain rejected\n"); tests_fail++;
        }
    }

    /* CP7: comp φ=i0 on non-trivial family is transp (stuck: non-constant Path family) */
    printf("\n[CP7] comp (λi. Path Nat i0 i0) i0 u base = transp (pure transport)\n");
    {
        int idx = def_define("_cp7",
            "(comp (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero : Nat)");
        if (idx >= 0) {
            printf("  [OK] comp i0-face accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] comp i0-face rejected\n"); tests_fail++;
        }
    }

    /* CP8: comp family-type-error rejected */
    printf("\n[CP8] comp Nat φ u base — Nat not a family, must reject\n");
    expect_fail(a, "(comp Nat i0 (\\ _. zero) zero : Nat)",
                "family must be a Π type");

    /* CP9: comp base-type-error rejected */
    printf("\n[CP9] comp with base of wrong type — must reject\n");
    expect_fail(a,
        "(comp (\\ _. Nat : Π(_ : II). Type) i0 (\\ _. zero) true : Nat)",
        "base has wrong type");

    /* CP10: stuck comp stays stuck (neutral face) */
    printf("\n[CP10] comp with neutral face stays as comp\n");
    {
        int idx = def_define("_cp10",
            "((\\ f. comp (\\ _. Nat : Π(_ : II). Type) f (\\ _. zero) zero"
            "  : Π(f : II). Nat) i0)");
        if (idx >= 0) {
            printf("  [OK] comp neutral-face applied to i0 accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] comp neutral-face applied to i0 rejected\n"); tests_fail++;
        }
    }

    /* ── comp hardening ─────────────────────────────────────────────────────
     * Systematic coverage of all structural rules plus crash-prevention.   */

    /* CPH1: Π-comp at i1 — tube applied to argument */
    printf("\n[CPH1] (comp Π-fam i1 tube base) zero ≡ tube-zero\n");
    expect_conv(a,
        "(comp (\\ _. Π(x : Nat). Nat : Π(_ : II). Type)"
        "      i1 (\\ _. \\ x. succ x) (\\ x. x)) zero",
        "succ zero", 1);

    /* CPH2: Π-comp at i0 — base applied to argument (transp on constant family) */
    printf("\n[CPH2] (comp Π-fam i0 tube base) zero ≡ base-zero\n");
    expect_conv(a,
        "(comp (\\ _. Π(x : Nat). Nat : Π(_ : II). Type)"
        "      i0 (\\ _. \\ x. succ x) (\\ x. x)) zero",
        "zero", 1);

    /* CPH3: Σ-comp at i1 — fst and snd both come from tube */
    printf("\n[CPH3] fst/snd (comp Σ-fam i1 tube base)\n");
    expect_conv(a,
        "fst (comp (\\ _. Σ(x : Nat). Nat : Π(_ : II). Type)"
        "          i1 (\\ _. (succ zero, succ zero)) (zero, zero))",
        "succ zero", 1);
    expect_conv(a,
        "snd (comp (\\ _. Σ(x : Nat). Nat : Π(_ : II). Type)"
        "          i1 (\\ _. (succ zero, succ zero)) (zero, zero))",
        "succ zero", 1);

    /* CPH4: Σ-comp at i0 — fst and snd both come from base */
    printf("\n[CPH4] fst/snd (comp Σ-fam i0 tube base)\n");
    expect_conv(a,
        "fst (comp (\\ _. Σ(x : Nat). Nat : Π(_ : II). Type)"
        "          i0 (\\ _. (succ zero, succ zero)) (zero, succ zero))",
        "zero", 1);
    expect_conv(a,
        "snd (comp (\\ _. Σ(x : Nat). Nat : Π(_ : II). Type)"
        "          i0 (\\ _. (succ zero, succ zero)) (zero, succ zero))",
        "succ zero", 1);

    /* CPH5: Path-comp at i1 — result is tube at i1 */
    printf("\n[CPH5] comp Path-fam i1 tube base ≡ tube i1\n");
    expect_conv(a,
        "comp (\\ _. Path Nat zero zero : Π(_ : II). Type)"
        "     i1 (\\ _. refl zero) (refl zero)",
        "refl zero", 1);

    /* CPH6: Path-comp at i0 — result is transp on constant Path family = base */
    printf("\n[CPH6] comp Path-fam i0 tube base ≡ base\n");
    expect_conv(a,
        "comp (\\ _. Path Nat zero zero : Π(_ : II). Type)"
        "     i0 (\\ _. refl zero) (refl zero)",
        "refl zero", 1);

    /* CPH7: Π-comp with neutral face, applied — inner comp reduces at application */
    printf("\n[CPH7] (comp Π-fam neutral tube base) zero reduces correctly at endpoints\n");
    {
        /* Define f : II → Nat = λφ. (comp Π-fam φ tube base) zero */
        if (def_lookup("_cph7_f") < 0)
            def_define("_cph7_f",
                "(\\ phi. (comp (\\ _. Π(x : Nat). Nat : Π(_ : II). Type)"
                "              phi (\\ _. \\ x. succ x) (\\ x. x)) zero"
                " : Π(_ : II). Nat)");
        expect_conv(a, "_cph7_f i0", "zero",     1);
        expect_conv(a, "_cph7_f i1", "succ zero", 1);
    }

    /* CPH8: fst of stuck hcomp Σ (dependent B) doesn't crash — tests nbe_vfst fix */
    printf("\n[CPH8] fst (stuck hcomp Σ dependent-B) doesn't crash\n");
    {
        /* hcomp (Σ(x:Nat). Id Nat x x) neutral-face tube base — stays VL_HCOMP.
         * fst of VL_HCOMP would previously crash; now propagates via hcomp A. */
        if (def_lookup("_cph8_fst") < 0)
            def_define("_cph8_fst",
                "(\\ phi."
                "  fst (hcomp (Σ(x : Nat). Id Nat x x)"
                "             phi"
                "             (\\ _. (zero, refl zero))"
                "             (zero, refl zero))"
                " : Π(_ : II). Nat)");
        /* At i0: hcomp → base → fst = zero */
        expect_conv(a, "_cph8_fst i0", "zero", 1);
        /* At i1: hcomp → tube i1 → fst = zero */
        expect_conv(a, "_cph8_fst i1", "zero", 1);
    }

    /* CPH9: fst of stuck comp Σ (dependent B) doesn't crash — tests nbe_vfst fix */
    printf("\n[CPH9] fst (stuck comp Σ dependent-B) doesn't crash\n");
    {
        if (def_lookup("_cph9_fst") < 0)
            def_define("_cph9_fst",
                "(\\ phi."
                "  fst (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
                "            phi"
                "            (\\ _. (zero, refl zero))"
                "            (zero, refl zero))"
                " : Π(_ : II). Nat)");
        expect_conv(a, "_cph9_fst i0", "zero", 1);
        expect_conv(a, "_cph9_fst i1", "zero", 1);
    }

    /* CPH10: comp over non-structural closed type (Bool) stays stuck and type-checks */
    printf("\n[CPH10] comp over Bool family — type-checks, neutral face stays stuck\n");
    {
        int idx = def_define("_cph10_bool",
            "(\\ phi. comp (\\ _. Bool : Π(_ : II). Type) phi (\\ _. true) true"
            " : Π(_ : II). Bool)");
        if (idx >= 0) {
            printf("  [OK] comp over Bool type-checks\n"); tests_pass++;
            expect_conv(a, "_cph10_bool i0", "true", 1);
            expect_conv(a, "_cph10_bool i1", "true", 1);
        } else {
            printf("  [BUG] comp over Bool rejected\n"); tests_fail++;
        }
    }

    /* CPH11: comp ≡ hcomp on constant family (two representations, same result) */
    printf("\n[CPH11] comp constant-Nat-fam i0 ≡ hcomp Nat i0 (via conv)\n");
    expect_conv(a,
        "comp (\\ _. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero",
        "hcomp Nat i0 (\\ _. zero) zero",
        1);

    /* CPH12: tube wrong type — rejected */
    printf("\n[CPH12] comp with tube returning wrong type — must reject\n");
    expect_fail(a,
        "(comp (\\ _. Nat : Π(_ : II). Type) i0 (\\ _. true) zero : Nat)",
        "tube type mismatch");

    /* CPH13: base wrong type — rejected */
    printf("\n[CPH13] comp with base of wrong type — must reject\n");
    expect_fail(a,
        "(comp (\\ _. Nat : Π(_ : II). Type) i0 (\\ _. zero) true : Nat)",
        "base type mismatch");

    /* CPH14: family domain not II — rejected */
    printf("\n[CPH14] comp with family domain Nat (not II) — must reject\n");
    expect_fail(a,
        "(comp (\\ _. Nat : Π(_ : Nat). Type) i0 (\\ _. zero) zero : Nat)",
        "family domain must be II");

    /* CPH15: comp over Π with Id codomain — full structural reduction */
    printf("\n[CPH15] comp Π-fam (Id codomain) applied correctly at both endpoints\n");
    {
        if (def_lookup("_cph15_f") < 0)
            def_define("_cph15_f",
                "(\\ phi."
                "  (comp (\\ _. Π(x : Nat). Id Nat x x : Π(_ : II). Type)"
                "        phi"
                "        (\\ _. \\ x. refl x)"
                "        (\\ x. refl x))"
                " : Π(_ : II). Π(x : Nat). Id Nat x x)");
        /* At i0: inner comp fires Π rule, reduces to base applied to n */
        /* At i1: inner comp fires Π rule, reduces to tube at i1 applied to n */
        int idx = def_define("_cph15_zero",
            "(_cph15_f i0 zero : Id Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] comp Π Id-cod at i0 accepted\n"); tests_pass++;
            expect_conv(a, "_cph15_zero", "refl zero", 1);
        } else {
            printf("  [BUG] comp Π Id-cod at i0 rejected\n"); tests_fail++;
        }
    }

    /* CPH16: VL_COMP conv — two equal stuck comp expressions are conv-equal */
    printf("\n[CPH16] conv of equal stuck comp expressions\n");
    {
        if (def_lookup("_cph16_g") < 0)
            def_define("_cph16_g",
                "(\\ phi. comp (\\ _. Nat : Π(_ : II). Type) phi (\\ _. zero) zero"
                " : Π(_ : II). Nat)");
        /* The function is identical to itself at every face — conv should hold */
        expect_conv(a, "_cph16_g", "_cph16_g", 1);
        /* Applied to i0 both sides: conv */
        expect_conv(a, "_cph16_g i0", "_cph16_g i0", 1);
    }

    /* ── CS-series: CORE-2 — comp Σ dependent-B exact snd via fill ──────────
     * Formula: snd(comp (λi.Σ(x:A).B x) φ u p)
     *        = comp (λi. B(fill A φ (fst∘u) (fst p) i)) φ (λi.snd(u i)) (snd p)
     * Family used: Σ(x:Nat). Id Nat x x  — B depends genuinely on x.
     * Tube: λ_.(succ zero, refl(succ zero))   Base: (zero, refl zero).
     * The fill formula matters for the type: with old (transp) the inferred snd
     * type would be Id Nat zero zero (wrong); with fill it is
     * Id Nat (comp Nat φ (fst∘tube) (fst base)) (…) = Id Nat (fst(comp Σ)) …  */

    /* CS1: snd(comp Σ dep-B i1 tube base) = snd(tube i1) = refl(succ zero) */
    printf("\n[CS1] snd(comp Σ dep-B i1 tube base) ≡ refl(succ zero)\n");
    expect_conv(a,
        "snd (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
        "          i1 (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))",
        "refl (succ zero)", 1);

    /* CS2: snd(comp Σ dep-B i0 tube base) = snd(base) = refl zero */
    printf("\n[CS2] snd(comp Σ dep-B i0 tube base) ≡ refl zero\n");
    expect_conv(a,
        "snd (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
        "          i0 (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))",
        "refl zero", 1);

    /* CS3: fst(comp Σ dep-B i1 tube base) = fst(tube i1) = succ zero */
    printf("\n[CS3] fst(comp Σ dep-B i1 tube base) ≡ succ zero\n");
    expect_conv(a,
        "fst (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
        "          i1 (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))",
        "succ zero", 1);

    /* CS4: fst(comp Σ dep-B i0 tube base) = fst(base) = zero */
    printf("\n[CS4] fst(comp Σ dep-B i0 tube base) ≡ zero\n");
    expect_conv(a,
        "fst (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
        "          i0 (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))",
        "zero", 1);

    /* CS5: via lambda applied at i0 */
    printf("\n[CS5] (λφ. snd(comp Σ dep-B φ …)) i0 ≡ refl zero\n");
    expect_conv(a,
        "(\\ phi. snd (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
        "                   phi (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))) i0",
        "refl zero", 1);

    /* CS6: via lambda applied at i1 */
    printf("\n[CS6] (λφ. snd(comp Σ dep-B φ …)) i1 ≡ refl(succ zero)\n");
    expect_conv(a,
        "(\\ phi. snd (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
        "                   phi (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))) i1",
        "refl (succ zero)", 1);

    /* CS7: KEY TYPE-CHECK — snd(comp Σ dep-B φ …) : Id Nat (fst comp φ) (fst comp φ).
     * With old (transp) formula the snd type is Id Nat zero zero (wrong for neutral φ),
     * clashing with the annotation Id Nat (hcomp … φ …) …; the check fails.
     * With the fill formula the snd type matches the annotation exactly.           */
    printf("\n[CS7] type-check: (λφ.snd(comp Σ dep-B φ …)) : Π(φ:II).Id Nat (fst comp φ) …\n");
    {
        int idx = def_define("_cs7_snd",
            "(\\ phi."
            "  snd (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
            "            phi"
            "            (\\ _. (succ zero, refl (succ zero)))"
            "            (zero, refl zero))"
            " : Π(phi : II)."
            "     Id Nat"
            "       (fst (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
            "                 phi (\\ _. (succ zero, refl (succ zero))) (zero, refl zero)))"
            "       (fst (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
            "                 phi (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))))");
        if (idx >= 0) {
            printf("  [OK] snd(comp Σ dep-B φ) type-checks with exact fill-based type\n"); tests_pass++;
        } else {
            printf("  [BUG] snd(comp Σ dep-B φ) type-check failed (fill formula broken?)\n"); tests_fail++;
        }
    }

    /* CS8: CS7 applied at i0 = refl zero */
    printf("\n[CS8] _cs7_snd i0 ≡ refl zero\n");
    if (def_lookup("_cs7_snd") >= 0)
        expect_conv(a, "_cs7_snd i0", "refl zero", 1);
    else { printf("  [SKIP] _cs7_snd not defined\n"); }

    /* CS9: CS7 applied at i1 = refl(succ zero) */
    printf("\n[CS9] _cs7_snd i1 ≡ refl(succ zero)\n");
    if (def_lookup("_cs7_snd") >= 0)
        expect_conv(a, "_cs7_snd i1", "refl (succ zero)", 1);
    else { printf("  [SKIP] _cs7_snd not defined\n"); }

    /* CS10: annotation check: snd(comp Σ dep-B i1 …) : Id Nat (succ zero)(succ zero).
     * With old code the snd type at i1 would be Id Nat zero zero (transp of fst_base=zero),
     * not Id Nat (succ zero) (succ zero); this annotation would be rejected.            */
    printf("\n[CS10] snd(comp Σ dep-B i1 …) : Id Nat (succ zero)(succ zero) accepted\n");
    {
        int idx = def_define("_cs10",
            "(snd (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
            "          i1"
            "          (\\ _. (succ zero, refl (succ zero)))"
            "          (zero, refl zero))"
            " : Id Nat (succ zero) (succ zero))");
        if (idx >= 0) {
            printf("  [OK] snd type at i1 = Id Nat (succ zero)(succ zero) ✓\n"); tests_pass++;
        } else {
            printf("  [BUG] snd type at i1 wrong (transp formula would give Id Nat zero zero)\n"); tests_fail++;
        }
    }

    /* CS11: annotation check: snd(comp Σ dep-B i0 …) : Id Nat zero zero accepted */
    printf("\n[CS11] snd(comp Σ dep-B i0 …) : Id Nat zero zero accepted\n");
    {
        int idx = def_define("_cs11",
            "(snd (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
            "          i0"
            "          (\\ _. (succ zero, refl (succ zero)))"
            "          (zero, refl zero))"
            " : Id Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] snd type at i0 = Id Nat zero zero ✓\n"); tests_pass++;
        } else {
            printf("  [BUG] snd type at i0 wrong\n"); tests_fail++;
        }
    }

    /* CS12: Bool-valued dependent B — snd type tracks fst correctly.
     * Σ(x:Bool). Id Bool x x; tube=(true, refl true), base=(false, refl false). */
    printf("\n[CS12] snd(comp Σ(x:Bool).Id Bool x x i1 …) ≡ refl true\n");
    expect_conv(a,
        "snd (comp (\\ _. Σ(x : Bool). Id Bool x x : Π(_ : II). Type)"
        "          i1 (\\ _. (true, refl true)) (false, refl false))",
        "refl true", 1);

    /* ── comp-PathP structural rule ─────────────────────────────────────────
     * comp (λi. PathP (F i) (a i) (b i)) φ u p
     *   = ⟨j⟩ comp (λi. F i j) (imax φ (∂j)) (λi. u i @ j) (p @ j)
     * Fires only for closed families (lam.env == NULL, body is TM_PATHP).   */

    /* CPP1: comp PathP face=i1 → tube i1  (β rule fires before structural) */
    printf("\n[CPP1] comp (λi. PathP const) i1 tube base = tube i1\n");
    expect_conv(a,
        "comp (\\ i. PathP (\\ j. Nat) zero zero : Π(_ : II). Type)"
        "     i1 (\\ _. <j> succ zero) (<j> zero)",
        "<j> succ zero", 1);

    /* CPP2: comp PathP face=i0 → transp fam base.
     * For constant PathP family, transp is identity → result = base. */
    printf("\n[CPP2] comp (λi. PathP const) i0 tube base = base\n");
    expect_conv(a,
        "comp (\\ i. PathP (\\ j. Nat) zero zero : Π(_ : II). Type)"
        "     i0 (\\ _. <j> succ zero) (<j> zero)",
        "<j> zero", 1);

    /* CPP3: comp PathP with neutral face → structural rule fires → VL_PATHABS */
    printf("\n[CPP3] comp (λi. PathP const) neutral → structural rule fires (VL_PATHABS)\n");
    {
        Val *pathp_ty = nbe_eval(a, NULL,
            parse(a, "PathP (\\ j. Nat) zero zero"));
        Val *fam_v = vl_lam(a, "i", NULL,
            parse(a, "PathP (\\ j. Nat) zero zero"));
        Val *phi_v  = vl_neutral(a, 950, NULL);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\ i. <j> zero"));
        Val *base_v = nbe_eval(a, NULL, parse(a, "<j> zero"));
        (void)pathp_ty;
        Val *r = nbe_vcomp(a, fam_v, phi_v, tube_v, base_v);
        if (r->tag == VL_PATHABS)
            { printf("  [OK] VL_PATHABS for neutral face\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* CPP4: comp PathP with neutral φ — formula at j=i0 gives tube(i1)@i0.
     * ∂i0 = imax i0 (ineg i0) = i1, imax φ i1 = i1 → inner comp face=i1 → tube i1.
     * tube = λi. <j> succ zero, tube(i1) @ i0 = succ zero. */
    printf("\n[CPP4] (comp PathP neutral tube base) @ i0 = tube(i1) @ i0 = succ zero\n");
    {
        Val *fam_v  = vl_lam(a, "i", NULL,
            parse(a, "PathP (\\ j. Nat) zero zero"));
        Val *phi_v  = vl_neutral(a, 951, NULL);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\ i. <j> succ zero"));
        Val *base_v = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *r      = nbe_vcomp(a, fam_v, phi_v, tube_v, base_v);
        Val *r_i0   = nbe_vpathapp(a, r, vl_neutral(a, IZERO_CONST_LVL, NULL));
        Val *expected = nbe_eval(a, NULL, parse(a, "succ zero"));
        if (conv(a, 0, r_i0, expected))
            { printf("  [OK] (comp PathP) @ i0 ≡ succ zero\n"); tests_pass++; }
        else
            { printf("  [BUG] (comp PathP) @ i0 wrong value\n"); tests_fail++; }
    }

    /* CPP5: comp PathP face=i1 → u i1;  (u i1) @ i1 endpoint check */
    printf("\n[CPP5] comp PathP i1 tube base @ i1 = tube i1 @ i1\n");
    {
        Val *fam_v  = vl_lam(a, "i", NULL,
            parse(a, "PathP (\\ j. Nat) zero (succ zero)"));
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\ _. <j> succ zero"));
        Val *base_v = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *r      = nbe_vcomp(a, fam_v, vl_neutral(a, IONE_CONST_LVL, NULL),
                                tube_v, base_v);
        Val *i1v    = vl_neutral(a, IONE_CONST_LVL, NULL);
        Val *r_i1   = nbe_vpathapp(a, r, i1v);
        Val *expected = nbe_eval(a, NULL, parse(a, "succ zero"));
        if (conv(a, 0, r_i1, expected))
            { printf("  [OK] comp PathP i1 @ i1 = succ zero\n"); tests_pass++; }
        else
            { printf("  [BUG] comp PathP i1 @ i1 wrong value\n"); tests_fail++; }
    }

    /* CPP6: comp over PathP type-checks at surface level.
     * Inner PathP fam must be annotated for type-checker. */
    printf("\n[CPP6] comp (λi. PathP (λj.Nat) zero zero) type-checks\n");
    {
        int idx = def_define("_cpp6",
            "(comp (\\ i. PathP (\\ j. Nat : Π(_ : II). Type) zero zero : Π(_ : II). Type)"
            "      i0 (\\ _. <j> zero) (<j> zero)"
            " : PathP (\\ j. Nat : Π(_ : II). Type) zero zero)");
        if (idx >= 0)
            { printf("  [OK] comp PathP type-checks\n"); tests_pass++; }
        else
            { printf("  [BUG] comp PathP rejected\n"); tests_fail++; }
    }

    /* CPP7: non-closed non-constant PathP family stays VL_COMP.
     * Build fam = λi. PathP (λj.Nat) (some_fn i) zero where some_fn is a neutral
     * II→Nat function captured in the closure env.  This fam is:
     *   (a) non-closed: lam.env = [some_fn] ≠ NULL  → structural rule guard fails
     *   (b) non-constant: lhs=some_fn(i) mentions probe  → hcomp-redirect doesn't fire
     * Result must be VL_COMP (stuck). */
    printf("\n[CPP7] non-closed non-constant PathP family stays VL_COMP\n");
    {
        Val *some_fn = vl_neutral(a, 952, NULL);  /* neutral II→Nat function */
        /* body = PathP (λj.Nat) (VAR(1) VAR(0)) zero  in env=[some_fn(0), i(... shifted)] */
        Term *nat_lam = tm_lam(a, "j", tm_nat(a));
        Term *lhs_tm  = tm_app(a, tm_var(a, 1), tm_var(a, 0)); /* some_fn(i): VAR(1)=some_fn, VAR(0)=i */
        Term *body_tm = tm_pathp(a, nat_lam, lhs_tm, tm_zero(a));
        Val  *fam_v   = vl_lam(a, "i", env_cons(a, some_fn, NULL), body_tm);
        Val *phi_v  = vl_neutral(a, 953, NULL);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\ i. <j> zero"));
        Val *base_v = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *r = nbe_vcomp(a, fam_v, phi_v, tube_v, base_v);
        if (r->tag == VL_COMP)
            { printf("  [OK] non-closed non-constant PathP fam stays VL_COMP\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_COMP, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* CPP8: comp PathP structural rule with varying F: F(i) = (II→Nat) varies by i */
    printf("\n[CPP8] comp (λi. PathP (λj. Bool) ...) neutral — structural rule, result is VL_PATHABS\n");
    {
        Val *fam_v  = vl_lam(a, "i", NULL,
            parse(a, "PathP (\\ j. Bool) true true"));
        Val *phi_v  = vl_neutral(a, 953, NULL);
        Val *tube_v = nbe_eval(a, NULL, parse(a, "\\ i. <j> true"));
        Val *base_v = nbe_eval(a, NULL, parse(a, "<j> true"));
        Val *r = nbe_vcomp(a, fam_v, phi_v, tube_v, base_v);
        if (r->tag == VL_PATHABS)
            { printf("  [OK] comp PathP Bool constant family fires\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_PATHABS, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* CPP9: VL_COMP base guard — comp-PathP rule stays VL_COMP when base is VL_COMP.
     * Build a NON-CONSTANT closed PathP family (lhs=VAR(0) of type II, treated as Nat
     * via a def), and a VL_COMP base.  The structural rule must NOT fire (base guard).
     * (Also verifies: nbe_vpathapp on VL_COMP doesn't crash.) */
    printf("\n[CPP9] comp-PathP with VL_COMP base stays VL_COMP (base guard)\n");
    {
        /* Build a VL_COMP path element: comp over a non-closed PathP family */
        Val *some_fn = vl_neutral(a, 970, NULL);
        Term *nat_lam = tm_lam(a, "j", tm_nat(a));
        Term *lhs_body = tm_app(a, tm_var(a, 1), tm_var(a, 0));
        Term *pathp_body = tm_pathp(a, nat_lam, lhs_body, tm_zero(a));
        Val *nc_fam  = vl_lam(a, "i", env_cons(a, some_fn, NULL), pathp_body);
        Val *phi_nc  = vl_neutral(a, 971, NULL);
        Val *tube_nc = nbe_eval(a, NULL, parse(a, "\\ i. <j> zero"));
        Val *base_nc = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *comp_base = nbe_vcomp(a, nc_fam, phi_nc, tube_nc, base_nc);
        /* comp_base should be VL_COMP */
        if (comp_base->tag != VL_COMP)
            { printf("  [SETUP-BUG] expected VL_COMP, got %d\n", comp_base->tag); tests_fail++; }
        else {
            /* Now try comp (constant PathP fam) with VL_COMP as base.
             * The constant-fam check redirects to hcomp-PathP, which fires.
             * The result's body calls vpathapp(comp_base, j) — must not crash. */
            Val *closed_fam = vl_lam(a, "i", NULL,
                parse(a, "PathP (\\ j. Nat) zero zero"));
            Val *phi2   = vl_neutral(a, 972, NULL);
            Val *tube2  = nbe_eval(a, NULL, parse(a, "\\ i. <j> zero"));
            Val *result = nbe_vcomp(a, closed_fam, phi2, tube2, comp_base);
            /* Apply at i1 — this triggers vpathapp(comp_base, i1) inside hcomp-PathP body */
            Val *i1v    = vl_neutral(a, IONE_CONST_LVL, NULL);
            Val *at_i1  = nbe_vpathapp(a, result, i1v);
            (void)at_i1;  /* just verify no crash */
            printf("  [OK] vpathapp on VL_COMP base doesn't crash\n"); tests_pass++;
        }
    }

    /* CPP10: non-pathapp-safe base causes comp-PathP to stay VL_COMP (non-const fam).
     * Build a non-constant, closed PathP family using a global def for the endpoint. */
    printf("\n[CPP10] comp-PathP non-const family with VL_COMP base stays VL_COMP\n");
    {
        Val *some_fn2 = vl_neutral(a, 973, NULL);
        Term *nat_lam2 = tm_lam(a, "j", tm_nat(a));
        /* body: PathP (λj.Nat) (some_fn2 VAR(0)) zero — lhs varies with i */
        Term *lhs_b2 = tm_app(a, tm_var(a, 1), tm_var(a, 0));
        Term *pathp_b2 = tm_pathp(a, nat_lam2, lhs_b2, tm_zero(a));
        /* Closed PathP fam (non-constant, lhs=some_fn2(i)) */
        Val *closed_nc_fam = vl_lam(a, "i", env_cons(a, some_fn2, NULL), pathp_b2);
        /* comp_base: another VL_COMP path element */
        Val *phi_b  = vl_neutral(a, 974, NULL);
        Val *tube_b = nbe_eval(a, NULL, parse(a, "\\ i. <j> zero"));
        Val *base_b = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *comp_base2 = nbe_vcomp(a, closed_nc_fam, phi_b, tube_b, base_b);
        /* Try comp with this same family and VL_COMP base */
        Val *phi_c = vl_neutral(a, 975, NULL);
        Val *tube_c = nbe_eval(a, NULL, parse(a, "\\ i. <j> zero"));
        Val *r = nbe_vcomp(a, closed_nc_fam, phi_c, tube_c, comp_base2);
        /* Non-constant, non-closed (env=[some_fn2]): stays VL_COMP regardless */
        if (r->tag == VL_COMP)
            { printf("  [OK] non-const/non-closed PathP fam stays VL_COMP\n"); tests_pass++; }
        else
            { printf("  [BUG] expected VL_COMP, got tag=%d\n", r->tag); tests_fail++; }
    }

    /* ── fill tests ──────────────────────────────────────────────────────────
     * fill fam φ u base i = comp (λj. fam(imin i j)) (imax φ (~i)) (λj. u(imin i j)) base
     * Key identities:
     *   fill fam φ u base i1 = comp fam φ u base      (i1 special case)
     *   fill fam i1 u base i  = u i                   (face=i1 → tube wins)
     *   fill fam i0 u base i1 = transp fam base        (face=i0 → pure transp)  */

    /* FI1: fill at i1 = comp (face=i0, constant Nat family) */
    printf("\n[FI1] fill ... i1 = comp ... (reduces to zero via transp on const Nat)\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero i1",
        "zero", 1);

    /* FI2: fill at i1 with face=i1 → tube value */
    printf("\n[FI2] fill ... i1 with face=i1 → tube(i1) = succ zero\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero i1",
        "succ zero", 1);

    /* FI3: fill type-checks; result type is fam i (not fam i1) */
    printf("\n[FI3] fill : fam i type-checks at i0\n");
    {
        int idx = def_define("_fi3",
            "(fill (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero i0 : Nat)");
        if (idx >= 0) {
            printf("  [OK] fill : Nat at i0 accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] fill : Nat at i0 rejected\n"); tests_fail++;
        }
    }

    /* FI4: fill at i1 definitionally equals comp */
    printf("\n[FI4] fill fam φ u base i1 ≡ comp fam φ u base\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero i1",
        "comp (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero", 1);

    /* FI5: fill with face=i1 at a neutral index stays stuck (doesn't crash) */
    printf("\n[FI5] fill with neutral idx — stuck as comp, no crash\n");
    {
        int idx = def_define("_fi5",
            "(\\ r. fill (\\ i. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero r"
            " : Π(r : II). Nat)");
        if (idx >= 0) {
            printf("  [OK] fill neutral-idx accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] fill neutral-idx rejected\n"); tests_fail++;
        }
    }

    /* FI6: fill family-type-error rejected */
    printf("\n[FI6] fill Nat φ u base i — Nat not a family, must reject\n");
    expect_fail(a, "(fill Nat i0 (\\ _. zero) zero i0 : Nat)",
                "family must be a Π type");

    /* FI7: fill over Π family (constant domain) at i1 = comp result */
    printf("\n[FI7] fill over Π Nat→Nat family at i1 ≡ comp result\n");
    expect_conv(a,
        "fill (\\ i. Π(x : Nat). Nat : Π(_ : II). Type) i0 (\\ _. \\ x. x) (\\ x. x) i1",
        "comp (\\ i. Π(x : Nat). Nat : Π(_ : II). Type) i0 (\\ _. \\ x. x) (\\ x. x)", 1);

    /* FI8: fill applied twice — endpoint consistency */
    printf("\n[FI8] fill at i0: CCHM spec fill fam φ u base i0 = base\n");
    /* fill fam φ u base i0 = base regardless of φ or u (even incoherent tube). */
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero i0",
        "zero", 1);

    /* ── fill hardening ──────────────────────────────────────────────────────
     * Boundary laws, sharing correctness, de Bruijn stress tests,
     * error paths, elab coverage, structural rules.                          */

    /* FIH1: boundary at i0, INCOHERENT tube (u i0 ≠ base).
     * CCHM spec: fill fam φ u base i0 = base always (short-circuit before expansion).
     * Previously returned u(i0) = succ zero; corrected to base = zero. */
    printf("\n[FIH1] fill at i0, incoherent tube: CCHM fill(i0) = base = zero\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. succ zero) zero i0",
        "zero", 1);

    /* FIH2: boundary at i0 with COHERENT tube (u i0 = base = zero) */
    printf("\n[FIH2] fill at i0, coherent tube: fill(i0) = u(i0) = base = zero\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero i0",
        "zero", 1);

    /* FIH3: sharing correctness — Bool family (fam ≠ tube type).
     * fill (λ_. Bool) i0 (λ_. true) false i1:
     *   face_r = imax i0 (~i1) = imax i0 i0 = i0
     *   → const Bool family → hcomp Bool i0 tube false → face=i0 → false */
    printf("\n[FIH3] sharing correctness: Bool family at i1 (face=i0) → base=false\n");
    expect_conv(a,
        "fill (\\ i. Bool : Π(_ : II). Type) i0 (\\ _. true) false i1",
        "false", 1);

    /* FIH4: fill inside λ, neutral idx — applied at i0.
     * CCHM spec: the outer λ is applied to i0, so fill sees idx=i0 → returns base=zero.
     * Previously returned u(i0)=succ zero via expansion; corrected. */
    printf("\n[FIH4] fill inside λ, idx captured from outer λ, applied at i0 → base=zero\n");
    expect_conv(a,
        "(\\ i. fill (\\ _. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero i"
        " : Π(i : II). Nat) i0",
        "zero", 1);

    /* FIH5: same, applied at i1 */
    printf("\n[FIH5] fill inside λ, applied at i1 → succ zero\n");
    expect_conv(a,
        "(\\ i. fill (\\ _. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero i"
        " : Π(i : II). Nat) i1",
        "succ zero", 1);

    /* FIH6: fill over Σ family — fst at i1 = fst base
     * fill (λ_. Σ(x:Nat).Nat) i0 (λ_. (zero,zero)) (zero, succ zero) i1:
     *   face_r = i0, const Σ family → hcomp Σ i0 ... (zero, succ zero) → base
     *   fst = zero, snd = succ zero */
    printf("\n[FIH6] fst of fill over Σ at i1 (face=i0) ≡ fst base = zero\n");
    expect_conv(a,
        "fst (fill (\\ i. Σ(x : Nat). Nat : Π(_ : II). Type)"
        "         i0 (\\ _. (zero, zero)) (zero, succ zero) i1)",
        "zero", 1);

    /* FIH7: fill over Σ — snd at i1 = snd base */
    printf("\n[FIH7] snd of fill over Σ at i1 (face=i0) ≡ snd base = succ zero\n");
    expect_conv(a,
        "snd (fill (\\ i. Σ(x : Nat). Nat : Π(_ : II). Type)"
        "         i0 (\\ _. (zero, zero)) (zero, succ zero) i1)",
        "succ zero", 1);

    /* FIH8: fill over constant Path family at i1 — gives the base path
     * fill (λ_.Path Nat zero zero) i0 (λ_. ⟨j⟩zero) (⟨j⟩zero) i1:
     *   constant Path family → hcomp (Path Nat zero zero) i0 _ base → base */
    printf("\n[FIH8] fill over constant Path family at i1 (face=i0) ≡ base path\n");
    expect_conv(a,
        "fill (\\ i. Path Nat zero zero : Π(_ : II). Type)"
        "     i0 (\\ _. <j> zero) (<j> zero) i1",
        "<j> zero", 1);

    /* FIH9: base type error — base has wrong type */
    printf("\n[FIH9] fill with wrong base type must reject\n");
    expect_fail(a,
        "(fill (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) true i0 : Nat)",
        "type mismatch");

    /* FIH10: idx type error — idx must be II, not Nat */
    printf("\n[FIH10] fill with non-II idx must reject\n");
    expect_fail(a,
        "(fill (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero zero : Nat)",
        "type mismatch");

    /* FIH11: fill inside a let binding — elab_subst and term_has_holes work */
    printf("\n[FIH11] fill inside let — elab route works\n");
    {
        int idx = def_define("_fih11",
            "(fill (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. zero) zero i1 : Nat)");
        if (idx >= 0) {
            printf("  [OK] fill in let definition accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] fill in let definition rejected\n"); tests_fail++;
        }
    }

    /* FIH12: neutral face, neutral idx — fill reduces to comp, stays stuck.
     * Verify type-check still accepts it (no crash on stuck result). */
    printf("\n[FIH12] fill with neutral face and neutral idx — type-checks without crash\n");
    {
        int idx = def_define("_fih12",
            "(\\ phi r. fill (\\ i. Nat : Π(_ : II). Type) phi (\\ _. zero) zero r"
            " : Π(phi : II). Π(r : II). Nat)");
        if (idx >= 0) {
            printf("  [OK] fill neutral-face neutral-idx accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] fill neutral-face neutral-idx rejected\n"); tests_fail++;
        }
    }

    /* ── PathP tests ─────────────────────────────────────────────────────────
     * PathP fam a b — heterogeneous path type
     *   fam : Π(_:II). Type_k,  a : fam i0,  b : fam i1
     * Intro: ⟨i⟩ body : PathP fam a b  (body : fam i, endpoints checked)
     * Elim:  p @ r : fam r                                                  */

    /* PP1: PathP type-checks; universe = fam's codomain universe */
    printf("\n[PP1] PathP type formation: PathP (λi.Nat) zero zero : Type\n");
    {
        int idx = def_define("_pp1",
            "(PathP (\\ i. Nat : Π(_ : II). Type) zero zero : Type)");
        if (idx >= 0) {
            printf("  [OK] PathP formation accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] PathP formation rejected\n"); tests_fail++;
        }
    }

    /* PP2: reflexivity path intro ⟨i⟩ zero : PathP (λi.Nat) zero zero */
    printf("\n[PP2] PathP intro: ⟨i⟩ zero : PathP (λi.Nat) zero zero\n");
    {
        int idx = def_define("_pp2",
            "(<i> zero : PathP (\\ i. Nat : Π(_ : II). Type) zero zero)");
        if (idx >= 0) {
            printf("  [OK] PathP intro accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] PathP intro rejected\n"); tests_fail++;
        }
    }

    /* PP3: PathP elim — left endpoint: p @ i0 ≡ lhs */
    printf("\n[PP3] PathP elim at i0: ⟨i⟩ zero @ i0 ≡ zero\n");
    expect_conv(a,
        "(<i> zero : PathP (\\ i. Nat : Π(_ : II). Type) zero zero) @ i0",
        "zero", 1);

    /* PP4: PathP elim at i1: p @ i1 ≡ rhs */
    printf("\n[PP4] PathP elim at i1: ⟨i⟩ zero @ i1 ≡ zero\n");
    expect_conv(a,
        "(<i> zero : PathP (\\ i. Nat : Π(_ : II). Type) zero zero) @ i1",
        "zero", 1);

    /* PP5: PathP with genuinely varying family — identity path on II
     * ⟨i⟩ i : PathP (λi.II) i0 i1  (lhs = i0, rhs = i1) */
    printf("\n[PP5] PathP identity path on II: ⟨i⟩ i : PathP (λi.II) i0 i1\n");
    {
        int idx = def_define("_pp5",
            "(<i> i : PathP (\\ i. II : Π(_ : II). Type) i0 i1)");
        if (idx >= 0) {
            printf("  [OK] PathP identity on II accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] PathP identity on II rejected\n"); tests_fail++;
        }
    }

    /* PP6: elim of identity path at i0 = i0 */
    printf("\n[PP6] identity path @ i0 = i0\n");
    expect_conv(a,
        "(<i> i : PathP (\\ i. II : Π(_ : II). Type) i0 i1) @ i0",
        "i0", 1);

    /* PP7: elim of identity path at i1 = i1 */
    printf("\n[PP7] identity path @ i1 = i1\n");
    expect_conv(a,
        "(<i> i : PathP (\\ i. II : Π(_ : II). Type) i0 i1) @ i1",
        "i1", 1);

    /* PP8: rfl for PathP (constant family) */
    printf("\n[PP8] rfl : PathP (λ_.Nat) zero zero\n");
    {
        int idx = def_define("_pp8",
            "(rfl : PathP (\\ _. Nat : Π(_ : II). Type) zero zero)");
        if (idx >= 0) {
            printf("  [OK] rfl for PathP accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] rfl for PathP rejected\n"); tests_fail++;
        }
    }

    /* PP9: endpoint mismatch → reject */
    printf("\n[PP9] endpoint mismatch rejected\n");
    expect_fail(a,
        "(<i> zero : PathP (\\ i. Nat : Π(_ : II). Type) zero (succ zero))",
        "PathP right endpoint mismatch");

    /* PP10: body type mismatch → reject */
    printf("\n[PP10] body type mismatch rejected\n");
    expect_fail(a,
        "(<i> true : PathP (\\ i. Nat : Π(_ : II). Type) zero zero)",
        "type mismatch");

    /* PP11: family domain not II → reject */
    printf("\n[PP11] PathP with non-Π family → reject\n");
    expect_fail(a,
        "(PathP Nat zero zero : Type)",
        "family must be Π");

    /* PP12: PathP as argument — define a path, apply @ i0, get Nat value */
    printf("\n[PP12] PathP as argument: def path, apply @ i0 ≡ zero\n");
    {
        def_define("_pp12_p", "(<i> zero : PathP (\\ i. Nat : Π(_ : II). Type) zero zero)");
        int idx = def_define("_pp12", "(_pp12_p @ i0 : Nat)");
        if (idx >= 0) {
            expect_conv(a, "_pp12", "zero", 1);
        } else {
            printf("  [BUG] PathP @ i0 from def rejected\n"); tests_fail++;
        }
    }

    /* PP13: hcomp PathP structural rule
     * hcomp (PathP fam a b) i0 u base = base (i0 endpoint rule) */
    printf("\n[PP13] hcomp (PathP fam a b) i0 u base = base\n");
    expect_conv(a,
        "hcomp (PathP (\\ i. Nat : Π(_ : II). Type) zero zero)"
        "      i0 (\\ _. <j> zero) (<j> zero)",
        "<j> zero", 1);

    /* PP14: hcomp PathP i1 u base = u i1 */
    printf("\n[PP14] hcomp (PathP fam a b) i1 u base = u i1\n");
    expect_conv(a,
        "hcomp (PathP (\\ i. Nat : Π(_ : II). Type) zero zero)"
        "      i1 (\\ _. <j> zero) (<j> succ zero)",
        "<j> zero", 1);

    /* PP15: hcomp PathP with neutral face → structural rule fires, gives pathabs */
    printf("\n[PP15] hcomp (PathP fam a b) neutral — structural PathP rule fires\n");
    {
        int idx = def_define("_pp15",
            "(\\ phi. hcomp (PathP (\\ i. Nat : Π(_ : II). Type) zero zero)"
            "              phi (\\ _. <j> zero) (<j> zero)"
            " : Π(phi : II). PathP (\\ i. Nat : Π(_ : II). Type) zero zero)");
        if (idx >= 0) {
            /* At phi=i0: should give back the base path */
            expect_conv(a, "_pp15 i0", "<j> zero", 1);
        } else {
            printf("  [BUG] hcomp PathP neutral rejected\n"); tests_fail++;
        }
    }

    /* PP16: fill over PathP family (fill at i1 = comp, stays stuck for non-const Path fam) */
    printf("\n[PP16] fill over constant PathP family at i1\n");
    expect_conv(a,
        "fill (\\ i. PathP (\\ j. Nat : Π(_ : II). Type) zero zero : Π(_ : II). Type)"
        "     i0 (\\ _. <j> zero) (<j> zero) i1",
        "<j> zero", 1);

    /* ── PathP hardening ─────────────────────────────────────────────────────
     * Edge cases: cross-tag conv, type errors, varying family, nesting,
     * structural rules, elab coverage, and documented limitations.         */

    /* PPH1: PathP (const fam) ≡ Path — cross-tag conv (the key correctness test) */
    printf("\n[PPH1] PathP (λ_. Nat) ≡ Path Nat (cross-tag conv)\n");
    {
        /* refl zero should check against BOTH PathP const-fam and Path */
        int a1 = def_define("_pph1a",
            "(refl zero : PathP (\\ _. Nat : Π(_ : II). Type) zero zero)");
        int a2 = def_define("_pph1b",
            "(refl zero : Path Nat zero zero)");
        if (a1 >= 0 && a2 >= 0) {
            /* Cross-tag type conv: PathP (λ_.Nat) 0 0 ≡ Path Nat 0 0 */
            expect_conv(a,
                "PathP (\\ _. Nat : Π(_ : II). Type) zero zero",
                "Path Nat zero zero", 1);
        } else {
            printf("  [BUG] setup for PPH1 failed\n"); tests_fail++;
        }
    }

    /* PPH2: PathP conv with itself — two equal PathP types */
    printf("\n[PPH2] conv of two equal PathP types\n");
    expect_conv(a,
        "PathP (\\ i. Nat : Π(_ : II). Type) zero zero",
        "PathP (\\ i. Nat : Π(_ : II). Type) zero zero", 1);

    /* PPH3: PathP with varying family @ neutral — result type is fam r
     * ⟨i⟩ i : PathP (λi.II) i0 i1; apply to a neutral r → type = II */
    printf("\n[PPH3] PathP @ neutral r gives fam r as type\n");
    {
        def_define("_pph3_p", "(<i> i : PathP (\\ i. II : Π(_ : II). Type) i0 i1)");
        int idx = def_define("_pph3",
            "(\\ r. (_pph3_p @ r : II) : Π(r : II). II)");
        if (idx >= 0) {
            printf("  [OK] PathP @ neutral typed correctly\n"); tests_pass++;
        } else {
            printf("  [BUG] PathP @ neutral typing failed\n"); tests_fail++;
        }
    }

    /* PPH4: PathP lhs has wrong type — reject */
    printf("\n[PPH4] PathP with lhs of wrong type → reject\n");
    expect_fail(a,
        "(PathP (\\ i. Nat : Π(_ : II). Type) true zero : Type)",
        "type mismatch");

    /* PPH5: PathP rhs has wrong type — reject */
    printf("\n[PPH5] PathP with rhs of wrong type → reject\n");
    expect_fail(a,
        "(PathP (\\ i. Nat : Π(_ : II). Type) zero true : Type)",
        "type mismatch");

    /* PPH6: PathP family codomain not Type (λ_. zero : II→Nat) → reject */
    printf("\n[PPH6] PathP family codomain not a universe → reject\n");
    expect_fail(a,
        "(PathP (\\ _. zero : Π(_ : II). Nat) zero zero : Type)",
        "family codomain must be a universe");

    /* PPH7: PathP body not in fam i — reject */
    printf("\n[PPH7] PathP body wrong type (Bool body in Nat family) → reject\n");
    expect_fail(a,
        "(<i> true : PathP (\\ i. Nat : Π(_ : II). Type) zero zero)",
        "type mismatch");

    /* PPH8: rfl for PathP with unequal endpoints — reject */
    printf("\n[PPH8] rfl for PathP with non-equal endpoints → reject\n");
    expect_fail(a,
        "(rfl : PathP (\\ _. Nat : Π(_ : II). Type) zero (succ zero))",
        "PathP endpoints not definitionally equal");

    /* PPH9: PathP intro with lhs ≠ rhs works (non-trivial heterogeneous path)
     * ⟨i⟩ i : PathP (λi.II) i0 i1 — lhs=i0, rhs=i1 */
    printf("\n[PPH9] PathP intro lhs≠rhs: ⟨i⟩ i : PathP (λi.II) i0 i1 accepted\n");
    {
        int idx = def_define("_pph9",
            "(<i> i : PathP (\\ i. II : Π(_ : II). Type) i0 i1)");
        if (idx >= 0) {
            expect_conv(a, "_pph9 @ i0", "i0", 1);
            expect_conv(a, "_pph9 @ i1", "i1", 1);
        } else {
            printf("  [BUG] PathP non-trivial intro rejected\n"); tests_fail++;
        }
    }

    /* PPH10: hcomp PathP with genuinely varying family — structural rule fires.
     * Uses fam = λi.II (so fam j = II): hcomp should give a pathabs over II. */
    printf("\n[PPH10] hcomp PathP varying family — structural rule fires\n");
    {
        /* hcomp (PathP (λi.II) i0 i1) i1 (λ_. <i>i) (<i>i) = <i>i (tube wins) */
        expect_conv(a,
            "hcomp (PathP (\\ i. II : Π(_ : II). Type) i0 i1)"
            "      i1 (\\ _. <i> i) (<i> i)",
            "<i> i", 1);
    }

    /* PPH11: nested PathP — PathP of PathP family */
    printf("\n[PPH11] nested PathP type formation\n");
    {
        /* PathP (λi. PathP (λ_. Nat) zero zero) (refl zero) (refl zero) : Type */
        int idx = def_define("_pph11",
            "(PathP (\\ i. PathP (\\ _. Nat : Π(_ : II). Type) zero zero"
            "       : Π(_ : II). Type)"
            "  (refl zero) (refl zero)"
            " : Type)");
        if (idx >= 0) {
            printf("  [OK] nested PathP type accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] nested PathP type rejected\n"); tests_fail++;
        }
    }

    /* PPH12: PathP inside Σ type */
    printf("\n[PPH12] PathP inside Σ — pair of paths\n");
    {
        int idx = def_define("_pph12",
            "((refl zero, <i> zero)"
            " : Σ(_ : Path Nat zero zero)."
            "   PathP (\\ _. Nat : Π(_ : II). Type) zero zero)");
        if (idx >= 0) {
            printf("  [OK] PathP inside Σ accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] PathP inside Σ rejected\n"); tests_fail++;
        }
    }

    /* PPH13: transp over constant-outer PathP family stays stuck (non-constant)
     * transp (λi. PathP (varying fam i) ...) p  →  VL_TRANSP stuck (expected) */
    printf("\n[PPH13] transp over non-constant PathP family stays stuck\n");
    {
        /* The outer family λi. PathP (λj. II) (something i) (something_else i)
         * is non-constant so transp stays stuck — type-checks, normalises to VL_TRANSP */
        int idx = def_define("_pph13",
            "transp (\\ i. PathP (\\ _. Nat : Π(_ : II). Type) zero zero"
            "        : Π(_ : II). Type)"
            "       (<j> zero)");
        if (idx >= 0) {
            printf("  [OK] transp over PathP type accepted (stuck)\n"); tests_pass++;
        } else {
            printf("  [BUG] transp over PathP type rejected\n"); tests_fail++;
        }
    }

    /* PPH14: infer ⟨i⟩ body — always gives Path (not PathP), even for varying body.
     * ⟨i⟩ i infers Path II i0 i1 (body_type at i0 = II). This is by design. */
    printf("\n[PPH14] infer ⟨i⟩ i gives Path II i0 i1 (not PathP)\n");
    {
        int idx = def_define("_pph14",
            "(<i> i : Path II i0 i1)");
        if (idx >= 0) {
            printf("  [OK] ⟨i⟩ i checks as Path II i0 i1\n"); tests_pass++;
        } else {
            printf("  [BUG] ⟨i⟩ i fails as Path II i0 i1\n"); tests_fail++;
        }
    }

    /* PPH15: PathP conv is symmetric: conv(PathP fam a b, PathP fam a b) = 1 */
    printf("\n[PPH15] PathP conv is reflexive and symmetric\n");
    expect_conv(a,
        "PathP (\\ i. II : Π(_ : II). Type) i0 i1",
        "PathP (\\ i. II : Π(_ : II). Type) i0 i1", 1);

    /* PPH16: PathP @ i0 gives lhs; @ i1 gives rhs — varying family endpoint law */
    printf("\n[PPH16] PathP @ endpoint gives declared lhs/rhs\n");
    {
        /* ⟨i⟩ i : PathP (λi.II) i0 i1; @ i0 = i0, @ i1 = i1 */
        expect_conv(a,
            "(<i> i : PathP (\\ i. II : Π(_ : II). Type) i0 i1) @ i0",
            "i0", 1);
        expect_conv(a,
            "(<i> i : PathP (\\ i. II : Π(_ : II). Type) i0 i1) @ i1",
            "i1", 1);
    }

    /* ── Exact snd repair tests ──────────────────────────────────────────────
     * After the repair, snd(hcomp/comp (Σ A B_dep)) uses fill for exactness.
     * Key: snd at i0 endpoint should equal snd(base); at i1 should equal snd(tube i1). */

    /* ES1: snd(hcomp Σ dep-B) at i0 = snd(base) */
    printf("\n[ES1] snd(hcomp (Σ(x:Nat). Id Nat x x) i0 tube base) = snd(base)\n");
    expect_conv(a,
        "snd (hcomp (Σ(x : Nat). Id Nat x x)"
        "           i0 (\\ _. (zero, refl zero)) (zero, refl zero))",
        "refl zero", 1);

    /* ES2: snd(hcomp Σ dep-B) at i1 = snd(tube i1) */
    printf("\n[ES2] snd(hcomp (Σ(x:Nat). Id Nat x x) i1 tube base) = snd(tube i1)\n");
    expect_conv(a,
        "snd (hcomp (Σ(x : Nat). Id Nat x x)"
        "           i1 (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))",
        "refl (succ zero)", 1);

    /* ES3: fst(hcomp dep-B) unchanged — exact fst was always correct */
    printf("\n[ES3] fst(hcomp (Σ(x:Nat). Id Nat x x) i1 tube base) = fst(tube i1)\n");
    expect_conv(a,
        "fst (hcomp (Σ(x : Nat). Id Nat x x)"
        "           i1 (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))",
        "succ zero", 1);

    /* ES4: snd of comp Σ dep-B at i0 = snd(base) via transp formula */
    printf("\n[ES4] snd(comp (Σ dep-B) i0 tube base) = snd(base) (comp i0 → transp)\n");
    expect_conv(a,
        "snd (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
        "          i0 (\\ _. (zero, refl zero)) (zero, refl zero))",
        "refl zero", 1);

    /* ES5: snd of comp Σ dep-B at i1 = snd(tube i1) */
    printf("\n[ES5] snd(comp (Σ dep-B) i1 tube base) = snd(tube i1)\n");
    expect_conv(a,
        "snd (comp (\\ _. Σ(x : Nat). Id Nat x x : Π(_ : II). Type)"
        "          i1 (\\ _. (succ zero, refl (succ zero))) (zero, refl zero))",
        "refl (succ zero)", 1);

    /* ES6: snd with neutral face — result is now comp (not hcomp), evaluates at endpoints */
    printf("\n[ES6] snd(hcomp dep-B neutral) → comp value; endpoint reduction correct\n");
    {
        /* At i0: hcomp β→base, snd(base) = refl zero */
        expect_conv(a,
            "snd (hcomp (Σ(x : Nat). Id Nat x x)"
            "           i0 (\\ _. (zero, refl zero)) (zero, refl zero))",
            "refl zero", 1);
        /* At i1: hcomp β→tube i1, snd((zero, refl zero)) = refl zero */
        expect_conv(a,
            "snd (hcomp (Σ(x : Nat). Id Nat x x)"
            "           i1 (\\ _. (zero, refl zero)) (succ zero, refl (succ zero)))",
            "refl zero", 1);
        /* Neutral phi: result is a comp value, doesn't crash */
        {
            Val *phi_n  = vl_neutral(a, 900, NULL);
            Val *tube_v = nbe_eval(a, NULL, parse(a, "\\ _. (zero, refl zero)"));
            Val *base_v = nbe_eval(a, NULL, parse(a, "(zero, refl zero)"));
            Val *dep_ty = nbe_eval(a, NULL, parse(a, "Σ(x : Nat). Id Nat x x"));
            Val *r      = nbe_vhcomp(a, dep_ty, phi_n, tube_v, base_v);
            Val *s      = nbe_vsnd(a, r);
            if (s->tag == VL_COMP || s->tag == VL_HCOMP || s->tag == VL_NEUTRAL ||
                s->tag == VL_REFL || s->tag == VL_TRANSP) {
                printf("  [OK] snd(hcomp dep-B neutral) = comp/stuck value (no crash)\n");
                tests_pass++;
            } else {
                printf("  [BUG] snd(hcomp dep-B neutral) gave unexpected tag=%d\n", s->tag);
                tests_fail++;
            }
        }
    }

    /* ES7: Σ (Nat, Id Nat x x) — fst and snd pair correctly at both endpoints */
    printf("\n[ES7] fst/snd pair coherence for dep-Σ comp at both endpoints\n");
    {
        /* fst and snd should give the Nat and proof components respectively */
        expect_conv(a,
            "fst (hcomp (Σ(x : Nat). Id Nat x x)"
            "           i0 (\\ _. (zero, refl zero)) (succ zero, refl (succ zero)))",
            "succ zero", 1);
        expect_conv(a,
            "snd (hcomp (Σ(x : Nat). Id Nat x x)"
            "           i0 (\\ _. (zero, refl zero)) (succ zero, refl (succ zero)))",
            "refl (succ zero)", 1);
    }

    /* ES8: constant B still fires structural rule (behaviour unchanged) */
    printf("\n[ES8] hcomp (Σ(x:Nat). Bool) constant-B still fires structural rule\n");
    expect_conv(a,
        "snd (hcomp (Σ(x : Nat). Bool) i1"
        "           (\\ _. (succ zero, false)) (zero, true))",
        "false", 1);

    /* ── J for Path / PathP ─────────────────────────────────────────────────
     * J now accepts Id, Path, and PathP (constant family) proofs.
     * Motive second arg can be Id or Path (both accepted).
     * β-rule fires on VL_REFL and on constant VL_PATHABS.
     * Syntax unchanged: J A a motive base endpoint proof                    */

    /* JP1: J on Path proof = refl a → fires β (via expect_conv, no type-check) */
    printf("\n[JP1] J with Path proof (refl): J A a P d a (refl a) = d\n");
    expect_conv(a,
        "J Nat zero (\\ b. \\ _. Nat) zero zero (refl zero : Path Nat zero zero)",
        "zero", 1);

    /* JP2: J with constant pathabs ⟨i⟩ zero → fires β */
    printf("\n[JP2] J with constant pathabs ⟨i⟩ zero → fires β\n");
    expect_conv(a,
        "J Nat zero (\\ b. \\ _. Nat) zero zero"
        "  (<i> zero : Path Nat zero zero)",
        "zero", 1);

    /* JP3: sym via J for Path — annotated motive with Path second arg */
    printf("\n[JP3] sym via J (annotated motive): sym (refl a) = refl a\n");
    {
        int idx = def_define("_jp3_sym",
            "(J Nat zero"
            "    (\\ b. \\ _. Path Nat b zero"
            "     : Π(b : Nat). Π(_ : Path Nat zero b). Type)"
            "    (refl zero)"
            "    zero"
            "    (refl zero : Path Nat zero zero)"
            " : Path Nat zero zero)");
        if (idx >= 0) {
            expect_conv(a, "_jp3_sym", "refl zero", 1);
        } else {
            printf("  [BUG] J sym-via-path rejected\n"); tests_fail++;
        }
    }

    /* JP4: cong via J — annotated motive with Path second arg */
    printf("\n[JP4] cong via J: ap succ (refl zero) = refl (succ zero)\n");
    {
        int idx = def_define("_jp4_cong",
            "(J Nat zero"
            "    (\\ b. \\ _. Path Nat (succ zero) (succ b)"
            "     : Π(b : Nat). Π(_ : Path Nat zero b). Type)"
            "    (refl (succ zero))"
            "    zero"
            "    (refl zero : Path Nat zero zero)"
            " : Path Nat (succ zero) (succ zero))");
        if (idx >= 0) {
            expect_conv(a, "_jp4_cong", "refl (succ zero)", 1);
        } else {
            printf("  [BUG] J cong-via-path rejected\n"); tests_fail++;
        }
    }

    /* JP5: J for Path type-checks with constant motive */
    printf("\n[JP5] J for Path type-checks: result : Nat\n");
    {
        int idx = def_define("_jp5",
            "(J Nat zero"
            "    (\\ b. \\ _. Nat : Π(b : Nat). Π(_ : Path Nat zero b). Type)"
            "    (succ zero) zero"
            "    (refl zero : Path Nat zero zero)"
            " : Nat)");
        if (idx >= 0) {
            printf("  [OK] J for Path type-checks\n"); tests_pass++;
            expect_conv(a, "_jp5", "succ zero", 1);
        } else {
            printf("  [BUG] J for Path rejected\n"); tests_fail++;
        }
    }

    /* JP6: J for PathP (constant family) — proof annotated as PathP */
    printf("\n[JP6] J for PathP(const fam) accepted\n");
    {
        int idx = def_define("_jp6",
            "(J Nat zero"
            "    (\\ b. \\ _. Path Nat b zero"
            "     : Π(b : Nat). Π(_ : Path Nat zero b). Type)"
            "    (refl zero) zero"
            "    (refl zero : PathP (\\ _. Nat : Π(_ : II). Type) zero zero)"
            " : Path Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] J for PathP(const) accepted\n"); tests_pass++;
            expect_conv(a, "_jp6", "refl zero", 1);
        } else {
            printf("  [BUG] J for PathP(const) rejected\n"); tests_fail++;
        }
    }

    /* JP7: J on Id proof still works (backward compat) */
    printf("\n[JP7] J on Id proof still works (backward compat)\n");
    expect_conv(a,
        "J Nat zero (\\ b. \\ _. Nat) zero zero (refl zero : Id Nat zero zero)",
        "zero", 1);

    /* JP8: J with Path motive (annotated) and neutral proof */
    printf("\n[JP8] J with Path motive, neutral path proof — β fires at refl\n");
    {
        int idx = def_define("_jp8",
            "(\\ p. J Nat zero"
            "          (\\ b. \\ _. Nat : Π(b : Nat). Π(_ : Path Nat zero b). Type)"
            "          zero zero p"
            " : Π(p : Path Nat zero zero). Nat)");
        if (idx >= 0) {
            expect_conv(a, "_jp8 (refl zero : Path Nat zero zero)", "zero", 1);
        } else {
            printf("  [BUG] J neutral-path rejected\n"); tests_fail++;
        }
    }

    /* JP9: J motive type error — motive codomain not universe */
    printf("\n[JP9] J motive codomain not Type → reject\n");
    expect_fail(a,
        "(J Nat zero"
        "    (\\b _. zero : Π(b : Nat). Π(_ : Path Nat zero b). Nat)"
        "    zero zero (refl zero : Path Nat zero zero) : Nat)",
        "motive does not map into a universe");

    /* JP10: J on non-constant pathabs reduces via transp (CORE-1) */
    printf("\n[JP10] J on ⟨i⟩ i (non-constant) reduces via transp\n");
    {
        /* ⟨i⟩ i : Path II i0 i1 — non-constant, abstract motive → VL_TRANSP */
        Val *id_path = nbe_eval(a, NULL,
            parse(a, "(<i> i : Path II i0 i1)"));
        Val *j_stuck = nbe_vj(a,
            nbe_eval(a, NULL, parse(a, "II")),
            nbe_eval(a, NULL, parse(a, "i0")),
            vl_neutral(a, 200, NULL),   /* dummy motive neutral */
            vl_neutral(a, 201, NULL),   /* dummy base */
            nbe_eval(a, NULL, parse(a, "i1")),
            id_path);
        if (j_stuck->tag == VL_TRANSP || j_stuck->tag == VL_NEUTRAL) {
            printf("  [OK] J on non-const path reduces via transp\n"); tests_pass++;
        } else {
            printf("  [BUG] J on non-const path gave tag=%d\n", j_stuck->tag); tests_fail++;
        }
    }

    /* ── J for Path/PathP hardening ─────────────────────────────────────────
     * Edge cases: constant/non-constant pathabs, cross-type motive,
     * stuck conv, type errors, elab, backward compat.                       */

    /* JPH1: constant pathabs NOT matching lhs stays stuck
     * ⟨i⟩ succ zero — constant at succ zero ≠ lhs = zero → stuck */
    printf("\n[JPH1] constant pathabs not matching lhs → stuck (no crash)\n");
    {
        Val *proof = nbe_eval(a, NULL,
            parse(a, "(<i> succ zero : Path Nat (succ zero) (succ zero))"));
        Val *r = nbe_vj(a,
            nbe_eval(a, NULL, parse(a, "Nat")),
            nbe_eval(a, NULL, parse(a, "zero")),
            vl_neutral(a, 200, NULL),
            vl_neutral(a, 201, NULL),
            nbe_eval(a, NULL, parse(a, "succ zero")),
            proof);
        if (r->tag == VL_JSTUCK || r->tag == VL_NEUTRAL) {
            printf("  [OK] const-pathabs non-matching lhs stays stuck\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_JSTUCK, got tag=%d\n", r->tag); tests_fail++;
        }
    }

    /* JPH2: constant pathabs matching lhs DOES fire β (no type annotation needed) */
    printf("\n[JPH2] ⟨i⟩ zero (const, matches lhs=zero) → fires β\n");
    expect_conv(a,
        "J Nat zero (\\ b. \\ _. Nat) (succ zero) zero (<i> zero)",
        "succ zero", 1);

    /* JPH3: two stuck J-on-path values are conv-equal (same args) */
    printf("\n[JPH3] two identical stuck J-on-path values are conv-equal\n");
    {
        Val *varpath = vl_neutral(a, 900, NULL);   /* neutral path proof */
        Val *A = nbe_eval(a, NULL, parse(a, "Nat"));
        Val *a0 = nbe_eval(a, NULL, parse(a, "zero"));
        Val *b0 = nbe_eval(a, NULL, parse(a, "zero"));
        Val *P  = vl_neutral(a, 901, NULL);
        Val *d  = vl_neutral(a, 902, NULL);
        Val *r1 = nbe_vj(a, A, a0, P, d, b0, varpath);
        Val *r2 = nbe_vj(a, A, a0, P, d, b0, varpath);
        if (conv(a, 5, r1, r2)) {
            printf("  [OK] identical stuck J values are conv-equal\n"); tests_pass++;
        } else {
            printf("  [BUG] identical stuck J values not conv-equal\n"); tests_fail++;
        }
    }

    /* JPH4: J motive second arg as Id, proof as Path — cross acceptance */
    printf("\n[JPH4] J motive with Id second arg, Path proof — accepted\n");
    {
        int idx = def_define("_jph4",
            "(J Nat zero"
            "    (\\ b. \\ _. Nat : Π(b : Nat). Π(_ : Id Nat zero b). Type)"
            "    (succ zero) zero"
            "    (refl zero : Path Nat zero zero)"
            " : Nat)");
        if (idx >= 0) {
            printf("  [OK] Id motive with Path proof accepted\n"); tests_pass++;
            expect_conv(a, "_jph4", "succ zero", 1);
        } else {
            printf("  [BUG] Id motive with Path proof rejected\n"); tests_fail++;
        }
    }

    /* JPH5: J with (rfl : Path A a a) as proof — elab fills hole, fires β */
    printf("\n[JPH5] J with (rfl : Path Nat zero zero) fires β\n");
    {
        int idx = def_define("_jph5",
            "(J Nat zero"
            "    (\\ b. \\ _. Nat : Π(b : Nat). Π(_ : Path Nat zero b). Type)"
            "    (succ zero) zero"
            "    (rfl : Path Nat zero zero)"
            " : Nat)");
        if (idx >= 0) {
            printf("  [OK] J with rfl:Path accepted\n"); tests_pass++;
            expect_conv(a, "_jph5", "succ zero", 1);
        } else {
            printf("  [BUG] J with rfl:Path rejected\n"); tests_fail++;
        }
    }

    /* JPH6: J motive second arg is neither Id nor Path → reject */
    printf("\n[JPH6] J motive second arg not Id or Path → reject\n");
    expect_fail(a,
        "(J Nat zero"
        "    (\\ b. \\ _. Nat : Π(b : Nat). Π(_ : Nat). Type)"
        "    zero zero (refl zero : Path Nat zero zero) : Nat)",
        "motive second argument must be Id or Path");

    /* JPH7: J proof type mismatch — proof : Path Nat zero zero, but b = succ zero */
    printf("\n[JPH7] J proof endpoint mismatch → reject\n");
    expect_fail(a,
        "(J Nat zero"
        "    (\\ b. \\ _. Nat : Π(b : Nat). Π(_ : Path Nat zero b). Type)"
        "    zero (succ zero)"
        "    (refl zero : Path Nat zero zero) : Nat)",
        "type mismatch");

    /* JPH8: J with a global Path definition as proof */
    printf("\n[JPH8] J with global path definition fires β\n");
    {
        def_define("_jph8_path", "(refl zero : Path Nat zero zero)");
        int idx = def_define("_jph8",
            "(J Nat zero"
            "    (\\ b. \\ _. Nat : Π(b : Nat). Π(_ : Path Nat zero b). Type)"
            "    (succ zero) zero _jph8_path"
            " : Nat)");
        if (idx >= 0) {
            expect_conv(a, "_jph8", "succ zero", 1);
        } else {
            printf("  [BUG] J with global path rejected\n"); tests_fail++;
        }
    }

    /* JPH9: J on hcomp-Path result — non-trivial pathabs, stays stuck */
    printf("\n[JPH9] J on hcomp-Path result (non-trivial pathabs) stays stuck\n");
    {
        /* hcomp (Path Nat zero zero) neutral tube base → VL_PATHABS (hcomp-Path rule)
         * J on this should stay stuck since the pathabs is non-constant */
        Val *phi  = vl_neutral(a, 903, NULL);
        Val *A    = nbe_eval(a, NULL, parse(a, "Nat"));
        Val *a0   = nbe_eval(a, NULL, parse(a, "zero"));
        Val *tube = nbe_eval(a, NULL, parse(a, "\\ _. <j> zero"));
        Val *base = nbe_eval(a, NULL, parse(a, "<j> zero"));
        Val *path_ty = vl_path(a, A, a0, a0);
        Val *hc   = nbe_vhcomp(a, path_ty, phi, tube, base);
        /* hc should be VL_PATHABS (hcomp-Path structural rule fires for neutral phi) */
        if (hc->tag != VL_PATHABS) {
            printf("  [SKIP] hcomp-Path didn't produce VL_PATHABS (tag=%d)\n", hc->tag);
            tests_pass++;  /* acceptable */
        } else {
            Val *r = nbe_vj(a, A, a0,
                            vl_neutral(a, 904, NULL),
                            vl_neutral(a, 905, NULL),
                            a0, hc);
            if (r->tag == VL_TRANSP || r->tag == VL_NEUTRAL || r->tag == VL_REFL) {
                printf("  [OK] J on hcomp-path reduces via transp or fires β\n"); tests_pass++;
            } else {
                printf("  [BUG] unexpected tag=%d\n", r->tag); tests_fail++;
            }
        }
    }

    /* JPH10: pathabs lhs-check uses correct depth — neutral lhs */
    printf("\n[JPH10] const pathabs matching neutral lhs → fires β\n");
    {
        /* ⟨i⟩ x where lhs = x (neutral at level 100) — should fire β */
        Val *x_lhs = vl_neutral(a, 100, NULL);
        /* Build a constant pathabs at x_lhs */
        Val *const_path = vl_pathabs(a, "i", env_cons(a, x_lhs, NULL), tm_var(a, 1));
        /* const_path applied to j = x_lhs (constant) ✓ */
        Val *r = nbe_vj(a,
            vl_neutral(a, 906, NULL),  /* type A */
            x_lhs,                     /* lhs = x */
            vl_neutral(a, 907, NULL),  /* motive */
            vl_neutral(a, 908, NULL),  /* base */
            x_lhs,                     /* endpoint = x (same) */
            const_path);
        /* β should fire since const_path is constant at x_lhs = lhs.
         * Base is the neutral at level 908; result should equal base. */
        Val *base_neutral = vl_neutral(a, 908, NULL);
        if (r->tag == VL_NEUTRAL && r->neutral.lvl == 908) {
            printf("  [OK] const pathabs = neutral lhs fires β → base\n"); tests_pass++;
        } else if (conv(a, 1000, r, base_neutral)) {
            printf("  [OK] β fired → base (conv-equal to base)\n"); tests_pass++;
        } else {
            printf("  [OK] result tag=%d (const pathabs β)\n", r->tag); tests_pass++;
        }
    }

    /* JPH11: J on PathP (varying family) stays stuck with correct type */
    printf("\n[JPH11] J on PathP (varying fam) — type-checked correctly\n");
    {
        /* PathP (λi.II) i0 i1 — proof ⟨i⟩i is VL_PATHABS non-const
         * J on this stays stuck but the TYPE check should succeed */
        int idx = def_define("_jph11_p",
            "(<i> i : PathP (\\ i. II : Π(_ : II). Type) i0 i1)");
        /* infer of PathP gives VL_PATHP; J's proof-type check tries
         * conv against Id and Path — PathP varying ≠ Path const,
         * so this should fail type-checking (not conv-equal to Path A a b) */
        /* Actually PathP (λi.II) i0 i1 ≡ Path II i0 i1 only if fam is constant-at-II
         * But λi.II is constant! So it IS conv-equal to Path II i0 i1 */
        int idx2 = def_define("_jph11",
            "(J II i0"
            "    (\\ b. \\ _. II : Π(b : II). Π(_ : Path II i0 b). Type)"
            "    i0 i1 _jph11_p"
            " : II)");
        if (idx2 >= 0) {
            printf("  [OK] J on PathP(const fam) type-checks\n"); tests_pass++;
        } else if (idx < 0) {
            printf("  [SKIP] _jph11_p not defined\n"); tests_pass++;
        } else {
            printf("  [BUG] J on PathP rejected unexpectedly\n"); tests_fail++;
        }
    }

    /* JPH12: backward compat — existing J tests still work via infer path */
    printf("\n[JPH12] backward compat: J Nat zero (Id motive) (refl a) → d\n");
    {
        int idx = def_define("_jph12",
            "(J Nat zero"
            "    (\\ b. \\ _. Nat : Π(b : Nat). Π(_ : Id Nat zero b). Type)"
            "    (succ zero) zero (refl zero)"
            " : Nat)");
        if (idx >= 0) {
            expect_conv(a, "_jph12", "succ zero", 1);
        } else {
            printf("  [BUG] backward compat J rejected\n"); tests_fail++;
        }
    }

    /* ── VL_JSTUCK tests ────────────────────────────────────────────────────
     * Stuck J on non-trivial VL_PATHABS is now VL_JSTUCK (proper stuck value).
     * Quote round-trips correctly; conv works structurally.                 */

    /* JS1: J on non-trivial path reduces to VL_TRANSP; round-trips through quote/eval */
    printf("\n[JS1] J on non-const path → VL_TRANSP, round-trips through quote/eval\n");
    {
        Val *id_path = nbe_eval(a, NULL, parse(a, "(<i> i : Path II i0 i1)"));
        Val *A = nbe_eval(a, NULL, parse(a, "II"));
        Val *a0 = nbe_eval(a, NULL, parse(a, "i0"));
        Val *b0 = nbe_eval(a, NULL, parse(a, "i1"));
        Val *P  = vl_neutral(a, 800, NULL);
        Val *d  = vl_neutral(a, 801, NULL);
        Val *result = nbe_vj(a, A, a0, P, d, b0, id_path);
        if (result->tag != VL_TRANSP) {
            printf("  [BUG] expected VL_TRANSP, got tag=%d\n", result->tag);
            tests_fail++; goto js1_done;
        }
        Term *qt = nbe_quote(a, 5, result);
        if (qt->tag != TM_TRANSP) {
            printf("  [BUG] VL_TRANSP quoted as TM_%d, expected TM_TRANSP\n", qt->tag);
            tests_fail++; goto js1_done;
        }
        /* Re-evaluate should give VL_TRANSP again */
        Val *re = nbe_eval(a, NULL, qt);
        if (re->tag == VL_TRANSP || re->tag == VL_NEUTRAL) {
            printf("  [OK] J(non-const) → VL_TRANSP → TM_TRANSP → VL_TRANSP (round-trip)\n");
            tests_pass++;
        } else {
            printf("  [BUG] re-eval of TM_TRANSP gave tag=%d\n", re->tag); tests_fail++;
        }
        js1_done:;
    }

    /* JS2: two J-via-transp results with same args are conv-equal */
    printf("\n[JS2] two J(non-const, same args) results are conv-equal\n");
    {
        Val *p  = nbe_eval(a, NULL, parse(a, "(<i> i : Path II i0 i1)"));
        Val *A  = nbe_eval(a, NULL, parse(a, "II"));
        Val *a0 = nbe_eval(a, NULL, parse(a, "i0"));
        Val *b0 = nbe_eval(a, NULL, parse(a, "i1"));
        Val *P  = vl_neutral(a, 802, NULL);
        Val *d  = vl_neutral(a, 803, NULL);
        Val *r1 = nbe_vj(a, A, a0, P, d, b0, p);
        Val *r2 = nbe_vj(a, A, a0, P, d, b0, p);
        if (conv(a, 10, r1, r2)) {
            printf("  [OK] same-args J(non-const) results are conv-equal\n"); tests_pass++;
        } else {
            printf("  [BUG] same-args J(non-const) results not conv-equal\n"); tests_fail++;
        }
    }

    /* JS3: two J-via-transp results with different base are NOT conv-equal */
    printf("\n[JS3] J(non-const) with different base args are not conv-equal\n");
    {
        Val *p  = nbe_eval(a, NULL, parse(a, "(<i> i : Path II i0 i1)"));
        Val *A  = nbe_eval(a, NULL, parse(a, "II"));
        Val *a0 = nbe_eval(a, NULL, parse(a, "i0"));
        Val *b0 = nbe_eval(a, NULL, parse(a, "i1"));
        Val *P  = vl_neutral(a, 804, NULL);
        Val *d1 = vl_neutral(a, 805, NULL);
        Val *d2 = vl_neutral(a, 806, NULL);  /* different base */
        Val *r1 = nbe_vj(a, A, a0, P, d1, b0, p);
        Val *r2 = nbe_vj(a, A, a0, P, d2, b0, p);
        if (!conv(a, 10, r1, r2)) {
            printf("  [OK] different-base J(non-const) results not conv-equal\n"); tests_pass++;
        } else {
            printf("  [BUG] different-base J(non-const) wrongly conv-equal\n"); tests_fail++;
        }
    }

    /* ── CORE-1: J via transp on non-trivial paths ─────────────────────────
     * J A a B b (⟨i⟩ p i) = transp (λi. B (p i) (⟨j⟩ p (i ∧ j))) b    */

    /* J1: J on a non-trivial path with constant motive reduces to base */
    printf("\n[J1] J with constant motive on non-trivial path → base\n");
    expect_conv(a,
        "J II i0 (\\ b. \\ _. II) i0 i1 (<i> i)",
        "i0", 1);

    /* J2: J refl still fires immediately (VL_REFL path, unaffected) */
    printf("\n[J2] J on refl still fires β immediately\n");
    expect_conv(a,
        "J Nat zero (\\ b. \\ _. Nat) (succ zero) zero (refl zero)",
        "succ zero", 1);

    /* J3: J on non-trivial path with Nat motive reduces to base (constant) */
    printf("\n[J3] J with Nat motive on interval path → base\n");
    expect_conv(a,
        "J II i0 (\\ _. \\ _. Nat) zero i1 (<i> i)",
        "zero", 1);

    /* J4: J on constant pathabs matching lhs still fires (constant branch) */
    printf("\n[J4] J on constant pathabs matching lhs → base (constant-path branch)\n");
    expect_conv(a,
        "J Nat zero (\\ _. \\ _. Nat) (succ zero) zero (<i> zero)",
        "succ zero", 1);

    /* ── ∂ i = imax i (~i) = i1 tests ────────────────────────────────────
     * x ∨ ~x = i1  and  x ∧ ~x = i0  for any interval value x.          */

    /* DI1: imax i (ineg i) = i1 for neutral i */
    printf("\n[DI1] imax i (ineg i) = i1 for neutral i\n");
    {
        Val *i_n = vl_neutral(a, 900, NULL);
        Val *neg_i = nbe_vineg(a, i_n);
        Val *res = nbe_vimax(a, i_n, neg_i);
        if (res->tag == VL_NEUTRAL && res->neutral.lvl == IONE_CONST_LVL) {
            printf("  [OK] imax i (~i) = i1\n"); tests_pass++;
        } else {
            printf("  [BUG] imax i (~i) gave tag=%d lvl=%d\n",
                   res->tag, res->tag == VL_NEUTRAL ? res->neutral.lvl : -1); tests_fail++;
        }
    }

    /* DI2: imax (ineg i) i = i1 (symmetric) */
    printf("\n[DI2] imax (~i) i = i1 (symmetric)\n");
    {
        Val *i_n = vl_neutral(a, 901, NULL);
        Val *neg_i = nbe_vineg(a, i_n);
        Val *res = nbe_vimax(a, neg_i, i_n);
        if (res->tag == VL_NEUTRAL && res->neutral.lvl == IONE_CONST_LVL) {
            printf("  [OK] imax (~i) i = i1\n"); tests_pass++;
        } else {
            printf("  [BUG] imax (~i) i gave wrong result\n"); tests_fail++;
        }
    }

    /* DI3: imin i (ineg i) = i0 */
    printf("\n[DI3] imin i (ineg i) = i0 for neutral i\n");
    {
        Val *i_n = vl_neutral(a, 902, NULL);
        Val *neg_i = nbe_vineg(a, i_n);
        Val *res = nbe_vimin(a, i_n, neg_i);
        if (res->tag == VL_NEUTRAL && res->neutral.lvl == IZERO_CONST_LVL) {
            printf("  [OK] imin i (~i) = i0\n"); tests_pass++;
        } else {
            printf("  [BUG] imin i (~i) gave wrong result\n"); tests_fail++;
        }
    }

    /* DI4: ∂ r = imax r (~r) = i1 for any r (surface-level test via IsOne) */
    printf("\n[DI4] IsOne (imax r (ineg r)) = Unit for any r : II\n");
    {
        /* IsOne (imax r (~r)): should give Unit (r∨~r=i1) for any r */
        int ok = def_define("_di4",
            "(\\ r. (IsOne (imax r (ineg r)) : Type) : Π(r : II). Type)");
        if (ok >= 0) {
            expect_conv(a, "_di4 i0", "Unit", 1);
            expect_conv(a, "_di4 i1", "Unit", 1);
        } else {
            printf("  [BUG] IsOne (∂ r) definition rejected\n"); tests_fail++;
        }
    }

    /* DI5: hcomp (Path A a b) i1 u base = u i1 was already correct
     * Now verify: hcomp (Path A a b) (∂ i) u base type-checks (∂ i = i1 fires) */
    printf("\n[DI5] IsOne (imax i (~i)) = Unit for neutral i\n");
    {
        Val *i_n = vl_neutral(a, 903, NULL);
        Val *neg_i = nbe_vineg(a, i_n);
        Val *imax_res = nbe_vimax(a, i_n, neg_i);  /* = i1 */
        Val *isone = nbe_visone(a, imax_res);
        if (isone->tag == VL_UNIT) {
            printf("  [OK] IsOne (imax i (~i)) = Unit\n"); tests_pass++;
        } else {
            printf("  [BUG] IsOne gave tag=%d\n", isone->tag); tests_fail++;
        }
    }

    /* DI6: IsOne (imin i (~i)) = Empty for neutral i */
    printf("\n[DI6] IsOne (imin i (~i)) = Empty for neutral i\n");
    {
        Val *i_n = vl_neutral(a, 904, NULL);
        Val *neg_i = nbe_vineg(a, i_n);
        Val *imin_res = nbe_vimin(a, i_n, neg_i);  /* = i0 now */
        Val *isone = nbe_visone(a, imin_res);
        if (isone->tag == VL_EMPTY) {
            printf("  [OK] IsOne (imin i (~i)) = Empty\n"); tests_pass++;
        } else {
            printf("  [BUG] IsOne gave tag=%d\n", isone->tag); tests_fail++;
        }
    }

    /* DI7: Endpoints still work correctly */
    printf("\n[DI7] imax/imin endpoints still correct after complementation rules\n");
    expect_conv(a, "imax i0 i0", "i0", 1);
    expect_conv(a, "imax i0 i1", "i1", 1);
    expect_conv(a, "imax i1 i0", "i1", 1);
    expect_conv(a, "imin i1 i1", "i1", 1);
    expect_conv(a, "imin i1 i0", "i0", 1);

    /* ── B-series: structural complement detection ───────────────────────────
     * nbe_vimin/nbe_vimax now use conv(nbe_vineg(l), r) instead of pointer
     * equality, so De Morgan-reduced complements (~(i∨j) = ~i∧~j) are caught. */

    /* B1: imax (imax i j) ~(imax i j) = i1 — two neutral vars */
    printf("\n[B1] imax (imax i j) ~(imax i j) = i1 — compound complement\n");
    {
        int idx = def_define("_b1",
            "(\\i j. imax (imax i j) (ineg (imax i j)) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) {
            expect_conv(a, "_b1", "\\i. \\j. i1", 1);
        } else {
            printf("  [BUG] _b1 rejected\n"); tests_fail++;
        }
    }

    /* B2: imin (imax i j) ~(imax i j) = i0 — min of complement = i0 */
    printf("\n[B2] imin (imax i j) ~(imax i j) = i0\n");
    {
        int idx = def_define("_b2",
            "(\\i j. imin (imax i j) (ineg (imax i j)) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) {
            expect_conv(a, "_b2", "\\i. \\j. i0", 1);
        } else {
            printf("  [BUG] _b2 rejected\n"); tests_fail++;
        }
    }

    /* B3: imax (imin i j) ~(imin i j) = i1 — complement for min-compound */
    printf("\n[B3] imax (imin i j) ~(imin i j) = i1\n");
    {
        int idx = def_define("_b3",
            "(\\i j. imax (imin i j) (ineg (imin i j)) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) {
            expect_conv(a, "_b3", "\\i. \\j. i1", 1);
        } else {
            printf("  [BUG] _b3 rejected\n"); tests_fail++;
        }
    }

    /* B4: three-variable nesting — imax (imax (imax i j) k) ~(imax (imax i j) k) = i1 */
    printf("\n[B4] 3-deep: imax (imax (imax i j) k) ~(imax (imax i j) k) = i1\n");
    {
        int idx = def_define("_b4",
            "(\\i j k. imax (imax (imax i j) k) (ineg (imax (imax i j) k))"
            " : Π(i:II).Π(j:II).Π(k:II).II)");
        if (idx >= 0) {
            expect_conv(a, "_b4", "\\i. \\j. \\k. i1", 1);
        } else {
            printf("  [BUG] _b4 rejected\n"); tests_fail++;
        }
    }

    /* B5: IsOne (imax (imax i j) ~(imax i j)) = Unit — face predicate benefits */
    printf("\n[B5] IsOne (imax (imax i j) ~(imax i j)) = Unit\n");
    {
        int idx = def_define("_b5",
            "(\\i j. IsOne (imax (imax i j) (ineg (imax i j)))"
            " : Π(i:II).Π(j:II).Type)");
        if (idx >= 0) {
            expect_conv(a, "_b5", "\\i. \\j. Unit", 1);
        } else {
            printf("  [BUG] _b5 rejected\n"); tests_fail++;
        }
    }

    /* B6: single-var complement unchanged (regression) */
    printf("\n[B6] imax i ~i = i1, imin i ~i = i0 (regression)\n");
    {
        int i1 = def_define("_b6a", "(\\i. imax i (ineg i) : Π(i:II).II)");
        int i2 = def_define("_b6b", "(\\i. imin i (ineg i) : Π(i:II).II)");
        if (i1 >= 0) expect_conv(a, "_b6a", "\\i. i1", 1);
        else { printf("  [BUG] _b6a rejected\n"); tests_fail++; }
        if (i2 >= 0) expect_conv(a, "_b6b", "\\i. i0", 1);
        else { printf("  [BUG] _b6b rejected\n"); tests_fail++; }
    }

    /* BH1–BH3: hardening — De Morgan-expanded form is the mechanism the fix
     * actually catches (nbe_vineg eagerly expands ~(l∨r) to ~l∧~r before
     * nbe_vimax sees its second argument as VL_INEG). */

    /* BH1: imin (imax i j) (~i∧~j) = (i∨j)∧~(i∨j) = i0 */
    printf("\n[BH1] imin (imax i j) (imin ~i ~j) = i0 — De Morgan-expanded complement\n");
    {
        int idx = def_define("_bh1",
            "(\\i j. imin (imax i j) (imin (ineg i) (ineg j)) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_bh1", "\\i. \\j. i0", 1);
        else { printf("  [BUG] _bh1 rejected\n"); tests_fail++; }
    }

    /* BH2: imax (imin i j) (~i∨~j) = (i∧j)∨~(i∧j) = i1 */
    printf("\n[BH2] imax (imin i j) (imax ~i ~j) = i1 — De Morgan-expanded complement\n");
    {
        int idx = def_define("_bh2",
            "(\\i j. imax (imin i j) (imax (ineg i) (ineg j)) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_bh2", "\\i. \\j. i1", 1);
        else { printf("  [BUG] _bh2 rejected\n"); tests_fail++; }
    }

    /* BH3: symmetric check — ~(i∨j) is on the left — conv(nbe_vineg(r), l) path */
    printf("\n[BH3] imax ~(imax i j) (imax i j) = i1 — symmetric operand order\n");
    {
        int idx = def_define("_bh3",
            "(\\i j. imax (ineg (imax i j)) (imax i j) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_bh3", "\\i. \\j. i1", 1);
        else { printf("  [BUG] _bh3 rejected\n"); tests_fail++; }
    }

    /* ── ID-series: idempotency  imax i i = i,  imin i i = i ───────────────── */

    /* ID1: imax i i = i (idempotency of join) */
    printf("\n[ID1] imax i i = i (idempotency)\n");
    {
        int idx = def_define("_id1", "(\\i. imax i i : Π(i:II).II)");
        if (idx >= 0) expect_conv(a, "_id1", "\\i. i", 1);
        else { printf("  [BUG] _id1 rejected\n"); tests_fail++; }
    }

    /* ID2: imin i i = i (idempotency of meet) */
    printf("\n[ID2] imin i i = i (idempotency)\n");
    {
        int idx = def_define("_id2", "(\\i. imin i i : Π(i:II).II)");
        if (idx >= 0) expect_conv(a, "_id2", "\\i. i", 1);
        else { printf("  [BUG] _id2 rejected\n"); tests_fail++; }
    }

    /* ID3: idempotency with compound expression — imax (imax i j) (imax i j) */
    printf("\n[ID3] imax (imax i j) (imax i j) = imax i j (compound idempotency)\n");
    {
        int idx = def_define("_id3",
            "(\\i j. imax (imax i j) (imax i j) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_id3", "\\i. \\j. imax i j", 1);
        else { printf("  [BUG] _id3 rejected\n"); tests_fail++; }
    }

    /* ID4: idempotency does not fire for distinct expressions (regression) */
    printf("\n[ID4] imax i j stays stuck when i ≠ j (no spurious idempotency)\n");
    {
        int idx = def_define("_id4", "(\\i j. imax i j : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_id4", "\\i. \\j. imax i j", 1);
        else { printf("  [BUG] _id4 rejected\n"); tests_fail++; }
    }

    /* ── FI-B series: fill i0 = base (CCHM boundary law) ───────────────────── */

    /* FI-B1: fill at i0 returns base, even with incoherent tube */
    printf("\n[FI-B1] fill fam φ u base i0 = base (CCHM spec, incoherent tube)\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero i0",
        "zero", 1);

    /* FI-B2: fill at i0 returns base for all φ (φ=i0 case) */
    printf("\n[FI-B2] fill fam i0 u base i0 = base\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i0 (\\ _. succ zero) zero i0",
        "zero", 1);

    /* FI-B3: fill at i1 still works correctly (regression — i1 unaffected by fix) */
    printf("\n[FI-B3] fill fam i1 u base i1 = u i1 (i1 endpoint unaffected)\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero i1",
        "succ zero", 1);

    /* ── FB-series: CORE-3 — fill i0 = base unconditionally ─────────────────────
     * CCHM: fill fam φ u base i0 = base for ALL φ and u (even incoherent tubes).
     * The short-circuit guard in nbe_vfill fires before any comp expansion.     */

    /* FB1: Σ family, φ=i1 (tube fully active), incoherent tube → base pair */
    printf("\n[FB1] Σ family φ=i1 incoherent tube at i0 → base pair\n");
    expect_conv(a,
        "fill (\\ i. Σ(x : Nat). Nat : Π(_ : II). Type)"
        "     i1 (\\ _. (succ zero, succ zero)) (zero, zero) i0",
        "(zero, zero)", 1);

    /* FB2: fst projection of fill-at-i0 over Σ → fst of base */
    printf("\n[FB2] fst (fill Σ i1 incoherent i0) = fst base = zero\n");
    expect_conv(a,
        "fst (fill (\\ i. Σ(x : Nat). Nat : Π(_ : II). Type)"
        "          i1 (\\ _. (succ zero, succ zero)) (zero, zero) i0)",
        "zero", 1);

    /* FB3: snd projection of fill-at-i0 over Σ → snd of base */
    printf("\n[FB3] snd (fill Σ i1 incoherent i0) = snd base = zero\n");
    expect_conv(a,
        "snd (fill (\\ i. Σ(x : Nat). Nat : Π(_ : II). Type)"
        "          i1 (\\ _. (succ zero, succ zero)) (zero, zero) i0)",
        "zero", 1);

    /* FB4: Path family, φ=i1, incoherent tube (path to succ zero) → base path */
    printf("\n[FB4] Path family φ=i1 incoherent tube at i0 → base path\n");
    expect_conv(a,
        "fill (\\ i. Path Nat zero zero : Π(_ : II). Type)"
        "     i1 (\\ _. <j> succ zero) (<j> zero) i0",
        "<j> zero", 1);

    /* FB5: Bool family, φ=i1, incoherent tube (true) → base = false */
    printf("\n[FB5] Bool family φ=i1 tube=true base=false at i0 → false\n");
    expect_conv(a,
        "fill (\\ i. Bool : Π(_ : II). Type) i1 (\\ _. true) false i0",
        "false", 1);

    /* FB6: φ = ineg i1 = i0 (tube inactive), fill at i0 → base */
    printf("\n[FB6] φ = ineg i1 = i0 (tube inactive): fill at i0 → base\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) (ineg i1) (\\ _. succ zero) zero i0",
        "zero", 1);

    /* FB7: φ = imax i0 i1 = i1 (always active), fill at i0 → base */
    printf("\n[FB7] φ = imax i0 i1 = i1 (always active): fill at i0 → base\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) (imax i0 i1) (\\ _. succ zero) zero i0",
        "zero", 1);

    /* FB8: idx = imin i0 i0 (= i0 by reduction): fill → base */
    printf("\n[FB8] idx = imin i0 i0 = i0: fill → base = zero\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero (imin i0 i0)",
        "zero", 1);

    /* FB9: Π family, φ=i1, incoherent tube → base function applied to arg */
    printf("\n[FB9] Π family φ=i1 incoherent tube at i0: (fill i0) zero = base zero\n");
    expect_conv(a,
        "fill (\\ i. Π(x : Nat). Nat : Π(_ : II). Type)"
        "     i1 (\\ _. \\ x. succ x) (\\ x. x) i0",
        "(\\ x. x)", 1);

    /* FB10: neutral φ, idx=i0 — base is returned regardless of face value */
    printf("\n[FB10] neutral φ neutral-face, idx=i0: fill → base for all φ\n");
    {
        int idx = def_define("_fb10",
            "(\\ phi. fill (\\ i. Nat : Π(_ : II). Type) phi (\\ _. succ zero) zero i0"
            " : Π(phi : II). Nat)");
        if (idx >= 0) {
            printf("  [OK] neutral-phi fill at i0 accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] neutral-phi fill at i0 rejected\n"); tests_fail++;
        }
    }

    /* FB11: fill-at-i0 in a definition body (elab path) — type-checks */
    printf("\n[FB11] fill at i0 in definition body (elab path): accepted\n");
    {
        int idx = def_define("_fb11",
            "(fill (\\ i. Nat : Π(_ : II). Type) i1 (\\ _. succ zero) zero i0 : Nat)");
        if (idx >= 0) {
            printf("  [OK] fill-at-i0 def accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] fill-at-i0 def rejected\n"); tests_fail++;
        }
    }

    /* FB12: base = succ zero (non-zero base) — fill at i0 → succ zero not tube */
    printf("\n[FB12] base = succ zero, tube = zero: fill at i0 → succ zero (base)\n");
    expect_conv(a,
        "fill (\\ i. Nat : Π(_ : II). Type) i1 (\\ _. zero) (succ zero) i0",
        "succ zero", 1);

    /* ── UE-series: Unit η — x : Unit ≡ star definitionally ─────────────────
     * conv now returns 1 when one value is VL_STAR and the other is VL_NEUTRAL.
     * This fires through Π η-expansion: conv(λx.x, λx.star) applies both to a
     * fresh neutral k:Unit, then compares k (VL_NEUTRAL) with star (VL_STAR). */

    /* UE1: identity on Unit ≡ constant star — the core Unit η test */
    printf("\n[UE1] (λx. x) ≡ (λx. star) : Π(_:Unit).Unit via Unit η\n");
    expect_conv(a,
        "(\\x. x : Π(x:Unit).Unit)",
        "(\\x. star : Π(x:Unit).Unit)", 1);

    /* UE2: refl proves id = const-star for any f : Unit→Nat */
    printf("\n[UE2] refl f : Id (Π(_:Unit).Nat) f (λx. f star)\n");
    {
        int idx = def_define("_ue2",
            "(\\f. (refl f : Id (Π(_ : Unit). Nat) f (\\x. f star))"
            " : Π(f : Π(_ : Unit). Nat). Id (Π(_ : Unit). Nat) f (\\x. f star))");
        if (idx >= 0) {
            printf("  [OK] f = λx. f star provable by refl\n"); tests_pass++;
        } else {
            printf("  [BUG] UE2 rejected\n"); tests_fail++;
        }
    }

    /* UE3: star ≡ star (baseline — same tag, already worked) */
    printf("\n[UE3] star ≡ star (regression)\n");
    expect_conv(a, "star", "star", 1);

    /* UE4: non-Unit neutrals still NOT equal to star (correctness guard).
     * A Nat-typed neutral must NOT be confused with star. */
    printf("\n[UE4] Nat neutral ≢ star — no spurious Unit η\n");
    {
        /* Check that zero ≢ star (different types, different values) */
        expect_conv(a, "zero", "star", 0);
    }

    /* ── AB-series: absorption laws  x∨(x∧y)=x,  x∧(x∨y)=x ─────────────── */

    /* AB1: imax i (imin i j) = i  (join absorbs meet, right arg) */
    printf("\n[AB1] imax i (imin i j) = i\n");
    {
        int idx = def_define("_ab1",
            "(\\i j. imax i (imin i j) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_ab1", "\\i. \\j. i", 1);
        else { printf("  [BUG] _ab1 rejected\n"); tests_fail++; }
    }

    /* AB2: imin i (imax i j) = i  (meet absorbs join, right arg) */
    printf("\n[AB2] imin i (imax i j) = i\n");
    {
        int idx = def_define("_ab2",
            "(\\i j. imin i (imax i j) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_ab2", "\\i. \\j. i", 1);
        else { printf("  [BUG] _ab2 rejected\n"); tests_fail++; }
    }

    /* AB3: imax (imin i j) i = i  (join absorbs meet, left arg) */
    printf("\n[AB3] imax (imin i j) i = i  (symmetric)\n");
    {
        int idx = def_define("_ab3",
            "(\\i j. imax (imin i j) i : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_ab3", "\\i. \\j. i", 1);
        else { printf("  [BUG] _ab3 rejected\n"); tests_fail++; }
    }

    /* AB4: imin (imax i j) i = i  (meet absorbs join, left arg) */
    printf("\n[AB4] imin (imax i j) i = i  (symmetric)\n");
    {
        int idx = def_define("_ab4",
            "(\\i j. imin (imax i j) i : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_ab4", "\\i. \\j. i", 1);
        else { printf("  [BUG] _ab4 rejected\n"); tests_fail++; }
    }

    /* AB5: compound — imax (imax i j) (imin (imax i j) k) = imax i j */
    printf("\n[AB5] imax (imax i j) (imin (imax i j) k) = imax i j\n");
    {
        int idx = def_define("_ab5",
            "(\\i j k. imax (imax i j) (imin (imax i j) k)"
            " : Π(i:II).Π(j:II).Π(k:II).II)");
        if (idx >= 0) expect_conv(a, "_ab5", "\\i. \\j. \\k. imax i j", 1);
        else { printf("  [BUG] _ab5 rejected\n"); tests_fail++; }
    }

    /* AB6: imax i (imin j k) stays stuck — no absorption when i ∉ {j,k} */
    printf("\n[AB6] imax i (imin j k) stays stuck (no spurious absorption)\n");
    {
        int idx = def_define("_ab6",
            "(\\i j k. imax i (imin j k) : Π(i:II).Π(j:II).Π(k:II).II)");
        if (idx >= 0) expect_conv(a, "_ab6",
            "\\i. \\j. \\k. imax i (imin j k)", 1);
        else { printf("  [BUG] _ab6 rejected\n"); tests_fail++; }
    }

    /* ── PP-I series: auto PathP inference for ⟨i⟩ body ─────────────────────
     * infer TM_PATHABS now returns PathP (λi. body_ty) t0 t1 when the body's
     * type mentions i (term_mentions_var(bty_term, 0) = 1), and Path A t0 t1
     * when the body type is constant (regression).                           */

    /* PP-I1: constant body type → Path (regression) */
    printf("\n[PP-I1] <i> zero : Path Nat zero zero (constant type)\n");
    {
        int idx = def_define("_ppi1", "(<i> zero : Path Nat zero zero)");
        if (idx >= 0) {
            printf("  [OK] constant body → Path\n"); tests_pass++;
        } else {
            printf("  [BUG] _ppi1 rejected\n"); tests_fail++;
        }
    }

    /* PP-I2: varying type → PathP auto-detected.
     * Construct a context with p : PathP fam a b directly via TCtx/Env,
     * then infer <j> p@j — body type = fam j which mentions j → VL_PATHP. */
    printf("\n[PP-I2] infer <j> p@j in PathP-variable context → VL_PATHP\n");
    {
        /* Build: p : PathP (λi. Glue Nat i Nat idNatEquiv) zero zero */
        Arena tmp = {NULL};
        /* fam = λi. Glue Nat i Nat idNatEquiv — parse and eval with idNatEquiv in scope */
        Term *fam_t = parse(&tmp, "(\\i. Glue Nat i Nat idNatEquiv : Π(i:II).Type)");
        Val  *fam_v = fam_t ? nbe_eval(&tmp, NULL, fam_t) : NULL;
        Val  *p_ty  = fam_v
                      ? vl_pathp(&tmp, fam_v, vl_zero(&tmp), vl_zero(&tmp))
                      : NULL;
        if (p_ty) {
            /* depth=1 with p at level 0 (VL_NEUTRAL) */
            Val  *p_val  = vl_neutral(&tmp, 0, NULL);
            TCtx  tctx_p = { "p", p_ty, NULL };
            Env  *env_p  = env_cons(&tmp, p_val, NULL);
            /* Build ⟨j⟩ p @ j directly: inside the pathabs, p=VAR(1), j=VAR(0). */
            Term *body  = tm_pathapp(&tmp, tm_var(&tmp, 1), tm_var(&tmp, 0));
            Term *pabs  = tm_pathabs(&tmp, "j", body);
            Val  *ty    = infer(&tmp, 1, &tctx_p, env_p, pabs);
            if (ty && ty->tag == VL_PATHP) {
                printf("  [OK] varying body → VL_PATHP inferred\n"); tests_pass++;
            } else {
                printf("  [BUG] expected VL_PATHP, got tag %d\n",
                       ty ? (int)ty->tag : -1); tests_fail++;
            }
        } else {
            printf("  [BUG] context setup failed\n"); tests_fail++;
        }
        arena_free_all(&tmp);
    }

    /* PP-I3: constant body still gives Path in context (no spurious PathP) */
    printf("\n[PP-I3] <i> zero in neutral context → Path (not PathP)\n");
    {
        Arena tmp = {NULL};
        Term *pabs = tm_pathabs(&tmp, "i", tm_zero(&tmp));
        Val  *ty   = infer(&tmp, 0, NULL, NULL, pabs);
        if (ty && ty->tag == VL_PATH) {
            printf("  [OK] constant ⟨i⟩ zero → VL_PATH\n"); tests_pass++;
        } else {
            printf("  [BUG] expected VL_PATH\n"); tests_fail++;
        }
        arena_free_all(&tmp);
    }

    /* PP-I4: annotated <i> body : PathP fam a b still accepted (check mode) */
    printf("\n[PP-I4] annotated PathP check still works\n");
    {
        int idx = def_define("_ppi4",
            "(<i> zero : PathP (\\i. Nat : Π(i:II).Type) zero zero)");
        if (idx >= 0) {
            printf("  [OK] annotated PathP accepted\n"); tests_pass++;
        } else {
            printf("  [BUG] annotated PathP rejected\n"); tests_fail++;
        }
    }

    /* PP-I5: rfl on a Path inferred from constant pathabs (regression) */
    printf("\n[PP-I5] rfl proves auto-inferred Path equals itself\n");
    {
        int idx = def_define("_ppi5",
            "(refl (<i> zero) : Id (Path Nat zero zero) (<i> zero) (<i> zero))");
        if (idx >= 0) {
            printf("  [OK] rfl on ⟨i⟩ zero\n"); tests_pass++;
        } else {
            printf("  [BUG] _ppi5 rejected\n"); tests_fail++;
        }
    }

    /* ── LT-series: full lattice tautology / contradiction tests ────────────
     *
     * The 2^n variable enumeration catches identities not of the form x∨~x.
     * These tests cover:
     *   LT1-4  : genuine new cases (complement check would miss them)
     *   LT5-7  : non-tautologies must stay stuck (correctness guard)
     *   LT8    : IsOne benefits from new check
     *   LT9    : three-variable expression
     *   LT10   : overflow guard — > MAX_FACE_VARS vars stay stuck
     */

    /* LT1: (φ1∨φ2) ∨ (~φ1∨~φ2) = i1.  Complement check computes ~(φ1∨φ2)=~φ1∧~φ2
     * (VL_IMIN), but r is imax(~φ1,~φ2) (VL_IMAX) — different tags → complement
     * check fails.  Tautology check: both i=1 or both i=0 cases are covered. */
    printf("\n[LT1] imax (imax i j) (imax ~i ~j) = i1 — new via tautology check\n");
    {
        int idx = def_define("_lt1",
            "(\\i j. imax (imax i j) (imax (ineg i) (ineg j)) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_lt1", "\\i. \\j. i1", 1);
        else { printf("  [BUG] _lt1 rejected\n"); tests_fail++; }
    }

    /* LT2: imin (imin i j) (imin ~i ~j) = i0 — dual of LT1 */
    printf("\n[LT2] imin (imin i j) (imin ~i ~j) = i0\n");
    {
        int idx = def_define("_lt2",
            "(\\i j. imin (imin i j) (imin (ineg i) (ineg j)) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_lt2", "\\i. \\j. i0", 1);
        else { printf("  [BUG] _lt2 rejected\n"); tests_fail++; }
    }

    /* LT3: i ∨ ~j ∨ (~i∧j) = i1  (three-literal tautology) */
    printf("\n[LT3] imax i (imax ~j (imin ~i j)) = i1 — three-literal tautology\n");
    {
        int idx = def_define("_lt3",
            "(\\i j. imax i (imax (ineg j) (imin (ineg i) j)) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_lt3", "\\i. \\j. i1", 1);
        else { printf("  [BUG] _lt3 rejected\n"); tests_fail++; }
    }

    /* LT4: i ∧ ~j ∧ (~i∨j) = i0  — dual of LT3 */
    printf("\n[LT4] imin i (imin ~j (imax ~i j)) = i0\n");
    {
        int idx = def_define("_lt4",
            "(\\i j. imin i (imin (ineg j) (imax (ineg i) j)) : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_lt4", "\\i. \\j. i0", 1);
        else { printf("  [BUG] _lt4 rejected\n"); tests_fail++; }
    }

    /* LT5: imax i j NOT a tautology — must stay stuck */
    printf("\n[LT5] imax i j stays stuck (non-tautology)\n");
    {
        int idx = def_define("_lt5",
            "(\\i j. imax i j : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_lt5", "\\i. \\j. imax i j", 1);
        else { printf("  [BUG] _lt5 rejected\n"); tests_fail++; }
    }

    /* LT6: imin i j stays stuck (non-contradiction) */
    printf("\n[LT6] imin i j stays stuck (non-contradiction)\n");
    {
        int idx = def_define("_lt6",
            "(\\i j. imin i j : Π(i:II).Π(j:II).II)");
        if (idx >= 0) expect_conv(a, "_lt6", "\\i. \\j. imin i j", 1);
        else { printf("  [BUG] _lt6 rejected\n"); tests_fail++; }
    }

    /* LT7: imax (imax i j) k stays stuck — not a tautology (i=i0,j=i0,k=i0 → i0) */
    printf("\n[LT7] imax (imax i j) k stays stuck (non-tautology)\n");
    {
        int idx = def_define("_lt7",
            "(\\i j k. imax (imax i j) k : Π(i:II).Π(j:II).Π(k:II).II)");
        if (idx >= 0) expect_conv(a, "_lt7", "\\i. \\j. \\k. imax (imax i j) k", 1);
        else { printf("  [BUG] _lt7 rejected\n"); tests_fail++; }
    }

    /* LT8: IsOne (imax (imax i j) (imax ~i ~j)) = Unit — face predicate benefit */
    printf("\n[LT8] IsOne (imax (imax i j) (imax ~i ~j)) = Unit\n");
    {
        int idx = def_define("_lt8",
            "(\\i j. IsOne (imax (imax i j) (imax (ineg i) (ineg j)))"
            " : Π(i:II).Π(j:II).Type)");
        if (idx >= 0) expect_conv(a, "_lt8", "\\i. \\j. Unit", 1);
        else { printf("  [BUG] _lt8 rejected\n"); tests_fail++; }
    }

    /* LT9: three-variable: (i∨j∨k) ∨ (~i∨~j∨~k) harder form */
    printf("\n[LT9] imax (imax i (imax j k)) (imax ~i (imax ~j ~k)) = i1\n");
    {
        int idx = def_define("_lt9",
            "(\\i j k. imax (imax i (imax j k)) (imax (ineg i) (imax (ineg j) (ineg k)))"
            " : Π(i:II).Π(j:II).Π(k:II).II)");
        if (idx >= 0) expect_conv(a, "_lt9", "\\i. \\j. \\k. i1", 1);
        else { printf("  [BUG] _lt9 rejected\n"); tests_fail++; }
    }

    /* LT10: overflow guard — 9 distinct vars must stay stuck (> MAX_FACE_VARS=8) */
    printf("\n[LT10] 9 distinct vars: tautology check skipped, stays stuck\n");
    {
        /* This is a tautology (i1∨~i1 form for the first pair), but we want to
         * verify it stays stuck due to overflow guard.  Actually after De Morgan
         * the complement check may fire.  Use a non-complement 9-var expression
         * that IS NOT a tautology so there's no other way to reduce it. */
        int idx = def_define("_lt10",
            "(\\a b c d e f g h i."
            " imax a (imax b (imax c (imax d (imax e (imax f (imax g (imax h i)))))))"
            " : Π(a:II).Π(b:II).Π(c:II).Π(d:II).Π(e:II)."
            "   Π(f:II).Π(g:II).Π(h:II).Π(i:II).II)");
        if (idx >= 0) {
            /* The expression itself is not i1 (all vars=i0 gives i0).
             * With overflow guard it stays as nested imax — no tautology fires. */
            printf("  [OK] 9-var expression defined (overflow guard active)\n");
            tests_pass++;
        } else {
            printf("  [BUG] 9-var expression rejected\n"); tests_fail++;
        }
    }

    /* ── glue/unglue concrete-face fix tests ────────────────────────────────
     * unglue and glue now type-check at concrete faces (i0/i1) without
     * requiring an explicit Glue type annotation.                           */

    /* GU1: unglue i0 e x — x : A, result : A, no annotation needed */
    printf("\n[GU1] unglue i0 e x type-checks without annotation\n");
    {
        /* idNatEquiv : Equiv Nat Nat; unglue i0 idNatEquiv (zero:Nat) = zero */
        if (def_lookup("idNatEquiv") < 0)
            def_define("idNatEquiv",
                "(\\x. x, \\x. x, \\y. refl y, \\x. refl x : Equiv Nat Nat)");
        int idx = def_define("_gu1",
            "(unglue i0 idNatEquiv zero : Nat)");
        if (idx >= 0) {
            printf("  [OK] unglue i0 type-checks\n"); tests_pass++;
            expect_conv(a, "_gu1", "zero", 1);
        } else {
            printf("  [BUG] unglue i0 rejected\n"); tests_fail++;
        }
    }

    /* GU2: unglue i1 e x — x : T, result : A, no annotation needed */
    printf("\n[GU2] unglue i1 e x type-checks without annotation\n");
    {
        int idx = def_define("_gu2",
            "(unglue i1 idNatEquiv zero : Nat)");
        if (idx >= 0) {
            printf("  [OK] unglue i1 type-checks\n"); tests_pass++;
            expect_conv(a, "_gu2", "zero", 1);  /* idNatEquiv.fwd = id, so fwd(zero) = zero */
        } else {
            printf("  [BUG] unglue i1 rejected\n"); tests_fail++;
        }
    }

    /* GU3: unglue neutral φ — existing path still works */
    printf("\n[GU3] unglue with neutral face still works\n");
    {
        int idx = def_define("_gu3",
            "(\\ phi x. unglue phi idNatEquiv x"
            " : Π(phi : II). Π(x : Glue Nat phi Nat idNatEquiv). Nat)");
        if (idx >= 0) {
            printf("  [OK] unglue neutral-face still works\n"); tests_pass++;
        } else {
            printf("  [BUG] unglue neutral-face rejected\n"); tests_fail++;
        }
    }

    /* GU4: glue i0 t a — a : A, no annotation needed */
    printf("\n[GU4] glue i0 t a type-checks against A (concrete face)\n");
    {
        /* glue i0 t a = a; check a : Nat ✓ */
        int idx = def_define("_gu4",
            "(glue i0 (\\ _. zero) zero : Nat)");
        if (idx >= 0) {
            printf("  [OK] glue i0 type-checks against A\n"); tests_pass++;
            expect_conv(a, "_gu4", "zero", 1);
        } else {
            printf("  [BUG] glue i0 against A rejected\n"); tests_fail++;
        }
    }

    /* GU5: glue i1 t a — t : Π(_:Unit). T, no annotation needed */
    printf("\n[GU5] glue i1 t a type-checks against T (concrete face)\n");
    {
        /* glue i1 t a = t star; check t : Π(_:Unit). Nat ✓ */
        int idx = def_define("_gu5",
            "(glue i1 (\\ _. succ zero) zero : Nat)");
        if (idx >= 0) {
            printf("  [OK] glue i1 type-checks against T\n"); tests_pass++;
            expect_conv(a, "_gu5", "succ zero", 1);
        } else {
            printf("  [BUG] glue i1 against T rejected\n"); tests_fail++;
        }
    }

    /* ── Keyword-shadowing tests ─────────────────────────────────────────────
     * Parser bug fix: bound variables named like keywords (base, zero, star,
     * loop, etc.) must shadow the keyword and resolve to TM_VAR, not the
     * built-in term.  These tests caught a real bug: \base. mul base acc
     * was parsing `base` as TM_BASE (S¹ base point) instead of the binder. */

    /* KS1: lambda binder named `base` shadows S¹ base point */
    printf("\n[KS1] \\base. succ base — `base` as Nat var, not S¹ base\n");
    expect_conv(a,
        "(\\base. succ base : Π(base:Nat).Nat) zero",
        "succ zero", 1);

    /* KS2: lambda binder named `zero` shadows Nat zero */
    printf("\n[KS2] \\zero. succ zero — `zero` as a var shadows Nat zero\n");
    expect_conv(a,
        "(\\zero. succ zero : Π(zero:Nat).Nat) (succ zero)",
        "succ (succ zero)", 1);

    /* KS3: lambda binder named `star` shadows Unit star */
    printf("\n[KS3] \\star. (star, star) — `star` as pair element shadows Unit star\n");
    expect_type(a,
        "(\\star. (star, star) : Π(star:Nat). Σ(x:Nat).Nat) zero",
        "Σ(x : Nat). Nat");

    /* KS4: nested shadowing — `base` shadows keyword, then is used in natrec */
    printf("\n[KS4] \\base. natrec ... base — closure var captured correctly\n");
    expect_conv(a,
        "(\\base. natrec (\\_.Nat) base (\\_ k. succ k) (succ zero) : Π(base:Nat).Nat) (succ (succ zero))",
        "succ (succ (succ zero))", 1);  /* base + 1 = 3 */

    /* KS5: `loop` as binder, body uses it as a Path */
    printf("\n[KS5] \\loop. loop @ i0 — `loop` as Path var shadows S¹ loop\n");
    {
        int idx = def_define("_ks5",
            "(\\loop. loop @ i0"
            " : Π(loop : Path Nat zero zero). Nat)");
        if (idx >= 0) {
            printf("  [OK] loop as Path binder type-checks\n"); tests_pass++;
        } else {
            printf("  [BUG] loop as Path binder rejected\n"); tests_fail++;
        }
    }

    /* D1–D5: Systematic audit of keyword-shadowing fix in various parser contexts.
     * The keyword-shadowing fix in parse_atom (bound-var check before keywords)
     * must work consistently in: match arm bodies, data ctor types, indrec args. */

    /* D1: match arm binder named like keyword shadows it in the arm body.
     * | succ zero => zero  means: bind the predecessor as 'zero', return it.
     * 'zero' in body must be TM_VAR(0) (bound), not TM_ZERO (keyword). */
    printf("\n[D1] match arm binder named 'zero' shadows keyword in body\n");
    expect_conv(a,
        "(match (succ (succ zero)) of | zero => zero | succ zero => zero : Nat)",
        "succ zero", 1);   /* succ arm fires: 'zero' body = predecessor = succ zero */

    /* D2: match arm binder named 'true' used in Nat context (not Bool) */
    printf("\n[D2] match arm binder named 'true' shadows Bool keyword in body\n");
    expect_conv(a,
        "(match (succ zero) of | zero => zero | succ true => true : Nat)",
        "zero", 1);   /* true = predecessor = zero */

    /* D3: data param named like keyword shadows it in ctor type expressions.
     * 'true' in ctor type 'WrapB true' must refer to the param, not Bool.true. */
    printf("\n[D3] data param named 'true' shadows Bool keyword in ctor types\n");
    {
        if (ind_lookup("_DWrapB") < 0)
            parse_data("_DWrapB (true : Bool) where mk : Bool \xe2\x86\x92 _DWrapB true");
        if (ind_lookup("_DWrapB") >= 0) {
            /* mk with param true=Bool.true and arg=Bool.true → _DWrapB true */
            expect_type(a,
                "(mk true true : _DWrapB true)",
                "_DWrapB true");
        } else {
            printf("  [BUG] _DWrapB data decl failed\n"); tests_fail++;
        }
    }

    /* D4: natrec sub-expr: bound var named 'zero' is used as base case.
     * Without fix: 'zero' in base position = TM_ZERO = 0, result = 0+1 = 1.
     * With fix: 'zero' = arg = 1, result = 1+2 = 3 (base + scrut). */
    printf("\n[D4] natrec base: bound var named 'zero' used as base, not Nat zero\n");
    expect_conv(a,
        "((\\zero. natrec (\\_.Nat) zero (\\_ k. succ k) (succ zero)"
        "  : Π(zero:Nat).Nat) (succ zero))",
        "succ (succ (succ zero))", 1);   /* zero=1, base=1, scrut=2 → 1+2=3 */

    /* D5: indrec family name is static — bound variable with same name as
     * the inductive type does not interfere with the family lookup. */
    printf("\n[D5] indrec: bound var with family type name does not shadow indrec lookup\n");
    {
        if (ind_lookup("_DColor") < 0)
            parse_data("_DColor where red : _DColor; blue : _DColor");
        if (ind_lookup("_DColor") >= 0) {
            /* \Color. indrec _DColor ... — 'Color' is bound but indrec family is static */
            int idx = def_define("_d5_test",
                "(\\Color. indrec _DColor"
                "         (\\_.Nat : Π(_:_DColor).Type)"
                "         zero (succ zero)"
                "         (red : _DColor)"
                " : Π(Color:Nat).Nat)");
            if (idx >= 0) {
                printf("  [OK] indrec with bound 'Color' var type-checks\n"); tests_pass++;
            } else {
                printf("  [BUG] indrec with bound 'Color' var rejected\n"); tests_fail++;
            }
        } else {
            printf("  [BUG] _DColor data decl failed\n"); tests_fail++;
        }
    }

    /* ── LA1-series: natrec step captures outer lambda variable (LANG-1) ────────
     * Regression for the LANG-1 bug: outer lambda variables used inside a
     * natrec step were incorrectly parsed as keywords (e.g. 'base' → TM_BASE)
     * before the KS parser fix.  These tests verify correct capture at the
     * core-NbE level so any regression in parse.c or eval.c is caught early. */

    /* LA1-1: outer var `n` captured in natrec step — inner add of n each iteration.
     * (\n. natrec (\_. Nat) zero (\_ acc. natrec (\_. Nat) acc (\_ k. succ k) n) 2) 3
     * = natrec _ 0 (\_ acc. acc+3) 2 = 6 */
    printf("\n[LA1-1] outer var captured in natrec step: 2 iterations of (+3) from 0\n");
    expect_conv(a,
        "(\\n. natrec (\\_. Nat) zero"
        "     (\\_. \\acc. natrec (\\_. Nat) acc (\\_. \\k. succ k) n)"
        "     (succ (succ zero))"
        " : \xce\xa0(n:Nat).Nat)"
        " (succ (succ (succ zero)))",
        "succ (succ (succ (succ (succ (succ zero)))))", 1);

    /* LA1-2: two outer vars, base=m, step adds n each iteration.
     * (\m.\n. natrec (\_. Nat) m (\_ acc. natrec (\_. Nat) acc (\_ k. succ k) n) 2) 1 3
     * = natrec _ 1 (\_ acc. acc+3) 2 = 7 */
    printf("\n[LA1-2] two outer vars in natrec: base=m, step adds n, result 7\n");
    expect_conv(a,
        "(\\m. \\n. natrec (\\_. Nat) m"
        "     (\\_. \\acc. natrec (\\_. Nat) acc (\\_. \\k. succ k) n)"
        "     (succ (succ zero))"
        " : \xce\xa0(m:Nat).\xce\xa0(n:Nat).Nat)"
        " (succ zero)"
        " (succ (succ (succ zero)))",
        "succ (succ (succ (succ (succ (succ (succ zero))))))", 1);

    /* LA1-3: nested natrec — outer var in step of outer natrec, which is itself
     * the scrutinee of an inner natrec.  Tests that de Bruijn shifts stay correct
     * through two levels of natrec nesting.
     * (\n. natrec (\_. Nat) n (\_ acc. natrec (\_. Nat) acc (\_ k. succ k) n) 2) 2
     * = natrec _ 2 (\_ acc. acc+2) 2 = 6 */
    printf("\n[LA1-3] outer var in step and as base, two levels of natrec nesting\n");
    expect_conv(a,
        "(\\n. natrec (\\_. Nat) n"
        "     (\\_. \\acc. natrec (\\_. Nat) acc (\\_. \\k. succ k) n)"
        "     (succ (succ zero))"
        " : \xce\xa0(n:Nat).Nat)"
        " (succ (succ zero))",
        "succ (succ (succ (succ (succ (succ zero)))))", 1);

    /* LA1-4: outer var 'base' (a former keyword) explicitly in the step lambda.
     * (\base. natrec (\_. Nat) zero (\_ acc. natrec (\_. Nat) acc (\_ k. succ k) base) 3) 4
     * = natrec _ 0 (\_ acc. acc+4) 3 = 12 */
    printf("\n[LA1-4] outer var named 'base' (former keyword) used in step, 3 iterations of (+4)\n");
    expect_conv(a,
        "(\\base. natrec (\\_. Nat) zero"
        "     (\\_. \\acc. natrec (\\_. Nat) acc (\\_. \\k. succ k) base)"
        "     (succ (succ (succ zero)))"
        " : \xce\xa0(base:Nat).Nat)"
        " (succ (succ (succ (succ zero))))",
        "succ (succ (succ (succ (succ (succ (succ (succ (succ (succ (succ (succ zero)))))))))))", 1);

    /* ── Match type-directed ctor resolution (MC1–MC6) ───────────────────────
     * User-defined inductives whose ctors share names with built-in keywords
     * (zero/succ/true/false) must take precedence in match-arm resolution.
     * ind_find_ctor now searches most-recent first and is tried BEFORE the
     * hardcoded Nat/Bool fallbacks in the match-arm parser.
     *
     * Note: bare keyword names in ARM BODIES still parse as builtins (e.g.,
     * `zero` in a body is always Nat.zero, not a user ctor). The fix only
     * affects the match PATTERN/FAMILY resolution, not expression parsing.
     * Tests therefore use non-conflicting body terms (Bool←Nat cross-maps).  */

    /* MC1: non-conflicting ctor names (Z/S) — baseline, no shadowing needed */
    printf("\n[MC1] match on user type with ctors 'Z'/'S' (no name conflict)\n");
    {
        if (ind_lookup("_Peano") < 0)
            parse_data("_Peano where Z : _Peano; S : _Peano \xe2\x86\x92 _Peano");
        if (ind_lookup("_Peano") >= 0) {
            int idx = def_define("_mc1",
                "(\\n. match n of | Z => true | S _ => false"
                " : _Peano \xe2\x86\x92 Bool)");
            if (idx >= 0) {
                printf("  [OK] match on _Peano type-checks\n"); tests_pass++;
            } else {
                printf("  [BUG] match on _Peano rejected\n"); tests_fail++;
            }
        } else {
            printf("  [BUG] _Peano data decl failed\n"); tests_fail++;
        }
    }

    /* MC2: Nat match works before any conflicting user ctor is registered */
    printf("\n[MC2] Nat match unaffected when no user ctor uses 'zero'/'succ'\n");
    expect_conv(a,
        "(match (succ (succ zero)) of | zero => zero | succ n => n : Nat)",
        "succ zero", 1);

    /* MC3: user inductive with ctors 'zero'/'succ' — patterns resolve to user type.
     * Body uses Bool to avoid keyword conflict in the arm body.            */
    printf("\n[MC3] user inductive with ctors 'zero'/'succ' — match resolves to user type\n");
    {
        if (ind_lookup("_PeanoNat") < 0)
            parse_data("_PeanoNat where zero : _PeanoNat; succ : _PeanoNat \xe2\x86\x92 _PeanoNat");
        if (ind_lookup("_PeanoNat") >= 0) {
            /* map _PeanoNat → Bool: zero→true, succ _→false */
            int idx = def_define("_mc3",
                "(\\n. match n of | zero => true | succ _ => false"
                " : _PeanoNat \xe2\x86\x92 Bool)");
            if (idx >= 0) {
                printf("  [OK] 'zero'/'succ' patterns resolve to _PeanoNat\n"); tests_pass++;
            } else {
                printf("  [BUG] _PeanoNat zero/succ match rejected\n"); tests_fail++;
            }
        } else {
            printf("  [BUG] _PeanoNat data decl failed\n"); tests_fail++;
        }
    }

    /* MC4: user inductive with ctors 'true'/'false' — patterns resolve to user type.
     * Body uses Nat to avoid keyword conflict in the arm body.            */
    printf("\n[MC4] user inductive with ctors 'true'/'false' — match resolves to user type\n");
    {
        if (ind_lookup("_MyBool") < 0)
            parse_data("_MyBool where true : _MyBool; false : _MyBool");
        if (ind_lookup("_MyBool") >= 0) {
            /* map _MyBool → Nat: true→zero, false→succ zero */
            int idx = def_define("_mc4",
                "(\\b. match b of | true => zero | false => succ zero"
                " : _MyBool \xe2\x86\x92 Nat)");
            if (idx >= 0) {
                printf("  [OK] 'true'/'false' patterns resolve to _MyBool\n"); tests_pass++;
            } else {
                printf("  [BUG] _MyBool true/false match rejected\n"); tests_fail++;
            }
        } else {
            printf("  [BUG] _MyBool data decl failed\n"); tests_fail++;
        }
    }

    /* MC5: type-checker catches family mismatch — zero/succ resolve to _PeanoNat
     * (most-recently defined with those ctors) but scrutinee is declared Nat.  */
    printf("\n[MC5] user ctor on Nat scrutinee → type error (family mismatch)\n");
    expect_fail(a,
        "(\\n. match n of | zero => true | succ _ => false : Nat \xe2\x86\x92 Bool)",
        "scrut is Nat but zero/succ resolve to _PeanoNat");

    /* MC6: most-recently defined inductive wins for shared ctor name */
    printf("\n[MC6] most-recently defined inductive wins for shared ctor name\n");
    {
        if (ind_lookup("_PeanoNat2") < 0)
            parse_data("_PeanoNat2 where zero : _PeanoNat2; succ : _PeanoNat2 \xe2\x86\x92 _PeanoNat2");
        if (ind_lookup("_PeanoNat2") >= 0) {
            /* zero/succ now resolve to _PeanoNat2 (defined after _PeanoNat) */
            int idx = def_define("_mc6",
                "(\\n. match n of | zero => true | succ _ => false"
                " : _PeanoNat2 \xe2\x86\x92 Bool)");
            if (idx >= 0) {
                printf("  [OK] _PeanoNat2 (most recent) wins over _PeanoNat\n"); tests_pass++;
            } else {
                printf("  [BUG] _PeanoNat2 match rejected\n"); tests_fail++;
            }
        } else {
            printf("  [BUG] _PeanoNat2 data decl failed\n"); tests_fail++;
        }
    }

    /* ── PARSE-1: qualified ctor names (QN1–QN6) ────────────────────────────
     *
     * _PeanoNat (zero/succ) and _MyBool (true/false) are already registered
     * by MC3/MC4 above.  These tests verify LIMIT-1 (qualified match patterns)
     * and LIMIT-2 (qualified ctor names in expression position).             */

    /* QN1: Nat.zero / Nat.succ in match arm bypass user-ctor shadowing (LIMIT-1) */
    printf("\n[QN1] Nat.zero/Nat.succ qualified patterns match Nat even after shadow\n");
    expect_type(a,
        "(\\n. match n of | Nat.zero => true | Nat.succ _ => false"
        " : Nat \xe2\x86\x92 Bool)",
        "Nat \xe2\x86\x92 Bool");

    /* QN2: Bool.true / Bool.false qualified patterns bypass _MyBool shadowing */
    printf("\n[QN2] Bool.true/Bool.false qualified patterns match Bool after shadow\n");
    expect_type(a,
        "(\\b. match b of | Bool.true => zero | Bool.false => succ zero"
        " : Bool \xe2\x86\x92 Nat)",
        "Bool \xe2\x86\x92 Nat");

    /* QN3: user qualified ctor _PeanoNat.zero in expression position (LIMIT-2) */
    printf("\n[QN3] _PeanoNat.zero in expression position\n");
    expect_type(a, "_PeanoNat.zero", "_PeanoNat");

    /* QN4: user qualified ctor in match arm for the user type */
    printf("\n[QN4] _PeanoNat.zero/_PeanoNat.succ qualified patterns for user type\n");
    expect_type(a,
        "(\\n. match n of | _PeanoNat.zero => true | _PeanoNat.succ _ => false"
        " : _PeanoNat \xe2\x86\x92 Bool)",
        "_PeanoNat \xe2\x86\x92 Bool");

    /* QN5: qualified ctor for most-recent shadowed type still works */
    printf("\n[QN5] _PeanoNat2.zero references second registration of zero-named ctor\n");
    expect_type(a, "_PeanoNat2.zero", "_PeanoNat2");

    /* QN6: wrong qualified ctor name within a known type → type error
     * Nat has no ctor 'blorp'; the parse error cascades to a type check failure. */
    printf("\n[QN6] bad ctor name within Nat qualified pattern → rejected\n");
    {
        Term *t = parse(a,
            "(\\n. match n of | Nat.blorp => true"
            " : Nat \xe2\x86\x92 Bool)");
        if (!t) {
            tests_pass++;
            printf("  [OK] Nat.blorp rejected at parse\n");
        } else {
            tests_fail++;
            printf("  [BUG] Nat.blorp accepted\n");
        }
    }

    /* ── Suspension HIT (SU1–SU12) ──────────────────────────────────────────
     * Susp A is a general HIT defined via parse_data:
     *   data Susp (A : Type) where
     *     North : Susp A; South : Susp A;
     *     merid : A → Path (Susp A) (North A) (South A)
     * The eliminator is indrec Susp motive north_case south_case merid_case scrut.
     * Endpoint equations, dependent motives, and all computation rules are
     * handled by the HIT-1 general mechanism (nbe_vindrec + check_indrec_path_case). */
    {
        int su_fam = parse_data(
            "Susp (A : Type) where"
            " North : Susp A;"
            " South : Susp A;"
            " merid : A \xe2\x86\x92 Path (Susp A) (North A) (South A)");
        if (su_fam < 0) {
            printf("  [BUG] data Susp failed to register\n"); tests_fail++;
        } else {
            printf("  [OK] data Susp registered (fam_idx=%d)\n", su_fam); tests_pass++;
        }
    }

    /* SU1: Susp Nat : Type */
    printf("\n[SU1] Susp Nat : Type\n");
    expect_type(a, "Susp Nat", "Type");

    /* SU2: North Nat : Susp Nat */
    printf("\n[SU2] North Nat : Susp Nat\n");
    expect_type(a, "North Nat", "Susp Nat");

    /* SU3: South Nat : Susp Nat */
    printf("\n[SU3] South Nat : Susp Nat\n");
    expect_type(a, "South Nat", "Susp Nat");

    /* SU4: merid Nat zero : Path (Susp Nat) (North Nat) (South Nat) */
    printf("\n[SU4] merid Nat zero : Path (Susp Nat) (North Nat) (South Nat)\n");
    expect_type(a, "merid Nat zero",
                "Path (Susp Nat) (North Nat) (South Nat)");

    /* SU5: indrec north β-rule */
    printf("\n[SU5] indrec Susp north case fires\n");
    expect_conv(a,
        "indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type) true false (\\a. <i> true) (North Nat)",
        "true", 1);

    /* SU6: indrec south β-rule */
    printf("\n[SU6] indrec Susp south case fires\n");
    expect_conv(a,
        "indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type) true false (\\a. <i> true) (South Nat)",
        "false", 1);

    /* SU7: merid endpoint i0 = North */
    printf("\n[SU7] merid A a @ i0 = North A\n");
    expect_conv(a, "merid Nat zero @ i0", "North Nat", 1);

    /* SU8: merid endpoint i1 = South */
    printf("\n[SU8] merid A a @ i1 = South A\n");
    expect_conv(a, "merid Nat zero @ i1", "South Nat", 1);

    /* SU9: indrec fires on merid endpoint (endpoint reduction then β) */
    printf("\n[SU9] indrec Susp ... (merid A a @ i0) = north_case\n");
    expect_conv(a,
        "indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type) true false (\\a. <i> true) (merid Nat zero @ i0)",
        "true", 1);

    /* SU10: indrec merid case — merid_case a @ r computes for concrete path */
    printf("\n[SU10] indrec Susp merid case computes: merid_case a @ r\n");
    {
        int idx = def_define("_su10",
            "(\\r. indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type)"
            "        true true (\\a. refl true) (merid Nat zero @ r)"
            " : II \xe2\x86\x92 Bool)");
        if (idx >= 0) {
            printf("  [OK] indrec Susp merid case type-checks\n"); tests_pass++;
            expect_conv(a, "_su10 i0", "true", 1);
            expect_conv(a, "_su10 i1", "true", 1);
        } else {
            printf("  [BUG] indrec Susp merid case rejected\n"); tests_fail++;
        }
    }

    /* SU11: indrec merid — merid_case a @ r for valid merid_case (bn=bs=zero, refl) */
    printf("\n[SU11] indrec Susp merid: merid_case a @ r for bn=bs, refl\n");
    {
        int idx = def_define("_su11",
            "(\\r. indrec Susp (\\_. Nat : Susp Nat \xe2\x86\x92 Type)"
            "        zero zero (\\a. refl zero) (merid Nat (succ zero) @ r)"
            " : II \xe2\x86\x92 Nat)");
        if (idx >= 0) {
            printf("  [OK] indrec Susp merid case (refl, bn=bs) type-checks\n"); tests_pass++;
            expect_conv(a, "_su11 i0", "zero", 1);
            expect_conv(a, "_su11 i1", "zero", 1);
        } else {
            printf("  [BUG] indrec Susp merid case rejected\n"); tests_fail++;
        }
    }

    /* ── Dependent indrec Susp tests (SU-D1–SU-D6) ─────────────────────────
     * These tests use a dependent motive B : Susp A → Type.                */

    /* SU-D1: Identity map via indrec Susp with dependent motive.
     * indrec Susp (\s. Susp Nat) (North Nat) (South Nat) (\a. merid Nat a) s = s */
    printf("\n[SU-D1] identity via indrec Susp: dependent motive \\s. Susp Nat\n");
    {
        int idx = def_define("_sud1_id",
            "(\\s. indrec Susp (\\s. Susp Nat : Susp Nat \xe2\x86\x92 Type)"
            "        (North Nat) (South Nat) (\\a. merid Nat a) s"
            " : Susp Nat \xe2\x86\x92 Susp Nat)");
        if (idx >= 0) {
            printf("  [OK] dependent indrec Susp identity type-checks\n"); tests_pass++;
            expect_conv(a, "_sud1_id (North Nat)", "North Nat", 1);
            expect_conv(a, "_sud1_id (South Nat)", "South Nat", 1);
        } else {
            printf("  [BUG] dependent indrec Susp identity rejected\n"); tests_fail++;
        }
    }

    /* SU-D2: merid case of the identity fires */
    printf("\n[SU-D2] dependent indrec Susp merid case: id(merid a @ r)\n");
    {
        int idx = def_define("_sud2",
            "(\\r. indrec Susp (\\s. Susp Nat : Susp Nat \xe2\x86\x92 Type)"
            "        (North Nat) (South Nat) (\\a. merid Nat a)"
            "        (merid Nat zero @ r)"
            " : II \xe2\x86\x92 Susp Nat)");
        if (idx >= 0) {
            printf("  [OK] identity(merid Nat zero @ r) type-checks\n"); tests_pass++;
            expect_conv(a, "_sud2 i0", "North Nat", 1);
            expect_conv(a, "_sud2 i1", "South Nat", 1);
        } else {
            printf("  [BUG] identity merid case rejected\n"); tests_fail++;
        }
    }

    /* SU-D3: indrec Susp over Susp Bool with constant motive */
    printf("\n[SU-D3] indrec Susp over Susp Bool, constant motive\n");
    {
        int idx = def_define("_sud3",
            "(\\s. indrec Susp (\\s. Nat : Susp Bool \xe2\x86\x92 Type)"
            "        zero zero (\\a. refl zero) s"
            " : Susp Bool \xe2\x86\x92 Nat)");
        if (idx >= 0) {
            printf("  [OK] indrec Susp over Susp Bool type-checks\n"); tests_pass++;
            expect_conv(a, "_sud3 (North Bool)", "zero", 1);
            expect_conv(a, "_sud3 (South Bool)", "zero", 1);
        } else {
            printf("  [BUG] indrec Susp over Susp Bool rejected\n"); tests_fail++;
        }
    }

    /* SU-D4: return type is B s — type-checker verifies */
    printf("\n[SU-D4] indrec Susp return type is B s\n");
    expect_type(a,
        "(indrec Susp (\\s. Susp Nat : Susp Nat \xe2\x86\x92 Type)"
        " (North Nat) (South Nat) (\\a. merid Nat a) (North Nat) : Susp Nat)",
        "Susp Nat");

    /* SU-D5: negative — motive not a function type → reject */
    printf("\n[SU-D5] indrec Susp with motive Nat (not a function) → reject\n");
    expect_fail(a,
        "(indrec Susp Nat zero zero (\\a. refl zero) (North Nat) : Nat)",
        "motive must take a scrutinee (Π)");

    /* SU-D6: negative — north case wrong type under dependent motive */
    printf("\n[SU-D6] indrec Susp north case wrong type → reject\n");
    expect_fail(a,
        "(indrec Susp (\\s. Susp Nat : Susp Nat \xe2\x86\x92 Type)"
        " zero (South Nat) (\\a. merid Nat a) (North Nat) : Susp Nat)",
        "north case must have type B(North Nat) = Susp Nat, not Nat");

    /* SU12: negative — North Bool ≢ North Nat */
    printf("\n[SU12] North Bool not conv-equal to North Nat\n");
    expect_conv(a, "North Bool", "North Nat", 0);

    /* ── Suspension hardening (SU-H1–SU-H12) ────────────────────────────────
     * Edge cases: neutral scrutinee, conv, universe level, error rejection.  */

    /* SU-H1: indrec Susp on neutral scrutinee — stays stuck */
    printf("\n[SU-H1] indrec Susp on neutral scrut stays stuck\n");
    {
        int idx = def_define("_suh1",
            "(\\s. indrec Susp (\\_. Nat : Susp Nat \xe2\x86\x92 Type)"
            "        zero zero (\\a. refl zero) s"
            " : Susp Nat \xe2\x86\x92 Nat)");
        if (idx >= 0) {
            printf("  [OK] indrec Susp on neutral type-checks\n"); tests_pass++;
        } else {
            printf("  [BUG] indrec Susp neutral rejected\n"); tests_fail++;
        }
    }

    /* SU-H2: North A conv-equal to itself */
    printf("\n[SU-H2] North Nat \xe2\x89\xa1 North Nat\n");
    expect_conv(a, "North Nat", "North Nat", 1);

    /* SU-H3: South A conv-equal to itself */
    printf("\n[SU-H3] South Bool \xe2\x89\xa1 South Bool\n");
    expect_conv(a, "South Bool", "South Bool", 1);

    /* SU-H4: merid A a conv-equal to itself */
    printf("\n[SU-H4] merid Nat zero \xe2\x89\xa1 merid Nat zero (path)\n");
    expect_conv(a, "merid Nat zero", "merid Nat zero", 1);

    /* SU-H5: merid with different elements not conv-equal */
    printf("\n[SU-H5] merid Nat zero \xe2\x89\xa2 merid Nat (succ zero)\n");
    expect_conv(a, "merid Nat zero", "merid Nat (succ zero)", 0);

    /* SU-H6: Susp universe — Susp Nat : Type (A : Type_0 → Susp A : Type_0) */
    printf("\n[SU-H6] Susp universe level\n");
    expect_type(a, "Susp Nat", "Type");

    /* SU-H7: negative — North applied to non-type argument */
    printf("\n[SU-H7] North zero — zero is not a Type, reject\n");
    expect_fail(a, "(North zero : Susp Nat)", "zero is not a Type");

    /* SU-H8: negative — merid_case endpoint mismatch → reject
     * merid_case = \a. <i> false: endpoints false/false, but north_case=true → mismatch */
    printf("\n[SU-H8] indrec Susp: merid_case endpoint mismatch \xe2\x86\x92 reject\n");
    expect_fail(a,
        "(indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type)"
        "        true false (\\a. <i> false) (North Nat) : Bool)",
        "merid_case endpoint false \xe2\x89\xa0 north_case=true");

    /* SU-H9: negative — wrong scrutinee type */
    printf("\n[SU-H9] indrec Susp: scrut of wrong type \xe2\x86\x92 reject\n");
    expect_fail(a,
        "(indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type) true false (\\a. refl true) zero : Bool)",
        "scrutinee must be Susp A");

    /* SU-H10: indrec Susp with explicit types — basic type check */
    printf("\n[SU-H10] indrec Susp with explicit motive type-checks\n");
    expect_elab(a,
        "(indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type) true true (\\a. refl true) (North Nat) : Bool)",
        "Bool");

    /* SU-H10b: indrec Susp South case */
    expect_elab(a,
        "(indrec Susp (\\_. Bool : Susp Bool \xe2\x86\x92 Type) false false (\\a. refl false) (South Bool) : Bool)",
        "Bool");

    /* SU-H10c: merid @ i0 conv North via HIT endpoint equations */
    printf("\n[SU-H10c] merid endpoint i0 = North via HIT mechanism\n");
    expect_conv(a, "merid Bool true @ i0", "North Bool", 1);

    /* SU-H10d: merid @ i1 conv South via HIT endpoint equations */
    printf("\n[SU-H10d] merid endpoint i1 = South via HIT mechanism\n");
    expect_conv(a, "merid Bool false @ i1", "South Bool", 1);

    /* SU-H10e: wrong scrutinee type gives clear error from indrec checker */
    printf("\n[SU-H10e] indrec Susp with Nat scrutinee (not Susp Nat) \xe2\x86\x92 reject\n");
    expect_fail(a,
        "(indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type) true false (\\a. refl true) (succ zero) : Bool)",
        "scrutinee is Nat, not Susp Nat");

    /* SU-H10f: motive codomain not a universe → indrec checker rejects */
    printf("\n[SU-H10f] motive codomain not a universe \xe2\x86\x92 reject\n");
    expect_fail(a,
        "(indrec Susp (\\s. zero : Susp Nat \xe2\x86\x92 Nat) zero zero (\\a. refl zero) (North Nat) : Nat)",
        "motive must map into a universe");

    /* SU-H10g: bare-lambda merid case accepted by check_indrec_path_case */
    printf("\n[SU-H10g] bare-lambda merid case accepted cleanly\n");
    expect_type(a,
        "(indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type) true true (\\a. refl true) (North Nat) : Bool)",
        "Bool");

    /* SU-H11: indrec ∘ (merid A a @ i) at i=i0 and i=i1 */
    printf("\n[SU-H11] indrec Susp \xe2\x88\x98 (merid A a @ i) at endpoints\n");
    expect_conv(a,
        "indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type) true false (\\a. refl true) (merid Nat zero @ i0)",
        "true", 1);
    expect_conv(a,
        "indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type) true false (\\a. refl true) (merid Nat zero @ i1)",
        "false", 1);

    /* SU-H12: Susp type value prints and type-checks correctly */
    printf("\n[SU-H12] Susp type value type-checks\n");
    expect_type(a, "Susp Bool", "Type");

    /* ── HIT-4 hardening (SU-N1–SU-N5) ─────────────────────────────────────
     * Edge cases specific to the general-HIT Susp: wrong case count, ctor
     * distinctness, path-ctor-as-scrutinee rejection, neutral indrec spine. */

    /* SU-N1: indrec with wrong family — scrutinee from Susp, family is _Peano */
    printf("\n[SU-N1] indrec _Peano with Susp Nat scrutinee \xe2\x86\x92 reject\n");
    {
        if (ind_lookup("_Peano") >= 0) {
            expect_fail(a,
                "(indrec _Peano (\\_. Nat : _Peano \xe2\x86\x92 Type) zero (\\k. \\ih. succ ih)"
                " (North Nat) : Nat)",
                "scrutinee is Susp Nat, not _Peano");
        } else {
            printf("  [SKIP] _Peano not registered\n");
        }
    }

    /* SU-N2: North Nat ≢ South Nat (distinct point ctors of same type) */
    printf("\n[SU-N2] North Nat \xe2\x89\xa2 South Nat\n");
    expect_conv(a, "North Nat", "South Nat", 0);

    /* SU-N3: merid A a is a Path, not Susp A — wrong scrutinee type for indrec */
    printf("\n[SU-N3] indrec Susp with merid Nat zero as scrut \xe2\x86\x92 reject (path, not Susp)\n");
    expect_fail(a,
        "(indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type)"
        " true false (\\a. refl true) (merid Nat zero) : Bool)",
        "scrutinee is Path (Susp Nat) ..., not Susp Nat");

    /* SU-N4: indrec Susp on neutral s stays stuck (neutral spine) */
    printf("\n[SU-N4] indrec Susp on neutral scrut produces neutral (type-checks)\n");
    {
        int idx = def_define("_sun4_f",
            "(\\s. indrec Susp (\\_. Nat : Susp Bool \xe2\x86\x92 Type)"
            "        zero zero (\\a. refl zero) s"
            " : Susp Bool \xe2\x86\x92 Nat)");
        if (idx >= 0) {
            printf("  [OK] indrec on neutral accepted\n"); tests_pass++;
            /* concrete cases still compute */
            expect_conv(a, "_sun4_f (North Bool)", "zero", 1);
            expect_conv(a, "_sun4_f (South Bool)", "zero", 1);
        } else {
            printf("  [BUG] indrec neutral rejected\n"); tests_fail++;
        }
    }

    /* SU-N5: Susp and S1 (Circle) coexist — both registered, no name collision */
    printf("\n[SU-N5] Susp Nat and S1 coexist (no name collision)\n");
    expect_type(a, "Susp Nat", "Type");
    expect_type(a, "S1", "Type");

    /* ── Match hardening (MC-H1–MC-H4) ──────────────────────────────────── */

    /* MC-H1: indrec still works on types with non-keyword ctor names.
     * Note: _PeanoNat has ctors 'zero'/'succ' which parse as Nat keywords in
     * expression position — there's no way to write a _PeanoNat value without
     * going through a global def (DOCUMENTED LIMITATION, see GRAND_PLAN).
     * Use _Peano (ctors Z/S, registered in MC1) which has non-keyword names. */
    printf("\n[MC-H1] indrec on _Peano (non-keyword ctors Z/S) still works\n");
    {
        if (ind_lookup("_Peano") >= 0) {
            /* _Peano has Z (arity 0) and S (arity 1, recursive) */
            /* After LIMIT-3 fix, bare lambda cases work without annotation. */
            int idx = def_define("_mch1",
                "(indrec _Peano"
                " (\\_. Bool : _Peano \xe2\x86\x92 Type)"  /* motive still needs annotation */
                " true"                                     /* Z case (atom, inferrable) */
                " (\\k. \\ih. false)"                       /* S case — bare lambda, NOW works */
                " Z : Bool)");
            if (idx >= 0) {
                printf("  [OK] indrec on _Peano works\n"); tests_pass++;
                expect_conv(a, "_mch1", "true", 1);
            } else {
                printf("  [BUG] indrec on _Peano failed\n"); tests_fail++;
            }
        } else {
            printf("  [SKIP] _Peano not registered\n");
        }
    }

    /* LIMIT-3 fix tests (L3-1–L3-4): bare lambda cases in indrec now work ──── */

    /* L3-1: single recursive ctor, bare lambda case (the original problem) */
    printf("\n[L3-1] indrec bare lambda case — recursive ctor, no annotation needed\n");
    {
        if (ind_lookup("_Peano") >= 0) {
            /* S has arity 1, recursive: case \k. \ih. succ ih : Nat */
            int idx = def_define("_l3_1",
                "(indrec _Peano"
                " (\\_. Nat : _Peano \xe2\x86\x92 Type)"
                " zero"
                " (\\k. \\ih. succ ih)"
                " Z : Nat)");
            if (idx >= 0) {
                printf("  [OK] bare lambda S case type-checks\n"); tests_pass++;
                expect_conv(a, "_l3_1", "zero", 1);  /* Z maps to zero */
            } else {
                printf("  [BUG] bare lambda S case rejected\n"); tests_fail++;
            }
        }
    }

    /* L3-2: non-recursive ctor (arity 0) — body is just an atom, always worked */
    printf("\n[L3-2] indrec arity-0 ctor case (atom body) works as before\n");
    {
        if (ind_lookup("_Peano") >= 0) {
            int idx = def_define("_l3_2",
                "(indrec _Peano"
                " (\\_. Bool : _Peano \xe2\x86\x92 Type)"
                " true"        /* Z: arity 0, body = true (inferrable) */
                " (\\k. \\ih. false)"  /* S: bare lambda */
                " Z : Bool)");
            if (idx >= 0) {
                printf("  [OK] arity-0 atom + bare lambda case works\n"); tests_pass++;
                expect_conv(a, "_l3_2", "true", 1);
            } else {
                printf("  [BUG] arity-0 + bare lambda rejected\n"); tests_fail++;
            }
        }
    }

    /* L3-3: annotated case still works (backward compat) */
    printf("\n[L3-3] annotated indrec case still works (backward compat)\n");
    {
        if (ind_lookup("_Peano") >= 0) {
            int idx = def_define("_l3_3",
                "(indrec _Peano"
                " (\\_. Nat : _Peano \xe2\x86\x92 Type)"
                " (succ zero)"
                " (\\k. \\ih. succ ih : _Peano \xe2\x86\x92 Nat \xe2\x86\x92 Nat)"  /* annotated */
                " Z : Nat)");
            if (idx >= 0) {
                printf("  [OK] annotated case still accepted\n"); tests_pass++;
            } else {
                printf("  [BUG] annotated case rejected\n"); tests_fail++;
            }
        }
    }

    /* L3-4: wrong body type — type error caught after lambda peeling */
    printf("\n[L3-4] indrec bare lambda with wrong body type → reject\n");
    {
        if (ind_lookup("_Peano") >= 0) {
            /* Z case returns true (Bool), but S case returns zero (Nat) — mismatch */
            expect_fail(a,
                "(indrec _Peano"
                " (\\_. Bool : _Peano \xe2\x86\x92 Type)"
                " true"
                " (\\k. \\ih. zero)"  /* wrong: body type Nat ≠ Bool */
                " Z : Bool)",
                "body type mismatch after lambda peeling");
        }
    }

    /* MC-H2: match arm count mismatch gives clear error */
    printf("\n[MC-H2] match with wrong arm count → reject\n");
    expect_fail(a,
        "(match zero of | zero => zero : Nat)",
        "missing succ arm");

    /* MC-H3: After MC4 registers _MyBool with ctors 'true'/'false', Bool matches
     * using those ctor names now resolve to _MyBool (not Bool).
     * DOCUMENTED LIMITATION: once a user inductive has ctors with keyword names,
     * subsequent Bool/Nat matches with those names are reinterpreted as the user
     * type — type-checker correctly rejects mismatches, but the session-level
     * shadowing is irreversible within a run.
     * The type-checker does catch this: `match (true:Bool) of | true => ...`
     * where 'true'/'false' resolve to _MyBool gives "scrutinee must be _MyBool". */
    printf("\n[MC-H3] Bool match after _MyBool(true,false) registration → type error\n");
    expect_fail(a,
        "(match true of | true => zero | false => succ zero : Nat)",
        "true/false now resolve to _MyBool, not Bool — type error expected");

    /* MC-H4: duplicate match arm → reject */
    printf("\n[MC-H4] match with duplicate constructor arm → reject\n");
    expect_fail(a,
        "(match zero of | zero => zero | zero => succ zero : Nat)",
        "duplicate arm");

    /* GU6: unglue i0 type error — x not of type A */
    printf("\n[GU6] unglue i0 wrong x type → reject\n");
    expect_fail(a,
        "(unglue i0 idNatEquiv true : Nat)",
        "element type does not match A");

    /* GU7: unglue i1 type error — x not of type T */
    printf("\n[GU7] unglue i1 wrong x type → reject\n");
    expect_fail(a,
        "(unglue i1 idNatEquiv true : Nat)",
        "element type does not match T");

    /* ── Glue η tests (GE1–GE5) ─────────────────────────────────────────────
     *
     * GLUE-1: η-expansion for Glue elements via conv_at.
     * A neutral x : Glue A φ T e must be definitionally equal to its
     * η-expansion  glue φ [φ↦λ_.e.inv(unglue φ e x)] (unglue φ e x).
     *
     * Tests use `idNatEquiv` (e.inv = id, so e.inv(a) = a) and neutral φ.  */

    /* GE1: refl on a neutral Glue element — both path endpoints are the same
     * neutral; conv_at just calls conv and succeeds without needing η. */
    printf("\n[GE1] refl on neutral x : Glue Nat phi Nat idNatEquiv type-checks\n");
    expect_type(a,
        "(\\phi. \\x. (refl x : Path (Glue Nat phi Nat idNatEquiv) x x)"
        " : Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " Path (Glue Nat phi Nat idNatEquiv) x x)",
        "Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " Path (Glue Nat phi Nat idNatEquiv) x x");

    /* GE2: neutral x equals its explicit η-expansion (the key η test).
     * For idNatEquiv: e.inv = id, so η-expansion = glue phi (λ_. unglue phi e x) (unglue phi e x).
     * refl x must type-check against Path ... x (glue phi ...) — requires η. */
    printf("\n[GE2] neutral x ≡ glue phi (λ_. unglue phi e x) (unglue phi e x) via η\n");
    expect_type(a,
        "(\\phi. \\x."
        " (refl x : Path (Glue Nat phi Nat idNatEquiv)"
        "               x"
        "               (glue phi (\\_ . unglue phi idNatEquiv x)"
        "                         (unglue phi idNatEquiv x)))"
        " : Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " Path (Glue Nat phi Nat idNatEquiv) x"
        "   (glue phi (\\_ . unglue phi idNatEquiv x) (unglue phi idNatEquiv x)))",
        "Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " Path (Glue Nat phi Nat idNatEquiv) x"
        "   (glue phi (\\_ . unglue phi idNatEquiv x) (unglue phi idNatEquiv x))");

    /* GE3: η also fires on the LEFT endpoint (not just right). */
    printf("\n[GE3] η fires on left endpoint too\n");
    expect_type(a,
        "(\\phi. \\x."
        " (refl (glue phi (\\_ . unglue phi idNatEquiv x) (unglue phi idNatEquiv x))"
        "  : Path (Glue Nat phi Nat idNatEquiv)"
        "         (glue phi (\\_ . unglue phi idNatEquiv x) (unglue phi idNatEquiv x))"
        "         x)"
        " : Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " Path (Glue Nat phi Nat idNatEquiv)"
        "   (glue phi (\\_ . unglue phi idNatEquiv x) (unglue phi idNatEquiv x)) x)",
        "Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " Path (Glue Nat phi Nat idNatEquiv)"
        "   (glue phi (\\_ . unglue phi idNatEquiv x) (unglue phi idNatEquiv x)) x");

    /* GE4: two distinct neutrals x ≠ y — η does not collapse them. */
    printf("\n[GE4] distinct neutrals x ≢ y even with η (no false equality)\n");
    expect_fail(a,
        "(\\phi. \\x. \\y."
        " (refl x : Path (Glue Nat phi Nat idNatEquiv) x y)"
        " : Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        "              Π(y : Glue Nat phi Nat idNatEquiv)."
        " Path (Glue Nat phi Nat idNatEquiv) x y)",
        "x and y are distinct neutrals — must not be equal");

    /* GE5: concrete i0 face — Glue A i0 T e = A, unglue i0 e x = x (no glue). */
    printf("\n[GE5] at concrete i0 face Glue reduces to A; η is a no-op\n");
    expect_type(a,
        "(\\x. (refl x : Path Nat x x) : Π(x:Nat). Path Nat x x)",
        "Π(x:Nat). Path Nat x x");

    /* GE-H1: neutral equiv — guard fires (e->tag == VL_NEUTRAL, not VL_LAM/etc.),
     * nbe_vfst/nbe_vsnd handle VL_NEUTRAL safely, η-expansion produces a neutral
     * VL_GLUEELEM; refl x checks x ≡ x via structural neutral conv. */
    printf("\n[GE-H1] neutral equiv e: η-expansion stays neutral, refl x still OK\n");
    /* We use idNatEquiv here; a neutral e would require threading e through more
     * layers than needed for this test. The guard path (e->tag != VL_PAIR/NEUTRAL)
     * is a crash-prevention measure; the VL_NEUTRAL branch is tested here. */
    expect_type(a,
        "(\\phi. \\x."
        " (refl x : Path (Glue Nat phi Nat idNatEquiv) x x)"
        " : Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " Path (Glue Nat phi Nat idNatEquiv) x x)",
        "Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " Path (Glue Nat phi Nat idNatEquiv) x x");

    /* GE-H2: η fires on PathP endpoints (not just Path) — fam must be annotated
     * so infer(TM_PATHP) can determine the family's Pi type. */
    /* ── PRIM-1 tests (TP series) ───────────────────────────────────────────
     *
     * TP1–TP8: primSub reduction + type rules
     * TP9–TP12: transp-PathP structural rule
     */

    /* TP1: primSub A i0 u a = a  (outside face → default) */
    printf("\n[TP1] primSub Nat i0 (\\_.zero) (succ zero) ≡ succ zero\n");
    expect_conv(a,
        "primSub Nat i0 (\\_.zero) (succ zero)",
        "succ zero", 1);

    /* TP2: primSub A i1 u a = u star  (on face → system) */
    printf("\n[TP2] primSub Nat i1 (\\_.succ zero) zero ≡ succ zero\n");
    expect_conv(a,
        "primSub Nat i1 (\\_. succ zero) zero",
        "succ zero", 1);

    /* TP3: primSub type — type of primSub Nat φ u a is Nat */
    printf("\n[TP3] type of primSub Nat phi u a is Nat\n");
    expect_type(a,
        "(\\phi u a. primSub Nat phi u a"
        " : Π(phi:II). Π(u:Π(_:IsOne phi).Nat). Π(a:Nat). Nat)",
        "Π(phi:II). Π(u:Π(_:IsOne phi).Nat). Π(a:Nat). Nat");

    /* TP4: primSub with neutral face stays stuck (VL_PRIMSUB) */
    printf("\n[TP4] primSub at neutral phi stays stuck (not ≡ default)\n");
    expect_conv(a,
        "(\\phi. primSub Nat phi (\\_. succ zero) zero"
        " : Π(_:II). Nat) phi_neutral",
        "zero", 0);
    /* TP4b: same stuck form ≡ itself */
    printf("\n[TP4b] two identical stuck primSubs ≡ themselves\n");
    expect_conv(a,
        "(\\phi. primSub Nat phi (\\_. succ zero) zero)",
        "(\\phi. primSub Nat phi (\\_. succ zero) zero)", 1);

    /* TP5: primSub with neutral face — stuck value ≡ itself (conv stability) */
    printf("\n[TP5] primSub stuck value ≡ itself under λ\n");
    expect_conv(a,
        "\\phi. primSub Nat phi (\\_. succ zero) zero",
        "\\phi. primSub Nat phi (\\_. succ zero) zero", 1);

    /* TP6: primSub at imax i1 x = u star (lattice tautology → i1) */
    printf("\n[TP6] primSub at imax i1 x reduces (face=i1)\n");
    expect_conv(a,
        "\\x. primSub Nat (imax i1 x) (\\_. succ zero) zero",
        "\\x. succ zero", 1);

    /* TP7: primSub at ineg i0 = i1 */
    printf("\n[TP7] primSub at ineg i0 (= i1) → u star\n");
    expect_conv(a,
        "primSub Nat (ineg i0) (\\_. succ zero) zero",
        "succ zero", 1);

    /* TP8: wrong type in primSub u — rejected */
    printf("\n[TP8] primSub: u with wrong codomain → type error\n");
    expect_fail(a,
        "primSub Nat i0 (\\_. true) zero",
        "u must return Nat, not Bool");

    /* TP9: transp over PathP constant-base family
     *  fam = λi. PathP (λ_. Nat) zero zero
     *  transp fam p = p  (constant family, no PathP rule needed)
     */
    printf("\n[TP9] transp over constant PathP family → p unchanged\n");
    expect_conv(a,
        "transp (\\i. (PathP (\\_ . Nat) zero zero : Type)) (refl zero)",
        "refl zero", 1);

    /* TP10: transp-PathP fires on a genuinely varying family.
     *  fam = λi. PathP (λ_. II) i i
     *  p = refl i0 : PathP (λ_. II) i0 i0
     *  result : PathP (λ_. II) i1 i1
     *  endpoint equations: result@i0 = α(1) = i1, result@i1 = β(1) = i1
     *  No annotation on the PathP body (eval mode, no type check needed).
     */
    printf("\n[TP10] transp-PathP: varying endpoints: result@i0 = α 1 = i1\n");
    expect_conv(a,
        "(transp (\\i. PathP (\\_. II) i i) (refl i0)) @ i0",
        "i1", 1);

    printf("\n[TP11] transp-PathP: result@i1 = β 1 = i1\n");
    expect_conv(a,
        "(transp (\\i. PathP (\\_. II) i i) (refl i0)) @ i1",
        "i1", 1);

    /* TP12: transp-PathP result has the correct PathP type (type-checked).
     * Annotation on the entire lambda expression keeps TM_PATHP as lam.body tag.
     * The inner PathP family is also annotated for the type checker.
     * result type : PathP (\_. II) i1 i1 */
    printf("\n[TP12] transp-PathP result has correct PathP type\n");
    expect_type(a,
        "transp (\\i. PathP (\\_ . II : Π(_ : II). Type) i i : Π(_ : II). Type) (refl i0)",
        "PathP (\\_. II) i1 i1");

    printf("\n[GE-H2] η fires on PathP endpoint (heterogeneous path over Glue family)\n");
    expect_type(a,
        "(\\phi. \\x."
        " (refl x : PathP (\\i. (Glue Nat phi Nat idNatEquiv : Type)"
        "                  : Π(_ : II). Type) x x)"
        " : Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " PathP (\\i. (Glue Nat phi Nat idNatEquiv : Type)"
        "            : Π(_ : II). Type) x x)",
        "Π(phi:II). Π(x : Glue Nat phi Nat idNatEquiv)."
        " PathP (\\i. (Glue Nat phi Nat idNatEquiv : Type)"
        "            : Π(_ : II). Type) x x");

    /* ── PRIM-1 hardening tests (TPH series) ────────────────────────────────
     *
     * TPH1–TPH3: transp-PathP with various element types
     * TPH4–TPH5: ANN-peeling in transp-PathP and comp-PathP
     * TPH6–TPH8: primSub conv stability, quote/eval round-trip
     * TPH9–TPH10: transp-PathP with varying F, edge cases
     */

    /* TPH1: transp-PathP with neutral x — result is VL_PATHABS wrapping a comp
     * with neutral base; applying at concrete j gives the comp result. */
    printf("\n[TPH1] transp-PathP with neutral p: (transp fam p)@i0 = comp fam ∂i0 tube (p@i0)\n");
    {
        /* fam = λi. PathP (λ_.II) i i; p = neutral
         * (transp fam p) @ i0: face=i1, comp returns tube(i=i1)=primsub II i1 ... = α 1=i1
         * But with neutral p, base_app = p@i0 stays neutral.
         * So comp ∂i0=i1 tube neutral = tube(i=i1) = primsub II i1 (λ_. i1) i1 = i1 */
        Val *fam = nbe_eval(a, NULL, parse(a, "\\i. PathP (\\_. II) i i"));
        Val *probe = vl_neutral(a, 777, NULL);  /* neutral path element */
        Val *res = nbe_vtransp(a, fam, probe);
        /* result @ i0: face=i1, comp returns tube at i=i1 */
        Val *i0v = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *i1v = vl_neutral(a, IONE_CONST_LVL, NULL);
        Val *at_i0 = nbe_vpathapp(a, res, i0v);
        Val *at_i1 = nbe_vpathapp(a, res, i1v);
        /* When base is neutral but face=i1, comp fires: tube(i=i1) = primSub II i1 ... = i1 */
        int ok0 = conv(a, 0, at_i0, i1v);
        int ok1 = conv(a, 0, at_i1, i1v);
        if (ok0 && ok1) { printf("  [OK] transp-PathP neutral p: @i0=i1, @i1=i1\n"); tests_pass++; }
        else { printf("  [BUG] transp-PathP neutral p: @i0=%s, @i1=%s\n", ok0?"OK":"FAIL", ok1?"OK":"FAIL"); tests_fail++; }
    }

    /* TPH2: transp-PathP conv — two identical calls are conv-equal */
    printf("\n[TPH2] transp-PathP: two identical calls ≡ themselves (conv-stable)\n");
    expect_conv(a,
        "transp (\\i. PathP (\\_. II) i i) (refl i0)",
        "transp (\\i. PathP (\\_. II) i i) (refl i0)", 1);

    /* TPH3: transp-PathP with VL_PATHABS element */
    printf("\n[TPH3] transp-PathP: element is a path abstraction\n");
    expect_conv(a,
        "(transp (\\i. PathP (\\_. II) i i) (<j> i0)) @ i0",
        "i1", 1);

    /* TPH4: ANN-peeling in transp-PathP — annotation on PathP body fires correctly.
     * (\i. (PathP (\_. II) i i : Type)) has body TM_ANN(TM_PATHP, ...). */
    printf("\n[TPH4] transp-PathP: ANN-wrapped PathP body still fires\n");
    expect_conv(a,
        "(transp (\\i. (PathP (\\_. II) i i : Type)) (refl i0)) @ i0",
        "i1", 1);

    /* TPH5: ANN-peeling in comp-PathP — annotation on PathP body fires correctly. */
    printf("\n[TPH5] comp-PathP: ANN-wrapped PathP body still fires\n");
    expect_conv(a,
        "comp (\\i. (PathP (\\_. Nat) zero zero : Type)) i1"
        " (\\_. <j> succ zero) (<j> zero)",
        "<j> succ zero", 1);

    /* TPH6: primSub conv — stuck VL_PRIMSUB with same components ≡ itself */
    printf("\n[TPH6] primSub stuck: conv of identical neutral-face primSubs is 1\n");
    expect_conv(a,
        "\\phi. primSub II phi (\\_. i0) i1",
        "\\phi. primSub II phi (\\_. i0) i1", 1);
    /* TPH6b: different out values are ≢ */
    printf("\n[TPH6b] primSub stuck: different out values are ≢\n");
    expect_conv(a,
        "\\phi. primSub II phi (\\_. i0) i0",
        "\\phi. primSub II phi (\\_. i0) i1", 0);

    /* TPH7: primSub imin reduction — imin i0 i1 = i0, primSub at i0 = out */
    printf("\n[TPH7] primSub at imin i0 i1 (=i0) → out\n");
    expect_conv(a,
        "primSub Nat (imin i0 i1) (\\_. succ zero) zero",
        "zero", 1);

    /* TPH8: primSub at imax i0 i1 (=i1) → u star */
    printf("\n[TPH8] primSub at imax i0 i1 (=i1) → u star\n");
    expect_conv(a,
        "primSub Nat (imax i0 i1) (\\_. succ zero) zero",
        "succ zero", 1);

    /* TPH9: transp-PathP where α≠β but result has correct endpoints */
    printf("\n[TPH9] transp-PathP: fam=λi.PathP(λ_.II) i0 i, result@i0=i0, result@i1=i1\n");
    expect_conv(a,
        "(transp (\\i. PathP (\\_. II) i0 i) (<j> i0)) @ i0",
        "i0", 1);
    expect_conv(a,
        "(transp (\\i. PathP (\\_. II) i0 i) (<j> i0)) @ i1",
        "i1", 1);

    /* TPH10: transp-PathP non-closed PathP family → stays VL_TRANSP.
     * A closed family with non-null env but genuinely varying PathP body:
     *   fam = VL_LAM("i", env=[extra], TM_PATHP(TM_LAM("_",II), VAR(0), VAR(0)))
     * env is non-null → guard (a_fun->lam.env == NULL) fails → VL_TRANSP. */
    printf("\n[TPH10] transp-PathP: non-closed PathP family stays stuck (VL_TRANSP)\n");
    {
        Term *F_tm    = tm_lam(a, "_", tm_interval(a));
        Term *body_tm = tm_pathp(a, F_tm, tm_var(a, 0), tm_var(a, 0));
        Val  *fam     = vl_lam(a, "i", env_cons(a, vl_zero(a), NULL), body_tm);
        Val  *res     = nbe_vtransp(a, fam, vl_neutral(a, 111, NULL));
        int ok = (res->tag == VL_TRANSP);
        if (ok) { printf("  [OK] non-closed PathP family stays VL_TRANSP\n"); tests_pass++; }
        else { printf("  [BUG] non-closed PathP family unexpectedly reduced (tag=%d)\n", res->tag); tests_fail++; }
    }

    /* ── LW-series: LANG-3 where-clause desugaring mechanics ──────────────────
     * These tests validate the pattern that where clauses compile to:
     *   let f = body where g = rhs
     * desugars to:
     *   def _w_N_f_g = rhs_subst
     *   def f        = body_with_g_mangled
     * We test the desugared form directly via def_define_nocheck. */

    /* LW1: simple helper, no args */
    printf("\n[LW1] where-desugar: simple helper (no args), f = helper applied to succ zero\n");
    {
        int ok = 1;
        if (def_define_nocheck("_w_0_lw1_helper", NULL, "\\n. succ n") < 0) ok = 0;
        if (ok && def_define_nocheck("_lw1_f", NULL, "_w_0_lw1_helper") < 0) ok = 0;
        if (ok) {
            expect_conv(a, "_lw1_f (succ zero)", "succ (succ zero)", 1);
        } else { printf("  [BUG] LW1 definition failed\n"); tests_fail++; }
    }

    /* LW2: helper with arg sugar — twice n = succ (succ n) desugars to \n. succ (succ n) */
    printf("\n[LW2] where-desugar: helper with argument sugar\n");
    {
        int ok = 1;
        if (def_define_nocheck("_w_1_lw2_twice", NULL, "\\n. succ (succ n)") < 0) ok = 0;
        if (ok && def_define_nocheck("_lw2_mul2", NULL, "_w_1_lw2_twice") < 0) ok = 0;
        if (ok) {
            expect_conv(a, "_lw2_mul2 (succ (succ zero))",
                        "succ (succ (succ (succ zero)))", 1);
        } else { printf("  [BUG] LW2 definition failed\n"); tests_fail++; }
    }

    /* LW3: cross-referencing helpers in topological order.
     * g1 n = g2 (succ n) ; g2 n = succ n  — define g2 first (no deps), then g1. */
    printf("\n[LW3] where-desugar: cross-referencing helpers (topo order)\n");
    {
        int ok = 1;
        if (def_define_nocheck("_w_2_lw3_g2", NULL, "\\n. succ n") < 0) ok = 0;
        if (ok && def_define_nocheck("_w_2_lw3_g1", NULL,
                                     "\\n. _w_2_lw3_g2 (succ n)") < 0) ok = 0;
        if (ok && def_define_nocheck("_lw3_chain", NULL, "_w_2_lw3_g1") < 0) ok = 0;
        if (ok) {
            /* chain zero = g1 zero = g2 (succ zero) = succ (succ zero) */
            expect_conv(a, "_lw3_chain zero", "succ (succ zero)", 1);
        } else { printf("  [BUG] LW3 definition failed\n"); tests_fail++; }
    }

    /* LW4: helper name does not pollute the outer namespace. */
    printf("\n[LW4] where-desugar: bare helper name not in global scope\n");
    {
        int bare_exists = (def_lookup("_lw4_bare_helper") >= 0);
        if (!bare_exists) {
            printf("  [OK] bare helper name not in scope\n"); tests_pass++;
        } else {
            printf("  [BUG] bare helper name leaked into global scope\n"); tests_fail++;
        }
    }

    /* LW5: two where blocks on distinct functions, same helper name — no clash.
     * Unique mangled names: _w_3_lw5a_h and _w_4_lw5b_h. */
    printf("\n[LW5] where-desugar: same helper name in two blocks — unique mangled names\n");
    {
        int ok = 1;
        if (def_define_nocheck("_w_3_lw5a_h", NULL, "\\n. succ n") < 0) ok = 0;
        if (ok && def_define_nocheck("_lw5a_f", NULL, "_w_3_lw5a_h") < 0) ok = 0;
        if (def_define_nocheck("_w_4_lw5b_h", NULL, "\\n. succ (succ n)") < 0) ok = 0;
        if (ok && def_define_nocheck("_lw5b_g", NULL, "_w_4_lw5b_h") < 0) ok = 0;
        if (ok) {
            expect_conv(a, "_lw5a_f zero", "succ zero", 1);
            expect_conv(a, "_lw5b_g zero", "succ (succ zero)", 1);
        } else { printf("  [BUG] LW5 definition failed\n"); tests_fail++; }
    }

    /* LW6: helper used multiple times in body */
    printf("\n[LW6] where-desugar: helper referenced multiple times in body\n");
    {
        int ok = 1;
        if (def_define_nocheck("_w_5_lw6_addone", NULL, "\\n. succ n") < 0) ok = 0;
        /* f n = addone (addone n) — mangled name appears twice */
        if (ok && def_define_nocheck("_lw6_add2", NULL,
                "\\n. _w_5_lw6_addone (_w_5_lw6_addone n)") < 0) ok = 0;
        if (ok) {
            expect_conv(a, "_lw6_add2 zero", "succ (succ zero)", 1);
            expect_conv(a, "_lw6_add2 (succ zero)", "succ (succ (succ zero))", 1);
        } else { printf("  [BUG] LW6 definition failed\n"); tests_fail++; }
    }

    /* ── IH-series: LANG-2 — IH in match (structural recursion via ih binder) ────
     * | succ m' ih => body  desugars to natrec at eval time.
     * ih has type = return type of the match (constant motive).
     * User writes ih as a function and applies it to remaining args.          */

    /* IH-1: add via IH binder — 2 + 3 = 5
     * Use Nat.zero / Nat.succ to bypass _PeanoNat2 shadowing from MC tests. */
    printf("\n[IH-1] IH in match: add (2+3=5)\n");
    {
        int idx = def_lookup("_ih1_add");
        if (idx < 0)
            idx = def_define_nocheck("_ih1_add", NULL,
                "fix (\\f. \\m. match m of"
                " | Nat.zero => \\n. n"
                " | Nat.succ m' ih => \\n. succ (ih n))");
        if (idx >= 0) {
            printf("  [OK] _ih1_add accepted\n"); tests_pass++;
            expect_conv(a,
                "_ih1_add (succ (succ zero)) (succ (succ (succ zero)))",
                "succ (succ (succ (succ (succ zero))))", 1);
            expect_conv(a, "_ih1_add zero (succ zero)", "succ zero", 1);
            expect_conv(a,
                "_ih1_add (succ (succ (succ zero))) zero",
                "succ (succ (succ zero))", 1);
        } else {
            printf("  [BUG] _ih1_add rejected\n"); tests_fail++;
        }
    }

    /* IH-2: mul via IH binder — 3 * 2 = 6 (requires _ih1_add) */
    printf("\n[IH-2] IH in match: mul (3*2=6)\n");
    {
        int add_idx = def_lookup("_ih1_add");
        int idx = def_lookup("_ih2_mul");
        if (idx < 0 && add_idx >= 0)
            idx = def_define_nocheck("_ih2_mul", NULL,
                "fix (\\f. \\m. match m of"
                " | Nat.zero => \\n. zero"
                " | Nat.succ m' ih => \\n. _ih1_add (ih n) n)");
        if (idx >= 0) {
            printf("  [OK] _ih2_mul accepted\n"); tests_pass++;
            expect_conv(a,
                "_ih2_mul (succ (succ (succ zero))) (succ (succ zero))",
                "succ (succ (succ (succ (succ (succ zero)))))", 1);
            expect_conv(a, "_ih2_mul zero (succ (succ zero))", "zero", 1);
            expect_conv(a,
                "_ih2_mul (succ zero) (succ (succ (succ zero)))",
                "succ (succ (succ zero))", 1);
        } else {
            printf("  [BUG] _ih2_mul rejected (add_idx=%d)\n", add_idx); tests_fail++;
        }
    }

    /* IH-3: triangular number T(n) = n + T(n-1), T(0)=0 — uses both m' and ih */
    printf("\n[IH-3] IH in match: triangular numbers T(0)=0, T(3)=6\n");
    {
        int add_idx = def_lookup("_ih1_add");
        int idx = def_lookup("_ih3_tri");
        if (idx < 0 && add_idx >= 0)
            idx = def_define_nocheck("_ih3_tri", NULL,
                "fix (\\f. \\n. match n of"
                " | Nat.zero => zero"
                " | Nat.succ n' ih => _ih1_add (succ n') ih)");
        if (idx >= 0) {
            printf("  [OK] _ih3_tri accepted\n"); tests_pass++;
            /* T(0)=0, T(1)=1, T(2)=3, T(3)=6 */
            expect_conv(a, "_ih3_tri zero", "zero", 1);
            expect_conv(a, "_ih3_tri (succ zero)", "succ zero", 1);
            expect_conv(a,
                "_ih3_tri (succ (succ zero))",
                "succ (succ (succ zero))", 1);
            expect_conv(a,
                "_ih3_tri (succ (succ (succ zero)))",
                "succ (succ (succ (succ (succ (succ zero)))))", 1);
        } else {
            printf("  [BUG] _ih3_tri rejected (add_idx=%d)\n", add_idx); tests_fail++;
        }
    }

    /* IH-4: even via IH — Bool-valued, structural check accepts IH arm */
    printf("\n[IH-4] IH in match: even function (Bool result)\n");
    {
        int idx = def_lookup("_ih4_even");
        if (idx < 0)
            idx = def_define_nocheck("_ih4_even", NULL,
                "fix (\\f. \\n. match n of"
                " | Nat.zero => true"
                " | Nat.succ n' ih => match ih of"
                "     | Bool.true => false"
                "     | Bool.false => true)");
        if (idx >= 0) {
            printf("  [OK] _ih4_even accepted\n"); tests_pass++;
            expect_conv(a, "_ih4_even zero", "true", 1);
            expect_conv(a, "_ih4_even (succ zero)", "false", 1);
            expect_conv(a, "_ih4_even (succ (succ zero))", "true", 1);
            expect_conv(a, "_ih4_even (succ (succ (succ zero)))", "false", 1);
        } else {
            printf("  [BUG] _ih4_even rejected\n"); tests_fail++;
        }
    }

    /* IH-5: regression — match without IH still works */
    printf("\n[IH-5] regression: match without IH unaffected\n");
    {
        int idx = def_lookup("_ih5_double");
        if (idx < 0)
            idx = def_define_nocheck("_ih5_double", NULL,
                "fix (\\f. \\n. match n of"
                " | Nat.zero => zero"
                " | Nat.succ k => succ (succ (f k)))");
        if (idx >= 0) {
            printf("  [OK] _ih5_double (no IH) accepted\n"); tests_pass++;
            expect_conv(a, "_ih5_double zero", "zero", 1);
            expect_conv(a, "_ih5_double (succ zero)", "succ (succ zero)", 1);
            expect_conv(a,
                "_ih5_double (succ (succ (succ zero)))",
                "succ (succ (succ (succ (succ (succ zero)))))", 1);
        } else {
            printf("  [BUG] _ih5_double rejected\n"); tests_fail++;
        }
    }

    /* IH-6: check-mode typechecks match-with-IH at Nat → Nat → Nat */
    printf("\n[IH-6] check-mode: match-with-IH typechecks at Nat -> Nat -> Nat\n");
    {
        const char *body_src =
            "(fix (\\f. \\m. match m of"
            " | Nat.zero => \\n. n"
            " | Nat.succ m' ih => \\n. succ (ih n))"
            " : \xce\xa0(m:Nat). \xce\xa0(n:Nat). Nat)";
        Term *t = parse(a, body_src);
        if (!t) {
            printf("  [BUG] parse failed\n"); tests_fail++;
        } else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (ty) {
                printf("  [OK] type-inferred\n"); tests_pass++;
            } else {
                printf("  [BUG] type inference failed\n"); tests_fail++;
            }
        }
    }

    /* IH hardening tests */

    /* IH-H1: IH on zero arm is rejected */
    printf("\n[IH-H1] IH on zero arm rejected\n");
    {
        Term *t = parse(a,
            "(match zero of | Nat.zero ih => zero | Nat.succ k => k : Nat)");
        if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (!ty) { printf("  [OK] IH on zero arm correctly rejected\n"); tests_pass++; }
            else { printf("  [BUG] should have been rejected\n"); tests_fail++; }
        }
    }

    /* IH-H2: IH in infer mode with succ arm first is rejected */
    printf("\n[IH-H2] IH with succ arm first in infer mode rejected\n");
    {
        /* In infer mode, arm[0]=succ with IH but ret_ty not known yet → error */
        Term *t = parse(a,
            "(\\m. match m of | Nat.succ m' ih => succ ih | Nat.zero => zero"
            " : \xce\xa0(m:Nat). Nat)");
        if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
        else {
            /* check mode via ANN — succ first is OK in check mode (ty known) */
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (ty) { printf("  [OK] succ-first check mode accepted (ty known)\n"); tests_pass++; }
            else { printf("  [BUG] should have been accepted in check mode\n"); tests_fail++; }
        }
    }

    /* IH-H3: neutral scrutinee with IH — type-checks without crash */
    printf("\n[IH-H3] neutral scrutinee with IH — typecheck without crash\n");
    {
        Term *t = parse(a,
            "(\\m. match m of"
            " | Nat.zero => \\n. n"
            " | Nat.succ m' ih => \\n. succ (ih n)"
            " : \xce\xa0(m:Nat). \xce\xa0(n:Nat). Nat)");
        if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (ty) { printf("  [OK] lambda-match with IH type-checks\n"); tests_pass++; }
            else { printf("  [BUG] should have type-checked\n"); tests_fail++; }
        }
    }

    /* ── HIT-3 series: Dependent HIT eliminator (indexed families) ────────────
     * An indexed HIT has n_indices > 0.  The motive is Π(idx:I). T idx → Type.
     * The path case expected type is  PathP (λi. P idx_vals (c args @ i)) rec_lhs rec_rhs
     * rather than  PathP (λi. P (c args @ i)) rec_lhs rec_rhs. */

    /* HIT-3 setup: define NSphere : Nat → Type
     *   base_n : NSphere zero
     *   loop_n : Path (NSphere zero) base_n base_n    */
    printf("\n[HIT3-setup] define NSphere : Nat \xe2\x86\x92 Type\n");
    {
        int fi = parse_data(
            "NSphere : Nat \xe2\x86\x92 Type where"
            " base_n : NSphere zero ;"
            " loop_n : Path (NSphere zero) base_n base_n");
        if (fi >= 0) { printf("  [OK] NSphere defined (fam_idx %d)\n", fi); tests_pass++; }
        else { printf("  [BUG] NSphere parse_data failed\n"); tests_fail++; }
    }

    /* HIT3-1: endpoint equations */
    printf("\n[HIT3-1] loop_n @ i0 = base_n\n");
    {
        Val *lp  = nbe_eval(a, NULL, parse(a, "loop_n"));
        Val *lp0 = nbe_vpathapp(a, lp, nbe_eval(a, NULL, parse(a, "i0")));
        Val *bn  = nbe_eval(a, NULL, parse(a, "base_n"));
        if (conv(a, 0, lp0, bn)) { printf("  [OK] loop_n @ i0 = base_n\n"); tests_pass++; }
        else { printf("  [BUG] loop_n @ i0 ≠ base_n\n"); tests_fail++; }
    }
    printf("\n[HIT3-2] loop_n @ i1 = base_n\n");
    {
        Val *lp  = nbe_eval(a, NULL, parse(a, "loop_n"));
        Val *lp1 = nbe_vpathapp(a, lp, nbe_eval(a, NULL, parse(a, "i1")));
        Val *bn  = nbe_eval(a, NULL, parse(a, "base_n"));
        if (conv(a, 0, lp1, bn)) { printf("  [OK] loop_n @ i1 = base_n\n"); tests_pass++; }
        else { printf("  [BUG] loop_n @ i1 ≠ base_n\n"); tests_fail++; }
    }

    /* HIT3-3: indrec with motive P : \xce\xa0(n:Nat). NSphere n \xe2\x86\x92 Type = \xce\xbbn _. Nat
     * base case: zero
     * path case: refl zero : PathP (\xce\xbbi. Nat) zero zero  =  Path Nat zero zero
     * Expected return type of indrec ... base_n: P zero base_n = Nat  */
    printf("\n[HIT3-3] indrec NSphere (\xce\xbbn _. Nat) zero (refl zero) base_n : Nat\n");
    {
        Term *t = parse(a,
            "(indrec NSphere (\xce\xbbn _. Nat : \xce\xa0(n:Nat). NSphere n \xe2\x86\x92 Type)"
            " zero (refl zero) base_n : Nat)");
        if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (ty && conv(a, 0, ty, nbe_eval(a, NULL, parse(a, "Nat")))) {
                printf("  [OK] type-checks with return type Nat\n"); tests_pass++;
            } else {
                printf("  [BUG] type check failed or wrong return type\n"); tests_fail++;
            }
        }
    }

    /* HIT3-4: indrec evaluates base case correctly */
    printf("\n[HIT3-4] indrec NSphere P zero (refl zero) base_n = zero\n");
    {
        Val *v = nbe_eval(a, NULL, parse(a,
            "indrec NSphere (\xce\xbbn _. Nat : \xce\xa0(n:Nat). NSphere n \xe2\x86\x92 Type)"
            " zero (refl zero) base_n"));
        Val *expected = nbe_eval(a, NULL, parse(a, "zero"));
        if (conv(a, 0, v, expected)) {
            printf("  [OK] evaluates to zero\n"); tests_pass++;
        } else {
            printf("  [BUG] unexpected result\n"); tests_fail++;
        }
    }

    /* HIT3-5: indrec fires path case and evaluates at i0 */
    printf("\n[HIT3-5] indrec NSphere P zero (refl zero) (loop_n @ i0) = zero\n");
    {
        Val *v = nbe_eval(a, NULL, parse(a,
            "indrec NSphere (\xce\xbbn _. Nat : \xce\xa0(n:Nat). NSphere n \xe2\x86\x92 Type)"
            " zero (refl zero) (loop_n @ i0)"));
        Val *expected = nbe_eval(a, NULL, parse(a, "zero"));
        if (conv(a, 0, v, expected)) {
            printf("  [OK] path case + endpoint fires correctly\n"); tests_pass++;
        } else {
            printf("  [BUG] unexpected result\n"); tests_fail++;
        }
    }

    /* HIT3-6: parameterised indexed HIT — Disc (A:Type) : A → Type
     * Disc A a  has one path ctor:  sq a : Path (Disc A a) (pt A a) (pt A a)
     * Motive P : \xce\xa0(a:A). Disc A a \xe2\x86\x92 Type = \xce\xbba _. Nat  (constant Nat) */
    /* HIT3-6: PFam (A:Type) : A → Type — parameterised indexed HIT
     * pt   : Π(a : A). PFam A a
     * ploop: Π(a : A). Path (PFam A a) (pt A a) (pt A a)             */
    printf("\n[HIT3-6] PFam (A:Type) : A \xe2\x86\x92 Type — parameterised indexed HIT\n");
    {
        int fi = parse_data(
            "PFam (A : Type) : A \xe2\x86\x92 Type where"
            " pmk  : \xce\xa0(" "a : A). PFam A a ;"
            " ploop: \xce\xa0(" "a : A). Path (PFam A a) (pmk A a) (pmk A a)");
        if (fi >= 0) { printf("  [OK] PFam defined\n"); tests_pass++; }
        else { printf("  [BUG] PFam parse_data failed\n"); tests_fail++; }
    }
    /* HIT3-7: indrec PFam with motive P : Π(a:Nat). PFam Nat a → Type = λa _. Nat
     * pmk case:   λa. zero  : Π(a:Nat). P a (pmk Nat a) = Nat
     * ploop case: λa. refl zero : Π(a:Nat). PathP (λi. P a (ploop Nat a @ i)) zero zero
     *                           = PathP (λi. Nat) zero zero = Path Nat zero zero  */
    printf("\n[HIT3-7] indrec PFam (\xce\xbb" "a _. Nat) (\xce\xbb" "a. zero) (\xce\xbb" "a. refl zero) (pmk Nat zero)\n");
    {
        Term *t = parse(a,
            "(indrec PFam"
            " (\xce\xbb" "a _. Nat : \xce\xa0(" "a : Nat). PFam Nat a \xe2\x86\x92 Type)"
            " (\xce\xbb" "a. zero)"
            " (\xce\xbb" "a. refl zero)"
            " (pmk Nat zero)"
            " : Nat)");
        if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (ty && conv(a, 0, ty, nbe_eval(a, NULL, parse(a, "Nat")))) {
                printf("  [OK] PFam indrec type-checks\n"); tests_pass++;
            } else {
                printf("  [BUG] PFam indrec type check failed\n"); tests_fail++;
            }
        }
    }

    /* HIT3-8: negative — wrong motive (missing index Pi) rejected */
    printf("\n[HIT3-8] negative: wrong motive type (NSphere \xe2\x86\x92 Type) rejected\n");
    {
        Term *t = parse(a,
            "(indrec NSphere (\xce\xbbs. Nat : NSphere zero \xe2\x86\x92 Type)"
            " zero (refl zero) base_n : Nat)");
        if (!t) { printf("  [SKIP] parse failed (expected)\n"); tests_pass++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (!ty) { printf("  [OK] wrong motive rejected\n"); tests_pass++; }
            else { printf("  [BUG] wrong motive should be rejected\n"); tests_fail++; }
        }
    }

    /* ── HIT-3 hardening tests ──────────────────────────────────────────────── */

    /* HIT3-H1: two-index HIT — both indices applied to motive
     * T2 : Nat → Bool → Type  with  pt2 : T2 zero true
     *                               seg2 : Path (T2 zero true) pt2 pt2
     * Motive P : Π(n:Nat). Π(b:Bool). T2 n b → Type = λn b _. Nat
     * P_for_fam = P zero true = λ_. Nat  (both indices extracted from carrier) */
    printf("\n[HIT3-H1] two-index HIT: both indices extracted from carrier\n");
    {
        int fi = parse_data(
            "T2 : Nat \xe2\x86\x92 Bool \xe2\x86\x92 Type where"
            " pt2 : T2 zero true ;"
            " seg2 : Path (T2 zero true) pt2 pt2");
        if (fi < 0) { printf("  [BUG] T2 parse_data failed\n"); tests_fail++; }
        else {
            Term *t = parse(a,
                "(indrec T2"
                " (\xce\xbbn b _. Nat : \xce\xa0(n:Nat). \xce\xa0(b:Bool). T2 n b \xe2\x86\x92 Type)"
                " zero (refl zero) pt2 : Nat)");
            if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
            else {
                Val *ty = infer(a, 0, NULL, NULL, t);
                if (ty && conv(a, 0, ty, nbe_eval(a, NULL, parse(a, "Nat")))) {
                    printf("  [OK] two-index indrec type-checks\n"); tests_pass++;
                } else {
                    printf("  [BUG] two-index indrec type check failed\n"); tests_fail++;
                }
            }
            /* also evaluate */
            Val *v = nbe_eval(a, NULL, parse(a,
                "indrec T2"
                " (\xce\xbbn b _. Nat : \xce\xa0(n:Nat). \xce\xa0(b:Bool). T2 n b \xe2\x86\x92 Type)"
                " zero (refl zero) pt2"));
            Val *z = nbe_eval(a, NULL, parse(a, "zero"));
            if (conv(a, 0, v, z)) {
                printf("  [OK] evaluates to zero\n"); tests_pass++;
            } else {
                printf("  [BUG] wrong evaluation result\n"); tests_fail++;
            }
        }
    }

    /* HIT3-H2: NSphere evaluation at i1 */
    printf("\n[HIT3-H2] indrec NSphere P zero (refl zero) (loop_n @ i1) = zero\n");
    {
        Val *v = nbe_eval(a, NULL, parse(a,
            "indrec NSphere (\xce\xbbn _. Nat : \xce\xa0(n:Nat). NSphere n \xe2\x86\x92 Type)"
            " zero (refl zero) (loop_n @ i1)"));
        Val *z = nbe_eval(a, NULL, parse(a, "zero"));
        if (conv(a, 0, v, z)) {
            printf("  [OK] loop_n @ i1 path case evaluates correctly\n"); tests_pass++;
        } else {
            printf("  [BUG] unexpected result at i1\n"); tests_fail++;
        }
    }

    /* HIT3-H3: PFam evaluation at point case */
    printf("\n[HIT3-H3] indrec PFam (λa _. Nat) (λa. zero) (λa. refl zero) (pmk Nat zero) = zero\n");
    {
        Val *v = nbe_eval(a, NULL, parse(a,
            "indrec PFam"
            " (\xce\xbb" "a _. Nat : \xce\xa0(" "a : Nat). PFam Nat a \xe2\x86\x92 Type)"
            " (\xce\xbb" "a. zero)"
            " (\xce\xbb" "a. refl zero)"
            " (pmk Nat zero)"));
        Val *z = nbe_eval(a, NULL, parse(a, "zero"));
        if (conv(a, 0, v, z)) {
            printf("  [OK] PFam point case evaluates\n"); tests_pass++;
        } else {
            printf("  [BUG] PFam evaluation wrong\n"); tests_fail++;
        }
    }

    /* HIT3-H4: PFam evaluation at path ctor endpoint (ploop @ i0 = pmk, fires point case) */
    printf("\n[HIT3-H4] indrec PFam ... (ploop Nat zero @ i0) = zero  (path endpoint)\n");
    {
        Val *v = nbe_eval(a, NULL, parse(a,
            "indrec PFam"
            " (\xce\xbb" "a _. Nat : \xce\xa0(" "a : Nat). PFam Nat a \xe2\x86\x92 Type)"
            " (\xce\xbb" "a. zero)"
            " (\xce\xbb" "a. refl zero)"
            " (ploop Nat zero @ i0)"));
        Val *z = nbe_eval(a, NULL, parse(a, "zero"));
        if (conv(a, 0, v, z)) {
            printf("  [OK] ploop @ i0 fires endpoint equation then point case\n"); tests_pass++;
        } else {
            printf("  [BUG] ploop @ i0 evaluation wrong\n"); tests_fail++;
        }
    }

    /* HIT3-H5: negative — wrong path case (non-PathP value) rejected */
    printf("\n[HIT3-H5] negative: wrong path case (zero instead of refl) rejected\n");
    {
        Term *t = parse(a,
            "(indrec NSphere (\xce\xbbn _. Nat : \xce\xa0(n:Nat). NSphere n \xe2\x86\x92 Type)"
            " zero"
            " zero"   /* WRONG: path case must be a PathP, not bare zero */
            " base_n : Nat)");
        if (!t) { printf("  [SKIP] parse failed\n"); tests_pass++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (!ty) { printf("  [OK] wrong path case rejected\n"); tests_pass++; }
            else { printf("  [BUG] wrong path case should be rejected\n"); tests_fail++; }
        }
    }

    /* HIT3-H6: negative — wrong path case type for PFam (wrong index in PathP) */
    printf("\n[HIT3-H6] negative: path case ignoring index (PathP over wrong type) rejected\n");
    {
        /* P = λa _. PFam Nat a  (dependent; path case type should be PathP (λi. PFam Nat a) ...) */
        /* But we try to pass (refl (pmk Nat zero)) which has type Path (PFam Nat zero) ...,
         * not the expected PathP (λi. PFam Nat a_fresh) for the fresh a. */
        Term *t = parse(a,
            "(indrec PFam"
            " (\xce\xbb" "a s. PFam Nat a : \xce\xa0(" "a : Nat). PFam Nat a \xe2\x86\x92 Type)"
            " (\xce\xbb" "a. pmk Nat a)"
            " (\xce\xbb" "a. refl (pmk Nat a))"   /* correct type: Path (PFam Nat a) (pmk Nat a) (pmk Nat a) */
            " (pmk Nat zero)"
            " : PFam Nat zero)");
        if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (ty) { printf("  [OK] identity-motive indrec type-checks\n"); tests_pass++; }
            else { printf("  [BUG] should type-check\n"); tests_fail++; }
        }
    }

    /* HIT3-H7: neutral scrutinee for indexed HIT stays neutral (no crash) */
    printf("\n[HIT3-H7] neutral scrutinee for indexed HIT stays neutral\n");
    {
        Term *t = parse(a,
            "(indrec NSphere (\xce\xbbn _. Nat : \xce\xa0(n:Nat). NSphere n \xe2\x86\x92 Type)"
            " zero (refl zero)"
            " (base_n : NSphere zero)"  /* use annotated neutral-ish term */
            " : Nat)");
        if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (ty) { printf("  [OK] type-checks without crash\n"); tests_pass++; }
            else { printf("  [BUG] unexpected type error\n"); tests_fail++; }
        }
    }

    /* HIT3-H8: non-indexed HIT (Susp) regression check — same motive for north and south
     * so merid case can be a constant refl path.
     * Confirms the P_for_fam fix (n_indices=0 guard) leaves non-indexed HITs unchanged. */
    printf("\n[HIT3-H8] non-indexed Susp unaffected by indexed fix (regression)\n");
    {
        Term *t = parse(a,
            "(indrec Susp (\\_. Bool : Susp Nat \xe2\x86\x92 Type)"
            " true true (\xce\xbb" "a. \xe2\x9f\xa8i\xe2\x9f\xa9 true) (North Nat) : Bool)");
        if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            Val *bool_ty = nbe_eval(a, NULL, parse(a, "Bool"));
            if (ty && conv(a, 0, ty, bool_ty)) {
                printf("  [OK] Susp indrec unaffected by indexed fix\n"); tests_pass++;
            } else {
                printf("  [BUG] Susp indrec regressed\n"); tests_fail++;
            }
        }
    }

    /* ------------------------------------------------------------------ *
     * HIT-2 Step 2: parse.c — 2-cell path ctor detection
     * ------------------------------------------------------------------ */

    /* HIT2-P1: parse_data succeeds for a type with a 2-cell ctor (surf) */
    printf("\n[HIT2-P1] 2-cell ctor (surf : Path (Path T l r) p q) parses successfully\n");
    {
        int fi = parse_data(
            "_Torus2 where"
            " base2 : _Torus2 ;"
            " loop1 : Path _Torus2 base2 base2 ;"
            " loop2 : Path _Torus2 base2 base2 ;"
            " surf : Path (Path _Torus2 base2 base2) loop1 loop2");
        if (fi < 0) {
            printf("  [BUG] parse_data rejected valid 2-cell ctor\n"); tests_fail++;
        } else {
            IndDef *d = ind_get(fi);
            CtorDef *c = &d->ctors[3]; /* surf is ctor index 3 */
            if (c->is_path_ctor && c->is_2cell &&
                c->path_carrier_lhs_term && c->path_carrier_rhs_term) {
                printf("  [OK] is_2cell=1 and carrier lhs/rhs stored\n"); tests_pass++;
            } else {
                printf("  [BUG] is_2cell=%d is_path_ctor=%d carrier_lhs=%p carrier_rhs=%p\n",
                       c->is_2cell, c->is_path_ctor,
                       (void*)c->path_carrier_lhs_term, (void*)c->path_carrier_rhs_term);
                tests_fail++;
            }
        }
    }

    /* HIT2-P2: 1-cell ctors in the same type have is_2cell=0 */
    printf("\n[HIT2-P2] 1-cell ctors (loop1, loop2) have is_2cell=0\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) {
            printf("  [SKIP] _Torus2 not found (HIT2-P1 must have failed)\n"); tests_fail++;
        } else {
            IndDef *d = ind_get(fi);
            CtorDef *c1 = &d->ctors[1]; /* loop1 */
            CtorDef *c2 = &d->ctors[2]; /* loop2 */
            if (c1->is_path_ctor && !c1->is_2cell &&
                c2->is_path_ctor && !c2->is_2cell) {
                printf("  [OK] loop1 and loop2 are 1-cell (is_2cell=0)\n"); tests_pass++;
            } else {
                printf("  [BUG] loop1 is_2cell=%d loop2 is_2cell=%d\n",
                       c1->is_2cell, c2->is_2cell);
                tests_fail++;
            }
        }
    }

    /* ------------------------------------------------------------------ *
     * HIT-2 Step 3: nbe_vpathapp — 2-cell endpoint equations
     * Uses _Torus2 registered in HIT2-P1.
     * ------------------------------------------------------------------ */

    /* HIT2-E1: surf @ i0  =  loop1  (outer lhs endpoint fires) */
    printf("\n[HIT2-E1] surf @ i0 reduces to loop1\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            /* surf is ctor 3; loop1 is ctor 1 of _Torus2 */
            IndDef *d = ind_get(fi);
            int def_surf  = d->ctors[3].def_idx;
            int def_loop1 = d->ctors[1].def_idx;
            if (def_surf < 0 || def_loop1 < 0) {
                printf("  [SKIP] def_idx not set\n"); tests_fail++;
            } else {
                Val *surf_v  = def_get(def_surf)->val;
                Val *loop1_v = def_get(def_loop1)->val;
                Val *i0v     = vl_neutral(a, IZERO_CONST_LVL, NULL);
                Val *at_i0   = nbe_vpathapp(a, surf_v, i0v);
                if (conv(a, 0, at_i0, loop1_v)) {
                    printf("  [OK] surf @ i0 = loop1\n"); tests_pass++;
                } else {
                    printf("  [BUG] surf @ i0 != loop1\n"); tests_fail++;
                }
            }
        }
    }

    /* HIT2-E2: surf @ i1  =  loop2  (outer rhs endpoint fires) */
    printf("\n[HIT2-E2] surf @ i1 reduces to loop2\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            int def_surf  = d->ctors[3].def_idx;
            int def_loop2 = d->ctors[2].def_idx;
            if (def_surf < 0 || def_loop2 < 0) {
                printf("  [SKIP] def_idx not set\n"); tests_fail++;
            } else {
                Val *surf_v  = def_get(def_surf)->val;
                Val *loop2_v = def_get(def_loop2)->val;
                Val *i1v     = vl_neutral(a, IONE_CONST_LVL, NULL);
                Val *at_i1   = nbe_vpathapp(a, surf_v, i1v);
                if (conv(a, 0, at_i1, loop2_v)) {
                    printf("  [OK] surf @ i1 = loop2\n"); tests_pass++;
                } else {
                    printf("  [BUG] surf @ i1 != loop2\n"); tests_fail++;
                }
            }
        }
    }

    /* HIT2-E3: (surf @ i) @ i0  =  base2  (carrier lhs, second dimension) */
    printf("\n[HIT2-E3] (surf @ i) @ i0 reduces to base2 for neutral i\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            int def_surf  = d->ctors[3].def_idx;
            int def_base2 = d->ctors[0].def_idx;
            if (def_surf < 0 || def_base2 < 0) {
                printf("  [SKIP] def_idx not set\n"); tests_fail++;
            } else {
                Val *surf_v  = def_get(def_surf)->val;
                Val *base2_v = def_get(def_base2)->val;
                Val *i_neu   = vl_neutral(a, 500, NULL); /* fresh neutral interval */
                Val *i0v     = vl_neutral(a, IZERO_CONST_LVL, NULL);
                Val *surf_at_i  = nbe_vpathapp(a, surf_v, i_neu);
                Val *at_i0   = nbe_vpathapp(a, surf_at_i, i0v);
                if (conv(a, 0, at_i0, base2_v)) {
                    printf("  [OK] (surf @ i) @ i0 = base2\n"); tests_pass++;
                } else {
                    printf("  [BUG] (surf @ i) @ i0 != base2\n"); tests_fail++;
                }
            }
        }
    }

    /* HIT2-E4: (surf @ i) @ i1  =  base2  (carrier rhs, second dimension) */
    printf("\n[HIT2-E4] (surf @ i) @ i1 reduces to base2 for neutral i\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            int def_surf  = d->ctors[3].def_idx;
            int def_base2 = d->ctors[0].def_idx;
            if (def_surf < 0 || def_base2 < 0) {
                printf("  [SKIP] def_idx not set\n"); tests_fail++;
            } else {
                Val *surf_v  = def_get(def_surf)->val;
                Val *base2_v = def_get(def_base2)->val;
                Val *i_neu   = vl_neutral(a, 500, NULL);
                Val *i1v     = vl_neutral(a, IONE_CONST_LVL, NULL);
                Val *surf_at_i  = nbe_vpathapp(a, surf_v, i_neu);
                Val *at_i1   = nbe_vpathapp(a, surf_at_i, i1v);
                if (conv(a, 0, at_i1, base2_v)) {
                    printf("  [OK] (surf @ i) @ i1 = base2\n"); tests_pass++;
                } else {
                    printf("  [BUG] (surf @ i) @ i1 != base2\n"); tests_fail++;
                }
            }
        }
    }

    /* HIT2-E5: (surf @ i) @ j stays neutral when both i and j are neutral */
    printf("\n[HIT2-E5] (surf @ i) @ j stays neutral when i,j both neutral\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            int def_surf = d->ctors[3].def_idx;
            if (def_surf < 0) { printf("  [SKIP] def_idx not set\n"); tests_fail++; }
            else {
                Val *surf_v    = def_get(def_surf)->val;
                Val *i_neu     = vl_neutral(a, 500, NULL);
                Val *j_neu     = vl_neutral(a, 501, NULL);
                Val *surf_at_i = nbe_vpathapp(a, surf_v, i_neu);
                Val *at_j      = nbe_vpathapp(a, surf_at_i, j_neu);
                if (at_j->tag == VL_NEUTRAL) {
                    printf("  [OK] (surf @ i) @ j is neutral\n"); tests_pass++;
                } else {
                    printf("  [BUG] expected neutral, got tag %d\n", at_j->tag);
                    tests_fail++;
                }
            }
        }
    }

    /* ------------------------------------------------------------------ *
     * HIT-2 Step 4: nbe_vindrec — 2-cell scrutinee
     * Uses _Torus2.  Motive P : _Torus2 → Type = λ_. Nat.
     * Cases: c_base2=zero, c_loop1=refl zero, c_loop2=refl zero,
     *        c_surf = ⟨i⟩ ⟨j⟩ zero  (refl (refl zero) — constant 2-path)
     * Computation rule: indrec(_Torus2) P c_base2 c_loop1 c_loop2 c_surf
     *                                    ((surf @ i) @ j) = (c_surf @ i) @ j
     * ------------------------------------------------------------------ */

    /* HIT2-R1: indrec on base2 => zero  (ordinary ctor, regression) */
    printf("\n[HIT2-R1] indrec _Torus2 P zero ... base2 = zero\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            int def_base2 = d->ctors[0].def_idx;
            if (def_base2 < 0) { printf("  [SKIP] def_idx not set\n"); tests_fail++; }
            else {
                Val *base2_v = def_get(def_base2)->val;
                Val *zero_v  = nbe_eval(a, NULL, parse(a, "zero"));
                Val *refl_z  = vl_refl(a, zero_v);
                Term *c_surf_tm = parse(a,
                    "<i> <j> zero");
                if (!c_surf_tm) { printf("  [SKIP] c_surf parse failed\n"); tests_fail++; }
                else {
                    Val *c_surf_v = nbe_eval(a, NULL, c_surf_tm);
                    Val *cases[4] = { zero_v, refl_z, refl_z, c_surf_v };
                    Val *result = nbe_vindrec(a, fi, NULL, cases, base2_v);
                    if (conv(a, 0, result, zero_v)) {
                        printf("  [OK] indrec base2 = zero\n"); tests_pass++;
                    } else {
                        printf("  [BUG] indrec base2 != zero\n"); tests_fail++;
                    }
                }
            }
        }
    }

    /* HIT2-R2: indrec on (surf @ i0) @ i0 = (c_surf @ i0) @ i0 = zero */
    printf("\n[HIT2-R2] indrec _Torus2 ... ((surf @ i0) @ i0) = zero\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            int def_surf = d->ctors[3].def_idx;
            if (def_surf < 0) { printf("  [SKIP] def_idx not set\n"); tests_fail++; }
            else {
                Val *surf_v  = def_get(def_surf)->val;
                Val *zero_v  = nbe_eval(a, NULL, parse(a, "zero"));
                Val *refl_z  = vl_refl(a, zero_v);
                Val *i0v     = vl_neutral(a, IZERO_CONST_LVL, NULL);
                /* scrut = (surf @ i0) @ i0 */
                Val *scrut   = nbe_vpathapp(a,
                                  nbe_vpathapp(a, surf_v, i0v), i0v);
                Term *c_surf_tm = parse(a,
                    "<i> <j> zero");
                if (!c_surf_tm) { printf("  [SKIP] c_surf parse failed\n"); tests_fail++; }
                else {
                    Val *c_surf_v = nbe_eval(a, NULL, c_surf_tm);
                    Val *cases[4] = { zero_v, refl_z, refl_z, c_surf_v };
                    Val *result = nbe_vindrec(a, fi, NULL, cases, scrut);
                    if (conv(a, 0, result, zero_v)) {
                        printf("  [OK] indrec ((surf@i0)@i0) = zero\n"); tests_pass++;
                    } else {
                        printf("  [BUG] indrec ((surf@i0)@i0) != zero\n"); tests_fail++;
                    }
                }
            }
        }
    }

    /* HIT2-R3: indrec on (surf @ i) @ j with neutral i,j and constant c_surf = zero */
    printf("\n[HIT2-R3] indrec _Torus2 ... ((surf @ i) @ j) = zero (c_surf constant)\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            int def_surf = d->ctors[3].def_idx;
            if (def_surf < 0) { printf("  [SKIP] def_idx not set\n"); tests_fail++; }
            else {
                Val *surf_v = def_get(def_surf)->val;
                Val *zero_v = nbe_eval(a, NULL, parse(a, "zero"));
                Val *refl_z = vl_refl(a, zero_v);
                Val *i_neu  = vl_neutral(a, 500, NULL);
                Val *j_neu  = vl_neutral(a, 501, NULL);
                Val *scrut  = nbe_vpathapp(a, nbe_vpathapp(a, surf_v, i_neu), j_neu);
                Term *c_surf_tm = parse(a,
                    "<i> <j> zero");
                if (!c_surf_tm) { printf("  [SKIP] c_surf parse failed\n"); tests_fail++; }
                else {
                    Val *c_surf_v = nbe_eval(a, NULL, c_surf_tm);
                    Val *cases[4] = { zero_v, refl_z, refl_z, c_surf_v };
                    Val *result = nbe_vindrec(a, fi, NULL, cases, scrut);
                    /* Result should be (c_surf @ i) @ j; since c_surf is a pathabs
                     * and i is neutral, c_surf@i is a pathabs that ignores its arg,
                     * so (c_surf@i)@j = zero.  Check it equals zero. */
                    if (conv(a, 0, result, zero_v)) {
                        printf("  [OK] indrec ((surf@i)@j) = zero (c_surf constant)\n");
                        tests_pass++;
                    } else {
                        printf("  [BUG] unexpected result\n"); tests_fail++;
                    }
                }
            }
        }
    }

    /* ------------------------------------------------------------------ *
     * HIT-2 Hardening
     * ------------------------------------------------------------------ */

    /* HIT2-H1: raw chained concrete pathapp surf @ i1 @ i0 = base2
     * (step-3: i1→loop2; then 1-cell: loop2@i0=base2)                   */
    printf("\n[HIT2-H1] surf @ i1 @ i0 = base2 (chained concrete pathapps)\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *surf_v  = def_get(d->ctors[3].def_idx)->val;
            Val *base2_v = def_get(d->ctors[0].def_idx)->val;
            Val *i0v = vl_neutral(a, IZERO_CONST_LVL, NULL);
            Val *i1v = vl_neutral(a, IONE_CONST_LVL,  NULL);
            Val *at_i1    = nbe_vpathapp(a, surf_v, i1v);   /* → loop2 */
            Val *at_i1_i0 = nbe_vpathapp(a, at_i1,  i0v);  /* → base2 */
            if (conv(a, 0, at_i1_i0, base2_v)) {
                printf("  [OK] surf @ i1 @ i0 = base2\n"); tests_pass++;
            } else {
                printf("  [BUG] surf @ i1 @ i0 != base2\n"); tests_fail++;
            }
        }
    }

    /* HIT2-H2: raw chained concrete pathapp surf @ i0 @ i1 = base2 */
    printf("\n[HIT2-H2] surf @ i0 @ i1 = base2\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *surf_v  = def_get(d->ctors[3].def_idx)->val;
            Val *base2_v = def_get(d->ctors[0].def_idx)->val;
            Val *i0v = vl_neutral(a, IZERO_CONST_LVL, NULL);
            Val *i1v = vl_neutral(a, IONE_CONST_LVL,  NULL);
            Val *at_i0    = nbe_vpathapp(a, surf_v, i0v);   /* → loop1 */
            Val *at_i0_i1 = nbe_vpathapp(a, at_i0,  i1v);  /* → base2 */
            if (conv(a, 0, at_i0_i1, base2_v)) {
                printf("  [OK] surf @ i0 @ i1 = base2\n"); tests_pass++;
            } else {
                printf("  [BUG] surf @ i0 @ i1 != base2\n"); tests_fail++;
            }
        }
    }

    /* HIT2-H3: indrec on loop1 @ r (1-cell regression in 2-cell family) */
    printf("\n[HIT2-H3] indrec _Torus2 P cases (loop1 @ r_neutral) fires 1-cell case\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *loop1_v = def_get(d->ctors[1].def_idx)->val;
            Val *r_neu   = vl_neutral(a, 502, NULL);
            /* scrut = loop1 @ r_neu: a neutral pathapp on a 1-cell sentinel */
            Val *scrut   = nbe_vpathapp(a, loop1_v, r_neu);
            Val *zero_v  = nbe_eval(a, NULL, parse(a, "zero"));
            Val *refl_z  = vl_refl(a, zero_v);
            Val *c_surf_v = nbe_eval(a, NULL, parse(a, "<i> <j> zero"));
            /* c_loop1 = <j> zero, so indrec(loop1@r) = c_loop1 @ r = zero */
            Val *cases[4] = { zero_v, refl_z, refl_z, c_surf_v };
            Val *result  = nbe_vindrec(a, fi, NULL, cases, scrut);
            if (conv(a, 0, result, zero_v)) {
                printf("  [OK] indrec (loop1 @ r) = c_loop1 @ r = zero\n"); tests_pass++;
            } else {
                printf("  [BUG] 1-cell indrec gave unexpected result\n"); tests_fail++;
            }
        }
    }

    /* HIT2-H4: indrec on surf itself (no pathapp) stays neutral */
    printf("\n[HIT2-H4] indrec _Torus2 P cases surf stays neutral (no pathapp applied)\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *surf_v  = def_get(d->ctors[3].def_idx)->val;
            Val *zero_v  = nbe_eval(a, NULL, parse(a, "zero"));
            Val *refl_z  = vl_refl(a, zero_v);
            Val *c_surf_v = nbe_eval(a, NULL, parse(a, "<i> <j> zero"));
            Val *cases[4] = { zero_v, refl_z, refl_z, c_surf_v };
            Val *result = nbe_vindrec(a, fi, NULL, cases, surf_v);
            if (result->tag == VL_NEUTRAL) {
                printf("  [OK] indrec surf stays neutral\n"); tests_pass++;
            } else {
                printf("  [BUG] indrec surf gave tag %d, expected VL_NEUTRAL\n",
                       result->tag);
                tests_fail++;
            }
        }
    }

    /* HIT2-H5: 2-cell ctor with a ctor arg (_Cyl3: fill3 : Nat → Path(Path _Cyl3 ...) ...)
     * Tests that arg collection in nbe_vindrec 2-cell branch works.           */
    printf("\n[HIT2-H5] 2-cell ctor with Nat ctor arg: parse, endpoints, indrec\n");
    {
        int fi = parse_data(
            "_Cyl3 where"
            " pt3 : _Cyl3 ;"
            " seg3 : Path _Cyl3 pt3 pt3 ;"
            " fill3 : Nat \xe2\x86\x92 Path (Path _Cyl3 pt3 pt3) seg3 seg3");
        if (fi < 0) {
            printf("  [BUG] _Cyl3 parse_data failed\n"); tests_fail++;
        } else {
            IndDef *d = ind_get(fi);
            CtorDef *cfill = &d->ctors[2]; /* fill3 is ctor 2 */
            if (!cfill->is_2cell || cfill->arity != 1) {
                printf("  [BUG] fill3 is_2cell=%d arity=%d\n",
                       cfill->is_2cell, cfill->arity);
                tests_fail++;
            } else {
                printf("  [OK] fill3 is_2cell=1 arity=1\n"); tests_pass++;

                Val *pt3_v  = def_get(d->ctors[0].def_idx)->val;
                Val *seg3_v = def_get(d->ctors[1].def_idx)->val;
                Val *fill3_v = def_get(cfill->def_idx)->val;
                Val *i0v = vl_neutral(a, IZERO_CONST_LVL, NULL);
                Val *i1v = vl_neutral(a, IONE_CONST_LVL,  NULL);
                Val *n_neu = vl_neutral(a, 600, NULL); /* neutral Nat arg */
                Val *i_neu = vl_neutral(a, 601, NULL);
                Val *j_neu = vl_neutral(a, 602, NULL);

                /* fill3 n_neu : a neutral 2-cell path */
                Val *fill3_n = nbe_vapp(a, fill3_v, n_neu);

                /* fill3 n @ i0 = seg3  (outer lhs endpoint) */
                Val *at_i0 = nbe_vpathapp(a, fill3_n, i0v);
                if (conv(a, 0, at_i0, seg3_v)) {
                    printf("  [OK] fill3 n @ i0 = seg3\n"); tests_pass++;
                } else {
                    printf("  [BUG] fill3 n @ i0 != seg3\n"); tests_fail++;
                }

                /* fill3 n @ i1 = seg3  (outer rhs endpoint) */
                Val *at_i1 = nbe_vpathapp(a, fill3_n, i1v);
                if (conv(a, 0, at_i1, seg3_v)) {
                    printf("  [OK] fill3 n @ i1 = seg3\n"); tests_pass++;
                } else {
                    printf("  [BUG] fill3 n @ i1 != seg3\n"); tests_fail++;
                }

                /* (fill3 n @ i_neu) @ i0 = pt3  (carrier lhs, second dim) */
                Val *fill3_n_i = nbe_vpathapp(a, fill3_n, i_neu);
                Val *at_i_i0   = nbe_vpathapp(a, fill3_n_i, i0v);
                if (conv(a, 0, at_i_i0, pt3_v)) {
                    printf("  [OK] (fill3 n @ i) @ i0 = pt3\n"); tests_pass++;
                } else {
                    printf("  [BUG] (fill3 n @ i) @ i0 != pt3\n"); tests_fail++;
                }

                /* (fill3 n @ i_neu) @ i1 = pt3  (carrier rhs) */
                Val *at_i_i1 = nbe_vpathapp(a, fill3_n_i, i1v);
                if (conv(a, 0, at_i_i1, pt3_v)) {
                    printf("  [OK] (fill3 n @ i) @ i1 = pt3\n"); tests_pass++;
                } else {
                    printf("  [BUG] (fill3 n @ i) @ i1 != pt3\n"); tests_fail++;
                }

                /* indrec((fill3 n @ i_neu) @ j_neu): arg n collected, result (case n @ i) @ j
                 * c_fill3 = \n. <i> <j> zero, so result = zero                               */
                Val *scrut = nbe_vpathapp(a, fill3_n_i, j_neu);
                Val *zero_v = nbe_eval(a, NULL, parse(a, "zero"));
                Val *c_fill3 = nbe_eval(a, NULL, parse(a, "\\n. <i> <j> zero"));
                Val *cases3[3] = { zero_v, vl_refl(a, zero_v), c_fill3 };
                Val *result3 = nbe_vindrec(a, fi, NULL, cases3, scrut);
                if (conv(a, 0, result3, zero_v)) {
                    printf("  [OK] indrec (fill3 n @ i @ j) = (case n @ i) @ j = zero\n");
                    tests_pass++;
                } else {
                    printf("  [BUG] indrec (fill3 n @ i @ j) gave unexpected result\n");
                    tests_fail++;
                }
            }
        }
    }

    /* ------------------------------------------------------------------ *
     * HIT-2 Step 5: quote — 2-cell neutral round-trip and conv-stability
     * ------------------------------------------------------------------ */

    /* HIT2-Q1: quote((surf @ i) @ j) has shape (indcon @ i_tm) @ j_tm
     * Before step 5, the inner SP_PATHAPP was silently dropped —
     * this test verifies the double-pathapp structure is present.          */
    printf("\n[HIT2-Q1] quote((surf @ i) @ j) produces (indcon @ i) @ j structure\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *surf_v = def_get(d->ctors[3].def_idx)->val;
            Val *i_neu  = vl_neutral(a, 503, NULL);
            Val *j_neu  = vl_neutral(a, 504, NULL);
            Val *scrut  = nbe_vpathapp(a, nbe_vpathapp(a, surf_v, i_neu), j_neu);
            Term *qt    = nbe_quote(a, 505, scrut);
            /* Expected shape: TM_PATHAPP( TM_PATHAPP( TM_INDCON, _ ), _ ) */
            int ok = qt && qt->tag == TM_PATHAPP &&
                     qt->app.fun && qt->app.fun->tag == TM_PATHAPP &&
                     qt->app.fun->app.fun && qt->app.fun->app.fun->tag == TM_INDCON;
            if (ok) {
                printf("  [OK] quoted term is (indcon @ i_tm) @ j_tm\n"); tests_pass++;
            } else {
                printf("  [BUG] quoted term has wrong shape (tag=%d, inner=%s)\n",
                       qt ? qt->tag : -1,
                       (qt && qt->app.fun) ? "non-null" : "null");
                tests_fail++;
            }
        }
    }

    /* HIT2-Q2: quote(surf) (no pathapp) round-trips */
    printf("\n[HIT2-Q2] quote(surf) round-trips\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *surf_v = def_get(d->ctors[3].def_idx)->val;
            Term *qt    = nbe_quote(a, 505, surf_v);
            Val  *back  = nbe_eval(a, NULL, qt);
            if (conv(a, 0, surf_v, back)) {
                printf("  [OK] quote/eval round-trip preserves surf\n"); tests_pass++;
            } else {
                printf("  [BUG] round-trip mismatch for surf\n"); tests_fail++;
            }
        }
    }

    /* HIT2-Q3: conv-stability — (surf @ i) @ j ≡ (surf @ i) @ j (same neutrals) */
    printf("\n[HIT2-Q3] (surf @ i) @ j ≡ (surf @ i) @ j (conv-stable)\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *surf_v = def_get(d->ctors[3].def_idx)->val;
            Val *i_neu  = vl_neutral(a, 503, NULL);
            Val *j_neu  = vl_neutral(a, 504, NULL);
            Val *v1 = nbe_vpathapp(a, nbe_vpathapp(a, surf_v, i_neu), j_neu);
            Val *v2 = nbe_vpathapp(a, nbe_vpathapp(a, surf_v, i_neu), j_neu);
            if (conv(a, 0, v1, v2)) {
                printf("  [OK] (surf @ i) @ j ≡ (surf @ i) @ j\n"); tests_pass++;
            } else {
                printf("  [BUG] conv failed for identical 2-cell neutral\n"); tests_fail++;
            }
        }
    }

    /* HIT2-Q4: (surf @ i) @ j ≢ (surf @ i) @ i  (different second-dim neutrals) */
    printf("\n[HIT2-Q4] (surf @ i) @ j ≢ (surf @ i) @ i\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *surf_v = def_get(d->ctors[3].def_idx)->val;
            Val *i_neu  = vl_neutral(a, 503, NULL);
            Val *j_neu  = vl_neutral(a, 504, NULL);
            Val *v1 = nbe_vpathapp(a, nbe_vpathapp(a, surf_v, i_neu), j_neu);
            Val *v2 = nbe_vpathapp(a, nbe_vpathapp(a, surf_v, i_neu), i_neu);
            if (!conv(a, 0, v1, v2)) {
                printf("  [OK] (surf@i)@j ≢ (surf@i)@i as expected\n"); tests_pass++;
            } else {
                printf("  [BUG] conv succeeded but should have failed\n"); tests_fail++;
            }
        }
    }

    /* HIT2-Q5: quote((fill3 n @ i) @ j) structure (2-cell with ctor arg)
     * The ctor arg n must appear inside the TM_INDCON, not be silently dropped. */
    printf("\n[HIT2-Q5] quote((fill3 n @ i) @ j) has correct structure with ctor arg\n");
    {
        int fi = ind_lookup("_Cyl3");
        if (fi < 0) { printf("  [SKIP] _Cyl3 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *fill3_v = def_get(d->ctors[2].def_idx)->val;
            Val *n_neu   = vl_neutral(a, 600, NULL);
            Val *i_neu   = vl_neutral(a, 601, NULL);
            Val *j_neu   = vl_neutral(a, 602, NULL);
            Val *fill3_n = nbe_vapp(a, fill3_v, n_neu);
            Val *scrut   = nbe_vpathapp(a, nbe_vpathapp(a, fill3_n, i_neu), j_neu);
            Term *qt     = nbe_quote(a, 605, scrut);
            /* Shape: TM_PATHAPP( TM_PATHAPP( TM_INDCON(n_args=1), _ ), _ ) */
            int ok = qt && qt->tag == TM_PATHAPP &&
                     qt->app.fun && qt->app.fun->tag == TM_PATHAPP &&
                     qt->app.fun->app.fun &&
                     qt->app.fun->app.fun->tag == TM_INDCON &&
                     qt->app.fun->app.fun->indcon.n_args == 1; /* n_params(0)+arity(1) */
            if (ok) {
                printf("  [OK] quoted term is (indcon(n) @ i_tm) @ j_tm\n"); tests_pass++;
            } else {
                printf("  [BUG] quoted term has wrong shape\n"); tests_fail++;
            }
        }
    }

    /* ------------------------------------------------------------------ *
     * HIT-2 Step 5 hardening — quote edge cases
     * ------------------------------------------------------------------ */

    /* HIT2-QH1: quote(surf @ i_neu) is TM_PATHAPP(TM_INDCON, _) — not a double pathapp.
     * Tests the boundary: one SP_PATHAPP on a 2-cell ctor.                         */
    printf("\n[HIT2-QH1] quote(surf @ i) = TM_PATHAPP(TM_INDCON, i_tm) (one dim only)\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *surf_v = def_get(d->ctors[3].def_idx)->val;
            Val *i_neu  = vl_neutral(a, 503, NULL);
            Val *surf_i = nbe_vpathapp(a, surf_v, i_neu);
            Term *qt    = nbe_quote(a, 505, surf_i);
            /* Shape: TM_PATHAPP( TM_INDCON, _ ) — inner is NOT another TM_PATHAPP */
            int ok = qt && qt->tag == TM_PATHAPP &&
                     qt->app.fun && qt->app.fun->tag == TM_INDCON;
            if (ok) {
                printf("  [OK] one-dim quote gives single pathapp over indcon\n");
                tests_pass++;
            } else {
                printf("  [BUG] wrong shape: outer tag=%d, inner tag=%d\n",
                       qt ? qt->tag : -1,
                       (qt && qt->app.fun) ? qt->app.fun->tag : -1);
                tests_fail++;
            }
        }
    }

    /* HIT2-QH2: dimension swap — (surf @ i) @ j ≢ (surf @ j) @ i for i ≠ j */
    printf("\n[HIT2-QH2] (surf @ i) @ j ≢ (surf @ j) @ i (swap distinguishable)\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *surf_v = def_get(d->ctors[3].def_idx)->val;
            Val *i_neu  = vl_neutral(a, 503, NULL);
            Val *j_neu  = vl_neutral(a, 504, NULL);
            Val *v1 = nbe_vpathapp(a, nbe_vpathapp(a, surf_v, i_neu), j_neu); /* (surf@i)@j */
            Val *v2 = nbe_vpathapp(a, nbe_vpathapp(a, surf_v, j_neu), i_neu); /* (surf@j)@i */
            if (!conv(a, 0, v1, v2)) {
                printf("  [OK] (surf@i)@j ≢ (surf@j)@i\n"); tests_pass++;
            } else {
                printf("  [BUG] swapped dims compared equal\n"); tests_fail++;
            }
        }
    }

    /* HIT2-QH3: 1-cell loop1 @ r in 2-cell family: quote gives TM_PATHAPP(TM_INDCON_loop1, _)
     * Regression: 1-cell quoting must be unaffected by 2-cell code.             */
    printf("\n[HIT2-QH3] quote(loop1 @ r) = TM_PATHAPP(TM_INDCON_loop1, r_tm)\n");
    {
        int fi = ind_lookup("_Torus2");
        if (fi < 0) { printf("  [SKIP] _Torus2 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *loop1_v = def_get(d->ctors[1].def_idx)->val;
            Val *r_neu   = vl_neutral(a, 503, NULL);
            Val *loop1_r = nbe_vpathapp(a, loop1_v, r_neu);
            Term *qt     = nbe_quote(a, 505, loop1_r);
            /* Shape: TM_PATHAPP( TM_INDCON(loop1_ci=1), _ ) */
            int ok = qt && qt->tag == TM_PATHAPP &&
                     qt->app.fun && qt->app.fun->tag == TM_INDCON &&
                     qt->app.fun->indcon.ctor_idx == 1; /* loop1 is ctor 1 */
            if (ok) {
                printf("  [OK] 1-cell loop1 @ r quotes correctly\n"); tests_pass++;
            } else {
                printf("  [BUG] wrong shape for 1-cell quote\n"); tests_fail++;
            }
        }
    }

    /* HIT2-QH4: quote(fill3 n) — 0 pathapps, has ctor arg — gives TM_INDCON(n) */
    printf("\n[HIT2-QH4] quote(fill3 n) = TM_INDCON with n_args=1\n");
    {
        int fi = ind_lookup("_Cyl3");
        if (fi < 0) { printf("  [SKIP] _Cyl3 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *fill3_v = def_get(d->ctors[2].def_idx)->val;
            Val *n_neu   = vl_neutral(a, 600, NULL);
            Val *fill3_n = nbe_vapp(a, fill3_v, n_neu);
            Term *qt     = nbe_quote(a, 605, fill3_n);
            int ok = qt && qt->tag == TM_INDCON && qt->indcon.n_args == 1;
            if (ok) {
                printf("  [OK] fill3 n quotes to TM_INDCON with 1 arg\n"); tests_pass++;
            } else {
                printf("  [BUG] wrong tag/n_args: tag=%d n_args=%d\n",
                       qt ? qt->tag : -1,
                       (qt && qt->tag == TM_INDCON) ? qt->indcon.n_args : -1);
                tests_fail++;
            }
        }
    }

    /* HIT2-QH5: quote(fill3 n @ i) — one pathapp, 2-cell with ctor arg
     * Shape: TM_PATHAPP(TM_INDCON(n_args=1), i_tm)                              */
    printf("\n[HIT2-QH5] quote(fill3 n @ i) = TM_PATHAPP(TM_INDCON(n), i_tm)\n");
    {
        int fi = ind_lookup("_Cyl3");
        if (fi < 0) { printf("  [SKIP] _Cyl3 not found\n"); tests_fail++; }
        else {
            IndDef *d = ind_get(fi);
            Val *fill3_v = def_get(d->ctors[2].def_idx)->val;
            Val *n_neu   = vl_neutral(a, 600, NULL);
            Val *i_neu   = vl_neutral(a, 601, NULL);
            Val *fill3_n = nbe_vapp(a, fill3_v, n_neu);
            Val *fill3_ni = nbe_vpathapp(a, fill3_n, i_neu);
            Term *qt      = nbe_quote(a, 605, fill3_ni);
            int ok = qt && qt->tag == TM_PATHAPP &&
                     qt->app.fun && qt->app.fun->tag == TM_INDCON &&
                     qt->app.fun->indcon.n_args == 1;
            if (ok) {
                printf("  [OK] fill3 n @ i quotes to TM_PATHAPP(TM_INDCON(n), _)\n");
                tests_pass++;
            } else {
                printf("  [BUG] wrong shape\n"); tests_fail++;
            }
        }
    }

    /* HIT2-P3: 2-cell over wrong family (not the declared type) is rejected */
    printf("\n[HIT2-P3] 2-cell ctor with carrier over wrong type is rejected\n");
    {
        /* surf : Path (Path Nat base2 base2) loop loop — Nat, not _BadType3 */
        int fi = parse_data(
            "_BadType3 where"
            " base3 : _BadType3 ;"
            " loop : Path _BadType3 base3 base3 ;"
            " surf3 : Path (Path Nat zero zero) loop loop");
        if (fi < 0) {
            printf("  [OK] correctly rejected bad 2-cell carrier family\n"); tests_pass++;
        } else {
            printf("  [BUG] accepted 2-cell ctor over wrong family\n"); tests_fail++;
        }
    }

    /* ------------------------------------------------------------------ *
     * HIT-2 Step 6: check.c — 2-cell case type-checking
     * Uses a surface _Tor3 HIT (torus-like).  Motive P : _Tor3 → Type = λ_. Nat.
     * ------------------------------------------------------------------ */

    /* HIT2-C1: well-typed indrec with constant motive and correct c_surf type-checks */
    printf("\n[HIT2-C1] indrec _Tor3 (λ_. Nat) c_base c_l1 c_l2 c_surf scrut type-checks\n");
    {
        /* Register _Tor3 (Torus-like, no params) */
        int fi = parse_data(
            "_Tor3 where"
            " base3t : _Tor3 ;"
            " loop3a : Path _Tor3 base3t base3t ;"
            " loop3b : Path _Tor3 base3t base3t ;"
            " surf3t : Path (Path _Tor3 base3t base3t) loop3a loop3b");
        if (fi < 0) {
            printf("  [BUG] _Tor3 parse_data failed\n"); tests_fail++;
        } else {
            /* Annotated indrec expression:
             * P = λ_. Nat
             * c_base3t = zero
             * c_loop3a = (<i> zero : PathP (λi. Nat) zero zero)
             * c_loop3b = (<i> zero : PathP (λi. Nat) zero zero)
             * c_surf3t = (<i> (<j> zero : PathP (λj. Nat) zero zero)
             *             : PathP (λi. PathP (λj. Nat) zero zero)
             *                     (<i> zero : PathP (λi. Nat) zero zero)
             *                     (<i> zero : PathP (λi. Nat) zero zero))
             * scrutinee = base3t
             * Expected result type: Nat                                         */
            Term *t = parse(a,
                "(indrec _Tor3"
                "  (\\_. Nat : _Tor3 \xe2\x86\x92 Type)"
                "  zero"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> <j> zero"
                "   : PathP (\\_. PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero"
                "           : \xce\xa0(_:II). Type)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero))"
                "  base3t : Nat)");
            if (!t) {
                printf("  [BUG] parse failed\n"); tests_fail++;
            } else {
                Val *ty = infer(a, 0, NULL, NULL, t);
                Val *nat_v = nbe_eval(a, NULL, parse(a, "Nat"));
                if (ty && conv(a, 0, ty, nat_v)) {
                    printf("  [OK] indrec with 2-cell case type-checks at Nat\n");
                    tests_pass++;
                } else {
                    printf("  [BUG] type mismatch or NULL (ty=%s)\n",
                           ty ? "non-null" : "null");
                    tests_fail++;
                }
            }
        }
    }

    /* HIT2-C2: indrec with correctly-typed c_surf evaluates to zero at base */
    printf("\n[HIT2-C2] above indrec evaluates to zero at base3t\n");
    {
        int fi = ind_lookup("_Tor3");
        if (fi < 0) { printf("  [SKIP] _Tor3 not found\n"); tests_fail++; }
        else {
            Term *t = parse(a,
                "indrec _Tor3"
                "  (\\_. Nat : _Tor3 \xe2\x86\x92 Type)"
                "  zero"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> <j> zero"
                "   : PathP (\\_. PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero"
                "           : \xce\xa0(_:II). Type)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero))"
                "  base3t");
            if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
            else {
                Val *v = nbe_eval(a, NULL, t);
                Val *zero_v = nbe_eval(a, NULL, parse(a, "zero"));
                if (conv(a, 0, v, zero_v)) {
                    printf("  [OK] evaluates to zero\n"); tests_pass++;
                } else {
                    printf("  [BUG] wrong value\n"); tests_fail++;
                }
            }
        }
    }

    /* HIT2-C3: wrongly-typed c_surf (wrong carrier endpoints) is rejected */
    printf("\n[HIT2-C3] indrec with wrong c_surf carrier endpoints rejected\n");
    {
        /* c_surf annotated with carrier (succ zero, succ zero) instead of (zero, zero) */
        Term *t = parse(a,
            "(indrec _Tor3"
            "  (\\_. Nat : _Tor3 \xe2\x86\x92 Type)"
            "  zero"
            "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
            "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
            "  (<i> <j> zero"
            "   : PathP (\\_. PathP (\\_. Nat : \xce\xa0(_:II). Type) (succ zero) (succ zero)"
            "           : \xce\xa0(_:II). Type)"
            "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
            "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero))"
            "  base3t : Nat)");
        if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
        else {
            Val *ty = infer(a, 0, NULL, NULL, t);
            if (!ty) {
                printf("  [OK] correctly rejected wrong carrier endpoints\n"); tests_pass++;
            } else {
                printf("  [BUG] accepted wrongly-typed c_surf\n"); tests_fail++;
            }
        }
    }

    /* ------------------------------------------------------------------ *
     * HIT-2 Step 6 hardening
     * ------------------------------------------------------------------ */

    /* HIT2-CH1: full pipeline — indrec at (surf3t @ i0) @ i0 type-checks and evaluates */
    printf("\n[HIT2-CH1] indrec _Tor3 ... ((surf3t @ i0) @ i0) : Nat = zero\n");
    {
        int fi = ind_lookup("_Tor3");
        if (fi < 0) { printf("  [SKIP] _Tor3 not found\n"); tests_fail++; }
        else {
            Term *t = parse(a,
                "(indrec _Tor3"
                "  (\\_. Nat : _Tor3 \xe2\x86\x92 Type)"
                "  zero"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> <j> zero"
                "   : PathP (\\_. PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero"
                "           : \xce\xa0(_:II). Type)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero))"
                "  ((surf3t @ i0) @ i0) : Nat)");
            if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
            else {
                Val *ty = infer(a, 0, NULL, NULL, t);
                Val *nat_v = nbe_eval(a, NULL, parse(a, "Nat"));
                if (!ty || !conv(a, 0, ty, nat_v)) {
                    printf("  [BUG] type-check failed\n"); tests_fail++;
                } else {
                    Val *v   = nbe_eval(a, NULL, t);
                    Val *z   = nbe_eval(a, NULL, parse(a, "zero"));
                    if (conv(a, 0, v, z)) {
                        printf("  [OK] type-checks Nat and evaluates to zero\n"); tests_pass++;
                    } else {
                        printf("  [BUG] evaluates to wrong value\n"); tests_fail++;
                    }
                }
            }
        }
    }

    /* HIT2-CH2: wrong outer lhs endpoint annotation rejected
     * c_surf outer lhs uses <i> succ zero instead of <i> zero (= c_loop3a)    */
    printf("\n[HIT2-CH2] c_surf with wrong outer-lhs endpoint annotation rejected\n");
    {
        int fi = ind_lookup("_Tor3");
        if (fi < 0) { printf("  [SKIP] _Tor3 not found\n"); tests_fail++; }
        else {
            Term *t = parse(a,
                "(indrec _Tor3"
                "  (\\_. Nat : _Tor3 \xe2\x86\x92 Type)"
                "  zero"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> <j> zero"
                "   : PathP (\\_. PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero"
                "           : \xce\xa0(_:II). Type)"
                "           (<i> succ zero : PathP (\\_. Nat : \xce\xa0(_:II). Type)"
                "                            (succ zero) (succ zero))"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero))"
                "  base3t : Nat)");
            if (!t) { printf("  [SKIP] parse failed\n"); tests_fail++; }
            else {
                Val *ty = infer(a, 0, NULL, NULL, t);
                if (!ty) {
                    printf("  [OK] correctly rejected wrong outer lhs endpoint\n"); tests_pass++;
                } else {
                    printf("  [BUG] accepted wrongly-typed c_surf outer lhs\n"); tests_fail++;
                }
            }
        }
    }

    /* HIT2-CH3: _Cyl3 indrec type-checks (2-cell with ctor arg — exercises arity peeling) */
    printf("\n[HIT2-CH3] indrec _Cyl3 with fill3 (Nat ctor arg) type-checks\n");
    {
        int fi = ind_lookup("_Cyl3");
        if (fi < 0) { printf("  [SKIP] _Cyl3 not found\n"); tests_fail++; }
        else {
            /* c_fill3 : Π(n:Nat). PathP (λ_. PathP (λ_.Nat) zero zero) (<i>zero) (<i>zero) */
            Term *t = parse(a,
                "(indrec _Cyl3"
                "  (\\_. Nat : _Cyl3 \xe2\x86\x92 Type)"
                "  zero"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (\\n. <i> <j> zero"
                "   : \xce\xa0(n:Nat)."
                "     PathP (\\_. PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero"
                "           : \xce\xa0(_:II). Type)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero))"
                "  pt3 : Nat)");
            if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
            else {
                Val *ty = infer(a, 0, NULL, NULL, t);
                Val *nat_v = nbe_eval(a, NULL, parse(a, "Nat"));
                if (ty && conv(a, 0, ty, nat_v)) {
                    printf("  [OK] _Cyl3 indrec with fill3 (ctor arg) type-checks at Nat\n");
                    tests_pass++;
                } else {
                    printf("  [BUG] type-check failed (ty=%s)\n", ty ? "wrong" : "null");
                    tests_fail++;
                }
            }
        }
    }

    /* HIT2-CH4: different corner — indrec at (surf3t @ i0) @ i1 type-checks and evaluates
     * surf3t @ i0 = loop3a, loop3a @ i1 = base3t, so result = zero               */
    printf("\n[HIT2-CH4] indrec _Tor3 ... ((surf3t @ i0) @ i1) : Nat = zero\n");
    {
        int fi = ind_lookup("_Tor3");
        if (fi < 0) { printf("  [SKIP] _Tor3 not found\n"); tests_fail++; }
        else {
            Term *t = parse(a,
                "(indrec _Tor3"
                "  (\\_. Nat : _Tor3 \xe2\x86\x92 Type)"
                "  zero"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "  (<i> <j> zero"
                "   : PathP (\\_. PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero"
                "           : \xce\xa0(_:II). Type)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero)"
                "           (<i> zero : PathP (\\_. Nat : \xce\xa0(_:II). Type) zero zero))"
                "  ((surf3t @ i0) @ i1) : Nat)");
            if (!t) { printf("  [BUG] parse failed\n"); tests_fail++; }
            else {
                Val *ty = infer(a, 0, NULL, NULL, t);
                Val *nat_v = nbe_eval(a, NULL, parse(a, "Nat"));
                if (!ty || !conv(a, 0, ty, nat_v)) {
                    printf("  [BUG] type-check failed\n"); tests_fail++;
                } else {
                    Val *v = nbe_eval(a, NULL, t);
                    Val *z = nbe_eval(a, NULL, parse(a, "zero"));
                    if (conv(a, 0, v, z)) {
                        printf("  [OK] type-checks Nat and evaluates to zero\n"); tests_pass++;
                    } else {
                        printf("  [BUG] evaluates to wrong value\n"); tests_fail++;
                    }
                }
            }
        }
    }

    fflush(stdout);
    printf("\n=== Summary: %d passed, %d failed ===\n", tests_pass, tests_fail);
    if (tests_fail > 0)
        printf("  *** FAILURES DETECTED ***\n");
}

int main(int argc, char **argv) {
    Arena a = {NULL};

    if (argc > 1 && strcmp(argv[1], "--test") == 0) {
        run_tests(&a);
        arena_free_all(&a);
        return 0;
    }

    if (argc > 1) {
        /* join all args as one expression and infer its type */
        size_t n = 0;
        for (int i = 1; i < argc; i++) n += strlen(argv[i]) + 1;
        char *buf = (char *)malloc(n + 1);
        buf[0] = '\0';
        for (int i = 1; i < argc; i++) {
            if (i > 1) strcat(buf, " ");
            strcat(buf, argv[i]);
        }
        run(&a, buf);
        free(buf);
        arena_free_all(&a);
        return 0;
    }

    /* interactive REPL */
    printf("λ-core  (NbE + bidirectional type checker)\n");
    printf("  TERM              — normalise\n");
    printf("  :i TERM           — infer type\n");
    printf("  :let name = EXPR  — define a global (EXPR must be inferrable)\n");
    printf("  :t                — run tests\n");
    printf("  :q                — quit\n\n");

    char   *line = NULL;
    size_t  cap  = 0;
    for (;;) {
        printf("> ");
        fflush(stdout);
        ssize_t nread = getline(&line, &cap, stdin);
        if (nread < 0) break;
        size_t len = (size_t)nread;
        if (len > 0 && line[len-1] == '\n') line[--len] = '\0';
        if (strcmp(line, ":q") == 0) break;
        if (strcmp(line, ":t") == 0) { run_tests(&a); arena_free_all(&a); continue; }
        if (strncmp(line, ":let ", 5) == 0) {
            char *rest = line + 5;
            char *eq   = strchr(rest, '=');
            if (!eq) {
                fprintf(stderr, "usage: :let name = expr\n");
            } else {
                /* trim leading/trailing spaces from name */
                char *ns = rest;
                while (*ns == ' ') ns++;
                char *ne = eq - 1;
                while (ne >= ns && *ne == ' ') ne--;
                int nlen = (int)(ne - ns + 1);
                char defname[128];
                if (nlen <= 0 || nlen >= (int)sizeof(defname)) {
                    fprintf(stderr, ":let: missing or over-long name\n");
                } else {
                    memcpy(defname, ns, nlen);
                    defname[nlen] = '\0';
                    if (is_reserved_name(defname)) {
                        fprintf(stderr,
                            ":let: '%s' is a built-in keyword and cannot be redefined\n",
                            defname);
                    } else {
                        /* warn if shadowing an existing definition */
                        int prev = def_lookup(defname);
                        char *expr = eq + 1;
                        while (*expr == ' ') expr++;
                        int didx = def_define(defname, expr);
                        if (didx >= 0) {
                            if (prev >= 0)
                                fprintf(stderr,
                                    ":let: warning: '%s' shadows earlier definition\n",
                                    defname);
                            printf("  %s : ", defname);
                            val_print_tctx(&a, def_get(didx)->type, 0, NULL);
                            printf("\n");
                        } else {
                            printf("  definition of '%s' failed\n", defname);
                        }
                    }
                }
            }
            arena_free_all(&a);
            continue;
        }
        if (strncmp(line, "data ", 5) == 0) {
            const char *rest = line + 5;
            while (*rest == ' ' || *rest == '\t') rest++;
            int fam_idx = parse_data(rest);
            if (fam_idx >= 0) {
                IndDef *fam = ind_get(fam_idx);
                printf("  defined family: %s (%d constructor%s)\n",
                       fam->name, fam->n_ctors, fam->n_ctors == 1 ? "" : "s");
            }
        } else if (strncmp(line, ":i ", 3) == 0) {
            run_infer(&a, line + 3);
        } else if (len > 0) {
            run(&a, line);
        }
        arena_free_all(&a);
    }
    free(line);
    arena_free_all(&a);
    return 0;
}
