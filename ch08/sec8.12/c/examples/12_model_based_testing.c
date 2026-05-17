#include "../src/core/property_test.h"
#include "../src/strategies/integer_strategy.h"
#include "../src/strategies/list_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TABLE_SIZE 16

typedef enum {
    CMD_PUT,
    CMD_GET,
    CMD_DELETE
} CommandType;

typedef struct {
    CommandType type;
    int key;
    int value;
} HashMapCommand;

typedef struct {
    HashMapCommand* commands;
    int length;
    int capacity;
} CommandSequence;

typedef struct HashNode {
    int key;
    int value;
    struct HashNode* next;
} HashNode;

typedef struct {
    HashNode* buckets[TABLE_SIZE];
    int count;
} HashMap;

typedef struct {
    int* keys;
    int* values;
    int count;
    int capacity;
} ReferenceModel;

HashMap* hashmap_create(void) {
    HashMap* map = (HashMap*)malloc(sizeof(HashMap));
    for (int i = 0; i < TABLE_SIZE; i++) {
        map->buckets[i] = NULL;
    }
    map->count = 0;
    return map;
}

int hash_function(int key) {
    return (key < 0 ? -key : key) % TABLE_SIZE;
}

void hashmap_put(HashMap* map, int key, int value) {
    int bucket = hash_function(key);
    
    HashNode* current = map->buckets[bucket];
    while (current != NULL) {
        if (current->key == key) {
            current->value = value;
            return;
        }
        current = current->next;
    }
    
    HashNode* new_node = (HashNode*)malloc(sizeof(HashNode));
    new_node->key = key;
    new_node->value = value;
    new_node->next = map->buckets[bucket];
    map->buckets[bucket] = new_node;
    map->count++;
}

int hashmap_get(HashMap* map, int key, int* found) {
    int bucket = hash_function(key);
    
    HashNode* current = map->buckets[bucket];
    while (current != NULL) {
        if (current->key == key) {
            *found = 1;
            return current->value;
        }
        current = current->next;
    }
    
    *found = 0;
    return 0;
}

void hashmap_remove(HashMap* map, int key) {
    int bucket = hash_function(key);
    
    HashNode** indirect = &map->buckets[bucket];
    while (*indirect != NULL) {
        HashNode* current = *indirect;
        if (current->key == key) {
            *indirect = current->next;
            free(current);
            map->count--;
            return;
        }
        indirect = &current->next;
    }
}

void hashmap_free(HashMap* map) {
    if (map) {
        for (int i = 0; i < TABLE_SIZE; i++) {
            HashNode* current = map->buckets[i];
            while (current != NULL) {
                HashNode* next = current->next;
                free(current);
                current = next;
            }
        }
        free(map);
    }
}

ReferenceModel* model_create(void) {
    ReferenceModel* model = (ReferenceModel*)malloc(sizeof(ReferenceModel));
    model->capacity = 10;
    model->keys = (int*)malloc(model->capacity * sizeof(int));
    model->values = (int*)malloc(model->capacity * sizeof(int));
    model->count = 0;
    return model;
}

void model_put(ReferenceModel* model, int key, int value) {
    for (int i = 0; i < model->count; i++) {
        if (model->keys[i] == key) {
            model->values[i] = value;
            return;
        }
    }
    
    if (model->count >= model->capacity) {
        model->capacity *= 2;
        model->keys = (int*)realloc(model->keys, model->capacity * sizeof(int));
        model->values = (int*)realloc(model->values, model->capacity * sizeof(int));
    }
    
    model->keys[model->count] = key;
    model->values[model->count] = value;
    model->count++;
}

int model_get(ReferenceModel* model, int key, int* found) {
    for (int i = 0; i < model->count; i++) {
        if (model->keys[i] == key) {
            *found = 1;
            return model->values[i];
        }
    }
    *found = 0;
    return 0;
}

void model_remove(ReferenceModel* model, int key) {
    for (int i = 0; i < model->count; i++) {
        if (model->keys[i] == key) {
            for (int j = i; j < model->count - 1; j++) {
                model->keys[j] = model->keys[j + 1];
                model->values[j] = model->values[j + 1];
            }
            model->count--;
            return;
        }
    }
}

void model_free(ReferenceModel* model) {
    if (model) {
        free(model->keys);
        free(model->values);
        free(model);
    }
}

typedef struct {
    HashMap* implementation;
    ReferenceModel* model;
} ModelBasedState;

void* model_based_init(void) {
    ModelBasedState* state = (ModelBasedState*)malloc(sizeof(ModelBasedState));
    state->implementation = hashmap_create();
    state->model = model_create();
    return state;
}

void model_based_cleanup(void* state_ptr) {
    ModelBasedState* state = (ModelBasedState*)state_ptr;
    hashmap_free(state->implementation);
    model_free(state->model);
    free(state);
}

