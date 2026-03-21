/*
 * forth.c — token-threaded Forth interpreter for pico-lambda
 *
 * A derived from forth-vga/forth.c with the following cuts:
 *   - Float stack and all F* words removed
 *   - RTOS words (TASKS, UPTIME, MS, YIELD) removed
 *   - Filesystem words (INCLUDE, EDIT) removed
 *   - forth_save_words() removed
 *   - Interactive REPL (forth_run) and line editor removed
 *   - VGA / RGB vocabulary removed
 *
 * Key additions vs the original:
 *   - forth_set_output_fn(): redirect Forth output to a caller callback
 *     instead of USB serial; used by dispatch.c to capture into a buffer
 *   - Execution step counter: stops runaway programs at EXEC_LIMIT steps
 *   - forth_had_error(): lets dispatch.c set out->ok correctly
 *
 * Architecture (unchanged from original):
 *   Dictionary : flat array of word_t structs, newest-first search
 *   Body pool  : int32_t array; colon-word bodies are token sequences
 *   Data stack : cell_t array, 64 deep
 *   Return stack: {word_index, body_position} pairs, 32 deep
 *   Loop stack : limit/index pairs for DO..LOOP, 8 deep
 *   String pool: char array for ." and S" literals, monotonic alloc
 */

#include "forth.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

/* ------------------------------------------------------------------- */
/*  Configuration                                                      */
/* ------------------------------------------------------------------- */
#define DS_SZ       64      /* data stack depth                        */
#define RS_SZ       32      /* return stack depth                      */
#define LS_SZ        8      /* DO..LOOP nesting depth                  */
#define CS_SZ       32      /* compile-time branch/loop address stack  */
#define BODY_SZ   4096      /* int32_t cells for compiled word bodies  */
#define STR_SZ     512      /* bytes for inline string literals        */
#define VAR_SZ     128      /* cells for VARIABLE storage              */
#define MAX_WORDS  256      /* maximum dictionary entries              */
#define NAME_MAX    32      /* max word name length (incl. NUL)        */
#define LINE_MAX   512      /* max input line length                   */

/* Hard limit on interpreter steps per forth_eval_string() call.
 * Prevents infinite loops from locking the HTTP event loop. */
#define EXEC_LIMIT  100000

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */
typedef intptr_t cell_t;

typedef struct { int wi; int pos; } rf_t;   /* return stack frame */

typedef struct {
    char    name[NAME_MAX];
    bool    immediate;
    bool    is_prim;
    bool    hidden;     /* set by forth_restrict_to(); invisible to user input */
    void  (*prim)(void);
    int     body;       /* body_pool start index (colon words) */
    int     blen;       /* body length in cells                */
} word_t;

/* ------------------------------------------------------------------ */
/*  Global state                                                      */
/* ------------------------------------------------------------------ */
static word_t   dict[MAX_WORDS];
static int      nwords = 0;

static cell_t   ds[DS_SZ];         /* data stack, grows up       */
static int      dsp = 0;           /* next free slot             */

static rf_t     rs[RS_SZ];         /* return stack               */
static int      rsp = 0;

static cell_t   bp[BODY_SZ];       /* body pool                  */
static int      here = 0;          /* next free body_pool index  */

static char     sp[STR_SZ];        /* string pool                */
static int      sp_here = 0;

static cell_t   vp[VAR_SZ];        /* variable storage           */
static int      vp_here = 0;

static cell_t   ls_lim[LS_SZ];     /* loop limit                 */
static cell_t   ls_idx[LS_SZ];     /* loop index                 */
static int      lsp = 0;

static int      cs[CS_SZ];         /* compile-time addr stack    */
static int      csp = 0;

static bool     compiling = false;
static int      cur_def   = -1;    /* word index being compiled  */

static char     ibuf[LINE_MAX];    /* input line buffer          */
static int      ilen = 0;
static int      ipos = 0;

static int      forth_base = 10;   /* number I/O radix           */

/* Indices of special executor tokens — assigned in forth_init() */
static int tok_lit, tok_br0, tok_br, tok_do_rt, tok_loop_rt,
           tok_exit_rt, tok_slit;

/* Error flags — cleared in forth_init(), set on any error path  */
static bool ds_fault   = false;   /* stack overflow / underflow  */
static bool pool_fault = false;   /* body / string pool overflow */
static bool error_flag = false;   /* any error this session      */

