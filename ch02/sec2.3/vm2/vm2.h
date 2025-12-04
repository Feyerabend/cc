#include <stdio.h>
#include <stdlib.h>

#define STACK_SIZE 200
#define TRUE 1
#define FALSE 0

typedef struct {
	int* vars;
	int* code;
	int* stack;
	int pc;
	int sp;
} VM;

enum {
	ADD,
	DEC,
	EQ,
	EQZ,
	HALT,
	INC,
	JP,
	JPNZ,
	JPZ,
	LOAD,
	LT,
	MUL,
	NOP,
	PRINT,
	SET,
	SETZ,
	STORE,
	SUB,

// "forthified"
	DROP,
	DUP,
	OVER,
	ROT,
	SWAP,
	TWODUP
};

VM* newVM(int* code, int pc, int datasize);
void freeVM(VM* vm);
void run(VM* vm);
