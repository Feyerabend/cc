# Compiler Project Makefile
# Usage: make [target]

PYTHON := python3
COMPILER := compiler.py
TEST_DIR := tests
EXAMPLES_DIR := examples

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help all clean test demo run verbose check lint format setup

# Default target
help:
	@echo "$(BLUE)Compiler Project - Available Targets$(NC)"
	@echo ""
	@echo "  $(GREEN)make run FILE=<file>$(NC)      - Compile and run a source file"
	@echo "  $(GREEN)make verbose FILE=<file>$(NC)  - Run with verbose output"
	@echo "  $(GREEN)make context FILE=<file>$(NC)  - Run with error context (N=2 by default)"
	@echo "  $(GREEN)make demo$(NC)                 - Run error reporting demonstration"
	@echo "  $(GREEN)make test$(NC)                 - Run all tests"
	@echo "  $(GREEN)make check$(NC)                - Check all Python files for syntax errors"
	@echo "  $(GREEN)make lint$(NC)                 - Run pylint on all Python files"
	@echo "  $(GREEN)make format$(NC)               - Format code with black"
	@echo "  $(GREEN)make clean$(NC)                - Remove generated files"
	@echo "  $(GREEN)make setup$(NC)                - Create example directories"
	@echo "  $(GREEN)make examples$(NC)             - Run all example programs"
	@echo ""
	@echo "Examples:"
	@echo "  make run FILE=program.txt"
	@echo "  make verbose FILE=program.txt"
	@echo "  make context FILE=program.txt N=3"

# Run a program
run:
ifndef FILE
	@echo "$(RED)Error: FILE parameter required$(NC)"
	@echo "Usage: make run FILE=<source_file>"
	@exit 1
endif
	@echo "$(BLUE)Compiling: $(FILE)$(NC)"
	@$(PYTHON) $(COMPILER) $(FILE)

# Run with verbose output
verbose:
ifndef FILE
	@echo "$(RED)Error: FILE parameter required$(NC)"
	@echo "Usage: make verbose FILE=<source_file>"
	@exit 1
endif
	@echo "$(BLUE)Compiling (verbose): $(FILE)$(NC)"
	@$(PYTHON) $(COMPILER) $(FILE) --verbose

# Run with error context
N ?= 2
context:
ifndef FILE
	@echo "$(RED)Error: FILE parameter required$(NC)"
	@echo "Usage: make context FILE=<source_file> [N=<context_lines>]"
	@exit 1
endif
	@echo "$(BLUE)Compiling with context ($(N) lines): $(FILE)$(NC)"
	@$(PYTHON) $(COMPILER) $(FILE) --context $(N)

# Run error demonstration
demo:
	@echo "$(YELLOW)Running error reporting demonstration...$(NC)"
	@$(PYTHON) error_examples.py

# Run all test files
test: check
	@echo "$(BLUE)Running all tests...$(NC)"
	@if [ -d "$(TEST_DIR)" ]; then \
		for file in $(TEST_DIR)/*.txt; do \
			echo "$(YELLOW)Testing: $$file$(NC)"; \
			$(PYTHON) $(COMPILER) $$file || true; \
			echo ""; \
		done; \
	else \
		echo "$(YELLOW)No test directory found. Run 'make setup' first.$(NC)"; \
	fi

# Check Python syntax
check:
	@echo "$(BLUE)Checking Python syntax...$(NC)"
	@$(PYTHON) -m py_compile *.py && echo "$(GREEN)✓ All files passed syntax check$(NC)" || echo "$(RED)✗ Syntax errors found$(NC)"

# Run pylint
lint:
	@echo "$(BLUE)Running pylint...$(NC)"
	@which pylint > /dev/null 2>&1 || (echo "$(RED)pylint not found. Install with: pip install pylint$(NC)" && exit 1)
	@pylint *.py || echo "$(YELLOW)Linting completed with warnings$(NC)"

# Format code with black
format:
	@echo "$(BLUE)Formatting code with black...$(NC)"
	@which black > /dev/null 2>&1 || (echo "$(RED)black not found. Install with: pip install black$(NC)" && exit 1)
	@black *.py && echo "$(GREEN)✓ Code formatted$(NC)"

# Create directory structure and example files
setup:
	@echo "$(BLUE)Setting up project directories...$(NC)"
	@mkdir -p $(TEST_DIR) $(EXAMPLES_DIR)
	@echo "# Test program 1" > $(TEST_DIR)/test1.txt
	@echo "let x = 10;" >> $(TEST_DIR)/test1.txt
	@echo "print(x);" >> $(TEST_DIR)/test1.txt
	@echo "# Valid example program" > $(EXAMPLES_DIR)/hello.txt
	@echo "let name = \"World\";" >> $(EXAMPLES_DIR)/hello.txt
	@echo "print(\"Hello, \" + name);" >> $(EXAMPLES_DIR)/hello.txt
	@echo "$(GREEN)✓ Created $(TEST_DIR)/ and $(EXAMPLES_DIR)/ directories$(NC)"

# Run example programs
examples:
	@echo "$(BLUE)Running example programs...$(NC)"
	@if [ -d "$(EXAMPLES_DIR)" ]; then \
		for file in $(EXAMPLES_DIR)/*.txt; do \
			echo "$(YELLOW)Running: $$file$(NC)"; \
			$(PYTHON) $(COMPILER) $$file; \
			echo ""; \
		done; \
	else \
		echo "$(YELLOW)No examples directory found. Run 'make setup' first.$(NC)"; \
	fi

# Clean generated files
clean:
	@echo "$(BLUE)Cleaning generated files...$(NC)"
	@rm -rf __pycache__ *.pyc *.pyo .pytest_cache .mypy_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# Quick compile shortcut
c: run

# Quick verbose shortcut  
v: verbose

# All-in-one test
all: check demo examples
	@echo "$(GREEN)✓ All tasks completed$(NC)"