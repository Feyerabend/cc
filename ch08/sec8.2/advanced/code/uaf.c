#include <stdlib.h>
#include <string.h>
#include <stdio.h>

typedef struct { char name[32]; void (*greet)(void); } User;

static void hello(void) { puts("hello"); }

/*
 * Vulnerable: the pointer is freed but not nulled. A later allocation of the
 * same size may reuse the same heap slot. If an attacker controls what goes
 * into that allocation they can overwrite the function pointer and redirect
 * execution when greet() is called.
 */
void uaf_bad(void) {
    User *u = malloc(sizeof(User));
    strcpy(u->name, "alice");
    u->greet = hello;

    free(u);               /* slot returned to allocator */
    /* ... attacker-controlled allocation may land here ... */
    u->greet();            /* calls whatever is now at that address */
}

/*
 * Safe: null the pointer immediately after free. Any subsequent dereference
 * will fault with a clean SIGSEGV rather than silently executing attacker
 * data. In C++ prefer smart pointers (unique_ptr / shared_ptr) which null
 * themselves on destruction.
 */
void uaf_safe(void) {
    User *u = malloc(sizeof(User));
    strcpy(u->name, "alice");
    u->greet = hello;

    u->greet();
    free(u);
    u = NULL;              /* any later dereference is a clean crash */
}
