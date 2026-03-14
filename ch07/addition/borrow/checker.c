/*
 * checker.c  -  Full borrow and resource checker.  Zero I/O.
 *
 * Three-phase contract for every bc_* function:
 *   1. VALIDATE  - inspect live state, push Diag(s) on violations.
 *   2. MUTATE    - update live state only when operation is legal.
 *   3. SNAPSHOT  - push an Event (full state copy) to the log.
 *
 * New features over the previous version
 * ---------------------------------------
 *  Use-kind checking
 *    bc_use() is read-only.  bc_use_write() requires the target to be
 *    either an owned mutable variable or an active &mut borrow.
 *    Writing through a shared &T borrow is an error.
 *
 *  Lifetime regions
 *    Named regions created with bc_region_begin/end.  Borrows can be
 *    tagged to a region; they become dangling when the region ends.
 *    bc_region_outlives(R1, R2) records that R1 outlives R2; the checker
 *    verifies borrows passed across region boundaries respect this.
 *    bc_coerce_region coerces a borrow to a shorter region (variance).
 *
 *  Non-lexical lifetimes (NLL)
 *    bc_last_use(ref) ends the borrow at that point even if still in
 *    lexical scope, immediately freeing the target for re-borrowing.
 *
 *  Partial moves
 *    bc_field_move(dst, src, field) moves one named field out of src.
 *    src transitions to VS_PARTIALLY_MOVED; the checker records which
 *    fields are gone and rejects use of moved-out fields.
 *
 *  Slice / index borrows
 *    bc_borrow_slice / bc_borrow_mut_slice tag a borrow with [lo, hi).
 *    Two slice borrows of the same owner are compatible iff their ranges
 *    do not overlap.  Mutable slice borrows additionally must not overlap
 *    with any other borrow (shared or mutable) of the same owner.
 *
 *  Two-phase borrows
 *    bc_two_phase_reserve creates a BS_RESERVED &mut borrow.  While
 *    reserved, shared borrows of the same target are still allowed.
 *    bc_two_phase_activate promotes it to BS_ACTIVE, at which point the
 *    normal exclusive rules apply.
 *
 *  Interior mutability
 *    bc_declare_interior_mut marks a var as RefCell-like.  Shared borrows
 *    are allowed even when the var is "mutated" through them; the checker
 *    emits a NOTE that runtime checks apply.
 *
 *  Region variance / coercion
 *    bc_coerce_region(ref, new_region) re-tags a borrow to a shorter
 *    region, valid because a longer-lived borrow can always satisfy a
 *    shorter-lived requirement (covariance in region parameters).
 */

#include "checker.h"
#include <string.h>
#include <stdio.h>
#include <stdarg.h>

/* 
 * Name tables
 */

const char *bc_var_state_name(VarState s) {
    switch (s) {
        case VS_ALIVE:           return "alive";
        case VS_MOVED:           return "moved";
        case VS_DROPPED:         return "dropped";
        case VS_PARTIALLY_MOVED: return "partially-moved";
    }
    return "?";
}

const char *bc_borrow_kind_name(BorrowKind k) {
    switch (k) {
        case BK_SHARED:   return "&T";
        case BK_MUTABLE:  return "&mut T";
        case BK_UNIQUE:   return "&unique T";
    }
    return "?";
}

const char *bc_borrow_state_name(BorrowState s) {
    switch (s) {
        case BS_RESERVED: return "reserved";
        case BS_ACTIVE:   return "active";
        case BS_RELEASED: return "released";
        case BS_DANGLING: return "dangling";
    }
    return "?";
}

const char *bc_resource_kind_name(ResourceKind k) {
    switch (k) {
        case RK_PLAIN:  return "value";
        case RK_HEAP:   return "HeapAlloc";
        case RK_FILE:   return "FileHandle";
        case RK_SOCKET: return "Socket";
        case RK_LOCK:   return "Lock";
        case RK_CUSTOM: return "Resource";
    }
    return "?";
}

const char *bc_use_kind_name(UseKind uk) {
    switch (uk) {
        case UK_READ:     return "read";
        case UK_WRITE:    return "write";
        case UK_MOVE_OUT: return "move-out";
    }
    return "?";
}

const char *bc_op_name(OpKind op) {
    switch (op) {
        case OP_SCOPE_ENTER:          return "SCOPE ENTER";
        case OP_SCOPE_EXIT:           return "SCOPE EXIT";
        case OP_REGION_BEGIN:         return "REGION BEGIN";
        case OP_REGION_END:           return "REGION END";
        case OP_DECLARE:              return "DECLARE";
        case OP_DECLARE_COPY:         return "DECLARE (Copy)";
        case OP_DECLARE_INTERIOR_MUT: return "DECLARE (IntMut)";
        case OP_MOVE:                 return "MOVE";
        case OP_COPY:                 return "COPY";
        case OP_ASSIGN:               return "ASSIGN";
        case OP_FIELD_MOVE:           return "FIELD MOVE";
        case OP_DROP:                 return "DROP";
        case OP_BORROW:               return "BORROW &";
        case OP_BORROW_MUT:           return "BORROW &mut";
        case OP_BORROW_SLICE:         return "BORROW &[lo,hi)";
        case OP_BORROW_MUT_SLICE:     return "BORROW &mut[lo,hi)";
        case OP_TWO_PHASE_RESERVE:    return "2PH RESERVE";
        case OP_TWO_PHASE_ACTIVATE:   return "2PH ACTIVATE";
        case OP_RELEASE:              return "RELEASE";
        case OP_USE:                  return "USE";
        case OP_USE_WRITE:            return "USE (write)";
        case OP_LAST_USE:             return "LAST USE (NLL)";
        case OP_REBORROW:             return "REBORROW";
        case OP_RESOURCE_ACQUIRE:     return "ACQUIRE";
        case OP_RESOURCE_RELEASE:     return "RELEASE_RES";
        case OP_DEFER:                return "DEFER";
        case OP_ASSERT_CONSUMED:      return "ASSERT_CONSUMED";
        case OP_COERCE_REGION:        return "COERCE REGION";
    }
    return "?";
}

/*
 * Internal lookup
 */

static Var *find_var_mut(BC *bc, const char *name) {
    for (int i = bc->var_count - 1; i >= 0; i--)
        if (strcmp(bc->vars[i].name, name) == 0)
            return &bc->vars[i];
    return NULL;
}

static Borrow *find_borrow_mut(BC *bc, const char *name) {
    for (int j = bc->borrow_count - 1; j >= 0; j--)
        if (strcmp(bc->borrows[j].name, name) == 0)
            return &bc->borrows[j];
    return NULL;
}

