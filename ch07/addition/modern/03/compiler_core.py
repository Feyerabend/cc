#!/usr/bin/env python3

from typing import Tuple, Optional, List, Callable, Any, Dict
from abc import ABC, abstractmethod
from enum import Enum


class MessageLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class CompilerMessage:
    def __init__(self, level: MessageLevel, message: str, position: Optional[int] = None, 
                 source: Optional[str] = None, context: Optional[Dict] = None):
        self.level = level
        self.message = message
        self.position = position
        self.source = source
        self.context = context or {}

    def __str__(self):
        pos_info = f" at position {self.position}" if self.position is not None else ""
        source_info = f" in {self.source}" if self.source else ""
        return f"[{self.level.value}]{source_info}{pos_info}: {self.message}"


class MessageCollector:
    def __init__(self):
        self.messages: List[CompilerMessage] = []
        self.debug_enabled = False

    def add(self, level: MessageLevel, message: str, position: Optional[int] = None, 
            source: Optional[str] = None, context: Optional[Dict] = None):
        msg = CompilerMessage(level, message, position, source, context)
        self.messages.append(msg)
        if self.debug_enabled or level != MessageLevel.DEBUG:
            print(str(msg))

    def debug(self, message: str, position: Optional[int] = None, source: Optional[str] = None, context: Optional[Dict] = None):
        self.add(MessageLevel.DEBUG, message, position, source, context)

    def info(self, message: str, position: Optional[int] = None, source: Optional[str] = None, context: Optional[Dict] = None):
        self.add(MessageLevel.INFO, message, position, source, context)

    def warning(self, message: str, position: Optional[int] = None, source: Optional[str] = None, context: Optional[Dict] = None):
        self.add(MessageLevel.WARNING, message, position, source, context)

    def error(self, message: str, position: Optional[int] = None, source: Optional[str] = None, context: Optional[Dict] = None):
        self.add(MessageLevel.ERROR, message, position, source, context)

    def has_errors(self) -> bool:
        return any(msg.level == MessageLevel.ERROR for msg in self.messages)

    def get_messages(self, level: Optional[MessageLevel] = None) -> List[CompilerMessage]:
        if level is None:
            return self.messages[:]
        return [msg for msg in self.messages if msg.level == level]

    def enable_debug(self, enabled: bool = True):
        self.debug_enabled = enabled

    def clear(self):
        self.messages.clear()


class Lexer:
    def __init__(self, code: str, messages: MessageCollector):
        self.code = code.strip()
        self.tokens = []
        self.pos = 0
        self.messages = messages
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
                self.messages.debug(f"Lexer produced token: 'end.' (kw)", self.pos, "Lexer")
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
                self.messages.error(f"Unexpected character: '{self.code[self.pos]}'", self.pos, "Lexer")
                raise SyntaxError(f"Unexpected character: '{self.code[self.pos]}'")
            self.tokens.append((token, kind))
            self.messages.debug(f"Lexer produced token: '{token}' ({kind})", self.pos, "Lexer")

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
    def __init__(self):
        self.metadata = {}
        self.source_position = None

    @abstractmethod
    def accept(self, visitor):
        pass

    def set_metadata(self, key: str, value: Any):
        self.metadata[key] = value

    def get_metadata(self, key: str, default=None):
        return self.metadata.get(key, default)


class BlockNode(ASTNode):
    def __init__(self, variables: List[str], procedures: List[Tuple[str, ASTNode]], statement: ASTNode):
        super().__init__()
        self.variables = variables
        self.procedures = procedures
        self.statement = statement
    def accept(self, visitor):
        return visitor.visit_block(self)


class AssignNode(ASTNode):
    def __init__(self, var_name: str, expression: ASTNode):
        super().__init__()
        self.var_name = var_name
        self.expression = expression
    def accept(self, visitor):
        return visitor.visit_assign(self)


class CallNode(ASTNode):
    def __init__(self, proc_name: str):
        super().__init__()
        self.proc_name = proc_name
    def accept(self, visitor):
        return visitor.visit_call(self)


class ReadNode(ASTNode):
    def __init__(self, var_name: str):
        super().__init__()
        self.var_name = var_name
    def accept(self, visitor):
        return visitor.visit_read(self)


class WriteNode(ASTNode):
    def __init__(self, expression: ASTNode):
        super().__init__()
        self.expression = expression
    def accept(self, visitor):
        return visitor.visit_write(self)


