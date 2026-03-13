#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "effects.h"


// Effect constructors

// Return
Effect eff_return(void* value) {
    Effect e;

    e.tag = EFF_RETURN;
    e.data.return_val = value;
    e.continuation = NULL;

    return e;
}


// State GET
Effect eff_get(char* key, Continuation* k) {
    Effect e;

    e.tag = EFF_STATE_GET;
    e.data.get.key = key;
    e.continuation = k;

    return e;
}


// State PUT
Effect eff_put(char* key, int value, Continuation* k) {
    Effect e;

    e.tag = EFF_STATE_PUT;
    e.data.put.key = key;
    e.data.put.value = value;
    e.continuation = k;

    return e;
}


// Error
Effect eff_error(char* msg) {
    Effect e;

    e.tag = EFF_ERROR;
    e.data.error.message = msg;
    e.continuation = NULL;

    return e;
}


// Nondeterministic choice
Effect eff_choose(int* choices, int count, Continuation* k) {
    Effect e;

    e.tag = EFF_NONDETERMINISM;
    e.data.choice.choices = choices;
    e.data.choice.count = count;
    e.continuation = k;

    return e;
}

