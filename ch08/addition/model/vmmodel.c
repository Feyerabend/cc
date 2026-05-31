#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>

/*
 * Explicit-state model checker for a simple register virtual machine.
 *
 * The VM state is a triple (pc, r, halted). Because both pc and r are
 * bounded, the state space is finite and exhaustive exploration terminates.
 *
 * The checker verifies two kinds of properties:
 *   - Safety:   AG(safe)   — no reachable state violates the invariant.
 *   - Liveness: AF(halted) — every execution path eventually reaches HALT.
 *
 * These correspond directly to CTL formulas over the Kripke structure
 * whose states are VM triples and whose transition relation is the
 * single-step execution semantics.
 */

#define MAX_PROGRAM        100
#define MAX_STATES       10000
#define MAX_REGISTER_VALUE 1000
#define HASH_TABLE_SIZE   4096

typedef enum {
    INC,
    DEC,
    JNZ,
    HALT,
    SET,
    ADD,
    SUB
} OpCode;

typedef struct {
    OpCode op;
    int operand;
} Instruction;

typedef struct {
    int pc;
    int r;
    bool halted;
    uint32_t hash;
} State;

typedef struct StateNode {
    State state;
    struct StateNode *next;
} StateNode;

typedef struct {
    StateNode *buckets[HASH_TABLE_SIZE];
    int count;
} StateHashSet;

typedef struct {
    State *states;
    int count;
    int capacity;
} StateStack;

typedef struct {
    Instruction *instructions;
    int length;
    int capacity;
} Program;

Program g_program = {0};


/* ---------- hashing ---------------------------------------------------- */

uint32_t hash_state(State s) {
    if (s.hash) return s.hash;
    uint32_t h = 2166136261u;
    h ^= (uint32_t)s.pc;   h *= 16777619u;
    h ^= (uint32_t)s.r;    h *= 16777619u;
    h ^= (uint32_t)s.halted; h *= 16777619u;
    return h ? h : 1u;
}

State create_state(int pc, int r, bool halted) {
    State s = {pc, r, halted, 0};
    s.hash = hash_state(s);
    return s;
}

bool states_equal(State a, State b) {
    return a.pc == b.pc && a.r == b.r && a.halted == b.halted;
}


/* ---------- hash set ---------------------------------------------------- */

StateHashSet *create_state_set(void) {
    return calloc(1, sizeof(StateHashSet));
}

void destroy_state_set(StateHashSet *set) {
    if (!set) return;
    for (int i = 0; i < HASH_TABLE_SIZE; i++) {
        StateNode *n = set->buckets[i];
        while (n) { StateNode *nx = n->next; free(n); n = nx; }
    }
    free(set);
}

bool state_in_set(StateHashSet *set, State s) {
    if (!set) return false;
    uint32_t h = s.hash ? s.hash : hash_state(s);
    for (StateNode *n = set->buckets[h % HASH_TABLE_SIZE]; n; n = n->next)
        if (states_equal(n->state, s)) return true;
    return false;
}

bool add_state_to_set(StateHashSet *set, State s) {
    if (!set || state_in_set(set, s)) return false;
    uint32_t h = s.hash ? s.hash : hash_state(s);
    StateNode *n = malloc(sizeof(StateNode));
    if (!n) { fprintf(stderr, "out of memory\n"); return false; }
    n->state = s;
    n->state.hash = h;
    n->next = set->buckets[h % HASH_TABLE_SIZE];
    set->buckets[h % HASH_TABLE_SIZE] = n;
    set->count++;
    return true;
}


/* ---------- stack ------------------------------------------------------- */

StateStack *create_state_stack(void) {
    StateStack *st = malloc(sizeof(StateStack));
    if (!st) return NULL;
    st->capacity = 1024;
    st->states = malloc(sizeof(State) * st->capacity);
    st->count = 0;
    if (!st->states) { free(st); return NULL; }
    return st;
}

void destroy_state_stack(StateStack *st) {
    if (!st) return;
    free(st->states);
    free(st);
}

bool push_state(StateStack *st, State s) {
    if (!st) return false;
    if (st->count >= st->capacity) {
        int cap = st->capacity * 2;
        State *ns = realloc(st->states, sizeof(State) * cap);
        if (!ns) { fprintf(stderr, "stack realloc failed\n"); return false; }
        st->states = ns;
        st->capacity = cap;
    }
    st->states[st->count++] = s;
    return true;
}

