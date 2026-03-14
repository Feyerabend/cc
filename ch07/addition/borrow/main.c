/*
 * main.c  -  Scenario runner for the full-featured borrow checker.
 *
 * Each scenario exercises a specific checker capability.
 * The checker (bc_*) and renderer (diag_*) are entirely separate;
 * this file only wires them together.
 *
 * Scenarios
 *
 *   1.  Happy path: ownership, shared borrows, mutable borrow, assign
 *   2.  Double free
 *   3.  Use after move
 *   4.  Dangling borrow: borrow outlives owner via nested scope
 *   5.  Shared + mutable borrow conflict (with provenance)
 *   6.  Move while borrowed
 *   7.  Drop while borrowed --> dangling + use of dangling
 *   8.  Copy types: no move invalidation
 *   9.  Re-borrow chain
 *  10.  Assign to immutable / borrowed variable
 *  11.  Resource: acquire + explicit release (file handle)
 *  12.  Resource: leak detection (no release before scope exit)
 *  13.  Resource: double-release
 *  14.  Resource: borrow a resource handle, then try to release it
 *  15.  Defer: register cleanup, verify it is satisfied
 *  16.  Defer: unsatisfied defer (missing release)
 *  17.  Mixed: heap allocation leaked on error path
 *  18.  assert_consumed: enforce linear types
 *  19.  Use-kind: write through &T is an error
 *  20.  Use-kind: write through &mut T is fine
 *  21.  Interior mutability: write through &T of RefCell-like var (note)
 *  22.  NLL: borrow ends at last-use, target re-borrowed in same scope
 *  23.  Partial move: field moved out, container partially-moved
 *  24.  Slice borrows: non-overlapping slices compatible, overlapping rejected
 *  25.  Two-phase borrows: reserve then activate
 *  26.  Lifetime regions: borrow in region, region ends, borrow dangling
 *  27.  Region outlives: coerce borrow to shorter region (variance)
 *  28.  Region outlives violation: borrow in shorter region used where longer needed
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

/* -- helpers  */
#define RUN(bc, opts, body) do {                   \
    BC *bc = calloc(1, sizeof *bc); bc_init(bc);   \
    body                                           \
    diag_render_all(bc, opts);                     \
    diag_render_summary(bc, opts);                 \
    free(bc);                                      \
} while (0)



/* -- Scenario 1: Happy path  */
static void s1(const DiagOpts *o) {
    title(1, "Happy path - ownership, borrows, assign");
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
    title(4, "Dangling borrow - borrow outlives owner across scopes");
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
    title(7, "Drop while borrowed - dangling pointer + use");
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
    title(8, "Copy types - no move invalidation");
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
      /* fd never released - ERROR at scope exit */
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
      /* no release - ERROR at scope exit */
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
    title(18, "assert_consumed - linear type enforcement");
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
      /* forgot to submit - just leaves the scope */
      bc_assert_consumed(bc2, "ticket");        /* ERROR: still alive */
    bc_scope_exit(bc2);
    diag_render_all(bc2, o); diag_render_summary(bc2, o); free(bc2);
}

/* 
 * New scenarios
 */

/* -- Scenario 19: write through &T is an error  */
static void s19(const DiagOpts *o) {
    title(19, "USE-KIND: write through &T is rejected");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare    (bc, "data", 1);
          bc_borrow     (bc, "r",    "data");    /* shared borrow */
          bc_use        (bc, "r");               /* read: OK */
          bc_use_write  (bc, "r");               /* write through &T: ERROR */
          bc_release    (bc, "r");
        bc_scope_exit(bc);
    });
}

/* -- Scenario 20: write through &mut T is fine  */
static void s20(const DiagOpts *o) {
    title(20, "USE-KIND: write through &mut T is accepted");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare    (bc, "data", 1);
          bc_borrow_mut (bc, "m",    "data");
          bc_use        (bc, "m");               /* read */
          bc_use_write  (bc, "m");               /* write through &mut: OK */
          bc_release    (bc, "m");
        bc_scope_exit(bc);
    });
}

/* -- Scenario 21: interior mutability  */
static void s21(const DiagOpts *o) {
    title(21, "Interior mutability: write through &T of RefCell-like var (note)");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare_interior_mut(bc, "cell");  /* like RefCell<T> */
          bc_borrow              (bc, "r", "cell");
          bc_use                 (bc, "r");
          bc_use_write           (bc, "r");     /* NOTE: runtime check applies */
          bc_release             (bc, "r");
        bc_scope_exit(bc);
    });
}

/* -- Scenario 22: NLL - borrow ends at last use  */
static void s22(const DiagOpts *o) {
    title(22, "NLL: borrow ends at last-use, target re-borrowed in same scope");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare    (bc, "v",  1);
          bc_borrow     (bc, "r1", "v");
          bc_use        (bc, "r1");
          bc_last_use   (bc, "r1");           /* NLL: r1 ends here */
          /* v is now free to borrow mutably despite r1 not being lexically gone */
          bc_borrow_mut (bc, "m",  "v");
          bc_use_write  (bc, "m");
          bc_release    (bc, "m");
          bc_use        (bc, "r1");           /* ERROR: used after NLL end */
        bc_scope_exit(bc);
    });
}

