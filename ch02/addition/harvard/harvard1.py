class HarvardVM:
    def __init__(self, instructions, data):
        self.instructions = instructions  # instruction memory
        self.data = data  # data memory
        self.pc = 0  # program counter
        self.registers = [0] * 4  # simple general-purpose registers

    def run(self):
        while self.pc < len(self.instructions):
            instruction = self.instructions[self.pc]
            if instruction == "ADD":
                self.registers[0] += self.registers[1]
            elif instruction == "LOAD":
                self.registers[1] = self.data[self.instructions[self.pc + 1]]
                self.pc += 1
            elif instruction == "PRINT":
                print(self.registers[0])
            elif instruction == "HALT":
                break
            self.pc += 1

# example
instructions = ["LOAD", 0, "ADD", "PRINT", "HALT"]
data = [10, 20, 30]
vm = HarvardVM(instructions, data)
vm.run()

# 0 + 10 = 10 in print