/* Step counter — reset in forth_init(), checked in executor */
static int  exec_steps = 0;

/* Output callback — set by forth_set_output_fn() */
static void (*out_fn)(const char *s, int len) = NULL;

/* ------------------------------------------------------------------ */
/*  Output helpers                                                    */
/* ------------------------------------------------------------------ */
static void out_write(const char *s, int len)
{
    if (out_fn && len > 0) out_fn(s, len);
}

static void out_char(char c)
{
    out_write(&c, 1);
}

static void out_str(const char *s)
{
    out_write(s, (int)strlen(s));
}

/* ------------------------------------------------------------------ */
/*  Stack helpers                                                     */
/* ------------------------------------------------------------------ */
static void push(cell_t v)
{
    if (dsp < DS_SZ) { ds[dsp++] = v; }
    else { ds_fault = true; error_flag = true; }
}

static cell_t pop(void)
{
    if (dsp > 0) { return ds[--dsp]; }
    ds_fault = true; error_flag = true;
    return 0;
}

/* ------------------------------------------------------------------ */
/*  Dictionary helpers                                                */
/* ------------------------------------------------------------------ */
static int find_word(const char *n)
{
    for (int i = nwords - 1; i >= 0; i--)
        if (!dict[i].hidden && strcasecmp(dict[i].name, n) == 0) return i;
    return -1;
}

static int add_prim(const char *n, void (*fn)(void), bool imm)
{
    if (nwords >= MAX_WORDS) {
        printf("FATAL: dictionary full, cannot add '%s'\r\n", n);
        return -1;
    }
    word_t *w = &dict[nwords];
    snprintf(w->name, NAME_MAX, "%s", n);
    w->immediate = imm;
    w->is_prim   = true;
    w->prim      = fn;
    w->body = w->blen = 0;
    return nwords++;
}

/* Panics on failure — used during forth_init() so MAX_WORDS misconfiguration
 * is caught at startup rather than silently misbehaving later. */
static int add_prim_required(const char *n, void (*fn)(void), bool imm)
{
    int idx = add_prim(n, fn, imm);
    if (idx < 0) { while (1) tight_loop_contents(); }
    return idx;
}

/* ------------------------------------------------------------------ */
/*  Compile helpers                                                   */
/* ------------------------------------------------------------------ */
static void emit_tok(int t)
{
    if (here < BODY_SZ) { bp[here++] = (cell_t)t; }
    else { pool_fault = true; error_flag = true; }
}

static void emit_cell(cell_t v)
{
    if (here < BODY_SZ) { bp[here++] = v; }
    else { pool_fault = true; error_flag = true; }
}

/* Patch a forward-branch placeholder.
 * At runtime the offset cell is read and ip_pos advances past it
 * (ip_pos == patch_pos+1), so offset = target - patch_pos - 1. */
static void patch_fwd(int patch_pos, int target)
{
    bp[patch_pos] = (cell_t)(target - patch_pos - 1);
}

