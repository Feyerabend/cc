/*
 * checker.h  -  Static borrow and resource checker.
 *
 * Features
 * --------
 *  Ownership
 *    Linear ownership with move semantics; Copy types bypass move
 *    invalidation; partial moves mark a struct VS_PARTIALLY_MOVED.
 *
 *  Borrows
 *    Shared (&T), mutable (&mut T), unique (&unique T).
 *    Read-use vs. write-use tracked: writing through a &T is an error.
 *    Re-borrows.  Two-phase borrows (reserve → activate).
 *    Slice/index borrows: non-overlapping sub-ranges of the same owner
 *    are compatible.
 *
 *  Lifetime regions
 *    Named regions with explicit outlives constraints (R1: R2 means R1
 *    outlives R2).  Every borrow is tagged with a region.  The checker
 *    verifies borrows do not escape their region and that region
 *    constraints are respected.  Variance: covariant region coercion
 *    (borrow in longer region usable where shorter region expected).
 *
 *  Non-lexical lifetimes (NLL)
 *    bc_last_use(bc, ref) marks the last use point of a borrow.  After
 *    that point the borrow is considered ended even if still in scope,
 *    allowing re-borrow of the same target in the same scope.
 *
 *  Resources
 *    First-class typed resources (heap, file, socket, lock, custom).
 *    Leak detection at scope exit.  Double-release detection.
 *
 *  Defer / early-exit
 *    bc_defer registers a mandatory cleanup.  bc_scope_exit verifies
 *    all defers for that scope were satisfied.
 *
 *  Interior mutability
 *    bc_declare_interior_mut marks a variable as having interior
 *    mutability (RefCell / UnsafeCell pattern).  The static checker
 *    allows &T borrows of it and notes that runtime checks apply.
 *
 *  Drop order
 *    Reverse declaration order enforced at scope exit (LIFO).
 *
 *  Linear types
 *    bc_assert_consumed verifies a value was moved or dropped.
 *
 *  Diagnostics
 *    Every Diag carries cause_event (where bad state was introduced)
 *    and detect_event (where it was spotted) for two-location errors.
 *
 * Zero I/O.  All state lives in a BC handle.
 */

#ifndef CHECKER_H
#define CHECKER_H

/* -- capacity limits  */
#define BC_MAX_VARS         256
#define BC_MAX_BORROWS      256
#define BC_MAX_RESOURCES    256
#define BC_MAX_EVENTS      4096
#define BC_MAX_DIAGS        512
#define BC_MAX_DEFERS       128
#define BC_MAX_REGIONS       64
#define BC_MAX_REGION_CONS  128   /* outlives constraints                  */
#define BC_MAX_FIELDS        16   /* fields per struct for partial moves   */
#define BC_MAX_SLICES        64   /* active slice borrow records           */
#define BC_MAX_NAME          48
#define BC_MAX_SCOPES        64

/* -- resource kinds  */
typedef enum {
    RK_PLAIN = 0,
    RK_HEAP,
    RK_FILE,
    RK_SOCKET,
    RK_LOCK,
    RK_CUSTOM
} ResourceKind;

/* -- variable state  */
typedef enum {
    VS_ALIVE,
    VS_MOVED,
    VS_DROPPED,
    VS_PARTIALLY_MOVED   /* some fields moved out, others still live       */
} VarState;

/* -- borrow kinds  */
typedef enum {
    BK_SHARED,           /* &T   - read-only, many allowed                 */
    BK_MUTABLE,          /* &mut T - exclusive read/write                  */
    BK_UNIQUE            /* &unique T - non-owning exclusive (Pin-like)    */
} BorrowKind;

typedef enum {
    BS_RESERVED,         /* two-phase: declared but not yet activated      */
    BS_ACTIVE,
    BS_RELEASED,
    BS_DANGLING
} BorrowState;

/* -- use kind  */
typedef enum {
    UK_READ,             /* read-only access                               */
    UK_WRITE,            /* mutation (only valid through &mut or owner)    */
    UK_MOVE_OUT          /* consuming use (only valid on owner)            */
} UseKind;

