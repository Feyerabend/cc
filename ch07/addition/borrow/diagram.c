/*
 * diagram.c  —  String-diagram renderer.  Zero checker logic.
 *
 * Reads BC event snapshots and produces human-readable output.
 * Every rendering decision is driven by Event and Diag data only.
 */

#include "diagram.h"
#include <stdio.h>
#include <string.h>

/* -- ANSI colour codes  */
#define C_RESET  "\033[0m"
#define C_BOLD   "\033[1m"
#define C_DIM    "\033[2m"
#define C_RED    "\033[31m"
#define C_GREEN  "\033[32m"
#define C_YELLOW "\033[33m"
#define C_BLUE   "\033[34m"
#define C_CYAN   "\033[36m"
#define C_GREY   "\033[90m"
#define C_BRED   "\033[91m"
#define C_BGRN   "\033[92m"
#define C_BYLW   "\033[93m"
#define C_BBLU   "\033[94m"
#define C_BCYN   "\033[96m"
#define C_BWHT   "\033[97m"

/* -- helpers  */

DiagOpts diag_default_opts(void) {
    DiagOpts o = {0};
    o.show_resources   = 1;
    o.show_generations = 1;
    o.show_scope_depth = 1;
    o.show_provenance  = 1;
    o.compact          = 0;
    o.colour           = 1;
    return o;
}

static void c(const DiagOpts *o, const char *code) {
    if (o->colour) fputs(code, stdout);
}

static void rule(const DiagOpts *o) {
    c(o, C_GREY);
    printf("  %.*s\n", 68,
        "----------------------------------------------------------------------");
    c(o, C_RESET);
}

/* Find var name by id inside an Event snapshot */
static const char *var_name_by_id(const Event *ev, int id) {
    for (int i = 0; i < ev->var_count; i++)
        if (ev->vars[i].id == id) return ev->vars[i].name;
    return "?";
}

/* Resource kind badge */
static const char *res_badge(ResourceKind k) {
    switch (k) {
        case RK_HEAP:   return "▣Heap";
        case RK_FILE:   return "▣File";
        case RK_SOCKET: return "▣Sock";
        case RK_LOCK:   return "▣Lock";
        case RK_CUSTOM: return "▣Res";
        default:        return "";
    }
}

/* -- event header  */

static void print_header(const Event *ev, const DiagOpts *o) {
    c(o, C_BOLD);
    printf("┌- #%-3d  ", ev->index);
    c(o, C_RESET);

    c(o, ev->ok ? C_BGRN : C_BRED);
    printf("%-16s", bc_op_name(ev->op));
    c(o, C_RESET);
    printf("  ");

    c(o, C_BOLD);
    switch (ev->op) {
        case OP_SCOPE_ENTER:
            printf("{ scope depth → %d", ev->scope_after);
            break;
        case OP_SCOPE_EXIT:
            printf("} scope depth → %d", ev->scope_after);
            break;
        case OP_DECLARE:
        case OP_DECLARE_COPY:
            printf("let %s%s", ev->a,
                ev->op == OP_DECLARE_COPY ? "  [Copy]" : "");
            break;
        case OP_MOVE:
            printf("let %s = move(%s)", ev->b, ev->a);
            break;
        case OP_COPY:
            printf("let %s = copy(%s)", ev->b, ev->a);
            break;
        case OP_DROP:
            printf("drop(%s)", ev->a);
            break;
        case OP_ASSIGN:
            printf("%s = …", ev->a);
            break;
        case OP_BORROW:
            printf("let %s = &%s", ev->a, ev->b);
            break;
        case OP_BORROW_MUT:
            printf("let %s = &mut %s", ev->a, ev->b);
            break;
        case OP_RELEASE:
            printf("release(%s)", ev->a);
            break;
        case OP_USE:
            printf("use(%s)", ev->a);
            break;
        case OP_REBORROW:
            printf("let %s = reborrow(%s)", ev->a, ev->b);
            break;
        case OP_RESOURCE_ACQUIRE:
            printf("acquire(%s)", ev->a);
            break;
        case OP_RESOURCE_RELEASE:
            printf("release_resource(%s)", ev->a);
            break;
        case OP_DEFER:
            printf("defer { release(%s) }", ev->a);
            break;
        case OP_ASSERT_CONSUMED:
            printf("assert_consumed(%s)", ev->a);
            break;
    }
    c(o, C_RESET);

    if (!ev->ok) {
        c(o, C_BRED);
        printf("  ← BLOCKED");
        c(o, C_RESET);
    }
    putchar('\n');
}

