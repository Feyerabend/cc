/*
 * gc_vm_extended.c - Two GC strategies in one tiny Stack-Based VM
 *
 * Extends gc_vm.c to contrast TWO memory management strategies
 * operating on the same object graph:
 *
 *   Strategy A: Mark-and-Sweep (tracing GC)
 *     - Used for "MS" objects: OBJ_INT, OBJ_PAIR
 *     - Objects are freed in bulk, lazily, when the heap fills up
 *     - Cannot detect garbage immediately; can handle cycles
 *
 *   Strategy B: Reference Counting
 *     - Used for "RC" objects: OBJ_RC_INT, OBJ_RC_PAIR
 *     - refcount incremented on every pointer store, decremented on release
 *     - Object freed immediately when refcount hits zero
 *     - Cannot handle cycles without auxiliary cycle detection
 *
 * WHY THIS MATTERS FOR LOW-LEVEL PROGRAMMING
 * -----------------------
 * Both strategies appear constantly in production C/C++ code:
 *
 *   Mark-and-sweep:
 *     - Lua, MicroPython, SpiderMonkey (all C)
 *     - GHC's runtime (for Haskell compiled to native code)
 *
 *   Reference counting:
 *     - Linux kernel: struct kref, used in drivers, net stack, VFS
 *     - COM/OLE on Windows: IUnknown::AddRef / Release
 *     - CPython: every PyObject has ob_refcnt
 *     - LLVM/Clang's ARC (Automatic Reference Counting) for Obj-C
 *     - C++ shared_ptr<T> (std::atomic<int> ref counter underneath)
 *
 * The key engineering trade-off:
 *
 *   Mark-and-sweep  -> latency spikes (stop-the-world), but simple
 *                      allocation (just bump a pointer or prepend to list),
 *                      handles cycles for free.
 *
 *   Ref-counting    -> free is immediate and incremental (good for
 *                      real-time / embedded), but every pointer write
 *                      costs an atomic inc/dec, and cycles leak forever
 *                      unless you add a cycle-breaker (CPython's cyclic GC
 *                      is a mark-and-sweep pass added on top of refcounting
 *                      purely to handle cycles).
 *
 * In the taxonomy from the accompanying document:
 *
 *   Primary class  : Memory Management
 *   Touching also  : Execution Contexts (stop-the-world pauses affect all)
 *                    Synchronisation Primitives (atomic refcounts in MT code)
 *                    Scheduling (incremental / concurrent GC interleaves work)
 *
 * Compile:  gcc -Wall -Wextra -o gc_vm_extended gc_vm_extended.c
 * Run:      ./gc_vm_extended
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#define STACK_MAX 256
#define GC_MS_THRESHOLD 8   /* mark-and-sweep fires after N heap objects */


/* 
 * Object types
 *
 * OBJ_INT / OBJ_PAIR  -> managed by mark-and-sweep
 * OBJ_RC_INT / OBJ_RC_PAIR -> managed by reference counting
 */

typedef enum {
    OBJ_INT,
    OBJ_PAIR,
    OBJ_RC_INT,
    OBJ_RC_PAIR
} ObjType;

typedef struct Object {
    ObjType type;

    /* -- Mark-and-sweep fields -- */
    int marked; /* GC mark bit (MS objects only) */
    struct Object *next; /* intrusive list of ALL ms-managed objects */

    /* -- Reference-counting field -- */
    int refcount; /* 0 = unreachable, free immediately (RC objects) */

    /* -- Payload -- */
    union {
        int value; /* OBJ_INT / OBJ_RC_INT */
        struct {
            struct Object *head;
            struct Object *tail;
        }; /* OBJ_PAIR / OBJ_RC_PAIR */
    };
} Object;


/* VM */

typedef struct {
    /* Value stack - shared by both GC strategies */
    Object *stack[STACK_MAX];
    int stack_top;

    /* --- Mark-and-sweep heap --- */
    Object *ms_heap_head;  /* linked list of all MS objects */
    int ms_heap_count;
    int ms_threshold;

    /* --- Stats --- */
    int gc_ms_runs;
    int total_ms_freed;
    int total_ms_allocated;

    int total_rc_allocated;
    int total_rc_freed;
} VM;


/* Fwd decl */
static void gc_ms(VM *vm);
static void rc_release(VM *vm, Object *obj);   /* decrement + maybe free */


/* VM lifecycle */

