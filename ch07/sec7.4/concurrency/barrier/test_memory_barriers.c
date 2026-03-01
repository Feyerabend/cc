#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>
#include <assert.h>

#include "atomic.h"
#include "arena_threadsafe.h"

/* Test configuration */
#define NUM_THREADS 8
#define ALLOCATIONS_PER_THREAD 10000
#define SMALL_ALLOC_SIZE 32
#define MEDIUM_ALLOC_SIZE 256
#define LARGE_ALLOC_SIZE 4096

/* Color output */
#define COLOR_GREEN "\033[0;32m"
#define COLOR_RED "\033[0;31m"
#define COLOR_YELLOW "\033[0;33m"
#define COLOR_BLUE "\033[0;34m"
#define COLOR_RESET "\033[0m"

#define PASS(msg) printf(COLOR_GREEN "✓ PASS: %s" COLOR_RESET "\n", msg)
#define FAIL(msg) printf(COLOR_RED "✗ FAIL: %s" COLOR_RESET "\n", msg)
#define INFO(msg) printf(COLOR_BLUE "ℹ INFO: %s" COLOR_RESET "\n", msg)

/* Test utilities */
static int total_tests = 0;
static int passed_tests = 0;

#define TEST_START(name) \
    do { \
        printf("\n" COLOR_YELLOW "Test: %s" COLOR_RESET "\n", name); \
        total_tests++; \
    } while(0)

#define TEST_PASS() \
    do { \
        passed_tests++; \
        PASS("Test passed"); \
    } while(0)

#define ASSERT_TRUE(cond, msg) \
    do { \
        if (!(cond)) { \
            FAIL(msg); \
            return; \
        } \
    } while(0)

#define ASSERT_TRUE_PTR(cond, msg) \
    do { \
        if (!(cond)) { \
            FAIL(msg); \
            return NULL; \
        } \
    } while(0)

/* Thread data for tests */
typedef struct {
    int thread_id;
    ThreadSafeArena *arena;
    atomic_size_t *counter;
    void **allocations;
    int num_allocations;
} ThreadData;

/* =============================================================================
 * TEST 1: Basic Memory Barriers
 * =============================================================================
 */

static atomic_int shared_value;
static atomic_bool ready_flag;

void* barrier_test_writer(void *arg) {
    (void)arg;
    
    // Write to shared value
    atomic_store_explicit(&shared_value, 42, memory_order_relaxed);
    
    // Release barrier ensures the write is visible
    memory_barrier_release();
    
    // Signal ready
    atomic_store_explicit(&ready_flag, true, memory_order_release);
    
    return NULL;
}

void* barrier_test_reader(void *arg) {
    (void)arg;
    
    // Wait for ready flag (with acquire)
    while (!atomic_load_explicit(&ready_flag, memory_order_acquire)) {
        // Busy wait
    }
    
    // Acquire barrier ensures we see the write
    memory_barrier_acquire();
    
    // Read shared value
    int value = atomic_load_explicit(&shared_value, memory_order_relaxed);
    
    // Value should be 42
    return (void*)(intptr_t)value;
}

void test_memory_barriers(void) {
    TEST_START("Memory Barriers - Store/Load Ordering");
    
    atomic_store_explicit(&shared_value, 0, memory_order_relaxed);
    atomic_store_explicit(&ready_flag, false, memory_order_relaxed);
    
    pthread_t writer, reader;
    
    pthread_create(&writer, NULL, barrier_test_writer, NULL);
    pthread_create(&reader, NULL, barrier_test_reader, NULL);
    
    void *result;
    pthread_join(writer, NULL);
    pthread_join(reader, &result);
    
    int value = (int)(intptr_t)result;
    ASSERT_TRUE(value == 42, "Reader should see value written by writer");
    
    TEST_PASS();
}

/* =============================================================================
 * TEST 2: Atomic Operations
 * =============================================================================
 */

void* atomic_increment_worker(void *arg) {
    atomic_size_t *counter = (atomic_size_t*)arg;
    
    for (int i = 0; i < 10000; i++) {
        atomic_increment_size(counter);
    }
    
    return NULL;
}

