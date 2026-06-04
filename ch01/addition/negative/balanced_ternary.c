/*
 * balanced_ternary.c  --  base 3 with digits {-1, 0, +1}
 *
 * Representation: each trit stored in 2 bits inside a uint64_t.
 *   00  =  0
 *   01  = +1
 *   10  = -1  (we use 2 to represent -1 internally)
 *   11  =  unused
 *
 * Trit k occupies bits 2k and 2k+1.
 * Place value of trit k  =  trit_value(k) * 3^k.
 *
 * Fixed-point: the low FRAC_TRITS trit positions are fractional.
 * Place value of fractional trit at position -j  =  digit * 3^(-j).
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>


#define BT_TRITS   20       /* number of trits in one word */
#define FRAC_TRITS  8       /* must be even for clean fixed-point scaling */

typedef uint64_t bt_t;      /* packed trit word */

/* encoding helpers */
#define TRIT_ZERO  0u
#define TRIT_POS   1u
#define TRIT_NEG   2u       /* stored as 2, represents -1 */

static inline unsigned int get_trit(bt_t w, int k)
{
    return (w >> (2 * k)) & 3u;
}

static inline bt_t set_trit(bt_t w, int k, unsigned int t)
{
    w &= ~((uint64_t)3u << (2 * k));
    w |=  ((uint64_t)(t & 3u) << (2 * k));
    return w;
}

/* convert packed trit encoding {0,1,2} to integer value {0,+1,-1} */
static inline int trit_val(unsigned int t)
{
    return (t == TRIT_POS) ? 1 : (t == TRIT_NEG) ? -1 : 0;
}

/* convert integer trit value {-1,0,+1} to packed encoding */
static inline unsigned int trit_enc(int v)
{
    return (v ==  1) ? TRIT_POS :
           (v == -1) ? TRIT_NEG : TRIT_ZERO;
}


/*
 * Compute the integer value of a packed balanced ternary word.
 */
int64_t bt_to_int(bt_t w)
{
    int64_t result = 0;
    int64_t power  = 1;

    for (int k = 0; k < BT_TRITS; k++) {
        result += trit_val(get_trit(w, k)) * power;
        power  *= 3;
    }
    return result;
}

/*
 * Convert a (possibly negative) integer to balanced ternary.
 *
 * At each step:
 *   remainder = n % 3   (can be 0, 1, or 2 in C for positive n,
 *                         but for negative n C may give -2, -1, 0)
 *   Adjust: if remainder == 2, use -1 and add 1 to quotient.
 *           if remainder == -1, use -1+3=... actually:
 *           Always force remainder into {0, 1}: if it is 2, set trit=-1 carry=+1.
 *           Negative remainders: if rem == -2 set trit=1 and adjust n.
 *           if rem == -1 set trit=-1... easier: normalise remainder explicitly.
 */
bt_t int_to_bt(int64_t n)
{
    bt_t result = 0;

    for (int k = 0; k < BT_TRITS && n != 0; k++) {
        int rem = (int)(n % 3);

        /* normalise to {-1, 0, 1} */
        if (rem == 2)  { rem =  -1; n += 1; }
        if (rem == -2) { rem =   1; n -= 1; }

        result = set_trit(result, k, trit_enc(rem));
        n /= 3;
    }
    return result;
}

/*
 * Print a balanced ternary value as a string (MSB first, no leading zeros).
 * Digits: '1' for +1, '0' for 0, 'T' for -1.
 * buf must hold at least BT_TRITS + 1 bytes.
 */
void bt_to_str(bt_t w, char *buf)
{
    if (w == 0) {
        buf[0] = '0';
        buf[1] = '\0';
        return;
    }

    int top = 0;
    for (int k = BT_TRITS - 1; k >= 0; k--) {
        if (get_trit(w, k) != TRIT_ZERO) { top = k; break; }
    }

    static const char digit_char[] = { '0', '1', 'T' };
    int pos = 0;
    for (int k = top; k >= 0; k--)
        buf[pos++] = digit_char[get_trit(w, k)];
    buf[pos] = '\0';
}

/*
 * Negate: flip every trit (T <-> 1, 0 stays 0).
 * This is the key elegance of balanced ternary: negation is trivial.
 */
bt_t bt_negate(bt_t w)
{
    bt_t result = 0;

    for (int k = 0; k < BT_TRITS; k++) {
        unsigned int t = get_trit(w, k);
        unsigned int flipped = (t == TRIT_POS) ? TRIT_NEG :
                               (t == TRIT_NEG) ? TRIT_POS : TRIT_ZERO;
        result = set_trit(result, k, flipped);
    }
    return result;
}

/*
 * Add two balanced ternary values.
 *
 * Trit addition table (carry can be -1, 0, or +1):
 *   s = trit_a + trit_b + carry
 *   out_trit  = s mod_balanced 3   (nearest value in {-1,0,1})
 *   carry_out = (s - out_trit) / 3
 *
 * "mod_balanced": adjust s into {-1, 0, 1} by adding/subtracting 3.
 */
