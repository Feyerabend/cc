#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include "../core/arena.h"
#include "../core/term.h"
#include "../core/eval.h"
#include "../core/parse.h"
#include "../core/check.h"
#include "../core/defs.h"

/*
 * lang -- surface language for the HoTT core.
 *
 * This layer elaborates surface syntax down to core terms and hands them
 * to the core type checker. The core (lambda/core/) is not modified.
 *
 * Planned surface features:
 *   let x : A = t in body      desugared to  (λx. body)(t : A)
 *   let x = t in body          desugared to  (λx. body) t  (type inferred)
 *   λ(x:A)(y:B). body          multi-arg lambda shorthand
 *   where x = t; y = s         trailing where-block
 */

int main(void) {
    printf("lang: surface language (not yet implemented)\n"); // PENDING
    return 0;
}