void test_atomic_operations(void) {
    TEST_START("Atomic Operations - Concurrent Increments");
    
    atomic_size_t counter;
    atomic_store_explicit(&counter, 0, memory_order_relaxed);
    
    pthread_t threads[NUM_THREADS];
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_create(&threads[i], NULL, atomic_increment_worker, &counter);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    size_t final_value = atomic_load_explicit(&counter, memory_order_seq_cst);
    size_t expected = NUM_THREADS * 10000;
    
    ASSERT_TRUE(final_value == expected, "Final counter value should match expected");
    
    printf("  Final value: %zu (expected: %zu)\n", final_value, expected);
    TEST_PASS();
}

/* =============================================================================
 * TEST 3: Compare-and-Swap
 * =============================================================================
 */

void* cas_test_worker(void *arg) {
    atomic_size_t *value = (atomic_size_t*)arg;
    
    for (int i = 0; i < 1000; i++) {
        size_t old_val = atomic_load_explicit(value, memory_order_relaxed);
        size_t new_val;
        
        do {
            new_val = old_val + 1;
        } while (!atomic_cas_size(value, &old_val, new_val,
                                  MEMORY_ORDER_RELEASE,
                                  MEMORY_ORDER_RELAXED));
    }
    
    return NULL;
}

void test_compare_and_swap(void) {
    TEST_START("Compare-and-Swap - Lock-Free Counter");
    
    atomic_size_t value;
    atomic_store_explicit(&value, 0, memory_order_relaxed);
    
    pthread_t threads[NUM_THREADS];
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_create(&threads[i], NULL, cas_test_worker, &value);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    size_t final_value = atomic_load_explicit(&value, memory_order_seq_cst);
    size_t expected = NUM_THREADS * 1000;
    
    ASSERT_TRUE(final_value == expected, "CAS-based counter should be accurate");
    
    printf("  Final value: %zu (expected: %zu)\n", final_value, expected);
    TEST_PASS();
}

/* =============================================================================
 * TEST 4: Spinlock
 * =============================================================================
 */

static Spinlock test_lock;
static size_t protected_counter = 0;

void* spinlock_test_worker(void *arg) {
    (void)arg;
    
    for (int i = 0; i < 10000; i++) {
        spinlock_lock(&test_lock);
        protected_counter++;
        spinlock_unlock(&test_lock);
    }
    
    return NULL;
}

void test_spinlock(void) {
    TEST_START("Spinlock - Mutual Exclusion");
    
    spinlock_init(&test_lock);
    protected_counter = 0;
    
    pthread_t threads[NUM_THREADS];
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_create(&threads[i], NULL, spinlock_test_worker, NULL);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    size_t expected = NUM_THREADS * 10000;
    ASSERT_TRUE(protected_counter == expected, "Spinlock should protect counter");
    
    printf("  Final value: %zu (expected: %zu)\n", protected_counter, expected);
    TEST_PASS();
}

/* =============================================================================
 * TEST 5: Lock-Free Stack
 * =============================================================================
 */

void* lfstack_test_worker(void *arg) {
    LockFreeStack *stack = (LockFreeStack*)arg;
    
    // Push 100 nodes
    for (int i = 0; i < 100; i++) {
        LockFreeNode *node = malloc(sizeof(LockFreeNode));
        node->data = (void*)(intptr_t)(i + 1);
        lfstack_push(stack, node);
    }
    
    // Pop 50 nodes
    for (int i = 0; i < 50; i++) {
        LockFreeNode *node = lfstack_pop(stack);
        if (node) {
            free(node);
        }
    }
    
    return NULL;
}