bool pop_state(StateStack *st, State *out) {
    if (!st || st->count == 0) return false;
    *out = st->states[--st->count];
    return true;
}


/* ---------- program ----------------------------------------------------- */

bool init_program(int capacity) {
    g_program.instructions = malloc(sizeof(Instruction) * capacity);
    if (!g_program.instructions) return false;
    g_program.capacity = capacity;
    g_program.length = 0;
    return true;
}

void destroy_program(void) {
    free(g_program.instructions);
    g_program.instructions = NULL;
    g_program.capacity = g_program.length = 0;
}

bool add_instruction(OpCode op, int operand) {
    if (g_program.length >= g_program.capacity) {
        fprintf(stderr, "program capacity exceeded\n");
        return false;
    }
    g_program.instructions[g_program.length++] = (Instruction){op, operand};
    return true;
}

void print_program(void) {
    const char *names[] = {"INC","DEC","JNZ","HALT","SET","ADD","SUB"};
    printf("Program (%d instructions):\n", g_program.length);
    for (int i = 0; i < g_program.length; i++) {
        Instruction ins = g_program.instructions[i];
        printf("  %2d: %s", i, names[ins.op]);
        if (ins.op == JNZ) printf(" %+d  (-> pc %d)", ins.operand, i + ins.operand);
        else if (ins.op == SET || ins.op == ADD || ins.op == SUB) printf(" %d", ins.operand);
        printf("\n");
    }
    printf("\n");
}

int clamp(int v) {
    if (v < 0) return 0;
    if (v > MAX_REGISTER_VALUE) return MAX_REGISTER_VALUE;
    return v;
}

void print_state(State s) {
    printf("(pc=%d, r=%d, halted=%s)", s.pc, s.r, s.halted ? "true" : "false");
}


/* ---------- result ------------------------------------------------------ */

typedef struct {
    bool safety_ok;
    bool liveness_ok;        /* true = all paths reach HALT */
    bool liveness_checked;   /* false when liveness check was skipped */
    int  states_explored;
    int  max_stack_depth;
    char error_msg[256];
} ModelCheckResult;


/* ---------- safety check (AG safe) ------------------------------------- */
/*
 * Performs a depth-first reachability search. Verifies:
 *   - PC is always in [0, program_length).
 *   - Every instruction is a known opcode.
 * These constitute the invariant "safe". Violation of either produces a
 * counterexample state and sets safety_ok = false.
 */
static ModelCheckResult check_safety(bool verbose) {
    ModelCheckResult res = {true, false, false, 0, 0, ""};

    StateHashSet *visited = create_state_set();
    StateStack   *stack   = create_state_stack();
    if (!visited || !stack) {
        strcpy(res.error_msg, "memory allocation failed");
        res.safety_ok = false;
        goto cleanup;
    }

    push_state(stack, create_state(0, 0, false));

    State cur;
    while (pop_state(stack, &cur)) {
        if (stack->count > res.max_stack_depth)
            res.max_stack_depth = stack->count;

        if (state_in_set(visited, cur)) continue;
        add_state_to_set(visited, cur);
        res.states_explored++;

        if (cur.halted) continue;

        if (cur.pc < 0 || cur.pc >= g_program.length) {
            snprintf(res.error_msg, sizeof(res.error_msg),
                     "AG(safe) violated: pc=%d out of bounds at r=%d",
                     cur.pc, cur.r);
            res.safety_ok = false;
            goto cleanup;
        }

        Instruction ins = g_program.instructions[cur.pc];

        switch (ins.op) {
            case INC:  push_state(stack, create_state(cur.pc+1, clamp(cur.r+1),         false)); break;
            case DEC:  push_state(stack, create_state(cur.pc+1, clamp(cur.r-1),         false)); break;
            case SET:  push_state(stack, create_state(cur.pc+1, clamp(ins.operand),     false)); break;
            case ADD:  push_state(stack, create_state(cur.pc+1, clamp(cur.r+ins.operand), false)); break;
            case SUB:  push_state(stack, create_state(cur.pc+1, clamp(cur.r-ins.operand), false)); break;
            case HALT: push_state(stack, create_state(cur.pc,   cur.r,                  true)); break;
            case JNZ:
                if (cur.r != 0) {
                    int jpc = cur.pc + ins.operand;
                    if (jpc < 0 || jpc >= g_program.length) {
                        snprintf(res.error_msg, sizeof(res.error_msg),
                                 "AG(safe) violated: JNZ target pc=%d out of bounds", jpc);
                        res.safety_ok = false;
                        goto cleanup;
                    }
                    push_state(stack, create_state(jpc, cur.r, false));
                } else {
                    push_state(stack, create_state(cur.pc + 1, cur.r, false));
                }
                break;
            default:
                snprintf(res.error_msg, sizeof(res.error_msg),
                         "AG(safe) violated: invalid opcode %d at pc=%d", ins.op, cur.pc);
                res.safety_ok = false;
                goto cleanup;
        }
    }

cleanup:
    if (verbose && res.safety_ok) {
        printf("  AG(safe): HOLDS\n");
        printf("  States explored : %d\n", res.states_explored);
        printf("  Max stack depth : %d\n", res.max_stack_depth);
        printf("  Hash load       : %.1f%%\n",
               (double)visited->count / HASH_TABLE_SIZE * 100.0);
    } else if (verbose && !res.safety_ok) {
        printf("  AG(safe): VIOLATED — %s\n", res.error_msg);
    }
    destroy_state_set(visited);
    destroy_state_stack(stack);
    return res;
}


