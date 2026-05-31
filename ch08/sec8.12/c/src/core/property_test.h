#ifndef PROPERTY_TEST_H
#define PROPERTY_TEST_H

#include <stddef.h>
#include <stdbool.h>
#include <time.h>
#include <setjmp.h>
#include "../types/types.h"

typedef struct Strategy Strategy;
typedef struct TestResult TestResult;
typedef struct ShrinkIterator ShrinkIterator;

typedef void* (*GenerateFn)(Strategy* strategy, unsigned int* seed, int size);
typedef ShrinkIterator* (*ShrinkFn)(Strategy* strategy, void* value);
typedef void (*FreeFn)(void* value);

struct Strategy {
    GenerateFn generate;
    ShrinkFn shrink;
    FreeFn free_value;
    void* context;
};

struct ShrinkIterator {
    void* current;
    void* state;
    bool (*has_next)(ShrinkIterator* iter);
    void* (*next)(ShrinkIterator* iter);
    void (*free_iter)(ShrinkIterator* iter);
};

struct TestResult {
    bool passed;
    int examples_tried;
    int shrink_iterations;
    void* minimal_failing_case;
    char* error_message;
    double execution_time;
};

typedef void (*PropertyFn)(void* input);

extern jmp_buf property_test_jmp_buf;
extern bool property_test_active;

TestResult* test_property(
    PropertyFn property_func,
    Strategy* strategy,
    int max_examples,
    unsigned int random_seed
);

void* shrink_failure(
    PropertyFn property_func,
    void* failing_input,
    Strategy* strategy,
    int* iterations_out,
    int max_iterations
);

void test_result_free(TestResult* result);
void strategy_free(Strategy* strategy);

unsigned int rand_range(unsigned int* seed, int min, int max);

void property_assert(bool condition, const char* message);

#define PROPERTY_ASSERT(cond) property_assert((cond), #cond)

#endif
