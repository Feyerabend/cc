.PHONY: all clean

all: sample.d

sample.d: sample.b disasm.py
	clear
	python3 disasm.py -i sample.b -o sample.d

clean:
	rm -f sample.d