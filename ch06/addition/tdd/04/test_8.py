class VirtualMachine:
    def __init__(self):
        self.registers = {f"R{i}": 0 for i in range(10)}  # 10 general-purpose registers
        self.status_flag = None
        self.flags = {}  # storing CMP results

    def resolve_operand(self, operand):
        if operand in self.registers:
            return self.registers[operand]
        return operand

    def execute(self, instructions):
        ip = 0
        while ip < len(instructions):
            instr = instructions[ip]
            opcode = instr[0]

            if opcode == "MOV":
                _, reg, value = instr
                self.registers[reg] = self.resolve_operand(value)

            elif opcode == "ADD":
                _, reg, value = instr
                self.registers[reg] += self.resolve_operand(value)

            elif opcode == "SUB":
                _, reg, value = instr
                self.registers[reg] -= self.resolve_operand(value)

            elif opcode == "MUL":
                _, reg, value = instr
                self.registers[reg] *= self.resolve_operand(value)

            elif opcode == "CMP":
                _, reg1, reg2 = instr
                val1 = self.resolve_operand(reg1)
                val2 = self.resolve_operand(reg2)
                if val1 < val2:
                    self.status_flag = "LESS"
                elif val1 > val2:
                    self.status_flag = "GREATER"
                else:
                    self.status_flag = "ZERO" # or EQUALS

            elif opcode == "JMP_IF":
                if self.status_flag == instr[1]:
                    ip = instr[2]  # jump address
                    continue

            elif opcode == "JMP":
                ip = instr[1]  # jump unconditionally
                continue

            elif opcode == "HALT":
                return

            ip += 1

    def get_register(self, reg):
        return self.registers[reg]

    def get_status_flag(self):
        return self.status_flag

def test_jmp_if_instruction():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 10),
        ("MOV", "R1", 20),
        ("MOV", "R2", 200),
        ("CMP", "R0", "R1"),      # Sets status flag to "LESS"
        ("JMP_IF", "LESS", 6),    # Should jump to instruction 6
        ("MOV", "R2", 100),       # Skipped if LESS
        ("MOV", "R2", 200)        # Executed if LESS
    ]
    vm.execute(program)
    assert vm.get_register("R2") == 200  # Ensure R2 holds the value from instruction 6

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

def test_loop_with_counter():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 5),          # R0 = 5 (loop counter)
        ("MOV", "R2", 1),          # R2 = 1 (const)
        ("MOV", "R1", 0),          # R1 = 0 (accumulator)
        ("CMP", "R0", 0),          # Compare R0 with 0
        ("JMP_IF", "ZERO", 8),     # Exit loop if R0 == 0
        ("ADD", "R1", "R0"),       # R1 += R0
        ("SUB", "R0", "R2"),       # R0 -= 1
        ("JMP", 3),                # Go back to loop start
        ("HALT",)                  # End program
    ]
    vm.execute(program)
    assert vm.get_register("R0") == 0   # Counter ends at 0
    assert vm.get_register("R1") == 15  # Accumulator = 5 + 4 + 3 + 2 + 1

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
    vm.execute(program)
    assert vm.get_register("R0") == 0  # unchanged
    assert vm.get_register("R1") == 0  # unchanged

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
    vm.execute(program)
    assert vm.get_register("R2") == 20  # R2 modified because conditions are true

def test_nested_loop_with_conditions():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 3),         # Outer loop counter              0
        ("MOV", "R2", 0),         # Accumulator                     1   
        ("MOV", "R1", 4),         # Condition variable              2
        # Outer Loop Start
        ("CMP", "R0", 0),         # Compare R0 with 0               3
        ("JMP_IF", "ZERO", 10),   # Exit outer loop if R0 == 0      4
        ("CMP", "R1", 5),         # Check R1 < 5                    5
        ("JMP_IF", "GREATER", 8), # Skip increment if R1 >= 5       6
        ("ADD", "R2", 10),        # Increment accumulator           7
        # Outer Loop End
        ("SUB", "R0", 1),         # Decrement R0                    8
        ("JMP", 2),               # Repeat outer loop               9
        ("HALT",)                 # Program end                     10
    ]
    vm.execute(program)
    assert vm.get_register("R2") == 30  # 3 * 10, as R1 < 5 in each iteration

def test_factorial():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 1),        # factorial = 1
        ("MOV", "R1", 5),        # n = 5

        # Loop start
        ("CMP", "R1", 0),        # Compare n > 0
        ("JMP_IF", "ZERO", 7),   # Exit loop if n == 0

        ("MUL", "R0", "R1"),     # factorial *= n
        ("SUB", "R1", 1),        # n -= 1
        ("JMP", 2),              # Jump to loop start

        # End of loop
        ("HALT",)
    ]
    vm.execute(program)
    assert vm.get_register("R0") == 120  # 5!


test_jmp_if_instruction()
test_jmp_if_not_met()
test_loop_with_counter()
test_loop_skipped()
test_nested_conditional_logic()
test_nested_loop_with_conditions()
test_factorial()
