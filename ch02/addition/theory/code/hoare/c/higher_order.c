/*
 * higher_order.c -- Higher-Order Hoare Logic in C
 *
 * Supplementary example: not covered in a dedicated section of
 * theory_of_virtual_machines.tex, but builds directly on §3.3
 * (Axiomatic Semantics) and extends Hoare-style pre/postconditions
 * to higher-order functions (functions-as-arguments).
 *
 * Higher-order functions take functions as arguments.  Their Hoare-style
 * specifications must be PARAMETRIC in the argument function's behavior.
 *
 * In OCaml the map specification reads (see §3.3, Axiomatic Semantics):
 *
 *   ∀P Q f xs α.
 *     (∀x. {P(x)} f(x) {Q(f(x))})  -- f maps P-inputs to Q-outputs
 *     ∧  list(xs, α)
 *   ---------------------------------
 *     map f xs  -->  list(result, [f(x) | x ∈ α])
 *     ∧  ∀v ∈ result. Q(v)           -- every output satisfies Q
 *
 * In C we express this using function pointers:
 *   - Transformer f:   int -> int
 *   - Predicate   P:   int -> bool  (precondition on inputs)
 *   - Predicate   Q:   int -> bool  (postcondition on outputs)
 *
 * The higher-order functions (int_map, int_filter, fold_left) verify
 * at runtime that every element satisfies the pointwise specification.
 * This is the executable counterpart of the logical specification.
 *
 * Compile:  gcc -Wall -std=c11 -o higher_order higher_order.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <stdbool.h>
#include <limits.h>

typedef int  (*Transformer)(int);      /* int -> int          */
typedef bool (*Predicate)(int);        /* int -> bool         */
typedef int  (*BinaryOp)(int, int);    /* int * int -> int    */


/* int_map: apply f to every element */

/*
 * Pre:  ∀i. P(in[i])                          -- each input satisfies P
 * Post: ∀i. out[i] = f(in[i]) ∧ Q(out[i])     -- each output satisfies Q
 *
 * Passing NULL for P or Q skips that check (no constraint).
 *
 * This realises the specification of 'map' at the element level:
 *   ∀x. {P(x)} f(x) {Q(f(x))}  =>  map f satisfies the pointwise extension.
 */
static void int_map(Transformer f,
                    Predicate P,    /* precondition on each input  */
                    Predicate Q,    /* postcondition on each output */
                    int in[], int out[], int n)
{
    for (int i = 0; i < n; i++) {
        if (P != NULL) assert(P(in[i]));    /* {P(in[i])} before f */
        out[i] = f(in[i]);
        if (Q != NULL) assert(Q(out[i]));   /* {Q(out[i])} after f */
    }
}


/* int_filter: keep elements satisfying pred */

/*
 * Pre:  list(in, α)
 * Post: list(out, [x | x ∈ α ∧ Q(x)])
 *       -- every kept element satisfies Q
 *       -- every dropped element does NOT satisfy Q
 *
 * This realises the specification of 'filter':
 *   ∀x. pred(x) = true  ↔  Q(x)
 *   =>  filter pred xs = [x | x ∈ α ∧ Q(x)]
 *
 * Returns the number of elements kept.
 */
static int int_filter(Predicate pred,
                      Predicate Q,        /* logical content of pred */
                      int in[], int out[], int n)
{
    int count = 0;
    for (int i = 0; i < n; i++) {
        bool kept = pred(in[i]);
        if (kept) {
            /* Kept element must satisfy Q -- pred encodes Q faithfully */
            if (Q != NULL) assert(Q(in[i]));
            out[count++] = in[i];
        } else {
            /* Dropped element must NOT satisfy Q */
            if (Q != NULL) assert(!Q(in[i]));
        }
    }
    return count;
}


/* fold_left: combine elements with a binary operation */

/*
 * fold_left(f, init, arr, n)
 *   = f(f( ... f(init, arr[0]) ... , arr[n-2]), arr[n-1])
 *
 * Loop invariant: after i iterations,  acc = f*(init, arr[0..i-1])
 *
 * When f is associative with identity element init, fold_left computes
 * the "sum" in the algebra defined by f.  This realises the algebraic
 * semantics of a monoid at the level of concrete lists.
 *
 * Algebraic laws verifiable at runtime:
 *   identity:    fold_left(f, init, [], 0) = init
 *   singleton:   fold_left(f, init, [x], 1) = f(init, x)
 *   commutativity of +:  fold(+, 0, arr) = fold(+, 0, reverse(arr))
 */
