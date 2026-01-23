CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -g
TARGET = css_parser
OBJS = main.o css_parser.o arena.o

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS)

main.o: main.c css_parser.h arena.h
	$(CC) $(CFLAGS) -c main.c

css_parser.o: css_parser.c css_parser.h arena.h
	$(CC) $(CFLAGS) -c css_parser.c

arena.o: arena.c arena.h
	$(CC) $(CFLAGS) -c arena.c

clean:
	rm -f $(TARGET) $(OBJS)

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run
