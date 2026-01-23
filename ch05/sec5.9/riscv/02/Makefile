# Makefile for RISC-V Toolchain
# Assembles, links, and runs sample programs

PYTHON = python3
ASM = $(PYTHON) asm_obj.py
LINKER = $(PYTHON) linker.py
VM = $(PYTHON) vm.py
ASM_SIMPLE = $(PYTHON) asm.py

# Directories
SAMPLES_DIR = samples
BUILD_DIR = build

# Sample programs
SIMPLE_PROGS = hello factorial fibonacci sum_array
MULTI_OBJS = multifile_main.o multifile_math.o

# Default target
.PHONY: all
all: setup $(SIMPLE_PROGS) multifile

# Create build directory
.PHONY: setup
setup:
	@mkdir -p $(BUILD_DIR)
	@mkdir -p $(SAMPLES_DIR)
	@echo "=== RISC-V Toolchain Build System ==="
	@echo ""

# Pattern rule for single-file programs (direct assembly to binary)
$(SIMPLE_PROGS): %: $(SAMPLES_DIR)/%.asm
	@echo "--- Building $@ (single file) ---"
	$(ASM_SIMPLE) $< $(BUILD_DIR)/$@.bin
	@echo "Running $@:"
	@$(VM) $(BUILD_DIR)/$@.bin
	@echo ""

# Multi-file example
.PHONY: multifile
multifile: $(BUILD_DIR)/multifile
	@echo "--- Building multifile (linked from multiple objects) ---"
	@echo "Running multifile:"
	@$(VM) $(BUILD_DIR)/multifile
	@echo ""

# Compile object files
$(BUILD_DIR)/multifile_main.o: $(SAMPLES_DIR)/multifile_main.asm
	@echo "Assembling multifile_main.asm -> multifile_main.o"
	$(ASM) $< $@

$(BUILD_DIR)/multifile_math.o: $(SAMPLES_DIR)/multifile_math.asm
	@echo "Assembling multifile_math.asm -> multifile_math.o"
	$(ASM) $< $@

# Link multi-file program
$(BUILD_DIR)/multifile: $(BUILD_DIR)/multifile_main.o $(BUILD_DIR)/multifile_math.o
	@echo "Linking multifile_main.o + multifile_math.o -> multifile"
	$(LINKER) $@ $(BUILD_DIR)/multifile_main.o $(BUILD_DIR)/multifile_math.o

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build directory..."
	@rm -rf $(BUILD_DIR)
	@echo "Done."

# Run a specific program
.PHONY: run-%
run-%: $(BUILD_DIR)/%.bin
	@echo "Running $*:"
	@$(VM) $<

# Run with debug output
.PHONY: debug-%
debug-%: $(BUILD_DIR)/%.bin
	@echo "Running $* (debug mode):"
	@$(VM) $< -d

# Help target
.PHONY: help
help:
	@echo "RISC-V Toolchain Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all           - Build and run all sample programs"
	@echo "  clean         - Remove all build artifacts"
	@echo "  hello         - Build and run hello.asm"
	@echo "  factorial     - Build and run factorial.asm"
	@echo "  fibonacci     - Build and run fibonacci.asm"
	@echo "  sum_array     - Build and run sum_array.asm"
	@echo "  multifile     - Build and run multi-file example"
	@echo "  run-PROG      - Run a specific program"
	@echo "  debug-PROG    - Run a program with debug output"
	@echo "  help          - Show this help message"
	@echo ""
	@echo "Example:"
	@echo "  make factorial      # Build and run factorial"
	@echo "  make debug-hello    # Run hello with debug output"
