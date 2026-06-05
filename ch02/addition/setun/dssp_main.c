#include <stdio.h>
#include <string.h>
#include "dssp.h"

static int g_pass = 0, g_fail = 0;

static void test(dssp_t *d, const char *input)
{
    printf("  %-50s", input);
    fflush(stdout);
    int rc = dssp_eval(d, input);
    if (rc == 0) { printf("ok\n");    g_pass++; }
    else         { printf("ERROR\n"); g_fail++; }
}

int main(int argc, char **argv)
{
    dssp_t d;
    dssp_init(&d);

    printf("=== DSSP / Setun-70 Forth ===\n");
    printf("Primitives: %d   Kernel size: %d trytes\n\n",
           d.nprim, d.here);

    if (argc > 1 && strcmp(argv[1], "-i") == 0) {
        dssp_repl(&d);
        return 0;
    }

    printf("--- Arithmetic ---\n");
    test(&d, "3 4 + .");
    test(&d, "10 3 - .");
    test(&d, "6 7 * .");
    test(&d, "20 4 / .");
    test(&d, "7 3 mod .");
    test(&d, "5 negate .");
    test(&d, "-8 abs .");
    test(&d, "7 sgn .");
    test(&d, "0 sgn .");

    printf("\n--- Stack ops ---\n");
    test(&d, "1 2 dup .s cr");
    test(&d, "1 2 drop . cr");
    test(&d, "1 2 swap . . cr");
    test(&d, "1 2 over . . . cr");
    test(&d, "1 2 3 rot . . . cr");

    printf("\n--- Comparisons ---\n");
    test(&d, "3 3 = .");
    test(&d, "3 4 = .");
    test(&d, "2 5 < .");
    test(&d, "0 0= .");
    test(&d, "3 0= .");
    test(&d, "-1 0< .");
    test(&d, "5 0> .");

    printf("\n--- Ternary logic (Setun-70 native) ---\n");
    test(&d, "-1 1 and .");
    test(&d, "-1 1 or .");
    test(&d, "1 not .");

    printf("\n--- Ternary output ---\n");
    test(&d, "13 .t");
    test(&d, "7 .t");
    test(&d, "-13 .t");

    printf("\n--- Memory ---\n");
    test(&d, "42 here ! here @ .");

    printf("\n--- Colon definitions ---\n");
    test(&d, ": square dup * ;");
    test(&d, "7 square .");
    test(&d, ": cube dup square * ;");
    test(&d, "3 cube .");
    test(&d, ": twice dup + ;");
    test(&d, "5 twice .");

    printf("\n--- Control flow ---\n");
    test(&d, ": pos? dup 0> if 1 else 0 then nip ;");
    test(&d, "5 pos? .");
    test(&d, "-3 pos? .");

    test(&d, ": count 3 begin dup . 1 - dup 0= until drop ;");
    test(&d, "count cr");

    test(&d, ": sum5 0 1 begin swap over + swap 1 + dup 6 = until drop ;");
    test(&d, "sum5 .");

    printf("\n--- Ternary-specific ---\n");
    test(&d, "1 1 1 and and .");
    test(&d, "-1 0 1 or or .");

    printf("\n=== Results: %d pass, %d fail ===\n", g_pass, g_fail);
    return g_fail ? 1 : 0;
}