/* ------------------------------------------------------------------ */
/*  Executor                                                          */
/* ------------------------------------------------------------------ */
static void execute(int wi)
{
    rsp = 0; lsp = 0; ds_fault = false;
    int ip_wi = wi, ip_pos = 0;

    for (;;) {
        if (exec_steps++ >= EXEC_LIMIT) {
            printf("Error: execution step limit reached\r\n");
            error_flag = true;
            rsp = 0; lsp = 0;
            return;
        }

        word_t *w = &dict[ip_wi];

        if (w->is_prim) {
            w->prim();
            if (ds_fault) {
                printf("Error: stack fault in '%s'\r\n", w->name);
                dsp = 0; ds_fault = false;
                rsp = 0; lsp = 0;
                return;
            }
            if (rsp == 0) return;
            --rsp; ip_wi = rs[rsp].wi; ip_pos = rs[rsp].pos;
            continue;
        }

        /* Colon word: step through body */
        if (ip_pos >= w->blen) {
            if (rsp == 0) return;
            --rsp; ip_wi = rs[rsp].wi; ip_pos = rs[rsp].pos;
            continue;
        }

        int tok = (int)bp[w->body + ip_pos++];

        if (tok == tok_lit) {
            push(bp[w->body + ip_pos++]);
        } else if (tok == tok_slit) {
            int off = (int)bp[w->body + ip_pos++];
            int len = (int)bp[w->body + ip_pos++];
            push((cell_t)(uintptr_t)(sp + off));
            push((cell_t)len);
        } else if (tok == tok_br0) {
            int off = (int)bp[w->body + ip_pos++];
            if (pop() == 0) ip_pos += off;
        } else if (tok == tok_br) {
            int off = (int)bp[w->body + ip_pos++];
            ip_pos += off;
        } else if (tok == tok_do_rt) {
            cell_t start = pop(), lim = pop();
            if (lsp >= LS_SZ) {
                printf("Error: DO loop stack overflow (max %d deep)\r\n", LS_SZ);
                error_flag = true;
                rsp = 0; lsp = 0;
                return;
            }
            ls_lim[lsp] = lim; ls_idx[lsp] = start; lsp++;
        } else if (tok == tok_loop_rt) {
            int off = (int)bp[w->body + ip_pos++];
            if (lsp > 0) {
                if (++ls_idx[lsp - 1] < ls_lim[lsp - 1]) ip_pos += off;
                else lsp--;
            }
        } else if (tok == tok_exit_rt) {
            if (rsp == 0) return;
            --rsp; ip_wi = rs[rsp].wi; ip_pos = rs[rsp].pos;
        } else {
            /* Call another word */
            if (rsp >= RS_SZ) {
                printf("Error: return stack overflow (max %d deep)\r\n", RS_SZ);
                error_flag = true;
                rsp = 0; lsp = 0;
                return;
            }
            rs[rsp].wi = ip_wi; rs[rsp].pos = ip_pos; rsp++;
            ip_wi = tok; ip_pos = 0;
        }
    }
}

/* ------------------------------------------------------------------ */
/*  Tokeniser                                                         */
/* ------------------------------------------------------------------ */
static bool next_token(char *out, int maxlen)
{
    while (ipos < ilen && isspace((unsigned char)ibuf[ipos])) ipos++;
    if (ipos >= ilen) return false;
    int start = ipos;
    while (ipos < ilen && !isspace((unsigned char)ibuf[ipos])) ipos++;
    int len = ipos - start;
    if (len >= maxlen) len = maxlen - 1;
    memcpy(out, ibuf + start, len);
    out[len] = '\0';
    return true;
}

/* Read rest of input up to delimiter ch; store in sp[].
 * Returns offset into sp[] and sets *len. */
static int read_string(char delim, int *len)
{
    int start = sp_here;
    if (ipos < ilen && ibuf[ipos] == ' ') ipos++;   /* skip one leading space */
    while (ipos < ilen && ibuf[ipos] != delim) {
        if (sp_here < STR_SZ) { sp[sp_here++] = ibuf[ipos]; }
        else { pool_fault = true; error_flag = true; }
        ipos++;
    }
    if (ipos < ilen) ipos++;  /* consume delimiter */
    *len = sp_here - start;
    return start;
}

/* ------------------------------------------------------------------ */
/*  Primitive implementations                                         */
/* ------------------------------------------------------------------ */
static void p_noop(void) {}   /* placeholder for special executor tokens */

/* Stack */
static void p_dup(void)   { if (dsp > 0) push(ds[dsp-1]); }
static void p_drop(void)  { pop(); }
static void p_swap(void)  { if (dsp >= 2) { cell_t b=pop(),a=pop(); push(b); push(a); } }
static void p_over(void)  { if (dsp >= 2) push(ds[dsp-2]); }
static void p_rot(void)   { if (dsp >= 3) { cell_t c=pop(),b=pop(),a=pop(); push(b); push(c); push(a); } }
static void p_nip(void)   { if (dsp >= 2) { cell_t v=pop(); pop(); push(v); } }
static void p_tuck(void)  { if (dsp >= 2) { cell_t b=pop(),a=pop(); push(b); push(a); push(b); } }
static void p_2dup(void)  { if (dsp >= 2) { cell_t a=ds[dsp-2],b=ds[dsp-1]; push(a); push(b); } }
static void p_2drop(void) { if (dsp >= 2) { pop(); pop(); } }
static void p_2swap(void) { if (dsp >= 4) { cell_t d=pop(),c=pop(),b=pop(),a=pop(); push(c); push(d); push(a); push(b); } }
static void p_depth(void) { push((cell_t)dsp); }
static void p_qdup(void)  { if (dsp > 0 && ds[dsp-1]) push(ds[dsp-1]); }

