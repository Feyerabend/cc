/*
 * checker.h  -  Static borrow and resource checker.
 *
 * Design goals
 * ------------
 * 1. Complete static safety: a language using this checker needs zero
 *    runtime checks for memory safety, double-free, leaks, or dangling
 *    pointers.  If bc_error_count == 0 the program is safe.
 *
 * 2. Resources as first-class entities: file handles, sockets, locks,
 *    heap allocations are tracked with the same rigour as owned values.
 *    Each has a ResourceKind so diagnostics can say "FileHandle leaked".
 *
 * 3. Drop-order guarantees: variables drop in reverse declaration order
 *    at scope exit.  Borrows that would violate this are rejected.
 *
 * 4. Defer / early-exit paths: bc_defer() registers "this name MUST be
 *    released before scope exits."  The checker verifies completeness
 *    at scope_exit, covering every exit path statically.
 *
 * 5. Rich provenance: every Diag carries both the event where the bad
 *    state was *introduced* and the event where it was *detected*.
 *    A language front-end can emit two-location error messages.
 *
 * 6. Order independence: the checker requires only the natural program
 *    structure (enter before exit, declare before use).  It internally
 *    enforces everything else - no specific call ordering needed.
 *
 * Zero I/O: no printf, no globals, all state lives in a BC handle.
 */

#ifndef CHECKER_H
#define CHECKER_H

/* -- capacity limits  */
#define BC_MAX_VARS       256
#define BC_MAX_BORROWS    256
#define BC_MAX_RESOURCES  256
#define BC_MAX_EVENTS    2048
#define BC_MAX_DIAGS      512
#define BC_MAX_DEFERS     128
#define BC_MAX_NAME        48
#define BC_MAX_SCOPES      64

/* -- resource kinds  */
typedef enum {
    RK_PLAIN = 0,   /* generic owned value                  */
    RK_HEAP,        /* heap allocation (malloc/free)        */
    RK_FILE,        /* file handle (open/close)             */
    RK_SOCKET,      /* network socket                       */
    RK_LOCK,        /* mutex / rwlock                       */
    RK_CUSTOM       /* language-defined                     */
} ResourceKind;

/* -- variable state machine  */
typedef enum {
    VS_ALIVE,
    VS_MOVED,
    VS_DROPPED,
    VS_PARTIALLY_MOVED
} VarState;

/* -- borrow flavours  */
typedef enum {
    BK_SHARED,      /* &T    - read-only, many allowed      */
    BK_MUTABLE,     /* &mut T - exclusive read/write        */
    BK_UNIQUE       /* unique non-owning ref (like Pin)     */
} BorrowKind;

typedef enum {
    BS_ACTIVE,
    BS_RELEASED,
    BS_DANGLING
} BorrowState;

/* -- operations  */
typedef enum {
    OP_SCOPE_ENTER,
    OP_SCOPE_EXIT,
    OP_DECLARE,
    OP_DECLARE_COPY,
    OP_MOVE,
    OP_COPY,
    OP_ASSIGN,
    OP_DROP,
    OP_BORROW,
    OP_BORROW_MUT,
    OP_RELEASE,
    OP_USE,
    OP_REBORROW,
    OP_RESOURCE_ACQUIRE,
    OP_RESOURCE_RELEASE,
    OP_DEFER,
    OP_ASSERT_CONSUMED
} OpKind;

/* -- diagnostic severity  */
typedef enum {
    DIAG_ERROR,
    DIAG_WARNING,
    DIAG_NOTE
} DiagLevel;

/* -- diagnostic with provenance  */
typedef struct {
    DiagLevel   level;
    OpKind      op;
    char        subject[BC_MAX_NAME];
    char        msg[320];
    int         cause_event;    /* event that *introduced* the bad state  */
    int         detect_event;   /* event where the checker *detected* it  */
} Diag;

/* -- variable record  */
typedef struct {
    int           id;
    char          name[BC_MAX_NAME];
    VarState      state;
    ResourceKind  res_kind;     /* RK_PLAIN for ordinary values           */
    int           scope;
    int           decl_order;   /* position within scope (for drop order) */
    int           is_copy;
    int           is_mut;
    int           shared_count;
    int           mut_count;
    int           generation;   /* incremented on each assign             */
    int           cause_event;  /* event where this var was declared      */
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
    int           target_generation;
} Borrow;

