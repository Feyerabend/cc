#include "node.h"
#include "reduce.h"
#include "../core/term.h"
#include "../core/defs.h"

/* Heap */

#define HEAP_INIT_CAP 8192

void heap_init(Heap *h) {
    h->cap   = HEAP_INIT_CAP;
    h->size  = 0;
    h->nodes = (Node *)malloc(h->cap * sizeof(Node));
    if (!h->nodes) { perror("heap_init"); exit(1); }
}

void heap_free(Heap *h) {
    free(h->nodes);
    h->nodes = NULL;
    h->size  = 0;
    h->cap   = 0;
}

NodeRef heap_alloc(Heap *h) {
    if (h->size >= h->cap) {
        h->cap *= 2;
        h->nodes = (Node *)realloc(h->nodes, h->cap * sizeof(Node));
        if (!h->nodes) { perror("heap_alloc"); exit(1); }
    }
    NodeRef r = (NodeRef)h->size++;
    Node *n = &h->nodes[r];
    n->tag   = 0;
    n->flags = 0;
    n->_pad  = 0;
    n->ch[0] = NULL_REF;
    n->ch[1] = NULL_REF;
    n->ch[2] = NULL_REF;
    n->ch[3] = NULL_REF;
    n->ch[4] = NULL_REF;
    n->ch[5] = NULL_REF;
    n->name  = NULL;
    n->aux   = NULL;
    return r;
}

/* Environment lookup */

NodeRef env_lookup(Heap *h, NodeRef env, int idx) {
    NodeRef cur = node_deref(h, env);
    for (int i = 0; i < idx; i++) {
        if (cur == NULL_REF) {
            fprintf(stderr, "env_lookup: free variable (de Bruijn index %d)\n", idx);
            exit(1);
        }
        cur = node_deref(h, h->nodes[cur].ch[1]);
    }
    if (cur == NULL_REF) {
        fprintf(stderr, "env_lookup: empty environment at index 0\n");
        exit(1);
    }
    return h->nodes[cur].ch[0];
}

/* Internal helpers */

static NodeRef mk0(Heap *h, NodeTag tag, uint8_t flags) {
    NodeRef r = heap_alloc(h);
    h->nodes[r].tag   = (uint8_t)tag;
    h->nodes[r].flags = flags;
    return r;
}

/* Constructors */

NodeRef mk_app(Heap *h, NodeRef fun, NodeRef arg) {
    NodeRef r = mk0(h, ND_APP, 0);
    h->nodes[r].ch[0] = fun;
    h->nodes[r].ch[1] = arg;
    return r;
}

NodeRef mk_lam(Heap *h, char *name, NodeRef env, void *body_term) {
    NodeRef r = mk0(h, ND_LAM, NF_WHNF);
    h->nodes[r].ch[0] = env;
    h->nodes[r].name  = name;
    h->nodes[r].aux   = body_term;
    return r;
}

NodeRef mk_env(Heap *h, NodeRef val, NodeRef next) {
    NodeRef r = mk0(h, ND_ENV, NF_WHNF);
    h->nodes[r].ch[0] = val;
    h->nodes[r].ch[1] = next;
    return r;
}

NodeRef mk_var(Heap *h, int lvl) {
    NodeRef r = mk0(h, ND_VAR, NF_WHNF | NF_NF);
    h->nodes[r].lvl = lvl;
    return r;
}

NodeRef mk_thunk(Heap *h, void *expr_term, NodeRef env) {
    NodeRef r = mk0(h, ND_THUNK, 0);
    h->nodes[r].ch[0] = env;
    h->nodes[r].aux   = expr_term;
    return r;
}

NodeRef mk_zero (Heap *h) { return mk0(h, ND_ZERO,  NF_WHNF | NF_NF); }
NodeRef mk_nat  (Heap *h) { return mk0(h, ND_NAT,   NF_WHNF | NF_NF); }
NodeRef mk_true (Heap *h) { return mk0(h, ND_TRUE,  NF_WHNF | NF_NF); }
NodeRef mk_false(Heap *h) { return mk0(h, ND_FALSE, NF_WHNF | NF_NF); }
NodeRef mk_bool (Heap *h) { return mk0(h, ND_BOOL,  NF_WHNF | NF_NF); }
NodeRef mk_star (Heap *h) { return mk0(h, ND_STAR,  NF_WHNF | NF_NF); }
NodeRef mk_unit (Heap *h) { return mk0(h, ND_UNIT,  NF_WHNF | NF_NF); }
NodeRef mk_empty(Heap *h) { return mk0(h, ND_EMPTY, NF_WHNF | NF_NF); }
NodeRef mk_s1   (Heap *h) { return mk0(h, ND_S1,    NF_WHNF | NF_NF); }
NodeRef mk_base (Heap *h) { return mk0(h, ND_BASE,  NF_WHNF | NF_NF); }
NodeRef mk_loop (Heap *h) { return mk0(h, ND_LOOP,  NF_WHNF | NF_NF); }
NodeRef mk_trunc(Heap *h) { return mk0(h, ND_TRUNC, NF_WHNF | NF_NF); }
NodeRef mk_trint(Heap *h) { return mk0(h, ND_TRINT, NF_WHNF | NF_NF); }

