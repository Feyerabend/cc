CC = gcc
CFLAGS = -Wall -g -O2
LDFLAGS = -lm
SOURCES = main.c model.c rendering.c rmath.c
OBJECTS = $(SOURCES:.c=.o)
EXEC = renderer
TEXTURE_PAM = texture.pam
OUTPUT_PAM = frame*.pam
PNGS = *.png
GIFS = *.gif
PYTHON = python3
MERGE_SCRIPT = pam7merge.py

# Default target: build the executable
all: $(EXEC) run merge

# Compile and link to build the executable
$(EXEC): $(OBJECTS)
	$(CC) $(OBJECTS) -o $(EXEC) $(LDFLAGS)

# Compile source files to object files
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Run the renderer with a texture file
run: $(EXEC)
	@if [ -f $(TEXTURE_PAM) ]; then \
		./$(EXEC) $(TEXTURE_PAM); \
	else \
		echo "Error: Texture file $(TEXTURE_PAM) not found"; \
		exit 1; \
	fi

# Merge PAM files using the Python script
merge:
	$(PYTHON) $(MERGE_SCRIPT)

# Clean up generated files
clean:
	rm -f $(OBJECTS) $(EXEC) $(OUTPUT_PAM)

# Clean up everything, including PNGs and GIFs
cleaner:
	rm -f $(OBJECTS) $(EXEC) $(OUTPUT_PAM) $(PNGS) $(GIFS)

# Phony targets
.PHONY: all run merge clean cleaner