#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "vm2.h"

int fibonacci_recursive(int n) {
	if (n == 0)
		return 0;
	if (n < 3)
		return 1;
	else
		return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2);
}

int fibonacci_iterative(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;

    int n1 = 0, n2 = 1, n3;

    for (int i = 2; i <= n; i++) {
        n3 = n1 + n2;
        n1 = n2;
        n2 = n3;
    }
    return n3;
}

void native() {
	clock_t t;
    printf("----- native -----\n");
	t = clock();
	printf(" %d\n", fibonacci_recursive(20));
	t = clock() - t;
	double time_taken = ((double)t)/CLOCKS_PER_SEC;
  	printf(" %f seconds\n", time_taken);
    printf("\n\n");
};



// compressed
int compressed_program[] = {
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

void compressed() {
	VM* vm = newVM(compressed_program, 0, 5);
	if (vm != NULL) {
        printf("--- compressed ---\n");
		run(vm);
        printf("\n\n");
		freeVM(vm);
	}
};



// expanded (unrolled)
// 0
// 1
// 1
// 2
// 3
// 5
// 8
// 13
// 21
// 34
// 55
// 89
// 144
// 233
// 377
// 610
// 987
// 1597
// 2584
// 4181
// 6765

int expanded_program[] = {
	SET, 0,
	PRINT,

	SET, 1,
	DUP,
	PRINT,

	SET, 1,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	TWODUP,
	ADD,
	ROT,
	DROP,
	DUP,
	PRINT,

	HALT
};

void expanded() {
	VM* vm = newVM(expanded_program, 0, 5);
	if (vm != NULL) {
        printf("---- expanded ----\n");
		run(vm);
        printf("\n\n");
		freeVM(vm);
	}
}

// test all
int main() {
	native();
	compressed();
	expanded();
	return 0;
}

/* EOF */