/* -- Scenario 23: partial moves  */
static void s23(const DiagOpts *o) {
    title(23, "Partial move: field moved out, container partially-moved");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare    (bc, "pair",  0);        /* struct with fields */
          bc_field_move (bc, "first", "pair", "fst");
          bc_use        (bc, "first");           /* moved field: OK */
          bc_use        (bc, "pair");            /* ERROR: partially moved */
          bc_field_move (bc, "second","pair", "fst"); /* ERROR: fst already moved */
        bc_scope_exit(bc);
    });
}

/* -- Scenario 24: slice borrows  */
static void s24(const DiagOpts *o) {
    title(24, "Slice borrows: non-overlapping OK, overlapping rejected");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare        (bc, "arr",  1);
          bc_borrow_slice   (bc, "s1",  "arr", 0, 4);   /* arr[0..4] */
          bc_borrow_slice   (bc, "s2",  "arr", 4, 8);   /* arr[4..8]: OK */
          bc_use            (bc, "s1");
          bc_use            (bc, "s2");
          bc_release        (bc, "s1");
          bc_release        (bc, "s2");
          /* now try overlapping mutable slices */
          bc_borrow_mut_slice(bc, "m1", "arr", 0, 5);
          bc_borrow_mut_slice(bc, "m2", "arr", 3, 7);   /* ERROR: overlaps m1 */
        bc_scope_exit(bc);
    });
}

/* -- Scenario 25: two-phase borrows  */
static void s25(const DiagOpts *o) {
    title(25, "Two-phase borrows: reserve allows shared borrows to coexist");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare           (bc, "v",   1);
          bc_two_phase_reserve (bc, "m",   "v");  /* reserve &mut (not yet active) */
          bc_borrow            (bc, "r",   "v");  /* shared borrow still allowed */
          bc_use               (bc, "r");
          bc_release           (bc, "r");
          bc_two_phase_activate(bc, "m");          /* now activate: exclusive */
          bc_use_write         (bc, "m");
          bc_release           (bc, "m");
        bc_scope_exit(bc);
    });
}

/* -- Scenario 26: lifetime regions  */
static void s26(const DiagOpts *o) {
    title(26, "Lifetime regions: borrow outlives its region");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare           (bc, "data", 0);
          bc_region_begin      (bc, "'a");
            bc_borrow_in_region(bc, "r", "data", "'a");
            bc_use             (bc, "r");
          bc_region_end        (bc, "'a");   /* r's region ends - r dangling */
          bc_use               (bc, "r");    /* ERROR */
        bc_scope_exit(bc);
    });
}

/* -- Scenario 27: region variance - valid coercion  */
/* There is one legitimate error: the coercion itself succeeds
 * (correct - 'long outlives 'short), but the borrow is still
 * active when 'short ends. That's actually the right behaviour:
 * the coercion doesn't extend the borrow's end-of-life obligation,
 * it only restricts which region it's tagged to.
 * A language front-end would need to release the borrow before
 * calling bc_region_end on 'short.
 */
static void s27(const DiagOpts *o) {
    title(27, "Region variance: coerce borrow from longer to shorter region");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare        (bc, "data", 0);
          bc_region_begin   (bc, "'long");
          bc_region_begin   (bc, "'short");
          bc_region_outlives (bc, "'long", "'short"); /* 'long outlives 'short */

          bc_borrow_in_region(bc, "r", "data", "'long");
          bc_coerce_region   (bc, "r", "'short"); /* valid: 'long outlives 'short */
          bc_use             (bc, "r");

          bc_region_end      (bc, "'short");
          bc_region_end      (bc, "'long");
        bc_scope_exit(bc);
    });
}

/* -- Scenario 28: region outlives violation  */
static void s28(const DiagOpts *o) {
    title(28, "Region outlives violation: coerce to longer region rejected");
    RUN(bc, o, {
        bc_scope_enter(bc);
          bc_declare        (bc, "data", 0);
          bc_region_begin   (bc, "'short");
          bc_region_begin   (bc, "'long");
          /* no outlives constraint recorded - 'short does NOT outlive 'long */

          bc_borrow_in_region(bc, "r", "data", "'short");
          bc_coerce_region   (bc, "r", "'long"); /* ERROR: 'short !outlives 'long */

          bc_region_end      (bc, "'long");
          bc_region_end      (bc, "'short");
        bc_scope_exit(bc);
    });
}

/* -- Entry point  */
int main(void) {
    DiagOpts opts = diag_default_opts();

    s1 (&opts); s2 (&opts); s3 (&opts); s4 (&opts); s5 (&opts);
    s6 (&opts); s7 (&opts); s8 (&opts); s9 (&opts); s10(&opts);

    s11(&opts); s12(&opts); s13(&opts); s14(&opts); s15(&opts);
    s16(&opts); s17(&opts); s18(&opts);

    s19(&opts); s20(&opts); s21(&opts); s22(&opts); s23(&opts);
    s24(&opts); s25(&opts); s26(&opts); s27(&opts); s28(&opts);

    return 0;
}

/*
 * The main things outside this checkers scope would be type-level
 * variance (contravariance in function argument positions),
 * trait object lifetime elision, and anything requiring unification
 * across call sites. These belong in a type checker above this layer,
 * and not here.
*/