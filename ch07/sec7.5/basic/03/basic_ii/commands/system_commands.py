"""
System commands for BASIC.
Implements RUN, LIST, SAVE, LOAD, NEW, END, STOP, CONTINUE, CLS, HELP.
"""
import os
import sys
from typing import Optional
from ..commands.base import Command, ParsedCommand
from ..core.state import InterpreterState
from ..core.exceptions import ExecutionError


class RunCommand(Command):
    """
    RUN command - execute the program from the beginning.
    
    Syntax: RUN
    or: RUN line_number (start from specific line)
    
    Note: This command needs access to the interpreter to call its run() method.
    It will be set by the interpreter when the command is created.
    """
    
    def __init__(self, state, debug=False):
        super().__init__(state, debug)
        self.interpreter = None  # Will be set by interpreter

    def execute(self, args: str) -> None:
        """Process RUN statement."""
        # Reset state but preserve code
        self.state.reset(preserve_code=True)
        
        # Determine starting line
        start_line = None
        if args.strip():
            try:
                start_line = int(args.strip())
                if start_line not in self.state.code:
                    raise ExecutionError(f"Line {start_line} does not exist")
            except ValueError:
                raise ExecutionError("RUN requires a valid line number")
        
        if not self.state.code:
            raise ExecutionError("No program in memory")
        
        # If we have interpreter reference, call its run method
        if self.interpreter:
            self._log(f"RUN from line {start_line if start_line else min(self.state.code.keys())}")
            self.interpreter.run(start_line=start_line)
        else:
            # Fallback: set the line and let calling code handle it
            if start_line is None:
                start_line = min(self.state.code.keys())
            self.state.set_current_line(start_line)
            self._log(f"RUN from line {start_line} (fallback mode)")


class ListCommand(ParsedCommand):
    """
    LIST command - display program lines.
    
    Syntax: LIST
    or: LIST start
    or: LIST start-end
    """

    def process(self, args: str) -> None:
        """Process LIST statement."""
        if not self.state.code:
            print("No program in memory")
            return
        
        # Parse range if specified
        start_line = None
        end_line = None
        
        if args.strip():
            if '-' in args:
                # Range specified
                parts = args.split('-', 1)
                try:
                    if parts[0].strip():
                        start_line = int(parts[0].strip())
                    if parts[1].strip():
                        end_line = int(parts[1].strip())
                except ValueError:
                    raise ExecutionError("LIST requires valid line numbers")
            else:
                # Single line
                try:
                    start_line = int(args.strip())
                    end_line = start_line
                except ValueError:
                    raise ExecutionError("LIST requires a valid line number")
        
        # Display lines
        for line_num in sorted(self.state.code.keys()):
            if start_line is not None and line_num < start_line:
                continue
            if end_line is not None and line_num > end_line:
                break
            
            print(f"{line_num} {self.state.code[line_num]}")


class RenumberCommand(ParsedCommand):
    """
    REN (RENUMBER) command - renumber program lines.
    
    Syntax: REN
    or: REN start, increment
    
    Default: start=10, increment=10
    """

    def process(self, args: str) -> None:
        """Process REN statement."""
        # Parse arguments
        start = 10
        increment = 10
        
        if args.strip():
            parts = [p.strip() for p in args.split(',')]
            try:
                if len(parts) >= 1 and parts[0]:
                    start = int(parts[0])
                if len(parts) >= 2 and parts[1]:
                    increment = int(parts[1])
            except ValueError:
                raise ExecutionError("REN requires valid numbers")
        
        if start < 1 or increment < 1:
            raise ExecutionError("REN requires positive numbers")
        
        # Create mapping of old to new line numbers
        old_lines = sorted(self.state.code.keys())
        mapping = {}
        new_line = start
        
        for old_line in old_lines:
            mapping[old_line] = new_line
            new_line += increment
        
        # Renumber code
        new_code = {}
        for old_line, content in self.state.code.items():
            new_code[mapping[old_line]] = self._update_references(content, mapping)
        
        self.state.code = new_code
        print(f"Program renumbered starting at {start}, increment {increment}")
        self._log(f"Renumbered {len(old_lines)} lines")

    def _update_references(self, line: str, mapping: dict) -> str:
        """Update GOTO, GOSUB, THEN line number references."""
        # This is a simplified implementation
        # A full implementation would need proper parsing
        import re
        
        # Find GOTO/GOSUB/THEN followed by numbers
        patterns = [
            (r'\bGOTO\s+(\d+)', 'GOTO '),
            (r'\bGOSUB\s+(\d+)', 'GOSUB '),
            (r'\bTHEN\s+(\d+)', 'THEN '),
        ]
        
        result = line
        for pattern, prefix in patterns:
            def replacer(match):
                old_num = int(match.group(1))
                new_num = mapping.get(old_num, old_num)
                return prefix + str(new_num)
            
            result = re.sub(pattern, replacer, result, flags=re.IGNORECASE)
        
        return result


