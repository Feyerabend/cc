# Makefile for VTable Compiler Project

# Default target: generate C code, compile, and run
all: run

# Generate C code by running the Python compiler
generate:
	@echo "Generating C code..."
	python3 main.py

# Compile the generated C code
compile: generate
	@echo "Compiling C code..."
	gcc output.c -o output -Wall -Wextra

# Run the compiled executable
run: compile
	@echo "Running the executable..."
	./output

# Clean up generated files
clean:
	rm -f output.c output
	find . -type d -name __pycache__ -exec rm -rf {} +

.PHONY: all generate compile run clean
