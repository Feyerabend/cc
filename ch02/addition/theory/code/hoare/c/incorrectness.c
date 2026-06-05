/*
 * incorrectness.c -- Incorrectness Logic: Bug Witnesses
 *
 * Supplementary example: Incorrectness Logic is not covered in
 * theory_of_virtual_machines.tex but complements §3.3 (Axiomatic
 * Semantics).  It is the theoretical basis for tools such as Meta's
 * Infer.  Reference: O'Hearn, "Incorrectness Logic" (POPL 2020).
 *
 * Hoare Logic is built on OVERAPPROXIMATION:
 *   {P} S {Q}  means: for ALL executions from P, Q holds after S.
 *   Useful for proving ABSENCE of bugs.
 *
 * Incorrectness Logic is built on UNDERAPPROXIMATION:
 *   [P] S [Q]  means: every Q-state is REACHABLE from some P-state.
 *   In other words, there EXISTS a concrete execution from P to Q.
 *   Useful for proving PRESENCE of bugs.
 *
 * To certify a bug using Incorrectness Logic:
 *   1. Set Q = the error state (null deref, overflow, etc.)
 *   2. Find a WITNESS -- a specific input in P from which S reaches Q.
 *   3. The triple [P] S [Q] is proved by exhibiting the witness.
 *
 * The consequence rule in Incorrectness Logic runs in the OPPOSITE
 * direction from Hoare Logic:
 *   Hoare:        P' ⇒ P  (weaken P)   Q ⇒ Q'  (strengthen Q)
 *   Incorrectness: P ⇒ P' (strengthen P) Q' ⇒ Q (weaken Q)
 *
 * Strengthening P means "find a tighter witness."
 * Weakening Q means "generalize the bug category."
 *
 * This is the theoretical foundation for tools like Meta's Infer.
 *
 * Compile:  gcc -Wall -std=c11 -o incorrectness incorrectness.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <assert.h>
#include <stdbool.h>


/* Example 1: Null pointer dereference */

/*
 * process(p) dereferences p without a null check.
 *
 * HOARE perspective:
 *   {p != NULL} process(p) {result = *p + 1}
 *   This triple IS provable -- for non-null inputs the code is correct.
 *   Hoare logic certifies the SAFE path.
 *
 * INCORRECTNESS perspective:
 *   [p = NULL] process(p) [NULL_DEREF]
 *   Witness: calling with p = NULL reaches the error state.
 *   Incorrectness logic certifies the BUG path.
 *
 * Neither perspective alone is the whole story.
 */
static int process(int *p)
{
    /* No null check -- potential null dereference */
    return *p + 1;
}

static void demo_null_deref(void)
{
    printf("-- Null Pointer Dereference (Incorrectness Logic) --\n\n");

    printf("Function: process(p) = *p + 1   (no null check)\n\n");

    printf("HOARE-STYLE: certify the safe path\n");
    printf("  {p != NULL} process(p) {result = *p + 1}\n");
    int val = 42;
    int r = process(&val);
    printf("  process(&42) = %d  -- safe, postcondition holds\n\n", r);

    printf("INCORRECTNESS-STYLE: certify the bug\n");
    printf("  [p = NULL] process(p) [NULL_DEREF]\n");
    printf("  Witness: p = NULL\n");
    printf("  Is the null-deref path reachable? ");
    /*
     * We demonstrate reachability without crashing by checking the
     * condition that would trigger it.  In a real analysis tool,
     * this witness would be used to generate a test case.
     */
    int *bug_witness = NULL;
    bool reachable = (bug_witness == NULL);   /* the crash would happen here */
    printf("%s\n", reachable ? "YES -- incorrectness triple holds" : "no");
    assert(reachable);

    printf("\nKey difference:\n");
    printf("  Hoare triple needs ALL executions from P to satisfy Q.\n");
    printf("  Incorrectness triple needs ONE execution from P to Q.\n");
    printf("  [p = NULL] process [NULL_DEREF] is proved by a single witness.\n\n");
}


/* Example 2: Integer overflow */

