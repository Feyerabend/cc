#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <alloca.h>
#include <errno.h>
#include <limits.h>
#include <unistd.h>   /* isatty */

/* ── ANSI terminal colours ───────────────────────────────────────────────── */
static int use_color = 0;   /* set to 1 if stdout is a real terminal */
#define COL(x)     (use_color ? (x) : "")
#define C_RESET    "\033[0m"
#define C_BOLD     "\033[1m"
#define C_PROMPT   "\033[1;36m"   /* bold cyan   — prompt >> */
#define C_RESULT   "\033[1;32m"   /* bold green  — normal : */
#define C_TYPE     "\033[1;33m"   /* bold yellow — type   : */
#define C_CONV_Y   "\033[1;32m"   /* bold green  — conv yes */
#define C_CONV_N   "\033[1;31m"   /* bold red    — conv no  */
#define C_LOADED   "\033[0;34m"   /* blue        — loaded : */
#define C_ERROR    "\033[1;31m"   /* bold red    — error   */
#define C_DIM      "\033[0;2m"    /* dim         — usage hints */

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

/* Helper: char c is not an identifier continuation (i.e. a word boundary follows) */
#define NOT_IDENT(c) (!isalnum((unsigned char)(c)) && (c) != '_' && (c) != '\'')

    while (i < n) {
        int at_id_boundary = (i == 0) || NOT_IDENT(src[i-1]);
        /* fn / fun / lam  →  \  (lambda) */
        if (at_id_boundary && src[i] == 'f' && i+1 < n && src[i+1] == 'n' &&
            (i+2 >= n || NOT_IDENT(src[i+2]))) {
            dst[j++] = '\\'; i += 2;
        } else if (at_id_boundary && src[i] == 'f' && i+1 < n && src[i+1] == 'u' &&
                   i+2 < n && src[i+2] == 'n' && (i+3 >= n || NOT_IDENT(src[i+3]))) {
            dst[j++] = '\\'; i += 3;
        } else if (at_id_boundary && src[i] == 'l' && i+1 < n && src[i+1] == 'a' &&
                   i+2 < n && src[i+2] == 'm' && (i+3 >= n || NOT_IDENT(src[i+3]))) {
            dst[j++] = '\\'; i += 3;
        /* Pi / forall  →  Π (UTF-8: 0xCE 0xA0) */
        } else if (at_id_boundary && src[i] == 'P' && i+1 < n && src[i+1] == 'i' &&
                   i+2 < n && src[i+2] == '(') {
            dst[j++] = (char)0xCE; dst[j++] = (char)0xA0; i += 2;
        } else if (at_id_boundary && src[i] == 'f' && i+1 < n && src[i+1] == 'o' &&
                   i+2 < n && src[i+2] == 'r' && i+3 < n && src[i+3] == 'a' &&
                   i+4 < n && src[i+4] == 'l' && i+5 < n && src[i+5] == 'l' &&
                   i+6 < n && src[i+6] == '(') {
            dst[j++] = (char)0xCE; dst[j++] = (char)0xA0; i += 6;
        /* Sg / exists  →  Σ (UTF-8: 0xCE 0xA3) */
        } else if (at_id_boundary && src[i] == 'S' && i+1 < n && src[i+1] == 'g' &&
                   i+2 < n && src[i+2] == '(') {
            dst[j++] = (char)0xCE; dst[j++] = (char)0xA3; i += 2;
        } else if (at_id_boundary && src[i] == 'e' && i+1 < n && src[i+1] == 'x' &&
                   i+2 < n && src[i+2] == 'i' && i+3 < n && src[i+3] == 's' &&
                   i+4 < n && src[i+4] == 't' && i+5 < n && src[i+5] == 's' &&
                   i+6 < n && src[i+6] == '(') {
            dst[j++] = (char)0xCE; dst[j++] = (char)0xA3; i += 6;
        /* -> / => (in match-arm position)  →  → (UTF-8: 0xE2 0x86 0x92) */
        } else if (src[i] == '-' && i+1 < n && src[i+1] == '>') {
            dst[j++] = (char)0xE2; dst[j++] = (char)0x86; dst[j++] = (char)0x92; i += 2;
        } else if (src[i] == '=' && i+1 < n && src[i+1] == '>') {
            dst[j++] = (char)0xE2; dst[j++] = (char)0x86; dst[j++] = (char)0x92; i += 2;
        } else {
            dst[j++] = src[i++];
        }
    }
#undef NOT_IDENT
    dst[j] = '\0';
    return dst;
}

/* ── Where-clause helpers ── */

static int is_word_char(unsigned char c) {
    return isalnum(c) || c == '_' || c == '\'';
}

/* Return pointer to the bare word "where" at parenthesis depth 0, or NULL.
 * Checks both sides for word boundaries so "somewhere" or "where_" won't match. */
