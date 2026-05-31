#include "oneof_strategy.h"
#include <stdlib.h>

typedef struct {
    Strategy** strategies;
    int count;
} OneOfContext;

typedef struct {
    void* value;
    int chosen_index;
    Strategy* chosen_strategy;
} OneOfShrinkState;

static void* oneof_generate(Strategy* strategy, unsigned int* seed, int size) {
    OneOfContext* ctx = (OneOfContext*)strategy->context;
    
    int chosen = rand_range(seed, 0, ctx->count - 1);
    
    return ctx->strategies[chosen]->generate(ctx->strategies[chosen], seed, size);
}

static bool oneof_shrink_has_next(ShrinkIterator* iter) {
    OneOfShrinkState* state = (OneOfShrinkState*)iter->state;
    
    if (state->chosen_strategy == NULL) {
        return false;
    }
    
    ShrinkIterator* inner = state->chosen_strategy->shrink(
        state->chosen_strategy,
        state->value
    );
    
    bool result = inner->has_next(inner);
    inner->free_iter(inner);
    
    return result;
}

static void* oneof_shrink_next(ShrinkIterator* iter) {
    OneOfShrinkState* state = (OneOfShrinkState*)iter->state;
    
    if (state->chosen_strategy == NULL) {
        return NULL;
    }
    
    ShrinkIterator* inner = state->chosen_strategy->shrink(
        state->chosen_strategy,
        state->value
    );
    
    void* result = inner->next(inner);
    inner->free_iter(inner);
    
    return result;
}

static void oneof_shrink_free(ShrinkIterator* iter) {
    if (iter->state) {
        free(iter->state);
    }
    free(iter);
}

static ShrinkIterator* oneof_shrink(Strategy* strategy, void* value) {
    (void)strategy;
    
    ShrinkIterator* iter = (ShrinkIterator*)malloc(sizeof(ShrinkIterator));
    OneOfShrinkState* state = (OneOfShrinkState*)malloc(sizeof(OneOfShrinkState));
    
    state->value = value;
    state->chosen_index = -1;
    state->chosen_strategy = NULL;
    
    iter->state = state;
    iter->current = NULL;
    iter->has_next = oneof_shrink_has_next;
    iter->next = oneof_shrink_next;
    iter->free_iter = oneof_shrink_free;
    
    return iter;
}

static void oneof_free_value(void* value) {
    free(value);
}

Strategy* oneof_strategy_create(Strategy** strategies, int count) {
    Strategy* strategy = (Strategy*)malloc(sizeof(Strategy));
    OneOfContext* ctx = (OneOfContext*)malloc(sizeof(OneOfContext));
    
    ctx->strategies = (Strategy**)malloc(count * sizeof(Strategy*));
    for (int i = 0; i < count; i++) {
        ctx->strategies[i] = strategies[i];
    }
    ctx->count = count;
    
    strategy->context = ctx;
    strategy->generate = oneof_generate;
    strategy->shrink = oneof_shrink;
    strategy->free_value = oneof_free_value;
    
    return strategy;
}
