# Makefile for Advanced Hoare Logic examples
# Each file illustrates one or more sections of ADVANCED.md
#
#   various       -- Sections 1-2: wp, sp, invariants, basic rules
#   linked_list   -- Section 4:    Separation Logic, list reversal, frame rule
#   concurrency   -- Sections 5-6: Owicki-Gries, resource invariants, Rely-Guarantee
#   incorrectness -- Section 7:    Incorrectness Logic, bug witnesses
#   higher_order  -- Section 8:    Higher-order functions, parametric specs

CC     = gcc
CFLAGS = -Wall -Wextra -std=c11 -g

TARGETS = various linked_list concurrency incorrectness higher_order

.PHONY: all clean run

all: $(TARGETS)

various: various.c
	$(CC) $(CFLAGS) -o $@ $<

linked_list: linked_list.c
	$(CC) $(CFLAGS) -o $@ $<

concurrency: concurrency.c
	$(CC) $(CFLAGS) -o $@ $< -lpthread

incorrectness: incorrectness.c
	$(CC) $(CFLAGS) -o $@ $<

higher_order: higher_order.c
	$(CC) $(CFLAGS) -o $@ $<

run: all
	@echo "========== various =========="
	./various
	@echo ""
	@echo "========== linked_list =========="
	./linked_list
	@echo ""
	@echo "========== concurrency =========="
	./concurrency
	@echo ""
	@echo "========== incorrectness =========="
	./incorrectness
	@echo ""
	@echo "========== higher_order =========="
	./higher_order

clean:
	rm -f $(TARGETS)