/* -- ownership wire  */

static void print_var_wire(const Var *v, const DiagOpts *o) {
    /* build label */
    char label[BC_MAX_NAME + 12];
    int n = 0;
    n += snprintf(label + n, sizeof label - n - 1, "%s", v->name);
    if (v->is_copy)
        n += snprintf(label + n, sizeof label - n - 1, "©");
    if (o->show_generations && v->generation > 1)
        n += snprintf(label + n, sizeof label - n - 1, "ᵍ%d", v->generation);
    (void)n;

    printf("│    [%-16s] ", label);

    if (v->state == VS_ALIVE) {
        /* resource badge if applicable */
        const char *badge = (v->res_kind != RK_PLAIN) ? res_badge(v->res_kind) : "";
        c(o, C_BGRN);
        printf("---owns--►");
        c(o, C_RESET);
        c(o, C_GREEN);
        printf(" [%s]", v->name);
        c(o, C_RESET);
        if (badge[0]) {
            c(o, C_BYLW);
            printf("  %s", badge);
            c(o, C_RESET);
        }
        if (o->show_scope_depth)
            printf("  s%d", v->scope);
        if (v->shared_count > 0 || v->mut_count > 0) {
            c(o, C_CYAN);
            printf("  {&×%d", v->shared_count);
            if (v->mut_count) printf(" &mut×%d", v->mut_count);
            printf("}");
            c(o, C_RESET);
        }
    } else if (v->state == VS_MOVED) {
        c(o, C_DIM); c(o, C_YELLOW);
        printf("╌╌╌╌ moved ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌");
        c(o, C_RESET);
    } else {
        c(o, C_RED);
        printf("✗  dropped");
        c(o, C_RESET);
    }
    putchar('\n');
}

/* -- borrow wire  */

static void print_borrow_wire(const Borrow *b, const char *tgt,
                               const DiagOpts *o)
{
    if (b->state == BS_RELEASED) return;

    printf("│    [%-16s] ", b->name);

    if (b->state == BS_DANGLING) {
        c(o, C_BRED);
        printf("~~✗~~~~~~~~~~~~~~~~~~~~~~~~►");
        c(o, C_RESET);
        c(o, C_RED);
        printf(" [%s]  ⚡DANGLING", tgt);
        c(o, C_RESET);
    } else if (b->kind == BK_SHARED) {
        c(o, C_BCYN);
        printf("·····&T····················►");
        c(o, C_RESET);
        c(o, C_CYAN);
        printf(" [%s]", tgt);
        c(o, C_RESET);
        if (o->show_scope_depth) printf("  s%d", b->scope);
    } else {
        c(o, C_BBLU);
        printf("═════&mut══════════════════►");
        c(o, C_RESET);
        c(o, C_BLUE);
        printf(" [%s]", tgt);
        c(o, C_RESET);
        if (o->show_scope_depth) printf("  s%d", b->scope);
    }
    putchar('\n');
}

/* -- resource summary row  */

static void print_resource_row(const Resource *res, const DiagOpts *o) {
    if (!o->show_resources) return;
    printf("│    %-20s  ", res->var_name);
    if (res->is_released) {
        c(o, C_DIM);
        printf("%-10s  released at #%d",
            bc_resource_kind_name(res->kind), res->release_event + 1);
        c(o, C_RESET);
    } else {
        c(o, C_BYLW);
        printf("%-10s  OPEN (acquired #%d)",
            bc_resource_kind_name(res->kind), res->acquire_event + 1);
        c(o, C_RESET);
    }
    putchar('\n');
}

/* -- diagram body  */