static Resource *find_resource_mut(BC *bc, const char *name) {
    for (int r = bc->resource_count - 1; r >= 0; r--)
        if (strcmp(bc->resources[r].var_name, name) == 0)
            return &bc->resources[r];
    return NULL;
}

static Region *find_region_mut(BC *bc, const char *name) {
    for (int r = bc->region_count - 1; r >= 0; r--)
        if (strcmp(bc->regions[r].name, name) == 0)
            return &bc->regions[r];
    return NULL;
}

const Var    *bc_find_var     (const BC *bc, const char *n) {
    for (int i = bc->var_count    - 1; i >= 0; i--)
        if (strcmp(bc->vars[i].name,     n) == 0) return &bc->vars[i];
    return NULL;
}
const Borrow *bc_find_borrow  (const BC *bc, const char *n) {
    for (int j = bc->borrow_count - 1; j >= 0; j--)
        if (strcmp(bc->borrows[j].name,  n) == 0) return &bc->borrows[j];
    return NULL;
}
const Resource *bc_find_resource(const BC *bc, const char *n) {
    for (int r = bc->resource_count - 1; r >= 0; r--)
        if (strcmp(bc->resources[r].var_name, n) == 0) return &bc->resources[r];
    return NULL;
}
const Region *bc_find_region  (const BC *bc, const char *n) {
    for (int r = bc->region_count - 1; r >= 0; r--)
        if (strcmp(bc->regions[r].name,  n) == 0) return &bc->regions[r];
    return NULL;
}

/*
 * Diagnostic helpers
 */

static Diag *push_diag(BC *bc, DiagLevel level, OpKind op,
                        const char *subject, int cause_ev,
                        const char *fmt, ...)
{
    if (bc->diag_count >= BC_MAX_DIAGS) return NULL;
    Diag *d       = &bc->diags[bc->diag_count++];
    d->level       = level;
    d->op          = op;
    d->cause_event = cause_ev;
    d->detect_event = bc->event_count;
    strncpy(d->subject, subject ? subject : "", BC_MAX_NAME - 1);
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(d->msg, sizeof d->msg, fmt, ap);
    va_end(ap);
    if (level == DIAG_ERROR)   bc->error_count++;
    if (level == DIAG_WARNING) bc->warning_count++;
    return d;
}

/*
 * Event snapshot
 */

static void push_event(BC *bc, OpKind op, const char *a, const char *b,
                        int int_arg, int int_arg2, int scope_before, int ok)
{
    if (bc->event_count >= BC_MAX_EVENTS) return;
    Event *ev        = &bc->events[bc->event_count];
    ev->index        = bc->event_count + 1;
    ev->op           = op;
    ev->scope_before = scope_before;
    ev->scope_after  = bc->scope;
    ev->scope        = bc->scope;
    ev->ok           = ok;
    ev->int_arg      = int_arg;
    ev->int_arg2     = int_arg2;
    strncpy(ev->a, a ? a : "", BC_MAX_NAME - 1);
    strncpy(ev->b, b ? b : "", BC_MAX_NAME - 1);

    ev->var_count      = bc->var_count;
    ev->borrow_count   = bc->borrow_count;
    ev->resource_count = bc->resource_count;
    ev->region_count   = bc->region_count;
    memcpy(ev->vars,      bc->vars,      sizeof(Var)      * (size_t)bc->var_count);
    memcpy(ev->borrows,   bc->borrows,   sizeof(Borrow)   * (size_t)bc->borrow_count);
    memcpy(ev->resources, bc->resources, sizeof(Resource) * (size_t)bc->resource_count);
    memcpy(ev->regions,   bc->regions,   sizeof(Region)   * (size_t)bc->region_count);

    bc->event_count++;
}

/*
 * Internal drop helpers
 */

static void dec_borrow_counts(BC *bc, Borrow *b) {
    for (int i = 0; i < bc->var_count; i++) {
        if (bc->vars[i].id == b->target_var_id) {
            if (b->kind == BK_SHARED) bc->vars[i].shared_count--;
            else                      bc->vars[i].mut_count--;
            break;
        }
    }
    b->state = BS_RELEASED;
}

static void mark_dangling_borrows(BC *bc, const Var *v, OpKind trigger) {
    for (int j = 0; j < bc->borrow_count; j++) {
        Borrow *b = &bc->borrows[j];
        if ((b->state == BS_ACTIVE || b->state == BS_RESERVED)
                && b->target_var_id == v->id) {
            push_diag(bc, DIAG_ERROR, trigger, b->name, b->cause_event,
                "dangling %s borrow '%s' of '%s': target dropped "
                "(borrow from event #%d)",
                bc_borrow_kind_name(b->kind), b->name, v->name,
                b->cause_event + 1);
            push_diag(bc, DIAG_NOTE, trigger, b->name, b->cause_event,
                "borrow '%s' was created at event #%d",
                b->name, b->cause_event + 1);
            b->state = BS_DANGLING;
        }
    }
}

static void drop_var(BC *bc, Var *v, OpKind trigger) {
    if (v->state != VS_ALIVE && v->state != VS_PARTIALLY_MOVED) return;
    mark_dangling_borrows(bc, v, trigger);
    Resource *res = find_resource_mut(bc, v->name);
    if (res && !res->is_released)
        push_diag(bc, DIAG_ERROR, trigger, v->name, res->acquire_event,
            "%s '%s' leaked: acquired at event #%d, never released",
            bc_resource_kind_name(res->kind), v->name,
            res->acquire_event + 1);
    v->state = VS_DROPPED;
}

/*
 * Lifecycle
 */

void bc_init(BC *bc) {
    memset(bc, 0, sizeof *bc);
    bc->next_var_id      = 1;
    bc->next_borrow_id   = 1;
    bc->next_resource_id = 1;
    bc->next_region_id   = 1;
}

/*
 * Scope
 */

void bc_scope_enter(BC *bc) {
    int before = bc->scope;
    if (bc->scope < BC_MAX_SCOPES - 1) {
        bc->scope++;
        bc->scope_decl_order[bc->scope] = 0;
    } else {
        push_diag(bc, DIAG_ERROR, OP_SCOPE_ENTER, NULL, bc->event_count,
            "scope depth limit exceeded");
    }
    push_event(bc, OP_SCOPE_ENTER, NULL, NULL, 0, 0, before, 1);
}

