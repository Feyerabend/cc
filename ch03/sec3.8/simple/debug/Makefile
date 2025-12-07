.PHONY: all run clean

PYTHON = python3
SCRIPT = dvm.py
INPUT = sample.b
OPTIONS = --singlestep true --breakpoints 14,16 --trace true --input $(INPUT)

all: run

run: $(INPUT) $(SCRIPT)
	clear
	$(PYTHON) $(SCRIPT) $(OPTIONS)

clean:
	rm -f *.pyc