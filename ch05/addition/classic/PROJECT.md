
## Design and Implementation of a Custom Programming Language and Its Compiler

Creating your own programming language and compiler is a highly educational project
that allows you to understand fundamental concepts in computer science, such as
parsing, syntax trees, code generation, and optimization. This enhanced guide provides
detailed grammar specifications and comprehensive testing strategies.


### 1. Language Design

Start by defining the syntax, semantics, and goals of your programming language.
For this guide, we'll design "SimpleLang"--a statically-typed imperative language.


#### Sample Complete Grammar (EBNF)

Here's a comprehensive grammar for SimpleLang using Extended Backus-Naur Form:

```ebnf
(* Program Structure *)
program = { declaration } ;

declaration = function_declaration 
           | variable_declaration ;

(* Function Declarations *)
function_declaration = "function" identifier "(" [ parameter_list ] ")" ":" type "{" statement_list "}" ;

parameter_list = parameter { "," parameter } ;
parameter = identifier ":" type ;

(* Variable Declarations *)
variable_declaration = "let" identifier ":" type [ "=" expression ] ";" ;

(* Types *)
type = "int" | "bool" | "string" | "void" ;

(* Statements *)
statement_list = { statement } ;

statement = assignment_statement
         | if_statement
         | while_statement
         | return_statement
         | expression_statement
         | block_statement ;

assignment_statement = identifier "=" expression ";" ;

if_statement = "if" "(" expression ")" statement [ "else" statement ] ;

while_statement = "while" "(" expression ")" statement ;

return_statement = "return" [ expression ] ";" ;

expression_statement = expression ";" ;

block_statement = "{" statement_list "}" ;

(* Expressions *)
expression = logical_or ;

logical_or = logical_and { "||" logical_and } ;

logical_and = equality { "&&" equality } ;

equality = comparison { ( "==" | "!=" ) comparison } ;

comparison = term { ( ">" | ">=" | "<" | "<=" ) term } ;

term = factor { ( "+" | "-" ) factor } ;

factor = unary { ( "*" | "/" | "%" ) unary } ;

unary = ( "!" | "-" ) unary | primary ;

primary = number
        | string
        | "true"
        | "false"
        | identifier [ "(" [ argument_list ] ")" ]
        | "(" expression ")" ;

argument_list = expression { "," expression } ;

(* Terminals *)
identifier = letter { letter | digit | "_" } ;
number = digit { digit } ;
string = '"' { character } '"' ;
letter = "A" | "B" | ... | "Z" | "a" | "b" | ... | "z" ;
digit = "0" | "1" | ... | "9" ;
character = (* any printable character except " *) ;
```


#### Example Program in SimpleLang

```c
function fibonacci(n: int): int {
    if (n <= 1) {
        return n;
    } else {
        return fibonacci(n - 1) + fibonacci(n - 2);
    }
}

function main(): void {
    let result: int = fibonacci(10);
    print(result);
}
```


### 2. Enhanced Lexer Implementation

