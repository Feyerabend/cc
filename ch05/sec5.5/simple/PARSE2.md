
## Extended Simple Recursive Descent Parser

This code is an implementation of a simple parser for expressions involving identifiers, numbers, operators,
member access, and array indexing, designed to convert input strings into an Abstract Syntax Tree (AST).


### Constants for Symbol Types

The code defines a set of constants to represent different types of tokens and symbols that the lexer and
parser will recognise. These include operators (e.g., PLUS, MINUS, TIMES, etc.), symbols for assignment (ASSIGN),
and access operators like member access (PERIOD) and array indexing (LBRACKET, RBRACKET).


### Tokenisation (Lexer)

The tokenise function is responsible for converting an input string into a list of tokens that the parser can
process. Each token corresponds to a meaningful element in the input string (e.g. an identifier, number,
operator, or symbol). The `token_list` holds these tokens, and the nextsym function retrieves the next token
for processing.

The lexer recognises:
- *Identifiers*: Alphanumeric sequences representing variable names.
- *Numbers*: Integer values.
- *Operators*: Arithmetic and logical operators (+, -, *, /, %, &, |, ^).
- *Symbols*: Parentheses ((, )), assignment (=), member access (.), and array indexing ([ and ]).

The lexer also skips over whitespace and raises an error if it encounters an unknown character.

#### Token Types

Token types are represented as strings, such as 'IDENT', 'NUMBER', 'PERIOD', 'LBRACKET', etc., which are used
by the parser to recognise specific language constructs.

AST Nodes

The ASTNode class represents nodes in the Abstract Syntax Tree (AST). Each node can store:
- `type`: The type of the node (e.g., ASSIGNMENT, MEMBER_ACCESS, ARRAY_ACCESS, OP for operators).
- `node1` and `node2`: References to child nodes, allowing for binary tree-like structures for operations.
- `value`: The value of the node (used for literals such as numbers).
- `name`: The name of an identifier (used for variable names).
- `member`: For member access, stores the name of the member being accessed.
- `index`: For array access, stores the index expression.

The `nnode()` function creates a new ASTNode with the specified type.

### The Parser

The parser consists of several functions that parse specific parts of an expression and build the
corresponding AST.

- `parse_factor`: This function handles the lowest-level constructs (e.g. identifiers, numbers, parentheses,
  member access, and array indexing). If it encounters an identifier, it will check for possible member
  access or array indexing and build the corresponding AST nodes.

- `parse_expression`: This function handles expressions that involve assignments and operators. It handles
  the assignment (=) operator and various arithmetic (+, -, etc.) and logical operators (OR, XORSYM).

- `parse_term`: This function handles terms that involve multiplication (*), division (/), modulus (%),
  and logical AND (&).

Each of these functions processes tokens in a left-to-right order and recursively constructs an AST by
linking nodes together for operations.


#### Operator Precedence

The precedence of operations is handled by the order in which the parsing functions are invoked:
- `parse_factor` handles the lowest precedence operations (e.g. literal values and parentheses).
- `parse_term` handles multiplication, division, modulus, and logical AND (higher precedence).
- `parse_expression` handles addition, subtraction, and logical OR and XOR (lowest precedence).

This results in a correct handling of operator precedence when constructing the AST.


### Example

__Test Case 1: Array Indexing and Assignment__

*Input: "array[3] = object.property + 5"*
1. `parse_expression` starts the parsing process and recognizes the assignment (=) operator.
2. `parse_term` handles the left-hand side of the assignment (array[3]), which involves array indexing.
   It constructs an ARRAY_ACCESS node.
3. `parse_factor` is called to parse the right-hand side (object.property + 5), which involves member
   access (object.property). This constructs a MEMBER_ACCESS node.
4. The result is an AST representing the assignment with array indexing and member access.

__Test Case 2: Simple Assignment__

*Input: "x = 3"*
1. `parse_expression` starts the parsing process and recognizes the assignment (=) operator.
2. The left-hand side is parsed as an identifier (x), and the right-hand side is parsed as a number (3).
3. The result is an ASSIGNMENT AST node representing the assignment.

__Test Case 3: Member Access__

*Input: "object.property"*
1. `parse_expression` starts the parsing process and calls parse_factor to handle the identifier object.
2. It then detects the member access (.) and constructs a MEMBER_ACCESS node for property.
3. The result is an AST representing the member access.


#### Output of the AST

The `print_ast()` function recursively prints the structure of the AST in a readable format. It shows the
type of each node, along with the values for identifiers, numbers, and any additional attributes like
member (for member access) and index (for array indexing).


### Summary

This code implements a simple lexer and parser for a language with basic arithmetic expressions,
assignment operations, member access, and array indexing. The lexer converts input strings into
tokens, and the parser constructs an Abstract Syntax Tree (AST) from those tokens. Each expression
is parsed based on its precedence, and the resulting AST reflects the structure of the input
program. The system handles both simple assignments and more complex constructs like array indexing
and member access.
