#!/usr/bin/env python3

import sys
from typing import Tuple, Optional, List, Callable, Any #, Dict
from abc import ABC, abstractmethod


class Lexer:
    def __init__(self, code: str):
        self.code = code.strip()
        self.tokens = []
        self.pos = 0
        self.keywords = {"begin", "end", "end.", "if", "then", "while", "do", "var", "call", "procedure", "!", "?"}
        self.operators = {"<=", ">=", "<", ">", "=", "+", "-", "*", "/", "(", ")", ":=", ";", ","}
        self.tokenize()

    def tokenize(self):
        while self.pos < len(self.code):
            if self.code[self.pos].isspace():
                self.pos += 1
                continue
            if self.pos + 4 <= len(self.code) and self.code[self.pos:self.pos+4] == "end.":
                self.tokens.append(("end.", "kw"))
                self.pos += 4
                print(f"DEBUG: Lexer produced token: 'end.' (kw)")
                continue
            if self.code[self.pos].isalpha():
                token = self.read_alpha()
                kind = "kw" if token in self.keywords else "id"
            elif self.code[self.pos].isdigit():
                token = self.read_digit()
                kind = "num"
            elif self.code[self.pos] in "<>=+-*/();,?!" or self.code[self.pos:self.pos+2] in {":=", "<=", ">="}:
                token = self.read_operator()
                kind = "kw" if token in {"!", "?"} else "asgn" if token == ":=" else "semi" if token == ";" else "comma" if token == "," else "op"
            else:
                raise SyntaxError(f"Unexpected character: '{self.code[self.pos]}'")
            self.tokens.append((token, kind))
            print(f"DEBUG: Lexer produced token: '{token}' ({kind})")

    def read_alpha(self):
        start = self.pos
        while self.pos < len(self.code) and self.code[self.pos].isalpha():
            self.pos += 1
        return self.code[start:self.pos]

    def read_digit(self):
        start = self.pos
        while self.pos < len(self.code) and self.code[self.pos].isdigit():
            self.pos += 1
        return self.code[start:self.pos]

    def read_operator(self):
        if self.pos + 1 < len(self.code):
            two_char = self.code[self.pos:self.pos+2]
            if two_char in {"<=", ">=", ":="}:
                self.pos += 2
                return two_char
        token = self.code[self.pos]
        self.pos += 1
        return token


class ASTNode(ABC):
    @abstractmethod
    def accept(self, visitor):
        pass


class BlockNode(ASTNode):
    def __init__(self, variables: List[str], procedures: List[Tuple[str, ASTNode]], statement: ASTNode):
        self.variables = variables
        self.procedures = procedures
        self.statement = statement
    def accept(self, visitor):
        return visitor.visit_block(self)


class AssignNode(ASTNode):
    def __init__(self, var_name: str, expression: ASTNode):
        self.var_name = var_name
        self.expression = expression
    def accept(self, visitor):
        return visitor.visit_assign(self)


class CallNode(ASTNode):
    def __init__(self, proc_name: str):
        self.proc_name = proc_name
    def accept(self, visitor):
        return visitor.visit_call(self)


class ReadNode(ASTNode):
    def __init__(self, var_name: str):
        self.var_name = var_name
    def accept(self, visitor):
        return visitor.visit_read(self)


class WriteNode(ASTNode):
    def __init__(self, expression: ASTNode):
        self.expression = expression
    def accept(self, visitor):
        return visitor.visit_write(self)


