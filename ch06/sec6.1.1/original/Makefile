
PYTHON := python3
TEST_FILE := test_vm.py

all: test

test:
	$(PYTHON) -m unittest $(TEST_FILE)

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -exec rm -f {} +

.PHONY: all test clean