NodeRef mk_succ(Heap *h, NodeRef pred) {
    NodeRef r = mk0(h, ND_SUCC, NF_WHNF);
    h->nodes[r].ch[0] = pred;
    return r;
}

NodeRef mk_refl(Heap *h, NodeRef t) {
    NodeRef r = mk0(h, ND_REFL, NF_WHNF);
    h->nodes[r].ch[0] = t;
    return r;
}

NodeRef mk_inl(Heap *h, NodeRef t) {
    NodeRef r = mk0(h, ND_INL, NF_WHNF);
    h->nodes[r].ch[0] = t;
    return r;
}

NodeRef mk_inr(Heap *h, NodeRef t) {
    NodeRef r = mk0(h, ND_INR, NF_WHNF);
    h->nodes[r].ch[0] = t;
    return r;
}

NodeRef mk_pair(Heap *h, NodeRef fst, NodeRef snd) {
    NodeRef r = mk0(h, ND_PAIR, NF_WHNF);
    h->nodes[r].ch[0] = fst;
    h->nodes[r].ch[1] = snd;
    return r;
}

NodeRef mk_sum(Heap *h, NodeRef l, NodeRef rn) {
    NodeRef r = mk0(h, ND_SUM, NF_WHNF);
    h->nodes[r].ch[0] = l;
    h->nodes[r].ch[1] = rn;
    return r;
}

NodeRef mk_uni(Heap *h, int ulvl) {
    NodeRef r = mk0(h, ND_UNI, NF_WHNF | NF_NF);
    h->nodes[r].ulvl = ulvl;
    return r;
}

NodeRef mk_global(Heap *h, int idx) {
    NodeRef r = mk0(h, ND_GLOBAL, 0);
    h->nodes[r].lvl = idx;
    return r;
}

/* Dump graph (raw heap) */

static const char *tag_name(NodeTag t) {
    switch (t) {
    case ND_APP:          return "APP";
    case ND_LAM:          return "LAM";
    case ND_ENV:          return "ENV";
    case ND_VAR:          return "VAR";
    case ND_REF:          return "REF";
    case ND_THUNK:        return "THUNK";
    case ND_BLACKHOLE_TAG:return "BLACKHOLE";
    case ND_PI:           return "PI";
    case ND_SIGMA:        return "SIGMA";
    case ND_ID:           return "ID";
    case ND_UNI:          return "UNI";
    case ND_W:            return "W";
    case ND_SUM:          return "SUM";
    case ND_ZERO:         return "ZERO";
    case ND_SUCC:         return "SUCC";
    case ND_NAT:          return "NAT";
    case ND_TRUE:         return "TRUE";
    case ND_FALSE:        return "FALSE";
    case ND_BOOL:         return "BOOL";
    case ND_STAR:         return "STAR";
    case ND_UNIT:         return "UNIT";
    case ND_EMPTY:        return "EMPTY";
    case ND_PAIR:         return "PAIR";
    case ND_REFL:         return "REFL";
    case ND_INL:          return "INL";
    case ND_INR:          return "INR";
    case ND_SUP:          return "SUP";
    case ND_S1:           return "S1";
    case ND_BASE:         return "BASE";
    case ND_TRUNC:        return "TRUNC";
    case ND_TRINT:        return "TRINT";
    case ND_LOOP:         return "LOOP";
    case ND_FST:          return "FST";
    case ND_SND:          return "SND";
    case ND_NATREC:       return "NATREC";
    case ND_BOOLREC:      return "BOOLREC";
    case ND_S1REC:        return "S1REC";
    case ND_TRUNCREC:     return "TRUNCREC";
    case ND_CASESPLIT:    return "CASESPLIT";
    case ND_ABORT:        return "ABORT";
    case ND_UNITREC:      return "UNITREC";
    case ND_J:            return "J";
    case ND_WREC:         return "WREC";
    case ND_GLOBAL:       return "GLOBAL";
    case ND_CORE:         return "CORE";
    case ND_INDTYPE:      return "INDTYPE";
    case ND_INDCON:       return "INDCON";
    case ND_INDREC:       return "INDREC";
    case ND_FIX:          return "FIX";
    case ND_LEVEL:        return "LEVEL";
    case ND_LZERO:        return "LZERO";
    case ND_LSUC:         return "LSUC";
    case ND_UNI_V:        return "UNI_V";
    default:              return "?";
    }
}

