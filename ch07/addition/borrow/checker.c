/*
 * checker.c  -  Borrow and resource checker implementation.  Zero I/O.
 *
 * Every public bc_* function follows the same three-phase contract:
 *   1. VALIDATE  - inspect live state, push Diag(s) for violations.
 *   2. MUTATE    - update live state only if the operation is legal.
 *   3. SNAPSHOT  . push an Event (full state copy) to the history log.
 *
 * The event log is append-only and never mutated after writing.
 * The diagram layer reads bc->events[] and bc->diags[]; it never calls
 * any bc_* function.
 *
 * Drop-order enforcement
 * ----------------------
 * Each Var carries a decl_order field set at declaration time from
 * scope_decl_order[current_scope].  At scope exit we drop vars in
 * descending decl_order (i.e. reverse declaration order), exactly as
 * Rust does.  Any borrow whose target has a lower decl_order than the
 * borrow itself will be dangling when the target drops first; we detect
 * this at scope_exit.
 *
 * Resource leak detection
 * -----------------------
 * bc_resource_acquire creates both a Var and a Resource record.
 * At scope exit, any Resource in this scope that is not released (and
 * not registered as a defer that was satisfied) emits a DIAG_ERROR
 * naming the resource kind, before the drop pass runs.
 *
 * Defer verification
 * ------------------
 * bc_defer(bc, name) registers that <name> MUST be released by the time
 * the current scope exits.  bc_scope_exit checks that every Defer for
 * this scope has satisfied == 1.  Unsatisfied defers are errors.
 * This lets a language front-end model try/finally, RAII, or
 * explicit cleanup blocks and have the checker verify completeness.
 */

#include "checker.h"
#include <string.h>
#include <stdio.h>
#include <stdarg.h>

/* 
 * Name table helpers
 */

const char *bc_var_state_name(VarState s) {
    switch (s) {
        case VS_ALIVE:            return "alive";
        case VS_MOVED:            return "moved";
        case VS_DROPPED:          return "dropped";
        case VS_PARTIALLY_MOVED:  return "partially-moved";
    }
    return "unknown";
}

const char *bc_borrow_kind_name(BorrowKind k) {
    switch (k) {
        case BK_SHARED:   return "&T";
        case BK_MUTABLE:  return "&mut T";
        case BK_UNIQUE:   return "&unique T";
    }
    return "?";
}

const char *bc_resource_kind_name(ResourceKind k) {
    switch (k) {
        case RK_PLAIN:   return "value";
        case RK_HEAP:    return "HeapAlloc";
        case RK_FILE:    return "FileHandle";
        case RK_SOCKET:  return "Socket";
        case RK_LOCK:    return "Lock";
        case RK_CUSTOM:  return "Resource";
    }
    return "?";
}

