import sys
import re
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple, Callable
from basic_tokenizer import Tokenizer, Token
from basic_evaluator import Evaluator
from basic_utils import create_parser
from basic_shared import InterpreterState, ParserError
from basic_expressions import ArrayExpression, Expression

class InterpreterError(Exception):
    pass

class ExecutionError(InterpreterError):
    pass

class Command(ABC):
    def __init__(self, state: InterpreterState):
        self.state = state
    
    @abstractmethod
    def execute(self, args: str) -> None:
        pass

class ParsedCommand(Command):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state)
        self.parser_factory = parser_factory

    def execute(self, args: str) -> None:
        self.preprocess(args)
        self.process(args)
        self.postprocess(args)
    
    def preprocess(self, args: str) -> None:
        pass
    
    @abstractmethod
    def process(self, args: str) -> None:
        pass
    
    def postprocess(self, args: str) -> None:
        pass
    
    def parse_expression(self, expr: str) -> Any:
        try:
            tokenizer = Tokenizer(expr)
            tokens = tokenizer.tokenize()
            if tokenizer.errors:
                raise ParserError(f"Tokenization errors: {tokenizer.errors}")
            parser = self.parser_factory(tokens)
            expression = parser.parse()
            evaluator = Evaluator(self.state)
            return evaluator.evaluate(expression)
        except Exception as e:
            raise ParserError(f"Error parsing expression '{expr}': {e}")

class DimCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        try:
            array_decls = self.split_declarations(args)
            for decl in array_decls:
                decl = decl.strip()
                if not decl:
                    continue
                self._process_declaration(decl)
        except Exception as e:
            print(f"Error in DIM statement '{args}': {e}")

    def _process_declaration(self, decl: str) -> None:
        try:
            self._validate_syntax(decl)
            name, dims_str = self._parse_declaration(decl)
            self._validate_name(name)
            dim_values = self._parse_dimensions(dims_str)
            self._create_array(name, dim_values)
        except Exception as e:
            print(f"Error in DIM declaration '{decl}': {e}")

    def _validate_syntax(self, decl: str) -> None:
        if not decl.endswith(")"):
            raise ParserError(f"Invalid DIM syntax: Missing closing parenthesis in '{decl}'")
        if "(" not in decl:
            raise ParserError(f"Invalid DIM syntax: Missing opening parenthesis in '{decl}'")

    def _parse_declaration(self, decl: str) -> Tuple[str, str]:
        parts = decl.split("(", 1)
        if len(parts) != 2:
            raise ParserError(f"Invalid DIM syntax: Incorrect format in '{decl}'")
        
        name = parts[0].strip()
        dims_str = parts[1].rstrip(")").strip()
        
        if not name:
            raise ParserError(f"Invalid DIM syntax: Array name missing in '{decl}'")
        if not dims_str:
            raise ParserError(f"Invalid DIM syntax: No dimensions specified in '{decl}'")
        
        return name, dims_str

    def _validate_name(self, name: str) -> None:
        if CommandFactory.is_reserved(name):
            raise ParserError(f"Cannot use reserved word '{name}' as array name")
        if name in self.state.arrays or name in self.state.variables:
            raise ParserError(f"Variable or array '{name}' already declared")

    def _parse_dimensions(self, dims_str: str) -> List[int]:
        dims = [d.strip() for d in dims_str.split(",") if d.strip()]
        if len(dims) not in (1, 2):
            raise ParserError(f"Array must have 1 or 2 dimensions, got {len(dims)}")
        
        dim_values = []
        for d in dims:
            value = int(self.parse_expression(d))
            if value < 1:
                raise ParserError(f"Array dimensions must be positive: {value}")
            dim_values.append(value)
        
        return dim_values

    def _create_array(self, name: str, dim_values: List[int]) -> None:
        adjusted_dims = tuple(d + 1 for d in dim_values)
        self.state.arrays[name] = {}
        self.state.array_dims[name] = adjusted_dims

    def split_declarations(self, args: str) -> List[str]:
        declarations = []
        current = []
        paren_count = 0
        in_string = False
        quote_char = None
        i = 0

        while i < len(args):
            char = args[i]
            
            if char in ('"', "'") and (not in_string or quote_char == char):
                if in_string:
                    in_string = False
                    quote_char = None
                else:
                    in_string = True
                    quote_char = char
                current.append(char)
            
            elif char == '(' and not in_string:
                paren_count += 1
                current.append(char)
            
            elif char == ')' and not in_string:
                paren_count -= 1
                current.append(char)
            
            elif char == ',' and paren_count == 0 and not in_string:
                declaration = ''.join(current).strip()
                if declaration:
                    declarations.append(declaration)
                current = []
            
            else:
                current.append(char)
            
            i += 1
        
        declaration = ''.join(current).strip()
        if declaration:
            declarations.append(declaration)
        
        return declarations


class PrintCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)
        self.current_pos = 0
        self.output_parts = []

    def process(self, args: str) -> None:
        if not args.strip():
            print()
            return

        self.current_pos = 0
        self.output_parts = []

        # Split on semicolons and commas, preserving trailing semicolon
        expressions = self.split_expressions(args)
        trailing_semicolon = args.rstrip().endswith(";") and not args.rstrip().endswith(" ")

        for expr in expressions:
            expr = expr.strip()
            if not expr:
                continue
            try:
                self._process_expression(expr)
            except Exception as e:
                print(f"Error processing expression '{expr}': {e}")
                self.output_parts.append("0")  # Default output on error
                self.current_pos += 1

        self._finalize_output(trailing_semicolon)

    def _process_expression(self, expr: str) -> None:
        if expr == ",":  # Handle comma for spacing
            self._handle_comma_spacing()
        elif expr.upper().startswith("TAB("):
            self._handle_tab(expr)
        elif expr.upper().startswith("USING"):
            self._handle_using(expr)
        else:
            self._handle_regular_expression(expr)

    def _handle_comma_spacing(self) -> None:
        # Add 8 spaces or align to next 8-space boundary
        spaces_needed = 8 - (self.current_pos % 8) if self.current_pos % 8 != 0 else 8
        self.output_parts.append(" " * spaces_needed)
        self.current_pos += spaces_needed

    def _handle_tab(self, expr: str) -> None:
        try:
            tab_arg = expr[4:-1].strip()
            if not tab_arg:
                raise ValueError("Empty TAB argument")
            tab_pos = int(self.parse_expression(tab_arg))
            if tab_pos < 0:
                raise ValueError("TAB position must be non-negative")
            if tab_pos > self.current_pos:
                spaces_needed = tab_pos - self.current_pos
                self.output_parts.append(" " * spaces_needed)
                self.current_pos = tab_pos
        except Exception as e:
            print(f"Error evaluating TAB argument '{tab_arg}': {e}")

    def _handle_using(self, expr: str) -> None:
        try:
            parts = expr.split(";", 1)
            format_str = self.parse_expression(parts[0][5:].strip())
            if not isinstance(format_str, str):
                raise ValueError("USING expects a string format")
            value_expr = parts[1].strip() if len(parts) > 1 else ""
            if not value_expr:
                raise ValueError("Expected expression after USING")
            result = self.parse_expression(value_expr)
            if not isinstance(result, (int, float)):
                raise ValueError("USING format requires a numeric value")
            formatted = self.format_using(result, format_str)
            self.output_parts.append(formatted)
            self.current_pos += len(formatted)
        except Exception as e:
            print(f"Error in USING clause: {e}")

    def _handle_regular_expression(self, expr: str) -> None:
        try:
            result = self.parse_expression(expr)
            if isinstance(result, str):
                formatted = result
            elif isinstance(result, float):
                formatted = f"{result:.6f}".rstrip("0").rstrip(".") if result != int(result) else str(int(result))
            else:
                formatted = str(result)
            print(f"DEBUG: Evaluated '{expr}' to {formatted}")
            self.output_parts.append(formatted)
            self.current_pos += len(formatted)
        except Exception as e:
            print(f"Error evaluating expression '{expr}': {e}")
            self.output_parts.append("0")
            self.current_pos += 1

    def _finalize_output(self, trailing_semicolon: bool) -> None:
        print("".join(self.output_parts), end="" if trailing_semicolon else "\n", flush=True)

    def split_expressions(self, args: str) -> List[str]:
        expressions = []
        current = []
        paren_count = 0
        in_string = False
        quote_char = None
        i = 0

        while i < len(args):
            char = args[i]
            
            if char in ('"', "'") and (not in_string or quote_char == char):
                if in_string:
                    in_string = False
                    quote_char = None
                else:
                    in_string = True
                    quote_char = char
                current.append(char)
            
            elif char == '(' and not in_string:
                paren_count += 1
                current.append(char)
            
            elif char == ')' and not in_string:
                paren_count -= 1
                current.append(char)
            
            elif char in (',', ';') and paren_count == 0 and not in_string:
                expression = ''.join(current).strip()
                if expression:
                    expressions.append(expression)
                if char == ',':
                    expressions.append(",")  # Comma for spacing
                current = []
            
            else:
                current.append(char)
            
            i += 1
        
        expression = ''.join(current).strip()
        if expression:
            expressions.append(expression)
        
        return expressions

    def format_using(self, value: float, format_str: str) -> str:
        if format_str == "#.##":
            return f"{value:.2f}"
        elif format_str == "#.###":
            return f"{value:.3f}"
        elif format_str == "#,###.##":
            return f"{value:,.2f}"
        else:
            raise ValueError(f"Unsupported format string: {format_str}")

class InputCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        parts = args.split(";", 1)
        prompt = ""
        var_name = args.strip()
        
        if len(parts) > 1:
            prompt_text = parts[0].strip()
            var_name = parts[1].strip()
            
            try:
                prompt = str(self.parse_expression(prompt_text)) + "? "
            except Exception as e:
                print(f"Error in INPUT prompt: {e}")
                prompt = "? "
        
        input_value = input(prompt).strip()
        
        try:
            if var_name.endswith(")"):
                let_statement = f"{var_name} = {input_value}"
                let_command = LetCommand(self.state, self.parser_factory)
                let_command.execute(let_statement)
            else:
                if var_name.endswith("$"):
                    self.state.variables[var_name] = input_value
                else:
                    try:
                        if '.' in input_value:
                            self.state.variables[var_name] = float(input_value)
                        else:
                            self.state.variables[var_name] = int(input_value)
                    except ValueError:
                        self.state.variables[var_name] = input_value
        except Exception as e:
            print(f"Error processing INPUT: {e}")

class LetCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        try:
            var_part, expr = args.split("=", 1)
            var_part = var_part.strip()
            expr = expr.strip()
            
            if var_part.endswith(")"):
                self._process_array_assignment(var_part, expr)
            else:
                self._process_variable_assignment(var_part, expr)
        except Exception as e:
            print(f"Error in LET statement '{args}': {e}")
            if not var_part.endswith(")"):
                self.state.variables[var_part] = 0

    def _process_array_assignment(self, var_part: str, expr: str) -> None:
        try:
            array_expr = self._parse_array_expression(var_part)
            
            name = array_expr.name
            self._validate_array_name(name)
            
            indices = self._evaluate_indices(array_expr.indices)
            
            self._validate_indices(name, indices)
            
            self._assign_array_value(name, indices, expr)
        except Exception as e:
            raise ParserError(f"Error in array assignment '{var_part}': {e}")

    def _parse_array_expression(self, var_part: str) -> ArrayExpression:
        try:
            tokenizer = Tokenizer(var_part)
            tokens = tokenizer.tokenize()
            if tokenizer.errors:
                raise ParserError(f"Tokenization errors: {tokenizer.errors}")
            parser = self.parser_factory(tokens)
            expr = parser.parse()
            if not isinstance(expr, ArrayExpression):
                raise ParserError(f"Expected array expression, got {type(expr).__name__}")
            return expr
        except Exception as e:
            raise ParserError(f"Failed to parse array expression '{var_part}': {e}")

    def _validate_array_name(self, name: str) -> None:
        if CommandFactory.is_reserved(name):
            raise ParserError(f"Cannot assign to reserved word '{name}'")
        if name not in self.state.arrays:
            raise ParserError(f"Array '{name}' not declared")

    def _evaluate_indices(self, indices: List[Expression]) -> List[int]:
        try:
            evaluator = Evaluator(self.state)
            return [int(evaluator.evaluate(idx)) for idx in indices]
        except Exception as e:
            raise ParserError(f"Failed to evaluate indices: {e}")

    def _validate_indices(self, name: str, indices: List[int]) -> None:
        dims = self.state.array_dims.get(name, ())
        if len(indices) != len(dims):
            raise ParserError(f"Array '{name}' expects {len(dims)} indices, got {len(indices)}")
        for i, idx in enumerate(indices):
            if not (1 <= idx <= dims[i] - 1):
                raise ParserError(f"Index {idx} out of bounds for array '{name}' dimension {i}")

    def _assign_array_value(self, name: str, indices: List[int], expr: str) -> None:
        try:
            value = self.parse_expression(expr)
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            adjusted_indices = [idx - 1 for idx in indices]
            index_tuple = tuple(adjusted_indices)
            print(f"DEBUG: Assigning {value} to array {name} at indices {indices} -> adjusted {adjusted_indices}")
            self.state.arrays[name][index_tuple] = value
        except Exception as e:
            raise ParserError(f"Failed to assign value to array '{name}': {e}")

    def _process_variable_assignment(self, var: str, expr: str) -> None:
        try:
            if CommandFactory.is_reserved(var):
                raise ParserError(f"Cannot assign to reserved word '{var}'")
            value = self.parse_expression(expr)
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            self.state.variables[var] = value
        except Exception as e:
            raise ParserError(f"Error in variable assignment '{var}': {e}")

class IfCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        try:
            parts = re.split(r"THEN", args, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) != 2:
                raise ValueError("Invalid IF syntax: Missing 'THEN'")

            condition = parts[0].strip()
            rest = parts[1].strip()
            
            else_part = ""
            if "ELSE" in rest.upper():
                then_else = re.split(r"ELSE", rest, maxsplit=1, flags=re.IGNORECASE)
                then_part = then_else[0].strip()
                else_part = then_else[1].strip()
            else:
                then_part = rest
            
            condition_value = self.parse_expression(condition)
            
            engine = InterpreterEngine()
            if condition_value != 0:
                if then_part.isdigit():
                    self.state.variables["#"] = int(then_part)
                else:
                    engine.execute_line(then_part)
            elif else_part:
                if else_part.isdigit():
                    self.state.variables["#"] = int(else_part)
                else:
                    engine.execute_line(else_part)
        except Exception as e:
            print(f"Error in IF statement: {e}")

class GotoCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        try:
            line_num = int(self.parse_expression(args)) if not args.strip().isdigit() else int(args.strip())
            if line_num in self.state.code:
                self.state.variables["#"] = line_num
            else:
                print(f"Error: Line {line_num} does not exist.")
        except Exception as e:
            print(f"Error in GOTO statement: {e}")

class GosubCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        try:
            line_num = int(self.parse_expression(args)) if not args.strip().isdigit() else int(args.strip())
            if line_num in self.state.code:
                self.state.stack.append(self.state.variables["#"])
                self.state.variables["#"] = line_num
            else:
                print(f"Error: Line {line_num} does not exist.")
        except Exception as e:
            print(f"Error in GOSUB statement: {e}")

class ReturnCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        if self.state.stack:
            self.state.variables["#"] = self.state.stack.pop()
        else:
            print("RETURN without GOSUB")
            self.state.variables["#"] = 0

class ForCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        try:
            var_part, rest = args.split("=", 1)
            var = var_part.strip()
            if not var.isidentifier():
                raise ParserError(f"Invalid loop variable: {var}")
            
            tokenizer = Tokenizer(rest.strip())
            tokens = tokenizer.tokenize()
            if tokenizer.errors:
                raise ParserError(f"Tokenization errors: {tokenizer.errors}")
            
            if not tokens or tokens[0].type != "NUMBER":
                raise ParserError("Expected start value after '='")
            start_value = float(tokens[0].value)
            
            if len(tokens) < 2 or tokens[1].type != "KEYWORD" or tokens[1].value.lower() != "to":
                raise ParserError("Invalid FOR syntax: Missing 'TO'")
            if len(tokens) < 3 or tokens[2].type != "NUMBER":
                raise ParserError("Expected end value after 'TO'")
            end_value = float(tokens[2].value)
            
            step_value = 1
            if len(tokens) > 3:
                if tokens[3].type != "KEYWORD" or tokens[3].value.lower() != "step":
                    raise ParserError("Expected 'STEP' or end of statement")
                if len(tokens) < 5 or tokens[4].type != "NUMBER":
                    raise ParserError("Expected step value after 'STEP'")
                step_value = float(tokens[4].value)
            
            self.state.variables[var] = start_value
            
            if not hasattr(self.state, 'loops') or self.state.loops is None:
                self.state.loops = {}
                
            self.state.loops[var] = {
                "start": start_value,
                "end": end_value,
                "step": step_value,
                "line": self.state.variables["#"],  # line number of the FOR statement
                "active": True                      # flag this loop is currently active
            }

            current_line = self.state.variables["#"]
            next_line = next((n for n in sorted(self.state.code.keys()) if n > current_line), 0)
            self.state.variables["#"] = next_line

        except Exception as e:
            print(f"Error in FOR statement: {e}")
            raise

class NextCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        try:
            var = args.strip() if args.strip() else self._get_last_loop_variable()
            
            if not var:
                raise ParserError("No active loops to NEXT")
                
            if var not in self.state.loops:
                raise ParserError(f"Loop variable '{var}' not found")
                
            loop_info = self.state.loops[var]
            
            if not loop_info.get("active", False):
                raise ParserError(f"Loop for '{var}' is not active")
                
            current_value = self.state.variables[var]
            
            new_value = current_value + loop_info["step"]
            self.state.variables[var] = new_value
            
            continue_loop = False
            if loop_info["step"] > 0:
                continue_loop = new_value <= loop_info["end"]
            else:
                continue_loop = new_value >= loop_info["end"]
                
            if continue_loop:
                self.state.variables["#"] = loop_info["line"]
                next_line = next((n for n in sorted(self.state.code.keys()) if n > loop_info["line"]), 0)
                self.state.variables["#"] = next_line
            else:
                loop_info["active"] = False
                current_line = self.state.variables["#"]
                next_line = next((n for n in sorted(self.state.code.keys()) if n > current_line), 0)
                self.state.variables["#"] = next_line
                
        except Exception as e:
            print(f"Error in NEXT statement: {e}")
            raise
            
    def _get_last_loop_variable(self):
        active_loops = [(var, info) for var, info in self.state.loops.items() if info.get("active", False)]
        if not active_loops:
            return None
            
        return active_loops[-1][0]

