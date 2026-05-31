/* presburger.c
 *
 * Presburger arithmetic: linear constraints over natural numbers.
 *
 * Three levels of sophistication:
 *   1. Direct evaluation of ground (variable-free) constraints
 *   2. Bounded existential search: try x = 0, 1, ..., SEARCH_MAX
 *   3. Cooper equality elimination: O(1) check for  exists x. a*x = c
 *
 * Compile:  cc -std=c99 -o presburger presburger.c
 * Run:      ./presburger
 */

#include <stdio.h>
#include <stdbool.h>
#include <string.h>

#define MAX_VARS    8
#define SEARCH_MAX  1000


/* Terms and constraints */

/* A linear term:  coeffs[0]*x0 + coeffs[1]*x1 + ... + constant      */
typedef struct {
    int coeffs[MAX_VARS];
    int constant;
} LinTerm;

typedef enum { REL_EQ, REL_LT, REL_LE } Rel;

typedef struct {
    LinTerm lhs;
    Rel     rel;
    LinTerm rhs;
} LinConstraint;



/* Evaluation */

static int eval_term(const LinTerm *t, const int env[MAX_VARS]) {
    int v = t->constant;
    for (int i = 0; i < MAX_VARS; i++)
        v += t->coeffs[i] * env[i];
    return v;
}

static bool eval_constraint(const LinConstraint *c, const int env[MAX_VARS]) {
    int l = eval_term(&c->lhs, env);
    int r = eval_term(&c->rhs, env);
    switch (c->rel) {
        case REL_EQ: return l == r;
        case REL_LT: return l <  r;
        case REL_LE: return l <= r;
    }
    return false;
}

static bool eval_all(const LinConstraint cs[], int n, const int env[MAX_VARS]) {
    for (int i = 0; i < n; i++)
        if (!eval_constraint(&cs[i], env))
            return false;
    return true;
}


/* Bounded existential search
 *
 * Decides  exists x[idx] in [0, SEARCH_MAX].  cs[0] /\ ... /\ cs[n-1]
 * by brute force. Sound but incomplete for witnesses above SEARCH_MAX. */

static bool exists_bounded(const LinConstraint cs[], int n,
                            int idx, int env[MAX_VARS], int *witness)
{
    for (int v = 0; v <= SEARCH_MAX; v++) {
        env[idx] = v;
        if (eval_all(cs, n, env)) {
            if (witness) *witness = v;
            return true;
        }
    }
    env[idx] = 0;
    return false;
}


/* Cooper equality elimination
 *
 * Decides  exists x in N. (a*x = c)  in O(1) then no search needed.
 *
 * This is the base case of Cooper's algorithm: when the quantified
 * variable appears only in an equality a*x = c, we can eliminate it
 * analytically.  A natural-number solution exists iff:
 *   (i)  a != 0
 *   (ii) a divides c
 *   (iii) c/a >= 0
 */

static bool cooper_eq(int a, int c, int *witness) {
    if (a == 0)       return c == 0;   /* degenerate: 0*x = c */
    if (c % a != 0)   return false;    /* divisibility check */
    int x = c / a;
    if (x < 0)        return false;    /* natural numbers: x >= 0 */
    if (witness) *witness = x;
    return true;
}


/* Divisibility predicate: d | v
 *
 * A core primitive in Presburger arithmetic: divisibility constraints
 * arise naturally during Cooper's quantifier elimination and capture
 * modular/periodic properties.
 */

static bool divides(int d, int v) {
    return d != 0 && v % d == 0;
}


/* Loop-access safety
 *
 * Checks: forall i in [0, n).  a*i + b < size
 *
 * A typical Presburger query in compiler and verifier contexts: prove
 * that every loop iteration accesses within array bounds.
 * For coefficient a > 0 the worst case is i = n-1.
 */

static bool loop_access_safe(int a, int b, int n, int size) {
    if (n <= 0) return true;
    return a * (n - 1) + b < size;
}


/* Demos */

