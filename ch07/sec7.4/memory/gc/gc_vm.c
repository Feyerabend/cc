/*
 * gc_vm.c - Mark-and-Sweep Garbage Collection in a tiny Stack-Based VM
 *
 * This file is a self-contained illustration of how garbage collection
 * works, built around the simplest possible virtual machine.
 *
 * THE VM
 * ------
 * Our VM has:
 *   - A value stack  (where the "program" pushes/pops values)
 *   - A heap         (a linked list of all allocated objects)
 *   - A GC           (mark-and-sweep, triggered when heap gets full)
 *
 * OBJECT TYPES
 * ------------
 *   OBJ_INT   - wraps a plain integer
 *   OBJ_PAIR  - holds two pointers to other objects (head / tail)
 *               This gives us a reference graph for the GC to trace.
 *
 * GARBAGE COLLECTION - MARK AND SWEEP
 * ------------------------------------
 * Step 1 - MARK
 *   Starting from every object reachable from the VM stack ("roots"),
 *   recursively set the `marked` flag on every reachable object.
 *
 * Step 2 - SWEEP
 *   Walk the entire heap list. Any object that is NOT marked is
 *   unreachable - free it. Reset `marked` on surviving objects.
 *
 * DEMO PROGRAM
 * ------------
 * We run a short sequence of VM "instructions" by calling helper
 * functions, watching the heap grow and the GC fire automatically.
 *
 * Compile:  gcc -Wall -Wextra -o gc_vm gc_vm.c
 * Run:      ./gc_vm
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#define STACK_MAX 256 /* maximum VM stack depth */
#define GC_INITIAL_THRESH 8 /* trigger first GC after N objects  */


/* Object representation */

typedef enum {
    OBJ_INT,
    OBJ_PAIR
} ObjType;

typedef struct Object {
    ObjType type;
    int marked; /* GC mark bit */
    struct Object *next; /* intrusive linked list of ALL objects */

    union {
        /* OBJ_INT */
        int value;

        /* OBJ_PAIR */
        struct {
            struct Object *head;
            struct Object *tail;
        };
    };
} Object;


/* VM */

typedef struct {
    Object *stack[STACK_MAX]; /* value stack */
    int stack_top;            /* index of next free slot */

    Object *heap_head;        /* head of the all-objects linked list */
    int heap_count;           /* number of live objects on the heap */
    int gc_threshold;         /* run GC when heap_count reaches this */
    int gc_runs;              /* total GC cycles executed */
    int total_freed;          /* total objects freed across all GCs */
    int total_allocated;      /* total objects ever allocated */
} VM;


/* Fwd decl */

static void gc(VM *vm);
static Object *alloc_object(VM *vm, ObjType type);


/*  VM lifecycle  */

VM *vm_create(void) {
    VM *vm = malloc(sizeof(VM));
    assert(vm != NULL);
    vm->stack_top = 0;
    vm->heap_head = NULL;
    vm->heap_count = 0;
    vm->gc_threshold = GC_INITIAL_THRESH;
    vm->gc_runs = 0;
    vm->total_freed = 0;
    vm->total_allocated = 0;
    return vm;
}

void vm_destroy(VM *vm) {
    /* Free every remaining object */
    Object *obj = vm->heap_head;
    while (obj) {
        Object *next = obj->next;
        free(obj);
        obj = next;
    }
    free(vm);
}


/*  Stack helpers  */

static void stack_push(VM *vm, Object *obj) {
    assert(vm->stack_top < STACK_MAX && "Stack overflow");
    vm->stack[vm->stack_top++] = obj;
}

static Object *stack_pop(VM *vm) {
    assert(vm->stack_top > 0 && "Stack underflow");
    return vm->stack[--vm->stack_top];
}

/* Peek without popping */
static Object *stack_peek(VM *vm, int depth) {
    assert(vm->stack_top - 1 - depth >= 0 && "Peek out of range");
    return vm->stack[vm->stack_top - 1 - depth];
}


/*  Object allocation */

static Object *alloc_object(VM *vm, ObjType type) {
    /* Auto-trigger GC before we grow past the threshold */
    if (vm->heap_count >= vm->gc_threshold) {
        printf("\n  [GC trigger] heap_count=%d >= threshold=%d\n", vm->heap_count, vm->gc_threshold);
        gc(vm);
        /* After GC, grow the threshold to avoid thrashing */
        vm->gc_threshold = vm->heap_count * 2;
        if (vm->gc_threshold < GC_INITIAL_THRESH)
            vm->gc_threshold = GC_INITIAL_THRESH;
    }

    Object *obj = malloc(sizeof(Object));
    assert(obj != NULL);

    obj->type = type;
    obj->marked = 0;

    /* Prepend to the heap linked list */
    obj->next = vm->heap_head;
    vm->heap_head = obj;
    vm->heap_count++;
    vm->total_allocated++;

    return obj;
}