const char *bc_op_name(OpKind op) {
    switch (op) {
        case OP_SCOPE_ENTER:       return "SCOPE ENTER";
        case OP_SCOPE_EXIT:        return "SCOPE EXIT";
        case OP_DECLARE:           return "DECLARE";
        case OP_DECLARE_COPY:      return "DECLARE (Copy)";
        case OP_MOVE:              return "MOVE";
        case OP_COPY:              return "COPY";
        case OP_ASSIGN:            return "ASSIGN";
        case OP_DROP:              return "DROP";
        case OP_BORROW:            return "BORROW &";
        case OP_BORROW_MUT:        return "BORROW &mut";
        case OP_RELEASE:           return "RELEASE";
        case OP_USE:               return "USE";
        case OP_REBORROW:          return "REBORROW";
        case OP_RESOURCE_ACQUIRE:  return "ACQUIRE";
        case OP_RESOURCE_RELEASE:  return "RELEASE_RES";
        case OP_DEFER:             return "DEFER";
        case OP_ASSERT_CONSUMED:   return "ASSERT_CONSUMED";
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

static Resource *find_resource_mut(BC *bc, const char *var_name) {
    for (int r = bc->resource_count - 1; r >= 0; r--)
        if (strcmp(bc->resources[r].var_name, var_name) == 0)
            return &bc->resources[r];
    return NULL;
}

const Var *bc_find_var(const BC *bc, const char *name) {
    for (int i = bc->var_count - 1; i >= 0; i--)
        if (strcmp(bc->vars[i].name, name) == 0)
            return &bc->vars[i];
    return NULL;
}

const Borrow *bc_find_borrow(const BC *bc, const char *name) {
    for (int j = bc->borrow_count - 1; j >= 0; j--)
        if (strcmp(bc->borrows[j].name, name) == 0)
            return &bc->borrows[j];
    return NULL;
}

const Resource *bc_find_resource(const BC *bc, const char *var_name) {
    for (int r = bc->resource_count - 1; r >= 0; r--)
        if (strcmp(bc->resources[r].var_name, var_name) == 0)
            return &bc->resources[r];
    return NULL;
}

/*
 * Diagnostic helpers
 */

static Diag *push_diag(BC *bc, DiagLevel level, OpKind op,
                        const char *subject,
                        int cause_event,
                        const char *fmt, ...)
{
    if (bc->diag_count >= BC_MAX_DIAGS) return NULL;
    Diag *d = &bc->diags[bc->diag_count++];
    d->level        = level;
    d->op           = op;
    d->cause_event  = cause_event;
    d->detect_event = bc->event_count;  /* filled in by push_event */
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
                        int scope_before, int ok)
{
    if (bc->event_count >= BC_MAX_EVENTS) return;
    Event *ev = &bc->events[bc->event_count];

    ev->index        = bc->event_count + 1;
    ev->op           = op;
    ev->scope_before = scope_before;
    ev->scope_after  = bc->scope;
    ev->scope        = bc->scope;
    ev->ok           = ok;
    strncpy(ev->a, a ? a : "", BC_MAX_NAME - 1);
    strncpy(ev->b, b ? b : "", BC_MAX_NAME - 1);

    ev->var_count      = bc->var_count;
    ev->borrow_count   = bc->borrow_count;
    ev->resource_count = bc->resource_count;
    memcpy(ev->vars,      bc->vars,      sizeof(Var)      * (size_t)bc->var_count);
    memcpy(ev->borrows,   bc->borrows,   sizeof(Borrow)   * (size_t)bc->borrow_count);
    memcpy(ev->resources, bc->resources, sizeof(Resource) * (size_t)bc->resource_count);

    /* patch detect_event on all pending diags */
    for (int d = 0; d < bc->diag_count; d++)
        if (bc->diags[d].detect_event == bc->event_count)
            bc->diags[d].detect_event = bc->event_count;

    bc->event_count++;
}

/*
 * Internal drop helpers
 */

static void release_borrow_counts(BC *bc, Borrow *b) {
    for (int i = 0; i < bc->var_count; i++) {
        if (bc->vars[i].id == b->target_var_id) {
            if (b->kind == BK_SHARED) bc->vars[i].shared_count--;
            else                      bc->vars[i].mut_count--;
            break;
        }
    }
    b->state = BS_RELEASED;
}

static void mark_borrows_dangling(BC *bc, const Var *v, OpKind trigger_op) {
    for (int j = 0; j < bc->borrow_count; j++) {
        Borrow *b = &bc->borrows[j];
        if (b->state != BS_ACTIVE || b->target_var_id != v->id) continue;
        push_diag(bc, DIAG_ERROR, trigger_op, b->name,
            b->cause_event,
            "dangling %s borrow '%s' of '%s': target is dropped "
            "(borrow created at event #%d)",
            bc_borrow_kind_name(b->kind),
            b->name, v->name, b->cause_event + 1);
        /* emit a note pointing back to the borrow origin */
        push_diag(bc, DIAG_NOTE, trigger_op, b->name,
            b->cause_event,
            "borrow '%s' was created here (event #%d)",
            b->name, b->cause_event + 1);
        b->state = BS_DANGLING;
    }
}

/* Drop a variable; returns 1 if any borrows were made dangling. */
static int drop_var(BC *bc, Var *v, OpKind trigger_op) {
    if (v->state != VS_ALIVE) return 0;
    mark_borrows_dangling(bc, v, trigger_op);

    /* If this variable is a resource, check it was released */
    Resource *res = find_resource_mut(bc, v->name);
    if (res && !res->is_released) {
        push_diag(bc, DIAG_ERROR, trigger_op, v->name,
            res->acquire_event,
            "%s '%s' leaked: acquired at event #%d but never released",
            bc_resource_kind_name(res->kind), v->name,
            res->acquire_event + 1);
    }

    v->state = VS_DROPPED;
    return 1;
}

/*
 * Scope
 */

void bc_init(BC *bc) {
    memset(bc, 0, sizeof *bc);
    bc->next_var_id      = 1;
    bc->next_borrow_id   = 1;
    bc->next_resource_id = 1;
    for (int i = 0; i < BC_MAX_SCOPES; i++)
        bc->scope_decl_order[i] = 0;
}

void bc_scope_enter(BC *bc) {
    int before = bc->scope;
    if (bc->scope < BC_MAX_SCOPES - 1) {
        bc->scope++;
        bc->scope_decl_order[bc->scope] = 0;
    } else {
        push_diag(bc, DIAG_ERROR, OP_SCOPE_ENTER, NULL, bc->event_count,
            "scope depth limit (%d) exceeded", BC_MAX_SCOPES);
    }
    push_event(bc, OP_SCOPE_ENTER, NULL, NULL, before, 1);
}

void bc_scope_exit(BC *bc) {
    if (bc->scope == 0) {
        push_diag(bc, DIAG_ERROR, OP_SCOPE_EXIT, NULL, bc->event_count,
            "scope_exit with no matching scope_enter");
        push_event(bc, OP_SCOPE_EXIT, NULL, NULL, 0, 0);
        return;
    }
    int before = bc->scope;

    /* -- phase 1: verify deferred releases -------------------------------- */
    for (int d = 0; d < bc->defer_count; d++) {
        Defer *df = &bc->defers[d];
        if (df->scope != bc->scope) continue;
        if (!df->satisfied) {
            push_diag(bc, DIAG_ERROR, OP_SCOPE_EXIT, df->var_name,
                df->register_event,
                "deferred release of '%s' was not satisfied before scope exit "
                "(registered at event #%d)",
                df->var_name, df->register_event + 1);
        }
    }

    /* -- phase 2: release borrows created in this scope ------------------- */
    for (int j = 0; j < bc->borrow_count; j++) {
        Borrow *b = &bc->borrows[j];
        if (b->state == BS_ACTIVE && b->scope == bc->scope)
            release_borrow_counts(bc, b);
    }

    /* -- phase 3: drop vars in reverse declaration order ------------------ */
    /*
     * We collect the vars for this scope, sort by descending decl_order,
     * then drop.  This gives deterministic LIFO semantics.
     */
    int order[BC_MAX_VARS];
    int ncollect = 0;
    for (int i = 0; i < bc->var_count; i++) {
        if (bc->vars[i].scope == bc->scope && bc->vars[i].state == VS_ALIVE)
            order[ncollect++] = i;
    }
    /* bubble sort descending by decl_order (ncollect is small) */
    for (int a = 0; a < ncollect - 1; a++) {
        for (int b2 = a + 1; b2 < ncollect; b2++) {
            if (bc->vars[order[a]].decl_order < bc->vars[order[b2]].decl_order) {
                int tmp = order[a]; order[a] = order[b2]; order[b2] = tmp;
            }
        }
    }
    for (int k = 0; k < ncollect; k++)
        drop_var(bc, &bc->vars[order[k]], OP_SCOPE_EXIT);

    bc->scope--;
    push_event(bc, OP_SCOPE_EXIT, NULL, NULL, before, 1);
}

/*
 * Variable operations
 */

static Var *alloc_var(BC *bc, const char *name, int is_mut, ResourceKind rk) {
    if (bc->var_count >= BC_MAX_VARS) return NULL;
    Var *v = &bc->vars[bc->var_count++];
    memset(v, 0, sizeof *v);
    strncpy(v->name, name, BC_MAX_NAME - 1);
    v->id           = bc->next_var_id++;
    v->state        = VS_ALIVE;
    v->scope        = bc->scope;
    v->is_mut       = is_mut;
    v->res_kind     = rk;
    v->generation   = 1;
    v->cause_event  = bc->event_count;
    if (bc->scope < BC_MAX_SCOPES)
        v->decl_order = bc->scope_decl_order[bc->scope]++;
    return v;
}

void bc_declare(BC *bc, const char *name, int is_mut) {
    int ok = 1;
    Var *existing = find_var_mut(bc, name);
    if (existing && existing->state == VS_ALIVE && existing->scope == bc->scope) {
        push_diag(bc, DIAG_WARNING, OP_DECLARE, name, bc->event_count,
            "shadowing live variable '%s' in the same scope", name);
        existing->state = VS_MOVED;
    }
    if (bc->var_count >= BC_MAX_VARS) {
        push_diag(bc, DIAG_ERROR, OP_DECLARE, name, bc->event_count,
            "variable table full");
        ok = 0;
    }
    if (ok) alloc_var(bc, name, is_mut, RK_PLAIN);
    push_event(bc, OP_DECLARE, name, NULL, bc->scope, ok);
}

void bc_declare_copy(BC *bc, const char *name) {
    bc_declare(bc, name, 0);
    if (bc->var_count > 0)
        bc->vars[bc->var_count - 1].is_copy = 1;
    if (bc->event_count > 0)
        bc->events[bc->event_count - 1].op = OP_DECLARE_COPY;
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
            "cannot assign to immutable variable '%s' "
            "(declared at event #%d)", name, v->cause_event + 1);
        ok = 0;
    } else if (v->state != VS_ALIVE) {
        push_diag(bc, DIAG_ERROR, OP_ASSIGN, name, v->cause_event,
            "cannot assign to %s variable '%s'",
            bc_var_state_name(v->state), name);
        ok = 0;
    } else if (v->shared_count > 0 || v->mut_count > 0) {
        /* find the borrow that's in the way */
        int borrow_ev = bc->event_count;
        for (int j = 0; j < bc->borrow_count; j++) {
            Borrow *b = &bc->borrows[j];
            if (b->state == BS_ACTIVE && b->target_var_id == v->id)
                borrow_ev = b->cause_event;
        }
        push_diag(bc, DIAG_ERROR, OP_ASSIGN, name, borrow_ev,
            "cannot assign to '%s' while it is borrowed "
            "(%d shared, %d mutable; borrow from event #%d)",
            name, v->shared_count, v->mut_count, borrow_ev + 1);
        ok = 0;
    }
    if (ok) v->generation++;
    push_event(bc, OP_ASSIGN, name, NULL, bc->scope, ok);
}

