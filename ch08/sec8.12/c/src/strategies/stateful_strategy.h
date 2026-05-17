#ifndef STATEFUL_STRATEGY_H
#define STATEFUL_STRATEGY_H

#include "../core/property_test.h"

typedef enum {
    OP_PUT,
    OP_GET,
    OP_DELETE
} OperationType;

typedef struct {
    OperationType type;
    char key[32];
    char value[64];
} KVOperation;

typedef struct {
    KVOperation* operations;
    int count;
    int capacity;
} KVOperationList;

KVOperationList* kv_operation_list_create(int capacity);
void kv_operation_list_free(KVOperationList* list);
void kv_operation_list_append(
    KVOperationList* list,
    OperationType type,
    const char* key,
    const char* value
);

Strategy* kv_operation_strategy_create(int max_keys, int max_operations);

typedef enum {
    CMD_PUSH,
    CMD_POP
} StackCommandType;

typedef struct {
    StackCommandType type;
    int value;
} StackCommand;

typedef struct {
    StackCommand* commands;
    int count;
    int capacity;
} StackCommandList;

StackCommandList* stack_command_list_create(int capacity);
void stack_command_list_free(StackCommandList* list);
void stack_command_list_append(StackCommandList* list, StackCommandType type, int value);

Strategy* stack_command_strategy_create(int max_commands);

#endif
