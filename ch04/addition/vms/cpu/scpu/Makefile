# Compiler to use
CC = gcc

# Compiler flags
CFLAGS = -Wall -Wextra -g -std=c99

# Target executable name
TARGET = test_cpu

# Source files
SOURCES = cpu.c test_cpu.c

# Object files (automatically derived from sources)
OBJECTS = $(SOURCES:.c=.o)

# Header files
HEADERS = cpu.h

# Default target
all: $(TARGET)

# Link object files to create the executable
$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $(TARGET)

# Compile source files to object files
%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

# Clean up generated files
clean:
	rm -f $(OBJECTS) $(TARGET)

# Phony targets (not actual files)
.PHONY: all clean
