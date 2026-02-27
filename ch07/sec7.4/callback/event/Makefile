CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2
TARGET = event_demo

all: $(TARGET)

$(TARGET): event_lang.o example.o
	$(CC) $(CFLAGS) -o $(TARGET) event_lang.o example.o

event_lang.o: event_lang.c event_lang.h
	$(CC) $(CFLAGS) -c event_lang.c

example.o: example.c event_lang.h
	$(CC) $(CFLAGS) -c example.c

clean:
	rm -f *.o $(TARGET)

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run
