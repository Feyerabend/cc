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


// fwd decl
struct Effect;
struct Continuation;


//   Resume function type

typedef struct Effect (*ResumeFn)(
    struct Continuation* k,
    void* value
);


//   Continuation

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
        struct {
            char* key;
        } get;

        struct {
            char* key;
            int value;
        } put;

        struct {
            void* (*computation)(void*);
            void* arg;
        } async;

        struct {
            char* message;
        } error;

        struct {
            int* choices;
            int count;
        } choice;

    } data;

    Continuation* continuation;
} Effect;


//   Effect constructors

Effect eff_return(void* value);
Effect eff_get(char* key, Continuation* k);
Effect eff_put(char* key, int value, Continuation* k);
Effect eff_error(char* msg);
Effect eff_choose(int* choices, int count, Continuation* k);

#endif // EFFECT_H