void bc_scope_exit(BC *bc) {
    if (bc->scope == 0) {
        push_diag(bc, DIAG_ERROR, OP_SCOPE_EXIT, NULL, bc->event_count,
            "scope_exit with no matching scope_enter");
        push_event(bc, OP_SCOPE_EXIT, NULL, NULL, 0, 0, 0, 0);
        return;
    }
    int before = bc->scope;

    /* phase 1: auto-close any regions opened in this scope */
    for (int r = 0; r < bc->region_count; r++) {
        Region *rg = &bc->regions[r];
        if (rg->is_open && rg->scope == bc->scope) {
            rg->is_open   = 0;
            rg->end_event = bc->event_count;
            /* mark borrows in this region dangling */
            for (int j = 0; j < bc->borrow_count; j++) {
                Borrow *b = &bc->borrows[j];
                if ((b->state == BS_ACTIVE || b->state == BS_RESERVED)
                        && b->region_id == rg->id) {
                    push_diag(bc, DIAG_ERROR, OP_SCOPE_EXIT, b->name,
                        b->cause_event,
                        "borrow '%s' in region '%s' outlives its region "
                        "(borrow from event #%d)",
                        b->name, rg->name, b->cause_event + 1);
                    b->state = BS_DANGLING;
                }
            }
        }
    }

    /* phase 2: verify defers */
    for (int d = 0; d < bc->defer_count; d++) {
        Defer *df = &bc->defers[d];
        if (df->scope == bc->scope && !df->satisfied)
            push_diag(bc, DIAG_ERROR, OP_SCOPE_EXIT, df->var_name,
                df->register_event,
                "deferred release of '%s' not satisfied before scope exit "
                "(registered at event #%d)",
                df->var_name, df->register_event + 1);
    }

    /* phase 3: release borrows created in this scope */
    for (int j = 0; j < bc->borrow_count; j++) {
        Borrow *b = &bc->borrows[j];
        if ((b->state == BS_ACTIVE || b->state == BS_RESERVED)
                && b->scope == bc->scope)
            dec_borrow_counts(bc, b);
    }

    /* phase 4: drop vars in reverse declaration order */
    int order[BC_MAX_VARS];
    int nc = 0;
    for (int i = 0; i < bc->var_count; i++)
        if (bc->vars[i].scope == bc->scope
                && (bc->vars[i].state == VS_ALIVE
                    || bc->vars[i].state == VS_PARTIALLY_MOVED))
            order[nc++] = i;
    for (int a = 0; a < nc - 1; a++)
        for (int b2 = a + 1; b2 < nc; b2++)
            if (bc->vars[order[a]].decl_order < bc->vars[order[b2]].decl_order) {
                int tmp = order[a]; order[a] = order[b2]; order[b2] = tmp;
            }
    for (int k = 0; k < nc; k++)
        drop_var(bc, &bc->vars[order[k]], OP_SCOPE_EXIT);

    bc->scope--;
    push_event(bc, OP_SCOPE_EXIT, NULL, NULL, 0, 0, before, 1);
}

/*
 * Lifetime regions
 */

int bc_region_begin(BC *bc, const char *name) {
    if (bc->region_count >= BC_MAX_REGIONS) {
        push_diag(bc, DIAG_ERROR, OP_REGION_BEGIN, name, bc->event_count,
            "region table full");
        push_event(bc, OP_REGION_BEGIN, name, NULL, 0, 0, bc->scope, 0);
        return -1;
    }
    Region *rg   = &bc->regions[bc->region_count++];
    strncpy(rg->name, name, BC_MAX_NAME - 1);
    rg->id          = bc->next_region_id++;
    rg->is_open     = 1;
    rg->begin_event = bc->event_count;
    rg->end_event   = -1;
    rg->scope       = bc->scope;
    push_event(bc, OP_REGION_BEGIN, name, NULL, rg->id, 0, bc->scope, 1);
    return rg->id;
}

void bc_region_end(BC *bc, const char *name) {
    Region *rg = find_region_mut(bc, name);
    int ok = 1;
    if (!rg) {
        push_diag(bc, DIAG_ERROR, OP_REGION_END, name, bc->event_count,
            "region_end: unknown region '%s'", name);
        ok = 0;
    } else if (!rg->is_open) {
        push_diag(bc, DIAG_ERROR, OP_REGION_END, name, rg->begin_event,
            "region '%s' is already closed", name);
        ok = 0;
    }
    if (ok) {
        rg->is_open   = 0;
        rg->end_event = bc->event_count;
        /* invalidate borrows tagged to this region */
        for (int j = 0; j < bc->borrow_count; j++) {
            Borrow *b = &bc->borrows[j];
            if ((b->state == BS_ACTIVE || b->state == BS_RESERVED)
                    && b->region_id == rg->id) {
                push_diag(bc, DIAG_ERROR, OP_REGION_END, b->name,
                    b->cause_event,
                    "borrow '%s' in region '%s' is still active when region ends "
                    "(borrow from event #%d)",
                    b->name, name, b->cause_event + 1);
                b->state = BS_DANGLING;
            }
        }
    }
    push_event(bc, OP_REGION_END, name, NULL, 0, 0, bc->scope, ok);
}

void bc_region_outlives(BC *bc, const char *longer, const char *shorter) {
    Region *rl = find_region_mut(bc, longer);
    Region *rs = find_region_mut(bc, shorter);
    if (!rl || !rs) {
        push_diag(bc, DIAG_ERROR, OP_REGION_BEGIN, longer, bc->event_count,
            "region_outlives: unknown region '%s' or '%s'", longer, shorter);
        return;
    }
    if (bc->reg_con_count >= BC_MAX_REGION_CONS) return;
    RegionConstraint *rc = &bc->reg_cons[bc->reg_con_count++];
    rc->longer_id  = rl->id;
    rc->shorter_id = rs->id;
}

/* check that region r_long outlives r_short per recorded constraints */
static int region_outlives(BC *bc, int r_long_id, int r_short_id) {
    if (r_long_id == r_short_id) return 1;
    for (int i = 0; i < bc->reg_con_count; i++)
        if (bc->reg_cons[i].longer_id  == r_long_id &&
            bc->reg_cons[i].shorter_id == r_short_id)
            return 1;
    return 0;
}

void bc_coerce_region(BC *bc, const char *ref_name,
                       const char *new_region_name)
{
    Borrow *b  = find_borrow_mut(bc, ref_name);
    Region *nr = find_region_mut(bc, new_region_name);
    int ok = 1;

    if (!b) {
        push_diag(bc, DIAG_ERROR, OP_COERCE_REGION, ref_name, bc->event_count,
            "coerce_region: unknown borrow '%s'", ref_name);
        ok = 0;
    } else if (!nr) {
        push_diag(bc, DIAG_ERROR, OP_COERCE_REGION, ref_name, bc->event_count,
            "coerce_region: unknown region '%s'", new_region_name);
        ok = 0;
    } else if (b->region_id != -1 &&
               !region_outlives(bc, b->region_id, nr->id)) {
        push_diag(bc, DIAG_ERROR, OP_COERCE_REGION, ref_name, b->cause_event,
            "cannot coerce borrow '%s' to region '%s': "
            "source region does not outlive target region",
            ref_name, new_region_name);
        ok = 0;
    }
    if (ok && b) b->region_id = nr->id;
    push_event(bc, OP_COERCE_REGION, ref_name, new_region_name, 0, 0,
               bc->scope, ok);
}