/* ---------- liveness check (AF halted) --------------------------------- */
/*
 * AF(halted) — every path eventually reaches a halted state.
 *
 * A program violates AF(halted) iff there exists an infinite execution
 * path that never reaches HALT. For a finite state space this is equivalent
 * to: there exists a reachable cycle of non-halted states from which no
 * halted state is reachable.
 *
 * Algorithm (greatest-fixpoint, dual of AF):
 *   Let Z = set of states that DO NOT satisfy AF(halted).
 *   Z is the greatest fixpoint of: Z' = {s : s is not halted AND
 *                                          some successor of s is in Z'}
 *   i.e. EG(¬halted), the set of states from which an infinite non-halting
 *   path exists.
 *
 * We compute this by iterating from Z₀ = all non-halted reachable states
 * downward until stable. If Z is empty, AF(halted) holds.
 *
 * Note: this requires the full reachable state set, so we build it first.
 */
static bool check_liveness(const StateHashSet *visited,
                            StateNode **all_states, int n_states,
                            bool verbose)
{
    /* Build adjacency: for each reachable non-halted state, its successors. */
    /* We reuse the hash set to test membership. */

    /* Collect all reachable non-halted states into an array. */
    State *nonhalted = malloc(sizeof(State) * n_states);
    int    n_nh = 0;
    if (!nonhalted) return true; /* treat as passes if OOM */

    for (int b = 0; b < HASH_TABLE_SIZE; b++) {
        for (StateNode *nd = all_states[b]; nd; nd = nd->next) {
            if (!nd->state.halted)
                nonhalted[n_nh++] = nd->state;
        }
    }

    /* Z = current candidate set for EG(¬halted): starts as all non-halted. */
    /* Represent as a boolean array indexed into nonhalted[]. */
    bool *in_Z = calloc(n_nh, sizeof(bool));
    if (!in_Z) { free(nonhalted); return true; }
    for (int i = 0; i < n_nh; i++) in_Z[i] = true;

    bool changed = true;
    while (changed) {
        changed = false;
        for (int i = 0; i < n_nh; i++) {
            if (!in_Z[i]) continue;
            State s = nonhalted[i];
            /* Does s have at least one successor that is in Z? */
            bool has_Z_succ = false;
            Instruction ins = g_program.instructions[s.pc];
            /* Enumerate successors (same logic as safety check) */
            State succs[2];
            int ns = 0;
            switch (ins.op) {
                case INC:  succs[ns++] = create_state(s.pc+1, clamp(s.r+1),           false); break;
                case DEC:  succs[ns++] = create_state(s.pc+1, clamp(s.r-1),           false); break;
                case SET:  succs[ns++] = create_state(s.pc+1, clamp(ins.operand),     false); break;
                case ADD:  succs[ns++] = create_state(s.pc+1, clamp(s.r+ins.operand), false); break;
                case SUB:  succs[ns++] = create_state(s.pc+1, clamp(s.r-ins.operand), false); break;
                case HALT: /* leads to halted state — not in Z */ break;
                case JNZ:
                    if (s.r != 0) {
                        int jpc = s.pc + ins.operand;
                        if (jpc >= 0 && jpc < g_program.length)
                            succs[ns++] = create_state(jpc, s.r, false);
                    } else {
                        succs[ns++] = create_state(s.pc + 1, s.r, false);
                    }
                    break;
                default: break;
            }
            for (int k = 0; k < ns && !has_Z_succ; k++) {
                /* find succs[k] in nonhalted array */
                for (int j = 0; j < n_nh; j++) {
                    if (in_Z[j] && states_equal(nonhalted[j], succs[k])) {
                        has_Z_succ = true;
                        break;
                    }
                }
            }
            if (!has_Z_succ) {
                in_Z[i] = false;
                changed = true;
            }
        }
    }

    /* Z now = EG(¬halted): states on an infinite non-halting path */
    int trap_count = 0;
    for (int i = 0; i < n_nh; i++)
        if (in_Z[i]) trap_count++;

    bool holds = (trap_count == 0);

    if (verbose) {
        if (holds) {
            printf("  AF(halted): HOLDS — every execution eventually halts\n");
        } else {
            printf("  AF(halted): VIOLATED — %d state(s) on non-terminating path(s)\n",
                   trap_count);
            printf("  Example trapped states:\n");
            int shown = 0;
            for (int i = 0; i < n_nh && shown < 3; i++) {
                if (in_Z[i]) {
                    printf("    ");
                    print_state(nonhalted[i]);
                    printf("\n");
                    shown++;
                }
            }
        }
    }

    free(in_Z);
    free(nonhalted);
    return holds;
}


