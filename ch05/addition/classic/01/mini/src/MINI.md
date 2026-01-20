
## Compiling in Practice: A Mini Compiler

Here we explore the practical aspects of building a simple compiler for arithmetic expressions.
While the concepts of compilers and interpreters have been discussed previously, here we focus
on a hands-on example. The goal is to create a minimal compiler that translates arithmetic expressions
into assembly-like instructions. This example demonstrates each step of the compilation process, 
from lexical analysis to code generation.

The assembly-like language we'll target is deliberately simple, designed for a hypothetical
stack-based virtual machine. While we won't provide the full implementation of this virtual
machine, we encourage you to extend the example by creating one, turning this simple compiler
into a complete system as a first project or exercise.

### The Input Language: Arithmetic Expressions

The input language for our compiler consists of basic arithmetic expressions using the following elements:
- Operands: Non-negative integers (e.g. 0, 42, 123).
- Operators: Standard arithmetic operators: addition (+), subtraction (-), multiplication (*), and division (/).
- Precedence and Associativity: Operators follow standard precedence rules:
- Multiplication and division have higher precedence than addition and subtraction.
- Operators of the same precedence are evaluated from left to right (left-associative).
- Whitespace: Spaces between tokens are allowed but ignored during compilation.

Example Input:

```
3 + 7 * 2 - 4
```

The Output: Assembly-Like Instructions

The compiler's output is a series of stack-based assembly instructions. These instructions are designed
to be executed by a simple virtual machine with the following properties:
1.	Stack-Based Execution:
- All calculations are performed using a stack.
- Operands are pushed onto the stack, and operators pop operands, perform the operation, and push the result back.

2. Instruction Set:
- PUSH <value>: Push a constant value onto the stack.
- ADD: Pop the top two values from the stack, add them, and push the result.
- SUB: Pop the top two values, subtract the second from the first, and push the result.
- MUL: Multiply the top two values.
- DIV: Divide the second value on the stack by the top value.

Example Output for '3 + 7 * 2 - 4':

```assembly
PUSH 3
PUSH 7
PUSH 2
MUL
ADD
PUSH 4
SUB
```

#### Compilation Steps

1. Lexical Analysis (Tokenisation, Tokenization):
   The compiler reads the input string and breaks it into tokens (e.g. numbers and operators).
   Each token has a type (such as NUMBER, PLUS, MINUS) and possibly a value (e.g. 3).

2. Syntax Analysis (Parsing):
   Using a recursive descent parser, the compiler processes the tokens to construct an
   Abstract Syntax Tree (AST). This tree represents the structure of the expression and
   respects operator precedence and associativity.

3. Semantic Analysis:
   The compiler ensures the AST is valid. For example, it verifies that division by zero
   is not attempted.

4. Code Generation:
   The AST is traversed, and stack-based assembly instructions are generated. These
   instructions correspond to the operations required to evaluate the expression.


#### Extending the Compiler: Implementing the Virtual Machine

While the compiler produces stack-based assembly, we do not include a complete virtual
machine in this chapter. However, the provided assembly language is straightforward to
implement.

- Stack Implementation:
  Use an array to simulate a stack. Operations like PUSH add values to the stack,
  while operations like ADD pop the top two values, perform the operation, and push the result.

- Execution Loop:
  Implement a loop that reads each instruction, performs the corresponding operation
  on the stack, and proceeds to the next instruction.


#### Example Virtual Machine Pseudocode:

```
initialise stack
for each instruction in program:
    if instruction is PUSH:
        push value onto stack
    if instruction is ADD:
        pop two values, add them, and push result
    if instruction is SUB:
        pop two values, subtract them, and push result
    if instruction is MUL:
        pop two values, multiply them, and push result
    if instruction is DIV:
        pop two values, divide them, and push result
print top of stack as the final result
```

### Mini Compiler: Overview

Let's recapitulate the simple compiler for arithmetic expressions, converting
high-level input into a pseudo-assembly language.
1. Lexical Analysis: Tokenise the input.
2. Syntax Analysis: Parse tokens into an Abstract Syntax Tree (AST).
3. Semantic Analysis: Ensure the AST is valid. (Example division by zero.)
4. Intermediate Code Generation: Transform the AST into a simpler representation. (Not implemented here.)
5. Code Generation: Generate pseudo-assembly from the intermediate representation.


### Code

