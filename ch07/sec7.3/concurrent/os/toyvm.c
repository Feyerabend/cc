/*
 * toyvm.c — A cooperative kernel simulator in C
 *
 * Ported and expanded from toyvm.py. The goal is not just a port but a
 * readable illustration of what an OS kernel actually does to manage
 * concurrency: thread control blocks, a run queue, a scheduler, locks
 * with wait queues, semaphores, and message passing.
 *
 * Everything runs in one real OS thread (cooperative, not preemptive),
 * exactly like the Python original — but the data structures and the
 * main loop are written to resemble the structures you'd find inside
 * a real kernel (Linux task_struct, wait_queue_head_t, etc.).
 *
 * Build:   gcc -Wall -o toyvm toyvm.c
 * Run:     ./toyvm
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>


/* CONFIGURATION */

#define MAX_THREADS      16
#define MAX_STACK        64
#define MAX_INSTRUCTIONS 256
#define MAX_LOCKS        16
#define MAX_SEMAPHORES   16
#define MAX_QUEUES       16
#define MAX_WAIT_QUEUE   16
#define MAX_LOCAL_VARS   32
#define MAX_GLOBALS      32
#define NAME_LEN         32

typedef int Value;

/* OPCODES */

typedef enum {
    OP_PUSH,
    OP_POP,
    OP_DUP,
    OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_MOD,
    OP_LOAD,    /* push thread-local variable        */
    OP_STORE,   /* pop into thread-local variable    */
    OP_GLOAD,   /* push shared/global variable       */
    OP_GSTORE,  /* pop into shared/global variable   */
    OP_JUMP,
    OP_JUMP_IF,          /* pop; jump if non-zero    */
    OP_JUMP_IFNOT,       /* pop; jump if zero        */
    OP_EQ, OP_LT, OP_GT,
    OP_LOCK_ACQUIRE,
    OP_LOCK_RELEASE,
    OP_SEM_ACQUIRE,
    OP_SEM_RELEASE,
    OP_QUEUE_SEND,
    OP_QUEUE_RECV,
    OP_PRINT,        /* pop and print as integer        */
    OP_PRINT_STR,    /* print literal string from sarg  */
    OP_NOP,
    OP_EXIT,
} Opcode;


/* INSTRUCTIONS */

typedef struct {
    Opcode op;
    int    iarg;           /* integer immediate or resource id */
    char   sarg[NAME_LEN]; /* variable / string argument       */
} Instr;

/*
 * THREAD CONTROL BLOCK (TCB)
 *
 * In a real OS every thread/process has one of these. Linux calls it
 * task_struct. It holds everything needed to suspend and resume a thread:
 *   - saved registers (here: pc + evaluation stack)
 *   - scheduling state and priority
 *   - pointer into whichever wait queue this thread is blocked on
 */

typedef enum {
    TS_RUNNABLE,   /* on the run queue, ready to execute  */
    TS_WAITING,    /* blocked on lock / semaphore / queue */
    TS_TERMINATED, /* finished                            */
} ThreadState;

typedef struct {
    int  id;
    char name[NAME_LEN];

    /* Saved execution context */
    int   pc;
    Value stack[MAX_STACK];
    int   sp;           /* index of top; -1 = empty */

    /* Thread-local symbol table */
    char  local_var_names[MAX_LOCAL_VARS][NAME_LEN];
    Value local_var_values[MAX_LOCAL_VARS];
    int   num_local_vars;

    /* Program */
    Instr instructions[MAX_INSTRUCTIONS];
    int   num_instructions;

    /* Scheduler metadata */
    ThreadState state;
    int         priority;

    /* Which resource is this thread waiting for? (-1 if none) */
    int wait_resource_id;
} Thread;

/*
 * WAIT QUEUE
 * FIFO list of thread IDs blocked on a resource.
 * Linux uses a doubly-linked list embedded in the TCB.
 */

typedef struct {
    int thread_ids[MAX_WAIT_QUEUE];
    int head, tail, count;
} WaitQueue;

static void wait_queue_init(WaitQueue *wait_queue) {
    wait_queue->head = wait_queue->tail = wait_queue->count = 0;
}

static int wait_queue_is_empty(WaitQueue *wait_queue) {
    return wait_queue->count == 0;
}

static void wait_queue_push(WaitQueue *wait_queue, int thread_id) {
    assert(wait_queue->count < MAX_WAIT_QUEUE);
    wait_queue->thread_ids[wait_queue->tail] = thread_id;
    wait_queue->tail = (wait_queue->tail + 1) % MAX_WAIT_QUEUE;
    wait_queue->count++;
}

static int wait_queue_pop(WaitQueue *wait_queue) {
    assert(wait_queue->count > 0);
    int thread_id = wait_queue->thread_ids[wait_queue->head];
    wait_queue->head = (wait_queue->head + 1) % MAX_WAIT_QUEUE;
    wait_queue->count--;
    return thread_id;
}

