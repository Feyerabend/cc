/*
 * main.c  -  Scenario runner.
 *
 * Each scenario exercises a specific checker capability.
 * The checker (bc_*) and renderer (diag_*) are entirely separate;
 * this file only wires them together.
 *
 * Scenarios
 *
 *  1.  Happy path: ownership, shared borrows, mutable borrow, assign
 *  2.  Double free
 *  3.  Use after move
 *  4.  Dangling borrow: borrow outlives owner via nested scope
 *  5.  Shared + mutable borrow conflict (with provenance)
 *  6.  Move while borrowed
 *  7.  Drop while borrowed --> dangling + use of dangling
 *  8.  Copy types: no move invalidation
 *  9.  Re-borrow chain
 * 10.  Assign to immutable / borrowed variable
 * 11.  Resource: acquire + explicit release (file handle)
 * 12.  Resource: leak detection (no release before scope exit)
 * 13.  Resource: double-release
 * 14.  Resource: borrow a resource handle, then try to release it
 * 15.  Defer: register cleanup, verify it is satisfied
 * 16.  Defer: unsatisfied defer (missing release)
 * 17.  Mixed: heap allocation leaked on error path
 * 18.  assert_consumed: enforce linear types
 */

 /* gcc -Wall -Wextra -std=c11 -o bc checker.c diagram.c main.c */

#include <stdio.h>
#include <stdlib.h>
#include "checker.h"
#include "diagram.h"

static void title(int n, const char *desc) {
    printf("\n\n");
    printf("\n");
    printf("  Scenario %2d : %s\n", n, desc);
    printf("\n");
}

