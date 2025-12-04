## Harvard Architecture vs. von Neumann Architecture

There are alternative approaches to the von Neumann architecture for building computers, one
of which is the Harvard architecture. Both the Harvard and von Neumann architectures are
foundational paradigms in computer architecture, primarily differing in how they manage memory
and interact with processing units.

1. von Neumann
  - Unified memory: In a von Neumann architecture, the program instructions and data *share* the same memory space.
  - Single data path: This means the processor fetches both instructions and data from the same memory using a single bus.
  - Bottleneck: The shared memory and bus often lead to the so-called 'von Neumann bottleneck,' where the speed of the
    system is limited by the rate at which the processor can fetch data and instructions.

2. Harvard
  - Separate memories: The Harvard architecture uses *separate* memory spaces for program instructions and data.
  - Parallel fetching: With distinct buses for instructions and data, the processor can fetch instructions and
    access data simultaneously, leading to potential performance improvements.
  - Modern usage: This architecture is commonly found in embedded systems and DSPs (Digital Signal Processors).


### Conceptual example

Illustration of the often mentioned distinction between the two: __memory__.

__von Neumann VM__

In a von Neumann VM, both data and instructions are stored in the same array.

```python
class VonNeumannVM:
    def __init__(self, memory):
        self.memory = memory  # unified memory for instructions and data
        self.pc = 0  # program counter
        self.registers = [0] * 4  # simple general-purpose registers

    def run(self):
        while self.pc < len(self.memory):
            instruction = self.memory[self.pc]
            if instruction == "ADD":
                self.registers[0] += self.registers[1]
            elif instruction == "LOAD":
                self.registers[1] = self.memory[self.pc + 1]
                self.pc += 1
            elif instruction == "PRINT":
                print(self.registers[0])
            elif instruction == "HALT":
                break
            self.pc += 1

# example
program = ["LOAD", 10, "ADD", "PRINT", "HALT", 0, 0, 0, 0, 0, 0, 0, 0]
vm = VonNeumannVM(program)
vm.run()
```

Here, both the instructions ("LOAD", "ADD", etc.) and data (10, 0, etc.) are stored
in the same memory array.


__Harvard VM__

In a Harvard VM, instructions and data are stored in *separate* arrays.
The VM fetches instructions from one array and data from another.

```python
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
```

In this example, instructions and data are stored in separate memory arrays.
The LOAD instruction fetches data from the data array based on an index.

* In the *von Neumann* example, both instructions and data occupy the same memory,
  leading to simpler implementation but potential contention.

* In the *Harvard* example, the separation allows parallel access to instructions
  and data, showcasing the core difference in memory handling.



### Project

*Design and Implement a Harvard Virtual Machine*

Design and implement a simplified Harvard architecture virtual machine (VM) in Python. The project will teach foundational
concepts of computer architecture, memory management, and instruction processing. By separating instruction and data memory,
you will explore the key differences between the Harvard and von Neumann architectures while developing problem-solving
and coding skills.

#### Steps

1. You will start with research and discussions on the key characteristics of Harvard architecture.
  - Separate memory for instructions and data.
  - Parallel access and reduced memory bottleneck.

2. Define a basic architecture with:
  - Two memory arrays: one for instructions, one for data.
  - A program counter (PC) to keep track of the current instruction.
  - Registers for temporary data storage (e.g., R0 for the accumulator).
  - A small instruction set (e.g., LOAD, STORE, ADD, SUB, PRINT, HALT).

3. Implement the VM in Python:
  - Init memory arrays.
  - Implement a simple instruction decoder.
  - Write the main loop to execute instructions step by step.

4. Build examples: write small 'programs' using the VM’s instruction set:
  - Arithmetic operations (e.g., adding and printing numbers).
  - Simulating control flow (loops, conditionals).
  - A basic calculator program.

5. Extend the VM (optional):
  - Stack-based operations. How would a stack operate in this machine?
  - Conditional jumps (JMP_IF, JMP).
  - A basic assembler to convert human-readable instructions to the VM’s format.


#### Tasks

*Task 1: Define the Instruction Set*

Decide on a minimal instruction set. For example:
- LOAD: Load data from memory into a register.
- STORE: Store data from a register into memory.
- ADD: Add values from two registers.
- SUB: Subtract values from two registers.
- PRINT: Print the value of a register.
- HALT: Stop execution.

