
## Building Your Own Programming Language: A Project Guide

Perhaps one of the most exciting projects in computer science:
build your own programming language. This guide will walk you
through the process, from initial design decisions to a
compiler and virtual machine.

You will build:
1. *A programming language* with its own syntax and semantics
2. *A type system* that catches errors before runtime
3. *A compiler* that transforms source code into bytecode
4. *A virtual machine* that executes your bytecode
5. *A standard library* with basic functionality

You should be comfortable with:
- Programming in at least one language
  (we have already assumed Python, JavaScript, and C)
- Basic data structures (trees, stacks, hash tables)
- Recursion and recursive data structures
- Basic algorithm complexity (Big-O notation)

This is a semester-long project,
designed for 10-15 hours per week:
- *Weeks 1-3*: Design and specification
- *Weeks 4-6*: Lexer and parser
- *Weeks 7-9*: Type checker and semantic analysis
- *Weeks 10-12*: Code generation and VM
- *Weeks 13-15*: Testing, optimisation, and documentation

Making the assumptions you have studied [ch05](./../../ch05/)
carefully, and done some exercises, some of this should/might
go much faster than expected. For clarity though, we include
the whole schedule.


### Part 1: Understanding the Big Picture

#### How the Pieces Fit Together

We have already a familiarity with compilation and parts of
a compiler. We add some theory to this. Your project then 
consists of two main components that work together:
- Source Code >
- Lexer (tokenization) >
- Parser (syntax tree) >
- Type Checker (semantic analysis)
- IR Generator (intermediate representation) >
- Optimiser (optional) >
- Code Generator (bytecode) >
    - VM: Bytecode Loader >
    - VM: Instruction Dispatcher >
    - VM: Stack + Memory Management >
    - VM : Output ..

You've been provided with two key documents:
1. *DESIGN.md* - *Designing Programming Languages: From Type Theory to Virtual Machine Code*
   - Teaches language design principles
   - Explains type systems and formal semantics
   - Shows how to compile high-level code to VM instructions
   - Provides complete examples from source to bytecode

2. *VM-SPECIFICATION.md* - *Educational Virtual Machine Specification*
   - Defines the exact instruction set your compiler targets
   - Specifies memory model and execution semantics
   - Documents bytecode format
   - Shows example VM programs



### Part 2: Phase-by-Phase Project Plan

#### Phase 1: Design and Specification (Weeks 1-3)

##### Week 1: Language Design Decisions

*Your Task*: Design the syntax and features of your language.

*Key Decisions to Make*:

1. *Syntax Style*: Choose your aesthetic
   - C-like: `int x = 5; if (x > 0) { ... }`
   - Python-like: `x = 5` with indentation
   - ML-like: `let x = 5 in ...`
   - Your own style!

2. *Type System*: How strict?
   - Static typing: `let x: Int32 = 5`
   - Type inference: `let x = 5` (compiler figures out Int32)
   - Dynamic typing: `x = 5` (type checked at runtime)
   
   *Recommendation*: Start with static typing + basic inference

3. *Features to Include*:
   - *Minimum (start here)*:
     - Variables and assignment
     - Arithmetic (`+`, `-`, `*`, `/`)
     - Comparisons (`<`, `>`, `==`)
     - Conditionals (`if/then/else`)
     - Functions (definition and calls)
   - *Medium (add if time permits)*:
     - Loops (`while`, `for`)
     - Arrays or lists
     - Strings
     - Records/structs
   - *Advanced (optional challenges)*:
     - First-class functions
     - Closures
     - Generic/polymorphic types
     - Pattern matching

*Deliverable*: A language specification document including:
- Grammar (BNF or EBNF notation)
- Type rules
- Example programs
- Semantic description (what each construct means)

*Example Mini-Spec*:

```
# MyLang Specification

## Syntax

Program    ::= Statement*
Statement  ::= VarDecl | FunDecl | Expression
VarDecl    ::= "let" IDENT ":" Type "=" Expression
FunDecl    ::= "fn" IDENT "(" Params ")" "->" Type "{" Statement* "}"
Expression ::= Literal | IDENT | BinOp | Call | IfExpr
BinOp      ::= Expression ("+" | "-" | "*" | "/") Expression
Call       ::= IDENT "(" Args ")"
IfExpr     ::= "if" Expression "then" Expression "else" Expression

## Types

Type ::= "Int32" | "Bool" | Type "->" Type

## Example Program

fn factorial(n: Int32) -> Int32 {
  if n <= 1 then
    1
  else
    n * factorial(n - 1)
}

let result: Int32 = factorial(5)
```

##### Week 2: VM Customisation

*Your Task*: Decide if you'll use the provided VM as-is or customise it.

*Options*:

1. *Use the standard VM* (recommended for first-timers)
   - Follow VM-SPECIFICATION.md exactly
   - Focus on compiler implementation
   - Should be less to debug!

2. *Modify the VM* (if you want extra challenge)
   - Add new instructions for your language features
   - Change stack behavior
   - Add new data types
   - *Warning*: Must update both specification and implementation

*If modifying, document*:
- New instructions with opcodes
- Changed semantics
- Updated examples

*Deliverable*: VM specification (either "using standard" or your modified version)

##### Week 3: Development Environment Setup

*Your Task*: Set up tools and write a project plan.

*Choose Your Implementation Language*:

Recommended options (pick based on what you know):

1. *Python* (easiest to start)
   - Pros: Fast development, great for prototyping, rich libraries
   - Cons: Slower execution
   - Libraries: `ply` (lexer/parser), `dataclasses` (AST nodes)

2. *JavaScript/TypeScript* (good balance)
   - Pros: Fast, good tooling, easy testing
   - Cons: Need to understand async (but not much for this project)
   - Libraries: `moo` + `nearley` (parsing), or hand-written

3. *Java* (well-structured)
   - Pros: Strong typing helps catch bugs, good for larger projects
   - Cons: More verbose
   - Libraries: ANTLR (parser generator)

4. *C/C++* (if you want maximum performance)
   - Pros: Fast, teaches low-level details
   - Cons: Memory management, slower development
   - Libraries: Flex/Bison (lexer/parser)

5. *Rust* (modern systems language)
   - Pros: Memory safe, fast, excellent error messages
   - Cons: Steeper learning curve
   - Libraries: `nom` or `pest` (parsing)

*Set Up Your Repository*:

```
my-language/
├── DESIGN.md              # Your project documentation
├── docs/
│   ├── language-spec.md   # Your language specification
│   └── vm-spec.md         # VM specification (original or modified)
├── src/
│   ├── lexer/             # Tokenization
│   ├── parser/            # Syntax analysis
│   ├── ast/               # AST data structures
│   ├── typechecker/       # Type checking
│   ├── codegen/           # Code generation
│   └── vm/                # Virtual machine
├── tests/
│   ├── lexer/
│   ├── parser/
│   ├── typechecker/
│   └── integration/
└── examples/              # Example programs in your language
```

*Deliverable*: 
- Repository with structure
- DESIGN explaining your design choices
- Project timeline with milestones



#### Phase 2: Frontend Implementation (Weeks 4-6)

This shoud be rather easy, as we have already studied this in the
compiler chapter [ch05](./../../ch05/).

##### Week 4: Lexer (Tokenizer)

*Your Task*: Convert source text into tokens.

*What is a Lexer?*

The lexer breaks source code into meaningful chunks (tokens):

```
Input:  "let x = 42 + 7"
Output: [LET, IDENT("x"), EQUALS, NUMBER(42), PLUS, NUMBER(7)]
```

*Implementation Steps*:

1. *Define Token Types*:
   ```python
   # Python example
   from enum import Enum
   
   class TokenType(Enum):
       # Keywords
       LET = "let"
       FN = "fn"
       IF = "if"
       THEN = "then"
       ELSE = "else"
       
       # Operators
       PLUS = "+"
       MINUS = "-"
       STAR = "*"
       EQUALS = "="
       
       # Literals
       NUMBER = "number"
       IDENTIFIER = "identifier"
       
       # Punctuation
       LPAREN = "("
       RPAREN = ")"
       LBRACE = "{"
       RBRACE = "}"
   
   class Token:
       def __init__(self, type, value, line, column):
           self.type = type
           self.value = value
           self.line = line
           self.column = column
   ```