/*
 * Variable helpers
 */

static Var *alloc_var(BC *bc, const char *name, int is_mut, ResourceKind rk) {
    if (bc->var_count >= BC_MAX_VARS) return NULL;
    Var *v = &bc->vars[bc->var_count++];
    memset(v, 0, sizeof *v);
    strncpy(v->name, name, BC_MAX_NAME - 1);
    v->id          = bc->next_var_id++;
    v->state       = VS_ALIVE;
    v->scope       = bc->scope;
    v->is_mut      = is_mut;
    v->res_kind    = rk;
    v->generation  = 1;
    v->cause_event = bc->event_count;
    v->region_id   = -1;
    if (bc->scope < BC_MAX_SCOPES)
        v->decl_order = bc->scope_decl_order[bc->scope]++;
    return v;
}

/*
 * Variable operations
 */

void bc_declare(BC *bc, const char *name, int is_mut) {
    int ok = 1;
    Var *ex = find_var_mut(bc, name);
    if (ex && ex->state == VS_ALIVE && ex->scope == bc->scope) {
        push_diag(bc, DIAG_WARNING, OP_DECLARE, name, bc->event_count,
            "shadowing live variable '%s' in the same scope", name);
        ex->state = VS_MOVED;
    }
    if (!alloc_var(bc, name, is_mut, RK_PLAIN)) {
        push_diag(bc, DIAG_ERROR, OP_DECLARE, name, bc->event_count,
            "variable table full");
        ok = 0;
    }
    push_event(bc, OP_DECLARE, name, NULL, 0, 0, bc->scope, ok);
}

void bc_declare_copy(BC *bc, const char *name) {
    bc_declare(bc, name, 0);
    if (bc->var_count > 0)
        bc->vars[bc->var_count - 1].is_copy = 1;
    if (bc->event_count > 0)
        bc->events[bc->event_count - 1].op = OP_DECLARE_COPY;
}

void bc_declare_interior_mut(BC *bc, const char *name) {
    bc_declare(bc, name, 0);
    if (bc->var_count > 0)
        bc->vars[bc->var_count - 1].is_interior_mut = 1;
    if (bc->event_count > 0)
        bc->events[bc->event_count - 1].op = OP_DECLARE_INTERIOR_MUT;
}

void bc_assign(BC *bc, const char *name) {
    Var *v = find_var_mut(bc, name);
    int ok = 1;

    if (!v) {
        push_diag(bc, DIAG_ERROR, OP_ASSIGN, name, bc->event_count,
            "assign to undeclared '%s'", name);
        ok = 0;
    } else if (!v->is_mut) {
        push_diag(bc, DIAG_ERROR, OP_ASSIGN, name, v->cause_event,
            "cannot assign to immutable variable '%s' (declared at event #%d)",
            name, v->cause_event + 1);
        ok = 0;
    } else if (v->state != VS_ALIVE) {
        push_diag(bc, DIAG_ERROR, OP_ASSIGN, name, v->cause_event,
            "cannot assign to %s variable '%s'",
            bc_var_state_name(v->state), name);
        ok = 0;
    } else if (v->shared_count > 0 || v->mut_count > 0) {
        int bev = bc->event_count;
        for (int j = 0; j < bc->borrow_count; j++) {
            Borrow *b = &bc->borrows[j];
            if (b->state == BS_ACTIVE && b->target_var_id == v->id) {
                bev = b->cause_event; break;
            }
        }
        push_diag(bc, DIAG_ERROR, OP_ASSIGN, name, bev,
            "cannot assign to '%s' while borrowed "
            "(%d shared, %d mutable; borrow from event #%d)",
            name, v->shared_count, v->mut_count, bev + 1);
        ok = 0;
    }
    if (ok) { v->generation++; v->moved_field_count = 0; }
    push_event(bc, OP_ASSIGN, name, NULL, 0, 0, bc->scope, ok);
}

void bc_move(BC *bc, const char *dst, const char *src) {
    Var *s = find_var_mut(bc, src);
    int ok = 1;

    if (!s) {
        push_diag(bc, DIAG_ERROR, OP_MOVE, src, bc->event_count,
            "move from unknown '%s'", src);
        ok = 0;
    } else if (s->is_copy) {
        push_diag(bc, DIAG_NOTE, OP_MOVE, src, s->cause_event,
            "'%s' is Copy; this is a copy, not a move", src);
        bc_copy(bc, dst, src);
        return;
    } else if (s->state == VS_MOVED) {
        push_diag(bc, DIAG_ERROR, OP_MOVE, src, s->cause_event,
            "use after move: '%s' moved at event #%d", src, s->cause_event + 1);
        ok = 0;
    } else if (s->state == VS_DROPPED) {
        push_diag(bc, DIAG_ERROR, OP_MOVE, src, s->cause_event,
            "use after free: '%s' dropped at event #%d", src, s->cause_event + 1);
        ok = 0;
    } else if (s->state == VS_PARTIALLY_MOVED) {
        push_diag(bc, DIAG_ERROR, OP_MOVE, src, s->cause_event,
            "cannot move '%s': it is partially moved (%d field(s) already moved)",
            src, s->moved_field_count);
        ok = 0;
    } else if (s->shared_count > 0 || s->mut_count > 0) {
        int bev = bc->event_count;
        for (int j = 0; j < bc->borrow_count; j++) {
            Borrow *b = &bc->borrows[j];
            if (b->state == BS_ACTIVE && b->target_var_id == s->id) {
                bev = b->cause_event; break;
            }
        }
        push_diag(bc, DIAG_ERROR, OP_MOVE, src, bev,
            "cannot move '%s': borrowed (%d shared, %d mutable; from event #%d)",
            src, s->shared_count, s->mut_count, bev + 1);
        ok = 0;
    }

    if (ok) {
        if (bc->var_count >= BC_MAX_VARS) {
            push_diag(bc, DIAG_ERROR, OP_MOVE, dst, bc->event_count,
                "variable table full");
            ok = 0;
        } else {
            Var *d = alloc_var(bc, dst, s->is_mut, s->res_kind);
            d->id         = s->id;
            d->generation = s->generation;
            d->region_id  = s->region_id;
            s->state      = VS_MOVED;
            /* re-point defers */
            for (int df = 0; df < bc->defer_count; df++)
                if (strcmp(bc->defers[df].var_name, src) == 0
                        && !bc->defers[df].satisfied)
                    strncpy(bc->defers[df].var_name, dst, BC_MAX_NAME - 1);
        }
    }
    push_event(bc, OP_MOVE, src, dst, 0, 0, bc->scope, ok);
}

