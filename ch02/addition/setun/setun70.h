#ifndef SETUN70_H
#define SETUN70_H

#include "trit.h"

/*
 * Setun-70 (1970) architecture
 *
 * The Setun-70 is a two-stack machine oriented towards structured
 * programming (Dijkstra's method).  Its smallest addressable unit is
 * the 6-trit tryte (range -364..+364 in balanced ternary).
 *
 * Memory:
 *   9 pages of 81 trytes each = 729 trytes total.
 *   Only 3 pages are "open" at once, selected by three page registers (PR).
 *   A 1-3 tryte "addressing word" specifies the operand address.
 *
 * Stacks:
 *   DS  - data stack   (operands; grows upward)
 *   RS  - return stack (procedure return addresses)
 *
 * Processor register:
 *   T   - top-of-stack cache / working register (1 tryte)
 *
 * Operations (81 total):
 *   27 basic     (arithmetic, stack manipulation, memory access)
 *   27 auxiliary (I/O, page switching, system calls)
 *   27 user-programmable (patched at run-time into the dispatch table)
 *
 * Instruction format:
 *   An "operating tryte" encodes the operation (value -364..+364, though
 *   only 81 values are used as 4-trit opcode: range -40..+40).
 *   An optional "addressing word" of 1-3 trytes follows for memory ops.
 *
 * The paper confirms these structural points but does not give a full
 * opcode table; we define a representative set consistent with a
 * Forth-like two-stack architecture and the described operations.
 */

#define S70_PAGE_SIZE      81
#define S70_NUM_PAGES      27      /* expanded: 27 pages x 81 = 2187 trytes */
#define S70_OPEN_PAGES      3
#define S70_MEM_TRYTES     (S70_PAGE_SIZE * S70_NUM_PAGES)  /* 2187 */
#define S70_STACK_DEPTH    64

typedef struct {
    tryte_t  mem[S70_MEM_TRYTES];

    /* Page registers: which 3 of the 9 pages are currently open. */
    int      page_reg[S70_OPEN_PAGES];

    /* Data stack and return stack. */
    tryte_t  ds[S70_STACK_DEPTH];
    int      ds_top;   /* index of next free slot */

    tryte_t  rs[S70_STACK_DEPTH];
    int      rs_top;

    /* Program counter: tryte address in the flat memory space. */
    int      pc;

    int      halted;
    int      error;

    /* User-programmable dispatch table (27 entries, indices 54..80). */
    int      user_op_target[27];  /* jump targets for user ops */
} setun70_t;

/*
 * Setun-70 opcodes (operating tryte value).
 * We encode them as small integers; the actual tryte value is this integer
 * converted via int_to_tryte().  The 81 slots are [-40..+40]; we assign:
 *   0..26  basic ops
 *   27..53 auxiliary ops
 *   54..80 user-programmable ops  (stored as 0-based index into user_op_target)
 * Note: the paper says 27+27+27; we use 0-based integers and convert to
 * balanced ternary internally only when encoding/decoding trytes.
 */
typedef enum {
    /* Basic operations (0..26) */
    S70_NOP      =  0,
    S70_PUSH     =  1,   /* push literal (next tryte in stream) onto DS */
    S70_POP      =  2,   /* discard top of DS */
    S70_DUP      =  3,   /* duplicate top of DS */
    S70_SWAP     =  4,   /* swap top two DS items */
    S70_OVER     =  5,   /* copy second DS item to top */
    S70_ADD      =  6,   /* DS: a b -> a+b */
    S70_SUB      =  7,   /* DS: a b -> a-b */
    S70_MUL      =  8,   /* DS: a b -> a*b */
    S70_DIV      =  9,   /* DS: a b -> a/b */
    S70_NEG      = 10,   /* DS: a -> -a */
    S70_ABS      = 11,   /* DS: a -> |a| */
    S70_SGN      = 12,   /* DS: a -> sign(a) in {-1,0,+1} */
    S70_EQ       = 13,   /* DS: a b -> (a==b ? +1 : 0) */
    S70_LT       = 14,   /* DS: a b -> (a<b  ? +1 : 0) */
    S70_AND      = 15,   /* DS: a b -> min(a,b)  (ternary AND) */
    S70_OR       = 16,   /* DS: a b -> max(a,b)  (ternary OR) */
    S70_NOT      = 17,   /* DS: a   -> -a         (ternary NOT) */
    S70_LOAD     = 18,   /* DS: addr -> mem[addr] */
    S70_STORE    = 19,   /* DS: val addr -> ; mem[addr]:=val */
    S70_CALL     = 20,   /* push PC+1 onto RS; jump to addr from next tryte */
    S70_RET      = 21,   /* pop RS into PC */
    S70_JUMP     = 22,   /* unconditional jump; addr from next tryte */
    S70_JPOS     = 23,   /* DS: cond; jump if cond > 0 */
    S70_JZERO    = 24,   /* DS: cond; jump if cond == 0 */
    S70_JNEG     = 25,   /* DS: cond; jump if cond < 0 */
    S70_HALT     = 26,

    /* Auxiliary operations (27..53) */
    S70_EMIT     = 27,   /* DS: char -> ; output character */
    S70_KEY      = 28,   /* DS: -> char; read character */
    S70_PAGESEL  = 29,   /* DS: slot page -> ; select page into open slot */
    S70_DEPTH    = 30,   /* DS: -> n; push current DS depth */
    S70_RDEPTH   = 31,   /* DS: -> n; push current RS depth */
    S70_RPUSH    = 32,   /* DS: n -> ; RS: -> n; move DS top to RS */
    S70_RPOP     = 33,   /* RS: n -> ; DS: -> n; move RS top to DS */
    S70_RPEEK    = 34,   /* DS: -> n; copy RS top to DS without popping */

    /* Remaining auxiliary slots are reserved (35..53). */

    /* User-programmable (54..80) — resolved via user_op_target table. */
    S70_USER_BASE = 54
} s70_opcode_t;

/* Initialise a Setun-70 machine. */
void setun70_init(setun70_t *cpu);

/* Write a tryte to a flat memory address. */
void setun70_mem_write(setun70_t *cpu, int addr, const tryte_t *tr);

/* Read a tryte from a flat memory address. */
tryte_t setun70_mem_read(const setun70_t *cpu, int addr);

/* Push a tryte onto the data stack. */
void setun70_ds_push(setun70_t *cpu, const tryte_t *val);

/* Pop a tryte from the data stack. */
tryte_t setun70_ds_pop(setun70_t *cpu);

/* Peek at the data stack top without popping. */
tryte_t setun70_ds_peek(const setun70_t *cpu);

/* Push a tryte onto the return stack. */
void setun70_rs_push(setun70_t *cpu, const tryte_t *val);

/* Pop a tryte from the return stack. */
tryte_t setun70_rs_pop(setun70_t *cpu);

/* Execute one instruction; return 0 on normal step, -1 on halt/error. */
int setun70_step(setun70_t *cpu);

/* Run until halted or error. */
void setun70_run(setun70_t *cpu);

/* Print current machine state. */
void setun70_dump(const setun70_t *cpu);

/* Load a program (array of tryte integer values) starting at flat address. */
void setun70_load_program(setun70_t *cpu, int start_addr,
                          const int *values, int count);

#endif
