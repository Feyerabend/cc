#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "parse.h"
#include "defs.h"

/* -- Name context (for de Bruijn conversion) */

typedef struct NameCtx NameCtx;
struct NameCtx {
    const char *name;
    NameCtx    *next;
};

static int name_lookup(NameCtx *ctx, const char *name) {
    int i = 0;
    for (; ctx; ctx = ctx->next, i++)
        if (strcmp(ctx->name, name) == 0) return i;
    return -1;
}

/* -- Lexer state */

typedef struct {
    const char *src;
    int         pos;
    Arena      *arena;
} Parser;

static void skip_ws(Parser *p) {
    while (p->src[p->pos] && isspace((unsigned char)p->src[p->pos]))
        p->pos++;
}

static int peek(Parser *p) {
    skip_ws(p);
    return (unsigned char)p->src[p->pos];
}

static int expect(Parser *p, char c) {
    if (peek(p) != (unsigned char)c) {
        fprintf(stderr, "parse: expected '%c' at ...%s\n", c, p->src + p->pos);
        return 0;
    }
    p->pos++;
    return 1;
}

/* Returns 1 if current position (after whitespace) is → (UTF-8 E2 86 92) */
static int peek_arrow(Parser *p) {
    skip_ws(p);
    return (unsigned char)p->src[p->pos]   == 0xE2 &&
           (unsigned char)p->src[p->pos+1] == 0x86 &&
           (unsigned char)p->src[p->pos+2] == 0x92;
}
static void consume_arrow(Parser *p) { p->pos += 3; }

#define IDENT_MAX 64
static char *read_ident(Parser *p) {
    skip_ws(p);
    if (!isalpha((unsigned char)p->src[p->pos]) && p->src[p->pos] != '_')
        return NULL;
    char buf[IDENT_MAX];
    int  n = 0;
    while (isalnum((unsigned char)p->src[p->pos]) || p->src[p->pos] == '_' ||
           p->src[p->pos] == '\'') {
        if (n >= IDENT_MAX - 1) {
            buf[n] = '\0';
            fprintf(stderr, "parse: identifier too long (max %d chars): '%.20s...'\n",
                    IDENT_MAX - 1, buf);
            return NULL;
        }
        buf[n++] = p->src[p->pos++];
    }
    buf[n] = '\0';
    return arena_strdup(p->arena, buf);
}

/* -- Forward declarations */

static Term *parse_expr(Parser *p, NameCtx *ctx);
static Term *parse_atom(Parser *p, NameCtx *ctx);

/* -- Lambda: λ x y z. body  (multi-binder syntactic sugar) */

static Term *parse_lam(Parser *p, NameCtx *ctx) {
    int c = peek(p);
    if (c == '\\') { p->pos++; }
    else { p->pos++; p->pos++; }  /* UTF-8 λ: 0xCE 0xBB */
    char *names[32]; int n = 0;
    while (n < 32) {
        char *nm = read_ident(p);
        if (!nm) break;
        names[n++] = nm;
    }
    if (n == 0) { fprintf(stderr, "parse: λ needs at least one name\n"); return NULL; }
    if (!expect(p, '.')) return NULL;
    /* Build context: stack outermost first so innermost ends up at index 0 */
    NameCtx *cur = ctx;
    NameCtx ctxs[32];
    for (int i = 0; i < n; i++) {
        ctxs[i].name = names[i];
        ctxs[i].next = cur;
        cur = &ctxs[i];
    }
    Term *body = parse_expr(p, cur);
    if (!body) return NULL;
    Term *result = body;
    for (int i = n - 1; i >= 0; i--)
        result = tm_lam(p->arena, names[i], result);
    return result;
}

/* -- Pi type: Π(x : A). B */

static Term *parse_pi(Parser *p, NameCtx *ctx) {
    p->pos++; p->pos++;  /* UTF-8 Π: 0xCE 0xA0 */
    if (!expect(p, '(')) return NULL;
    char *name = read_ident(p);
    if (!name) { fprintf(stderr, "parse: Π needs a name\n"); return NULL; }
    if (!expect(p, ':')) return NULL;
    Term *dom = parse_expr(p, ctx);
    if (!dom) return NULL;
    if (!expect(p, ')')) return NULL;
    if (!expect(p, '.')) return NULL;
    NameCtx ext = { name, ctx };
    Term *cod = parse_expr(p, &ext);
    if (!cod) return NULL;
    return tm_pi(p->arena, name, dom, cod);
}

/* -- Sigma type: Σ(x : A). B */

