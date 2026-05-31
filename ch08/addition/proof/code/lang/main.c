#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif
#include "../core/arena.h"
#include "../core/term.h"
#include "../core/eval.h"
#include "../core/parse.h"
#include "../core/check.h"
#include "../core/defs.h"
#include "../core/elab.h"
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

/* ── Shared result printer ───────────────────────────────────────────
 * Type-former nodes (PI/SIGMA/W/ID/SUM) have unforced cod thunks;
 * route them through bridge for term_fprint.  Others use node_print.
 * ──────────────────────────────────────────────────────────────────── */
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

/* ── File-scope state ────────────────────────────────────────────── */
static int dump_graph_g = 0;

/* Load-stack for cycle detection: canonical paths of files currently
   being opened (so a→b→a is caught before infinite recursion). */
#define LOAD_STACK_MAX 32
static const char *load_stack[LOAD_STACK_MAX];
static int         load_depth = 0;

/* Already-loaded set: canonical paths of files successfully loaded at
   least once.  A second :load of the same file is a silent no-op. */
#define LOADED_SET_MAX 256
static char *loaded_set[LOADED_SET_MAX];
static int   n_loaded = 0;

/* Return a malloc'd canonical (absolute, symlink-resolved) copy of path,
   or a plain strdup if realpath fails (file not yet created, etc.). */
static char *canonical_path(const char *path) {
    char buf[PATH_MAX];
    if (realpath(path, buf)) return strdup(buf);
    return strdup(path); /* fallback: use as given */
}

static int in_load_stack(const char *canon) {
    for (int i = 0; i < load_depth; i++)
        if (strcmp(load_stack[i], canon) == 0) return 1;
    return 0;
}

static int in_loaded_set(const char *canon) {
    for (int i = 0; i < n_loaded; i++)
        if (strcmp(loaded_set[i], canon) == 0) return 1;
    return 0;
}

static void add_to_loaded_set(const char *canon) {
    if (n_loaded >= LOADED_SET_MAX) return; /* silently drop if table full */
    loaded_set[n_loaded++] = strdup(canon);
}

/* ── Forward declaration ─────────────────────────────────────────── */
static int load_file(const char *path);

/* ── process_line ────────────────────────────────────────────────────
 *
 * Execute one pre-processed REPL/file line.
 *
 *   origin  "filename:lineno" string prepended to error messages;
 *           NULL when called from the interactive REPL.
 *   quiet   if non-zero, suppress "defined:" / "defined family:"
 *           output (used when loading library files).
 *
 * Returns 0 on success, -1 if the line produced an error.
 */
