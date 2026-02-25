/*
 * toyos.c — Operating System layer built on toyvm.c
 *
 * Adds OS abstractions on top of the cooperative kernel:
 *   - Process table (extends thread concept with parent/child relationships)
 *   - Virtual file system (in-memory files with file descriptors)
 *   - System call interface (syscall opcode with syscall numbers)
 *   - Simple shell for interactive command execution
 *   - Process lifecycle: fork, exec, exit, wait
 *
 * This demonstrates what an OS adds beyond a bare kernel:
 *   Kernel (toyvm.c): threads, scheduling, locks, IPC primitives
 *   OS (toyos.c):     processes, files, user/kernel mode boundary
 *
 * Build:   gcc -Wall -o toyos toyos.c
 * Run:     ./toyos
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>

/* CONFIGURATION */

#define MAX_PROCESSES    16
#define MAX_STACK        64
#define MAX_INSTRUCTIONS 512
#define MAX_LOCKS        16
#define MAX_SEMAPHORES   16
#define MAX_QUEUES       16
#define MAX_WAIT_QUEUE   16
#define MAX_LOCAL_VARS   32
#define MAX_GLOBALS      32
#define NAME_LEN         32

/* FILE SYSTEM */
#define MAX_FILES        32
#define MAX_FILE_SIZE    4096
#define MAX_OPEN_FILES   8   /* per process */
#define MAX_PATH         64

typedef int Value;

/* EXTENDED OPCODES (includes original VM opcodes + syscalls) */

typedef enum {
    OP_PUSH,
    OP_POP,
    OP_DUP,
    OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_MOD,
    OP_LOAD,
    OP_STORE,
    OP_GLOAD,
    OP_GSTORE,
    OP_JUMP,
    OP_JUMP_IF,
    OP_JUMP_IFNOT,
    OP_EQ, OP_LT, OP_GT,
    OP_LOCK_ACQUIRE,
    OP_LOCK_RELEASE,
    OP_SEM_ACQUIRE,
    OP_SEM_RELEASE,
    OP_QUEUE_SEND,
    OP_QUEUE_RECV,
    OP_PRINT,
    OP_PRINT_STR,
    OP_NOP,
    OP_EXIT,
    
    /* NEW: System call interface */
    OP_SYSCALL,      /* iarg = syscall number */
} Opcode;

/* SYSTEM CALL NUMBERS */

typedef enum {
    SYS_GETPID,      /* () -> pid */
    SYS_FORK,        /* () -> child_pid (0 in child) */
    SYS_EXEC,        /* (program_id) -> doesn't return on success */
    SYS_WAIT,        /* () -> child_pid */
    SYS_OPEN,        /* (path, flags) -> fd or -1 */
    SYS_READ,        /* (fd, count) -> value or -1 */
    SYS_WRITE,       /* (fd, value) -> bytes written or -1 */
    SYS_CLOSE,       /* (fd) -> 0 or -1 */
    SYS_SLEEP,       /* (ticks) -> 0 */
    SYS_GETTIME,     /* () -> current tick count */
} Syscall;

/* INSTRUCTIONS */

typedef struct {
    Opcode op;
    int    iarg;
    char   sarg[NAME_LEN];
} Instr;

/* FILE DESCRIPTOR */

typedef struct {
    int  file_id;    /* -1 if unused */
    int  offset;     /* current read/write position */
    int  flags;      /* open flags */
} FileDescriptor;

/* IN-MEMORY FILE */

typedef struct {
    char  path[MAX_PATH];
    char  data[MAX_FILE_SIZE];
    int   size;
    int   ref_count;  /* number of open file descriptors */
} File;

/* PROCESS CONTROL BLOCK
 * Extends the thread concept with parent/child relationships
 * and file descriptor table
 */

typedef enum {
    PS_RUNNING,
    PS_READY,
    PS_WAITING,
    PS_ZOMBIE,     /* terminated but parent hasn't wait()ed */
    PS_TERMINATED,
} ProcessState;

typedef struct {
    int  pid;
    int  parent_pid;
    char name[NAME_LEN];
    
    /* Execution context (same as Thread from toyvm) */
    int   pc;
    Value stack[MAX_STACK];
    int   sp;
    
    /* Thread-local variables */
    char  local_var_names[MAX_LOCAL_VARS][NAME_LEN];
    Value local_var_values[MAX_LOCAL_VARS];
    int   num_local_vars;
    
    /* Program */
    Instr instructions[MAX_INSTRUCTIONS];
    int   num_instructions;
    
    /* Process metadata */
    ProcessState state;
    int          priority;
    int          wait_resource_id;
    int          exit_code;
    
    /* File descriptor table */
    FileDescriptor fds[MAX_OPEN_FILES];
    
    /* Timing */
    int ticks_to_sleep;  /* 0 = not sleeping */
} Process;

