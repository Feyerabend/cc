#include "property_test.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

jmp_buf property_test_jmp_buf;
bool property_test_active = false;

void property_assert(bool condition, const char* message) {
    if (!condition) {
        if (property_test_active) {
            longjmp(property_test_jmp_buf, 1);
        } else {
            fprintf(stderr, "Property assertion failed: %s\n", message);
            exit(1);
        }
    }
}

unsigned int rand_range(unsigned int* seed, int min, int max) {
    *seed = (*seed * 1103515245 + 12345) & 0x7fffffff;
    return min + (*seed % (max - min + 1));
}

void* shrink_failure(
    PropertyFn property_func,
    void* failing_input,
    Strategy* strategy,
    int* iterations_out,
    int max_iterations
) {
    void* current = failing_input;
    int iterations = 0;
    bool improved = true;
    
    while (iterations < max_iterations && improved) {
        improved = false;
        ShrinkIterator* iter = strategy->shrink(strategy, current);
        
        while (iter->has_next(iter) && iterations < max_iterations) {
            void* candidate = iter->next(iter);
            if (candidate == NULL) {
                break;
            }
            
            iterations++;
            
            property_test_active = true;
            int failed = setjmp(property_test_jmp_buf);
            
            if (failed) {
                if (current != failing_input) {
                    strategy->free_value(current);
                }
                current = candidate;
                improved = true;
                property_test_active = false;
                iter->free_iter(iter);
                break;
            }
            
            property_func(candidate);
            property_test_active = false;
            strategy->free_value(candidate);
        }
        
        if (!improved) {
            iter->free_iter(iter);
        }
    }
    
    if (iterations_out) {
        *iterations_out = iterations;
    }
    
    return current;
}

TestResult* test_property(
    PropertyFn property_func,
    Strategy* strategy,
    int max_examples,
    unsigned int random_seed
) {
    TestResult* result = (TestResult*)malloc(sizeof(TestResult));
    clock_t start_time = clock();
    unsigned int seed = random_seed;
    
    result->passed = true;
    result->examples_tried = 0;
    result->shrink_iterations = 0;
    result->minimal_failing_case = NULL;
    result->error_message = NULL;
    
    for (int i = 0; i < max_examples; i++) {
        int size = (i / 10) + 1;
        if (size < 1) {
            size = 1;
        }
        
        void* test_case = strategy->generate(strategy, &seed, size);
        result->examples_tried = i + 1;
        
        property_test_active = true;
        int failed = setjmp(property_test_jmp_buf);
        
        if (failed) {
            result->passed = false;
            property_test_active = false;
            
            int shrink_iters = 0;
            void* minimal = shrink_failure(
                property_func,
                test_case,
                strategy,
                &shrink_iters,
                1000
            );
            
            result->shrink_iterations = shrink_iters;
            result->minimal_failing_case = minimal;
            
            clock_t end_time = clock();
            result->execution_time = (double)(end_time - start_time) / CLOCKS_PER_SEC;
            return result;
        }
        
        property_func(test_case);
        property_test_active = false;
        
        strategy->free_value(test_case);
    }
    
    clock_t end_time = clock();
    result->execution_time = (double)(end_time - start_time) / CLOCKS_PER_SEC;
    return result;
}

void test_result_free(TestResult* result) {
    if (result->error_message) {
        free(result->error_message);
    }
    free(result);
}

void strategy_free(Strategy* strategy) {
    if (strategy->context) {
        free(strategy->context);
    }
    free(strategy);
}
