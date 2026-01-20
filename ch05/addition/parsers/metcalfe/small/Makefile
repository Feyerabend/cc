# Makefile

.PHONY: all clean run

SRC=small.mc
BIN=small.b
TEST=small.test
OUT=small.out

all: $(BIN)

$(BIN): $(SRC)
	python3 met.py -v -i $(SRC) -o $(BIN)

run: $(BIN)
	python3 calfe.py -v -t $(TEST) -i $(BIN) -o $(OUT)

clean:
	rm -f $(BIN) $(OUT)