/* -- Scenario 1: Happy path  */
static void s1(const DiagOpts *o) {
    title(1, "Happy path — ownership, borrows, assign");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_declare    (bc, "x",  1);
      bc_borrow     (bc, "r1", "x");
      bc_borrow     (bc, "r2", "x");
      bc_use        (bc, "r1");
      bc_use        (bc, "r2");
      bc_release    (bc, "r1");
      bc_release    (bc, "r2");
      bc_borrow_mut (bc, "m",  "x");
      bc_use        (bc, "m");
      bc_release    (bc, "m");
      bc_assign     (bc, "x");
      bc_use        (bc, "x");
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 2: Double free  */
static void s2(const DiagOpts *o) {
    title(2, "Double free");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_declare(bc, "p", 0);
      bc_drop   (bc, "p");
      bc_drop   (bc, "p");   /* ERROR: double free */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 3: Use after move  */
static void s3(const DiagOpts *o) {
    title(3, "Use after move");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_declare(bc, "a", 0);
      bc_move   (bc, "b", "a");
      bc_use    (bc, "a");      /* ERROR: moved */
      bc_use    (bc, "b");      /* OK */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 4: Dangling borrow  */
static void s4(const DiagOpts *o) {
    title(4, "Dangling borrow — borrow outlives owner across scopes");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_scope_enter(bc);
        bc_declare(bc, "tmp",    0);
        bc_borrow (bc, "dangle", "tmp");
        bc_use    (bc, "dangle");
      bc_scope_exit(bc);   /* tmp + dangle released */
      bc_use(bc, "dangle"); /* ERROR: released */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 5: Borrow conflict with provenance  */
static void s5(const DiagOpts *o) {
    title(5, "Shared + mutable borrow conflict (provenance shown)");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_declare   (bc, "v",  1);
      bc_borrow    (bc, "r1", "v");   /* shared borrow created here */
      bc_borrow    (bc, "r2", "v");   /* second shared borrow */
      bc_borrow_mut(bc, "mr", "v");   /* ERROR: shared borrows exist */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 6: Move while borrowed  */
static void s6(const DiagOpts *o) {
    title(6, "Move while borrowed");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_declare(bc, "src",  0);
      bc_borrow (bc, "ref1", "src");
      bc_move   (bc, "dst",  "src"); /* ERROR: borrowed */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 7: Drop while borrowed --> dangling use  */
static void s7(const DiagOpts *o) {
    title(7, "Drop while borrowed — dangling pointer + use");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_declare(bc, "data", 0);
      bc_borrow (bc, "ptr",  "data");
      bc_drop   (bc, "data");   /* ERROR: ptr still alive */
      bc_use    (bc, "ptr");    /* ERROR: dangling */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 8: Copy types  */
static void s8(const DiagOpts *o) {
    title(8, "Copy types — no move invalidation");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_declare_copy(bc, "i");
      bc_copy        (bc, "j", "i");
      bc_use         (bc, "i");         /* still alive */
      bc_move        (bc, "k", "i");    /* NOTE: Copy => copy */
      bc_use         (bc, "i");         /* still alive */
      bc_use         (bc, "k");
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 9: Re-borrow chain  */
static void s9(const DiagOpts *o) {
    title(9, "Re-borrow chain");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_declare    (bc, "val", 1);
      bc_borrow_mut (bc, "m1", "val");
      bc_reborrow   (bc, "m2", "m1");
      bc_use        (bc, "m2");
      bc_release    (bc, "m2");
      bc_use        (bc, "m1");   /* OK: m2 released */
      bc_release    (bc, "m1");
      bc_use        (bc, "val");
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 10: Immutable / borrowed assign  */
static void s10(const DiagOpts *o) {
    title(10, "Assign to immutable / borrowed variable");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_declare (bc, "imm",   0);
      bc_declare (bc, "mut_v", 1);
      bc_assign  (bc, "imm");           /* ERROR: immutable */
      bc_borrow  (bc, "r", "mut_v");
      bc_assign  (bc, "mut_v");         /* ERROR: borrowed */
      bc_release (bc, "r");
      bc_assign  (bc, "mut_v");         /* OK */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 11: Resource acquire + release  */
static void s11(const DiagOpts *o) {
    title(11, "Resource: FileHandle acquire and explicit release");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_resource_acquire(bc, "fd",  RK_FILE);
      bc_use             (bc, "fd");
      bc_borrow          (bc, "r",   "fd");    /* borrow the handle */
      bc_use             (bc, "r");
      bc_release         (bc, "r");
      bc_resource_release(bc, "fd");           /* close file */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 12: Resource leak  */
static void s12(const DiagOpts *o) {
    title(12, "Resource: FileHandle leaked (no release before scope exit)");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_resource_acquire(bc, "fd",  RK_FILE);
      bc_resource_acquire(bc, "buf", RK_HEAP);
      bc_use             (bc, "fd");
      bc_use             (bc, "buf");
      bc_resource_release(bc, "buf"); /* buf released OK */
      /* fd never released — ERROR at scope exit */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 13: Resource double-release  */
static void s13(const DiagOpts *o) {
    title(13, "Resource: double-release (close called twice)");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_resource_acquire(bc, "sock", RK_SOCKET);
      bc_resource_release(bc, "sock");
      bc_resource_release(bc, "sock"); /* ERROR */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 14: Borrow a resource handle, drop owner  */
static void s14(const DiagOpts *o) {
    title(14, "Resource: release handle while borrowed");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_resource_acquire(bc, "lk",  RK_LOCK);
      bc_borrow          (bc, "guard", "lk");   /* guard holds a ref */
      bc_resource_release(bc, "lk");            /* ERROR: guard still alive */
      bc_use             (bc, "guard");         /* ERROR: dangling */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 15: Defer satisfied  */
static void s15(const DiagOpts *o) {
    title(15, "Defer: cleanup registered and satisfied");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_resource_acquire(bc, "conn", RK_SOCKET);
      bc_defer           (bc, "conn");          /* MUST be released */
      bc_use             (bc, "conn");
      bc_resource_release(bc, "conn");          /* defer satisfied */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 16: Defer NOT satisfied  */
static void s16(const DiagOpts *o) {
    title(16, "Defer: cleanup registered but NOT satisfied (missing close)");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);
    bc_scope_enter(bc);
      bc_resource_acquire(bc, "conn", RK_SOCKET);
      bc_defer           (bc, "conn");
      bc_use             (bc, "conn");
      /* no release — ERROR at scope exit */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 17: Heap leak on error path  */
static void s17(const DiagOpts *o) {
    title(17, "Mixed: heap allocation + file handle, file open fails");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);

    /*
     * Simulates:
     *   buf  = malloc(N);          // heap alloc
     *   fd   = open("f", ...);     // file open (succeeds)
     *   buf2 = malloc(M);          // second alloc
     *   // ... use all three ...
     *   free(buf2);                // OK
     *   close(fd);                 // OK
     *   // forgot to free(buf)     // LEAK
     */
    bc_scope_enter(bc);
      bc_resource_acquire(bc, "buf",  RK_HEAP);
      bc_defer           (bc, "buf");           /* safety net */
      bc_resource_acquire(bc, "fd",   RK_FILE);
      bc_resource_acquire(bc, "buf2", RK_HEAP);
      bc_use             (bc, "buf");
      bc_use             (bc, "fd");
      bc_use             (bc, "buf2");
      bc_resource_release(bc, "buf2");
      bc_resource_release(bc, "fd");
      /* buf never freed: defer unsatisfied => ERROR */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);
}

/* -- Scenario 18: assert_consumed linear types  */
static void s18(const DiagOpts *o) {
    title(18, "assert_consumed — linear type enforcement");
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);

    /*
     * Simulates a language where a "ticket" token must be consumed
     * (submitted, not ignored) before leaving a transaction block.
     * The compiler calls bc_assert_consumed() at the end of the block.
     */
    bc_scope_enter(bc);
      bc_declare        (bc, "ticket", 0);
      bc_use            (bc, "ticket");
      /* Correct use: move into submit() */
      bc_move           (bc, "submitted", "ticket");
      bc_drop           (bc, "submitted");      /* consumed */
      bc_assert_consumed(bc, "ticket");         /* OK: was moved */
    bc_scope_exit(bc);
    diag_render_all(bc, o); diag_render_summary(bc, o); free(bc);

    /* Now the failing case: ticket never consumed */
    printf("\n  [failing case: ticket never consumed]\n");
    BC *bc2 = calloc(1, sizeof *bc2); bc_init(bc2);
    bc_scope_enter(bc2);
      bc_declare        (bc2, "ticket", 0);
      bc_use            (bc2, "ticket");
      /* forgot to submit — just leaves the scope */
      bc_assert_consumed(bc2, "ticket");        /* ERROR: still alive */
    bc_scope_exit(bc2);
    diag_render_all(bc2, o); diag_render_summary(bc2, o); free(bc2);
}

/* -- Entry point  */
int main(void) {
    DiagOpts opts = diag_default_opts();
    opts.colour           = 1;
    opts.show_scope_depth = 1;
    opts.show_generations = 1;
    opts.show_provenance  = 1;
    opts.show_resources   = 1;

    s1 (&opts);
    s2 (&opts);
    s3 (&opts);
    s4 (&opts);
    s5 (&opts);
    s6 (&opts);
    s7 (&opts);
    s8 (&opts);
    s9 (&opts);
    s10(&opts);
    s11(&opts);
    s12(&opts);
    s13(&opts);
    s14(&opts);
    s15(&opts);
    s16(&opts);
    s17(&opts);
    s18(&opts);

    return 0;
}
