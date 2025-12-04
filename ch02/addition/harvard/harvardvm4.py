import threading
import queue
import time

class PipelinedHarvardVM:
    def __init__(self, instructions, data):
        self.instructions = instructions
        self.data = data
        self.registers = [0] * 4
        self.pc = 0
        self.running = True
        self.fetch_queue = queue.Queue()
        self.decode_queue = queue.Queue()
        self.execute_queue = queue.Queue()

    def fetch(self):
        while self.running:
            if self.pc < len(self.instructions):
                instruction = self.instructions[self.pc]
                self.fetch_queue.put((self.pc, instruction))
                self.pc += 1
                time.sleep(0.1)  # .. fetch delay
            else:
                self.running = False

    def decode(self):
        while self.running or not self.fetch_queue.empty():
            try:
                pc, instruction = self.fetch_queue.get(timeout=0.1)
                if instruction == "HALT":
                    self.running = False
                self.decode_queue.put((pc, instruction))
            except queue.Empty:
                pass

    def execute(self):
        while self.running or not self.decode_queue.empty():
            try:
                pc, instruction = self.decode_queue.get(timeout=0.1)
                if instruction == "LOAD":
                    reg = self.instructions[pc + 1]
                    addr = self.instructions[pc + 2]
                    self.registers[reg] = self.data[addr]
                elif instruction == "ADD":
                    reg1 = self.instructions[pc + 1]
                    reg2 = self.instructions[pc + 2]
                    self.registers[reg1] += self.registers[reg2]
                elif instruction == "PRINT":
                    reg = self.instructions[pc + 1]
                    print(f"Output: {self.registers[reg]}")
                elif instruction == "HALT":
                    self.running = False
                time.sleep(0.1)  # .. execute delay
            except queue.Empty:
                pass

    def run(self):
        threads = [
            threading.Thread(target=self.fetch),
            threading.Thread(target=self.decode),
            threading.Thread(target=self.execute),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

# example
instructions = ["LOAD", 0, 0, "LOAD", 1, 1, "ADD", 0, 1, "PRINT", 0, "HALT"]
data = [5, 10]
vm = PipelinedHarvardVM(instructions, data)
vm.run()
