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

/* ── normalize and print */

static void run(Arena *a, const char *src) {
    Term *t = parse(a, src);
    if (!t) return;
    printf("  parsed : "); term_print(t); printf("\n");
    Term *nf = nbe_nf(a, t);
    printf("  normal : "); term_print(nf); printf("\n");
}

/* ── infer type and print */

static void run_infer(Arena *a, const char *src) {
    Term *t = parse(a, src);
    if (!t) return;
    printf("  term   : "); term_print(t); printf("\n");
    Val *ty = infer(a, 0, NULL, NULL, t);
    if (!ty) return;
    printf("  type   : "); val_print_tctx(a, ty, 0, NULL); printf("\n");
    /* also normalize the term itself */
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

    /* FE3: fully applied to neutral proof — stays stuck */
    printf("\n[FE3] funext applied to neutral proof stays stuck\n");
    run_infer(a,
        "(\\ A B f g h."
        "  funext A B f g h"
        " : Π(A : Type). Π(B : Π(_ : A). Type)."
        "   Π(f : Π(x : A). B x). Π(g : Π(x : A). B x)."
        "   Π(h : Π(x : A). Id (B x) (f x) (g x))."
        "   Id (Π(x : A). B x) f g)");

    /* FE4: conv — funext equal to itself, different args unequal */
    printf("\n[FE4] conv tests\n");
    expect_conv(a, "funext", "funext", 1);
    expect_conv(a, "funext Nat", "funext Nat", 1);
    expect_conv(a, "funext Nat", "funext Bool", 0);

    /* FE5: negative — B must be a fibration A→Type, not a term */
    printf("\n[FE5] negative: funext with non-fibration B\n");
    expect_fail(a, "funext Nat zero", "zero is not a fibration Nat → Type");

    /* FE6: non-dependent fibration (B = λ_.Nat): Id-argument types β-reduce to Nat */
    printf("\n[FE6] non-dependent funext (B=λ_.Nat) typechecks\n");
    run_infer(a,
        "(\\ f g h. funext Nat (\\_. Nat) f g h"
        " : Π(f : Π(_ : Nat). Nat). Π(g : Π(_ : Nat). Nat)."
        "   Π(h : Π(x : Nat). Id Nat (f x) (g x))."
        "   Id (Π(_ : Nat). Nat) f g)");

    /* FE7: funext is a pure axiom — stays neutral, never computes to refl */
    printf("\n[FE7] funext ≢ refl: no computation rule\n");
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

    /* FE11: h must be a pointwise Id proof, not a Nat→Nat function */
    printf("\n[FE11] negative: h with type Nat→Nat instead of Nat→Id rejected\n");
    expect_fail(a,
        "(\\ f. funext Nat (\\_. Nat) f f f"
        " : Π(f : Π(_ : Nat). Nat). Id (Π(_ : Nat). Nat) f f)",
        "h : Nat→Nat instead of Nat→Id Nat (f x) (f x)");

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
        if (strncmp(line, ":i ", 3) == 0) {
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
