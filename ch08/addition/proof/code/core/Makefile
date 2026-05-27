CC      = cc
CFLAGS  = -std=c11 -Wall -Wextra -O2
TARGET  = lcore
SRCS    = main.c term.c eval.c parse.c check.c defs.c elab.c

$(TARGET): $(SRCS) arena.h term.h eval.h parse.h check.h defs.h
	$(CC) $(CFLAGS) -o $@ $(SRCS)

clean:
	rm -f $(TARGET)

.PHONY: clean
