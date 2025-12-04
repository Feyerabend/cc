class HarvardVM:
    def __init__(self, instructions, data):
        self.instructions = instructions  # instruction memory
        self.data = data  # data memory
        self.pc = 0  # program counter
        self.registers = [0] * 4  # R0, R1, R2, R3

    def run(self):
        while self.pc < len(self.instructions):
            instruction = self.instructions[self.pc]
            if instruction == "LOAD":
                reg = self.instructions[self.pc + 1]
                addr = self.instructions[self.pc + 2]
                self.registers[reg] = self.data[addr]
                self.pc += 2
            elif instruction == "ADD":
                reg1 = self.instructions[self.pc + 1]
                reg2 = self.instructions[self.pc + 2]
                self.registers[reg1] += self.registers[reg2]
                self.pc += 2
            elif instruction == "PRINT":
                reg = self.instructions[self.pc + 1]
                print(self.registers[reg])
                self.pc += 1
            elif instruction == "HALT":
                break
            self.pc += 1

# example
instructions = ["LOAD", 0, 0, "LOAD", 1, 1, "ADD", 0, 1, "PRINT", 0, "HALT"]
data = [5, 10]
vm = HarvardVM(instructions, data)
vm.run()

# print 15
