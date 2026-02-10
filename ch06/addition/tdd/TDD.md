
## TDD in Practice

For building a more advanced TDD-driven virtual machine, let's expand the earlier
concepts to include features like registers, stack frames for function calls, basic I/O,
and more advanced control flow (e.g. conditionals, loops). This will result in a
richer virtual machine, while still keeping it manageable.

Let's design a Register-Based Virtual Machine (RVM) with a small instruction set that
can run more complex programs.


### Outline

1.	Registers: A fixed number of general-purpose registers (R0, R1, etc.)
    for storing values and intermediate results.

2.	Stack Frame: Support for function calls, with local variables and a
    return address, managed in a stack frame.

3.	Conditionals and Control Flow: JMP_IF, CMP (comparison), and branching
    instructions to allow conditional execution and loops.

4.	Basic I/O: Simple print or store operations to observe output.

5.	Additional Instructions: Support for additional operations, such as
    MUL, DIV, MOD, and others as needed.


### Expanded set

1.	MOV Rx, N: Move value N to register Rx.
2.	ADD Rx, Ry: Add values in registers Rx and Ry and store the result in Rx.
3.	SUB Rx, Ry: Subtract value in Ry from Rx and store the result in Rx.
4.	MUL, DIV, MOD: Multiplication, division, and modulus.
5.	PUSH Rx: Push the value in Rx onto the stack.
6.	POP Rx: Pop the top of the stack into register Rx.
7.	CALL addr: Call function at address addr, saving the return address.
8.	RET: Return from a function.
9.	JMP addr: Unconditional jump to address addr.
10.	CMP Rx, Ry: Compare values in Rx and Ry, setting status flags (e.g. ZERO, LESS, GREATER).
11.	JMP_IF flag, addr: Jump to addr if flag is true.
12.	PRINT Rx: Print the value in Rx.



### TDD Process for the RVM

How do we go about constructing this, if we would adopt a TDD process?

1. Start with a behaviour test: Define what the virtual machine should do, not how it works internally.
Example: __"The MOV instruction places a value into a register, and we can verify it by querying that register."__
As we are planning a virtual machine we can not abstract too much from implementation, even if we leave the
details.

2. Write the test First.

```python
def test_mov_register():
    vm = VirtualMachine()
    vm.execute([("MOV", "R0", 42)])
    assert vm.get_register("R0") == 42
```

3. Implementation (a minimum to pass): Implement just enough to make the test pass. This might mean hardcoding
the result initially.

```python
class VirtualMachine:
    def __init__(self):
        self.registers = {"R0": 0}
    
    def execute(self, instructions):
        if instructions[0] == ("MOV", "R0", 42):
            self.registers["R0"] = 42

    def get_register(self, reg):
        return self.registers[reg]
```

4. Refactor: Once the test passes, generalize the implementation without breaking the test.

```python
class VirtualMachine:
    def __init__(self):
        self.registers = {"R0": 0, "R1": 0}

    def execute(self, instructions):
        for instr in instructions:
            if instr[0] == "MOV":
                self.registers[instr[1]] = instr[2]

    def get_register(self, reg):
        return self.registers[reg]
```

Or, actually run the test 'test_mov_register()' so it fails when running in step 3. Then
make the minimum effort to see it succeed.

5. Expand tests: Write more tests for different cases and new instructions,
building on the general implementation.
- Test `ADD`: Ensure adding two registers updates the correct value.
- Test `CMP`: Ensure comparisons set a status flag correctly.
- Test `JMP_IF`: Validate branching behaviour based on status flags.

Each test focuses solely on *what* the VM does, not *how* it achieves it.

This approach ensures that:
- Behaviour-Driven: You only define what the system should do (outputs) given specific inputs.
- No Premature Optimisation: The design of the system emerges organically to satisfy the tests.
- No Over-design: Only the functionality that is required by the tests gets implemented.


### Conditional jumps and comparison

Let's see how we can expand this with jumps and comparison.

A. Test: Comparison (CMP)

Behaviour Definition: The CMP instruction compares the values of two registers and sets a status flag
(ZERO, LESS, or GREATER) based on the result.

1. Start with a simple test for the CMP instruction.

```python
def test_cmp_instruction():
    vm = VirtualMachine()
    vm.execute([
        ("MOV", "R0", 10),  # Init R0 with 10
        ("MOV", "R1", 20),  # Init R1 with 20
        ("CMP", "R0", "R1") # Compare R0 and R1
    ])
    assert vm.get_status_flag() == "LESS"  # 10 < 20
```

2. Implementation (minimum to pass)

Initially, implement just enough to make this test pass.