bt_t bt_add(bt_t a, bt_t b)
{
    bt_t result = 0;
    int  carry  = 0;

    for (int k = 0; k < BT_TRITS; k++) {
        int s    = trit_val(get_trit(a, k)) + trit_val(get_trit(b, k)) + carry;
        int trit = s % 3;

        /* adjust s % 3 into {-1, 0, 1} */
        if (trit ==  2) trit = -1;
        if (trit == -2) trit =  1;

        carry  = (s - trit) / 3;
        result = set_trit(result, k, trit_enc(trit));
    }
    return result;
}

/*
 * Subtract b from a.  Because negation is just a trit flip, this is cheap.
 */
bt_t bt_subtract(bt_t a, bt_t b)
{
    return bt_add(a, bt_negate(b));
}

/*
 * Multiply two balanced ternary values using long multiplication.
 *
 * For each trit of b at position i:
 *   - if trit is +1: add a shifted left by i
 *   - if trit is -1: add -a (= bt_negate(a)) shifted left by i
 *   - if trit is  0: skip
 */
bt_t bt_multiply(bt_t a, bt_t b)
{
    bt_t result = 0;

    for (int i = 0; i < BT_TRITS; i++) {
        int tv = trit_val(get_trit(b, i));
        if (tv == 0) continue;

        bt_t shifted = (tv == 1) ? a : bt_negate(a);

        /* shift left by i trit positions (each trit is 2 bits) */
        shifted <<= (2 * i);
        result = bt_add(result, shifted);
    }
    return result;
}


/*
 * Fixed-point balanced ternary
 *
 * The low FRAC_TRITS trit positions are fractional; the rest are integer.
 * Trit at position k has place value 3^(k - FRAC_TRITS).
 *
 * We scale by 3^FRAC_TRITS to convert to integer, then convert to bt_t.
 */

typedef bt_t bt_fixed_t;

static int64_t ipow3(int n)
{
    int64_t r = 1;
    for (int i = 0; i < n; i++) r *= 3;
    return r;
}

bt_fixed_t double_to_bt_fixed(double x)
{
    int64_t scale  = ipow3(FRAC_TRITS);
    int64_t scaled = (int64_t)round(x * (double)scale);
    return int_to_bt(scaled);
}

double bt_fixed_to_double(bt_fixed_t fp)
{
    double result = 0.0;
    double base   = pow(3.0, -(double)FRAC_TRITS);

    for (int k = 0; k < BT_TRITS; k++) {
        result += trit_val(get_trit(fp, k)) * base;
        base   *= 3.0;
    }
    return result;
}

bt_fixed_t bt_fixed_add(bt_fixed_t a, bt_fixed_t b)
{
    return bt_add(a, b);
}

bt_fixed_t bt_fixed_subtract(bt_fixed_t a, bt_fixed_t b)
{
    return bt_subtract(a, b);
}

bt_fixed_t bt_fixed_multiply(bt_fixed_t a, bt_fixed_t b)
{
    /*
     * Both operands have FRAC_TRITS fractional trits, so the raw product
     * has 2*FRAC_TRITS.  Shift right by FRAC_TRITS trit positions
     * (= 2*FRAC_TRITS bits) to normalise back to FRAC_TRITS.
     */
    bt_t raw = bt_multiply(a, b);
    return raw >> (2 * FRAC_TRITS);
}


/*
 * Demo functions
 */

static void demo_place_values(void)
{
    printf("=== Place values: 3^k for k = 6 down to -4 ===\n\n");
    printf("  %8s   %8s\n", "position", "value");
    printf("  %8s   %8s\n", "--------", "--------");

    for (int k = 6; k >= 0; k--) {
        int64_t val = ipow3(k);
        printf("  %7s3^%d   %8lld\n", "", k, (long long)val);
    }
    for (int k = 1; k <= 4; k++) {
        double val = pow(3.0, -k);
        printf("  %6s3^-%d   %8.4f\n", "", k, val);
    }
    printf("\n");
}

static void demo_conversion(void)
{
    printf("=== Conversion: integer <-> balanced ternary ===\n\n");
    printf("  %5s   %10s   %5s\n", "n", "bt", "back");
    printf("  %5s   %10s   %5s\n", "-----", "----------", "-----");

    char buf[BT_TRITS + 1];
    for (int n = -13; n <= 13; n++) {
        bt_t    w    = int_to_bt(n);
        int64_t back = bt_to_int(w);
        bt_to_str(w, buf);
        printf("  %5d   %10s   %5lld\n", n, buf, (long long)back);
    }
    printf("\n");
}

static void demo_negation(void)
{
    printf("=== Negation (just flip every trit: T <-> 1) ===\n\n");

    int tests[] = { 5, -5, 13, -13, 0 };
    char buf_a[BT_TRITS+1], buf_b[BT_TRITS+1];

    for (int i = 0; i < 5; i++) {
        int n       = tests[i];
        bt_t w      = int_to_bt(n);
        bt_t neg    = bt_negate(w);
        bt_to_str(w,   buf_a);
        bt_to_str(neg, buf_b);
        printf("  %4d  %8s   ->  %8s  = %lld\n",
               n, buf_a, buf_b, (long long)bt_to_int(neg));
    }
    printf("\n");
}