void node_dump_graph(Heap *h) {
    for (size_t i = 0; i < h->size; i++) {
        Node *n = &h->nodes[i];
        fprintf(stderr, "[%4zu: %-9s", i, tag_name((NodeTag)n->tag));
        for (int j = 0; j < 6; j++) {
            if (n->ch[j] != NULL_REF) fprintf(stderr, " %5u", n->ch[j]);
            else                      fprintf(stderr, "     -");
        }
        if (n->name) fprintf(stderr, "  name=%s", n->name);
        if ((NodeTag)n->tag == ND_VAR || (NodeTag)n->tag == ND_GLOBAL ||
            (NodeTag)n->tag == ND_INDTYPE || (NodeTag)n->tag == ND_INDREC)
            fprintf(stderr, "  lvl=%d", n->lvl);
        if ((NodeTag)n->tag == ND_INDCON)
            fprintf(stderr, "  fam=%d ctor=%d", (n->lvl>>16)&0xFFFF, n->lvl&0xFFFF);
        if ((NodeTag)n->tag == ND_UNI)
            fprintf(stderr, "  ulvl=%d", n->ulvl);
        fprintf(stderr, "  flags=0x%x]\n", n->flags);
    }
}

/* Neutral-chain helpers */

int node_is_elim_tag(NodeTag t) {
    switch (t) {
    case ND_FST: case ND_SND:
    case ND_NATREC: case ND_BOOLREC: case ND_S1REC:
    case ND_TRUNCREC: case ND_CASESPLIT: case ND_ABORT:
    case ND_UNITREC: case ND_J: case ND_WREC:
    case ND_INDREC:
        return 1;
    default: return 0;
    }
}

/* Scrutinee child NodeRef for any eliminator. */
NodeRef node_scrut_of(Heap *h, NodeRef r) {
    switch ((NodeTag)h->nodes[r].tag) {
    case ND_FST:
    case ND_SND:      return h->nodes[r].ch[0];
    case ND_INDREC:   return h->nodes[r].ch[0];  /* scrut at ch[0] */
    case ND_ABORT:    return h->nodes[r].ch[1];
    case ND_UNITREC:
    case ND_WREC:     return h->nodes[r].ch[2];
    case ND_J:        return h->nodes[r].ch[5];
    default:          return h->nodes[r].ch[3]; /* NATREC BOOLREC S1REC TRUNCREC CASESPLIT */
    }
}

/* A node is neutral if it is ND_LOOP / open ND_VAR, or a stuck
 * eliminator (NF_WHNF set) whose scrutinee is also neutral. */
static int is_neutral(Heap *h, NodeRef r) {
    r = node_deref(h, r);
    if (r == NULL_REF) return 0;
    NodeTag tag = (NodeTag)h->nodes[r].tag;
    if (tag == ND_LOOP || tag == ND_VAR) return 1;
    if (!node_is_elim_tag(tag))  return 0;
    if (!(h->nodes[r].flags & NF_WHNF)) return 0;
    return is_neutral(h, node_scrut_of(h, r));
}

/* Print the non-scrutinee args of an eliminator as one spine frame. */
static void print_elim_frame(Heap *h, NodeRef r, int depth) {
    switch ((NodeTag)h->nodes[r].tag) {
    case ND_FST:  printf("fst"); break;
    case ND_SND:  printf("snd"); break;
    case ND_NATREC:
        printf("natrec(");
        node_print(h, h->nodes[r].ch[0], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[1], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[2], depth, 0); printf(")");
        break;
    case ND_BOOLREC:
        printf("boolrec(");
        node_print(h, h->nodes[r].ch[0], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[1], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[2], depth, 0); printf(")");
        break;
    case ND_S1REC:
        printf("S1rec(");
        node_print(h, h->nodes[r].ch[0], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[1], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[2], depth, 0); printf(")");
        break;
    case ND_TRUNCREC:
        printf("truncrec(");
        node_print(h, h->nodes[r].ch[0], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[1], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[2], depth, 0); printf(")");
        break;
    case ND_CASESPLIT:
        printf("case(");
        node_print(h, h->nodes[r].ch[0], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[1], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[2], depth, 0); printf(")");
        break;
    case ND_ABORT:
        printf("abort(");
        node_print(h, h->nodes[r].ch[0], depth, 0); printf(")");
        break;
    case ND_UNITREC:
        printf("unitrec(");
        node_print(h, h->nodes[r].ch[0], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[1], depth, 0); printf(")");
        break;
    case ND_J:
        printf("J(");
        node_print(h, h->nodes[r].ch[0], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[1], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[2], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[3], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[4], depth, 0); printf(")");
        break;
    case ND_WREC:
        printf("wrec(");
        node_print(h, h->nodes[r].ch[0], depth, 0); printf(", ");
        node_print(h, h->nodes[r].ch[1], depth, 0); printf(")");
        break;
    case ND_INDREC: {
        int fam_idx = h->nodes[r].lvl;
        IndDef *fam = ind_get(fam_idx);
        if (fam->n_ctors > 4) { printf("<indrec:%s/overflow>", fam->name); break; }
        printf("indrec(%s, ", fam->name);
        node_print(h, h->nodes[r].ch[1], depth, 0);  /* motive */
        for (int i = 0; i < fam->n_ctors; i++) {
            printf(", ");
            node_print(h, h->nodes[r].ch[2+i], depth, 0);
        }
        printf(")");
        break;
    }
    default: printf("<%s>", tag_name((NodeTag)h->nodes[r].tag)); break;
    }
}

