class VirtualMachine:
    def __init__(self):
        self.stack = []
        self.memory = {}
        self.pc = 0  # program counter
        self.instructions = []
        self.labels = {}
    
    def load(self, instructions):
        self.instructions = instructions
        self.build_label_table()
    
    def build_label_table(self):
        for i, instr in enumerate(self.instructions):
            if instr.endswith(":"):
                label = instr[:-1]
                self.labels[label] = i
    
    def run(self):
        while self.pc < len(self.instructions):
            instruction = self.instructions[self.pc]
            
            # Skip labels
            if instruction.endswith(":"):
                self.pc += 1
                continue
            
            parts = instruction.split(maxsplit=1)
            op = parts[0]
            arg = parts[1] if len(parts) > 1 else None
            
            if op == "PUSH":
                if arg.startswith('"') and arg.endswith('"'):
                    self.stack.append(arg[1:-1])
                else:
                    value = float(arg) if '.' in arg else int(arg)
                    self.stack.append(value)
            
            elif op == "STORE":
                self.memory[arg] = self.stack.pop()
            
            elif op == "LOAD":
                if arg not in self.memory:
                    raise RuntimeError(f"Undefined variable: {arg}")
                self.stack.append(self.memory[arg])
            
            elif op == "ADD":
                b = self.stack.pop()
                a = self.stack.pop()
                if isinstance(a, str) or isinstance(b, str):
                    self.stack.append(str(a) + str(b))
                else:
                    self.stack.append(a + b)
            
            elif op == "SUB":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)
            
            elif op == "MUL":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
            
            elif op == "DIV":
                b = self.stack.pop()
                a = self.stack.pop()
                if b == 0:
                    raise RuntimeError("Division by zero")
                self.stack.append(a // b if isinstance(a, int) and isinstance(b, int) else a / b)
            
            elif op == "MOD":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a % b)
            
            elif op == "NEG":
                self.stack.append(-self.stack.pop())
            
            elif op == "EQ":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a == b else 0)
            
            elif op == "NE":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a != b else 0)
            
            elif op == "LT":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a < b else 0)
            
            elif op == "GT":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a > b else 0)
            
            elif op == "LE":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a <= b else 0)
            
            elif op == "GE":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a >= b else 0)
            
            elif op == "JMP":
                self.pc = self.labels[arg]
                continue
            
            elif op == "JZ":
                if self.stack.pop() == 0:
                    self.pc = self.labels[arg]
                    continue
            
            elif op == "PRINT":
                print(self.stack.pop())
            
            elif op == "INPUT":
                value = input("> ")
                try:
                    value = float(value) if '.' in value else int(value)
                except ValueError:
                    pass  # keep as string
                self.stack.append(value)
            
            elif op == "HALT":
                break
            
            else:
                raise RuntimeError(f"Unknown instruction: {instruction}")
            
            self.pc += 1

if __name__ == "__main__":
    instructions = [
        'PUSH 10',
        'STORE x',
        'PUSH 20',
        'STORE y',
        'LOAD x',
        'LOAD y',
        'LT',
        'JZ L0',
        'PUSH "x is smaller"',
        'PRINT',
        'L0:',
        'HALT'
    ]
    
    vm = VirtualMachine()
    vm.load(instructions)
    vm.run()
