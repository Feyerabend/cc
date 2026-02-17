# Makefile for Knapsack Problem Implementations
# Compiler settings
CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c11
CFLAGS_DEBUG = -Wall -Wextra -g -std=c11

# Python interpreter
PYTHON = python3

# Targets
.PHONY: all clean test run-c run-python run-html help install-deps

# Default target
all: knapsack knapsack_original

help:
	@echo "Knapsack Problem - Build System"
	@echo "-------------------------------"
	@echo ""
	@echo "Available targets:"
	@echo "  all          - Build all C implementations"
	@echo "  clean        - Remove compiled binaries"
	@echo "  test         - Run all tests"
	@echo "  run-c        - Run C implementation"
	@echo "  run-python   - Run Python implementation"
	@echo "  run-html     - Open HTML visualisation"
	@echo "  install-deps - Install Python dependencies"
	@echo ""
	@echo "Individual builds:"
	@echo "  knapsack           - Build C version"
	@echo "  debug              - Build with debug symbols"
	@echo ""
	@echo "Usage examples:"
	@echo "  make all            # Build everything"
	@echo "  make test           # Run comprehensive tests"
	@echo "  make run-python     # Run Python implementation"

# Build enhanced C implementation
knapsack: knapsack.c
	@echo "Building C implementation.."
	$(CC) $(CFLAGS) -o knapsack knapsack.c
	@echo "  Built: knapsack"

# Debug builds
debug: knapsack.c
	@echo "Building with debug symbols.."
	$(CC) $(CFLAGS_DEBUG) -o knapsack_debug knapsack.c
	@echo "  Built: knapsack_debug (use with gdb)"

# Clean compiled files
clean:
	@echo "Cleaning u..."
	rm -f knapsack knapsack_debug
	rm -rf __pycache__ *.pyc
	@echo "Clean complete"

# Run C implementation
run-c: knapsack
	@echo "Running C implementation.."
	@echo ""
	./knapsack

# Run Python implementation
run-python:
	@echo "Running enhanced Python implementation.."
	@echo ""
	$(PYTHON) knapsack.py

# Run comprehensive Python tests
test: knapsack
	@echo "COMPREHENSIVE TEST SUITE"
	@echo ""
	@echo "1. Testing Python implementation..."
	@echo ""
	$(PYTHON) knapsack.py
	@echo ""
	@echo "2. Testing C implementation..."
	@echo ""
	./knapsack
	@echo ""
	@echo "All tests completed"

# Open HTML visualisation
run-html:
	@echo "Opening HTML visualisation.."
	@if command -v xdg-open > /dev/null; then \
		xdg-open knapsack.html; \
	elif command -v open > /dev/null; then \
		open knapsack.html; \
	else \
		echo "Please open knapsack.html manually"; \
	fi

# Install Python dependencies (if needed)
install-deps:
	@echo "Checking Python dependencies.."
	@$(PYTHON) -c "import typing" 2>/dev/null || pip install typing
	@echo "Dependencies ready"

# Memory check with valgrind (if available)
memcheck: knapsack
	@if command -v valgrind > /dev/null; then \
		echo "Running memory check with valgrind.."; \
		valgrind --leak-check=full --show-leak-kinds=all ./knapsack; \
	else \
		echo "valgrind not found. Install it for memory checking."; \
	fi

# Profile with gprof (requires compilation with -pg)
profile:
	$(CC) $(CFLAGS) -pg -o knapsack_profile knapsack.c
	./knapsack_profile
	gprof knapsack_profile gmon.out > analysis.txt
	@echo "Profile saved to analysis.txt"

# Benchmark all implementations
benchmark: all
	@echo "Running benchmarks.."
	@echo ""
	@echo "Python:"
	@time $(PYTHON) knapsack.py > /dev/null
	@echo ""
	@echo "C:"
	@time ./knapsack > /dev/null

# Static analysis (if cppcheck available)
analyze:
	@if command -v cppcheck > /dev/null; then \
		echo "Running static analysis..."; \
		cppcheck --enable=all --suppress=missingIncludeSystem knapsack.c; \
	else \
		echo "cppcheck not found. Install for static analysis."; \
	fi
