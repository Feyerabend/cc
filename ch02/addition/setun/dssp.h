#ifndef DSSP_H
#define DSSP_H

#include "setun70.h"

/*
 * DSSP  —  Dialogue System of Structured Programming
 *
 * A Forth-like interpreter that runs authentically *inside* the Setun-70
 * emulator.  All word bodies, the dictionary, and the outer interpreter loop
 * are Setun-70 tryte programs loaded into VM memory.
 *
 * Threading model:  DIRECT THREADING.
 *   The Setun-70 CALL/RET pair is the inner interpreter.
 *   A colon definition is a sequence of:
 *       CALL lo hi   CALL lo hi  ...  RET
 *   where lo+hi*243 is the target CFA.  Primitives are native Setun-70
 *   instruction sequences ending in RET.
 *
 * All jump/call addresses are 2 trytes (lo = addr%243, hi = addr/243).
 * This covers the full 2187-tryte address space (27 pages x 81 trytes).
 *
 * Memory map:
 *   0          HALT sentinel (catch-all return)
 *   1..199     kernel primitive bodies  (dict header + body interleaved)
 *   200..299   outer interpreter code
 *   300..399   compiler word bodies  (IF, THEN, ELSE, BEGIN, etc.)
 *   400..499   system variables + buffers
 *   500..2186  user HERE space  (grows upward)
 *
 * System variables  (fixed C-side; synced via host calls):
 *   These are kept as C integers in dssp_t and NOT stored as trytes —
 *   that avoids the tryte-range overflow issue entirely.
 *   The VM words "state @", "here", etc. use host calls to read them.
 *
 * Dictionary header layout (written at HERE, grows upward):
 *   [link_lo][link_hi][flags][namelen][name bytes...][body begins here = CFA]
 *
 *   link_lo + link_hi*243  =  address of previous header (0 = chain end)
 *   flags   bit 0 = IMMEDIATE
 *   namelen = byte count of name
 *   CFA     = address of first instruction of word body
 *
 * Host-call opcodes  (auxiliary slots 35..53, intercepted before VM sees them):
 *   35  HC_WORD     scan next blank-delimited token into WORDBUF
 *   36  HC_FIND     look up WORDBUF in dict; push CFA or 0
 *   37  HC_NUMBER   parse WORDBUF as number; push value + ok_flag
 *   38  HC_DOT      pop and print as decimal with trailing space
 *   39  HC_DOTTERN  pop and print in balanced ternary
 *   40  HC_DOTS     print entire data stack
 *   41  HC_EXECUTE  pop CFA; push return addr; jump to CFA
 *   42  HC_COMPILE  pop CFA; if immediate execute, else emit CALL lo hi at HERE
 *   43  HC_TICK     scan next word, push its CFA
 *   44  HC_STATE_R  push STATE value onto DS
 *   45  HC_STATE_W  pop value and store into STATE
 *   46  HC_HERE_R   push HERE value onto DS
 *   47  HC_HERE_W   pop value and store into HERE
 *   48  HC_IMMPATCH pop (hole_addr, target); patch 2-tryte hole with target
 */

#define ADDR_WORDBUF     400
#define ADDR_TIB         420   /* 60-tryte text input buffer */

#define DICT_START       500   /* initial HERE — dictionary grows up from here */
#define FLAG_IMMEDIATE     1

#define S70_HC_WORD       35
#define S70_HC_FIND       36
#define S70_HC_NUMBER     37
#define S70_HC_DOT        38
#define S70_HC_DOTTERN    39
#define S70_HC_DOTS       40
#define S70_HC_EXECUTE    41
#define S70_HC_COMPILE    42
#define S70_HC_TICK       43
#define S70_HC_STATE_R    44
#define S70_HC_STATE_W    45
#define S70_HC_HERE_R     46
#define S70_HC_HERE_W     47
#define S70_HC_IMMPATCH   48
#define S70_HC_COMMA      49   /* DS: val -> ; mem[HERE]=val, HERE++ */
#define S70_HC_ALLOT      50   /* DS: n -> ; HERE += n */
#define S70_HC_MEMW2      51   /* DS: val lo hi -> ; mem[lo+hi*243]=val */
#define S70_HC_MEMR2      52   /* DS: lo hi -> val */
#define S70_HC_MAX        53

#define MAX_PRIMS 80

typedef struct {
    const char *name;
    int         cfa;
    int         immediate;
} prim_t;

typedef struct {
    setun70_t  vm;

    /* C-side system state — no tryte overflow possible */
    int        here;       /* next free address */
    int        latest;     /* address of most recent dict header */
    int        state;      /* 0 = interpret, 1 = compile */
    int        base;       /* number base */

    /* Input buffer */
    char       tib[80];
    int        tiblen;
    int        toin;       /* parse position */

    /* Word scan buffer */
    char       wordbuf[64];
    int        wordlen;

    /* Primitive registry (for cross-referencing during bootstrap) */
    prim_t     prims[MAX_PRIMS];
    int        nprim;

    /* Entry point of the outer interpreter loop */
    int        outer_addr;
} dssp_t;

/* Initialise DSSP: load kernel into VM, build dictionary. */
void dssp_init(dssp_t *d);

/* Evaluate one line of text.  Returns 0 on ok, -1 on error. */
int  dssp_eval(dssp_t *d, const char *line);

/* Run interactive REPL. */
void dssp_repl(dssp_t *d);

/* Search dictionary by name.  Returns CFA or -1.  Sets *imm if found. */
int  dssp_find(const dssp_t *d, const char *name, int *imm);

/* Bootstrap helpers used only during dssp_init. */
void dssp_emit(dssp_t *d, int val);
void dssp_emit2(dssp_t *d, int addr);    /* emit 2-tryte address */
void dssp_patch2(dssp_t *d, int at, int addr);  /* patch 2-tryte addr at 'at' */

int  dssp_read_sysvar(const dssp_t *d, int addr);
void dssp_write_sysvar(dssp_t *d, int addr, int val);

#endif
