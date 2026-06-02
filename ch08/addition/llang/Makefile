CC     = cc
CFLAGS = -std=c11 -Wall -Wextra -O2

# ── NbE kernel (type-checker + evaluator REPL)
CORE_SRCS = main.c term.c eval.c parse.c check.c defs.c elab.c termcheck.c
CORE_HDRS = arena.h term.h eval.h parse.h check.h defs.h elab.h termcheck.h

# ── Core files used by lang (all except main.c which has its own main)
CORE_LIB = term.c eval.c parse.c check.c defs.c elab.c termcheck.c

all: core/lcore lang/llang

core/lcore: $(addprefix core/,$(CORE_SRCS)) $(addprefix core/,$(CORE_HDRS))
	$(CC) $(CFLAGS) -o $@ $(addprefix core/,$(CORE_SRCS))

lang/llang: $(addprefix lang/,main.c node.c bridge.c reduce.c) \
            $(addprefix core/,$(CORE_LIB)) $(addprefix core/,$(CORE_HDRS))
	$(CC) $(CFLAGS) -Icore -o $@ \
	    $(addprefix lang/,main.c node.c bridge.c reduce.c) \
	    $(addprefix core/,$(CORE_LIB))

test: core/lcore
	echo ":t" | core/lcore

clean:
	rm -f core/lcore lang/llang

.PHONY: all test clean
