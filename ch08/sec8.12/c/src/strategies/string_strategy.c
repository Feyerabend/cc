#include "string_strategy.h"
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

typedef struct {
    char* alphabet;
    int alphabet_len;
    int max_length;
} StringContext;

typedef struct {
    String* original;
    int shrink_mode;
    int current_length;
    int position;
} StringShrinkState;

static void* string_generate(Strategy* strategy, unsigned int* seed, int size) {
    StringContext* ctx = (StringContext*)strategy->context;
    
    int length = rand_range(
        seed,
        0,
        size < ctx->max_length ? size : ctx->max_length
    );
    
    String* str = string_create(length + 1);
    
    for (int i = 0; i < length; i++) {
        int idx = rand_range(seed, 0, ctx->alphabet_len - 1);
        string_append_char(str, ctx->alphabet[idx]);
    }
    
    return str;
}

static bool string_shrink_has_next(ShrinkIterator* iter) {
    StringShrinkState* state = (StringShrinkState*)iter->state;
    
    if (state->shrink_mode == 0) {
        return state->current_length >= 0;
    } else if (state->shrink_mode == 1) {
        return state->position < state->original->length;
    } else if (state->shrink_mode == 2) {
        return state->position < state->original->length;
    }
    
    return false;
}

static void* string_shrink_next(ShrinkIterator* iter) {
    StringShrinkState* state = (StringShrinkState*)iter->state;
    
    if (state->shrink_mode == 0) {
        if (state->current_length < 0) {
            state->shrink_mode = 1;
            state->position = 0;
            return string_shrink_next(iter);
        }
        
        String* result = string_create(state->current_length + 1);
        if (state->current_length > 0) {
            string_append(result, state->original->data, state->current_length);
        }
        
        state->current_length--;
        return result;
    } else if (state->shrink_mode == 1) {
        while (state->position < state->original->length) {
            char c = state->original->data[state->position];
            int pos = state->position;
            state->position++;
            
            if (isalpha(c) && tolower(c) != 'a') {
                String* result = string_copy(state->original);
                char new_char = (char)(tolower(c) - 1);
                if (new_char < 'a') {
                    new_char = 'a';
                }
                result->data[pos] = new_char;
                return result;
            }
        }
        
        state->shrink_mode = 2;
        state->position = 0;
        return string_shrink_next(iter);
    } else if (state->shrink_mode == 2) {
        if (state->position >= state->original->length) {
            return NULL;
        }
        
        int pos = state->position;
        state->position++;
        
        String* result = string_create(state->original->length);
        
        if (pos > 0) {
            string_append(result, state->original->data, pos);
        }
        if (pos + 1 < state->original->length) {
            string_append(
                result,
                state->original->data + pos + 1,
                state->original->length - pos - 1
            );
        }
        
        return result;
    }
    
    return NULL;
}

static void string_shrink_free(ShrinkIterator* iter) {
    if (iter->state) {
        free(iter->state);
    }
    free(iter);
}

static ShrinkIterator* string_shrink(Strategy* strategy, void* value) {
    (void)strategy;
    String* str = (String*)value;
    
    ShrinkIterator* iter = (ShrinkIterator*)malloc(sizeof(ShrinkIterator));
    StringShrinkState* state = (StringShrinkState*)malloc(sizeof(StringShrinkState));
    
    state->original = str;
    state->shrink_mode = 0;
    state->current_length = str->length - 1;
    state->position = 0;
    
    iter->state = state;
    iter->current = NULL;
    iter->has_next = string_shrink_has_next;
    iter->next = string_shrink_next;
    iter->free_iter = string_shrink_free;
    
    return iter;
}

static void string_free_value(void* value) {
    string_free((String*)value);
}

Strategy* string_strategy_create(const char* alphabet, int max_length) {
    Strategy* strategy = (Strategy*)malloc(sizeof(Strategy));
    StringContext* ctx = (StringContext*)malloc(sizeof(StringContext));
    
    if (alphabet == NULL) {
        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789";
    }
    
    ctx->alphabet_len = strlen(alphabet);
    ctx->alphabet = (char*)malloc(ctx->alphabet_len + 1);
    strcpy(ctx->alphabet, alphabet);
    ctx->max_length = max_length;
    
    strategy->context = ctx;
    strategy->generate = string_generate;
    strategy->shrink = string_shrink;
    strategy->free_value = string_free_value;
    
    return strategy;
}
