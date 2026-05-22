CC      = cc
CFLAGS  = -std=c11 -Wall -Wextra -O2 -I../core
TARGET  = llang

CORE_SRCS = ../core/term.c ../core/eval.c ../core/parse.c \
            ../core/check.c ../core/defs.c
LANG_SRCS = main.c

SRCS = $(LANG_SRCS) $(CORE_SRCS)

$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) -o $@ $(SRCS)

clean:
	rm -f $(TARGET)

.PHONY: clean
