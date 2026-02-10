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

def test_cmp_instruction():
    vm = VirtualMachine()
    vm.execute([
        ("MOV", "R0", 10),  # Initialize R0 with 10
        ("MOV", "R1", 20),  # Initialize R1 with 20
        ("CMP", "R0", "R1") # Compare R0 and R1
    ])
    assert vm.get_status_flag() == "LESS"  # 10 < 20

test_cmp_instruction()