/*
 * double_it(x) = 2 * x
 *
 * HOARE (restricted precondition, safe path):
 *   {x <= INT_MAX/2} double_it(x) {result = 2*x}
 *   Provable because 2*x fits in int when x <= INT_MAX/2.
 *
 * INCORRECTNESS (bug witness):
 *   [x = INT_MAX] double_it(x) [OVERFLOW]
 *   Witness: x = INT_MAX -- 2*INT_MAX overflows signed int.
 */
static void demo_overflow(void)
{
    printf("-- Integer Overflow (Incorrectness Logic) --\n\n");

    printf("Function: double_it(x) = 2 * x   (no overflow check)\n\n");

    printf("HOARE (safe precondition):\n");
    printf("  {x <= INT_MAX/2} double_it(x) {result = 2*x}\n");
    int safe = 1000;
    printf("  double_it(%d) = %d  -- no overflow\n\n", safe, 2 * safe);

    printf("INCORRECTNESS (bug witness):\n");
    printf("  [x = INT_MAX] double_it(x) [OVERFLOW]\n");
    printf("  INT_MAX = %d\n", INT_MAX);

    /*
     * Check the overflow condition without triggering undefined behavior
     * by testing BEFORE the operation.
     */
    int x = INT_MAX;
    bool overflows = (x > INT_MAX / 2);
    printf("  2 * INT_MAX overflows? %s\n", overflows ? "YES" : "no");
    printf("  Incorrectness triple [x = INT_MAX] double_it [OVERFLOW]: %s\n\n",
           overflows ? "holds (witness valid)" : "does not hold");
    assert(overflows);
}


/* Example 3: Consequence rule -- tightening and generalising */

/*
 * lookup(arr, n, index) = arr[index]   (no bounds check)
 *
 * The incorrectness consequence rule lets us:
 *   Step 1: derive a specific triple with a concrete witness.
 *   Step 2: WEAKEN the postcondition (generalise the bug category).
 *   Step 3: WEAKEN the precondition (generalise the inputs that trigger it).
 *
 * This is the REVERSE of Hoare's consequence rule:
 *   Hoare:        weaken P,  strengthen Q
 *   Incorrectness: strengthen P (concrete witness), then weaken P and Q outward
 */
static void demo_consequence_rule(void)
{
    printf("-- Incorrectness Consequence Rule --\n\n");

    int n = 3;   /* array length (arr = {10, 20, 30}) */

    printf("Function: lookup(arr, n, index) = arr[index]  (no bounds check)\n\n");

    printf("Step 1 -- specific witness:\n");
    printf("  [index = 5] lookup [reads arr[5] -- out of bounds]\n");
    printf("  Witness: index = 5, n = 3  =>  5 >= 3 (out of bounds)\n");
    assert(5 >= n);
    printf("  Witness is valid.\n\n");

    printf("Step 2 -- weaken postcondition (broaden bug category):\n");
    printf("  [index = 5] lookup [reads arr[5]]\n");
    printf("  =>  [index = 5] lookup [undefined behavior]\n");
    printf("  (arr[5] IS undefined behavior; broader Q)\n\n");

    printf("Step 3 -- weaken precondition (cover all triggers):\n");
    printf("  [index = 5] lookup [UB]\n");
    printf("  =>  [index >= n] lookup [UB]\n");
    printf("  Because {5} ⊆ {index | index >= %d}\n\n", n);

    printf("  Checking: all indices >= n trigger the bug:\n");
    for (int idx = n; idx <= n + 3; idx++) {
        printf("  index = %d >= %d: %s\n", idx, n,
               idx >= n ? "out of bounds (bug path)" : "safe");
        assert(idx >= n);
    }

    printf("\nFinal incorrectness triple:\n");
    printf("  [index >= %d] lookup [undefined behavior]\n", n);
    printf("  Derived from one witness by two applications of consequence.\n\n");
}


/* Example 4: Hoare + Incorrectness for a complete picture */

/*
 * A thorough analysis of any function should use BOTH logics:
 *   - Hoare Logic  : certify safe inputs (absence of bugs on those inputs)
 *   - Incorrectness: certify bug witnesses (presence of bugs for other inputs)
 *
 * Together they give a complete characterisation of the function.
 *
 * divide(a, b) = a / b
 *   Hoare:         {b != 0} divide {result = a/b}      -- safe path
 *   Incorrectness: [b = 0] divide [division-by-zero]   -- bug path
 */
