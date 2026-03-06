/*
 * immutability.c
 * Functional Patterns -- 3. Immutability
 *
 * C has no language-level immutable values, but it has two partial tools:
 *   - const: a promise about one access path, not about the value itself.
 *   - copying: pass/return by value so no shared pointer exists.
 *
 * Sections:
 *   1. const correctness -- what it protects and what it does not.
 *   2. Alias hazard -- const does not prevent writes through other pointers.
 *   3. Immutable by copy -- struct pass/return by value.
 *   4. Functional update -- produce a new struct, leave the original alone.
 *   5. read-only segment -- static const at file scope.
 *   6. Copy-on-write sketch -- the minimal pattern for structural sharing.
 *   7. Concurrency note -- why read-only data needs no synchronisation.
 *
 * Build:  cc -Wall -o immutability immutability.c
 * Run:    ./immutability
 */

#include <stdio.h>
#include <string.h>

/* 
 * 1. const correctness
 *
 * const int *p means "I will not write through p".
 * It says nothing about other aliases.
 */
static void print_array(const int *arr, int n) {
    /* arr[0] = 99;  -- compile error: read-only through this pointer */
    printf("  [");
    for (int i = 0; i < n; i++)
        printf("%s%d", i ? ", " : "", arr[i]);
    printf("]\n");
}

/* 
 * 2. The alias hazard: const is a view, not a lock
 */
static void alias_demo(void) {
    int data[3] = { 1, 2, 3 };
    int       *mutable_alias   = data;
    const int *immutable_view  = data;

    printf("  before:  ");  print_array(immutable_view, 3);

    mutable_alias[0] = 99;   /* legal: no const on mutable_alias */

    /* immutable_view[0] = 99;  -- compile error, but the value changed: */
    printf("  after mutable_alias[0]=99 (through other pointer):\n");
    printf("  immutable_view[0] = %d  (changed despite const view)\n",
           immutable_view[0]);
}

/* 
 * 3. Immutable by copy: point_t
 *
 * Passing and returning structs by value copies them.
 * The caller's original is untouched; no heap allocation needed.
 */
typedef struct { int x; int y; } point_t;

static point_t translate(point_t p, int dx, int dy) {
    /* p is a local copy -- modifying it does not affect the caller */
    return (point_t){ p.x + dx, p.y + dy };
}

static point_t scale(point_t p, int factor) {
    return (point_t){ p.x * factor, p.y * factor };
}

static void print_point(const char *label, point_t p) {
    printf("  %s (%d, %d)\n", label, p.x, p.y);
}

/* 
 * 4. Functional update of a record
 *
 * Produce a new struct with one field changed; leave the original alone.
 */
typedef struct {
    char name[32];
    int  age;
    char city[32];
} person_t;

static person_t set_age(person_t p, int new_age) {
    p.age = new_age;   /* p is already a copy -- safe to modify */
    return p;
}

static void print_person(const char *label, const person_t *p) {
    printf("  %s: name=%s age=%d city=%s\n", label, p->name, p->age, p->city);
}

/* 
 * 5. Read-only segment: static const at file scope
 *
 * The linker may place this in a read-only segment.
 * A write attempt causes a segfault rather than silent corruption.
 * Safe to read from multiple threads without synchronisation.
 */
static const int lookup_table[8] = { 0, 1, 4, 9, 16, 25, 36, 49 };

/* 
 * 6. Copy-on-write sketch
 *
 * A simplified illustration of the pattern used by persistent data
 * structures: share until you need to mutate, then copy just what changes.
 *
 * Here: a "persistent" integer array of fixed size 4.
 * We represent two versions that share elements they have in common.
 * (A real implementation would use reference counting and heap nodes.)
 * */
#define ARR_SIZE 4

typedef struct {
    int data[ARR_SIZE];
} arr_t;

/* Return a new arr_t with index i set to value; original untouched. */
static arr_t arr_set(arr_t a, int i, int value) {
    /* Full copy -- structural sharing would avoid this for large arrays */
    a.data[i] = value;
    return a;
}

static void print_arr(const char *label, const arr_t *a) {
    printf("  %s: [%d, %d, %d, %d]\n", label,
           a->data[0], a->data[1], a->data[2], a->data[3]);
}

/* 
 * 7. Thread-safety note (no actual threads -- just the pattern)
 *
 * A value that is never written after construction can be read by any
 * number of concurrent readers with no synchronisation overhead.
 * The C standard guarantees this for static const objects.
 */


 int main(void) {
    /* --- 1 & 2. const and aliases */
    printf("-- 1. const -- what it protects --\n");
    {
        int arr[5] = { 10, 20, 30, 40, 50 };
        printf("  print_array with const int*:\n  ");
        print_array(arr, 5);
    }

    printf("\n-- 2. Alias hazard --\n");
    alias_demo();

    /* --- 3. Immutable by copy */
    printf("\n-- 3. Immutable by copy (point_t) --\n");
    {
        point_t origin = { 0, 0 };
        point_t moved  = translate(origin, 3, 4);
        point_t scaled = scale(moved, 2);

        print_point("origin (unchanged):", origin);
        print_point("moved  (translate):", moved);
        print_point("scaled (scale*2):  ", scaled);
    }

    /* --- 4. Functional update */
    printf("\n-- 4. Functional update (person_t) --\n");
    {
        person_t alice;
        strncpy(alice.name, "Alice", sizeof(alice.name) - 1);
        alice.age = 30;
        strncpy(alice.city, "Berlin", sizeof(alice.city) - 1);

        person_t older = set_age(alice, 31);

        print_person("original", &alice);
        print_person("updated ", &older);
        printf("  original age unchanged: %d\n", alice.age);
    }

    /* --- 5. Read-only segment */
    printf("\n-- 5. Static const lookup table --\n");
    {
        printf("  squares: ");
        for (int i = 0; i < 8; i++)
            printf("%d ", lookup_table[i]);
        printf("\n");
        printf("  (attempting to write would segfault -- not attempted)\n");
    }

    /* --- 6. Copy-on-write sketch */
    printf("\n-- 6. Copy-on-write (persistent array sketch) --\n");
    {
        arr_t v1 = { { 1, 2, 3, 4 } };
        arr_t v2 = arr_set(v1, 2, 99);   /* new version, index 2 changed */
        arr_t v3 = arr_set(v1, 0,  0);   /* another version from v1 */

        print_arr("v1 (original)", &v1);
        print_arr("v2 (v1 with [2]=99)", &v2);
        print_arr("v3 (v1 with [0]=0)",  &v3);
        printf("  v1 unchanged: %s\n",
               v1.data[2] == 3 && v1.data[0] == 1 ? "yes" : "no");
    }

    /* --- Key observations */
    printf("\n-- Key observations --\n");
    printf("  const in C restricts one access path, not the value.\n");
    printf("  True immutability requires: no shared mutable pointer.\n");
    printf("  Struct-by-value copy is the simplest safe pattern.\n");
    printf("  Static const data is safe for concurrent reads; no lock needed.\n");

    return 0;
}