class WhileCommand(ParsedCommand):
    _loop_counter = 0
    
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        try:
            if not args.strip():
                raise ParserError("Syntax error in WHILE statement: missing condition")
            
            condition = args.strip()
            
            WhileCommand._loop_counter += 1
            loop_id = f"while_{self.state.variables['#']}_{WhileCommand._loop_counter}"
            
            self.state.whiles[loop_id] = (self.state.variables["#"], condition)
            
            condition_result = self.parse_expression(condition)
            if not condition_result:
                self.skip_to_wend()
            else:
                current_line = self.state.variables["#"]
                next_line = next((n for n in sorted(self.state.code.keys()) if n > current_line), 0)
                self.state.variables["#"] = next_line
        except Exception as e:
            print(f"Syntax error in WHILE statement: {e}")

    def skip_to_wend(self):
        current_line = self.state.variables["#"]
        wend_count = 1
        
        line_numbers = sorted(self.state.code.keys())
        
        start_idx = 0
        for i, line_num in enumerate(line_numbers):
            if line_num > current_line:
                start_idx = i
                break
        
        for i in range(start_idx, len(line_numbers)):
            line_num = line_numbers[i]
            line = self.state.code[line_num].strip().upper()
            
            if line.startswith("WHILE"):
                wend_count += 1
            elif line.startswith("WEND"):
                wend_count -= 1
                if wend_count == 0:
                    next_line = next((n for n in sorted(self.state.code.keys()) if n > line_num), 0)
                    self.state.variables["#"] = next_line
                    return
        
        print("Error: WHILE without matching WEND")
        self.state.variables["#"] = 0  # end of program

class WendCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        loop_id = None
        for id in sorted(self.state.whiles.keys(), reverse=True):
            if id.startswith("while_"):
                loop_id = id
                break

        if loop_id and loop_id in self.state.whiles:
            start_line, condition = self.state.whiles[loop_id]
            if self.parse_expression(condition):
                self.state.variables["#"] = start_line
            else:
                del self.state.whiles[loop_id]
                current_line = self.state.variables["#"]
                next_line = next((n for n in sorted(self.state.code.keys()) if n > current_line), 0)
                self.state.variables["#"] = next_line
        else:
            print("Error: WEND without matching WHILE")
            self.state.variables["#"] = 0

class ListCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        start_line, end_line = self.parse_range(args)
        if not self.state.code:
            print("No program loaded.")
            return

        for line_num in sorted(self.state.code.keys()):
            if start_line <= line_num <= end_line:
                print(f"{line_num} {self.state.code[line_num]}")

    def parse_range(self, args: str) -> Tuple[int, int]:
        default_start = min(self.state.code.keys(), default=1)
        default_end = max(self.state.code.keys(), default=1)

        if not args.strip():
            return default_start, default_end

        try:
            parts = args.strip().split("-")
            parts = [part.strip() for part in parts if part.strip()]
            if len(parts) == 1:
                start = self.evaluate_line(parts[0])
                return start, start
            elif len(parts) == 2:
                start = self.evaluate_line(parts[0]) if parts[0] else default_start
                end = self.evaluate_line(parts[1])
                if start > end:
                    print(f"Warning: Start line {start} is greater than end line {end}. Swapping.")
                    start, end = end, start
                return start, end
            else:
                raise ValueError("Invalid range format")
        except (ValueError, ParserError) as e:
            print(f"Error parsing range: {e}. Listing all lines.")
            return default_start, default_end

    def evaluate_line(self, expr: str) -> int:
        if not expr:
            return min(self.state.code.keys(), default=1)
        return int(self.parse_expression(expr))

class RemCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        pass

class EndCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        self.state.variables["#"] = 0
        self.state.reset(True)

class ByeCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        sys.exit(0)

class ClsCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        import os
        os.system('cls||clear')

class StopCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        print("Program paused.")
        self.state.paused = True
        current_line = self.state.variables["#"]
        next_line = next((n for n in sorted(self.state.code.keys()) if n > current_line), 0)
        self.state.variables["#"] = next_line

class SaveCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        try:
            filename = self.parse_filename(args)
            if not filename:
                raise ValueError("Filename must be a non-empty quoted string")
            
            if not filename.endswith(".bas"):
                filename += ".bas"
            
            with open(filename, "w") as file:
                for line_number in sorted(self.state.code.keys()):
                    code = self.state.code[line_number]
                    file.write(f"{line_number} {code}\n")
            
            print(f"Program saved to '{filename}'")
        except Exception as e:
            print(f"Error saving program: {e}")

    def parse_filename(self, args: str) -> str:
        args = args.strip()
        if (args.startswith('"') and args.endswith('"')) or (args.startswith("'") and args.endswith("'")):
            return args[1:-1].strip()
        return ""

class LoadCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        try:
            filename = self.parse_filename(args)
            if not filename:
                raise ValueError("Filename must be a non-empty quoted string")
            
            if not filename.endswith(".bas"):
                filename += ".bas"
            
            self.state.code.clear()
            
            engine = InterpreterEngine()
            with open(filename, "r") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            line_number, line_code = engine.parse_line(line)
                            if line_number <= 0:
                                raise ValueError(f"Invalid line number: {line_number}")
                            self.state.code[line_number] = line_code
                        except Exception as e:
                            print(f"Warning: Skipping invalid line '{line}': {e}")
            
            if not self.state.code:
                print(f"Warning: No valid program lines loaded from '{filename}'")
            else:
                print(f"Program loaded from '{filename}'")
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
        except Exception as e:
            print(f"Error loading program: {e}")

    def parse_filename(self, args: str) -> str:
        args = args.strip()
        if (args.startswith('"') and args.endswith('"')) or (args.startswith("'") and args.endswith("'")):
            return args[1:-1].strip()
        return ""

class ContinueCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        if self.state.paused:
            if self.state.variables["#"] == 0 or self.state.variables["#"] not in self.state.code:
                print("No more lines to continue.")
                self.state.paused = False
                return
            print("Resuming program...")
            self.state.paused = False
            InterpreterEngine().run()
        else:
            print("Program is not paused.")
            self.state.paused = False

class RenumberCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        if not self.state.code:
            print("No program to renumber.")
            return

        start_line, increment = self.parse_args(args)
        old_lines = sorted(self.state.code.keys())
        new_code = {}
        line_mapping = {}

        for i, old_line in enumerate(old_lines):
            new_line = start_line + i * increment
            line_mapping[old_line] = new_line
            new_code[new_line] = self.state.code[old_line]

        for new_line in new_code:
            new_code[new_line] = self.update_line_references(new_code[new_line], line_mapping)

        self.state.code.clear()
        self.state.code.update(new_code)
        print("Program renumbered successfully.")

    def parse_args(self, args: str) -> Tuple[int, int]:
        default_start = 10
        default_increment = 10

        if not args.strip():
            return default_start, default_increment

        try:
            parts = [part.strip() for part in args.split(",")]
            if len(parts) == 1:
                start = int(parts[0])
                increment = default_increment
            elif len(parts) == 2:
                start = int(parts[0])
                increment = int(parts[1])
            else:
                raise ValueError("Invalid number of arguments")

            if start <= 0 or increment <= 0:
                raise ValueError("Start line and increment must be positive")
            return start, increment
        except ValueError as e:
            print(f"Error parsing RENUMBER arguments: {e}. Using defaults ({default_start}, {default_increment})")
            return default_start, default_increment

    def update_line_references(self, line: str, line_mapping: dict) -> str:
        parts = line.split(None, 1)
        if not parts:
            return line

        original_cmd = parts[0]  # Keep the original command with its case
        cmd_lower = original_cmd.lower()  # Lowercase version for comparison
        args = parts[1] if len(parts) > 1 else ""

        if cmd_lower in ["goto", "gosub"]:
            try:
                old_line = int(args.strip())
                if old_line in line_mapping:
                    return f"{original_cmd} {line_mapping[old_line]}"
                else:
                    print(f"Warning: Referenced line {old_line} in {original_cmd} does not exist.")
                    return line
            except ValueError:
                return line

        elif cmd_lower == "if":
            modified_line = line
            
            # Handle THEN clause
            match = re.search(r'\bTHEN\b\s*(\d+)', args, re.IGNORECASE)
            if match:
                old_line = int(match.group(1))
                if old_line in line_mapping:
                    modified_line = modified_line.replace(match.group(1), str(line_mapping[old_line]))
                else:
                    print(f"Warning: Referenced line {old_line} in IF...THEN does not exist.")
            
            # Handle ELSE clause
            match = re.search(r'\bELSE\b\s*(\d+)', args, re.IGNORECASE)
            if match:
                old_line = int(match.group(1))
                if old_line in line_mapping:
                    modified_line = modified_line.replace(match.group(1), str(line_mapping[old_line]))
                else:
                    print(f"Warning: Referenced line {old_line} in IF...ELSE does not exist.")
            
            return modified_line

        return line

class DeleteCommand(ParsedCommand):
    def __init__(self, state: InterpreterState, parser_factory: Callable[[List[Token]], Any] = create_parser):
        super().__init__(state, parser_factory)

    def process(self, args: str) -> None:
        start_line, end_line = self.parse_range(args)
        deleted = 0
        for line_num in list(self.state.code.keys()):
            if start_line <= line_num <= end_line:
                del self.state.code[line_num]
                deleted += 1
        print(f"Deleted {deleted} line(s).")

    def parse_range(self, args: str) -> tuple[int, int]:
        if not args.strip():
            return 1, max(self.state.code.keys()) if self.state.code else 1
        
        parts = args.split("-", 1)
        start = self.evaluate_line(parts[0].strip()) if parts[0].strip() else 1
        end = self.evaluate_line(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else start
        return start, end

    def evaluate_line(self, expr: str) -> int:
        try:
            value = self.parse_expression(expr.strip())
            return int(value)
        except Exception as e:
            print(f"Error evaluating line number '{expr}': {e}")
            return int(expr) if expr.strip().isdigit() else 1

class RunCommand(ParsedCommand):
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

        engine = InterpreterEngine()
        engine.state = self.state
        engine.run()
        self.state.reset(True)

    def parse_start_line(self, args: str) -> int:
        if not args.strip():
            return min(self.state.code.keys()) if self.state.code else 1
        try:
            tokenizer = Tokenizer(args.strip())
            tokens = tokenizer.tokenize()
            if tokens and tokens[0].type == "NUMBER":
                parser = create_parser(tokens)
                expr = parser.parse_number()
                evaluator = Evaluator(self.state)
                return int(evaluator.evaluate(expr))
            return int(self.parse_expression(args))
        except Exception as e:
            print(f"Error parsing start line: {e}")
            return min(self.state.code.keys()) if self.state.code else 1

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

        engine = InterpreterEngine()
        engine.state = self.state
        engine.run(trace=True)
        self.state.reset(True)

    def parse_start_line(self, args: str) -> int:
        if not args.strip():
            return min(self.state.code.keys()) if self.state.code else 1
        try:
            tokenizer = Tokenizer(args.strip())
            tokens = tokenizer.tokenize()
            if tokens and tokens[0].type == "NUMBER":
                parser = create_parser(tokens)
                expr = parser.parse_number()
                evaluator = Evaluator(self.state)
                return int(evaluator.evaluate(expr))
            return int(self.parse_expression(args))
        except Exception as e:
            print(f"Error parsing start line: {e}")
            return min(self.state.code.keys()) if self.state.code else 1

class ResetCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        self.state.reset(True)
        print("Interpreter state reset.")

class NewCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)

    def execute(self, args: str) -> None:
        self.state.reset()
        print("Program cleared.")

