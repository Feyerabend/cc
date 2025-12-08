# 
PYTHON := python3
TEST_DIR := tests

all: test

# run all unit tests
test:
	$(PYTHON) -m unittest discover -s $(TEST_DIR)

# clean up
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +
	rm -rf .coverage

# 
.PHONY: all test clean
