# Ferrite Compiler Makefile

FERRITE = python3 ferrite.py
CC = gcc
CFLAGS = -Wall -O2

# Find all .fe files in examples/
SOURCES = $(wildcard examples/*.fe)
C_FILES = $(SOURCES:.fe=.c)
EXECUTABLES = $(SOURCES:.fe=)

.PHONY: all clean run-all examples

# Default target: compile all examples
all: examples

# Compile all .fe files to C and then to executables
examples: $(EXECUTABLES)
	@echo "✓ All examples compiled successfully"

# Pattern rule: .fe -> .c
%.c: %.fe ferrite.py
	@echo "Compiling $< to C..."
	@$(FERRITE) $< -o $@

# Pattern rule: .c -> executable
%: %.c
	@echo "Compiling $< to executable..."
	@$(CC) $(CFLAGS) -o $@ $<

# Run all examples
run-all: $(EXECUTABLES)
	@for exe in $(EXECUTABLES); do \
		echo ""; \
		echo "=== Running $$exe ==="; \
		./$$exe; \
	done

# Individual run targets
run-hello: examples/hello
	@echo "=== Running hello ==="
	@./examples/hello

run-struct: examples/struct
	@echo "=== Running struct ==="
	@./examples/struct

run-borrow: examples/borrow
	@echo "=== Running borrow ==="
	@./examples/borrow

run-advanced: examples/advanced
	@echo "=== Running advanced ==="
	@./examples/advanced

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -f $(C_FILES) $(EXECUTABLES)
	@echo "✓ Clean complete"

# Help target
help:
	@echo "Ferrite Compiler - Available targets:"
	@echo "  make all         - Compile all examples"
	@echo "  make examples    - Same as 'make all'"
	@echo "  make run-all     - Compile and run all examples"
	@echo "  make run-hello   - Run hello example"
	@echo "  make run-struct  - Run struct example"
	@echo "  make run-borrow  - Run borrow example"
	@echo "  make run-advanced - Run advanced example"
	@echo "  make clean       - Remove all generated files"