/* WAIT QUEUE */

typedef struct {
    int pids[MAX_WAIT_QUEUE];
    int head, tail, count;
} WaitQueue;

/*
static void wait_queue_init(WaitQueue *wq) {
    wq->head = wq->tail = wq->count = 0;
}

static int wait_queue_is_empty(WaitQueue *wq) {
    return wq->count == 0;
}

//__attribute__((unused)) static int wait_queue_is_empty(WaitQueue *wq) {
//    return wq->count == 0;
//}

static void wait_queue_push(WaitQueue *wq, int pid) {
    assert(wq->count < MAX_WAIT_QUEUE);
    wq->pids[wq->tail] = pid;
    wq->tail = (wq->tail + 1) % MAX_WAIT_QUEUE;
    wq->count++;
}

static int wait_queue_pop(WaitQueue *wq) {
    assert(wq->count > 0);
    int pid = wq->pids[wq->head];
    wq->head = (wq->head + 1) % MAX_WAIT_QUEUE;
    wq->count--;
    return pid;
}
*/

/* LOCK */

typedef struct {
    int       id;
    int       locked;
    int       owner_pid;
    WaitQueue waiters;
} Lock;

/* SEMAPHORE */

typedef struct {
    int       id;
    int       count;
    WaitQueue waiters;
} Semaphore;

/* MESSAGE QUEUE */

#define MESSAGE_QUEUE_CAPACITY 32
typedef struct {
    int       id;
    Value     buffer[MESSAGE_QUEUE_CAPACITY];
    int       head, tail, count;
    WaitQueue receivers;
} MessageQueue;

/*
static void message_queue_init(MessageQueue *mq, int id) {
    mq->id = id;
    mq->head = mq->tail = mq->count = 0;
    wait_queue_init(&mq->receivers);
}

static int message_queue_is_empty(MessageQueue *mq) {
    return mq->count == 0;
}

static int message_queue_is_full(MessageQueue *mq) {
    return mq->count == MESSAGE_QUEUE_CAPACITY;
}

static void message_queue_enqueue(MessageQueue *mq, Value val) {
    assert(!message_queue_is_full(mq));
    mq->buffer[mq->tail] = val;
    mq->tail = (mq->tail + 1) % MESSAGE_QUEUE_CAPACITY;
    mq->count++;
}

static Value message_queue_dequeue(MessageQueue *mq) {
    assert(!message_queue_is_empty(mq));
    Value val = mq->buffer[mq->head];
    mq->head = (mq->head + 1) % MESSAGE_QUEUE_CAPACITY;
    mq->count--;
    return val;
}
*/

/* GLOBAL VARIABLES */

typedef struct {
    char name[NAME_LEN];
    Value val;
} Global;

/* OPERATING SYSTEM */

typedef struct {
    Process      processes[MAX_PROCESSES];
    int          num_processes;
    int          next_pid;
    
    int          run_queue[MAX_PROCESSES];
    int          run_queue_head;
    int          run_queue_tail;
    int          run_queue_count;
    
    Lock         locks[MAX_LOCKS];
    int          num_locks;
    
    Semaphore    semaphores[MAX_SEMAPHORES];
    int          num_semaphores;
    
    MessageQueue message_queues[MAX_QUEUES];
    int          num_message_queues;
    
    Global       globals[MAX_GLOBALS];
    int          num_globals;
    
    /* File system */
    File         files[MAX_FILES];
    int          num_files;
    
    /* System time */
    int          current_tick;
    
    int          debug;
} OS;

/* HELPER FUNCTIONS */

static void push(Process *p, Value val) {
    assert(p->sp < MAX_STACK - 1);
    p->stack[++p->sp] = val;
}

static Value pop(Process *p) {
    assert(p->sp >= 0);
    return p->stack[p->sp--];
}

static Value peek(Process *p) {
    assert(p->sp >= 0);
    return p->stack[p->sp];
}

