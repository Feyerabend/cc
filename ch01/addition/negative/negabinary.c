/*
 * negabinary.c  --  base -2 integer and fixed-point arithmetic
 *
 * Representation: bits stored in a uint32_t, LSB = position 0.
 * Place value of bit k  =  (-2)^k  (alternating sign).
 * No sign bit needed; negative numbers arise naturally.
 *
 * Fixed-point: we use a scale of 2^FRAC_BITS (even, so (-2)^FRAC_BITS = 2^FRAC_BITS).
 * The low FRAC_BITS bits of a negabinary word are the fractional part;
 * the remaining high bits are the integer part.
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>


#define NB_BITS   32
#define FRAC_BITS 12    /* must be even so (-2)^FRAC_BITS = 2^FRAC_BITS */


/*
 * Compute the integer value of a negabinary bit pattern.
 * Bit k contributes bits[k] * (-2)^k.
 */
int64_t nb_to_int(uint32_t nb)
{
    int64_t result = 0;
    int64_t base   = 1;

    for (int k = 0; k < NB_BITS; k++) {
        if (nb & (1u << k))
            result += base;
        base *= -2;
    }
    return result;
}

/*
 * Convert a (possibly negative) integer to its negabinary bit pattern.
 * Algorithm: remainder = n % 2 (always 0 or 1 for positive divisor 2),
 *            next n    = -(n / 2)  after adjusting for the remainder.
 * Equivalent to: remainder = n & 1, n = -(n >> 1) when n >= 0,
 * but we use the explicit form to stay clear about the sign handling.
 */
uint32_t int_to_nb(int64_t n)
{
    uint32_t result = 0;

    for (int k = 0; k < NB_BITS && n != 0; k++) {
        int rem = (int)(n % 2);
        if (rem < 0) rem += 2;   /* force remainder into {0, 1} */
        if (rem)
            result |= (1u << k);
        n = -((n - rem) / 2);
    }
    return result;
}

/*
 * Print a negabinary value as a binary string (MSB first, no leading zeros).
 * buf must hold at least NB_BITS + 1 bytes.
 */
void nb_to_str(uint32_t nb, char *buf)
{
    if (nb == 0) {
        buf[0] = '0';
        buf[1] = '\0';
        return;
    }

    int top = 0;
    for (int k = NB_BITS - 1; k >= 0; k--) {
        if (nb & (1u << k)) { top = k; break; }
    }

    int pos = 0;
    for (int k = top; k >= 0; k--)
        buf[pos++] = (nb & (1u << k)) ? '1' : '0';
    buf[pos] = '\0';
}

/*
 * Negate a negabinary value.
 * No simple bit-flip rule exists (unlike balanced ternary); we go via integer.
 */
uint32_t nb_negate(uint32_t nb)
{
    return int_to_nb(-nb_to_int(nb));
}

/*
 * Add two negabinary values.
 *
 * At each bit position:
 *     s     = a_bit + b_bit + carry
 *     bit   = s & 1
 *     carry = -(s >> 1)
 *
 * carry can be -1, 0, or +1.
 */
uint32_t nb_add(uint32_t a, uint32_t b)
{
    uint32_t result = 0;
    int      carry  = 0;

    for (int k = 0; k < NB_BITS; k++) {
        int a_bit = (a >> k) & 1;
        int b_bit = (b >> k) & 1;
        int s     = a_bit + b_bit + carry;
        int bit   = s & 1;
        carry     = -(s >> 1);
        if (bit)
            result |= (1u << k);
    }
    return result;
}

/*
 * Subtract b from a.
 */
uint32_t nb_subtract(uint32_t a, uint32_t b)
{
    return nb_add(a, nb_negate(b));
}

/*
 * Multiply two negabinary values using long multiplication.
 *
 * For each set bit of b at position i, add a shifted left by i.
 * Shifting left by i in negabinary multiplies by (-2)^i, which is
 * exactly the place value at that position.
 */
uint32_t nb_multiply(uint32_t a, uint32_t b)
{
    uint32_t result = 0;

    for (int i = 0; i < NB_BITS; i++) {
        if ((b >> i) & 1)
            result = nb_add(result, a << i);
    }
    return result;
}


/*
 * Fixed-point representation
 *
 * A fixed-point negabinary value is a uint32_t where the low FRAC_BITS bits
 * are the fractional part and the remaining bits are the integer part.
 *
 * Because FRAC_BITS is even, (-2)^FRAC_BITS = 2^FRAC_BITS, so we can
 * scale by 2^FRAC_BITS, convert the resulting integer to negabinary, and
 * the low FRAC_BITS bits naturally encode the fractional portion.
 *
 * Bit k in the fixed-point word has place value (-2)^(k - FRAC_BITS).
 */