void test_lock_free_stack(void) {
    TEST_START("Lock-Free Stack - Concurrent Push/Pop");
    
    LockFreeStack stack;
    lfstack_init(&stack);
    
    pthread_t threads[NUM_THREADS];
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_create(&threads[i], NULL, lfstack_test_worker, &stack);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    size_t final_size = lfstack_size(&stack);
    size_t expected = NUM_THREADS * 50; // 100 pushed - 50 popped per thread
    
    printf("  Final size: %zu (expected: %zu)\n", final_size, expected);
    ASSERT_TRUE(final_size == expected, "Stack size should match expected");
    
    // Cleanup
    LockFreeNode *node;
    while ((node = lfstack_pop(&stack)) != NULL) {
        free(node);
    }
    
    TEST_PASS();
}

/* =============================================================================
 * TEST 6: Thread-Safe Arena - Concurrent Small Allocations
 * =============================================================================
 */

void* arena_small_alloc_worker(void *arg) {
    ThreadData *data = (ThreadData*)arg;
    
    for (int i = 0; i < data->num_allocations; i++) {
        void *ptr = ts_arena_alloc(data->arena, SMALL_ALLOC_SIZE);
        ASSERT_TRUE_PTR(ptr != NULL, "Allocation should succeed");
        
        // Write pattern to verify no corruption
        memset(ptr, (unsigned char)(data->thread_id + i), SMALL_ALLOC_SIZE);
        data->allocations[i] = ptr;
    }
    
    return NULL;
}

void test_threadsafe_arena_small(void) {
    TEST_START("Thread-Safe Arena - Concurrent Small Allocations");
    
    ThreadSafeArena *arena = ts_arena_create(8192);
    ASSERT_TRUE(arena != NULL, "Arena creation should succeed");
    
    pthread_t threads[NUM_THREADS];
    ThreadData thread_data[NUM_THREADS];
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].arena = arena;
        thread_data[i].num_allocations = ALLOCATIONS_PER_THREAD;
        thread_data[i].allocations = calloc(ALLOCATIONS_PER_THREAD, sizeof(void*));
        
        pthread_create(&threads[i], NULL, arena_small_alloc_worker, &thread_data[i]);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Verify allocations
    for (int t = 0; t < NUM_THREADS; t++) {
        for (int i = 0; i < ALLOCATIONS_PER_THREAD; i++) {
            unsigned char *ptr = (unsigned char*)thread_data[t].allocations[i];
            unsigned char expected = (unsigned char)(thread_data[t].thread_id + i);
            
            for (size_t j = 0; j < SMALL_ALLOC_SIZE; j++) {
                if (ptr[j] != expected) {
                    FAIL("Memory corruption detected");
                    goto cleanup;
                }
            }
        }
    }
    
    size_t total_allocated = ts_arena_total_allocated(arena);
    size_t total_blocks = ts_arena_total_blocks(arena);
    
    printf("  Total allocated: %zu bytes in %zu blocks\n", total_allocated, total_blocks);
    printf("  Allocations: %d threads × %d = %d\n", 
           NUM_THREADS, ALLOCATIONS_PER_THREAD, NUM_THREADS * ALLOCATIONS_PER_THREAD);
    
    TEST_PASS();
    
cleanup:
    for (int i = 0; i < NUM_THREADS; i++) {
        free(thread_data[i].allocations);
    }
    ts_arena_destroy(arena);
}

/* =============================================================================
 * TEST 7: Thread-Safe Arena - Mixed Size Allocations
 * =============================================================================
 */

void* arena_mixed_alloc_worker(void *arg) {
    ThreadData *data = (ThreadData*)arg;
    
    for (int i = 0; i < data->num_allocations; i++) {
        size_t size;
        
        // Vary allocation size
        if (i % 3 == 0) {
            size = SMALL_ALLOC_SIZE;
        } else if (i % 3 == 1) {
            size = MEDIUM_ALLOC_SIZE;
        } else {
            size = LARGE_ALLOC_SIZE;
        }
        
        void *ptr = ts_arena_alloc(data->arena, size);
        ASSERT_TRUE_PTR(ptr != NULL, "Allocation should succeed");
        
        // Write to verify
        memset(ptr, (unsigned char)data->thread_id, size);
        
        // Update counter atomically
        atomic_fetch_add_size(data->counter, 1, MEMORY_ORDER_RELAXED);
    }
    
    return NULL;
}