/* Walk inward to the sentinel, then unwind printing each frame. */
static void print_neutral_inner(Heap *h, NodeRef r, int depth) {
    r = node_deref(h, r);
    if (r == NULL_REF) { printf("?"); return; }
    NodeTag tag = (NodeTag)h->nodes[r].tag;
    if (tag == ND_LOOP) { printf("loop"); return; }
    if (tag == ND_VAR)  { printf("<var:%d>", h->nodes[r].lvl); return; }
    print_neutral_inner(h, node_scrut_of(h, r), depth);
    printf(" · ");
    print_elim_frame(h, r, depth);
}

/* Pretty printer */

void node_print(Heap *h, NodeRef r, int depth, int prec) {
    (void)depth;
    if (r == NULL_REF) { printf("?"); return; }
    r = node_deref(h, r);
    if (r == NULL_REF) { printf("?"); return; }

    NodeTag tag = (NodeTag)h->nodes[r].tag;

    switch (tag) {
    case ND_TRUE:  printf("true");  break;
    case ND_FALSE: printf("false"); break;
    case ND_ZERO:  printf("zero");  break;
    case ND_NAT:   printf("Nat");   break;
    case ND_BOOL:  printf("Bool");  break;
    case ND_UNIT:  printf("Unit");  break;
    case ND_EMPTY: printf("Empty"); break;
    case ND_STAR:  printf("star");  break;
    case ND_S1:    printf("S1");    break;
    case ND_BASE:  printf("base");  break;
    case ND_LOOP:  printf("loop");  break;
    case ND_UNI:
        if (h->nodes[r].ulvl == 0) printf("Type");
        else                       printf("Type_%d", h->nodes[r].ulvl);
        break;
    case ND_SUCC: {
        int wrap = (prec >= 2);
        if (wrap) printf("(");
        printf("succ ");
        node_print(h, h->nodes[r].ch[0], depth, 2);
        if (wrap) printf(")");
        break;
    }
    case ND_REFL: {
        int wrap = (prec >= 2);
        if (wrap) printf("(");
        printf("refl ");
        node_print(h, h->nodes[r].ch[0], depth, 2);
        if (wrap) printf(")");
        break;
    }
    case ND_INL: {
        int wrap = (prec >= 2);
        if (wrap) printf("(");
        printf("inl ");
        node_print(h, h->nodes[r].ch[0], depth, 2);
        if (wrap) printf(")");
        break;
    }
    case ND_INR: {
        int wrap = (prec >= 2);
        if (wrap) printf("(");
        printf("inr ");
        node_print(h, h->nodes[r].ch[0], depth, 2);
        if (wrap) printf(")");
        break;
    }
    case ND_PAIR:
        printf("(");
        node_print(h, h->nodes[r].ch[0], depth, 0);
        printf(", ");
        node_print(h, h->nodes[r].ch[1], depth, 0);
        printf(")");
        break;
    case ND_TRUNC: printf("trunc"); break;
    case ND_TRINT: printf("trint"); break;
    case ND_LAM:
        /* Lambda in result — print body as raw term (approximation) */
        printf("<fn>");
        break;
    case ND_VAR:
        printf("<var:%d>", h->nodes[r].lvl);
        break;
    case ND_GLOBAL:
        switch (h->nodes[r].lvl) {
        case -1: printf("ua");     break;
        case -2: printf("funext"); break;
        case -3: printf("squash"); break;
        default: printf("<global:%d>", h->nodes[r].lvl); break;
        }
        break;
    case ND_APP:
        /* Stuck application (neutral function applied to argument) */
        printf("<app>");
        break;
    case ND_THUNK:
        printf("<thunk>");
        break;
    /* Stuck eliminators: print as neutral chain if scrutinee is sentinel,
     * otherwise fall back to the generic <TAG> form. */
    case ND_FST: case ND_SND:
    case ND_NATREC: case ND_BOOLREC: case ND_S1REC:
    case ND_TRUNCREC: case ND_CASESPLIT: case ND_ABORT:
    case ND_UNITREC: case ND_J: case ND_WREC: case ND_INDREC:
        if (is_neutral(h, r)) {
            printf("[");
            print_neutral_inner(h, r, depth);
            printf("]");
        } else {
            printf("<%s>", tag_name(tag));
        }
        break;
    case ND_INDTYPE: {
        int fam_idx = h->nodes[r].lvl;
        IndDef *fam = ind_get(fam_idx);
        int n_total = fam->n_params + fam->n_indices;
        if (n_total > 6) { printf("<indtype:%s/overflow>", fam->name); break; }
        if (n_total == 0) {
            printf("%s", fam->name);
        } else {
            int wrap = (prec >= 2);
            if (wrap) printf("(");
            printf("%s", fam->name);
            for (int i = 0; i < n_total; i++) {
                printf(" ");
                node_print(h, h->nodes[r].ch[i], depth, 2);
            }
            if (wrap) printf(")");
        }
        break;
    }
    case ND_INDCON: {
        int packed    = h->nodes[r].lvl;
        int fam_idx   = (packed >> 16) & 0xFFFF;
        int ctor_idx  = packed & 0xFFFF;
        IndDef  *fam  = ind_get(fam_idx);
        if (ctor_idx >= fam->n_ctors) {
            printf("<indcon:bad-ctor-%d>", ctor_idx);
            break;
        }
        CtorDef *ctor = &fam->ctors[ctor_idx];
        int n_params  = fam->n_params;
        int arity     = ctor->arity;
        int n_total   = n_params + arity;
        if (n_total > 6) { printf("<indcon:%s/overflow>", ctor->name); break; }
        if (arity == 0) {
            printf("%s", ctor->name);
        } else {
            int wrap = (prec >= 2);
            if (wrap) printf("(");
            printf("%s", ctor->name);
            for (int i = n_params; i < n_total; i++) {
                printf(" ");
                node_print(h, h->nodes[r].ch[i], depth, 2);
            }
            if (wrap) printf(")");
        }
        break;
    }
    case ND_FIX: {
        int wrap = (prec >= 2);
        if (wrap) printf("(");
        printf("fix ");
        node_print(h, h->nodes[r].ch[0], depth, 2);
        if (wrap) printf(")");
        break;
    }
    case ND_LEVEL: printf("Level"); break;
    case ND_LZERO: printf("lzero"); break;
    case ND_LSUC: {
        int wrap = (prec >= 2);
        if (wrap) printf("(");
        printf("lsuc ");
        node_print(h, h->nodes[r].ch[0], depth, 2);
        if (wrap) printf(")");
        break;
    }
    case ND_UNI_V:
        printf("Type_(");
        node_print(h, h->nodes[r].ch[0], depth, 0);
        printf(")");
        break;
    default:
        printf("<%s>", tag_name(tag));
        break;
    }
}