void bc_move(BC *bc, const char *dst, const char *src) {
    Var *s = find_var_mut(bc, src);
    int ok = 1;

    if (!s) {
        push_diag(bc, DIAG_ERROR, OP_MOVE, src, bc->event_count,
            "move from unknown variable '%s'", src);
        ok = 0;
    } else if (s->is_copy) {
        push_diag(bc, DIAG_NOTE, OP_MOVE, src, s->cause_event,
            "'%s' is a Copy type; this becomes a copy, not a move", src);
        bc_copy(bc, dst, src);
        return;
    } else if (s->state == VS_MOVED) {
        push_diag(bc, DIAG_ERROR, OP_MOVE, src, s->cause_event,
            "use after move: '%s' was already moved out (at event #%d)",
            src, s->cause_event + 1);
        ok = 0;
    } else if (s->state == VS_DROPPED) {
        push_diag(bc, DIAG_ERROR, OP_MOVE, src, s->cause_event,
            "use after free: '%s' was dropped (at event #%d)",
            src, s->cause_event + 1);
        ok = 0;
    } else if (s->shared_count > 0 || s->mut_count > 0) {
        int borrow_ev = bc->event_count;
        for (int j = 0; j < bc->borrow_count; j++) {
            Borrow *b = &bc->borrows[j];
            if (b->state == BS_ACTIVE && b->target_var_id == s->id)
                borrow_ev = b->cause_event;
        }
        push_diag(bc, DIAG_ERROR, OP_MOVE, src, borrow_ev,
            "cannot move '%s': still borrowed "
            "(%d shared, %d mutable — borrow from event #%d)",
            src, s->shared_count, s->mut_count, borrow_ev + 1);
        ok = 0;
    }

    if (ok) {
        if (bc->var_count >= BC_MAX_VARS) {
            push_diag(bc, DIAG_ERROR, OP_MOVE, dst, bc->event_count,
                "variable table full");
            ok = 0;
        } else {
            Var *d = alloc_var(bc, dst, s->is_mut, s->res_kind);
            d->id         = s->id;   /* same underlying slot */
            d->generation = s->generation;
            s->state      = VS_MOVED;
            /* Satisfy any defer on src under the new name */
            for (int df = 0; df < bc->defer_count; df++) {
                Defer *def = &bc->defers[df];
                if (strcmp(def->var_name, src) == 0 && !def->satisfied)
                    strncpy(def->var_name, dst, BC_MAX_NAME - 1);
            }
        }
    }
    push_event(bc, OP_MOVE, src, dst, bc->scope, ok);
}

