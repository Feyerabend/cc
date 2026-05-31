#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "../core/arena.h"
#include "../core/term.h"
#include "../core/eval.h"
#include "../core/parse.h"
#include "../core/check.h"
#include "../core/defs.h"
#include "node.h"
#include "reduce.h"
#include "bridge.h"

#ifdef HAVE_READLINE
#  include <editline/readline.h>
#endif

/* Input pre-processing 
 *
 * ASCII-friendly aliases for Unicode parser tokens:
 *
 *   fn  x. body       →  \x. body         (lambda)
 *   Pi(x : A). B      →  Π(x : A). B      (dependent Pi)
 *   Sg(x : A). B      →  Σ(x : A). B      (dependent Sigma)
 *   A -> B            →  A → B            (simple function type)
 *
 * fn/Pi/Sg are rewritten only at token boundaries (preceded by a
 * non-identifier character, followed by whitespace or '(').
 * -> is rewritten anywhere.
 *
 * Worst-case output length: each 2-byte "->" expands to 3-byte "→",
 * so allocate src_len * 3 + 1 bytes (safe for all substitutions).
 */
static const char *preprocess(Arena *a, const char *src) {
    size_t n = strlen(src);
    char  *dst = (char *)arena_alloc(a, n * 3 + 1);
    size_t i = 0, j = 0;

    while (i < n) {
        int at_id_boundary = (i == 0) ||
                             !(isalnum((unsigned char)src[i-1]) ||
                               src[i-1] == '_' || src[i-1] == '\'');
        /* fn → \ */
        if (at_id_boundary &&
            src[i] == 'f' && i+1 < n && src[i+1] == 'n' &&
            (i+2 >= n || src[i+2] == ' ' || src[i+2] == '\t' ||
             src[i+2] == '(')) {
            dst[j++] = '\\';
            i += 2;
        /* Pi → Π (UTF-8: 0xCE 0xA0) */
        } else if (at_id_boundary &&
                   src[i] == 'P' && i+1 < n && src[i+1] == 'i' &&
                   i+2 < n && src[i+2] == '(') {
            dst[j++] = (char)0xCE; dst[j++] = (char)0xA0;
            i += 2;
        /* Sg → Σ (UTF-8: 0xCE 0xA3) */
        } else if (at_id_boundary &&
                   src[i] == 'S' && i+1 < n && src[i+1] == 'g' &&
                   i+2 < n && src[i+2] == '(') {
            dst[j++] = (char)0xCE; dst[j++] = (char)0xA3;
            i += 2;
        /* -> → → (UTF-8: 0xE2 0x86 0x92) */
        } else if (src[i] == '-' && i+1 < n && src[i+1] == '>') {
            dst[j++] = (char)0xE2; dst[j++] = (char)0x86; dst[j++] = (char)0x92;
            i += 2;
        } else {
            dst[j++] = src[i++];
        }
    }
    dst[j] = '\0';
    return dst;
}

/* Standard library globals 
 * sym, trans, transport, ap : derived from J; available everywhere.
 * */
static void load_stdlib(void) {
    if (def_lookup("sym") < 0)
        def_define("sym",
            "(\\A a b p."
            " J A a"
            " (\\y _. Id A y a : Π(y : A). Π(_ : Id A a y). Type)"
            " (refl a) b p"
            " : Π(A : Type). Π(a : A). Π(b : A). Π(_ : Id A a b). Id A b a)");

    if (def_lookup("trans") < 0)
        def_define("trans",
            "(\\A a b c p q."
            " J A a"
            " (\\y _. Π(_ : Id A y c). Id A a c : Π(y : A). Π(_ : Id A a y). Type)"
            " (\\q. q) b p q"
            " : Π(A : Type). Π(a : A). Π(b : A). Π(c : A)."
            "   Π(_ : Id A a b). Π(_ : Id A b c). Id A a c)");

    if (def_lookup("transport") < 0)
        def_define("transport",
            "(\\A P a b p x."
            " J A a"
            " (\\y _. P y : Π(y : A). Π(_ : Id A a y). Type)"
            " x b p"
            " : Π(A : Type). Π(P : Π(_ : A). Type). Π(a : A). Π(b : A)."
            "   Π(_ : Id A a b). Π(_ : P a). P b)");

    if (def_lookup("ap") < 0)
        def_define("ap",
            "(\\A B f a b p."
            " J A a"
            " (\\y _. Id B (f a) (f y) : Π(y : A). Π(_ : Id A a y). Type)"
            " (refl (f a)) b p"
            " : Π(A : Type). Π(B : Type). Π(f : Π(_ : A). B)."
            "   Π(a : A). Π(b : A). Π(_ : Id A a b). Id B (f a) (f b))");
}

