#!/usr/bin/env python3
"""
BASIC Interpreter — Visitor Pattern implementation
This is a simple interpreter for a small subset of BASIC
"""

import sys
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type


# Exception hierarchy

class InterpreterError(Exception):
    """Base for all interpreter errors."""

class ParserError(InterpreterError):
    """Raised when the expression parser encounters invalid syntax."""

class ExecutionError(InterpreterError):
    """Raised during program execution (type mismatches, missing lines, etc.)."""

class StackError(ExecutionError):
    """Raised on GOSUB/RETURN stack violations."""

class UndefinedLineError(ExecutionError):
    """Raised when a GOTO/GOSUB targets a non-existent line."""


# Interpreter state  (singleton, but properly reset-able)

_GOSUB_STACK_LIMIT = 256
_LOOP_DEPTH_LIMIT  = 128

class InterpreterState:
    """
    Holds all mutable interpreter state.

    The singleton is created once; call ``InterpreterState.reset()`` to
    clear it between programs without touching the singleton machinery.
    """

    _instance: Optional["InterpreterState"] = None

    def __new__(cls) -> "InterpreterState":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.code:      Dict[int, str]            = {}
        self.variables: Dict[str, Any]            = {"#": 10}
        self.stack:     List[int]                 = []
        self.loops:     Dict[str, Tuple[int, Any]] = {}

    def reset(self) -> None:
        """Wipe all program state (code, variables, stack, loops)."""
        self._init()



# AST node hierarchy

class Expression(ABC):
    """Abstract base for all AST expression nodes."""

    @abstractmethod
    def accept(self, visitor: "ExpressionVisitor") -> Any:
        ...


class NumberExpression(Expression):
    __slots__ = ("value",)

    def __init__(self, value: int) -> None:
        self.value = value

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_number(self)


class StringExpression(Expression):
    __slots__ = ("value",)

    def __init__(self, value: str) -> None:
        self.value = value

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_string(self)


class VariableExpression(Expression):
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_variable(self)


class BinaryExpression(Expression):
    __slots__ = ("left", "operator", "right")

    def __init__(
        self,
        left: Expression,
        operator: str,
        right: Expression,
    ) -> None:
        self.left     = left
        self.operator = operator
        self.right    = right

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_binary(self)


class FunctionExpression(Expression):
    __slots__ = ("name", "args")

    def __init__(self, name: str, args: List[Expression]) -> None:
        self.name = name
        self.args = args

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_function(self)


# Visitor interface + concrete evaluation visitor

class ExpressionVisitor(ABC):
    """Visitor interface — one method per concrete Expression subclass."""

    @abstractmethod
    def visit_number(self, expr: NumberExpression) -> Any: ...

    @abstractmethod
    def visit_string(self, expr: StringExpression) -> Any: ...

    @abstractmethod
    def visit_variable(self, expr: VariableExpression) -> Any: ...

    @abstractmethod
    def visit_binary(self, expr: BinaryExpression) -> Any: ...

    @abstractmethod
    def visit_function(self, expr: FunctionExpression) -> Any: ...


