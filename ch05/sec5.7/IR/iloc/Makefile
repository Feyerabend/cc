# Makefile for RISC-V Compilation Pipeline
# Compiles: AST > ILOC > RISC-V > Binary > Execute

# Directories
BUILD_DIR = build
SRC_DIR = .

# Files
ILOC_FILE = $(BUILD_DIR)/program.iloc
ASM_FILE = $(BUILD_DIR)/program.s
BIN_FILE = $(BUILD_DIR)/program.bin

# Python interpreter
PYTHON = python3

# Phony targets
.PHONY: all clean run debug help view-iloc view-asm view-binary view iloc asm binary

# Default target: build everything
all: $(BIN_FILE)
	@echo ""
	@echo "  Build complete!"
	@echo "Binary: $(BIN_FILE)"
	@echo ""
	@echo "Run with: make run"

# Step 1: AST → ILOC
$(ILOC_FILE): ast_nodes.py iloc_ir.py ast_to_iloc.py example_program.py | $(BUILD_DIR)
	@echo "[1/3] Generating ILOC from AST..."
	$(PYTHON) ast_to_iloc.py $(ILOC_FILE)
	@echo ""

# Step 2: ILOC → RISC-V Assembly
$(ASM_FILE): $(ILOC_FILE) iloc_to_riscv.py
	@echo "[2/3] Translating ILOC to RISC-V..."
	$(PYTHON) iloc_to_riscv.py $(ILOC_FILE) $(ASM_FILE)
	@echo ""

# Step 3: RISC-V Assembly → Binary
$(BIN_FILE): $(ASM_FILE) asm.py
	@echo "[3/3] Assembling RISC-V to binary..."
	$(PYTHON) asm.py $(ASM_FILE) $(BIN_FILE)
	@echo ""

# Create build directory
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

# Run the compiled binary
run: $(BIN_FILE)
	@echo "Executing RISC-V binary..."
	$(PYTHON) vm.py $(BIN_FILE)
	@echo ""
	@echo "  Execution complete"

# Debug mode: run with debug output
debug: $(BIN_FILE)
	@echo "Executing RISC-V binary (DEBUG MODE)..."
	$(PYTHON) vm.py $(BIN_FILE) -d
	@echo ""

# View intermediate files
view-iloc: $(ILOC_FILE)
	@echo "ILOC Intermediate Representation"
	@cat $(ILOC_FILE)
	@echo ""

view-asm: $(ASM_FILE)
	@echo "RISC-V Assembly Code"
	@cat $(ASM_FILE)
	@echo ""

view-binary: $(BIN_FILE)
	@echo "Binary Machine Code (hexdump)"
	@hexdump -C $(BIN_FILE) | head -20
	@echo ""

# View all intermediate files
view: view-iloc view-asm view-binary

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@rm -f *.pyc
	@rm -rf __pycache__
	@echo "  Clean complete"

# Help target
help:
	@echo "RISC-V Compilation Pipeline - Makefile"
	@echo ""
	@echo "Main targets:"
	@echo "  make              - Build all (AST → ILOC → RISC-V → Binary)"
	@echo "  make run          - Build and execute the binary"
	@echo "  make debug        - Build and execute with debug output"
	@echo "  make clean        - Remove build artifacts"
	@echo ""
	@echo "View intermediate files:"
	@echo "  make view-iloc    - Display ILOC code"
	@echo "  make view-asm     - Display RISC-V assembly"
	@echo "  make view-binary  - Display binary (hexdump)"
	@echo "  make view         - Display all intermediate files"
	@echo ""
	@echo "Individual stages:"
	@echo "  make iloc         - Generate ILOC only"
	@echo "  make asm          - Generate assembly (requires ILOC)"
	@echo "  make binary       - Generate binary (requires assembly)"
	@echo ""
	@echo "Pipeline stages:"
	@echo "  $(ILOC_FILE)  - ILOC intermediate code"
	@echo "  $(ASM_FILE)   - RISC-V assembly"
	@echo "  $(BIN_FILE)   - Binary machine code"
	@echo ""

# Individual stage targets for manual control
iloc: $(ILOC_FILE)
	@echo "  ILOC generation complete"

asm: $(ASM_FILE)
	@echo "  Assembly generation complete"

binary: $(BIN_FILE)
	@echo "  Binary generation complete"

