import asyncio
import time

class ParallelHarvardVM:
    def __init__(self, instructions, data):
        self.instructions = instructions  # instruction memory
        self.data = data  # data memory
        self.pc = 0  # program counter
        self.registers = [0] * 4  # R0, R1, R2, R3
        self.running = True

    async def fetch_instructions(self):
        """Fetch instructions asynchronously."""
        while self.running:
            if self.pc < len(self.instructions):
                instruction = self.instructions[self.pc]
                await self.execute_instruction(instruction)
                self.pc += 1
                await asyncio.sleep(0.1)  # .. fetch delay
            else:
                self.running = False

    async def execute_instruction(self, instruction):
        """Simulate execution of a fetched instruction."""
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
            print(f"Output: {self.registers[reg]}")
            self.pc += 1
        elif instruction == "HALT":
            self.running = False
        await asyncio.sleep(0.05)  # .. execute delay

    async def run(self):
        """Simulate parallel processing of fetch and execution."""
        await self.fetch_instructions()

# example
instructions = ["LOAD", 0, 0, "LOAD", 1, 1, "ADD", 0, 1, "PRINT", 0, "HALT"]
data = [5, 10]
vm = ParallelHarvardVM(instructions, data)

asyncio.run(vm.run())
