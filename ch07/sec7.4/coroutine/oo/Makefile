CC = gcc

# suppress warnings:
CFLAGS = -Wall -Wextra -std=c99 -D_POSIX_C_SOURCE=200809L -Wno-switch
# or do not:
# CFLAGS = -Wall -Wextra -std=c99

TARGET = oop_coroutines

all: $(TARGET)

$(TARGET): oop_coroutines.c
	$(CC) $(CFLAGS) -o $(TARGET) oop_coroutines.c

clean:
	rm -f $(TARGET)

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run
