# Ferrite Compiler Makefile
# Combines compilation, running, cleaning, and automated regression testing with .expected files

FERRITE = python3 ferrite.py
CC = gcc
CFLAGS = -Wall -O2

# Sources are in examples/
SOURCES = $(wildcard examples/*.fe)
C_FILES = $(SOURCES:.fe=.c)
EXECUTABLES = $(SOURCES:.fe=)

# Keep C files by default for inspection
.SECONDARY: $(C_FILES)

.PHONY: all clean clean-all clean-exe clean-c run-all test update-expected help \
        run-hello run-struct run-borrow run-advanced run-factorial run-fibonacci \
        run-gcd run-countdown force force-test

# Default: compile all examples (keeps C files)
all: examples

examples: $(EXECUTABLES)
	@echo "  All examples compiled successfully"
	@echo "  C files kept in examples/ (use 'make clean-c' to remove them)"

# Pattern rule: .fe → .c
examples/%.c: examples/%.fe ferrite.py
	@echo "Compiling $< to C..."
	@$(FERRITE) $< -o $@

# Pattern rule: .c → executable
examples/%: examples/%.c
	@echo "Compiling C to executable: $@"
	@$(CC) $(CFLAGS) -o $@ $<

# Run all executables (shows raw output)
run-all: $(EXECUTABLES)
	@echo "Running all examples:"
	@for exe in $(EXECUTABLES); do \
		echo ""; \
		echo "=== Running $$(basename $$exe) ==="; \
		./$$exe || echo "✗ $$exe crashed"; \
	done

# Individual run targets
run-hello: examples/hello
	@echo "=== Running hello ==="
	@./examples/hello

run-struct: examples/struct
	@echo "=== Running struct ==="
	@./examples/struct

run-borrow: examples/borrow
	@echo "=== Running borrow ==="
	@./examples/borrow

run-advanced: examples/advanced
	@echo "=== Running advanced ==="
	@./examples/advanced

run-factorial: examples/factorial
	@echo "=== Running factorial ==="
	@./examples/factorial

run-fibonacci: examples/fibonacci
	@echo "=== Running fibonacci ==="
	@./examples/fibonacci

run-gcd: examples/gcd
	@echo "=== Running gcd ==="
	@./examples/gcd

run-countdown: examples/countdown
	@echo "=== Running countdown ==="
	@./examples/countdown

# Automated regression testing: compare output to .expected files
test: $(EXECUTABLES)
	@echo "Running automated regression tests:"
	@echo "  (Compares each program's output to examples/<name>.expected)"
	@pass=0; fail=0; skipped=0; \
	for exe in $(EXECUTABLES); do \
		base=$$(basename $$exe); \
		expected="examples/$$base.expected"; \
		if [ ! -f "$$expected" ]; then \
			echo "  $$base: NO .expected file -> SKIPPED (run 'make update-expected' to create it)"; \
			skipped=$$((skipped+1)); \
			continue; \
		fi; \
		echo -n "$$base ... "; \
		output=$$(./$$exe 2>&1); \
		expected_content=$$(cat "$$expected"); \
		if [ "$$output" = "$$expected_content" ]; then \
			echo "PASS"; \
			pass=$$((pass+1)); \
		else \
			echo "FAIL"; \
			echo "=== Got ==="; \
			echo "$$output"; \
			echo "=== Expected ==="; \
			echo "$$expected_content"; \
			echo ""; \
			fail=$$((fail+1)); \
		fi; \
	done; \
	echo ""; \
	echo "Summary: $$pass PASS, $$fail FAIL, $$skipped SKIPPED"; \
	if [ $$fail -eq 0 ]; then exit 0; else exit 1; fi

# Regenerate all .expected files from current compiler output
update-expected: $(EXECUTABLES)
	@echo "Updating all .expected files based on current compiler output..."
	@echo "  (This records what each program currently prints)"
	@for exe in $(EXECUTABLES); do \
		base=$$(basename $$exe); \
		expected="examples/$$base.expected"; \
		echo "  -> $$expected"; \
		./$$exe > "$$expected"; \
	done
	@echo "  All .expected files updated"

# Force full clean + rebuild + test
force-test: clean-all test

# Force full clean + rebuild
force: clean-all examples

# Clean only executables
clean-exe:
	@echo "Removing executables..."
	@rm -f $(EXECUTABLES)

# Clean only C files
clean-c:
	@echo "Removing C files..."
	@rm -f $(C_FILES)

# Clean everything
clean: clean-all

clean-all: clean-exe clean-c
	@echo "  All generated files removed"

# Detailed help
help:
	@echo "Ferrite Compiler - Helpful Guide"
	@echo ""
	@echo "This Makefile helps you compile, run, and test your Ferrite examples."
	@echo "Examples live in the 'examples/' directory."
	@echo ""
	@echo "=== First-time setup (do this once) ==="
	@echo "  make update-expected"
	@echo "    -> Compiles everything and creates .expected files with current output"
	@echo ""
	@echo "=== Normal workflow ==="
	@echo "  make test"
	@echo "    -> Compiles (only what's needed) and checks if output matches .expected"
	@echo "    -> Shows PASS/FAIL for each example"
	@echo "    -> If something FAILs, you'll see the diff"
	@echo ""
	@echo "  If you changed the compiler and the new output is correct:"
	@echo "    make update-expected"
	@echo "    -> Accepts the new output as the expected one"
	@echo ""
	@echo "=== Common commands ==="
	@echo "  make                -> Compile all examples (default)"
	@echo "  make all / examples -> Same as above (C files are kept for inspection)"
	@echo "  make run-all        -> Compile + run every example (raw output)"
	@echo "  make run-<name>     -> Run one example (e.g. make run-hello)"
	@echo "  make force-test     -> Clean everything, recompile, and test (useful after big changes)"
	@echo "  make clean-all      -> Remove all generated .c files and executables"
	@echo ""
	@echo "=== Why you might see no compilation messages ==="
	@echo "  Make only recompiles files that changed. This is normal and fast."
	@echo "  To force full recompilation: make clean-all && make test"
	@echo ""
	@echo "=== Adding a new example ==="
	@echo "  1. Put new.fe in examples/"
	@echo "  2. Run 'make update-expected' → creates its .expected file"
	@echo "  3. Now 'make test' will include it"
	@echo ""
	@echo "Run 'make help' anytime for this guide!"