void bc_copy(BC *bc, const char *dst, const char *src) {
    Var *s = find_var_mut(bc, src);
    int ok = 1;

    if (!s) {
        push_diag(bc, DIAG_ERROR, OP_COPY, src, bc->event_count,
            "copy from unknown variable '%s'", src);
        ok = 0;
    } else if (s->state != VS_ALIVE) {
        push_diag(bc, DIAG_ERROR, OP_COPY, src, s->cause_event,
            "copy of %s variable '%s' (became %s at event #%d)",
            bc_var_state_name(s->state), src,
            bc_var_state_name(s->state), s->cause_event + 1);
        ok = 0;
    }

    if (ok) {
        if (bc->var_count >= BC_MAX_VARS) {
            push_diag(bc, DIAG_ERROR, OP_COPY, dst, bc->event_count,
                "variable table full");
            ok = 0;
        } else {
            Var *d = alloc_var(bc, dst, 0, RK_PLAIN);
            d->is_copy = s->is_copy;
        }
    }
    push_event(bc, OP_COPY, src, dst, bc->scope, ok);
}

void bc_drop(BC *bc, const char *name) {
    Var *v = find_var_mut(bc, name);
    int ok = 1;

    if (!v) {
        push_diag(bc, DIAG_ERROR, OP_DROP, name, bc->event_count,
            "drop of unknown variable '%s'", name);
        ok = 0;
    } else if (v->state == VS_DROPPED) {
        push_diag(bc, DIAG_ERROR, OP_DROP, name, v->cause_event,
            "double free: '%s' was already dropped (original drop at event #%d)",
            name, v->cause_event + 1);
        ok = 0;
    } else if (v->state == VS_MOVED) {
        push_diag(bc, DIAG_ERROR, OP_DROP, name, v->cause_event,
            "drop of moved value: '%s' was moved out at event #%d",
            name, v->cause_event + 1);
        ok = 0;
    }

    if (ok) {
        /* Satisfy any matching defer */
        for (int d = 0; d < bc->defer_count; d++) {
            if (strcmp(bc->defers[d].var_name, name) == 0)
                bc->defers[d].satisfied = 1;
        }
        drop_var(bc, v, OP_DROP);
    }
    push_event(bc, OP_DROP, name, NULL, bc->scope, ok);
}

