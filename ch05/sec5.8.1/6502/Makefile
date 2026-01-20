
# Makefile for 6502 Tail-Recursive Fibonacci

CC = gcc
CFLAGS = -Wall -O2 -I.
PYTHON = python3

# Targets
EMULATOR = run6502
ASM_FILE = fib_tail.asm
BIN_FILE = fib.bin

all: $(EMULATOR) $(BIN_FILE)

# Build the emulator
$(EMULATOR): main.c fake6502.c fake6502.h
	$(CC) $(CFLAGS) -o $(EMULATOR) main.c fake6502.c

# Assemble the 6502 code
$(BIN_FILE): $(ASM_FILE) asm.py
	$(PYTHON) asm.py $(ASM_FILE) $(BIN_FILE)

# Run the complete program
run: all
	./$(EMULATOR) $(BIN_FILE)

# Clean build artefacts
clean:
	rm -f $(EMULATOR) $(BIN_FILE) *.o

# Assemble with verbose output
debug: $(ASM_FILE) asm.py
	$(PYTHON) asm.py $(ASM_FILE) $(BIN_FILE) -v

# Show disassembly (hex dump)
dump: $(BIN_FILE)
	hexdump -C $(BIN_FILE)

.PHONY: all run clean debug dump
