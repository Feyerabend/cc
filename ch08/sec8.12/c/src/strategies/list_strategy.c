#include "list_strategy.h"
#include "../types/types.h"
#include <stdlib.h>
#include <string.h>

typedef struct {
    Strategy* element_strategy;
    int max_length;
} ListContext;

typedef struct {
    IntList* original;
    int current_length;
    int shrink_mode;
    int position;
    Strategy* element_strategy;
} ListShrinkState;

static void* list_generate(Strategy* strategy, unsigned int* seed, int size) {
    ListContext* ctx = (ListContext*)strategy->context;
    
    int length = rand_range(seed, 0, size < ctx->max_length ? size : ctx->max_length);
    IntList* list = int_list_create(length + 1);
    
    int sub_size = size > 2 ? size / 2 : 1;
    
    for (int i = 0; i < length; i++) {
        int* element = (int*)ctx->element_strategy->generate(
            ctx->element_strategy,
            seed,
            sub_size
        );
        int_list_append(list, *element);
        ctx->element_strategy->free_value(element);
    }
    
    return list;
}

static bool list_shrink_has_next(ShrinkIterator* iter) {
    ListShrinkState* state = (ListShrinkState*)iter->state;
    
    if (state->shrink_mode == 0) {
        return state->current_length > 0;
    } else if (state->shrink_mode == 1) {
        return state->position < state->original->length;
    }
    
    return false;
}

static void* list_shrink_next(ShrinkIterator* iter) {
    ListShrinkState* state = (ListShrinkState*)iter->state;
    
    if (state->shrink_mode == 0) {
        state->current_length--;
        
        if (state->current_length < 0) {
            state->shrink_mode = 1;
            state->position = 0;
            state->current_length = state->original->length;
            return list_shrink_next(iter);
        }
        
        IntList* result = int_list_create(state->current_length + 1);
        for (int i = 0; i < state->current_length; i++) {
            int_list_append(result, state->original->data[i]);
        }
        
        return result;
    } else if (state->shrink_mode == 1) {
        if (state->position >= state->original->length) {
            return NULL;
        }
        
        int pos = state->position;
        state->position++;
        
        ShrinkIterator* elem_iter = state->element_strategy->shrink(
            state->element_strategy,
            &state->original->data[pos]
        );
        
        if (!elem_iter->has_next(elem_iter)) {
            elem_iter->free_iter(elem_iter);
            return list_shrink_next(iter);
        }
        
        int* shrunken_elem = (int*)elem_iter->next(elem_iter);
        elem_iter->free_iter(elem_iter);
        
        if (shrunken_elem == NULL) {
            return list_shrink_next(iter);
        }
        
        IntList* result = int_list_copy(state->original);
        result->data[pos] = *shrunken_elem;
        free(shrunken_elem);
        
        return result;
    }
    
    return NULL;
}

static void list_shrink_free(ShrinkIterator* iter) {
    if (iter->state) {
        free(iter->state);
    }
    free(iter);
}

static ShrinkIterator* list_shrink(Strategy* strategy, void* value) {
    IntList* list = (IntList*)value;
    ListContext* ctx = (ListContext*)strategy->context;
    
    ShrinkIterator* iter = (ShrinkIterator*)malloc(sizeof(ShrinkIterator));
    ListShrinkState* state = (ListShrinkState*)malloc(sizeof(ListShrinkState));
    
    state->original = list;
    state->current_length = list->length - 1;
    state->shrink_mode = 0;
    state->position = 0;
    state->element_strategy = ctx->element_strategy;
    
    iter->state = state;
    iter->current = NULL;
    iter->has_next = list_shrink_has_next;
    iter->next = list_shrink_next;
    iter->free_iter = list_shrink_free;
    
    return iter;
}

static void list_free_value(void* value) {
    int_list_free((IntList*)value);
}

Strategy* list_strategy_create(Strategy* element_strategy, int max_length) {
    Strategy* strategy = (Strategy*)malloc(sizeof(Strategy));
    ListContext* ctx = (ListContext*)malloc(sizeof(ListContext));
    
    ctx->element_strategy = element_strategy;
    ctx->max_length = max_length;
    
    strategy->context = ctx;
    strategy->generate = list_generate;
    strategy->shrink = list_shrink;
    strategy->free_value = list_free_value;
    
    return strategy;
}