/*  VM PUSH/POP */

/* PUSH_INT: allocate an OBJ_INT, push it onto the stack */
Object *vm_push_int(VM *vm, int value) {
    Object *obj = alloc_object(vm, OBJ_INT);
    obj->value  = value;
    stack_push(vm, obj);
    printf("  push_int(%d)  --> heap_count=%d\n", value, vm->heap_count);
    return obj;
}

/* PUSH_PAIR: pop top two stack values, wrap them in an OBJ_PAIR, push it */
Object *vm_push_pair(VM *vm) {
    Object *obj  = alloc_object(vm, OBJ_PAIR);
    obj->tail    = stack_pop(vm);   /* second-from-top becomes tail  */
    obj->head    = stack_pop(vm);   /* top becomes head */
    stack_push(vm, obj);
    printf("  push_pair()   --> heap_count=%d\n", vm->heap_count);
    return obj;
}

/* POP: discard the top stack value (it MAY become unreachable --> garbage) */
void vm_pop(VM *vm) {
    Object *obj = stack_pop(vm);
    (void)obj; /* dangling/orphaned object .. */
    printf("  pop()         --> stack_top=%d\n", vm->stack_top);
}


/*  GC: Mark Phase */

static void mark_object(Object *obj) {
    if (obj == NULL) return;
    if (obj->marked) return;   /* already visited - avoid cycles */

    obj->marked = 1;
    printf("    mark obj@%p  type=%s", (void *)obj, obj->type == OBJ_INT ? "INT " : "PAIR");

    if (obj->type == OBJ_INT) {
        printf("  value=%d\n", obj->value);
    } else {
        printf("  head=%p tail=%p\n", (void *)obj->head, (void *)obj->tail);
        /* Recursively mark children */
        mark_object(obj->head);
        mark_object(obj->tail);
    }
}

static void mark_all(VM *vm) {
    printf("  MARK PHASE ..\n");
    for (int i = 0; i < vm->stack_top; i++) {
        printf("  root[%d]:\n", i);
        mark_object(vm->stack[i]);
    }
}


/*  GC: Sweep Phase */

static void sweep(VM *vm) {
    printf("  SWEEP PHASE ..\n");
    int freed = 0;

    Object **obj = &vm->heap_head;  /* pointer-to-pointer for clean removal */
    while (*obj) {
        if (!(*obj)->marked) {
            /* Unreachable - unlink and free */
            Object *garbage = *obj;
            *obj = garbage->next;   /* skip over it in the list */
            printf("    sweep  obj@%p  type=%s  <-- FREED\n", (void *)garbage, garbage->type == OBJ_INT ? "INT " : "PAIR");
            free(garbage);
            vm->heap_count--;
            freed++;
        } else {
            /* Reachable - clear the mark for the next GC cycle */
            (*obj)->marked = 0;
            obj = &(*obj)->next;
        }
    }

    vm->total_freed += freed;
    printf("  SWEEP done: freed %d object(s), heap_count=%d\n", freed, vm->heap_count);
}


/* GC cycle */

static void gc(VM *vm) {
    int before = vm->heap_count;
    printf("  GC #%d  (heap before=%d)\n", ++vm->gc_runs, before);
    mark_all(vm);
    sweep(vm);
    printf("  GC done: %d --> %d objects\n\n", before, vm->heap_count);
}


/*  Pretty-print the current heap */

static void print_heap(VM *vm) {
    printf("  Heap (%d objects): ", vm->heap_count);
    Object *obj = vm->heap_head;
    while (obj) {
        if (obj->type == OBJ_INT)
            printf("[INT %d]", obj->value);
        else
            printf("[PAIR head=%p tail=%p]", (void *)obj->head, (void *)obj->tail);
        if (obj->next) printf(" --> ");
        obj = obj->next;
    }
    printf("\n");
}

static void print_stack(VM *vm) {
    printf("  Stack (%d values): [", vm->stack_top);
    for (int i = 0; i < vm->stack_top; i++) {
        Object *o = vm->stack[i];
        if (o->type == OBJ_INT)
            printf(" INT(%d)", o->value);
        else
            printf(" PAIR");
        if (i < vm->stack_top - 1) printf(",");
    }
    printf(" ]\n");
}