/* MUTEX LOCK
 * Corresponds to struct mutex in Linux, or CRITICAL_SECTION on Windows.
 */

typedef struct {
    int       id;
    int       locked;
    int       owner_thread_id; /* -1 if free */
    WaitQueue waiters;
} Lock;

/* SEMAPHORE
 * Corresponds to struct semaphore in Linux.
 * count > 0: resource(s) available. count == 0: callers block.
 */

typedef struct {
    int       id;
    int       count;
    WaitQueue waiters;
} Semaphore;

/* MESSAGE QUEUE
 * Like a bounded pipe or POSIX message queue.
 */

#define MESSAGE_QUEUE_CAPACITY 32
typedef struct {
    int       id;
    Value     buffer[MESSAGE_QUEUE_CAPACITY];
    int       head, tail, count;
    WaitQueue receivers;
} MessageQueue;

static void message_queue_init(MessageQueue *message_queue, int id) {
    message_queue->id = id;
    message_queue->head = message_queue->tail = message_queue->count = 0;
    wait_queue_init(&message_queue->receivers);
}

static int message_queue_is_empty(MessageQueue *message_queue) {
    return message_queue->count == 0;
}

static int message_queue_is_full(MessageQueue *message_queue) {
    return message_queue->count == MESSAGE_QUEUE_CAPACITY;
}

static void message_queue_enqueue(MessageQueue *message_queue, Value value) {
    assert(!message_queue_is_full(message_queue));
    message_queue->buffer[message_queue->tail] = value;
    message_queue->tail = (message_queue->tail + 1) % MESSAGE_QUEUE_CAPACITY;
    message_queue->count++;
}

static Value message_queue_dequeue(MessageQueue *message_queue) {
    assert(!message_queue_is_empty(message_queue));
    Value value = message_queue->buffer[message_queue->head];
    message_queue->head = (message_queue->head + 1) % MESSAGE_QUEUE_CAPACITY;
    message_queue->count--;
    return value;
}

/* GLOBAL / SHARED VARIABLES */

typedef struct { char name[NAME_LEN]; Value val; } Global;

/* THE KERNEL */

typedef struct {
    Thread      threads[MAX_THREADS];
    int         num_threads;
    int         next_thread_id;
    int         run_queue[MAX_THREADS];
    int         run_queue_head;
    int         run_queue_tail;
    int         run_queue_count;
    Lock        locks[MAX_LOCKS];
    int         num_locks;
    Semaphore   semaphores[MAX_SEMAPHORES];
    int         num_semaphores;
    MessageQueue message_queues[MAX_QUEUES];
    int         num_message_queues;
    Global      globals[MAX_GLOBALS];
    int         num_globals;
    int         debug;
} Kernel;

/* STACK / VARIABLE HELPERS */

static void push(Thread *thread, Value value) {
    assert(thread->sp < MAX_STACK - 1);
    thread->stack[++thread->sp] = value;
}

static Value pop(Thread *thread) {
    assert(thread->sp >= 0);
    return thread->stack[thread->sp--];
}

static Value peek(Thread *thread) {
    assert(thread->sp >= 0);
    return thread->stack[thread->sp];
}

static void store_local(Thread *thread, const char *name, Value value) {
    for (int i = 0; i < thread->num_local_vars; i++) {
        if (!strcmp(thread->local_var_names[i], name)) {
            thread->local_var_values[i] = value;
            return;
        }
    }
    assert(thread->num_local_vars < MAX_LOCAL_VARS);
    strncpy(thread->local_var_names[thread->num_local_vars], name, NAME_LEN - 1);
    thread->local_var_values[thread->num_local_vars++] = value;
}

static int load_local(Thread *thread, const char *name, Value *out) {
    for (int i = 0; i < thread->num_local_vars; i++) {
        if (!strcmp(thread->local_var_names[i], name)) {
            *out = thread->local_var_values[i];
            return 1;
        }
    }
    return 0;
}

static void store_global(Kernel *kernel, const char *name, Value value) {
    for (int i = 0; i < kernel->num_globals; i++) {
        if (!strcmp(kernel->globals[i].name, name)) {
            kernel->globals[i].val = value;
            return;
        }
    }
    assert(kernel->num_globals < MAX_GLOBALS);
    strncpy(kernel->globals[kernel->num_globals].name, name, NAME_LEN - 1);
    kernel->globals[kernel->num_globals++].val = value;
}

static int load_global(Kernel *kernel, const char *name, Value *out) {
    for (int i = 0; i < kernel->num_globals; i++) {
        if (!strcmp(kernel->globals[i].name, name)) {
            *out = kernel->globals[i].val;
            return 1;
        }
    }
    return 0;
}

/* RUN QUEUE */

