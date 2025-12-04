#include <stdio.h>
#include <stdlib.h>

#define STACK_SIZE 1024
#define TRUE 1
#define FALSE 0

typedef struct {
    int* code;
    int* stack;
    int pc;
    int sp;
    int fp;
} VM;

enum {      // arity
    ADD,    // 0
    AND,    // 0
    CALL,   // 1
    DEC,    // 0
    DROP,   // 0
    DUP,    // 0
    EQ,     // 0
    EQZ,    // 0
    HALT,   // 0
    INC,    // 0
    JP,     // 1
    JPNZ,   // 1
    JPZ,    // 1
    LD,     // 1
    LOAD,   // 1
    LSH,    // 0
    LT,     // 0
    MOD,    // 0
    MUL,    // 0
    NOP,    // 0
    OR,     // 0
    PRINT,  // 0
    PRNT,   // 0
    RET,    // 0
    RSH,    // 0
    SET,    // 1
    SETZ,   // 0
    ST,     // 1
    STORE,  // 1
    SUB     // 0
};

VM* newVM(int* code, int pc);
void freeVM(VM* vm);
void run(VM* vm);
