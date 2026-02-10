
def test_mov_register():
    vm = VirtualMachine()
    vm.execute([("MOV", "R0", 42)])
    assert vm.get_register("R0") == 42

test_mov_register()
