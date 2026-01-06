# Makefile for Ferrite (Python-based compiler)

# How we invoke the compiler
PYTHON      ?= python3
COMPILER    = $(PYTHON) ./ferrite.py

# Where the source examples live
EXAMPLES_DIR = examples

# Where we put generated .c files and executables
BUILD_DIR    = build

# Find all Ferrite source files
SOURCES      = $(wildcard $(EXAMPLES_DIR)/*.fe)

# Generated files
C_FILES      = $(patsubst $(EXAMPLES_DIR)/%.fe, $(BUILD_DIR)/%.c, $(SOURCES))
EXECS        = $(patsubst $(EXAMPLES_DIR)/%.fe, $(BUILD_DIR)/%, $(SOURCES))

# Default target: build all examples
all: $(EXECS)

# Rule: .fe → .c  (run the Python compiler)
$(BUILD_DIR)/%.c: $(EXAMPLES_DIR)/%.fe | $(BUILD_DIR)
	$(COMPILER) $< -o $@

# Rule: .c → executable
$(BUILD_DIR)/%: $(BUILD_DIR)/%.c
	gcc -Wall -O2 -o $@ $<

# Create output directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Clean everything we generated
clean:
	rm -rf $(BUILD_DIR)

# Convenience: run one specific example
#   usage:  make run-test    or    make run-fib
run-%: $(BUILD_DIR)/%
	@echo "Running $< ..."
	@$<

# Run every compiled example
run-all: $(EXECS)
	@for prog in $(EXECS); do \
		echo "────────────────────"; \
		echo "Running $$prog"; \
		echo "────────────────────"; \
		$$prog; \
		echo ""; \
	done

.PHONY: all clean run-all
