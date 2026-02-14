"""
State management for the BASIC interpreter.
Centralizes all runtime state including variables, arrays, code, and control flow.
"""
from typing import Dict, Any, List, Tuple, Optional


class InterpreterState:
    """Maintains the runtime state of the BASIC interpreter."""
    
    def __init__(self):
        # Variables storage (including special "#" line number variable)
        self.variables: Dict[str, Any] = {"#": 0}
        
        # Arrays storage: array_name -> {tuple_of_indices: value}
        self.arrays: Dict[str, Dict[Tuple[int, ...], Any]] = {}
        
        # Array dimensions: array_name -> tuple_of_dimensions
        self.array_dims: Dict[str, Tuple[int, ...]] = {}
        
        # Program code: line_number -> code_string
        self.code: Dict[int, str] = {}
        
        # User-defined functions: func_name -> {params: [...], expression: "..."}
        self.user_functions: Dict[str, Dict[str, Any]] = {}
        
        # Control flow state
        self.paused: bool = False
        self.loops: Dict[str, Dict[str, Any]] = {}
        self.whiles: Dict[str, Tuple[int, ...]] = {}
        self.stack: List[int] = []

    def reset(self, preserve_code: bool = False) -> None:
        """Reset interpreter state, optionally preserving loaded code."""
        self.variables = {"#": 0}
        self.arrays = {}
        self.array_dims = {}
        self.user_functions = {}
        if not preserve_code:
            self.code = {}
        self.paused = False
        self.loops = {}
        self.whiles = {}
        self.stack = []

    def get_variable(self, name: str, default: Any = 0) -> Any:
        """Get variable value with default."""
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: Any) -> None:
        """Set variable value."""
        self.variables[name] = value

    def declare_array(self, name: str, dimensions: Tuple[int, ...]) -> None:
        """Declare an array with given dimensions."""
        self.array_dims[name] = dimensions
        self.arrays[name] = {}

    def get_array_value(self, name: str, indices: Tuple[int, ...], default: Any = 0) -> Any:
        """Get array value at indices with default."""
        if name not in self.arrays:
            return default
        return self.arrays[name].get(indices, default)

    def set_array_value(self, name: str, indices: Tuple[int, ...], value: Any) -> None:
        """Set array value at indices."""
        if name not in self.arrays:
            raise ValueError(f"Array '{name}' not declared")
        self.arrays[name][indices] = value

    def get_current_line(self) -> int:
        """Get current execution line number."""
        return self.variables.get("#", 0)

    def set_current_line(self, line_number: int) -> None:
        """Set current execution line number."""
        self.variables["#"] = line_number

    def get_next_line(self, current: int) -> Optional[int]:
        """Get next line number after current, or None if at end."""
        sorted_lines = sorted(self.code.keys())
        for line in sorted_lines:
            if line > current:
                return line
        return None
