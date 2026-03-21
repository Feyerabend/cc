/*
 * sandbox.c — word whitelist for pico-lambda
 *
 * After forth_init() builds the full dictionary, sandbox_install()
 * hides everything not on the whitelist below.  Hidden words are
 * invisible to the interpreter: typing them produces "?: name" just
 * as if they had never existed.
 *
 * Words blocked and why:
 *   C@  C!         — byte-level memory access; can read/write RP2350 peripherals
 *   +!             — in-place store; harder to reason about in sandboxed code
 *   CELLS          — pointer arithmetic helper; not needed without ALLOT/HERE
 *   EXECUTE  '     — execute arbitrary word by index; combined they can invoke
 *                    internal executor tokens and corrupt interpreter state
 *   [ ] LITERAL    — switch in/out of compile mode at runtime; meta-programming
 *   IMMEDIATE      — retroactively change a word's parse behaviour
 *   LSHIFT RSHIFT  — bit-shifting on untrusted input is fine arithmetically but
 *                    shifts by large amounts on addresses could craft pointers;
 *                    excluded for simplicity (not in the spec's keep list)
 *   HEX DECIMAL    — change the number base mid-expression; surprising behaviour
 *                    for callers who don't expect hex output from "."
 *   COUNT          — counted-string helper; no use without raw memory access
 *   CHAR           — push ASCII value of next token; not in spec's keep list
 *   U.             — unsigned print; not in spec's keep list
 *   AGAIN          — infinite loop construct; BEGIN..AGAIN has no exit condition.
 *                    The step counter will catch it but better to block outright.
 *   LEAVE          — early exit from DO..LOOP; not in spec's keep list
 *   I  J           — DO..LOOP index access; not in spec's keep list
 *   NIP TUCK       — extra stack ops; not in spec's keep list
 *   2DUP 2DROP 2SWAP DEPTH ?DUP  — same as above
 *   /MOD           — quotient-and-remainder; not in spec's keep list
 *   XOR INVERT     — bitwise; NOT covers logical negation, XOR/INVERT are extra
 *   TRUE FALSE     — constants; callers can use 0= or -1 directly
 *   0<> 0< 0>      — extra zero-comparisons; not in spec's keep list
 *   NEGATE ABS 1+ 1- 2+ 2* 2/ MAX MIN  — extra arithmetic; not in spec list
 *   SPACE SPACES   — whitespace output; CR and EMIT cover this
 *   S"             — string address/length pair; useful but not in spec list
 *   EXIT           — early return from word; not in spec's keep list
 *   WORDS          — introspection; disable in production, useful when debugging
 *
 * To re-enable any blocked word for debugging, add its name to the
 * ALLOWED array below and reflash.
 */

#include "sandbox.h"
#include "forth.h"

static const char *ALLOWED[] = {
    /* Arithmetic */
    "+", "-", "*", "/", "MOD",

    /* Stack */
    "DUP", "DROP", "SWAP", "OVER", "ROT",

    /* Comparison */
    "=", "<>", "<", ">", "<=", ">=",

    /* Logic */
    "AND", "OR", "NOT",

    /* Control flow */
    "IF", "ELSE", "THEN",
    "BEGIN", "WHILE", "REPEAT", "UNTIL",

    /* Output */
    ".", ".S", "EMIT", "CR",

    /* String literals — ." is compile-time so the token ." must be allowed */
    ".\"",

    /* Word definition */
    ":", ";",

    /* Defining words */
    "CONSTANT", "VARIABLE",

    /* Memory — @ and ! only reach addresses returned by VARIABLE,
     * which live in the interpreter's internal vp[] pool */
    "@", "!",

    /* Comments — needed so users can annotate their code */
    "(", "\\",
};

#define ALLOWED_COUNT ((int)(sizeof(ALLOWED) / sizeof(ALLOWED[0])))

void sandbox_install(void)
{
    forth_restrict_to(ALLOWED, ALLOWED_COUNT);
}