```python
class VirtualMachine:
    def __init__(self):
        self.registers = {"R0": 0, "R1": 0}
        self.status_flag = None  # Tracks comparison result

    def execute(self, instructions):
        for instr in instructions:
            if instr[0] == "MOV":
                self.registers[instr[1]] = instr[2]
            elif instr[0] == "CMP":
                if self.registers[instr[1]] < self.registers[instr[2]]:
                    self.status_flag = "LESS"

    def get_status_flag(self):
        return self.status_flag
```

3. Refactor

Generalize the comparison logic to handle all cases (LESS, GREATER, ZERO).

```python
elif instr[0] == "CMP":
    reg1, reg2 = instr[1], instr[2]
    if self.registers[reg1] < self.registers[reg2]:
        self.status_flag = "LESS"
    elif self.registers[reg1] > self.registers[reg2]:
        self.status_flag = "GREATER"
    else:
        self.status_flag = "ZERO"
```

4. Add More Tests

Expand the tests to cover all comparison outcomes.

```python
def test_cmp_equal():
    vm = VirtualMachine()
    vm.execute([
        ("MOV", "R0", 15),
        ("MOV", "R1", 15),
        ("CMP", "R0", "R1")
    ])
    assert vm.get_status_flag() == "ZERO"  # 15 == 15

def test_cmp_greater():
    vm = VirtualMachine()
    vm.execute([
        ("MOV", "R0", 25),
        ("MOV", "R1", 10),
        ("CMP", "R0", "R1")
    ])
    assert vm.get_status_flag() == "GREATER"  # 25 > 10
```


B. Test: Conditional Jump (JMP_IF)

Behaviour Definition: The JMP_IF instruction jumps to a specified instruction address if a given condition (LESS, GREATER, ZERO) is met.

1. Write a test where conditional jumping skips an instruction based on the flag.

```python
def test_jmp_if_instruction():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 10),
        ("MOV", "R1", 20),
        ("CMP", "R0", "R1"),      # Sets status flag to "LESS"
        ("JMP_IF", "LESS", 6),    # Should jump to instruction 6
        ("MOV", "R2", 100),       # Skipped if LESS
        ("MOV", "R2", 200)        # Executed if LESS
    ]
    vm.execute(program)
    assert vm.get_register("R2") == 200  # Ensure R2 holds the value from instruction 6
```

2. Implementation (minimum to pass)

Start with a hardcoded solution to handle the jump:

```python
def execute(self, instructions):
    ip = 0  # Instruction pointer
    while ip < len(instructions):
        instr = instructions[ip]
        if instr[0] == "MOV":
            self.registers[instr[1]] = instr[2]
        elif instr[0] == "CMP":
            reg1, reg2 = instr[1], instr[2]
            if self.registers[reg1] < self.registers[reg2]:
                self.status_flag = "LESS"
            elif self.registers[reg1] > self.registers[reg2]:
                self.status_flag = "GREATER"
            else:
                self.status_flag = "ZERO"
        elif instr[0] == "JMP_IF":
            if self.status_flag == instr[1]:
                ip = instr[2]  # Jump to address
                continue
        ip += 1
```

3. Refactor

Generalize the `JMP_IF` logic to handle all cases and prevent infinite loops.

Additional Tests and Features

1. Negative Tests: Ensure the jump doesn't happen if the condition is not met.

```python
def test_jmp_if_not_met():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 20),
        ("MOV", "R1", 10),
        ("CMP", "R0", "R1"),       # Sets status flag to "GREATER"
        ("JMP_IF", "LESS", 5),     # Should NOT jump
        ("MOV", "R2", 300)         # Executed because LESS is not met
    ]
    vm.execute(program)
    assert vm.get_register("R2") == 300
```

2. Chained Conditions: Test programs with multiple `JMP_IF` instructions for complex control flows.
3. Integration with Loops: Use `JMP_IF` for iterative behaviours (e.g. counting loops).

Recap: TDD in Action

1. Define Behaviour: Each test specifies what the VM should do for a given scenario.
2. Write the Test First: Add tests incrementally, covering basic and edge cases.
3. Implement Only to Pass: Create the simplest implementation that satisfies the test.
4. Refactor: Improve the code structure after passing tests, ensuring no regressions.


### Loops or nested conditional logic

To explore loops and nested conditional logic, we'll enhance the virtual machine's behaviour
step-by-step using TDD. Loops and nested logic often involve a combination of comparison (`CMP`),
conditional jumps (`JMP_IF`), and sometimes unconditional jumps (`JMP`).

1. Loops with Counter

Behaviour Definition

We'll implement a loop that decrements a register value until it reaches zero.

```pseudo
R0 = 5
while (R0 > 0):
    R1 += 10
    R0 -= 1
```

Test Case

Write a test to validate the loop's behaviour.