/* -- operations  */
typedef enum {
    OP_SCOPE_ENTER,
    OP_SCOPE_EXIT,
    OP_REGION_BEGIN,
    OP_REGION_END,
    OP_DECLARE,
    OP_DECLARE_COPY,
    OP_DECLARE_INTERIOR_MUT,
    OP_MOVE,
    OP_COPY,
    OP_ASSIGN,
    OP_FIELD_MOVE,       /* partial move of a named field                  */
    OP_DROP,
    OP_BORROW,
    OP_BORROW_MUT,
    OP_BORROW_SLICE,     /* borrow a sub-range [lo, hi)                    */
    OP_BORROW_MUT_SLICE,
    OP_TWO_PHASE_RESERVE,/* reserve a &mut without activating yet          */
    OP_TWO_PHASE_ACTIVATE,
    OP_RELEASE,
    OP_USE,              /* use(name, UK_READ)                             */
    OP_USE_WRITE,        /* use(name, UK_WRITE)                            */
    OP_LAST_USE,         /* NLL: mark last-use point; borrow ends here     */
    OP_REBORROW,
    OP_RESOURCE_ACQUIRE,
    OP_RESOURCE_RELEASE,
    OP_DEFER,
    OP_ASSERT_CONSUMED,
    OP_COERCE_REGION     /* coerce borrow to a shorter region (variance)   */
} OpKind;

/* -- diagnostic severity  */
typedef enum {
    DIAG_ERROR,
    DIAG_WARNING,
    DIAG_NOTE
} DiagLevel;

typedef struct {
    DiagLevel   level;
    OpKind      op;
    char        subject[BC_MAX_NAME];
    char        msg[320];
    int         cause_event;
    int         detect_event;
} Diag;

/* -- lifetime region record  */
/*
 * A region is a named lifetime scope.  Regions nest like scopes but are
 * independent - a region can span multiple lexical scopes or be a subset
 * of one.  Borrows are tagged with a region; the checker ensures they do
 * not outlive it.
 *
 * Outlives constraint R1: R2 means "region R1 must live at least as long
 * as region R2".  Stored in the constraint table and checked when a borrow
 * in R2 is used where R1 is required.
 */
typedef struct {
    int   id;
    char  name[BC_MAX_NAME];
    int   is_open;
    int   begin_event;
    int   end_event;       /* -1 while open                                */
    int   scope;           /* lexical scope at region_begin                */
} Region;

typedef struct {
    int longer_id;         /* longer_id outlives shorter_id                */
    int shorter_id;
} RegionConstraint;

/* -- slice borrow record  */
/*
 * Tracks a borrow of a sub-range [lo, hi) of an indexed owner.
 * Two slice borrows of the same owner are compatible iff their ranges
 * do not overlap.
 */
typedef struct {
    int   borrow_id;       /* links to Borrow record                       */
    int   lo;              /* inclusive lower bound                        */
    int   hi;              /* exclusive upper bound                        */
} SliceBorrow;

/* -- variable record  */
typedef struct {
    int           id;
    char          name[BC_MAX_NAME];
    VarState      state;
    ResourceKind  res_kind;
    int           scope;
    int           decl_order;
    int           is_copy;
    int           is_mut;
    int           is_interior_mut;  /* RefCell-style: &T can still mutate  */
    int           shared_count;
    int           mut_count;
    int           generation;
    int           cause_event;
    int           region_id;        /* -1 if no explicit region            */
    /* partial-move field tracking (up to BC_MAX_FIELDS named fields) */
    char          moved_fields[BC_MAX_FIELDS][BC_MAX_NAME];
    int           moved_field_count;
} Var;

/* -- borrow record  */
typedef struct {
    int           id;
    char          name[BC_MAX_NAME];
    int           target_var_id;
    BorrowKind    kind;
    BorrowState   state;
    int           scope;
    int           cause_event;
    int           last_use_event;   /* NLL: -1 until bc_last_use called    */
    int           target_generation;
    int           region_id;        /* -1 if no explicit region            */
    int           is_slice;         /* 1 if this is a slice borrow         */
    int           slice_lo;
    int           slice_hi;
} Borrow;

/* -- resource record  */
typedef struct {
    int           id;
    char          var_name[BC_MAX_NAME];
    ResourceKind  kind;
    int           is_released;
    int           scope;
    int           acquire_event;
    int           release_event;
} Resource;

/* -- defer record  */
typedef struct {
    char  var_name[BC_MAX_NAME];
    int   scope;
    int   satisfied;
    int   register_event;
} Defer;