void bc_use(BC *bc, const char *name) {
    Var    *v = find_var_mut(bc, name);
    Borrow *b = find_borrow_mut(bc, name);
    int ok = 1;

    if (v) {
        if (v->state == VS_MOVED) {
            push_diag(bc, DIAG_ERROR, OP_USE, name, v->cause_event,
                "use after move: '%s' was moved at event #%d",
                name, v->cause_event + 1);
            ok = 0;
        } else if (v->state == VS_DROPPED) {
            push_diag(bc, DIAG_ERROR, OP_USE, name, v->cause_event,
                "use after free: '%s' was dropped at event #%d",
                name, v->cause_event + 1);
            ok = 0;
        }
    } else if (b) {
        if (b->state == BS_DANGLING) {
            push_diag(bc, DIAG_ERROR, OP_USE, name, b->cause_event,
                "use of dangling borrow '%s' (target dropped; "
                "borrow created at event #%d)",
                name, b->cause_event + 1);
            ok = 0;
        } else if (b->state == BS_RELEASED) {
            push_diag(bc, DIAG_ERROR, OP_USE, name, b->cause_event,
                "use of released borrow '%s' (released; "
                "created at event #%d)",
                name, b->cause_event + 1);
            ok = 0;
        }
    } else {
        push_diag(bc, DIAG_ERROR, OP_USE, name, bc->event_count,
            "use of undeclared name '%s'", name);
        ok = 0;
    }
    push_event(bc, OP_USE, name, NULL, bc->scope, ok);
}

