// fib_sm.c – Fibonacci sequence generator driven purely by state machine
// compile:  gcc -std=c99 -O2 -Wall -Wextra -o fib_demo fib_sm.c
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <inttypes.h>

typedef enum {
    FIB_UNINIT = 0,    // Uninitialised state
    FIB_INIT,          // Ready to start, n=0 case
    FIB_FIRST,         // Computing F(1) = 1
    FIB_COMPUTING,     // Computing F(n) where n >= 2
    FIB_COMPLETE,      // Result ready
    FIB_OVERFLOW,      // Arithmetic overflow detected
    FIB_ERROR          // Invalid operation
} FibState;

typedef enum {
    FEV_INIT = 0,      // Init for F(n), param_in = target n
    FEV_STEP,          // Advance one step in computation
    FEV_GET_RESULT,    // Get current result, writes to *param_out
    FEV_GET_N,         // Get current n being computed, writes to *param_out
    FEV_RESET,         // Reset to uninit state
    FEV_GET_STATE      // Get current state code, writes to *param_out
} FibEvent;

typedef struct {
    uint64_t    current;     // Current Fibonacci number F(i)
    uint64_t    previous;    // Previous Fibonacci number F(i-1)
    int         target_n;    // Target index we're computing towards
    int         current_n;   // Current index i
    FibState    state;       // Current state
} FibSM;

static const char* fib_state_name(FibState s) {
    switch (s) {
        case FIB_UNINIT:    return "UNINIT";
        case FIB_INIT:      return "INIT";
        case FIB_FIRST:     return "FIRST";
        case FIB_COMPUTING: return "COMPUTING";
        case FIB_COMPLETE:  return "COMPLETE";
        case FIB_OVERFLOW:  return "OVERFLOW";
        case FIB_ERROR:     return "ERROR";
        default:            return "?";
    }
}

// check if adding a + b would overflow uint64_t
static bool would_overflow(uint64_t a, uint64_t b) {
    return a > UINT64_MAX - b;
}

// The ONLY API: drive the Fibonacci computation by sending events
bool fib_step(FibSM *sm, FibEvent ev, int param_in, uint64_t *param_out) {
    if (!sm) return false;

    // global rule: if in ERROR or OVERFLOW, only RESET is accepted
    if ((sm->state == FIB_ERROR || sm->state == FIB_OVERFLOW) && ev != FEV_RESET) {
        return false;
    }

    switch (ev) {
    case FEV_INIT: {
        if (param_in < 0) {
            sm->state = FIB_ERROR;
            return true;
        }
        
        sm->target_n = param_in;
        sm->current_n = 0;
        
        if (param_in == 0) {
            sm->current = 0;
            sm->previous = 0;
            sm->state = FIB_COMPLETE;
        } else if (param_in == 1) {
            sm->current = 0;  // step to F(1) = 1
            sm->previous = 0;
            sm->state = FIB_FIRST;
        } else {
            sm->current = 0;   // F(0)
            sm->previous = 0;
            sm->state = FIB_INIT;
        }
        return true;
    }

    case FEV_STEP: {
        switch (sm->state) {
        case FIB_INIT: {
            // transition: F(0)=0 -> F(1)=1
            sm->previous = sm->current;  // previous = F(0) = 0
            sm->current = 1;             // current = F(1) = 1
            sm->current_n = 1;
            sm->state = (sm->target_n == 1) ? FIB_COMPLETE : FIB_COMPUTING;
            return true;
        }
        case FIB_FIRST: {
            // special case: we initialized for F(1), now compute it
            sm->current = 1;
            sm->current_n = 1;
            sm->state = FIB_COMPLETE;
            return true;
        }
        case FIB_COMPUTING: {
            if (sm->current_n >= sm->target_n) {
                sm->state = FIB_COMPLETE;
                return true;
            }
            
            // check for overflow before computing next number
            if (would_overflow(sm->current, sm->previous)) {
                sm->state = FIB_OVERFLOW;
                return true;
            }
            
            // compute next Fibonacci number: F(n) = F(n-1) + F(n-2)
            uint64_t next = sm->current + sm->previous;
            sm->previous = sm->current;
            sm->current = next;
            sm->current_n++;
            
            if (sm->current_n >= sm->target_n) {
                sm->state = FIB_COMPLETE;
            }
            return true;
        }
        case FIB_COMPLETE:
        case FIB_OVERFLOW: {
            // no more steps needed
            return true;
        }
        default: {
            sm->state = FIB_ERROR;
            return true;
        }
        }
    }

    case FEV_GET_RESULT: {
        if (param_out) {
            *param_out = sm->current;
        }
        return true;
    }

    case FEV_GET_N: {
        if (param_out) {
            *param_out = sm->current_n;
        }
        return true;
    }

    case FEV_RESET: {
        sm->current = 0;
        sm->previous = 0;
        sm->target_n = 0;
        sm->current_n = 0;
        sm->state = FIB_UNINIT;
        return true;
    }

    case FEV_GET_STATE: {
        if (param_out) {
            *param_out = (uint64_t)sm->state;
        }
        return true;
    }

    default:
        return false;
    }
}

