"""
Custom exceptions for the BASIC interpreter.
Provides specific error types for different failure modes.
"""


class BasicError(Exception):
    """Base exception for all BASIC interpreter errors."""
    pass


class TokenizationError(BasicError):
    """Raised when tokenization fails."""
    pass


class ParserError(BasicError):
    """Raised when parsing fails."""
    pass


class EvaluationError(BasicError):
    """Raised when expression evaluation fails."""
    pass


class ExecutionError(BasicError):
    """Raised when command execution fails."""
    pass


class ArrayError(BasicError):
    """Raised for array-related errors."""
    pass


class ControlFlowError(BasicError):
    """Raised for control flow errors (GOTO, GOSUB, etc.)."""
    pass