/* Arithmetic */
static void p_add(void)    { cell_t b=pop(),a=pop(); push(a+b); }
static void p_sub(void)    { cell_t b=pop(),a=pop(); push(a-b); }
static void p_mul(void)    { cell_t b=pop(),a=pop(); push(a*b); }
static void p_div(void)    { cell_t b=pop(),a=pop(); push(b ? a/b : 0); }
static void p_mod(void)    { cell_t b=pop(),a=pop(); push(b ? a%b : 0); }
static void p_divmod(void) { cell_t b=pop(),a=pop(); push(b ? a%b : 0); push(b ? a/b : 0); }
static void p_neg(void)    { push(-pop()); }
static void p_abs(void)    { cell_t v=pop(); push(v<0?-v:v); }
static void p_1plus(void)  { push(pop()+1); }
static void p_1minus(void) { push(pop()-1); }
static void p_2plus(void)  { push(pop()+2); }
static void p_2mul(void)   { push(pop()*2); }
static void p_2div(void)   { push(pop()/2); }
static void p_max(void)    { cell_t b=pop(),a=pop(); push(a>b?a:b); }
static void p_min(void)    { cell_t b=pop(),a=pop(); push(a<b?a:b); }
static void p_lshift(void) { cell_t n=pop(),v=pop(); push(v<<n); }
static void p_rshift(void) { cell_t n=pop(),v=pop(); push((int32_t)((uint32_t)v>>n)); }

/* Comparison — Forth convention: -1 = true, 0 = false */
static void p_eq(void)   { cell_t b=pop(),a=pop(); push(a==b?-1:0); }
static void p_ne(void)   { cell_t b=pop(),a=pop(); push(a!=b?-1:0); }
static void p_lt(void)   { cell_t b=pop(),a=pop(); push(a<b?-1:0); }
static void p_gt(void)   { cell_t b=pop(),a=pop(); push(a>b?-1:0); }
static void p_le(void)   { cell_t b=pop(),a=pop(); push(a<=b?-1:0); }
static void p_ge(void)   { cell_t b=pop(),a=pop(); push(a>=b?-1:0); }
static void p_0eq(void)  { push(pop()==0?-1:0); }
static void p_0ne(void)  { push(pop()!=0?-1:0); }
static void p_0lt(void)  { push(pop()<0?-1:0); }
static void p_0gt(void)  { push(pop()>0?-1:0); }

/* Logic */
static void p_and(void)    { cell_t b=pop(),a=pop(); push(a&b); }
static void p_or(void)     { cell_t b=pop(),a=pop(); push(a|b); }
static void p_xor(void)    { cell_t b=pop(),a=pop(); push(a^b); }
static void p_invert(void) { push(~pop()); }
static void p_true(void)   { push(-1); }
static void p_false(void)  { push(0); }

/* Memory — @ and ! operate on the variable pool addresses returned by VARIABLE.
 * Arithmetic on arbitrary pointers is not sandbox-safe, but sandbox.c handles
 * the word-level whitelist; here we just implement the semantics correctly. */
static void p_fetch(void)      { cell_t a=pop(); push(*(cell_t *)(uintptr_t)a); }
static void p_store(void)      { cell_t a=pop(),v=pop(); *(cell_t *)(uintptr_t)a=v; }
static void p_cfetch(void)     { cell_t a=pop(); push(*(uint8_t *)(uintptr_t)a); }
static void p_cstore(void)     { cell_t a=pop(),v=pop(); *(uint8_t *)(uintptr_t)a=(uint8_t)v; }
static void p_plus_store(void) { cell_t a=pop(),v=pop(); *(cell_t *)(uintptr_t)a += v; }
static void p_cells(void)      { push(pop() * (cell_t)sizeof(cell_t)); }

/* I/O — all user-visible output goes through out_fn */
static void p_emit(void)
{
    char c = (char)pop();
    out_char(c);
}

static void p_cr(void)
{
    out_str("\n");
}

static void p_space(void)
{
    out_char(' ');
}

static void p_spaces(void)
{
    cell_t n = pop();
    for (cell_t i = 0; i < n; i++) out_char(' ');
}

