CC      = gcc
CFLAGS  = -std=c11 -Wall -Wextra -Wpedantic -O2 -g

CORE_SRCS  = trit.c setun.c setun70.c
CORE_OBJS  = $(CORE_SRCS:.c=.o)

all: setun dssp

setun: $(CORE_OBJS) main.o
	$(CC) $(CFLAGS) -o $@ $^

dssp: $(CORE_OBJS) dssp.o dssp_main.o
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

trit.o:      trit.c trit.h
setun.o:     setun.c setun.h trit.h
setun70.o:   setun70.c setun70.h trit.h
main.o:      main.c setun.h setun70.h trit.h
dssp.o:      dssp.c dssp.h setun70.h trit.h
dssp_main.o: dssp_main.c dssp.h setun70.h trit.h

clean:
	rm -f $(CORE_OBJS) main.o dssp.o dssp_main.o setun dssp

.PHONY: all clean