static void print_body(const Event *ev, const DiagOpts *o) {
    printf("│\n");

    /* ownership wires */
    int any_var = 0;
    for (int i = 0; i < ev->var_count; i++) {
        if (ev->vars[i].scope > ev->scope) continue;
        print_var_wire(&ev->vars[i], o);
        any_var = 1;
    }
    if (!any_var) {
        printf("│    ");
        c(o, C_GREY); printf("(no variables)\n"); c(o, C_RESET);
    }

    /* borrow wires */
    int any_borrow = 0;
    for (int j = 0; j < ev->borrow_count; j++)
        if (ev->borrows[j].state != BS_RELEASED) { any_borrow = 1; break; }
    if (any_borrow) {
        printf("│\n");
        for (int j = 0; j < ev->borrow_count; j++) {
            if (ev->borrows[j].state == BS_RELEASED) continue;
            const char *tname = var_name_by_id(ev, ev->borrows[j].target_var_id);
            print_borrow_wire(&ev->borrows[j], tname, o);
        }
    }

    /* resource table */
    if (o->show_resources && ev->resource_count > 0) {
        printf("│\n│    ");
        c(o, C_GREY); printf("Resources:\n"); c(o, C_RESET);
        for (int r = 0; r < ev->resource_count; r++) {
            if (ev->resources[r].scope > ev->scope) continue;
            print_resource_row(&ev->resources[r], o);
        }
    }
    printf("│\n");
}

/* -- diagnostics for one event  */

static void print_diags_for(const BC *bc, int event_idx,
                              const DiagOpts *o)
{
    for (int d = 0; d < bc->diag_count; d++) {
        const Diag *diag = &bc->diags[d];
        if (diag->detect_event != event_idx) continue;

        switch (diag->level) {
            case DIAG_ERROR:
                c(o, C_BRED);
                printf("│  ╔ ERROR ╗  ");
                c(o, C_RESET);
                c(o, C_RED);
                printf("%s", diag->msg);
                c(o, C_RESET);
                if (o->show_provenance && diag->cause_event != diag->detect_event) {
                    c(o, C_GREY);
                    printf("  [cause: event #%d]", diag->cause_event + 1);
                    c(o, C_RESET);
                }
                putchar('\n');
                break;
            case DIAG_WARNING:
                c(o, C_BYLW);
                printf("│  ⚠ warning  ");
                c(o, C_RESET);
                printf("%s\n", diag->msg);
                break;
            case DIAG_NOTE:
                c(o, C_BCYN);
                printf("│  ℹ note     ");
                c(o, C_RESET);
                printf("%s\n", diag->msg);
                break;
        }
    }
}

/* 
 * Public API
 */

void diag_render_event(const BC *bc, int idx, const DiagOpts *opts) {
    if (idx < 0 || idx >= bc->event_count) return;
    const Event *ev = &bc->events[idx];
    rule(opts);
    print_header(ev, opts);
    if (!opts->compact) print_body(ev, opts);
    print_diags_for(bc, idx, opts);
}

void diag_render_all(const BC *bc, const DiagOpts *opts) {
    for (int i = 0; i < bc->event_count; i++)
        diag_render_event(bc, i, opts);
    rule(opts);
}

void diag_render_final(const BC *bc, const DiagOpts *opts) {
    if (bc->event_count > 0)
        diag_render_event(bc, bc->event_count - 1, opts);
}

void diag_render_summary(const BC *bc, const DiagOpts *opts) {
    rule(opts);
    c(opts, C_BOLD); printf("  SUMMARY\n"); c(opts, C_RESET);
    printf("  Events    : %d\n", bc->event_count);
    printf("  Variables : %d\n", bc->var_count);
    printf("  Borrows   : %d\n", bc->borrow_count);
    printf("  Resources : %d\n", bc->resource_count);

    if (bc->error_count == 0) {
        c(opts, C_BGRN);
        printf("  Errors    : 0  ✓  all checks passed\n");
        c(opts, C_RESET);
    } else {
        c(opts, C_BRED);
        printf("  Errors    : %d\n", bc->error_count);
        c(opts, C_RESET);
    }
    if (bc->warning_count > 0) {
        c(opts, C_BYLW);
        printf("  Warnings  : %d\n", bc->warning_count);
        c(opts, C_RESET);
    }

    if (bc->error_count > 0 || bc->warning_count > 0) {
        printf("\n");
        int en = 1;
        for (int d = 0; d < bc->diag_count; d++) {
            const Diag *diag = &bc->diags[d];
            if (diag->level == DIAG_NOTE) continue;
            const char *tag = (diag->level == DIAG_ERROR) ? "error" : "warning";
            c(opts, diag->level == DIAG_ERROR ? C_RED : C_YELLOW);
            printf("  [%s #%d @ event #%d]  %s",
                tag, en++, diag->detect_event + 1, diag->msg);
            if (opts->show_provenance && diag->cause_event != diag->detect_event)
                printf("  (cause: event #%d)", diag->cause_event + 1);
            c(opts, C_RESET);
            putchar('\n');
        }
    }
    rule(opts);
}
