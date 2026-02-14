"""
Control flow commands for BASIC.
Implements IF, GOTO, GOSUB, RETURN, FOR, NEXT, WHILE, WEND.
"""
from typing import Optional
from ..commands.base import ParsedCommand, Command
from ..core.state import InterpreterState
from ..core.exceptions import ExecutionError, ControlFlowError
from ..utils.helpers import split_on_delimiter


class IfCommand(ParsedCommand):
    """
    IF command - conditional execution.
    
    Syntax: IF condition THEN statement
    or: IF condition THEN statement ELSE statement
    or: IF condition THEN line_number
    or: IF condition GOTO line_number
    """
    
    def __init__(self, state, debug=False):
        super().__init__(state, debug)
        self.interpreter = None  # Will be set by interpreter

    def process(self, args: str) -> None:
        """Process IF statement."""
        args_upper = args.upper()
        
        # Find THEN keyword
        then_pos = args_upper.find(" THEN ")
        if then_pos == -1:
            # Try without spaces (e.g., "IF X=5THEN...")
            then_pos = args_upper.find("THEN")
            if then_pos == -1:
                raise ExecutionError("IF requires THEN keyword")
        
        # Extract condition
        condition_str = args[:then_pos].strip()
        remainder = args[then_pos:].strip()
        
        # Remove THEN keyword
        if remainder.upper().startswith("THEN "):
            remainder = remainder[5:].strip()
        elif remainder.upper().startswith("THEN"):
            remainder = remainder[4:].strip()
        
        # Evaluate condition
        try:
            condition_value = self.parse_expression(condition_str)
            # In BASIC, non-zero is true
            condition_is_true = (condition_value != 0)
        except Exception as e:
            raise ExecutionError(f"Error evaluating condition '{condition_str}': {e}")
        
        # Find ELSE clause if present
        else_pos = self._find_else(remainder)
        
        if else_pos != -1:
            then_part = remainder[:else_pos].strip()
            else_part = remainder[else_pos + 4:].strip()  # Skip "ELSE"
        else:
            then_part = remainder.strip()
            else_part = None
        
        # Execute appropriate branch
        if condition_is_true:
            self._execute_branch(then_part)
        elif else_part:
            self._execute_branch(else_part)

    def _find_else(self, text: str) -> int:
        """Find ELSE keyword position, respecting strings."""
        in_string = False
        quote_char = None
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # Handle quotes
            if char in ('"', "'"):
                if not in_string:
                    in_string = True
                    quote_char = char
                elif char == quote_char:
                    in_string = False
                    quote_char = None
            
            # Check for ELSE outside strings
            elif not in_string and i + 4 <= len(text):
                if text[i:i+4].upper() == "ELSE":
                    # Make sure it's a word boundary
                    if (i == 0 or not text[i-1].isalnum()) and \
                       (i+4 >= len(text) or not text[i+4].isalnum()):
                        return i
            
            i += 1
        
        return -1

    def _execute_branch(self, branch: str) -> None:
        """Execute a branch (THEN or ELSE part)."""
        if not branch:
            return
        
        # Check if it's a line number (GOTO)
        if branch.isdigit():
            line_num = int(branch)
            self.state.set_current_line(line_num)
        else:
            # It's a statement - execute it via the interpreter
            if self.interpreter:
                self.interpreter.execute_line(branch)
            else:
                # Fallback: try to execute as a simple statement
                self._log(f"Executing branch: {branch}")
                # This is a simplified fallback - ideally should use interpreter


class GotoCommand(ParsedCommand):
    """
    GOTO command - unconditional jump to line number.
    
    Syntax: GOTO line_number
    """

    def process(self, args: str) -> None:
        """Process GOTO statement."""
        if not args.strip():
            raise ExecutionError("GOTO requires a line number")
        
        try:
            line_num = int(self.parse_expression(args.strip()))
        except Exception as e:
            raise ExecutionError(f"Invalid line number in GOTO: {e}")
        
        if line_num not in self.state.code:
            raise ExecutionError(f"Line {line_num} does not exist")
        
        self.state.set_current_line(line_num)
        self._log(f"GOTO {line_num}")


class GosubCommand(ParsedCommand):
    """
    GOSUB command - call subroutine at line number.
    
    Syntax: GOSUB line_number
    
    Pushes current line on stack for RETURN.
    """

    def process(self, args: str) -> None:
        """Process GOSUB statement."""
        if not args.strip():
            raise ExecutionError("GOSUB requires a line number")
        
        try:
            line_num = int(self.parse_expression(args.strip()))
        except Exception as e:
            raise ExecutionError(f"Invalid line number in GOSUB: {e}")
        
        if line_num not in self.state.code:
            raise ExecutionError(f"Line {line_num} does not exist")
        
        # Push current line onto stack
        current_line = self.state.get_current_line()
        self.state.stack.append(current_line)
        
        # Jump to subroutine
        self.state.set_current_line(line_num)
        self._log(f"GOSUB {line_num} (return to {current_line})")


