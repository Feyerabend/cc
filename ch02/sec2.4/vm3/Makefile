CC             = gcc
CFLAGS         = -Wall
LDFLAGS        =
OBJFILES       = main.o vm3.o
TARGET         = main
PYTHON_SCRIPT  = asm.py

FILE	?= input
INPUT_FILE	= $(FILE).a
OUTPUT_FILE	= $(FILE).b

all: python_run $(TARGET) run_c_program

$(TARGET): $(OBJFILES)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJFILES) $(LDFLAGS)

python_run:
	python3 $(PYTHON_SCRIPT) -v -i $(INPUT_FILE) -o $(OUTPUT_FILE)

run_c_program: $(TARGET)
	./$(TARGET) $(OUTPUT_FILE)

clean:
	rm -f $(OBJFILES) $(TARGET) *~