static void p_dot(void)
{
    char buf[24];
    int n = snprintf(buf, sizeof(buf),
                     forth_base == 16 ? "%lX " : "%ld ",
                     (long)pop());
    out_write(buf, n);
}

static void p_udot(void)
{
    char buf[24];
    int n = snprintf(buf, sizeof(buf),
                     forth_base == 16 ? "%lX " : "%lu ",
                     (unsigned long)(uint32_t)pop());
    out_write(buf, n);
}

static void p_dots(void)
{
    char buf[24];
    int n = snprintf(buf, sizeof(buf), "<%d> ", dsp);
    out_write(buf, n);
    for (int i = 0; i < dsp; i++) {
        n = snprintf(buf, sizeof(buf), "%ld ", (long)ds[i]);
        out_write(buf, n);
    }
}

static void p_type(void)
{
    cell_t len  = pop();
    char  *addr = (char *)(uintptr_t)pop();
    out_write(addr, (int)len);
}

static void p_count(void) /* ( addr -- addr+1 len ) counted string */
{
    cell_t a = pop();
    uint8_t l = *(uint8_t *)(uintptr_t)a;
    push(a + 1);
    push((cell_t)l);
}

static void p_hex(void)     { forth_base = 16; }
static void p_decimal(void) { forth_base = 10; }

static void p_char(void)
{
    char t[NAME_MAX];
    if (next_token(t, NAME_MAX)) push((cell_t)(uint8_t)t[0]);
}

/* Compiler support */
static void p_colon(void)
{
    char name[NAME_MAX];
    if (!next_token(name, NAME_MAX)) {
        printf("?: missing name after :\r\n");
        error_flag = true;
        return;
    }
    if (nwords >= MAX_WORDS) {
        printf("Error: dictionary full\r\n");
        error_flag = true;
        return;
    }
    word_t *w = &dict[nwords];
    snprintf(w->name, NAME_MAX, "%s", name);
    w->immediate = false; w->is_prim = false;
    w->body = here; w->blen = 0;
    cur_def   = nwords++;
    compiling = true;
}

static void p_semicolon(void)   /* IMMEDIATE */
{
    emit_tok(tok_exit_rt);
    if (cur_def >= 0) dict[cur_def].blen = here - dict[cur_def].body;
    compiling = false; cur_def = -1;
}

static void p_immediate(void)
{
    if (nwords > 0) dict[nwords - 1].immediate = true;
}

static void p_lbracket(void) { compiling = false; }   /* IMMEDIATE */
static void p_rbracket(void) { compiling = true;  }

static void p_literal(void)   /* IMMEDIATE: compile TOS as literal */
{
    emit_tok(tok_lit); emit_cell(pop());
}

static void p_tick(void)   /* ' name -- wi */
{
    char name[NAME_MAX];
    if (!next_token(name, NAME_MAX)) return;
    int wi = find_word(name);
    if (wi < 0) {
        printf("?: %s\r\n", name);
        error_flag = true;
    } else {
        push((cell_t)wi);
    }
}

static void p_execute(void)
{
    cell_t wi = pop();
    if (wi >= 0 && wi < nwords) execute((int)wi);
}

static void p_paren(void)   /* ( skip comment until ) */
{
    while (ipos < ilen && ibuf[ipos] != ')') ipos++;
    if (ipos < ilen) ipos++;
}

static void p_backslash(void)   /* \ skip rest of line */
{
    ipos = ilen;
}

static void p_dotquote(void)    /* ." string" — print string (IMMEDIATE) */
{
    int len, off = read_string('"', &len);
    if (compiling) {
        emit_tok(tok_slit); emit_cell((cell_t)off); emit_cell((cell_t)len);
        emit_tok(find_word("TYPE"));
    } else {
        out_write(sp + off, len);
    }
}

static void p_squote(void)      /* S" string" — ( -- addr len ) (IMMEDIATE) */
{
    int len, off = read_string('"', &len);
    if (compiling) {
        emit_tok(tok_slit); emit_cell((cell_t)off); emit_cell((cell_t)len);
    } else {
        push((cell_t)(uintptr_t)(sp + off));
        push((cell_t)len);
    }
}

/* Control flow — all IMMEDIATE, compile only */
static void p_if(void)
{
    emit_tok(tok_br0);
    if (csp < CS_SZ) cs[csp++] = here;
    emit_cell(0);
}