/*  Demos */

static void separator(const char *title) {
    printf("\n\n%s\n", title);
    printf("---------------------------------------------------------\n");
}

/*
 * Scenario 1 - Objects left on the stack stay alive.
 * We push 4 integers, then manually trigger GC.
 * All 4 are reachable --> nothing freed.
 */
static void demo_all_reachable(VM *vm) {
    separator("Scenario 1: All objects reachable (stack roots)");

    vm_push_int(vm, 1);
    vm_push_int(vm, 2);
    vm_push_int(vm, 3);
    vm_push_int(vm, 4);

    print_stack(vm);
    print_heap(vm);

    printf("\n  Manually triggering GC..\n");
    gc(vm);

    print_heap(vm);

    /* Clean up for next demo */
    while (vm->stack_top) vm_pop(vm);
    gc(vm);
}

/*
 * Scenario 2 - Objects that fall off the stack become garbage.
 * Push 2 ints, pop them (stack drops to 0), then GC.
 * Both are now unreachable --> both freed.
 */
static void demo_unreachable(VM *vm) {
    separator("Scenario 2: Popped objects become garbage");

    vm_push_int(vm, 10);
    vm_push_int(vm, 20);
    print_stack(vm);

    printf("\n  Popping both values off the stack..\n");
    vm_pop(vm);
    vm_pop(vm);
    print_stack(vm);

    printf("\n  Manually triggering GC..\n");
    gc(vm);
    print_heap(vm);
}

/*
 * Scenario 3 - Nested pairs keep children alive.
 * Build: pair( pair(1,2), pair(3,4) )
 * Then pop the outer pair --> all 5 objects become garbage.
 */
static void demo_nested_pairs(VM *vm) {
    separator("Scenario 3: Nested pairs - children reachable via parent");

    vm_push_int(vm, 1);
    vm_push_int(vm, 2);
    Object *inner1 = vm_push_pair(vm);  /* pair(1,2)      */

    vm_push_int(vm, 3);
    vm_push_int(vm, 4);
    Object *inner2 = vm_push_pair(vm);  /* pair(3,4)      */

    vm_push_pair(vm);                   /* pair(inner1, inner2) */

    printf("\n  Stack has the outer pair rooted:\n");
    print_stack(vm);
    print_heap(vm);

    printf("\n  GC now - outer pair on stack keeps everything alive:\n");
    gc(vm);
    print_heap(vm);

    printf("\n  Popping the outer pair (now all 5 objects are garbage):\n");
    vm_pop(vm);
    gc(vm);
    print_heap(vm);

    (void)inner1; (void)inner2;  /* suppress unused-variable warning */
}

/*
 * Scenario 4 - Auto-GC triggered by allocation pressure.
 * We keep allocating until the GC fires automatically.
 */
static void demo_auto_gc(VM *vm) {
    separator("Scenario 4: Automatic GC triggered by allocation pressure");

    printf("  GC threshold is currently %d objects.\n", vm->gc_threshold);
    printf("  We will push %d integers and pop the first half,\n", vm->gc_threshold + 2);
    printf("  creating garbage that the auto-GC should reclaim.\n\n");

    int n = vm->gc_threshold + 2;

    /* Push half, immediately pop them (they become garbage) */
    for (int i = 0; i < n / 2; i++) {
        vm_push_int(vm, i * 100);
        vm_pop(vm);
    }

    /* Push the other half, keep them on the stack */
    for (int i = 0; i < n / 2; i++) {
        vm_push_int(vm, i);
    }

    printf("\nAfter all allocations:\n");
    print_stack(vm);
    print_heap(vm);

    while (vm->stack_top) vm_pop(vm);
    gc(vm);
}



int main(void) {
    printf("Mark-and-Sweep GC\n");
    printf("\nObjects live on a singly-linked heap list.\n");
    printf("GC roots = everything currently on the VM stack.\n");
    printf("GC = mark reachable objects, then sweep the rest.\n\n");

    VM *vm = vm_create();

    demo_all_reachable(vm);
    demo_unreachable(vm);
    demo_nested_pairs(vm);
    demo_auto_gc(vm);

    printf("Statistics\n");
    printf("  Total objects allocated : %d\n", vm->total_allocated);
    printf("  Total objects freed     : %d\n", vm->total_freed);
    printf("  Objects still on heap   : %d\n", vm->heap_count);
    printf("  GC cycles executed      : %d\n", vm->gc_runs);

    vm_destroy(vm);
    printf("\nDone.\n\n");
    return 0;
}