class EvaluationVisitor(ExpressionVisitor):
    """Walks the AST and returns the computed value of each node."""

    def __init__(self) -> None:
        self.state = InterpreterState()


    # - leaf nodes

    def visit_number(self, expr: NumberExpression) -> int:
        return expr.value

    def visit_string(self, expr: StringExpression) -> str:
        return expr.value

    def visit_variable(self, expr: VariableExpression) -> Any:
        name = expr.name
        if name not in self.state.variables:
            # Auto-initialise: string vars (ending with $) -> "", numeric -> 0
            self.state.variables[name] = "" if name.endswith("$") else 0
        return self.state.variables[name]


    # - binary operations

    def visit_binary(self, expr: BinaryExpression) -> Any:
        left  = expr.left.accept(self)
        right = expr.right.accept(self)

        # Coerce mixed string/number for concatenation with +
        if expr.operator == "+" and isinstance(left, str) != isinstance(right, str):
            left  = str(left)
            right = str(right)

        op = expr.operator
        try:
            if op == "+":
                return left + right
            if op == "-":
                return left - right       # type: ignore[operator]
            if op == "*":
                return left * right       # type: ignore[operator]
            if op == "/":
                if right == 0:
                    raise ExecutionError("Division by zero")
                return left / right       # type: ignore[operator]
            if op == "=":
                return 1 if left == right else 0
            if op == "<":
                return 1 if left < right else 0   # type: ignore[operator]
            if op == ">":
                return 1 if left > right else 0   # type: ignore[operator]
        except TypeError as exc:
            raise ExecutionError(
                f"Type error for operator '{op}' on "
                f"{type(left).__name__} and {type(right).__name__}: {exc}"
            ) from exc

        raise ExecutionError(f"Unknown operator: '{op}'")


    # - built-in functions

    def visit_function(self, expr: FunctionExpression) -> Any:
        args: List[Any] = [a.accept(self) for a in expr.args]
        name = expr.name

        if not args:
            raise ParserError(f"Function '{name}' requires at least one argument")

        s = str(args[0])

        try:
            if name == "LEFT":
                n = int(args[1]) if len(args) > 1 else 0
                return s[:n]
            if name == "RIGHT":
                n = int(args[1]) if len(args) > 1 else 0
                return s[-n:] if n else ""
            if name == "MID":
                start = int(args[1]) - 1 if len(args) > 1 else 0
                length = int(args[2]) if len(args) > 2 else len(s) - start
                return s[start: start + length]
            if name == "LEN":
                return len(s)
            if name == "STR":
                return str(args[0])
        except (IndexError, ValueError) as exc:
            raise ParserError(f"Error in function {name}: {exc}") from exc

        raise ParserError(f"Unknown function: '{name}'")



# Expression parser

class ExpressionParser:
    """
    Recursive-descent parser that produces an Expression AST.

    Grammar (simplified):
        expr   = term  { ('+' | '-' | '=' | '<' | '>') term }
        term   = factor { ('*' | '/') factor }
        factor = FUNC'$(' args ')' | '(' expr ')' | STRING | NUMBER | VARIABLE
    """

    def __init__(self, text: str) -> None:
        self.text = text.strip()

    def parse(self, text: Optional[str] = None) -> Expression:
        if text is not None:
            self.text = text.strip()
        if not self.text:
            raise ParserError("Empty expression")
        return self._parse_expr()

    # - grammar rules

    def _parse_expr(self) -> Expression:
        left = self._parse_term()
        while self.text and self.text[0] in "+-=<>":
            op = self.text[0]
            self.text = self.text[1:].strip()
            right = self._parse_term()
            left = BinaryExpression(left, op, right)
        return left

    def _parse_term(self) -> Expression:
        left = self._parse_factor()
        while self.text and self.text[0] in "*/":
            op = self.text[0]
            self.text = self.text[1:].strip()
            right = self._parse_factor()
            left = BinaryExpression(left, op, right)
        return left

    def _parse_factor(self) -> Expression:
        # Built-in function call:  NAME$(arg, ...)
        func_match = re.match(r'([A-Z]+)\$\((.*?)\)', self.text)
        if func_match:
            func_name = func_match.group(1)
            args_text = func_match.group(2)
            self.text  = self.text[len(func_match.group(0)):].strip()
            args: List[Expression] = []
            for raw in args_text.split(","):
                raw = raw.strip()
                if raw:
                    args.append(ExpressionParser(raw).parse())
            return FunctionExpression(func_name, args)

        # Parenthesised sub-expression
        if self.text and self.text[0] == "(":
            self.text = self.text[1:].strip()
            expr = self._parse_expr()
            if not self.text or self.text[0] != ")":
                raise ParserError("Missing closing parenthesis")
            self.text = self.text[1:].strip()
            return expr

        if self.text.startswith('"'):
            return self._parse_string()

        if self.text and self.text[0].isdigit():
            return self._parse_number()

        return self._parse_variable()

    # - terminals

    def parse_number(self) -> NumberExpression:
        """Public helper used by the REPL loader."""
        return self._parse_number()

    def _parse_number(self) -> NumberExpression:
        i = 0
        while i < len(self.text) and self.text[i].isdigit():
            i += 1
        if i == 0:
            raise ParserError(f"Expected number, got: {self.text!r}")
        n = int(self.text[:i])
        self.text = self.text[i:].strip()
        return NumberExpression(n)

    def _parse_string(self) -> StringExpression:
        match = re.match(r'"([^"]*)"', self.text)
        if not match:
            raise ParserError("Unterminated string literal")
        self.text = self.text[len(match.group(0)):].strip()
        return StringExpression(match.group(1))

    def _parse_variable(self) -> VariableExpression:
        i = 0
        while i < len(self.text) and (self.text[i].isalnum() or self.text[i] == "$"):
            i += 1
        if i == 0:
            raise ParserError(f"Unexpected token: {self.text!r}")
        name = self.text[:i]
        self.text = self.text[i:].strip()
        return VariableExpression(name)



