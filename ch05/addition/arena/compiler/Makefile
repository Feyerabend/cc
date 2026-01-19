# Makefile for PL/0 Compiler

# Compiler settings
CC = gcc
CFLAGS = -Wall -Wextra -Werror -std=c11 -O2 -g
LDFLAGS = 

# Directories
SRC_DIR = src
BUILD_DIR = build
BIN_DIR = bin
TEST_DIR = tests

# Output binary
TARGET = $(BIN_DIR)/pl0c

# Source files
SOURCES = $(SRC_DIR)/main.c \
          $(SRC_DIR)/arena.c \
          $(SRC_DIR)/token_stream.c \
          $(SRC_DIR)/lexer.c \
          $(SRC_DIR)/ast.c \
          $(SRC_DIR)/parser.c \
          $(SRC_DIR)/symbol_table.c \
          $(SRC_DIR)/tac_generator.c \
          $(SRC_DIR)/compiler.c \
          $(SRC_DIR)/util.c

# Object files
OBJECTS = $(SOURCES:$(SRC_DIR)/%.c=$(BUILD_DIR)/%.o)

# Header dependencies
HEADERS = $(SRC_DIR)/compiler.h \
          $(SRC_DIR)/arena.h \
          $(SRC_DIR)/token_stream.h \
          $(SRC_DIR)/ast.h \
          $(SRC_DIR)/symbol_table.h \
          $(SRC_DIR)/tac.h


# Targets

.PHONY: all clean test install uninstall help debug release

# Default target
all: $(TARGET)

# Main binary
$(TARGET): $(OBJECTS) | $(BIN_DIR)
	@echo "Linking $@"
	@$(CC) $(LDFLAGS) -o $@ $^
	@echo "✓ Build complete: $@"

# Compile object files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c $(HEADERS) | $(BUILD_DIR)
	@echo "Compiling $<"
	@$(CC) $(CFLAGS) -c -o $@ $<

# Create directories
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

$(BIN_DIR):
	@mkdir -p $(BIN_DIR)


# Debug and Release

debug: CFLAGS += -DDEBUG -fsanitize=address -fsanitize=undefined
debug: LDFLAGS += -fsanitize=address -fsanitize=undefined
debug: clean all

release: CFLAGS = -Wall -Wextra -std=c11 -O3 -DNDEBUG
release: clean all


# Test

test: $(TARGET)
	@echo "Running tests..."
	@./run_tests.sh

# Test individual files
test-file: $(TARGET)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Specify FILE=<path>"; \
		exit 1; \
	fi
	@echo "Testing $(FILE)..."
	@$(TARGET) -A --verbose $(FILE)


# Examples

examples: $(TARGET)
	@echo "Compiling example programs..."
	@mkdir -p examples/output
	@for file in examples/*.pl0; do \
		echo "  Compiling $$file..."; \
		$(TARGET) -A -o examples/output $$file || exit 1; \
	done
	@echo "✓ All examples compiled"


# Installation

PREFIX ?= /usr/local
INSTALL_BIN = $(PREFIX)/bin

install: $(TARGET)
	@echo "Installing to $(INSTALL_BIN)..."
	@install -d $(INSTALL_BIN)
	@install -m 755 $(TARGET) $(INSTALL_BIN)/
	@echo "✓ Installation complete"

uninstall:
	@echo "Uninstalling from $(INSTALL_BIN)..."
	@rm -f $(INSTALL_BIN)/pl0c
	@echo "✓ Uninstall complete"


# Cleaning

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR) $(BIN_DIR)
	@rm -f examples/output/*
	@echo "✓ Clean complete"

distclean: clean
	@rm -rf *.o *.out *.log
	@rm -rf examples/output


# Documentation and help

help:
	@echo "PL/0 Compiler - Makefile targets"
	@echo ""
	@echo "Build targets:"
	@echo "  all          - Build the compiler (default)"
	@echo "  debug        - Build with debugging symbols and sanitizers"
	@echo "  release      - Build optimized release version"
	@echo "  clean        - Remove build artifacts"
	@echo "  distclean    - Remove all generated files"
	@echo ""
	@echo "Testing:"
	@echo "  test         - Run all tests"
	@echo "  test-file FILE=<path> - Test single file"
	@echo "  examples     - Compile all example programs"
	@echo ""
	@echo "Installation:"
	@echo "  install      - Install to $(PREFIX)/bin"
	@echo "  uninstall    - Remove installation"
	@echo ""
	@echo "Usage examples:"
	@echo "  make                    # Build compiler"
	@echo "  make debug              # Build with debug info"
	@echo "  make test               # Run test suite"
	@echo "  make test-file FILE=test.pl0"
	@echo "  make install PREFIX=/opt"
	@echo ""


# Project info

info:
	@echo "PL/0 Compiler Build Information"
	@echo "================================"
	@echo "Compiler:    $(CC)"
	@echo "C Flags:     $(CFLAGS)"
	@echo "LD Flags:    $(LDFLAGS)"
	@echo "Sources:     $(words $(SOURCES)) files"
	@echo "Target:      $(TARGET)"
	@echo ""
	@echo "Source files:"
	@for src in $(SOURCES); do echo "  - $$src"; done


# Code statistics

stats:
	@echo "Code Statistics"
	@echo "==============="
	@echo -n "Source files:    "
	@find $(SRC_DIR) -name '*.c' -o -name '*.h' | wc -l
	@echo -n "Lines of code:   "
	@find $(SRC_DIR) -name '*.c' -o -name '*.h' | xargs wc -l | tail -1
	@echo -n "Test files:      "
	@find $(TEST_DIR) -name '*.pl0' 2>/dev/null | wc -l || echo "0"


# Helpers

# Format code using clang-format
format:
	@if command -v clang-format >/dev/null 2>&1; then \
		echo "Formatting source files..."; \
		find $(SRC_DIR) -name '*.c' -o -name '*.h' | xargs clang-format -i; \
		echo "✓ Formatting complete"; \
	else \
		echo "Error: clang-format not found"; \
		exit 1; \
	fi

# Run static analysis
analyze:
	@if command -v cppcheck >/dev/null 2>&1; then \
		echo "Running static analysis..."; \
		cppcheck --enable=all --suppress=missingIncludeSystem $(SRC_DIR); \
	else \
		echo "Error: cppcheck not found"; \
		exit 1; \
	fi

# Dependency tracking (automatic recompilation when headers change)
-include $(OBJECTS:.o=.d)

$(BUILD_DIR)/%.d: $(SRC_DIR)/%.c | $(BUILD_DIR)
	@$(CC) -MM -MT $(@:.d=.o) $(CFLAGS) $< -o $@
