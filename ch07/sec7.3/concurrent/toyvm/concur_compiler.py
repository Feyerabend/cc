"""
concur_compiler.py
==================
A compiler for the Concur language that produces ToyVM instruction lists.

Usage:
    from concur_compiler import compile_concur

    source = '''
    x = 10
    y = 20
    z = x + y
    print("Sum: ", z)
    '''
    instructions = compile_concur(source)

    # Then run with ToyVM:
    # vm = ToyVM()
    # vm.create_thread(instructions, name="main")
    # vm.run(debug=True)

Or from the command line:
    python concur_compiler.py my_program.concur
    python concur_compiler.py my_program.concur --run      # also runs via ToyVM if available
    python concur_compiler.py my_program.concur --run --debug
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple



# Tokens

@dataclass
class Token:
    type: str
    value: Any
    line: int

TOKEN_PATTERNS = [
    ("COMMENT",    r"#[^\n]*"),
    ("STRING",     r'"[^"]*"'),
    ("NUMBER",     r"\d+"),
    ("NEWLINE",    r"\n"),
    ("WHITESPACE", r"[ \t]+"),
    ("LBRACE",     r"\{"),
    ("RBRACE",     r"\}"),
    ("COMMA",      r","),
    ("EQ",         r"=="),
    ("NEQ",        r"!="),
    ("LTE",        r"<="),
    ("GTE",        r">="),
    ("LT",         r"<"),
    ("GT",         r">"),
    ("ASSIGN",     r"="),
    ("PLUS",       r"\+"),
    ("MINUS",      r"-"),
    ("STAR",       r"\*"),
    ("SLASH",      r"/"),
    ("PERCENT",    r"%"),
    ("IDENT",      r"[A-Za-z_][A-Za-z0-9_]*"),
]

KEYWORDS = {
    "thread", "join", "lock", "semaphore", "acquire", "release",
    "queue", "send", "receive", "atomic", "increment", "decrement", "get",
    "if", "else", "while", "print", "sleep", "global", "true", "false",
}

_TOKEN_RE = re.compile(
    "|".join(f"(?P<{name}>{pat})" for name, pat in TOKEN_PATTERNS)
)


def tokenise(source: str) -> List[Token]:
    tokens = []
    line = 1
    for m in _TOKEN_RE.finditer(source):
        kind = m.lastgroup
        value = m.group()
        if kind in ("COMMENT", "WHITESPACE"):
            continue
        if kind == "NEWLINE":
            line += 1
            tokens.append(Token("NEWLINE", "\n", line))
            continue
        if kind == "STRING":
            tokens.append(Token("STRING", value[1:-1], line))
            continue
        if kind == "NUMBER":
            tokens.append(Token("NUMBER", int(value), line))
            continue
        if kind == "IDENT" and value in KEYWORDS:
            tokens.append(Token(value.upper(), value, line))
            continue
        tokens.append(Token(kind, value, line))
    tokens.append(Token("EOF", None, line))
    return tokens



# AST Nodes

@dataclass
class AssignNode:
    name: str
    is_global: bool
    expr: Any

@dataclass
class PrintNode:
    template: Optional[str]
    exprs: List[Any]

@dataclass
class NumberNode:
    value: int

@dataclass
class StringNode:
    value: str

@dataclass
class IdentNode:
    name: str

@dataclass
class BinOpNode:
    op: str
    left: Any
    right: Any

@dataclass
class ReceiveNode:
    queue_name: str

@dataclass
class GetAtomicNode:
    name: str

@dataclass
class ThreadNode:
    name: str
    body: List[Any]

@dataclass
class JoinNode:
    name: str

@dataclass
class LockDeclNode:
    name: str

@dataclass
class LockBlockNode:
    name: str
    body: List[Any]

@dataclass
class SemaphoreNode:
    name: str
    count_expr: Any

@dataclass
class AcquireNode:
    name: str

@dataclass
class ReleaseNode:
    name: str

@dataclass
class QueueNode:
    name: str

@dataclass
class SendNode:
    queue_name: str
    value_expr: Any

@dataclass
class AtomicNode:
    name: str
    initial_expr: Any

@dataclass
class IncrementNode:
    name: str

@dataclass
class DecrementNode:
    name: str

@dataclass
class IfNode:
    condition: Any
    body: List[Any]
    else_body: Optional[List[Any]]

@dataclass
class WhileNode:
    condition: Any
    body: List[Any]

@dataclass
class SleepNode:
    expr: Any



# Parser

class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def peek_type(self) -> str:
        return self.tokens[self.pos].type

    def consume(self, *expected_types) -> Token:
        tok = self.tokens[self.pos]
        if expected_types and tok.type not in expected_types:
            raise ParseError(
                f"Line {tok.line}: expected {expected_types}, got {tok.type!r} ({tok.value!r})"
            )
        self.pos += 1
        return tok

    def skip_newlines(self):
        while self.peek_type() == "NEWLINE":
            self.pos += 1

    def parse_program(self) -> List[Any]:
        stmts = []
        self.skip_newlines()
        while self.peek_type() != "EOF":
            stmt = self.parse_statement()
            if stmt is not None:
                stmts.append(stmt)
            self.skip_newlines()
        return stmts

    def parse_block(self) -> List[Any]:
        self.consume("LBRACE")
        self.skip_newlines()
        stmts = []
        while self.peek_type() != "RBRACE":
            if self.peek_type() == "EOF":
                raise ParseError("Unexpected EOF inside block")
            stmt = self.parse_statement()
            if stmt is not None:
                stmts.append(stmt)
            self.skip_newlines()
        self.consume("RBRACE")
        return stmts

    def parse_statement(self) -> Optional[Any]:
        self.skip_newlines()
        t = self.peek_type()
        if t == "NEWLINE":
            self.consume("NEWLINE")
            return None
        if t == "GLOBAL":   return self.parse_global_assign()
        if t == "THREAD":   return self.parse_thread()
        if t == "JOIN":     return self.parse_join()
        if t == "LOCK":     return self.parse_lock()
        if t == "SEMAPHORE":return self.parse_semaphore()
        if t == "ACQUIRE":  return self.parse_acquire()
        if t == "RELEASE":  return self.parse_release()
        if t == "QUEUE":    return self.parse_queue()
        if t == "SEND":     return self.parse_send()
        if t == "ATOMIC":   return self.parse_atomic()
        if t == "INCREMENT":return self.parse_increment()
        if t == "DECREMENT":return self.parse_decrement()
        if t == "IF":       return self.parse_if()
        if t == "WHILE":    return self.parse_while()
        if t == "PRINT":    return self.parse_print()
        if t == "SLEEP":    return self.parse_sleep()
        if t == "IDENT":    return self.parse_assign_or_expr()
        raise ParseError(f"Line {self.peek().line}: unexpected token {t!r} ({self.peek().value!r})")

    def parse_global_assign(self) -> AssignNode:
        self.consume("GLOBAL")
        name = self.consume("IDENT").value
        self.consume("ASSIGN")
        expr = self.parse_expr()
        self.consume_newline_or_eof()
        return AssignNode(name, True, expr)

    def parse_thread(self) -> ThreadNode:
        self.consume("THREAD")
        name = self.consume("IDENT").value
        body = self.parse_block()
        return ThreadNode(name, body)

    def parse_join(self) -> JoinNode:
        self.consume("JOIN")
        name = self.consume("IDENT").value
        self.consume_newline_or_eof()
        return JoinNode(name)

    def parse_lock(self):
        self.consume("LOCK")
        name = self.consume("IDENT").value
        if self.peek_type() == "LBRACE":
            body = self.parse_block()
            return LockBlockNode(name, body)
        self.consume_newline_or_eof()
        return LockDeclNode(name)

    def parse_semaphore(self) -> SemaphoreNode:
        self.consume("SEMAPHORE")
        name = self.consume("IDENT").value
        self.consume("ASSIGN")
        count_expr = self.parse_expr()
        self.consume_newline_or_eof()
        return SemaphoreNode(name, count_expr)

    def parse_acquire(self) -> AcquireNode:
        self.consume("ACQUIRE")
        name = self.consume("IDENT").value
        self.consume_newline_or_eof()
        return AcquireNode(name)

    def parse_release(self) -> ReleaseNode:
        self.consume("RELEASE")
        name = self.consume("IDENT").value
        self.consume_newline_or_eof()
        return ReleaseNode(name)

    def parse_queue(self) -> QueueNode:
        self.consume("QUEUE")
        name = self.consume("IDENT").value
        self.consume_newline_or_eof()
        return QueueNode(name)

    def parse_send(self) -> SendNode:
        self.consume("SEND")
        qname = self.consume("IDENT").value
        self.consume("COMMA")
        val = self.parse_expr()
        self.consume_newline_or_eof()
        return SendNode(qname, val)

    def parse_atomic(self) -> AtomicNode:
        self.consume("ATOMIC")
        name = self.consume("IDENT").value
        self.consume("ASSIGN")
        init = self.parse_expr()
        self.consume_newline_or_eof()
        return AtomicNode(name, init)

    def parse_increment(self) -> IncrementNode:
        self.consume("INCREMENT")
        name = self.consume("IDENT").value
        self.consume_newline_or_eof()
        return IncrementNode(name)

    def parse_decrement(self) -> DecrementNode:
        self.consume("DECREMENT")
        name = self.consume("IDENT").value
        self.consume_newline_or_eof()
        return DecrementNode(name)

    def parse_if(self) -> IfNode:
        self.consume("IF")
        cond = self.parse_comparison()
        body = self.parse_block()
        else_body = None
        self.skip_newlines()
        if self.peek_type() == "ELSE":
            self.consume("ELSE")
            else_body = self.parse_block()
        return IfNode(cond, body, else_body)

    def parse_while(self) -> WhileNode:
        self.consume("WHILE")
        cond = self.parse_comparison()
        body = self.parse_block()
        return WhileNode(cond, body)

    def parse_print(self) -> PrintNode:
        self.consume("PRINT")
        parts = []
        # collect comma-separated args until end of line
        first = self.parse_expr()
        parts.append(first)
        while self.peek_type() == "COMMA":
            self.consume("COMMA")
            parts.append(self.parse_expr())
        self.consume_newline_or_eof()
        # Build template: string literals become text, non-strings become {}
        template_parts = []
        value_exprs = []
        for p in parts:
            if isinstance(p, StringNode):
                template_parts.append(p.value)
            else:
                template_parts.append("{}")
                value_exprs.append(p)
        return PrintNode("".join(template_parts), value_exprs)

    def parse_sleep(self) -> SleepNode:
        self.consume("SLEEP")
        expr = self.parse_expr()
        self.consume_newline_or_eof()
        return SleepNode(expr)

    def parse_assign_or_expr(self):
        name = self.consume("IDENT").value
        if self.peek_type() == "ASSIGN":
            self.consume("ASSIGN")
            expr = self.parse_expr()
            self.consume_newline_or_eof()
            return AssignNode(name, False, expr)
        raise ParseError(f"Line {self.peek().line}: expected assignment after identifier {name!r}")

    def consume_newline_or_eof(self):
        if self.peek_type() == "NEWLINE":
            self.consume("NEWLINE")

    def parse_expr(self) -> Any:
        if self.peek_type() == "RECEIVE":
            self.consume("RECEIVE")
            name = self.consume("IDENT").value
            return ReceiveNode(name)
        if self.peek_type() == "GET":
            self.consume("GET")
            name = self.consume("IDENT").value
            return GetAtomicNode(name)
        return self.parse_additive()

    def parse_additive(self) -> Any:
        left = self.parse_multiplicative()
        while self.peek_type() in ("PLUS", "MINUS"):
            op = self.consume().value
            right = self.parse_multiplicative()
            left = BinOpNode(op, left, right)
        return left

    def parse_multiplicative(self) -> Any:
        left = self.parse_primary()
        while self.peek_type() in ("STAR", "SLASH", "PERCENT"):
            op = self.consume().value
            right = self.parse_primary()
            left = BinOpNode(op, left, right)
        return left

    def parse_primary(self) -> Any:
        t = self.peek_type()
        if t == "NUMBER":
            return NumberNode(self.consume("NUMBER").value)
        if t == "STRING":
            return StringNode(self.consume("STRING").value)
        if t == "IDENT":
            return IdentNode(self.consume("IDENT").value)
        if t == "MINUS":
            self.consume("MINUS")
            return BinOpNode("-", NumberNode(0), self.parse_primary())
        raise ParseError(f"Line {self.peek().line}: unexpected token in expression: {t!r} ({self.peek().value!r})")

    def parse_comparison(self) -> Any:
        left = self.parse_expr()
        if self.peek_type() in ("LT", "GT", "LTE", "GTE", "EQ", "NEQ"):
            op = self.consume().value
            right = self.parse_expr()
            return BinOpNode(op, left, right)
        return left



# Code Generator

class CompileError(Exception):
    pass


class CodeGen:
    """
    Walks the AST and emits ToyVM instruction tuples.

    Shared resources (locks, queues, semaphores, atomics, thread handles)
    are stored with GLOBAL_STORE so child threads can LOAD them.  Regular
    variables use thread-local STORE/LOAD.

    Jump addresses in while/if sublists are relative to the sublist's own
    index-0; they are offset to absolute positions when the sublist is
    appended to the growing output list.
    """

    def __init__(self):
        self.globals: set = set()       # explicit `global x = ...` names
        self.shared: set = set()        # locks, queues, semaphores, atomics, thread handles
        self.locks_declared: set = set()

    def compile(self, stmts: List[Any]) -> List[Tuple]:
        # First pass: identify all names that need to be globally visible
        for stmt in stmts:
            if isinstance(stmt, AssignNode) and stmt.is_global:
                self.globals.add(stmt.name)
            if isinstance(stmt, LockDeclNode):
                self.locks_declared.add(stmt.name)
                self.shared.add(stmt.name)
            if isinstance(stmt, LockBlockNode):
                self.shared.add(stmt.name)
            if isinstance(stmt, QueueNode):
                self.shared.add(stmt.name)
            if isinstance(stmt, SemaphoreNode):
                self.shared.add(stmt.name)
            if isinstance(stmt, AtomicNode):
                self.shared.add(stmt.name)
            if isinstance(stmt, ThreadNode):
                self.shared.add(stmt.name)
        return self._compile_stmts(stmts)

    def _store(self, name: str) -> Tuple:
        """Return the right STORE instruction for a name."""
        if name in self.globals or name in self.shared:
            return ("GLOBAL_STORE", name)
        return ("STORE", name)

    def _compile_stmts(self, stmts: List[Any]) -> List[Tuple]:
        out = []
        for stmt in stmts:
            sub = self._compile_stmt(stmt)
            # If the sublist contains jumps, offset them to absolute positions
            # now that we know where they will land in `out`.
            self._append_with_offset(out, sub)
        return out

    def _append_with_offset(self, out: List[Tuple], sublist: List[Tuple]):
        """
        Append sublist to out, adjusting JUMP/JUMP_IF addresses by len(out)
        so they become absolute in the final flat list.
        """
        offset = len(out)
        for instr in sublist:
            if instr[0] in ("JUMP", "JUMP_IF") and len(instr) > 1:
                out.append((instr[0], instr[1] + offset))
            else:
                out.append(instr)

    def _compile_stmt(self, stmt) -> List[Tuple]:
        if isinstance(stmt, AssignNode):    return self._compile_assign(stmt)
        if isinstance(stmt, PrintNode):     return self._compile_print(stmt)
        if isinstance(stmt, ThreadNode):    return self._compile_thread(stmt)
        if isinstance(stmt, JoinNode):      return self._compile_join(stmt)
        if isinstance(stmt, LockDeclNode):  return self._compile_lock_decl(stmt)
        if isinstance(stmt, LockBlockNode): return self._compile_lock_block(stmt)
        if isinstance(stmt, SemaphoreNode): return self._compile_semaphore(stmt)
        if isinstance(stmt, AcquireNode):   return self._compile_acquire(stmt)
        if isinstance(stmt, ReleaseNode):   return self._compile_release(stmt)
        if isinstance(stmt, QueueNode):     return self._compile_queue(stmt)
        if isinstance(stmt, SendNode):      return self._compile_send(stmt)
        if isinstance(stmt, AtomicNode):    return self._compile_atomic(stmt)
        if isinstance(stmt, IncrementNode): return self._compile_increment(stmt)
        if isinstance(stmt, DecrementNode): return self._compile_decrement(stmt)
        if isinstance(stmt, IfNode):        return self._compile_if(stmt)
        if isinstance(stmt, WhileNode):     return self._compile_while(stmt)
        if isinstance(stmt, SleepNode):     return self._compile_sleep(stmt)
        raise CompileError(f"Unknown AST node: {type(stmt)}")

    def _compile_assign(self, node: AssignNode) -> List[Tuple]:
        out = self._compile_expr(node.expr)
        if node.is_global:
            out.append(("GLOBAL_STORE", node.name))
        else:
            out.append(self._store(node.name))
        return out

    def _compile_print(self, node: PrintNode) -> List[Tuple]:
        """
        ToyVM PRINT peeks (does not pop) the stack for {} substitution.
        We compile each value expression, PRINT it with its prefix, then POP.
        """
        template = node.template
        value_exprs = list(node.exprs)

        if not value_exprs:
            return [("PRINT", template)]

        parts = template.split("{}")  # len == len(value_exprs) + 1
        out = []
        for i, expr in enumerate(value_exprs):
            prefix = parts[i]
            fmt = prefix + "{}"
            out.extend(self._compile_expr(expr))
            out.append(("PRINT", fmt))
            out.append(("POP",))
        suffix = parts[-1]
        if suffix:
            out.append(("PRINT", suffix))
        return out

    def _compile_thread(self, node: ThreadNode) -> List[Tuple]:
        # Compile body with same shared/globals context
        body_gen = CodeGen()
        body_gen.globals = self.globals
        body_gen.shared = self.shared
        body_gen.locks_declared = self.locks_declared
        body_instructions = body_gen._compile_stmts(node.body)
        return [
            ("PUSH", 0),
            ("THREAD_CREATE", [body_instructions]),
            ("GLOBAL_STORE", node.name),   # store globally so join can find it
        ]

    def _compile_join(self, node: JoinNode) -> List[Tuple]:
        return [("LOAD", node.name), ("THREAD_JOIN",)]

    def _compile_lock_decl(self, node: LockDeclNode) -> List[Tuple]:
        return [("LOCK_CREATE",), ("GLOBAL_STORE", node.name)]

    def _compile_lock_block(self, node: LockBlockNode) -> List[Tuple]:
        out = []
        if node.name not in self.locks_declared:
            out += [("LOCK_CREATE",), ("GLOBAL_STORE", node.name)]
            self.locks_declared.add(node.name)
            self.shared.add(node.name)
        out += [("LOAD", node.name), ("LOCK_ACQUIRE",)]
        out += self._compile_stmts(node.body)
        out += [("LOAD", node.name), ("LOCK_RELEASE",)]
        return out

    def _compile_semaphore(self, node: SemaphoreNode) -> List[Tuple]:
        out = self._compile_expr(node.count_expr)
        out += [("SEMAPHORE_CREATE",), ("GLOBAL_STORE", node.name)]
        return out

    def _compile_acquire(self, node: AcquireNode) -> List[Tuple]:
        return [("LOAD", node.name), ("SEMAPHORE_ACQUIRE",)]

    def _compile_release(self, node: ReleaseNode) -> List[Tuple]:
        return [("LOAD", node.name), ("SEMAPHORE_RELEASE",)]

    def _compile_queue(self, node: QueueNode) -> List[Tuple]:
        return [("QUEUE_CREATE",), ("GLOBAL_STORE", node.name)]

    def _compile_send(self, node: SendNode) -> List[Tuple]:
        # ToyVM QUEUE_SEND: message = stack.pop() (top), queue_name = stack.pop() (second)
        # So push queue_name first, then message on top.
        out = [("LOAD", node.queue_name)]
        out += self._compile_expr(node.value_expr)
        out.append(("QUEUE_SEND",))
        return out

    def _compile_atomic(self, node: AtomicNode) -> List[Tuple]:
        out = self._compile_expr(node.initial_expr)
        out += [("ATOMIC_CREATE",), ("GLOBAL_STORE", node.name)]
        return out

    def _compile_increment(self, node: IncrementNode) -> List[Tuple]:
        return [("LOAD", node.name), ("ATOMIC_INCREMENT",), ("POP",)]

    def _compile_decrement(self, node: DecrementNode) -> List[Tuple]:
        return [("LOAD", node.name), ("ATOMIC_DECREMENT",), ("POP",)]

    def _compile_if(self, node: IfNode) -> List[Tuple]:
        """
        Compile if/else with relative indices, then offset on append.

          <cond>          # >= 0 means true
          JUMP_IF body    # jump to body if true
          JUMP else/end   # else skip body
        body:
          ...
          JUMP end        # skip else (only if else exists)
        else:
          ...
        end:
        """
        cond = self._compile_condition(node.condition)
        body = self._compile_stmts(node.body)
        els  = self._compile_stmts(node.else_body) if node.else_body else []

        sub = []
        sub.extend(cond)
        jump_if_idx = len(sub);  sub.append(("JUMP_IF", 0))
        jump_else_idx = len(sub); sub.append(("JUMP", 0))
        body_start = len(sub)
        sub.extend(body)
        jump_end_idx = len(sub)
        if els:
            sub.append(("JUMP", 0))
        else_start = len(sub)
        sub.extend(els)
        end = len(sub)

        sub[jump_if_idx]   = ("JUMP_IF", body_start)
        sub[jump_else_idx] = ("JUMP",    else_start)
        if els:
            sub[jump_end_idx] = ("JUMP", end)

        return sub

    def _compile_while(self, node: WhileNode) -> List[Tuple]:
        """
        Compile while with relative indices, then offset on append.

        loop_start(=0):
          <cond>            # >= 0 means keep looping
          JUMP_IF body
          JUMP end
        body:
          ...
          JUMP loop_start   # always 0 within sublist
        end:
        """
        cond = self._compile_condition(node.condition)
        body = self._compile_stmts(node.body)

        sub = []
        loop_start = 0                          # always 0 in sublist
        sub.extend(cond)
        jump_if_idx  = len(sub); sub.append(("JUMP_IF", 0))
        jump_end_idx = len(sub); sub.append(("JUMP",    0))
        body_start   = len(sub)
        sub.extend(body)
        sub.append(("JUMP", loop_start))        # back to condition (relative=0)
        end = len(sub)

        sub[jump_if_idx]  = ("JUMP_IF", body_start)
        sub[jump_end_idx] = ("JUMP",    end)

        return sub

    def _compile_sleep(self, node: SleepNode) -> List[Tuple]:
        out = self._compile_expr(node.expr)
        out.append(("SLEEP",))
        return out

    def _compile_expr(self, node) -> List[Tuple]:
        if isinstance(node, NumberNode):   return [("PUSH", node.value)]
        if isinstance(node, StringNode):   return [("PUSH", node.value)]
        if isinstance(node, IdentNode):    return [("LOAD", node.name)]
        if isinstance(node, BinOpNode):    return self._compile_binop(node)
        if isinstance(node, ReceiveNode):
            return [("LOAD", node.queue_name), ("QUEUE_RECEIVE",)]
        if isinstance(node, GetAtomicNode):
            return [("LOAD", node.name), ("ATOMIC_GET",)]
        raise CompileError(f"Unknown expression node: {type(node)}")

    def _compile_binop(self, node: BinOpNode) -> List[Tuple]:
        left  = self._compile_expr(node.left)
        right = self._compile_expr(node.right)
        if node.op == "+": return left + right + [("ADD",)]
        if node.op == "-": return left + right + [("SUB",)]
        if node.op == "*": return left + right + [("MUL",)]
        if node.op == "/": return left + right + [("DIV",)]
        if node.op == "%": return left + right + [("MUL", "mod")]
        # Comparison ops fall through to condition compiler
        return self._compile_condition(node)

    def _compile_condition(self, node) -> List[Tuple]:
        """
        Produce a stack value that is >= 0 when the condition is TRUE,
        and < 0 when FALSE — suitable for JUMP_IF.

        Mapping (using integer arithmetic):
          a <  b  =>  b - a - 1   (>= 0 iff a <  b)
          a >  b  =>  a - b - 1   (>= 0 iff a >  b)
          a <= b  =>  b - a       (>= 0 iff a <= b)
          a >= b  =>  a - b       (>= 0 iff a >= b)
          a == b  =>  -(a-b)^2    (== 0 iff equal, < 0 otherwise)
                      computed as: (a-b)*(-1) if a!=b, 0 if equal
                      simpler:     PUSH 0 when equal, else negative
                      practical:   push (b-a), DUP, MUL gives (b-a)^2 >= 0.
                                   Negate: PUSH 0, swap_sub = 0 - (b-a)^2.
                                   When equal => 0 (jump), else negative (no jump). ✓
          a != b  =>  (a-b)^2 - 1  (>= 0 iff a != b, since (a-b)^2 >= 1 when a!=b)
        """
        if not isinstance(node, BinOpNode) or node.op not in ("<",">","<=",">=","==","!="):
            return self._compile_expr(node)

        L = self._compile_expr(node.left)
        R = self._compile_expr(node.right)

        if node.op == "<":   return R + L + [("SUB",), ("PUSH", 1), ("SUB",)]
        if node.op == ">":   return L + R + [("SUB",), ("PUSH", 1), ("SUB",)]
        if node.op == "<=":  return R + L + [("SUB",)]
        if node.op == ">=":  return L + R + [("SUB",)]
        if node.op == "==":
            # (b-a)^2, then negate: 0-(b-a)^2
            diff = R + L + [("SUB",)]
            return diff + [("DUP",), ("MUL",), ("PUSH", 0), ("PUSH", 1), ("SUB",), ("MUL",)]
        if node.op == "!=":
            # (a-b)^2 - 1
            diff = L + R + [("SUB",)]
            return diff + [("DUP",), ("MUL",), ("PUSH", 1), ("SUB",)]
        return self._compile_expr(node)



# Public API

def compile_concur(source: str) -> List[Tuple]:
    """
    Compile a Concur source string into a ToyVM instruction list.
    Returns a list of instruction tuples for ToyVM.create_thread().
    """
    tokens = tokenise(source)
    parser = Parser(tokens)
    ast = parser.parse_program()
    codegen = CodeGen()
    return codegen.compile(ast)


def compile_file(path: str) -> List[Tuple]:
    with open(path, "r") as f:
        return compile_concur(f.read())


def pretty_print(instructions: List[Tuple], indent: int = 0) -> str:
    lines = []
    pad = "    " * indent
    for i, instr in enumerate(instructions):
        if instr[0] == "THREAD_CREATE":
            lines.append(f"{pad}{i:3d}: THREAD_CREATE [")
            for j, body in enumerate(instr[1]):
                lines.append(f"{pad}    # body {j}:")
                lines.append(pretty_print(body, indent + 2))
            lines.append(f"{pad}     ]")
        else:
            lines.append(f"{pad}{i:3d}: {instr}")
    return "\n".join(lines)


# CLI

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Concur → ToyVM compiler")
    ap.add_argument("source", help="Path to .concur source file")
    ap.add_argument("--run",       action="store_true", help="Run via ToyVM after compiling")
    ap.add_argument("--debug",     action="store_true", help="Enable ToyVM debug output")
    ap.add_argument("--max-steps", type=int, default=10000)
    ap.add_argument("--emit",      action="store_true", help="Print compiled instructions")
    args = ap.parse_args()

    try:
        instructions = compile_file(args.source)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.emit or not args.run:
        print("=== Compiled Instructions ===")
        print(pretty_print(instructions))

    if args.run:
        try:
            from toyvm import ToyVM
        except ImportError:
            print("\nCould not import ToyVM — make sure toyvm.py is in the same directory.")
            sys.exit(1)
        print("\n=== Running ===")
        vm = ToyVM()
        vm.create_thread(instructions, name="main")
        vm.run(max_steps=args.max_steps, debug=args.debug)


if __name__ == "__main__":
    main()
