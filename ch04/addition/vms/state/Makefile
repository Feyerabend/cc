# Makefile for compiling vm_sm.c, new_vm.c, and fib_sm.c
CC = gcc
CFLAGS = -std=c99 -O2 -Wall -Wextra
TARGETS = vm_demo new_vm_demo fib_demo

# Default target: build all executables
all: $(SAR)

# Build vm_demo from vm_sm.c
vm_demo: vm_sm.c
	$(CC) $(CFLAGS) -o vm_demo vm_sm.c

# Build new_vm_demo from new_vm.c
new_vm_demo: new_vm.c
	$(CC) $(CFLAGS) -o new_vm_demo new_vm.c

# Build fib_demo from fib_sm.c
fib_demo: fib_sm.c
	$(CC) $(CFLAGS) -o fib_demo fib_sm.c

# Clean up generated files
clean:
	rm -f $(TARGETS)

# Run all demos
run: all
	./vm_demo
	./new_vm_demo
	./fib_demo

# Phony targets
.PHONY: all clean run
