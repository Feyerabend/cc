CC = gcc
CFLAGS = -std=c99 -Wall -O2
TARGET = emu6502

SRCS = main.c fake6502.c
OBJS = $(SRCS:.c=.o)

all: $(TARGET) test.bin

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c fake6502.h
	$(CC) $(CFLAGS) -c $<

test.bin: generate_test.py
	python3 generate_test.py

clean:
	rm -f $(OBJS) $(TARGET) test.bin

clear:
	clear

.PHONY: all clean clear
