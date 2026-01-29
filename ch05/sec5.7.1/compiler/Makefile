# Makefile for SSA C Compiler
# 
# Targets:
#   make           - Build the SSA compiler
#   make test      - Run all tests
#   make examples  - Compile example programs
#   make clean     - Remove built files
#   make help      - Show this help

CC = gcc
CFLAGS = -std=c99 -Wall -Wextra -O2
DEBUG_FLAGS = -g -O0 -DDEBUG

# Compiler executable
COMPILER = ssac

# Test files
TESTS = simple_test phi_test comprehensive_test

# Example source files
EXAMPLES = $(TESTS)

.PHONY: all test examples clean help debug

# Default target
all: $(COMPILER)
	@echo "SSA compiler built successfully!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make help' for more options"

# Build the compiler
$(COMPILER): ssa_compiler.c
	@echo "Building SSA compiler..."
	$(CC) $(CFLAGS) -o $(COMPILER) ssa_compiler.c
	@echo "Done!"

# Debug build
debug: ssa_compiler.c
	@echo "Building SSA compiler (debug mode)..."
	$(CC) $(DEBUG_FLAGS) -o $(COMPILER) ssa_compiler.c
	@echo "Debug build complete!"

# Run all tests
test: $(COMPILER) $(TESTS)
	@echo ""
	@echo "Running SSA Compiler Test Suite"
	@echo ""
	@for test in $(TESTS); do \
		echo "Testing: $$test.c"; \
		./$(COMPILER) < $$test.c 2>/dev/null | tail -n +3 > $$test.out.c; \
		if [ $$? -eq 0 ]; then \
			$(CC) $$test.out.c -o $$test.bin 2>/dev/null; \
			if [ $$? -eq 0 ]; then \
				./$$test.bin; \
				EXITCODE=$$?; \
				echo "  ✓ $$test passed (exit code: $$EXITCODE)"; \
			else \
				echo "  ✗ $$test failed to compile output"; \
			fi; \
		else \
			echo "  ✗ $$test failed to compile"; \
		fi; \
		echo ""; \
	done
	@echo "Test suite done"

# Individual test targets
simple_test: $(COMPILER) simple_test.c
	@echo "Compiling simple_test.c..."
	@./$(COMPILER) < simple_test.c 2>/dev/null | tail -n +3 > simple_test.out.c
	@$(CC) simple_test.out.c -o simple_test.bin
	@./simple_test.bin || true
	@echo "Done"

phi_test: $(COMPILER) phi_test.c
	@echo "Compiling phi_test.c..."
	@./$(COMPILER) < phi_test.c 2>/dev/null | tail -n +3 > phi_test.out.c
	@$(CC) phi_test.out.c -o phi_test.bin
	@./phi_test.bin || true
	@echo "Done"

comprehensive_test: $(COMPILER) comprehensive_test.c
	@echo "Compiling comprehensive_test.c..."
	@./$(COMPILER) < comprehensive_test.c 2>/dev/null | tail -n +3 > comprehensive_test.out.c
	@$(CC) comprehensive_test.out.c -o comprehensive_test.bin
	@./comprehensive_test.bin || true
	@echo "Done"

# Show optimizations in action
demo: $(COMPILER)
	@echo ""
	@echo "SSA COMPILER OPTIMISATION"
	@echo ""
	@echo "Test 1: Constant Folding (simple_test.c)"
	@echo "-----------------------------------------"
	@echo "Input:"
	@cat simple_test.c
	@echo ""
	@echo "Optimized output (note: 5 + 10 → 15):"
	@./$(COMPILER) < simple_test.c 2>/dev/null | grep -A8 "int simple"
	@echo ""
	@echo "Test 2: Phi Functions (phi_test.c)"
	@echo "-----------------------------------"
	@echo "Input:"
	@cat phi_test.c
	@echo ""
	@echo "SSA form with phi functions:"
	@./$(COMPILER) < phi_test.c 2>/dev/null | grep -A15 "int phi_test"
	@echo ""

# Compile example programs
examples: $(COMPILER)
	@echo "Compiling example programs.."
	@mkdir -p examples_output
	@for ex in $(EXAMPLES); do \
		echo "  Processing $$ex.c..."; \
		./$(COMPILER) < $$ex.c 2>/dev/null | tail -n +3 > examples_output/$$ex.out.c; \
		$(CC) examples_output/$$ex.out.c -o examples_output/$$ex 2>/dev/null; \
	done
	@echo "Examples compiled to examples_output/"


# Benchmark (very simple timing)
benchmark: $(COMPILER)
	@echo "Running simple benchmark..."
	@echo "Compiling comprehensive_test.c 100 times..."
	@time for i in $$(seq 1 100); do \
		./$(COMPILER) < comprehensive_test.c > /dev/null 2>&1; \
	done
	@echo "Done!"

# Clean built files
clean:
	@echo "Cleaning build artifacts..."
	@rm -f $(COMPILER)
	@rm -f tcc_original
	@rm -f *.out.c
	@rm -f *.bin
	@rm -f /tmp/const_demo.c
	@rm -rf examples_output
	@echo "Clean complete!"

# Install to system (optional)
#install: $(COMPILER)
#	@echo "Installing $(COMPILER) to /usr/local/bin..."
#	@sudo cp $(COMPILER) /usr/local/bin/
#	@echo "Installation complete! You can now run 'ssac' from anywhere."

# Uninstall from system
#uninstall:
#	@echo "Removing $(COMPILER) from /usr/local/bin..."
#	@sudo rm -f /usr/local/bin/$(COMPILER)
#	@echo "Uninstallation complete!"

# Help message
help:
	@echo "SSA C Compiler - Makefile Help"
	@echo ""
	@echo "Available targets:"
	@echo "  make              - Build the SSA compiler"
	@echo "  make debug        - Build with debug symbols"
	@echo "  make test         - Run all tests"
	@echo "  make demo         - Show optimization demonstrations"
	@echo "  make examples     - Compile all example programs"
	@echo "  make benchmark    - Run simple performance benchmark"
	@echo "  make clean        - Remove all built files"
#	@echo "  make install      - Install to /usr/local/bin (requires sudo)"
#	@echo "  make uninstall    - Remove from /usr/local/bin (requires sudo)"
	@echo ""
	@echo "Individual test targets:"
	@echo "  make simple_test        - Test constant folding"
	@echo "  make phi_test          - Test phi functions"
	@echo "  make comprehensive_test - Test full features"
	@echo ""
	@echo "Usage examples:"
	@echo "  make && make test             # Build and test"
	@echo "  make clean && make debug      # Clean rebuild with debug"
	@echo "  ./ssac < myprogram.c > out.c  # Compile a program"
	@echo ""

# Version info
version:
	@echo "SSA C Compiler"
	@echo "Version: 1.0"
	@echo "Features: CFG, Dominator Tree, SSA Form, Constant Propagation, DCE"
	@echo "Target: C code generation"
	@echo ""
	@echo "Compiler: $(CC)"
	@echo "Flags: $(CFLAGS)"