// Helper to compute F(n) completely using the state machine
bool compute_fibonacci(int n, uint64_t *result) {
    if (!result) return false;
    
    FibSM sm = {0};
    
    // Init for F(n)
    if (!fib_step(&sm, FEV_INIT, n, NULL)) return false;
    
    // Step until complete or error
    while (sm.state != FIB_COMPLETE && 
           sm.state != FIB_OVERFLOW && 
           sm.state != FIB_ERROR) {
        if (!fib_step(&sm, FEV_STEP, 0, NULL)) return false;
    }
    
    if (sm.state == FIB_COMPLETE) {
        fib_step(&sm, FEV_GET_RESULT, 0, result);
        return true;
    }
    
    return false;  // err or overflow
}

// --------- demo / self-test ----------
static void print_fib_state(const FibSM *sm) {
    printf("[state=%s n=%d/%d] F(%d) = %" PRIu64 " (prev=%" PRIu64 ")\n",
           fib_state_name(sm->state), sm->current_n, sm->target_n,
           sm->current_n, sm->current, sm->previous);
}

int main(void) {
    FibSM sm = {0};
    uint64_t result = 0;

    printf("-- Computing F(10) step by step --\n");
    fib_step(&sm, FEV_INIT, 10, NULL);
    print_fib_state(&sm);
    
    while (sm.state != FIB_COMPLETE && sm.state != FIB_OVERFLOW && sm.state != FIB_ERROR) {
        fib_step(&sm, FEV_STEP, 0, NULL);
        print_fib_state(&sm);
    }
    
    fib_step(&sm, FEV_GET_RESULT, 0, &result);
    printf("Final result: F(10) = %" PRIu64 "\n", result);

    printf("\n-- Quick computation of F(0) through F(20) --\n");
    for (int i = 0; i <= 20; i++) {
        if (compute_fibonacci(i, &result)) {
            printf("F(%2d) = %" PRIu64 "\n", i, result);
        } else {
            printf("F(%2d) = ERROR/OVERFLOW\n", i);
        }
    }

    printf("\n-- Testing overflow with F(100) --\n");
    fib_step(&sm, FEV_RESET, 0, NULL);
    fib_step(&sm, FEV_INIT, 100, NULL);
    
    int step_count = 0;
    while (sm.state == FIB_INIT || sm.state == FIB_FIRST || sm.state == FIB_COMPUTING) {
        fib_step(&sm, FEV_STEP, 0, NULL);
        step_count++;
        if (step_count % 10 == 0 || sm.state == FIB_OVERFLOW) {
            print_fib_state(&sm);
        }
        if (step_count > 100) break;  // safety break
    }

    printf("\n-- Edge cases --\n");
    printf("F(0): ");
    if (compute_fibonacci(0, &result)) printf("%" PRIu64 "\n", result);
    else printf("ERROR\n");
    
    printf("F(1): ");
    if (compute_fibonacci(1, &result)) printf("%" PRIu64 "\n", result);
    else printf("ERROR\n");
    
    printf("F(-1): ");
    if (compute_fibonacci(-1, &result)) printf("%" PRIu64 "\n", result);
    else printf("ERROR (as expected)\n");

    return 0;
}

