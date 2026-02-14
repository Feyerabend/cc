
## Projects

This document outlines three projects to enhance the software architecture of the BASIC interpreter's
Python implementation. You'll modify core components (e.g., `basic_evaluator.py`, `basic_commands.py`,
`basic_parser.py`) to improve modularity, extend functionality, or optimize performance.

In the next section 02, we will take the interpreter apart, but in a more radical way.


### 1. Modular Function Registry for Evaluator

You'll refactor the `Evaluator` class in `basic_evaluator.py` to use a modular function registry, allowing
new functions (e.g., `MAX`, `MIN`) to be added without modifying the core code. This improves the interpreter's
extensibility, a key aspect of its software architecture, by separating function definitions from evaluation logic.

Objectives:
- Learn how the evaluator processes `FunctionExpression` objects.
- Implement a registry pattern to manage functions dynamically.
- Add `MAX` and `MIN` functions to handle variable-length numeric arguments.
- Update the parser to recognize new functions.

Code Changes:

1. *Refactor `basic_evaluator.py`*:
   Create a function registry and move function definitions to a separate dictionary.

   ```python
   # In basic_evaluator.py
   from typing import Any, Callable, Dict, List
   from basic_expressions import Expression, FunctionExpression

   class FunctionRegistry:
       functions: Dict[str, Callable[[List[Any]], Any]] = {
           "sin": lambda x: math.sin(x[0]) if len(x) == 1 else math.sin(0),
           "cos": lambda x: math.cos(x[0]) if len(x) == 1 else math.cos(0),
           "tan": lambda x: math.tan(x[0]) if len(x) == 1 else math.tan(0),
           "atn": lambda x: math.atan(x[0]) if len(x) == 1 else math.atan(0),
           "abs": lambda x: abs(x[0]) if len(x) == 1 else 0,
           "sqr": lambda x: math.sqrt(x[0]) if len(x) == 1 and x[0] >= 0 else 0,
           "log": lambda x: math.log(x[0]) if len(x) == 1 and x[0] > 0 else 0,
           "exp": lambda x: math.exp(x[0]) if len(x) == 1 else 0,
           "int": lambda x: int(x[0]) if len(x) == 1 else 0,
           "rnd": lambda x: random.random() if len(x) == 0 else (random.seed(x[0]), random.random())[1] if len(x) == 1 and isinstance(x[0], (int, float)) else 0,
           "left$": lambda x: x[0][:int(x[1])] if len(x) == 2 and isinstance(x[0], str) else "",
           "right$": lambda x: x[0][-int(x[1]):] if len(x) == 2 and isinstance(x[0], str) else "",
           "mid$": lambda x: x[0][int(x[1])-1:int(x[1])-1+int(x[2])] if len(x) >= 3 and isinstance(x[0], str) else "",
           "len": lambda x: len(x[0]) if len(x) == 1 and isinstance(x[0], str) else 0,
           "str$": lambda x: str(x[0]) if len(x) == 1 else "",
           "val": lambda x: float(x[0]) if len(x) == 1 and isinstance(x[0], str) else 0,
           "chr$": lambda x: chr(int(x[0])) if len(x) == 1 and isinstance(x[0], (int, float)) else "",
           "asc": lambda x: ord(x[0][0]) if len(x) == 1 and isinstance(x[0], str) and x[0] else 0,
           "max": lambda x: max(x) if x and all(isinstance(v, (int, float)) for v in x) else 0,
           "min": lambda x: min(x) if x and all(isinstance(v, (int, float)) for v in x) else 0
       }

       @classmethod
       def register(cls, name: str, func: Callable[[List[Any]], Any]) -> None:
           cls.functions[name.lower()] = func

       @classmethod
       def get(cls, name: str) -> Callable[[List[Any]], Any]:
           return cls.functions.get(name.lower(), lambda x: 0)

   class Evaluator:
       def __init__(self, state: InterpreterState):
           self.state = state

       def evaluate(self, expr: Expression) -> Any:
           # ... (unchanged code for other expression types) ...

       def evaluate_function(self, expr: FunctionExpression) -> Any:
           args = [self.evaluate(arg) for arg in expr.args]
           func = FunctionRegistry.get(expr.name)
           result = func(args)
           print(f"DEBUG: Evaluated function {expr.name} with args {args} to {result}")
           return result
   ```

2. *Update `basic_parser.py`*:
   Add `max` and `min` to the `RESERVED_FUNCTIONS` set.

   ```python
   # In basic_parser.py
   RESERVED_FUNCTIONS = {
       "sin", "cos", "tan", "atn", "abs", "sqr", "log", "exp", "int", "rnd",
       "left$", "right$", "mid$", "len", "str$", "val", "chr$", "asc", "max", "min"
   }
   ```

