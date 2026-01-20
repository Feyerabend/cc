
## Simple Recursive Descent Parser

This code implements a simple tokeniser and parser for a basic arithmetic expression language.
The language supports variables (identifiers), integers, floating-point numbers, and common
arithmetic operations like addition, subtraction, multiplication, division, modulus, bitwise
AND, OR, XOR, and unary minus. The parser constructs an Abstract Syntax Tree (AST) to represent
the parsed input, which can then be used for evaluation or further processing.


1. *Token Types (Symbol Constants)*:
   The code defines constants for the various token types that the lexer (tokeniser) will recognise.
   These tokens are used by the parser to identify different elements of the input.
	- Identifiers (IDENT): Represent variable names, such as a, b, x.
	- Numbers (NUMBER, FLOAT): Represent integer and floating-point numbers.
	- Operators: The code recognises several operators such as addition (PLUS), subtraction (MINUS),
      multiplication (TIMES), division (SLASH), modulus (PERCENT), bitwise AND (ANDSYM), OR (ORSYM),
      XOR (XORSYM), and unary minus (UMINUS).
	- Parentheses: Used for grouping expressions.
	- Period (PERIOD): Not specifically used in this example but can represent a decimal point or
      another operator (context-dependent).

2. *Lexer (Tokeniser)*:
   The lexer is responsible for converting the input string into a sequence of tokens that the parser
   can understand. It processes each character in the input and classifies it into one of the defined
   token types.

   Main Steps in the Tokeniser:
	- It checks if the current character is part of an identifier (variable) or a number.
	- For numbers, it differentiates between integers and floating-point numbers using the presence
      of a dot (.).
	- It handles the parsing of arithmetic operators, parentheses, and whitespace.
	- If an unrecognized character is encountered, a SyntaxError is raised.

   Example Tokenisation:
   For the input string "(a + 3.5) * (c - 1.2) + 3 * -4.5", the lexer generates tokens such as
   LPAREN, IDENT("a"), PLUS, FLOAT(3.5), and so on.

3. *Parser*:
   The parser uses recursive descent parsing to handle different levels of expressions. It constructs
   an Abstract Syntax Tree (AST) as it processes the tokens.

	- `factor()`: This function handles the base components of an expression—either a number (integer or
      floating-point), an identifier (variable), or an expression within parentheses. It also handles
      unary minus (e.g. -a or -(a + b)).
	- `term()`: This function handles multiplication, division, modulus, and bitwise AND operations.
      It combines factors using these operators.
	- `expression()`: The main entry point for parsing expressions. It handles addition, subtraction,
      bitwise OR, and XOR operations. It uses terms to build more complex expressions.

   The parser uses a set of functions that process each operator and operand, recursively building
   nodes for the AST.

4. *Abstract Syntax Tree (AST)*:
   The AST is a hierarchical tree structure where each node represents a computational step (like an
   operation or a value) in the parsed expression. The tree allows easy manipulation of expressions
   and can be evaluated or transformed.

	- *Node Class*: The Node class defines the structure of each AST node. It includes a type (operator
      or operand), pointers to left and right children (node1 and node2), and additional properties
      for values or names.
	- *Value Class*: The Value class is used to store the position of the tokens (start and end),
      though it isn't used in detail in this code but can be expanded to add more tracking functionality.

   Example AST for (a + 3.5) * (c - 1.2) + 3 * -4.5:
   The AST will contain nodes for operations like addition (+), multiplication (*), and unary minus (-).
   The identifiers and numbers are leaf nodes in the tree.

5. *Evaluation/Output*:
   After parsing the input, the AST is printed using the print_tree() function, which recursively prints
   the structure of the AST. This is a simple textual representation to visualise how the input was parsed.

   Example Output for the Input (a + 3.5) * (c - 1.2) + 3 * -4.5:

```text
Parsed AST:
OP(ADD)
  OP(MULTIPLY)
    OP(PLUS)
      IDENT(a)
      FLOAT(3.5)
    OP(MULTIPLY)
      IDENT(c)
      FLOAT(1.2)
  OP(MULTIPLY)
    NUMBER(3)
    OP(UMINUS)
      FLOAT(4.5)
```

### Extended Backus-Naur Form (EBNF) for the Language

The grammar for the language defined by this parser can be described using EBNF.

```ebnf
<expression> ::= <term> { ("+" | "-" | "or" | "xor") <term> }

<term> ::= <factor> { ("*" | "/" | "%" | "and") <factor> }

<factor> ::= <identifier>
          | <number>
          | "(" <expression> ")"
          | "-" <factor>     // unary minus
          
<identifier> ::= [a-zA-Z][a-zA-Z0-9]*

<number> ::= [0-9]+ | [0-9]+"."<digit>+    // either integer or float
```

Explanation:
- An expression consists of one or more terms, where terms are combined by
  addition (+), subtraction (-), OR, or XOR.
- A term consists of one or more factors, which are combined using
  multiplication (*), division (/), modulus (%), or AND.
- A factor can be an identifier, a number, a parenthesised expression,
  or a unary minus applied to another factor.

This grammar reflects the structure of arithmetic and logical operations allowed by the language.

How the Code Works:
1. *Tokenisation*: The `tokenize()` function processes the input string and produces a list of tokens,
   which are the basic building blocks for parsing.
2. *Parsing*: The recursive functions `factor()`, `term()`, and `expression()` build the Abstract Syntax
   Tree (AST) based on the token sequence produced by the lexer.
3. *Abstract Syntax Tree (AST)*: Each expression is represented as a tree of Node objects, where
   each node represents either a value (number, identifier) or an operation (e.g. addition,
   multiplication).
4. *Output*: The `print_tree()` function prints the structure of the AST, which can be further used
   for evaluation, transformation, or optimisation.

This implementation serves as the foundation for more complex expression evaluation and manipulation
tasks, such as evaluating the expression values or transforming the AST into machine code or intermediate
representations for a compiler.
