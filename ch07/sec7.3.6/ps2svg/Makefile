
# Makefile - ps2svg  PostScript --> SVG transpiler
#
# Usage:
#   make              build ./ps2svg
#   make debug        build with -g -fsanitize=address,undefined
#   make check        build and run the full test suite
#   make clean        remove all build artefacts
#   make help         print this reference
#
# Override variables on the command line:
#   CC=clang make
#   CFLAGS_EXTRA="-DDEBUG_VERBOSE" make check

#  Toolchain 

CC     ?= gcc
CFLAGS  = -std=c11 -O2 -Wall -Wextra \
          -Wno-unused-function -Wno-unused-result \
          $(CFLAGS_EXTRA)
LDFLAGS =
LIBS    = -lm

#  Source files 

SRCS   = ps_parser.c ps_codegen.c ps2svg.c
OBJS   = $(SRCS:.c=.o)
TARGET = ps2svg

#  Primary targets 

.PHONY: all debug check clean help

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LIBS)
	@echo "Built: ./$@"

# The parser also has its own main() (for use as a standalone tool).
# Suppress it when compiling as a library unit for ps2svg.
ps_parser.o: ps_parser.c ps_ast.h
	$(CC) $(CFLAGS) -DPS_PARSER_LIB_MODE -c -o $@ $<

ps_codegen.o: ps_codegen.c ps_ast.h ps_codegen.h
	$(CC) $(CFLAGS) -c -o $@ $<

ps2svg.o: ps2svg.c ps_ast.h ps_codegen.h
	$(CC) $(CFLAGS) -c -o $@ $<

#  Debug build 

debug: CFLAGS = -std=c11 -g -O0 -Wall -Wextra \
                -Wno-unused-function -Wno-unused-result \
                -fsanitize=address,undefined \
                -fno-omit-frame-pointer \
                $(CFLAGS_EXTRA)
debug: LIBS += -fsanitize=address,undefined
debug: $(TARGET)

#  Test suite 
#
# Layout expected under $(TEST_DIR):
#   pass/  *.ps files that must parse and produce valid SVG
#   fail/  *.ps files that must be rejected by the parser
#
# Each pass-case SVG is validated with xmllint if available.

TEST_DIR = tests

check: $(TARGET)
	@$(MAKE) --no-print-directory _run_tests

_run_tests:
	@PASS=0; FAIL=0; TOTAL=0; \
	PASS_DIR="$(TEST_DIR)/pass"; \
	FAIL_DIR="$(TEST_DIR)/fail"; \
	XMLLINT=$$(command -v xmllint 2>/dev/null || echo ""); \
	\
	if [ ! -d "$$PASS_DIR" ] && [ ! -d "$$FAIL_DIR" ]; then \
	    echo "ERROR: test directory '$(TEST_DIR)' not found."; \
	    echo "       Unzip ps_tests.zip here first:"; \
	    echo "         unzip ps_tests.zip"; \
	    exit 1; \
	fi; \
	\
	echo ""; \
	echo "=== ps2svg test suite ==="; \
	echo "    Parser: ./$(TARGET)"; \
	echo "    Tests:  $(TEST_DIR)/"; \
	echo ""; \
	\
	if [ -d "$$PASS_DIR" ]; then \
	    echo "[ Should PASS ]"; \
	    for f in "$$PASS_DIR"/*.ps; do \
	        [ -f "$$f" ] || continue; \
	        TOTAL=$$((TOTAL+1)); \
	        label=$$(basename "$$f"); \
	        tmpsvg=$$(mktemp /tmp/ps2svg_check_XXXXXX.svg); \
	        if ./$(TARGET) "$$f" "$$tmpsvg" >/dev/null 2>&1; then \
	            if [ -n "$$XMLLINT" ] && ! $$XMLLINT --noout "$$tmpsvg" 2>/dev/null; then \
	                printf "  FAIL  %-42s  (invalid SVG output)\n" "$$label"; \
	                FAIL=$$((FAIL+1)); \
	            else \
	                printf "  PASS  %s\n" "$$label"; \
	                PASS=$$((PASS+1)); \
	            fi; \
	        else \
	            printf "  FAIL  %-42s  (unexpected parse error)\n" "$$label"; \
	            FAIL=$$((FAIL+1)); \
	        fi; \
	        rm -f "$$tmpsvg"; \
	    done; \
	    echo ""; \
	fi; \
	\
	if [ -d "$$FAIL_DIR" ]; then \
	    echo "[ Should FAIL ]"; \
	    for f in "$$FAIL_DIR"/*.ps; do \
	        [ -f "$$f" ] || continue; \
	        TOTAL=$$((TOTAL+1)); \
	        label=$$(basename "$$f"); \
	        tmpsvg=$$(mktemp /tmp/ps2svg_check_XXXXXX.svg); \
	        if ./$(TARGET) "$$f" "$$tmpsvg" >/dev/null 2>&1; then \
	            printf "  XPAS  %-42s  (should have been rejected)\n" "$$label"; \
	            FAIL=$$((FAIL+1)); \
	        else \
	            printf "  RJCT  %s\n" "$$label"; \
	            PASS=$$((PASS+1)); \
	        fi; \
	        rm -f "$$tmpsvg"; \
	    done; \
	    echo ""; \
	fi; \
	\
	echo "=== Results: $$PASS/$$TOTAL correct  ($$FAIL unexpected) ==="; \
	echo ""; \
	test $$FAIL -eq 0

#  Clean 

clean:
	rm -f $(OBJS) $(TARGET)
	@echo "Cleaned."

#  Help 

help:
	@echo ""
	@echo "  make              build ./$(TARGET)"
	@echo "  make debug        build with -g -fsanitize=address,undefined"
	@echo "  make check        build + run test suite (needs tests/ directory)"
	@echo "  make clean        remove build artefacts"
	@echo "  make help         show this message"
	@echo ""
	@echo "  Override toolchain:   CC=clang make"
	@echo "  Add compiler flags:   CFLAGS_EXTRA=-DFOO make"
	@echo ""
