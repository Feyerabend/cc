
## Continuous Integration (CI)

Continuous Integration (CI) is a software development practice where code changes are
automatically built, tested, and verified for correctness as soon as they are committed
to a shared repository. This ensures that problems are detected early, before they become
large and costly to fix. CI is a crucial part of modern DevOps workflows, promoting
collaboration, code quality, and faster release cycles.

#### Project

*Adapt the scripts below and install them in your own repository, using more robust and
production-ready code. Additionally, implement the suggested improvements to expand the
YAML script. Take some time to read up on how 'GitHub Actions' work to make the most of
this tool.*

### Example on GitHub

First an example of how CI work on GitHub with a Pyhton script.
A badge react to how the automatic runs work, if it breaks it changes colour.

[![Python CI](https://github.com/Feyerabend/bb/actions/workflows/main.yml/badge.svg)](https://github.com/Feyerabend/bb/actions/workflows/main.yml)

The file 'main.yml' lives in 'bb/.github/workflows/main.yml'.

```yml
name: Python CI

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    # repository code
    - name: Checkout code
      uses: actions/checkout@v4

    # set up
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    # dependencies, if any
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f workbook/ch03/ci/requirements.txt ]; then pip install -r requirements.txt; fi

    # PYTHONPATH (include script's parent directory, if needed)
    - name: Set PYTHONPATH
      run: echo "PYTHONPATH=$PYTHONPATH:$(pwd)" >> $GITHUB_ENV

    # check where we are? /home/runner/work/bb/bb
    - name: Print working directory
      run: pwd

    # right place?
    - name: List files
      run: ls -R workbook/ch03/ci

    # unit tests using Python's unittest: workbook/ch03/ci
    - name: Run tests
      run: |
        python -m unittest discover -s workbook/ch03/ci -p 'test_*.py'
```


#### 1. 'name': Python CI

This defines the name of the workflow. “Python CI” is descriptive
and indicates that the workflow is a Continuous Integration process
for a Python project.


#### 2. Triggers (on)

```yml
on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
```

This section defines the triggers for the workflow:
- `push`: The workflow runs whenever a commit is pushed to the main branch.
- `pull_request`: The workflow also runs for pull requests targeting the main branch.

These triggers ensure that the pipeline is executed whenever
changes are made to critical code paths.


#### 3. 'jobs'

Jobs represent individual tasks or a sequence of tasks within the
workflow. The script defines a single job named build.


#### 3.1 'runs-on'

```yml
runs-on: ubuntu-latest
```

This specifies the environment in which the job will execute.
`ubuntu-latest` is a virtual machine running the latest stable
Ubuntu release. It provides a clean and standardized environment
for CI tasks.


#### 3.2 Steps in the job

The steps section defines the actions to perform in sequence.

1.	Checkout Code
```yml
- name: Checkout code
  uses: actions/checkout@v4
```

This uses the actions/checkout action to clone the repository’s code
into the virtual machine, enabling subsequent steps to work with the
source code.

2.	Set Up Python

```yml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.9'
```
This installs Python 3.9 on the runner. The actions/setup-python
action simplifies setting up Python environments in CI pipelines.

3.	Install Dependencies

```yml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    if [ -f workbook/ch03/ci/requirements.txt ]; then pip install -r requirements.txt; fi
```

Upgrades pip to the latest version.

Checks for a requirements.txt file (at the specified path) and
installs any dependencies listed in it. This makes the environment
ready for testing.

4. Set PYTHONPATH

```yml
- name: Set PYTHONPATH
  run: echo "PYTHONPATH=$PYTHONPATH:$(pwd)" >> $GITHUB_ENV
```
Extends the PYTHONPATH environment variable to include the repository’s
root directory. This ensures that Python can locate modules and packages
correctly.

5. Run tests

```yml
- name: Run tests
  run: |
    python -m unittest discover -s workbook/ch03/ci -p 'test_*.py'
```

Executes all unit tests found in the directory workbook/ch03/ci whose
filenames match the pattern test_*.py. The unittest framework is used
for testing.


### Customization suggestions

Additional Python Versions: To test against multiple Python versions,
you can use a strategy matrix:

```yml
strategy:
  matrix:
    python-version: [3.8, 3.9, 3.10]
with:
  python-version: ${{ matrix.python-version }}
```

Code Coverage: Integrate tools like coverage.py to generate a test
coverage report.

```yml
- name: Generate coverage report
  run: |
    pip install coverage
    coverage run -m unittest discover -s workbook/ch03/ci -p 'test_*.py'
    coverage report
```

Linting: Add a step to run a linter like flake8 or pylint for code
quality checks.

```yml
- name: Lint code
  run: |
    pip install flake8
    flake8 .
```

This workflow provides a solid foundation for CI in a Python project,
ensuring code quality and functionality are maintained with every change.


### Sample

`main.py`

```python
# some function
def some_function(a, b):
    return a + b
```

`test_main.py`

```python
import unittest
from main import some_function

class TestMain(unittest.TestCase):
    def test_some_function(self):
        self.assertEqual(some_function(2, 3), 5)

if __name__ == '__main__':
    unittest.main()
```