void model_based_apply(void* state_ptr, HashMapCommand* cmd) {
    ModelBasedState* state = (ModelBasedState*)state_ptr;
    
    int key = cmd->key;
    int value = cmd->value;
    
    if (cmd->type == CMD_PUT) {
        hashmap_put(state->implementation, key, value);
        model_put(state->model, key, value);
    } else if (cmd->type == CMD_GET) {
        int impl_found = 0, model_found = 0;
        int impl_value = hashmap_get(state->implementation, key, &impl_found);
        int model_value = model_get(state->model, key, &model_found);
        
        if (impl_found != model_found) {
            longjmp(property_test_jmp_buf, 1);
        }
        if (impl_found && impl_value != model_value) {
            longjmp(property_test_jmp_buf, 1);
        }
    } else if (cmd->type == CMD_DELETE) {
        hashmap_remove(state->implementation, key);
        model_remove(state->model, key);
    }
}

int model_based_check(void* state_ptr) {
    ModelBasedState* state = (ModelBasedState*)state_ptr;
    
    if (state->implementation->count != state->model->count) {
        return 0;
    }
    
    for (int i = 0; i < state->model->count; i++) {
        int key = state->model->keys[i];
        int model_value = state->model->values[i];
        
        int impl_found = 0;
        int impl_value = hashmap_get(state->implementation, key, &impl_found);
        
        if (!impl_found || impl_value != model_value) {
            return 0;
        }
    }
    
    return 1;
}

CommandSequence* generate_command_sequence(int max_commands, unsigned int* seed) {
    CommandSequence* seq = (CommandSequence*)malloc(sizeof(CommandSequence));
    seq->capacity = max_commands;
    seq->commands = (HashMapCommand*)malloc(max_commands * sizeof(HashMapCommand));
    
    srand(*seed);
    
    int num_commands = (rand() % max_commands) + 1;
    seq->length = num_commands;
    
    int* known_keys = (int*)malloc(max_commands * sizeof(int));
    int known_count = 0;
    
    for (int i = 0; i < num_commands; i++) {
        int op = rand() % 10;
        
        if (op < 5 || known_count == 0) {
            seq->commands[i].type = CMD_PUT;
            seq->commands[i].key = rand() % 20;
            seq->commands[i].value = rand() % 100;
            
            int already_known = 0;
            for (int j = 0; j < known_count; j++) {
                if (known_keys[j] == seq->commands[i].key) {
                    already_known = 1;
                    break;
                }
            }
            if (!already_known && known_count < max_commands) {
                known_keys[known_count++] = seq->commands[i].key;
            }
        } else if (op < 8) {
            seq->commands[i].type = CMD_GET;
            seq->commands[i].key = known_keys[rand() % known_count];
            seq->commands[i].value = 0;
        } else {
            seq->commands[i].type = CMD_DELETE;
            int idx = rand() % known_count;
            seq->commands[i].key = known_keys[idx];
            seq->commands[i].value = 0;
            
            for (int j = idx; j < known_count - 1; j++) {
                known_keys[j] = known_keys[j + 1];
            }
            known_count--;
            if (known_count == 0) known_count = 1;
        }
    }
    
    free(known_keys);
    return seq;
}

void command_sequence_free(CommandSequence* seq) {
    if (seq) {
        free(seq->commands);
        free(seq);
    }
}

void test_hashmap_matches_model(void* input) {
    IntList* params = (IntList*)input;
    
    unsigned int seed = (unsigned int)time(NULL) + params->length;
    CommandSequence* seq = generate_command_sequence(20, &seed);
    
    ModelBasedState* state = (ModelBasedState*)model_based_init();
    
    for (int i = 0; i < seq->length; i++) {
        model_based_apply(state, &seq->commands[i]);
    }
    
    PROPERTY_ASSERT(model_based_check(state));
    
    model_based_cleanup(state);
    command_sequence_free(seq);
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
    printf("Property-Based Testing - Model-Based Testing\n");
    printf("============================================\n\n");
    
    printf("Testing HashMap Against Reference Model:\n");
    printf("----------------------------------------\n");
    
    Strategy* int_strategy = integer_strategy_create(0, 10);
    Strategy* list_strategy = list_strategy_create(int_strategy, 5);
    
    run_property_test(
        "HashMap implementation matches simple reference model",
        test_hashmap_matches_model,
        list_strategy,
        100
    );
    
    strategy_free(list_strategy);
    strategy_free(int_strategy);
    
    printf("All tests completed.\n");
    printf("\nModel-Based Testing Pattern:\n");
    printf("  Compare complex implementation against simple model:\n");
    printf("  - Implementation: Fast hash table with buckets/chaining\n");
    printf("  - Model: Simple array-based list (slow but obviously correct)\n");
    printf("  - Test: Both produce same results for all operations\n");
    printf("\nAdvantages:\n");
    printf("  - Don't need to know 'correct' output\n");
    printf("  - Model is simple enough to trust\n");
    printf("  - Finds subtle implementation bugs\n");
    printf("  - Tests consistency, not correctness\n");
    
    return 0;
}