2. *Write the Lexer*:
   
   *Option A: Hand-written (good learning experience)*
   ```python
   class Lexer:
       def __init__(self, source):
           self.source = source
           self.pos = 0
           self.line = 1
           self.column = 1
       
       def peek(self):
           if self.pos >= len(self.source):
               return None
           return self.source[self.pos]
       
       def advance(self):
           if self.peek() == '\n':
               self.line += 1
               self.column = 1
           else:
               self.column += 1
           self.pos += 1
       
       def skip_whitespace(self):
           while self.peek() in ' \t\n\r':
               self.advance()
       
       def read_number(self):
           start = self.pos
           while self.peek() and self.peek().isdigit():
               self.advance()
           return int(self.source[start:self.pos])
       
       def read_identifier(self):
           start = self.pos
           while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
               self.advance()
           return self.source[start:self.pos]
       
       def next_token(self):
           self.skip_whitespace()
           
           if self.peek() is None:
               return Token(TokenType.EOF, None, self.line, self.column)
           
           if self.peek().isdigit():
               return Token(TokenType.NUMBER, self.read_number(), 
                          self.line, self.column)
           
           if self.peek().isalpha():
               ident = self.read_identifier()
               # Check if it's a keyword
               if ident == "let":
                   return Token(TokenType.LET, ident, self.line, self.column)
               # .. check other keywords
               return Token(TokenType.IDENTIFIER, ident, self.line, self.column)
           
           # Single character tokens
           if self.peek() == '+':
               self.advance()
               return Token(TokenType.PLUS, '+', self.line, self.column)
           
           # .. other chars
   ```

   *Option B: Using a library* (faster to write)
   ```python
   # Using Python's ply library
   import ply.lex as lex
   
   tokens = ['NUMBER', 'IDENTIFIER', 'PLUS', 'MINUS']
   reserved = {'let': 'LET', 'fn': 'FN', 'if': 'IF'}
   
   t_PLUS = r'\+'
   t_MINUS = r'-'
   
   def t_NUMBER(t):
       r'\d+'
       t.value = int(t.value)
       return t
   
   def t_IDENTIFIER(t):
       r'[a-zA-Z_][a-zA-Z0-9_]*'
       t.type = reserved.get(t.value, 'IDENTIFIER')
       return t
   
   lexer = lex.lex()
   ```

3. *Test Your Lexer*:
   ```python
   def test_lexer():
       source = "let x = 42 + 7"
       lexer = Lexer(source)
       tokens = []
       while True:
           tok = lexer.next_token()
           tokens.append(tok)
           if tok.type == TokenType.EOF:
               break
       
       assert tokens[0].type == TokenType.LET
       assert tokens[1].type == TokenType.IDENTIFIER
       assert tokens[1].value == "x"
       # .. more assertions
   ```