class HelpCommand(Command):
    def __init__(self, state: InterpreterState):
        super().__init__(state)
        self.command_help = {
            "dim": "DIM var(size) - Declares an array with specified size (1D or 2D).",
            "print": "PRINT expr[;] - Prints expressions, strings, or numbers; semicolon suppresses newline.",
            "input": "INPUT [prompt;] var - Prompts for input and stores in variable or array.",
            "goto": "GOTO line - Jumps to the specified line number.",
            "if": "IF condition THEN stmt [ELSE stmt] - Executes statement if condition is true.",
            "run": "RUN [line] - Runs the program from the start or specified line.",
            "trace": "TRACE [line] - Runs the program with line-by-line tracing.",
            "let": "LET var = expr - Assigns a value to a variable or array element.",
            "gosub": "GOSUB line - Calls a subroutine at the specified line.",
            "return": "RETURN - Returns from a subroutine.",
            "for": "FOR var = start TO end [STEP step] - Starts a loop with a variable.",
            "next": "NEXT [var] - Ends a FOR loop and increments the loop variable.",
            "list": "LIST [start-end] - Lists program lines, optionally within a range.",
            "ren": "RENUMBER [start, increment] - Renumbers program lines.",
            "del": "DELETE [start-end] - Deletes program lines in the specified range.",
            "while": "WHILE condition - Starts a loop while condition is true.",
            "wend": "WEND - Ends a WHILE loop.",
            "bye": "BYE - Exits the interpreter.",
            "stop": "STOP - Pauses the program execution.",
            "end": "END - Ends the program and resets state.",
            "continue": "CONTINUE - Resumes a paused program.",
            "reset": "RESET - Resets interpreter state, preserving code.",
            "save": "SAVE \"filename\" - Saves the program to a file.",
            "load": "LOAD \"filename\" - Loads a program from a file.",
            "new": "NEW - Clears the program and resets state.",
            "rem": "REM comment - Adds a comment (ignored by interpreter).",
            "cls": "CLS - Clears the screen.",
            "help": "HELP [command] - Displays list of commands or help for a specific command."
        }

    def execute(self, args: str) -> None:
        args = args.strip().lower()
        if args:
            # Display help for a specific command
            if args in self.command_help:
                print(self.command_help[args])
            else:
                print(f"No help available for '{args}'. Type HELP for a list of commands.")
        else:
            # Display all commands
            print("Available BASIC Commands:")
            print("-" * 40)
            for cmd, description in sorted(self.command_help.items()):
                print(f"{cmd.upper():<10} {description}")
            print("-" * 40)
            print("Type HELP command for details on a specific command.")

class CommandFactory:
    _reserved_functions = {
        "sin", "cos", "tan", "atn", "abs", "sqr", "log", "exp", "int", "rnd",
        "left$", "right$", "mid$", "len", "str$", "val", "chr$", "asc"
    }
    _reserved_keywords = {
        "print", "input", "let", "if", "goto", "gosub", "return", "for", "next",
        "while", "wend", "list", "ren", "del", "run", "end", "stop", "bye", "continue",
        "save", "load", "new", "rem", "to", "step", "then", "else", "using", "dim"
    }
    
    _commands = {
        "dim": DimCommand,
        "print": PrintCommand,
        "input": InputCommand,
        "goto": GotoCommand,
        "if": IfCommand,
        "run": RunCommand,
        "trace": TraceCommand,
        "let": LetCommand,
        "gosub": GosubCommand,
        "return": ReturnCommand,
        "for": ForCommand,
        "next": NextCommand,
        "list": ListCommand,
        "ren": RenumberCommand,
        "del": DeleteCommand,
        "while": WhileCommand,
        "wend": WendCommand,
        "bye": ByeCommand,
        "stop": StopCommand,
        "end": EndCommand,
        "continue": ContinueCommand,
        "reset": ResetCommand,
        "save": SaveCommand,
        "load": LoadCommand,
        "new": NewCommand,
        "rem": RemCommand,
        "cls": ClsCommand,
        "help": HelpCommand,
    }
    
    _parser_factory = None

    @classmethod
    def set_parser_factory(cls, parser_factory: Callable[[List[Token]], Any]) -> None:
        cls._parser_factory = parser_factory

    @classmethod
    def create_command(cls, name: str, state: InterpreterState) -> Optional[Command]:
        name = name.lower()
        command_class = cls._commands.get(name)
        if command_class:
            if issubclass(command_class, ParsedCommand):
                return command_class(state, cls._parser_factory)
            return command_class(state)
        return None
    
    @classmethod
    def is_reserved_function(cls, name: str) -> bool:
        return name.lower() in cls._reserved_functions
    
    @classmethod
    def is_reserved_keyword(cls, name: str) -> bool:
        return name.lower() in cls._reserved_keywords
    
    @classmethod
    def is_reserved(cls, name: str) -> bool:
        return cls.is_reserved_function(name) or cls.is_reserved_keyword(name)

