CC = gcc
CFLAGS = -Wall -std=c99 -I./include
PYTH = python3

SRCDIR = src
OBJDIR = obj
SCRIPTS = ./tools
TESTDIR = ./tests
SAMPLESDIR = ./samples
BINDIR = .
OUTPUTDIR = ./output
TOKENSDIR = ./tokens
ASTDIR = ./ast
SYMBOLDIR = ./table
TOOLSDIR = ./tools

SOURCES = $(wildcard $(SRCDIR)/*.c)
OBJECTS = $(patsubst $(SRCDIR)/%.c, $(OBJDIR)/%.o, $(SOURCES))
TARGET = $(BINDIR)/main

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $@

$(OBJDIR)/%.o: $(SRCDIR)/%.c
	@mkdir -p $(OBJDIR)
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -rf $(OBJDIR) $(TARGET) $(OUTPUTDIR) $(TOKENSDIR) $(ASTDIR) $(SYMBOLDIR)

samples: $(TARGET)
	@mkdir -p $(ASTDIR)  # 'ast' directory exists
	@mkdir -p $(OUTPUTDIR)  # 'output' directory exists
	@mkdir -p $(TOKENSDIR)  # 'token' directory exists
	@for file in $(SAMPLESDIR)/sample*.pas; do \
		base=$$(basename $$file .pas); \
		tokens_output="$(TOKENSDIR)/$$base.token"; \
		annotated_tokens_output="$(TOKENSDIR)/$$base.antok"; \
		ast_output="$(ASTDIR)/$$base.json"; \
		echo "\n- - - - - - -"; \
		echo "Running $$file -> $$tokens_output, $$annotated_tokens_output, $$ast_output"; \
		./main $$file $$tokens_output $$annotated_tokens_output $$ast_output; \
	done

table: $(SCRIPTS)/symbol.py
	@mkdir -p $(SYMBOLDIR)  # 'table' directory exists
	@for file in $(ASTDIR)/*.json; do \
		base=$$(basename $$file .json); \
		symbol_output="$(SYMBOLDIR)/$$base.symbol"; \
		echo "Generating symbol table for $$file -> $$symbol_output"; \
		$(PYTH) $(SCRIPTS)/symbol.py -i $$file -o $$symbol_output; \
	done

valid: $(TOOLSDIR)/ast_checker.py
	@for file in $(ASTDIR)/*.json; do \
		base=$$(basename $$file .json); \
		echo "Check $$file"; \
		$(PYTH) $(TOOLSDIR)/ast_checker.py $$file; \
	done

interpret: $(TOOLSDIR)/ast_interpreter.py
	@for file in $(ASTDIR)/*.json; do \
		base=$$(basename $$file .json); \
		echo "Interpreting $$file"; \
		$(PYTH) $(TOOLSDIR)/ast_interpreter.py $$file; \
	done


# make -- compiles
# make clean -- clean up
# make samples -- make outputs: here from samples to tokens
# make table -- generate symbol tables from samples, assume ast
# make interpret -- interpret program as AST, assume ast
