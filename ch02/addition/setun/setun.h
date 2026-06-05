#ifndef SETUN_H
#define SETUN_H

#include "trit.h"

/*
 * Setun (1958) architecture
 *
 * Memory: 162 cells of 9 trits each, organised as 3 pages of 54 cells.
 *         Addresses are 5 trits (range -121..+121 in balanced ternary,
 *         but only 0..161 are used as unsigned indices here).
 *         A 9-trit cell holds either:
 *           - one instruction word, or
 *           - the upper or lower half of an 18-trit data word.
 *
 * Registers:
 *   S   - 18-trit accumulator / summariser
 *   R   - 18-trit multiplier register
 *   F   - 9-trit index register (address modifier)
 *   P   - 9-trit program counter (cell address)
 *   omega - 1-trit result-sign pointer (used for conditional branches)
 *
 * Instruction format (9 trits):
 *   trits 8..6  : opcode  (3 trits => 27 possible opcodes, 24 used)
 *   trits 5..0  : address (6 trits => word address within 3-page window)
 *
 * The paper gives 24 single-address commands; we define them below.
 * Floating-point is handled by interpretive system (IP-2 etc.) layered on
 * top; the bare machine only does fixed-point 18-trit arithmetic.
 */

#define SETUN_MEM_CELLS   162
#define SETUN_PAGE_SIZE    54
#define SETUN_NUM_PAGES     3

typedef struct {
    word9_t  mem[SETUN_MEM_CELLS];

    word18_t S;       /* accumulator */
    word18_t R;       /* multiplier */
    word9_t  F;       /* index register */
    word9_t  P;       /* program counter */
    trit_t   omega;   /* sign flag */

    int      halted;
    int      error;
} setun_t;

/*
 * Setun opcode encoding: 3-trit field (trits 8..6 of instruction word).
 * Encoded as balanced ternary integer -13..+13 (only 24 values used).
 * We map them to a C enum for clarity.
 */
typedef enum {
    OP_LOAD     =  0,   /* S := mem[addr]        (load 18-trit word, upper half) */
    OP_STORE    =  1,   /* mem[addr] := S upper  */
    OP_ADD      =  2,   /* S := S + mem[addr]    */
    OP_SUB      =  3,   /* S := S - mem[addr]    */
    OP_MUL      =  4,   /* R := S * mem[addr]; S := upper product */
    OP_DIV      =  5,   /* S := S / mem[addr]; R := remainder     */
    OP_NEG      =  6,   /* S := -S               (trit-inversion) */
    OP_ABS      =  7,   /* S := |S|              */
    OP_LOADR    =  8,   /* S := R                */
    OP_STORER   =  9,   /* R := S                */
    OP_LOADF    = 10,   /* F := mem[addr] lower9 */
    OP_STOREF   = 11,   /* mem[addr] lower9 := F */
    OP_ADDF     = 12,   /* F := F + mem[addr] lower9 */
    OP_ADDPROD  = 13,   /* S := S + (R * mem[addr])  (optimises polynomial eval) */
    OP_JUMP     = 14,   /* P := addr             (unconditional jump) */
    OP_JPOS     = 15,   /* if omega == +1: P := addr */
    OP_JZERO    = 16,   /* if omega ==  0: P := addr */
    OP_JNEG     = 17,   /* if omega == -1: P := addr */
    OP_JNPOS    = 18,   /* if omega != +1: P := addr */
    OP_JNZERO   = 19,   /* if omega !=  0: P := addr */
    OP_JNNEG    = 20,   /* if omega != -1: P := addr */
    OP_SETOMEGA = 21,   /* omega := sign(S)      */
    OP_NOP      = 22,   /* no operation          */
    OP_HALT     = 23    /* stop execution        */
} setun_opcode_t;

/* Initialise a Setun machine (zero memory and registers). */
void setun_init(setun_t *cpu);

/* Write a 9-trit word to a memory cell (0-based flat address). */
void setun_mem_write(setun_t *cpu, int addr, const word9_t *w);

/* Read a 9-trit word from a memory cell. */
word9_t setun_mem_read(const setun_t *cpu, int addr);

/*
 * Write an 18-trit data word to two consecutive cells (upper half at addr,
 * lower half at addr+1), matching the Setun convention.
 */
void setun_mem_write18(setun_t *cpu, int addr, const word18_t *w);

/* Read an 18-trit data word from two consecutive cells. */
word18_t setun_mem_read18(const setun_t *cpu, int addr);

/*
 * Assemble one 9-trit instruction from an opcode integer (-13..+13 range
 * maps to the 3-trit opcode field) and a 6-trit address field value.
 */
word9_t setun_assemble(int opcode_val, int addr_val);

/*
 * Decode a 9-trit instruction word into its opcode integer and address.
 */
void setun_decode(const word9_t *instr, int *opcode_val, int *addr_val);

/* Execute one instruction cycle; return 0 on normal step, -1 on halt/error. */
int setun_step(setun_t *cpu);

/* Run until halted or error. */
void setun_run(setun_t *cpu);

/* Print current register state. */
void setun_dump(const setun_t *cpu);

#endif
