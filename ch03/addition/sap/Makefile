# SAP VM Project Makefile
# Builds the complete SAP Virtual Machine system with debugger and test suite

# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra -Werror -std=c99 -pedantic -O2 -g
LDFLAGS = -lm

# Source directories and files
SRCDIR = .
OBJDIR = obj
BINDIR = bin

# Core VM sources
VM_SOURCES = sap_vm.c sap_vm_debug_support.c
VM_OBJECTS = $(VM_SOURCES:%.c=$(OBJDIR)/%.o)

# Debugger sources (includes VM core + samples)
DEBUG_SOURCES = sap_vm_debug.c sap_vm_samples.c $(VM_SOURCES)
DEBUG_OBJECTS = $(DEBUG_SOURCES:%.c=$(OBJDIR)/%.o)

# Test suite sources (includes VM core + samples)
TEST_SOURCES = sap_vm_test.c sap_vm_samples.c $(VM_SOURCES)
TEST_OBJECTS = $(TEST_SOURCES:%.c=$(OBJDIR)/%.o)

# Header files for dependency tracking
HEADERS = sap_vm.h sap_vm_config.h sap_vm_samples.h

# Target executables
DEBUGGER = $(BINDIR)/sap_vm_debug
TEST_SUITE = $(BINDIR)/sap_vm_test

# Default target
.PHONY: all
all: $(DEBUGGER) $(TEST_SUITE)

# Create directories
$(OBJDIR):
	@mkdir -p $(OBJDIR)

$(BINDIR):
	@mkdir -p $(BINDIR)

# Build debugger
$(DEBUGGER): $(DEBUG_OBJECTS) | $(BINDIR)
	@echo "Linking debugger..."
	$(CC) $(DEBUG_OBJECTS) -o $@ $(LDFLAGS)
	@echo "Built SAP VM Debugger: $@"

# Build test suite
$(TEST_SUITE): $(TEST_OBJECTS) | $(BINDIR)
	@echo "Linking test suite..."
	$(CC) $(TEST_OBJECTS) -o $@ $(LDFLAGS)
	@echo "Built SAP VM Test Suite: $@"

# Compile source files to object files
$(OBJDIR)/%.o: $(SRCDIR)/%.c $(HEADERS) | $(OBJDIR)
	@echo "Compiling $<..."
	$(CC) $(CFLAGS) -c $< -o $@

# Run tests
.PHONY: test
test: $(TEST_SUITE)
	@echo "Running SAP VM Test Suite..."
	@echo "=============================="
	./$(TEST_SUITE)

# Run debugger
.PHONY: debug
debug: $(DEBUGGER)
	@echo "Starting SAP VM Debugger..."
	@echo "Type 'help' for commands, 'quit' to exit"
	@echo "=========================================="
	./$(DEBUGGER)

# Quick test of specific sample programs
.PHONY: test-samples
test-samples: $(DEBUGGER)
	@echo "Testing sample programs..."
	@echo "=========================="
	@echo "Testing Fibonacci (should output F(10) = 55):"
	@echo -e "load fib\nrun\nquit" | ./$(DEBUGGER) | grep -A5 -B5 "55\|Final"
	@echo ""
	@echo "Testing Factorial (should output 5! = 120):"
	@echo -e "load fact\nrun\nquit" | ./$(DEBUGGER) | grep -A5 -B5 "120\|Final"

# Build with debug symbols and no optimization
.PHONY: debug-build
debug-build: CFLAGS = -Wall -Wextra -std=c99 -pedantic -g -O0 -DDEBUG
debug-build: clean all

# Build optimized release version
.PHONY: release
release: CFLAGS = -Wall -Wextra -Werror -std=c99 -pedantic -O3 -DNDEBUG -s
release: clean all
	@echo "Built optimized release version"

# Static analysis with additional warnings
.PHONY: analyze
analyze: CFLAGS += -Wshadow -Wcast-align -Wunused -Wpedantic -Wconversion -Wsign-conversion
analyze: clean all

