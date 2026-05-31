#include "stateful_strategy.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

KVOperationList* kv_operation_list_create(int capacity) {
    KVOperationList* list = (KVOperationList*)malloc(sizeof(KVOperationList));
    list->capacity = capacity;
    list->count = 0;
    list->operations = (KVOperation*)malloc(capacity * sizeof(KVOperation));
    return list;
}

void kv_operation_list_free(KVOperationList* list) {
    if (list) {
        free(list->operations);
        free(list);
    }
}

void kv_operation_list_append(
    KVOperationList* list,
    OperationType type,
    const char* key,
    const char* value
) {
    if (list->count >= list->capacity) {
        list->capacity *= 2;
        list->operations = (KVOperation*)realloc(
            list->operations,
            list->capacity * sizeof(KVOperation)
        );
    }
    
    KVOperation* op = &list->operations[list->count++];
    op->type = type;
    strncpy(op->key, key, sizeof(op->key) - 1);
    op->key[sizeof(op->key) - 1] = '\0';
    
    if (value) {
        strncpy(op->value, value, sizeof(op->value) - 1);
        op->value[sizeof(op->value) - 1] = '\0';
    } else {
        op->value[0] = '\0';
    }
}

typedef struct {
    int max_keys;
    int max_operations;
} KVContext;

static void* kv_generate(Strategy* strategy, unsigned int* seed, int size) {
    KVContext* ctx = (KVContext*)strategy->context;
    
    int num_ops = rand_range(seed, 1, size < ctx->max_operations ? size : ctx->max_operations);
    KVOperationList* ops = kv_operation_list_create(num_ops + 1);
    
    char active_keys[100][32];
    int active_count = 0;
    
    for (int i = 0; i < num_ops; i++) {
        if (active_count == 0 || rand_range(seed, 0, 100) < 60) {
            int key_num = rand_range(seed, 0, ctx->max_keys - 1);
            char key[32];
            snprintf(key, sizeof(key), "key_%d", key_num);
            
            int value_num = rand_range(seed, 0, 999);
            char value[64];
            snprintf(value, sizeof(value), "value_%d", value_num);
            
            kv_operation_list_append(ops, OP_PUT, key, value);
            
            int found = 0;
            for (int j = 0; j < active_count; j++) {
                if (strcmp(active_keys[j], key) == 0) {
                    found = 1;
                    break;
                }
            }
            
            if (!found && active_count < 100) {
                strncpy(active_keys[active_count++], key, sizeof(active_keys[0]));
            }
        } else {
            int idx = rand_range(seed, 0, active_count - 1);
            const char* key = active_keys[idx];
            
            if (rand_range(seed, 0, 100) < 70) {
                kv_operation_list_append(ops, OP_GET, key, NULL);
            } else {
                kv_operation_list_append(ops, OP_DELETE, key, NULL);
                
                for (int j = idx; j < active_count - 1; j++) {
                    strncpy(active_keys[j], active_keys[j + 1], sizeof(active_keys[0]));
                }
                active_count--;
            }
        }
    }
    
    return ops;
}

static bool kv_shrink_has_next(ShrinkIterator* iter) {
    (void)iter;
    return false;
}

static void* kv_shrink_next(ShrinkIterator* iter) {
    (void)iter;
    return NULL;
}

static void kv_shrink_free(ShrinkIterator* iter) {
    free(iter);
}

static ShrinkIterator* kv_shrink(Strategy* strategy, void* value) {
    (void)strategy;
    (void)value;
    
    ShrinkIterator* iter = (ShrinkIterator*)malloc(sizeof(ShrinkIterator));
    iter->state = NULL;
    iter->current = NULL;
    iter->has_next = kv_shrink_has_next;
    iter->next = kv_shrink_next;
    iter->free_iter = kv_shrink_free;
    
    return iter;
}

static void kv_free_value(void* value) {
    kv_operation_list_free((KVOperationList*)value);
}

Strategy* kv_operation_strategy_create(int max_keys, int max_operations) {
    Strategy* strategy = (Strategy*)malloc(sizeof(Strategy));
    KVContext* ctx = (KVContext*)malloc(sizeof(KVContext));
    
    ctx->max_keys = max_keys;
    ctx->max_operations = max_operations;
    
    strategy->context = ctx;
    strategy->generate = kv_generate;
    strategy->shrink = kv_shrink;
    strategy->free_value = kv_free_value;
    
    return strategy;
}

StackCommandList* stack_command_list_create(int capacity) {
    StackCommandList* list = (StackCommandList*)malloc(sizeof(StackCommandList));
    list->capacity = capacity;
    list->count = 0;
    list->commands = (StackCommand*)malloc(capacity * sizeof(StackCommand));
    return list;
}

void stack_command_list_free(StackCommandList* list) {
    if (list) {
        free(list->commands);
        free(list);
    }
}

void stack_command_list_append(StackCommandList* list, StackCommandType type, int value) {
    if (list->count >= list->capacity) {
        list->capacity *= 2;
        list->commands = (StackCommand*)realloc(
            list->commands,
            list->capacity * sizeof(StackCommand)
        );
    }
    
    StackCommand* cmd = &list->commands[list->count++];
    cmd->type = type;
    cmd->value = value;
}

typedef struct {
    int max_commands;
} StackContext;

static void* stack_generate(Strategy* strategy, unsigned int* seed, int size) {
    StackContext* ctx = (StackContext*)strategy->context;
    
    int num_cmds = rand_range(seed, 1, size < ctx->max_commands ? size : ctx->max_commands);
    StackCommandList* cmds = stack_command_list_create(num_cmds + 1);
    
    int stack_size = 0;
    
    for (int i = 0; i < num_cmds; i++) {
        if (stack_size == 0) {
            int value = rand_range(seed, -100, 100);
            stack_command_list_append(cmds, CMD_PUSH, value);
            stack_size++;
        } else if (stack_size >= 100) {
            stack_command_list_append(cmds, CMD_POP, 0);
            stack_size--;
        } else {
            if (rand_range(seed, 0, 100) < 50) {
                int value = rand_range(seed, -100, 100);
                stack_command_list_append(cmds, CMD_PUSH, value);
                stack_size++;
            } else {
                stack_command_list_append(cmds, CMD_POP, 0);
                stack_size--;
            }
        }
    }
    
    return cmds;
}

static bool stack_shrink_has_next(ShrinkIterator* iter) {
    (void)iter;
    return false;
}

static void* stack_shrink_next(ShrinkIterator* iter) {
    (void)iter;
    return NULL;
}

static void stack_shrink_free(ShrinkIterator* iter) {
    free(iter);
}

static ShrinkIterator* stack_shrink(Strategy* strategy, void* value) {
    (void)strategy;
    (void)value;
    
    ShrinkIterator* iter = (ShrinkIterator*)malloc(sizeof(ShrinkIterator));
    iter->state = NULL;
    iter->current = NULL;
    iter->has_next = stack_shrink_has_next;
    iter->next = stack_shrink_next;
    iter->free_iter = stack_shrink_free;
    
    return iter;
}

static void stack_free_value(void* value) {
    stack_command_list_free((StackCommandList*)value);
}

Strategy* stack_command_strategy_create(int max_commands) {
    Strategy* strategy = (Strategy*)malloc(sizeof(Strategy));
    StackContext* ctx = (StackContext*)malloc(sizeof(StackContext));
    
    ctx->max_commands = max_commands;
    
    strategy->context = ctx;
    strategy->generate = stack_generate;
    strategy->shrink = stack_shrink;
    strategy->free_value = stack_free_value;
    
    return strategy;
}