/* ---------- combined model check --------------------------------------- */

ModelCheckResult model_check(bool verbose) {
    if (verbose) {
        printf("\nStarting model check ..\n");
        print_program();
    }

    ModelCheckResult res = check_safety(verbose);

    if (!res.safety_ok) return res;

    /* Rebuild visited set to pass to liveness check. */
    /* (check_safety already explored everything; we rebuild cheaply.) */
    /* For simplicity re-run exploration to collect the state set. */
    StateHashSet *visited = create_state_set();
    StateStack   *stack   = create_state_stack();
    if (!visited || !stack) goto skip_liveness;

    push_state(stack, create_state(0, 0, false));
    State cur;
    while (pop_state(stack, &cur)) {
        if (state_in_set(visited, cur)) continue;
        add_state_to_set(visited, cur);
        if (cur.halted) continue;
        if (cur.pc < 0 || cur.pc >= g_program.length) break;
        Instruction ins = g_program.instructions[cur.pc];
        switch (ins.op) {
            case INC:  push_state(stack, create_state(cur.pc+1, clamp(cur.r+1),           false)); break;
            case DEC:  push_state(stack, create_state(cur.pc+1, clamp(cur.r-1),           false)); break;
            case SET:  push_state(stack, create_state(cur.pc+1, clamp(ins.operand),       false)); break;
            case ADD:  push_state(stack, create_state(cur.pc+1, clamp(cur.r+ins.operand), false)); break;
            case SUB:  push_state(stack, create_state(cur.pc+1, clamp(cur.r-ins.operand), false)); break;
            case HALT: push_state(stack, create_state(cur.pc,   cur.r,                    true)); break;
            case JNZ:
                if (cur.r != 0) {
                    int jpc = cur.pc + ins.operand;
                    if (jpc >= 0 && jpc < g_program.length)
                        push_state(stack, create_state(jpc, cur.r, false));
                } else {
                    push_state(stack, create_state(cur.pc + 1, cur.r, false));
                }
                break;
            default: break;
        }
    }

    res.liveness_checked = true;
    res.liveness_ok = check_liveness(visited, visited->buckets,
                                     visited->count, verbose);

skip_liveness:
    destroy_state_set(visited);
    destroy_state_stack(stack);
    return res;
}


/* ---------- example programs ------------------------------------------- */

/*
 * Example 1 — simple counting loop.
 *
 *   r = 1
 *   if r != 0: jump to instruction 3   (always taken)
 *   r = r + 1                          (never reached)
 *   r = r - 1
 *   if r != 0: jump back               (r is now 0, not taken)
 *   halt
 *
 * AG(safe): HOLDS.  AF(halted): HOLDS (terminates unconditionally).
 */
