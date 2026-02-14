from typing import Dict, Any, List

class ParserError(Exception):
    pass

class InterpreterError(Exception):
    pass

class ExecutionError(InterpreterError):
    pass

class InterpreterState:
    def __init__(self):
        self.variables: Dict[str, Any] = {"#": 0}
        self.arrays: Dict[str, Dict[tuple, Any]] = {}
        self.array_dims: Dict[str, tuple] = {}
        self.code: Dict[int, str] = {}
        self.paused: bool = False
        self.loops: Dict[str, Dict[str, Any]] = {}
        self.whiles: Dict[str, tuple] = {}
        self.stack: List[int] = []

    def reset(self, preserve_code: bool = False):
        self.variables = {"#": 0}
        self.arrays = {}
        self.array_dims = {}
        if not preserve_code:
            self.code = {}
        self.paused = False
        self.loops = {}
        self.whiles = {}
        self.stack = []