/*
 * Borrow operations
 */

static void borrow_impl(BC *bc, const char *ref_name, const char *target,
                         BorrowKind kind, OpKind op)
{
    Var *tgt = find_var_mut(bc, target);
    int ok = 1;

    if (!tgt) {
        push_diag(bc, DIAG_ERROR, op, target, bc->event_count,
            "borrow of unknown variable '%s'", target);
        ok = 0;
    } else if (tgt->state != VS_ALIVE) {
        push_diag(bc, DIAG_ERROR, op, target, tgt->cause_event,
            "cannot borrow '%s': it is %s (since event #%d)",
            target, bc_var_state_name(tgt->state), tgt->cause_event + 1);
        ok = 0;
    } else if (kind == BK_MUTABLE && !tgt->is_mut) {
        push_diag(bc, DIAG_ERROR, op, target, tgt->cause_event,
            "cannot borrow immutable variable '%s' as &mut "
            "(declared immutable at event #%d)",
            target, tgt->cause_event + 1);
        ok = 0;
    } else if (kind == BK_MUTABLE && tgt->shared_count > 0) {
        int first_borrow_ev = bc->event_count;
        for (int j = 0; j < bc->borrow_count; j++) {
            Borrow *b = &bc->borrows[j];
            if (b->state == BS_ACTIVE && b->target_var_id == tgt->id
                    && b->kind == BK_SHARED)
                first_borrow_ev = b->cause_event;
                break; /* on first match */
        }
        push_diag(bc, DIAG_ERROR, op, target, first_borrow_ev,
            "borrow conflict: '%s' has %d active shared borrow(s); "
            "cannot create &mut (first shared borrow at event #%d)",
            target, tgt->shared_count, first_borrow_ev + 1);
        ok = 0;
    } else if (kind == BK_MUTABLE && tgt->mut_count > 0) {
        int mut_ev = bc->event_count;
        for (int j = 0; j < bc->borrow_count; j++) {
            Borrow *b = &bc->borrows[j];
            if (b->state == BS_ACTIVE && b->target_var_id == tgt->id
                    && b->kind == BK_MUTABLE)
                mut_ev = b->cause_event;
                break;
        }
        push_diag(bc, DIAG_ERROR, op, target, mut_ev,
            "borrow conflict: '%s' is already &mut borrowed "
            "(that borrow is from event #%d)",
            target, mut_ev + 1);
        ok = 0;
    } else if (kind == BK_SHARED && tgt->mut_count > 0) {
        int mut_ev = bc->event_count;
        for (int j = 0; j < bc->borrow_count; j++) {
            Borrow *b = &bc->borrows[j];
            if (b->state == BS_ACTIVE && b->target_var_id == tgt->id
                    && b->kind == BK_MUTABLE)
                mut_ev = b->cause_event;
                break;
        }
        push_diag(bc, DIAG_ERROR, op, target, mut_ev,
            "borrow conflict: '%s' is &mut borrowed; "
            "cannot create shared borrow (mut borrow from event #%d)",
            target, mut_ev + 1);
        ok = 0;
    }

    if (ok) {
        if (bc->borrow_count >= BC_MAX_BORROWS) {
            push_diag(bc, DIAG_ERROR, op, ref_name, bc->event_count,
                "borrow table full");
            ok = 0;
        } else {
            Borrow *b = &bc->borrows[bc->borrow_count++];
            memset(b, 0, sizeof *b);
            strncpy(b->name, ref_name, BC_MAX_NAME - 1);
            b->id                = bc->next_borrow_id++;
            b->target_var_id     = tgt->id;
            b->kind              = kind;
            b->state             = BS_ACTIVE;
            b->scope             = bc->scope;
            b->cause_event       = bc->event_count;
            b->target_generation = tgt->generation;

            if (kind == BK_SHARED) tgt->shared_count++;
            else                   tgt->mut_count++;
        }
    }
    push_event(bc, op, ref_name, target, bc->scope, ok);
}

