#include "../src/core/property_test.h"
#include "../src/strategies/stateful_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct KVNode {
    char key[32];
    char value[64];
    struct KVNode* next;
} KVNode;

typedef struct {
    KVNode* head;
    int size;
} KeyValueStore;

KeyValueStore* kv_store_create(void) {
    KeyValueStore* store = (KeyValueStore*)malloc(sizeof(KeyValueStore));
    store->head = NULL;
    store->size = 0;
    return store;
}

void kv_store_free(KeyValueStore* store) {
    if (store) {
        KVNode* current = store->head;
        while (current) {
            KVNode* next = current->next;
            free(current);
            current = next;
        }
        free(store);
    }
}

void kv_store_put(KeyValueStore* store, const char* key, const char* value) {
    KVNode* current = store->head;
    while (current) {
        if (strcmp(current->key, key) == 0) {
            strncpy(current->value, value, sizeof(current->value) - 1);
            current->value[sizeof(current->value) - 1] = '\0';
            return;
        }
        current = current->next;
    }
    
    KVNode* node = (KVNode*)malloc(sizeof(KVNode));
    strncpy(node->key, key, sizeof(node->key) - 1);
    node->key[sizeof(node->key) - 1] = '\0';
    strncpy(node->value, value, sizeof(node->value) - 1);
    node->value[sizeof(node->value) - 1] = '\0';
    node->next = store->head;
    store->head = node;
    store->size++;
}

bool kv_store_get(KeyValueStore* store, const char* key, char* out_value) {
    KVNode* current = store->head;
    while (current) {
        if (strcmp(current->key, key) == 0) {
            strcpy(out_value, current->value);
            return true;
        }
        current = current->next;
    }
    return false;
}

bool kv_store_delete(KeyValueStore* store, const char* key) {
    KVNode** indirect = &store->head;
    
    while (*indirect) {
        KVNode* current = *indirect;
        if (strcmp(current->key, key) == 0) {
            *indirect = current->next;
            free(current);
            store->size--;
            return true;
        }
        indirect = &current->next;
    }
    
    return false;
}

bool kv_store_contains(KeyValueStore* store, const char* key) {
    KVNode* current = store->head;
    while (current) {
        if (strcmp(current->key, key) == 0) {
            return true;
        }
        current = current->next;
    }
    return false;
}

void test_kv_put_then_get(void* input) {
    KVOperationList* ops = (KVOperationList*)input;
    
    KeyValueStore* store = kv_store_create();
    
    for (int i = 0; i < ops->count; i++) {
        KVOperation* op = &ops->operations[i];
        
        if (op->type == OP_PUT) {
            kv_store_put(store, op->key, op->value);
            
            char retrieved[64];
            bool found = kv_store_get(store, op->key, retrieved);
            
            PROPERTY_ASSERT(found);
            PROPERTY_ASSERT(strcmp(retrieved, op->value) == 0);
        } else if (op->type == OP_GET) {
            char retrieved[64];
            bool found = kv_store_get(store, op->key, retrieved);
            
            PROPERTY_ASSERT(found);
        } else if (op->type == OP_DELETE) {
            bool existed = kv_store_delete(store, op->key);
            
            PROPERTY_ASSERT(existed);
            PROPERTY_ASSERT(!kv_store_contains(store, op->key));
        }
    }
    
    kv_store_free(store);
}

void test_kv_shadow_state(void* input) {
    KVOperationList* ops = (KVOperationList*)input;
    
    KeyValueStore* store = kv_store_create();
    KeyValueStore* shadow = kv_store_create();
    
    for (int i = 0; i < ops->count; i++) {
        KVOperation* op = &ops->operations[i];
        
        if (op->type == OP_PUT) {
            kv_store_put(store, op->key, op->value);
            kv_store_put(shadow, op->key, op->value);
            
            PROPERTY_ASSERT(kv_store_contains(store, op->key));
            PROPERTY_ASSERT(kv_store_contains(shadow, op->key));
        } else if (op->type == OP_GET) {
            char store_value[64];
            char shadow_value[64];
            
            bool store_found = kv_store_get(store, op->key, store_value);
            bool shadow_found = kv_store_get(shadow, op->key, shadow_value);
            
            PROPERTY_ASSERT(store_found == shadow_found);
            
            if (store_found) {
                PROPERTY_ASSERT(strcmp(store_value, shadow_value) == 0);
            }
        } else if (op->type == OP_DELETE) {
            bool store_existed = kv_store_delete(store, op->key);
            bool shadow_existed = kv_store_delete(shadow, op->key);
            
            PROPERTY_ASSERT(store_existed == shadow_existed);
            PROPERTY_ASSERT(!kv_store_contains(store, op->key));
            PROPERTY_ASSERT(!kv_store_contains(shadow, op->key));
        }
    }
    
    PROPERTY_ASSERT(store->size == shadow->size);
    
    kv_store_free(store);
    kv_store_free(shadow);
}

void test_kv_size_consistency(void* input) {
    KVOperationList* ops = (KVOperationList*)input;
    
    KeyValueStore* store = kv_store_create();
    int expected_size = 0;
    char keys[100][32];
    int key_count = 0;
    
    for (int i = 0; i < ops->count; i++) {
        KVOperation* op = &ops->operations[i];
        
        if (op->type == OP_PUT) {
            bool already_exists = false;
            for (int j = 0; j < key_count; j++) {
                if (strcmp(keys[j], op->key) == 0) {
                    already_exists = true;
                    break;
                }
            }
            
            kv_store_put(store, op->key, op->value);
            
            if (!already_exists) {
                if (key_count < 100) {
                    strncpy(keys[key_count++], op->key, sizeof(keys[0]));
                }
                expected_size++;
            }
        } else if (op->type == OP_DELETE) {
            bool existed = kv_store_delete(store, op->key);
            
            if (existed) {
                for (int j = 0; j < key_count; j++) {
                    if (strcmp(keys[j], op->key) == 0) {
                        for (int k = j; k < key_count - 1; k++) {
                            strncpy(keys[k], keys[k + 1], sizeof(keys[0]));
                        }
                        key_count--;
                        break;
                    }
                }
                expected_size--;
            }
        }
    }
    
    PROPERTY_ASSERT(store->size == expected_size);
    
    kv_store_free(store);
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
    printf("Property-Based Testing - Key-Value Store (Dependent Generation)\n");
    printf("===============================================================\n\n");
    
    Strategy* kv_strategy = kv_operation_strategy_create(20, 50);
    
    printf("Testing Key-Value Store Properties:\n");
    printf("-----------------------------------\n");
    
    run_property_test(
        "KV store: Put then Get retrieves correct value",
        test_kv_put_then_get,
        kv_strategy,
        100
    );
    
    run_property_test(
        "KV store: Shadow state matches actual state",
        test_kv_shadow_state,
        kv_strategy,
        100
    );
    
    run_property_test(
        "KV store: Size remains consistent",
        test_kv_size_consistency,
        kv_strategy,
        100
    );
    
    strategy_free(kv_strategy);
    
    printf("All tests completed.\n");
    printf("\nNote: This demonstrates dependent generation:\n");
    printf("  - Operations depend on previous state\n");
    printf("  - Get/Delete only target existing keys\n");
    printf("  - Shadow state validates correctness\n");
    printf("  - Size tracking ensures consistency\n");
    printf("\nThis parallels the 'Dependent Generation' section in the book.\n");
    
    return 0;
}