typedef uint32_t nb_fixed_t;

nb_fixed_t double_to_nb_fixed(double x)
{
    int64_t scaled = (int64_t)round(x * (1 << FRAC_BITS));
    return int_to_nb(scaled);
}

double nb_fixed_to_double(nb_fixed_t fp)
{
    double result = 0.0;
    double base   = pow(-2.0, -(double)FRAC_BITS);

    for (int k = 0; k < NB_BITS; k++) {
        if (fp & (1u << k))
            result += base;
        base *= -2.0;
    }
    return result;
}

nb_fixed_t nb_fixed_add(nb_fixed_t a, nb_fixed_t b)
{
    return nb_add(a, b);
}

nb_fixed_t nb_fixed_subtract(nb_fixed_t a, nb_fixed_t b)
{
    return nb_subtract(a, b);
}

nb_fixed_t nb_fixed_multiply(nb_fixed_t a, nb_fixed_t b)
{
    /*
     * Multiply two fixed-point values.
     * Both have FRAC_BITS fractional bits, so the product has 2*FRAC_BITS.
     * We shift the negabinary product right by FRAC_BITS to normalise.
     * Right-shifting a negabinary word by FRAC_BITS (even) divides by
     * (-2)^FRAC_BITS = 2^FRAC_BITS, which corrects the scale.
     */
    uint32_t raw = nb_multiply(a, b);
    return raw >> FRAC_BITS;
}

void nb_fixed_to_str(nb_fixed_t fp, char *buf)
{
    /* print as integer_bits . frac_bits */
    char all[NB_BITS + 1];
    nb_to_str(fp, all);

    int len = (int)strlen(all);
    int dot_pos = len - FRAC_BITS;

    if (dot_pos <= 0) {
        /* all bits are fractional */
        strcpy(buf, "0.");
        for (int i = 0; i < -dot_pos; i++) { buf[2+i] = '0'; buf[3+i] = '\0'; }
        strcat(buf, all);
    } else {
        strncpy(buf, all, dot_pos);
        buf[dot_pos] = '.';
        strcpy(buf + dot_pos + 1, all + dot_pos);
        buf[len + 1] = '\0';
    }
}


/*
 * Demo functions
 */

static void demo_place_values(void)
{
    printf("=== Place values: (-2)^k for k = 7 down to -4 ===\n\n");
    printf("  %9s   %8s\n", "position", "value");
    printf("  %9s   %8s\n", "---------", "--------");

    for (int k = 7; k >= 0; k--) {
        int64_t val = 1;
        for (int i = 0; i < k; i++) val *= -2;
        printf("  %4s(-2)^%d   %8lld\n", "", k, (long long)val);
    }
    for (int k = 1; k <= 4; k++) {
        double val = pow(-2.0, -k);
        printf("  %3s(-2)^-%d   %8.4f\n", "", k, val);
    }
    printf("\n");
}

static void demo_conversion(void)
{
    printf("=== Conversion: integer <-> negabinary ===\n\n");
    printf("  %5s   %12s   %5s\n", "n", "negabinary", "back");
    printf("  %5s   %12s   %5s\n", "-----", "------------", "-----");

    char buf[NB_BITS + 1];
    for (int n = -13; n <= 13; n++) {
        uint32_t nb   = int_to_nb(n);
        int64_t  back = nb_to_int(nb);
        nb_to_str(nb, buf);
        printf("  %5d   %12s   %5lld\n", n, buf, (long long)back);
    }
    printf("\n");
}

static void demo_negation(void)
{
    printf("=== Negation (no simple bit-flip; goes via integer) ===\n\n");

    int tests[] = { 5, -5, 6, -6, 13, -13, 0 };
    char buf_a[NB_BITS + 1], buf_b[NB_BITS + 1];

    for (int i = 0; i < 7; i++) {
        int n         = tests[i];
        uint32_t nb   = int_to_nb(n);
        uint32_t neg  = nb_negate(nb);
        nb_to_str(nb,  buf_a);
        nb_to_str(neg, buf_b);
        printf("  %4d  %10s   ->  %10s  = %lld\n",
               n, buf_a, buf_b, (long long)nb_to_int(neg));
    }
    printf("\n");
}

