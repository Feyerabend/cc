.PHONY: all clean run1 run2 run3 run4 test verbose help

PYTHON = python3
COMPILER = compiler.py

all: test

help:
	@echo "Simple Language Compiler - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make run1      - Run sample1.prog (Hello World)"
	@echo "  make run2      - Run sample2.prog (Conditionals)"
	@echo "  make run3      - Run sample3.prog (Loops)"
	@echo "  make run4      - Run sample4.prog (Fibonacci)"
	@echo "  make test      - Run all sample programs"
	@echo "  make verbose   - Run all samples with verbose output"
	@echo "  make clean     - Clean up generated files"

run1:
	@echo "=== Running sample1.prog ==="
	@$(PYTHON) $(COMPILER) sample1.prog

run2:
	@echo "=== Running sample2.prog ==="
	@$(PYTHON) $(COMPILER) sample2.prog

run3:
	@echo "=== Running sample3.prog ==="
	@$(PYTHON) $(COMPILER) sample3.prog

run4:
	@echo "=== Running sample4.prog ==="
	@$(PYTHON) $(COMPILER) sample4.prog

test: run1 run2 run3 run4
	@echo ""
	@echo "All tests completed!"

verbose:
	@echo "=== Running sample1.prog (verbose) ==="
	@$(PYTHON) $(COMPILER) sample1.prog --verbose
	@echo ""
	@echo "=== Running sample2.prog (verbose) ==="
	@$(PYTHON) $(COMPILER) sample2.prog --verbose
	@echo ""
	@echo "=== Running sample3.prog (verbose) ==="
	@$(PYTHON) $(COMPILER) sample3.prog --verbose
	@echo ""
	@echo "=== Running sample4.prog (verbose) ==="
	@$(PYTHON) $(COMPILER) sample4.prog --verbose

clean:
	@echo "Cleaning up..."
	@rm -f *.pyc
	@rm -rf __pycache__
	@echo "Done!"