```python
import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    
    # Keywords
    FUNCTION = auto()
    LET = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    
    # Types
    INT = auto()
    BOOL = auto()
    STRING_TYPE = auto()
    VOID = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    ASSIGN = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LOGICAL_AND = auto()
    LOGICAL_OR = auto()
    LOGICAL_NOT = auto()
    
    # Punctuation
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    SEMICOLON = auto()
    COMMA = auto()
    COLON = auto()
    
    # Special
    EOF = auto()
    NEWLINE = auto()

@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        
        self.keywords = {
            'function': TokenType.FUNCTION,
            'let': TokenType.LET,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'while': TokenType.WHILE,
            'return': TokenType.RETURN,
            'true': TokenType.TRUE,
            'false': TokenType.FALSE,
            'int': TokenType.INT,
            'bool': TokenType.BOOL,
            'string': TokenType.STRING_TYPE,
            'void': TokenType.VOID,
        }
    
    def scan_tokens(self) -> List[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens
    
    def scan_token(self):
        c = self.advance()
        
        if c.isspace():
            if c == '\n':
                self.line += 1
                self.column = 1
            return
        
        single_char_tokens = {
            '(': TokenType.LEFT_PAREN,
            ')': TokenType.RIGHT_PAREN,
            '{': TokenType.LEFT_BRACE,
            '}': TokenType.RIGHT_BRACE,
            ';': TokenType.SEMICOLON,
            ',': TokenType.COMMA,
            ':': TokenType.COLON,
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MULTIPLY,
            '/': TokenType.DIVIDE,
            '%': TokenType.MODULO,
        }
        
        if c in single_char_tokens:
            self.add_token(single_char_tokens[c])
        elif c == '=':
            self.add_token(TokenType.EQUALS if self.match('=') else TokenType.ASSIGN)
        elif c == '!':
            self.add_token(TokenType.NOT_EQUALS if self.match('=') else TokenType.LOGICAL_NOT)
        elif c == '<':
            self.add_token(TokenType.LESS_EQUAL if self.match('=') else TokenType.LESS)
        elif c == '>':
            self.add_token(TokenType.GREATER_EQUAL if self.match('=') else TokenType.GREATER)
        elif c == '&':
            if self.match('&'):
                self.add_token(TokenType.LOGICAL_AND)
            else:
                raise SyntaxError(f"Unexpected character '&' at line {self.line}, column {self.column}")
        elif c == '|':
            if self.match('|'):
                self.add_token(TokenType.LOGICAL_OR)
            else:
                raise SyntaxError(f"Unexpected character '|' at line {self.line}, column {self.column}")
        elif c == '"':
            self.string()
        elif c.isdigit():
            self.number()
        elif c.isalpha() or c == '_':
            self.identifier()
        else:
            raise SyntaxError(f"Unexpected character '{c}' at line {self.line}, column {self.column}")
    
    def advance(self) -> str:
        if self.is_at_end():
            return '\0'
        self.current += 1
        self.column += 1
        return self.source[self.current - 1]
    
    def match(self, expected: str) -> bool:
        if self.is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True
    
    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]
    
    def is_at_end(self) -> bool:
        return self.current >= len(self.source)
    
    def add_token(self, token_type: TokenType):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, text, self.line, self.column - len(text)))
    
    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
            self.advance()
        
        if self.is_at_end():
            raise SyntaxError(f"Unterminated string at line {self.line}")
        
        self.advance()  # Closing "
        value = self.source[self.start + 1:self.current - 1]  # Trim quotes
        self.add_token(TokenType.STRING)
    
    def number(self):
        while self.peek().isdigit():
            self.advance()
        self.add_token(TokenType.NUMBER)
    
    def identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        
        text = self.source[self.start:self.current]
        token_type = self.keywords.get(text, TokenType.IDENTIFIER)
        self.add_token(token_type)
```


### 3. Enhanced Parser with AST Nodes

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Any

# AST Node Classes
class ASTNode(ABC):
    pass

class Expression(ASTNode):
    pass

class Statement(ASTNode):
    pass

class Declaration(ASTNode):
    pass

# Expression nodes
class BinaryExpression(Expression):
    def __init__(self, left: Expression, operator: Token, right: Expression):
        self.left = left
        self.operator = operator
        self.right = right

class UnaryExpression(Expression):
    def __init__(self, operator: Token, operand: Expression):
        self.operator = operator
        self.operand = operand

class LiteralExpression(Expression):
    def __init__(self, value: Any):
        self.value = value

class IdentifierExpression(Expression):
    def __init__(self, name: str):
        self.name = name

class CallExpression(Expression):
    def __init__(self, callee: Expression, arguments: List[Expression]):
        self.callee = callee
        self.arguments = arguments

# Statement nodes
class ExpressionStatement(Statement):
    def __init__(self, expression: Expression):
        self.expression = expression

class AssignmentStatement(Statement):
    def __init__(self, name: str, value: Expression):
        self.name = name
        self.value = value

class IfStatement(Statement):
    def __init__(self, condition: Expression, then_stmt: Statement, else_stmt: Optional[Statement] = None):
        self.condition = condition
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

class WhileStatement(Statement):
    def __init__(self, condition: Expression, body: Statement):
        self.condition = condition
        self.body = body

class ReturnStatement(Statement):
    def __init__(self, value: Optional[Expression] = None):
        self.value = value

class BlockStatement(Statement):
    def __init__(self, statements: List[Statement]):
        self.statements = statements

# Declaration nodes
class FunctionDeclaration(Declaration):
    def __init__(self, name: str, parameters: List[tuple], return_type: str, body: BlockStatement):
        self.name = name
        self.parameters = parameters  # List of (name, type) tuples
        self.return_type = return_type
        self.body = body

class VariableDeclaration(Declaration):
    def __init__(self, name: str, var_type: str, initializer: Optional[Expression] = None):
        self.name = name
        self.var_type = var_type
        self.initializer = initializer

class Program(ASTNode):
    def __init__(self, declarations: List[Declaration]):
        self.declarations = declarations
```


### 4. Comprehensive Testing Strategies

### Unit Testing Framework

```python
import unittest
from typing import List
import os
import tempfile

