CC     ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -O2

.PHONY: all run asan clean

all: calc

calc: calc.c
	$(CC) $(CFLAGS) -o calc calc.c

run: calc
	./calc

# Build with sanitizers to demonstrate the manual frees are leak-free.
asan: calc.c
	$(CC) -std=c11 -fsanitize=address,undefined -g -o calc_asan calc.c
	./calc_asan

clean:
	rm -f calc calc_asan
	rm -rf calc.dSYM calc_asan.dSYM