# Command hierarchy

class Command(ABC):
    def __init__(self) -> None:
        self.state = InterpreterState()

    @abstractmethod
    def execute(self, args: str) -> None: ...


class ParsedCommand(Command):
    """
    Template Method pattern layered on top of Command:
      preprocess → process → postprocess
    Subclasses only need to implement process().
    """

    def execute(self, args: str) -> None:
        self.preprocess(args)
        self.process(args)
        self.postprocess(args)

    def preprocess(self, args: str) -> None:
        pass

    @abstractmethod
    def process(self, args: str) -> None: ...

    def postprocess(self, args: str) -> None:
        pass

    def parse_expression(self, expr: str) -> Any:
        parser    = ExpressionParser(expr)
        tree      = parser.parse()
        evaluator = EvaluationVisitor()
        return tree.accept(evaluator)


# - concrete commands

class PrintCommand(ParsedCommand):
    def process(self, args: str) -> None:
        parts  = args.split(";")
        tokens: List[str] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            try:
                value = self.parse_expression(part)
                # Suppress numeric zero placeholders only if the original
                # expression was not a bare literal "0"
                if value != 0 or part == "0":
                    tokens.append(str(value))
            except InterpreterError as exc:
                print(f"[PRINT error] {exc}")
        print(" ".join(tokens))


class InputCommand(ParsedCommand):
    def process(self, args: str) -> None:
        parts    = args.split(";", 1)
        prompt   = "> "
        var_name = args.strip()

        if len(parts) > 1:
            try:
                evaluator  = EvaluationVisitor()
                prompt_val = ExpressionParser(parts[0].strip()).parse().accept(evaluator)
                prompt     = str(prompt_val) + " "
            except InterpreterError:
                pass
            var_name = parts[1].strip()

        raw = input(prompt).strip()

        if var_name.endswith("$"):
            self.state.variables[var_name] = raw
        else:
            try:
                self.state.variables[var_name] = (
                    int(raw) if raw.lstrip("-").isdigit()
                    else float(raw)
                )
            except ValueError:
                print(f"[INPUT] Non-numeric value for '{var_name}'; storing 0")
                self.state.variables[var_name] = 0


class LetCommand(ParsedCommand):
    def process(self, args: str) -> None:
        if "=" not in args:
            print(f"[LET] Syntax error: missing '=' in '{args}'")
            return
        var, _, expr = args.partition("=")
        var  = var.strip()
        expr = expr.strip()
        if not var:
            print("[LET] Syntax error: empty variable name")
            return
        try:
            self.state.variables[var] = self.parse_expression(expr)
        except InterpreterError as exc:
            print(f"[LET] Error: {exc}")


class IfCommand(ParsedCommand):
    def process(self, args: str) -> None:
        match = re.search(r'\bTHEN\b', args, re.IGNORECASE)
        if match:
            cond      = args[:match.start()].strip()
            then_stmt = args[match.end():].strip()
        else:
            cond      = args.strip()
            then_stmt = ""

        try:
            result = self.parse_expression(cond)
        except InterpreterError as exc:
            print(f"[IF] Condition error: {exc}")
            return

        if result and then_stmt:
            InterpreterEngine().execute_line(then_stmt)


