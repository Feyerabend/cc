# Makefile for RISC-V VM with Examples
# Builds VM, assembler wrapper, and example programs

CC = gcc
CFLAGS = -Wall -Wextra -O2 -D_POSIX_C_SOURCE=200112L
LDFLAGS = -lm -lpthread
PYTHON = python3

# Main targets
TARGETS = riscv_vm vm_with_ivt

# VM object files
VM_OBJS = main.o riscv_vm.o
IVT_OBJS = vm_with_ivt.o riscv_vm.o riscv_interrupt.o

# Assembler
ASM = ./asm.py

# Example programs
EXAMPLES_DIR = examples
EXAMPLES_ASM = $(wildcard $(EXAMPLES_DIR)/*.asm)
EXAMPLES_BIN = $(EXAMPLES_ASM:.asm=.bin)

.PHONY: all clean examples run-examples help

all: $(TARGETS) examples

help:
	@echo "RISC-V VM Build System"
	@echo ""
	@echo "Targets:"
	@echo "  make              - Build VM and all examples"
	@echo "  make vm           - Build both VM versions"
	@echo "  make examples     - Build all example programs"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make run-examples - Run all examples with basic VM"
	@echo "  make test-ivt     - Run interrupt test with IVT VM"
	@echo ""
	@echo "Individual VMs:"
	@echo "  make riscv_vm     - Build basic VM"
	@echo "  make vm_with_ivt  - Build VM with interrupt support"
	@echo ""
	@echo "Example programs:"
	@echo "  $(EXAMPLES_BIN)"
	@echo ""
	@echo "Run individual examples:"
	@echo "  ./riscv_vm examples/hello.bin"
	@echo "  ./riscv_vm examples/factorial.bin"
	@echo "  ./vm_with_ivt examples/interrupt_test.bin"

# ============================================================================
# VM Targets
# ============================================================================

vm: $(TARGETS)

riscv_vm: $(VM_OBJS)
	$(CC) $(VM_OBJS) -o riscv_vm $(LDFLAGS)
	@echo "✓ Built basic VM: riscv_vm"

vm_with_ivt: $(IVT_OBJS)
	$(CC) $(IVT_OBJS) -o vm_with_ivt $(LDFLAGS)
	@echo "✓ Built VM with IVT: vm_with_ivt"

main.o: main.c riscv_vm.h
	$(CC) $(CFLAGS) -c main.c

riscv_vm.o: riscv_vm.c riscv_vm.h
	$(CC) $(CFLAGS) -c riscv_vm.c

riscv_interrupt.o: riscv_interrupt.c riscv_interrupt.h riscv_vm.h
	$(CC) $(CFLAGS) -c riscv_interrupt.c

vm_with_ivt.o: vm_with_ivt.c riscv_vm.h riscv_interrupt.h
	$(CC) $(CFLAGS) -c vm_with_ivt.c

# ============================================================================
# Assembler Setup
# ============================================================================

$(ASM):
	@if [ ! -f asm.py ]; then \
		echo "Error: asm.py not found. Please place the assembler in the current directory."; \
		exit 1; \
	fi
	@chmod +x asm.py

# ============================================================================
# Example Programs
# ============================================================================

examples: $(EXAMPLES_BIN)
	@echo "✓ Built $(words $(EXAMPLES_BIN)) example programs"

$(EXAMPLES_DIR)/%.bin: $(EXAMPLES_DIR)/%.asm $(ASM)
	@echo "Assembling $<..."
	@$(PYTHON) $(ASM) $< $@

# ============================================================================
# Run Targets
# ============================================================================

run-examples: riscv_vm examples
	@echo ""
	@echo "========================================"
	@echo "Running: Hello World"
	@echo "========================================"
	@./riscv_vm examples/hello.bin
	@echo ""
	@echo "========================================"
	@echo "Running: Counter (1-20)"
	@echo "========================================"
	@./riscv_vm examples/counter.bin
	@echo ""
	@echo "========================================"
	@echo "Running: Fibonacci"
	@echo "========================================"
	@./riscv_vm examples/fibonacci.bin
	@echo ""
	@echo "========================================"
	@echo "Running: Factorial (5!)"
	@echo "========================================"
	@./riscv_vm examples/factorial.bin
	@echo ""
	@echo "========================================"
	@echo "Running: Array Sum"
	@echo "========================================"
	@./riscv_vm examples/array_sum.bin
	@echo ""
	@echo "========================================"
	@echo "Running: Multiply/Divide Test"
	@echo "========================================"
	@./riscv_vm examples/multest.bin

test-ivt: vm_with_ivt examples
	@echo ""
	@echo "========================================"
	@echo "Running Interrupt Test with IVT"
	@echo "========================================"
	@echo "Watch for timer and watchpoint interrupts!"
	@echo "PID will be shown - you can send SIGUSR1 to trigger breakpoint"
	@echo ""
	@./vm_with_ivt examples/interrupt_test.bin

test-ivt-queued: vm_with_ivt examples
	@echo ""
	@echo "========================================"
	@echo "Running Interrupt Test (Queued Mode)"
	@echo "========================================"
	@./vm_with_ivt -q examples/interrupt_test.bin

# Individual example runs
run-hello: riscv_vm examples
	@./riscv_vm examples/hello.bin

run-counter: riscv_vm examples
	@./riscv_vm examples/counter.bin

run-fibonacci: riscv_vm examples
	@./riscv_vm examples/fibonacci.bin

run-factorial: riscv_vm examples
	@./riscv_vm examples/factorial.bin

run-array: riscv_vm examples
	@./riscv_vm examples/array_sum.bin

run-multest: riscv_vm examples
	@./riscv_vm examples/multest.bin

# ============================================================================
# Debugging and Testing
# ============================================================================

debug-hello: riscv_vm examples
	@echo "Running hello.bin with debug and trace"
	@./riscv_vm -d -t examples/hello.bin

debug-factorial: riscv_vm examples
	@echo "Running factorial.bin with debug and registers"
	@./riscv_vm -d -r examples/factorial.bin

# ============================================================================
# Clean
# ============================================================================

clean:
	rm -f $(VM_OBJS) $(IVT_OBJS) $(TARGETS)
	rm -f $(EXAMPLES_BIN)
	rm -f *.o
	@echo "✓ Cleaned build artifacts"

# ============================================================================
# Quick Reference
# ============================================================================

quickref:
	@echo "Quick Reference for RISC-V VM"
	@echo ""
	@echo "Basic VM Usage:"
	@echo "  ./riscv_vm <program.bin>           Run program"
	@echo "  ./riscv_vm -d <program.bin>        Debug mode"
	@echo "  ./riscv_vm -t <program.bin>        Trace execution"
	@echo "  ./riscv_vm -r <program.bin>        Show registers"
	@echo "  ./riscv_vm -m 0:100 <program.bin>  Dump memory"
	@echo ""
	@echo "IVT VM Usage:"
	@echo "  ./vm_with_ivt <program.bin>        Run with interrupts"
	@echo "  ./vm_with_ivt -q <program.bin>     Queued dispatch mode"
	@echo "  ./vm_with_ivt -b ADDR <prog.bin>   Set breakpoint"
	@echo "  ./vm_with_ivt -w ADDR <prog.bin>   Set watchpoint"
	@echo "  kill -USR1 <PID>                   Trigger interrupt"
	@echo ""
	@echo "Assembler Usage:"
	@echo "  python3 asm.py input.asm output.bin"
	@echo "  python3 asm.py -v input.asm output.bin  (verbose)"
	@echo "  python3 asm.py -d input.asm output.bin  (dump hex)"
