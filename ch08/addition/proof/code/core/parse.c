#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "parse.h"
#include "defs.h"
#include "eval.h"

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
        /* bare '_' is an implicit-argument hole */
        if (strcmp(name, "_") == 0) return tm_hole(p->arena, -1);
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
        if (strcmp(name, "fix") == 0) {
            Term *body = parse_atom(p, ctx); if (!body) return NULL;
            return tm_fix(p->arena, body);
        }
        /* Level terms (universe polymorphism) */
        if (strcmp(name, "Level") == 0) return tm_level(p->arena);
        if (strcmp(name, "lzero") == 0) return tm_lzero(p->arena);
        if (strcmp(name, "lsuc")  == 0) {
            Term *arg = parse_atom(p, ctx); if (!arg) return NULL;
            return tm_lsuc(p->arena, arg);
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
        /* User-declared inductive families */
        if (strcmp(name, "indrec") == 0) {
            char *fname = read_ident(p);
            if (!fname) {
                fprintf(stderr, "parse: 'indrec' needs a family name\n");
                return NULL;
            }
            int fam_idx = ind_lookup(fname);
            if (fam_idx < 0) {
                fprintf(stderr, "parse: indrec: unknown family '%s'\n", fname);
                return NULL;
            }
            IndDef *fam = ind_get(fam_idx);
            Term *motive = parse_atom(p, ctx);
            if (!motive) return NULL;
            int n = fam->n_ctors;
            Term **cases = n > 0 ? (Term **)arena_alloc(p->arena, n * sizeof(Term *)) : NULL;
            for (int i = 0; i < n; i++) {
                cases[i] = parse_atom(p, ctx);
                if (!cases[i]) return NULL;
            }
            Term *scrut = parse_atom(p, ctx);
            if (!scrut) return NULL;
            return tm_indrec(p->arena, fam_idx, motive, n, cases, scrut);
        }
        /* Type[_N|_ident|_(expr)]: universe at concrete or variable level */
        if (strncmp(name, "Type", 4) == 0) {
            int level = 0;
            const char *rest = name + 4;
            if (*rest == '_') {
                const char *suffix = rest + 1;
                if (*suffix == '\0') {
                    /* "Type_" in token buffer — peek stream for rest */
                    int c2 = peek(p);
                    if (isdigit((unsigned char)c2)) {
                        int level = 0;
                        while (isdigit((unsigned char)p->src[p->pos]))
                            level = level * 10 + (p->src[p->pos++] - '0');
                        return tm_uni(p->arena, level);
                    }
                    if (isalpha((unsigned char)c2) || c2 == '_') {
                        char *lname = read_ident(p);
                        if (!lname) return NULL;
                        int idx = name_lookup(ctx, lname);
                        if (idx < 0) {
                            int gidx = def_lookup(lname);
                            if (gidx >= 0) return tm_uni_v(p->arena, tm_global(p->arena, gidx));
                            fprintf(stderr, "parse: unbound level variable '%s'\n", lname);
                            return NULL;
                        }
                        return tm_uni_v(p->arena, tm_var(p->arena, idx));
                    }
                    if (c2 == '(') {
                        p->pos++;
                        Term *lvl = parse_expr(p, ctx);
                        if (!lvl) return NULL;
                        if (!expect(p, ')')) return NULL;
                        return tm_uni_v(p->arena, lvl);
                    }
                    return tm_uni(p->arena, 0);
                }
                if (isdigit((unsigned char)*suffix)) {
                    /* "Type_N" — digits only */
                    const char *d = suffix;
                    while (isdigit((unsigned char)*d)) d++;
                    if (*d != '\0') goto lookup;  /* "Type_1abc" → variable */
                    return tm_uni(p->arena, atoi(suffix));
                }
                if (isalpha((unsigned char)*suffix) || *suffix == '_') {
                    /* "Type_ident" — level variable baked into token */
                    int idx = name_lookup(ctx, suffix);
                    if (idx < 0) {
                        int gidx = def_lookup(suffix);
                        if (gidx >= 0) return tm_uni_v(p->arena, tm_global(p->arena, gidx));
                        fprintf(stderr, "parse: unbound level variable '%s'\n", suffix);
                        return NULL;
                    }
                    return tm_uni_v(p->arena, tm_var(p->arena, idx));
                }
                goto lookup;  /* unrecognised suffix */
            } else if (*rest == '\0' && peek(p) == '_') {
                p->pos++;  /* consume '_' */
                int c2 = peek(p);
                if (isdigit((unsigned char)c2)) {
                    /* "Type" then "_N" */
                    while (isdigit((unsigned char)p->src[p->pos]))
                        level = level * 10 + (p->src[p->pos++] - '0');
                    return tm_uni(p->arena, level);
                }
                if (isalpha((unsigned char)c2) || c2 == '_') {
                    /* "Type" then "_ident" */
                    char *lname = read_ident(p);
                    if (!lname) return NULL;
                    int idx = name_lookup(ctx, lname);
                    if (idx < 0) {
                        int gidx = def_lookup(lname);
                        if (gidx >= 0) return tm_uni_v(p->arena, tm_global(p->arena, gidx));
                        fprintf(stderr, "parse: unbound level variable '%s'\n", lname);
                        return NULL;
                    }
                    return tm_uni_v(p->arena, tm_var(p->arena, idx));
                }
                if (c2 == '(') {
                    /* "Type_(expr)" — complex level expression */
                    p->pos++;  /* consume '(' */
                    Term *lvl = parse_expr(p, ctx);
                    if (!lvl) return NULL;
                    if (!expect(p, ')')) return NULL;
                    return tm_uni_v(p->arena, lvl);
                }
                /* Bare "Type_" with nothing → Type_0 */
                return tm_uni(p->arena, 0);
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
    if (c == ')' || c == '.' || c == ':' || c == ',' || c == '\0' || c == ';') return 1;
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

/* ── Strict-positivity helpers ──────────────────────────────────────────────
 *
 * Used by parse_data to reject non-positive recursive occurrences, which
 * would break logical consistency (e.g. data Bad where bad : (Bad → A) → Bad).
 *
 * term_not_occurs(gidx, t)  — 1 if global gidx does not appear in t.
 * term_strictly_positive(gidx, t) — 1 if gidx appears only positively in t:
 *   · not at all                                                           → OK
 *   · as the head of an application F a1 … an, F absent from each ai     → OK
 *   · Π(x:A).B / Σ(x:A).B / W(x:A).B: F absent from A, strictly pos in B → OK
 *   · anything else (F in dom, F nested in another type's args, …)        → NOT OK
 */

static int term_not_occurs(int gidx, Term *t) {
    if (!t) return 1;
    switch (t->tag) {
    /* Atoms that never mention a global */
    case TM_VAR: case TM_UNI:
    case TM_NAT: case TM_ZERO: case TM_BOOL: case TM_TRUE: case TM_FALSE:
    case TM_UNIT: case TM_STAR: case TM_EMPTY:
    case TM_CIRCLE: case TM_BASE: case TM_LOOP:
    case TM_UA: case TM_FUNEXT:
    case TM_TRUNC: case TM_TRINT: case TM_SQUASH:
    case TM_LEVEL: case TM_LZERO:
        return 1;
    case TM_GLOBAL:  return t->idx != gidx;
    case TM_APP:     return term_not_occurs(gidx, t->app.fun) &&
                            term_not_occurs(gidx, t->app.arg);
    case TM_LAM:     return term_not_occurs(gidx, t->lam.body);
    case TM_ANN:     return term_not_occurs(gidx, t->ann.term) &&
                            term_not_occurs(gidx, t->ann.type);
    case TM_PI:
    case TM_SIG:
    case TM_W:       return term_not_occurs(gidx, t->pi.dom) &&
                            term_not_occurs(gidx, t->pi.cod);
    case TM_PAIR:    return term_not_occurs(gidx, t->pair.fst) &&
                            term_not_occurs(gidx, t->pair.snd);
    case TM_FST: case TM_SND:
    case TM_SUCC: case TM_INL: case TM_INR:
                     return term_not_occurs(gidx, t->elim);
    case TM_REFL:    return term_not_occurs(gidx, t->refl);
    case TM_ID:      return term_not_occurs(gidx, t->id.ty)  &&
                            term_not_occurs(gidx, t->id.lhs) &&
                            term_not_occurs(gidx, t->id.rhs);
    case TM_SUM:     return term_not_occurs(gidx, t->sum_t.left) &&
                            term_not_occurs(gidx, t->sum_t.right);
    case TM_NATREC:  return term_not_occurs(gidx, t->natrec.motive) &&
                            term_not_occurs(gidx, t->natrec.base)   &&
                            term_not_occurs(gidx, t->natrec.step)   &&
                            term_not_occurs(gidx, t->natrec.scrut);
    case TM_BOOLREC: return term_not_occurs(gidx, t->boolrec.motive) &&
                            term_not_occurs(gidx, t->boolrec.tcase)  &&
                            term_not_occurs(gidx, t->boolrec.fcase)  &&
                            term_not_occurs(gidx, t->boolrec.scrut);
    case TM_J:       return term_not_occurs(gidx, t->j.ty)       &&
                            term_not_occurs(gidx, t->j.lhs)      &&
                            term_not_occurs(gidx, t->j.motive)   &&
                            term_not_occurs(gidx, t->j.base)     &&
                            term_not_occurs(gidx, t->j.endpoint) &&
                            term_not_occurs(gidx, t->j.proof);
    case TM_ABORT:   return term_not_occurs(gidx, t->abort_t.motive) &&
                            term_not_occurs(gidx, t->abort_t.scrut);
    case TM_UNITREC: return term_not_occurs(gidx, t->unitrec_t.motive) &&
                            term_not_occurs(gidx, t->unitrec_t.base)   &&
                            term_not_occurs(gidx, t->unitrec_t.scrut);
    case TM_CASESPLIT: return term_not_occurs(gidx, t->casesplit_t.motive) &&
                              term_not_occurs(gidx, t->casesplit_t.lcase)  &&
                              term_not_occurs(gidx, t->casesplit_t.rcase)  &&
                              term_not_occurs(gidx, t->casesplit_t.scrut);
    case TM_SUP:     return term_not_occurs(gidx, t->sup.label) &&
                            term_not_occurs(gidx, t->sup.children);
    case TM_WREC:    return term_not_occurs(gidx, t->wrec.motive) &&
                            term_not_occurs(gidx, t->wrec.step)   &&
                            term_not_occurs(gidx, t->wrec.scrut);
    case TM_TRUNCREC: return term_not_occurs(gidx, t->truncrec_t.ty_a)  &&
                             term_not_occurs(gidx, t->truncrec_t.ty_b)  &&
                             term_not_occurs(gidx, t->truncrec_t.func)  &&
                             term_not_occurs(gidx, t->truncrec_t.scrut);
    case TM_CIRCREC: return term_not_occurs(gidx, t->circrec_t.motive)    &&
                            term_not_occurs(gidx, t->circrec_t.base_case) &&
                            term_not_occurs(gidx, t->circrec_t.loop_case) &&
                            term_not_occurs(gidx, t->circrec_t.scrut);
    case TM_INDTYPE: {
        for (int i = 0; i < t->indtype.n_args; i++)
            if (!term_not_occurs(gidx, t->indtype.args[i])) return 0;
        return 1;
    }
    case TM_INDCON: {
        for (int i = 0; i < t->indcon.n_args; i++)
            if (!term_not_occurs(gidx, t->indcon.args[i])) return 0;
        return 1;
    }
    case TM_INDREC:
        if (!term_not_occurs(gidx, t->indrec.motive)) return 0;
        if (!term_not_occurs(gidx, t->indrec.scrut))  return 0;
        for (int i = 0; i < t->indrec.n_cases; i++)
            if (!term_not_occurs(gidx, t->indrec.cases[i])) return 0;
        return 1;
    case TM_FIX:   return term_not_occurs(gidx, t->fix.body);
    case TM_LSUC:  return term_not_occurs(gidx, t->elim);
    case TM_UNI_V: return term_not_occurs(gidx, t->uni_v_lvl);
    case TM_HOLE:  return 1;  /* holes never contain a global */
    default:
        return 0;  /* conservative: unknown tag — assume F might appear */
    }
}

static int term_strictly_positive(int gidx, Term *t) {
    if (term_not_occurs(gidx, t)) return 1;

    /* Walk application spine to find the head */
    Term *head = t;
    while (head->tag == TM_APP) head = head->app.fun;

    if (head->tag == TM_GLOBAL && head->idx == gidx) {
        /* Head is F. F must not appear in any argument. */
        Term *a = t;
        while (a->tag == TM_APP) {
            if (!term_not_occurs(gidx, a->app.arg)) return 0;
            a = a->app.fun;
        }
        return 1;
    }

    /* Binder types (Π, Σ, W) — F must be absent from the domain,
       and strictly positive in the codomain.
       Allows: Π(n:Nat). F n → F (succ n)
               Σ(n:Nat). F n    (F in cod only)
       Rejects: Π(x:F). …       (F in dom = negative position) */
    if (t->tag == TM_PI || t->tag == TM_SIG || t->tag == TM_W)
        return term_not_occurs(gidx, t->pi.dom) &&
               term_strictly_positive(gidx, t->pi.cod);

    return 0;  /* F appears but not in a recognised positive form */
}

/* ── Inductive data declaration ─────────────────────────────────────────────
 *
 * parse_data(src)  src is the text AFTER the "data" keyword (already
 * preprocessed: fn→\, Pi→Π, ->→→).
 *
 * Grammar (indexed inductive families):
 *   data_decl ::= IDENT ['(' IDENT ':' type [',' IDENT ':' type]* ')']
 *                      [':' Π-chain '→' 'Type'] 'where'
 *                 (IDENT ':' type [';'])*
 *
 * All permanent data (names, telescopes, globals) is allocated in the defs
 * permanent arena so it survives arena_free_all() calls.
 *
 * Returns fam_idx on success, -1 on failure.
 */

#define IND_MAX_PARAMS  16
#define IND_MAX_INDICES  8
#define IND_MAX_CTORS   64
#define IND_MAX_ARITY   32

int parse_data(const char *src) {
    Arena   *perm = def_perm_arena();
    Parser   p    = { src, 0, perm };
    skip_ws(&p);

    /* Family name */
    char *fam_name = read_ident(&p);
    if (!fam_name) {
        fprintf(stderr, "data: expected family name\n");
        return -1;
    }
    fam_name = arena_strdup(perm, fam_name);

    /* Optional uniform parameters: '(' name ':' type [, ...]* ')' */
    int      n_params = 0;
    char    *param_names[IND_MAX_PARAMS];
    Term    *param_types[IND_MAX_PARAMS];
    NameCtx  param_nodes[IND_MAX_PARAMS];
    NameCtx *param_ctx = NULL;

    if (peek(&p) == '(') {
        p.pos++;
        for (;;) {
            char *pname = read_ident(&p);
            if (!pname) {
                fprintf(stderr, "data '%s': expected parameter name\n", fam_name);
                return -1;
            }
            if (!expect(&p, ':')) return -1;
            Term *ptype = parse_expr(&p, param_ctx);
            if (!ptype) return -1;
            if (n_params >= IND_MAX_PARAMS) {
                fprintf(stderr, "data '%s': too many parameters (max %d)\n",
                        fam_name, IND_MAX_PARAMS);
                return -1;
            }
            param_names[n_params] = arena_strdup(perm, pname);
            param_types[n_params] = ptype;
            param_nodes[n_params].name = param_names[n_params];
            param_nodes[n_params].next = param_ctx;
            param_ctx = &param_nodes[n_params];
            n_params++;
            int c = peek(&p);
            if (c == ')') { p.pos++; break; }
            if (c == ',') { p.pos++; continue; }
            fprintf(stderr, "data '%s': expected ',' or ')' in parameter list\n", fam_name);
            return -1;
        }
    }

    /* Optional index telescope: ': I₁ → I₂ → … → Type' before 'where'
       e.g.  data Vec (A : Type) : Nat → Type where ...
             data Fin           : Nat → Type where ...

       parse_expr is greedy and would consume 'where' as a variable, so we
       locate 'where' first and parse only the telescope substring.          */
    int    n_indices = 0;
    char  *idx_names_arr[IND_MAX_INDICES];
    Term  *idx_types_arr[IND_MAX_INDICES];

    skip_ws(&p);
    if (peek(&p) == ':') {
        p.pos++;
        skip_ws(&p);

        /* Find the 'where' keyword so we can bound the parse */
        int where_start = -1;
        for (int s = p.pos; src[s]; s++) {
            if (strncmp(src + s, "where", 5) != 0) continue;
            char before = (s > 0) ? src[s-1] : ' ';
            char after  = src[s+5];
            if ((isalnum((unsigned char)before) || before == '_' || before == '\'') ||
                (isalnum((unsigned char)after)  || after  == '_' || after  == '\''))
                continue;
            where_start = s;
            break;
        }
        if (where_start < 0) {
            fprintf(stderr, "data '%s': index telescope has no 'where'\n", fam_name);
            return -1;
        }

        /* Copy the telescope substring so parse_expr sees a clean \0-terminated string */
        int tlen = where_start - p.pos;
        char *tsrc = (char *)arena_alloc(perm, tlen + 1);
        memcpy(tsrc, src + p.pos, tlen);
        tsrc[tlen] = '\0';

        Parser ptele = { tsrc, 0, perm };
        Term *idx_kind = parse_expr(&ptele, param_ctx);
        if (!idx_kind) {
            fprintf(stderr, "data '%s': failed to parse index telescope\n", fam_name);
            return -1;
        }

        /* Walk the Π-chain; each domain is the type of one index parameter.
           De Bruijn indices are already correct: the j-th domain was parsed in
           a context with j outer index binders + params, matching idx_env in
           the checker. */
        Term *t = idx_kind;
        while (t->tag == TM_PI) {
            if (n_indices >= IND_MAX_INDICES) {
                fprintf(stderr, "data '%s': too many indices (max %d)\n",
                        fam_name, IND_MAX_INDICES);
                return -1;
            }
            idx_names_arr[n_indices] = t->pi.name ? t->pi.name : (char *)"_";
            idx_types_arr[n_indices] = t->pi.dom;
            n_indices++;
            t = t->pi.cod;
        }
        if (t->tag != TM_UNI) {
            fprintf(stderr,
                "data '%s': index kind must be Π-types ending in 'Type' (got tag %d)\n",
                fam_name, (int)t->tag);
            return -1;
        }

        /* Advance main parser past the telescope and onto 'where' */
        p.pos = where_start;
    }

    /* 'where' keyword */
    char *where_kw = read_ident(&p);
    if (!where_kw || strcmp(where_kw, "where") != 0) {
        fprintf(stderr, "data '%s': expected 'where'%s%s\n",
                fam_name,
                where_kw ? ", got '" : "",
                where_kw ? where_kw  : "");
        return -1;
    }

    /* First pass: locate each constructor declaration (NAME ':' type).
       We record the source position of each NAME for re-parsing in pass 2. */
    char *ctor_names[IND_MAX_CTORS];
    int   ctor_src_pos[IND_MAX_CTORS];
    int   n_ctors = 0;
    {
        int s = p.pos;
        while (1) {
            /* skip whitespace and semicolons */
            while (src[s] && (isspace((unsigned char)src[s]) || src[s] == ';'))
                s++;
            if (!src[s]) break;
            /* try to read a constructor name */
            if (!isalpha((unsigned char)src[s]) && src[s] != '_') break;
            int name_start = s;
            while (isalnum((unsigned char)src[s]) || src[s] == '_' || src[s] == '\'')
                s++;
            int after_name = s;
            /* skip whitespace, check for ':' */
            while (isspace((unsigned char)src[s])) s++;
            if (src[s] != ':') break;
            /* record */
            if (n_ctors >= IND_MAX_CTORS) {
                fprintf(stderr, "data '%s': too many constructors (max %d)\n",
                        fam_name, IND_MAX_CTORS);
                return -1;
            }
            int nlen = after_name - name_start;
            char nbuf[IDENT_MAX];
            if (nlen >= IDENT_MAX) nlen = IDENT_MAX - 1;
            memcpy(nbuf, src + name_start, nlen);
            nbuf[nlen] = '\0';
            ctor_names[n_ctors]   = arena_strdup(perm, nbuf);
            ctor_src_pos[n_ctors] = name_start;
            n_ctors++;
            /* skip past ':' and scan to ';' or end, respecting nesting */
            s++;  /* skip ':' */
            int depth = 0;
            while (src[s]) {
                int ch = (unsigned char)src[s];
                if (ch == '(' || ch == '[') { depth++; s++; }
                else if ((ch == ')' || ch == ']') && depth > 0) { depth--; s++; }
                else if ((ch == ')' || ch == ']') && depth == 0) break;
                else if (src[s] == ';' && depth == 0) break;
                else s++;
            }
        }
    }

    /* CtorDef array in perm (telescopes filled in pass 2) */
    CtorDef *ctor_defs = n_ctors > 0
        ? (CtorDef *)arena_alloc(perm, n_ctors * sizeof(CtorDef)) : NULL;
    for (int i = 0; i < n_ctors; i++)
        ctor_defs[i] = (CtorDef){ ctor_names[i], 0, NULL, n_indices, NULL, NULL, -1 };

    /* perm copies of param arrays for IndDef storage */
    char **pnames_perm = NULL;
    Term **ptypes_perm = NULL;
    if (n_params > 0) {
        pnames_perm = (char **)arena_alloc(perm, n_params * sizeof(char *));
        ptypes_perm = (Term **)arena_alloc(perm, n_params * sizeof(Term *));
        for (int i = 0; i < n_params; i++) {
            pnames_perm[i] = param_names[i];
            ptypes_perm[i] = param_types[i];
        }
    }

    /* perm copies of index type array for IndDef storage */
    Term **idx_types_perm = NULL;
    if (n_indices > 0) {
        idx_types_perm = (Term **)arena_alloc(perm, n_indices * sizeof(Term *));
        for (int j = 0; j < n_indices; j++)
            idx_types_perm[j] = idx_types_arr[j];  /* already in perm from parsing */
    }

    IndDef fam_def = {
        fam_name, n_params, pnames_perm, ptypes_perm,
        n_indices, idx_types_perm, n_ctors, ctor_defs, -1, -1
    };
    int fam_idx = ind_add(&fam_def);

    /* Register type constructor as a global.
         type = Π(p0:P0). … Π(i0:I0). … Type_0
         val  = λp0. … λi0. … IndType(fam_idx, n_params+n_indices,
                                        [VAR(n_total-1),…,VAR(0)])

       Index binders are INSIDE param binders in the telescope.
       The de Bruijn indices in idx_types_arr[j] were produced by parse_expr
       with the param context active, so they're correct as-is.           */
    {
        int n_total = n_params + n_indices;
        Term **args = n_total > 0
            ? (Term **)arena_alloc(perm, n_total * sizeof(Term *)) : NULL;
        for (int k = 0; k < n_total; k++)
            args[k] = tm_var(perm, n_total - 1 - k);
        Term *val_term  = tm_indtype(perm, fam_idx, n_total, args);
        Term *type_term = tm_uni(perm, 0);
        /* Wrap index binders innermost (j from last to first) */
        for (int j = n_indices - 1; j >= 0; j--) {
            val_term  = tm_lam(perm, idx_names_arr[j], val_term);
            type_term = tm_pi(perm, idx_names_arr[j], idx_types_arr[j], type_term);
        }
        /* Wrap param binders outermost */
        for (int i = n_params - 1; i >= 0; i--) {
            val_term  = tm_lam(perm, param_names[i], val_term);
            type_term = tm_pi(perm, param_names[i], param_types[i], type_term);
        }
        Val *type_val = nbe_eval(perm, NULL, type_term);
        Val *val_val  = nbe_eval(perm, NULL, val_term);
        int gidx = def_add(fam_name, type_val, val_val);
        ind_get(fam_idx)->type_def_idx = gidx;
    }

    /* Second pass: parse each constructor's type, verify, build globals. */
    int type_ctor_gidx = ind_get(fam_idx)->type_def_idx;
    if (type_ctor_gidx < 0) {
        fprintf(stderr, "data '%s': internal error: type constructor not registered\n",
                fam_name);
        return -1;
    }

    for (int i = 0; i < n_ctors; i++) {
        Parser p2 = { src, ctor_src_pos[i], perm };
        read_ident(&p2);   /* consume constructor name */
        skip_ws(&p2);
        if (p2.src[p2.pos] != ':') {
            fprintf(stderr, "data '%s': expected ':' after constructor '%s'\n",
                    fam_name, ctor_names[i]);
            return -1;
        }
        p2.pos++;

        Term *tele = parse_expr(&p2, param_ctx);
        if (!tele) {
            fprintf(stderr, "data '%s': failed to parse type of constructor '%s'\n",
                    fam_name, ctor_names[i]);
            return -1;
        }

        /* Count arity = Pi binders before the return type */
        int arity = 0;
        Term *t = tele;
        while (t->tag == TM_PI) { arity++; t = t->pi.cod; }

        /* Verify the return type head is this family's type constructor */
        {
            Term *head = t;
            while (head->tag == TM_APP) head = head->app.fun;
            if (head->tag != TM_GLOBAL || head->idx != type_ctor_gidx) {
                fprintf(stderr,
                        "data '%s': constructor '%s' return type is not '%s'\n",
                        fam_name, ctor_names[i], fam_name);
                return -1;
            }
        }

        /* is_recursive[j] = 1 if arg j's type head is the family's type ctor */
        char *is_rec = NULL;
        if (arity > 0) {
            is_rec = (char *)arena_alloc(perm, arity);
            Term *u = tele;
            for (int j = 0; j < arity; j++) {
                Term *head = u->pi.dom;
                while (head->tag == TM_APP) head = head->app.fun;
                is_rec[j] = (head->tag == TM_GLOBAL &&
                             head->idx == type_ctor_gidx) ? 1 : 0;
                u = u->pi.cod;
            }
        }

        /* Strict positivity: each argument type must not place the family
           in a negative position (i.e., to the left of a function arrow
           where it is not the head, or nested inside another type's args).
           A negative occurrence breaks strong normalisation and consistency. */
        {
            Term *u = tele;
            for (int j = 0; j < arity; j++) {
                Term *dom = u->pi.dom;
                if (!term_strictly_positive(type_ctor_gidx, dom)) {
                    /* Try to give a more specific diagnosis */
                    const char *reason;
                    /* Walk the dom's own Pi/Sg/W chain: if F is in any domain
                       of an inner binder, it is in a negative position. */
                    Term *inner = dom;
                    int found_neg = 0;
                    while (inner->tag == TM_PI || inner->tag == TM_SIG ||
                           inner->tag == TM_W) {
                        if (!term_not_occurs(type_ctor_gidx, inner->pi.dom)) {
                            found_neg = 1;
                            break;
                        }
                        inner = inner->pi.cod;
                    }
                    if (found_neg)
                        reason = "appears to the left of '→' (negative position)";
                    else if (!term_not_occurs(type_ctor_gidx, dom))
                        reason = "appears inside another type's arguments (nested, not supported)";
                    else
                        reason = "appears in an unrecognised non-positive form";
                    fprintf(stderr,
                        "data '%s': constructor '%s': argument %d is not "
                        "strictly positive\n"
                        "  '%s' %s\n",
                        fam_name, ctor_names[i], j, fam_name, reason);
                    return -1;
                }
                u = u->pi.cod;
            }
        }

        /* Collect arg names from Pi binders */
        if (arity > IND_MAX_ARITY) {
            fprintf(stderr,
                "data '%s': constructor '%s' has %d arguments (max %d)\n",
                fam_name, ctor_names[i], arity, IND_MAX_ARITY);
            return -1;
        }
        char *arg_names[IND_MAX_ARITY];
        {
            Term *u = tele;
            for (int j = 0; j < arity; j++) {
                arg_names[j] = (u->tag == TM_PI) ? u->pi.name : (char *)"_";
                u = u->pi.cod;
            }
        }

        ctor_defs[i].arity        = arity;
        ctor_defs[i].telescope    = tele;
        ctor_defs[i].is_recursive = is_rec;

        /* Register constructor as a global.
             type = Π(p0:P0). … tele
             val  = λp0. … λa0. … IndCon(fam, i, n_total,
                                          [VAR(n_total-1),…,VAR(0)])       */
        {
            int n_total = n_params + arity;
            Term **con_args = n_total > 0
                ? (Term **)arena_alloc(perm, n_total * sizeof(Term *)) : NULL;
            for (int j = 0; j < n_total; j++)
                con_args[j] = tm_var(perm, n_total - 1 - j);
            Term *val_term = tm_indcon(perm, fam_idx, i, n_total, con_args);
            for (int j = arity - 1; j >= 0; j--)
                val_term = tm_lam(perm, arg_names[j], val_term);
            for (int j = n_params - 1; j >= 0; j--)
                val_term = tm_lam(perm, param_names[j], val_term);

            Term *type_term = tele;
            for (int j = n_params - 1; j >= 0; j--)
                type_term = tm_pi(perm, param_names[j], param_types[j], type_term);

            Val *type_val = nbe_eval(perm, NULL, type_term);
            Val *val_val  = nbe_eval(perm, NULL, val_term);
            int gidx = def_add(ctor_names[i], type_val, val_val);
            ctor_defs[i].def_idx = gidx;
        }
    }

    return fam_idx;
}
