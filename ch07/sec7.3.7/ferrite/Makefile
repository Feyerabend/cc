# Ferrite Compiler Makefile
FERRITE = python3 ferrite.py
CC = gcc
CFLAGS = -Wall -O2

# Find all .fe files in examples/
SOURCES = $(wildcard examples/*.fe)
C_FILES = $(SOURCES:.fe=.c)
EXECUTABLES = $(SOURCES:.fe=)

# Check if KEEP_C is set (use: make KEEP_C=1 or make keep-c)
ifndef KEEP_C
  KEEP_C = 0
endif

# Tell Make not to delete intermediate C files
.SECONDARY: $(C_FILES)

.PHONY: all clean run-all examples keep-c clean-exe clean-all help

# Default target: compile all examples
all: examples

# Compile with C files kept
keep-c: all

# Compile all .fe files to C and then to executables
examples: $(EXECUTABLES)
	@echo "✓ All examples compiled successfully"
	@echo "✓ C files kept in examples/ (use 'make clean-c' to remove them)"

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

run-factorial: examples/factorial
	@echo "=== Running factorial ==="
	@./examples/factorial

run-fibonacci: examples/fibonacci
	@echo "=== Running fibonacci ==="
	@./examples/fibonacci

run-gcd: examples/gcd
	@echo "=== Running gcd ==="
	@./examples/gcd

run-countdown: examples/countdown
	@echo "=== Running countdown ==="
	@./examples/countdown

# Clean only executables (keep C files)
clean-exe:
	@echo "Cleaning executables..."
	@rm -f $(EXECUTABLES)
	@echo "✓ Executables removed (C files kept)"

# Clean only C files (keep executables)
clean-c:
	@echo "Cleaning C files..."
	@rm -f $(C_FILES)
	@echo "✓ C files removed (executables kept)"

# Clean generated files (default: removes both)
clean: clean-all

# Clean everything
clean-all:
	@echo "Cleaning all generated files..."
	@rm -f $(C_FILES) $(EXECUTABLES)
	@echo "✓ Clean complete"

# Help target
help:
	@echo "Ferrite Compiler - Available targets:"
	@echo ""
	@echo "Compilation:"
	@echo "  make all         - Compile all examples (C files are kept)"
	@echo "  make keep-c      - Same as 'make all'"
	@echo "  make examples    - Same as 'make all'"
	@echo ""
	@echo "Running:"
	@echo "  make run-all     - Compile and run all examples"
	@echo "  make run-hello   - Run hello example"
	@echo "  make run-struct  - Run struct example"
	@echo "  make run-borrow  - Run borrow example"
	@echo "  make run-advanced - Run advanced example"
	@echo "  make run-factorial - Run factorial example"
	@echo "  make run-fibonacci - Run fibonacci example"
	@echo "  make run-gcd     - Run gcd example"
	@echo "  make run-countdown - Run countdown example"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean       - Remove all generated files"
	@echo "  make clean-all   - Remove all generated files"
	@echo "  make clean-exe   - Remove executables only (keep C files)"
	@echo "  make clean-c     - Remove C files only (keep executables)"
	@echo ""
	@echo "Note: C source files are now kept by default for inspection"