static Term *parse_sigma(Parser *p, NameCtx *ctx) {
    p->pos++; p->pos++;  /* UTF-8 Σ: 0xCE 0xA3 */
    if (!expect(p, '(')) return NULL;
    char *name = read_ident(p);
    if (!name) { fprintf(stderr, "parse: Σ needs a name\n"); return NULL; }
    if (!expect(p, ':')) return NULL;
    Term *dom = parse_expr(p, ctx);
    if (!dom) return NULL;
    if (!expect(p, ')')) return NULL;
    if (!expect(p, '.')) return NULL;
    NameCtx ext = { name, ctx };
    Term *cod = parse_expr(p, &ext);
    if (!cod) return NULL;
    return tm_sig(p->arena, name, dom, cod);
}

/* -- Atom: variable | (expr [:type]) | (a,b) | fst/snd | Type[_N]  */

static Term *parse_atom(Parser *p, NameCtx *ctx) {
    int c = peek(p);
    if (c == '(') {
        p->pos++;
        Term *t = parse_expr(p, ctx);
        if (!t) return NULL;
        if (peek(p) == ',') {
            /* (fst, snd) pair constructor */
            p->pos++;
            Term *snd = parse_expr(p, ctx);
            if (!snd) return NULL;
            if (!expect(p, ')')) return NULL;
            return tm_pair(p->arena, t, snd);
        }
        if (peek(p) == ':') {
            /* (term : type) annotation */
            p->pos++;
            Term *ty = parse_expr(p, ctx);
            if (!ty) return NULL;
            if (!expect(p, ')')) return NULL;
            return tm_ann(p->arena, t, ty);
        }
        if (!expect(p, ')')) return NULL;
        return t;
    }
    if (isalpha(c) || c == '_') {
        char *name = read_ident(p);
        if (!name) return NULL;
        /* Axioms */
        if (strcmp(name, "ua")     == 0) return tm_ua(p->arena);
        if (strcmp(name, "funext") == 0) return tm_funext(p->arena);
        /* Natural numbers */
        if (strcmp(name, "Nat")  == 0) return tm_nat(p->arena);
        if (strcmp(name, "zero") == 0) return tm_zero(p->arena);
        if (strcmp(name, "succ") == 0) {
            Term *n = parse_atom(p, ctx);
            if (!n) return NULL;
            return tm_succ(p->arena, n);
        }
        /* Booleans */
        if (strcmp(name, "Bool")    == 0) return tm_bool(p->arena);
        if (strcmp(name, "true")    == 0) return tm_true(p->arena);
        if (strcmp(name, "false")   == 0) return tm_false(p->arena);
        if (strcmp(name, "boolrec") == 0) {
            Term *mot   = parse_atom(p, ctx); if (!mot)   return NULL;
            Term *tcase = parse_atom(p, ctx); if (!tcase) return NULL;
            Term *fcase = parse_atom(p, ctx); if (!fcase) return NULL;
            Term *scr   = parse_atom(p, ctx); if (!scr)   return NULL;
            return tm_boolrec(p->arena, mot, tcase, fcase, scr);
        }
        if (strcmp(name, "natrec") == 0) {
            Term *mot  = parse_atom(p, ctx); if (!mot)  return NULL;
            Term *base = parse_atom(p, ctx); if (!base) return NULL;
            Term *step = parse_atom(p, ctx); if (!step) return NULL;
            Term *scr  = parse_atom(p, ctx); if (!scr)  return NULL;
            return tm_natrec(p->arena, mot, base, step, scr);
        }
        /* Identity type keywords */
        if (strcmp(name, "Id") == 0) {
            Term *ty  = parse_atom(p, ctx); if (!ty)  return NULL;
            Term *lhs = parse_atom(p, ctx); if (!lhs) return NULL;
            Term *rhs = parse_atom(p, ctx); if (!rhs) return NULL;
            return tm_id(p->arena, ty, lhs, rhs);
        }
        if (strcmp(name, "refl") == 0) {
            Term *t = parse_atom(p, ctx);
            if (!t) return NULL;
            return tm_refl(p->arena, t);
        }
        if (strcmp(name, "J") == 0) {
            Term *ty       = parse_atom(p, ctx); if (!ty)       return NULL;
            Term *lhs      = parse_atom(p, ctx); if (!lhs)      return NULL;
            Term *motive   = parse_atom(p, ctx); if (!motive)   return NULL;
            Term *base     = parse_atom(p, ctx); if (!base)     return NULL;
            Term *endpoint = parse_atom(p, ctx); if (!endpoint) return NULL;
            Term *proof    = parse_atom(p, ctx); if (!proof)    return NULL;
            return tm_j(p->arena, ty, lhs, motive, base, endpoint, proof);
        }
        /* W-types */
        /* Unit type */
        if (strcmp(name, "Unit") == 0) return tm_unit(p->arena);
        if (strcmp(name, "star") == 0) return tm_star(p->arena);
        if (strcmp(name, "unitrec") == 0) {
            Term *mot = parse_atom(p, ctx); if (!mot) return NULL;
            Term *bas = parse_atom(p, ctx); if (!bas) return NULL;
            Term *scr = parse_atom(p, ctx); if (!scr) return NULL;
            return tm_unitrec(p->arena, mot, bas, scr);
        }
        /* Sum type */
        if (strcmp(name, "Sum") == 0) {
            Term *left  = parse_atom(p, ctx); if (!left)  return NULL;
            Term *right = parse_atom(p, ctx); if (!right) return NULL;
            return tm_sum(p->arena, left, right);
        }
        if (strcmp(name, "inl") == 0) {
            Term *arg = parse_atom(p, ctx);
            if (!arg) return NULL;
            return tm_inl(p->arena, arg);
        }
        if (strcmp(name, "inr") == 0) {
            Term *arg = parse_atom(p, ctx);
            if (!arg) return NULL;
            return tm_inr(p->arena, arg);
        }
        if (strcmp(name, "case") == 0) {
            Term *mot   = parse_atom(p, ctx); if (!mot)   return NULL;
            Term *lcase = parse_atom(p, ctx); if (!lcase) return NULL;
            Term *rcase = parse_atom(p, ctx); if (!rcase) return NULL;
            Term *scr   = parse_atom(p, ctx); if (!scr)   return NULL;
            return tm_casesplit(p->arena, mot, lcase, rcase, scr);
        }
        /* Propositional truncation */
        if (strcmp(name, "trunc") == 0) return tm_trunc(p->arena);
        if (strcmp(name, "trint") == 0) return tm_trint(p->arena);
        if (strcmp(name, "squash") == 0) return tm_squash(p->arena);
        if (strcmp(name, "truncrec") == 0) {
            Term *ty_a = parse_atom(p, ctx); if (!ty_a) return NULL;
            Term *ty_b = parse_atom(p, ctx); if (!ty_b) return NULL;
            Term *func  = parse_atom(p, ctx); if (!func)  return NULL;
            Term *scr   = parse_atom(p, ctx); if (!scr)   return NULL;
            return tm_truncrec(p->arena, ty_a, ty_b, func, scr);
        }
        /* Circle S¹ */
        if (strcmp(name, "S1") == 0)   return tm_circle(p->arena);
        if (strcmp(name, "base") == 0) return tm_base(p->arena);
        if (strcmp(name, "loop") == 0) return tm_loop(p->arena);
        if (strcmp(name, "S1rec") == 0) {
            Term *mot  = parse_atom(p, ctx); if (!mot)  return NULL;
            Term *bc   = parse_atom(p, ctx); if (!bc)   return NULL;
            Term *lc   = parse_atom(p, ctx); if (!lc)   return NULL;
            Term *scr  = parse_atom(p, ctx); if (!scr)  return NULL;
            return tm_circrec(p->arena, mot, bc, lc, scr);
        }
        /* Empty type */
        if (strcmp(name, "Empty") == 0) return tm_empty(p->arena);
        if (strcmp(name, "abort") == 0) {
            Term *mot = parse_atom(p, ctx); if (!mot) return NULL;
            Term *scr = parse_atom(p, ctx); if (!scr) return NULL;
            return tm_abort(p->arena, mot, scr);
        }
        if (strcmp(name, "W") == 0) {
            if (!expect(p, '(')) return NULL;
            char *wname = read_ident(p);
            if (!wname) { fprintf(stderr, "parse: W needs a name\n"); return NULL; }
            if (!expect(p, ':')) return NULL;
            Term *dom = parse_expr(p, ctx);
            if (!dom) return NULL;
            if (!expect(p, ')')) return NULL;
            if (!expect(p, '.')) return NULL;
            NameCtx ext = { wname, ctx };
            Term *cod = parse_expr(p, &ext);
            if (!cod) return NULL;
            return tm_w(p->arena, wname, dom, cod);
        }
        if (strcmp(name, "sup") == 0) {
            Term *label    = parse_atom(p, ctx); if (!label)    return NULL;
            Term *children = parse_atom(p, ctx); if (!children) return NULL;
            return tm_sup(p->arena, label, children);
        }
        if (strcmp(name, "wrec") == 0) {
            Term *mot  = parse_atom(p, ctx); if (!mot)  return NULL;
            Term *step = parse_atom(p, ctx); if (!step) return NULL;
            Term *scr  = parse_atom(p, ctx); if (!scr)  return NULL;
            return tm_wrec(p->arena, mot, step, scr);
        }
        /* fst / snd eliminators */
        if (strcmp(name, "fst") == 0) {
            Term *arg = parse_atom(p, ctx);
            if (!arg) return NULL;
            return tm_fst(p->arena, arg);
        }
        if (strcmp(name, "snd") == 0) {
            Term *arg = parse_atom(p, ctx);
            if (!arg) return NULL;
            return tm_snd(p->arena, arg);
        }
        /* Type[_N]: handles "Type", "Type_N" (read as one token), "Type" + "_N" */
        if (strncmp(name, "Type", 4) == 0) {
            int level = 0;
            const char *rest = name + 4;
            if (*rest == '_' && isdigit((unsigned char)rest[1])) {
                /* validate all remaining chars are digits */
                const char *d = rest + 1;
                while (isdigit((unsigned char)*d)) d++;
                if (*d != '\0') goto lookup;  /* e.g. "Type_1abc" */
                level = atoi(rest + 1);
            } else if (*rest == '\0' && peek(p) == '_') {
                p->pos++;
                while (isdigit((unsigned char)p->src[p->pos]))
                    level = level * 10 + (p->src[p->pos++] - '0');
            } else if (*rest != '\0') {
                goto lookup;  /* "Types" etc — treat as variable */
            }
            return tm_uni(p->arena, level);
        }
    lookup:;
        int idx = name_lookup(ctx, name);
        if (idx < 0) {
            int gidx = def_lookup(name);
            if (gidx >= 0) return tm_global(p->arena, gidx);
            fprintf(stderr, "parse: unbound variable '%s'\n", name);
            return NULL;
        }
        return tm_var(p->arena, idx);
    }
    fprintf(stderr, "parse: unexpected char '%c'\n", c);
    return NULL;
}

