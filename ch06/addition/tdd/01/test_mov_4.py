
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

def test_mov_register_zero():
    vm = VirtualMachine()
    vm.execute([("MOV", "R0", 0)])
    assert vm.get_register("R0") == 0

def test_mov_registers():
    vm = VirtualMachine()
    vm.execute([("MOV", "R1", 142)])
    vm.execute([("MOV", "R0", 78)])
    assert vm.get_register("R1") == 142
    assert vm.get_register("R0") == 78

def test_mov_register_negative():
    vm = VirtualMachine()
    vm.execute([("MOV", "R1", -42)])
    assert vm.get_register("R1") == -42

def test_mov_register_negative_float():
    vm = VirtualMachine()
    vm.execute([("MOV", "R1", -123.4)])
    assert vm.get_register("R1") == -123.4

test_mov_register()
test_mov_register_zero()
test_mov_registers()
