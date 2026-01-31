# Makefile for TAC Generator Examples
# =====================================
#
# This Makefile provides convenient targets for building and running
# the Three-Address Code generator examples.

# Compiler settings
CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2
PYTHON = python3

# Targets
C_PROGRAM = tac_generator
C_SOURCE = tac_generator.c

# Default target
.PHONY: all
all: help

# Help target
.PHONY: help
help:
	@echo "TAC Generator - Available Commands"
	@echo "==================================="
	@echo ""
	@echo "Build targets:"
	@echo "  make build-c        - Compile the C version"
	@echo "  make clean          - Remove compiled files"
	@echo ""
	@echo "Run targets:"
	@echo "  make run-c          - Run the C implementation"
	@echo "  make run-py         - Run the Python expression generator"
	@echo "  make run-interp     - Run the Python TAC interpreter"
	@echo ""
	@echo "Combined targets:"
	@echo "  make demo           - Run all demonstrations"
	@echo "  make all-python     - Run all Python examples"
	@echo ""

# Build the C program
.PHONY: build-c
build-c: $(C_PROGRAM)

$(C_PROGRAM): $(C_SOURCE)
	@echo "Compiling $(C_SOURCE)..."
	$(CC) $(CFLAGS) -o $(C_PROGRAM) $(C_SOURCE)
	@echo "Build successful!"

# Clean compiled files
.PHONY: clean
clean:
	@echo "Cleaning up..."
	rm -f $(C_PROGRAM)
	@echo "Clean complete!"

# Run the C implementation
.PHONY: run-c
run-c: build-c
	@echo ""
	@echo "Running C implementation..."
	@echo ""
	./$(C_PROGRAM)

# Run the Python expression generator
.PHONY: run-py
run-py:
	@echo ""
	@echo "Running Python expression generator..."
	@echo ""
	$(PYTHON) tac_generator.py

# Run the Python TAC interpreter
.PHONY: run-interp
run-interp:
	@echo ""
	@echo "Running Python TAC interpreter..."
	@echo ""
	$(PYTHON) tac_interpreter.py

# Run all Python examples
.PHONY: all-python
all-python: run-py run-interp

# Run all demonstrations
.PHONY: demo
demo: run-c all-python

# Check if programs exist
.PHONY: check
check:
	@echo "Checking for required files..."
	@test -f $(C_SOURCE) && echo "✓ $(C_SOURCE) found" || echo "✗ $(C_SOURCE) missing"
	@test -f tac_generator.py && echo "✓ tac_generator.py found" || echo "✗ tac_generator.py missing"
	@test -f tac_interpreter.py && echo "✓ tac_interpreter.py found" || echo "✗ tac_interpreter.py missing"
	@test -f README.md && echo "✓ README.md found" || echo "✗ README.md missing"
	@echo ""
	@which $(CC) > /dev/null && echo "✓ C compiler ($(CC)) found" || echo "✗ C compiler not found"
	@which $(PYTHON) > /dev/null && echo "✓ Python ($(PYTHON)) found" || echo "✗ Python not found"