class DeleteCommand(ParsedCommand):
    """
    DEL (DELETE) command - delete program lines.
    
    Syntax: DEL line
    or: DEL start-end
    """

    def process(self, args: str) -> None:
        """Process DEL statement."""
        if not args.strip():
            raise ExecutionError("DEL requires a line number or range")
        
        # Parse range
        if '-' in args:
            parts = args.split('-', 1)
            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except ValueError:
                raise ExecutionError("DEL requires valid line numbers")
            
            # Delete range
            deleted = 0
            for line_num in list(self.state.code.keys()):
                if start <= line_num <= end:
                    del self.state.code[line_num]
                    deleted += 1
            
            print(f"Deleted {deleted} line(s)")
        else:
            # Single line
            try:
                line_num = int(args.strip())
            except ValueError:
                raise ExecutionError("DEL requires a valid line number")
            
            if line_num in self.state.code:
                del self.state.code[line_num]
                print(f"Deleted line {line_num}")
            else:
                print(f"Line {line_num} not found")


class SaveCommand(ParsedCommand):
    """
    SAVE command - save program to file.
    
    Syntax: SAVE "filename"
    or: SAVE filename
    """

    def process(self, args: str) -> None:
        """Process SAVE statement."""
        if not args.strip():
            raise ExecutionError("SAVE requires a filename")
        
        # Remove quotes if present
        filename = args.strip().strip('"').strip("'")
        
        if not filename:
            raise ExecutionError("SAVE requires a filename")
        
        try:
            with open(filename, 'w') as f:
                for line_num in sorted(self.state.code.keys()):
                    f.write(f"{line_num} {self.state.code[line_num]}\n")
            
            print(f"Program saved to {filename}")
            self._log(f"Saved {len(self.state.code)} lines to {filename}")
        except IOError as e:
            raise ExecutionError(f"Error saving file: {e}")


class LoadCommand(ParsedCommand):
    """
    LOAD command - load program from file.
    
    Syntax: LOAD "filename"
    or: LOAD filename
    """

    def process(self, args: str) -> None:
        """Process LOAD statement."""
        if not args.strip():
            raise ExecutionError("LOAD requires a filename")
        
        # Remove quotes if present
        filename = args.strip().strip('"').strip("'")
        
        if not filename:
            raise ExecutionError("LOAD requires a filename")
        
        try:
            # Clear existing program
            self.state.reset(preserve_code=False)
            
            # Load file
            with open(filename, 'r') as f:
                lines_loaded = 0
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse line number and content
                    parts = line.split(None, 1)
                    if parts and parts[0].isdigit():
                        line_num = int(parts[0])
                        content = parts[1] if len(parts) > 1 else ""
                        self.state.code[line_num] = content
                        lines_loaded += 1
            
            print(f"Program loaded from {filename}")
            self._log(f"Loaded {lines_loaded} lines from {filename}")
        except FileNotFoundError:
            raise ExecutionError(f"File not found: {filename}")
        except IOError as e:
            raise ExecutionError(f"Error loading file: {e}")


class NewCommand(Command):
    """
    NEW command - clear program and variables.
    
    Syntax: NEW
    """

    def execute(self, args: str) -> None:
        """Process NEW statement."""
        self.state.reset(preserve_code=False)
        print("Program cleared")
        self._log("NEW - all state reset")


class ResetCommand(Command):
    """
    RESET command - clear variables but keep program.
    
    Syntax: RESET
    """

    def execute(self, args: str) -> None:
        """Process RESET statement."""
        self.state.reset(preserve_code=True)
        print("Variables cleared")
        self._log("RESET - variables cleared, program preserved")


class EndCommand(Command):
    """
    END command - stop program execution.
    
    Syntax: END
    """

    def execute(self, args: str) -> None:
        """Process END statement."""
        self.state.set_current_line(0)  # Stop execution
        self._log("END - program terminated")


class StopCommand(Command):
    """
    STOP command - pause program execution.
    
    Syntax: STOP
    """

    def execute(self, args: str) -> None:
        """Process STOP statement."""
        current_line = self.state.get_current_line()
        print(f"STOP at line {current_line}")
        self.state.paused = True
        self._log(f"STOP - paused at line {current_line}")


class ContinueCommand(Command):
    """
    CONTINUE command - resume paused program.
    
    Syntax: CONTINUE
    or: CONT
    """

    def execute(self, args: str) -> None:
        """Process CONTINUE statement."""
        if not self.state.paused:
            print("Program not paused")
            return
        
        self.state.paused = False
        print("Continuing..")
        self._log("CONTINUE - resuming execution")


