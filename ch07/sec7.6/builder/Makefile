# Makefile for PL/0 Interpreter (C and Python versions)

CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2
PYTHON = python3

# Targets
C_TARGET = pl0
PY_SCRIPT = pl0.py

# Source files
C_SOURCES = pl0.c
C_OBJECTS = $(C_SOURCES:.c=.o)

# Default target - build C version
all: $(C_TARGET)

# Build C executable
$(C_TARGET): $(C_OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^

# Compile C object files
%.o: %.c
	$(CC) $(CFLAGS) -c $<

# Run C version
run-c: $(C_TARGET)
	./$(C_TARGET) $(ARGS)

# Run Python version
run-py: $(PY_SCRIPT)
	$(PYTHON) $(PY_SCRIPT) $(ARGS)

# Install Python script (make it executable)
install-py: $(PY_SCRIPT)
	chmod +x $(PY_SCRIPT)

# Clean build artifacts and symbol tables
clean:
	rm -f $(C_TARGET)
	rm -f $(C_OBJECTS)
	rm -f *.o
	rm -f *.out
	rm -f *.a
	rm -f *.so
	rm -f *.dylib
	rm -f core
	rm -f vgcore.*
	rm -rf *.dSYM
	rm -rf __pycache__
	rm -f *.pyc
	rm -f *.pyo

# Deep clean - remove all generated files including symbol tables
distclean: clean
	rm -f *.sym
	rm -f *.symtab
	rm -f *.map
	rm -f .*.swp
	rm -f *~
	rm -f \#*\#

# Help target
help:
	@echo "PL/0 Interpreter Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all         - Build C version (default)"
	@echo "  clean       - Remove build artifacts and symbol tables"
	@echo "  distclean   - Deep clean (removes all generated files)"
	@echo "  run-c       - Run C version (use ARGS=file.pl)"
	@echo "  run-py      - Run Python version (use ARGS=file.pl)"
	@echo "  install-py  - Make Python script executable"
	@echo "  help        - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make"
	@echo "  make run-c ARGS=sample.pl"
	@echo "  make run-py ARGS=sample.pl"
	@echo "  make clean"

.PHONY: all clean distclean run-c run-py install-py help
