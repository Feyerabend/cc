
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

    def get_status_flag(self):
        return self.status_flag

def test_mov_register():
    vm = VirtualMachine()
    vm.execute([("MOV", "R0", 42)])
    assert vm.get_register("R0") == 42

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

test_mov_register()
test_cmp_equal()
test_cmp_greater()