/* -- event snapshot  */
typedef struct {
    int       index;
    OpKind    op;
    char      a[BC_MAX_NAME];
    char      b[BC_MAX_NAME];
    int       int_arg;        /* lo index, use-kind, or region id          */
    int       int_arg2;       /* hi index                                  */
    int       scope_before;
    int       scope_after;
    int       ok;

    Var       vars      [BC_MAX_VARS];
    int       var_count;
    Borrow    borrows   [BC_MAX_BORROWS];
    int       borrow_count;
    Resource  resources [BC_MAX_RESOURCES];
    int       resource_count;
    Region    regions   [BC_MAX_REGIONS];
    int       region_count;
    int       scope;
} Event;

/* -- checker handle  */
typedef struct {
    Var               vars        [BC_MAX_VARS];
    int               var_count;
    Borrow            borrows     [BC_MAX_BORROWS];
    int               borrow_count;
    Resource          resources   [BC_MAX_RESOURCES];
    int               resource_count;
    Defer             defers      [BC_MAX_DEFERS];
    int               defer_count;
    Region            regions     [BC_MAX_REGIONS];
    int               region_count;
    RegionConstraint  reg_cons    [BC_MAX_REGION_CONS];
    int               reg_con_count;
    int               scope;
    int               scope_decl_order[BC_MAX_SCOPES];

    Event             events      [BC_MAX_EVENTS];
    int               event_count;
    Diag              diags       [BC_MAX_DIAGS];
    int               diag_count;

    int               next_var_id;
    int               next_borrow_id;
    int               next_resource_id;
    int               next_region_id;
    int               error_count;
    int               warning_count;
} BC;

/* 
 * Public API
 */

/* lifecycle */
void bc_init                (BC *bc);

/* scopes */
void bc_scope_enter         (BC *bc);
void bc_scope_exit          (BC *bc);

/* lifetime regions */
int  bc_region_begin        (BC *bc, const char *name);
void bc_region_end          (BC *bc, const char *name);
void bc_region_outlives     (BC *bc, const char *longer, const char *shorter);
void bc_borrow_in_region    (BC *bc, const char *ref_name, const char *target,
                             const char *region_name);
void bc_borrow_mut_in_region(BC *bc, const char *ref_name, const char *target,
                             const char *region_name);
void bc_coerce_region       (BC *bc, const char *ref_name,
                             const char *new_region_name);

/* variables */
void bc_declare             (BC *bc, const char *name, int is_mut);
void bc_declare_copy        (BC *bc, const char *name);
void bc_declare_interior_mut(BC *bc, const char *name);
void bc_assign              (BC *bc, const char *name);
void bc_move                (BC *bc, const char *dst, const char *src);
void bc_copy                (BC *bc, const char *dst, const char *src);
void bc_field_move          (BC *bc, const char *dst, const char *src,
                             const char *field);
void bc_drop                (BC *bc, const char *name);
void bc_use                 (BC *bc, const char *name);
void bc_use_write           (BC *bc, const char *name);

/* borrows */
void bc_borrow              (BC *bc, const char *ref_name, const char *target);
void bc_borrow_mut          (BC *bc, const char *ref_name, const char *target);
void bc_borrow_slice        (BC *bc, const char *ref_name, const char *target,
                             int lo, int hi);
void bc_borrow_mut_slice    (BC *bc, const char *ref_name, const char *target,
                             int lo, int hi);
void bc_two_phase_reserve   (BC *bc, const char *ref_name, const char *target);
void bc_two_phase_activate  (BC *bc, const char *ref_name);
void bc_reborrow            (BC *bc, const char *new_ref, const char *src_ref);
void bc_release             (BC *bc, const char *ref_name);
void bc_last_use            (BC *bc, const char *ref_name);

/* resources */
void bc_resource_acquire    (BC *bc, const char *name, ResourceKind kind);
void bc_resource_release    (BC *bc, const char *name);

/* defer / linear */
void bc_defer               (BC *bc, const char *name);
void bc_assert_consumed     (BC *bc, const char *name);

/* queries */
const Var      *bc_find_var      (const BC *bc, const char *name);
const Borrow   *bc_find_borrow   (const BC *bc, const char *name);
const Resource *bc_find_resource (const BC *bc, const char *name);
const Region   *bc_find_region   (const BC *bc, const char *name);

/* name helpers */
const char *bc_var_state_name    (VarState s);
const char *bc_borrow_kind_name  (BorrowKind k);
const char *bc_borrow_state_name (BorrowState s);
const char *bc_resource_kind_name(ResourceKind k);
const char *bc_op_name           (OpKind op);
const char *bc_use_kind_name     (UseKind uk);

#endif /* CHECKER_H */