void bc_borrow    (BC *bc, const char *r, const char *t) { borrow_impl(bc, r, t, BK_SHARED,  OP_BORROW);     }
void bc_borrow_mut(BC *bc, const char *r, const char *t) { borrow_impl(bc, r, t, BK_MUTABLE, OP_BORROW_MUT); }

void bc_reborrow(BC *bc, const char *new_ref, const char *src_ref) {
    Borrow *src = find_borrow_mut(bc, src_ref);
    int ok = 1;

    if (!src) {
        push_diag(bc, DIAG_ERROR, OP_REBORROW, src_ref, bc->event_count,
            "reborrow of unknown borrow '%s'", src_ref);
        ok = 0;
    } else if (src->state != BS_ACTIVE) {
        push_diag(bc, DIAG_ERROR, OP_REBORROW, src_ref, src->cause_event,
            "reborrow of %s borrow '%s' (created at event #%d)",
            src->state == BS_RELEASED ? "released" : "dangling",
            src_ref, src->cause_event + 1);
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
            Borrow *nb = &bc->borrows[bc->borrow_count++];
            memset(nb, 0, sizeof *nb);
            strncpy(nb->name, new_ref, BC_MAX_NAME - 1);
            nb->id                = bc->next_borrow_id++;
            nb->target_var_id     = src->target_var_id;
            nb->kind              = src->kind;
            nb->state             = BS_ACTIVE;
            nb->scope             = bc->scope;
            nb->cause_event       = bc->event_count;
            nb->target_generation = src->target_generation;

            if (src->kind == BK_SHARED) tgt->shared_count++;
            else                        tgt->mut_count++;
        }
    }
    push_event(bc, OP_REBORROW, new_ref, src_ref, bc->scope, ok);
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
            "redundant release: borrow '%s' was already released "
            "(created at event #%d)", ref_name, b->cause_event + 1);
        ok = 0;
    } else if (b->state == BS_DANGLING) {
        push_diag(bc, DIAG_ERROR, OP_RELEASE, ref_name, b->cause_event,
            "cannot release dangling borrow '%s'", ref_name);
        ok = 0;
    }

    if (ok) release_borrow_counts(bc, b);
    push_event(bc, OP_RELEASE, ref_name, NULL, bc->scope, ok);
}

