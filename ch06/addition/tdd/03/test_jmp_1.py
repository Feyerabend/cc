
def test_jmp_if_instruction():
    vm = VirtualMachine()
    program = [
        ("MOV", "R0", 10),
        ("MOV", "R1", 20),
        ("CMP", "R0", "R1"),      # Sets status flag to "LESS"
        ("JMP_IF", "LESS", 6),    # Should jump to instruction 6
        ("MOV", "R2", 100),       # Skipped if LESS
        ("MOV", "R2", 200)        # Executed if LESS
    ]
    vm.execute(program)
    assert vm.get_register("R2") == 200  # Ensure R2 holds the value from instruction 6

test_jmp_if_instruction()
