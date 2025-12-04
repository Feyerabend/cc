#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "vm2.h"

// Fibonacci
int code[] = {
	SET, 18, // print 20, but starting with 2 (3) constants
	STORE, 0,

	SETZ,
	PRINT,

	SET, 1,
	DUP,
	PRINT,

	SET, 1,
	DUP,
	PRINT,

// 14:
	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	LOAD, 0,
	DEC,
	DUP,
	STORE, 0,

	JPNZ, 14,
	HALT
};

void program() {
	VM* vm = newVM(code, 0, 30);
	if (vm != NULL) {
		clock_t t;
		t = clock();

		run(vm);

		t = clock() - t;
		double duration = ((double) t) / CLOCKS_PER_SEC;
		printf("%f seconds\n", duration);
		freeVM(vm);
	}
}

int main() {
	program();
	return 0;
}