static void store_local(Process *p, const char *name, Value val) {
    for (int i = 0; i < p->num_local_vars; i++) {
        if (!strcmp(p->local_var_names[i], name)) {
            p->local_var_values[i] = val;
            return;
        }
    }
    assert(p->num_local_vars < MAX_LOCAL_VARS);
    strcpy(p->local_var_names[p->num_local_vars], name);
    p->local_var_values[p->num_local_vars] = val;
    p->num_local_vars++;
}

static Value load_local(Process *p, const char *name) {
    for (int i = 0; i < p->num_local_vars; i++) {
        if (!strcmp(p->local_var_names[i], name)) {
            return p->local_var_values[i];
        }
    }
    fprintf(stderr, "ERROR: undefined local variable '%s'\n", name);
    return 0;
}

static void store_global(OS *os, const char *name, Value val) {
    for (int i = 0; i < os->num_globals; i++) {
        if (!strcmp(os->globals[i].name, name)) {
            os->globals[i].val = val;
            return;
        }
    }
    assert(os->num_globals < MAX_GLOBALS);
    strcpy(os->globals[os->num_globals].name, name);
    os->globals[os->num_globals].val = val;
    os->num_globals++;
}

static int load_global(OS *os, const char *name, Value *out) {
    for (int i = 0; i < os->num_globals; i++) {
        if (!strcmp(os->globals[i].name, name)) {
            *out = os->globals[i].val;
            return 1;
        }
    }
    return 0;
}

/* RUN QUEUE OPERATIONS */

static void enqueue_process(OS *os, int pid) {
    assert(os->run_queue_count < MAX_PROCESSES);
    os->run_queue[os->run_queue_tail] = pid;
    os->run_queue_tail = (os->run_queue_tail + 1) % MAX_PROCESSES;
    os->run_queue_count++;
}

static int dequeue_process(OS *os) {
    assert(os->run_queue_count > 0);
    int pid = os->run_queue[os->run_queue_head];
    os->run_queue_head = (os->run_queue_head + 1) % MAX_PROCESSES;
    os->run_queue_count--;
    return pid;
}

/* FILE SYSTEM OPERATIONS */

static int find_file(OS *os, const char *path) {
    for (int i = 0; i < os->num_files; i++) {
        if (strcmp(os->files[i].path, path) == 0) {
            return i;
        }
    }
    return -1;
}

static int create_file(OS *os, const char *path) {
    int existing = find_file(os, path);
    if (existing >= 0) {
        return existing;
    }
    
    assert(os->num_files < MAX_FILES);
    int file_id = os->num_files++;
    strcpy(os->files[file_id].path, path);
    os->files[file_id].size = 0;
    os->files[file_id].ref_count = 0;
    memset(os->files[file_id].data, 0, MAX_FILE_SIZE);
    return file_id;
}

static int allocate_fd(Process *p, int file_id, int flags) {
    for (int fd = 0; fd < MAX_OPEN_FILES; fd++) {
        if (p->fds[fd].file_id == -1) {
            p->fds[fd].file_id = file_id;
            p->fds[fd].offset = 0;
            p->fds[fd].flags = flags;
            return fd;
        }
    }
    return -1;  /* no free file descriptors */
}

/* INSTRUCTION CONSTRUCTORS */

static Instr instr_push(int val) {
    Instr i = {OP_PUSH, val, ""};
    return i;
}

static Instr instr_pop(void) {
    Instr i = {OP_POP, 0, ""};
    return i;
}

static Instr instr_dup(void) {
    Instr i = {OP_DUP, 0, ""};
    return i;
}

static Instr instr_add(void) {
    Instr i = {OP_ADD, 0, ""};
    return i;
}

/*
static Instr instr_sub(void) {
    Instr i = {OP_SUB, 0, ""};
    return i;
}

static Instr instr_mul(void) {
    Instr i = {OP_MUL, 0, ""};
    return i;
}

static Instr instr_div(void) {
    Instr i = {OP_DIV, 0, ""};
    return i;
}

static Instr instr_mod(void) {
    Instr i = {OP_MOD, 0, ""};
    return i;
}
*/

static Instr instr_load(const char *name) {
    Instr i = {OP_LOAD, 0, ""};
    strncpy(i.sarg, name, NAME_LEN - 1);
    return i;
}

static Instr instr_store(const char *name) {
    Instr i = {OP_STORE, 0, ""};
    strncpy(i.sarg, name, NAME_LEN - 1);
    return i;
}

