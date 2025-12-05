
## Tutorial to 'make' and 'Makefiles'

The 'make' is a build automation tool commonly used in software development.
It uses a 'Makefile' to define a set of rules for building and managing
dependencies (in a project). It is especially helpful when your
project involves multiple files and complex compilation steps.


### What is make?

- Purpose: Automate the process of compiling and building software.
- How it works: make reads instructions from a Makefile, which specifies:
    - Targets: The files or actions you want to build or perform.
    - Dependencies: Files or prerequisites required to build a target.
    - Commands: Steps to generate the target from its dependencies.


#### Basic Structure of a Makefile

```makefile
target: dependencies
    command
```

- `target`: The file to build (e.g., an executable, object file, or document).
- `dependencies`: Files or targets needed to build the target.
- `command`: Shell commands executed to create the target.


##### 1. A Simple Example

Suppose we have a C program 'main.c':

```c
#include <stdio.h>
int main() {
    printf("Hello, Make!\n");
    return 0;
}
```

Without make you compile it manually using:

```shell
gcc -o main main.c
```

With make create a file named 'Makefile' (no file extension):

```makefile
main: main.c
    gcc -o main main.c
```

To build the program, simply run 'make' at the command line.

- `main`: This is the target. It will be created when you run make.
- `main.c`: This is the *dependency*. If main.c is modified, the target will be rebuilt.
- `gcc -o main main.c`: The command to compile the program.

##### 2. Adding Cleanup

You can add a clean target to remove build files:

```makefile
main: main.c
    gcc -o main main.c

clean:
    rm -f main
```

Run make clean to delete the main executable:

```shell
make clean
```

##### 3. Variables in Makefiles

You can simplify your Makefile by using variables:

```makefile
CC = gcc
CFLAGS = -Wall
TARGET = main

$(TARGET): main.c
    $(CC) $(CFLAGS) -o $(TARGET) main.c

clean:
    rm -f $(TARGET)
```

- `$(CC)`: Refers to the gcc compiler.
- `$(CFLAGS)`: Compiler flags (e.g., -Wall enables warnings).
- `$(TARGET)`: A custom variable holding the target name.

##### 4. Handling Multiple Files

For larger projects, source files are often split across multiple .c files, main.c:

```c
#include <stdio.h>
#include "hello.h"
int main() {
    print_hello();
    return 0;
}
```

hello.c:

```c
#include <stdio.h>
void print_hello() {
    printf("Hello from another file!\n");
}
```

hello.h:

```c
void print_hello();
```

To compile manually:

```shell
gcc -c main.c
gcc -c hello.c
gcc -o main main.o hello.o
```

With 'make', the 'Makefile' simplifies this process:

```makefile
CC = gcc
CFLAGS = -Wall
TARGET = main
OBJS = main.o hello.o

$(TARGET): $(OBJS)
    $(CC) $(CFLAGS) -o $(TARGET) $(OBJS)

main.o: main.c hello.h
    $(CC) $(CFLAGS) -c main.c

hello.o: hello.c hello.h
    $(CC) $(CFLAGS) -c hello.c

clean:
    rm -f $(TARGET) $(OBJS)
```

Run make to build the program, and make clean to remove generated files.

##### 5. Automatic Dependency Handling

Makefiles can automatically detect changes in dependencies using special features using pattern rules:

```makefile
%.o: %.c
    $(CC) $(CFLAGS) -c $<
```
Updated Makefile:

```makefile
CC = gcc
CFLAGS = -Wall
TARGET = main
OBJS = main.o hello.o

$(TARGET): $(OBJS)
    $(CC) $(CFLAGS) -o $(TARGET) $(OBJS)

%.o: %.c
    $(CC) $(CFLAGS) -c $<

clean:
    rm -f $(TARGET) $(OBJS)
```

- `%.o: %.c`: A pattern rule for generating .o files from .c files.
- `$<`: Refers to the first dependency (e.g. main.c for main.o).

##### 6. Using Built-in Functions

Makefiles include functions for string manipulation and other utilities. Common ones include:
- `$@`: The target name.
- `$^`: All dependencies.
- `$<`: The first dependency.

Example:

```makefile
$(TARGET): $(OBJS)
    $(CC) $(CFLAGS) -o $@ $^
```

- Build `$(TARGET)` using `$(CC)` with all dependencies `$^`.

##### 7. Phony Targets

Some targets, like 'clean', don’t correspond to actual files. To prevent conflicts, you can declare them phony:

```makefile
.PHONY: clean
clean:
    rm -f $(TARGET) $(OBJS)
```

##### 8. Advanced: Conditional Compilation

You can include optional features using conditions:

```makefile
DEBUG = 1

ifeq ($(DEBUG), 1)
    CFLAGS += -g
else
    CFLAGS += -O2
endif
```

Run make with custom variables:

```shell
make DEBUG=0
```

#### Summary

|Command|	Description|
|--|--|
|make|	Build the default target (first in the file).|
|make <target>|	Build a specific target.|
|make clean|	Execute the clean target.|
|make -n|	Show the commands without running them.|
|make -j <N>|	Run make with N parallel jobs.|


#### Recommendations

1.	List targets logically, and use comments to document the purpose of each.
2.	Use variables and pattern rules to minimize repetition.
3.	Check that changes to source files trigger only necessary recompilation.
4.	Leverage .PHONY to avoid issues with non-file targets like clean.


### GitHub Actions

[![Build in Subdirectory](https://github.com/Feyerabend/bb/actions/workflows/build.yml/badge.svg)](https://github.com/Feyerabend/bb/actions/workflows/build.yml)

Using make with GitHub Actions allows you to automate the build and testing process of your
code directly within your CI/CD pipeline. GitHub Actions provides an environment to define
workflows, automate tasks, and execute scripts, such as running make commands to compile or
test code. Typically, you’d use a .github/workflows directory in your repository to define
YAML files that describe the build process and the steps required to execute it.

To use make in a GitHub Actions workflow, you first need to specify the environment. This can
be done using the runs-on key, which defines the operating system of the runner
(e.g. ubuntu-latest, windows-latest). You then define the steps of the workflow, which might
include checking out the repository, installing necessary tools (like gcc and make), and
running the make command to build or test the project. The working-directory key can be used
to specify a subdirectory containing your Makefile, ensuring the make command is executed in
the correct location.

A typical GitHub Actions configuration for running make would involve first checking out the
repository with actions/checkout, followed by setting up the necessary build environment
(such as installing make and other dependencies). Then, you would run make to execute targets
such as make build to compile the code or make test to run unit tests. You can also add custom
commands to clean up after the build using a target like make clean. By automating this
process in GitHub Actions, you ensure consistent, repeatable builds and tests without manual
intervention.

main.c:

```c
#include <stdio.h>
int main() {
    printf("Hello, make!\n");
    return 0;
}
```

Makefile:

```makefile
build:
	gcc -o main main.c

test:
	./main

clean:
	rm -f main
```

And YAML build.yml:

```yaml
name: Build in Subdirectory

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up build tools
      run: sudo apt-get update && sudo apt-get install -y gcc make

    - name: List directory contents
      run: ls -l workbook/ch03/make

    - name: Navigate to subdirectory and build
      working-directory: workbook/ch03/make
      run: make build

    - name: Run tests
      working-directory: workbook/ch03/make
      run: make test | grep "Hello, make!"

    - name: Clean up
      working-directory: workbook/ch03/make
      run: make clean
```