static void demo_trit_add_table(void)
{
    printf("=== Trit addition table ===\n\n");
    printf("  %3s  %3s  %3s  %6s  %5s  %6s\n",
           "a", "b", "cin", "sum", "trit", "carry");
    printf("  %3s  %3s  %3s  %6s  %5s  %6s\n",
           "---", "---", "---", "------", "-----", "------");

    int vals[] = { -1, 0, 1 };
    for (int ci = 0; ci < 3; ci++) {
        for (int ai = 0; ai < 3; ai++) {
            for (int bi = 0; bi < 3; bi++) {
                int a     = vals[ai];
                int b     = vals[bi];
                int carry = vals[ci];
                int s     = a + b + carry;
                int trit  = s % 3;
                if (trit ==  2) trit = -1;
                if (trit == -2) trit =  1;
                int cout  = (s - trit) / 3;
                printf("  %3d  %3d  %3d  %6d  %5d  %6d\n",
                       a, b, carry, s, trit, cout);
            }
        }
    }
    printf("\n");
}

static void demo_addition(void)
{
    printf("=== Addition ===\n\n");

    int pairs[][2] = { {5,3}, {5,-3}, {-5,-3}, {13,-7}, {0,-9} };
    char buf_a[BT_TRITS+1], buf_b[BT_TRITS+1], buf_r[BT_TRITS+1];

    for (int i = 0; i < 5; i++) {
        int x = pairs[i][0], y = pairs[i][1];
        bt_t ax = int_to_bt(x);
        bt_t ay = int_to_bt(y);
        bt_t r  = bt_add(ax, ay);
        bt_to_str(ax, buf_a);
        bt_to_str(ay, buf_b);
        bt_to_str(r,  buf_r);
        printf("  %4d (%6s) + %4d (%6s)  =  %8s  = %lld  (expected %d)\n",
               x, buf_a, y, buf_b, buf_r, (long long)bt_to_int(r), x + y);
    }
    printf("\n");
}

static void demo_subtraction(void)
{
    printf("=== Subtraction ===\n\n");

    int pairs[][2] = { {5,3}, {3,5}, {-5,-3}, {10,4} };
    char buf_a[BT_TRITS+1], buf_b[BT_TRITS+1], buf_r[BT_TRITS+1];

    for (int i = 0; i < 4; i++) {
        int x = pairs[i][0], y = pairs[i][1];
        bt_t ax = int_to_bt(x);
        bt_t ay = int_to_bt(y);
        bt_t r  = bt_subtract(ax, ay);
        bt_to_str(ax, buf_a);
        bt_to_str(ay, buf_b);
        bt_to_str(r,  buf_r);
        printf("  %4d (%6s) - %4d (%6s)  =  %8s  = %lld  (expected %d)\n",
               x, buf_a, y, buf_b, buf_r, (long long)bt_to_int(r), x - y);
    }
    printf("\n");
}

static void demo_multiplication(void)
{
    printf("=== Multiplication ===\n\n");

    int pairs[][2] = { {3,4}, {-3,4}, {-3,-4}, {5,5}, {9,-3} };
    char buf_a[BT_TRITS+1], buf_b[BT_TRITS+1], buf_r[BT_TRITS+1];

    for (int i = 0; i < 5; i++) {
        int x = pairs[i][0], y = pairs[i][1];
        bt_t ax = int_to_bt(x);
        bt_t ay = int_to_bt(y);
        bt_t r  = bt_multiply(ax, ay);
        bt_to_str(ax, buf_a);
        bt_to_str(ay, buf_b);
        bt_to_str(r,  buf_r);
        printf("  %4d (%5s) * %4d (%5s)  =  %9s  = %lld  (expected %d)\n",
               x, buf_a, y, buf_b, buf_r, (long long)bt_to_int(r), x * y);
    }
    printf("\n");
}

static void demo_float(void)
{
    printf("=== Floating point in balanced ternary (FRAC_TRITS = %d) ===\n\n",
           FRAC_TRITS);
    printf("  %8s   %10s   %14s\n", "x", "int part", "reconstructed");
    printf("  %8s   %10s   %14s\n", "--------", "----------", "--------------");

    double tests[] = { 0.5, -0.5, 1.0/3.0, -1.0/3.0, 1.25, -3.75, 0.1, -0.1 };
    char buf_int[BT_TRITS+1];

    for (int i = 0; i < 8; i++) {
        double      x  = tests[i];
        bt_fixed_t  fp = double_to_bt_fixed(x);
        double      rc = bt_fixed_to_double(fp);

        bt_t int_part = fp >> (2 * FRAC_TRITS);
        bt_to_str(int_part, buf_int);

        printf("  %8.5f   %10s   %14.8f\n", x, buf_int, rc);
    }
    printf("\n");
}


int main(void)
{
    demo_place_values();
    demo_conversion();
    demo_negation();
    demo_trit_add_table();
    demo_addition();
    demo_subtraction();
    demo_multiplication();
    demo_float();
    return 0;
}
