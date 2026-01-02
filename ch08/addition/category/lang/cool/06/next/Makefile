# Makefile for COOL Free-Monad Compiler Pipeline

PYTHON := python3

SRC := \
	cat_free.py \
	ir.py \
	ir_lowering.py \
	codegen_core.py \
	codegen_state.py \
	codegen_driver.py \
	trace_algebra.py \
	test_pipeline.py

.PHONY: all test run clean check

all: test

test: check
	$(PYTHON) test_pipeline.py

run: test

check:
	@for f in $(SRC); do \
		if [ ! -f $$f ]; then \
			echo "Missing file: $$f"; exit 1; \
		fi \
	done
	@echo "All source files present."

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "Cleaned."