static void p_else(void)
{
    emit_tok(tok_br);
    int else_patch = here; emit_cell(0);
    if (csp > 0) patch_fwd(cs[csp - 1], here);
    cs[csp - 1] = else_patch;
}

static void p_then(void)
{
    if (csp > 0) patch_fwd(cs[--csp], here);
}

static void p_begin(void)  { if (csp < CS_SZ) cs[csp++] = here; }

static void p_until(void)
{
    if (csp > 0) {
        int begin = cs[--csp];
        emit_tok(tok_br0); emit_cell(0);
        patch_fwd(here - 1, begin);
    }
}

static void p_again(void)
{
    if (csp > 0) {
        int begin = cs[--csp];
        emit_tok(tok_br); emit_cell(0);
        patch_fwd(here - 1, begin);
    }
}

static void p_while(void)
{
    emit_tok(tok_br0);
    if (csp < CS_SZ) cs[csp++] = here;
    emit_cell(0);
}

static void p_repeat(void)
{
    if (csp >= 2) {
        int while_patch = cs[--csp];
        int begin       = cs[--csp];
        emit_tok(tok_br); emit_cell(0);
        patch_fwd(here - 1, begin);
        patch_fwd(while_patch, here);
    }
}

static void p_do(void)     /* IMMEDIATE */
{
    emit_tok(tok_do_rt);
    if (csp < CS_SZ) cs[csp++] = here;
}

static void p_loop(void)   /* IMMEDIATE */
{
    if (csp > 0) {
        int loop_start = cs[--csp];
        emit_tok(tok_loop_rt); emit_cell(0);
        patch_fwd(here - 1, loop_start);
    }
}

static void p_leave(void) { if (lsp > 0) ls_idx[lsp-1] = ls_lim[lsp-1]; }
static void p_i(void)     { if (lsp > 0) push(ls_idx[lsp-1]); }
static void p_j(void)     { if (lsp > 1) push(ls_idx[lsp-2]); }
static void p_exit(void)  { if (compiling) emit_tok(tok_exit_rt); }

/* Defining words */
static void p_constant(void)
{
    char name[NAME_MAX];
    if (!next_token(name, NAME_MAX)) return;
    cell_t val = pop();
    if (nwords >= MAX_WORDS) { error_flag = true; return; }
    word_t *w = &dict[nwords];
    snprintf(w->name, NAME_MAX, "%s", name);
    w->immediate = false; w->is_prim = false; w->body = here;
    emit_tok(tok_lit); emit_cell(val); emit_tok(tok_exit_rt);
    w->blen = here - w->body;
    nwords++;
}

static void p_variable(void)
{
    char name[NAME_MAX];
    if (!next_token(name, NAME_MAX)) return;
    if (nwords >= MAX_WORDS || vp_here >= VAR_SZ) {
        error_flag = true;
        return;
    }
    cell_t *addr = &vp[vp_here++]; *addr = 0;
    word_t *w = &dict[nwords];
    snprintf(w->name, NAME_MAX, "%s", name);
    w->immediate = false; w->is_prim = false; w->body = here;
    emit_tok(tok_lit); emit_cell((cell_t)(uintptr_t)addr); emit_tok(tok_exit_rt);
    w->blen = here - w->body;
    nwords++;
}

/* Introspection — output goes through callback so /eval WORDS is usable */
static void p_words(void)
{
    int col = 0;
    out_str("\n");
    for (int i = 0; i < nwords; i++) {
        if (dict[i].name[0] == '(') continue;
        /* Left-pad name to 13 chars for column alignment.
         * Precision caps the name at NAME_MAX-1 so GCC can prove
         * the output fits and suppresses -Wformat-truncation.      */
        char buf[NAME_MAX + 16];
        snprintf(buf, sizeof(buf), "%-13.*s", NAME_MAX - 1, dict[i].name);
        out_str(buf);
        if (++col % 4 == 0) out_str("\n");
    }
    out_str("\n");
}

/* ------------------------------------------------------------------ */
/*  Interpreter                                                       */
/* ------------------------------------------------------------------ */
static void abort_compile(void)
{
    compiling = false;
    if (cur_def >= 0) {
        here   = dict[cur_def].body;
        nwords = cur_def;
        cur_def = -1;
    }
    dsp = 0; csp = 0; rsp = 0; lsp = 0;
}

