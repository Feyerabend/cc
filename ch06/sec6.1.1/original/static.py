INSTRUCTION_ANNOTATIONS = {
    'PUSH': {
        'pre': lambda vm, args: len(args) == 1,
        'post': lambda vm, args: vm.stack[-1] == args[0],
    },
    'ADD': {
        'pre': lambda vm, args: len(vm.stack) >= 2 and all(isinstance(x, int) for x in vm.stack[-2:]),
        'post': lambda vm, args: len(vm.stack) > 0 and isinstance(vm.stack[-1], int),
    },
    'PUSH_LIST': {
        'pre': lambda vm, args: True,
        'post': lambda vm, args: isinstance(vm.stack[-1], list),
    },
    'APPEND': {
        'pre': lambda vm, args: len(vm.stack) >= 2 and isinstance(vm.stack[-2], list),
        'post': lambda vm, args: isinstance(vm.stack[-1], list),
    },
    'STORE': {
        'pre': lambda vm, args: len(args) == 1 and len(vm.stack) > 0,
        'post': lambda vm, args: args[0] in vm.memory,
    },
}

class StaticAnalyzer:
    def __init__(self, program, vm):
        self.program = program
        self.vm = vm

    def analyze(self):
        print("Starting static analysis...")
        for i, instruction in enumerate(self.program):
            opcode = instruction[0]
            args = instruction[1:] if len(instruction) > 1 else ()

            print(f"\nAnalyzing instruction {i}: {instruction}")
            print(f"Stack before analysis: {self.vm.stack}")
            print(f"Memory before analysis: {self.vm.memory}")

            # Get annotations for the opcode
            annotations = INSTRUCTION_ANNOTATIONS.get(opcode, None)
            if annotations is None:
                raise Exception(f"No annotations found for instruction: {opcode}")

            # Check precondition
            precondition = annotations.get('pre', lambda vm, args: True)
            if not precondition(self.vm, args):
                raise Exception(f"Precondition failed at instruction {i}: {instruction}")

            # Simulate the effect of the instruction
            self.simulate_instruction(opcode, args)

            # Check postcondition
            postcondition = annotations.get('post', lambda vm, args: True)
            if not postcondition(self.vm, args):
                raise Exception(f"Postcondition failed at instruction {i}: {instruction}")

            print(f"Stack after analysis: {self.vm.stack}")
            print(f"Memory after analysis: {self.vm.memory}")

        print("Static analysis passed.")
        return True

    def simulate_instruction(self, opcode, args):
        """Simulate the effect of the instruction on the VM state."""
        if opcode == 'PUSH':
            if len(args) != 1:
                raise Exception("PUSH expects one argument.")
            self.vm.stack.append(args[0])

        elif opcode == 'ADD':
            if len(self.vm.stack) < 2:
                raise Exception("Stack underflow during ADD.")
            x = self.vm.stack.pop()
            y = self.vm.stack.pop()
            self.vm.stack.append(x + y)

        elif opcode == 'PUSH_LIST':
            self.vm.stack.append([])

        elif opcode == 'APPEND':
            if len(self.vm.stack) < 2:
                raise Exception("Stack underflow during APPEND.")
            value = self.vm.stack.pop()
            lst = self.vm.stack.pop()
            if not isinstance(lst, list):
                raise Exception(f"Expected a list, but found {type(lst)} during APPEND.")
            lst.append(value)
            self.vm.stack.append(lst)

        elif opcode == 'STORE':
            if len(args) != 1:
                raise Exception("STORE expects one argument (variable name).")
            if len(self.vm.stack) == 0:
                raise Exception("Stack underflow during STORE.")
            var_name = args[0]
            value = self.vm.stack.pop()
            self.vm.memory[var_name] = value

        else:
            raise Exception(f"Unknown instruction: {opcode}")

# Define a simple VM with a stack and memory
class VirtualMachine:
    def __init__(self):
        self.stack = []
        self.memory = {}

# Define a test program
program = [
    ('PUSH', 5),         # Push 5 onto the stack
    ('PUSH', 10),        # Push 10 onto the stack
    ('ADD',),            # Add the top two numbers (5 + 10)
    ('PUSH_LIST',),      # Push an empty list onto the stack
    ('PUSH', 15),        # Push 15 (value to append to the list)
    ('APPEND',),         # Append 15 to the list
    ('STORE', 'result'), # Store the list in memory under 'result'
]

# Define a simple VM with a stack and memory
class VirtualMachine:
    def __init__(self):
        self.stack = []
        self.memory = {}

# Create a VM instance
vm = VirtualMachine()

# Analyze the program
analyzer = StaticAnalyzer(program, vm)
try:
    analyzer.analyze()
except Exception as e:
    print(f"Static analysis failed: {e}")