VM *vm_create(void) {
    VM *vm = malloc(sizeof(VM));
    assert(vm);
    vm->stack_top = 0;
    vm->ms_heap_head = NULL;
    vm->ms_heap_count = 0;
    vm->ms_threshold = GC_MS_THRESHOLD;
    vm->gc_ms_runs = 0;
    vm->total_ms_freed = 0;
    vm->total_ms_allocated = 0;
    vm->total_rc_allocated = 0;
    vm->total_rc_freed = 0;
    return vm;
}

void vm_destroy(VM *vm) {
    /* Release all RC objects still on the stack */
    for (int i = 0; i < vm->stack_top; i++) {
        Object *o = vm->stack[i];
        if (o->type == OBJ_RC_INT || o->type == OBJ_RC_PAIR)
            rc_release(vm, o);
    }
    /* Sweep remaining MS objects */
    Object *obj = vm->ms_heap_head;
    while (obj) {
        Object *next = obj->next;
        free(obj);
        obj = next;
    }
    free(vm);
}


/* Stack helpers */

static void stack_push(VM *vm, Object *obj) {
    assert(vm->stack_top < STACK_MAX && "Stack overflow");
    vm->stack[vm->stack_top++] = obj;
}

static Object *stack_pop(VM *vm) {
    assert(vm->stack_top > 0 && "Stack underflow");
    return vm->stack[--vm->stack_top];
}


/* Strategy A: MARK-AND-SWEEP */

/* Allocate a new MS-managed object */
static Object *ms_alloc(VM *vm, ObjType type) {
    if (vm->ms_heap_count >= vm->ms_threshold) {
        printf("\n  [MS-GC trigger] heap_count=%d >= threshold=%d\n",
               vm->ms_heap_count, vm->ms_threshold);
        gc_ms(vm);
        vm->ms_threshold = vm->ms_heap_count * 2;
        if (vm->ms_threshold < GC_MS_THRESHOLD)
            vm->ms_threshold = GC_MS_THRESHOLD;
    }

    Object *obj = malloc(sizeof(Object));
    assert(obj);
    obj->type = type;
    obj->marked = 0;
    obj->refcount = 0;   /* unused for MS, but keep zeroed */
    obj->next = vm->ms_heap_head;
    vm->ms_heap_head = obj;
    vm->ms_heap_count++;
    vm->total_ms_allocated++;
    return obj;
}

/* Mark one object and recurse into children */
static void ms_mark(Object *obj) {
    if (!obj || obj->marked) return;
    obj->marked = 1;
    if (obj->type == OBJ_PAIR) {
        ms_mark(obj->head);
        ms_mark(obj->tail);
    }
}

/* Mark phase: trace from every stack root */
static void ms_mark_all(VM *vm) {
    printf("  [MS] MARK PHASE -- %d stack roots\n", vm->stack_top);
    for (int i = 0; i < vm->stack_top; i++) {
        Object *o = vm->stack[i];
        /* Only mark MS-managed objects */
        if (o->type == OBJ_INT || o->type == OBJ_PAIR)
            ms_mark(o);
    }
}

/* Sweep phase: free every unmarked MS object */
static void ms_sweep(VM *vm) {
    printf("  [MS] SWEEP PHASE\n");
    int freed = 0;
    Object **cursor = &vm->ms_heap_head;
    while (*cursor) {
        if (!(*cursor)->marked) {
            Object *garbage = *cursor;
            *cursor = garbage->next;
            printf("    freed MS obj@%p  type=%s\n",
                   (void *)garbage,
                   garbage->type == OBJ_INT ? "INT" : "PAIR");
            free(garbage);
            vm->ms_heap_count--;
            freed++;
        } else {
            (*cursor)->marked = 0; /* clear for next cycle */
            cursor = &(*cursor)->next;
        }
    }
    vm->total_ms_freed += freed;
    printf("  [MS] freed=%d  heap_count=%d\n", freed, vm->ms_heap_count);
}

static void gc_ms(VM *vm) {
    int before = vm->ms_heap_count;
    printf("  MS-GC #%d (heap before=%d)\n", ++vm->gc_ms_runs, before);
    ms_mark_all(vm);
    ms_sweep(vm);
    printf("  MS-GC done: %d --> %d objects\n\n", before, vm->ms_heap_count);
}

/* VM instruction: push integer (MS-managed) */
Object *vm_push_int(VM *vm, int value) {
    Object *obj = ms_alloc(vm, OBJ_INT);
    obj->value  = value;
    stack_push(vm, obj);
    printf("  [MS] push_int(%d)  heap=%d\n", value, vm->ms_heap_count);
    return obj;
}

