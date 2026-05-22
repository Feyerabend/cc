#include "node.h"

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
        if ((NodeTag)n->tag == ND_VAR || (NodeTag)n->tag == ND_GLOBAL)
            fprintf(stderr, "  lvl=%d", n->lvl);
        if ((NodeTag)n->tag == ND_UNI)
            fprintf(stderr, "  ulvl=%d", n->ulvl);
        fprintf(stderr, "  flags=0x%x]\n", n->flags);
    }
}

/* Neutral-chain helpers */

static int is_stuck_elim_tag(NodeTag t) {
    switch (t) {
    case ND_FST: case ND_SND:
    case ND_NATREC: case ND_BOOLREC: case ND_S1REC:
    case ND_TRUNCREC: case ND_CASESPLIT: case ND_ABORT:
    case ND_UNITREC: case ND_J: case ND_WREC:
        return 1;
    default: return 0;
    }
}

/* Scrutinee child NodeRef for any eliminator. */
static NodeRef scrut_of(Heap *h, NodeRef r) {
    switch ((NodeTag)h->nodes[r].tag) {
    case ND_FST:
    case ND_SND:      return h->nodes[r].ch[0];
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
    if (!is_stuck_elim_tag(tag))  return 0;
    if (!(h->nodes[r].flags & NF_WHNF)) return 0;
    return is_neutral(h, scrut_of(h, r));
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
    print_neutral_inner(h, scrut_of(h, r), depth);
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
        /* Lambda in result — print body as raw term (Phase 0 approximation) */
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
    case ND_UNITREC: case ND_J: case ND_WREC:
        if (is_neutral(h, r)) {
            printf("[");
            print_neutral_inner(h, r, depth);
            printf("]");
        } else {
            printf("<%s>", tag_name(tag));
        }
        break;
    default:
        printf("<%s>", tag_name(tag));
        break;
    }
}
