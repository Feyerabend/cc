
class REGVMStaticAnalyzer:
    def __init__(self):
        self.valid_opcodes = {
            'MOV': 2,   # intruction: no. of arguments
            'ADD': 2, 
            'SUB': 2, 
            'MUL': 2, 
            'CMP': 2, 
            'JMP': 1, 
            'JZ': 1, 
            'PRINT': 1
        }
        self.registers = {'A', 'B', 'C', 'D'}
        self.labels = set()

    def analyze(self, program):
        issues = []
        # pass 1: collect labels
        for i, instruction in enumerate(program):
            parts = instruction.split()
            if len(parts) == 1 and parts[0].endswith(':'):
                label = parts[0][:-1]
                if not label.isidentifier():
                    issues.append((i, f"Invalid label name: {label}"))
                self.labels.add(label)

        # pass 2: check instructions
        for i, instruction in enumerate(program):
            parts = instruction.split()
            if len(parts) == 0:
                issues.append((i, "Empty instruction"))
                continue

            if parts[0].endswith(':'):
                # skip labels e.g. 'START:'
                continue

            opcode = parts[0]
            args = parts[1:]

            if opcode not in self.valid_opcodes:
                issues.append((i, f"Unknown opcode: {opcode}"))
                continue

            required_args = self.valid_opcodes[opcode]
            if len(args) != required_args:
                issues.append((i, f"Incorrect number of arguments for {opcode}: expected {required_args}, got {len(args)}"))
                continue

            if opcode == 'MOV':
                if args[0] not in self.registers:
                    issues.append((i, f"Invalid destination register: {args[0]}"))
                if not (args[1].isdigit() or args[1].isalpha()):
                    issues.append((i, f"Invalid source operand: {args[1]}"))

            elif opcode in {'ADD', 'SUB', 'MUL'}:
                if args[0] not in self.registers:
                    issues.append((i, f"Invalid destination register: {args[0]}"))
                if not (args[1].isdigit() or args[1] in self.registers):
                    issues.append((i, f"Invalid operand: {args[1]}"))

            elif opcode == 'CMP':
                if args[0] not in self.registers:
                    issues.append((i, f"Invalid first operand: {args[0]}"))
                if not args[1].isdigit():
                    issues.append((i, f"Second operand must be an integer: {args[1]}"))

            elif opcode in {'JMP', 'JZ'}:
                if not args[0].isdigit() and args[0] not in self.labels:
                    issues.append((i, f"Invalid jump target: {args[0]}"))

            elif opcode == 'PRINT':
                if args[0] not in self.registers:
                    issues.append((i, f"Invalid register to print: {args[0]}"))

        return issues


# example
factorial = [
    # start:
    "MOV A 1",   # init A with 1
    "MOV B 5",   # init B with 5
    
    # loop:
    "CMP B 0",   # compare B with 0
    "JZ 7",      # if B is 0, jump to end
    
    "MUL A B",   # multiply A by B and store in A
    "SUB B 1",   # subtract 1 from B
    "JMP 3",     # jump to loop
    
    # end:
    "PRINT A",   # print the result in register A
]

analyzer = REGVMStaticAnalyzer()
issues = analyzer.analyze(factorial)

if issues:
    print("Static Analysis:")
    for line, issue in issues:
        print(f"Line {line + 1}: {issue}")
else:
    print("No issues found in the program.")