/* VM instruction: push pair (MS-managed) */
Object *vm_push_pair(VM *vm) {
    Object *obj = ms_alloc(vm, OBJ_PAIR);
    obj->tail   = stack_pop(vm);
    obj->head   = stack_pop(vm);
    stack_push(vm, obj);
    printf("  [MS] push_pair()  heap=%d\n", vm->ms_heap_count);
    return obj;
}

/* VM instruction: pop (MS objects just fall off the stack; GC handles free) */
void vm_pop_ms(VM *vm) {
    Object *o = stack_pop(vm);
    (void)o;
    printf("  [MS] pop()  stack_top=%d  (object may become garbage)\n",
           vm->stack_top);
}


/* 
 * Strategy B: REFERENCE COUNTING
 *
 * Every time we store a pointer TO an RC object, we call rc_retain().
 * Every time we discard a pointer, we call rc_release().
 * When refcount hits zero, the object is freed immediately.
 *
 * This mirrors what CPython does with every PyObject, what the Linux
 * kernel does with struct kref, and what C++ shared_ptr does under
 * the hood (with an atomic counter for thread safety).
 */

/* Increment refcount */
static void rc_retain(Object *obj) {
    if (!obj) return;
    obj->refcount++;
    printf("    [RC] retain obj@%p  type=%s  refcount --> %d\n",
           (void *)obj,
           (obj->type == OBJ_RC_INT) ? "RC_INT" : "RC_PAIR",
           obj->refcount);
}

/* Decrement refcount; free if zero (and recursively release children) */
static void rc_release(VM *vm, Object *obj) {
    if (!obj) return;

    obj->refcount--;
    printf("    [RC] release obj@%p  type=%s  refcount --> %d\n",
           (void *)obj,
           (obj->type == OBJ_RC_INT) ? "RC_INT" : "RC_PAIR",
           obj->refcount);

    if (obj->refcount == 0) {
        /* Recursively release children before freeing the parent */
        if (obj->type == OBJ_RC_PAIR) {
            printf("    [RC] releasing children of pair@%p\n", (void *)obj);
            rc_release(vm, obj->head);
            rc_release(vm, obj->tail);
        }
        printf("    [RC] FREE obj@%p  type=%s  <-- refcount=0\n",
               (void *)obj,
               (obj->type == OBJ_RC_INT) ? "RC_INT" : "RC_PAIR");
        free(obj);
        vm->total_rc_freed++;
    }
}

/* Allocate a new RC object (not tracked on the MS heap) */
static Object *rc_alloc(VM *vm, ObjType type) {
    Object *obj = malloc(sizeof(Object));
    assert(obj);
    obj->type = type;
    obj->marked = 0;
    obj->refcount = 0;   /* will be incremented when stored */
    obj->next = NULL; /* NOT on the MS heap list */
    vm->total_rc_allocated++;
    return obj;
}

/* VM instruction: push RC integer */
Object *vm_push_rc_int(VM *vm, int value) {
    Object *obj = rc_alloc(vm, OBJ_RC_INT);
    obj->value  = value;
    rc_retain(obj);         /* stack holds a reference */
    stack_push(vm, obj);
    printf("  [RC] push_rc_int(%d)  refcount=%d\n", value, obj->refcount);
    return obj;
}

/* VM instruction: push RC pair */
Object *vm_push_rc_pair(VM *vm) {
    Object *obj = rc_alloc(vm, OBJ_RC_PAIR);
    obj->tail = stack_pop(vm);   /* borrow raw pointer first */
    obj->head = stack_pop(vm);

    /*
     * The pair now holds references to head and tail.
     * Retain both children; the stack entries being replaced
     * would release their holds, but here we simply transfer
     * ownership from the stack into the pair, so net change = 0
     * for each child's refcount.  We do need to retain for the
     * pair's own pointers though.
     *
     * For clarity in this demo we just retain (pair -> child):
     */
    rc_retain(obj->head);
    rc_retain(obj->tail);

    /* Release the stack's own references to head and tail
     * (they are now owned by the pair, not by the stack directly) */
    rc_release(vm, obj->head);   /* -1 for stack slot */
    rc_release(vm, obj->tail);   /* -1 for stack slot */

    rc_retain(obj);              /* stack holds a reference to the pair */
    stack_push(vm, obj);
    printf("  [RC] push_rc_pair()  refcount=%d\n", obj->refcount);
    return obj;
}

/* VM instruction: pop RC object - releases the stack's reference */
void vm_pop_rc(VM *vm) {
    Object *obj = stack_pop(vm);
    printf("  [RC] pop()  stack_top=%d  --> releasing stack reference\n",
           vm->stack_top);
    rc_release(vm, obj);   /* may free immediately if refcount hits 0 */
}


/*  Demos  */