class CompoundNode(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        super().__init__()
        self.statements = statements
    def accept(self, visitor):
        return visitor.visit_compound(self)


class NestedBlockNode(ASTNode):
    def __init__(self, variables: List[str], statements: List[ASTNode]):
        super().__init__()
        self.variables = variables
        self.statements = statements
    def accept(self, visitor):
        return visitor.visit_nested_block(self)


class IfNode(ASTNode):
    def __init__(self, condition: ASTNode, then_statement: ASTNode):
        super().__init__()
        self.condition = condition
        self.then_statement = then_statement
    def accept(self, visitor):
        return visitor.visit_if(self)


class WhileNode(ASTNode):
    def __init__(self, condition: ASTNode, body: ASTNode):
        super().__init__()
        self.condition = condition
        self.body = body
    def accept(self, visitor):
        return visitor.visit_while(self)


class OperationNode(ASTNode):
    def __init__(self, operator: str, left: ASTNode, right: ASTNode):
        super().__init__()
        self.operator = operator
        self.left = left
        self.right = right
    def accept(self, visitor):
        return visitor.visit_operation(self)


class VariableNode(ASTNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
    def accept(self, visitor):
        return visitor.visit_variable(self)


class NumberNode(ASTNode):
    def __init__(self, value: int):
        super().__init__()
        self.value = value
    def accept(self, visitor):
        return visitor.visit_number(self)


class PackratParser:
    def __init__(self, tokens: List[Tuple[str, str]], messages: MessageCollector):
        self.tokens = tokens
        self.cache = {}
        self.messages = messages

    def parse(self):
        result, pos = self.program(0)
        if result is None:
            self.messages.error("Failed to parse program", pos, "Parser")
            raise SyntaxError("Failed to parse program")
        if pos != len(self.tokens):
            self.messages.error("Incomplete parse - tokens remaining", pos, "Parser")
            raise SyntaxError("Incomplete parse")
        return result

    def memoize(self, rule: str, pos: int, func: Callable[[int], Tuple[Any, int]]) -> Tuple[Any, int]:
        key = (rule, pos)
        if key in self.cache:
            self.messages.debug(f"Cache hit for {rule} at pos {pos}", pos, "Parser")
            return self.cache[key]
        result = func(pos)
        self.cache[key] = result
        return result

    def program(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _program(p: int) -> Tuple[Optional[ASTNode], int]:
            self.messages.debug(f"Entering program at pos {p}", p, "Parser")
            block, p = self.block(p)
            if block is None:
                self.messages.error(f"Failed to parse block", p, "Parser")
                return None, p
            if p == len(self.tokens) or (p < len(self.tokens) and self.tokens[p] == ("end.", "kw")):
                if p < len(self.tokens):
                    self.messages.debug(f"Consumed end.", p, "Parser")
                    p += 1
                return block, p
            self.messages.error(f"Expected 'end.' or EOF, got {self.tokens[p] if p < len(self.tokens) else 'EOF'}", p, "Parser")
            return None, p
        return self.memoize("program", pos, _program)

    def block(self, pos: int) -> Tuple[Optional[BlockNode], int]:
        def _block(p: int) -> Tuple[Optional[BlockNode], int]:
            self.messages.debug(f"Entering block", p, "Parser")
            variables = []
            procedures = []
            if p < len(self.tokens) and self.tokens[p] == ("var", "kw"):
                self.messages.debug(f"Found 'var'", p, "Parser")
                p += 1
                if p >= len(self.tokens) or self.tokens[p][1] != "id":
                    self.messages.error(f"Expected identifier after 'var' but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}", p, "Parser")
                    raise SyntaxError(f"Expected identifier after 'var'")
                variables.append(self.tokens[p][0])
                self.messages.debug(f"Processing variable: '{variables[-1]}'", p, "Parser")
                p += 1
                while p < len(self.tokens) and self.tokens[p] == (",", "comma"):
                    self.messages.debug(f"Consumed comma", p, "Parser")
                    p += 1
                    if p >= len(self.tokens) or self.tokens[p][1] != "id" or self.tokens[p][0] in (";", ",", "end.", "end"):
                        self.messages.error(f"Expected identifier after comma but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}", p, "Parser")
                        raise SyntaxError(f"Expected identifier after comma")
                    variables.append(self.tokens[p][0])
                    self.messages.debug(f"Processing variable: '{variables[-1]}'", p, "Parser")
                    p += 1
                if p >= len(self.tokens) or self.tokens[p] != (";", "semi"):
                    self.messages.error(f"Expected semicolon but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}", p, "Parser")
                    raise SyntaxError(f"Expected semicolon")
                self.messages.debug(f"Consumed semicolon", p, "Parser")
                p += 1
            while p < len(self.tokens) and self.tokens[p] == ("procedure", "kw"):
                self.messages.debug(f"Found 'procedure'", p, "Parser")
                p += 1
                if p >= len(self.tokens) or self.tokens[p][1] != "id":
                    self.messages.error(f"Expected identifier after 'procedure' but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}", p, "Parser")
                    raise SyntaxError(f"Expected identifier after 'procedure'")
                proc_name = self.tokens[p][0]
                self.messages.debug(f"Processing procedure: '{proc_name}'", p, "Parser")
                p += 1
                if p >= len(self.tokens) or self.tokens[p] != (";", "semi"):
                    self.messages.error(f"Expected semicolon after procedure name", p, "Parser")
                    raise SyntaxError(f"Expected semicolon after procedure name")
                self.messages.debug(f"Consumed semicolon", p, "Parser")
                p += 1
                proc_body, p = self.block(p)
                if proc_body is None:
                    self.messages.error(f"Failed to parse procedure body", p, "Parser")
                    return None, p
                procedures.append((proc_name, proc_body))
                if p >= len(self.tokens) or self.tokens[p] != (";", "semi"):
                    self.messages.error(f"Expected semicolon after procedure body", p, "Parser")
                    raise SyntaxError(f"Expected semicolon after procedure body")
                self.messages.debug(f"Consumed semicolon after procedure", p, "Parser")
                p += 1
            self.messages.debug(f"Parsing statement", p, "Parser")
            statement, p = self.statement(p)
            if statement is None:
                self.messages.error(f"Failed to parse statement", p, "Parser")
                return None, p
            self.messages.debug(f"Block parsed successfully", p, "Parser")
            return BlockNode(variables, procedures, statement), p
        return self.memoize("block", pos, _block)

    def statement(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _statement(p: int) -> Tuple[Optional[ASTNode], int]:
            self.messages.debug(f"Entering statement", p, "Parser")
            if p >= len(self.tokens):
                self.messages.debug(f"End of tokens reached", p, "Parser")
                return None, p
            token, kind = self.tokens[p]
            if kind == "id":
                var_name = token
                p += 1
                if p >= len(self.tokens) or self.tokens[p] != (":=", "asgn"):
                    self.messages.error(f"Expected ':=' after id", p, "Parser")
                    return None, p
                p += 1
                expr, p = self.expression(p)
                if expr is None:
                    self.messages.error(f"Failed to parse expression", p, "Parser")
                    return None, p
                self.messages.debug(f"Parsed assignment", p, "Parser")
                return AssignNode(var_name, expr), p
            elif token == "call" and kind == "kw":
                p += 1
                if p >= len(self.tokens) or self.tokens[p][1] != "id":
                    self.messages.error(f"Expected id after 'call'", p, "Parser")
                    return None, p
                proc_name = self.tokens[p][0]
                p += 1
                self.messages.debug(f"Parsed call", p, "Parser")
                return CallNode(proc_name), p
            elif token == "?" and kind == "kw":
                p += 1
                if p >= len(self.tokens) or self.tokens[p][1] != "id":
                    self.messages.error(f"Expected id after '?'", p, "Parser")
                    return None, p
                var_name = self.tokens[p][0]
                p += 1
                self.messages.debug(f"Parsed read", p, "Parser")
                return ReadNode(var_name), p
            elif token == "!" and kind == "kw":
                p += 1
                expr, p = self.expression(p)
                if expr is None:
                    self.messages.error(f"Failed to parse expression after '!'", p, "Parser")
                    return None, p
                self.messages.debug(f"Parsed write", p, "Parser")
                return WriteNode(expr), p
            elif token == "begin" and kind == "kw":
                p += 1
                variables = []
                if p < len(self.tokens) and self.tokens[p] == ("var", "kw"):
                    self.messages.debug(f"Found 'var' in nested block", p, "Parser")
                    p += 1
                    if p >= len(self.tokens) or self.tokens[p][1] != "id":
                        self.messages.error(f"Expected identifier after 'var' but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}", p, "Parser")
                        raise SyntaxError(f"Expected identifier after 'var'")
                    variables.append(self.tokens[p][0])
                    self.messages.debug(f"Processing nested variable: '{variables[-1]}'", p, "Parser")
                    p += 1
                    while p < len(self.tokens) and self.tokens[p] == (",", "comma"):
                        self.messages.debug(f"Consumed comma in nested block", p, "Parser")
                        p += 1
                        if p >= len(self.tokens) or self.tokens[p][1] != "id" or self.tokens[p][0] in (";", ",", "end.", "end"):
                            self.messages.error(f"Expected identifier after comma but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}", p, "Parser")
                            raise SyntaxError(f"Expected identifier after comma")
                        variables.append(self.tokens[p][0])
                        self.messages.debug(f"Processing nested variable: '{variables[-1]}'", p, "Parser")
                        p += 1
                    if p >= len(self.tokens) or self.tokens[p] != (";", "semi"):
                        self.messages.error(f"Expected semicolon but got: {self.tokens[p] if p < len(self.tokens) else 'EOF'}", p, "Parser")
                        raise SyntaxError(f"Expected semicolon")
                    self.messages.debug(f"Consumed semicolon in nested block", p, "Parser")
                    p += 1
                
                statements = []
                stmt, p = self.statement(p)
                if stmt is None:
                    self.messages.error(f"Failed to parse first statement in begin", p, "Parser")
                    return None, p
                statements.append(stmt)
                while p < len(self.tokens) and self.tokens[p] == (";", "semi"):
                    self.messages.debug(f"Consumed semicolon in begin", p, "Parser")
                    p += 1
                    stmt, p = self.statement(p)
                    if stmt is None:
                        self.messages.debug(f"Failed to parse statement after semicolon", p, "Parser")
                        break
                    statements.append(stmt)
                if p >= len(self.tokens) or self.tokens[p][0] not in ("end", "end."):
                    self.messages.error(f"Expected 'end' or 'end.', got {self.tokens[p] if p < len(self.tokens) else 'EOF'}", p, "Parser")
                    return None, p
                self.messages.debug(f"Consumed end", p, "Parser")
                p += 1
                
                if variables:
                    self.messages.debug(f"Parsed nested block with variables", p, "Parser")
                    return NestedBlockNode(variables, statements), p
                else:
                    self.messages.debug(f"Parsed compound statement", p, "Parser")
                    return CompoundNode(statements), p
                    
            elif token == "if" and kind == "kw":
                p += 1
                cond, p = self.condition(p)
                if cond is None:
                    self.messages.error(f"Failed to parse condition", p, "Parser")
                    return None, p
                if p >= len(self.tokens) or self.tokens[p] != ("then", "kw"):
                    self.messages.error(f"Expected 'then'", p, "Parser")
                    return None, p
                p += 1
                stmt, p = self.statement(p)
                if stmt is None:
                    self.messages.error(f"Failed to parse statement after then", p, "Parser")
                    return None, p
                self.messages.debug(f"Parsed if statement", p, "Parser")
                return IfNode(cond, stmt), p
            elif token == "while" and kind == "kw":
                p += 1
                cond, p = self.condition(p)
                if cond is None:
                    self.messages.error(f"Failed to parse condition", p, "Parser")
                    return None, p
                if p >= len(self.tokens) or self.tokens[p] != ("do", "kw"):
                    self.messages.error(f"Expected 'do'", p, "Parser")
                    return None, p
                p += 1
                stmt, p = self.statement(p)
                if stmt is None:
                    self.messages.error(f"Failed to parse statement after do", p, "Parser")
                    return None, p
                self.messages.debug(f"Parsed while statement", p, "Parser")
                return WhileNode(cond, stmt), p
            self.messages.debug(f"No valid statement, token: {token}", p, "Parser")
            return None, p
        return self.memoize("statement", pos, _statement)

    def condition(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _condition(p: int) -> Tuple[Optional[ASTNode], int]:
            self.messages.debug(f"Entering condition", p, "Parser")
            left, p = self.expression(p)
            if left is None:
                self.messages.error(f"Failed to parse left expression", p, "Parser")
                return None, p
            if p >= len(self.tokens) or self.tokens[p][0] not in ("=", "<", ">", "<=", ">="):
                self.messages.error(f"Expected comparison operator", p, "Parser")
                return None, p
            op = self.tokens[p][0]
            p += 1
            right, p = self.expression(p)
            if right is None:
                self.messages.error(f"Failed to parse right expression", p, "Parser")
                return None, p
            self.messages.debug(f"Parsed condition", p, "Parser")
            return OperationNode(op, left, right), p
        return self.memoize("condition", pos, _condition)

    def expression(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _expression(p: int) -> Tuple[Optional[ASTNode], int]:
            self.messages.debug(f"Entering expression", p, "Parser")
            left, p = self.term(p)
            if left is None:
                self.messages.error(f"Failed to parse term", p, "Parser")
                return None, p
            while p < len(self.tokens) and self.tokens[p][0] in ("+", "-"):
                op = self.tokens[p][0]
                p += 1
                right, p = self.term(p)
                if right is None:
                    self.messages.error(f"Failed to parse right term", p, "Parser")
                    return None, p
                left = OperationNode(op, left, right)
            self.messages.debug(f"Parsed expression", p, "Parser")
            return left, p
        return self.memoize("expression", pos, _expression)

    def term(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _term(p: int) -> Tuple[Optional[ASTNode], int]:
            self.messages.debug(f"Entering term", p, "Parser")
            left, p = self.factor(p)
            if left is None:
                self.messages.error(f"Failed to parse factor", p, "Parser")
                return None, p
            while p < len(self.tokens) and self.tokens[p][0] in ("*", "/"):
                op = self.tokens[p][0]
                p += 1
                right, p = self.factor(p)
                if right is None:
                    self.messages.error(f"Failed to parse right factor", p, "Parser")
                    return None, p
                left = OperationNode(op, left, right)
            self.messages.debug(f"Parsed term", p, "Parser")
            return left, p
        return self.memoize("term", pos, _term)

    def factor(self, pos: int) -> Tuple[Optional[ASTNode], int]:
        def _factor(p: int) -> Tuple[Optional[ASTNode], int]:
            self.messages.debug(f"Entering factor", p, "Parser")
            if p >= len(self.tokens):
                self.messages.debug(f"End of tokens reached", p, "Parser")
                return None, p
            token, kind = self.tokens[p]
            if kind == "id":
                p += 1
                self.messages.debug(f"Parsed variable", p, "Parser")
                return VariableNode(token), p
            elif kind == "num":
                p += 1
                self.messages.debug(f"Parsed number", p, "Parser")
                return NumberNode(int(token)), p
            elif token == "(" and kind == "op":
                p += 1
                expr, p = self.expression(p)
                if expr is None or p >= len(self.tokens) or self.tokens[p] != (")", "op"):
                    self.messages.error(f"Failed to parse parenthesized expression", p, "Parser")
                    return None, p
                p += 1
                self.messages.debug(f"Parsed parenthesized expression", p, "Parser")
                return expr, p
            self.messages.debug(f"No valid factor, token: {token}", p, "Parser")
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
    def visit_nested_block(self, node: NestedBlockNode): pass
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
        self.block_counter = 0
        self.plugin_results = {}
        self.generated_outputs = {}

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

    def generate_block_id(self) -> str:
        block_id = f"_block{self.block_counter}"
        self.block_counter += 1
        return block_id

    def add_code(self, code: str):
        self.generated_code.append("\t" * self.indent_level + code)

    def get_code(self) -> str:
        return "\n".join(self.generated_code)

    def register_procedure(self, name: str, node: ASTNode):
        self.procedures[name] = node


class Plugin:    
    def __init__(self, name: str, description: str = "", version: str = "1.0"):
        self.name = name
        self.description = description
        self.version = version
        self.enabled = True
        self.dependencies = []  # list of plugin names this plugin depends on

    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> dict:
        """Override this method to implement plugin functionality"""
        return {}
    
    def get_info(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "dependencies": self.dependencies
        }


def plugin_function(name: str = None, description: str = "", version: str = "1.0", dependencies=None):
    """Decorator to mark a function as a plugin"""
    def decorator(func):
        func._is_plugin = True
        func._plugin_name = name or func.__name__
        func._plugin_description = description or func.__doc__ or ""
        func._plugin_version = version
        func._plugin_dependencies = dependencies or []
        return func
    return decorator