class VirtualMachine:
    def __init__(self):
        self.registers = {"R0": 0, "R1": 0, "R2": 0}
        self.status_flag = None

    def execute(self, instructions):
        ip = 0  # instruction pointer
        while ip < len(instructions):
            instr = instructions[ip]
            opcode = instr[0]

            print("R0:", self.registers["R0"])
            if opcode == "MOV":
                self.registers[instr[1]] = instr[2]

            elif opcode == "ADD":
                self.registers[instr[1]] += self.registers[instr[2]]

            elif opcode == "SUB":
                self.registers[instr[1]] -= self.registers[instr[2]]

            # we change this to include the optional numbers also, besides registers
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

test_jmp_if_instruction()
test_jmp_if_not_met()
test_loop_with_counter()
test_loop_skipped()