class ByeCommand(Command):
    """
    BYE command - exit interpreter.
    
    Syntax: BYE
    """

    def execute(self, args: str) -> None:
        """Process BYE statement."""
        print("Bye Bye!")
        self._log("BYE - exiting interpreter")
        sys.exit(0)


class ClsCommand(Command):
    """
    CLS command - clear screen.
    
    Syntax: CLS
    """

    def execute(self, args: str) -> None:
        """Process CLS statement."""
        # Clear screen (works on most terminals)
        os.system('cls' if os.name == 'nt' else 'clear')
        self._log("CLS - screen cleared")


class TraceCommand(Command):
    """
    TRACE command - toggle trace mode.
    
    Syntax: TRACE ON
    or: TRACE OFF
    
    Trace mode shows each line before execution.
    """

    def execute(self, args: str) -> None:
        """Process TRACE statement."""
        # This would need to be implemented in the interpreter
        # For now, just acknowledge the command
        arg = args.strip().upper()
        
        if arg == "ON":
            print("Trace mode ON")
            self._log("TRACE ON")
        elif arg == "OFF":
            print("Trace mode OFF")
            self._log("TRACE OFF")
        else:
            print("Usage: TRACE ON or TRACE OFF")


class HelpCommand(Command):
    """
    HELP command - display help information.
    
    Syntax: HELP
    or: HELP command_name
    """

    def execute(self, args: str) -> None:
        """Process HELP statement."""
        if args.strip():
            # Help for specific command
            self._show_command_help(args.strip().upper())
        else:
            # General help
            self._show_general_help()

    def _show_general_help(self) -> None:
        """Show general help."""
        print("""
BASIC Interpreter Help
=====================

Program Control:
  RUN [line]           - Run program from start or specified line
  LIST [start-end]     - List program lines
  NEW                  - Clear program and variables
  RESET                - Clear variables, keep program
  END                  - Stop program execution
  STOP                 - Pause program execution
  CONTINUE/CONT        - Resume paused program
  BYE                  - Exit interpreter

File Operations:
  SAVE "filename"      - Save program to file
  LOAD "filename"      - Load program from file

Editing:
  DEL line[-line]      - Delete line(s)
  REN [start,inc]      - Renumber lines

Data:
  LET var = expr       - Assign value to variable
  DIM array(size)      - Declare array
  INPUT var            - Read input from user
  PRINT expr           - Display output

Control Flow:
  IF cond THEN stmt    - Conditional execution
  GOTO line            - Jump to line number
  GOSUB line           - Call subroutine
  RETURN               - Return from subroutine
  FOR var=start TO end - Start loop
  NEXT [var]           - End loop
  WHILE cond           - Start while loop
  WEND                 - End while loop

Functions:
  Math: SIN, COS, TAN, ATN, ABS, SQR, LOG, EXP, INT, RND
  String: LEFT$, RIGHT$, MID$, LEN, STR$, VAL, CHR$, ASC

Other:
  REM comment          - Comment (ignored)
  CLS                  - Clear screen
  TRACE ON/OFF         - Toggle trace mode
  HELP [command]       - Show help

Type HELP <command> for specific help.
""")

    def _show_command_help(self, command: str) -> None:
        """Show help for a specific command."""
        help_text = {
            "PRINT": """
PRINT - Display output
Syntax: PRINT expr1; expr2, expr3
  ; (semicolon) - no space between items
  , (comma) - tab to next column
  Trailing ; suppresses newline
Example: PRINT "X="; X
""",
            "INPUT": """
INPUT - Read user input
Syntax: INPUT "prompt"; var1, var2
Example: INPUT "Enter age"; AGE
""",
            "LET": """
LET - Assign value (LET is optional)
Syntax: [LET] var = expression
Example: LET X = 10
         Y = X * 2
""",
            "DIM": """
DIM - Declare array
Syntax: DIM array(size) or DIM array(rows, cols)
Arrays use 1-based indexing
Example: DIM A(10)      ' 1D array, indices 1-10
         DIM B(5,5)     ' 2D array, 5x5
""",
            "IF": """
IF - Conditional execution
Syntax: IF condition THEN statement [ELSE statement]
        IF condition THEN line_number
Example: IF X > 10 THEN PRINT "Big"
         IF X = 0 THEN 100 ELSE 200
""",
            "FOR": """
FOR/NEXT - Loop structure
Syntax: FOR var = start TO end [STEP increment]
        ... loop body ...
        NEXT [var]
Example: FOR I = 1 TO 10
           PRINT I
         NEXT I
""",
            "WHILE": """
WHILE/WEND - While loop
Syntax: WHILE condition
        ... loop body ...
        WEND
Example: WHILE X < 100
           X = X * 2
         WEND
""",
        }
        
        if command in help_text:
            print(help_text[command])
        else:
            print(f"No specific help available for {command}")
            print("Type HELP for list of commands")