static void run_queue_enqueue(Kernel *kernel, int thread_id) {
    assert(kernel->run_queue_count < MAX_THREADS);
    kernel->run_queue[kernel->run_queue_tail] = thread_id;
    kernel->run_queue_tail = (kernel->run_queue_tail + 1) % MAX_THREADS;
    kernel->run_queue_count++;
}

static int run_queue_dequeue(Kernel *kernel) {
    assert(kernel->run_queue_count > 0);
    int thread_id = kernel->run_queue[kernel->run_queue_head];
    kernel->run_queue_head = (kernel->run_queue_head + 1) % MAX_THREADS;
    kernel->run_queue_count--;
    return thread_id;
}

/* WAKEUP
 * Move a thread from WAITING -> RUNNABLE.
 * Corresponds to wake_up() / try_to_wake_up() in Linux. */

static void wakeup(Kernel *kernel, int thread_id) {
    Thread *thread = &kernel->threads[thread_id];
    if (thread->state == TS_WAITING) {
        thread->state = TS_RUNNABLE;
        thread->wait_resource_id = -1;
        run_queue_enqueue(kernel, thread_id);
        if (kernel->debug) {
            printf("  [kernel] wakeup: %s -> RUNNABLE\n", thread->name);
        }
    }
}

/* KERNEL + THREAD CREATION */

static void kernel_init(Kernel *kernel, int debug) {
    memset(kernel, 0, sizeof *kernel);
    kernel->debug = debug;
}

static int create_thread(Kernel *kernel, const char *name, const Instr *program, int num_instructions, int priority) {
    assert(kernel->num_threads < MAX_THREADS);
    int thread_id = kernel->next_thread_id++;
    Thread *thread = &kernel->threads[thread_id];
    memset(thread, 0, sizeof *thread);
    thread->id = thread_id;
    thread->sp = -1;
    thread->state = TS_RUNNABLE;
    thread->priority = priority;
    thread->wait_resource_id = -1;
    strncpy(thread->name, name, NAME_LEN - 1);
    assert(num_instructions <= MAX_INSTRUCTIONS);
    memcpy(thread->instructions, program, num_instructions * sizeof(Instr));
    thread->num_instructions = num_instructions;
    kernel->num_threads++;
    run_queue_enqueue(kernel, thread_id);
    if (kernel->debug) {
        printf("  [kernel] created %s (tid=%d)\n", name, thread_id);
    }
    return thread_id;
}

static int create_lock(Kernel *kernel) {
    assert(kernel->num_locks < MAX_LOCKS);
    int lock_id = kernel->num_locks++;
    kernel->locks[lock_id].id = lock_id;
    kernel->locks[lock_id].locked = 0;
    kernel->locks[lock_id].owner_thread_id = -1;
    wait_queue_init(&kernel->locks[lock_id].waiters);
    return lock_id;
}

static int create_semaphore(Kernel *kernel, int count) {
    assert(kernel->num_semaphores < MAX_SEMAPHORES);
    int semaphore_id = kernel->num_semaphores++;
    kernel->semaphores[semaphore_id].id = semaphore_id;
    kernel->semaphores[semaphore_id].count = count;
    wait_queue_init(&kernel->semaphores[semaphore_id].waiters);
    return semaphore_id;
}

static int create_message_queue(Kernel *kernel) {
    assert(kernel->num_message_queues < MAX_QUEUES);
    int queue_id = kernel->num_message_queues++;
    message_queue_init(&kernel->message_queues[queue_id], queue_id);
    return queue_id;
}

/* EXECUTE ONE INSTRUCTION
 *
 * This is the user->kernel boundary. When a thread executes a sync
 * instruction (lock, semaphore, queue) the kernel may:
 *   a) Let it proceed (resource available — fast path).
 *   b) Block it: set state=WAITING, remove from run queue, schedule
 *      someone else. On blocking we decrement pc so the instruction
 *      re-executes when woken (it will then take the fast path).
 *
 * Real kernels do the same via futex/sys_futex or __mutex_lock_slowpath. */