class CompilerTestCase(unittest.TestCase):
    def setUp(self):
        self.lexer = None
        self.parser = None
        self.compiler = None
    
    def create_temp_file(self, content: str) -> str:
        """Create a temporary file with the given content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sl', delete=False) as f:
            f.write(content)
            return f.name
    
    def cleanup_temp_file(self, filepath: str):
        """Clean up temporary file."""
        if os.path.exists(filepath):
            os.unlink(filepath)

class LexerTests(CompilerTestCase):
    def test_tokenize_keywords(self):
        """Test that keywords are properly tokenized."""
        source = "function let if else while return true false"
        lexer = Lexer(source)
        tokens = lexer.scan_tokens()
        
        expected_types = [
            TokenType.FUNCTION, TokenType.LET, TokenType.IF, TokenType.ELSE,
            TokenType.WHILE, TokenType.RETURN, TokenType.TRUE, TokenType.FALSE,
            TokenType.EOF
        ]
        
        actual_types = [token.type for token in tokens]
        self.assertEqual(actual_types, expected_types)
    
    def test_tokenize_operators(self):
        """Test operator tokenization."""
        source = "+ - * / % = == != < <= > >= && || !"
        lexer = Lexer(source)
        tokens = lexer.scan_tokens()
        
        expected_types = [
            TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE,
            TokenType.MODULO, TokenType.ASSIGN, TokenType.EQUALS, TokenType.NOT_EQUALS,
            TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL,
            TokenType.LOGICAL_AND, TokenType.LOGICAL_OR, TokenType.LOGICAL_NOT, TokenType.EOF
        ]
        
        actual_types = [token.type for token in tokens]
        self.assertEqual(actual_types, expected_types)
    
    def test_tokenize_literals(self):
        """Test literal tokenization."""
        source = '42 "hello world" true false identifier_123'
        lexer = Lexer(source)
        tokens = lexer.scan_tokens()
        
        expected = [
            (TokenType.NUMBER, "42"),
            (TokenType.STRING, '"hello world"'),
            (TokenType.TRUE, "true"),
            (TokenType.FALSE, "false"),
            (TokenType.IDENTIFIER, "identifier_123"),
            (TokenType.EOF, "")
        ]
        
        actual = [(token.type, token.lexeme) for token in tokens]
        self.assertEqual(actual, expected)
    
    def test_error_handling(self):
        """Test lexer error handling."""
        source = "@invalid_char"
        lexer = Lexer(source)
        
        with self.assertRaises(SyntaxError):
            lexer.scan_tokens()

class ParserTests(CompilerTestCase):
    def test_parse_function_declaration(self):
        """Test parsing function declarations."""
        source = """
        function add(a: int, b: int): int {
            return a + b;
        }
        """
        # Implementation depends on your parser
        
    def test_parse_expressions(self):
        """Test expression parsing with precedence."""
        test_cases = [
            ("1 + 2 * 3", "1 + (2 * 3)"),  # Multiplication has higher precedence
            ("(1 + 2) * 3", "(1 + 2) * 3"),  # Parentheses override precedence
            ("a && b || c", "(a && b) || c"),  # AND has higher precedence than OR
        ]
        
        for source, expected in test_cases:
            # Parse and compare AST structure
            pass

class IntegrationTests(CompilerTestCase):
    def test_compile_factorial(self):
        """Test compiling a factorial function."""
        source = """
        function factorial(n: int): int {
            if (n <= 1) {
                return 1;
            } else {
                return n * factorial(n - 1);
            }
        }
        
        function main(): void {
            let result: int = factorial(5);
        }
        """
        
        temp_file = self.create_temp_file(source)
        try:
            # Compile and check for errors
            result = self.compiler.compile(temp_file)
            self.assertTrue(result.success)
            self.assertEqual(len(result.errors), 0)
        finally:
            self.cleanup_temp_file(temp_file)
    
    def test_compile_fibonacci(self):
        """Test compiling Fibonacci sequence."""
        source = """
        function fibonacci(n: int): int {
            if (n <= 1) {
                return n;
            }
            return fibonacci(n - 1) + fibonacci(n - 2);
        }
        """
        
        temp_file = self.create_temp_file(source)
        try:
            result = self.compiler.compile(temp_file)
            self.assertTrue(result.success)
        finally:
            self.cleanup_temp_file(temp_file)

class ErrorHandlingTests(CompilerTestCase):
    def test_syntax_errors(self):
        """Test various syntax error scenarios."""
        error_cases = [
            ("function missing_brace() {", "Missing closing brace"),
            ("let x int = 5;", "Missing colon in variable declaration"),
            ("if (condition {}", "Missing closing parenthesis"),
            ("return;", "Return statement outside function"),
        ]
        
        for source, expected_error in error_cases:
            with self.subTest(source=source):
                temp_file = self.create_temp_file(source)
                try:
                    result = self.compiler.compile(temp_file)
                    self.assertFalse(result.success)
                    self.assertGreater(len(result.errors), 0)
                finally:
                    self.cleanup_temp_file(temp_file)
    
    def test_semantic_errors(self):
        """Test semantic error detection."""
        error_cases = [
            ("let x: int = true;", "Type mismatch"),
            ("undeclared_var = 5;", "Undeclared variable"),
            ("function f(): int { return; }", "Missing return value"),
        ]
        
        for source, expected_error in error_cases:
            with self.subTest(source=source):
                # Test semantic analysis
                pass

class PerformanceTests(CompilerTestCase):
    def test_large_program_compilation(self):
        """Test compilation performance with large programs."""
        # Generate a large program
        source = self.generate_large_program(1000)  # 1000 functions
        
        import time
        start_time = time.time()
        
        temp_file = self.create_temp_file(source)
        try:
            result = self.compiler.compile(temp_file)
            compilation_time = time.time() - start_time
            
            self.assertTrue(result.success)
            self.assertLess(compilation_time, 10.0)  # Should compile in < 10 seconds
        finally:
            self.cleanup_temp_file(temp_file)
    
    def generate_large_program(self, num_functions: int) -> str:
        """Generate a large program for performance testing."""
        functions = []
        for i in range(num_functions):
            functions.append(f"""
            function func_{i}(x: int): int {{
                if (x <= 1) {{
                    return x;
                }}
                return func_{max(0, i-1)}(x - 1) + x;
            }}
            """)
        return "\n".join(functions)

class RegressionTests(CompilerTestCase):
    def test_known_bugs(self):
        """Test cases for previously found and fixed bugs."""
        # Add test cases for any bugs you've found and fixed
        pass

# Test Runner Configuration
def create_test_suite():
    """Create a comprehensive test suite."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        LexerTests,
        ParserTests,
        IntegrationTests,
        ErrorHandlingTests,
        PerformanceTests,
        RegressionTests,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite

