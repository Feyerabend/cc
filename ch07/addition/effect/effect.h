#ifndef EFFECT_H
#define EFFECT_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef enum {
    EFF_RETURN,
    EFF_STATE_GET,
    EFF_STATE_PUT,
    EFF_ASYNC,
    EFF_ERROR,
    EFF_NONDETERMINISM
} EffectTag;

// Forward decl
struct Effect;
struct Continuation;

typedef struct Effect (*ResumeFn)(struct Continuation* k, void* value);

// Continuation structure
typedef struct Continuation {
    ResumeFn resume;
    void* context;
    struct Continuation* parent;
} Continuation;

// Effect structure
typedef struct Effect {
    EffectTag tag;
    union {
        void* return_val;
        struct { int dummy; } get;
        struct { int value; } put;
        struct { void* (*computation)(void*); void* arg; } async;
        struct { char* message; } error;
        struct { int* choices; int count; } choice;
    } data;
    Continuation* continuation;
} Effect;

/* Effect constructors */
extern Effect eff_return(void* value);
extern Effect eff_get(Continuation* k);
extern Effect eff_put(int value, Continuation* k);
extern Effect eff_error(char* msg);
extern Effect eff_choose(int* choices, int count, Continuation* k);

#endif // EFFECT_H