/*
static Instr instr_global_load(const char *name) {
    Instr i = {OP_GLOAD, 0, ""};
    strncpy(i.sarg, name, NAME_LEN - 1);
    return i;
}

static Instr instr_global_store(const char *name) {
    Instr i = {OP_GSTORE, 0, ""};
    strncpy(i.sarg, name, NAME_LEN - 1);
    return i;
}
*/

static Instr instr_jump(int addr) {
    Instr i = {OP_JUMP, addr, ""};
    return i;
}

// static Instr instr_jump_if(int addr) {
//    Instr i = {OP_JUMP_IF, addr, ""};
//    return i;
// }

static Instr instr_jump_ifnot(int addr) {
    Instr i = {OP_JUMP_IFNOT, addr, ""};
    return i;
}

static Instr instr_eq(void) {
    Instr i = {OP_EQ, 0, ""};
    return i;
}

static Instr instr_lt(void) {
    Instr i = {OP_LT, 0, ""};
    return i;
}

/*
static Instr instr_gt(void) {
    Instr i = {OP_GT, 0, ""};
    return i;
}


static Instr instr_lock_acquire(int lock_id) {
    Instr i = {OP_LOCK_ACQUIRE, lock_id, ""};
    return i;
}

static Instr instr_lock_release(int lock_id) {
    Instr i = {OP_LOCK_RELEASE, lock_id, ""};
    return i;
}

static Instr instr_sem_acquire(int sem_id) {
    Instr i = {OP_SEM_ACQUIRE, sem_id, ""};
    return i;
}

static Instr instr_sem_release(int sem_id) {
    Instr i = {OP_SEM_RELEASE, sem_id, ""};
    return i;
}

static Instr instr_queue_send(int queue_id) {
    Instr i = {OP_QUEUE_SEND, queue_id, ""};
    return i;
}

static Instr instr_queue_recv(int queue_id) {
    Instr i = {OP_QUEUE_RECV, queue_id, ""};
    return i;
}
*/

static Instr instr_print(void) {
    Instr i = {OP_PRINT, 0, ""};
    return i;
}

static Instr instr_print_str(const char *str) {
    Instr i = {OP_PRINT_STR, 0, ""};
    strncpy(i.sarg, str, NAME_LEN - 1);
    return i;
}

// static Instr instr_nop(void) {
//    Instr i = {OP_NOP, 0, ""};
//    return i;
// }

static Instr instr_exit(void) {
    Instr i = {OP_EXIT, 0, ""};
    return i;
}

static Instr instr_syscall(int syscall_num) {
    Instr i = {OP_SYSCALL, syscall_num, ""};
    return i;
}


/* OPERATING SYSTEM INITIALIZATION */

static void os_init(OS *os, int debug) {
    memset(os, 0, sizeof(OS));
    os->next_pid = 1;
    os->debug = debug;
    os->current_tick = 0;
    
    /* Initialize all file descriptors to -1 (unused) */
    for (int i = 0; i < MAX_PROCESSES; i++) {
        for (int fd = 0; fd < MAX_OPEN_FILES; fd++) {
            os->processes[i].fds[fd].file_id = -1;
        }
    }
    
    /* Create standard files */
    create_file(os, "/dev/null");
    create_file(os, "/tmp/output.txt");
}

/* PROCESS CREATION */

static int create_process(OS *os, const char *name, Instr *instructions, 
                         int num_instructions, int priority, int parent_pid) {
    assert(os->num_processes < MAX_PROCESSES);
    
    int pid = os->next_pid++;
    Process *p = &os->processes[os->num_processes++];
    
    p->pid = pid;
    p->parent_pid = parent_pid;
    strncpy(p->name, name, NAME_LEN - 1);
    p->pc = 0;
    p->sp = -1;
    p->num_local_vars = 0;
    p->state = PS_READY;
    p->priority = priority;
    p->wait_resource_id = -1;
    p->exit_code = 0;
    p->ticks_to_sleep = 0;
    
    assert(num_instructions < MAX_INSTRUCTIONS);
    memcpy(p->instructions, instructions, num_instructions * sizeof(Instr));
    p->num_instructions = num_instructions;
    
    /* Initialize file descriptors */
    for (int fd = 0; fd < MAX_OPEN_FILES; fd++) {
        p->fds[fd].file_id = -1;
    }
    
    enqueue_process(os, pid);
    
    if (os->debug) {
        printf("  [OS] Created process %d (%s), priority=%d\n", 
               pid, name, priority);
    }
    
    return pid;
}