class GotoCommand(ParsedCommand):
    def process(self, args: str) -> None:
        try:
            line_num = int(self.parse_expression(args.strip()))
        except (InterpreterError, ValueError) as exc:
            print(f"[GOTO] Bad line number: {exc}")
            return
        if line_num not in self.state.code:
            print(f"[GOTO] Line {line_num} does not exist")
            return
        self.state.variables["#"] = line_num


class GosubCommand(ParsedCommand):
    def process(self, args: str) -> None:
        if len(self.state.stack) >= _GOSUB_STACK_LIMIT:
            raise StackError(
                f"GOSUB stack overflow (limit {_GOSUB_STACK_LIMIT})"
            )
        try:
            line_num = int(self.parse_expression(args.strip()))
        except (InterpreterError, ValueError) as exc:
            print(f"[GOSUB] Bad line number: {exc}")
            return
        if line_num not in self.state.code:
            raise UndefinedLineError(f"GOSUB to undefined line {line_num}")
        self.state.stack.append(self.state.variables["#"])
        self.state.variables["#"] = line_num


class ReturnCommand(Command):
    def execute(self, args: str) -> None:
        if not self.state.stack:
            print("[RETURN] RETURN without GOSUB — halting")
            self.state.variables["#"] = 0
            return
        self.state.variables["#"] = self.state.stack.pop()


class ForCommand(ParsedCommand):
    def process(self, args: str) -> None:
        if len(self.state.loops) >= _LOOP_DEPTH_LIMIT:
            raise ExecutionError(
                f"FOR loop depth limit reached ({_LOOP_DEPTH_LIMIT})"
            )
        if "=" not in args:
            print("[FOR] Syntax error: missing '='")
            return
        var, _, rest = args.partition("=")
        var   = var.strip()
        parts = re.split(r'\bTO\b', rest, flags=re.IGNORECASE, maxsplit=1)
        if len(parts) < 2:
            print("[FOR] Syntax error: missing TO clause")
            return
        try:
            start = self.parse_expression(parts[0].strip())
            end   = self.parse_expression(parts[1].strip())
        except InterpreterError as exc:
            print(f"[FOR] Error: {exc}")
            return

        self.state.variables[var] = start
        # Store (loop-start-line, end-value)
        self.state.loops[var] = (self.state.variables["#"], end)


class NextCommand(ParsedCommand):
    def process(self, args: str) -> None:
        var = args.strip()
        if var not in self.state.loops:
            print(f"[NEXT] NEXT without matching FOR for '{var}'")
            return

        start_line, end_value = self.state.loops[var]
        self.state.variables[var] += 1

        if self.state.variables[var] <= end_value:
            self.state.variables["#"] = start_line + 1
        else:
            del self.state.loops[var]
            following = next(
                (n for n in sorted(self.state.code) if n > self.state.variables["#"]),
                0,
            )
            self.state.variables["#"] = following


class ListCommand(Command):
    def execute(self, args: str) -> None:
        if not self.state.code:
            print("[LIST] No program loaded.")
            return
        for n, line in sorted(self.state.code.items()):
            print(f"{n:5}  {line}")


