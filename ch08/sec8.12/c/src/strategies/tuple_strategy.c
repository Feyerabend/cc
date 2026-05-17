#include "tuple_strategy.h"
#include <stdlib.h>

typedef struct {
    Strategy* first_strategy;
    Strategy* second_strategy;
} Tuple2Context;

typedef struct {
    Strategy* first_strategy;
    Strategy* second_strategy;
    Strategy* third_strategy;
} Tuple3Context;

typedef struct {
    Tuple2* original;
    int shrink_mode;
    Strategy* first_strategy;
    Strategy* second_strategy;
    ShrinkIterator* current_iter;
} Tuple2ShrinkState;

typedef struct {
    Tuple3* original;
    int shrink_mode;
    Strategy* first_strategy;
    Strategy* second_strategy;
    Strategy* third_strategy;
    ShrinkIterator* current_iter;
} Tuple3ShrinkState;

static void* tuple2_generate(Strategy* strategy, unsigned int* seed, int size) {
    Tuple2Context* ctx = (Tuple2Context*)strategy->context;
    
    void* first = ctx->first_strategy->generate(ctx->first_strategy, seed, size);
    void* second = ctx->second_strategy->generate(ctx->second_strategy, seed, size);
    
    return tuple2_create(first, second);
}

static bool tuple2_shrink_has_next(ShrinkIterator* iter) {
    Tuple2ShrinkState* state = (Tuple2ShrinkState*)iter->state;
    
    if (state->shrink_mode == 0) {
        if (state->current_iter == NULL) {
            state->current_iter = state->first_strategy->shrink(
                state->first_strategy,
                state->original->first
            );
        }
        return state->current_iter->has_next(state->current_iter);
    } else if (state->shrink_mode == 1) {
        if (state->current_iter == NULL) {
            state->current_iter = state->second_strategy->shrink(
                state->second_strategy,
                state->original->second
            );
        }
        return state->current_iter->has_next(state->current_iter);
    }
    
    return false;
}

static void* tuple2_shrink_next(ShrinkIterator* iter) {
    Tuple2ShrinkState* state = (Tuple2ShrinkState*)iter->state;
    
    if (state->shrink_mode == 0) {
        void* shrunken_first = state->current_iter->next(state->current_iter);
        
        if (shrunken_first == NULL) {
            state->current_iter->free_iter(state->current_iter);
            state->current_iter = NULL;
            state->shrink_mode = 1;
            return tuple2_shrink_next(iter);
        }
        
        void* second_copy = state->second_strategy->generate(
            state->second_strategy,
            &(unsigned int){0},
            0
        );
        
        return tuple2_create(shrunken_first, second_copy);
    } else if (state->shrink_mode == 1) {
        void* shrunken_second = state->current_iter->next(state->current_iter);
        
        if (shrunken_second == NULL) {
            return NULL;
        }
        
        void* first_copy = state->first_strategy->generate(
            state->first_strategy,
            &(unsigned int){0},
            0
        );
        
        return tuple2_create(first_copy, shrunken_second);
    }
    
    return NULL;
}

static void tuple2_shrink_free(ShrinkIterator* iter) {
    Tuple2ShrinkState* state = (Tuple2ShrinkState*)iter->state;
    if (state->current_iter) {
        state->current_iter->free_iter(state->current_iter);
    }
    free(state);
    free(iter);
}

static ShrinkIterator* tuple2_shrink(Strategy* strategy, void* value) {
    Tuple2Context* ctx = (Tuple2Context*)strategy->context;
    Tuple2* tuple = (Tuple2*)value;
    
    ShrinkIterator* iter = (ShrinkIterator*)malloc(sizeof(ShrinkIterator));
    Tuple2ShrinkState* state = (Tuple2ShrinkState*)malloc(sizeof(Tuple2ShrinkState));
    
    state->original = tuple;
    state->shrink_mode = 0;
    state->first_strategy = ctx->first_strategy;
    state->second_strategy = ctx->second_strategy;
    state->current_iter = NULL;
    
    iter->state = state;
    iter->current = NULL;
    iter->has_next = tuple2_shrink_has_next;
    iter->next = tuple2_shrink_next;
    iter->free_iter = tuple2_shrink_free;
    
    return iter;
}

static void tuple2_free_value(void* value) {
    tuple2_free((Tuple2*)value, free, free);
}

Strategy* tuple2_strategy_create(
    Strategy* first_strategy,
    Strategy* second_strategy
) {
    Strategy* strategy = (Strategy*)malloc(sizeof(Strategy));
    Tuple2Context* ctx = (Tuple2Context*)malloc(sizeof(Tuple2Context));
    
    ctx->first_strategy = first_strategy;
    ctx->second_strategy = second_strategy;
    
    strategy->context = ctx;
    strategy->generate = tuple2_generate;
    strategy->shrink = tuple2_shrink;
    strategy->free_value = tuple2_free_value;
    
    return strategy;
}

static void* tuple3_generate(Strategy* strategy, unsigned int* seed, int size) {
    Tuple3Context* ctx = (Tuple3Context*)strategy->context;
    
    void* first = ctx->first_strategy->generate(ctx->first_strategy, seed, size);
    void* second = ctx->second_strategy->generate(ctx->second_strategy, seed, size);
    void* third = ctx->third_strategy->generate(ctx->third_strategy, seed, size);
    
    return tuple3_create(first, second, third);
}

static void tuple3_free_value(void* value) {
    tuple3_free((Tuple3*)value, free, free, free);
}

static ShrinkIterator* tuple3_shrink(Strategy* strategy, void* value) {
    (void)strategy;
    (void)value;
    
    ShrinkIterator* iter = (ShrinkIterator*)malloc(sizeof(ShrinkIterator));
    iter->state = NULL;
    iter->current = NULL;
    iter->has_next = NULL;
    iter->next = NULL;
    iter->free_iter = tuple2_shrink_free;
    
    return iter;
}

Strategy* tuple3_strategy_create(
    Strategy* first_strategy,
    Strategy* second_strategy,
    Strategy* third_strategy
) {
    Strategy* strategy = (Strategy*)malloc(sizeof(Strategy));
    Tuple3Context* ctx = (Tuple3Context*)malloc(sizeof(Tuple3Context));
    
    ctx->first_strategy = first_strategy;
    ctx->second_strategy = second_strategy;
    ctx->third_strategy = third_strategy;
    
    strategy->context = ctx;
    strategy->generate = tuple3_generate;
    strategy->shrink = tuple3_shrink;
    strategy->free_value = tuple3_free_value;
    
    return strategy;
}