class ReturnCommand(Command):
    """
    RETURN command - return from subroutine.
    
    Syntax: RETURN
    
    Pops line from stack and continues execution.
    """

    def execute(self, args: str) -> None:
        """Process RETURN statement."""
        if not self.state.stack:
            raise ControlFlowError("RETURN without GOSUB")
        
        # Pop return address from stack
        return_line = self.state.stack.pop()
        
        # Get next line after the GOSUB
        next_line = self.state.get_next_line(return_line)
        if next_line is None:
            next_line = 0  # End of program
        
        self.state.set_current_line(next_line)
        self._log(f"RETURN to line {next_line}")


class ForCommand(ParsedCommand):
    """
    FOR command - start of FOR/NEXT loop.
    
    Syntax: FOR variable = start TO end
    or: FOR variable = start TO end STEP increment
    
    Default STEP is 1.
    """

    def process(self, args: str) -> None:
        """Process FOR statement."""
        # Parse: variable = start TO end [STEP increment]
        if '=' not in args:
            raise ExecutionError("FOR requires assignment (variable = start)")
        
        args_upper = args.upper()
        
        # Find TO keyword
        to_pos = args_upper.find(" TO ")
        if to_pos == -1:
            raise ExecutionError("FOR requires TO keyword")
        
        # Extract variable and start value
        assignment = args[:to_pos].strip()
        var_name, start_expr = assignment.split('=', 1)
        var_name = var_name.strip()
        start_expr = start_expr.strip()
        
        # Find STEP keyword if present
        remainder = args[to_pos + 4:].strip()  # Skip " TO "
        step_pos = remainder.upper().find(" STEP ")
        
        if step_pos != -1:
            end_expr = remainder[:step_pos].strip()
            step_expr = remainder[step_pos + 6:].strip()  # Skip " STEP "
        else:
            end_expr = remainder.strip()
            step_expr = "1"
        
        # Check if this loop is already active (re-entering from NEXT)
        current_line = self.state.get_current_line()
        
        if var_name in self.state.loops and self.state.loops[var_name]['line'] == current_line:
            # Loop is active - this is a continuation from NEXT
            # Just check if we should continue or exit
            loop_info = self.state.loops[var_name]
            current_value = self.state.get_variable(var_name)
            
            if loop_info['step'] > 0 and current_value > loop_info['end']:
                # Exit loop
                del self.state.loops[var_name]
                self._skip_to_next(var_name)
                return
            elif loop_info['step'] < 0 and current_value < loop_info['end']:
                # Exit loop
                del self.state.loops[var_name]
                self._skip_to_next(var_name)
                return
            # Otherwise continue into loop body (fall through)
            return
        
        # First time entering this FOR loop - initialize it
        # Evaluate expressions
        try:
            start_value = self.parse_expression(start_expr)
            end_value = self.parse_expression(end_expr)
            step_value = self.parse_expression(step_expr)
        except Exception as e:
            raise ExecutionError(f"Error evaluating FOR parameters: {e}")
        
        # Initialize loop variable
        self.state.set_variable(var_name, start_value)
        
        # Store loop information
        self.state.loops[var_name] = {
            'start': start_value,
            'end': end_value,
            'step': step_value,
            'line': current_line
        }
        
        self._log(f"FOR {var_name} = {start_value} TO {end_value} STEP {step_value}")
        
        # Check if loop should execute at all
        current_value = self.state.get_variable(var_name)
        if step_value > 0 and current_value > end_value:
            # Skip to after NEXT
            self._skip_to_next(var_name)
        elif step_value < 0 and current_value < end_value:
            # Skip to after NEXT
            self._skip_to_next(var_name)

    def _skip_to_next(self, var_name: str) -> None:
        """Skip to line after matching NEXT."""
        current_line = self.state.get_current_line()
        nest_level = 1
        
        for line_num in sorted(self.state.code.keys()):
            if line_num <= current_line:
                continue
            
            line_content = self.state.code[line_num].strip().upper()
            
            # Check for nested FOR
            if line_content.startswith("FOR "):
                nest_level += 1
            # Check for NEXT
            elif line_content.startswith("NEXT"):
                nest_level -= 1
                if nest_level == 0:
                    # Found matching NEXT
                    next_line = self.state.get_next_line(line_num)
                    self.state.set_current_line(next_line if next_line else 0)
                    return
        
        # No matching NEXT found
        raise ControlFlowError(f"FOR without matching NEXT for variable {var_name}")


