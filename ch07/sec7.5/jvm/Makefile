test:
	python3 -m pytest tests/ -v

quick:
	python3 quick_test.py

example: Example.class
	python3 main.py Example . -v

Example.class: Example.java
	javac Example.java

clean:
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null; true
	find . -name '*.pyc' -delete 2>/dev/null; true