class CompoundNode(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements
    def accept(self, visitor):
        return visitor.visit_compound(self)


class IfNode(ASTNode):
    def __init__(self, condition: ASTNode, then_statement: ASTNode):
        self.condition = condition
        self.then_statement = then_statement
    def accept(self, visitor):
        return visitor.visit_if(self)


class WhileNode(ASTNode):
    def __init__(self, condition: ASTNode, body: ASTNode):
        self.condition = condition
        self.body = body
    def accept(self, visitor):
        return visitor.visit_while(self)


class OperationNode(ASTNode):
    def __init__(self, operator: str, left: ASTNode, right: ASTNode):
        self.operator = operator
        self.left = left
        self.right = right
    def accept(self, visitor):
        return visitor.visit_operation(self)


class VariableNode(ASTNode):
    def __init__(self, name: str):
        self.name = name
    def accept(self, visitor):
        return visitor.visit_variable(self)


class NumberNode(ASTNode):
    def __init__(self, value: int):
        self.value = value
    def accept(self, visitor):
        return visitor.visit_number(self)


class PackratParser:
    def __init__(self, tokens: List[Tuple[str, str]]):
        self.tokens = tokens
        self.cache = {}  # (rule, pos) -> (result, new_pos)

    def parse(self):
        result, pos = self.program(0)
        if result is None or pos != len(self.tokens):
            raise SyntaxError("Incomplete parse")
        return result

    def memoize(self, rule: str, pos: int, func: Callable[[int], Tuple[Any, int]]) -> Tuple[Any, int]:
        key = (rule, pos)
        if key in self.cache:
            print(f"DEBUG: Cache hit for {rule} at pos {pos}")
            return self.cache[key]
        result = func(pos)
        self.cache[key] = result
        return result

    def program(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _program(p: int) -> Tuple[Optional[ASTNode], int]:
            print(f"DEBUG: Entering program at pos {p}")
            block, p = self.block(p)
            if block is None:
                print(f"DEBUG: Failed to parse block at pos {p}")
                return None, p
            if p == len(self.tokens) or (p < len(self.tokens) and self.tokens[p] == ("end.", "kw")):
                if p < len(self.tokens):
                    print(f"DEBUG: Consumed end. at pos {p}")
                    p += 1
                return block, p
            print(f"DEBUG: Expected 'end.' or EOF at pos {p}, got {self.tokens[p] if p < len(self.tokens) else 'EOF'}")
            return None, p
        return self.memoize("program", pos, _program)

    def block(self, pos: int) -> Tuple[Optional[BlockNode], int]:
        def _block(p: int) -> Tuple[Optional[BlockNode], int]:
            print(f"DEBUG: Entering block at pos {p}")
            variables = []
            procedures = []
            if p < len(self.tokens) and self.tokens[p] == ("var", "kw"):
                print(f"DEBUG: Found 'var' at pos {p}")
                p += 1
                if p >= len(self.tokens) or self.tokens[p][1] != "id":
                    raise SyntaxError(f"Expected identifier after 'var' but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}")
                variables.append(self.tokens[p][0])
                print(f"DEBUG: Processing variable: '{variables[-1]}'")
                p += 1
                while p < len(self.tokens) and self.tokens[p] == (",", "comma"):
                    print(f"DEBUG: Consumed comma at pos {p}")
                    p += 1
                    if p >= len(self.tokens) or self.tokens[p][1] != "id" or self.tokens[p][0] in (";", ",", "end.", "end"):
                        raise SyntaxError(f"Expected identifier after comma but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}")
                    variables.append(self.tokens[p][0])
                    print(f"DEBUG: Processing variable: '{variables[-1]}'")
                    p += 1
                if p >= len(self.tokens) or self.tokens[p] != (";", "semi"):
                    raise SyntaxError(f"Expected semicolon but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}")
                print(f"DEBUG: Consumed semicolon at pos {p}")
                p += 1
            while p < len(self.tokens) and self.tokens[p] == ("procedure", "kw"):
                print(f"DEBUG: Found 'procedure' at pos {p}")
                p += 1
                if p >= len(self.tokens) or self.tokens[p][1] != "id":
                    raise SyntaxError(f"Expected identifier after 'procedure' but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}")
                proc_name = self.tokens[p][0]
                print(f"DEBUG: Processing procedure: '{proc_name}'")
                p += 1
                if p >= len(self.tokens) or self.tokens[p] != (";", "semi"):
                    raise SyntaxError(f"Expected semicolon after procedure name")
                print(f"DEBUG: Consumed semicolon at pos {p}")
                p += 1
                proc_body, p = self.block(p)
                if proc_body is None:
                    print(f"DEBUG: Failed to parse procedure body at pos {p}")
                    return None, p
                procedures.append((proc_name, proc_body))
                if p >= len(self.tokens) or self.tokens[p] != (";", "semi"):
                    raise SyntaxError(f"Expected semicolon after procedure body")
                print(f"DEBUG: Consumed semicolon after procedure at pos {p}")
                p += 1
            print(f"DEBUG: Parsing statement at pos {p}")
            statement, p = self.statement(p)
            if statement is None:
                print(f"DEBUG: Failed to parse statement at pos {p}")
                return None, p
            print(f"DEBUG: Block parsed successfully, returning at pos {p}")
            return BlockNode(variables, procedures, statement), p
        return self.memoize("block", pos, _block)

    def statement(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _statement(p: int) -> Tuple[Optional[ASTNode], int]:
            print(f"DEBUG: Entering statement at pos {p}")
            if p >= len(self.tokens):
                print(f"DEBUG: End of tokens reached at pos {p}")
                return None, p
            token, kind = self.tokens[p]
            if kind == "id":
                var_name = token
                p += 1
                if p >= len(self.tokens) or self.tokens[p] != (":=", "asgn"):
                    print(f"DEBUG: Expected ':=' after id at pos {p}")
                    return None, p
                p += 1
                expr, p = self.expression(p)
                if expr is None:
                    print(f"DEBUG: Failed to parse expression at pos {p}")
                    return None, p
                print(f"DEBUG: Parsed assignment at pos {p}")
                return AssignNode(var_name, expr), p
            elif token == "call" and kind == "kw":
                p += 1
                if p >= len(self.tokens) or self.tokens[p][1] != "id":
                    print(f"DEBUG: Expected id after 'call' at pos {p}")
                    return None, p
                proc_name = self.tokens[p][0]
                p += 1
                print(f"DEBUG: Parsed call at pos {p}")
                return CallNode(proc_name), p
            elif token == "?" and kind == "kw":
                p += 1
                if p >= len(self.tokens) or self.tokens[p][1] != "id":
                    print(f"DEBUG: Expected id after '?' at pos {p}")
                    return None, p
                var_name = self.tokens[p][0]
                p += 1
                print(f"DEBUG: Parsed read at pos {p}")
                return ReadNode(var_name), p
            elif token == "!" and kind == "kw":
                p += 1
                expr, p = self.expression(p)
                if expr is None:
                    print(f"DEBUG: Failed to parse expression after '!' at pos {p}")
                    return None, p
                print(f"DEBUG: Parsed write at pos {p}")
                return WriteNode(expr), p
            elif token == "begin" and kind == "kw":
                p += 1
                statements = []
                stmt, p = self.statement(p)
                if stmt is None:
                    print(f"DEBUG: Failed to parse first statement in begin at pos {p}")
                    return None, p
                statements.append(stmt)
                while p < len(self.tokens) and self.tokens[p] == (";", "semi"):
                    print(f"DEBUG: Consumed semicolon in begin at pos {p}")
                    p += 1
                    stmt, p = self.statement(p)
                    if stmt is None:
                        print(f"DEBUG: Failed to parse statement after semicolon at pos {p}")
                        break
                    statements.append(stmt)
                if p >= len(self.tokens) or self.tokens[p][0] not in ("end", "end."):
                    print(f"DEBUG: Expected 'end' or 'end.' at pos {p}, got {self.tokens[p] if p < len(self.tokens) else 'EOF'}")
                    return None, p
                print(f"DEBUG: Consumed end at pos {p}")
                p += 1
                print(f"DEBUG: Parsed compound statement at pos {p}")
                return CompoundNode(statements), p
            elif token == "if" and kind == "kw":
                p += 1
                cond, p = self.condition(p)
                if cond is None:
                    print(f"DEBUG: Failed to parse condition at pos {p}")
                    return None, p
                if p >= len(self.tokens) or self.tokens[p] != ("then", "kw"):
                    print(f"DEBUG: Expected 'then' at pos {p}")
                    return None, p
                p += 1
                stmt, p = self.statement(p)
                if stmt is None:
                    print(f"DEBUG: Failed to parse statement after then at pos {p}")
                    return None, p
                print(f"DEBUG: Parsed if statement at pos {p}")
                return IfNode(cond, stmt), p
            elif token == "while" and kind == "kw":
                p += 1
                cond, p = self.condition(p)
                if cond is None:
                    print(f"DEBUG: Failed to parse condition at pos {p}")
                    return None, p
                if p >= len(self.tokens) or self.tokens[p] != ("do", "kw"):
                    print(f"DEBUG: Expected 'do' at pos {p}")
                    return None, p
                p += 1
                stmt, p = self.statement(p)
                if stmt is None:
                    print(f"DEBUG: Failed to parse statement after do at pos {p}")
                    return None, p
                print(f"DEBUG: Parsed while statement at pos {p}")
                return WhileNode(cond, stmt), p
            print(f"DEBUG: No valid statement at pos {p}, token: {token}")
            return None, p
        return self.memoize("statement", pos, _statement)

    def condition(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _condition(p: int) -> Tuple[Optional[ASTNode], int]:
            print(f"DEBUG: Entering condition at pos {p}")
            left, p = self.expression(p)
            if left is None:
                print(f"DEBUG: Failed to parse left expression at pos {p}")
                return None, p
            if p >= len(self.tokens) or self.tokens[p][0] not in ("=", "<", ">", "<=", ">="):
                print(f"DEBUG: Expected comparison operator at pos {p}")
                return None, p
            op = self.tokens[p][0]
            p += 1
            right, p = self.expression(p)
            if right is None:
                print(f"DEBUG: Failed to parse right expression at pos {p}")
                return None, p
            print(f"DEBUG: Parsed condition at pos {p}")
            return OperationNode(op, left, right), p
        return self.memoize("condition", pos, _condition)

    def expression(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _expression(p: int) -> Tuple[Optional[ASTNode], int]:
            print(f"DEBUG: Entering expression at pos {p}")
            left, p = self.term(p)
            if left is None:
                print(f"DEBUG: Failed to parse term at pos {p}")
                return None, p
            while p < len(self.tokens) and self.tokens[p][0] in ("+", "-"):
                op = self.tokens[p][0]
                p += 1
                right, p = self.term(p)
                if right is None:
                    print(f"DEBUG: Failed to parse right term at pos {p}")
                    return None, p
                left = OperationNode(op, left, right)
            print(f"DEBUG: Parsed expression at pos {p}")
            return left, p
        return self.memoize("expression", pos, _expression)

    def term(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _term(p: int) -> Tuple[Optional[ASTNode], int]:
            print(f"DEBUG: Entering term at pos {p}")
            left, p = self.factor(p)
            if left is None:
                print(f"DEBUG: Failed to parse factor at pos {p}")
                return None, p
            while p < len(self.tokens) and self.tokens[p][0] in ("*", "/"):
                op = self.tokens[p][0]
                p += 1
                right, p = self.factor(p)
                if right is None:
                    print(f"DEBUG: Failed to parse right factor at pos {p}")
                    return None, p
                left = OperationNode(op, left, right)
            print(f"DEBUG: Parsed term at pos {p}")
            return left, p
        return self.memoize("term", pos, _term)

    def factor(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _factor(p: int) -> Tuple[Optional[ASTNode], int]:
            print(f"DEBUG: Entering factor at pos {p}")
            if p >= len(self.tokens):
                print(f"DEBUG: End of tokens reached at pos {p}")
                return None, p
            token, kind = self.tokens[p]
            if kind == "id":
                p += 1
                print(f"DEBUG: Parsed variable at pos {p}")
                return VariableNode(token), p
            elif kind == "num":
                p += 1
                print(f"DEBUG: Parsed number at pos {p}")
                return NumberNode(int(token)), p
            elif token == "(" and kind == "op":
                p += 1
                expr, p = self.expression(p)
                if expr is None or p >= len(self.tokens) or self.tokens[p] != (")", "op"):
                    print(f"DEBUG: Failed to parse parenthesized expression at pos {p}")
                    return None, p
                p += 1
                print(f"DEBUG: Parsed parenthesized expression at pos {p}")
                return expr, p
            print(f"DEBUG: No valid factor at pos {p}, token: {token}")
            return None, p
        return self.memoize("factor", pos, _factor)


class Visitor(ABC):
    @abstractmethod
    def visit_block(self, node: BlockNode): pass
    @abstractmethod
    def visit_assign(self, node: AssignNode): pass
    @abstractmethod
    def visit_call(self, node: CallNode): pass
    @abstractmethod
    def visit_read(self, node: ReadNode): pass
    @abstractmethod
    def visit_write(self, node: WriteNode): pass
    @abstractmethod
    def visit_compound(self, node: CompoundNode): pass
    @abstractmethod
    def visit_if(self, node: IfNode): pass
    @abstractmethod
    def visit_while(self, node: WhileNode): pass
    @abstractmethod
    def visit_operation(self, node: OperationNode): pass
    @abstractmethod
    def visit_variable(self, node: VariableNode): pass
    @abstractmethod
    def visit_number(self, node: NumberNode): pass


class CompilerContext:
    def __init__(self):
        self.scopes = [{}]
        self.current_scope_level = 0
        self.generated_code = []
        self.indent_level = 0
        self.temp_var_counter = 0
        self.current_procedure = None
        self.procedures = {}

    def enter_scope(self):
        self.scopes.append({})
        self.current_scope_level += 1
        self.indent_level += 1

    def exit_scope(self):
        if self.current_scope_level > 0:
            self.scopes.pop()
            self.current_scope_level -= 1
            self.indent_level -= 1

    def add_variable(self, name: str):
        self.scopes[-1][name] = True

    def variable_exists(self, name: str) -> bool:
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False

    def generate_temp_var(self) -> str:
        temp_var = f"_temp{self.temp_var_counter}"
        self.temp_var_counter += 1
        return temp_var

    def add_code(self, code: str):
        self.generated_code.append("\t" * self.indent_level + code)

    def get_code(self) -> str:
        return "\n".join(self.generated_code)

    def register_procedure(self, name: str, node: ASTNode):
        self.procedures[name] = node


class CCompiler(Visitor):
    def __init__(self):
        self.context = CompilerContext()
        self.procedures = set()

    def compile(self, ast: ASTNode) -> str:
        self.collect_procedures(ast)
        self.context.add_code("#include <stdio.h>\n")
        # Generate function prototypes
        for proc in sorted(self.procedures):
            self.context.add_code(f"void {proc}();")
        self.context.add_code("")
        # Process the AST to generate global variables and functions
        ast.accept(self)
        return self.context.get_code()

    def collect_procedures(self, node: ASTNode):
        if isinstance(node, BlockNode):
            for proc_name, proc_body in node.procedures:
                self.procedures.add(proc_name)
                self.collect_procedures(proc_body)
            self.collect_procedures(node.statement)
        elif isinstance(node, CompoundNode):
            for stmt in node.statements:
                self.collect_procedures(stmt)
        elif isinstance(node, IfNode):
            self.collect_procedures(node.then_statement)
        elif isinstance(node, WhileNode):
            self.collect_procedures(node.body)
        elif isinstance(node, (AssignNode, WriteNode)):
            self.collect_procedures(node.expression)
        elif isinstance(node, OperationNode):
            self.collect_procedures(node.left)
            self.collect_procedures(node.right)

    def visit_block(self, node: BlockNode) -> Any:
        if self.context.current_procedure is None:
            # Global (main) block
            for var in node.variables:
                self.context.add_code(f"int {var};")
            for proc_name, proc_body in node.procedures:
                self.context.add_code(f"\nvoid {proc_name}() {{")
                self.context.enter_scope()
                for var in proc_body.variables:
                    self.context.add_code(f"int {var};")
                prev_proc = self.context.current_procedure
                self.context.current_procedure = proc_name
                proc_body.accept(self)
                self.context.current_procedure = prev_proc
                self.context.exit_scope()
                self.context.add_code("}\n")
            self.context.add_code("\nint main() {")
            self.context.enter_scope()
            node.statement.accept(self)
            self.context.add_code("\treturn 0;")
            self.context.exit_scope()
            self.context.add_code("}")
        else:
            # Procedure's local block
            for var in node.variables:
                self.context.add_code(f"int {var};")
            node.statement.accept(self)

    def visit_assign(self, node: AssignNode) -> Any:
        expr = node.expression.accept(self)
        self.context.add_code(f"{node.var_name} = {expr};")

    def visit_call(self, node: CallNode) -> Any:
        self.context.add_code(f"{node.proc_name}();")

    def visit_read(self, node: ReadNode) -> Any:
        self.context.add_code(f'scanf("%d", &{node.var_name});')

    def visit_write(self, node: WriteNode) -> Any:
        expr = node.expression.accept(self)
        self.context.add_code(f'printf("%d\\n", {expr});')

    def visit_compound(self, node: CompoundNode) -> Any:
        for stmt in node.statements:
            stmt.accept(self)

    def visit_if(self, node: IfNode) -> Any:
        cond = node.condition.accept(self)
        self.context.add_code(f"if ({cond}) {{")
        self.context.enter_scope()
        node.then_statement.accept(self)
        self.context.exit_scope()
        self.context.add_code("}")

    def visit_while(self, node: WhileNode) -> Any:
        cond = node.condition.accept(self)
        self.context.add_code(f"while ({cond}) {{")
        self.context.enter_scope()
        node.body.accept(self)
        self.context.exit_scope()
        self.context.add_code("}")

    def visit_operation(self, node: OperationNode) -> str:
        left = node.left.accept(self)
        right = node.right.accept(self)
        op_map = {
            "+": "+", "-": "-", "*": "*", "/": "/",
            "<": "<", ">": ">", "=": "==", "<=": "<=", ">=": ">="
        }
        return f"({left} {op_map[node.operator]} {right})"

    def visit_variable(self, node: VariableNode) -> str:
        return node.name

    def visit_number(self, node: NumberNode) -> str:
        return str(node.value)


class PL0Compiler:
    @staticmethod
    def compile_file(input_filename: str, output_filename: str = None):
        try:
            with open(input_filename, 'r') as file:
                code = file.read()
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        if output_filename is None:
            output_filename = input_filename.rsplit('.', 1)[0] + ".c"
        try:
            lexer = Lexer(code)
            parser = PackratParser(lexer.tokens)
            ast = parser.parse()
            compiler = CCompiler()  # Changed to CCompiler
            c_code = compiler.compile(ast)
            with open(output_filename, 'w') as file:
                file.write(c_code)
            print(f"Compiled {input_filename} to {output_filename}")
        except SyntaxError as e:
            print(f"Syntax error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Compilation error: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: compiler.py <input_filename> [output_filename]", file=sys.stderr)
        sys.exit(1)
    input_filename = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) == 3 else None
    PL0Compiler.compile_file(input_filename, output_filename)


if __name__ == "__main__":
    main()

