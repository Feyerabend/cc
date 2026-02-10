
def test_cmp_instruction():
    vm = VirtualMachine()
    vm.execute([
        ("MOV", "R0", 10),  # Initialize R0 with 10
        ("MOV", "R1", 20),  # Initialize R1 with 20
        ("CMP", "R0", "R1") # Compare R0 and R1
    ])
    assert vm.get_status_flag() == "LESS"  # 10 < 20

test_cmp_instruction()