void bc_copy(BC *bc, const char *dst, const char *src) {
    Var *s = find_var_mut(bc, src);
    int ok = 1;

    if (!s) {
        push_diag(bc, DIAG_ERROR, OP_COPY, src, bc->event_count,
            "copy from unknown '%s'", src);
        ok = 0;
    } else if (s->state != VS_ALIVE) {
        push_diag(bc, DIAG_ERROR, OP_COPY, src, s->cause_event,
            "copy of %s variable '%s'", bc_var_state_name(s->state), src);
        ok = 0;
    }
    if (ok) {
        Var *d = alloc_var(bc, dst, 0, RK_PLAIN);
        if (!d) {
            push_diag(bc, DIAG_ERROR, OP_COPY, dst, bc->event_count,
                "variable table full");
            ok = 0;
        } else {
            d->is_copy = s->is_copy;
        }
    }
    push_event(bc, OP_COPY, src, dst, 0, 0, bc->scope, ok);
}

void bc_field_move(BC *bc, const char *dst, const char *src,
                   const char *field)
{
    Var *s = find_var_mut(bc, src);
    int ok = 1;

    if (!s) {
        push_diag(bc, DIAG_ERROR, OP_FIELD_MOVE, src, bc->event_count,
            "field_move from unknown '%s'", src);
        ok = 0;
    } else if (s->state == VS_MOVED || s->state == VS_DROPPED) {
        push_diag(bc, DIAG_ERROR, OP_FIELD_MOVE, src, s->cause_event,
            "field_move from %s variable '%s'",
            bc_var_state_name(s->state), src);
        ok = 0;
    } else {
        /* check this field hasn't already been moved */
        for (int f = 0; f < s->moved_field_count; f++) {
            if (strcmp(s->moved_fields[f], field) == 0) {
                push_diag(bc, DIAG_ERROR, OP_FIELD_MOVE, src, s->cause_event,
                    "field '%s' of '%s' has already been moved out",
                    field, src);
                ok = 0;
                break;
            }
        }
    }

    if (ok && s) {
        /* create dst as the moved-out field */
        Var *d = alloc_var(bc, dst, 0, RK_PLAIN);
        if (!d) {
            push_diag(bc, DIAG_ERROR, OP_FIELD_MOVE, dst, bc->event_count,
                "variable table full");
            ok = 0;
        } else {
            /* record field as moved in src */
            if (s->moved_field_count < BC_MAX_FIELDS)
                strncpy(s->moved_fields[s->moved_field_count++], field,
                        BC_MAX_NAME - 1);
            s->state = VS_PARTIALLY_MOVED;
        }
    }
    /* b holds the field name for the renderer */
    push_event(bc, OP_FIELD_MOVE, src, field, 0, 0, bc->scope, ok);
    (void)dst;
}

void bc_drop(BC *bc, const char *name) {
    Var *v = find_var_mut(bc, name);
    int ok = 1;

    if (!v) {
        push_diag(bc, DIAG_ERROR, OP_DROP, name, bc->event_count,
            "drop of unknown '%s'", name);
        ok = 0;
    } else if (v->state == VS_DROPPED) {
        push_diag(bc, DIAG_ERROR, OP_DROP, name, v->cause_event,
            "double free: '%s' already dropped (event #%d)",
            name, v->cause_event + 1);
        ok = 0;
    } else if (v->state == VS_MOVED) {
        push_diag(bc, DIAG_ERROR, OP_DROP, name, v->cause_event,
            "drop of moved value '%s' (moved at event #%d)",
            name, v->cause_event + 1);
        ok = 0;
    }
    if (ok) {
        for (int d = 0; d < bc->defer_count; d++)
            if (strcmp(bc->defers[d].var_name, name) == 0)
                bc->defers[d].satisfied = 1;
        drop_var(bc, v, OP_DROP);
    }
    push_event(bc, OP_DROP, name, NULL, 0, 0, bc->scope, ok);
}

/* -- common use validation shared by bc_use and bc_use_write -- */
static int validate_name_live(BC *bc, const char *name, OpKind op,
                               Var **out_v, Borrow **out_b)
{
    *out_v = find_var_mut(bc, name);
    *out_b = find_borrow_mut(bc, name);

    if (*out_v) {
        if ((*out_v)->state == VS_MOVED) {
            push_diag(bc, DIAG_ERROR, op, name, (*out_v)->cause_event,
                "use after move: '%s' moved at event #%d",
                name, (*out_v)->cause_event + 1);
            return 0;
        }
        if ((*out_v)->state == VS_DROPPED) {
            push_diag(bc, DIAG_ERROR, op, name, (*out_v)->cause_event,
                "use after free: '%s' dropped at event #%d",
                name, (*out_v)->cause_event + 1);
            return 0;
        }
        return 1;
    }
    if (*out_b) {
        if ((*out_b)->state == BS_DANGLING) {
            push_diag(bc, DIAG_ERROR, op, name, (*out_b)->cause_event,
                "use of dangling borrow '%s' (from event #%d)",
                name, (*out_b)->cause_event + 1);
            return 0;
        }
        if ((*out_b)->state == BS_RELEASED) {
            push_diag(bc, DIAG_ERROR, op, name, (*out_b)->cause_event,
                "use of released borrow '%s' (from event #%d)",
                name, (*out_b)->cause_event + 1);
            return 0;
        }
        if ((*out_b)->state == BS_RESERVED) {
            push_diag(bc, DIAG_WARNING, op, name, (*out_b)->cause_event,
                "use of two-phase reserved borrow '%s' before activation",
                name);
            /* not fatal - allow read use */
        }
        return 1;
    }
    push_diag(bc, DIAG_ERROR, op, name, bc->event_count,
        "use of undeclared name '%s'", name);
    return 0;
}

void bc_use(BC *bc, const char *name) {
    Var *v; Borrow *b;
    int ok = validate_name_live(bc, name, OP_USE, &v, &b);
    /* NLL: if borrow had a last_use already recorded, it's now dead */
    if (ok && b && b->last_use_event != -1
            && bc->event_count > b->last_use_event) {
        push_diag(bc, DIAG_ERROR, OP_USE, name, b->last_use_event,
            "use of borrow '%s' after its NLL last-use point (event #%d)",
            name, b->last_use_event + 1);
        ok = 0;
    }
    push_event(bc, OP_USE, name, NULL, (int)UK_READ, 0, bc->scope, ok);
}