/* -- Application: left-associative sequence of atoms */

static int is_app_stop(Parser *p) {
    int c = peek(p);
    if (c == ')' || c == '.' || c == ':' || c == ',' || c == '\0') return 1;
    if (c == '\\') return 1;
    if ((unsigned char)p->src[p->pos] == 0xCE &&
        ((unsigned char)p->src[p->pos+1] == 0xBB ||  /* λ */
         (unsigned char)p->src[p->pos+1] == 0xA0 ||  /* Π */
         (unsigned char)p->src[p->pos+1] == 0xA3))   /* Σ */
        return 1;
    if (peek_arrow(p)) return 1;  /* → */
    return 0;
}

static Term *parse_app(Parser *p, NameCtx *ctx) {
    Term *t = parse_atom(p, ctx);
    if (!t) return NULL;
    while (!is_app_stop(p)) {
        Term *arg = parse_atom(p, ctx);
        if (!arg) break;
        t = tm_app(p->arena, t, arg);
    }
    return t;
}

/* -- Top-level expr: lam | pi | app [→ expr]  (→ is right-associative) */

static Term *parse_expr(Parser *p, NameCtx *ctx) {
    skip_ws(p);
    int c = (unsigned char)p->src[p->pos];
    Term *t;
    if (c == '\\')                                                 t = parse_lam(p, ctx);
    else if (c == 0xCE && (unsigned char)p->src[p->pos+1] == 0xBB) t = parse_lam(p, ctx);
    else if (c == 0xCE && (unsigned char)p->src[p->pos+1] == 0xA0) t = parse_pi(p, ctx);
    else if (c == 0xCE && (unsigned char)p->src[p->pos+1] == 0xA3) t = parse_sigma(p, ctx);
    else                                                           t = parse_app(p, ctx);
    if (!t) return NULL;

    /* A → B  sugar for  Π(_ : A). B  (right-associative, non-dependent) */
    if (peek_arrow(p)) {
        consume_arrow(p);
        char *underscore = arena_strdup(p->arena, "_");
        NameCtx ext = { underscore, ctx };
        Term *cod = parse_expr(p, &ext);
        if (!cod) return NULL;
        return tm_pi(p->arena, underscore, t, cod);
    }
    return t;
}

/* -- Public entry point */

Term *parse(Arena *a, const char *src) {
    Parser p = { src, 0, a };
    skip_ws(&p);
    if (p.src[p.pos] == '\0') return NULL;
    Term *t = parse_expr(&p, NULL);
    skip_ws(&p);
    if (t && p.src[p.pos] != '\0') {
        fprintf(stderr, "parse: trailing input: %s\n", p.src + p.pos);
        return NULL;
    }
    return t;
}