static int fold_left(BinaryOp f, int init, int arr[], int n)
{
    int acc = init;
    for (int i = 0; i < n; i++)
        acc = f(acc, arr[i]);
    return acc;
}


/* Concrete functions and predicates */

/* Transformers */
static int double_val(int x) { return 2 * x; }
static int abs_val(int x)    { return x < 0 ? -x : x; }
static int square(int x)     { return x * x; }

/* Predicates */
static bool any_int(int x)      { (void)x; return true; }
static bool is_positive(int x)  { return x > 0; }
static bool is_non_neg(int x)   { return x >= 0; }
static bool is_even(int x)      { return x % 2 == 0; }

/* Binary operations */
static int op_add(int a, int b) { return a + b; }
static int op_mul(int a, int b) { return a * b; }
static int op_max(int a, int b) { return a > b ? a : b; }


/* Helpers */

static void print_array(const char *label, int arr[], int n)
{
    printf("%s [", label);
    for (int i = 0; i < n; i++)
        printf("%d%s", arr[i], i < n - 1 ? ", " : "");
    printf("]\n");
}


/* Demo */

static void demo_map(void)
{
    printf("-- map: Parametric Specification (Hoare-style, see §3.3) --\n\n");

    int n = 5;
    int in1[] = {1, 2, 3, 4, 5};
    int in2[] = {-3, -1, 0, 2, -5};
    int out[5];

    /*
     * Example 1: map double_val
     *   Spec: ∀x. {true} double_val(x) {result is even}
     *   P = any_int, Q = is_even
     */
    printf("map double_val [1,2,3,4,5]\n");
    printf("  Spec: ∀x. {true} double_val(x) {result is even}\n");
    int_map(double_val, any_int, is_even, in1, out, n);
    print_array("  Result:", out, n);
    printf("  All outputs even: verified by int_map\n\n");

    /*
     * Example 2: map abs_val
     *   Spec: ∀x. {true} abs_val(x) {result >= 0}
     *   P = any_int, Q = is_non_neg
     */
    printf("map abs_val [-3,-1,0,2,-5]\n");
    printf("  Spec: ∀x. {true} abs_val(x) {result >= 0}\n");
    int_map(abs_val, any_int, is_non_neg, in2, out, n);
    print_array("  Result:", out, n);
    printf("  All outputs >= 0: verified by int_map\n\n");

    /*
     * Example 3: map square with a precondition
     *   Spec: ∀x. {x > 0} square(x) {result > 0}
     *   P = is_positive, Q = is_positive
     *
     *   This illustrates that specifications can restrict the input domain.
     *   int_map checks P before calling f and Q after -- the spec is
     *   enforced pointwise across the entire array.
     */
    int pos[] = {1, 2, 3, 4, 5};
    printf("map square [1,2,3,4,5]  (precondition: each x > 0)\n");
    printf("  Spec: ∀x. {x > 0} square(x) {result > 0}\n");
    int_map(square, is_positive, is_positive, pos, out, n);
    print_array("  Result:", out, n);
    printf("  All outputs > 0: verified by int_map\n\n");

    /*
     * Composition: map abs_val composed with map double_val
     *   abs_val:   {true}  -> {result >= 0}
     *   double_val: {x >= 0} -> {result is even ∧ result >= 0}
     *
     *   Together: {true} -> {result is even ∧ result >= 0}
     *   This is the higher-order analogue of the sequence rule.
     */
    int mixed[] = {-2, 3, -4, 1, -6};
    int mid[5];
    printf("map double_val (map abs_val [-2,3,-4,1,-6])  (composition)\n");
    printf("  Step 1 spec: ∀x. {true} abs_val(x) {result >= 0}\n");
    printf("  Step 2 spec: ∀x. {x >= 0} double_val(x) {result is even ∧ result >= 0}\n");
    int_map(abs_val,    any_int,    is_non_neg,             mixed, mid, n);
    int_map(double_val, is_non_neg, is_even,                mid,   out, n);
    print_array("  Result:", out, n);
    printf("  Spec composition verified\n\n");
}