/* ── Convertibility ──────────────────────────────────────────────────
 *
 * node_conv: structural α-equivalence of two NF (or WHNF) heap nodes.
 *
 * Thunks (PI/SIGMA/W cod under a binder) are compared by structural
 * Term* equality via term_eq + matching env chains.  Lambdas are
 * conservative: Term* body pointer must match (no eta-expansion).
 * ──────────────────────────────────────────────────────────────────── */

static int term_eq(const Term *t1, const Term *t2) {
    if (t1 == t2)   return 1;
    if (!t1 || !t2) return 0;
    if (t1->tag != t2->tag) return 0;
    switch (t1->tag) {
    /* Atoms */
    case TM_NAT: case TM_BOOL: case TM_UNIT: case TM_EMPTY:
    case TM_ZERO: case TM_TRUE: case TM_FALSE: case TM_STAR:
    case TM_CIRCLE: case TM_BASE: case TM_LOOP:
    case TM_TRUNC: case TM_TRINT: case TM_SQUASH:
    case TM_UA: case TM_FUNEXT:
        return 1;
    case TM_VAR:    return t1->idx    == t2->idx;
    case TM_UNI:    return t1->ulevel == t2->ulevel;
    case TM_GLOBAL: return t1->idx    == t2->idx;
    /* Single-child */
    case TM_FST: case TM_SND: case TM_SUCC: case TM_INL: case TM_INR:
        return term_eq(t1->elim, t2->elim);
    case TM_REFL:
        return term_eq(t1->refl, t2->refl);
    /* Two-child */
    case TM_LAM:  return term_eq(t1->lam.body,  t2->lam.body);  /* de Bruijn: names irrelevant */
    case TM_APP:  return term_eq(t1->app.fun,   t2->app.fun)  && term_eq(t1->app.arg,   t2->app.arg);
    case TM_ANN:  return term_eq(t1->ann.term,  t2->ann.term) && term_eq(t1->ann.type,  t2->ann.type);
    case TM_PAIR: return term_eq(t1->pair.fst,  t2->pair.fst) && term_eq(t1->pair.snd,  t2->pair.snd);
    case TM_SUM:  return term_eq(t1->sum_t.left,t2->sum_t.left)&&term_eq(t1->sum_t.right,t2->sum_t.right);
    case TM_SUP:  return term_eq(t1->sup.label, t2->sup.label)&& term_eq(t1->sup.children,t2->sup.children);
    /* Three-child */
    case TM_ID:
        return term_eq(t1->id.ty,  t2->id.ty)  &&
               term_eq(t1->id.lhs, t2->id.lhs) &&
               term_eq(t1->id.rhs, t2->id.rhs);
    /* Binder types (PI/SIG/W share layout) */
    case TM_PI: case TM_SIG: case TM_W:
        return term_eq(t1->pi.dom, t2->pi.dom) && term_eq(t1->pi.cod, t2->pi.cod);
    /* Eliminators */
    case TM_J:
        return term_eq(t1->j.ty,       t2->j.ty)       &&
               term_eq(t1->j.lhs,      t2->j.lhs)      &&
               term_eq(t1->j.motive,   t2->j.motive)   &&
               term_eq(t1->j.base,     t2->j.base)      &&
               term_eq(t1->j.endpoint, t2->j.endpoint) &&
               term_eq(t1->j.proof,    t2->j.proof);
    case TM_NATREC:
        return term_eq(t1->natrec.motive, t2->natrec.motive) &&
               term_eq(t1->natrec.base,   t2->natrec.base)   &&
               term_eq(t1->natrec.step,   t2->natrec.step)   &&
               term_eq(t1->natrec.scrut,  t2->natrec.scrut);
    case TM_BOOLREC:
        return term_eq(t1->boolrec.motive, t2->boolrec.motive) &&
               term_eq(t1->boolrec.tcase,  t2->boolrec.tcase)  &&
               term_eq(t1->boolrec.fcase,  t2->boolrec.fcase)  &&
               term_eq(t1->boolrec.scrut,  t2->boolrec.scrut);
    case TM_WREC:
        return term_eq(t1->wrec.motive, t2->wrec.motive) &&
               term_eq(t1->wrec.step,   t2->wrec.step)   &&
               term_eq(t1->wrec.scrut,  t2->wrec.scrut);
    case TM_ABORT:
        return term_eq(t1->abort_t.motive, t2->abort_t.motive) &&
               term_eq(t1->abort_t.scrut,  t2->abort_t.scrut);
    case TM_UNITREC:
        return term_eq(t1->unitrec_t.motive, t2->unitrec_t.motive) &&
               term_eq(t1->unitrec_t.base,   t2->unitrec_t.base)   &&
               term_eq(t1->unitrec_t.scrut,  t2->unitrec_t.scrut);
    case TM_CASESPLIT:
        return term_eq(t1->casesplit_t.motive, t2->casesplit_t.motive) &&
               term_eq(t1->casesplit_t.lcase,  t2->casesplit_t.lcase)  &&
               term_eq(t1->casesplit_t.rcase,  t2->casesplit_t.rcase)  &&
               term_eq(t1->casesplit_t.scrut,  t2->casesplit_t.scrut);
    case TM_TRUNCREC:
        return term_eq(t1->truncrec_t.ty_a,  t2->truncrec_t.ty_a)  &&
               term_eq(t1->truncrec_t.ty_b,  t2->truncrec_t.ty_b)  &&
               term_eq(t1->truncrec_t.func,  t2->truncrec_t.func)  &&
               term_eq(t1->truncrec_t.scrut, t2->truncrec_t.scrut);
    case TM_CIRCREC:
        return term_eq(t1->circrec_t.motive,    t2->circrec_t.motive)    &&
               term_eq(t1->circrec_t.base_case, t2->circrec_t.base_case) &&
               term_eq(t1->circrec_t.loop_case, t2->circrec_t.loop_case) &&
               term_eq(t1->circrec_t.scrut,     t2->circrec_t.scrut);
    case TM_INDTYPE: {
        if (t1->indtype.fam_idx != t2->indtype.fam_idx) return 0;
        if (t1->indtype.n_args  != t2->indtype.n_args)  return 0;
        for (int i = 0; i < t1->indtype.n_args; i++)
            if (!term_eq(t1->indtype.args[i], t2->indtype.args[i])) return 0;
        return 1;
    }
    case TM_INDCON: {
        if (t1->indcon.fam_idx  != t2->indcon.fam_idx)  return 0;
        if (t1->indcon.ctor_idx != t2->indcon.ctor_idx) return 0;
        if (t1->indcon.n_args   != t2->indcon.n_args)   return 0;
        for (int i = 0; i < t1->indcon.n_args; i++)
            if (!term_eq(t1->indcon.args[i], t2->indcon.args[i])) return 0;
        return 1;
    }
    case TM_INDREC: {
        if (t1->indrec.fam_idx != t2->indrec.fam_idx) return 0;
        if (t1->indrec.n_cases != t2->indrec.n_cases) return 0;
        if (!term_eq(t1->indrec.motive, t2->indrec.motive)) return 0;
        if (!term_eq(t1->indrec.scrut,  t2->indrec.scrut))  return 0;
        for (int i = 0; i < t1->indrec.n_cases; i++)
            if (!term_eq(t1->indrec.cases[i], t2->indrec.cases[i])) return 0;
        return 1;
    }
    case TM_FIX:
        return term_eq(t1->fix.body, t2->fix.body);
    case TM_LEVEL:
    case TM_LZERO:
        return 1;
    case TM_LSUC:
        return term_eq(t1->elim, t2->elim);
    case TM_UNI_V:
        return term_eq(t1->uni_v_lvl, t2->uni_v_lvl);
    default: return 0;
    }
}

