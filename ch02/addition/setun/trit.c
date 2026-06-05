#include "trit.h"
#include <stdio.h>

long word18_to_long(const word18_t *w)
{
    long result = 0;
    long power = 1;
    for (int i = 0; i < 18; i++) {
        result += (long) w->t[i] * power;
        power *= 3;
    }
    return result;
}

word18_t long_to_word18(long v)
{
    word18_t w;
    for (int i = 0; i < 18; i++) {
        int rem = (int) (v % 3);
        if (rem > 1)  rem -= 3;
        if (rem < -1) rem += 3;
        w.t[i] = (trit_t) rem;
        v = (v - rem) / 3;
    }
    return w;
}

int word9_to_int(const word9_t *w)
{
    int result = 0;
    int power = 1;
    for (int i = 0; i < 9; i++) {
        result += (int) w->t[i] * power;
        power *= 3;
    }
    return result;
}

word9_t int_to_word9(int v)
{
    word9_t w;
    for (int i = 0; i < 9; i++) {
        int rem = v % 3;
        if (rem > 1)  rem -= 3;
        if (rem < -1) rem += 3;
        w.t[i] = (trit_t) rem;
        v = (v - rem) / 3;
    }
    return w;
}

int tryte_to_int(const tryte_t *tr)
{
    int result = 0;
    int power = 1;
    for (int i = 0; i < 6; i++) {
        result += (int) tr->t[i] * power;
        power *= 3;
    }
    return result;
}

tryte_t int_to_tryte(int v)
{
    tryte_t tr;
    for (int i = 0; i < 6; i++) {
        int rem = v % 3;
        if (rem > 1)  rem -= 3;
        if (rem < -1) rem += 3;
        tr.t[i] = (trit_t) rem;
        v = (v - rem) / 3;
    }
    return tr;
}

word18_t word18_add(const word18_t *a, const word18_t *b, trit_t *overflow)
{
    word18_t result;
    trit_t carry = TRIT_ZERO;
    trit_t dummy;

    for (int i = 0; i < 18; i++) {
        trit_t c1;
        trit_t s = trit_add(a->t[i], b->t[i], &c1);
        trit_t c2;
        result.t[i] = trit_add(s, carry, &c2);
        carry = trit_add(c1, c2, &dummy);
    }

    if (overflow)
        *overflow = carry;

    return result;
}

word18_t word18_neg(const word18_t *a)
{
    word18_t result;
    for (int i = 0; i < 18; i++)
        result.t[i] = trit_neg(a->t[i]);
    return result;
}

word9_t word9_add(const word9_t *a, const word9_t *b, trit_t *overflow)
{
    word9_t result;
    trit_t carry = TRIT_ZERO;
    trit_t dummy;

    for (int i = 0; i < 9; i++) {
        trit_t c1;
        trit_t s = trit_add(a->t[i], b->t[i], &c1);
        trit_t c2;
        result.t[i] = trit_add(s, carry, &c2);
        carry = trit_add(c1, c2, &dummy);
    }

    if (overflow)
        *overflow = carry;

    return result;
}

word9_t word18_upper9(const word18_t *w)
{
    word9_t result;
    for (int i = 0; i < 9; i++)
        result.t[i] = w->t[i + 9];
    return result;
}

word9_t word18_lower9(const word18_t *w)
{
    word9_t result;
    for (int i = 0; i < 9; i++)
        result.t[i] = w->t[i];
    return result;
}

word18_t word9_combine(const word9_t *upper, const word9_t *lower)
{
    word18_t result;
    for (int i = 0; i < 9; i++) {
        result.t[i]     = lower->t[i];
        result.t[i + 9] = upper->t[i];
    }
    return result;
}

word18_t word18_mul(const word18_t *a, const word18_t *b)
{
    /* Grade-school balanced ternary multiplication, keep lower 18 trits. */
    long va = word18_to_long(a);
    long vb = word18_to_long(b);
    return long_to_word18(va * vb);
}

void word18_print(const word18_t *w)
{
    /* Print MST (most significant trit) first. */
    for (int i = 17; i >= 0; i--) {
        if (w->t[i] == TRIT_POS)       putchar('+');
        else if (w->t[i] == TRIT_NEG)  putchar('-');
        else                            putchar('0');
    }
}

void word9_print(const word9_t *w)
{
    for (int i = 8; i >= 0; i--) {
        if (w->t[i] == TRIT_POS)       putchar('+');
        else if (w->t[i] == TRIT_NEG)  putchar('-');
        else                            putchar('0');
    }
}

void tryte_print(const tryte_t *tr)
{
    for (int i = 5; i >= 0; i--) {
        if (tr->t[i] == TRIT_POS)       putchar('+');
        else if (tr->t[i] == TRIT_NEG)  putchar('-');
        else                             putchar('0');
    }
}
