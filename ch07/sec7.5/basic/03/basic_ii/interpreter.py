"""
Main BASIC interpreter engine.
Coordinates program execution and command dispatch.
"""
import sys
from typing import Optional, Dict, Type
from .core.state import InterpreterState
from .core.exceptions import BasicError, ExecutionError
from .commands.base import Command
from .utils.helpers import split_statements, parse_line_number


class Interpreter:
    """Main BASIC interpreter engine."""

    def __init__(self, debug: bool = False):
        self.state = InterpreterState()
        self.debug = debug
        self.command_registry: Dict[str, Type[Command]] = {}
        self._register_commands()

    def _register_commands(self) -> None:
        """Register all available commands."""
        # Import all command modules
        from .commands.io_commands import PrintCommand, InputCommand, RemCommand
        from .commands.data_commands import LetCommand, DimCommand
        from .commands.control_flow import (
            IfCommand, GotoCommand, GosubCommand, ReturnCommand,
            ForCommand, NextCommand, WhileCommand, WendCommand
        )
        from .commands.system_commands import (
            RunCommand, ListCommand, RenumberCommand, DeleteCommand,
            SaveCommand, LoadCommand, NewCommand, ResetCommand,
            EndCommand, StopCommand, ContinueCommand, ByeCommand,
            ClsCommand, TraceCommand, HelpCommand
        )
        from .commands.function_commands import DefCommand
        
        # I/O commands
        self.register_command("print", PrintCommand)
        self.register_command("input", InputCommand)
        self.register_command("rem", RemCommand)
        
        # Data commands
        self.register_command("let", LetCommand)
        self.register_command("dim", DimCommand)
        self.register_command("def", DefCommand)
        
        # Control flow commands
        self.register_command("if", IfCommand)
        self.register_command("goto", GotoCommand)
        self.register_command("gosub", GosubCommand)
        self.register_command("return", ReturnCommand)
        self.register_command("for", ForCommand)
        self.register_command("next", NextCommand)
        self.register_command("while", WhileCommand)
        self.register_command("wend", WendCommand)
        
        # System commands
        self.register_command("run", RunCommand)
        self.register_command("list", ListCommand)
        self.register_command("ren", RenumberCommand)
        self.register_command("renumber", RenumberCommand)
        self.register_command("del", DeleteCommand)
        self.register_command("delete", DeleteCommand)
        self.register_command("save", SaveCommand)
        self.register_command("load", LoadCommand)
        self.register_command("new", NewCommand)
        self.register_command("reset", ResetCommand)
        self.register_command("end", EndCommand)
        self.register_command("stop", StopCommand)
        self.register_command("continue", ContinueCommand)
        self.register_command("cont", ContinueCommand)
        self.register_command("bye", ByeCommand)
        self.register_command("cls", ClsCommand)
        self.register_command("trace", TraceCommand)
        self.register_command("help", HelpCommand)

    def register_command(self, name: str, command_class: Type[Command]) -> None:
        """Register a command handler."""
        self.command_registry[name.lower()] = command_class

    def load_program(self, filename: str) -> None:
        """Load a BASIC program from a file."""
        try:
            with open(filename, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            line_number, content = parse_line_number(line)
                            self.state.code[line_number] = content
                        except ValueError as e:
                            print(f"Warning: Skipping invalid line: {line} ({e})")
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
            raise
        except Exception as e:
            print(f"Error loading program: {e}")
            raise

    def save_program(self, filename: str) -> None:
        """Save the current program to a file."""
        try:
            with open(filename, 'w') as file:
                for line_num in sorted(self.state.code.keys()):
                    file.write(f"{line_num} {self.state.code[line_num]}\n")
        except Exception as e:
            print(f"Error saving program: {e}")
            raise

    def execute_line(self, line: str) -> None:
        """Execute a single line of BASIC code."""
        line = line.strip()
        if not line:
            return

        # Split into multiple statements if necessary
        statements = split_statements(line)

        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue

            self._execute_statement(statement)

    def _execute_statement(self, statement: str) -> None:
        """Execute a single statement."""
        # Parse statement into command and arguments
        parts = statement.split(None, 1)
        if not parts:
            return

        cmd_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Try to find and execute command
        command_class = self.command_registry.get(cmd_name)
        
        if command_class:
            try:
                command = command_class(self.state, self.debug)
                
                # Inject interpreter reference for commands that need it (like RUN)
                if hasattr(command, 'interpreter'):
                    command.interpreter = self
                
                command.execute(args)
            except BasicError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Unexpected error in {cmd_name}: {e}")
                if self.debug:
                    raise
        # Check if it's an assignment (LET can be implicit)
        elif "=" in statement and not statement.upper().startswith("IF"):
            let_command_class = self.command_registry.get("let")
            if let_command_class:
                try:
                    command = let_command_class(self.state, self.debug)
                    command.execute(statement)
                except BasicError as e:
                    print(f"Error: {e}")
        else:
            print(f"Syntax error: Unknown command '{cmd_name}'")

    def run(self, start_line: Optional[int] = None, trace: bool = False) -> None:
        """
        Run the loaded BASIC program.
        
        Args:
            start_line: Optional starting line number
            trace: Enable trace mode (show each line before execution)
        """
        if not self.state.code:
            print("No program loaded!")
            return

        # Set starting line
        if start_line is None:
            start_line = min(self.state.code.keys())
        
        self.state.set_current_line(start_line)
        self.state.paused = False

        try:
            while True:
                current_line = self.state.get_current_line()
                
                # Check if we've reached the end
                if current_line == 0:
                    break

                # Check if line exists
                if current_line not in self.state.code:
                    print(f"Error: Line {current_line} does not exist")
                    break

                # Trace mode
                if trace:
                    print(f"[{current_line}] {self.state.code[current_line]}")

                # Execute the line
                line_content = self.state.code[current_line]
                previous_line = current_line
                
                self.execute_line(line_content)

                # Check if paused
                if self.state.paused:
                    break

                # Auto-advance to next line if not changed by command
                if self.state.get_current_line() == previous_line:
                    next_line = self.state.get_next_line(current_line)
                    self.state.set_current_line(next_line if next_line else 0)

        except KeyboardInterrupt:
            print("\n\nProgram interrupted")
            self.state.paused = True

    def reset(self, preserve_code: bool = True) -> None:
        """Reset the interpreter state."""
        self.state.reset(preserve_code=preserve_code)

    def list_program(self, start: Optional[int] = None, end: Optional[int] = None) -> None:
        """List the program or a range of lines."""
        if not self.state.code:
            print("No program in memory")
            return

        lines = sorted(self.state.code.keys())
        
        for line_num in lines:
            # Filter by range if specified
            if start is not None and line_num < start:
                continue
            if end is not None and line_num > end:
                break
            
            print(f"{line_num} {self.state.code[line_num]}")