def split_statements(line: str) -> List[str]:
    parts = line.strip().split(' ', 1)
    if parts and parts[0].isdigit():
        if len(parts) > 1:
            line = parts[1]
        else:
            line = ""
    
    statements = []
    current = []
    in_string = False
    quote_char = None
    i = 0
    
    while i < len(line):
        char = line[i]
        
        if char in ('"', "'") and (not in_string or quote_char == char):
            if in_string:
                in_string = False
                quote_char = None
            else:
                in_string = True
                quote_char = char
            current.append(char)

        elif char == '\\' and i + 1 < len(line) and line[i + 1] in ('"', "'") and in_string:
            current.append(char)
            current.append(line[i + 1])
            i += 1

        elif char == ':' and not in_string:
            statement = ''.join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
        
        i += 1
    
    statement = ''.join(current).strip()
    if statement:
        statements.append(statement)
    
    return statements


class InterpreterEngine:
    def __init__(self):
        self.state = InterpreterState()
    
    def load_program(self, filename: str) -> None:
        try:
            with open(filename, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        line_number, line_code = self.parse_line(line)
                        self.state.code[line_number] = line_code
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
        except Exception as e:
            print(f"Error loading program: {e}")

    def parse_line(self, line: str) -> Tuple[int, str]:
        try:
            parts = line.split(maxsplit=1)
            if not parts or not parts[0].isdigit():
                raise ValueError("Line must start with a number")
            line_number = int(parts[0])
            code = parts[1] if len(parts) > 1 else ""
            return line_number, code
        except ValueError as e:
            raise ValueError(f"Invalid line format: {e}")
    
    def execute_line(self, line: str) -> None:
        line = line.strip()
        if not line or line.startswith("DEBUG:") or line.startswith("Parsed expression:"):
            return  # Skip debug output
        
        statements = split_statements(line)
        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue
            
            parts = statement.split(None, 1)
            if not parts:
                continue
                
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            # Skip if cmd is a loop variable or expression
            if cmd in self.state.variables or cmd in self.state.loops:
                continue
                
            command = CommandFactory.create_command(cmd, self.state)
            if command:
                command.execute(args)
            elif "=" in statement and not statement.upper().startswith("IF"):
                let_command = CommandFactory.create_command("let", self.state)
                if let_command:
                    let_command.execute(statement)
            else:
                print(f"Syntax error: Unknown command or statement '{statement}'")
    
    def run(self, trace: bool = False) -> None:
        if not self.state.code:
            print("No program loaded!")
            return

        step_mode = trace

        try:
            while self.state.variables["#"] > 0 and not self.state.paused:
                current_line = self.state.variables["#"]
                if current_line not in self.state.code:
                    print(f"Error: Line {current_line} does not exist.")
                    break
                
                if trace:
                    print(f"TRACE: {current_line} {self.state.code[current_line]}")
                
                if step_mode:
                    try:
                        user_input = input("Press Enter to step, 'c' to continue, 'q' to quit: ").strip().lower()
                        if user_input == 'q':
                            print("Program terminated by user.")
                            self.state.variables["#"] = 0
                            break
                        elif user_input == 'c':
                            step_mode = False  # Disable step mode, continue running ~ not working .. share state probl?

                    except EOFError:
                        print("\nExiting due to EOF.")
                        self.state.variables["#"] = 0
                        break
                
                line = self.state.code[current_line]
                self.execute_line(line)
                
                if self.state.paused:
                    break
                
                if self.state.variables["#"] == current_line:
                    next_line = next((n for n in sorted(self.state.code.keys()) if n > current_line), 0)
                    self.state.variables["#"] = next_line

        except KeyboardInterrupt:
            print("\n\nProgram paused by interrupt.")
            self.state.paused = True
            current_line = self.state.variables["#"]
            next_line = next((n for n in sorted(self.state.code.keys()) if n > current_line), 0)
            self.state.variables["#"] = next_line