void test_threadsafe_arena_mixed(void) {
    TEST_START("Thread-Safe Arena - Mixed Size Allocations");
    
    ThreadSafeArena *arena = ts_arena_create(16384);
    ASSERT_TRUE(arena != NULL, "Arena creation should succeed");
    
    atomic_size_t counter;
    atomic_store_explicit(&counter, 0, memory_order_relaxed);
    
    pthread_t threads[NUM_THREADS];
    ThreadData thread_data[NUM_THREADS];
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].arena = arena;
        thread_data[i].counter = &counter;
        thread_data[i].num_allocations = ALLOCATIONS_PER_THREAD / 10;
        
        pthread_create(&threads[i], NULL, arena_mixed_alloc_worker, &thread_data[i]);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    size_t total_allocs = atomic_load_explicit(&counter, memory_order_seq_cst);
    size_t expected = NUM_THREADS * (ALLOCATIONS_PER_THREAD / 10);
    
    ASSERT_TRUE(total_allocs == expected, "All allocations should be counted");
    
    printf("  Total allocations: %zu (expected: %zu)\n", total_allocs, expected);
    printf("  Arena stats: %zu bytes in %zu blocks\n",
           ts_arena_total_allocated(arena), ts_arena_total_blocks(arena));
    
    ts_arena_destroy(arena);
    TEST_PASS();
}

/* =============================================================================
 * TEST 8: Thread-Safe Arena - String Duplication
 * =============================================================================
 */

void* arena_strdup_worker(void *arg) {
    ThreadData *data = (ThreadData*)arg;
    char buffer[256];
    
    for (int i = 0; i < 1000; i++) {
        snprintf(buffer, sizeof(buffer), "Thread_%d_String_%d", data->thread_id, i);
        char *str = ts_arena_strdup(data->arena, buffer);
        
        ASSERT_TRUE_PTR(str != NULL, "String duplication should succeed");
        ASSERT_TRUE_PTR(strcmp(str, buffer) == 0, "Duplicated string should match original");
        
        atomic_fetch_add_size(data->counter, 1, MEMORY_ORDER_RELAXED);
    }
    
    return NULL;
}

void test_threadsafe_arena_strdup(void) {
    TEST_START("Thread-Safe Arena - Concurrent String Duplication");
    
    ThreadSafeArena *arena = ts_arena_create(8192);
    ASSERT_TRUE(arena != NULL, "Arena creation should succeed");
    
    atomic_size_t counter;
    atomic_store_explicit(&counter, 0, memory_order_relaxed);
    
    pthread_t threads[NUM_THREADS];
    ThreadData thread_data[NUM_THREADS];
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].arena = arena;
        thread_data[i].counter = &counter;
        
        pthread_create(&threads[i], NULL, arena_strdup_worker, &thread_data[i]);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    size_t total = atomic_load_explicit(&counter, memory_order_seq_cst);
    size_t expected = NUM_THREADS * 1000;
    
    ASSERT_TRUE(total == expected, "All string duplications should succeed");
    
    printf("  Total string duplications: %zu (expected: %zu)\n", total, expected);
    
    ts_arena_destroy(arena);
    TEST_PASS();
}

/* =============================================================================
 * TEST 9: Memory Ordering - Sequential Consistency
 * =============================================================================
 */

static atomic_int x, y;
static int r1, r2;

void* seq_cst_thread1(void *arg) {
    (void)arg;
    atomic_store_explicit(&x, 1, memory_order_seq_cst);
    r1 = atomic_load_explicit(&y, memory_order_seq_cst);
    return NULL;
}

void* seq_cst_thread2(void *arg) {
    (void)arg;
    atomic_store_explicit(&y, 1, memory_order_seq_cst);
    r2 = atomic_load_explicit(&x, memory_order_seq_cst);
    return NULL;
}