/* FIND PROCESS BY PID */

static Process* find_process(OS *os, int pid) {
    for (int i = 0; i < os->num_processes; i++) {
        if (os->processes[i].pid == pid) {
            return &os->processes[i];
        }
    }
    return NULL;
}

/* SYSTEM CALL IMPLEMENTATIONS */

static void syscall_getpid(OS *os, Process *p) {
    push(p, p->pid);
}

static void syscall_fork(OS *os, Process *parent) {
    /* Create child process as copy of parent */
    int child_pid = os->next_pid++;
    
    assert(os->num_processes < MAX_PROCESSES);
    Process *child = &os->processes[os->num_processes++];
    
    /* Copy parent's state */
    *child = *parent;
    child->pid = child_pid;
    child->parent_pid = parent->pid;
    snprintf(child->name, NAME_LEN, "%s-child", parent->name);
    child->state = PS_READY;
    
    /* Push return values: parent gets child PID, child gets 0 */
    push(parent, child_pid);
    child->sp = parent->sp;  /* child already has the stack copied */
    child->stack[child->sp] = 0;  /* overwrite with 0 for child */
    
    enqueue_process(os, child_pid);
    
    if (os->debug) {
        printf("  [FORK] Parent %d created child %d\n", 
               parent->pid, child_pid);
    }
}

static void syscall_wait(OS *os, Process *parent) {
    /* Find any zombie children */
    for (int i = 0; i < os->num_processes; i++) {
        Process *p = &os->processes[i];
        if (p->parent_pid == parent->pid && p->state == PS_ZOMBIE) {
            int child_pid = p->pid;
            push(parent, child_pid);
            p->state = PS_TERMINATED;  /* reap the zombie */
            if (os->debug) {
                printf("  [WAIT] Process %d reaped zombie child %d\n",
                       parent->pid, child_pid);
            }
            return;
        }
    }
    
    /* No zombie children - block until one exits */
    parent->state = PS_WAITING;
    if (os->debug) {
        printf("  [WAIT] Process %d blocked waiting for child\n", parent->pid);
    }
}

static void syscall_open(OS *os, Process *p) {
    int flags = pop(p);
    int path_val = pop(p);  /* simplified: path as integer ID */
    
    char path[MAX_PATH];
    snprintf(path, MAX_PATH, "/file%d", path_val);
    
    int file_id = create_file(os, path);
    int fd = allocate_fd(p, file_id, flags);
    
    if (fd >= 0) {
        os->files[file_id].ref_count++;
        if (os->debug) {
            printf("  [OPEN] Process %d opened %s as fd=%d\n", 
                   p->pid, path, fd);
        }
    }
    
    push(p, fd);
}

static void syscall_read(OS *os, Process *p) {
    pop(p); //int count = pop(p);
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_OPEN_FILES || p->fds[fd].file_id == -1) {
        push(p, -1);
        return;
    }
    
    int file_id = p->fds[fd].file_id;
    int offset = p->fds[fd].offset;
    File *f = &os->files[file_id];
    
    if (offset >= f->size) {
        push(p, 0);  /* EOF */
        return;
    }
    
    /* Read one value (simplified) */
    Value val = (offset < f->size) ? f->data[offset] : 0;
    p->fds[fd].offset++;
    
    push(p, val);
}

static void syscall_write(OS *os, Process *p) {
    int val = pop(p);
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_OPEN_FILES || p->fds[fd].file_id == -1) {
        push(p, -1);
        return;
    }
    
    int file_id = p->fds[fd].file_id;
    int offset = p->fds[fd].offset;
    File *f = &os->files[file_id];
    
    if (offset < MAX_FILE_SIZE) {
        f->data[offset] = (char)val;
        p->fds[fd].offset++;
        if (offset >= f->size) {
            f->size = offset + 1;
        }
        push(p, 1);  /* 1 byte written */
    } else {
        push(p, -1);  /* file full */
    }
}

static void syscall_close(OS *os, Process *p) {
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_OPEN_FILES || p->fds[fd].file_id == -1) {
        push(p, -1);
        return;
    }
    
    int file_id = p->fds[fd].file_id;
    os->files[file_id].ref_count--;
    p->fds[fd].file_id = -1;
    
    push(p, 0);
}

static void syscall_sleep(OS *os, Process *p) {
    int ticks = pop(p);
    p->ticks_to_sleep = ticks;
    p->state = PS_WAITING;
    
    if (os->debug) {
        printf("  [SLEEP] Process %d sleeping for %d ticks\n", p->pid, ticks);
    }
}

