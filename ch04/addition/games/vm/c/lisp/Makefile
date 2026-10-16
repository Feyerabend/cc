# Builds the PC version of the Lisp game VM, for trying games and running
# the tests without a Pico. The Pico version is built with CMake.

CC      ?= cc
CFLAGS  ?= -std=c11 -Wall -Wextra -pedantic -O2 -g

SRCS = lisp_vm.c lisp_builtins.c lisp_game.c host/display_host.c host/lisp_host.c
HDRS = lisp_vm.h lisp_game.h display.h font5x8.h host/display_host.h

.PHONY: all test clean

all: lisp_host

lisp_host: $(SRCS) $(HDRS)
	$(CC) $(CFLAGS) -o $@ $(SRCS)

# The stress build collects garbage before every allocation, which
# makes any value the collector fails to find show up at once.
lisp_host_stress: $(SRCS) $(HDRS)
	$(CC) $(CFLAGS) -DLISP_GC_STRESS -o $@ $(SRCS)

test: lisp_host lisp_host_stress
	sh tests/run.sh ./lisp_host
	sh tests/run.sh ./lisp_host_stress

clean:
	rm -f lisp_host lisp_host_stress tests/*.out *.ppm