void bc_use_write(BC *bc, const char *name) {
    Var *v; Borrow *b;
    int ok = validate_name_live(bc, name, OP_USE_WRITE, &v, &b);

    if (ok) {
        if (v) {
            /* writing to an owned variable - must be mutable */
            if (!v->is_mut && !v->is_interior_mut) {
                push_diag(bc, DIAG_ERROR, OP_USE_WRITE, name, v->cause_event,
                    "cannot write to immutable variable '%s' "
                    "(declared at event #%d)", name, v->cause_event + 1);
                ok = 0;
            }
        } else if (b) {
            /* writing through a borrow - must be &mut */
            if (b->kind == BK_SHARED) {
                /* interior mutability exception */
                Var *tgt = NULL;
                for (int i = 0; i < bc->var_count; i++)
                    if (bc->vars[i].id == b->target_var_id) {
                        tgt = &bc->vars[i]; break;
                    }
                if (tgt && tgt->is_interior_mut) {
                    push_diag(bc, DIAG_NOTE, OP_USE_WRITE, name,
                        b->cause_event,
                        "write through shared borrow '%s' of interior-mutable "
                        "target: static check bypassed, runtime check applies",
                        name);
                } else {
                    push_diag(bc, DIAG_ERROR, OP_USE_WRITE, name,
                        b->cause_event,
                        "cannot write through shared borrow '%s' (&T is read-only; "
                        "borrow from event #%d)",
                        name, b->cause_event + 1);
                    ok = 0;
                }
            }
            /* BK_UNIQUE or BK_MUTABLE: write is fine */
        }
    }
    push_event(bc, OP_USE_WRITE, name, NULL, (int)UK_WRITE, 0, bc->scope, ok);
}

/*
 * Borrow core
 */

static Borrow *create_borrow(BC *bc, const char *ref_name, int target_id,
                              BorrowKind kind, BorrowState initial_state,
                              int region_id, int lo, int hi)
{
    if (bc->borrow_count >= BC_MAX_BORROWS) return NULL;
    Borrow *b = &bc->borrows[bc->borrow_count++];
    memset(b, 0, sizeof *b);
    strncpy(b->name, ref_name, BC_MAX_NAME - 1);
    b->id                = bc->next_borrow_id++;
    b->target_var_id     = target_id;
    b->kind              = kind;
    b->state             = initial_state;
    b->scope             = bc->scope;
    b->cause_event       = bc->event_count;
    b->last_use_event    = -1;
    b->region_id         = region_id;
    b->is_slice          = (lo != 0 || hi != 0);
    b->slice_lo          = lo;
    b->slice_hi          = hi;
    return b;
}

/* check for slice overlap with existing borrows of the same target */
static int slice_conflicts(BC *bc, int target_id, int lo, int hi,
                            BorrowKind new_kind)
{
    for (int j = 0; j < bc->borrow_count; j++) {
        Borrow *b = &bc->borrows[j];
        if (b->state != BS_ACTIVE && b->state != BS_RESERVED) continue;
        if (b->target_var_id != target_id) continue;
        if (!b->is_slice) return 1; /* whole-object borrow conflicts */
        /* ranges overlap if lo < b->hi && b->lo < hi */
        if (lo < b->slice_hi && b->slice_lo < hi) {
            /* shared+shared is fine unless one is mutable */
            if (new_kind == BK_SHARED && b->kind == BK_SHARED) continue;
            return 1;
        }
    }
    return 0;
}

static void borrow_impl(BC *bc, const char *ref_name, const char *target,
                         BorrowKind kind, OpKind op,
                         BorrowState initial_state,
                         int region_id, int lo, int hi)
{
    Var *tgt = find_var_mut(bc, target);
    int ok = 1;

    if (!tgt) {
        push_diag(bc, DIAG_ERROR, op, target, bc->event_count,
            "borrow of unknown '%s'", target);
        ok = 0;
    } else if (tgt->state != VS_ALIVE && tgt->state != VS_PARTIALLY_MOVED) {
        push_diag(bc, DIAG_ERROR, op, target, tgt->cause_event,
            "cannot borrow '%s': it is %s (event #%d)",
            target, bc_var_state_name(tgt->state), tgt->cause_event + 1);
        ok = 0;
    } else if (kind == BK_MUTABLE && !tgt->is_mut && !tgt->is_interior_mut) {
        push_diag(bc, DIAG_ERROR, op, target, tgt->cause_event,
            "cannot borrow immutable '%s' as &mut (event #%d)",
            target, tgt->cause_event + 1);
        ok = 0;
    } else if (initial_state == BS_ACTIVE) {
        /* full conflict check - two-phase reserved borrows skip this */
        int is_slice = (lo != 0 || hi != 0);
        if (is_slice) {
            if (slice_conflicts(bc, tgt->id, lo, hi, kind)) {
                push_diag(bc, DIAG_ERROR, op, target, bc->event_count,
                    "slice borrow [%d,%d) of '%s' conflicts with existing borrow",
                    lo, hi, target);
                ok = 0;
            }
        } else if (kind == BK_MUTABLE && tgt->shared_count > 0) {
            int fev = bc->event_count;
            for (int j = 0; j < bc->borrow_count; j++) {
                Borrow *b = &bc->borrows[j];
                if (b->state == BS_ACTIVE && b->target_var_id == tgt->id
                        && b->kind == BK_SHARED) {
                    fev = b->cause_event; break;
                }
            }
            push_diag(bc, DIAG_ERROR, op, target, fev,
                "conflict: '%s' has %d shared borrow(s); cannot create &mut "
                "(first shared borrow at event #%d)",
                target, tgt->shared_count, fev + 1);
            ok = 0;
        } else if (kind == BK_MUTABLE && tgt->mut_count > 0) {
            int mev = bc->event_count;
            for (int j = 0; j < bc->borrow_count; j++) {
                Borrow *b = &bc->borrows[j];
                if (b->state == BS_ACTIVE && b->target_var_id == tgt->id
                        && b->kind == BK_MUTABLE) {
                    mev = b->cause_event; break;
                }
            }
            push_diag(bc, DIAG_ERROR, op, target, mev,
                "conflict: '%s' already &mut borrowed (from event #%d)",
                target, mev + 1);
            ok = 0;
        } else if (kind == BK_SHARED && tgt->mut_count > 0) {
            int mev = bc->event_count;
            for (int j = 0; j < bc->borrow_count; j++) {
                Borrow *b = &bc->borrows[j];
                if (b->state == BS_ACTIVE && b->target_var_id == tgt->id
                        && b->kind == BK_MUTABLE) {
                    mev = b->cause_event; break;
                }
            }
            push_diag(bc, DIAG_ERROR, op, target, mev,
                "conflict: '%s' is &mut borrowed; cannot create &T "
                "(mut borrow from event #%d)", target, mev + 1);
            ok = 0;
        }
    }

    if (ok) {
        if (bc->borrow_count >= BC_MAX_BORROWS) {
            push_diag(bc, DIAG_ERROR, op, ref_name, bc->event_count,
                "borrow table full");
            ok = 0;
        } else {
            Borrow *b = create_borrow(bc, ref_name, tgt->id, kind,
                                      initial_state, region_id, lo, hi);
            if (b) {
                b->target_generation = tgt->generation;
                /* reserved borrows don't yet count against the target */
                if (initial_state == BS_ACTIVE) {
                    if (kind == BK_SHARED) tgt->shared_count++;
                    else                   tgt->mut_count++;
                }
            }
        }
    }
    push_event(bc, op, ref_name, target, lo, hi, bc->scope, ok);
}