if __name__ == '__main__':
    # Run all tests
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
```


### Testing Strategy Categories

#### 1. *Unit Tests*
- *Lexer Tests*: Token recognition, keyword identification, operator parsing
- *Parser Tests*: Grammar rule validation, AST construction, precedence handling
- *Code Generator Tests*: IR generation, target code output, optimization passes

#### 2. *Integration Tests*
- *End-to-End Compilation*: Complete programs from source to executable
- *Multi-file Programs*: Testing module system and linking
- *Standard Library Integration*: Testing built-in functions and types

#### 3. *Error Handling Tests*
- *Syntax Errors*: Malformed code, missing punctuation, invalid tokens
- *Semantic Errors*: Type mismatches, undeclared variables, scope violations
- *Runtime Errors*: Division by zero, stack overflow, memory errors

#### 4. *Performance Tests*
- *Large Programs*: Compilation time scaling with program size
- *Memory Usage*: Memory consumption during compilation
- *Optimization Effectiveness*: Before/after optimization comparisons

#### 5. *Correctness Tests*
- *Algorithm Implementation*: Known algorithms (sorting, searching, mathematical)
- *Edge Cases*: Boundary conditions, empty inputs, maximum values
- *Cross-Platform*: Consistent behavior across different systems

#### 6. *Regression Tests*
- *Bug Database*: Test cases for all previously found bugs
- *Feature Preservation*: Ensure new changes don't break existing functionality
- *Backward Compatibility*: Older program versions still compile


### Automated Testing Pipeline

```bash
#!/bin/bash
# test_runner.sh - Automated testing pipeline

echo "Starting SimpleLang Compiler Test Suite..."

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v

# Run integration tests
echo "Running integration tests..."
python -m pytest tests/integration/ -v

# Run performance benchmarks
echo "Running performance tests..."
python tests/performance/benchmark.py

# Generate coverage report
echo "Generating coverage report..."
coverage run -m pytest tests/
coverage report -m
coverage html

# Run static analysis
echo "Running static analysis..."
pylint src/compiler/

echo "Test suite completed!"
```


This enhanced project guide provides:

1. *Complete Grammar Specification*: A full EBNF grammar for a simple but complete programming language
2. *Enhanced Implementation*: More robust lexer and parser with proper error handling
3. *Comprehensive Testing Strategy*: Multiple categories of tests covering all aspects of compiler development
4. *Automated Testing Pipeline*: Scripts for continuous integration and automated testing
5. *Performance Considerations*: Guidelines for testing compilation performance and memory usage

The sample grammar supports functions, variables, control flow, expressions with proper
precedence, and basic type checking - providing a solid foundation for a complete compiler implementation.