/* Compare two ND_ENV chains entry-by-entry. */
static int node_conv_env(Heap *h, Arena *a, NodeRef e1, NodeRef e2) {
    e1 = node_deref(h, e1);
    e2 = node_deref(h, e2);
    if (e1 == e2) return 1;  /* covers NULL==NULL */
    if (e1 == NULL_REF || e2 == NULL_REF) return 0;
    if (h->nodes[e1].tag != ND_ENV || h->nodes[e2].tag != ND_ENV) return 0;
    return node_conv(h, a, h->nodes[e1].ch[0], h->nodes[e2].ch[0]) &&
           node_conv_env(h, a, h->nodes[e1].ch[1], h->nodes[e2].ch[1]);
}

/* Compare two PI/SIGMA/W cod nodes by forcing both with the same fresh sentinel.
 * Using the same sentinel ensures that binder-variable occurrences in both cods
 * resolve to the identical heap node and compare equal. */
static int conv_cod(Heap *h, Arena *a, NodeRef cod1, NodeRef cod2) {
    cod1 = node_deref(h, cod1);
    cod2 = node_deref(h, cod2);
    if (cod1 == cod2) return 1;
    if (cod1 == NULL_REF || cod2 == NULL_REF) return 0;
    if (h->nodes[cod1].tag != ND_THUNK || h->nodes[cod2].tag != ND_THUNK)
        return node_conv(h, a, cod1, cod2);

    /* Capture thunk contents before heap mutation */
    void    *body1 = h->nodes[cod1].aux,  *body2 = h->nodes[cod2].aux;
    NodeRef  env1  = h->nodes[cod1].ch[0], env2  = h->nodes[cod2].ch[0];

    /* Same sentinel for both sides — binder occurrences compare equal by NodeRef */
    NodeRef sentinel = mk_var(h, BINDER_LVL);
    NodeRef copy1 = mk_thunk(h, body1, mk_env(h, sentinel, env1));
    NodeRef copy2 = mk_thunk(h, body2, mk_env(h, sentinel, env2));
    nf(h, a, copy1);
    nf(h, a, copy2);
    return node_conv(h, a, copy1, copy2);
}

