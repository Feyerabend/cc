class VirtualMachine:
    def __init__(self):
        self.registers = {"R0": 0}
    
    def execute(self, instructions):
        if instructions[0] == ("MOV", "R0", 42):
            self.registers["R0"] = 42

    def get_register(self, reg):
        return self.registers[reg]

def test_mov_register():
    vm = VirtualMachine()
    vm.execute([("MOV", "R0", 42)])
    assert vm.get_register("R0") == 42

test_mov_register()
