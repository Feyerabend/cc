class VirtualMachine:
    def __init__(self):
        self.registers = {"R0": 0, "R1": 0, "R2": 0}
        self.status_flag = None  # Tracks comparison result

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

test_jmp_if_instruction()
test_jmp_if_not_met()
