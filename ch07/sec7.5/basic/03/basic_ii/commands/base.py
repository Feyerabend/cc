"""
Base classes for BASIC commands.
Provides the framework for command execution.
"""
from abc import ABC, abstractmethod
from typing import Any
from ..core.state import InterpreterState
from ..core.exceptions import ExecutionError
from ..parsing.tokenizer import Tokenizer
from ..parsing.parser import ExpressionParser
from ..execution.evaluator import ExpressionEvaluator


class Command(ABC):
    """Base class for all BASIC commands."""

    def __init__(self, state: InterpreterState, debug: bool = False):
        self.state = state
        self.debug = debug

    @abstractmethod
    def execute(self, args: str) -> None:
        """Execute the command with given arguments."""
        pass

    def _log(self, message: str) -> None:
        """Log debug message if debug mode is enabled."""
        if self.debug:
            print(f"DEBUG: {message}")


class ParsedCommand(Command):
    """
    Base class for commands that need expression parsing.
    Provides lifecycle methods and expression evaluation.
    """

    def execute(self, args: str) -> None:
        """Execute command with pre/post processing hooks."""
        self.preprocess(args)
        self.process(args)
        self.postprocess(args)

    def preprocess(self, args: str) -> None:
        """Hook called before processing. Override if needed."""
        pass

    @abstractmethod
    def process(self, args: str) -> None:
        """Main command processing logic. Must be implemented."""
        pass

    def postprocess(self, args: str) -> None:
        """Hook called after processing. Override if needed."""
        pass

    def parse_expression(self, expr_str: str) -> Any:
        """Parse and evaluate an expression string."""
        try:
            tokenizer = Tokenizer(expr_str)
            tokens = tokenizer.tokenize()
            
            parser = ExpressionParser(tokens)
            expression = parser.parse()
            
            evaluator = ExpressionEvaluator(self.state, self.debug)
            return evaluator.evaluate(expression)
        except Exception as e:
            raise ExecutionError(f"Error evaluating expression '{expr_str}': {e}")