3. *Test Program*:
   Create a BASIC program to test the new functions.

   ```basic
   10 PRINT "Max and Min Calculator"
   20 INPUT "Enter first number: ", A
   30 INPUT "Enter second number: ", B
   40 INPUT "Enter third number: ", C
   50 PRINT "Maximum: "; MAX(A, B, C)
   60 PRINT "Minimum: "; MIN(A, B, C)
   70 END
   ```


How It Works:
- The `FunctionRegistry` class centralizes function definitions, making it easy to add new ones
  (e.g., `max`, `min`) without changing `Evaluator`.
- `MAX` and `MIN` accept variable-length numeric arguments, using Python's `max` and `min` functions.
- The parser recognizes `max` and `min` as reserved functions, allowing their use in BASIC programs.
- Run the test program with `RUN`, enter numbers (e.g., `5`, `2`, `8`), and expect outputs like
  `Maximum: 8`, `Minimum: 2`.


Challenge:
- Add a `SUM` function to `FunctionRegistry` that computes the sum of all numeric arguments.
  Test it with a BASIC program summing an array's elements.



### 2. Command Decorator for Tracing

You'll enhance the interpreter's architecture by adding a decorator to the `Command` classes in
`basic_commands.py` to enable automatic tracing of command execution. This improves debugging and
observability, a critical aspect of software architecture, without modifying each command's core logic.

Objectives:
- Understand the `Command` class hierarchy and `execute` method.
- Implement a Python decorator to log command execution.
- Integrate the decorator with `CommandFactory` for selective tracing.
- Test tracing with existing commands like `PRINT` and `LET`.

Code Changes:

1. *Add Decorator to `basic_commands.py`*:
   Create a tracing decorator and apply it conditionally.

   ```python
   # In basic_commands.py
   from functools import wraps
   from typing import Any, Callable, Optional

   def trace_command(func: Callable) -> Callable:
       @wraps(func)
       def wrapper(self: Command, args: str) -> None:
           print(f"TRACE: Executing {self.__class__.__name__} with args '{args}'")
           result = func(self, args)
           print(f"TRACE: Completed {self.__class__.__name__}")
           return result
       return wrapper

   class Command(ABC):
       def __init__(self, state: InterpreterState):
           self.state = state
           self.trace_enabled = False

       @abstractmethod
       def execute(self, args: str) -> None:
           pass

       def enable_tracing(self) -> None:
           self.trace_enabled = True

   class ParsedCommand(Command):
       def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
           super().__init__(state)
           self.parser_factory = parser_factory

       def execute(self, args: str) -> None:
           method = self._execute_with_trace if self.trace_enabled else self._execute
           method(args)

       @trace_command
       def _execute_with_trace(self, args: str) -> None:
           self.preprocess(args)
           self.process(args)
           self.postprocess(args)

       def _execute(self, args: str) -> None:
           self.preprocess(args)
           self.process(args)
           self.postprocess(args)

   # Example: Update PrintCommand to support tracing
   class PrintCommand(ParsedCommand):
       def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
           super().__init__(state, parser_factory)
           self.current_pos = 0
           self.output_parts = []

       # ... (rest of PrintCommand unchanged) ...
   ```

2. *Modify `TraceCommand` in `basic_commands.py`*:
   Update `TraceCommand` to enable tracing for all commands.

   ```python
   # In basic_commands.py
   class TraceCommand(ParsedCommand):
       def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
           super().__init__(state, parser_factory)

       def process(self, args: str) -> None:
           if not self.state.code:
               print("No program loaded!")
               return

           start_line = self.parse_start_line(args)
           if start_line not in self.state.code:
               print(f"Error: Line {start_line} does not exist.")
               return

           min_line = min(self.state.code.keys())
           if start_line != min_line:
               print(f"Warning: Starting at line {start_line} may skip initialization code.")

           self.state.reset(True)
           self.state.variables["#"] = start_line

           # Enable tracing for all commands
           for command in self.state.__dict__.values():
               if isinstance(command, Command):
                   command.enable_tracing()

           engine = InterpreterEngine()
           engine.state = self.state
           engine.run(trace=True)
           self.state.reset(True)

       # ... (parse_start_line unchanged) ...
   ```

3. *Test Program*:
   Create a BASIC program to test tracing.

   ```basic
   10 PRINT "Testing Tracing"
   20 LET X = 42
   30 PRINT X
   40 TRACE
   50 PRINT "Tracing Enabled"
   60 LET Y = X + 1
   70 PRINT Y
   80 END
   ```

How It Works:
- The `trace_command` decorator logs entry and exit for commands when `trace_enabled` is `True`.
- `ParsedCommand` dynamically selects `_execute_with_trace` or `_execute` based on `trace_enabled`.
- `TraceCommand` enables tracing for all commands before running the program.
- Run the test program with `RUN`. Before line 40, commands execute normally. After `TRACE`, you'll see outputs like `TRACE: Executing PrintCommand with args '"Tracing Enabled"'` for each command.

Challenge:
- Extend the decorator to log the state of variables modified by each command (e.g., `self.state.variables` changes in `LetCommand`).



### 3. Plugin System for Custom Commands

