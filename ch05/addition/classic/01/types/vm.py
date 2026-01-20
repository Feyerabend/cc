# This is the implementation of a simple stack-based virtual machine (VM) with
# support for functions, closures, and nested environments.

from validator import validate_bytecode

# vm
class VM:
    def __init__(self):
        self.stack = []
        self.call_stack = []
        self.functions = {}
        self.environment = [{}]  # dictionaries for nested environments
        self.pc = 0

    def define_function(self, name, arg_count, bytecode):
        self.functions[name] = (arg_count, bytecode)

    def create_closure(self, func_name):
        return (func_name, [env.copy() for env in self.environment])

    def call_closure(self, closure, args):
        func_name, saved_env = closure
        arg_count, bytecode = self.functions[func_name]
        if len(args) != arg_count:
            raise Exception("Argument count mismatch")

        self.call_stack.append((self.environment.copy(), self.stack[:]))
        self.environment = [env.copy() for env in saved_env]
        self.environment.append({f'ARG{i+1}': args[i] for i in range(arg_count)})
        self.execute(bytecode)
        self.environment, old_stack = self.call_stack.pop()

        if self.stack:
            return_value = self.stack.pop()
        else:
            return_value = None

        self.stack = old_stack
        self.stack.append(return_value)

    def call_function(self, func_name, args):
        if func_name not in self.functions:
            raise Exception(f"Function {func_name} not defined")

        arg_count, bytecode = self.functions[func_name]
        if len(args) != arg_count:
            raise Exception("Argument count mismatch")

        self.call_stack.append((self.environment.copy(), self.stack[:], self.pc))
        self.environment.append({f'ARG{i+1}': args[i] for i in range(arg_count)})
        self.execute(bytecode)

        self.environment, old_stack, old_pc = self.call_stack.pop()

        if self.stack:
            return_value = self.stack.pop()
        else:
            return_value = None

        self.stack = old_stack
        self.stack.append(return_value)

    def _check_type(self, value, expected_type, operation):
        if isinstance(value, expected_type):
            return value

        # int to float if expected type is float
        self._type_coerce(value, expected_type, operation)

    def _type_coerce(self, value, expected_type, operation):
        if expected_type == (int, float):
            if isinstance(value, int):
                return float(value)  # int to float if expected type is float
            elif isinstance(value, float):
                return value
            else:
                raise TypeError(f"Invalid type for {operation}: expected {expected_type}, got {type(value)}")

    def _type_coerce_bool(self, value, operation):
        if isinstance(value, int):
            return bool(value)
        elif isinstance(value, float):
            return bool(value)
        else:
            raise TypeError(f"Invalid type for {operation}: expected int, got {type(value)}")

    # main loop
    def execute(self, bytecode):
        validate_bytecode(bytecode)

        self.pc = 0

        while self.pc < len(bytecode):
            instr = bytecode[self.pc]
            self.pc += 1

            print(f"Executing instruction: {instr}, Stack: {self.stack}, Environment: {self.environment}")

            if instr == 'SET':
                value = bytecode[self.pc]
                self.pc += 1
                self.stack.append(value)

            elif instr == 'LOAD':
                var_name = bytecode[self.pc]
                self.pc += 1
                for env in reversed(self.environment):
                    if var_name in env:
                        self.stack.append(env[var_name])
                        break
                else:
                    raise Exception(f"Variable {var_name} not found")

            elif instr == 'STORE':
                if self.stack:
                    value = self.stack.pop()
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                var_name = bytecode[self.pc]
                self.pc += 1
                self.environment[-1][var_name] = value

            elif instr == 'ADD':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, (int, float), 'ADD')
                    self._check_type(b, (int, float), 'ADD')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                self.stack.append(a + b)


            elif instr == 'SUB':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, (int, float), 'SUB')
                    self._check_type(b, (int, float), 'SUB')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                self.stack.append(a - b)

            elif instr == 'MUL':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, (int, float), 'MUL')
                    self._check_type(b, (int, float), 'MUL')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                self.stack.append(a * b)

            elif instr == 'DIV':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, (int, float), 'DIV')
                    self._check_type(b, (int, float), 'DIV')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                if b == 0:
                    raise Exception("Division by zero")
                self.stack.append(a // b)

            elif instr == 'AND':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, int, 'AND')
                    self._check_type(b, int, 'AND')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                c = a & b
                self.stack.append(c)

            elif instr == 'OR':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, int, 'OR')
                    self._check_type(b, int, 'OR')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                c = a | b
                self.stack.append(c)

            elif instr == 'LOGICAL_AND':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._type_coerce_bool(a, 'LOGICAL_AND')
                    self._type_coerce_bool(b, 'LOGICAL_AND')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                c = a & b
                self.stack.append(c)

            elif instr == 'LOGICAL_OR':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._type_coerce_bool(a, 'LOGICAL_OR')
                    self._type_coerce_bool(b, 'LOGICAL_OR')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                c = a | b
                self.stack.append(c)

            elif instr == 'GEQ':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, int, 'GEQ')
                    self._check_type(b, int, 'GEQ')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                if a >= b:
                    c = 1
                else:
                    c = 0
                self.stack.append(c)

            elif instr == 'LEQ':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, int, 'LEQ')
                    self._check_type(b, int, 'LEQ')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                if a <= b:
                    c = 1
                else:
                    c = 0
                self.stack.append(c)

            elif instr == 'LT':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, int, 'LT')
                    self._check_type(b, int, 'LT')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                if a < b:
                    c = 1
                else:
                    c = 0
                self.stack.append(c)

            elif instr == 'GT':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, int, 'GT')
                    self._check_type(b, int, 'GT')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                if a > b:
                    c = 1
                else:
                    c = 0
                self.stack.append(c)

            elif instr == 'EQ':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, int, 'EQ')
                    self._check_type(b, int, 'EQ')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                if a == b:
                    c = 1
                else:
                    c = 0
                self.stack.append(c)

            elif instr == 'NEQ':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_type(a, int, 'NEQ')
                    self._check_type(b, int, 'NEQ')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                if a != b:
                    c = 1
                else:
                    c = 0
                self.stack.append(c)

            elif instr == 'SWAP':
                if self.stack:
                    b = self.stack.pop()
                    a = self.stack.pop()
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                self.stack.append(b)
                self.stack.append(a)

            elif instr == 'DUP':
                if self.stack:
                    value = self.stack[-1]
                else:
                    raise Exception(f"No item on stack for DUP")
                self.stack.append(value)

            elif instr == 'NEG':
                if self.stack:
                    value = self.stack.pop()
                    self._check_type(value, int, 'NEG')
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                self.stack.append(-value)

            elif instr == 'POP':
                if self.stack:
                    self.stack.pop()
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")

            elif instr == 'JP':
                target = bytecode[self.pc]
                self.pc = target

            elif instr == 'JZ':
                target = bytecode[self.pc]
                self.pc += 1
                if self.stack:
                    condition = self.stack.pop()
                else:
                    raise IndexError("Stack underflow: attempting to pop from an empty stack")
                if condition == 0:
                    self.pc = target

            elif instr == 'PRINT':
                if self.stack:
                    value = self.stack[-1] # leave val on stack
                else:
                    pass # nothing to print
                print(value)

            elif instr == 'NOP':
                pass

            elif instr == 'RET':
                if self.stack:
                    return_value = self.stack.pop()
                else:
                    return_value = None

                if self.call_stack:
                    self.environment, self.stack, self.pc = self.call_stack.pop()
                else:
                    raise Exception("RET instruction executed with an empty call stack")

                self.stack.append(return_value)
                self.pc += 1
                return

            elif instr == 'CALL':
                func_name = bytecode[self.pc]
                self.pc += 1
                arg_count = self.functions[func_name][0]
                args = [self.stack.pop() for _ in range(arg_count)]

                self.call_stack.append((self.environment.copy(), self.stack[:], self.pc))
                self.call_function(func_name, list(reversed(args)))

            elif instr == 'CAT':
                if self.stack:
                    lst2 = self.stack.pop()
                    lst1 = self.stack.pop()
                    if isinstance(lst1, list) and isinstance(lst2, list):
                        self.stack.append(lst1 + lst2)
                # else nothing to concatenate

            elif instr == 'CONS':
                if len(self.stack) < 2:
                    raise Exception("Stack underflow: insufficient elements for CONS")
                car = self.stack.pop()
                cdr = self.stack.pop()
                if isinstance(cdr, list):
                    self.stack.append([car] + cdr)
                else:
                    self.stack.append([car, cdr])

            elif instr == 'CAR':
                lst = self.stack.pop() if self.stack else None
                if isinstance(lst, list) and len(lst) > 0:
                    self.stack.append(lst[0])
                else:
                    raise Exception("Expected a non-empty list")

            elif instr == 'CDR':
                lst = self.stack.pop() if self.stack else None
                if isinstance(lst, list) and len(lst) > 0:
                    self.stack.append(lst[1:])
                else:
                    raise Exception("Expected a non-empty list")

            # LIST instruction to create a list from stack elements
            elif instr == 'LIST':
                elements = []
                while self.stack and not isinstance(self.stack[-1], str):
                    elements.append(self.stack.pop())
                self.stack.append(list(reversed(elements)))

            elif instr == 'LEN':
                def nested_LEN(lst):
                    return sum(nested_LEN(item) if isinstance(item, list) else 1 for item in lst)
                lst = self.stack[-1] if self.stack else None
                if isinstance(lst, list):
                    length = nested_LEN(lst)
                    self.stack.append(length)
                else:
                    raise Exception("Expected a list")

            elif instr == 'FLAT':
                def flatten(lst):
                    flat = []
                    for item in lst:
                        if isinstance(item, list):
                            flat.extend(flatten(item))
                        else:
                            flat.append(item)
                    return flat

                lst = self.stack.pop() if self.stack else None
                if isinstance(lst, list):
                    nlst = flatten(lst)
                    self.stack.append(nlst)
                # else:
                #    raise Exception("No list to flatten")

            elif instr == 'NTH':
                idx = self.stack.pop() if self.stack else None
                lst = self.stack[-1] if self.stack else None
                if isinstance(lst, list) and isinstance(idx, int) and 0 <= idx < len(lst):
                    self.stack.append(lst[idx])
                else:
                    raise Exception("Index out of bounds or not a list")

            elif instr == 'IDX':
                idx = self.stack.pop() if self.stack else None
                lst = self.stack[-1] if self.stack else None
                if isinstance(lst, list) and isinstance(idx, int):
                    if 0 <= idx < len(lst):
                        self.stack.append(lst[idx])
                    else:
                        raise Exception("Index out of bounds")
                else:
                    raise Exception("Expected a list and an integer for index")

            elif instr == 'HALT':
                break

            else:
                raise Exception(f"Unknown instruction: {instr}")

        # print('HALT')