static void demo_carry_table(void)
{
    printf("=== Carry table for negabinary addition ===\n\n");
    printf("  %3s  %3s  %9s  %6s  %4s  %10s\n",
           "a", "b", "carry_in", "total", "bit", "carry_out");
    printf("  %3s  %3s  %9s  %6s  %4s  %10s\n",
           "---", "---", "---------", "------", "----", "----------");

    int carry_ins[] = { 0, 1, -1 };
    for (int ci = 0; ci < 3; ci++) {
        int carry_in = carry_ins[ci];
        for (int a = 0; a <= 1; a++) {
            for (int b = 0; b <= 1; b++) {
                int s         = a + b + carry_in;
                int bit       = s & 1;
                int carry_out = -(s >> 1);
                if (bit == 0 || bit == 1) {
                    printf("  %3d  %3d  %9d  %6d  %4d  %10d\n",
                           a, b, carry_in, s, bit, carry_out);
                }
            }
        }
    }
    printf("\n");
}

static void demo_addition(void)
{
    printf("=== Addition ===\n\n");

    int pairs[][2] = { {5,3}, {5,-3}, {-5,-3}, {6,6}, {13,-7}, {0,-9} };
    char buf_a[NB_BITS+1], buf_b[NB_BITS+1], buf_r[NB_BITS+1];

    for (int i = 0; i < 6; i++) {
        int x = pairs[i][0], y = pairs[i][1];
        uint32_t ax = int_to_nb(x);
        uint32_t ay = int_to_nb(y);
        uint32_t r  = nb_add(ax, ay);
        nb_to_str(ax, buf_a);
        nb_to_str(ay, buf_b);
        nb_to_str(r,  buf_r);
        printf("  %4d (%8s) + %4d (%8s)  =  %10s  = %lld  (expected %d)\n",
               x, buf_a, y, buf_b, buf_r, (long long)nb_to_int(r), x + y);
    }
    printf("\n");
}

static void demo_subtraction(void)
{
    printf("=== Subtraction ===\n\n");

    int pairs[][2] = { {5,3}, {3,5}, {-5,-3}, {10,4}, {6,-2} };
    char buf_a[NB_BITS+1], buf_b[NB_BITS+1], buf_r[NB_BITS+1];

    for (int i = 0; i < 5; i++) {
        int x = pairs[i][0], y = pairs[i][1];
        uint32_t ax = int_to_nb(x);
        uint32_t ay = int_to_nb(y);
        uint32_t r  = nb_subtract(ax, ay);
        nb_to_str(ax, buf_a);
        nb_to_str(ay, buf_b);
        nb_to_str(r,  buf_r);
        printf("  %4d (%8s) - %4d (%8s)  =  %10s  = %lld  (expected %d)\n",
               x, buf_a, y, buf_b, buf_r, (long long)nb_to_int(r), x - y);
    }
    printf("\n");
}

static void demo_multiplication(void)
{
    printf("=== Multiplication ===\n\n");

    int pairs[][2] = { {3,4}, {-3,4}, {-3,-4}, {5,5}, {6,-3}, {2,-2} };
    char buf_a[NB_BITS+1], buf_b[NB_BITS+1], buf_r[NB_BITS+1];

    for (int i = 0; i < 6; i++) {
        int x = pairs[i][0], y = pairs[i][1];
        uint32_t ax = int_to_nb(x);
        uint32_t ay = int_to_nb(y);
        uint32_t r  = nb_multiply(ax, ay);
        nb_to_str(ax, buf_a);
        nb_to_str(ay, buf_b);
        nb_to_str(r,  buf_r);
        printf("  %4d (%7s) * %4d (%7s)  =  %12s  = %lld  (expected %d)\n",
               x, buf_a, y, buf_b, buf_r, (long long)nb_to_int(r), x * y);
    }
    printf("\n");
}

static void demo_float(void)
{
    printf("=== Floating point in negabinary (FRAC_BITS = %d) ===\n\n", FRAC_BITS);
    printf("  %8s   %10s   %s\n", "x", "int part", "reconstructed");
    printf("  %8s   %10s   %s\n", "--------", "----------", "-------------");

    double tests[] = { 0.5, -0.5, 0.25, -0.25, 1.25, -3.75, 0.1, -0.1 };
    char buf_int[NB_BITS+1], buf_fp[NB_BITS * 2 + 2];

    for (int i = 0; i < 8; i++) {
        double      x  = tests[i];
        nb_fixed_t  fp = double_to_nb_fixed(x);
        double      rc = nb_fixed_to_double(fp);

        /* print integer part separately */
        uint32_t int_part = fp >> FRAC_BITS;
        nb_to_str(int_part, buf_int);
        nb_fixed_to_str(fp, buf_fp);

        printf("  %8.4f   %10s   %14.8f\n", x, buf_int, rc);
    }
    printf("\n");
}


int main(void)
{
    demo_place_values();
    demo_conversion();
    demo_negation();
    demo_carry_table();
    demo_addition();
    demo_subtraction();
    demo_multiplication();
    demo_float();
    return 0;
}
