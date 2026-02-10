
class VirtualMachine:
    def __init__(self):
        self.registers = {"R0": 0, "R1": 0}

    def execute(self, instructions):
        for instr in instructions:
            if instr[0] == "MOV":
                self.registers[instr[1]] = instr[2]

    def get_register(self, reg):
        return self.registers[reg]

def test_mov_register():
    vm = VirtualMachine()
    vm.execute([("MOV", "R0", 42)])
    assert vm.get_register("R0") == 42

test_mov_register()
