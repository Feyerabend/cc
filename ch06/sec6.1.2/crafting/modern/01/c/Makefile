# Makefile for SVG Renderer
# Clean, professional build system

CC = gcc
CFLAGS = -Wall -Wextra -Wpedantic -Wconversion -Wshadow -O2 -std=c99
LDFLAGS = -lm

# Source files
SOURCES = svg_renderer.c demo.c
OBJECTS = $(SOURCES:.c=.o)
EXECUTABLE = svg_demo

# Header files
HEADERS = svg_renderer.h

.PHONY: all clean run

all: $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS)
	@echo "Linking $@..."
	@$(CC) $(OBJECTS) -o $@ $(LDFLAGS)
	@echo "Build complete!"

%.o: %.c $(HEADERS)
	@echo "Compiling $<..."
	@$(CC) $(CFLAGS) -c $< -o $@

run: $(EXECUTABLE)
	@echo "Running demo..."
	@./$(EXECUTABLE)

clean:
	@echo "Cleaning up..."
	@rm -f $(OBJECTS) $(EXECUTABLE)
	@rm -f *.ppm
	@echo "Clean complete!"

# Help target
help:
	@echo "SVG Renderer Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all     - Build the executable (default)"
	@echo "  run     - Build and run the demo"
	@echo "  clean   - Remove generated files"
	@echo "  help    - Show this help message"
