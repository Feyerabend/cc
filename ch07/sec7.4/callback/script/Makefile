CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2 -g
SOURCES = ast.c compiler.c vm.c demo.c
OBJECTS = $(SOURCES:.c=.o)
TARGET = eventscript

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJECTS)

%.o: %.c eventscript.h
	$(CC) $(CFLAGS) -c $<

clean:
	rm -f $(OBJECTS) $(TARGET)

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run