int main(void) {
    int env[MAX_VARS];
    int witness = 0;

    printf("=== Presburger Arithmetic in C ===\n\n");


    /* --- 1. Ground evaluation */
    printf("1. Ground evaluation\n");
    memset(env, 0, sizeof env);

    LinConstraint g = { .lhs = { .constant = 5 },
                        .rel = REL_EQ,
                        .rhs = { .constant = 5 } };
    printf("   5 = 5  :  %s\n", eval_constraint(&g, env) ? "true" : "false");
    g.rhs.constant = 6;
    printf("   5 = 6  :  %s\n\n", eval_constraint(&g, env) ? "true" : "false");


    /* --- 2. Bounded existential search */
    printf("2. Bounded existential search\n");
    memset(env, 0, sizeof env);

    /* exists x[0]. 2*x[0] = 6 */
    LinConstraint e = { .lhs = { .coeffs = {[0]=2}, .constant = 0 },
                        .rel = REL_EQ,
                        .rhs = { .constant = 6 } };
    bool ok = exists_bounded(&e, 1, 0, env, &witness);
    printf("   ex x. 2x = 6  :  %s  (x = %d)\n", ok ? "true" : "false", witness);

    e.rhs.constant = 7;
    memset(env, 0, sizeof env);
    ok = exists_bounded(&e, 1, 0, env, &witness);
    printf("   ex x. 2x = 7  :  %s\n\n", ok ? "true" : "false");


    /* --- 3. Cooper equality elimination */
    printf("3. Cooper equality elimination  (O(1), no search)\n");
    ok = cooper_eq(2, 6, &witness);
    printf("   ex x. 2x = 6  :  %s  (x = %d)\n", ok ? "true" : "false", witness);
    ok = cooper_eq(2, 7, NULL);
    printf("   ex x. 2x = 7  :  %s  (7 not divisible by 2)\n", ok ? "true" : "false");
    ok = cooper_eq(3, 9, &witness);
    printf("   ex x. 3x = 9  :  %s  (x = %d)\n\n", ok ? "true" : "false", witness);


    /* --- 4. Divisibility predicates */
    printf("4. Divisibility predicates\n");
    printf("   2 | 8  :  %s\n", divides(2, 8) ? "true" : "false");
    printf("   2 | 7  :  %s\n", divides(2, 7) ? "true" : "false");
    printf("   3 | 9  :  %s\n", divides(3, 9) ? "true" : "false");

    /* Periodicity: every n has remainder 0, 1, or 2 when divided by 3 */
    printf("   forall x in 0..9: x mod 3 in {0,1,2} -> ");
    bool all_ok = true;
    for (int x = 0; x < 10; x++) {
        int r = x % 3;
        if (r != 0 && r != 1 && r != 2) { all_ok = false; break; }
    }
    printf("%s\n\n", all_ok ? "true" : "false");


    /* --- 5. Loop-access safety */
    printf("5. Loop-access safety\n");
    printf("   for (i = 0; i < n; i++) a[2*i + 1] = b[i];\n");

    int n, size;
    n = 10; size = 22;
    printf("   n=%2d, array size=%2d, max index=%2d  ->  %s\n", n, size, 2*(n-1)+1, loop_access_safe(2, 1, n, size) ? "SAFE" : "UNSAFE");
    n = 10; size = 19;
    printf("   n=%2d, array size=%2d, max index=%2d  ->  %s\n\n", n, size, 2*(n-1)+1, loop_access_safe(2, 1, n, size) ? "SAFE" : "UNSAFE");


    /* --- 6. Conjunction: exists x y. x+y=10 /\ x>3 */
    printf("6. Conjunction: ex x y. x+y=10  /\\  x>3\n");

    LinConstraint conj[2];
    memset(conj, 0, sizeof conj);

    /* x[0] + x[1] = 10 */
    conj[0].lhs.coeffs[0] = 1;
    conj[0].lhs.coeffs[1] = 1;
    conj[0].rel            = REL_EQ;
    conj[0].rhs.constant   = 10;

    /* 3 < x[0],  written as  lhs=3, rel=LT, rhs=x[0] */
    conj[1].lhs.constant   = 3;
    conj[1].rel            = REL_LT;
    conj[1].rhs.coeffs[0]  = 1;

    memset(env, 0, sizeof env);
    bool found = false;
    for (int x0 = 0; x0 <= 10 && !found; x0++) {
        env[0] = x0;
        env[1] = 10 - x0;
        if (env[1] >= 0 && eval_all(conj, 2, env)) {
            printf("   first solution: x = %d, y = %d\n", env[0], env[1]);
            found = true;
        }
    }
    if (!found) printf("   no solution\n");

    return 0;
}
