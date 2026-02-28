#include <stdio.h>
#include <stdlib.h>

// Coroutine states
#define CO_READY 0
#define CO_RUNNING 1
#define CO_SUSPENDED 2
#define CO_DEAD 3

// Coroutine structure with explicit State Machine
typedef struct {
    int state;          // Current state (CO_*)
    int pc;             // "Program counter" - where to resume
    void* data;         // Coroutine-specific data
    int yield_value;    // Value passed through yield
    int id;             // Coroutine identifier
} Coroutine;

// Create a new coroutine
Coroutine* coroutine_create(void* data, int id) {
    Coroutine* co = (Coroutine*)malloc(sizeof(Coroutine));
    if (!co) return NULL;
    
    co->state = CO_READY;
    co->pc = 0;
    co->data = data;
    co->yield_value = 0;
    co->id = id;
    
    return co;
}

// Yield a value from a coroutine
void coroutine_yield(Coroutine* co, int value, int next_pc) {
    co->yield_value = value;
    co->pc = next_pc;
    co->state = CO_SUSPENDED;
}

// Resume a coroutine - returns yield value or -1 if done
int coroutine_resume(Coroutine* co, void (*func)(Coroutine*)) {
    if (!co || co->state == CO_DEAD) {
        return -1;
    }
    
    co->state = CO_RUNNING;
    func(co);  // Run the coroutine function
    
    if (co->state == CO_DEAD) {
        return -1;
    }
    
    return co->yield_value;
}

// Check if coroutine is complete
int coroutine_is_dead(Coroutine* co) {
    return co == NULL || co->state == CO_DEAD;
}

// Free coroutine resources
void coroutine_destroy(Coroutine* co) {
    if (co) {
        // Free coroutine-specific data if needed
        if (co->data) {
            free(co->data);
        }
        free(co);
    }
}

// Sample data structure for counter coroutine
typedef struct {
    int current;
    int limit;
} CounterData;

// Example coroutine function using explicit state machine
void counter_function(Coroutine* co) {
    CounterData* data = (CounterData*)co->data;
    
    switch (co->pc) {
        case 0:  // Starting point
            data->current = 1;
            // fall through
            
        while_loop:
        case 1:  // Loop condition check
            if (data->current > data->limit) {
                printf("Coroutine %d: Finished counting to %d\n", co->id, data->limit);
                co->state = CO_DEAD;
                return;
            }
            
            // Print and increment
            printf("Coroutine %d: count = %d\n", co->id, data->current);
            coroutine_yield(co, data->current, 2);
            return;
            
        case 2:  // After yield
            data->current++;
            goto while_loop;
    }
}

int main() {
    // Create data for coroutines
    CounterData* data1 = (CounterData*)malloc(sizeof(CounterData));
    data1->limit = 5;
    
    CounterData* data2 = (CounterData*)malloc(sizeof(CounterData));
    data2->limit = 3;
    
    // Create coroutines
    Coroutine* co1 = coroutine_create(data1, 1);
    Coroutine* co2 = coroutine_create(data2, 2);
    
    // Run until both are done
    while (!coroutine_is_dead(co1) || !coroutine_is_dead(co2)) {
        if (!coroutine_is_dead(co1)) {
            int val = coroutine_resume(co1, counter_function);
            if (val >= 0) {
                printf("Main: Coroutine 1 yielded %d\n", val);
            }
        }
        
        if (!coroutine_is_dead(co2)) {
            int val = coroutine_resume(co2, counter_function);
            if (val >= 0) {
                printf("Main: Coroutine 2 yielded %d\n", val);
            }
        }
    }
    
    // Clean up
    coroutine_destroy(co1);
    coroutine_destroy(co2);
    
    printf("Main: All coroutines have completed\n");
    return 0;
}