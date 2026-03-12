
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include <stdio.h>

#include "effect.h"


/* basic constructors for effects */

Effect eff_return(void* value) {
    Effect e = {.tag = EFF_RETURN, .data.return_val = value};
    return e;
}

Effect eff_get(Continuation* k) {
    Effect e = {.tag = EFF_STATE_GET, .continuation = k};
    return e;
}

Effect eff_put(int value, Continuation* k) {
    Effect e = {.tag = EFF_STATE_PUT, .data.put.value = value, .continuation = k};
    return e;
}

Effect eff_error(char* msg) {
    Effect e = {.tag = EFF_ERROR, .data.error.message = msg};
    return e;
}

Effect eff_choose(int* choices, int count, Continuation* k) {
    Effect e = {
        .tag = EFF_NONDETERMINISM,
        .data.choice.choices = choices,
        .data.choice.count = count,
        .continuation = k
    };
    return e;
}