*Task 2: Implement the VM Skeleton*

Write a Python class representing the Harvard VM. The class should include:
- Memory arrays for instructions and data.
- Registers and program counter.
- A method to execute instructions.

*Task 3: Develop and Test Programs*

Write small programs to test their VM. For example:
- Adding Two Numbers:
  - Data: [5, 10]
  - Instructions: [LOAD, 0, ADD, 1, PRINT, HALT]
- Simple Loop:
  - Data: [10]
  - Instructions: [LOAD, 0, PRINT, JMP, 1, HALT]

*Task 4: Debug and Optimise*

Run programs on the VM, identify bugs, and optimise execution (e.g. avoid hardcoded limits on memory).


#### Learning

1. Architecture Principles:
  - Understand the separation of instruction and data memory in Harvard architecture.
  - Compare the performance issues and complexity differences with von Neumann architecture.

2. Programming Skills:
  - Translate high-level logic into machine-level operations.
  - Implement and debug a processor-like system in Python.

3. Discovery and Insight:
  - Realize the constraints of early computing systems (e.g. limited instructions, memory management).
  - Explore the challenges of memory and instruction handling (e.g. bounds checking, program counter management).


#### Example Program

```python
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
```

#### Suggested Extensions

- Visualisation: Create a GUI to visualize the memory and instruction flow.
- Optimisation: Implement pipelining to simulate parallel fetching of instructions and data.
- Comparison: Build both von Neumann and Harvard VMs and run *the same program* on both to compare performance.


### Project 2

To simulate parallel processing in a Harvard machine using Python, we can explore the core
advantage of Harvard architecture: separate memory buses for instructions and data. This can
be extended by simulating simultaneous data access and instruction fetching, which is almost
achievable using Python's multithreading or asynchronous programming. While Python's Global
Interpreter Lock (GIL) prevents true parallel execution of threads in the standard CPython
interpreter, these approaches are sufficient to *illustrate* the concept.

#### Internals to Simulate

1. Parallel Fetching and Execution:
  - One thread or coroutine can simulate the instruction fetch unit (reading instructions).
  - Another can handle the data access unit (fetching/storing data for the current instruction).

2. Instruction Pipeline:
  - Implement a basic pipeline with stages such as fetch, decode, and execute, where different
    parts of the pipeline execute in parallel.
	
3. Memory Access Contention:
  - Simulate contention between instruction and data buses (optional for advanced scenarios).

4. Registers and ALU:
  - Design a simple arithmetic logic unit (ALU) for execution of instructions.
  - Use separate "registers" for instruction decoding and data handling.


#### Example: Simulating Parallel Fetch and Execute

Here’s how you could structure the simulation using Python’s asyncio for asynchronous operations:

```python
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
```


#### Enhanced Simulation: Instruction Pipelining

A more sophisticated parallel execution can include pipelining, where different stages
of instruction processing operate concurrently.

#### Pipelining Stages:

1. Fetch: Retrieve an instruction from instruction memory.
2. Decode: Decode the instruction to determine operands and operation.
3. Execute: Perform the operation, accessing data memory if needed.
4. Write back: Store results in registers or memory.

Using Python threads and queues to represent stages.

```python
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
```

#### Observations and Discussions

1. Parallelism: By *separating* fetching and execution, you can observe how tasks can overlap to improve performance.

2. Instruction pipelining: Learn the challenges of managing dependencies between instructions (e.g. a later instruction
   in the program relying on the result of a prior one).

3. Synchronization: There can be issues like queue contention, which mimic real-world complexities in hardware pipelines.

4. Efficiency trade-offs: Compare single-threaded execution with pipelined approaches to measure performance improvements.


#### Extensions

1. Hazards:
  - Explore data hazards, such as instructions that depend on the results of others.
  - Simulate pipeline stalls and hazard detection.

2. Out-of-Order Execution:
  - Simulate how modern processors execute independent instructions in parallel.

3. Cache Simulation:
  - Add caching for data memory and simulate how cache misses affect performance.

By simulating these advanced features, you can deepen your understanding of parallel processing and how it is implemented
in modern computing systems.
