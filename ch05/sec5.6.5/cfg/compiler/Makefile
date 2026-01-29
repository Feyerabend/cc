# Makefile for Tiny C Compiler

CC = gcc
CFLAGS = -Wall -O2
TCC = ./tcc

# Compiler target
tcc: tiny_c_compiler.c
	$(CC) $(CFLAGS) -o tcc tiny_c_compiler.c

# Test targets
test1: tcc test1_factorial.c
	$(TCC) < test1_factorial.c > test1_output.c
	$(CC) -o test1_prog test1_output.c
	@echo "Running factorial(5)..."
	@./test1_prog; echo "Exit code: $$?"

test2: tcc test2_fibonacci.c
	$(TCC) < test2_fibonacci.c > test2_output.c
	$(CC) -o test2_prog test2_output.c
	@echo "Running fibonacci(10)..."
	@./test2_prog; echo "Exit code: $$?"

test3: tcc test3_complex.c
	$(TCC) < test3_complex.c > test3_output.c
	$(CC) -o test3_prog test3_output.c
	@echo "Running complex nested control flow..."
	@./test3_prog; echo "Exit code: $$?"

test4: tcc test4_demo.c
	$(TCC) < test4_demo.c > test4_output.c
	$(CC) -o test4_prog test4_output.c
	@echo "Running optimization demo..."
	@./test4_prog; echo "Exit code: $$?"

# Run all tests
all-tests: test1 test2 test3 test4
	@echo ""
	@echo "All tests passed!"
	@echo "  - test1: factorial(5) = 120"
	@echo "  - test2: fibonacci(10) = 55"
	@echo "  - test3: complex = 80"
	@echo "  - test4: demo = 185"

# Clean generated files
clean:
	rm -f tcc test*_output.c test*_prog

# Phony targets
.PHONY: test1 test2 test3 test4 all-tests clean
