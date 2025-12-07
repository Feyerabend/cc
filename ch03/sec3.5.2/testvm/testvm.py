#!/usr/bin/env python3
# Test VM Engine - A comprehensive virtual machine for test execution
# with advanced features, better error handling, and extensible architecture


import time
import re
import json
import traceback
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import threading
from contextlib import contextmanager


class ValueType(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"
    NULL = "null"
    RESULT = "result"


@dataclass
class Value:
    type: ValueType
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        if self.type == ValueType.STRING:
            return f'"{self.data}"'
        elif self.type == ValueType.LIST:
            return f"[{', '.join(str(v) for v in self.data)}]"
        elif self.type == ValueType.DICT:
            return f"{{{', '.join(f'{k}: {v}' for k, v in self.data.items())}}}"
        elif self.type == ValueType.NULL:
            return "null"
        return str(self.data)
    
    def __eq__(self, other):
        if isinstance(other, Value):
            return self.type == other.type and self.data == other.data
        return False
    
    def to_bool(self) -> bool:
        if self.type == ValueType.BOOL:
            return self.data
        elif self.type == ValueType.INT or self.type == ValueType.FLOAT:
            return self.data != 0
        elif self.type == ValueType.STRING:
            return len(self.data) > 0
        elif self.type == ValueType.LIST:
            return len(self.data) > 0
        elif self.type == ValueType.NULL:
            return False
        return True


@dataclass
class Instruction:
    opcode: str
    args: List[str] = field(default_factory=list)
    line_number: int = 0
    source_line: str = ""
    
    def __str__(self):
        return f"{self.opcode} {' '.join(self.args)}"


@dataclass
class TestCase:
    name: str
    program: str
    expected_result: Optional[str] = None
    timeout: float = 10.0
    setup: Optional[str] = None
    teardown: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    name: str
    passed: bool
    failed: bool
    execution_time: float
    logs: List[str]
    error_message: str = ""
    stack_trace: str = ""
    assertions_count: int = 0
    assertions_passed: int = 0


class TestVMError(Exception):
    def __init__(self, message: str, line_number: int = 0, instruction: Optional[Instruction] = None):
        super().__init__(message)
        self.line_number = line_number
        self.instruction = instruction


class AssertionError(TestVMError):
    pass


class TimeoutError(TestVMError):
    pass


class Function(ABC):    
    @abstractmethod
    def __call__(self, *args: Value) -> Value:
        pass
    
    @property
    @abstractmethod
    def arity(self) -> int:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class BuiltinFunction(Function):
    def __init__(self, name: str, func: Callable, arity: int):
        self._name = name
        self._func = func
        self._arity = arity
    
    def __call__(self, *args: Value) -> Value:
        if len(args) != self._arity:
            raise TestVMError(f"Function {self._name} expects {self._arity} arguments, got {len(args)}")
        return self._func(*args)
    
    @property
    def arity(self) -> int:
        return self._arity
    
    @property
    def name(self) -> str:
        return self._name


class EnhancedTestVM:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.reset()
        self._setup_builtin_functions()
        self._execution_timeout = 30.0
        self._stop_execution = False
        
    def reset(self):
        self.stack: List[Value] = []
        self.variables: Dict[str, Value] = {}
        self.labels: Dict[str, int] = {}
        self.logs: List[str] = []
        self.pc = 0  # program counter
        self.failed = False
        self.passed = False
        self.last_assertion_failed = False
        self.fail_message = ""
        self.assertions_count = 0
        self.assertions_passed = 0
        self.execution_start_time = 0
        self.current_instruction: Optional[Instruction] = None
        self._call_stack: List[Tuple[str, int]] = []  # For debugging
        
    def _setup_builtin_functions(self):
        self.functions: Dict[str, Function] = {}
        
        # Math operations
        self._register_function("add", lambda x, y: Value(ValueType.INT, x.data + y.data), 2)
        self._register_function("subtract", lambda x, y: Value(ValueType.INT, x.data - y.data), 2)
        self._register_function("multiply", lambda x, y: Value(ValueType.INT, x.data * y.data), 2)
        self._register_function("divide", lambda x, y: Value(ValueType.FLOAT, x.data / y.data if y.data != 0 else float('inf')), 2)
        self._register_function("modulo", lambda x, y: Value(ValueType.INT, x.data % y.data if y.data != 0 else 0), 2)
        self._register_function("power", lambda x, y: Value(ValueType.INT, x.data ** y.data), 2)
        
        # String operations
        self._register_function("concat", lambda x, y: Value(ValueType.STRING, str(x.data) + str(y.data)), 2)
        self._register_function("length", lambda x: Value(ValueType.INT, len(str(x.data))), 1)
        self._register_function("substring", self._substring, 3)
        self._register_function("uppercase", lambda x: Value(ValueType.STRING, str(x.data).upper()), 1)
        self._register_function("lowercase", lambda x: Value(ValueType.STRING, str(x.data).lower()), 1)
        self._register_function("trim", lambda x: Value(ValueType.STRING, str(x.data).strip()), 1)
        
        # Comparison operations
        self._register_function("equals", lambda x, y: Value(ValueType.BOOL, x.data == y.data), 2)
        self._register_function("not_equals", lambda x, y: Value(ValueType.BOOL, x.data != y.data), 2)
        self._register_function("greater_than", lambda x, y: Value(ValueType.BOOL, x.data > y.data), 2)
        self._register_function("less_than", lambda x, y: Value(ValueType.BOOL, x.data < y.data), 2)
        self._register_function("greater_equal", lambda x, y: Value(ValueType.BOOL, x.data >= y.data), 2)
        self._register_function("less_equal", lambda x, y: Value(ValueType.BOOL, x.data <= y.data), 2)
        
        # Logic operations
        self._register_function("and", lambda x, y: Value(ValueType.BOOL, x.to_bool() and y.to_bool()), 2)
        self._register_function("or", lambda x, y: Value(ValueType.BOOL, x.to_bool() or y.to_bool()), 2)
        self._register_function("not", lambda x: Value(ValueType.BOOL, not x.to_bool()), 1)
        
        # List operations
        self._register_function("list_create", lambda: Value(ValueType.LIST, []), 0)
        self._register_function("list_append", self._list_append, 2)
        self._register_function("list_get", self._list_get, 2)
        self._register_function("list_size", lambda x: Value(ValueType.INT, len(x.data) if x.type == ValueType.LIST else 0), 1)
        
        # Type operations
        self._register_function("to_string", lambda x: Value(ValueType.STRING, str(x.data)), 1)
        self._register_function("to_int", self._to_int, 1)
        self._register_function("to_float", self._to_float, 1)
        self._register_function("typeof", lambda x: Value(ValueType.STRING, x.type.value), 1)
        
    def _register_function(self, name: str, func: Callable, arity: int):
        self.functions[name] = BuiltinFunction(name, func, arity)
    
    def _substring(self, string_val: Value, start_val: Value, length_val: Value) -> Value:
        s = str(string_val.data)
        start = start_val.data
        length = length_val.data
        return Value(ValueType.STRING, s[start:start+length])
    
    def _list_append(self, list_val: Value, item_val: Value) -> Value:
        if list_val.type != ValueType.LIST:
            raise TestVMError(f"Cannot append to non-list type: {list_val.type}")
        new_list = list_val.data.copy()
        new_list.append(item_val.data)
        return Value(ValueType.LIST, new_list)
    
    def _list_get(self, list_val: Value, index_val: Value) -> Value:
        if list_val.type != ValueType.LIST:
            raise TestVMError(f"Cannot index non-list type: {list_val.type}")
        if index_val.type != ValueType.INT:
            raise TestVMError(f"List index must be integer, got: {index_val.type}")
        
        try:
            item = list_val.data[index_val.data]
            # Infer type of the item
            if isinstance(item, int):
                return Value(ValueType.INT, item)
            elif isinstance(item, float):
                return Value(ValueType.FLOAT, item)
            elif isinstance(item, bool):
                return Value(ValueType.BOOL, item)
            elif isinstance(item, str):
                return Value(ValueType.STRING, item)
            elif isinstance(item, list):
                return Value(ValueType.LIST, item)
            else:
                return Value(ValueType.STRING, str(item))
        except IndexError:
            raise TestVMError(f"List index out of range: {index_val.data}")
    
    def _to_int(self, val: Value) -> Value:
        try:
            if val.type == ValueType.INT:
                return val
            elif val.type == ValueType.FLOAT:
                return Value(ValueType.INT, int(val.data))
            elif val.type == ValueType.STRING:
                return Value(ValueType.INT, int(val.data))
            elif val.type == ValueType.BOOL:
                return Value(ValueType.INT, 1 if val.data else 0)
            else:
                raise ValueError()
        except ValueError:
            raise TestVMError(f"Cannot convert {val.type} to int: {val.data}")
    
    def _to_float(self, val: Value) -> Value:
        try:
            if val.type == ValueType.FLOAT:
                return val
            elif val.type == ValueType.INT:
                return Value(ValueType.FLOAT, float(val.data))
            elif val.type == ValueType.STRING:
                return Value(ValueType.FLOAT, float(val.data))
            else:
                raise ValueError()
        except ValueError:
            raise TestVMError(f"Cannot convert {val.type} to float: {val.data}")
    
    def register_custom_function(self, name: str, func: Function):
        self.functions[name] = func
        
    def push(self, value: Value):
        self.stack.append(value)
        if self.debug:
            self.log(f"STACK PUSH: {value}")
        
    def pop(self) -> Value:
        if not self.stack:
            raise TestVMError("Stack underflow", 
                            self.current_instruction.line_number if self.current_instruction else 0,
                            self.current_instruction)
        value = self.stack.pop()
        if self.debug:
            self.log(f"STACK POP: {value}")
        return value
        
    def peek(self) -> Value:
        if not self.stack:
            raise TestVMError("Stack is empty", 
                            self.current_instruction.line_number if self.current_instruction else 0,
                            self.current_instruction)
        return self.stack[-1]
        
    def get_variable(self, name: str) -> Value:
        if name not in self.variables:
            raise TestVMError(f"Variable '{name}' not found", 
                            self.current_instruction.line_number if self.current_instruction else 0,
                            self.current_instruction)
        return self.variables[name]
        
    def set_variable(self, name: str, value: Value):
        self.variables[name] = value
        if self.debug:
            self.log(f"SET VAR {name} = {value}")
        
    def log(self, message: str):
        timestamp = time.time() - self.execution_start_time
        log_entry = f"[{timestamp:.3f}s] {message}"
        self.logs.append(log_entry)
        if self.debug:
            print(f"LOG: {log_entry}")
    
    def parse_value(self, value_str: str) -> Value:
        # Handle quoted strings
        if value_str.startswith('"') and value_str.endswith('"'):
            return Value(ValueType.STRING, value_str[1:-1])
        
        # Handle special values
        if value_str.lower() == "null":
            return Value(ValueType.NULL, None)
        elif value_str.lower() in ["true", "false"]:
            return Value(ValueType.BOOL, value_str.lower() == "true")
        
        # Try parsing as number
        try:
            if '.' in value_str:
                return Value(ValueType.FLOAT, float(value_str))
            else:
                return Value(ValueType.INT, int(value_str))
        except ValueError:
            pass
        
        # Handle lists (simple format: [1,2,3])
        if value_str.startswith('[') and value_str.endswith(']'):
            content = value_str[1:-1].strip()
            if not content:
                return Value(ValueType.LIST, [])
            items = [item.strip() for item in content.split(',')]
            parsed_items = []
            for item in items:
                parsed_val = self.parse_value(item)
                parsed_items.append(parsed_val.data)
            return Value(ValueType.LIST, parsed_items)
        
        # Default to string
        return Value(ValueType.STRING, value_str)
        
    def execute_instruction(self, instruction: Instruction) -> bool:
        self.current_instruction = instruction
        opcode = instruction.opcode
        args = instruction.args
        
        try:
            if self.debug:
                self.log(f"EXEC: {instruction}")
            
            if opcode == "LOAD":
                # LOAD <value> - Enhanced to auto-detect type
                value = self.parse_value(args[0])
                self.push(value)
                
            elif opcode == "LOAD_VAR":
                # LOAD_VAR <name>
                value = self.get_variable(args[0])
                self.push(value)
                
            elif opcode == "STORE_VAR":
                # STORE_VAR <name>
                value = self.pop()
                self.set_variable(args[0], value)
                
            elif opcode == "DUP":
                # DUP - Duplicate top of stack
                value = self.peek()
                self.push(value)
                
            elif opcode == "SWAP":
                # SWAP - Swap top two stack items
                if len(self.stack) < 2:
                    raise TestVMError("SWAP requires at least 2 items on stack")
                a = self.pop()
                b = self.pop()
                self.push(a)
                self.push(b)
                
            elif opcode == "CLEAR_STACK":
                # CLEAR_STACK
                self.stack.clear()
                
            elif opcode == "CLEAR_VARS":
                # CLEAR_VARS
                self.variables.clear()
                
            elif opcode == "CLEAR_ALL":
                # CLEAR_ALL
                self.stack.clear()
                self.variables.clear()
                
            elif opcode == "CALL":
                # CALL <func_name> - Enhanced function calling
                func_name = args[0]
                if func_name not in self.functions:
                    raise TestVMError(f"Function '{func_name}' not found")
                    
                func = self.functions[func_name]
                
                # Pop arguments from stack
                func_args = []
                for _ in range(func.arity):
                    if not self.stack:
                        raise TestVMError(f"Not enough arguments for function '{func_name}' (expected {func.arity})")
                    func_args.append(self.pop())
                func_args.reverse()  # Arguments were pushed in order
                
                # Call function and handle result
                result = func(*func_args)
                self.set_variable("result", result)
                self.push(result)
                
            elif opcode.startswith("ASSERT"):
                # Enhanced assertion handling
                self._handle_assertion(opcode, args)
                
            elif opcode == "JUMP":
                # JUMP <label>
                label = args[0]
                if label in self.labels:
                    self.pc = self.labels[label] - 1
                else:
                    raise TestVMError(f"Label '{label}' not found")
                    
            elif opcode.startswith("JUMP_IF"):
                # Conditional jumps
                self._handle_conditional_jump(opcode, args)
                
            elif opcode == "LABEL":
                # LABEL <name> - handled in preprocessing
                pass
                
            elif opcode == "LOG":
                # LOG <message> - Enhanced logging
                message = self._parse_message(args)
                self.log(message)
                
            elif opcode == "PRINT":
                # PRINT <message> - Print to stdout
                message = self._parse_message(args)
                print(message)
                
            elif opcode == "SLEEP":
                # SLEEP <seconds>
                seconds = float(args[0])
                time.sleep(min(seconds, 5.0))  # Cap at 5 seconds for safety
                
            elif opcode == "FAIL":
                # FAIL <message>
                self.failed = True
                self.fail_message = self._parse_message(args)
                return False
                
            elif opcode == "PASS":
                # PASS
                self.passed = True
                return False
                
            elif opcode == "EXIT":
                # EXIT - Stop execution
                return False
                
            elif opcode == "NOP":
                # NOP - No operation
                pass
                
            else:
                raise TestVMError(f"Unknown instruction: {opcode}")
                
        except TestVMError:
            raise
        except Exception as e:
            raise TestVMError(f"Runtime error in {opcode}: {str(e)}", 
                            instruction.line_number, instruction) from e
            
        return not self._stop_execution
    
    def _handle_assertion(self, opcode: str, args: List[str]):
        self.assertions_count += 1
        self.last_assertion_failed = False
        
        if opcode == "ASSERT_EQ":
            # ASSERT_EQ <var/result> <expected>
            actual = self._get_assertion_value(args[0])
            expected = self.parse_value(args[1])
            
            if actual != expected:
                self.last_assertion_failed = True
                self.fail_message = f"Assertion failed: expected {expected}, got {actual}"
            else:
                self.assertions_passed += 1
                
        elif opcode == "ASSERT_NE":
            # ASSERT_NE <var/result> <unexpected>
            actual = self._get_assertion_value(args[0])
            unexpected = self.parse_value(args[1])
            
            if actual == unexpected:
                self.last_assertion_failed = True
                self.fail_message = f"Assertion failed: expected not {unexpected}, but got {actual}"
            else:
                self.assertions_passed += 1
                
        elif opcode == "ASSERT_TRUE":
            # ASSERT_TRUE <var/result>
            actual = self._get_assertion_value(args[0])
            
            if not actual.to_bool():
                self.last_assertion_failed = True
                self.fail_message = f"Assertion failed: expected true, got {actual}"
            else:
                self.assertions_passed += 1
                
        elif opcode == "ASSERT_FALSE":
            # ASSERT_FALSE <var/result>
            actual = self._get_assertion_value(args[0])
            
            if actual.to_bool():
                self.last_assertion_failed = True
                self.fail_message = f"Assertion failed: expected false, got {actual}"
            else:
                self.assertions_passed += 1
        
        elif opcode == "ASSERT_CONTAINS":
            # ASSERT_CONTAINS <haystack_var> <needle>
            haystack = self._get_assertion_value(args[0])
            needle = self.parse_value(args[1])
            
            haystack_str = str(haystack.data)
            needle_str = str(needle.data)
            
            if needle_str not in haystack_str:
                self.last_assertion_failed = True
                self.fail_message = f"Assertion failed: '{needle_str}' not found in '{haystack_str}'"
            else:
                self.assertions_passed += 1
                
        elif opcode == "ASSERT_MATCHES":
            # ASSERT_MATCHES <var> <regex_pattern>
            actual = self._get_assertion_value(args[0])
            pattern = args[1]
            
            if not re.search(pattern, str(actual.data)):
                self.last_assertion_failed = True
                self.fail_message = f"Assertion failed: '{actual.data}' does not match pattern '{pattern}'"
            else:
                self.assertions_passed += 1
    
    def _get_assertion_value(self, var_name: str) -> Value:
        if var_name == "result":
            return self.get_variable("result")
        elif var_name == "stack":
            return self.peek()
        else:
            return self.get_variable(var_name)
    
    def _handle_conditional_jump(self, opcode: str, args: List[str]):
        if opcode == "JUMP_IF_FAIL":
            if self.last_assertion_failed:
                label = args[0]
                if label in self.labels:
                    self.pc = self.labels[label] - 1
                else:
                    raise TestVMError(f"Label '{label}' not found")
                    
        elif opcode == "JUMP_IF_TRUE":
            condition_var = args[0]
            label = args[1]
            condition = self._get_assertion_value(condition_var)
            
            if condition.to_bool():
                if label in self.labels:
                    self.pc = self.labels[label] - 1
                else:
                    raise TestVMError(f"Label '{label}' not found")
                    
        elif opcode == "JUMP_IF_FALSE":
            condition_var = args[0]
            label = args[1]
            condition = self._get_assertion_value(condition_var)
            
            if not condition.to_bool():
                if label in self.labels:
                    self.pc = self.labels[label] - 1
                else:
                    raise TestVMError(f"Label '{label}' not found")
    
    def _parse_message(self, args: List[str]) -> str:
        message = " ".join(args)
        
        # Remove quotes if the message is quoted
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        
        # Simple variable interpolation: {var_name}
        def replace_var(match):
            var_name = match.group(1)
            try:
                value = self.get_variable(var_name)
                return str(value.data)
            except TestVMError:
                return f"{{UNDEFINED:{var_name}}}"
        
        message = re.sub(r'\{(\w+)\}', replace_var, message)
        return message
        
    def parse_program(self, source: str) -> List[Instruction]:
        instructions = []
        
        for line_num, line in enumerate(source.strip().split('\n'), 1):
            original_line = line
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            try:
                # Parse instruction
                parts = self._tokenize_line(line)
                if not parts:
                    continue
                    
                opcode = parts[0].upper()
                args = parts[1:] if len(parts) > 1 else []
                
                instruction = Instruction(opcode, args, line_num, original_line)
                instructions.append(instruction)
                
            except Exception as e:
                raise TestVMError(f"Parse error at line {line_num}: {str(e)}", line_num)
            
        return instructions
    
    def _tokenize_line(self, line: str) -> List[str]:
        tokens = []
        current_token = ""
        in_quotes = False
        escape_next = False
        
        for char in line:
            if escape_next:
                current_token += char
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == '"':
                if in_quotes:
                    tokens.append('"' + current_token + '"')
                    current_token = ""
                    in_quotes = False
                else:
                    if current_token:
                        tokens.append(current_token)
                        current_token = ""
                    in_quotes = True
            elif char == ' ' and not in_quotes:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char
        
        if current_token:
            tokens.append(current_token)
            
        return tokens
        
    def collect_labels(self, instructions: List[Instruction]):
        self.labels.clear()
        for i, instruction in enumerate(instructions):
            if instruction.opcode == "LABEL":
                if not instruction.args:
                    raise TestVMError(f"LABEL instruction missing label name at line {instruction.line_number}")
                label_name = instruction.args[0]
                if label_name in self.labels:
                    raise TestVMError(f"Duplicate label '{label_name}' at line {instruction.line_number}")
                self.labels[label_name] = i
                
    @contextmanager
    def _execution_timeout_context(self, timeout: float):
        def timeout_handler():
            time.sleep(timeout)
            if not self.passed and not self.failed:
                self._stop_execution = True
        
        timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
        timeout_thread.start()
        try:
            yield
        finally:
            self._stop_execution = False
            
    def execute_program(self, source: str, timeout: float = 30.0) -> TestResult:
        self.reset()
        self.execution_start_time = time.time()
        
        try:
            with self._execution_timeout_context(timeout):
                instructions = self.parse_program(source)
                self.collect_labels(instructions)
                
                self.pc = 0
                while (self.pc < len(instructions) and 
                       not self.failed and 
                       not self.passed and 
                       not self._stop_execution):
                    
                    instruction = instructions[self.pc]
                    
                    if not self.execute_instruction(instruction):
                        break
                        
                    self.pc += 1
                
                # Check for timeout
                if self._stop_execution and not self.passed and not self.failed:
                    self.failed = True
                    self.fail_message = f"Execution timeout after {timeout} seconds"
                
        except TestVMError as e:
            self.failed = True
            self.fail_message = str(e)
            if e.line_number:
                self.fail_message += f" (line {e.line_number})"
        except Exception as e:
            self.failed = True
            self.fail_message = f"Unexpected error: {str(e)}"
            
        execution_time = time.time() - self.execution_start_time
        
        return TestResult(
            name="",
            passed=self.passed,
            failed=self.failed or self.last_assertion_failed,execution_time=execution_time,
            logs=self.logs.copy(),
            error_message=self.fail_message,
            stack_trace=traceback.format_exc() if self.failed else "",
            assertions_count=self.assertions_count,
            assertions_passed=self.assertions_passed
        )
        
    def execute_test_case(self, test_case: TestCase) -> TestResult:
        self.log(f"Starting test case: {test_case.name}")
        
        # Execute setup if provided
        if test_case.setup:
            try:
                self.log("Executing setup...")
                setup_result = self.execute_program(test_case.setup, test_case.timeout / 3)
                if setup_result.failed:
                    return TestResult(
                        name=test_case.name,
                        passed=False,
                        failed=True,
                        execution_time=setup_result.execution_time,
                        logs=setup_result.logs,
                        error_message=f"Setup failed: {setup_result.error_message}",
                        stack_trace=setup_result.stack_trace,
                        assertions_count=0,
                        assertions_passed=0
                    )
            except Exception as e:
                return TestResult(
                    name=test_case.name,
                    passed=False,
                    failed=True,
                    execution_time=0.0,
                    logs=self.logs.copy(),
                    error_message=f"Setup error: {str(e)}",
                    stack_trace=traceback.format_exc(),
                    assertions_count=0,
                    assertions_passed=0
                )
        
        # Execute main test
        try:
            main_result = self.execute_program(test_case.program, test_case.timeout)
            main_result.name = test_case.name
            
            # Check expected result if provided
            if test_case.expected_result is not None:
                if "result" in self.variables:
                    actual_result = str(self.variables["result"].data)
                    if actual_result != test_case.expected_result:
                        main_result.passed = False
                        main_result.failed = True
                        main_result.error_message = f"Expected result '{test_case.expected_result}', got '{actual_result}'"
                        
        except Exception as e:
            main_result = TestResult(
                name=test_case.name,
                passed=False,
                failed=True,
                execution_time=0.0,
                logs=self.logs.copy(),
                error_message=f"Test execution error: {str(e)}",
                stack_trace=traceback.format_exc(),
                assertions_count=self.assertions_count,
                assertions_passed=self.assertions_passed
            )
        
        # Execute teardown if provided
        if test_case.teardown and not main_result.failed:
            try:
                self.log("Executing teardown...")
                teardown_result = self.execute_program(test_case.teardown, test_case.timeout / 3)
                if teardown_result.failed:
                    main_result.logs.extend(teardown_result.logs)
                    main_result.error_message += f" | Teardown failed: {teardown_result.error_message}"
            except Exception as e:
                main_result.logs.append(f"Teardown error: {str(e)}")
                
        return main_result
        
    def execute_test_suite(self, test_cases: List[TestCase]) -> List[TestResult]:
        results = []
        
        for test_case in test_cases:
            self.reset()  # Reset VM state for each test
            result = self.execute_test_case(test_case)
            results.append(result)
            
        return results
        
    def get_state_snapshot(self) -> Dict[str, Any]:
        return {
            "stack": [{"type": v.type.value, "data": v.data} for v in self.stack],
            "variables": {k: {"type": v.type.value, "data": v.data} for k, v in self.variables.items()},
            "pc": self.pc,
            "labels": self.labels.copy(),
            "failed": self.failed,
            "passed": self.passed,
            "assertions_count": self.assertions_count,
            "assertions_passed": self.assertions_passed,
            "logs": self.logs.copy()
        }
        
    def load_state_snapshot(self, snapshot: Dict[str, Any]):
        self.stack = [Value(ValueType(v["type"]), v["data"]) for v in snapshot["stack"]]
        self.variables = {k: Value(ValueType(v["type"]), v["data"]) for k, v in snapshot["variables"].items()}
        self.pc = snapshot["pc"]
        self.labels = snapshot["labels"].copy()
        self.failed = snapshot["failed"]
        self.passed = snapshot["passed"]
        self.assertions_count = snapshot["assertions_count"]
        self.assertions_passed = snapshot["assertions_passed"]
        self.logs = snapshot["logs"].copy()


class TestSuite:    
    def __init__(self, name: str = "Default Test Suite"):
        self.name = name
        self.test_cases: List[TestCase] = []
        self.vm = EnhancedTestVM()
        
    def add_test_case(self, test_case: TestCase):
        self.test_cases.append(test_case)
        
    def add_test(self, name: str, program: str, expected_result: Optional[str] = None, 
                 timeout: float = 10.0, setup: Optional[str] = None, 
                 teardown: Optional[str] = None, tags: List[str] = None):
        test_case = TestCase(
            name=name,
            program=program,
            expected_result=expected_result,
            timeout=timeout,
            setup=setup,
            teardown=teardown,
            tags=tags or []
        )
        self.add_test_case(test_case)
        
    def run_all_tests(self, filter_tags: Optional[List[str]] = None) -> List[TestResult]:
        tests_to_run = self.test_cases
        
        if filter_tags:
            tests_to_run = [tc for tc in self.test_cases 
                          if any(tag in tc.tags for tag in filter_tags)]
            
        return self.vm.execute_test_suite(tests_to_run)
        
    def run_single_test(self, test_name: str) -> Optional[TestResult]:
        for test_case in self.test_cases:
            if test_case.name == test_name:
                self.vm.reset()
                return self.vm.execute_test_case(test_case)
        return None
        
    def generate_report(self, results: List[TestResult]) -> str:
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = sum(1 for r in results if r.failed)
        total_assertions = sum(r.assertions_count for r in results)
        passed_assertions = sum(r.assertions_passed for r in results)
        total_time = sum(r.execution_time for r in results)
        
        report = []
        report.append(f"Test Suite: {self.name}")
        report.append("=" * (len(self.name) + 12))
        report.append("")
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {passed_tests}")
        report.append(f"Failed: {failed_tests}")
        report.append(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        report.append(f"Total Assertions: {total_assertions}")
        report.append(f"Passed Assertions: {passed_assertions}")
        report.append(f"Assertion Success Rate: {(passed_assertions/total_assertions)*100:.1f}%" if total_assertions > 0 else "N/A")
        report.append(f"Total Execution Time: {total_time:.3f}s")
        report.append("")
        
        # Individual test results
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            report.append(f"[{status}] {result.name} ({result.execution_time:.3f}s)")
            
            if result.failed and result.error_message:
                report.append(f"    Error: {result.error_message}")
                
            if result.assertions_count > 0:
                report.append(f"    Assertions: {result.assertions_passed}/{result.assertions_count}")
                
        return "\n".join(report)


def create_example_test_suite() -> TestSuite:
    suite = TestSuite("Enhanced Test VM Examples")
    
    # Basic arithmetic test
    suite.add_test(
        name="Basic Arithmetic",
        program="""
            LOAD 10
            LOAD 5
            CALL add
            ASSERT_EQ result 15
            PASS
        """,
        tags=["arithmetic", "basic"]
    )
    
    # String operations test
    suite.add_test(
        name="String Operations",
        program="""
            LOAD "Hello"
            LOAD " World"
            CALL concat
            STORE_VAR greeting
            ASSERT_EQ greeting "Hello World"
            
            LOAD_VAR greeting
            CALL length
            ASSERT_EQ result 11
            PASS
        """,
        tags=["string", "basic"]
    )
    
    # List operations test
    suite.add_test(
        name="List Operations",
        program="""
            CALL list_create
            STORE_VAR mylist
            
            LOAD_VAR mylist
            LOAD 42
            CALL list_append
            STORE_VAR mylist
            
            LOAD_VAR mylist
            LOAD 0
            CALL list_get
            ASSERT_EQ result 42
            PASS
        """,
        tags=["list", "collections"]
    )
    
    # Conditional logic test
    suite.add_test(
        name="Conditional Logic",
        program="""
            LOAD 5
            LOAD 3
            CALL greater_than
            STORE_VAR is_greater
            
            JUMP_IF_TRUE is_greater success
            FAIL "5 should be greater than 3"
            
            LABEL success
            ASSERT_TRUE is_greater
            PASS
        """,
        tags=["logic", "conditionals"]
    )
    
    # Error handling test
    suite.add_test(
        name="Error Handling",
        program="""
            LOAD 10
            LOAD 0
            CALL divide
            STORE_VAR result_val
            
            # Should handle division by zero gracefully
            LOAD_VAR result_val
            CALL to_string
            ASSERT_CONTAINS result "inf"
            PASS
        """,
        tags=["error_handling", "edge_cases"]
    )
    
    return suite


if __name__ == "__main__":
    # Example usage
    print("Test VM Engine")
    print("-" * 25)
    
    # Create and run example test suite
    suite = create_example_test_suite()
    results = suite.run_all_tests()
    
    # Generate and print report
    report = suite.generate_report(results)
    print(report)
    
    print("\n" + "-" * 50)
    print("Individual Test Logs:")
    print("-" * 50)
    
    for result in results:
        if result.logs:
            print(f"\n--- {result.name} ---")
            for log_entry in result.logs:
                print(f"  {log_entry}")