static void interpret_line(void)
{
    char tok[NAME_MAX];
    while (next_token(tok, NAME_MAX)) {
        int wi = find_word(tok);
        if (wi >= 0) {
            if (compiling && !dict[wi].immediate) {
                emit_tok(wi);
            } else {
                execute(wi);
            }
        } else {
            /* Integer literal — hex (0x...) or decimal */
            char *end;
            bool is_hex = (tok[0] == '0' &&
                           (tok[1] == 'x' || tok[1] == 'X'));
            cell_t n;
            if (is_hex) {
                n = (cell_t)(uint32_t)strtoul(tok, &end, 16);
            } else {
                n = (cell_t)strtol(tok, &end, forth_base);
            }
            if (*end == '\0') {
                if (compiling) { emit_tok(tok_lit); emit_cell(n); }
                else push(n);
            } else {
                printf("?: %s\r\n", tok);
                error_flag = true;
                if (compiling) abort_compile();
                return;
            }
        }

        if (pool_fault) {
            printf("Error: compile pool full\r\n");
            pool_fault = false;
            if (compiling) abort_compile();
            return;
        }
    }
}

/* ------------------------------------------------------------------ */
/*  Public API                                                        */
/* ------------------------------------------------------------------ */

/* forth_init — reset all interpreter state.
 * Called before each HTTP request to enforce statelesness: one request
 * cannot read words defined by a previous request. This is intentional. */