# Memory check with valgrind (if available)
.PHONY: memcheck
memcheck: $(TEST_SUITE)
	@if command -v valgrind >/dev/null 2>&1; then \
		echo "Running memory check..."; \
		valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./$(TEST_SUITE); \
	else \
		echo "Valgrind not found, skipping memory check"; \
	fi

# Install to system (optional)
PREFIX ?= /usr/local
.PHONY: install
install: $(DEBUGGER) $(TEST_SUITE)
	install -d $(PREFIX)/bin
	install -m 755 $(DEBUGGER) $(PREFIX)/bin/sap-vm-debug
	install -m 755 $(TEST_SUITE) $(PREFIX)/bin/sap-vm-test
	@echo "Installed SAP VM to $(PREFIX)/bin/"

# Uninstall from system
.PHONY: uninstall
uninstall:
	rm -f $(PREFIX)/bin/sap-vm-debug
	rm -f $(PREFIX)/bin/sap-vm-test
	@echo "Uninstalled SAP VM from $(PREFIX)/bin/"

# Generate documentation (if doxygen available)
.PHONY: docs
docs:
	@if command -v doxygen >/dev/null 2>&1; then \
		echo "Generating documentation..."; \
		doxygen Doxyfile 2>/dev/null || echo "Doxygen config not found, skipping docs"; \
	else \
		echo "Doxygen not found, skipping documentation"; \
	fi

# Package source for distribution
.PHONY: dist
dist: clean
	@VERSION=$$(date +%Y%m%d); \
	DISTDIR="sap-vm-$$VERSION"; \
	mkdir -p "$$DISTDIR"; \
	cp *.c *.h Makefile README* LICENSE* "$$DISTDIR/" 2>/dev/null || true; \
	tar -czf "$$DISTDIR.tar.gz" "$$DISTDIR"; \
	rm -rf "$$DISTDIR"; \
	echo "Created distribution: $$DISTDIR.tar.gz"

# Show build information
.PHONY: info
info:
	@echo "SAP VM Project Build Information"
	@echo "==============================="
	@echo "Compiler: $(CC)"
	@echo "Flags: $(CFLAGS)"
	@echo "Sources: $(words $(DEBUG_SOURCES)) files"
	@echo "Targets: debugger, test suite"
	@echo ""
	@echo "Available targets:"
	@echo "  all          - Build debugger and test suite (default)"
	@echo "  test         - Build and run test suite"
	@echo "  debug        - Build and run debugger"
	@echo "  test-samples - Quick test of sample programs"
	@echo "  debug-build  - Build with debug symbols"
	@echo "  release      - Build optimized release"
	@echo "  analyze      - Build with extra warnings"
	@echo "  memcheck     - Run with valgrind memory check"
	@echo "  clean        - Remove build files"
	@echo "  install      - Install to system"
	@echo "  dist         - Create source distribution"

# Clean build files
.PHONY: clean
clean:
	@echo "Cleaning build files..."
	rm -rf $(OBJDIR) $(BINDIR)

# Full clean including any generated files
.PHONY: distclean
distclean: clean
	rm -f *.o *.a *.so core core.* gmon.out
	rm -f sap-vm-*.tar.gz
	rm -rf doc/ docs/ html/

# Dependencies for object files
$(OBJDIR)/sap_vm.o: sap_vm.c sap_vm.h sap_vm_config.h
$(OBJDIR)/sap_vm_debug_support.o: sap_vm_debug_support.c sap_vm.h sap_vm_config.h
$(OBJDIR)/sap_vm_debug.o: sap_vm_debug.c sap_vm.h sap_vm_config.h sap_vm_samples.h
$(OBJDIR)/sap_vm_samples.o: sap_vm_samples.c sap_vm.h sap_vm_config.h sap_vm_samples.h
$(OBJDIR)/sap_vm_test.o: sap_vm_test.c sap_vm.h sap_vm_config.h sap_vm_samples.h

# Help target
.PHONY: help
help: info