void bc_borrow    (BC *bc, const char *r, const char *t) {
    borrow_impl(bc, r, t, BK_SHARED,  OP_BORROW,     BS_ACTIVE,  -1, 0, 0);
}
void bc_borrow_mut(BC *bc, const char *r, const char *t) {
    borrow_impl(bc, r, t, BK_MUTABLE, OP_BORROW_MUT, BS_ACTIVE,  -1, 0, 0);
}
void bc_borrow_slice(BC *bc, const char *r, const char *t, int lo, int hi) {
    borrow_impl(bc, r, t, BK_SHARED,  OP_BORROW_SLICE,     BS_ACTIVE, -1, lo, hi);
}
void bc_borrow_mut_slice(BC *bc, const char *r, const char *t, int lo, int hi) {
    borrow_impl(bc, r, t, BK_MUTABLE, OP_BORROW_MUT_SLICE, BS_ACTIVE, -1, lo, hi);
}

void bc_borrow_in_region(BC *bc, const char *r, const char *t,
                          const char *region_name)
{
    Region *rg = find_region_mut(bc, region_name);
    int rid = rg ? rg->id : -1;
    if (!rg)
        push_diag(bc, DIAG_ERROR, OP_BORROW, r, bc->event_count,
            "borrow_in_region: unknown region '%s'", region_name);
    borrow_impl(bc, r, t, BK_SHARED,  OP_BORROW,     BS_ACTIVE, rid, 0, 0);
}

void bc_borrow_mut_in_region(BC *bc, const char *r, const char *t,
                              const char *region_name)
{
    Region *rg = find_region_mut(bc, region_name);
    int rid = rg ? rg->id : -1;
    if (!rg)
        push_diag(bc, DIAG_ERROR, OP_BORROW_MUT, r, bc->event_count,
            "borrow_mut_in_region: unknown region '%s'", region_name);
    borrow_impl(bc, r, t, BK_MUTABLE, OP_BORROW_MUT, BS_ACTIVE, rid, 0, 0);
}

/* -- two-phase borrows -- */

void bc_two_phase_reserve(BC *bc, const char *ref_name, const char *target) {
    /* reserve: creates the borrow in BS_RESERVED state; conflicts skipped */
    borrow_impl(bc, ref_name, target, BK_MUTABLE, OP_TWO_PHASE_RESERVE,
                BS_RESERVED, -1, 0, 0);
}

void bc_two_phase_activate(BC *bc, const char *ref_name) {
    Borrow *b = find_borrow_mut(bc, ref_name);
    int ok = 1;

    if (!b) {
        push_diag(bc, DIAG_ERROR, OP_TWO_PHASE_ACTIVATE, ref_name,
            bc->event_count, "activate: unknown borrow '%s'", ref_name);
        ok = 0;
    } else if (b->state != BS_RESERVED) {
        push_diag(bc, DIAG_ERROR, OP_TWO_PHASE_ACTIVATE, ref_name,
            b->cause_event,
            "activate: borrow '%s' is %s, not reserved",
            ref_name, bc_borrow_state_name(b->state));
        ok = 0;
    }

    if (ok && b) {
        /* now apply full conflict check */
        Var *tgt = NULL;
        for (int i = 0; i < bc->var_count; i++)
            if (bc->vars[i].id == b->target_var_id) { tgt = &bc->vars[i]; break; }

        if (tgt && (tgt->shared_count > 0 || tgt->mut_count > 0)) {
            push_diag(bc, DIAG_ERROR, OP_TWO_PHASE_ACTIVATE, ref_name,
                b->cause_event,
                "two-phase activate: '%s' still has active borrows "
                "(%d shared, %d mutable); cannot activate &mut",
                tgt->name, tgt->shared_count, tgt->mut_count);
            ok = 0;
        }
        if (ok && tgt) {
            b->state = BS_ACTIVE;
            tgt->mut_count++;
        }
    }
    push_event(bc, OP_TWO_PHASE_ACTIVATE, ref_name, NULL, 0, 0, bc->scope, ok);
}

/* -- NLL last-use -- */

void bc_last_use(BC *bc, const char *ref_name) {
    Borrow *b = find_borrow_mut(bc, ref_name);
    int ok = 1;

    if (!b) {
        push_diag(bc, DIAG_ERROR, OP_LAST_USE, ref_name, bc->event_count,
            "last_use: unknown borrow '%s'", ref_name);
        ok = 0;
    } else if (b->state != BS_ACTIVE) {
        push_diag(bc, DIAG_WARNING, OP_LAST_USE, ref_name, b->cause_event,
            "last_use on non-active borrow '%s'", ref_name);
    } else {
        b->last_use_event = bc->event_count;
        /* Immediately free the counts so the target can be re-borrowed */
        dec_borrow_counts(bc, b);
        /* We keep state as BS_RELEASED so subsequent use emits an error */
    }
    push_event(bc, OP_LAST_USE, ref_name, NULL, 0, 0, bc->scope, ok);
}

/* -- reborrow -- */

