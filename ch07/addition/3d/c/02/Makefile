CC = gcc
CFLAGS = -Wall -g
LDFLAGS = -lm
SOURCES = main.c model.c rendering.c rmath.c
OBJECTS = $(SOURCES:.c=.o)
EXEC = renderer
IMAGES = *.pam
PNGS = *.png
GIFS = *.gif
PYTHON = python3
MERGE_SCRIPT = pam7merge.py

# Default target: compile, link, run, and merge
all: $(EXEC) run merge

# Compile and link to build the executable
$(EXEC): $(OBJECTS)
	$(CC) $(OBJECTS) -o $(EXEC) $(LDFLAGS)

# Compile source files to object files
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Run the renderer executable
run: $(EXEC)
	./$(EXEC)

# Merge PAM files using the Python script
merge:
	$(PYTHON) $(MERGE_SCRIPT)

# Clean up generated files
clean:
	rm -f $(OBJECTS) $(EXEC) $(IMAGES)

cleaner:
	rm -f $(OBJECTS) $(EXEC) $(IMAGES) $(PNGS) $(GIFS)


# Phony targets
.PHONY: all run merge clean cleaner