class NextCommand(ParsedCommand):
    """
    NEXT command - end of FOR/NEXT loop.
    
    Syntax: NEXT variable
    or: NEXT (uses most recent FOR loop)
    """

    def process(self, args: str) -> None:
        """Process NEXT statement."""
        var_name = args.strip() if args.strip() else None
        
        # If no variable specified, use most recent loop
        if not var_name:
            if not self.state.loops:
                raise ControlFlowError("NEXT without FOR")
            # Get most recently started loop
            var_name = list(self.state.loops.keys())[-1]
        
        # Check if loop exists
        if var_name not in self.state.loops:
            raise ControlFlowError(f"NEXT {var_name} without matching FOR")
        
        loop_info = self.state.loops[var_name]
        
        # Increment loop variable
        current_value = self.state.get_variable(var_name)
        new_value = current_value + loop_info['step']
        self.state.set_variable(var_name, new_value)
        
        # Check if loop should continue
        step = loop_info['step']
        end = loop_info['end']
        
        should_continue = False
        if step > 0:
            should_continue = (new_value <= end)
        else:
            should_continue = (new_value >= end)
        
        if should_continue:
            # Jump back to FOR line
            self.state.set_current_line(loop_info['line'])
            self._log(f"NEXT {var_name} = {new_value}, continue loop")
        else:
            # Loop finished, remove from loops
            del self.state.loops[var_name]
            self._log(f"NEXT {var_name} = {new_value}, exit loop")


class WhileCommand(ParsedCommand):
    """
    WHILE command - start of WHILE/WEND loop.
    
    Syntax: WHILE condition
    
    Executes loop body while condition is true (non-zero).
    """

    def process(self, args: str) -> None:
        """Process WHILE statement."""
        if not args.strip():
            raise ExecutionError("WHILE requires a condition")
        
        # Evaluate condition
        try:
            condition_value = self.parse_expression(args.strip())
            condition_is_true = (condition_value != 0)
        except Exception as e:
            raise ExecutionError(f"Error evaluating WHILE condition: {e}")
        
        current_line = self.state.get_current_line()
        
        # Store WHILE information (line and condition)
        while_key = f"WHILE_{current_line}"
        self.state.whiles[while_key] = (current_line, args.strip())
        
        self._log(f"WHILE at line {current_line}, condition = {condition_value}")
        
        # If condition is false, skip to after WEND
        if not condition_is_true:
            self._skip_to_wend()

    def _skip_to_wend(self) -> None:
        """Skip to line after matching WEND."""
        current_line = self.state.get_current_line()
        nest_level = 1
        
        for line_num in sorted(self.state.code.keys()):
            if line_num <= current_line:
                continue
            
            line_content = self.state.code[line_num].strip().upper()
            
            # Check for nested WHILE
            if line_content.startswith("WHILE "):
                nest_level += 1
            # Check for WEND
            elif line_content.startswith("WEND"):
                nest_level -= 1
                if nest_level == 0:
                    # Found matching WEND
                    next_line = self.state.get_next_line(line_num)
                    self.state.set_current_line(next_line if next_line else 0)
                    # Remove WHILE from state
                    while_key = f"WHILE_{current_line}"
                    if while_key in self.state.whiles:
                        del self.state.whiles[while_key]
                    return
        
        # No matching WEND found
        raise ControlFlowError("WHILE without matching WEND")


class WendCommand(ParsedCommand):
    """
    WEND command - end of WHILE/WEND loop.
    
    Syntax: WEND
    
    Returns to matching WHILE and re-evaluates condition.
    """

    def process(self, args: str) -> None:
        """Process WEND statement."""
        # Find matching WHILE
        current_line = self.state.get_current_line()
        
        # Search backwards for matching WHILE
        while_line = None
        while_condition = None
        nest_level = 0
        
        for line_num in sorted(self.state.code.keys(), reverse=True):
            if line_num >= current_line:
                continue
            
            line_content = self.state.code[line_num].strip().upper()
            
            # Check for WEND (going backwards)
            if line_content.startswith("WEND"):
                nest_level += 1
            # Check for WHILE
            elif line_content.startswith("WHILE "):
                if nest_level == 0:
                    # Found matching WHILE
                    while_line = line_num
                    # Extract condition
                    while_condition = self.state.code[line_num][6:].strip()
                    break
                else:
                    nest_level -= 1
        
        if while_line is None:
            raise ControlFlowError("WEND without matching WHILE")
        
        # Evaluate condition
        try:
            condition_value = self.parse_expression(while_condition)
            condition_is_true = (condition_value != 0)
        except Exception as e:
            raise ControlFlowError(f"Error evaluating WHILE condition: {e}")
        
        if condition_is_true:
            # Continue loop - jump back to WHILE
            self.state.set_current_line(while_line)
            self._log(f"WEND: condition true, jump to line {while_line}")
        else:
            # Exit loop
            while_key = f"WHILE_{while_line}"
            if while_key in self.state.whiles:
                del self.state.whiles[while_key]
            self._log("WEND: condition false, exit loop")