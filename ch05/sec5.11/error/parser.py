from ast_nodes import *
from error_reporter import ErrorReporter, ErrorSeverity, ErrorCategory, get_suggestion

class Parser:
    def __init__(self, tokens, error_reporter=None):
        self.tokens = tokens
        self.pos = 0
        self.error_reporter = error_reporter or ErrorReporter()
        self.panic_mode = False
    
    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def peek(self, offset=1):
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else None
    
    def consume(self, expected_kind=None):
        """Consume a token, with error recovery"""
        token = self.current()
        
        if token is None:
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                f"Unexpected end of input" + (f", expected {expected_kind}" if expected_kind else ""),
                suggestion=get_suggestion("unexpected_eof")
            )
            # Return a dummy token for error recovery
            return Token("EOF", None, 0, 0)
        
        if expected_kind and token.kind != expected_kind:
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                f"Expected {expected_kind}, got {token.kind}",
                line=token.line,
                column=token.column,
                suggestion=self._get_token_suggestion(expected_kind, token.kind)
            )
            # Don't consume the token, let caller decide how to recover
            return Token(expected_kind, None, token.line, token.column)
        
        self.pos += 1
        return token
    
    def _get_token_suggestion(self, expected, got):
        """Provide helpful suggestions based on expected vs. got tokens"""
        suggestions = {
            ("SEMICOLON", "IDENTIFIER"): "Did you forget a semicolon ';' before this?",
            ("SEMICOLON", "RBRACE"): "Add a semicolon ';' before the closing brace.",
            ("RBRACE", "EOF"): "Missing closing brace '}'. Check that all blocks are closed.",
            ("RPAREN", "SEMICOLON"): "Missing closing parenthesis ')'.",
            ("LPAREN", "LBRACE"): "Add an opening parenthesis '(' before the condition.",
        }
        return suggestions.get((expected, got), get_suggestion("unexpected_token"))
    
    def synchronize(self):
        """Synchronize to the next statement after an error"""
        self.panic_mode = False
        
        while self.current() is not None:
            # Stop at statement boundaries
            if self.current().kind == "SEMICOLON":
                self.consume()
                return
            
            # Stop at keywords that start statements
            if self.current().kind in ("LET", "PRINT", "INPUT", "IF", "WHILE", "RBRACE"):
                return
            
            self.pos += 1
    
    def parse(self):
        """Parse the entire program, collecting as many errors as possible"""
        statements = []
        
        while self.current():
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except Exception as e:
                # Continue parsing to find more errors
                if not self.panic_mode:
                    self.panic_mode = True
                    if not self.error_reporter.has_errors():
                        # Only report if we haven't already reported this error
                        self.error_reporter.report(
                            ErrorSeverity.ERROR,
                            ErrorCategory.SYNTAX,
                            str(e),
                            suggestion="Fix the syntax error and try again."
                        )
                self.synchronize()
        
        return Program(statements)
    
    def parse_statement(self):
        token = self.current()
        
        if token is None:
            return None
        
        if token.kind == "LET":
            return self.parse_let()
        elif token.kind == "PRINT":
            return self.parse_print()
        elif token.kind == "INPUT":
            return self.parse_input()
        elif token.kind == "IF":
            return self.parse_if()
        elif token.kind == "WHILE":
            return self.parse_while()
        elif token.kind == "IDENTIFIER":
            return self.parse_assignment()
        elif token.kind == "RBRACE":
            # Extra closing brace
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                "Unexpected closing brace '}'",
                line=token.line,
                column=token.column,
                suggestion="Remove this brace or add a matching opening brace '{'."
            )
            self.consume()
            return None
        else:
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                f"Unexpected token {token.kind}, expected a statement",
                line=token.line,
                column=token.column,
                suggestion="Statements should start with 'let', 'print', 'input', 'if', 'while', or a variable name."
            )
            self.consume()  # Skip the problematic token
            return None
    
    def parse_let(self):
        self.consume("LET")
        
        if not self.current() or self.current().kind != "IDENTIFIER":
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                "Expected variable name after 'let'",
                line=self.current().line if self.current() else None,
                suggestion="Format: let variable_name = value;"
            )
            return None
        
        identifier = self.consume("IDENTIFIER").value
        self.consume("ASSIGN")
        expression = self.parse_expression()
        self.consume("SEMICOLON")
        return LetStatement(identifier, expression)
    
    def parse_assignment(self):
        identifier = self.consume("IDENTIFIER").value
        
        if not self.current() or self.current().kind != "ASSIGN":
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                f"Expected '=' after variable name '{identifier}'",
                line=self.current().line if self.current() else None,
                suggestion=f"Use: {identifier} = value;"
            )
        
        self.consume("ASSIGN")
        expression = self.parse_expression()
        self.consume("SEMICOLON")
        return AssignStatement(identifier, expression)
    
    def parse_print(self):
        self.consume("PRINT")
        self.consume("LPAREN")
        expression = self.parse_expression()
        self.consume("RPAREN")
        self.consume("SEMICOLON")
        return PrintStatement(expression)
    
    def parse_input(self):
        self.consume("INPUT")
        self.consume("LPAREN")
        
        if not self.current() or self.current().kind != "IDENTIFIER":
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                "Expected variable name in input()",
                suggestion="Format: input(variable_name);"
            )
            identifier = "error"
        else:
            identifier = self.consume("IDENTIFIER").value
        
        self.consume("RPAREN")
        self.consume("SEMICOLON")
        return InputStatement(identifier)
    
    def parse_if(self):
        self.consume("IF")
        condition = self.parse_expression()
        then_block = self.parse_block()
        else_block = None
        
        if self.current() and self.current().kind == "ELSE":
            self.consume("ELSE")
            else_block = self.parse_block()
        
        return IfStatement(condition, then_block, else_block)
    
    def parse_while(self):
        self.consume("WHILE")
        condition = self.parse_expression()
        body = self.parse_block()
        return WhileStatement(condition, body)
    
    def parse_block(self):
        if not self.current() or self.current().kind != "LBRACE":
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                "Expected '{' to start block",
                line=self.current().line if self.current() else None,
                suggestion="Blocks must be enclosed in braces: { statements }"
            )
        
        self.consume("LBRACE")
        statements = []
        
        while self.current() and self.current().kind != "RBRACE":
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        if not self.current():
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                "Expected '}' to close block, but reached end of file",
                suggestion=get_suggestion("missing_brace")
            )
        else:
            self.consume("RBRACE")
        
        return Block(statements)
    
    def parse_expression(self):
        return self.parse_comparison()
    
    def parse_comparison(self):
        node = self.parse_additive()
        
        while self.current() and self.current().kind in ("EQ", "NE", "LT", "GT", "LE", "GE"):
            op = self.consume().kind
            right = self.parse_additive()
            node = BinaryOp(op, node, right)
        
        return node
    
    def parse_additive(self):
        node = self.parse_multiplicative()
        
        while self.current() and self.current().kind in ("PLUS", "MINUS"):
            op = self.consume().kind
            right = self.parse_multiplicative()
            node = BinaryOp(op, node, right)
        
        return node
    
    def parse_multiplicative(self):
        node = self.parse_unary()
        
        while self.current() and self.current().kind in ("TIMES", "DIVIDE", "MOD"):
            op = self.consume().kind
            right = self.parse_unary()
            node = BinaryOp(op, node, right)
        
        return node
    
    def parse_unary(self):
        if self.current() and self.current().kind in ("MINUS", "PLUS"):
            op = self.consume().kind
            operand = self.parse_unary()
            return UnaryOp(op, operand)
        return self.parse_primary()
    
    def parse_primary(self):
        token = self.current()
        
        if not token:
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                "Expected expression, got end of file",
                suggestion="Complete the expression."
            )
            return NumberLiteral(0)
        
        if token.kind == "NUMBER":
            self.consume()
            return NumberLiteral(token.value)
        elif token.kind == "STRING":
            self.consume()
            return StringLiteral(token.value)
        elif token.kind == "IDENTIFIER":
            self.consume()
            return Identifier(token.value)
        elif token.kind == "LPAREN":
            self.consume("LPAREN")
            node = self.parse_expression()
            self.consume("RPAREN")
            return node
        else:
            self.error_reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.SYNTAX,
                f"Unexpected token {token.kind} in expression",
                line=token.line,
                column=token.column,
                suggestion="Expected a number, string, variable, or '(' to start an expression."
            )
            self.consume()  # Skip the bad token
            return NumberLiteral(0)  # Return dummy value for error recovery

if __name__ == "__main__":
    from lexer import tokenize
    from error_reporter import ErrorReporter
    
    code = '''
let x = 42
let name = "Alice";
print("Hello, " + name);

if x > 10 {
    print("x is large")
'''
    
    reporter = ErrorReporter(code)
    tokens = tokenize(code, reporter)
    parser = Parser(tokens, reporter)
    ast = parser.parse()
    
    reporter.print_report()
