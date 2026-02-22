# ─────────────────────────────────────────────────────────────────────────────
# THIS MAKEFILE MUST RUN BEFORE YOU COMPILE THE CODE FOR THE RPI PICO, I.E.
#    main.c & display.h/.c
# THE rom.h PRODUCED BY THIS MAKE, IS THE "program" THAT THE EMULATOR WILL RUN. 
# ─────────────────────────────────────────────────────────────────────────────
# Assume you have a assembled program, binary and header file will be produced.
# 6502 ROM build pipeline
#
#   *.asm  ──[asm.py]──►  *.bin  ──[bin2header.py]──►  rom.h
#
# Usage:
#   make [ROM=name]         assemble <n>.asm → <n>.bin → rom.h
#   make verbose [ROM=name] same, with verbose assembler listing
#   make clean              remove generated .bin and rom.h
#   make help               show this message
#
# ROM defaults to "demo" if not specified on the command line.
# asm.py, bin2header.py and your .asm must all live in the same directory.
# ─────────────────────────────────────────────────────────────────────────────

ROM     ?= demo

PYTHON  := python3
ASM     := $(PYTHON) asm.py
BIN2HDR := $(PYTHON) bin2header.py

SRC     := $(ROM).asm
BIN     := $(ROM).bin
HEADER  := rom.h
ARRAY   := rom_data

# ─────────────────────────────────────────────────────────────────────────────

.PHONY: all verbose clean help

## Default target – only rebuilds what has changed
all: $(HEADER)

## Step 1: .asm → .bin  (rebuild if source or assembler changes)
$(BIN): $(SRC) asm.py
	@echo "[asm]  $(SRC) → $(BIN)"
	@$(ASM) $(SRC) $(BIN)

## Step 2: .bin → rom.h  (rebuild if binary or script changes)
$(HEADER): $(BIN) bin2header.py
	@echo "[hdr]  $(BIN) → $(HEADER)"
	@$(BIN2HDR) $(BIN) $(HEADER) $(ARRAY)

## Same pipeline but with verbose assembler output (symbol table + listing)
verbose: $(SRC) asm.py bin2header.py
	@echo "[asm]  $(SRC) → $(BIN)  (verbose)"
	@$(ASM) $(SRC) $(BIN) -v
	@echo "[hdr]  $(BIN) → $(HEADER)"
	@$(BIN2HDR) $(BIN) $(HEADER) $(ARRAY)

## Remove generated files
clean:
	@echo "[clean] $(BIN) $(HEADER)"
	@rm -f $(BIN) $(HEADER)

help:
	@echo ""
	@echo "  make [ROM=name]          assemble <n>.asm and generate rom.h"
	@echo "  make verbose [ROM=name]  same, with verbose assembler output"
	@echo "  make clean               remove $(BIN) and $(HEADER)"
	@echo ""
	@echo "  Default: ROM=demo  →  reads demo.asm"
	@echo "  Example: make ROM=mygame  →  reads mygame.asm"
	@echo ""