static void execute(Kernel *kernel, Thread *thread) {
    if (thread->pc >= thread->num_instructions) {
        thread->state = TS_TERMINATED;
        return;
    }
    Instr *instruction = &thread->instructions[thread->pc++];
    if (kernel->debug) {
        printf("  [%-10s] pc=%-3d op=%d  sp=%d\n", thread->name, thread->pc - 1, instruction->op, thread->sp + 1);
    }

    switch (instruction->op) {
    case OP_PUSH:
        push(thread, instruction->iarg);
        break;
    case OP_POP:
        if (thread->sp >= 0) pop(thread);
        break;
    case OP_DUP:
        if (thread->sp >= 0) push(thread, peek(thread));
        break;

    case OP_ADD: {
        Value b = pop(thread), a = pop(thread);
        push(thread, a + b);
        break;
    }
    case OP_SUB: {
        Value b = pop(thread), a = pop(thread);
        push(thread, a - b);
        break;
    }
    case OP_MUL: {
        Value b = pop(thread), a = pop(thread);
        push(thread, a * b);
        break;
    }
    case OP_DIV: {
        Value b = pop(thread), a = pop(thread);
        push(thread, b ? a / b : 0);
        break;
    }
    case OP_MOD: {
        Value b = pop(thread), a = pop(thread);
        push(thread, b ? a % b : 0);
        break;
    }

    case OP_EQ: {
        Value b = pop(thread), a = pop(thread);
        push(thread, a == b);
        break;
    }
    case OP_LT: {
        Value b = pop(thread), a = pop(thread);
        push(thread, a < b);
        break;
    }
    case OP_GT: {
        Value b = pop(thread), a = pop(thread);
        push(thread, a > b);
        break;
    }

    case OP_LOAD: {
        Value value = 0;
        if (!load_local(thread, instruction->sarg, &value))
            printf("[%s] WARNING: LOAD undefined local '%s'\n", thread->name, instruction->sarg);
        push(thread, value);
        break;
    }
    case OP_STORE:
        store_local(thread, instruction->sarg, pop(thread));
        break;
    case OP_GLOAD: {
        Value value = 0;
        if (!load_global(kernel, instruction->sarg, &value))
            printf("[%s] WARNING: GLOAD undefined global '%s'\n", thread->name, instruction->sarg);
        push(thread, value);
        break;
    }
    case OP_GSTORE:
        store_global(kernel, instruction->sarg, pop(thread));
        break;

    case OP_JUMP:
        thread->pc = instruction->iarg;
        break;
    case OP_JUMP_IF: {
        Value condition = pop(thread);
        if (condition) thread->pc = instruction->iarg;
        break;
    }
    case OP_JUMP_IFNOT: {
        Value condition = pop(thread);
        if (!condition) thread->pc = instruction->iarg;
        break;
    }
    case OP_EXIT:
        thread->state = TS_TERMINATED;
        break;

    /*
     * MUTEX LOCK  (like mutex_lock / futex in Linux)
     *
     * Fast path:  lock is free -> claim it, continue.
     * Re-execute: we already own it (woken up by releaser) -> continue.
     * Slow path:  lock is held -> join wait queue, block.
     *
     * The "already owner" check is the key: the releaser calls wakeup()
     * AND sets owner_tid=waiter BEFORE the waiter re-runs. So when the
     * waiter re-executes OP_LOCK_ACQUIRE it sees it already owns the lock.
     */
    case OP_LOCK_ACQUIRE: {
        Lock *lock = &kernel->locks[instruction->iarg];
        if (!lock->locked) {
            lock->locked = 1;
            lock->owner_thread_id = thread->id;
            if (kernel->debug) printf("  [%-10s] acquired lock %d\n", thread->name, instruction->iarg);
        } else if (lock->owner_thread_id == thread->id) {
            /* already ours — re-execute path after wakeup, nothing to do */
        } else {
            if (kernel->debug) printf("  [%-10s] blocking on lock %d (held by tid=%d)\n", thread->name, instruction->iarg, lock->owner_thread_id);
            wait_queue_push(&lock->waiters, thread->id);
            thread->state = TS_WAITING;
            thread->wait_resource_id = instruction->iarg;
            thread->pc--; /* re-execute this instruction when woken */
        }
        break;
    }

    case OP_LOCK_RELEASE: {
        Lock *lock = &kernel->locks[instruction->iarg];
        if (!lock->locked || lock->owner_thread_id != thread->id) {
            printf("[%s] WARNING: LOCK_RELEASE not owner\n", thread->name);
            break;
        }
        if (!wait_queue_is_empty(&lock->waiters)) {
            int next_thread_id = wait_queue_pop(&lock->waiters);
            lock->owner_thread_id = next_thread_id; /* hand lock to next waiter directly */
            wakeup(kernel, next_thread_id);
            if (kernel->debug) printf("  [%-10s] released lock %d -> tid=%d\n", thread->name, instruction->iarg, next_thread_id);
        } else {
            lock->locked = 0;
            lock->owner_thread_id = -1;
            if (kernel->debug) printf("  [%-10s] released lock %d (free)\n", thread->name, instruction->iarg);
        }
        break;
    }

    /* SEMAPHORE  (like down() / up() in Linux)
     *
     * sem_wait / down: count > 0 -> decrement, proceed.
     *                  count == 0 -> block.
     * sem_post / up:   waiter exists -> wake one (permit handed directly).
     *                  no waiter -> increment count.
     *
     * Classic use: producer/consumer, resource pools.
     */
    case OP_SEM_ACQUIRE: {
        Semaphore *semaphore = &kernel->semaphores[instruction->iarg];
        if (semaphore->count > 0) {
            semaphore->count--;
            if (kernel->debug) printf("  [%-10s] sem %d acquired (count->%d)\n", thread->name, instruction->iarg, semaphore->count);
        } else {
            if (kernel->debug) printf("  [%-10s] blocking on sem %d (count=0)\n", thread->name, instruction->iarg);
            wait_queue_push(&semaphore->waiters, thread->id);
            thread->state = TS_WAITING;
            thread->wait_resource_id = instruction->iarg;
            thread->pc--;
        }
        break;
    }

    case OP_SEM_RELEASE: {
        Semaphore *semaphore = &kernel->semaphores[instruction->iarg];
        semaphore->count++; /* increment first so re-executing SACQ sees count > 0 */
        if (!wait_queue_is_empty(&semaphore->waiters)) {
            int next_thread_id = wait_queue_pop(&semaphore->waiters);
            wakeup(kernel, next_thread_id);
            if (kernel->debug) printf("  [%-10s] sem %d posted (count->%d) -> woke tid=%d\n", thread->name, instruction->iarg, semaphore->count, next_thread_id);
        } else {
            if (kernel->debug) printf("  [%-10s] sem %d posted (count->%d)\n", thread->name, instruction->iarg, semaphore->count);
        }
        break;
    }

    /* MESSAGE QUEUE  (like pipe / mq_send+mq_receive)
     *
     * SEND: receiver waiting -> direct rendezvous (push onto its stack).
     *       no receiver -> enqueue message.
     * RECV: message available -> dequeue.
     *       no message -> block.
     */
    case OP_QUEUE_SEND: {
        MessageQueue *message_queue = &kernel->message_queues[instruction->iarg];
        Value message = pop(thread);
        if (!wait_queue_is_empty(&message_queue->receivers)) {
            int receiver_thread_id = wait_queue_pop(&message_queue->receivers);
            push(&kernel->threads[receiver_thread_id], message); /* deliver directly */
            wakeup(kernel, receiver_thread_id);
            if (kernel->debug) printf("  [%-10s] sent %d directly to tid=%d\n", thread->name, message, receiver_thread_id);
        } else {
            message_queue_enqueue(message_queue, message);
            if (kernel->debug) printf("  [%-10s] enqueued %d -> queue %d\n", thread->name, message, instruction->iarg);
        }
        break;
    }

    case OP_QUEUE_RECV: {
        MessageQueue *message_queue = &kernel->message_queues[instruction->iarg];
        if (!message_queue_is_empty(message_queue)) {
            push(thread, message_queue_dequeue(message_queue));
            if (kernel->debug) printf("  [%-10s] received from queue %d\n", thread->name, instruction->iarg);
        } else {
            if (kernel->debug) printf("  [%-10s] blocking on queue %d (empty)\n", thread->name, instruction->iarg);
            wait_queue_push(&message_queue->receivers, thread->id);
            thread->state = TS_WAITING;
            thread->wait_resource_id = instruction->iarg;
            thread->pc--;
        }
        break;
    }

    case OP_PRINT:
        if (thread->sp >= 0) printf("  [%-10s] %d\n", thread->name, pop(thread));
        break;
    case OP_PRINT_STR:
        printf("  [%-10s] %s\n", thread->name, instruction->sarg);
        break;
    case OP_NOP:
        break;

    default:
        printf("[%s] unknown opcode %d\n", thread->name, instruction->op);
        break;
    }
}

