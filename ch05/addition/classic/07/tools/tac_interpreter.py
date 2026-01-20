import sys

class VM:
    def __init__(self, debug=False):
        self.variables = {}
        self.instructions = []
        self.pc = 0
        self.labels = {}
        self.call_stack = []
        self.comparison_ops = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '!=': lambda a, b: a != b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b
        }
        self.debug = debug
        self.breakpoints = set()
        self.current_frame = "main" # start at something

    def load_instruction(self, instruction):
        if instruction.get('op') == 'LABEL':
            label = instruction.get('result')
            if label:
                self.labels[label] = len(self.instructions)

        for field in ['arg1', 'arg2', 'result']:
            val = instruction.get(field)
            if val and not val.isdigit() and val != 'NULL':
                self.variables.setdefault(val, 0)
                
        self.instructions.append(instruction)

    def load_instructions_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                current = {}
                for line in file:
                    line = line.strip()
                    if not line:
                        if current:
                            self.load_instruction(current)
                            current = {}
                        continue
                    
                    if line.startswith('TYPE:'):
                        current['op'] = line.split('TYPE: ')[1]
                    elif line.startswith('ARG1:'):
                        current['arg1'] = line.split('ARG1: ')[1]
                    elif line.startswith('ARG2:'):
                        current['arg2'] = line.split('ARG2: ')[1]
                    elif line.startswith('RESULT:'):
                        current['result'] = line.split('RESULT: ')[1]
                
                if current:
                    self.load_instruction(current)
                    
        except Exception as e:
            print(f"Load error: {str(e)}")
            raise

    def load_symbol_table(self, filename):
        try:
            with open(filename, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith('GLOBAL_VARIABLE'):
                        parts = line.split()
                        var_name = parts[4]
                        var_type = parts[6]
                        self.variables[var_name] = 0  # init first to 0

                    elif line.startswith('PROCEDURE'):
                        parts = line.split()
                        proc_name = parts[4]
                        self.labels[proc_name] = len(self.instructions)  # procedure labels

        except Exception as e:
            print(f"Symbol table load error: {str(e)}")
            raise

    def initialize_globals_from_tac(self):
        for instr in self.instructions:
            op = instr['op']
            arg1 = instr.get('arg1', 'NULL')
            #arg2 = instr.get('arg2', 'NULL')
            result = instr.get('result', 'NULL')

            if op == 'LOAD':
                if arg1.isdigit():
                    self.variables[result] = int(arg1)
            elif op == '=':
                if result in self.variables:
                    self.variables[result] = self.get_val(arg1)

    def get_val(self, arg):
        if arg == 'NULL': return None
        if arg.isdigit(): return int(arg)
        return self.variables.get(arg, 0)

    def show_state(self):
        print(f"\n{' PC ':~^40}")
        print(f"Current Instruction: {self.pc}")
        print(f"Current Frame: {self.current_frame}")
        # print(f"Next Instruction: {self.instructions[self.pc] if self.pc < len(self.instructions) else 'END'}")
        print(f"\n{' VARIABLES ':~^40}")
        for k, v in self.filtered_variables().items():
            print(f"{k}: {v}")
        print(f"\n{' CALL STACK ':~^40}")
        print(self.call_stack)
        print(f"{'':~^40}\n")

    def filtered_variables(self):
        return {
            k: v for k, v in self.variables.items() 
            if not k.startswith('t') and 
            not k.endswith('.l') and 
            k not in self.labels
        }

    def handle_debug_input(self):
        while True:
            cmd = input("Debugger (step/break/continue/vars/quit): ").strip().lower()
            
            if cmd in ['', 's', 'step']:
                return True  # single step
            elif cmd.startswith('b '):
                try:
                    bp = int(cmd.split()[1])
                    self.breakpoints.add(bp)
                    print(f"Breakpoint set at PC {bp}")
                except (IndexError, ValueError):
                    print("Invalid breakpoint format. Use: b <pc>")
            elif cmd in ['c', 'continue']:
                return False  # continue ..
            elif cmd in ['v', 'vars']:
                self.show_state()
            elif cmd in ['q', 'quit']:
                sys.exit(0)
            else:
                print("Invalid command. Options: step(s), break(b), continue(c), vars(v), quit(q)")

    def execute(self):
        print("Starting execution...")
        self.pc = self.labels.get('main', 0)

        while self.pc < len(self.instructions):
            instr = self.instructions[self.pc]
            op = instr['op']
            arg1 = instr.get('arg1', 'NULL')
            arg2 = instr.get('arg2', 'NULL')
            result = instr.get('result', 'NULL')

            # debugger breakpoints and controls
            if self.debug:
                if self.pc in self.breakpoints:
                    print(f"\nBreakpoint hit at PC {self.pc}")
                    self.show_state()
                    if self.handle_debug_input():
                        continue
                
                self.show_state()
                if not self.handle_debug_input():
                    self.debug = False  # .. until next breakpoint

            try:
                # control flow operations
                if op == 'LABEL':
                    self.current_frame = result
                    self.pc += 1
                    continue
                    
                elif op == 'GOTO':
                    self.pc = self.labels[arg1]
                    continue
                    
                elif op == 'IF_NOT':
                    if not self.get_val(arg1):
                        self.pc = self.labels[arg2]
                    else:
                        self.pc += 1
                    continue
                    
                elif op == 'CALL':
                    self.call_stack.append((self.pc + 1, self.current_frame))
                    self.current_frame = arg1
                    self.pc = self.labels[arg1]
                    continue
                    
                elif op == 'RETURN':
                    ret_pc, self.current_frame = self.call_stack.pop()
                    self.pc = ret_pc
                    continue

                # data
                val1 = self.get_val(arg1)
                val2 = self.get_val(arg2) if arg2 != 'NULL' else None

                if op == '=':
                    self.variables[result] = val1
                elif op in self.comparison_ops:
                    cmp_result = self.comparison_ops[op](val1, val2)
                    self.variables[result] = 1 if cmp_result else 0
                elif op == '+':
                    self.variables[result] = val1 + val2
                elif op == '-':
                    self.variables[result] = val1 - val2
                elif op == '*':
                    self.variables[result] = val1 * val2
                elif op == '/':
                    self.variables[result] = val1 // val2
                elif op == 'LOAD':
                    self.variables[result] = val1
                else:
                    raise RuntimeError(f"Unknown operation: {op}")

                self.pc += 1

            except Exception as e:
                print(f"CRASH at PC {self.pc}")
                print(f"Instruction: {instr}")
                print(f"Variables: {self.filtered_variables()}")
                print(f"Call stack: {self.call_stack}")
                print(f"Error: {str(e)}")
                return

        print("Execution completed successfully")
        print("Final states:")
        self.show_state()

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 tac_interpreter.py <symbol_table_file> <tac_file> [output_file] [-d|--debug]")
        sys.exit(1)

    debug = '-d' in sys.argv or '--debug' in sys.argv
    args = [arg for arg in sys.argv[1:] if arg not in ['-d', '--debug']]

    symbol_table_file = args[0]
    tac_file = args[1]
    output_file = args[2] if len(args) > 2 else None

    vm = VM(debug=debug)
    vm.load_symbol_table(symbol_table_file)  # symbol table first
    vm.load_instructions_from_file(tac_file)  # TAC instructions
    vm.initialize_globals_from_tac()  # init global variables from TAC
    vm.execute()

    if output_file:
        with open(output_file, 'w') as f:
            f.write("Final memory state:\n")
            f.write(str(vm.filtered_variables()))

if __name__ == "__main__":
    main()