class RenumberCommand(Command):
    def execute(self, args: str) -> None:
        if not self.state.code:
            print("[REN] No program to renumber.")
            return

        old_lines   = sorted(self.state.code)
        line_map: Dict[int, int] = {}
        new_code:  Dict[int, str] = {}
        start, step = 10, 10

        for i, old in enumerate(old_lines):
            new = start + i * step
            line_map[old] = new
            new_code[new] = self.state.code[old]

        for new_n in new_code:
            new_code[new_n] = self._rewrite_refs(new_code[new_n], line_map)

        self.state.code.clear()
        self.state.code.update(new_code)
        print("[REN] Program renumbered.")

    def _rewrite_refs(self, line: str, mapping: Dict[int, int]) -> str:
        parts = line.split(None, 1)
        if not parts:
            return line
        cmd  = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        if cmd in ("goto", "gosub"):
            try:
                old = int(rest.strip())
                return f"{cmd} {mapping.get(old, old)}"
            except ValueError:
                return line

        if cmd == "if":
            m = re.search(r'\bTHEN\b\s*(\d+)', rest, re.IGNORECASE)
            if m:
                old = int(m.group(1))
                new = mapping.get(old, old)
                if old not in mapping:
                    print(f"[REN] Warning: line {old} referenced in IF..THEN not found")
                return line.replace(m.group(1), str(new), 1)

        return line


class RunCommand(Command):
    def execute(self, args: str) -> None:
        if not self.state.code:
            print("[RUN] No program loaded.")
            return
        self.state.variables["#"] = min(self.state.code)
        InterpreterEngine().run()


class HelpCommand(Command):
    _TEXT = """\
Commands
  PRINT expr [; expr ...]   Print values (semicolon-separated)
  INPUT [prompt ;] var      Read input into var (string vars end with $)
  LET var = expr            Assign a value  (LET is optional: var = expr works)
  IF cond THEN stmt         Conditional single-line branch
  GOTO lineno               Jump to a line number
  GOSUB lineno              Call subroutine at lineno  (stack limit: 256)
  RETURN                    Return from subroutine
  FOR var = start TO end    Begin a counted loop  (depth limit: 128)
  NEXT var                  End of counted loop
  RUN                       Run the stored program from the first line
  LIST                      Print the stored program
  REN                       Renumber stored lines in steps of 10
  STOP / END                Halt program execution
  BYE                       Exit the interpreter
  HELP                      Show this message

Built-in functions
  LEFT$(s, n)               First n characters of s
  RIGHT$(s, n)              Last n characters of s
  MID$(s, i, n)             n characters starting at position i (1-based)
  LEN$(s)                   Length of s
  STR$(x)                   Convert number x to string

Operators  + - * /  =  <  >
  + on strings performs concatenation.

Tips
  Lines that start with a number are stored in the program.
  Lines without a number are executed immediately.
  Press Ctrl-C during RUN to interrupt and return to the prompt.\
"""

    def execute(self, args: str) -> None:
        print(self._TEXT)


class ByeCommand(Command):
    def execute(self, args: str) -> None:
        sys.exit(0)


class StopCommand(Command):
    def execute(self, args: str) -> None:
        print("Program stopped.")
        self.state.variables["#"] = 0



# Command factory

class CommandFactory:
    _commands: Dict[str, Type[Command]] = {
        "print":  PrintCommand,
        "input":  InputCommand,
        "goto":   GotoCommand,
        "if":     IfCommand,
        "run":    RunCommand,
        "let":    LetCommand,
        "gosub":  GosubCommand,
        "return": ReturnCommand,
        "for":    ForCommand,
        "next":   NextCommand,
        "list":   ListCommand,
        "ren":    RenumberCommand,
        "help":   HelpCommand,
        "bye":    ByeCommand,
        "stop":   StopCommand,
        "end":    StopCommand,
    }

    @classmethod
    def create_command(cls, name: str) -> Optional[Command]:
        return cls._commands[name.lower()]() if name.lower() in cls._commands else None

    @classmethod
    def register_command(cls, name: str, command_class: Type[Command]) -> None:
        cls._commands[name.lower()] = command_class


# Interpreter engine

_MAX_STEPS = 1_000_000  # hard cap to detect infinite loops