static void syscall_gettime(OS *os, Process *p) {
    push(p, os->current_tick);
}

/* EXECUTE ONE INSTRUCTION */

static int execute_instruction(OS *os, Process *p) {
    if (p->pc >= p->num_instructions) {
        return 0;  /* program ended */
    }
    
    Instr instr = p->instructions[p->pc];
    p->pc++;
    
    switch (instr.op) {
        case OP_PUSH:
            push(p, instr.iarg);
            break;
            
        case OP_POP:
            pop(p);
            break;
            
        case OP_DUP:
            push(p, peek(p));
            break;
            
        case OP_ADD: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a + b);
            break;
        }
        
        case OP_SUB: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a - b);
            break;
        }
        
        case OP_MUL: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a * b);
            break;
        }
        
        case OP_DIV: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a / b);
            break;
        }
        
        case OP_MOD: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a % b);
            break;
        }
        
        case OP_LOAD:
            push(p, load_local(p, instr.sarg));
            break;
            
        case OP_STORE:
            store_local(p, instr.sarg, pop(p));
            break;
            
        case OP_GLOAD: {
            Value val;
            if (load_global(os, instr.sarg, &val)) {
                push(p, val);
            } else {
                push(p, 0);
            }
            break;
        }
        
        case OP_GSTORE:
            store_global(os, instr.sarg, pop(p));
            break;
            
        case OP_JUMP:
            p->pc = instr.iarg;
            break;
            
        case OP_JUMP_IF:
            if (pop(p)) {
                p->pc = instr.iarg;
            }
            break;
            
        case OP_JUMP_IFNOT:
            if (!pop(p)) {
                p->pc = instr.iarg;
            }
            break;
            
        case OP_EQ: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a == b);
            break;
        }
        
        case OP_LT: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a < b);
            break;
        }
        
        case OP_GT: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a > b);
            break;
        }
        
        case OP_PRINT:
            printf("%d\n", pop(p));
            break;
            
        case OP_PRINT_STR:
            printf("%s\n", instr.sarg);
            break;
            
        case OP_NOP:
            break;
            
        case OP_EXIT:
            return 0;
            
        case OP_SYSCALL:
            switch (instr.iarg) {
                case SYS_GETPID:
                    syscall_getpid(os, p);
                    break;
                case SYS_FORK:
                    syscall_fork(os, p);
                    break;
                case SYS_WAIT:
                    syscall_wait(os, p);
                    return 1;  /* may have blocked */
                case SYS_OPEN:
                    syscall_open(os, p);
                    break;
                case SYS_READ:
                    syscall_read(os, p);
                    break;
                case SYS_WRITE:
                    syscall_write(os, p);
                    break;
                case SYS_CLOSE:
                    syscall_close(os, p);
                    break;
                case SYS_SLEEP:
                    syscall_sleep(os, p);
                    return 1;  /* blocked */
                case SYS_GETTIME:
                    syscall_gettime(os, p);
                    break;
                default:
                    fprintf(stderr, "ERROR: unknown syscall %d\n", instr.iarg);
            }
            break;
            
        default:
            fprintf(stderr, "ERROR: unknown opcode %d\n", instr.op);
            return 0;
    }
    
    return 1;
}

/* SCHEDULER AND MAIN LOOP */

static void run(OS *os, int max_steps) {
    int steps = 0;
    
    while (steps < max_steps && os->run_queue_count > 0) {
        /* Advance time */
        os->current_tick++;
        
        /* Wake up sleeping processes */
        for (int i = 0; i < os->num_processes; i++) {
            Process *p = &os->processes[i];
            if (p->state == PS_WAITING && p->ticks_to_sleep > 0) {
                p->ticks_to_sleep--;
                if (p->ticks_to_sleep == 0) {
                    p->state = PS_READY;
                    enqueue_process(os, p->pid);
                    if (os->debug) {
                        printf("  [WAKE] Process %d woke up\n", p->pid);
                    }
                }
            }
        }
        
        /* Get next process from run queue */
        int pid = dequeue_process(os);
        Process *current = find_process(os, pid);
        
        if (!current || current->state != PS_READY) {
            continue;
        }
        
        current->state = PS_RUNNING;
        
        /* Execute one instruction */
        int continue_running = execute_instruction(os, current);
        
        steps++;
        
        if (!continue_running || current->pc >= current->num_instructions) {
            /* Process terminated */
            current->state = PS_ZOMBIE;
            
            /* Wake up parent if waiting */
            if (current->parent_pid > 0) {
                Process *parent = find_process(os, current->parent_pid);
                if (parent && parent->state == PS_WAITING) {
                    parent->state = PS_READY;
                    enqueue_process(os, parent->pid);
                }
            }
            
            if (os->debug) {
                printf("  [EXIT] Process %d terminated\n", pid);
            }
        } else if (current->state == PS_RUNNING) {
            /* Process yielded normally - put back in queue */
            current->state = PS_READY;
            enqueue_process(os, pid);
        }
        /* else: process is now WAITING, don't re-queue */
    }
    
    if (os->debug && steps >= max_steps) {
        printf("  [OS] Reached max steps (%d)\n", max_steps);
    }
}

