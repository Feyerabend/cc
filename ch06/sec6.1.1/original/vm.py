
class VirtualMachine:
    def __init__(self):
        self.stack = []
        self.memory = {}
        self.pc = 0

    def check_precondition(self, condition):
        if not condition(self):
            raise Exception("Precondition failed!")

    def check_postcondition(self, condition):
        if not condition(self):
            raise Exception("Postcondition failed!")

    def execute(self, program):
        while self.pc < len(program):
            instruction = program[self.pc]
            opcode = instruction[0]
            args = instruction[1:] if len(instruction) > 1 else ()
            self.pc += 1

            print(f"Executing {opcode} with args {args}")
            print(f"Stack before operation: {self.stack}")

            try:
                if opcode == 'CHECK_PRECONDITION':
                    self.check_precondition(*args)
                    print("Precondition passed.")

                elif opcode == 'CHECK_POSTCONDITION':
                    self.check_postcondition(*args)
                    print("Postcondition passed.")

                elif opcode == 'ADD':
                    x = self.stack.pop()
                    y = self.stack.pop()
                    self.stack.append(x + y)

                elif opcode == 'PUSH_LIST':
                    lst = []
                    self.stack.append(lst)

                elif opcode == 'APPEND':
                    if len(self.stack) < 2:
                        raise Exception("Not enough elements on the stack for APPEND operation.")
                    lst = self.stack.pop()
                    if not isinstance(lst, list):
                        raise Exception(f"Expected a list to append to, but found {type(lst)}!")
                    value = self.stack.pop()  
                    lst.append(value)
                    self.stack.append(lst)

                elif opcode == 'STORE':
                    var_name = args[0]
                    value = self.stack.pop()
                    self.memory[var_name] = value

                elif opcode == 'LOAD':
                    var_name = args[0]
                    value = self.memory.get(var_name)
                    if value is None:
                        raise Exception(f"Variable {var_name} not found!")
                    self.stack.append(value)

                elif opcode == 'PUSH':
                    self.stack.append(args[0])

                elif opcode == 'INDEX':
                    idx = self.stack.pop()
                    lst = self.stack.pop()

                    if not isinstance(lst, list):
                        raise Exception(f"Expected a list, but found {type(lst)}!")
                    if not isinstance(idx, int):
                        raise Exception(f"Expected an integer index, but found {type(idx)}!")
                    if idx < 0 or idx >= len(lst):
                        raise Exception(f"Index {idx} out of range for list of length {len(lst)}.")

                    result = lst[idx]
                    self.stack.append(result)

                elif opcode == 'HALT':
                    break

                else:
                    raise Exception(f"Unknown instruction: {opcode}")

                print(f"Stack after operation: {self.stack}")

            except Exception as e:
                print(f"Error during execution: {e}")
                break

        print(f"Final Stack: {self.stack}")
        print(f"Memory: {self.memory}")

program = [
    ('CHECK_PRECONDITION', lambda vm: 'x' in vm.memory),   # ensure 'x' is defined
    ('LOAD', 'x'),                                         # load variable 'x'
    ('CHECK_POSTCONDITION', lambda vm: len(vm.stack) > 0), # ensure stack isn't empty
    ('PUSH_LIST',),                                        # push a new list to the stack
    ('APPEND',),                                           # append 'x' to the list
    ('STORE', 'lst'),                                      # store the list in 'lst'
    ('CHECK_PRECONDITION', lambda vm: 'lst' in vm.memory), # ensure 'lst' exists
    ('LOAD', 'x'),                                         # load 'x'
    ('LOAD', 'lst'),                                       # load 'lst'
    ('PUSH', 0),                                           # push index for list access
    ('INDEX',),                                            # get 'lst[0]'
    ('CHECK_POSTCONDITION', lambda vm: isinstance(vm.stack[-1], int)), # ensure top is an int
    ('ADD',),                                              # add 'x' and 'lst[0]'
    ('HALT',),                                             # halt the program
]

vm = VirtualMachine()
vm.memory['x'] = 5  # predefine 'x' in memory
vm.execute(program)