```c
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

typedef enum {
    TOKEN_NUMBER,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_MULTIPLY,
    TOKEN_DIVIDE,
    TOKEN_END
} TokenType;

typedef struct {
    TokenType type;
    int value; // TOKEN_NUMBER
} Token;

typedef enum {
    AST_NUMBER,
    AST_BINARY_OP
} ASTNodeType;

typedef struct ASTNode {
    ASTNodeType type;
    int value; // numbers
    struct ASTNode *left, *right; // binary operations
    char op; // operator: +, -, *, /
} ASTNode;

// global state
const char *input;
Token current_token;

// fwd decl
void next_token();
ASTNode *parse_expression();
ASTNode *parse_term();
ASTNode *parse_factor();
void semantic_analysis(ASTNode *node);
void generate_code(ASTNode *node);
void error(const char *message);

// Lexical Analysis: Tokeniser
void next_token() {
    while (*input == ' ') input++; // skip whitespace

    if (*input == '\0') {
        current_token.type = TOKEN_END;
        return;
    }

    if (isdigit(*input)) {
        current_token.type = TOKEN_NUMBER;
        current_token.value = strtol(input, (char **)&input, 10);
        return;
    }

    switch (*input) {
        case '+': current_token.type = TOKEN_PLUS; input++; break;
        case '-': current_token.type = TOKEN_MINUS; input++; break;
        case '*': current_token.type = TOKEN_MULTIPLY; input++; break;
        case '/': current_token.type = TOKEN_DIVIDE; input++; break;
        default: error("Unexpected character");
    }
}

// Syntax Analysis: Recursive Descent Parser
ASTNode *create_node(ASTNodeType type, int value, ASTNode *left, ASTNode *right, char op) {
    ASTNode *node = (ASTNode *)malloc(sizeof(ASTNode));
    node->type = type;
    node->value = value;
    node->left = left;
    node->right = right;
    node->op = op;
    return node;
}

ASTNode *parse_expression() {
    ASTNode *node = parse_term(); // first term
    while (current_token.type == TOKEN_PLUS || current_token.type == TOKEN_MINUS) {
        char op = (current_token.type == TOKEN_PLUS) ? '+' : '-';
        next_token(); // consume operator
        node = create_node(AST_BINARY_OP, 0, node, parse_term(), op);
    }
    return node;
}

ASTNode *parse_term() {
    ASTNode *node = parse_factor(); // first factor
    while (current_token.type == TOKEN_MULTIPLY || current_token.type == TOKEN_DIVIDE) {
        char op = (current_token.type == TOKEN_MULTIPLY) ? '*' : '/';
        next_token(); // consume operator
        node = create_node(AST_BINARY_OP, 0, node, parse_factor(), op);
    }
    return node;
}

ASTNode *parse_factor() {
    if (current_token.type == TOKEN_NUMBER) {
        ASTNode *node = create_node(AST_NUMBER, current_token.value, NULL, NULL, 0);
        next_token(); // consume number
        return node;
    } else {
        error("Expected number");
        return NULL; // not reached
    }
}

// Semantic Analysis: Validate AST
void semantic_analysis(ASTNode *node) {
    if (node->type == AST_BINARY_OP) {
        semantic_analysis(node->left);
        semantic_analysis(node->right);
        if (node->op == '/' && node->right->type == AST_NUMBER && node->right->value == 0) {
            error("Division by zero");
        }
    }
}

// Code Generation: Recursive Postorder Traversal
void generate_code(ASTNode *node) {
    if (node->type == AST_NUMBER) {
        printf("PUSH %d\n", node->value);
    } else if (node->type == AST_BINARY_OP) {
        generate_code(node->left);
        generate_code(node->right);
        switch (node->op) {
            case '+': printf("ADD\n"); break;
            case '-': printf("SUB\n"); break;
            case '*': printf("MUL\n"); break;
            case '/': printf("DIV\n"); break;
        }
    }
}

void error(const char *message) {
    fprintf(stderr, "Error: %s\n", message);
    exit(EXIT_FAILURE);
}

int main() {
    char buffer[256];
    printf("Enter an arithmetic expression: ");
    if (fgets(buffer, sizeof(buffer), stdin)) {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') {
            buffer[len - 1] = '\0';
        }
    } else {
        error("Failed to read input");
    }

    input = buffer;
    next_token();

    // Compilation Pipeline
    ASTNode *ast = parse_expression();
    if (current_token.type != TOKEN_END) {
        error("Unexpected input after expression");
    }

    semantic_analysis(ast);
    printf("Generated Assembly:\n");
    generate_code(ast);

    return 0;
}
```

#### Explanation

1. Lexical Analysis:
- next_token scans the input and produces tokens (TOKEN_NUMBER, TOKEN_PLUS, etc.).

2. Syntax Analysis:
- The parser constructs an Abstract Syntax Tree (AST) using recursive descent:
- Nodes represent either numbers (AST_NUMBER) or binary operations (AST_BINARY_OP).

3. Semantic Analysis:
- Ensures correctness of the AST:
    - Example: Checking for division by zero.
4. Code Generation:
- Traverses the AST in postorder and generates stack-based pseudo-assembly.


#### Example

Input:
- Enter an arithmetic expression: '3 + 5 * 2'

Output:

Generated Assembly:
```assembly
PUSH 3
PUSH 5
PUSH 2
MUL
ADD
```
