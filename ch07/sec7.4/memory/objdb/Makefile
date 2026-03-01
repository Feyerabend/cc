# =================
# Makefile — objdb
# =================

CC      = gcc
CFLAGS  = -Wall -Wextra -std=c99
DBGFLAGS= -g -fsanitize=address,undefined
SRCS    = objdb.c
HDRS    = objdb.h

# targets

.PHONY: all clean debug

all: objdb objdb_repl

objdb: main.c $(SRCS) $(HDRS)
	$(CC) $(CFLAGS) -o $@ main.c $(SRCS)

objdb_repl: repl.c $(SRCS) $(HDRS)
	$(CC) $(CFLAGS) -o $@ repl.c $(SRCS)

debug: main.c $(SRCS) $(HDRS)
	$(CC) $(CFLAGS) $(DBGFLAGS) -o objdb_dbg main.c $(SRCS)
	$(CC) $(CFLAGS) $(DBGFLAGS) -o objdb_repl_dbg repl.c $(SRCS)

clean:
	rm -f objdb objdb_repl objdb_dbg objdb_repl_dbg
