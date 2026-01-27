# Makefile for the compiler system

# Python interpreter
PYTHON := python3

# Compiler script
COMPILER := compiler_main.py

# Source directory
SRC_DIR := src

# Output directory for all compilation results
OUTPUT_BASE_DIR := output

# Plugins directory
PLUGINS_DIR := plugins

# Compiler flags (can be overridden)
COMPILER_FLAGS := --plugins $(PLUGINS_DIR)

# Debug mode (set DEBUG=1 to enable)
ifdef DEBUG
    COMPILER_FLAGS += --debug
endif

# Find all .p files in the src directory
P_FILES := $(wildcard $(SRC_DIR)/*.p)

# Extract base names (without path and extension)
BASE_NAMES := $(basename $(notdir $(P_FILES)))

# Generate output directory names (under output/)
OUTPUT_DIRS := $(addprefix $(OUTPUT_BASE_DIR)/, $(addsuffix _compilation, $(BASE_NAMES)))

# Default target
.PHONY: all
all: $(OUTPUT_DIRS)

# Pattern rule for building individual files
$(OUTPUT_BASE_DIR)/%_compilation: $(SRC_DIR)/%.p $(COMPILER) builtin_plugins.py compiler_core.py plugin_system.py $(PLUGINS_DIR)/*.py
	@echo "Compiling $< with plugins from $(PLUGINS_DIR)..."
	@mkdir -p $(OUTPUT_BASE_DIR)
	@cd $(OUTPUT_BASE_DIR) && $(PYTHON) ../$(COMPILER) ../$< $(COMPILER_FLAGS)

# Individual targets for each source file (for convenience)
.PHONY: $(BASE_NAMES)
$(BASE_NAMES): %: $(OUTPUT_BASE_DIR)/%_compilation

# Clean target - remove all output directories and Python cache
.PHONY: clean
clean:
	@echo "Cleaning up compilation directories..."
	@if [ -d "$(OUTPUT_BASE_DIR)" ]; then \
		echo "Removing $(OUTPUT_BASE_DIR)/"; \
		rm -rf "$(OUTPUT_BASE_DIR)"; \
	fi
	@echo "Cleaning up Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@find . -name "*.pyd" -delete 2>/dev/null || true
	@find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# List available plugins
.PHONY: list-plugins
list-plugins:
	@echo "Listing available plugins..."
	$(PYTHON) $(COMPILER) dummy --plugins $(PLUGINS_DIR) --list-plugins 2>/dev/null || true

# Debug compilation targets
.PHONY: debug-all $(addsuffix -debug, $(BASE_NAMES))
debug-all:
	$(MAKE) all DEBUG=1

$(addsuffix -debug, $(BASE_NAMES)): %-debug: %
	$(MAKE) $* DEBUG=1

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all          - Compile all .p files in $(SRC_DIR)/"
	@echo "  clean        - Remove all compilation output directories"
	@echo "  debug-all    - Compile all files with debug output"
	@echo "  list-plugins - Show available plugins"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Individual file targets:"
	@for name in $(BASE_NAMES); do \
		echo "  $$name       - Compile $(SRC_DIR)/$$name.p"; \
		echo "  $$name-debug - Compile $(SRC_DIR)/$$name.p with debug output"; \
	done
	@echo ""
	@echo "Variables:"
	@echo "  DEBUG=1      - Enable debug mode (make all DEBUG=1)"
	@echo "  PLUGINS_DIR  - Override plugins directory (default: $(PLUGINS_DIR))"

# Debug target to show discovered files
.PHONY: debug
debug:
	@echo "Source files found: $(P_FILES)"
	@echo "Base names: $(BASE_NAMES)"
	@echo "Output directories: $(OUTPUT_DIRS)"
	@echo "Compiler flags: $(COMPILER_FLAGS)"

# Force rebuild target
.PHONY: rebuild
rebuild: clean all