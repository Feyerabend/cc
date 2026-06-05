#ifndef TRIT_H
#define TRIT_H

#include <stdint.h>
#include <stddef.h>

/* A trit holds one balanced ternary digit: -1, 0, or +1. */
typedef int8_t trit_t;

/* A tryte is 6 trits (Setun-70 addressable unit). */
typedef struct {
    trit_t t[6];
} tryte_t;

/* An 18-trit word (Setun register width). */
typedef struct {
    trit_t t[18];
} word18_t;

/* A 9-trit half-word (Setun memory cell / instruction word). */
typedef struct {
    trit_t t[9];
} word9_t;

/* Trit constants */
#define TRIT_NEG  ((trit_t) -1)
#define TRIT_ZERO ((trit_t)  0)
#define TRIT_POS  ((trit_t)  1)

/* Clamp an integer to a valid trit value. */
static inline trit_t trit_clamp(int v)
{
    if (v > 0) return TRIT_POS;
    if (v < 0) return TRIT_NEG;
    return TRIT_ZERO;
}

/* Negate a trit. */
static inline trit_t trit_neg(trit_t a)
{
    return (trit_t) (-a);
}

/*
 * Add two trits; carry is written to *carry_out.
 * Uses the balanced ternary addition table.
 */
static inline trit_t trit_add(trit_t a, trit_t b, trit_t *carry_out)
{
    int sum = (int) a + (int) b;
    if (sum > 1) {
        *carry_out = TRIT_POS;
        return (trit_t) (sum - 3);
    } else if (sum < -1) {
        *carry_out = TRIT_NEG;
        return (trit_t) (sum + 3);
    } else {
        *carry_out = TRIT_ZERO;
        return (trit_t) sum;
    }
}

/* Multiply two trits (result is always a single trit; no carry). */
static inline trit_t trit_mul(trit_t a, trit_t b)
{
    return (trit_t) ((int) a * (int) b);
}

/* Convert a balanced ternary word18 to a signed long integer. */
long word18_to_long(const word18_t *w);

/* Convert a signed long integer to a balanced ternary word18. */
word18_t long_to_word18(long v);

/* Convert a word9 to a signed integer. */
int word9_to_int(const word9_t *w);

/* Convert a signed integer to a word9. */
word9_t int_to_word9(int v);

/* Convert a tryte to a signed integer. */
int tryte_to_int(const tryte_t *tr);

/* Convert a signed integer to a tryte. */
tryte_t int_to_tryte(int v);

/* Add two 18-trit words; returns result and sets overflow flag. */
word18_t word18_add(const word18_t *a, const word18_t *b, trit_t *overflow);

/* Negate an 18-trit word (trit-wise inversion). */
word18_t word18_neg(const word18_t *a);

/* Add two 9-trit words. */
word9_t word9_add(const word9_t *a, const word9_t *b, trit_t *overflow);

/* Extract the upper 9 trits of an 18-trit word as a word9. */
word9_t word18_upper9(const word18_t *w);

/* Extract the lower 9 trits of an 18-trit word as a word9. */
word9_t word18_lower9(const word18_t *w);

/* Combine two word9 values into a word18 (upper, lower). */
word18_t word9_combine(const word9_t *upper, const word9_t *lower);

/* Multiply two 18-trit words; result is 18 trits (lower 18 of 36-trit product). */
word18_t word18_mul(const word18_t *a, const word18_t *b);

/* Sign of a word18: +1 if positive, -1 if negative, 0 if zero.
   In balanced ternary, the sign is determined by the most significant
   non-zero trit; if all trits are zero, the number is zero. */
static inline trit_t word18_sign(const word18_t *w)
{
    for (int i = 17; i >= 0; i--) {
        if (w->t[i] != TRIT_ZERO)
            return w->t[i];
    }
    return TRIT_ZERO;
}

/* Print a word18 as a ternary string (MST first). */
void word18_print(const word18_t *w);

/* Print a word9 as a ternary string (MST first). */
void word9_print(const word9_t *w);

/* Print a tryte as a ternary string (MST first). */
void tryte_print(const tryte_t *tr);

#endif
