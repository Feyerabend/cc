
class VirtualMachine:
    def __init__(self):
        self.registers = {"R0": 0, "R1": 0}

    def execute(self, instructions):
        for instr in instructions:
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

    def get_register(self, reg):
        return self.registers[reg]

def test_mov_register():
    vm = VirtualMachine()
    vm.execute([("MOV", "R0", 42)])
    assert vm.get_register("R0") == 42

test_mov_register()