/* 
 * THE SCHEDULER
 *
 * This is the kernel's main loop. Real kernels do this in schedule()
 * (Linux) or swtch() (xv6). We use round-robin: each thread gets one
 * instruction per turn (cooperative time-slicing).
 *
 * In a real preemptive kernel a hardware timer fires an interrupt that
 * forces a context switch. Here we move on after every instruction —
 * cooperative but sufficient to illustrate the concepts.
 *
 * Loop:
 *   1. Dequeue next RUNNABLE thread (round-robin).
 *   2. Execute one instruction (may block or terminate it).
 *   3. If still RUNNABLE, re-enqueue at tail.
 *   4. Repeat until all TERMINATED or run queue is empty (deadlock).
 */

static int all_terminated(Kernel *kernel) {
    for (int i = 0; i < kernel->num_threads; i++) {
        if (kernel->threads[i].state != TS_TERMINATED) return 0;
    }
    return 1;
}

static void run(Kernel *kernel, int max_steps) {
    int steps = 0;
    printf("\n  [scheduler] starting — %d thread(s)\n", kernel->num_threads);

    while (steps < max_steps && !all_terminated(kernel)) {
        if (kernel->run_queue_count == 0) {
            if (!all_terminated(kernel)) {
                printf("  [scheduler] DEADLOCK — run queue empty, blocked threads:\n");
                for (int i = 0; i < kernel->num_threads; i++) {
                    Thread *thread = &kernel->threads[i];
                    if (thread->state == TS_WAITING)
                        printf("    %s is waiting on resource %d\n", thread->name, thread->wait_resource_id);
                }
            }
            break;
        }

        /* --- CONTEXT SWITCH ---
         * Dequeue the next thread. In a real kernel this saves the
         * outgoing thread's register file and restores the incoming one
         * (assembly: __switch_to on x86, cpu_switch_to on ARM).
         * Our "register file" is just pc+stack inside Thread. */
        int thread_id = run_queue_dequeue(kernel);
        Thread *thread = &kernel->threads[thread_id];
        if (thread->state != TS_RUNNABLE) continue;

        execute(kernel, thread);
        steps++;

        if (thread->state == TS_RUNNABLE) {
            run_queue_enqueue(kernel, thread_id); /* back of the line (round-robin) */
        } else if (thread->state == TS_TERMINATED) {
            printf("  [scheduler] thread %s exited.\n", thread->name);
        }
        /* TS_WAITING: stays off run queue until wakeup() is called */
    }

    if (steps >= max_steps) printf("  [scheduler] step limit (%d) reached.\n", max_steps);
    else printf("  [scheduler] done in %d steps.\n\n", steps);
}