static void separator(const char *title) {
    printf("\n\n%s\n", title);
    printf("----------------------------------\n");
}

/*
 * Demo 1: MS strategy - classic mark-and-sweep behaviour.
 * Push 4 ints, pop 2 -> GC frees the 2 unreachable ones.
 */
static void demo_ms_basic(VM *vm) {
    separator("Demo 1 [MS]: Push 4, pop 2 -> GC frees 2");

    vm_push_int(vm, 10);
    vm_push_int(vm, 20);
    vm_push_int(vm, 30);
    vm_push_int(vm, 40);

    printf("\n  Popping 20 and 10 (they become garbage):\n");
    vm_pop_ms(vm);   /* 40 */
    vm_pop_ms(vm);   /* 30 */

    printf("\n  Triggering GC manually:\n");
    gc_ms(vm);

    /* Drain stack */
    while (vm->stack_top) vm_pop_ms(vm);
    gc_ms(vm);
}

/*
 * Demo 2: RC strategy - immediate reclamation on pop.
 * Push 2 RC ints, pop them.  Each pop frees immediately.
 * No separate GC phase required.
 */
static void demo_rc_immediate_free(VM *vm) {
    separator("Demo 2 [RC]: Immediate reclamation on pop");

    printf("  Note: with RC, objects are freed as soon as refcount -> 0.\n");
    printf("  There is no 'GC phase' - deallocation is woven into pop().\n\n");

    vm_push_rc_int(vm, 100);
    vm_push_rc_int(vm, 200);

    printf("\n  Popping 200 -> freed immediately:\n");
    vm_pop_rc(vm);

    printf("\n  Popping 100 -> freed immediately:\n");
    vm_pop_rc(vm);

    printf("\n  Heap has no RC objects lingering (all freed inline).\n");
}

/*
 * Demo 3: RC with a pair - refcount cascade.
 * Build RC pair(1, 2), pop it -> releases pair, which cascades
 * to release both children, all freed without a GC pass.
 */
static void demo_rc_cascade(VM *vm) {
    separator("Demo 3 [RC]: Pair pop cascades to children");

    vm_push_rc_int(vm, 1);
    vm_push_rc_int(vm, 2);
    printf("\n  Wrapping in RC pair:\n");
    vm_push_rc_pair(vm);

    printf("\n  Popping the pair -> should cascade-free both children:\n");
    vm_pop_rc(vm);

    printf("\n  Everything freed inline, zero GC cycles needed.\n");
}

/*
 * Demo 4: THE CYCLE PROBLEM - why RC alone is insufficient.
 *
 * We manually construct a cycle in raw C to show the leak:
 *   A -> B -> A  (A's tail points back to A)
 *
 * With reference counting, neither A nor B ever reaches refcount=0
 * because each holds a reference to the other.  This is the reason
 * CPython added a cyclic GC on top of its refcount system, and why
 * Rust's Rc<T> can leak with Rc::clone cycles.
 *
 * A tracing (mark-and-sweep) collector handles cycles for free
 * because it traces from roots, not from refcounts.
 */
static void demo_rc_cycle_leak(VM *vm) {
    separator("Demo 4 [RC]: The cycle problem - why RC leaks cycles");

    printf("  We build a cycle manually: A.tail -> B, B.tail -> A\n");
    printf("  Neither A nor B will ever reach refcount=0 via RC alone.\n\n");

    /* Allocate two RC pairs directly (not via push, to control refcounts) */
    Object *A = rc_alloc(vm, OBJ_RC_PAIR);
    Object *B = rc_alloc(vm, OBJ_RC_PAIR);

    /* Give them dummy integer heads */
    Object *ia = rc_alloc(vm, OBJ_RC_INT); ia->value = 1;
    Object *ib = rc_alloc(vm, OBJ_RC_INT); ib->value = 2;

    rc_retain(ia); A->head = ia;    /* A.head -> ia */
    rc_retain(ib); B->head = ib;    /* B.head -> ib */

    /* Create the cycle */
    rc_retain(B); A->tail = B;      /* A.tail -> B,  B.refcount = 1 */
    rc_retain(A); B->tail = A;      /* B.tail -> A,  A.refcount = 1 */

    /* "Stack" holds A (simulated) */
    rc_retain(A);

    printf("  A@%p refcount=%d  B@%p refcount=%d\n",
           (void *)A, A->refcount, (void *)B, B->refcount);

    printf("\n  Releasing the 'stack' reference to A:\n");
    rc_release(vm, A);   /* A.refcount: 2->1  (B still holds one) */

    printf("\n  A.refcount=%d  B.refcount=%d\n", A->refcount, B->refcount);
    printf("  Neither is zero -> MEMORY LEAK under pure RC.\n");
    printf("  A tracing GC would find both unreachable from roots and free them.\n\n");

    /*
     * In a real system we would now run a cycle-detecting pass
     * (like CPython's gc module) or use weak references to break
     * the cycle manually.  For this demo we free manually to avoid
     * actually leaking memory:
     */
    printf("  [demo cleanup] manually breaking cycle to avoid actual leak:\n");
    rc_release(vm, A->head);  /* release ia */
    rc_release(vm, B->head);  /* release ib */
    /* Break the cycle before releasing - null out one pointer */
    Object *tmp_B_tail = B->tail;
    B->tail = NULL;
    rc_release(vm, A->tail);  /* release B: B.refcount -> 0 -> freed */
    rc_release(vm, tmp_B_tail); /* release A: A.refcount -> 0 -> freed */
    /* Note: in practice this is why you need weak pointers or a cycle collector */
}