/* Shared result printer
 * Type-former nodes (PI/SIGMA/W/ID/SUM) have unforced cod thunks;
 * route them through bridge for term_fprint.  Others use node_print.
 */
static void print_result_node(Heap *h, NodeRef r, Arena *a) {
    NodeTag rtag = (NodeTag)h->nodes[r].tag;
    if (rtag == ND_PI || rtag == ND_SIGMA || rtag == ND_W ||
        rtag == ND_ID || rtag == ND_SUM) {
        Term *nt = node_to_term(h, r, a);
        if (nt) term_fprint(stdout, nt);
        else    node_print(h, r, 0, 0);
    } else {
        node_print(h, r, 0, 0);
    }
}

/* REPL */

int main(int argc, char **argv) {
    int dump_graph = 0;
    for (int i = 1; i < argc; i++)
        if (strcmp(argv[i], "--dump-graph") == 0) dump_graph = 1;

    load_stdlib();

    printf("llang\n");
    printf("  Lambda:  fn x. body          |  \\x. body  |  λx. body\n");
    printf("  Pi:      Pi(x:A). B          |  Π(x:A). B\n");
    printf("  Sigma:   Sg(x:A). B          |  Σ(x:A). B\n");
    printf("  Arrow:   A -> B              |  A → B\n");
    printf("  let name = expr              — bind global\n");
    printf("  let name : type = expr       — bind with type annotation\n");
    printf("  :type <expr>                 — reduce and show type\n");
    printf("  :conv e1 ; e2               — check convertibility\n");
    printf("  Quit:    Ctrl-D\n\n");

#ifndef HAVE_READLINE
    char   *buf = NULL;
    size_t  cap = 0;
#endif

    for (;;) {
        const char *raw = NULL;

#ifdef HAVE_READLINE
        raw = readline(">> ");
        if (!raw) { printf("\n"); break; }
        if (raw[0] != '\0') add_history(raw);
#else
        printf(">> ");
        fflush(stdout);
        ssize_t n = getline(&buf, &cap, stdin);
        if (n < 0) { printf("\n"); break; }
        size_t len = (size_t)n;
        if (len > 0 && buf[len-1] == '\n') buf[--len] = '\0';
        raw = buf;
#endif

        if (raw[0] == '\0') {
#ifdef HAVE_READLINE
            free((void *)raw);
#endif
            continue;
        }

        int         is_type = (strncmp(raw, ":type ", 6) == 0);
        int         is_conv = (strncmp(raw, ":conv ", 6) == 0);
        int         is_let  = (strncmp(raw, "let", 3) == 0 &&
                               (raw[3] == ' ' || raw[3] == '\t'));
        const char *expr    = is_type ? raw + 6 : raw;

        Arena a = {NULL};
        Heap  h;
        heap_init(&h);

        /* ── let name [: type] = expr ── */
        if (is_let) {
            const char *rest = raw + 4;
            while (*rest == ' ' || *rest == '\t') rest++;

            /* extract name */
            const char *name_start = rest;
            while (*rest && *rest != ' ' && *rest != '\t' &&
                   *rest != ':' && *rest != '=') rest++;
            size_t name_len = (size_t)(rest - name_start);
            if (name_len == 0) {
                printf("  usage  : let name [: type] = expr\n");
#ifdef HAVE_READLINE
                free((void *)raw);
#endif
                heap_free(&h); arena_free_all(&a); continue;
            }
            char *lname = (char *)arena_alloc(&a, name_len + 1);
            memcpy(lname, name_start, name_len);
            lname[name_len] = '\0';

            while (*rest == ' ' || *rest == '\t') rest++;

            const char *type_start = NULL;
            size_t      type_len   = 0;

            if (*rest == ':') {
                rest++;
                while (*rest == ' ' || *rest == '\t') rest++;
                const char *eq = strchr(rest, '=');
                if (!eq) {
                    printf("  usage  : let name [: type] = expr\n");
#ifdef HAVE_READLINE
                    free((void *)raw);
#endif
                    heap_free(&h); arena_free_all(&a); continue;
                }
                type_start = rest;
                type_len   = (size_t)(eq - rest);
                while (type_len > 0 && (type_start[type_len-1] == ' ' ||
                                        type_start[type_len-1] == '\t'))
                    type_len--;
                rest = eq + 1;
            } else if (*rest == '=') {
                rest++;
            } else {
                printf("  usage  : let name [: type] = expr\n");
#ifdef HAVE_READLINE
                free((void *)raw);
#endif
                heap_free(&h); arena_free_all(&a); continue;
            }
            while (*rest == ' ' || *rest == '\t') rest++;

#ifdef HAVE_READLINE
            free((void *)raw);
#endif

            /* preprocess both sides and register without type-checking */
            const char *pp_type = NULL;
            if (type_start && type_len > 0) {
                char *tbuf = (char *)arena_alloc(&a, type_len + 1);
                memcpy(tbuf, type_start, type_len);
                tbuf[type_len] = '\0';
                pp_type = preprocess(&a, tbuf);
            }
            const char *pp_expr = preprocess(&a, rest);

            int idx = def_define_nocheck(lname, pp_type, pp_expr);
            if (idx < 0)
                printf("  error  : could not define '%s'\n", lname);
            else
                printf("  defined: %s\n", lname);
            heap_free(&h); arena_free_all(&a); continue;
        }

        /* ── :conv e1 ; e2 ── */
        if (is_conv) {
            const char *rest = raw + 6;
            const char *semi = strchr(rest, ';');
            if (!semi) {
                printf("  usage  : :conv e1 ; e2\n");
#ifdef HAVE_READLINE
                free((void *)raw);
#endif
                heap_free(&h); arena_free_all(&a); continue;
            }
            size_t llen = (size_t)(semi - rest);
            while (llen > 0 && (rest[llen-1] == ' ' || rest[llen-1] == '\t')) llen--;
            char *lbuf = (char *)arena_alloc(&a, llen + 1);
            memcpy(lbuf, rest, llen); lbuf[llen] = '\0';
            const char *rhs_raw = semi + 1;
            while (*rhs_raw == ' ' || *rhs_raw == '\t') rhs_raw++;
            const char *src1 = preprocess(&a, lbuf);
            const char *src2 = preprocess(&a, rhs_raw);
#ifdef HAVE_READLINE
            free((void *)raw);
#endif
            Term *t1 = parse(&a, src1);
            Term *t2 = parse(&a, src2);
            if (!t1 || !t2) { heap_free(&h); arena_free_all(&a); continue; }
            NodeRef nr1 = term_to_node(&h, &a, t1, NULL_REF);
            NodeRef nr2 = term_to_node(&h, &a, t2, NULL_REF);
            nf(&h, &a, nr1); nf(&h, &a, nr2);
            NodeRef res1 = node_deref(&h, nr1);
            NodeRef res2 = node_deref(&h, nr2);
            printf("  lhs    : "); print_result_node(&h, res1, &a); printf("\n");
            printf("  rhs    : "); print_result_node(&h, res2, &a); printf("\n");
            printf("  conv   : %s\n", node_conv(&h, &a, res1, res2) ? "yes" : "no");
            heap_free(&h); arena_free_all(&a); continue;
        }

        const char *src = preprocess(&a, expr);
        Term       *t   = parse(&a, src);

#ifdef HAVE_READLINE
        free((void *)raw);
#endif

        if (!t) {
            heap_free(&h);
            arena_free_all(&a);
            continue;
        }

        NodeRef root   = term_to_node(&h, &a, t, NULL_REF);
        nf(&h, &a, root);
        NodeRef result = node_deref(&h, root);

        if (dump_graph) {
            fprintf(stderr, "\n-- heap dump (%zu nodes) --\n", h.size);
            node_dump_graph(&h);
            fprintf(stderr, "-- root=%u  result=%u --\n\n", root, result);
        }

        printf("  normal : ");
        print_result_node(&h, result, &a);
        printf("\n");

        if (is_type) {
            Val *ty = infer(&a, 0, NULL, NULL, t);
            if (!ty) {
                printf("  type   : (type error)\n");
            } else {
                printf("  type   : ");
                term_fprint(stdout, nbe_quote(&a, 0, ty));
                printf("\n");
            }
        }

        heap_free(&h);
        arena_free_all(&a);
    }

#ifndef HAVE_READLINE
    free(buf);
#endif
    return 0;
}