/*
 * INSTRUCTION BUILDER HELPERS
 */

static Instr instr_push(int value) {
    Instr instr = {OP_PUSH, value, ""};
    return instr;
}

static Instr instr_add(void) {
    Instr instr = {OP_ADD, 0, ""};
    return instr;
}

static Instr instr_sub(void) {
    Instr instr = {OP_SUB, 0, ""};
    return instr;
}

static Instr instr_mul(void) {
    Instr instr = {OP_MUL, 0, ""};
    return instr;
}

static Instr instr_lt(void) {
    Instr instr = {OP_LT, 0, ""};
    return instr;
}

static Instr instr_jump(int target) {
    Instr instr = {OP_JUMP, target, ""};
    return instr;
}

static Instr instr_jump_if(int target) {
    Instr instr = {OP_JUMP_IF, target, ""};
    return instr;
}

static Instr instr_jump_ifnot(int target) {
    Instr instr = {OP_JUMP_IFNOT, target, ""};
    return instr;
}

static Instr instr_load(const char *name) {
    Instr instr = {OP_LOAD, 0, ""};
    strncpy(instr.sarg, name, NAME_LEN - 1);
    return instr;
}

static Instr instr_store(const char *name) {
    Instr instr = {OP_STORE, 0, ""};
    strncpy(instr.sarg, name, NAME_LEN - 1);
    return instr;
}

static Instr instr_global_load(const char *name) {
    Instr instr = {OP_GLOAD, 0, ""};
    strncpy(instr.sarg, name, NAME_LEN - 1);
    return instr;
}

static Instr instr_global_store(const char *name) {
    Instr instr = {OP_GSTORE, 0, ""};
    strncpy(instr.sarg, name, NAME_LEN - 1);
    return instr;
}

static Instr instr_lock_acquire(int id) {
    Instr instr = {OP_LOCK_ACQUIRE, id, ""};
    return instr;
}

static Instr instr_lock_release(int id) {
    Instr instr = {OP_LOCK_RELEASE, id, ""};
    return instr;
}

static Instr instr_sem_acquire(int id) {
    Instr instr = {OP_SEM_ACQUIRE, id, ""};
    return instr;
}

static Instr instr_sem_release(int id) {
    Instr instr = {OP_SEM_RELEASE, id, ""};
    return instr;
}

static Instr instr_queue_send(int id) {
    Instr instr = {OP_QUEUE_SEND, id, ""};
    return instr;
}

static Instr instr_queue_recv(int id) {
    Instr instr = {OP_QUEUE_RECV, id, ""};
    return instr;
}

static Instr instr_print(void) {
    Instr instr = {OP_PRINT, 0, ""};
    return instr;
}

static Instr instr_print_str(const char *str) {
    Instr instr = {OP_PRINT_STR, 0, ""};
    strncpy(instr.sarg, str, NAME_LEN - 1);
    return instr;
}

static Instr instr_nop(void) {
    Instr instr = {OP_NOP, 0, ""};
    return instr;
}

static Instr instr_exit(void) {
    Instr instr = {OP_EXIT, 0, ""};
    return instr;
}

/*
 * DEMO 1: MUTEX — two threads, one shared counter
 *
 * Two worker threads each increment a shared counter 5 times, protected
 * by a mutex. Without the lock, interleaved read-modify-write cycles
 * would corrupt the counter.
 *
 * Illustrates:
 *   - critical sections
 *   - lock contention and wait-queue hand-off
 *   - why unprotected shared state is dangerous
 */

