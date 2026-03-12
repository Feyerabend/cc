
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include <stdio.h>

#include "effect.h"


/* basic constructors for effects */

/* eff_return: Create a return effect with the given value. */
Effect eff_return(void* value) {
    Effect e = {.tag = EFF_RETURN, .data.return_val = value};
    return e;
}

/* eff_get: Create a state get effect with the given continuation. */
Effect eff_get(Continuation* k) {
    Effect e = {.tag = EFF_STATE_GET, .continuation = k};
    return e;
}

/* eff_put: Create a state put effect with the given value and continuation. */
Effect eff_put(int value, Continuation* k) {
    Effect e = {.tag = EFF_STATE_PUT, .data.put.value = value, .continuation = k};
    return e;
}

/* eff_error: Create an error effect with the given message. */
Effect eff_error(char* msg) {
    Effect e = {.tag = EFF_ERROR, .data.error.message = msg};
    return e;
}

/* eff_choose: Create a nondeterministic choice effect with the given choices and continuation. */
Effect eff_choose(int* choices, int count, Continuation* k) {
    Effect e = {
        .tag = EFF_NONDETERMINISM,
        .data.choice.choices = choices,
        .data.choice.count = count,
        .continuation = k
    };
    return e;
}

/*
 * Note: The async effect constructor is not implemented here, as it would require
 * additional infrastructure for handling asynchronous computations, which is beyond
 * the scope of this basic effect system implementation.
*/

