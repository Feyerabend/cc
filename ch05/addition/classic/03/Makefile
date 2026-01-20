CC = gcc
CFLAGS = -Wall -std=c99 -I./include

SRCDIR = src
OBJDIR = obj
TESTDIR = ./tests
SAMPLESDIR = ./samples
BINDIR = .
OUTPUTDIR = ./output
TOKENSDIR = ./tokens
ASTDIR = ./ast
SYMBOLDIR = ./table

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

# make -- compiles
# make clean -- clean up
# make samples -- make outputs: here from samples to tokens