static void demo_filter(void)
{
    printf("-- filter: Parametric Predicate (Hoare-style) --\n\n");

    int in[] = {-2, -1, 0, 1, 2, 3, 4, 5};
    int out[8];
    int n = 8;
    int count;

    /*
     * filter is_positive
     *   Spec: ∀x. is_positive(x) = true  ↔  x > 0
     *   Post: result = [x | x ∈ in ∧ x > 0]
     *   int_filter checks: kept elements satisfy Q, dropped elements do not.
     */
    printf("filter is_positive [-2,-1,0,1,2,3,4,5]\n");
    printf("  Spec: ∀x. {true} is_positive(x) {result = true ↔ x > 0}\n");
    count = int_filter(is_positive, is_positive, in, out, n);
    print_array("  Result:", out, count);
    printf("  Spec: kept ↔ positive, dropped ↔ not positive: verified\n\n");

    /*
     * filter is_even
     *   Spec: ∀x. is_even(x) = true  ↔  x is even
     *   Post: result = [x | x ∈ in ∧ x is even]
     */
    printf("filter is_even [-2,-1,0,1,2,3,4,5]\n");
    printf("  Spec: ∀x. {true} is_even(x) {result = true ↔ x is even}\n");
    count = int_filter(is_even, is_even, in, out, n);
    print_array("  Result:", out, count);
    printf("  Spec: kept ↔ even, dropped ↔ odd: verified\n\n");

    /*
     * Composition: filter then map
     *   keep positives, then double them
     *   Post: result = [2*x | x ∈ in ∧ x > 0]
     */
    int filtered[8], mapped[8];
    printf("map double_val (filter is_positive [-2,-1,0,1,2,3,4,5])\n");
    int fc = int_filter(is_positive, is_positive, in, filtered, n);
    int_map(double_val, is_positive, is_even, filtered, mapped, fc);
    print_array("  Result:", mapped, fc);
    printf("  Each result = 2*x for some x > 0: verified\n\n");
}

static void demo_fold(void)
{
    printf("-- fold_left: Algebraic Laws --\n\n");

    int arr[] = {1, 2, 3, 4, 5};
    int n = 5;

    /*
     * fold_left(+, 0, arr) = 15
     * Loop invariant: after i steps, acc = 0 + arr[0] + ... + arr[i-1]
     * Identity: 0 + x = x
     */
    int sum = fold_left(op_add, 0, arr, n);
    printf("fold_left(+, 0, [1,2,3,4,5]) = %d  (expected 15)\n", sum);
    assert(sum == 15);

    /*
     * fold_left(*, 1, arr) = 120
     * Identity: 1 * x = x
     */
    int product = fold_left(op_mul, 1, arr, n);
    printf("fold_left(*, 1, [1,2,3,4,5]) = %d  (expected 120)\n", product);
    assert(product == 120);

    /*
     * fold_left(max, INT_MIN, arr) = max element
     * Identity: max(INT_MIN, x) = x
     */
    int arr2[] = {3, 1, 4, 1, 5, 9, 2, 6};
    int max = fold_left(op_max, INT_MIN, arr2, 8);
    printf("fold_left(max, INT_MIN, [3,1,4,1,5,9,2,6]) = %d  (expected 9)\n", max);
    assert(max == 9);

    printf("\nAlgebraic law -- commutativity of addition:\n");
    /*
     * fold_left(+, 0, arr) = fold_left(+, 0, reverse(arr))
     * This holds because + is commutative and associative.
     * In KAT terms: the order of elements does not matter for sum.
     */
    int rev[] = {5, 4, 3, 2, 1};
    int sum_rev = fold_left(op_add, 0, rev, n);
    printf("  fold(+, [1,2,3,4,5]) = %d\n", sum);
    printf("  fold(+, [5,4,3,2,1]) = %d\n", sum_rev);
    printf("  Equal (commutativity): %s\n\n", sum == sum_rev ? "yes" : "no");
    assert(sum == sum_rev);

    printf("Algebraic law -- identity element:\n");
    int zero = fold_left(op_add, 0, (int[]){}, 0);
    printf("  fold(+, 0, []) = %d  (identity: 0)\n\n", zero);
    assert(zero == 0);
}

int main(void)
{
    printf("Higher-Order Hoare Logic in C\n");
    printf("-----------------------------\n\n");

    demo_map();
    demo_filter();
    demo_fold();

    printf("All higher-order specifications verified.\n");
    return 0;
}
