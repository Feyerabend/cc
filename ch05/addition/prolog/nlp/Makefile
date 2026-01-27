# Makefile for Natural Language Parser (Prolog)
# Simple commands for testing and running the NLP parser

.PHONY: help demo test examples clean interactive run-mprolog run-sprolog

# Default target
help:
	@echo "Natural Language Parser - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make demo         - Run interactive NLP parser demo"
	@echo "  make test         - Run test suite"
	@echo "  make examples     - Show all example grammars"
	@echo "  make interactive  - Start interactive REPL"
	@echo "  make run-mprolog  - Run mprolog tests"
	@echo "  make all          - Run everything"
	@echo "  make clean        - Remove generated files"
	@echo ""
# minimal target is commented out for now

# Run the interactive demo
demo:
	@echo "Running NLP Parser Demo..."
	@echo ""
	@python nlp_prolog.py <<< "demo\nquit"

# Run test suite
test:
	@echo "Running Test Suite..."
	@echo ""
	@python test_nlp_parser.py

# Show examples
examples:
	@echo "Running Example Grammars..."
	@echo ""
	@python nlp_examples.py

# Interactive mode
interactive:
	@echo "Starting Interactive NLP Parser..."
	@echo "Type 'demo' to see examples, 'quit' to exit"
	@echo ""
	@python nlp_prolog.py

# Run mprolog tests
run-mprolog:
	@echo "Running Mini-Prolog Tests..."
	@echo ""
	@python mprolog.py --test

# Run minimal grammar example
#minimal:
#	@echo "Running Minimal Grammar Example..."
#	@echo ""
#	@python minimal_grammar.py

# Run all demos and tests
all: demo test examples
	@echo ""
	@echo "All demos and tests completed!"

# Clean generated files
clean:
	@echo "Cleaning up..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"

# Quick start guide
quickstart:
	@echo "Quick Start Guide"
	@echo "================="
	@echo ""
	@echo "1. See what the parser can do:"
	@echo "   make demo"
	@echo ""
	@echo "2. Run tests to verify everything works:"
	@echo "   make test"
	@echo ""
	@echo "3. Try parsing your own sentences:"
	@echo "   make interactive"
	@echo "   > parse the cat chases the mouse"
	@echo ""
	@echo "4. See more grammar examples:"
	@echo "   make examples"
	@echo ""

# Parse a specific sentence (example usage: make parse SENTENCE="the cat sleeps")
parse:
	@python -c "from nlp_prolog import create_advanced_grammar; \
	            db = create_advanced_grammar(); \
	            sentence = '$(SENTENCE)'.split(); \
	            solutions = db.parse_sentence('sentence', sentence); \
	            print('Parsing:', sentence); \
	            print('Valid!' if solutions else 'Invalid!')"
