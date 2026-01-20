
## Really Simple Recursive Descent

We look at a really simple parser which only takes care of S-expressions. S-expressions (Symbolic Expressions) are a simple,
parenthesised syntax for representing data and code in a hierarchical, tree-like structure. Originating in Lisp, they are used
for both the program's code and its data, emphasising simplicity and uniformity.

### 1. Simplified LISP Parser

*Grammar:*
```
S → ( A )
A → a A | ε
```

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char *input;
int pos = 0;

// glance at one character in front
char lookahead() {
    return input[pos];
}

// consume
void eat(char expected) {
    if (lookahead() == expected) {
        pos++;
    } else {
        printf("Error: Expected '%c' but found '%c'\n", expected, lookahead());
        exit(1);
    }
}

void A() {
    while (lookahead() == 'a') {
        eat('a');
    }
}

void S() {
    eat('(');
    A();
    eat(')');
}

int main() {
    input = "(aa)";  // example
    S();
    if (lookahead() == '\0') {
        printf("LISP input parsed successfully!\n");
    } else {
        printf("Error: Unexpected input at end\n");
    }
    return 0;
}
```

#### Python Implementation

```python
class LispParser:
    def __init__(self, input):
        self.input = input
        self.pos = 0

    def lookahead(self):
        return self.input[self.pos] if self.pos < len(self.input) else None

    def eat(self, expected):
        if self.lookahead() == expected:
            self.pos += 1
        else:
            raise Exception(f"Error: Expected '{expected}' but found '{self.lookahead()}'")

    def A(self):
        while self.lookahead() == 'a':
            self.eat('a')

    def S(self):
        self.eat('(')
        self.A()
        self.eat(')')

    def parse(self):
        self.S()
        if self.lookahead() is None:
            print("LISP input parsed successfully!")
        else:
            print("Error: Unexpected input at end")

# example
input_string = "(aa)"
parser = LispParser(input_string)
parser.parse()
```

### 2. Simplified Pascal Parser

Next, parsing Pascal (another programming language) in both C and Python.

*Grammar:*
```
S → BEGIN E END
E → ID := NUMBER
ID → [a-zA-Z][a-zA-Z0-9]*
NUMBER → [0-9]+
```

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

char *input;
int pos = 0;

char lookahead() {
    return input[pos];
}

void eat(char expected) {
    if (lookahead() == expected) {
        pos++;
    } else {
        printf("Error: Expected '%c' but found '%c'\n", expected, lookahead());
        exit(1);
    }
}

void ID() {
    if (isalpha(lookahead())) {
        eat(lookahead());
        while (isalnum(lookahead())) eat(lookahead());
    } else {
        printf("Error: Expected ID\n");
        exit(1);
    }
}

void E() {
    ID();
    eat('=');
    while (isdigit(lookahead())) eat(lookahead());
}

void S() {
    eat('B');
    eat('E');
    eat('G');
    eat('I');
    eat('N');
    E();
    eat('E');
    eat('N');
    eat('D');
}

int main() {
    input = "BEGIN x := 123 END";  // example
    S();
    if (lookahead() == '\0') {
        printf("PASCAL input parsed successfully!\n");
    } else {
        printf("Error: Unexpected input at end\n");
    }
    return 0;
}
```

#### Python Implementation

```python
class PascalParser:
    def __init__(self, input):
        self.input = input
        self.pos = 0

    def lookahead(self):
        return self.input[self.pos] if self.pos < len(self.input) else None

    def eat(self, expected):
        if self.lookahead() == expected:
            self.pos += 1
        else:
            raise Exception(f"Error: Expected '{expected}' but found '{self.lookahead()}'")

    def ID(self):
        if self.lookahead().isalpha():
            self.eat(self.lookahead())
            while self.lookahead() and self.lookahead().isalnum():
                self.eat(self.lookahead())
        else:
            raise Exception("Error: Expected ID")

    def E(self):
        self.ID()
        self.eat('=')
        while self.lookahead().isdigit():
            self.eat(self.lookahead())

    def S(self):
        for char in "BEGIN":
            self.eat(char)
        self.E()
        for char in "END":
            self.eat(char)

    def parse(self):
        self.S()
        if self.lookahead() is None:
            print("PASCAL input parsed successfully!")
        else:
            print("Error: Unexpected input at end")

# example
input_string = "BEGIN x := 123 END"
parser = PascalParser(input_string)
parser.parse()
```

### Summary

Each parser follows the grammar rules defined and provides basic handling of
specific constructs for each simplified language. You can test and modify these 
parsers by changing the input strings according to the grammar rules. Adjustments
may be necessary to extend the grammar or handle additional constructs as needed.