static const char *find_where_kw(const char *s) {
    int depth = 0;
    const char *p = s;
    while (*p) {
        if (*p == '(' || *p == '[') { depth++; p++; continue; }
        if ((*p == ')' || *p == ']') && depth > 0) { depth--; p++; continue; }
        if (depth == 0 && strncmp(p, "where", 5) == 0) {
            int before_ok = (p == s) || !is_word_char((unsigned char)p[-1]);
            int after_ok  = !is_word_char((unsigned char)p[5]);
            if (before_ok && after_ok) return p;
        }
        p++;
    }
    return NULL;
}

/* Word-boundary substitution: replace each olds[i] with news[i] in src.
 * Returns a newly arena-allocated string with all replacements applied.
 * Non-ASCII bytes (UTF-8 multi-byte sequences) are treated as non-word chars
 * and copied verbatim. */
static char *subst_words(Arena *a, const char *src,
                          const char **olds, const char **news, int n) {
    size_t old_lens[16], new_lens[16];
    if (n > 16) n = 16;
    for (int i = 0; i < n; i++) {
        old_lens[i] = strlen(olds[i]);
        new_lens[i] = strlen(news[i]);
    }

    /* Two passes: measure then copy. */
    size_t out_len = 0;
    const char *p = src;
    while (*p) {
        if (is_word_char((unsigned char)*p)) {
            const char *ws = p;
            while (is_word_char((unsigned char)*p)) p++;
            size_t wlen = (size_t)(p - ws);
            int hit = 0;
            for (int i = 0; i < n; i++) {
                if (wlen == old_lens[i] && memcmp(ws, olds[i], wlen) == 0) {
                    out_len += new_lens[i]; hit = 1; break;
                }
            }
            if (!hit) out_len += wlen;
        } else { out_len++; p++; }
    }

    char *out = (char *)arena_alloc(a, out_len + 1);
    char *q = out;
    p = src;
    while (*p) {
        if (is_word_char((unsigned char)*p)) {
            const char *ws = p;
            while (is_word_char((unsigned char)*p)) p++;
            size_t wlen = (size_t)(p - ws);
            int hit = 0;
            for (int i = 0; i < n; i++) {
                if (wlen == old_lens[i] && memcmp(ws, olds[i], wlen) == 0) {
                    memcpy(q, news[i], new_lens[i]); q += new_lens[i]; hit = 1; break;
                }
            }
            if (!hit) { memcpy(q, ws, wlen); q += wlen; }
        } else { *q++ = *p++; }
    }
    *q = '\0';
    return out;
}

/* Return 1 if bare word `word` appears in `src` at a word boundary. */
static int word_present(const char *src, const char *word) {
    size_t wlen = strlen(word);
    const char *p = src;
    while (*p) {
        if (is_word_char((unsigned char)*p)) {
            const char *ws = p;
            while (is_word_char((unsigned char)*p)) p++;
            if ((size_t)(p - ws) == wlen && memcmp(ws, word, wlen) == 0) return 1;
        } else p++;
    }
    return 0;
}

/* Counter for unique helper name mangling (incremented per where block). */
static int where_seq = 0;

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

/* ── Shared result printer 
 * Type-former nodes (PI/SIGMA/W/ID/SUM) have unforced cod thunks;
 * route them through bridge for term_fprint.  Others use node_print.
 */
static void print_result_node(Heap *h, NodeRef r, Arena *a) {
    NodeTag rtag = (NodeTag)h->nodes[r].tag;
    /* Route through core bridge for types and ND_CORE (L2 terms) */
    if (rtag == ND_PI || rtag == ND_SIGMA || rtag == ND_W ||
        rtag == ND_ID || rtag == ND_SUM   || rtag == ND_CORE) {
        Term *nt = node_to_term(h, r, a);
        if (nt) term_fprint(stdout, nt);
        else    node_print(h, r, 0, 0);
    } else {
        node_print(h, r, 0, 0);
    }
}

/* ── File-scope state */
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

/* ── Module system */
/* module Foo where ... end  pushes "Foo." onto the prefix stack.
 * Every let/let rec/data inside the block is registered as "Foo.name".
 * open Foo  creates unqualified aliases for all "Foo.*" definitions.
 * Nesting is supported up to MODULE_DEPTH_MAX levels.  */
#define MODULE_DEPTH_MAX 8
#define MODULE_PREFIX_MAX 256

static char module_stack[MODULE_DEPTH_MAX][MODULE_PREFIX_MAX]; /* e.g. "Foo." */
static int  module_depth = 0;

static const char *current_module_prefix(void) {
    return module_depth > 0 ? module_stack[module_depth - 1] : "";
}

/* Prepend current module prefix to name.  Returns name unchanged if no module. */
static const char *prefixed(Arena *a, const char *name) {
    const char *pfx = current_module_prefix();
    if (!pfx[0]) return name;
    size_t plen = strlen(pfx), nlen = strlen(name);
    char  *buf  = (char *)arena_alloc(a, plen + nlen + 1);
    memcpy(buf, pfx, plen);
    memcpy(buf + plen, name, nlen);
    buf[plen + nlen] = '\0';
    return buf;
}

/* ── Forward declaration  */
static int load_file(const char *path);

#define MAX_LET_ARGS 8