void test_sequential_consistency(void) {
    TEST_START("Memory Ordering - Sequential Consistency");
    
    int violations = 0;
    int iterations = 10000;
    
    for (int i = 0; i < iterations; i++) {
        atomic_store_explicit(&x, 0, memory_order_relaxed);
        atomic_store_explicit(&y, 0, memory_order_relaxed);
        r1 = 0;
        r2 = 0;
        
        pthread_t t1, t2;
        pthread_create(&t1, NULL, seq_cst_thread1, NULL);
        pthread_create(&t2, NULL, seq_cst_thread2, NULL);
        
        pthread_join(t1, NULL);
        pthread_join(t2, NULL);
        
        // With seq_cst, we should never see both r1 == 0 and r2 == 0
        if (r1 == 0 && r2 == 0) {
            violations++;
        }
    }
    
    printf("  Iterations: %d, Violations: %d\n", iterations, violations);
    ASSERT_TRUE(violations == 0, "Sequential consistency should prevent violations");
    
    TEST_PASS();
}

/* =============================================================================
 * TEST 10: Stress Test - High Contention
 * =============================================================================
 */

void* stress_test_worker(void *arg) {
    ThreadData *data = (ThreadData*)arg;
    
    for (int i = 0; i < 5000; i++) {
        // Mix of operations
        void *ptr1 = ts_arena_alloc(data->arena, 64);
        atomic_increment_size(data->counter);
        
        void *ptr2 = ts_arena_alloc(data->arena, 128);
        atomic_increment_size(data->counter);
        
        char *str = ts_arena_strdup(data->arena, "stress test string");
        
        if (ptr1 && ptr2 && str) {
            memset(ptr1, 0xFF, 64);
            memset(ptr2, 0xAA, 128);
        }
    }
    
    return NULL;
}

void test_stress_high_contention(void) {
    TEST_START("Stress Test - High Contention");
    
    ThreadSafeArena *arena = ts_arena_create(4096);
    ASSERT_TRUE(arena != NULL, "Arena creation should succeed");
    
    atomic_size_t counter;
    atomic_store_explicit(&counter, 0, memory_order_relaxed);
    
    pthread_t threads[NUM_THREADS];
    ThreadData thread_data[NUM_THREADS];
    
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].arena = arena;
        thread_data[i].counter = &counter;
        
        pthread_create(&threads[i], NULL, stress_test_worker, &thread_data[i]);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    double elapsed = (end.tv_sec - start.tv_sec) + 
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    
    size_t total = atomic_load_explicit(&counter, memory_order_seq_cst);
    size_t expected = NUM_THREADS * 5000 * 2;
    
    ASSERT_TRUE(total == expected, "Counter should match expected value");
    
    printf("  Time elapsed: %.3f seconds\n", elapsed);
    printf("  Operations: %zu (%.0f ops/sec)\n", total, total / elapsed);
    printf("  Arena: %zu bytes in %zu blocks\n",
           ts_arena_total_allocated(arena), ts_arena_total_blocks(arena));
    
    ts_arena_destroy(arena);
    TEST_PASS();
}

/* =============================================================================
 * Main Test Runner
 * =============================================================================
 */

int main(void) {
    printf("\n");
    printf("==================================================\n");
    printf("  Memory Barrier & Thread-Safety Test Suite\n");
    printf("==================================================\n");
    
    // Run all tests
    test_memory_barriers();
    test_atomic_operations();
    test_compare_and_swap();
    test_spinlock();
    test_lock_free_stack();
    test_threadsafe_arena_small();
    test_threadsafe_arena_mixed();
    test_threadsafe_arena_strdup();
    test_sequential_consistency();
    test_stress_high_contention();
    
    // Summary
    printf("\n");
    printf("==================================================\n");
    printf("  Test Summary\n");
    printf("==================================================\n");
    printf("  Total:  %d\n", total_tests);
    printf("  Passed: " COLOR_GREEN "%d" COLOR_RESET "\n", passed_tests);
    printf("  Failed: " COLOR_RED "%d" COLOR_RESET "\n", total_tests - passed_tests);
    printf("==================================================\n");
    
    return (passed_tests == total_tests) ? EXIT_SUCCESS : EXIT_FAILURE;
}
