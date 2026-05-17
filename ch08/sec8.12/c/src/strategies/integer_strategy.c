#include "integer_strategy.h"
#include <stdlib.h>

typedef struct {
    int min_value;
    int max_value;
} IntegerContext;

typedef struct {
    int current;
    int original;
    bool finished;
} IntegerShrinkState;

static void* integer_generate(Strategy* strategy, unsigned int* seed, int size) {
    IntegerContext* ctx = (IntegerContext*)strategy->context;
    int range_size = ctx->max_value - ctx->min_value;
    if (size * 10 < range_size) {
        range_size = size * 10;
    }
    
    int max = ctx->min_value + range_size;
    if (max > ctx->max_value) {
        max = ctx->max_value;
    }
    
    int value = rand_range(seed, ctx->min_value, max);
    int* result = (int*)malloc(sizeof(int));
    *result = value;
    return result;
}

static bool integer_shrink_has_next(ShrinkIterator* iter) {
    IntegerShrinkState* state = (IntegerShrinkState*)iter->state;
    return !state->finished;
}

static void* integer_shrink_next(ShrinkIterator* iter) {
    IntegerShrinkState* state = (IntegerShrinkState*)iter->state;
    
    if (state->finished) {
        return NULL;
    }
    
    int* result = (int*)malloc(sizeof(int));
    
    if (state->current == state->original) {
        if (state->original == 0) {
            state->finished = true;
            free(result);
            return NULL;
        }
        *result = 0;
        state->current = state->original;
    } else {
        int abs_current = state->current < 0 ? -state->current : state->current;
        if (abs_current > 1) {
            state->current = state->current / 2;
            *result = state->current;
        } else {
            state->finished = true;
            free(result);
            return NULL;
        }
    }
    
    return result;
}

static void integer_shrink_free(ShrinkIterator* iter) {
    if (iter->state) {
        free(iter->state);
    }
    free(iter);
}

static ShrinkIterator* integer_shrink(Strategy* strategy, void* value) {
    (void)strategy;
    int original = *(int*)value;
    
    ShrinkIterator* iter = (ShrinkIterator*)malloc(sizeof(ShrinkIterator));
    IntegerShrinkState* state = (IntegerShrinkState*)malloc(sizeof(IntegerShrinkState));
    
    state->original = original;
    state->current = original;
    state->finished = false;
    
    iter->state = state;
    iter->current = NULL;
    iter->has_next = integer_shrink_has_next;
    iter->next = integer_shrink_next;
    iter->free_iter = integer_shrink_free;
    
    return iter;
}

static void integer_free_value(void* value) {
    free(value);
}

Strategy* integer_strategy_create(int min_value, int max_value) {
    Strategy* strategy = (Strategy*)malloc(sizeof(Strategy));
    IntegerContext* ctx = (IntegerContext*)malloc(sizeof(IntegerContext));
    
    ctx->min_value = min_value;
    ctx->max_value = max_value;
    
    strategy->context = ctx;
    strategy->generate = integer_generate;
    strategy->shrink = integer_shrink;
    strategy->free_value = integer_free_value;
    
    return strategy;
}
