# ─────────────────────────────────────────────────────────────────────────────
# RISC-V Concurrent VM — Makefile
# ─────────────────────────────────────────────────────────────────────────────
# Usage:
#   make                  build all .bin files from .asm sources
#   make green            assemble + run green thread demo
#   make mutex            assemble + run mutex demo (kernel threads)
#   make green-trace      green demo with full instruction trace
#   make mutex-trace      mutex demo with full instruction trace
#   make compare          run green demo in BOTH modes side by side
#   make demos            run all demos back to back
#   make clean            remove all generated .bin and .sym files
#   make help             show this message
#
# Tuning:
#   make mutex QUANTUM=3          change timer quantum (default 5)
#   make green-trace QUANTUM=2    trace with tighter preemption
# ─────────────────────────────────────────────────────────────────────────────

PYTHON    := python3
ASM       := $(PYTHON) asm_concurrent.py
VM        := $(PYTHON) vm_concurrent.py

QUANTUM   ?= 5

# ── Sources & targets ────────────────────────────────────────────────────────

ASM_SRCS  := $(wildcard *.asm)
BIN_TARGETS := $(ASM_SRCS:.asm=.bin)

# ── Default target ───────────────────────────────────────────────────────────

.PHONY: all
all: $(BIN_TARGETS)
	@echo ""
	@echo "  Built: $(BIN_TARGETS)"
	@echo "  Try:   make green   /   make mutex   /   make demos"
	@echo ""

# ── Generic assemble rule ────────────────────────────────────────────────────

%.bin %.sym: %.asm asm_concurrent.py
	@echo "  ASM  $< → $@"
	@$(ASM) $< $@

# ── Demo targets ─────────────────────────────────────────────────────────────

.PHONY: green
green: demo_green.bin
	@echo ""
	@echo "━━━  GREEN THREAD DEMO  (cooperative, YIELD-driven)  ━━━"
	@echo ""
	@$(VM) demo_green.bin --mode green

.PHONY: green-trace
green-trace: demo_green.bin
	@echo ""
	@echo "━━━  GREEN THREAD DEMO — TRACE  ━━━"
	@echo ""
	@$(VM) demo_green.bin --mode green --trace

.PHONY: mutex
mutex: demo_mutex.bin
	@echo ""
	@echo "━━━  MUTEX DEMO  (kernel threads, quantum=$(QUANTUM))  ━━━"
	@echo ""
	@$(VM) demo_mutex.bin --mode kernel --quantum $(QUANTUM)

.PHONY: mutex-trace
mutex-trace: demo_mutex.bin
	@echo ""
	@echo "━━━  MUTEX DEMO — TRACE  (kernel threads, quantum=$(QUANTUM))  ━━━"
	@echo ""
	@$(VM) demo_mutex.bin --mode kernel --quantum $(QUANTUM) --trace

# ── Side-by-side comparison ──────────────────────────────────────────────────
# Runs demo_green.bin with BOTH schedulers so you can see the difference.
# Green:  threads switch only at YIELD → clean 1,2,1,2,1,2
# Kernel: timer preempts mid-loop      → nondeterministic interleaving

.PHONY: compare
compare: demo_green.bin
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  SAME BINARY — TWO SCHEDULERS"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "  ── 1.  GREEN  (cooperative) ──────────────────────────────────────"
	@echo ""
	@$(VM) demo_green.bin --mode green
	@echo ""
	@echo "  ── 2.  KERNEL (preemptive, quantum=$(QUANTUM)) ───────────────────────────"
	@echo ""
	@$(VM) demo_green.bin --mode kernel --quantum $(QUANTUM)
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Note: green always yields at the same point (predictable)."
	@echo "        kernel fires the timer mid-instruction-stream (nondeterministic)."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Built-in VM demos ────────────────────────────────────────────────────────

.PHONY: demo-barrier
demo-barrier:
	@echo ""
	@echo "━━━  MEMORY BARRIER DEMO  ━━━"
	@echo ""
	@$(VM) --demo barrier

.PHONY: demos
demos: green mutex demo-barrier
	@echo ""
	@echo "━━━  All demos complete  ━━━"

# ── Run any .asm file quickly ─────────────────────────────────────────────────
# Usage: make run FILE=myprog.asm MODE=kernel QUANTUM=8

FILE    ?= demo_green.asm
MODE    ?= green

.PHONY: run
run: $(FILE:.asm=.bin)
	@$(VM) $(FILE:.asm=.bin) --mode $(MODE) --quantum $(QUANTUM)

.PHONY: run-trace
run-trace: $(FILE:.asm=.bin)
	@$(VM) $(FILE:.asm=.bin) --mode $(MODE) --quantum $(QUANTUM) --trace

# ── Utility ──────────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	@echo "  Removing generated files..."
	@rm -f $(BIN_TARGETS) $(ASM_SRCS:.asm=.sym)
	@echo "  Done."

.PHONY: help
help:
	@echo ""
	@echo "  RISC-V Concurrent VM — Make targets"
	@echo ""
	@echo "  make                  assemble all .asm files"
	@echo "  make green            cooperative green thread demo"
	@echo "  make green-trace      green demo with per-instruction trace"
	@echo "  make mutex            mutex + kernel thread demo  (QUANTUM=$(QUANTUM))"
	@echo "  make mutex-trace      mutex demo with trace"
	@echo "  make compare          run same binary with green vs kernel scheduler"
	@echo "  make demo-barrier     memory barrier demo (built-in)"
	@echo "  make demos            run all demos in sequence"
	@echo "  make run  FILE=x.asm MODE=green|kernel  QUANTUM=N"
	@echo "  make run-trace  FILE=x.asm MODE=... QUANTUM=..."
	@echo "  make clean            remove .bin and .sym files"
	@echo ""
	@echo "  Tuning variables (override on command line):"
	@echo "    QUANTUM=$(QUANTUM)   instructions per timer tick (kernel mode)"
	@echo "    FILE=$(FILE)"
	@echo "    MODE=$(MODE)"
	@echo ""