/* ── process_line
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
    /* Strip leading whitespace — allows indented `let`/`data` inside modules */
    while (*raw == ' ' || *raw == '\t') raw++;
    /* Skip blank lines and -- comments (the file loader strips these, but
     * the interactive REPL doesn't, so handle them here for safety) */
    if (raw[0] == '\0') return 0;
    if (raw[0] == '-' && raw[1] == '-') return 0;
    /* Strip inline trailing comment -- */
    const char *cmt = strstr(raw, "--");
    if (cmt) {
        /* Don't strip inside a string (none exist in our language) */
        size_t clen = (size_t)(cmt - raw);
        char *stripped = (char *)alloca(clen + 1);
        memcpy(stripped, raw, clen);
        stripped[clen] = '\0';
        /* Trim trailing whitespace */
        while (clen > 0 && (stripped[clen-1] == ' ' || stripped[clen-1] == '\t'))
            stripped[--clen] = '\0';
        if (clen == 0) return 0;
        raw = stripped;
    }

    /* ── :q / :quit — ignored in file context, meaningful only in REPL ── */
    if ((strcmp(raw, ":q") == 0 || strcmp(raw, ":quit") == 0) && origin)
        return 0;

    /* ── module NAME where  (open a module namespace) ── */
    if (strncmp(raw, "module ", 7) == 0) {
        const char *p = raw + 7;
        while (*p == ' ' || *p == '\t') p++;
        const char *ns = p;
        while (*p && *p != ' ' && *p != '\t') p++;
        size_t nlen = (size_t)(p - ns);
        if (nlen == 0 || nlen >= MODULE_PREFIX_MAX - 1) {
            if (!origin) printf("  error  : invalid module name\n");
            return -1;
        }
        if (module_depth >= MODULE_DEPTH_MAX) {
            if (!origin) printf("  error  : modules nested too deeply (max %d)\n",
                                MODULE_DEPTH_MAX);
            return -1;
        }
        /* Cumulative prefix: outer prefix + NAME. */
        const char *outer = current_module_prefix();
        size_t olen = strlen(outer);
        if (olen + nlen + 1 >= MODULE_PREFIX_MAX) {
            if (!origin) printf("  error  : module prefix too long\n");
            return -1;
        }
        memcpy(module_stack[module_depth], outer, olen);
        memcpy(module_stack[module_depth] + olen, ns, nlen);
        module_stack[module_depth][olen + nlen]     = '.';
        module_stack[module_depth][olen + nlen + 1] = '\0';
        module_depth++;
        if (!quiet) {
            printf("  module : %.*s\n", (int)nlen, ns);
        }
        return 0;
    }

    /* ── end  (close current module) ── */
    if (strcmp(raw, "end") == 0 ||
        (strncmp(raw, "end", 3) == 0 && (raw[3] == ' ' || raw[3] == '\t'))) {
        if (module_depth == 0) {
            if (!origin) printf("  error  : 'end' without matching 'module'\n");
            return -1;
        }
        module_depth--;
        if (!quiet) {
            char disp[MODULE_PREFIX_MAX];
            strncpy(disp, module_stack[module_depth], MODULE_PREFIX_MAX - 1);
            disp[MODULE_PREFIX_MAX - 1] = '\0';
            int dlen = (int)strlen(disp);
            if (dlen > 0 && disp[dlen-1] == '.') disp[dlen-1] = '\0';
            printf("  end    : %s\n", disp);
        }
        return 0;
    }

    /* ── open NAME  (bring module definitions into scope unqualified) ── */
    if (strncmp(raw, "open ", 5) == 0) {
        const char *p = raw + 5;
        while (*p == ' ' || *p == '\t') p++;
        if (!*p) {
            if (!origin) printf("  usage  : open MODULE\n");
            return -1;
        }
        /* Strip trailing whitespace from module name */
        char modname[MODULE_PREFIX_MAX];
        strncpy(modname, p, MODULE_PREFIX_MAX - 1);
        modname[MODULE_PREFIX_MAX - 1] = '\0';
        int mlen = (int)strlen(modname);
        while (mlen > 0 && (modname[mlen-1] == ' ' || modname[mlen-1] == '\t'))
            modname[--mlen] = '\0';
        char pfx[MODULE_PREFIX_MAX + 2];
        snprintf(pfx, sizeof(pfx), "%s.", modname);
        int pfxlen = (int)strlen(pfx);
        int count = 0;
        /* Scan in reverse so most-recent definition of each name wins.
         * Track which short names we've already aliased to avoid double-counting. */
        int n = def_count();
        /* Use a simple seen-set via the permanent arena to track aliased names.
         * Since we allow shadowing (always alias), just alias and count unique short names. */
        for (int i = n - 1; i >= 0; i--) {
            const char *dname = def_name(i);
            if (strncmp(dname, pfx, (size_t)pfxlen) != 0) continue;
            const char *short_name = dname + pfxlen;
            /* Only alias the most-recent (first seen in reverse scan) definition */
            int already = 0;
            for (int j = i + 1; j < n; j++) {
                const char *dn2 = def_name(j);
                if (strncmp(dn2, pfx, (size_t)pfxlen) == 0 &&
                    strcmp(dn2 + pfxlen, short_name) == 0) { already = 1; break; }
            }
            if (already) continue;
            /* Always alias — shadows any existing short name */
            def_alias(short_name, i);
            count++;
        }
        if (count == 0 && !quiet)
            printf("  open   : %s (0 names — module not found or empty)\n", modname);
        else if (!quiet)
            printf("  open   : %s (%d name%s)\n", modname, count, count==1?"":"s");
        return 0;
    }

    /* ── import "path" [as NAME] ── */
    if (strncmp(raw, "import ", 7) == 0) {
        const char *p = raw + 7;
        while (*p == ' ' || *p == '\t') p++;
        if (*p != '"') {
            if (!origin) printf("  usage  : import \"file.lam\" [as Name]\n");
            return -1;
        }
        p++;
        const char *end_q = strchr(p, '"');
        if (!end_q) {
            if (!origin) printf("  error  : import: unterminated filename\n");
            return -1;
        }
        size_t plen = (size_t)(end_q - p);
        char *path = (char *)malloc(plen + 1);
        if (!path) { fprintf(stderr, "out of memory\n"); return -1; }
        memcpy(path, p, plen); path[plen] = '\0';

        /* Check for "as NAME" */
        const char *rest_q = end_q + 1;
        while (*rest_q == ' ' || *rest_q == '\t') rest_q++;
        int has_as = (strncmp(rest_q, "as ", 3) == 0 ||
                      strncmp(rest_q, "as\t", 3) == 0);
        char as_pfx[MODULE_PREFIX_MAX] = "";
        if (has_as) {
            rest_q += 3;
            while (*rest_q == ' ' || *rest_q == '\t') rest_q++;
            snprintf(as_pfx, sizeof(as_pfx), "%s.", rest_q);
        }

        int defs_before = def_count();
        int r = load_file(path);
        free(path);
        if (r < 0) return -1;

        /* If "as NAME": alias all newly-added defs with the NAME. prefix */
        if (has_as && as_pfx[0]) {
            int defs_after = def_count();
            for (int i = defs_before; i < defs_after; i++) {
                const char *dname = def_name(i);
                Arena tmp = {NULL};
                size_t alen = strlen(as_pfx) + strlen(dname) + 1;
                char  *aname = (char *)arena_alloc(&tmp, alen);
                snprintf(aname, alen, "%s%s", as_pfx, dname);
                if (def_lookup(aname) < 0) def_alias(aname, i);
                arena_free_all(&tmp);
            }
        }
        return 0;
    }

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
            /* If inside a module, create qualified aliases for type + ctors */
            const char *pfx = current_module_prefix();
            if (pfx[0]) {
                IndDef *fam = ind_get(fam_idx);
                /* Alias the type constructor */
                if (fam->type_def_idx >= 0) {
                    const char *qname = prefixed(&a, def_name(fam->type_def_idx));
                    if (def_lookup(qname) < 0) def_alias(qname, fam->type_def_idx);
                }
                /* Alias each data constructor */
                for (int ci = 0; ci < fam->n_ctors; ci++) {
                    if (fam->ctors[ci].def_idx >= 0) {
                        int di = fam->ctors[ci].def_idx;
                        const char *qname = prefixed(&a, def_name(di));
                        if (def_lookup(qname) < 0) def_alias(qname, di);
                    }
                }
                /* Alias the eliminator */
                if (fam->elim_def_idx >= 0) {
                    const char *qname = prefixed(&a, def_name(fam->elim_def_idx));
                    if (def_lookup(qname) < 0) def_alias(qname, fam->elim_def_idx);
                }
            }
            if (!quiet) {
                IndDef *fam = ind_get(fam_idx);
                if (pfx[0])
                    printf("  defined family: %s%s (%d constructor%s)\n",
                           pfx, fam->name, fam->n_ctors, fam->n_ctors == 1 ? "" : "s");
                else
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

        /* ── argument shorthand: let rec f x y = body ── */
        char *letrec_args[MAX_LET_ARGS];
        int   n_letrec_args = 0;
        while (is_word_char((unsigned char)*rest) && *rest != '=' &&
               n_letrec_args < MAX_LET_ARGS) {
            const char *as = rest;
            while (is_word_char((unsigned char)*rest)) rest++;
            size_t alen = (size_t)(rest - as);
            char *arg = (char *)arena_alloc(&a, alen + 1);
            memcpy(arg, as, alen); arg[alen] = '\0';
            letrec_args[n_letrec_args++] = arg;
            while (*rest == ' ' || *rest == '\t') rest++;
        }

        /* Optional type annotation */
        const char *type_src = NULL;
        if (*rest == ':') {
            if (n_letrec_args > 0) {
                if (!origin) printf("  error  : let rec %s: type annotation not allowed with argument shorthand\n", lname);
                heap_free(&h); arena_free_all(&a);
                return -1;
            }
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
            if (!origin) printf("  usage  : let rec name [args] = body  |  let rec name [: type] = body\n");
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        while (*rest == ' ' || *rest == '\t') rest++;

        /* Wrap body in lambdas for declared args (right-to-left) */
        const char *body_raw = rest;
        if (n_letrec_args > 0) {
            char *wrapped = (char *)arena_alloc(&a, strlen(rest) + 1);
            strcpy(wrapped, rest);
            for (int ai = n_letrec_args - 1; ai >= 0; ai--) {
                size_t flen = 4 + strlen(letrec_args[ai]) + 2 + strlen(wrapped) + 1;
                char *w2 = (char *)arena_alloc(&a, flen);
                snprintf(w2, flen, "fn %s. %s", letrec_args[ai], wrapped);
                wrapped = w2;
            }
            body_raw = wrapped;
        }

        /* Build "fix (\name. body)" as a string — self-ref uses unqualified name */
        const char *body_pp = preprocess(&a, body_raw);
        size_t blen = strlen(body_pp);
        /* "fix (\name. " + body + ")" */
        size_t fix_len = 7 + name_len + 2 + blen + 1 + 1;
        char *fix_src = (char *)arena_alloc(&a, fix_len);
        snprintf(fix_src, fix_len, "fix (\\%s. %s)", lname, body_pp);

        const char *qname = prefixed(&a, lname);  /* qualified name for registration */
        int idx = def_define_nocheck(qname, type_src, fix_src);
        if (idx < 0) {
            if (origin)
                fprintf(stderr, "%s: could not define '%s'\n", origin, qname);
            else
                printf("  error  : could not define '%s'\n", qname);
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        if (!quiet) printf("  defined: %s\n", qname);
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

        /* ── argument shorthand: let f x y = body  ──
         * Collect identifier tokens before ':' or '='.  Desugared later by
         * wrapping the body in fn-lambdas right-to-left. */
        char *let_args[MAX_LET_ARGS];
        int   n_let_args = 0;
        while (is_word_char((unsigned char)*rest) && *rest != '=' &&
               n_let_args < MAX_LET_ARGS) {
            const char *as = rest;
            while (is_word_char((unsigned char)*rest)) rest++;
            size_t alen = (size_t)(rest - as);
            char *arg = (char *)arena_alloc(&a, alen + 1);
            memcpy(arg, as, alen); arg[alen] = '\0';
            let_args[n_let_args++] = arg;
            while (*rest == ' ' || *rest == '\t') rest++;
        }

        const char *type_start = NULL;
        size_t      type_len   = 0;

        if (*rest == ':') {
            if (n_let_args > 0) {
                if (!origin) printf("  error  : let %s: type annotation not allowed with argument shorthand; write 'let %s : type = \\x. body' instead\n", lname, lname);
                heap_free(&h); arena_free_all(&a);
                return -1;
            }
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
            if (!origin) printf("  usage  : let name [args] = expr  |  let name [: type] = expr\n");
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

        /* ── Where clause: let f = body where g1 [args] = rhs1 ; g2 = rhs2 ── */
        const char *where_kw = find_where_kw(rest);
        if (where_kw) {
            /* Split main body from where clause */
            size_t body_len = (size_t)(where_kw - rest);
            while (body_len > 0 &&
                   (rest[body_len-1] == ' ' || rest[body_len-1] == '\t'))
                body_len--;
            char *body_raw = (char *)arena_alloc(&a, body_len + 1);
            memcpy(body_raw, rest, body_len);
            body_raw[body_len] = '\0';

            const char *wrest = where_kw + 5; /* skip "where" */
            while (*wrest == ' ' || *wrest == '\t') wrest++;

            /* Unique sequence number for this where block */
            int seq = where_seq++;

            /* Parse helpers: ';'-separated "hname [args] = rhs" entries */
#define MAX_WHERE_HELPERS 16
#define MAX_WHERE_ARGS     8
            char *h_names[MAX_WHERE_HELPERS];
            char *h_mangled[MAX_WHERE_HELPERS];
            char *h_rhs_raw[MAX_WHERE_HELPERS];
            int   h_nargs[MAX_WHERE_HELPERS];
            char *h_args[MAX_WHERE_HELPERS][MAX_WHERE_ARGS];
            int   n_h = 0;
            int   parse_ok = 1;

            const char *hp = wrest;
            while (*hp && n_h < MAX_WHERE_HELPERS) {
                /* Find next ';' at paren-depth 0 */
                const char *semi = NULL;
                int d = 0;
                for (const char *q = hp; *q; q++) {
                    if (*q == '(' || *q == '[') { d++; continue; }
                    if ((*q == ')' || *q == ']') && d > 0) { d--; continue; }
                    if (d == 0 && *q == ';') { semi = q; break; }
                }
                size_t seg_total = semi ? (size_t)(semi - hp) : strlen(hp);

                /* Trim segment */
                const char *seg = hp;
                size_t seg_len = seg_total;
                while (seg_len > 0 && (*seg == ' ' || *seg == '\t'))
                    { seg++; seg_len--; }
                while (seg_len > 0 &&
                       (seg[seg_len-1] == ' ' || seg[seg_len-1] == '\t'))
                    seg_len--;

                if (seg_len == 0) {
                    hp += seg_total + (semi ? 1 : 0);
                    while (*hp == ' ' || *hp == '\t') hp++;
                    continue;
                }

                /* Find '=' at depth 0 in segment */
                const char *eq = NULL;
                d = 0;
                for (size_t si = 0; si < seg_len; si++) {
                    if (seg[si] == '(' || seg[si] == '[') { d++; continue; }
                    if ((seg[si] == ')' || seg[si] == ']') && d > 0)
                        { d--; continue; }
                    if (d == 0 && seg[si] == '=') { eq = seg + si; break; }
                }
                if (!eq) {
                    if (origin)
                        fprintf(stderr,
                            "%s: where clause: missing '=' in helper\n", origin);
                    else
                        printf("  error  : where clause: missing '=' in helper\n");
                    parse_ok = 0; break;
                }

                /* LHS: seg..eq, trimmed */
                size_t lhs_len = (size_t)(eq - seg);
                while (lhs_len > 0 &&
                       (seg[lhs_len-1] == ' ' || seg[lhs_len-1] == '\t'))
                    lhs_len--;

                /* Extract helper name (first word in LHS) */
                size_t ni = 0;
                while (ni < lhs_len && (seg[ni] == ' ' || seg[ni] == '\t')) ni++;
                size_t hname_s = ni;
                while (ni < lhs_len && is_word_char((unsigned char)seg[ni])) ni++;
                size_t hname_len = ni - hname_s;
                if (hname_len == 0) {
                    if (origin)
                        fprintf(stderr,
                            "%s: where clause: invalid helper name\n", origin);
                    else
                        printf("  error  : where clause: invalid helper name\n");
                    parse_ok = 0; break;
                }
                char *hname = (char *)arena_alloc(&a, hname_len + 1);
                memcpy(hname, seg + hname_s, hname_len);
                hname[hname_len] = '\0';

                /* Extract args (remaining tokens in LHS after name) */
                int n_args = 0;
                while (ni < lhs_len) {
                    while (ni < lhs_len && (seg[ni] == ' ' || seg[ni] == '\t')) ni++;
                    if (ni >= lhs_len) break;
                    if (n_args >= MAX_WHERE_ARGS) {
                        if (origin)
                            fprintf(stderr, "%s: where clause: helper '%s' has"
                                    " too many args (max %d)\n",
                                    origin, hname, MAX_WHERE_ARGS);
                        else
                            printf("  error  : where clause: helper '%s' has"
                                   " too many args (max %d)\n",
                                   hname, MAX_WHERE_ARGS);
                        parse_ok = 0; break;
                    }
                    size_t as = ni;
                    while (ni < lhs_len && is_word_char((unsigned char)seg[ni])) ni++;
                    size_t alen = ni - as;
                    if (alen > 0) {
                        char *arg = (char *)arena_alloc(&a, alen + 1);
                        memcpy(arg, seg + as, alen);
                        arg[alen] = '\0';
                        h_args[n_h][n_args++] = arg;
                    }
                }
                if (!parse_ok) break;

                /* RHS: after '=', trimmed */
                const char *rhs_s = eq + 1;
                while (*rhs_s == ' ' || *rhs_s == '\t') rhs_s++;
                size_t rhs_len = seg_len - (size_t)(rhs_s - seg);
                while (rhs_len > 0 &&
                       (rhs_s[rhs_len-1] == ' ' || rhs_s[rhs_len-1] == '\t'))
                    rhs_len--;
                char *rhs_raw = (char *)arena_alloc(&a, rhs_len + 1);
                memcpy(rhs_raw, rhs_s, rhs_len);
                rhs_raw[rhs_len] = '\0';

                /* Generate unique mangled name: _w_SEQ_FNAME_HNAME */
                size_t mlen = 4 + 12 + name_len + 1 + hname_len + 1;
                char *mng = (char *)arena_alloc(&a, mlen);
                snprintf(mng, mlen, "_w_%d_%s_%s", seq, lname, hname);

                h_names[n_h]   = hname;
                h_mangled[n_h] = mng;
                h_rhs_raw[n_h] = rhs_raw;
                h_nargs[n_h]   = n_args;
                n_h++;

                hp += seg_total + (semi ? 1 : 0);
                while (*hp == ' ' || *hp == '\t') hp++;
            }

            /* Error if the where clause was truncated at the helper limit */
            if (*hp && n_h >= MAX_WHERE_HELPERS) {
                if (origin)
                    fprintf(stderr, "%s: where clause: too many helpers"
                            " (max %d)\n", origin, MAX_WHERE_HELPERS);
                else
                    printf("  error  : where clause: too many helpers"
                           " (max %d)\n", MAX_WHERE_HELPERS);
                parse_ok = 0;
            }

            if (!parse_ok) {
                heap_free(&h); arena_free_all(&a);
                return -1;
            }

            /* Build substitution arrays */
            const char *olds[MAX_WHERE_HELPERS], *news[MAX_WHERE_HELPERS];
            for (int i = 0; i < n_h; i++) {
                olds[i] = h_names[i];
                news[i] = h_mangled[i];
            }

            /* Topological sort: define helpers whose deps are already defined
             * first.  Detects circular deps (no progress → error).
             * dep[i][j]=1 means helper i's rhs mentions helper j's name. */
            int topo_order[MAX_WHERE_HELPERS];
            int in_topo[MAX_WHERE_HELPERS];
            int n_topo = 0;
            memset(in_topo, 0, sizeof(in_topo));

            while (n_topo < n_h && parse_ok) {
                int progress = 0;
                for (int i = 0; i < n_h; i++) {
                    if (in_topo[i]) continue;
                    /* Check: does h_rhs_raw[i] reference any helper j not yet ordered? */
                    int ready = 1;
                    for (int j = 0; j < n_h; j++) {
                        if (j == i || in_topo[j]) continue;
                        if (word_present(h_rhs_raw[i], h_names[j])) { ready = 0; break; }
                    }
                    if (ready) {
                        topo_order[n_topo++] = i;
                        in_topo[i] = 1;
                        progress = 1;
                    }
                }
                if (!progress) {
                    if (origin)
                        fprintf(stderr, "%s: where clause: circular dependency"
                                " between helpers (use fix for recursion)\n", origin);
                    else
                        printf("  error  : where clause: circular dependency"
                               " between helpers (use fix for recursion)\n");
                    parse_ok = 0;
                }
            }

            /* Define each helper in topological order */
            for (int ti = 0; ti < n_topo && parse_ok; ti++) {
                int i = topo_order[ti];
                char *rhs_s2 = subst_words(&a, h_rhs_raw[i], olds, news, n_h);
                /* Wrap rhs in lambdas for declared args (right-to-left) */
                char *full_rhs = rhs_s2;
                for (int ai = h_nargs[i] - 1; ai >= 0; ai--) {
                    const char *arg = h_args[i][ai];
                    size_t flen = 4 + strlen(arg) + 2 + strlen(full_rhs) + 1;
                    char *wrapped = (char *)arena_alloc(&a, flen);
                    snprintf(wrapped, flen, "fn %s. %s", arg, full_rhs);
                    full_rhs = wrapped;
                }
                const char *pp_rhs = preprocess(&a, full_rhs);
                int hidx = def_define_nocheck(h_mangled[i], NULL, pp_rhs);
                if (hidx < 0) {
                    if (origin)
                        fprintf(stderr, "%s: where clause: could not define"
                                " helper '%s'\n", origin, h_names[i]);
                    else
                        printf("  error  : where clause: could not define"
                               " helper '%s'\n", h_names[i]);
                    parse_ok = 0;
                }
            }

            if (!parse_ok) {
                heap_free(&h); arena_free_all(&a);
                return -1;
            }

            /* Substitute helper refs in main body and define the binding */
            char *body_s2  = subst_words(&a, body_raw, olds, news, n_h);
            const char *pp_body = preprocess(&a, body_s2);
            const char *qname   = prefixed(&a, lname);
            int idx = def_define_nocheck(qname, pp_type, pp_body);
            if (idx < 0) {
                if (origin)
                    fprintf(stderr, "%s: could not define '%s'\n", origin, qname);
                else
                    printf("  error  : could not define '%s'\n", qname);
                heap_free(&h); arena_free_all(&a);
                return -1;
            }
            if (!quiet) printf("  defined: %s\n", qname);
            heap_free(&h); arena_free_all(&a);
            return 0;
        }

        /* ── No where clause: original path ── */
        /* Wrap body in lambdas for declared args (right-to-left) */
        const char *body_src = rest;
        if (n_let_args > 0) {
            char *wrapped = (char *)arena_alloc(&a, strlen(rest) + 1);
            strcpy(wrapped, rest);
            for (int ai = n_let_args - 1; ai >= 0; ai--) {
                size_t flen = 4 + strlen(let_args[ai]) + 2 + strlen(wrapped) + 1;
                char *w2 = (char *)arena_alloc(&a, flen);
                snprintf(w2, flen, "fn %s. %s", let_args[ai], wrapped);
                wrapped = w2;
            }
            body_src = wrapped;
        }
        const char *pp_expr = preprocess(&a, body_src);
        const char *qname   = prefixed(&a, lname);  /* module-qualified name */

        int idx = def_define_nocheck(qname, pp_type, pp_expr);
        if (idx < 0) {
            if (origin)
                fprintf(stderr, "%s: could not define '%s'\n", origin, qname);
            else
                printf("  error  : could not define '%s'\n", qname);
            heap_free(&h); arena_free_all(&a);
            return -1;
        }
        if (!quiet) printf("  defined: %s\n", qname);
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
        {
            int eq = node_conv(&h, &a, res1, res2);
            printf("  conv   : %s%s%s\n",
                   COL(eq ? C_CONV_Y : C_CONV_N),
                   eq ? "yes" : "no",
                   COL(C_RESET));
        }
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

    printf("  %snormal%s : %s", COL(C_RESULT), COL(C_RESET), COL(C_BOLD));
    print_result_node(&h, result, &a);
    printf("%s\n", COL(C_RESET));

    if (is_type) {
        Val *ty = infer(&a, 0, NULL, NULL, t);
        if (!ty) {
            printf("  %stype%s   : %s(type error)%s\n",
                   COL(C_TYPE), COL(C_RESET), COL(C_ERROR), COL(C_RESET));
        } else {
            printf("  %stype%s   : %s", COL(C_TYPE), COL(C_RESET), COL(C_BOLD));
            term_fprint(stdout, nbe_quote(&a, 0, ty));
            printf("%s\n", COL(C_RESET));
        }
    }

    heap_free(&h);
    arena_free_all(&a);
    return 0;
}

/* ── load_file
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

    /* Save module depth: if the file opens a module but errors before end,
     * restore depth so the caller's module context is not corrupted. */
    int saved_module_depth = module_depth;

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

        /* import "other.lam" [as NAME] — resolve relative to current file's dir */
        if (strncmp(accum, "import", 6) == 0 &&
            (accum[6] == ' ' || accum[6] == '\t' || accum[6] == '"')) {
            char *p = accum + 6;
            while (*p == ' ' || *p == '\t') p++;
            if (*p == '"') {
                p++;
                char *end = strchr(p, '"');
                if (end) {
                    size_t flen = (size_t)(end - p);
                    char import_path[4096];
                    /* Absolute paths (start with '/') are used as-is */
                    if (dir_prefix[0] && p[0] != '/')
                        snprintf(import_path, sizeof(import_path), "%s%.*s",
                                 dir_prefix, (int)flen, p);
                    else
                        snprintf(import_path, sizeof(import_path), "%.*s",
                                 (int)flen, p);
                    /* Build a synthetic line with the resolved path for process_line
                     * so that "as NAME" support is handled there. */
                    const char *rest_after_quote = end + 1;
                    while (*rest_after_quote == ' ' || *rest_after_quote == '\t')
                        rest_after_quote++;
                    char synth[4096 + 256];
                    if (rest_after_quote[0])  /* has "as NAME" */
                        snprintf(synth, sizeof(synth), "import \"%s\" %s",
                                 import_path, rest_after_quote);
                    else
                        snprintf(synth, sizeof(synth), "import \"%s\"", import_path);
                    if (process_line(synth, origin, 1) < 0) errors++;
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

    /* Check for unclosed modules left by this file */
    if (module_depth > saved_module_depth) {
        int unclosed = module_depth - saved_module_depth;
        fprintf(stderr, "  warning: %s: %d unclosed module%s (missing 'end')\n",
                path, unclosed, unclosed == 1 ? "" : "s");
        /* Restore caller's module context */
        module_depth = saved_module_depth;
        errors++;
    }

    if (errors == 0) {
        add_to_loaded_set(canon); /* mark as successfully loaded */
        printf("  %sloaded%s : %s\n", COL(C_LOADED), COL(C_RESET), path);
    } else {
        fprintf(stderr, "  %sloaded%s : %s (%d error%s)\n",
                COL(C_ERROR), COL(C_RESET),
                path, errors, errors == 1 ? "" : "s");
    }
    free(canon);
    return errors > 0 ? -1 : 0;
}

/* ── REPL */

int main(int argc, char **argv) {
    for (int i = 1; i < argc; i++)
        if (strcmp(argv[i], "--dump-graph") == 0) dump_graph_g = 1;

    load_stdlib();

    use_color = isatty(STDOUT_FILENO);

    printf("%sllang%s  — MLTT + cubical HoTT proof assistant\n", COL(C_BOLD), COL(C_RESET));
    printf("\n");
    printf("  let name [args] = expr       — define a name (args desugared to lambdas)\n");
    printf("  let name : type = expr       — define with type annotation\n");
    printf("  let rec name [args] = expr   — structurally recursive definition\n");
    printf("  data T where ctor : T ; ...  — inductive type\n");
    printf("  :type expr                   — show type of expression\n");
    printf("  :conv e1 ; e2                — check definitional equality\n");
    printf("  :load \"file.lam\"             — load a source file\n");
    printf("  Ctrl-D to quit\n");
    printf("\n");
    printf("  %sfn x. body%s  or  %sλx. body%s     %sPi(x:A). B%s  or  %sΠ(x:A). B%s     %sSg(x:A). B%s  or  %sΣ(x:A). B%s\n",
           COL(C_DIM), COL(C_RESET), COL(C_DIM), COL(C_RESET),
           COL(C_DIM), COL(C_RESET), COL(C_DIM), COL(C_RESET),
           COL(C_DIM), COL(C_RESET), COL(C_DIM), COL(C_RESET));
    printf("\n");

#ifndef HAVE_READLINE
    char   *buf = NULL;
    size_t  cap = 0;
#endif

    for (;;) {
        const char *raw = NULL;

#ifdef HAVE_READLINE
        {
            char prompt[32];
            if (use_color) snprintf(prompt, sizeof(prompt), "\033[1;36m>>\033[0m ");
            else           snprintf(prompt, sizeof(prompt), ">> ");
            raw = readline(prompt);
        }
        if (!raw) { printf("\n"); break; }
        if (raw[0] != '\0') add_history(raw);
#else
        printf("%s>>%s ", COL(C_PROMPT), COL(C_RESET));
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