void bc_reborrow(BC *bc, const char *new_ref, const char *src_ref) {
    Borrow *src = find_borrow_mut(bc, src_ref);
    int ok = 1;

    if (!src) {
        push_diag(bc, DIAG_ERROR, OP_REBORROW, src_ref, bc->event_count,
            "reborrow of unknown borrow '%s'", src_ref);
        ok = 0;
    } else if (src->state != BS_ACTIVE) {
        push_diag(bc, DIAG_ERROR, OP_REBORROW, src_ref, src->cause_event,
            "reborrow of %s borrow '%s' (event #%d)",
            bc_borrow_state_name(src->state), src_ref, src->cause_event + 1);
        ok = 0;
    }

    if (ok) {
        Var *tgt = NULL;
        for (int i = 0; i < bc->var_count; i++)
            if (bc->vars[i].id == src->target_var_id) { tgt = &bc->vars[i]; break; }
        if (!tgt || tgt->state != VS_ALIVE) {
            push_diag(bc, DIAG_ERROR, OP_REBORROW, src_ref, src->cause_event,
                "reborrow: target of '%s' is gone", src_ref);
            ok = 0;
        } else if (bc->borrow_count >= BC_MAX_BORROWS) {
            push_diag(bc, DIAG_ERROR, OP_REBORROW, new_ref, bc->event_count,
                "borrow table full");
            ok = 0;
        } else {
            Borrow *nb = create_borrow(bc, new_ref, src->target_var_id,
                                       src->kind, BS_ACTIVE,
                                       src->region_id, 0, 0);
            if (nb) {
                nb->target_generation = src->target_generation;
                if (src->kind == BK_SHARED) tgt->shared_count++;
                else                        tgt->mut_count++;
            }
        }
    }
    push_event(bc, OP_REBORROW, new_ref, src_ref, 0, 0, bc->scope, ok);
}

void bc_release(BC *bc, const char *ref_name) {
    Borrow *b = find_borrow_mut(bc, ref_name);
    int ok = 1;

    if (!b) {
        push_diag(bc, DIAG_ERROR, OP_RELEASE, ref_name, bc->event_count,
            "release of unknown borrow '%s'", ref_name);
        ok = 0;
    } else if (b->state == BS_RELEASED) {
        push_diag(bc, DIAG_WARNING, OP_RELEASE, ref_name, b->cause_event,
            "redundant release of '%s' (already released at event #%d)",
            ref_name, b->cause_event + 1);
        ok = 0;
    } else if (b->state == BS_DANGLING) {
        push_diag(bc, DIAG_ERROR, OP_RELEASE, ref_name, b->cause_event,
            "cannot release dangling borrow '%s'", ref_name);
        ok = 0;
    } else if (b->state == BS_RESERVED) {
        /* releasing a reserved borrow is fine - just discard */
        b->state = BS_RELEASED;
    }

    if (ok && b->state == BS_ACTIVE) dec_borrow_counts(bc, b);
    push_event(bc, OP_RELEASE, ref_name, NULL, 0, 0, bc->scope, ok);
}

/*
 * Resources
 */

void bc_resource_acquire(BC *bc, const char *name, ResourceKind kind) {
    int ok = 1;
    Resource *ex = find_resource_mut(bc, name);
    if (ex && !ex->is_released) {
        push_diag(bc, DIAG_WARNING, OP_RESOURCE_ACQUIRE, name,
            ex->acquire_event,
            "re-acquiring '%s' while previous %s still open (event #%d)",
            name, bc_resource_kind_name(ex->kind), ex->acquire_event + 1);
    }
    if (bc->var_count >= BC_MAX_VARS || bc->resource_count >= BC_MAX_RESOURCES) {
        push_diag(bc, DIAG_ERROR, OP_RESOURCE_ACQUIRE, name, bc->event_count,
            "table full");
        ok = 0;
    }
    if (ok) {
        alloc_var(bc, name, 0, kind);
        Resource *res     = &bc->resources[bc->resource_count++];
        memset(res, 0, sizeof *res);
        res->id           = bc->next_resource_id++;
        strncpy(res->var_name, name, BC_MAX_NAME - 1);
        res->kind         = kind;
        res->scope        = bc->scope;
        res->acquire_event = bc->event_count;
        res->release_event = -1;
    }
    push_event(bc, OP_RESOURCE_ACQUIRE, name, NULL, 0, 0, bc->scope, ok);
}

void bc_resource_release(BC *bc, const char *name) {
    Resource *res = find_resource_mut(bc, name);
    Var      *v   = find_var_mut(bc, name);
    int ok = 1;

    if (!res) {
        push_diag(bc, DIAG_ERROR, OP_RESOURCE_RELEASE, name, bc->event_count,
            "release of unknown resource '%s'", name);
        ok = 0;
    } else if (res->is_released) {
        push_diag(bc, DIAG_ERROR, OP_RESOURCE_RELEASE, name,
            res->acquire_event,
            "double-release of %s '%s' "
            "(first at event #%d, acquired at event #%d)",
            bc_resource_kind_name(res->kind), name,
            res->release_event + 1, res->acquire_event + 1);
        ok = 0;
    }
    if (ok) {
        res->is_released   = 1;
        res->release_event = bc->event_count;
        for (int d = 0; d < bc->defer_count; d++)
            if (strcmp(bc->defers[d].var_name, name) == 0)
                bc->defers[d].satisfied = 1;
        if (v) drop_var(bc, v, OP_RESOURCE_RELEASE);
    }
    push_event(bc, OP_RESOURCE_RELEASE, name, NULL, 0, 0, bc->scope, ok);
}

/*
 * Defer / linear
 */

void bc_defer(BC *bc, const char *name) {
    if (bc->defer_count >= BC_MAX_DEFERS) {
        push_diag(bc, DIAG_ERROR, OP_DEFER, name, bc->event_count,
            "defer table full");
        push_event(bc, OP_DEFER, name, NULL, 0, 0, bc->scope, 0);
        return;
    }
    Defer *d = &bc->defers[bc->defer_count++];
    strncpy(d->var_name, name, BC_MAX_NAME - 1);
    d->scope          = bc->scope;
    d->satisfied      = 0;
    d->register_event = bc->event_count;
    push_event(bc, OP_DEFER, name, NULL, 0, 0, bc->scope, 1);
}

void bc_assert_consumed(BC *bc, const char *name) {
    Var *v = find_var_mut(bc, name);
    int ok = 1;
    if (!v) {
        push_diag(bc, DIAG_ERROR, OP_ASSERT_CONSUMED, name, bc->event_count,
            "assert_consumed: unknown '%s'", name);
        ok = 0;
    } else if (v->state == VS_ALIVE) {
        push_diag(bc, DIAG_ERROR, OP_ASSERT_CONSUMED, name, v->cause_event,
            "assert_consumed: '%s' still alive (event #%d) "
            "- language requires it be consumed here",
            name, v->cause_event + 1);
        ok = 0;
    }
    push_event(bc, OP_ASSERT_CONSUMED, name, NULL, 0, 0, bc->scope, ok);
}