static void demo_mutex(void) {
    printf("  DEMO 1: Mutex — two threads, shared counter\n\n");
    printf("  Two worker threads each increment a shared\n");
    printf("  counter 5 times under a mutex.\n");
    printf("  Expected final counter: 10\n");

    Kernel kernel;
    kernel_init(&kernel, 0);
    store_global(&kernel, "counter", 0);
    int lock_id = create_lock(&kernel);  /* lock id = 0 */

    /*
     * Instructions (indices 0..20):
     *
     *  0  PUSH 0
     *  1  STORE "i"          i = 0
     *  2  LOAD "i"           ← loop header
     *  3  PUSH 5
     *  4  LT                 i < 5?
     *  5  JIFNOT 20          if NOT (i<5) -> exit at 20
     *  6  LACQ lid           — critical section begin —
     *  7  GLOAD "counter"
     *  8  PUSH 1
     *  9  ADD
     * 10  GSTORE "counter"   counter++
     * 11  GLOAD "counter"
     * 12  PRINT              print new value
     * 13  LREL lid           — critical section end —
     * 14  LOAD "i"
     * 15  PUSH 1
     * 16  ADD
     * 17  STORE "i"          i++
     * 18  JMP 2              back to loop header
     * 19  NOP
     * 20  EXIT
     */
    Instr program_instructions[] = {
        /*  0 */ instr_push(0),
        /*  1 */ instr_store("i"),
        /*  2 */ instr_load("i"),
        /*  3 */ instr_push(5),
        /*  4 */ instr_lt(),
        /*  5 */ instr_jump_ifnot(20),
        /*  6 */ instr_lock_acquire(lock_id),
        /*  7 */ instr_global_load("counter"),
        /*  8 */ instr_push(1),
        /*  9 */ instr_add(),
        /* 10 */ instr_global_store("counter"),
        /* 11 */ instr_global_load("counter"),
        /* 12 */ instr_print(),
        /* 13 */ instr_lock_release(lock_id),
        /* 14 */ instr_load("i"),
        /* 15 */ instr_push(1),
        /* 16 */ instr_add(),
        /* 17 */ instr_store("i"),
        /* 18 */ instr_jump(2),
        /* 19 */ instr_nop(),
        /* 20 */ instr_exit(),
    };
    int num_instructions = (int)(sizeof program_instructions / sizeof program_instructions[0]);

    create_thread(&kernel, "worker-A", program_instructions, num_instructions, 0);
    create_thread(&kernel, "worker-B", program_instructions, num_instructions, 0);
    run(&kernel, 1000);

    Value final = 0;
    load_global(&kernel, "counter", &final);
    printf("  Final counter = %d  (expected 10)\n\n", final);
}

/*
 * DEMO 2: PRODUCER / CONSUMER — semaphore + message queue
 *
 * The classic OS bounded-buffer problem (Dijkstra, 1965).
 *
 * - Semaphore "items" counts produced-but-not-yet-consumed items.
 * - Queue carries the actual values.
 * - Producer: make item -> enqueue -> signal semaphore.
 * - Consumer: wait on semaphore -> dequeue -> process.
 *
 * The consumer may run ahead and block (items=0) until the producer
 * catches up. The scheduler interleaves them naturally.
 *
 * Illustrates:
 *   - semaphores as resource counters
 *   - blocking I/O and wakeup
 *   - direct message handoff (rendezvous)
 */

