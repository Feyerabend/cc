"""
FunLang Parser - A Functional Programming Language

A combinator-based parser that compiles FunLang syntax to the VM's AST.

Syntax:
- Functions: fn x -> x + 1
- Let bindings: let x = 5 in x + 10
- If expressions: if x > 0 then 1 else 0
- Pattern matching: case value of Some x -> x; Nothing -> 0
- Pipe operator: value |> function
- Lists: [1, 2, 3]
- Data constructors: Some(42), Ok("success"), Err("fail")
- Comments: -- this is a comment
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional, List as ListType, Tuple
import re
from functional_vm import *


# PARSER COMBINATORS

@dataclass
class ParseResult:
    """Result of a parse operation."""
    success: bool
    value: Any
    remaining: str
    error: Optional[str] = None
    position: int = 0  # Position in original string where parse started
    
    def __bool__(self):
        return self.success
    
    def with_context(self, source: str, max_context: int = 40) -> str:
        """Generate error message with context."""
        if not self.error:
            return "Unknown error"
        
        pos = len(source) - len(self.remaining)
        
        # Find line and column
        lines = source[:pos].split('\n')
        line_num = len(lines)
        col_num = len(lines[-1]) + 1 if lines else 1
        
        # Get context
        context_start = max(0, pos - max_context)
        context_end = min(len(source), pos + max_context)
        context = source[context_start:context_end]
        
        # Build error message
        msg = f"Line {line_num}, Column {col_num}: {self.error}\n"
        msg += f"  {context[:max_context]}\n"
        msg += f"  {' ' * (pos - context_start)}^"
        
        return msg


class Parser:
    """Base parser combinator."""
    
    def __init__(self, parse_fn: Callable[[str], ParseResult]):
        self.parse_fn = parse_fn
    
    def parse(self, input_str: str) -> ParseResult:
        """Parse the input string."""
        return self.parse_fn(input_str)
    
    def __or__(self, other: 'Parser') -> 'Parser':
        """Parser alternation: try this parser, if it fails try other."""
        def parse_alt(input_str: str) -> ParseResult:
            result = self.parse(input_str)
            if result:
                return result
            return other.parse(input_str)
        return Parser(parse_alt)
    
    def __rshift__(self, fn: Callable) -> 'Parser':
        """Map a function over the parse result."""
        def parse_map(input_str: str) -> ParseResult:
            result = self.parse(input_str)
            if result:
                return ParseResult(True, fn(result.value), result.remaining)
            return result
        return Parser(parse_map)
    
    def __and__(self, other: 'Parser') -> 'Parser':
        """Sequential composition: parse this, then other."""
        def parse_seq(input_str: str) -> ParseResult:
            result1 = self.parse(input_str)
            if not result1:
                return result1
            result2 = other.parse(result1.remaining)
            if not result2:
                return result2
            return ParseResult(True, (result1.value, result2.value), result2.remaining)
        return Parser(parse_seq)
    
    def many(self) -> 'Parser':
        """Parse zero or more occurrences."""
        def parse_many(input_str: str) -> ParseResult:
            results = []
            remaining = input_str
            while True:
                result = self.parse(remaining)
                if not result:
                    break
                results.append(result.value)
                remaining = result.remaining
            return ParseResult(True, results, remaining)
        return Parser(parse_many)
    
    def many1(self) -> 'Parser':
        """Parse one or more occurrences."""
        def parse_many1(input_str: str) -> ParseResult:
            result = self.parse(input_str)
            if not result:
                return ParseResult(False, None, input_str, "Expected at least one match")
            rest = (self.many()).parse(result.remaining)
            return ParseResult(True, [result.value] + rest.value, rest.remaining)
        return Parser(parse_many1)
    
    def optional(self) -> 'Parser':
        """Parse zero or one occurrence."""
        def parse_optional(input_str: str) -> ParseResult:
            result = self.parse(input_str)
            if result:
                return result
            return ParseResult(True, None, input_str)
        return Parser(parse_optional)



# BASIC COMBINATOR PARSERS

def string(s: str) -> Parser:
    """Parse an exact string."""
    def parse_string(input_str: str) -> ParseResult:
        if input_str.startswith(s):
            return ParseResult(True, s, input_str[len(s):])
        return ParseResult(False, None, input_str, f"Expected '{s}'")
    return Parser(parse_string)


def regex(pattern: str) -> Parser:
    """Parse using a regex pattern."""
    compiled = re.compile(f'^({pattern})')
    def parse_regex(input_str: str) -> ParseResult:
        match = compiled.match(input_str)
        if match:
            return ParseResult(True, match.group(1), input_str[match.end():])
        return ParseResult(False, None, input_str, f"Expected pattern {pattern}")
    return Parser(parse_regex)


def whitespace() -> Parser:
    """Parse whitespace (including comments)."""
    ws_pattern = r'(?:\s|--[^\n]*)*'
    return regex(ws_pattern) >> (lambda _: None)


def lexeme(parser: Parser) -> Parser:
    """Parse something followed by whitespace."""
    return (parser & whitespace()) >> (lambda x: x[0])


def keyword(kw: str) -> Parser:
    """Parse a keyword."""
    return lexeme(string(kw))


def symbol(sym: str) -> Parser:
    """Parse a symbol."""
    return lexeme(string(sym))


def parens(parser: Parser) -> Parser:
    """Parse something in parentheses."""
    return (symbol("(") & parser & symbol(")")) >> (lambda x: x[0][1])


def brackets(parser: Parser) -> Parser:
    """Parse something in brackets."""
    return (symbol("[") & parser & symbol("]")) >> (lambda x: x[0][1])



# LANGUAGE PARSERS

def identifier() -> Parser:
    """Parse an identifier (excluding keywords)."""
    keywords = {'fn', 'let', 'in', 'if', 'then', 'else', 'case', 'of', 
                'True', 'False', 'Some', 'Nothing', 'Ok', 'Err'}
    
    def parse_fn(input_str: str) -> ParseResult:
        pattern = r'[a-z_][a-zA-Z0-9_]*'
        result = lexeme(regex(pattern)).parse(input_str)
        if result and result.value in keywords:
            return ParseResult(False, None, input_str, f"'{result.value}' is a keyword")
        return result
    
    return Parser(parse_fn)


def type_constructor() -> Parser:
    """Parse a type constructor (capitalized)."""
    pattern = r'[A-Z][a-zA-Z0-9_]*'
    return lexeme(regex(pattern))


def integer() -> Parser:
    """Parse an integer literal."""
    return lexeme(regex(r'-?\d+')) >> int


def float_literal() -> Parser:
    """Parse a float literal."""
    return lexeme(regex(r'-?\d+\.\d+')) >> float


def string_literal() -> Parser:
    """Parse a string literal."""
    pattern = r'"([^"\\]|\\.)*"'
    return lexeme(regex(pattern)) >> (lambda s: s[1:-1])  # Remove quotes


def boolean() -> Parser:
    """Parse a boolean literal."""
    true_parser = keyword("True") >> (lambda _: True)
    false_parser = keyword("False") >> (lambda _: False)
    return true_parser | false_parser



# EXPRESSION PARSERS

# Forward declarations for recursive parsers
_expr_parser: Optional[Parser] = None


def expr() -> Parser:
    """Parse an expression (main entry point)."""
    global _expr_parser
    if _expr_parser is None:
        _expr_parser = _build_expr_parser()
    return _expr_parser


def _build_expr_parser() -> Parser:
    """Build the expression parser."""
    
    # Atom parser that defers to other parsers
    def atom() -> Parser:
        def parse_atom(input_str: str) -> ParseResult:
            # Try parenthesized expression first
            paren_result = symbol("(").parse(input_str)
            if paren_result:
                # Recursively parse expression inside parens
                inner_result = expr().parse(paren_result.remaining)
                if not inner_result:
                    return inner_result
                close_result = symbol(")").parse(inner_result.remaining)
                if not close_result:
                    return ParseResult(False, None, input_str, "Expected ')'")
                return ParseResult(True, inner_result.value, close_result.remaining)
            
            # Try each atom parser in order
            parsers = [
                literal(),
                data_constructor(),
                list_literal(),
                lambda_expr(),
                let_expr(),
                if_expression(),
                case_expr(),
                var_ref()
            ]
            
            for p in parsers:
                result = p.parse(input_str)
                if result:
                    return result
            
            return ParseResult(False, None, input_str, "Expected expression")
        
        return Parser(parse_atom)
    
    # Function application (left-associative)
    def application() -> Parser:
        def parse_app(input_str: str) -> ParseResult:
            result = atom().parse(input_str)
            if not result:
                return result
            
            func = result.value
            remaining = result.remaining
            
            # Parse arguments
            while True:
                arg_result = atom().parse(remaining)
                if not arg_result:
                    break
                func = app(func, arg_result.value)
                remaining = arg_result.remaining
            
            return ParseResult(True, func, remaining)
        return Parser(parse_app)
    
    # Binary operators
    def binop() -> Parser:
        return (application() & (
            (operator() & application()).many()
        )) >> build_binop_ast
    
    return binop()


def build_binop_ast(parsed) -> ASTNode:
    """Build AST from binary operator parse."""
    left, ops = parsed
    for op, right in ops:
        if op == '|>':
            # Pipe: left |> right becomes right(left)
            left = app(right, left)
        elif op == '+':
            left = add(left, right)
        elif op == '-':
            left = sub(left, right)
        elif op == '*':
            left = mul(left, right)
        elif op == '/':
            left = div(left, right)
        elif op == '==':
            left = eq(left, right)
        elif op == '<':
            left = lt(left, right)
        elif op == '>':
            left = ASTNode(NodeType.GT, children=[left, right])
        elif op == '::':
            left = ASTNode(NodeType.CONS, children=[left, right])
    return left


def operator() -> Parser:
    """Parse a binary operator."""
    ops = ['|>', '==', '<=', '>=', '+', '-', '*', '/', '<', '>', '::']
    parsers = [lexeme(string(op)) for op in sorted(ops, key=len, reverse=True)]
    combined = parsers[0]
    for p in parsers[1:]:
        combined = combined | p
    return combined


def literal() -> Parser:
    """Parse a literal value."""
    return (
        (float_literal() >> lit_float) |
        (integer() >> lit_int) |
        (string_literal() >> lit_str) |
        (boolean() >> lit_bool)
    )


def var_ref() -> Parser:
    """Parse a variable reference."""
    return identifier() >> var


def lambda_expr() -> Parser:
    """Parse a lambda expression: fn x -> body"""
    def parse_lambda(parsed):
        params, body = parsed
        # Right-fold to create nested lambdas
        result = body
        for param in reversed(params):
            result = lam(param, result)
        return result
    
    def parse_fn(input_str: str) -> ParseResult:
        # Manually sequence the parsers to avoid calling expr() at definition time
        kw_result = keyword("fn").parse(input_str)
        if not kw_result:
            return kw_result
        
        params_result = identifier().many1().parse(kw_result.remaining)
        if not params_result:
            return params_result
        
        arrow_result = symbol("->").parse(params_result.remaining)
        if not arrow_result:
            return arrow_result
        
        body_result = expr().parse(arrow_result.remaining)
        if not body_result:
            return body_result
        
        result = parse_lambda((params_result.value, body_result.value))
        return ParseResult(True, result, body_result.remaining)
    
    return Parser(parse_fn)


def let_expr() -> Parser:
    """Parse a let expression: let x = value in body"""
    def parse_fn(input_str: str) -> ParseResult:
        kw_result = keyword("let").parse(input_str)
        if not kw_result:
            return kw_result
        
        id_result = identifier().parse(kw_result.remaining)
        if not id_result:
            return id_result
        
        eq_result = symbol("=").parse(id_result.remaining)
        if not eq_result:
            return eq_result
        
        val_result = expr().parse(eq_result.remaining)
        if not val_result:
            return val_result
        
        in_result = keyword("in").parse(val_result.remaining)
        if not in_result:
            return in_result
        
        body_result = expr().parse(in_result.remaining)
        if not body_result:
            return body_result
        
        result = let(id_result.value, val_result.value, body_result.value)
        return ParseResult(True, result, body_result.remaining)
    
    return Parser(parse_fn)


def if_expression() -> Parser:
    """Parse an if expression: if cond then branch1 else branch2"""
    def parse_fn(input_str: str) -> ParseResult:
        if_result = keyword("if").parse(input_str)
        if not if_result:
            return if_result
        
        cond_result = expr().parse(if_result.remaining)
        if not cond_result:
            return cond_result
        
        then_result = keyword("then").parse(cond_result.remaining)
        if not then_result:
            return then_result
        
        then_branch_result = expr().parse(then_result.remaining)
        if not then_branch_result:
            return then_branch_result
        
        else_result = keyword("else").parse(then_branch_result.remaining)
        if not else_result:
            return else_result
        
        else_branch_result = expr().parse(else_result.remaining)
        if not else_branch_result:
            return else_branch_result
        
        result = if_expr(cond_result.value, then_branch_result.value, else_branch_result.value)
        return ParseResult(True, result, else_branch_result.remaining)
    
    return Parser(parse_fn)


def case_expr() -> Parser:
    """Parse a case expression: case value of pattern -> expr; ..."""
    def parse_case(value, branches):
        case_nodes = []
        for pattern, body in branches:
            case_nodes.append(case(pattern, body))
        return match(value, *case_nodes)
    
    def parse_fn(input_str: str) -> ParseResult:
        case_result = keyword("case").parse(input_str)
        if not case_result:
            return case_result
        
        val_result = expr().parse(case_result.remaining)
        if not val_result:
            return val_result
        
        of_result = keyword("of").parse(val_result.remaining)
        if not of_result:
            return of_result
        
        branches_result = case_branch().many1().parse(of_result.remaining)
        if not branches_result:
            return branches_result
        
        result = parse_case(val_result.value, branches_result.value)
        return ParseResult(True, result, branches_result.remaining)
    
    return Parser(parse_fn)


def case_branch() -> Parser:
    """Parse a case branch: pattern -> expr;"""
    def parse_fn(input_str: str) -> ParseResult:
        pattern_result = pattern().parse(input_str)
        if not pattern_result:
            return pattern_result
        
        arrow_result = symbol("->").parse(pattern_result.remaining)
        if not arrow_result:
            return arrow_result
        
        body_result = expr().parse(arrow_result.remaining)
        if not body_result:
            return body_result
        
        # Optional semicolon
        semi_result = symbol(";").parse(body_result.remaining)
        remaining = semi_result.remaining if semi_result else body_result.remaining
        
        return ParseResult(True, (pattern_result.value, body_result.value), remaining)
    
    return Parser(parse_fn)


def pattern() -> Parser:
    """Parse a pattern."""
    
    def parse_fn(input_str: str) -> ParseResult:
        # Wildcard pattern
        wildcard_result = symbol("_").parse(input_str)
        if wildcard_result:
            return ParseResult(True, {'type': 'wildcard'}, wildcard_result.remaining)
        
        # Try constructor patterns first (they're more specific)
        # Some(pattern)
        some_result = keyword("Some").parse(input_str)
        if some_result:
            lparen_result = symbol("(").parse(some_result.remaining)
            if not lparen_result:
                return ParseResult(False, None, input_str, "Expected '(' after Some")
            inner_result = pattern().parse(lparen_result.remaining)
            if not inner_result:
                return inner_result
            rparen_result = symbol(")").parse(inner_result.remaining)
            if not rparen_result:
                return ParseResult(False, None, input_str, "Expected ')' after Some")
            return ParseResult(True, {'type': 'Some', 'inner': inner_result.value}, rparen_result.remaining)
        
        # Nothing
        nothing_result = keyword("Nothing").parse(input_str)
        if nothing_result:
            return ParseResult(True, {'type': 'Nothing'}, nothing_result.remaining)
        
        # Ok(pattern)
        ok_result = keyword("Ok").parse(input_str)
        if ok_result:
            lparen_result = symbol("(").parse(ok_result.remaining)
            if not lparen_result:
                return ParseResult(False, None, input_str, "Expected '(' after Ok")
            inner_result = pattern().parse(lparen_result.remaining)
            if not inner_result:
                return inner_result
            rparen_result = symbol(")").parse(inner_result.remaining)
            if not rparen_result:
                return ParseResult(False, None, input_str, "Expected ')' after Ok")
            return ParseResult(True, {'type': 'Ok', 'inner': inner_result.value}, rparen_result.remaining)
        
        # Err(pattern)
        err_result = keyword("Err").parse(input_str)
        if err_result:
            lparen_result = symbol("(").parse(err_result.remaining)
            if not lparen_result:
                return ParseResult(False, None, input_str, "Expected '(' after Err")
            inner_result = pattern().parse(lparen_result.remaining)
            if not inner_result:
                return inner_result
            rparen_result = symbol(")").parse(inner_result.remaining)
            if not rparen_result:
                return ParseResult(False, None, input_str, "Expected ')' after Err")
            return ParseResult(True, {'type': 'Err', 'inner': inner_result.value}, rparen_result.remaining)
        
        # Literal pattern
        lit_result = integer().parse(input_str)
        if lit_result:
            return ParseResult(True, {'type': 'literal', 'value': lit_result.value}, lit_result.remaining)
        
        # Variable pattern (must be last since it matches any identifier)
        var_result = identifier().parse(input_str)
        if var_result:
            return ParseResult(True, {'type': 'var', 'name': var_result.value}, var_result.remaining)
        
        return ParseResult(False, None, input_str, "Expected pattern")
    
    return Parser(parse_fn)


def data_constructor() -> Parser:
    """Parse a data constructor: Some(expr), Ok(expr), etc."""
    
    def parse_fn(input_str: str) -> ParseResult:
        # Try Some(expr)
        some_result = keyword("Some").parse(input_str)
        if some_result:
            lparen_result = symbol("(").parse(some_result.remaining)
            if not lparen_result:
                return ParseResult(False, None, input_str, "Expected '(' after Some")
            expr_result = expr().parse(lparen_result.remaining)
            if not expr_result:
                return expr_result
            rparen_result = symbol(")").parse(expr_result.remaining)
            if not rparen_result:
                return ParseResult(False, None, input_str, "Expected ')' after Some")
            return ParseResult(True, some(expr_result.value), rparen_result.remaining)
        
        # Try Nothing
        nothing_result = keyword("Nothing").parse(input_str)
        if nothing_result:
            return ParseResult(True, nothing_node(), nothing_result.remaining)
        
        # Try Ok(expr)
        ok_result = keyword("Ok").parse(input_str)
        if ok_result:
            lparen_result = symbol("(").parse(ok_result.remaining)
            if not lparen_result:
                return ParseResult(False, None, input_str, "Expected '(' after Ok")
            expr_result = expr().parse(lparen_result.remaining)
            if not expr_result:
                return expr_result
            rparen_result = symbol(")").parse(expr_result.remaining)
            if not rparen_result:
                return ParseResult(False, None, input_str, "Expected ')' after Ok")
            return ParseResult(True, ok(expr_result.value), rparen_result.remaining)
        
        # Try Err(expr)
        err_result = keyword("Err").parse(input_str)
        if err_result:
            lparen_result = symbol("(").parse(err_result.remaining)
            if not lparen_result:
                return ParseResult(False, None, input_str, "Expected '(' after Err")
            expr_result = expr().parse(lparen_result.remaining)
            if not expr_result:
                return expr_result
            rparen_result = symbol(")").parse(expr_result.remaining)
            if not rparen_result:
                return ParseResult(False, None, input_str, "Expected ')' after Err")
            return ParseResult(True, err(expr_result.value), rparen_result.remaining)
        
        return ParseResult(False, None, input_str, "Expected data constructor")
    
    return Parser(parse_fn)


def list_literal() -> Parser:
    """Parse a list literal: [1, 2, 3]"""
    def parse_fn(input_str: str) -> ParseResult:
        lbracket_result = symbol("[").parse(input_str)
        if not lbracket_result:
            return lbracket_result
        
        # Check for empty list
        rbracket_result = symbol("]").parse(lbracket_result.remaining)
        if rbracket_result:
            return ParseResult(True, list_node(), rbracket_result.remaining)
        
        # Parse first element
        first_result = expr().parse(lbracket_result.remaining)
        if not first_result:
            return first_result
        
        items = [first_result.value]
        remaining = first_result.remaining
        
        # Parse remaining elements
        while True:
            comma_result = symbol(",").parse(remaining)
            if not comma_result:
                break
            
            item_result = expr().parse(comma_result.remaining)
            if not item_result:
                return item_result
            
            items.append(item_result.value)
            remaining = item_result.remaining
        
        # Parse closing bracket
        rbracket_result = symbol("]").parse(remaining)
        if not rbracket_result:
            return ParseResult(False, None, input_str, "Expected ']'")
        
        return ParseResult(True, list_node(*items), rbracket_result.remaining)
    
    return Parser(parse_fn)



# TOP-LEVEL PARSERS

def program() -> Parser:
    """Parse a complete program."""
    return (whitespace() & expr()) >> (lambda x: x[1])


# COMPILER

class FunLangCompiler:
    """Compiler from FunLang source to VM AST."""
    
    def __init__(self):
        self.parser = program()
        self.source = ""
    
    def compile(self, source: str) -> ASTNode:
        """Compile source code to AST."""
        self.source = source
        result = self.parser.parse(source)
        
        if not result:
            # Generate helpful error message
            error_msg = result.with_context(source) if hasattr(result, 'with_context') else str(result.error)
            raise SyntaxError(error_msg)
        
        if result.remaining.strip():
            # Calculate position
            pos = len(source) - len(result.remaining)
            lines = source[:pos].split('\n')
            line_num = len(lines)
            
            raise SyntaxError(
                f"Unexpected input at line {line_num}:\n"
                f"  {result.remaining[:50]}"
            )
        
        return result.value
    
    def compile_and_run(self, source: str, debug: bool = False) -> Any:
        """Compile and run source code."""
        ast = self.compile(source)
        vm = FunctionalVM(debug=debug)
        return vm.run(ast)



# CONVENIENCE

def compile_funlang(source: str) -> ASTNode:
    """Compile FunLang source to AST."""
    compiler = FunLangCompiler()
    return compiler.compile(source)


def run_funlang(source: str, debug: bool = False) -> Any:
    """Compile and run FunLang source code."""
    compiler = FunLangCompiler()
    return compiler.compile_and_run(source, debug=debug)