/*
 * Resource operations
 */

void bc_resource_acquire(BC *bc, const char *name, ResourceKind kind) {
    int ok = 1;

    if (bc->var_count >= BC_MAX_VARS || bc->resource_count >= BC_MAX_RESOURCES) {
        push_diag(bc, DIAG_ERROR, OP_RESOURCE_ACQUIRE, name, bc->event_count,
            "table full, cannot acquire resource '%s'", name);
        ok = 0;
    }
    /* Warn if there's already a live resource with this name */
    Resource *existing = find_resource_mut(bc, name);
    if (existing && !existing->is_released) {
        push_diag(bc, DIAG_WARNING, OP_RESOURCE_ACQUIRE, name,
            existing->acquire_event,
            "re-acquiring '%s' while previous %s is still open "
            "(acquired at event #%d)",
            name, bc_resource_kind_name(existing->kind),
            existing->acquire_event + 1);
    }

    if (ok) {
        Var *v = alloc_var(bc, name, 0, kind);
        (void)v;

        Resource *res = &bc->resources[bc->resource_count++];
        memset(res, 0, sizeof *res);
        res->id            = bc->next_resource_id++;
        strncpy(res->var_name, name, BC_MAX_NAME - 1);
        res->kind          = kind;
        res->is_released   = 0;
        res->scope         = bc->scope;
        res->acquire_event = bc->event_count;
        res->release_event = -1;
    }
    push_event(bc, OP_RESOURCE_ACQUIRE, name, NULL, bc->scope, ok);
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
            "(first release at event #%d, acquired at event #%d)",
            bc_resource_kind_name(res->kind), name,
            res->release_event + 1, res->acquire_event + 1);
        ok = 0;
    }

    if (ok) {
        res->is_released   = 1;
        res->release_event = bc->event_count;
        /* Satisfy any defer */
        for (int d = 0; d < bc->defer_count; d++) {
            if (strcmp(bc->defers[d].var_name, name) == 0)
                bc->defers[d].satisfied = 1;
        }
        /* Also drop the owning variable */
        if (v) drop_var(bc, v, OP_RESOURCE_RELEASE);
    }
    push_event(bc, OP_RESOURCE_RELEASE, name, NULL, bc->scope, ok);
}

/*
 * Defer and assertion
 */

void bc_defer(BC *bc, const char *name) {
    if (bc->defer_count >= BC_MAX_DEFERS) {
        push_diag(bc, DIAG_ERROR, OP_DEFER, name, bc->event_count,
            "defer table full");
        push_event(bc, OP_DEFER, name, NULL, bc->scope, 0);
        return;
    }
    Defer *d = &bc->defers[bc->defer_count++];
    strncpy(d->var_name, name, BC_MAX_NAME - 1);
    d->scope          = bc->scope;
    d->satisfied      = 0;
    d->register_event = bc->event_count;
    push_event(bc, OP_DEFER, name, NULL, bc->scope, 1);
}

void bc_assert_consumed(BC *bc, const char *name) {
    Var *v = find_var_mut(bc, name);
    int ok = 1;

    if (!v) {
        push_diag(bc, DIAG_ERROR, OP_ASSERT_CONSUMED, name, bc->event_count,
            "assert_consumed: unknown name '%s'", name);
        ok = 0;
    } else if (v->state == VS_ALIVE) {
        push_diag(bc, DIAG_ERROR, OP_ASSERT_CONSUMED, name, v->cause_event,
            "assert_consumed failed: '%s' is still alive "
            "(declared at event #%d) — language requires it be consumed here",
            name, v->cause_event + 1);
        ok = 0;
    }
    push_event(bc, OP_ASSERT_CONSUMED, name, NULL, bc->scope, ok);
}
