# Makefile for Aspect-Oriented Language

CC = gcc
CFLAGS = -Wall -O2
LIBS = -lm

all: aop_driver aspect_demo

aop_driver: aop_main.c
	$(CC) $(CFLAGS) -o aop aop_main.c

clean_version: aspect_lang_v4_clean.c
	$(CC) $(CFLAGS) -o aspect_v4 aspect_lang_v4_clean.c $(LIBS)

clean:
	rm -f aop aspect_demo aspect_v4 *.o

test: aop_driver
	@echo "Testing file checker..."
	./aop -c sample1_logging.aop
	@echo ""
	@echo "Testing version info..."
	./aop -v

demo: aspect_demo
	@echo "Running aspect-oriented demo..."
	./aspect_demo

samples: aop_driver
	@echo "Checking all sample files..."
	@for sample in sample*.aop; do \
		echo ""; \
		./aop -c $$sample; \
	done

help:
	@echo "Aspect-Oriented Language Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all            - Build everything (default)"
	@echo "  aop_driver     - Build file/REPL driver"
	@echo "  clean_version  - Build clean version (v4)"
	@echo "  clean          - Remove built files"
	@echo "  test           - Test the driver"
	@echo "  demo           - Run aspect demo"
	@echo "  samples        - Check all sample files"
	@echo ""
	@echo "Usage examples:"
	@echo "  make              # Build everything"
	@echo "  make test         # Test the driver"
	@echo "  make demo         # Run demo"
	@echo "  ./aop -h          # Show driver help"
	@echo "  ./aop -i          # Start REPL"
	@echo "  ./aop file.aop    # Run file"
	@echo "  ./aspect_demo     # Run integrated demo"

.PHONY: all clean test demo samples help
