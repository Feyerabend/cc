// ssm.c – a fixed-capacity int stack driven purely by a state machine
// compile:  gcc -std=c99 -O2 -Wall -Wextra -o ssm_demo ssm.c
#include <stdio.h>
#include <stdbool.h>
#include <string.h>

#ifndef STACK_CAP
#define STACK_CAP 8
#endif

typedef enum {
    ST_UNINIT = 0,
    ST_EMPTY,
    ST_READY,      // has 1..(CAP-1) items
    ST_FULL,
    ST_ERROR
} StackState;

typedef enum {
    EV_INIT = 0,   // param_in ignored
    EV_PUSH,       // param_in used
    EV_POP,        // writes to *param_out
    EV_PEEK,       // writes to *param_out
    EV_RESET,      // param_in ignored
    EV_GET_STATE   // writes state code to *param_out (optional convenience)
} StackEvent;

typedef struct {
    int         data[STACK_CAP];
    int         top;    // index of top item; -1 when empty
    StackState  state;
} StackSM;

static const char* stack_state_name(StackState s) {
    switch (s) {
        case ST_UNINIT: return "UNINIT";
        case ST_EMPTY:  return "EMPTY";
        case ST_READY:  return "READY";
        case ST_FULL:   return "FULL";
        case ST_ERROR:  return "ERROR";
        default:        return "?";
    }
}

// compute state from top index
static StackState state_from_top(int top) {
    if (top < 0) return ST_EMPTY;
    if (top >= STACK_CAP - 1) return ST_FULL;
    return ST_READY;
}

// The ONLY API: drive the stack by sending events to this function.
// Returns true if the event was handled (even if it led to ST_ERROR).
// For EV_POP/EV_PEEK/EV_GET_STATE, provide param_out != NULL.
bool stack_step(StackSM *sm, StackEvent ev, int param_in, int *param_out) {
    if (!sm) return false;

    // global rule: if in ST_ERROR, only EV_RESET is accepted.
    if (sm->state == ST_ERROR && ev != EV_RESET) {
        return false;
    }

    switch (ev) {
    case EV_INIT: {
        sm->top   = -1;
        sm->state = ST_EMPTY;
        // zeroing memory isn't required but helps deterministic demos
        memset(sm->data, 0, sizeof sm->data);
        return true;
    }
    case EV_RESET: {
        sm->top   = -1;
        sm->state = ST_EMPTY;
        return true;
    }
    case EV_PUSH: {
        if (sm->state == ST_UNINIT) { sm->state = ST_ERROR; return true; }
        if (sm->top + 1 >= STACK_CAP) {
            // overflow attempt -> enter ERROR
            sm->state = ST_ERROR;
            return true;
        }
        sm->data[++sm->top] = param_in;
        sm->state = state_from_top(sm->top);
        return true;
    }
    case EV_POP: {
        if (sm->state == ST_UNINIT || sm->top < 0) {
            sm->state = ST_ERROR;      // underflow or uninitialised
            return true;
        }
        if (param_out) *param_out = sm->data[sm->top];
        sm->top--;
        sm->state = state_from_top(sm->top);
        return true;
    }
    case EV_PEEK: {
        if (sm->state == ST_UNINIT || sm->top < 0) {
            sm->state = ST_ERROR;      // peek on empty/uninit
            return true;
        }
        if (param_out) *param_out = sm->data[sm->top];
        // state unchanged
        return true;
    }
    case EV_GET_STATE: {
        if (param_out) *param_out = (int)sm->state;
        return true;
    }
    default:
        return false;
    }
}

// --------- demo / self-test ----------
static void print_stack(const StackSM *sm) {
    printf("[state=%s top=%d size=%d] ", stack_state_name(sm->state), sm->top, sm->top + 1);
    printf("stack = [");
    for (int i = 0; i <= sm->top; ++i) {
        printf("%s%d", (i? ", ":""), sm->data[i]);
    }
    printf("]\n");
}

int main(void) {
    StackSM s = { .top = -2, .state = ST_UNINIT };
    int out = 0;

    printf("== INIT ==\n");
    stack_step(&s, EV_INIT, 0, NULL);
    print_stack(&s);

    printf("\n== PUSH 1..8 ==\n");
    for (int i = 1; i <= 8; ++i) {
        stack_step(&s, EV_PUSH, i, NULL);
        print_stack(&s);
    }

    printf("\n== PUSH overflow (should go to ERROR) ==\n");
    stack_step(&s, EV_PUSH, 99, NULL);
    print_stack(&s);

    printf("\n== POP while in ERROR (ignored), then RESET ==\n");
    if (!stack_step(&s, EV_POP, 0, &out)) {
        printf("(event rejected)\n");
    }
    print_stack(&s);
    stack_step(&s, EV_RESET, 0, NULL);
    print_stack(&s);

    printf("\n== PUSH 10,20,30; PEEK; POP x2 ==\n");
    stack_step(&s, EV_PUSH, 10, NULL);
    stack_step(&s, EV_PUSH, 20, NULL);
    stack_step(&s, EV_PUSH, 30, NULL);
    print_stack(&s);
    stack_step(&s, EV_PEEK, 0, &out);
    printf("PEEK -> %d\n", out);
    stack_step(&s, EV_POP, 0, &out);
    printf("POP  -> %d\n", out);
    stack_step(&s, EV_POP, 0, &out);
    printf("POP  -> %d\n", out);
    print_stack(&s);

    printf("\n== POP underflow (ERROR), then RESET ==\n");
    stack_step(&s, EV_POP, 0, &out); // underflow -> ERROR
    print_stack(&s);
    stack_step(&s, EV_RESET, 0, NULL);
    print_stack(&s);

    return 0;
}