void forth_init(void)
{
    nwords = 0; here = 0; sp_here = 0; vp_here = 0;
    dsp = 0; rsp = 0; lsp = 0; csp = 0;
    compiling = false; cur_def = -1; forth_base = 10;
    ds_fault = false; pool_fault = false; error_flag = false;
    exec_steps = 0;
    out_fn = NULL;

    /* Internal executor tokens — names start with ( so WORDS hides them */
    tok_lit     = add_prim_required("(lit)",  p_noop, false);
    tok_br0     = add_prim_required("(br0)",  p_noop, false);
    tok_br      = add_prim_required("(br)",   p_noop, false);
    tok_do_rt   = add_prim_required("(do)",   p_noop, false);
    tok_loop_rt = add_prim_required("(loop)", p_noop, false);
    tok_exit_rt = add_prim_required("(exit)", p_noop, false);
    tok_slit    = add_prim_required("(slit)", p_noop, false);

    /* Stack */
    add_prim("DUP",    p_dup,    false);
    add_prim("DROP",   p_drop,   false);
    add_prim("SWAP",   p_swap,   false);
    add_prim("OVER",   p_over,   false);
    add_prim("ROT",    p_rot,    false);
    add_prim("NIP",    p_nip,    false);
    add_prim("TUCK",   p_tuck,   false);
    add_prim("2DUP",   p_2dup,   false);
    add_prim("2DROP",  p_2drop,  false);
    add_prim("2SWAP",  p_2swap,  false);
    add_prim("DEPTH",  p_depth,  false);
    add_prim("?DUP",   p_qdup,   false);

    /* Arithmetic */
    add_prim("+",      p_add,    false);
    add_prim("-",      p_sub,    false);
    add_prim("*",      p_mul,    false);
    add_prim("/",      p_div,    false);
    add_prim("MOD",    p_mod,    false);
    add_prim("/MOD",   p_divmod, false);
    add_prim("NEGATE", p_neg,    false);
    add_prim("ABS",    p_abs,    false);
    add_prim("1+",     p_1plus,  false);
    add_prim("1-",     p_1minus, false);
    add_prim("2+",     p_2plus,  false);
    add_prim("2*",     p_2mul,   false);
    add_prim("2/",     p_2div,   false);
    add_prim("MAX",    p_max,    false);
    add_prim("MIN",    p_min,    false);
    add_prim("LSHIFT", p_lshift, false);
    add_prim("RSHIFT", p_rshift, false);

    /* Comparison */
    add_prim("=",      p_eq,    false);
    add_prim("<>",     p_ne,    false);
    add_prim("<",      p_lt,    false);
    add_prim(">",      p_gt,    false);
    add_prim("<=",     p_le,    false);
    add_prim(">=",     p_ge,    false);
    add_prim("0=",     p_0eq,   false);
    add_prim("0<>",    p_0ne,   false);
    add_prim("0<",     p_0lt,   false);
    add_prim("0>",     p_0gt,   false);
    add_prim("TRUE",   p_true,  false);
    add_prim("FALSE",  p_false, false);

    /* Logic */
    add_prim("AND",    p_and,    false);
    add_prim("OR",     p_or,     false);
    add_prim("XOR",    p_xor,    false);
    add_prim("INVERT", p_invert, false);
    add_prim("NOT",    p_invert, false);   /* alias — same semantics in Forth */

    /* Memory */
    add_prim("@",      p_fetch,      false);
    add_prim("!",      p_store,      false);
    add_prim("C@",     p_cfetch,     false);
    add_prim("C!",     p_cstore,     false);
    add_prim("+!",     p_plus_store, false);
    add_prim("CELLS",  p_cells,      false);

    /* I/O */
    add_prim("EMIT",    p_emit,    false);
    add_prim("CR",      p_cr,      false);
    add_prim("SPACE",   p_space,   false);
    add_prim("SPACES",  p_spaces,  false);
    add_prim(".",       p_dot,     false);
    add_prim("U.",      p_udot,    false);
    add_prim(".S",      p_dots,    false);
    add_prim("TYPE",    p_type,    false);
    add_prim("COUNT",   p_count,   false);
    add_prim("HEX",     p_hex,     false);
    add_prim("DECIMAL", p_decimal, false);
    add_prim("CHAR",    p_char,    false);

    /* Compiler */
    add_prim(":",         p_colon,     false);
    add_prim(";",         p_semicolon, true);
    add_prim("IMMEDIATE", p_immediate, false);
    add_prim("[",         p_lbracket,  true);
    add_prim("]",         p_rbracket,  false);
    add_prim("LITERAL",   p_literal,   true);
    add_prim("'",         p_tick,      false);
    add_prim("EXECUTE",   p_execute,   false);
    add_prim("(",         p_paren,     true);
    add_prim("\\",        p_backslash, true);
    add_prim(".\"",       p_dotquote,  true);
    add_prim("S\"",       p_squote,    true);
    add_prim("EXIT",      p_exit,      true);

    /* Control flow (all IMMEDIATE) */
    add_prim("IF",     p_if,     true);
    add_prim("ELSE",   p_else,   true);
    add_prim("THEN",   p_then,   true);
    add_prim("BEGIN",  p_begin,  true);
    add_prim("UNTIL",  p_until,  true);
    add_prim("AGAIN",  p_again,  true);
    add_prim("WHILE",  p_while,  true);
    add_prim("REPEAT", p_repeat, true);
    add_prim("DO",     p_do,     true);
    add_prim("LOOP",   p_loop,   true);
    add_prim("LEAVE",  p_leave,  false);
    add_prim("I",      p_i,      false);
    add_prim("J",      p_j,      false);

    /* Defining words */
    add_prim("CONSTANT", p_constant, false);
    add_prim("VARIABLE", p_variable, false);

    /* Introspection */
    add_prim("WORDS",  p_words, false);
}

/* Hide every word whose name is NOT in the allowed[] array.
 * Called by sandbox_install() after forth_init().
 * Internal tokens (names starting with '(') are always kept. */
void forth_restrict_to(const char **allowed, int count)
{
    for (int i = 0; i < nwords; i++) {
        if (dict[i].name[0] == '(') continue;   /* never hide executor tokens */
        bool found = false;
        for (int j = 0; j < count; j++) {
            if (strcasecmp(dict[i].name, allowed[j]) == 0) { found = true; break; }
        }
        if (!found) dict[i].hidden = true;
    }
}

void forth_set_output_fn(void (*fn)(const char *s, int len))
{
    out_fn = fn;
}

/* Evaluate a Forth source string.
 * Splits on newlines and feeds each line through the interpreter. */
void forth_eval_string(const char *src)
{
    const char *p = src;
    while (*p) {
        int n = 0;
        while (*p && *p != '\n' && *p != '\r' && n < LINE_MAX - 1)
            ibuf[n++] = *p++;
        if (*p == '\r') p++;
        if (*p == '\n') p++;
        ibuf[n] = '\0';
        ilen = n;
        ipos = 0;
        if (n > 0) interpret_line();
        if (error_flag && exec_steps >= EXEC_LIMIT) break;
    }
}

bool forth_had_error(void)
{
    return error_flag;
}