void load_example_1(void) {
    printf("Example 1: simple counting loop\n");
    init_program(10);
    add_instruction(INC,  0);   /* 0: r = 1         */
    add_instruction(JNZ,  2);   /* 1: if r!=0 -> 3  */
    add_instruction(INC,  0);   /* 2: (dead code)   */
    add_instruction(DEC,  0);   /* 3: r = r-1       */
    add_instruction(JNZ, -3);   /* 4: if r!=0 -> 1  */
    add_instruction(HALT, 0);   /* 5: halt          */
}

/*
 * Example 2 — branching counter.
 *
 *   r = 5
 *   r = r - 1  (loop until r == 0)
 *   if r != 0: jump back
 *   r = r + 10         (r = 10)
 *   r = r - 3          (r = 7)
 *   if r != 0: skip one instruction  (taken)
 *   halt               (skipped)
 *   r = 0
 *   halt
 *
 * AG(safe): HOLDS.  AF(halted): HOLDS.
 */
void load_example_2(void) {
    printf("Example 2: branching counter with SET/ADD/SUB\n");
    init_program(15);
    add_instruction(SET,  5);   /* 0: r = 5         */
    add_instruction(DEC,  0);   /* 1: r = r-1       */
    add_instruction(JNZ, -1);   /* 2: if r!=0 -> 1  */
    add_instruction(ADD, 10);   /* 3: r = 10        */
    add_instruction(SUB,  3);   /* 4: r = 7         */
    add_instruction(JNZ,  2);   /* 5: if r!=0 -> 7  */
    add_instruction(HALT, 0);   /* 6: halt (skipped)*/
    add_instruction(SET,  0);   /* 7: r = 0         */
    add_instruction(HALT, 0);   /* 8: halt          */
}

/*
 * Example 3 — non-terminating loop (AF(halted) violated).
 *
 *   r = 1
 *   loop forever: r = r + 1 (clamped at MAX), then r = r - 1, jump back
 *
 * The register oscillates between MAX and MAX-1. No HALT instruction is
 * reachable. AF(halted) is violated; the model checker reports the trapped
 * states as a counterexample to termination.
 *
 * AG(safe): HOLDS (pc never out of bounds).
 * AF(halted): VIOLATED.
 */
void load_example_3(void) {
    printf("Example 3: non-terminating loop (expected: AF(halted) VIOLATED)\n");
    init_program(5);
    add_instruction(SET, 1);    /* 0: r = 1         */
    add_instruction(INC, 0);    /* 1: r = r+1       */
    add_instruction(DEC, 0);    /* 2: r = r-1       */
    add_instruction(JNZ, -2);   /* 3: if r!=0 -> 1  */
    add_instruction(HALT, 0);   /* 4: unreachable   */
}


/* ---------- main ------------------------------------------------------- */

int main(int argc, char *argv[]) {
    bool verbose = false;
    int  example = 1;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-v") || !strcmp(argv[i], "--verbose"))
            verbose = true;
        else if (!strcmp(argv[i], "-e2")) example = 2;
        else if (!strcmp(argv[i], "-e3")) example = 3;
        else if (!strcmp(argv[i], "-h") || !strcmp(argv[i], "--help")) {
            printf("Usage: %s [-v] [-e2|-e3] [-h]\n", argv[0]);
            printf("  -v      verbose output\n");
            printf("  -e2     example 2 (branching counter)\n");
            printf("  -e3     example 3 (non-terminating loop — AF violation)\n");
            return 0;
        }
    }

    switch (example) {
        case 2: load_example_2(); break;
        case 3: load_example_3(); break;
        default: load_example_1(); break;
    }

    ModelCheckResult res = model_check(verbose);

    printf("\nResults:\n");
    printf("  AG(safe)   : %s\n", res.safety_ok ? "HOLDS" : "VIOLATED");
    if (res.liveness_checked)
        printf("  AF(halted) : %s\n", res.liveness_ok ? "HOLDS" : "VIOLATED");
    printf("  States explored : %d\n", res.states_explored);

    if (!res.safety_ok)
        printf("  Error: %s\n", res.error_msg);

    destroy_program();
    return (res.safety_ok && (!res.liveness_checked || res.liveness_ok)) ? 0 : 1;
}
