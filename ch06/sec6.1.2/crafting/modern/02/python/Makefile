# Makefile for SVG Renderer Testing
# Provides convenient commands for running tests

.PHONY: help test test-unit test-property test-integration test-all test-quick coverage clean fixtures install

# Default target
help:
	@echo "SVG Renderer Test Suite - Available Commands:"
	@echo ""
	@echo "  make install          Install testing dependencies"
	@echo "  make fixtures         Generate test SVG fixtures"
	@echo "  make test             Run all tests with coverage"
	@echo "  make test-quick       Run unit tests only (fast)"
	@echo "  make test-unit        Run unit tests"
	@echo "  make test-property    Run property-based tests"
	@echo "  make test-integration Run integration tests"
	@echo "  make coverage         Generate coverage report"
	@echo "  make coverage-html    Generate HTML coverage report and open"
	@echo "  make clean            Clean test artifacts"
	@echo "  make check            Run all checks (tests + coverage)"
	@echo ""

# Install dependencies
install:
	@echo "Installing testing dependencies..."
	pip install -r requirements-test.txt
	@echo "✓ Dependencies installed"

# Generate test fixtures
fixtures:
	@echo "Generating test fixtures..."
	python create_fixtures.py
	@echo "✓ Test fixtures created"

# Run all tests with coverage
test:
	@echo "Running all tests..."
	python run_tests.py

# Quick unit tests only
test-quick:
	@echo "Running quick unit tests..."
	python run_tests.py --quick

# Run unit tests
test-unit:
	@echo "Running unit tests..."
	python run_tests.py -s test_svg_renderer

# Run property-based tests
test-property:
	@echo "Running property-based tests..."
	python run_tests.py -s test_properties

# Run integration tests
test-integration:
	@echo "Running integration tests..."
	python run_tests.py -s test_integration

# Run all tests (alias)
test-all: test

# Generate coverage report
coverage:
	@echo "Generating coverage report..."
	python run_tests.py
	@echo ""
	@echo "View HTML report: open htmlcov/index.html"

# Generate and open HTML coverage
coverage-html: coverage
	@echo "Opening coverage report in browser..."
	@python -m webbrowser htmlcov/index.html 2>/dev/null || \
	 open htmlcov/index.html 2>/dev/null || \
	 xdg-open htmlcov/index.html 2>/dev/null || \
	 echo "Please open htmlcov/index.html manually"

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf test_fixtures/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -f .hypothesis
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	@echo "✓ Cleaned"

# Run all checks
check: clean fixtures test coverage-html
	@echo ""
	@echo "✓ All checks passed!"

# Setup everything
setup: install fixtures
	@echo ""
	@echo "✓ Setup complete! Run 'make test' to run tests."

# Pytest-specific targets
pytest:
	@echo "Running tests with pytest..."
	pytest -v

pytest-cov:
	@echo "Running pytest with coverage..."
	pytest --cov=svg_renderer --cov-report=html --cov-report=term

pytest-parallel:
	@echo "Running pytest in parallel..."
	pytest -n auto

# Verbose test output
test-verbose:
	@echo "Running tests with verbose output..."
	python run_tests.py -v 2

# Quiet test output
test-quiet:
	@echo "Running tests quietly..."
	python run_tests.py -v 0

# Stop on first failure
test-failfast:
	@echo "Running tests (stop on first failure)..."
	python run_tests.py -f

# Run specific test
test-specific:
	@echo "Usage: make test-specific TEST=test_svg_renderer.TestColor"
	@echo "Running: $(TEST)"
	python run_tests.py -s $(TEST)

# Watch for changes and re-run tests
watch:
	@echo "Watching for changes (requires: pip install pytest-watch)..."
	ptw -- -v

# Lint the test code
lint:
	@echo "Linting test code..."
	@command -v flake8 >/dev/null 2>&1 && flake8 test_*.py || echo "Install flake8: pip install flake8"

# Type check the test code
typecheck:
	@echo "Type checking..."
	@command -v mypy >/dev/null 2>&1 && mypy test_*.py || echo "Install mypy: pip install mypy"

# Format test code
format:
	@echo "Formatting code with black..."
	@command -v black >/dev/null 2>&1 && black test_*.py create_fixtures.py run_tests.py || echo "Install black: pip install black"

# Show test statistics
stats:
	@echo "Test Statistics:"
	@echo "================"
	@echo -n "Unit tests: "
	@grep -r "def test_" test_svg_renderer.py | wc -l
	@echo -n "Property tests: "
	@grep -r "def test_" test_properties.py | wc -l
	@echo -n "Integration tests: "
	@grep -r "def test_" test_integration.py | wc -l
	@echo -n "Total test methods: "
	@grep -r "def test_" test_*.py | wc -l

# Benchmark tests
benchmark:
	@echo "Running performance benchmarks..."
	pytest test_integration.py::TestMemoryAndPerformance -v

# Generate test report
report:
	@echo "Generating test report..."
	pytest --html=test_report.html --self-contained-html
	@echo "Report generated: test_report.html"
