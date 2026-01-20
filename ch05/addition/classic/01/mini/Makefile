# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra -g
LDFLAGS = 

# Directories
SRC_DIR = src
OBJ_DIR = obj
BIN_DIR = bin

# Target executable
TARGET = $(BIN_DIR)/program

# Source and object files
SRC_FILES = $(wildcard $(SRC_DIR)/*.c)
OBJ_FILES = $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRC_FILES))

# Default target
all: $(TARGET)

# Link the object files into the final executable
$(TARGET): $(OBJ_FILES)
	@mkdir -p $(BIN_DIR)
	$(CC) $(LDFLAGS) -o $@ $^

# Compile source files into object files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c -o $@ $<

# Build and run mini.c
run: mini
	./mini

mini: src/mini.c
	$(CC) $(CFLAGS) -o mini src/mini.c

# Clean up build artifacts
clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR) mini

# Phony targets
.PHONY: all clean run mini
