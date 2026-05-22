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

/* REPL */

int main(int argc, char **argv) {
    int dump_graph = 0;
    for (int i = 1; i < argc; i++)
        if (strcmp(argv[i], "--dump-graph") == 0) dump_graph = 1;

    load_stdlib();

    printf("llang  (graph reduction, Phase 3: β + ι + neutrals + :type)\n");
    printf("  Lambda:  fn x. body  |  \\x. body  |  λx. body\n");
    printf("  Pi:      Pi(x:A). B  |  Π(x:A). B\n");
    printf("  Sigma:   Sg(x:A). B  |  Σ(x:A). B\n");
    printf("  Arrow:   A -> B      |  A → B\n");
    printf("  :type <expr>  — reduce and show type\n");
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
        const char *expr    = is_type ? raw + 6 : raw;

        Arena a = {NULL};
        Heap  h;
        heap_init(&h);

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
        /* Type-former nodes store children as un-forced thunks : use bridge
         * to serialize back to Term and print via core's pretty-printer.
         * All other nodes (values, neutrals) use the graph printer. */
        NodeTag rtag = (NodeTag)h.nodes[result].tag;
        if (rtag == ND_PI || rtag == ND_SIGMA || rtag == ND_W ||
            rtag == ND_ID || rtag == ND_SUM) {
            Term *nt = node_to_term(&h, result, &a);
            if (nt) term_fprint(stdout, nt);
            else    node_print(&h, result, 0, 0);
        } else {
            node_print(&h, result, 0, 0);
        }
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
