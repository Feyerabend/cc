# Makefile

.PHONY: all clean run

SRC=etf.mc
BIN=etf.b
TEST=etf.test
OUT=etf.out

all: $(BIN)

$(BIN): $(SRC)
	python3 met.py -v -i $(SRC) -o $(BIN)

run: $(BIN)
	python3 calfe.py -v -t $(TEST) -i $(BIN) -o $(OUT)

clean:
	rm -f $(BIN) $(OUT)