*Common Pitfalls*:
- Forgetting to handle comments (`//` or `/* */`)
- Not tracking line/column numbers (you'll need these for error messages!)
- Keywords vs identifiers (check keywords first)
- Operators like `==` vs `=` (read ahead!)

*Deliverable*: Working lexer with tests for all token types

*Resources*:
- "Crafting Interpreters" Chapter 4 (Scanning)
- Dragon Book Chapter 3 (Lexical Analysis)

##### Week 5: Parser (Syntax Analysis)

*Your Task*: Build an Abstract Syntax Tree (AST) from tokens.

*What is a Parser?*

Converts flat token stream into hierarchical tree structure:

```
Tokens: [LET, IDENT("x"), EQUALS, NUMBER(42)]
AST:    VarDecl
          ├─ name: "x"
          └─ value: Literal(42)
```

*Implementation Steps*:

1. *Define AST Node Classes*:
   ```python
   from dataclasses import dataclass
   from typing import List
   
   # Base class
   class ASTNode:
       pass
   
   # Expressions
   @dataclass
   class Literal(ASTNode):
       value: int | bool
   
   @dataclass
   class Variable(ASTNode):
       name: str
   
   @dataclass
   class BinaryOp(ASTNode):
       op: str  # "+", "-", "*", etc.
       left: ASTNode
       right: ASTNode
   
   @dataclass
   class IfExpr(ASTNode):
       condition: ASTNode
       then_branch: ASTNode
       else_branch: ASTNode
   
   @dataclass
   class Call(ASTNode):
       function: str
       arguments: List[ASTNode]
   
   # Statements
   @dataclass
   class VarDecl(ASTNode):
       name: str
       type_annotation: str
       value: ASTNode
   
   @dataclass
   class FunctionDecl(ASTNode):
       name: str
       parameters: List[tuple[str, str]]  # (name, type) pairs
       return_type: str
       body: List[ASTNode]
   
   @dataclass
   class Program(ASTNode):
       declarations: List[ASTNode]
   ```

2. *Write Recursive Descent Parser*:
   
   The key idea: each grammar rule becomes a function.
   
   ```python
   class Parser:
       def __init__(self, lexer):
           self.lexer = lexer
           self.current_token = self.lexer.next_token()
       
       def eat(self, token_type):
           """Consume a token of expected type"""
           if self.current_token.type != token_type:
               raise SyntaxError(f"Expected {token_type}, got {self.current_token.type}")
           self.current_token = self.lexer.next_token()
       
       def parse_program(self):
           """Program ::= Declaration*"""
           declarations = []
           while self.current_token.type != TokenType.EOF:
               declarations.append(self.parse_declaration())
           return Program(declarations)
       
       def parse_declaration(self):
           """Declaration ::= VarDecl | FunctionDecl"""
           if self.current_token.type == TokenType.LET:
               return self.parse_var_decl()
           elif self.current_token.type == TokenType.FN:
               return self.parse_function_decl()
           else:
               raise SyntaxError(f"Unexpected token: {self.current_token}")
       
       def parse_var_decl(self):
           """VarDecl ::= 'let' IDENT ':' Type '=' Expression"""
           self.eat(TokenType.LET)
           name = self.current_token.value
           self.eat(TokenType.IDENTIFIER)
           self.eat(TokenType.COLON)
           type_name = self.current_token.value
           self.eat(TokenType.IDENTIFIER)  # type name
           self.eat(TokenType.EQUALS)
           value = self.parse_expression()
           return VarDecl(name, type_name, value)
       
       def parse_expression(self):
           """Expression ::= Comparison"""
           return self.parse_comparison()
       
       def parse_comparison(self):
           """Comparison ::= Addition (('<' | '>' | '==') Addition)*"""
           left = self.parse_addition()
           
           while self.current_token.type in [TokenType.LESS, TokenType.GREATER, TokenType.EQEQ]:
               op = self.current_token.value
               self.eat(self.current_token.type)
               right = self.parse_addition()
               left = BinaryOp(op, left, right)
           
           return left
       
       def parse_addition(self):
           """Addition ::= Multiplication (('+' | '-') Multiplication)*"""
           left = self.parse_multiplication()
           
           while self.current_token.type in [TokenType.PLUS, TokenType.MINUS]:
               op = self.current_token.value
               self.eat(self.current_token.type)
               right = self.parse_multiplication()
               left = BinaryOp(op, left, right)
           
           return left
       
       def parse_multiplication(self):
           """Multiplication ::= Primary (('*' | '/') Primary)*"""
           left = self.parse_primary()
           
           while self.current_token.type in [TokenType.STAR, TokenType.SLASH]:
               op = self.current_token.value
               self.eat(self.current_token.type)
               right = self.parse_primary()
               left = BinaryOp(op, left, right)
           
           return left
       
       def parse_primary(self):
           """Primary ::= NUMBER | IDENTIFIER | '(' Expression ')' | IfExpr"""
           if self.current_token.type == TokenType.NUMBER:
               value = self.current_token.value
               self.eat(TokenType.NUMBER)
               return Literal(value)
           
           elif self.current_token.type == TokenType.IDENTIFIER:
               name = self.current_token.value
               self.eat(TokenType.IDENTIFIER)
               
               # Function call?
               if self.current_token.type == TokenType.LPAREN:
                   return self.parse_call(name)
               else:
                   return Variable(name)
           
           elif self.current_token.type == TokenType.LPAREN:
               self.eat(TokenType.LPAREN)
               expr = self.parse_expression()
               self.eat(TokenType.RPAREN)
               return expr
           
           elif self.current_token.type == TokenType.IF:
               return self.parse_if_expr()
           
           else:
               raise SyntaxError(f"Unexpected token: {self.current_token}")
       
       def parse_if_expr(self):
           """IfExpr ::= 'if' Expression 'then' Expression 'else' Expression"""
           self.eat(TokenType.IF)
           condition = self.parse_expression()
           self.eat(TokenType.THEN)
           then_branch = self.parse_expression()
           self.eat(TokenType.ELSE)
           else_branch = self.parse_expression()
           return IfExpr(condition, then_branch, else_branch)
   ```

3. *Handle Operator Precedence*:
   
   Notice the parsing functions are nested by precedence:
   - `parse_expression` --> `parse_comparison`
   - `parse_comparison` --> `parse_addition`
   - `parse_addition` --> `parse_multiplication`
   - `parse_multiplication` --> `parse_primary`
   
   This automatically handles: `2 + 3 * 4` --> `2 + (3 * 4)`

4. *Test Your Parser*:
   ```python
   def test_parser():
       source = "let x: Int32 = 2 + 3 * 4"
       lexer = Lexer(source)
       parser = Parser(lexer)
       ast = parser.parse_program()
       
       # Should be: VarDecl with BinaryOp(+, Literal(2), BinaryOp(*, Literal(3), Literal(4)))
       assert isinstance(ast, Program)
       assert len(ast.declarations) == 1
       var_decl = ast.declarations[0]
       assert var_decl.name == "x"
       assert isinstance(var_decl.value, BinaryOp)
       assert var_decl.value.op == "+"
   ```

*Common Pitfalls*:
- Wrong precedence (test with `2 + 3 * 4` and `2 * 3 + 4`)
- Left vs right associativity
- Forgetting to handle parentheses
- Not giving good error messages (add line/column info!)

*Deliverable*: Working parser with comprehensive tests

*Resources*:
- DESIGN.md Section 2.2 (grammar examples)
- "Crafting Interpreters" Chapters 6-7 (Parsing)

##### Week 6: Pretty Printer and AST Visualisation

*Your Task*: Make your AST visible and debuggable.

*Why This Matters*:
- Debugging parser issues
- Understanding what your compiler sees
- Documentation and testing

*Implementation*:

1. *AST Pretty Printer*:
   ```python
   class ASTPrinter:
       def __init__(self):
           self.indent_level = 0
       
       def indent(self):
           return "  " * self.indent_level
       
       def print_ast(self, node):
           method_name = f"print_{node.__class__.__name__}"
           method = getattr(self, method_name, self.print_generic)
           return method(node)
       
       def print_Program(self, node):
           result = "Program:\n"
           self.indent_level += 1
           for decl in node.declarations:
               result += self.indent() + self.print_ast(decl) + "\n"
           self.indent_level -= 1
           return result
       
       def print_BinaryOp(self, node):
           result = f"({node.op}\n"
           self.indent_level += 1
           result += self.indent() + self.print_ast(node.left) + "\n"
           result += self.indent() + self.print_ast(node.right) + ")"
           self.indent_level -= 1
           return result
       
       def print_Literal(self, node):
           return f"Literal({node.value})"
       
       # .. more print
   ```

2. *Graphical Visualisation* (optional but cool):
   ```python
   # Using graphviz
   import graphviz
   
   class ASTVisualizer:
       def __init__(self):
           self.graph = graphviz.Digraph()
           self.counter = 0
       
       def visualize(self, node):
           node_id = self.visit(node)
           return self.graph
       
       def visit(self, node):
           node_id = str(self.counter)
           self.counter += 1
           
           if isinstance(node, BinaryOp):
               self.graph.node(node_id, node.op)
               left_id = self.visit(node.left)
               right_id = self.visit(node.right)
               self.graph.edge(node_id, left_id)
               self.graph.edge(node_id, right_id)
           elif isinstance(node, Literal):
               self.graph.node(node_id, str(node.value))
           # .. other node types
           
           return node_id
   ```

*Deliverable*: 
- Pretty printer for all AST nodes
- Example outputs showing your AST structure
- (Optional) Graphical visualizations



#### Phase 3: Semantic Analysis (Weeks 7-9)

##### Week 7: Type Checker - Part 1 (Basic Types)

*Your Task*: Implement type checking for expressions.

*What is Type Checking?*

Ensure operations are valid for their types:
- `2 + 3` (Int32 + Int32 --> Int32)
- `2 + true` (Int32 + Bool --> ERROR!)

*Implementation Steps*:

1. *Define Type Representation*:
   ```python
   from dataclasses import dataclass
   
   class Type:
       pass
   
   @dataclass
   class IntType(Type):
       width: int  # 8, 16, or 32
       
       def __str__(self):
           return f"Int{self.width}"
   
   @dataclass
   class BoolType(Type):
       def __str__(self):
           return "Bool"
   
   @dataclass
   class FunctionType(Type):
       param_types: List[Type]
       return_type: Type
       
       def __str__(self):
           params = ", ".join(str(t) for t in self.param_types)
           return f"({params}) -> {self.return_type}"
   
   # Type environment (symbol table)
   class TypeEnvironment:
       def __init__(self, parent=None):
           self.bindings = {}
           self.parent = parent
       
       def bind(self, name, type):
           self.bindings[name] = type
       
       def lookup(self, name):
           if name in self.bindings:
               return self.bindings[name]
           elif self.parent:
               return self.parent.lookup(name)
           else:
               raise TypeError(f"Undefined variable: {name}")
       
       def new_scope(self):
           return TypeEnvironment(parent=self)
   ```

2. *Implement Type Checker*:
   ```python
   class TypeChecker:
       def __init__(self):
           self.env = TypeEnvironment()
           # Add built-in types/functions if any
       
       def check_program(self, program):
           """Check entire program"""
           for decl in program.declarations:
               self.check_declaration(decl)
       
       def check_declaration(self, decl):
           """Check a declaration"""
           if isinstance(decl, VarDecl):
               # Check the value expression
               value_type = self.infer_type(decl.value)
               
               # Parse the type annotation
               expected_type = self.parse_type_annotation(decl.type_annotation)
               
               # Match?
               if not self.types_equal(value_type, expected_type):
                   raise TypeError(
                       f"Type mismatch: expected {expected_type}, got {value_type}"
                   )
               
               # Add to environment
               self.env.bind(decl.name, expected_type)
           
           elif isinstance(decl, FunctionDecl):
               # Create new scope for function body
               func_env = self.env.new_scope()
               
               # Add parameters to function's scope
               param_types = []
               for param_name, param_type_str in decl.parameters:
                   param_type = self.parse_type_annotation(param_type_str)
                   func_env.bind(param_name, param_type)
                   param_types.append(param_type)
               
               # Check function body in new scope
               old_env = self.env
               self.env = func_env
               
               for stmt in decl.body:
                   self.check_declaration(stmt)
               
               # Restore environment
               self.env = old_env
               
               # Add function to environment
               return_type = self.parse_type_annotation(decl.return_type)
               func_type = FunctionType(param_types, return_type)
               self.env.bind(decl.name, func_type)
       
       def infer_type(self, expr):
           """Infer the type of an expression"""
           if isinstance(expr, Literal):
               if isinstance(expr.value, int):
                   return IntType(32)  # Default to Int32
               elif isinstance(expr.value, bool):
                   return BoolType()
           
           elif isinstance(expr, Variable):
               return self.env.lookup(expr.name)
           
           elif isinstance(expr, BinaryOp):
               left_type = self.infer_type(expr.left)
               right_type = self.infer_type(expr.right)
               
               if expr.op in ['+', '-', '*', '/']:
                   # Arithmetic: both must be Int, result is Int
                   if not isinstance(left_type, IntType):
                       raise TypeError(f"Expected Int, got {left_type}")
                   if not isinstance(right_type, IntType):
                       raise TypeError(f"Expected Int, got {right_type}")
                   
                   # For now, require same width
                   if left_type.width != right_type.width:
                       raise TypeError(
                           f"Arithmetic requires same width: {left_type} vs {right_type}"
                       )
                   
                   return left_type
               
               elif expr.op in ['<', '>', '<=', '>=']:
                   # Comparison: both must be Int, result is Bool
                   if not isinstance(left_type, IntType):
                       raise TypeError(f"Expected Int, got {left_type}")
                   if not isinstance(right_type, IntType):
                       raise TypeError(f"Expected Int, got {right_type}")
                   return BoolType()
               
               elif expr.op == '==':
                   # Equality: types must match, result is Bool
                   if not self.types_equal(left_type, right_type):
                       raise TypeError(
                           f"Equality requires matching types: {left_type} vs {right_type}"
                       )
                   return BoolType()
           
           elif isinstance(expr, IfExpr):
               # Condition must be Bool
               cond_type = self.infer_type(expr.condition)
               if not isinstance(cond_type, BoolType):
                   raise TypeError(f"Condition must be Bool, got {cond_type}")
               
               # Both branches must have same type
               then_type = self.infer_type(expr.then_branch)
               else_type = self.infer_type(expr.else_branch)
               
               if not self.types_equal(then_type, else_type):
                   raise TypeError(
                       f"If branches must have same type: {then_type} vs {else_type}"
                   )
               
               return then_type
           
           elif isinstance(expr, Call):
               # Look up function type
               func_type = self.env.lookup(expr.function)
               
               if not isinstance(func_type, FunctionType):
                   raise TypeError(f"{expr.function} is not a function")
               
               # Check argument count
               if len(expr.arguments) != len(func_type.param_types):
                   raise TypeError(
                       f"Expected {len(func_type.param_types)} arguments, "
                       f"got {len(expr.arguments)}"
                   )
               
               # Check argument types
               for i, (arg, expected_type) in enumerate(
                   zip(expr.arguments, func_type.param_types)
               ):
                   arg_type = self.infer_type(arg)
                   if not self.types_equal(arg_type, expected_type):
                       raise TypeError(
                           f"Argument {i}: expected {expected_type}, got {arg_type}"
                       )
               
               return func_type.return_type
           
           else:
               raise TypeError(f"Unknown expression type: {type(expr)}")
       
       def types_equal(self, t1, t2):
           """Check if two types are equal"""
           if type(t1) != type(t2):
               return False
           
           if isinstance(t1, IntType):
               return t1.width == t2.width
           elif isinstance(t1, BoolType):
               return True
           elif isinstance(t1, FunctionType):
               if len(t1.param_types) != len(t2.param_types):
                   return False
               for p1, p2 in zip(t1.param_types, t2.param_types):
                   if not self.types_equal(p1, p2):
                       return False
               return self.types_equal(t1.return_type, t2.return_type)
           
           return False
       
       def parse_type_annotation(self, type_str):
           """Convert type string to Type object"""
           if type_str == "Int8":
               return IntType(8)
           elif type_str == "Int16":
               return IntType(16)
           elif type_str == "Int32":
               return IntType(32)
           elif type_str == "Bool":
               return BoolType()
           else:
               raise TypeError(f"Unknown type: {type_str}")
   ```

3. *Test Type Checker*:
   ```python
   def test_type_checker():
       # Valid program
       source = """
       let x: Int32 = 2 + 3
       let y: Bool = x > 0
       """
       ast = parse(source)
       checker = TypeChecker()
       checker.check_program(ast)  # Should not raise
       
       # Invalid program
       source = """
       let x: Int32 = 2 + true
       """
       ast = parse(source)
       checker = TypeChecker()
       try:
           checker.check_program(ast)
           assert False, "Should have raised TypeError"
       except TypeError as e:
           assert "Int32" in str(e) and "Bool" in str(e)
   ```

*Common Pitfalls*:
- Forgetting to check function return types
- Not handling scoping correctly (parameters vs outer variables)
- Poor error messages (always include location info!)

*Deliverable*: Type checker handling expressions and basic declarations

*Resources*:
- DESIGN.md Part II (Type System Design)
- DESIGN.md Section 4.4 (Type System Rules)

##### Week 8: Type Checker - Part 2 (Functions and Scoping)

*Your Task*: Handle function definitions, calls, and proper scoping.

*Key Concepts*:

1. *Lexical Scoping*: Inner scopes can see outer variables
   ```
   let x: Int32 = 5
   fn foo() -> Int32 {
       let y: Int32 = x + 1  // Can see x
       y
   }
   ```

2. *Function Type Checking*: Verify body matches return type
   ```python
   def check_function_body(self, func_decl):
       # .. set up parameter types in new scope ..
       
       # Check body
       body_type = None
       for stmt in func_decl.body:
           if isinstance(stmt, ReturnStmt):
               body_type = self.infer_type(stmt.value)
           else:
               self.check_declaration(stmt)
       
       # Verify return type matches
       expected_return = self.parse_type_annotation(func_decl.return_type)
       if body_type is None:
           raise TypeError(f"Function {func_decl.name} missing return statement")
       if not self.types_equal(body_type, expected_return):
           raise TypeError(
               f"Function {func_decl.name} returns {body_type}, expected {expected_return}"
           )
   ```

3. *Recursive Functions*: Add function to environment before checking body
   ```python
   # This lets factorial call itself
   func_type = FunctionType(param_types, return_type)
   self.env.bind(decl.name, func_type)  # Add BEFORE checking body
   self.check_function_body(decl)
   ```

*Deliverable*: Complete type checker with function support and tests

##### Week 9: Error Messages and Type Inference (Optional Enhancement)

*Your Task*: Make your compiler user-friendly.

*Good Error Messages*:

```python
class TypeError(Exception):
    def __init__(self, message, location=None):
        self.message = message
        self.location = location
    
    def __str__(self):
        if self.location:
            return f"Type error at line {self.location.line}: {self.message}"
        return f"Type error: {self.message}"

# When raising:
raise TypeError(
    f"Cannot add {left_type} and {right_type}",
    location=expr.location  # Store location in AST nodes!
)
```

*Basic Type Inference* (makes your language nicer to use):

```python
def infer_var_type(self, var_decl):
    """Infer type from initializer if not annotated"""
    if var_decl.type_annotation:
        expected = self.parse_type_annotation(var_decl.type_annotation)
        actual = self.infer_type(var_decl.value)
        if not self.types_equal(expected, actual):
            raise TypeError(f"Type mismatch: expected {expected}, got {actual}")
        return expected
    else:
        # Infer from value
        return self.infer_type(var_decl.value)
```

*Deliverable*: 
- Helpful error messages with line numbers
- (Optional) Basic type inference
- Documentation of your type system



#### Phase 4: Code Generation (Weeks 10-12)

##### Week 10: Intermediate Representation (IR)

*Your Task*: Convert AST to three-address code (TAC).

*Three-Address Code Format*:

Each instruction has at most 3 operands:
```
t1 = 2
t2 = 3
t3 = t1 + t2
t4 = t3 * 4
```

*Implementation*:

1. *Define IR Instructions*:
   ```python
   from dataclasses import dataclass
   
   class IRInstruction:
       pass
   
   @dataclass
   class LoadConst(IRInstruction):
       dest: str  # temporary variable name
       value: int | bool
       
       def __str__(self):
           return f"{self.dest} = {self.value}"
   
   @dataclass
   class BinaryOp(IRInstruction):
       dest: str
       op: str  # "+", "-", "*", etc.
       left: str
       right: str
       
       def __str__(self):
           return f"{self.dest} = {self.left} {self.op} {self.right}"
   
   @dataclass
   class Copy(IRInstruction):
       dest: str
       source: str
       
       def __str__(self):
           return f"{self.dest} = {self.source}"
   
   @dataclass
   class Label(IRInstruction):
       name: str
       
       def __str__(self):
           return f"{self.name}:"
   
   @dataclass
   class Jump(IRInstruction):
       target: str
       
       def __str__(self):
           return f"goto {self.target}"
   
   @dataclass
   class CondJump(IRInstruction):
       condition: str
       target: str
       
       def __str__(self):
           return f"if {self.condition} goto {self.target}"
   
   @dataclass
   class Call(IRInstruction):
       dest: str  # where to store result
       function: str
       args: List[str]
       
       def __str__(self):
           args_str = ", ".join(self.args)
           return f"{self.dest} = call {self.function}({args_str})"
   
   @dataclass
   class Return(IRInstruction):
       value: str
       
       def __str__(self):
           return f"return {self.value}"
   
   @dataclass
   class Param(IRInstruction):
       name: str
       index: int
       
       def __str__(self):
           return f"{self.name} = param {self.index}"
   ```

2. *IR Generator*:
   ```python
   class IRGenerator:
       def __init__(self):
           self.instructions = []
           self.temp_counter = 0
           self.label_counter = 0
       
       def new_temp(self):
           """Generate unique temporary variable"""
           temp = f"t{self.temp_counter}"
           self.temp_counter += 1
           return temp
       
       def new_label(self, prefix="L"):
           """Generate unique label"""
           label = f"{prefix}{self.label_counter}"
           self.label_counter += 1
           return label
       
       def emit(self, instruction):
           """Add instruction to list"""
           self.instructions.append(instruction)
       
       def generate_program(self, program):
           """Generate IR for entire program"""
           for decl in program.declarations:
               self.generate_declaration(decl)
           return self.instructions
       
       def generate_declaration(self, decl):
           if isinstance(decl, VarDecl):
               # Generate code for value
               value_temp = self.generate_expr(decl.value)
               # Store in variable (use variable name as temp)
               self.emit(Copy(decl.name, value_temp))
           
           elif isinstance(decl, FunctionDecl):
               # Function label
               self.emit(Label(decl.name))
               
               # Load parameters
               for i, (param_name, _) in enumerate(decl.parameters):
                   self.emit(Param(param_name, i))
               
               # Generate body
               for stmt in decl.body:
                   self.generate_declaration(stmt)
       
       def generate_expr(self, expr):
           """Generate IR for expression, return temp holding result"""
           if isinstance(expr, Literal):
               temp = self.new_temp()
               self.emit(LoadConst(temp, expr.value))
               return temp
           
           elif isinstance(expr, Variable):
               # Variable name is its "temporary"
               return expr.name
           
           elif isinstance(expr, BinaryOp):
               left_temp = self.generate_expr(expr.left)
               right_temp = self.generate_expr(expr.right)
               result_temp = self.new_temp()
               self.emit(BinaryOp(result_temp, expr.op, left_temp, right_temp))
               return result_temp
           
           elif isinstance(expr, IfExpr):
               # Generate:
               #   cond_temp = <condition>
               #   if_false cond_temp goto L_else
               #   then_temp = <then branch>
               #   result = then_temp
               #   goto L_end
               # L_else:
               #   else_temp = <else branch>
               #   result = else_temp
               # L_end:
               
               cond_temp = self.generate_expr(expr.condition)
               result_temp = self.new_temp()
               
               L_else = self.new_label("else")
               L_end = self.new_label("end")
               
               # if_false cond goto L_else
               self.emit(CondJump(cond_temp, L_else))
               
               # Then branch
               then_temp = self.generate_expr(expr.then_branch)
               self.emit(Copy(result_temp, then_temp))
               self.emit(Jump(L_end))
               
               # Else branch
               self.emit(Label(L_else))
               else_temp = self.generate_expr(expr.else_branch)
               self.emit(Copy(result_temp, else_temp))
               
               self.emit(Label(L_end))
               
               return result_temp
           
           elif isinstance(expr, Call):
               # Generate arguments
               arg_temps = [self.generate_expr(arg) for arg in expr.arguments]
               result_temp = self.new_temp()
               self.emit(Call(result_temp, expr.function, arg_temps))
               return result_temp
           
           else:
               raise ValueError(f"Unknown expression type: {type(expr)}")
   ```

3. *Test IR Generation*:
   ```python
   def test_ir_gen():
       source = """
       fn factorial(n: Int32) -> Int32 {
           if n <= 1 then
               1
           else
               n * factorial(n - 1)
       }
       """
       ast = parse(source)
       type_check(ast)
       
       ir_gen = IRGenerator()
       instructions = ir_gen.generate_program(ast)
       
       # Print for inspection
       for instr in instructions:
           print(instr)
       
       # Should see:
       # factorial:
       # n = param 0
       # t0 = 1
       # t1 = n <= t0
       # if_false t1 goto L_else0
       # ..
   ```

*Deliverable*: 
- IR generator for all language constructs
- Pretty printer for IR
- Tests showing correct translation

*Resources*:
- DESIGN.md Part III (Intermediate Representation)
- DESIGN.md Section 7 (Three-Address Code IR)

##### Week 11: VM Code Generation

*Your Task*: Convert IR to VM bytecode.

*Translation Strategy*:

Main tasks:
1. Map temporaries to local variable slots
2. Translate operations to stack-based VM instructions
3. Handle control flow (jumps, labels)

*Implementation*:

1. *Local Slot Allocation*:
   ```python
   class SlotAllocator:
       def __init__(self):
           self.slots = {}  # temp_name -> slot_number
           self.next_slot = 0
       
       def allocate(self, temp_name):
           """Allocate a slot for a temporary"""
           if temp_name not in self.slots:
               self.slots[temp_name] = self.next_slot
               self.next_slot += 1
           return self.slots[temp_name]
       
       def get(self, temp_name):
           """Get slot number for temporary"""
           return self.slots[temp_name]
   ```

2. *VM Code Generator*:
   ```python
   class VMCodeGenerator:
       def __init__(self):
           self.bytecode = bytearray()
           self.label_positions = {}  # label -> byte offset
           self.label_fixups = []  # (label, offset) to fix later
       
       def generate(self, ir_instructions):
           """Generate VM bytecode from IR"""
           # First pass: allocate slots
           allocator = SlotAllocator()
           for instr in ir_instructions:
               self.allocate_instruction_slots(instr, allocator)
           
           # Second pass: generate code
           for instr in ir_instructions:
               self.generate_instruction(instr, allocator)
           
           # Third pass: fix up jump targets
           self.fixup_jumps()
           
           return bytes(self.bytecode)
       
       def allocate_instruction_slots(self, instr, allocator):
           """Pre-allocate slots for instruction operands"""
           if isinstance(instr, LoadConst):
               allocator.allocate(instr.dest)
           elif isinstance(instr, BinaryOp):
               allocator.allocate(instr.dest)
               allocator.allocate(instr.left)
               allocator.allocate(instr.right)
           elif isinstance(instr, Copy):
               allocator.allocate(instr.dest)
               allocator.allocate(instr.source)
           # .. other instructions
       
       def generate_instruction(self, instr, allocator):
           """Generate VM instructions for single IR instruction"""
           if isinstance(instr, LoadConst):
               # PUSH_I32 value
               # STORE_LOCAL slot
               self.emit_opcode(0x03)  # PUSH_I32
               self.emit_i32(instr.value)
               self.emit_opcode(0x81)  # STORE_LOCAL
               self.emit_i16(allocator.get(instr.dest))
           
           elif isinstance(instr, BinaryOp):
               # LOAD_LOCAL left
               # LOAD_LOCAL right
               # ADD_I32 (or other op)
               # STORE_LOCAL dest
               self.emit_opcode(0x80)  # LOAD_LOCAL
               self.emit_i16(allocator.get(instr.left))
               self.emit_opcode(0x80)  # LOAD_LOCAL
               self.emit_i16(allocator.get(instr.right))
               
               # Operation
               if instr.op == '+':
                   self.emit_opcode(0x12)  # ADD_I32
               elif instr.op == '-':
                   self.emit_opcode(0x15)  # SUB_I32
               elif instr.op == '*':
                   self.emit_opcode(0x18)  # MUL_I32
               elif instr.op == '<':
                   self.emit_opcode(0x32)  # LT_I32
               # .. other ops
               
               self.emit_opcode(0x81)  # STORE_LOCAL
               self.emit_i16(allocator.get(instr.dest))
           
           elif isinstance(instr, Label):
               # Record position for jump fixup
               self.label_positions[instr.name] = len(self.bytecode)
           
           elif isinstance(instr, Jump):
               # JUMP offset (to be fixed up)
               self.emit_opcode(0x60)  # JUMP
               fixup_pos = len(self.bytecode)
               self.emit_i32(0)  # Placeholder
               self.label_fixups.append((instr.target, fixup_pos))
           
           elif isinstance(instr, CondJump):
               # LOAD_LOCAL condition
               # JUMP_IF_FALSE offset
               self.emit_opcode(0x80)  # LOAD_LOCAL
               self.emit_i16(allocator.get(instr.condition))
               self.emit_opcode(0x62)  # JUMP_IF_FALSE
               fixup_pos = len(self.bytecode)
               self.emit_i32(0)  # Placeholder
               self.label_fixups.append((instr.target, fixup_pos))
           
           elif isinstance(instr, Call):
               # LOAD_LOCAL for each argument
               for arg in instr.args:
                   self.emit_opcode(0x80)  # LOAD_LOCAL
                   self.emit_i16(allocator.get(arg))
               
               # CALL function arity
               func_index = self.get_function_index(instr.function)
               self.emit_opcode(0x70)  # CALL
               self.emit_i16(func_index)
               self.emit_byte(len(instr.args))
               
               # STORE_LOCAL result
               self.emit_opcode(0x81)  # STORE_LOCAL
               self.emit_i16(allocator.get(instr.dest))
           
           elif isinstance(instr, Return):
               # LOAD_LOCAL value
               # RETURN
               self.emit_opcode(0x80)  # LOAD_LOCAL
               self.emit_i16(allocator.get(instr.value))
               self.emit_opcode(0x71)  # RETURN
       
       def fixup_jumps(self):
           """Fix jump offsets now that we know label positions"""
           for label, fixup_pos in self.label_fixups:
               target_pos = self.label_positions[label]
               offset = target_pos - (fixup_pos + 4)  # +4 for the offset itself
               
               # Write offset at fixup_pos
               self.bytecode[fixup_pos:fixup_pos+4] = offset.to_bytes(
                   4, byteorder='little', signed=True
               )
       
       def emit_opcode(self, opcode):
           self.bytecode.append(opcode)
       
       def emit_byte(self, value):
           self.bytecode.append(value & 0xFF)
       
       def emit_i16(self, value):
           self.bytecode.extend(value.to_bytes(2, byteorder='little', signed=True))
       
       def emit_i32(self, value):
           self.bytecode.extend(value.to_bytes(4, byteorder='little', signed=True))
   ```

3. *Function Table*:
   ```python
   class Program:
       def __init__(self):
           self.functions = {}  # name -> function_info
           self.function_list = []  # ordered list for indexing
       
       def add_function(self, name, bytecode, num_locals, max_stack):
           func_info = {
               'name': name,
               'bytecode': bytecode,
               'num_locals': num_locals,
               'max_stack': max_stack,
               'index': len(self.function_list)
           }
           self.functions[name] = func_info
           self.function_list.append(func_info)
   ```

*Deliverable*:
- VM code generator
- Bytecode output format (see VM-SPECIFICATION.md Section 5)
- Tests comparing IR and VM code

*Resources*:
- VM-SPECIFICATION.md Section 4 (Instruction Set)
- DESIGN.md Part IV (Virtual Machine Code Generation)

##### Week 12: Virtual Machine Implementation

*Your Task*: Build the VM that executes your bytecode.

*Core VM Structure*:

```python
class VirtualMachine:
    def __init__(self, program):
        self.program = program
        self.stack = []  # Operand stack
        self.frames = []  # Call frames
        self.globals = {}  # Global variables
        self.pc = 0  # Program counter
        self.current_function = None
    
    def run(self, entry_point="main"):
        """Execute program starting at entry point"""
        # Find entry function
        func = self.program.functions[entry_point]
        
        # Create initial frame
        self.push_frame(func, [])
        
        # Execute until halt or return from main
        try:
            while True:
                self.execute_instruction()
        except VMHalt:
            pass
        
        # Return top of stack (result)
        if self.stack:
            return self.stack[-1]
        return None
    
    def push_frame(self, function, arguments):
        """Push new activation record"""
        frame = {
            'function': function,
            'locals': [0] * function['num_locals'],
            'return_pc': self.pc,
            'saved_sp': len(self.stack)
        }
        
        # Copy arguments to locals
        for i, arg in enumerate(arguments):
            frame['locals'][i] = arg
        
        self.frames.append(frame)
        self.current_function = function
        self.pc = 0  # Start at beginning of function
    
    def pop_frame(self):
        """Pop activation record and restore state"""
        frame = self.frames.pop()
        self.pc = frame['return_pc']
        
        if self.frames:
            self.current_function = self.frames[-1]['function']
        else:
            raise VMHalt()
    
    def fetch_byte(self):
        """Read next byte from bytecode"""
        byte = self.current_function['bytecode'][self.pc]
        self.pc += 1
        return byte
    
    def fetch_i16(self):
        """Read 16-bit signed integer"""
        bytes_data = self.current_function['bytecode'][self.pc:self.pc+2]
        self.pc += 2
        return int.from_bytes(bytes_data, byteorder='little', signed=True)
    
    def fetch_i32(self):
        """Read 32-bit signed integer"""
        bytes_data = self.current_function['bytecode'][self.pc:self.pc+4]
        self.pc += 4
        return int.from_bytes(bytes_data, byteorder='little', signed=True)
    
    def execute_instruction(self):
        """Fetch and execute one instruction"""
        opcode = self.fetch_byte()
        
        if opcode == 0x03:  # PUSH_I32
            value = self.fetch_i32()
            self.stack.append(value)
        
        elif opcode == 0x05:  # POP
            self.stack.pop()
        
        elif opcode == 0x06:  # DUP
            self.stack.append(self.stack[-1])
        
        elif opcode == 0x07:  # SWAP
            self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
        
        elif opcode == 0x12:  # ADD_I32
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a + b)
        
        elif opcode == 0x15:  # SUB_I32
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a - b)
        
        elif opcode == 0x18:  # MUL_I32
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a * b)
        
        elif opcode == 0x1B:  # DIV_I32
            b = self.stack.pop()
            if b == 0:
                raise RuntimeError("Division by zero")
            a = self.stack.pop()
            self.stack.append(a // b)
        
        elif opcode == 0x32:  # LT_I32
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a < b else 0)
        
        elif opcode == 0x38:  # GT_I32
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a > b else 0)
        
        elif opcode == 0x3E:  # EQ_I32
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a == b else 0)
        
        elif opcode == 0x60:  # JUMP
            offset = self.fetch_i32()
            self.pc += offset
        
        elif opcode == 0x61:  # JUMP_IF_TRUE
            offset = self.fetch_i32()
            condition = self.stack.pop()
            if condition:
                self.pc += offset
        
        elif opcode == 0x62:  # JUMP_IF_FALSE
            offset = self.fetch_i32()
            condition = self.stack.pop()
            if not condition:
                self.pc += offset
        
        elif opcode == 0x70:  # CALL
            func_index = self.fetch_i16()
            arity = self.fetch_byte()
            
            # Pop arguments
            args = []
            for _ in range(arity):
                args.append(self.stack.pop())
            args.reverse()  # They were pushed in order
            
            # Get function
            func = self.program.function_list[func_index]
            
            # Push new frame
            self.push_frame(func, args)
        
        elif opcode == 0x71:  # RETURN
            return_value = self.stack.pop()
            self.pop_frame()
            self.stack.append(return_value)
        
        elif opcode == 0x80:  # LOAD_LOCAL
            index = self.fetch_i16()
            value = self.frames[-1]['locals'][index]
            self.stack.append(value)
        
        elif opcode == 0x81:  # STORE_LOCAL
            index = self.fetch_i16()
            value = self.stack.pop()
            self.frames[-1]['locals'][index] = value
        
        elif opcode == 0xFF:  # HALT
            raise VMHalt()
        
        else:
            raise RuntimeError(f"Unknown opcode: 0x{opcode:02x}")

class VMHalt(Exception):
    """Exception to halt VM execution"""
    pass
```

*Testing the VM*:

```python
def test_factorial():
    # Compile this program:
    # fn factorial(n: Int32) -> Int32 {
    #   if n <= 1 then 1 else n * factorial(n - 1)
    # }
    
    source = """
    fn factorial(n: Int32) -> Int32 {
        if n <= 1 then
            1
        else
            n * factorial(n - 1)
    }
    """
    
    # Parse, type-check, generate IR, compile to bytecode
    ast = parse(source)
    type_check(ast)
    ir = generate_ir(ast)
    program = generate_vm_code(ir)
    
    # Run
    vm = VirtualMachine(program)
    
    # Call factorial(5)
    # (Need to add mechanism to call with arguments)
    result = vm.call_function("factorial", [5])
    
    assert result == 120
```

*Deliverable*:
- Working VM implementation
- Test suite with various programs
- Performance measurements (optional)



#### Phase 5: Polish and Extensions (Weeks 13-15)

##### Week 13: Standard Library

*Your Task*: Add useful built-in functions.

*Essential Functions*:

1. *I/O Functions*:
   ```python
   # Native functions (implemented in host language)
   NATIVE_FUNCTIONS = {
       'print_i32': {
           'id': 0,
           'arity': 1,
           'implementation': lambda x: print(x)
       },
       'print_bool': {
           'id': 1,
           'arity': 1,
           'implementation': lambda x: print('true' if x else 'false')
       },
       'read_i32': {
           'id': 2,
           'arity': 0,
           'implementation': lambda: int(input("Enter number: "))
       }
   }
   ```

2. *Math Functions* (optional):
   - `abs(x)`, `max(x, y)`, `min(x, y)`
   - `pow(x, n)` (integer exponentiation)

3. *String Functions* (if you added strings):
   - `print_string(s)`, `string_length(s)`, `string_concat(s1, s2)`

*Implementation in VM*:

```python
def execute_native_call(self, native_id, arity):
    """Execute native function"""
    # Pop arguments
    args = []
    for _ in range(arity):
        args.append(self.stack.pop())
    args.reverse()
    
    # Find and call native function
    for name, info in NATIVE_FUNCTIONS.items():
        if info['id'] == native_id:
            result = info['implementation'](*args)
            if result is not None:
                self.stack.append(result)
            return
    
    raise RuntimeError(f"Unknown native function: {native_id}")
```

*Deliverable*:
- Standard library documentation
- Example programs using stdlib

##### Week 14: Testing and Debugging

*Your Task*: Build comprehensive test suite and debugging tools.

*Test Categories*:

1. *Unit Tests*: Each compiler phase
   - Lexer: all token types
   - Parser: all grammar rules
   - Type checker: valid and invalid programs
   - Code gen: each IR instruction type
   - VM: each opcode

2. *Integration Tests*: Complete programs
   ```python
   def test_fibonacci():
       source = """
       fn fib(n: Int32) -> Int32 {
           if n <= 1 then
               n
           else
               fib(n-1) + fib(n-2)
       }
       let result: Int32 = fib(10)
       """
       assert compile_and_run(source) == 55
   ```

3. *Error Tests*: Verify error messages
   ```python
   def test_type_error():
       source = "let x: Int32 = true"
       try:
           compile(source)
           assert False, "Should have raised error"
       except TypeError as e:
           assert "Int32" in str(e) and "Bool" in str(e)
   ```

*Debugging Tools*:

1. *VM Trace Mode*:
   ```python
   class VirtualMachine:
       def __init__(self, program, trace=False):
           self.trace = trace
           # ..
       
       def execute_instruction(self):
           if self.trace:
               print(f"PC={self.pc:04x} Stack={self.stack}")
           
           opcode = self.fetch_byte()
           # .. execute ..
   ```

2. *Disassembler*:
   ```python
   def disassemble(bytecode):
       """Pretty-print bytecode"""
       pc = 0
       while pc < len(bytecode):
           opcode = bytecode[pc]
           print(f"{pc:04x}: ", end="")
           
           if opcode == 0x03:  # PUSH_I32
               value = int.from_bytes(bytecode[pc+1:pc+5], 'little', signed=True)
               print(f"PUSH_I32 {value}")
               pc += 5
           elif opcode == 0x12:
               print("ADD_I32")
               pc += 1
           # .. more opcodes
   ```

*Deliverable*:
- Comprehensive test suite (aim for >80% coverage)
- Debugging tools documentation
- Test results and coverage report

##### Week 15: Documentation and Presentation

*Your Task*: Document everything and prepare demo.

*Documentation Checklist*:

1. *User Guide*:
   - Language syntax reference
   - Type system explanation
   - Example programs
   - Standard library reference

2. *Developer Guide*:
   - Architecture overview
   - How to extend the language
   - Code organization
   - Build instructions

3. *Design Document*:
   - Design decisions and rationale
   - Comparison with other languages
   - Known limitations
   - Future improvements

4. *API Documentation*:
   - All public classes and functions
   - Usage examples

*Demo Program Ideas*:

1. *Classic Algorithms*:
   ```
   fn quicksort(arr: [Int32]) -> [Int32]
   fn binary_search(arr: [Int32], target: Int32) -> Int32
   ```

2. *Games*:
   ```
   fn guess_the_number() -> ()
   fn tic_tac_toe() -> ()
   ```

3. *Utilities*:
   ```
   fn fizzbuzz(n: Int32) -> ()
   fn is_prime(n: Int32) -> Bool
   ```

*Presentation Structure* (15-20 minutes):

1. Introduction (2 min)
   - What you built
   - Why it's interesting

2. Language Demo (5 min)
   - Show example programs
   - Highlight unique features

3. Architecture (5 min)
   - Compilation pipeline diagram
   - Key design decisions

4. Technical Deep Dive (5 min)
   - Most interesting challenge you solved
   - Show some implementation code

5. Conclusion (2 min)
   - What you learned
   - What you'd do differently
   - Future work

*Deliverable*:
- Complete documentation
- Demo programs
- Presentation slides
- Final project report



### Part 3: Theoretical Foundations

#### Type Theory Essentials

*Why Study Type Theory?*

Understanding the theory helps you:
- Design better type systems
- Prove your compiler is correct
- Understand error messages
- Implement advanced features

*Key Concepts*:

1. *Type Safety ("Well-typed programs don't go wrong")*
   
   Two properties guarantee safety:
   
   - *Progress*: Well-typed terms don't get stuck
     - Either a term is a value, or it can take a step
   
   - *Preservation*: Types are preserved by evaluation
     - If `e: T` and `e → e'`, then `e': T`

2. *Type Inference*
   
   *Algorithm W* (Hindley-Milner type inference):
   ```
   1. Generate constraints by traversing AST
   2. Solve constraints via unification
   3. Apply solution to get concrete types
   ```
   
   See DESIGN.md Section 5 for full algorithm.

3. *Subtyping*
   
   If you add subtyping:
   ```
   Int8 <: Int16 <: Int32  (smaller types can be used as larger)
   ```
   
   Need to add implicit conversions in code gen.

#### Formal Semantics

*Three Approaches*:

1. *Operational Semantics* (what we use)
   - Describes how programs execute step-by-step
   - Two styles: big-step (⇓) and small-step (→)
   - See DESIGN.md Section 3

2. *Denotational Semantics*
   - Maps programs to mathematical objects
   - Good for reasoning about equivalence
   - More abstract

3. *Axiomatic Semantics*
   - Uses logic to specify behavior
   - Hoare triples: `{P} C {Q}`
   - Good for program verification

Formal semantics let you:
- Prove compiler correctness
- Verify optimizations preserve meaning
- Generate test cases automatically
- Communicate precisely about behavior

#### Compiler Optimisation Theory

Recapitulation of [ch05](./../../../ch05/):

1. *Data Flow Analysis*
   - Live variable analysis
   - Reaching definitions
   - Available expressions

2. *SSA Form* (Static Single Assignment)
   - Each variable assigned exactly once
   - Makes optimization easier
   - Used by LLVM and modern compilers

3. *Graph Algorithms*
   - Control flow graphs (CFGs)
   - Dominance and post-dominance
   - Loop detection



### Part 4: Tools and Resources

#### Development Tools

*Parser Generators*:

| Tool | Language | Style | Difficulty |
|------|----------|-------|------------|
| ANTLR | Java/Python/C++/JS | LL(*) | Medium |
| Yacc/Bison | C/C++ | LALR | Medium |
| Menhir | OCaml | LR | Medium |
| Nearley | JavaScript | Earley | Easy |
| nom | Rust | Parser combinators | Medium |
| Hand-written | Any | Recursive descent | Easy-Medium |

*Recommendation*: Start with hand-written recursive descent.
It's educational and you'll understand what parser generators do.

*Testing Frameworks*:

- Python: `pytest`, `unittest`
- JavaScript: `Jest`, `Mocha`
- Java: `JUnit`
- C++: `Google Test`, `Catch2`
- Rust: built-in test framework

*Version Control*:

Use Git! Commit often. Suggested workflow:
```bash
main           # stable, working code
├─ dev         # integration branch
   ├─ feature/lexer
   ├─ feature/parser
   └─ feature/typechecker
```

#### Learning Resources

*Books*:

1. *Essentials* (read these):
   - *Crafting Interpreters* by Bob Nystrom
     - Best practical introduction
     - Walks through complete implementation
   
   - *Engineering a Compiler* by Cooper & Torczon
     - Comprehensive, modern approach
     - Good balance of theory and practice

2. *Advanced* (reference material):
   - *Types and Programming Languages* by Benjamin Pierce
     - The definitive type theory textbook
     - Mathematical but accessible
   
   - *Modern Compiler Implementation in ML* by Andrew Appel
     - Complete compiler in ML
     - Available in C and Java versions too

3. *Specific Topics*:
   - *Compilers: Principles, Techniques, and Tools* (Dragon Book)
     - Classic reference
     - Comprehensive but dense
   
   - *Static Program Analysis* by Anders Møller & Michael Schwartzbach
     - Deep dive into analysis techniques


#### Debugging Strategies

*Common Problems and Solutions*:

1. *Lexer Issues*:
   - Problem: Wrong tokens
   - Debug: Print each token as it's scanned
   - Fix: Check regex/state machine carefully

2. *Parser Issues*:
   - Problem: Syntax errors or wrong AST structure
   - Debug: Print AST at each step
   - Fix: Check grammar, ensure proper precedence

3. *Type Checker Issues*:
   - Problem: Wrong type errors or missed errors
   - Debug: Trace type inference step-by-step
   - Fix: Check type rules against formal specification

4. *Code Gen Issues*:
   - Problem: Wrong bytecode
   - Debug: Compare IR and VM code side-by-side
   - Fix: Check instruction translation tables

5. *VM Issues*:
   - Problem: Wrong results or crashes
   - Debug: Trace execution with stack dumps
   - Fix: Verify each opcode implementation

*General Strategy*:

1. Start with the simplest possible program
2. Add complexity incrementally
3. Test after each addition
4. When stuck, add more logging/tracing
5. Use a debugger to step through code



### Part 5: Assessment and Grading

#### Project Milestones

*Minimum Viable Product (60% of grade)*:

- [ ] Lexer handles basic tokens
- [ ] Parser builds AST for simple programs
- [ ] Type checker validates types
- [ ] Code generator produces valid bytecode
- [ ] VM executes simple programs correctly
- [ ] Documentation of architecture

*Standard Features (30% of grade)*:

- [ ] Comprehensive test suite
- [ ] Good error messages with locations
- [ ] Functions with parameters and return values
- [ ] Control flow (if/else)
- [ ] Example programs demonstrating features
- [ ] User guide and developer guide

*Advanced Features (10% of grade)*:

Choose at least one:
- [ ] Arrays or other data structures
- [ ] First-class functions/closures
- [ ] Type inference
- [ ] Basic optimization passes
- [ ] Garbage collection
- [ ] Exceptional error handling (try/catch)
- [ ] Module system

#### Evaluation Criteria

*Correctness (40%)*:
- Programs compile and run correctly
- Type system catches errors
- VM executes as specified
- Edge cases handled

*Code Quality (20%)*:
- Well-organized, readable code
- Appropriate abstractions
- Good naming conventions
- Commented where necessary

*Testing (15%)*:
- Comprehensive test coverage
- Tests for both valid and invalid inputs
- Integration tests for full pipeline

*Documentation (15%)*:
- Clear explanations of design
- User guide for language
- Developer guide for code
- Example programs

*Presentation (10%)*:
- Clear explanation of project
- Live demo of interesting programs
- Discussion of challenges and solutions



### Part 6: Common Pitfalls and How to Avoid Them

#### Scope Creep

*Pitfall*: Trying to add too many features.

*Solution*:
1. Start with bare minimum (integers, +, -, if/else, functions)
2. Get that working completely
3. Then add features one at a time
4. Each addition should take <1 week

#### Poor Error Messages

*Pitfall*: Compiler gives unhelpful errors like "Syntax error".

*Solution*:
```python
# Bad
raise SyntaxError("Parse error")

# Good
raise SyntaxError(
    f"Expected ')' after function arguments at line {token.line}, column {token.column}\n"
    f"  {source_line}\n"
    f"  {' ' * (token.column - 1)}^"
)
```

Always include:
- File name
- Line and column number
- What was expected
- What was found
- Suggestion for fix (if possible)

#### Not Testing Incrementally

*Pitfall*: Writing entire compiler before testing anything.

*Solution*:
- Test each component as you build it
- Write tests BEFORE implementation (TDD)
- Run full test suite after every change

#### Misunderstanding Stack vs Register Machines

*Pitfall*: Generating code that doesn't match VM model.

*Solution*:
- Trace example by hand on paper first
- Draw stack contents at each step
- Verify against VM specification
- Use VM trace mode to debug

#### Type System Bugs

*Pitfall*: Type checker accepts invalid programs or rejects valid ones.

*Solution*:
- Implement type checker EXACTLY per formal rules
- Test with many examples (valid and invalid)
- Compare behavior with another typed language
- Use property-based testing

#### Off-by-One Errors in Bytecode

*Pitfall*: Jump offsets or local indices wrong by one.

*Solution*:
- Always count from 0
- Draw memory layouts
- Write unit tests for each instruction
- Use assertions liberally



### Part 7: Going Further

#### After Completing the Basic Project

If you finish early or want to continue:

1. *Add More Features*:
   - Arrays and indexing
   - Strings and string operations
   - Structs/records
   - Pattern matching
   - Loops (while, for)

2. *Improve Performance*:
   - Add optimization passes
   - Profile and optimize VM
   - Implement JIT compilation
   - Add caching to compiler

3. *Better Developer Experience*:
   - Build VS Code extension
   - Add syntax highlighting
   - Implement code completion
   - Add refactoring tools

4. *Target Multiple Backends*:
   - Generate LLVM IR
   - Compile to JavaScript
   - Generate native code
   - Transpile to another language

5. *Advanced Type Features*:
   - Generics/parametric polymorphism
   - Type classes/traits
   - Dependent types
   - Effect systems

6. *Formal Verification*:
   - Prove compiler correctness
   - Verify optimizations
   - Check type soundness formally

#### Research Directions

If this interests you academically:

1. *Read Papers*:
   - PLDI (Programming Language Design and Implementation)
   - POPL (Principles of Programming Languages)
   - OOPSLA (Object-Oriented Programming, Systems, Languages & Applications)

2. *Study Modern Languages*:
   - Rust: Ownership and borrowing
   - Haskell: Advanced type system
   - Idris: Dependent types
   - Pony: Capabilities and actors

3. *Contribute to Compilers*:
   - LLVM, GCC
   - Language implementations (CPython, V8, etc.)
   - Smaller language projects




#### Final Checklist

Before submitting:

- [ ] All tests pass
- [ ] Code is well-commented
- [ ] Documentation is complete
- [ ] Example programs work
- [ ] You can explain every design decision
- [ ] You're proud of what you built!

#### Additional Support

*When You Get Stuck*:

1. Read the relevant section in DESIGN.md or VM-SPECIFICATION.md
2. Look at the examples provided
3. Check your test output carefully
4. Ask a classmate or instructor
5. Search for similar issues online
6. Take a break and come back with fresh eyes

*Remember*: Everyone gets stuck. The key is systematic debugging and patience.