class InterpreterEngine:
    def __init__(self) -> None:
        self.state = InterpreterState()

    # - public interface

    def load_program(self, filename: str) -> None:
        """Load a BASIC program from a file."""
        try:
            with open(filename) as fh:
                for raw in fh:
                    raw = raw.strip()
                    if raw:
                        lineno, code = self._split_line(raw)
                        self.state.code[lineno] = code
        except OSError as exc:
            raise ExecutionError(f"Cannot open '{filename}': {exc}") from exc

    def execute_line(self, line: str) -> None:
        """Execute a single (already stripped) line of BASIC code."""
        line = line.strip()
        if not line:
            return

        parts = line.split(None, 1)
        cmd   = parts[0].lower()
        args  = parts[1] if len(parts) > 1 else ""

        command = CommandFactory.create_command(cmd)
        if command:
            command.execute(args)
        elif "=" in line:
            # Implicit LET:  X = expr
            CommandFactory.create_command("let").execute(line)  # type: ignore[union-attr]
        else:
            print(f"[SYNTAX] Unknown command: '{cmd}'")

    def run(self) -> None:
        """Run the loaded program from the first line."""
        if not self.state.code:
            print("[RUN] No program loaded.")
            return

        self.state.variables["#"] = min(self.state.code)
        steps = 0

        try:
            while self.state.variables["#"] > 0:
                steps += 1
                if steps > _MAX_STEPS:
                    print(f"[RUN] Execution limit ({_MAX_STEPS} steps) reached — possible infinite loop")
                    break

                pc = self.state.variables["#"]

                if pc not in self.state.code:
                    # Skip to the next defined line
                    nxt = next((n for n in sorted(self.state.code) if n > pc), 0)
                    self.state.variables["#"] = nxt
                    continue

                line = self.state.code[pc]
                try:
                    self.execute_line(line)
                except (ExecutionError, StackError, UndefinedLineError) as exc:
                    print(f"[ERROR at line {pc}] {exc}")
                    break

                # Advance PC only if the command itself didn't change it
                if self.state.variables["#"] == pc:
                    nxt = next((n for n in sorted(self.state.code) if n > pc), 0)
                    self.state.variables["#"] = nxt

        except KeyboardInterrupt:
            print(f"\nInterrupted at line {self.state.variables['#']}.")
            self.state.variables["#"] = 0  # halt cleanly

    def evaluate_expression(self, expr: str) -> Any:
        """Public helper to evaluate a single expression string."""
        try:
            tree = ExpressionParser(expr).parse()
            return tree.accept(EvaluationVisitor())
        except InterpreterError as exc:
            print(f"[EVAL] Error in '{expr}': {exc}")
            return 0

    # - private helpers

    @staticmethod
    def _split_line(line: str) -> Tuple[int, str]:
        head, *rest = line.split(maxsplit=1)
        try:
            return int(head), rest[0] if rest else ""
        except ValueError as exc:
            raise ParserError(f"Line number expected, got '{head}'") from exc



# REPL / file-load entry point

def _feed_line(engine: InterpreterEngine, raw: str) -> None:
    """
    Dispatch a line from the REPL or a file.

    Lines that start with a digit are treated as numbered program lines to
    store (or overwrite).  Everything else is an immediate command — RUN,
    LIST, PRINT, LET, etc. — and is executed straight away.
    """
    raw = raw.strip()
    if not raw:
        return

    if raw[0].isdigit():
        # Numbered line: split off the line number and store the rest.
        parser = ExpressionParser(raw)
        try:
            lineno_expr = parser.parse_number()
            lineno      = lineno_expr.accept(EvaluationVisitor())
            engine.state.code[lineno] = parser.text
        except (ParserError, InterpreterError) as exc:
            print(f"[STORE] {exc}")
    else:
        # Immediate command: execute directly.
        engine.execute_line(raw)


def main() -> None:
    engine = InterpreterEngine()

    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1]) as fh:
                for line in fh:
                    _feed_line(engine, line)
        except OSError as exc:
            print(f"Cannot open file: {exc}", file=sys.stderr)
            sys.exit(1)
        engine.run()
    else:
        print("BASIC Interpreter  (type HELP for commands, BYE to quit)")
        while True:
            try:
                line = input("> ")
            except EOFError:
                break
            except KeyboardInterrupt:
                print()   # newline after ^C, then back to prompt
                continue
            _feed_line(engine, line)


if __name__ == "__main__":
    main()
