# Makefile for CPU Simulator

# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra -g -std=c99

# Source files and output executable
SOURCES = cpu.c demo.c
OBJECTS = $(SOURCES:.c=.o)
EXECUTABLE = cpu_simulator

# Header files
HEADERS = cpu.h

# Default target
all: $(EXECUTABLE)

# Link object files to create executable
$(EXECUTABLE): $(OBJECTS)
	$(CC) $(OBJECTS) -o $(EXECUTABLE)

# Compile source files to object files
%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

# Clean up generated files
clean:
	rm -f $(OBJECTS) $(EXECUTABLE)

# Phony targets
.PHONY: all clean