You'll add a plugin system to `CommandFactory` in `basic_commands.py`, allowing custom commands to be
registered dynamically from external modules. This enhances the interpreter's extensibility, a core
architectural principle, by enabling you to add commands without modifying the core codebase.

Objectives:
- Understand `CommandFactory`'s role in mapping command names to classes.
- Implement a plugin registry for dynamic command loading.
- Create a sample `LOG` command to log messages to a file.
- Test the plugin system with a BASIC program.

Code Changes:

1. *Update `CommandFactory` in `basic_commands.py`*:
   Add a plugin registry and method to register custom commands.

   ```python
   # In basic_commands.py
   class CommandFactory:
       _reserved_functions = {
           "sin", "cos", "tan", "atn", "abs", "sqr", "log", "exp", "int", "rnd",
           "left$", "right$", "mid$", "len", "str$", "val", "chr$", "asc", "max", "min"
       }
       _reserved_keywords = {
           "print", "input", "let", "if", "goto", "gosub", "return", "for", "next",
           "while", "wend", "list", "ren", "del", "run", "end", "stop", "bye", "continue",
           "save", "load", "new", "rem", "to", "step", "then", "else", "using", "dim",
           "trace", "reset", "cls", "help"
       }
       _commands = {
           "dim": DimCommand,
           "print": PrintCommand,
           # ... (other commands unchanged) ...
           "help": HelpCommand
       }
       _custom_commands: Dict[str, type] = {}

       @classmethod
       def set_parser_factory(cls, parser_factory: Callable[[List[Token]], Any]) -> None:
           cls._parser_factory = parser_factory

       @classmethod
       def register_custom_command(cls, name: str, command_class: type) -> None:
           if name.lower() in cls._reserved_keywords or name.lower() in cls._reserved_functions:
               raise ValueError(f"Cannot register '{name}' as it is a reserved keyword or function")
           cls._custom_commands[name.lower()] = command_class
           cls._reserved_keywords.add(name.lower())

       @classmethod
       def create_command(cls, name: str, state: InterpreterState) -> Optional[Command]:
           name = name.lower()
           command_class = cls._commands.get(name) or cls._custom_commands.get(name)
           if command_class:
               if issubclass(command_class, ParsedCommand):
                   return command_class(state, cls._parser_factory)
               return command_class(state)
           return None

       # ... (is_reserved_function, is_reserved_keyword, is_reserved unchanged) ...
   ```

2. *Create a Plugin Module (`basic_plugins.py`)*:
   Define a `LogCommand` to write messages to a file.

   ```python
   # In new file basic_plugins.py
   from basic_commands import Command, InterpreterState

   class LogCommand(Command):
       def __init__(self, state: InterpreterState):
           super().__init__(state)

       def execute(self, args: str) -> None:
           try:
               with open("basic_log.txt", "a") as f:
                   f.write(f"{args}\n")
               print(f"Logged: {args}")
           except Exception as e:
               print(f"Error logging message: {e}")

   # Register the command
   from basic_commands import CommandFactory
   CommandFactory.register_custom_command("log", LogCommand)
   ```

3. *Update `basic_interpreter.py`*:
   Import the plugin module to load custom commands.

   ```python
   # In basic_interpreter.py
   import sys
   import readline
   from typing import Any, Optional
   from basic_tokenizer import Tokenizer
   from basic_evaluator import Evaluator
   from basic_commands import CommandFactory, InterpreterEngine
   from basic_utils import create_parser
   import basic_plugins  # Import plugins to register custom commands

   # ... (rest of the file unchanged) ...
   ```

4. *Test Program*:
   Create a BASIC program to test the `LOG` command.

   ```basic
   10 PRINT "Testing Log Command"
   20 LOG "Program started"
   30 LET X = 42
   40 LOG "Set X to 42"
   50 PRINT X
   60 LOG "Program ended"
   70 END
   ```

How It Works:
- `CommandFactory` now supports a `_custom_commands` dictionary for plugin commands.
- `LogCommand` writes its argument to `basic_log.txt` and prints a confirmation.
- Importing `basic_plugins` registers `LOG` with `CommandFactory`.
- Run the test program with `RUN`. It logs messages to `basic_log.txt` (e.g., `Program started`, `Set X to 42`, `Program ended`) and prints confirmations.

Challenge:
- Create a plugin for a `STATS` command that tracks and prints the number of commands
  executed during a program run. Store the count in `InterpreterState` and display it with `STATS`.


### Architectural Insights
- *Modularity*: The interpreter's separation of concerns (tokenizer, parser, evaluator, commands) makes extensions like these feasible.
- *Extensibility*: The registry (Project 1) and plugin system (Project 3) demonstrate how to add features without altering core logic.
- *Observability*: The tracing decorator (Project 2) enhances debugging, a key architectural concern for maintainability.
- *State Management*: All projects interact with `InterpreterState`, highlighting its role as the central data store.

These projects help you explore the interpreter's software architecture while adding practical features.

