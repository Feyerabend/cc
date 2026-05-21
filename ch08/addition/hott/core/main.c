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
        NULL
    };
    for (int i = 0; kw[i]; i++)
        if (strcmp(n, kw[i]) == 0) return 1;
    if (strncmp(n, "Type", 4) == 0 && n[4] == '_') return 1;
    return 0;
}

/* ── built-in test suite */

/* ── expect a type error (negative test) */

static void expect_fail(Arena *a, const char *src, const char *reason) {
    Term *t = parse(a, src);
    if (!t) {
        printf("  [FAIL-PARSE unexpected] %s\n", src);
        return;
    }
    Val *ty = infer(a, 0, NULL, NULL, t);
    if (ty) {
        printf("  [BUG: should have failed] %s  — %s\n", src, reason);
        printf("    got type: "); term_print(nbe_quote(a, 0, ty)); printf("\n");
    } else {
        printf("  [REJECTED OK] %s\n", src);
    }
}

/* ── conv equality check */

static void expect_conv(Arena *a, const char *sa, const char *sb, int should_equal) {
    Term *ta = parse(a, sa);
    Term *tb = parse(a, sb);
    if (!ta || !tb) { printf("  [FAIL-PARSE] %s  ~  %s\n", sa, sb); return; }
    Val *va = nbe_eval(a, NULL, ta);
    Val *vb = nbe_eval(a, NULL, tb);
    int eq = conv(a, 0, va, vb);
    if (eq == should_equal) {
        printf("  [OK] %s  %s  %s\n", sa, eq ? "≡" : "≢", sb);
    } else {
        printf("  [BUG] %s  expected %s  %s\n",
               sa, should_equal ? "≡" : "≢", sb);
    }
}

static void run_tests(Arena *a) {
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
