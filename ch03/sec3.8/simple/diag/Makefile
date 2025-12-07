.PHONY: all run clean

PYTHON = python3
VM = dvm.py
DIAG = diag.py
INPUT = sample.b
LOG = log.txt

all: run

run: $(INPUT) $(VM) $(DIAG)
	clear
	$(PYTHON) $(VM) --input $(INPUT) > $(LOG)
	$(PYTHON) $(DIAG) < $(LOG)

clean:
	rm -f $(LOG) *.pyc