int node_conv(Heap *h, Arena *a, NodeRef r1, NodeRef r2) {
    r1 = node_deref(h, r1);
    r2 = node_deref(h, r2);
    if (r1 == r2) return 1;
    if (r1 == NULL_REF || r2 == NULL_REF) return 0;

    NodeTag t1 = (NodeTag)h->nodes[r1].tag;
    NodeTag t2 = (NodeTag)h->nodes[r2].tag;
    if (t1 != t2) return 0;

    /* Unforced thunk outside a binder context: compare Term* structurally.
     * This path is only hit when a thunk appears somewhere other than a PI/SIGMA/W
     * cod position (those go through conv_cod instead). */
    if (t1 == ND_THUNK)
        return term_eq((Term *)h->nodes[r1].aux, (Term *)h->nodes[r2].aux) &&
               node_conv_env(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0]);

    switch (t1) {
    /* Sentinels */
    case ND_LOOP:   return 1;
    /* BINDER_LVL sentinels compare by NodeRef (already handled by r1==r2 above) */
    case ND_VAR:    return h->nodes[r1].lvl  == h->nodes[r2].lvl;
    /* Atomic values / types */
    case ND_ZERO: case ND_TRUE: case ND_FALSE: case ND_STAR:
    case ND_BASE: case ND_NAT: case ND_BOOL: case ND_UNIT:
    case ND_EMPTY: case ND_S1: case ND_TRUNC: case ND_TRINT:
        return 1;
    case ND_UNI:    return h->nodes[r1].ulvl == h->nodes[r2].ulvl;
    case ND_GLOBAL: return h->nodes[r1].lvl  == h->nodes[r2].lvl;
    /* Single-child */
    case ND_SUCC: case ND_REFL: case ND_INL: case ND_INR:
    case ND_FST:  case ND_SND:
        return node_conv(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0]);
    /* Two-child, no binder */
    case ND_PAIR: case ND_SUM: case ND_SUP: case ND_APP: case ND_ABORT:
        return node_conv(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0]) &&
               node_conv(h, a, h->nodes[r1].ch[1], h->nodes[r2].ch[1]);
    /* Pi/Sigma/W: dom by node_conv, cod by conv_cod (forces both with shared sentinel) */
    case ND_PI: case ND_SIGMA: case ND_W:
        return node_conv(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0]) &&
               conv_cod(h, a, h->nodes[r1].ch[1], h->nodes[r2].ch[1]);
    /* Three-child */
    case ND_ID: case ND_UNITREC: case ND_WREC:
        return node_conv(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0]) &&
               node_conv(h, a, h->nodes[r1].ch[1], h->nodes[r2].ch[1]) &&
               node_conv(h, a, h->nodes[r1].ch[2], h->nodes[r2].ch[2]);
    /* Four-child */
    case ND_NATREC: case ND_BOOLREC: case ND_S1REC:
    case ND_TRUNCREC: case ND_CASESPLIT:
        return node_conv(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0]) &&
               node_conv(h, a, h->nodes[r1].ch[1], h->nodes[r2].ch[1]) &&
               node_conv(h, a, h->nodes[r1].ch[2], h->nodes[r2].ch[2]) &&
               node_conv(h, a, h->nodes[r1].ch[3], h->nodes[r2].ch[3]);
    /* Six-child */
    case ND_J: {
        for (int i = 0; i < 6; i++)
            if (!node_conv(h, a, h->nodes[r1].ch[i], h->nodes[r2].ch[i])) return 0;
        return 1;
    }
    /* Lambda: conservative — same Term* body and matching env */
    case ND_LAM:
        return h->nodes[r1].aux == h->nodes[r2].aux &&
               node_conv_env(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0]);
    /* Core Val*: pointer equality */
    case ND_CORE:
        return h->nodes[r1].aux == h->nodes[r2].aux;
    /* Inductive type former: same family, same param args */
    case ND_INDTYPE: {
        if (h->nodes[r1].lvl != h->nodes[r2].lvl) return 0;
        int fam_idx = h->nodes[r1].lvl;
        IndDef *fam = ind_get(fam_idx);
        int n_total = fam->n_params + fam->n_indices;
        if (n_total > 6) return 0;
        for (int i = 0; i < n_total; i++)
            if (!node_conv(h, a, h->nodes[r1].ch[i], h->nodes[r2].ch[i])) return 0;
        return 1;
    }
    /* Inductive constructor: same family+ctor, same args */
    case ND_INDCON: {
        if (h->nodes[r1].lvl != h->nodes[r2].lvl) return 0;
        int packed   = h->nodes[r1].lvl;
        int fam_idx  = (packed >> 16) & 0xFFFF;
        int ctor_idx = packed & 0xFFFF;
        IndDef *fam  = ind_get(fam_idx);
        if (ctor_idx >= fam->n_ctors) return 0;
        int n_total  = fam->n_params + fam->ctors[ctor_idx].arity;
        if (n_total > 6) return 0;
        for (int i = 0; i < n_total; i++)
            if (!node_conv(h, a, h->nodes[r1].ch[i], h->nodes[r2].ch[i])) return 0;
        return 1;
    }
    /* Stuck indrec: same family, scrut, motive, all cases */
    case ND_INDREC: {
        if (h->nodes[r1].lvl != h->nodes[r2].lvl) return 0;
        int fam_idx = h->nodes[r1].lvl;
        IndDef *fam = ind_get(fam_idx);
        if (fam->n_ctors > 4) return 0;
        if (!node_conv(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0])) return 0;
        if (!node_conv(h, a, h->nodes[r1].ch[1], h->nodes[r2].ch[1])) return 0;
        for (int i = 0; i < fam->n_ctors; i++)
            if (!node_conv(h, a, h->nodes[r1].ch[2+i], h->nodes[r2].ch[2+i])) return 0;
        return 1;
    }
    case ND_FIX:
        return node_conv(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0]);
    case ND_LEVEL:
    case ND_LZERO:
        return 1;
    case ND_LSUC:
    case ND_UNI_V:
        return node_conv(h, a, h->nodes[r1].ch[0], h->nodes[r2].ch[0]);
    default: return 0;
    }
}