static int process_line(const char *raw, const char *origin, int quiet) {
    if (!raw || raw[0] == '\0') return 0;

    /* ── :q / :quit — ignored in file context, meaningful only in REPL ── */
    if ((strcmp(raw, ":q") == 0 || strcmp(raw, ":quit") == 0) && origin)
        return 0;

    /* ── :load "path" ── */
    if (strncmp(raw, ":load", 5) == 0 &&
        (raw[5] == ' ' || raw[5] == '\t' || raw[5] == '"')) {
        const char *p = raw + 5;
        while (*p == ' ' || *p == '\t') p++;
        if (*p != '"') {
            printf("  usage  : :load \"file.lam\"\n");
            return -1;
        }
        p++;
        const char *end = strchr(p, '"');
        if (!end) {
            printf("  error  : :load: unterminated filename\n");
            return -1;
        }
        size_t len = (size_t)(end - p);
        char *path = (char *)malloc(len + 1);
        if (!path) { fprintf(stderr, "out of memory\n"); return -1; }
        memcpy(path, p, len);
        path[len] = '\0';
        int r = load_file(path);
        free(path);
        return r;
    }

    int is_type = (strncmp(raw, ":type ", 6) == 0);
    int is_conv = (strncmp(raw, ":conv ", 6) == 0);
    int is_data = (strncmp(raw, "data", 4) == 0 && (raw[4] == ' ' || raw[4] == '\t'));

    /* let rec: desugar to   let name [: T] = fix (\name. body)
     * Detect "let rec " (with optional extra spaces after "rec"). */
    int is_letrec = 0;
    if (strncmp(raw, "let", 3) == 0 && (raw[3] == ' ' || raw[3] == '\t')) {
        const char *p = raw + 3;
        while (*p == ' ' || *p == '\t') p++;
        if (strncmp(p, "rec", 3) == 0 && (p[3] == ' ' || p[3] == '\t'))
            is_letrec = 1;
    }
    int is_let  = !is_letrec &&
                  (strncmp(raw, "let",  3) == 0 && (raw[3] == ' ' || raw[3] == '\t'));
    const char *expr = is_type ? raw + 6 : raw;

    Arena a = {NULL};
    Heap  h;
    heap_init(&h);

    /* ── data FamName [params] [: indices] where ctor : type [; ...]* ── */
    if (is_data) {
        const char *rest = raw + 4;
        while (*rest == ' ' || *rest == '\t') rest++;
        const char *pp = preprocess(&a, rest);
        int fam_idx = parse_data(pp);
        if (fam_idx >= 0) {
            if (!quiet) {
                IndDef *fam = ind_get(fam_idx);
                printf("  defined family: %s (%d constructor%s)\n",
                       fam->name, fam->n_ctors, fam->n_ctors == 1 ? "" : "s");
            }
        } else if (origin) {
            fprintf(stderr, "%s: data declaration failed\n", origin);
        }
        heap_free(&h); arena_free_all(&a);
        return fam_idx >= 0 ? 0 : -1;
    }

    /* ── let rec name [: type] = body
     *  Desugars to:  let name [: type] = fix (\name. body)
     * ── */
    if (is_letrec) {
        /* Skip "let rec " */
        const char *rest = raw + 3;
        while (*rest == ' ' || *rest == '\t') rest++;
        rest += 3; /* skip "rec" */
        while (*rest == ' ' || *rest == '\t') rest++;

        /* Extract name */
        const char *name_start = rest;
        while (*rest && *rest != ' ' && *rest != '\t' &&
               *rest != ':' && *rest != '=') rest++;
        size_t name_len = (size_t)(rest - name_start);
        if (name_len == 0 || name_len > 256) {
            if (!origin) printf("  usage  : let rec name [: type] = body\n");
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        char lname[257];
        memcpy(lname, name_start, name_len);
        lname[name_len] = '\0';

        while (*rest == ' ' || *rest == '\t') rest++;

        /* Optional type annotation */
        const char *type_src = NULL;
        if (*rest == ':') {
            rest++;
            while (*rest == ' ' || *rest == '\t') rest++;
            const char *eq = strchr(rest, '=');
            if (!eq) {
                if (!origin) printf("  usage  : let rec name [: type] = body\n");
                heap_free(&h); arena_free_all(&a);
                return -1;
            }
            size_t tlen = (size_t)(eq - rest);
            while (tlen > 0 && (rest[tlen-1] == ' ' || rest[tlen-1] == '\t')) tlen--;
            char *tbuf = (char *)arena_alloc(&a, tlen + 1);
            memcpy(tbuf, rest, tlen); tbuf[tlen] = '\0';
            type_src = preprocess(&a, tbuf);
            rest = eq + 1;
        } else if (*rest == '=') {
            rest++;
        } else {
            if (!origin) printf("  usage  : let rec name [: type] = body\n");
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        while (*rest == ' ' || *rest == '\t') rest++;

        /* Build "fix (\name. body)" as a string */
        const char *body_pp = preprocess(&a, rest);
        size_t blen = strlen(body_pp);
        /* "fix (\name. " + body + ")" */
        size_t fix_len = 7 + name_len + 2 + blen + 1 + 1;
        char *fix_src = (char *)arena_alloc(&a, fix_len);
        snprintf(fix_src, fix_len, "fix (\\%s. %s)", lname, body_pp);

        int idx = def_define_nocheck(lname, type_src, fix_src);
        if (idx < 0) {
            if (origin)
                fprintf(stderr, "%s: could not define '%s'\n", origin, lname);
            else
                printf("  error  : could not define '%s'\n", lname);
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        if (!quiet) printf("  defined: %s\n", lname);
        heap_free(&h); arena_free_all(&a);
        return 0;
    }

    /* ── let name [: type] = expr ── */
    if (is_let) {
        const char *rest = raw + 4;
        while (*rest == ' ' || *rest == '\t') rest++;

        const char *name_start = rest;
        while (*rest && *rest != ' ' && *rest != '\t' &&
               *rest != ':' && *rest != '=') rest++;
        size_t name_len = (size_t)(rest - name_start);
        if (name_len == 0) {
            if (!origin) printf("  usage  : let name [: type] = expr\n");
            heap_free(&h); arena_free_all(&a);
            return -1;
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
                if (!origin) printf("  usage  : let name [: type] = expr\n");
                heap_free(&h); arena_free_all(&a);
                return -1;
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
            if (!origin) printf("  usage  : let name [: type] = expr\n");
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        while (*rest == ' ' || *rest == '\t') rest++;

        const char *pp_type = NULL;
        if (type_start && type_len > 0) {
            char *tbuf = (char *)arena_alloc(&a, type_len + 1);
            memcpy(tbuf, type_start, type_len);
            tbuf[type_len] = '\0';
            pp_type = preprocess(&a, tbuf);
        }
        const char *pp_expr = preprocess(&a, rest);

        int idx = def_define_nocheck(lname, pp_type, pp_expr);
        if (idx < 0) {
            if (origin)
                fprintf(stderr, "%s: could not define '%s'\n", origin, lname);
            else
                printf("  error  : could not define '%s'\n", lname);
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        if (!quiet) printf("  defined: %s\n", lname);
        heap_free(&h); arena_free_all(&a);
        return 0;
    }

    /* ── :conv e1 ; e2 ── */
    if (is_conv) {
        const char *rest = raw + 6;
        const char *semi = strchr(rest, ';');
        if (!semi) {
            if (!origin) printf("  usage  : :conv e1 ; e2\n");
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        size_t llen = (size_t)(semi - rest);
        while (llen > 0 && (rest[llen-1] == ' ' || rest[llen-1] == '\t')) llen--;
        char *lbuf = (char *)arena_alloc(&a, llen + 1);
        memcpy(lbuf, rest, llen); lbuf[llen] = '\0';
        const char *rhs_raw = semi + 1;
        while (*rhs_raw == ' ' || *rhs_raw == '\t') rhs_raw++;
        const char *src1 = preprocess(&a, lbuf);
        const char *src2 = preprocess(&a, rhs_raw);
        Term *t1 = parse(&a, src1);
        Term *t2 = parse(&a, src2);
        if (!t1 || !t2) { heap_free(&h); arena_free_all(&a); return -1; }
        NodeRef nr1 = term_to_node(&h, &a, t1, NULL_REF);
        NodeRef nr2 = term_to_node(&h, &a, t2, NULL_REF);
        nf(&h, &a, nr1); nf(&h, &a, nr2);
        NodeRef res1 = node_deref(&h, nr1);
        NodeRef res2 = node_deref(&h, nr2);
        printf("  lhs    : "); print_result_node(&h, res1, &a); printf("\n");
        printf("  rhs    : "); print_result_node(&h, res2, &a); printf("\n");
        printf("  conv   : %s\n", node_conv(&h, &a, res1, res2) ? "yes" : "no");
        heap_free(&h); arena_free_all(&a);
        return 0;
    }

    /* ── expression: reduce and optionally show type ── */
    const char *src = preprocess(&a, expr);
    Term       *t   = parse(&a, src);

    if (!t) {
        heap_free(&h); arena_free_all(&a);
        return -1;
    }

    if (term_has_holes(t)) {
        ElabCtx ec; elab_init(&ec, &a);
        if (!elab_infer(&ec, &a, 0, NULL, NULL, t)) {
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        t = elab_subst(&ec, &a, 0, t);
        if (!t) { heap_free(&h); arena_free_all(&a); return -1; }
    }

    NodeRef root   = term_to_node(&h, &a, t, NULL_REF);
    nf(&h, &a, root);
    NodeRef result = node_deref(&h, root);

    if (dump_graph_g) {
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
    return 0;
}

/* ── load_file ───────────────────────────────────────────────────────
 *
 * Read and execute a .lam source file.
 *
 * Each logical line is processed with process_line(..., quiet=1).
 * Logical lines may span multiple physical lines using a trailing '\'
 * (backslash) as a continuation marker.
 *
 * Comment syntax:  '--' to end of line (may appear after code).
 * Import syntax:   import "other.lam"  (resolved relative to the
 *                  importing file's directory).
 *
 * Errors are printed to stderr with "filename:lineno: " context;
 * processing continues past errors so all definitions are attempted.
 *
 * Returns 0 if no errors occurred, -1 otherwise.
 */
static int load_file(const char *path) {
    /* Canonicalize path for cycle and dedup checks */
    char *canon = canonical_path(path);
    if (!canon) { fprintf(stderr, "  error  : :load: out of memory\n"); return -1; }

    /* Deduplicate: skip files already successfully loaded */
    if (in_loaded_set(canon)) {
        free(canon);
        return 0; /* already loaded — silent no-op */
    }

    /* Cycle detection: catch circular imports before opening the file */
    if (in_load_stack(canon)) {
        fprintf(stderr, "  error  : :load: circular import of '%s'\n", path);
        free(canon);
        return -1;
    }

    FILE *f = fopen(path, "r");
    if (!f) {
        fprintf(stderr, "  error  : :load: cannot open '%s': %s\n",
                path, strerror(errno));
        free(canon);
        return -1;
    }

    /* Push onto load stack */
    if (load_depth >= LOAD_STACK_MAX) {
        fprintf(stderr, "  error  : :load: import nesting too deep (max %d)\n",
                LOAD_STACK_MAX);
        fclose(f); free(canon); return -1;
    }
    load_stack[load_depth++] = canon;

    char  *buf      = NULL;
    size_t bufsz    = 0;
    char  *accum    = NULL;
    size_t accsz    = 0;
    int    acclen   = 0;
    int    lineno   = 0;
    int    start_ln = 0;
    int    errors   = 0;

    /* Compute directory prefix for resolving relative imports */
    char dir_prefix[4096];
    dir_prefix[0] = '\0';
    const char *slash = strrchr(path, '/');
    if (slash) {
        size_t dlen = (size_t)(slash - path + 1);
        if (dlen < sizeof(dir_prefix)) {
            memcpy(dir_prefix, path, dlen);
            dir_prefix[dlen] = '\0';
        }
    }

    for (;;) {
        ssize_t n = getline(&buf, &bufsz, f);
        if (n < 0) break;
        lineno++;

        /* Strip trailing newline / carriage return */
        while (n > 0 && (buf[n-1] == '\n' || buf[n-1] == '\r'))
            buf[--n] = '\0';

        /* Strip leading whitespace */
        char *line = buf;
        while (*line == ' ' || *line == '\t') line++;

        /* Full-line comment or blank — skip unless we're mid-continuation */
        if (line[0] == '-' && line[1] == '-') continue;
        if (line[0] == '\0' && acclen == 0) continue;

        /* Strip inline comment: '--' not preceded by '-' (avoids -->)
           Since the language has no string literals, any '--' is a comment. */
        char *cmt = strstr(line, "--");
        if (cmt) {
            *cmt = '\0';
            n    = (ssize_t)(cmt - buf);
        }

        /* Trim trailing whitespace after comment removal */
        int len = (int)strlen(line);
        while (len > 0 && (line[len-1] == ' ' || line[len-1] == '\t'))
            line[--len] = '\0';

        /* Skip blank lines (possibly created by comment stripping) */
        if (len == 0 && acclen == 0) continue;

        /* Line continuation: trailing backslash joins to next physical line */
        int cont = (len > 0 && line[len-1] == '\\');
        if (cont) {
            line[--len] = '\0';
            while (len > 0 && (line[len-1] == ' ' || line[len-1] == '\t'))
                line[--len] = '\0';
        }

        /* Accumulate into logical line buffer */
        if (acclen == 0) start_ln = lineno;
        size_t need = (size_t)acclen + (size_t)len + 2;
        if (need > accsz) {
            accsz  = need * 2 + 128;
            accum  = (char *)realloc(accum, accsz);
            if (!accum) { fprintf(stderr, "out of memory\n"); errors++; break; }
        }
        if (acclen > 0 && len > 0) accum[acclen++] = ' ';
        memcpy(accum + acclen, line, (size_t)len + 1);
        acclen += len;

        if (cont) continue; /* need next physical line before processing */

        /* Dispatch the accumulated logical line */
        if (acclen == 0) continue;

        /* Build error-context string "path:lineno" */
        char origin[4096 + 32];
        snprintf(origin, sizeof(origin), "%s:%d", path, start_ln);

        /* import "other.lam" */
        if (strncmp(accum, "import", 6) == 0 &&
            (accum[6] == ' ' || accum[6] == '\t' || accum[6] == '"')) {
            char *p = accum + 6;
            while (*p == ' ' || *p == '\t') p++;
            if (*p == '"') {
                p++;
                char *end = strchr(p, '"');
                if (end) {
                    *end = '\0';
                    char import_path[4096];
                    if (dir_prefix[0])
                        snprintf(import_path, sizeof(import_path), "%s%s",
                                 dir_prefix, p);
                    else
                        snprintf(import_path, sizeof(import_path), "%s", p);
                    if (load_file(import_path) < 0) errors++;
                } else {
                    fprintf(stderr, "%s: import: unterminated filename\n", origin);
                    errors++;
                }
            } else {
                fprintf(stderr, "%s: import: expected quoted filename\n", origin);
                errors++;
            }
        } else {
            if (process_line(accum, origin, 1) < 0) errors++;
        }

        acclen = 0;
        if (accsz > 0) accum[0] = '\0';
    }

    /* Flush any trailing continuation line (no final newline in file) */
    if (acclen > 0) {
        char origin[4096 + 32];
        snprintf(origin, sizeof(origin), "%s:%d", path, start_ln);
        if (process_line(accum, origin, 1) < 0) errors++;
    }

    free(buf);
    free(accum);
    fclose(f);

    /* Pop load stack */
    if (load_depth > 0) load_depth--;

    if (errors == 0) {
        add_to_loaded_set(canon); /* mark as successfully loaded */
        printf("  loaded : %s\n", path);
    } else {
        fprintf(stderr, "  loaded : %s (%d error%s)\n",
                path, errors, errors == 1 ? "" : "s");
    }
    free(canon);
    return errors > 0 ? -1 : 0;
}

/* ── REPL ────────────────────────────────────────────────────────── */

int main(int argc, char **argv) {
    for (int i = 1; i < argc; i++)
        if (strcmp(argv[i], "--dump-graph") == 0) dump_graph_g = 1;

    load_stdlib();

    printf("llang  (graph reduction: β + ι + neutrals + :type + :conv + let + :load)\n");
    printf("  Lambda:  fn x. body          |  \\x. body  |  λx. body\n");
    printf("  Pi:      Pi(x:A). B          |  Π(x:A). B\n");
    printf("  Sigma:   Sg(x:A). B          |  Σ(x:A). B\n");
    printf("  Arrow:   A -> B              |  A → B\n");
    printf("  let name = expr              — bind global\n");
    printf("  let name : type = expr       — bind with type annotation\n");
    printf("  :type <expr>                 — reduce and show type\n");
    printf("  :conv e1 ; e2               — check convertibility\n");
    printf("  :load \"file.lam\"             — load definitions from file\n");
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

        process_line(raw, NULL, 0);

#ifdef HAVE_READLINE
        free((void *)raw);
#endif
    }

#ifndef HAVE_READLINE
    free(buf);
#endif
    return 0;
}
