CC      = cc
CFLAGS  = -std=c11 -Wall -Wextra -O2 -I../core

TARGET  = llang
TARGET_RL = llang-rl

CORE_SRCS = ../core/term.c ../core/eval.c ../core/parse.c \
            ../core/check.c ../core/defs.c ../core/elab.c

LANG_SRCS = main.c node.c reduce.c bridge.c

SRCS = $(LANG_SRCS) $(CORE_SRCS)

# Default: plain build (no readline dependency)
$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) -o $@ $(SRCS)

# Readline build: uses macOS libedit (readline-compatible, ships with macOS)
# Gives: arrow keys, history (up/down), Ctrl-A/E/K/U line editing.
$(TARGET_RL): $(SRCS)
	$(CC) $(CFLAGS) -DHAVE_READLINE -o $@ $(SRCS) -ledit

clean:
	rm -f $(TARGET) $(TARGET_RL)

.PHONY: clean