/* -- resource record  */
/*
 * A resource is an external capability (handle, allocation, lock) tied
 * to a variable.  Acquiring creates both a Var and a Resource record.
 * Releasing closes the resource and drops the variable in one step.
 * If a scope exits while a resource is unreleased the checker emits a
 * DIAG_ERROR naming the resource kind (e.g. "FileHandle leaked").
 */
typedef struct {
    int           id;
    char          var_name[BC_MAX_NAME];
    ResourceKind  kind;
    int           is_released;
    int           scope;
    int           acquire_event;
    int           release_event;  /* -1 if not yet released               */
} Resource;

/* -- deferred-release record  */
/*
 * bc_defer(bc, "name") says: before this scope exits, "name" MUST be
 * released on every exit path.  The checker verifies this at scope_exit.
 * This is the static equivalent of try/finally or C++ RAII destructors.
 */
typedef struct {
    char  var_name[BC_MAX_NAME];
    int   scope;
    int   satisfied;
    int   register_event;
} Defer;

/* -- immutable event snapshot  */
typedef struct {
    int       index;
    OpKind    op;
    char      a[BC_MAX_NAME];
    char      b[BC_MAX_NAME];
    int       scope_before;
    int       scope_after;
    int       ok;

    Var       vars      [BC_MAX_VARS];
    int       var_count;
    Borrow    borrows   [BC_MAX_BORROWS];
    int       borrow_count;
    Resource  resources [BC_MAX_RESOURCES];
    int       resource_count;
    int       scope;
} Event;

/* -- checker handle  */
typedef struct {
    Var       vars      [BC_MAX_VARS];
    int       var_count;
    Borrow    borrows   [BC_MAX_BORROWS];
    int       borrow_count;
    Resource  resources [BC_MAX_RESOURCES];
    int       resource_count;
    Defer     defers    [BC_MAX_DEFERS];
    int       defer_count;
    int       scope;
    int       scope_decl_order[BC_MAX_SCOPES];

    Event     events    [BC_MAX_EVENTS];
    int       event_count;
    Diag      diags     [BC_MAX_DIAGS];
    int       diag_count;

    int       next_var_id;
    int       next_borrow_id;
    int       next_resource_id;
    int       error_count;
    int       warning_count;
} BC;

/*
 * Public API
 *
 * Minimal required order:
 *   bc_scope_enter  before  bc_scope_exit  (for the same logical scope)
 *   bc_declare / bc_resource_acquire  before first use of that name
 *   Everything else is enforced by the checker.
 */

void bc_init             (BC *bc);

void bc_scope_enter      (BC *bc);
void bc_scope_exit       (BC *bc);

void bc_declare          (BC *bc, const char *name, int is_mut);
void bc_declare_copy     (BC *bc, const char *name);
void bc_assign           (BC *bc, const char *name);
void bc_move             (BC *bc, const char *dst, const char *src);
void bc_copy             (BC *bc, const char *dst, const char *src);
void bc_drop             (BC *bc, const char *name);
void bc_use              (BC *bc, const char *name);

void bc_borrow           (BC *bc, const char *ref_name, const char *target);
void bc_borrow_mut       (BC *bc, const char *ref_name, const char *target);
void bc_reborrow         (BC *bc, const char *new_ref,  const char *src_ref);
void bc_release          (BC *bc, const char *ref_name);

void bc_resource_acquire (BC *bc, const char *name, ResourceKind kind);
void bc_resource_release (BC *bc, const char *name);

void bc_defer            (BC *bc, const char *name);
void bc_assert_consumed  (BC *bc, const char *name);

const Var      *bc_find_var      (const BC *bc, const char *name);
const Borrow   *bc_find_borrow   (const BC *bc, const char *name);
const Resource *bc_find_resource (const BC *bc, const char *name);

const char *bc_var_state_name    (VarState s);
const char *bc_borrow_kind_name  (BorrowKind k);
const char *bc_resource_kind_name(ResourceKind k);
const char *bc_op_name           (OpKind op);

#endif /* CHECKER_H */