```python
def test_loop_with_counter():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 5),         # R0 = 5 (loop counter)
        ("MOV", "R1", 0),         # R1 = 0 (accumulator)
        ("CMP", "R0", 0),         # compare R0 with 0
        ("JMP_IF", "ZERO", 7),    # exit loop if R0 == 0
        ("ADD", "R1", 10),        # R1 += 10
        ("SUB", "R0", 1),         # R0 -= 1
        ("JMP", 2),               # go back to the loop start
        ("HALT",)                 # end program
    ]
    vm.load_program(program)
    vm.execute()
    assert vm.get_register("R0") == 0   # counter ends at 0
    assert vm.get_register("R1") == 50  # accumulator = 5 * 10
```

Why does this fail here? The comparison only takes care of registers
and not numbers, so also let's fix that. We make it more general, but we do not
break anything.

```python
elif opcode == "CMP":
    reg1, operand2 = instr[1], instr[2]
    value1 = self.registers[reg1]  # value from first register
    # if operand2 is a literal or a register
    value2 = self.registers[operand2] if operand2 in self.registers else operand2
    if value1 < value2:
        self.status_flag = "LESS"
    elif value1 > value2:
        self.status_flag = "GREATER"
    else:
        self.status_flag = "ZERO"
```

Refactor and Test Edge Cases

1. Edge Case: Ensure the loop is skipped if the initial condition is already false (e.g. R0 = 0).

```python
def test_loop_skipped():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 0),
        ("MOV", "R1", 0),
        ("CMP", "R0", 0),
        ("JMP_IF", "ZERO", 6),
        ("ADD", "R1", 10),     # skipped
        ("JMP", 2),
        ("HALT",)
    ]
    vm.load_program(program)
    vm.execute()
    assert vm.get_register("R0") == 0  # unchanged
    assert vm.get_register("R1") == 0  # unchanged
```

2. Nested Conditional Logic

Behavior Definition

Support nested conditions, e.g.

```pseudo
if (R0 > 0):
    if (R1 < 5):
        R2 += 20
```

Test Case

Write a test program with nested logic.

```python
def test_nested_conditional_logic():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 3),          # R0 = 3
        ("MOV", "R1", 4),          # R1 = 4
        ("MOV", "R2", 0),          # R2 = 0
        ("CMP", "R0", 0),          # compare R0 > 0
        ("JMP_IF", "LESS", 10),    # skip if R0 <= 0
        ("CMP", "R1", 5),          # compare R1 < 5
        ("JMP_IF", "GREATER", 10), # skip if R1 >= 5
        ("ADD", "R2", 20),         # R2 += 20 (if both conditions met)
        ("HALT",)
    ]
    vm.load_program(program)
    vm.execute()
    assert vm.get_register("R2") == 20  # R2 modified because conditions are true
```

Implementation

Update the VM to handle nested jumps by respecting the instruction pointer.
- Ensure CMP updates flags independently for each conditional block.
- Ensure JMP_IF doesn't interfere with subsequent instructions unless explicitly skipped.

And so on ..

*Project: Your task now, if you so wish to take this challenge, is to advance this project by completing
the current efforts. Review the work available in the folders 1, 2, 3, and 4, focusing on
refactoring at times of the code, and add logging to facilitate progress and troubleshooting.*


### Conclusion

Developing a robust virtual machine with TDD provides a structured, incremental approach
that emphasises clarity, correctness, and flexibility.

1. Behaviour-Driven Design: Each component (registers, stack frames, conditionals, loops,
   and I/O) is introduced with a clear behavioural expectation. Tests focus on what the
   system should achieve, not on how it is implemented.

2. Incremental Development: Starting with simple instructions like MOV and gradually adding
   complexity (e.g. CMP, JMP_IF, and nested conditionals) ensures that the implementation
   evolves in manageable steps. This approach avoids over-design and premature optimisation.

3. Refactoring for Generalisation: After passing initial tests, refactoring the implementation
   to handle edge cases and new scenarios promotes code reuse and flexibility, as seen with
   the CMP instruction's generalisation to handle both registers and literals.

4. Testing Edge Cases: Incorporating tests for skipped loops, nested conditionals, and invalid
   scenarios ensures the VM handles unexpected inputs gracefully, reinforcing its robustness.

5. Support for Advanced Control Flow: Implementing instructions for conditional and unconditional
   jumps enables complex program structures, including loops and nested logic, which are essential
   for more realistic programs.

6. Simplicity in Design: By adhering to TDD's “minimum effort to pass” philosophy, the implementation
   avoids unnecessary complexity, focusing only on functionality demanded by the tests.

This TDD-driven approach not only builds confidence in the correctness of the virtual
machine but also lays the groundwork for future expansions, such as support for arithmetic
operations, function calls, or even concurrency. The outlined process ensures a maintainable
and extensible design, making the RVM a practical foundation for increasingly sophisticated
programs.
