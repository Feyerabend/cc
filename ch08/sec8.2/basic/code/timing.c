#include <string.h>
#include <stdint.h>

/* Vulnerable: returns immediately on first mismatch, leaking position */
int verify_bad(const char *supplied, const char *secret) {
    return strcmp(supplied, secret) == 0;
}

/* Safe: XOR all bytes unconditionally; elapsed time is independent
   of where (or whether) a mismatch occurs */
int verify_ct(const char *a, const char *b, size_t len) {
    volatile uint8_t diff = 0;
    for (size_t i = 0; i < len; i++)
        diff |= (uint8_t)a[i] ^ (uint8_t)b[i];
    return diff == 0;
}
