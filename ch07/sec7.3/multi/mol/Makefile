CC = gcc
CFLAGS = -Wall -g -std=c99

OBJS = mol_value.o mol_env.o mol_ast.o mol_eval.o mol_lexer.o mol_parser.o main.o

all: mol

mol: $(OBJS)
	$(CC) $(CFLAGS) -o mol $(OBJS)

%.o: %.c mol.h
	$(CC) $(CFLAGS) -c $<

clean:
	rm -f $(OBJS) mol
