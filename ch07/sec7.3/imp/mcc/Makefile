CC = gcc
CFLAGS = -Wall -g -O0

all: minicc run6502 disasm

minicc: minicc.c
	$(CC) $(CFLAGS) -o minicc minicc.c

run6502: run6502.c fake6502.c fake6502.h
	$(CC) $(CFLAGS) -o run6502 run6502.c fake6502.c

disasm: disasm.c
	$(CC) $(CFLAGS) -o disasm disasm.c

test: minicc run6502 disasm
	@echo "Compiling simple.c..."
	./minicc simple.c
	@echo ""
	@echo "Disassembly:"
	./disasm out.bin | head -20
	@echo ""
	@echo "Running on 6502 emulator:"
	./run6502 out.bin

test2: minicc run6502 disasm
	@echo "Compiling test2.c (more complex example)..."
	./minicc test2.c
	@echo ""
	@echo "Running on 6502 emulator:"
	./run6502 out.bin

clean:
	rm -f minicc run6502 disasm out.bin *.o
	rm -Rf *.dSYM

.PHONY: all test test2 clean