static void demo_complete_analysis(void)
{
    printf("-- Hoare + Incorrectness: Complete Analysis --\n\n");

    printf("Function: divide(a, b) = a / b\n\n");

    printf("HOARE -- safe path:\n");
    printf("  {b != 0} divide(a, b) {result = a/b}\n");
    int a = 10, b_safe = 2;
    printf("  divide(%d, %d) = %d  -- postcondition holds\n\n", a, b_safe, a / b_safe);

    printf("INCORRECTNESS -- bug path:\n");
    printf("  [b = 0] divide(a, b) [division-by-zero]\n");
    int b_bug = 0;
    bool witness_valid = (b_bug == 0);
    printf("  Witness: b = 0  =>  division-by-zero reachable: %s\n\n",
           witness_valid ? "YES" : "no");
    assert(witness_valid);

    printf("Together:\n");
    printf("  b != 0 : safe, result = a/b         (Hoare)\n");
    printf("  b  = 0 : division-by-zero           (Incorrectness)\n");
    printf("  These two triples cover all inputs: {b != 0} ∪ {b = 0} = ℤ\n");
    printf("  Neither logic alone gives the full picture.\n\n");
}


/* Example 5: Loop with an off-by-one bug */

/*
 * sum_array(arr, n) sums arr[0..n], using <= instead of <.
 * This reads one past the end when n = len(arr).
 *
 * Hoare triple for the SAFE inputs (n < len(arr)):
 *   {0 <= n < len(arr)} sum_array {result = arr[0]+...+arr[n]}
 *
 * Incorrectness triple for the bug:
 *   [n = len(arr)] sum_array [out-of-bounds read on arr[n]]
 *   Witness: pass n equal to the actual array length.
 */
static int sum_array_buggy(int arr[], int n)
{
    int sum = 0;
    for (int i = 0; i <= n; i++)   /* BUG: should be i < n */
        sum += arr[i];
    return sum;
}

static void demo_off_by_one(void)
{
    printf("-- Off-By-One Bug (Incorrectness Logic) --\n\n");

    int arr[] = {1, 2, 3, 4, 5};
    int n = 5;   /* actual length */

    printf("Function: sum_array(arr, n) uses i <= n (should be i < n)\n\n");

    printf("HOARE (safe precondition, n interpreted as last valid index):\n");
    printf("  {0 <= n-1 < len(arr)} sum_array {result = sum of first n elements}\n");
    printf("  sum_array(arr, 4) = %d  -- reads arr[0..4], no overflow\n\n",
           sum_array_buggy(arr, 4));

    printf("INCORRECTNESS (bug witness):\n");
    printf("  [n = len(arr)] sum_array [reads arr[n] -- out of bounds]\n");
    printf("  Witness: n = %d (the array length)\n", n);

    /*
     * The loop "for (i = 0; i <= n; i++)" always reaches i = n,
     * reading arr[n].  When n equals the array length, arr[n] is
     * one past the end -- undefined behavior.
     *
     * We verify the witness precondition without running the UB:
     * the argument passed equals the array's actual length.
     */
    int arr_len = (int)(sizeof(arr) / sizeof(arr[0]));
    bool oob_reachable = (n == arr_len);   /* witness: called with length */
    printf("  Loop (i <= n) reaches arr[%d]; array size = %d\n", n, arr_len);
    printf("  Bug path reachable (n == arr_len)? %s\n",
           oob_reachable ? "YES" : "no");
    assert(oob_reachable);

    printf("\nIncorrectness triple holds: [n = len(arr)] sum_array [UB]\n\n");
}


int main(void)
{
    printf("Incorrectness Logic: Bug Witnesses in C\n");
    printf("---------------------------------------\n\n");

    demo_null_deref();
    demo_overflow();
    demo_consequence_rule();
    demo_complete_analysis();
    demo_off_by_one();

    printf("All incorrectness examples demonstrated.\n");
    return 0;
}