/*
 * Demo 5: Side-by-side comparison.
 * Allocate identical graphs under both strategies, then discard.
 * Observe MS waits for GC; RC frees inline.
 */
static void demo_side_by_side(VM *vm) {
    separator("Demo 5: Side-by-side - MS vs RC on the same workload");

    printf("  WORKLOAD: push pair(10,20), then discard it.\n\n");

    printf("  -- With MS --\n");
    vm_push_int(vm, 10);
    vm_push_int(vm, 20);
    vm_push_pair(vm);
    vm_pop_ms(vm);   /* discarded - becomes garbage */
    printf("  (MS objects still on heap; GC not yet triggered)\n");
    printf("  MS heap count = %d\n", vm->ms_heap_count);
    gc_ms(vm);
    printf("  MS heap count after GC = %d\n\n", vm->ms_heap_count);

    printf("  -- With RC --\n");
    vm_push_rc_int(vm, 10);
    vm_push_rc_int(vm, 20);
    vm_push_rc_pair(vm);
    printf("  (RC pair on stack, refcounts > 0)\n");
    vm_pop_rc(vm);   /* freed immediately, cascade to children */
    printf("  (RC objects freed inline, no GC pass needed)\n");
}



int main(void) {
    printf("\n");
    printf(" Garbage Collection at the Low Level: MS vs RC\n");
    printf("\n");
    printf("\n");
    printf("This demo illustrates two GC strategies in the same tiny VM:\n");
    printf("\n");
    printf("  Mark-and-Sweep (MS): traces from roots, frees in bulk.\n");
    printf("    Analogues: Lua, MicroPython, GHC runtime.\n");
    printf("\n");
    printf("  Reference Counting (RC): frees immediately on last release.\n");
    printf("    Analogues: CPython (PyObject.ob_refcnt), Linux kref,\n");
    printf("               Windows COM IUnknown, C++ shared_ptr.\n");
    printf("\n");
    printf("Both live under 'Memory Management' in the mechanism taxonomy,\n");
    printf("but touch Execution Contexts (GC pauses), Synchronisation\n");
    printf("(atomic refcounts in MT code), and Scheduling (incremental GC).\n");

    VM *vm = vm_create();

    demo_ms_basic(vm);
    demo_rc_immediate_free(vm);
    demo_rc_cascade(vm);
    demo_rc_cycle_leak(vm);
    demo_side_by_side(vm);

    separator("Statistics");
    printf("  MS objects allocated : %d\n", vm->total_ms_allocated);
    printf("  MS objects freed     : %d\n", vm->total_ms_freed);
    printf("  MS GC cycles run     : %d\n", vm->gc_ms_runs);
    printf("  RC objects allocated : %d\n", vm->total_rc_allocated);
    printf("  RC objects freed     : %d\n", vm->total_rc_freed);
    printf("  MS objects on heap   : %d\n", vm->ms_heap_count);

    vm_destroy(vm);
    printf("\nDone.\n\n");

/*
    Some Conclusions:

       1. GC is not a high-level language feature. Both strategies
          appear in production C/C++ (kernels, VMs, runtimes).

       2. MS: simple allocator, bulk free, handles cycles.
          Cost: latency spike when GC fires (stop-the-world).

       3. RC: free is immediate and incremental (predictable latency).
          Cost: every pointer store/release costs an inc/dec.
          Fatal flaw: cycles leak. Requires weak refs or a cycle pass.

       4. CPython uses BOTH: RC for everything, plus a mark-and-sweep
          cycle collector (the 'gc' module) to handle cycles.
          This is the canonical hybrid approach.
*/

}