/* DEMOS */

static void demo_fork_wait(void) {
    printf("\nDEMO 1: Fork and Wait\n\n");
    printf("Parent process forks a child.\n");
    printf("Child does some work and exits.\n");
    printf("Parent waits for child to finish.\n\n");
    
    OS os;
    os_init(&os, 1);
    
    /*
     * Parent program:
     *  0  PUSH 100
     *  1  STORE "marker"    just to have something in stack
     *  2  SYSCALL SYS_GETPID
     *  3  DUP
     *  4  PRINT              print parent PID
     *  5  SYSCALL SYS_FORK
     *  6  DUP
     *  7  STORE "child_pid"
     *  8  PUSH 0
     *  9  EQ
     * 10  JIFNOT 16         if not child, jump to parent code
     *  
     * Child code (11-15):
     * 11  PRINT_STR "Child process running"
     * 12  PUSH 10
     * 13  PUSH 20
     * 14  ADD
     * 15  PRINT
     * 16  EXIT              (child exits here)
     *
     * Parent code (17-20):
     * 17  PRINT_STR "Parent waiting for child"
     * 18  SYSCALL SYS_WAIT
     * 19  PRINT              print reaped child PID
     * 20  EXIT
     */
    
    Instr program[] = {
        instr_push(100),
        instr_store("marker"),
        instr_syscall(SYS_GETPID),
        instr_dup(),
        instr_print(),
        instr_syscall(SYS_FORK),
        instr_dup(),
        instr_store("child_pid"),
        instr_push(0),
        instr_eq(),
        instr_jump_ifnot(17),
        /* Child */
        instr_print_str("Child process running"),
        instr_push(10),
        instr_push(20),
        instr_add(),
        instr_print(),
        instr_exit(),
        /* Parent */
        instr_print_str("Parent waiting for child"),
        instr_syscall(SYS_WAIT),
        instr_print(),
        instr_exit(),
    };
    
    create_process(&os, "parent", program, sizeof(program) / sizeof(program[0]), 0, 0);
    run(&os, 200);
    
    printf("\nDemo complete.\n");
}

static void demo_file_io(void) {
    printf("\nDEMO 2: File I/O\n\n");
    printf("Process opens a file, writes data, then reads it back.\n\n");
    
    OS os;
    os_init(&os, 1);
    
    /*
     *  0  PUSH 1           path ID
     *  1  PUSH 1           flags (write)
     *  2  SYSCALL SYS_OPEN
     *  3  STORE "fd"
     *  
     *  Write 65 ('A'):
     *  4  LOAD "fd"
     *  5  PUSH 65
     *  6  SYSCALL SYS_WRITE
     *  7  POP
     *  
     *  Write 66 ('B'):
     *  8  LOAD "fd"
     *  9  PUSH 66
     * 10  SYSCALL SYS_WRITE
     * 11  POP
     * 
     * 12  LOAD "fd"
     * 13  SYSCALL SYS_CLOSE
     * 14  POP
     * 
     * 15  PRINT_STR "File written, now reading"
     * 
     *  Open for read:
     * 16  PUSH 1
     * 17  PUSH 0           flags (read)
     * 18  SYSCALL SYS_OPEN
     * 19  STORE "fd"
     * 
     * 20  LOAD "fd"
     * 21  PUSH 1
     * 22  SYSCALL SYS_READ
     * 23  PRINT
     * 
     * 24  LOAD "fd"
     * 25  PUSH 1
     * 26  SYSCALL SYS_READ
     * 27  PRINT
     * 
     * 28  LOAD "fd"
     * 29  SYSCALL SYS_CLOSE
     * 30  POP
     * 31  EXIT
     */
    
    Instr program[] = {
        instr_push(1),
        instr_push(1),
        instr_syscall(SYS_OPEN),
        instr_store("fd"),
        
        instr_load("fd"),
        instr_push(65),
        instr_syscall(SYS_WRITE),
        instr_pop(),
        
        instr_load("fd"),
        instr_push(66),
        instr_syscall(SYS_WRITE),
        instr_pop(),
        
        instr_load("fd"),
        instr_syscall(SYS_CLOSE),
        instr_pop(),
        
        instr_print_str("Reading back from file:"),
        
        instr_push(1),
        instr_push(0),
        instr_syscall(SYS_OPEN),
        instr_store("fd"),
        
        instr_load("fd"),
        instr_push(1),
        instr_syscall(SYS_READ),
        instr_print(),
        
        instr_load("fd"),
        instr_push(1),
        instr_syscall(SYS_READ),
        instr_print(),
        
        instr_load("fd"),
        instr_syscall(SYS_CLOSE),
        instr_pop(),
        
        instr_exit(),
    };
    
    create_process(&os, "file-test", program, sizeof(program) / sizeof(program[0]), 0, 0);
    run(&os, 200);
    
    printf("\nDemo complete.\n");
}

