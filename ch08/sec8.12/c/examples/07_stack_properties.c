#include "../src/core/property_test.h"
#include "../src/strategies/stateful_strategy.h"
#include <stdio.h>
#include <stdlib.h>

typedef struct StackNode {
    int value;
    struct StackNode* next;
} StackNode;

typedef struct {
    StackNode* top;
    int size;
} Stack;

Stack* stack_create(void) {
    Stack* stack = (Stack*)malloc(sizeof(Stack));
    stack->top = NULL;
    stack->size = 0;
    return stack;
}

void stack_free(Stack* stack) {
    if (stack) {
        StackNode* current = stack->top;
        while (current) {
            StackNode* next = current->next;
            free(current);
            current = next;
        }
        free(stack);
    }
}

void stack_push(Stack* stack, int value) {
    StackNode* node = (StackNode*)malloc(sizeof(StackNode));
    node->value = value;
    node->next = stack->top;
    stack->top = node;
    stack->size++;
}

bool stack_pop(Stack* stack, int* out_value) {
    if (stack->top == NULL) {
        return false;
    }
    
    StackNode* node = stack->top;
    *out_value = node->value;
    stack->top = node->next;
    stack->size--;
    free(node);
    
    return true;
}

bool stack_is_empty(Stack* stack) {
    return stack->top == NULL;
}

int stack_size(Stack* stack) {
    return stack->size;
}

void test_stack_preconditions(void* input) {
    StackCommandList* cmds = (StackCommandList*)input;
    
    Stack* stack = stack_create();
    
    for (int i = 0; i < cmds->count; i++) {
        StackCommand* cmd = &cmds->commands[i];
        
        if (cmd->type == CMD_PUSH) {
            stack_push(stack, cmd->value);
        } else if (cmd->type == CMD_POP) {
            int value;
            bool success = stack_pop(stack, &value);
            PROPERTY_ASSERT(success);
        }
    }
    
    stack_free(stack);
}

void test_stack_size_tracking(void* input) {
    StackCommandList* cmds = (StackCommandList*)input;
    
    Stack* stack = stack_create();
    int expected_size = 0;
    
    for (int i = 0; i < cmds->count; i++) {
        StackCommand* cmd = &cmds->commands[i];
        
        if (cmd->type == CMD_PUSH) {
            stack_push(stack, cmd->value);
            expected_size++;
        } else if (cmd->type == CMD_POP) {
            int value;
            bool success = stack_pop(stack, &value);
            PROPERTY_ASSERT(success);
            expected_size--;
        }
        
        PROPERTY_ASSERT(stack_size(stack) == expected_size);
    }
    
    stack_free(stack);
}

void test_stack_push_pop_roundtrip(void* input) {
    StackCommandList* cmds = (StackCommandList*)input;
    
    Stack* stack = stack_create();
    int push_values[1000];
    int push_count = 0;
    
    for (int i = 0; i < cmds->count; i++) {
        StackCommand* cmd = &cmds->commands[i];
        
        if (cmd->type == CMD_PUSH) {
            stack_push(stack, cmd->value);
            if (push_count < 1000) {
                push_values[push_count++] = cmd->value;
            }
        } else if (cmd->type == CMD_POP) {
            int value;
            bool success = stack_pop(stack, &value);
            PROPERTY_ASSERT(success);
            
            if (push_count > 0) {
                PROPERTY_ASSERT(value == push_values[--push_count]);
            }
        }
    }
    
    stack_free(stack);
}

void test_stack_empty_consistency(void* input) {
    StackCommandList* cmds = (StackCommandList*)input;
    
    Stack* stack = stack_create();
    
    for (int i = 0; i < cmds->count; i++) {
        StackCommand* cmd = &cmds->commands[i];
        
        bool was_empty = stack_is_empty(stack);
        
        if (cmd->type == CMD_PUSH) {
            stack_push(stack, cmd->value);
            PROPERTY_ASSERT(!stack_is_empty(stack));
        } else if (cmd->type == CMD_POP) {
            PROPERTY_ASSERT(!was_empty);
            
            int value;
            bool success = stack_pop(stack, &value);
            PROPERTY_ASSERT(success);
        }
        
        PROPERTY_ASSERT(stack_is_empty(stack) == (stack_size(stack) == 0));
    }
    
    stack_free(stack);
}

void run_property_test(
    const char* name,
    PropertyFn property,
    Strategy* strategy,
    int max_examples
) {
    printf("Running: %s\n", name);
    
    TestResult* result = test_property(
        property,
        strategy,
        max_examples,
        (unsigned int)time(NULL)
    );
    
    if (result->passed) {
        printf("  ✓ PASSED (%d examples in %.3fs)\n",
               result->examples_tried,
               result->execution_time);
    } else {
        printf("  ✗ FAILED after %d examples\n", result->examples_tried);
        printf("    Shrink iterations: %d\n", result->shrink_iterations);
    }
    
    test_result_free(result);
    printf("\n");
}

int main(void) {
    printf("Property-Based Testing - Stack (Stateful Commands)\n");
    printf("==================================================\n\n");
    
    Strategy* stack_strategy = stack_command_strategy_create(100);
    
    printf("Testing Stack Command Sequences:\n");
    printf("--------------------------------\n");
    
    run_property_test(
        "Stack: Pop precondition (never pops empty stack)",
        test_stack_preconditions,
        stack_strategy,
        100
    );
    
    run_property_test(
        "Stack: Size tracking remains consistent",
        test_stack_size_tracking,
        stack_strategy,
        100
    );
    
    run_property_test(
        "Stack: Push/Pop roundtrip (LIFO order preserved)",
        test_stack_push_pop_roundtrip,
        stack_strategy,
        100
    );
    
    run_property_test(
        "Stack: Empty state matches size == 0",
        test_stack_empty_consistency,
        stack_strategy,
        100
    );
    
    strategy_free(stack_strategy);
    
    printf("All tests completed.\n");
    printf("\nNote: This demonstrates stateful property testing:\n");
    printf("  - Commands have preconditions (can't pop empty)\n");
    printf("  - State evolves through command sequence\n");
    printf("  - LIFO ordering preserved across operations\n");
    printf("  - Invariants checked after each command\n");
    printf("\nThis parallels the 'Stateful Property Testing' section in the book.\n");
    
    return 0;
}