static void demo_producer_consumer(void) {
    printf("\n");
    printf("  DEMO 2: Producer/Consumer — semaphore + queue\n\n");
    printf("  Producer sends integers 0, 10, 20, 30, 40.\n");
    printf("  Consumer blocks until each one is ready.\n");

    Kernel kernel;
    kernel_init(&kernel, 0);
    int queue_id = create_message_queue(&kernel);      /* queue id = 0 */
    int semaphore_id = create_semaphore(&kernel, 0);   /* sem id = 0, starts at 0 */

    /*
     * PRODUCER (sends n*10 for n = 0..4):
     *  0  PUSH 0
     *  1  STORE "n"
     *  2  LOAD "n"         ← loop
     *  3  PUSH 5
     *  4  LT
     *  5  JIFNOT 15        n>=5 -> exit
     *  6  LOAD "n"
     *  7  PUSH 10
     *  8  MUL
     *  9  QSEND qid        push item
     * 10  SREL sid          signal: one more item
     * 11  LOAD "n"
     * 12  PUSH 1
     * 13  ADD
     * 14  STORE "n"
     * -> JMP back, but we need exit at a different index:
     *    JIFNOT(16) and JMP(2) at 15, EXIT at 16
     */
    Instr producer_instructions[] = {
        /*  0 */ instr_push(0),
        /*  1 */ instr_store("n"),
        /*  2 */ instr_load("n"),
        /*  3 */ instr_push(5),
        /*  4 */ instr_lt(),
        /*  5 */ instr_jump_ifnot(16),
        /*  6 */ instr_load("n"),
        /*  7 */ instr_push(10),
        /*  8 */ instr_mul(),
        /*  9 */ instr_queue_send(queue_id),
        /* 10 */ instr_sem_release(semaphore_id),
        /* 11 */ instr_load("n"),
        /* 12 */ instr_push(1),
        /* 13 */ instr_add(),
        /* 14 */ instr_store("n"),
        /* 15 */ instr_jump(2),
        /* 16 */ instr_exit(),
    };
    int num_producer_instructions = (int)(sizeof producer_instructions / sizeof producer_instructions[0]);

    /*
     * CONSUMER (receives 5 items):
     *  0  PUSH 0
     *  1  STORE "got"
     *  2  LOAD "got"       ← loop
     *  3  PUSH 5
     *  4  LT
     *  5  JIFNOT 14        got>=5 -> exit
     *  6  SACQ sid          wait: items > 0
     *  7  QRECV qid         receive
     *  8  PRINT
     *  9  LOAD "got"
     * 10  PUSH 1
     * 11  ADD
     * 12  STORE "got"
     * 13  JMP 2
     * 14  EXIT
     */
    Instr consumer_instructions[] = {
        /*  0 */ instr_push(0),
        /*  1 */ instr_store("got"),
        /*  2 */ instr_load("got"),
        /*  3 */ instr_push(5),
        /*  4 */ instr_lt(),
        /*  5 */ instr_jump_ifnot(14),
        /*  6 */ instr_sem_acquire(semaphore_id),
        /*  7 */ instr_queue_recv(queue_id),
        /*  8 */ instr_print(),
        /*  9 */ instr_load("got"),
        /* 10 */ instr_push(1),
        /* 11 */ instr_add(),
        /* 12 */ instr_store("got"),
        /* 13 */ instr_jump(2),
        /* 14 */ instr_exit(),
    };
    int num_consumer_instructions = (int)(sizeof consumer_instructions / sizeof consumer_instructions[0]);

    create_thread(&kernel, "producer", producer_instructions, num_producer_instructions, 0);
    create_thread(&kernel, "consumer", consumer_instructions, num_consumer_instructions, 0);
    run(&kernel, 500);
}

/*
 * DEMO 3: DEADLOCK DETECTION
 *
 * Thread A: acquires lock 0, then tries to acquire lock 1.
 * Thread B: acquires lock 1, then tries to acquire lock 0.
 *
 * Neither can proceed — classic circular wait deadlock.
 * The scheduler detects this when the run queue empties but threads
 * remain in WAITING state.
 *
 * Illustrates:
 *   - circular wait (Coffman's 4th condition for deadlock)
 *   - how the kernel detects "all threads permanently blocked"
 *   - why lock-ordering is the standard prevention strategy
 */

static void demo_deadlock(void) {
    printf("\n");
    printf("  DEMO 3: Deadlock — circular lock dependency\n\n");
    printf("  Thread A holds lock 0 and waits for lock 1.\n");
    printf("  Thread B holds lock 1 and waits for lock 0.\n\n");

    Kernel kernel;
    kernel_init(&kernel, 0);
    int lock0 = create_lock(&kernel);
    int lock1 = create_lock(&kernel);

    Instr thread_a_instructions[] = {
        /* 0 */ instr_lock_acquire(lock0),
        /* 1 */ instr_print_str("acquired lock 0, now trying lock 1..."),
        /* 2 */ instr_nop(), instr_nop(), instr_nop(),
        /* 5 */ instr_lock_acquire(lock1),   /* BLOCKS — B holds lock 1 */
        /* 6 */ instr_print_str("(unreachable) got both locks"),
        /* 7 */ instr_lock_release(lock1),
        /* 8 */ instr_lock_release(lock0),
        /* 9 */ instr_exit(),
    };

    Instr thread_b_instructions[] = {
        /* 0 */ instr_lock_acquire(lock1),
        /* 1 */ instr_print_str("acquired lock 1, now trying lock 0..."),
        /* 2 */ instr_nop(), instr_nop(), instr_nop(),
        /* 5 */ instr_lock_acquire(lock0),   /* BLOCKS — A holds lock 0 */
        /* 6 */ instr_print_str("(unreachable) got both locks"),
        /* 7 */ instr_lock_release(lock0),
        /* 8 */ instr_lock_release(lock1),
        /* 9 */ instr_exit(),
    };

    create_thread(&kernel, "thread-A", thread_a_instructions, (int)(sizeof thread_a_instructions / sizeof thread_a_instructions[0]), 0);
    create_thread(&kernel, "thread-B", thread_b_instructions, (int)(sizeof thread_b_instructions / sizeof thread_b_instructions[0]), 0);
    run(&kernel, 200);
    printf("  Deadlock detected. Prevention: always acquire locks in the same order.\n\n");
}


/* MAIN */

int main(void) {
    printf("\n\n");
    printf(" / vm.c — Cooperative Kernel Simulator in C\n");
    printf(" / Illustrating: TCBs, run queue, locks, semaphores\n");
    printf("\n\n");

    demo_mutex();
    demo_producer_consumer();
    demo_deadlock();

    return 0;
}