static void demo_sleep_and_time(void) {
    printf("\nDEMO 3: Sleep and Timing\n\n");
    printf("Two processes print timestamps, one sleeps periodically.\n\n");
    
    OS os;
    os_init(&os, 1);
    
    /*
     * Fast worker (prints every iteration):
     *  0  PUSH 0
     *  1  STORE "i"
     *  2  LOAD "i"
     *  3  PUSH 5
     *  4  LT
     *  5  JIFNOT 12
     *  6  SYSCALL SYS_GETTIME
     *  7  PRINT
     *  8  LOAD "i"
     *  9  PUSH 1
     * 10  ADD
     * 11  STORE "i"
     * 12  JMP 2
     * 13  EXIT
     */
    
    Instr fast_program[] = {
        instr_push(0),
        instr_store("i"),
        instr_load("i"),
        instr_push(5),
        instr_lt(),
        instr_jump_ifnot(13),
        instr_syscall(SYS_GETTIME),
        instr_print(),
        instr_load("i"),
        instr_push(1),
        instr_add(),
        instr_store("i"),
        instr_jump(2),
        instr_exit(),
    };
    
    /*
     * Slow worker (sleeps between prints):
     *  0  PUSH 0
     *  1  STORE "i"
     *  2  LOAD "i"
     *  3  PUSH 3
     *  4  LT
     *  5  JIFNOT 16
     *  6  SYSCALL SYS_GETTIME
     *  7  PRINT
     *  8  PUSH 5
     *  9  SYSCALL SYS_SLEEP
     * 10  LOAD "i"
     * 11  PUSH 1
     * 12  ADD
     * 13  STORE "i"
     * 14  JMP 2
     * 15  EXIT
     */
    
    Instr slow_program[] = {
        instr_push(0),
        instr_store("i"),
        instr_load("i"),
        instr_push(3),
        instr_lt(),
        instr_jump_ifnot(16),
        instr_syscall(SYS_GETTIME),
        instr_print(),
        instr_push(5),
        instr_syscall(SYS_SLEEP),
        instr_load("i"),
        instr_push(1),
        instr_add(),
        instr_store("i"),
        instr_jump(2),
        instr_exit(),
    };
    
    create_process(&os, "fast", fast_program, sizeof(fast_program) / sizeof(fast_program[0]), 0, 0);
    create_process(&os, "slow", slow_program, sizeof(slow_program) / sizeof(slow_program[0]), 0, 0);
    
    run(&os, 300);
    
    printf("\nDemo complete.\n");
}

/* MAIN */

int main(void) {
    printf("\n");
    printf(" / toyos.c - Operating System Simulator\n");
    printf(" / Built on toyvm cooperative kernel\n\n");
    printf("   Features:\n");
    printf("   - Process management (fork, wait, exit)\n");
    printf("   - Virtual file system with file descriptors\n");
    printf("   - System call interface\n");
    printf("   - Time-based scheduling (sleep, gettime)\n\n");
    
    demo_fork_wait();
    demo_file_io();
    demo_sleep_and_time();
    
    printf("\nAll completed.\n\n");
    
    return 0;
}
