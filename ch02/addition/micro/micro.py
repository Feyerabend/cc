class MicrocodeEngine:
    def __init__(self):
        self.registers = {'A': 0, 'B': 0, 'ACC': 0}  # Simulated registers: A, B, and accumulator (ACC)
        self.microcode = {
            'LOAD_A': self.load_a,
            'LOAD_B': self.load_b,
            'MICRO_ADD': self.micro_add,
            'MICRO_SUB': self.micro_sub,
            'OUTPUT_ACC': self.output_acc
        }

    def load_a(self, value):
        """Load a value into register A."""
        self.registers['A'] = value

    def load_b(self, value):
        """Load a value into register B."""
        self.registers['B'] = value

    def micro_add(self):
        """Perform addition of A and B, storing the result in ACC."""
        self.registers['ACC'] = self.registers['A'] + self.registers['B']

    def micro_sub(self):
        """Perform subtraction of B from A, storing the result in ACC."""
        self.registers['ACC'] = self.registers['A'] - self.registers['B']

    def output_acc(self):
        """Output the value in the accumulator."""
        print(f"Output (ACC): {self.registers['ACC']}")

    def execute_microcode(self, instructions):
        """Execute a series of micro-instructions."""
        for instr in instructions:
            if len(instr) == 2:
                # .. like LOAD_A 5
                self.microcode[instr[0]](instr[1])
            else:
                # .. like MICRO_ADD
                self.microcode[instr[0]]()

def execute_program(engine, program):
    """Translate high-level instructions into microcode and execute them."""
    for instruction in program:
        if instruction[0] == 'ADD':
            micro_instructions = [
                ('LOAD_A', instruction[1]),
                ('LOAD_B', instruction[2]),
                ('MICRO_ADD',),
                ('OUTPUT_ACC',)
            ]
        elif instruction[0] == 'SUB':
            micro_instructions = [
                ('LOAD_A', instruction[1]),
                ('LOAD_B', instruction[2]),
                ('MICRO_SUB',),
                ('OUTPUT_ACC',)
            ]
        else:
            raise ValueError(f"Unknown instruction: {instruction[0]}")
        
        engine.execute_microcode(micro_instructions)


engine = MicrocodeEngine()
program = [
    ('ADD', 7, 3),  # ADD: 7 + 3
    ('SUB', 10, 4)  # HSUB: 10 - 4
]
execute_program(engine, program)
