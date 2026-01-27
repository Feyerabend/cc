#!/usr/bin/env python3

import sys
import os
import importlib.util
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
    """Node for nested blocks with local variables"""
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
        self.cache = {}  # (rule, pos) -> (result, new_pos)
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
                # Check if this is a nested block with variables
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
                
                # Return NestedBlockNode if variables were declared, else CompoundNode
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
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.enabled = True

    # the main useful thing in this is the AST, so that we can analyze and transform it
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> dict:
        return {}


class PluginRegistry:
    def __init__(self):
        self.plugins = {}
        self.execution_order = []
    
    def register(self, plugin: Plugin):
        self.plugins[plugin.name] = plugin
        if plugin.name not in self.execution_order:
            self.execution_order.append(plugin.name)
    
    def register_function(self, name: str, func: Callable, description: str = ""):
        class FunctionPlugin(Plugin):
            def __init__(self, name, func, description):
                super().__init__(name, description)
                self.func = func
            
            def run(self, ast, context, messages):
                return self.func(ast, context, messages)
        
        self.register(FunctionPlugin(name, func, description))
    
    def set_order(self, order: List[str]):
        for name in order:
            if name not in self.plugins:
                raise ValueError(f"Plugin '{name}' not found")
        self.execution_order = order
    
    def run_all(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> CompilerContext:
        for plugin_name in self.execution_order:
            plugin = self.plugins[plugin_name]
            if not plugin.enabled:
                continue
                
            messages.info(f"Running plugin: {plugin_name}")
            try:
                result = plugin.run(ast, context, messages)
                if result:
                    context.plugin_results[plugin_name] = result
            except Exception as e:
                messages.error(f"Plugin '{plugin_name}' failed: {e}")
        
        return context
    
    def load_from_file(self, filepath: str):
        if not os.path.exists(filepath):
            return
        
        spec = importlib.util.spec_from_file_location("plugin_module", filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                plugin_instance = attr()
                self.register(plugin_instance)
            elif callable(attr) and hasattr(attr, '_is_plugin'):
                self.register_function(attr.__name__, attr, getattr(attr, '__doc__', ''))


def plugin(func):
    func._is_plugin = True
    return func


# built in plugins
class StaticAnalysisPlugin(Plugin):
    def __init__(self):
        super().__init__("static_analysis", "Analyzes variable usage and declarations")
    
    def run(self, ast, context, messages):
        analyzer = StaticAnalyzer(messages)
        return analyzer.analyze(ast)


class StaticAnalyzer(Visitor):
    def __init__(self, messages):
        self.messages = messages
        self.scopes = [set()]
        self.declared_vars = set()
        self.used_vars = set()
        self.undefined_vars = set()
        self.procedures = set()
        
    def analyze(self, ast: ASTNode) -> Dict[str, Any]:
        ast.accept(self)
        return {
            "declared_variables": list(self.declared_vars),
            "used_variables": list(self.used_vars),
            "undefined_variables": list(self.undefined_vars),
            "procedures": list(self.procedures)
        }
    
    def enter_scope(self):
        self.scopes.append(set())
    
    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
    
    def declare_variable(self, name: str):
        self.scopes[-1].add(name)
        self.declared_vars.add(name)
    
    def use_variable(self, name: str):
        self.used_vars.add(name)
        for scope in reversed(self.scopes):
            if name in scope:
                return
        self.undefined_vars.add(name)
        self.messages.warning(f"Variable '{name}' used but not declared", source="StaticAnalysis")
    
    def visit_block(self, node: BlockNode):
        self.enter_scope()
        for var in node.variables:
            self.declare_variable(var)
        for proc_name, proc_body in node.procedures:
            self.procedures.add(proc_name)
            proc_body.accept(self)
        node.statement.accept(self)
        self.exit_scope()
    
    def visit_nested_block(self, node: NestedBlockNode):
        self.enter_scope()
        for var in node.variables:
            self.declare_variable(var)
        for stmt in node.statements:
            stmt.accept(self)
        self.exit_scope()
    
    def visit_assign(self, node: AssignNode):
        self.use_variable(node.var_name)
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        if node.proc_name not in self.procedures:
            self.messages.warning(f"Procedure '{node.proc_name}' called but not declared", source="StaticAnalysis")
    
    def visit_read(self, node: ReadNode):
        self.use_variable(node.var_name)
    
    def visit_write(self, node: WriteNode):
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        node.condition.accept(self)
        node.then_statement.accept(self)
    
    def visit_while(self, node: WhileNode):
        node.condition.accept(self)
        node.body.accept(self)
    
    def visit_operation(self, node: OperationNode):
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        self.use_variable(node.name)
    
    def visit_number(self, node: NumberNode):
        pass


class TACGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__("tac_generator", "Generates Three-Address Code")
    
    def run(self, ast, context, messages):
        generator = TACGenerator(messages)
        tac_code = generator.generate(ast)
        context.generated_outputs["tac_code"] = "\n".join(tac_code)
        return {"generated": True}


class TACGenerator(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.code = []
        self.temp_counter = 0
        self.label_counter = 0
    
    def generate(self, ast: ASTNode) -> List[str]:
        ast.accept(self)
        return self.code
    
    def new_temp(self) -> str:
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def new_label(self) -> str:
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def visit_block(self, node: BlockNode):
        for var in node.variables:
            self.code.append(f"DECLARE {var}")
        for proc_name, proc_body in node.procedures:
            self.code.append(f"PROC {proc_name}:")
            proc_body.accept(self)
            self.code.append(f"ENDPROC {proc_name}")
        node.statement.accept(self)
    
    def visit_assign(self, node: AssignNode):
        expr_result = node.expression.accept(self)
        self.code.append(f"{node.var_name} := {expr_result}")
    
    def visit_call(self, node: CallNode):
        self.code.append(f"CALL {node.proc_name}")
    
    def visit_read(self, node: ReadNode):
        self.code.append(f"READ {node.var_name}")
    
    def visit_write(self, node: WriteNode):
        expr_result = node.expression.accept(self)
        self.code.append(f"WRITE {expr_result}")
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        for var in node.variables:
            self.code.append(f"DECLARE {var}")
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        cond_result = node.condition.accept(self)
        else_label = self.new_label()
        end_label = self.new_label()
        self.code.append(f"IF_FALSE {cond_result} GOTO {else_label}")
        node.then_statement.accept(self)
        self.code.append(f"GOTO {end_label}")
        self.code.append(f"{else_label}:")
        self.code.append(f"{end_label}:")
    
    def visit_while(self, node: WhileNode):
        start_label = self.new_label()
        end_label = self.new_label()
        self.code.append(f"{start_label}:")
        cond_result = node.condition.accept(self)
        self.code.append(f"IF_FALSE {cond_result} GOTO {end_label}")
        node.body.accept(self)
        self.code.append(f"GOTO {start_label}")
        self.code.append(f"{end_label}:")
    
    def visit_operation(self, node: OperationNode):
        left_result = node.left.accept(self)
        right_result = node.right.accept(self)
        temp = self.new_temp()
        self.code.append(f"{temp} := {left_result} {node.operator} {right_result}")
        return temp
    
    def visit_variable(self, node: VariableNode):
        return node.name
    
    def visit_number(self, node: NumberNode):
        return str(node.value)


class CCodeGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__("c_generator", "Generates C code")
    
    def run(self, ast, context, messages):
        compiler = CCompiler(messages)
        c_code = compiler.compile(ast)
        context.generated_outputs["c_code"] = c_code
        return {"generated": True}


class CCompiler(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.context = CompilerContext()
        self.procedures = set()

    def compile(self, ast: ASTNode) -> str:
        self.collect_procedures(ast)
        self.context.add_code("#include <stdio.h>\n")
        for proc in sorted(self.procedures):
            self.context.add_code(f"void {proc}();")
        self.context.add_code("")
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
        elif isinstance(node, NestedBlockNode):
            for stmt in node.statements:
                self.collect_procedures(stmt)
        elif isinstance(node, IfNode):
            self.collect_procedures(node.then_statement)
        elif isinstance(node, WhileNode):
            self.collect_procedures(node.body)
        elif isinstance(node, (AssignNode, WriteNode)):
            if hasattr(node, 'expression'):
                self.collect_procedures(node.expression)
        elif isinstance(node, OperationNode):
            self.collect_procedures(node.left)
            self.collect_procedures(node.right)

    def visit_block(self, node: BlockNode) -> Any:
        if self.context.current_procedure is None:
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
        else: # local
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

    def visit_nested_block(self, node: NestedBlockNode) -> Any:
        self.context.add_code("{")
        self.context.enter_scope()
        for var in node.variables:
            self.context.add_code(f"int {var};")
        for stmt in node.statements:
            stmt.accept(self)
        self.context.exit_scope()
        self.context.add_code("}")

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


# MAIN COMPILER CLASS
class PL0Compiler:
    def __init__(self):
        self.messages = MessageCollector()
        self.registry = PluginRegistry()
        
        # register built-in plugins
        self.registry.register(StaticAnalysisPlugin())
        self.registry.register(TACGeneratorPlugin())
        self.registry.register(CCodeGeneratorPlugin())
        
        # default execution order
        self.registry.set_order(["static_analysis", "tac_generator", "c_generator"])

    # custom
    def add_plugin(self, plugin: Plugin):
        self.registry.register(plugin)
    
    def add_plugin_function(self, name: str, func: Callable, description: str = ""):
        self.registry.register_function(name, func, description)
    
    def load_plugins(self, directory: str):
        if not os.path.exists(directory):
            return
        
        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                filepath = os.path.join(directory, filename)
                try:
                    self.registry.load_from_file(filepath)
                    self.messages.info(f"Loaded plugins from {filename}")
                except Exception as e:
                    self.messages.warning(f"Failed to load {filename}: {e}")
    
    def enable_debug(self):
        self.messages.enable_debug(True)
    
    def compile_string(self, code: str) -> Dict[str, Any]:
        self.messages.clear()
        
        try:
            # Lexical analysis
            lexer = Lexer(code, self.messages)
            
            # Syntax analysis
            parser = PackratParser(lexer.tokens, self.messages)
            ast = parser.parse()
            
            # Create context and run plugins
            context = CompilerContext()
            context = self.registry.run_all(ast, context, self.messages)
            
            return {
                "success": not self.messages.has_errors(),
                "ast": ast,
                "context": context,
                "messages": self.messages.get_messages(),
                "outputs": context.generated_outputs,
                "plugin_results": context.plugin_results
            }
            
        except Exception as e:
            self.messages.error(f"Compilation failed: {str(e)}", source="Compiler")
            return {
                "success": False,
                "ast": None,
                "context": None,
                "messages": self.messages.get_messages(),
                "outputs": {},
                "plugin_results": {}
            }
    
    @staticmethod
    def compile_file(input_filename: str, output_filename: str = None, debug: bool = False, plugins_dir: str = None):
        compiler = PL0Compiler()
        
        if debug:
            compiler.enable_debug()
        
        if plugins_dir:
            compiler.load_plugins(plugins_dir)
        
        try:
            with open(input_filename, 'r') as file:
                code = file.read()
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        
        if output_filename is None:
            output_filename = input_filename.rsplit('.', 1)[0] + ".c"
        
        result = compiler.compile_string(code)
        
        if result["success"]:
            # Write C code output
            if "c_code" in result["outputs"]:
                with open(output_filename, 'w') as file:
                    file.write(result["outputs"]["c_code"])
                print(f"Compiled {input_filename} to {output_filename}")
            
            # Write TAC output if requested
            tac_filename = input_filename.rsplit('.', 1)[0] + ".tac"
            if "tac_code" in result["outputs"]:
                with open(tac_filename, 'w') as file:
                    file.write(result["outputs"]["tac_code"])
                print(f"Generated TAC: {tac_filename}")
                
        else:
            print("Compilation failed with errors:", file=sys.stderr)
            for msg in result["messages"]:
                if msg.level == MessageLevel.ERROR:
                    print(f"  {msg}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def compile_file_with_optimization(input_filename: str, output_filename: str = None, 
                                    debug: bool = False, plugins_dir: str = None, 
                                    save_optimized: bool = False):
        compiler = PL0Compiler()
        
        if debug:
            compiler.enable_debug()
        
        if plugins_dir:
            compiler.load_plugins(plugins_dir)
        
        try:
            with open(input_filename, 'r') as file:
                code = file.read()
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        
        if output_filename is None:
            output_filename = input_filename.rsplit('.', 1)[0] + ".c"
        
        result = compiler.compile_string(code)
        
        if result["success"]:
            # Write C code output
            if "c_code" in result["outputs"]:
                with open(output_filename, 'w') as file:
                    file.write(result["outputs"]["c_code"])
                print(f"Compiled {input_filename} to {output_filename}")
            
            # Save optimized source code if requested
            if save_optimized and hasattr(result["context"], "optimized_ast"):
                optimized_filename = input_filename.rsplit('.', 1)[0] + "_optimized.pl0"
                reconstructor = CodeReconstructor()
                optimized_code = reconstructor.reconstruct(result["context"].optimized_ast)
                with open(optimized_filename, 'w') as file:
                    file.write(optimized_code)
                print(f"Optimized source saved to {optimized_filename}")
            
            # Show optimization stats
            if "optimizer" in result["plugin_results"]:
                opt_result = result["plugin_results"]["optimizer"]
                optimizations = opt_result.get('optimizations_applied', 0)
                if optimizations > 0:
                    print(f"Applied {optimizations} optimizations")
        else:
            print("Compilation failed with errors:", file=sys.stderr)
            for msg in result["messages"]:
                if msg.level == MessageLevel.ERROR:
                    print(f"  {msg}", file=sys.stderr)
            sys.exit(1)



class CodeReconstructor(Visitor):
    """Reconstructs PL0 source code from AST"""
    
    def __init__(self):
        self.output = []
        self.indent_level = 0
        self.indent_str = "    "
    
    def reconstruct(self, node: ASTNode) -> str:
        self.output = []
        self.indent_level = 0
        node.accept(self)
        return "".join(self.output)
    
    def _add(self, text: str):
        self.output.append(text)
    
    def visit_block(self, node: BlockNode):
        if node.variables:
            self._add("var ")
            self._add(", ".join(node.variables))
            self._add(";\n\n")
        
        for proc_name, proc_body in node.procedures:
            self._add(f"procedure {proc_name};\n")
            proc_body.accept(self)
            self._add(";\n\n")
        
        node.statement.accept(self)
        if not self.output[-1].endswith(".\n"):
            self._add(".")
    
    def visit_assign(self, node: AssignNode):
        self._add(f"{node.var_name} := ")
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        self._add(f"call {node.proc_name}")
    
    def visit_read(self, node: ReadNode):
        self._add(f"? {node.var_name}")
    
    def visit_write(self, node: WriteNode):
        self._add("! ")
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        if not node.statements:
            return
        if len(node.statements) == 1:
            node.statements[0].accept(self)
        else:
            self._add("begin\n")
            self.indent_level += 1
            for i, stmt in enumerate(node.statements):
                if i > 0:
                    self._add(";\n")
                self._add(self.indent_str * self.indent_level)
                stmt.accept(self)
            self._add("\n")
            self.indent_level -= 1
            self._add(self.indent_str * self.indent_level + "end")
    
    def visit_nested_block(self, node: NestedBlockNode):
        self._add("begin\n")
        self.indent_level += 1
        if node.variables:
            self._add(self.indent_str * self.indent_level + "var ")
            self._add(", ".join(node.variables))
            self._add(";\n")
        for i, stmt in enumerate(node.statements):
            if i > 0 or node.variables:
                self._add(";\n")
            self._add(self.indent_str * self.indent_level)
            stmt.accept(self)
        self._add("\n")
        self.indent_level -= 1
        self._add(self.indent_str * self.indent_level + "end")
    
    def visit_if(self, node: IfNode):
        self._add("if ")
        node.condition.accept(self)
        self._add(" then\n")
        self.indent_level += 1
        self._add(self.indent_str * self.indent_level)
        node.then_statement.accept(self)
        self.indent_level -= 1
    
    def visit_while(self, node: WhileNode):
        self._add("while ")
        node.condition.accept(self)
        self._add(" do\n")
        self.indent_level += 1
        self._add(self.indent_str * self.indent_level)
        node.body.accept(self)
        self.indent_level -= 1
    
    def visit_operation(self, node: OperationNode):
        self._add("(")
        node.left.accept(self)
        self._add(f" {node.operator} ")
        node.right.accept(self)
        self._add(")")
    
    def visit_variable(self, node: VariableNode):
        self._add(node.name)
    
    def visit_number(self, node: NumberNode):
        self._add(str(node.value))


# Update the main() function to support saving optimized source
def main():
    if len(sys.argv) < 2:
        print("Usage: compiler.py <input_filename> [output_filename] [--debug] [--plugins <directory>] [--save-optimized]", file=sys.stderr)
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = None
    debug = False
    plugins_dir = None
    save_optimized = False
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--debug":
            debug = True
        elif arg == "--save-optimized":
            save_optimized = True
        elif arg == "--plugins":
            if i + 1 < len(sys.argv):
                plugins_dir = sys.argv[i + 1]
                i += 1  # skip next argument as it's the plugins directory
            else:
                print("Error: --plugins requires a directory argument", file=sys.stderr)
                sys.exit(1)
        else:
            output_filename = arg
        i += 1
    
    # Use the enhanced compile_file function
    compile_file_enhanced(input_filename, output_filename, debug, plugins_dir, save_optimized)


def compile_file_enhanced(input_filename: str, output_filename: str = None, 
                         debug: bool = False, plugins_dir: str = None, 
                         save_optimized: bool = False):
    """Enhanced version of compile_file that can save optimized source"""
    
    compiler = PL0Compiler()
    
    if debug:
        compiler.enable_debug()
    
    if plugins_dir:
        compiler.load_plugins(plugins_dir)
    
    try:
        with open(input_filename, 'r') as file:
            code = file.read()
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if output_filename is None:
        output_filename = input_filename.rsplit('.', 1)[0] + ".c"
    
    result = compiler.compile_string(code)
    
    if result["success"]:
        # Write C code output (from optimized AST if available)
        if "c_code" in result["outputs"]:
            with open(output_filename, 'w') as file:
                file.write(result["outputs"]["c_code"])
            print(f"Compiled {input_filename} to {output_filename}")
        
        # Save optimized source code if requested
        if save_optimized and hasattr(result["context"], "optimized_ast"):
            optimized_filename = input_filename.rsplit('.', 1)[0] + "_optimized.pl0"
            reconstructor = CodeReconstructor()
            optimized_code = reconstructor.reconstruct(result["context"].optimized_ast)
            with open(optimized_filename, 'w') as file:
                file.write(optimized_code)
            print(f"Optimized source saved to {optimized_filename}")
        
        # Show optimization statistics
        if "optimizer" in result["plugin_results"]:
            opt_result = result["plugin_results"]["optimizer"]
            optimizations = opt_result.get('optimizations_applied', 0)
            passes = opt_result.get('passes', 0)
            if optimizations > 0:
                print(f"Applied {optimizations} optimizations in {passes} passes")
        
        # Write TAC output if requested
        tac_filename = input_filename.rsplit('.', 1)[0] + ".tac"
        if "tac_code" in result["outputs"]:
            with open(tac_filename, 'w') as file:
                file.write(result["outputs"]["tac_code"])
            print(f"Generated TAC: {tac_filename}")
                
    else:
        print("Compilation failed with errors:", file=sys.stderr)
        for msg in result["messages"]:
            if msg.level == MessageLevel.ERROR:
                print(f"  {msg}", file=sys.stderr)
        sys.exit(1)


# Replace the old main call
if __name__ == "__main__":
    main()  # This now uses the enhanced version